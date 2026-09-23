#!/usr/bin/env python3
"""PostgreSQL acceptance for browser cookie/CORS/CSRF boundaries.

This is a deterministic, no-network acceptance.  The exact allowed Origin is the
CSRF boundary for all cookie-authenticated state-changing browser routes; a
missing or foreign Origin must fail before any durable mutation.  Registration
delivery is synthetic and in-process only.
"""
from __future__ import annotations

import http.client
import json
import os
import sys
import threading
from http.server import HTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
    str(ENGINE / "peis-trusted-host-reference"),
    str(ENGINE / "identity-reference"),
]

import learner_web_runtime as learner_runtime  # noqa: E402
import runtime as core  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402

ORIGIN = "https://eksamio.ru"
ATTACKER_ORIGIN = "https://attacker.invalid"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class CaptureDelivery:
    def __init__(self) -> None:
        self.codes: dict[str, str] = {}
        self.calls = 0

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        require(channel == "email", "registration delivery remains email-only")
        require(contact.endswith("@learner.invalid"), "CI delivery must remain synthetic")
        self.calls += 1
        self.codes[challenge_id] = code
        return "capture:" + challenge_id


def request_json(
    port: int,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    cookie: str | None = None,
    origin: str | None = ORIGIN,
):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Content-Type": "application/json"}
    if origin is not None:
        headers["Origin"] = origin
    if cookie:
        headers["Cookie"] = cookie
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read()
    status = response.status
    out_headers = dict(response.getheaders())
    connection.close()
    decoded = json.loads(raw.decode("utf-8")) if raw else {}
    return status, out_headers, decoded


def registration_payload(*, request_id: str) -> dict[str, Any]:
    return {
        "email": "security-boundary@learner.invalid",
        "personal_data_consent": True,
        "marketing_consent": True,
        "personal_data_document_version": "pd-doc-v1",
        "personal_data_text_version": "pd-text-v1",
        "marketing_document_version": "marketing-doc-v1",
        "marketing_text_version": "marketing-text-v1",
        "client_request_id": request_id,
    }


def revoke_payload(*, request_id: str) -> dict[str, Any]:
    return {
        "document_version": "marketing-doc-v1",
        "text_version": "marketing-text-v1",
        "client_request_id": request_id,
    }


