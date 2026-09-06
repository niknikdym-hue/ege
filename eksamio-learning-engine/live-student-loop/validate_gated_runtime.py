#!/usr/bin/env python3
from __future__ import annotations

import http.client
import json
import tempfile
import threading
from pathlib import Path

import gated_runtime as gated
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


def raw_request(port: int, method: str, path: str, *, body: str | None = None, cookie: str | None = None):
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
    status = response.status
    conn.close()
    return status, headers_out, payload


def json_request(port: int, method: str, path: str, *, body: str | None = None, cookie: str | None = None):
    status, headers, payload = raw_request(port, method, path, body=body, cookie=cookie)
    return status, headers, json.loads(payload.decode("utf-8"))


def main() -> None:
    gated_source = Path(gated.__file__).read_text(encoding="utf-8")
    registered_source = Path(registered.__file__).read_text(encoding="utf-8")
    installer = (Path(__file__).parent / "macos" / "install-desktop-app.sh").read_text(encoding="utf-8")

    require("if self._authenticated_host(required=False) is None:" in gated_source,
            "trainer page itself must be authentication-gated")
    require("super()._serve_trainer()" in gated_source,
            "authenticated learner reuses the admitted trainer package")
    require("registration_http.py из PR #186" in gated_source,
            "owner-test login must not impersonate production legal registration")
    require("gated_runtime.py" in installer,
            "macOS staging app must launch the gated registered runtime")
    for forbidden in ("demo-continuity", "ANON_COOKIE", "_ensure_anon_cookie", "ensure_anonymous("):
        require(forbidden not in registered_source, f"registered transport excludes legacy anonymous admission: {forbidden}")
    require("anonymous_host_token=None" in registered_source,
            "registered owner-test identity is created without anonymous continuity")
    require('host = self._authenticated_host(required=True)' in registered_source,
            "server learning writes require authenticated session")

    with tempfile.TemporaryDirectory() as tmp:
        app = registered.RegisteredLiveStudentLoop(Path(tmp) / "registered.sqlite", b"r" * 48, owner_test=True)
        server = gated.GatedRegisteredLoopServer(("127.0.0.1", 0), app)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            status, headers, payload = json_request(port, "GET", "/api/identity/session")
            require(status == 200 and payload["authenticated"] is False,
                    "unauthenticated session probe stays unauthenticated")
            require("Set-Cookie" not in headers,
                    "unauthenticated read emits no anonymous cookie")

            status, headers, raw = raw_request(port, "GET", "/trainer/")
            html = raw.decode("utf-8")
            require(status == 200, "registered gate page is readable before login")
            require("Set-Cookie" not in headers, "gate page emits no identity cookie")
            require("Войдите, чтобы начать учебную работу" in html,
                    "unauthenticated learner sees registered entry gate")
            require("window.EKSAMIO_LEARNER_LOOP_CONFIG" not in html,
                    "actual trainer runtime is not delivered before login")
            require("__EKSAMIO_PEIS_HOOK__" not in html,
                    "PEIS browser hook is not delivered before login")

            status, _headers, payload = json_request(port, "POST", "/api/peis/checked-card", body="{}")
            require(status == 401 and payload["error"] == "AUTHENTICATION_REQUIRED",
                    "PEIS write is rejected before authentication")

            status, _headers, payload = json_request(port, "GET", "/api/russian/profile")
            require(status == 401 and payload["error"] == "AUTHENTICATION_REQUIRED",
                    "learner progress read is rejected before authentication")

            status, headers, payload = json_request(port, "POST", "/api/identity/owner-test-login", body="{}")
            require(status == 200 and payload["authenticated"] is True,
                    "owner-test login creates registered server session")
            set_cookie = headers.get("Set-Cookie", "")
            require(legacy.SESSION_COOKIE in set_cookie and "anon" not in set_cookie.lower(),
                    "login response contains no anonymous cookie")
            first_token = session_token(set_cookie)
            first_host = app.identity.resolve_session(first_token)

            status, _headers, payload = json_request(port, "GET", "/api/identity/session", cookie=cookie_pair(set_cookie))
            require(status == 200 and payload["authenticated"] is True,
                    "session cookie authenticates learner read path")

            status, headers_after, raw = raw_request(port, "GET", "/trainer/", cookie=cookie_pair(set_cookie))
            html = raw.decode("utf-8")
            require(status == 200, "authenticated trainer page is readable")
            require("Set-Cookie" not in headers_after, "authenticated trainer read does not mint another identity")
            require("window.EKSAMIO_LEARNER_LOOP_CONFIG" in html,
                    "actual trainer runtime is delivered after login")
            require("__EKSAMIO_PEIS_HOOK__" in html,
                    "PEIS browser hook is delivered only after login")

            _second_payload, second_cookie = app.owner_test_login()
            second_host = app.identity.resolve_session(session_token(second_cookie))
            require(first_host.learner_profile_id == second_host.learner_profile_id,
                    "same registered email resolves to one learner profile across sessions")
        finally:
            server.shutdown()
            server.server_close()
            app.close()
            thread.join(timeout=3)

    print("GATED_REGISTERED_LIVE_STUDENT_LOOP=PASS")
    print("trainer_before_auth=BLOCKED")
    print("anonymous_progress=0")
    print("anonymous_cookie=0")
    print("peis_requires_authentication=PASS")
    print("registered_profile_continuity=PASS")


if __name__ == "__main__":
    main()
