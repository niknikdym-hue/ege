#!/usr/bin/env python3
from __future__ import annotations

import http.client
import json
import tempfile
import threading
from pathlib import Path

import registered_runtime as registered
import runtime as legacy


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def cookie_pair(set_cookie: str) -> str:
    return set_cookie.split(";", 1)[0]


def session_token(set_cookie: str) -> str:
    pair = cookie_pair(set_cookie)
    name, value = pair.split("=", 1)
    require(name == legacy.SESSION_COOKIE, "owner-test login sets only the server session cookie")
    return value


def request(port: int, method: str, path: str, *, body: str | None = None, cookie: str | None = None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    headers = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body.encode("utf-8")))
    if cookie:
        headers["Cookie"] = cookie
    conn.request(method, path, body=body, headers=headers)
    response = conn.getresponse()
    payload = response.read()
    headers_out = dict(response.getheaders())
    conn.close()
    return response.status, headers_out, json.loads(payload.decode("utf-8"))


def main() -> None:
    source = Path(registered.__file__).read_text(encoding="utf-8")
    for forbidden in ("demo-continuity", "ANON_COOKIE", "_ensure_anon_cookie", "ensure_anonymous("):
        require(forbidden not in source, f"registered transport excludes legacy anonymous admission: {forbidden}")
    require("anonymous_host_token=None" in source, "owner-test login creates identity without anonymous continuity")
    require('host = self._authenticated_host(required=True)' in source, "learning writes require authenticated session")
    require('parsed.path in {"/v0/checked-card", "/api/peis/checked-card"}' in source, "PEIS route remains explicitly mounted")
    require("registration_http.py from PR #186" in source, "owner-test transport does not impersonate production registration")

    with tempfile.TemporaryDirectory() as tmp:
        app = registered.RegisteredLiveStudentLoop(Path(tmp) / "registered.sqlite", b"r" * 48, owner_test=True)
        server = registered.RegisteredLoopServer(("127.0.0.1", 0), app)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status, headers, payload = request(port, "GET", "/api/identity/session")
            require(status == 200 and payload["authenticated"] is False, "unauthenticated session probe creates no learner session")
            require("Set-Cookie" not in headers, "unauthenticated read emits no anonymous cookie")

            status, headers, payload = request(port, "GET", "/trainer/")
            require(status == 200, "trainer remains readable before login")
            require("Set-Cookie" not in headers, "trainer page emits no anonymous identity cookie")

            status, _headers, payload = request(port, "POST", "/api/peis/checked-card", body="{}")
            require(status == 401 and payload["error"] == "AUTHENTICATION_REQUIRED", "PEIS write is rejected before authentication")

            status, headers, payload = request(port, "POST", "/api/identity/owner-test-login", body="{}")
            require(status == 200 and payload["authenticated"] is True, "owner-test login creates registered server session")
            set_cookie = headers.get("Set-Cookie", "")
            require(legacy.SESSION_COOKIE in set_cookie and "anon" not in set_cookie.lower(), "login response contains no anonymous cookie")
            first_token = session_token(set_cookie)
            first_host = app.identity.resolve_session(first_token)

            status, _headers, payload = request(port, "GET", "/api/identity/session", cookie=cookie_pair(set_cookie))
            require(status == 200 and payload["authenticated"] is True, "session cookie authenticates learner read path")

            _second_payload, second_cookie = app.owner_test_login()
            second_host = app.identity.resolve_session(session_token(second_cookie))
            require(first_host.learner_profile_id == second_host.learner_profile_id, "same registered email resolves to one learner profile across sessions")
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=3)

    print("REGISTERED_LIVE_STUDENT_LOOP=PASS")
    print("anonymous_progress=0")
    print("anonymous_cookie=0")
    print("peis_requires_authentication=PASS")
    print("registered_profile_continuity=PASS")


if __name__ == "__main__":
    main()