def main() -> None:
    dsn = os.environ.get("EKSAMIO_TEST_POSTGRES_DSN", "")
    require(bool(dsn), "EKSAMIO_TEST_POSTGRES_DSN is required")
    evidence = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8")
    )
    nba = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(encoding="utf-8")
    )

    delivery = CaptureDelivery()
    ready = threading.Event()
    shared: dict[str, Any] = {}

    def server_thread() -> None:
        store = None
        server = None
        try:
            store = PostgresPeisPersistenceStore(dsn, evidence_schema=evidence, nba_schema=nba)
            runtime = core.build_runtime(
                store,
                writes_enabled=False,
                allowed_origin=ORIGIN,
                contact_hmac_key=b"c" * 32,
                verification_hmac_key=b"v" * 32,
                host_signing_key=b"h" * 32,
                delivery_provider=delivery,
                registration_begin_enabled=True,
                identity_required_for_ready=True,
            )
            server = HTTPServer(
                ("127.0.0.1", 0),
                learner_runtime.make_handler(runtime, None, None),
            )
            shared["server"] = server
            shared["port"] = int(server.server_address[1])
            ready.set()
            server.serve_forever()
        except BaseException as exc:
            shared["error"] = exc
            ready.set()
        finally:
            if server is not None:
                server.server_close()
            if store is not None:
                store.close()

    thread = threading.Thread(target=server_thread, name="browser-security-ci", daemon=True)
    thread.start()
    require(ready.wait(timeout=10), "browser security runtime did not become ready")
    if "error" in shared:
        raise shared["error"]
    port = int(shared["port"])
    server = shared["server"]

    try:
        # Registration itself is state-changing: foreign/missing Origin must fail
        # before a challenge or synthetic delivery can be created.
        status, _headers, blocked = request_json(
            port,
            "POST",
            "/v1/registration/begin",
            payload=registration_payload(request_id="csrf-registration-attacker"),
            origin=ATTACKER_ORIGIN,
        )
        require(status == 403 and blocked.get("error") == "ORIGIN_NOT_ALLOWED", "foreign-origin registration is blocked")
        require(delivery.calls == 0, "foreign-origin registration causes no delivery")

        status, _headers, blocked = request_json(
            port,
            "POST",
            "/v1/registration/begin",
            payload=registration_payload(request_id="csrf-registration-missing"),
            origin=None,
        )
        require(status == 403 and blocked.get("error") == "ORIGIN_NOT_ALLOWED", "missing-origin registration is blocked")
        require(delivery.calls == 0, "missing-origin registration causes no delivery")

        status, _headers, begin = request_json(
            port,
            "POST",
            "/v1/registration/begin",
            payload=registration_payload(request_id="csrf-registration-valid"),
        )
        require(status == 202 and begin.get("status") == "CHALLENGE_SENT", "allowed-origin registration begins")
        challenge_id = str(begin["challenge_id"])
        require(delivery.calls == 1, "allowed-origin registration produces one synthetic delivery")

        status, headers, verified = request_json(
            port,
            "POST",
            "/v1/registration/verify",
            payload={"challenge_id": challenge_id, "code": delivery.codes[challenge_id]},
        )
        require(status == 200 and verified.get("status") == "AUTHENTICATED", "allowed-origin verification authenticates")
        set_cookie = str(headers.get("Set-Cookie", ""))
        for attribute in ("Secure", "HttpOnly", "SameSite=Lax", "Path=/"):
            require(attribute in set_cookie, f"session cookie must contain {attribute}")
        require(headers.get("Access-Control-Allow-Origin") == ORIGIN, "credentialed CORS returns the exact allowed origin")
        require(headers.get("Access-Control-Allow-Credentials") == "true", "credentialed CORS is explicit")
        cookie = set_cookie.split(";", 1)[0]
        raw_token = cookie.split("=", 1)[1]
        require(raw_token and raw_token not in json.dumps(verified), "raw session token is not exposed in JSON")

        # Foreign/missing Origin must not revoke consent or log the learner out.
        status, _headers, blocked = request_json(
            port,
            "POST",
            "/api/consent/marketing/revoke",
            cookie=cookie,
            payload=revoke_payload(request_id="csrf-revoke-attacker"),
            origin=ATTACKER_ORIGIN,
        )
        require(status == 403 and blocked.get("error") == "ORIGIN_NOT_ALLOWED", "foreign-origin marketing revoke is blocked")

        status, _headers, blocked = request_json(
            port,
            "POST",
            "/api/consent/marketing/revoke",
            cookie=cookie,
            payload=revoke_payload(request_id="csrf-revoke-missing"),
            origin=None,
        )
        require(status == 403 and blocked.get("error") == "ORIGIN_NOT_ALLOWED", "missing-origin marketing revoke is blocked")

        status, _headers, blocked = request_json(
            port,
            "POST",
            "/api/identity/logout",
            cookie=cookie,
            payload={},
            origin=ATTACKER_ORIGIN,
        )
        require(status == 403 and blocked.get("error") == "ORIGIN_NOT_ALLOWED", "foreign-origin logout is blocked")

        status, _headers, blocked = request_json(
            port,
            "POST",
            "/api/identity/logout",
            cookie=cookie,
            payload={},
            origin=None,
        )
        require(status == 403 and blocked.get("error") == "ORIGIN_NOT_ALLOWED", "missing-origin logout is blocked")

        status, _headers, session = request_json(port, "GET", "/api/identity/session", cookie=cookie)
        require(status == 200 and session.get("authenticated") is True, "blocked CSRF attempts do not revoke the session")

        import psycopg

        with psycopg.connect(dsn) as connection:
            revoke_count = connection.execute(
                "SELECT COUNT(*) FROM registration_consent_events WHERE consent_type='MARKETING' AND action='REVOKE'"
            ).fetchone()[0]
        require(int(revoke_count) == 0, "blocked CSRF attempts create no marketing revoke event")

        status, _headers, revoked = request_json(
            port,
            "POST",
            "/api/consent/marketing/revoke",
            cookie=cookie,
            payload=revoke_payload(request_id="csrf-revoke-valid"),
        )
        require(status == 200 and revoked.get("status") == "RECORDED", "allowed-origin marketing revoke persists")

        status, logout_headers, logged_out = request_json(
            port,
            "POST",
            "/api/identity/logout",
            cookie=cookie,
            payload={},
        )
        require(status == 200 and logged_out.get("status") in {"LOGGED_OUT", "ALREADY_LOGGED_OUT"}, "allowed-origin logout revokes session")
        clear_cookie = str(logout_headers.get("Set-Cookie", ""))
        for attribute in ("Secure", "HttpOnly", "SameSite=Lax", "Path=/", "Max-Age=0"):
            require(attribute in clear_cookie, f"logout cookie must contain {attribute}")

        status, _headers, after_logout = request_json(port, "GET", "/api/identity/session", cookie=cookie)
        require(status == 200 and after_logout.get("authenticated") is False, "revoked cookie no longer authenticates")
    finally:
        server.shutdown()
        thread.join(timeout=10)

    if "error" in shared:
        raise shared["error"]

    print("BROWSER_SECURITY_POSTGRES=PASS")
    print("exact_origin_csrf_boundary=PASS")
    print("secure_httponly_samesite_cookie=PASS")
    print("blocked_csrf_mutations=0")
    print("real_provider_calls=0")


if __name__ == "__main__":
    main()
