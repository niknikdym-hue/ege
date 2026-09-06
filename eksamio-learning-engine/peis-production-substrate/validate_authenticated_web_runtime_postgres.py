#!/usr/bin/env python3
"""End-to-end private web runtime acceptance on real PostgreSQL."""
from __future__ import annotations

import http.client
import json
import os
import sys
import threading
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
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from russian_exceptions_practice_adapter import (  # noqa: E402
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)
from runtime import build_runtime, make_handler  # noqa: E402
from http.server import HTTPServer  # noqa: E402


ORIGIN = "https://eksamio.ru"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class CaptureDelivery:
    def __init__(self) -> None:
        self.codes: dict[str, str] = {}
        self.contacts: dict[str, str] = {}

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        require(channel == "email", "runtime registration is email-only")
        require(contact.endswith("@learner.invalid"), "CI delivery remains synthetic")
        self.codes[challenge_id] = code
        self.contacts[challenge_id] = contact
        return "capture:" + challenge_id

    def code_for(self, challenge_id: str) -> str:
        return self.codes[challenge_id]


def request_json(
    port: int,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    cookie: str | None = None,
    origin: str = ORIGIN,
    preflight: bool = False,
):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers: dict[str, str] = {"Origin": origin}
    body = None
    if preflight:
        headers["Access-Control-Request-Method"] = "POST"
        headers["Access-Control-Request-Headers"] = "Content-Type"
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(body))
    if cookie:
        headers["Cookie"] = cookie
    conn.request(method, path, body=body, headers=headers)
    response = conn.getresponse()
    raw = response.read()
    status = response.status
    out_headers = dict(response.getheaders())
    conn.close()
    decoded = json.loads(raw.decode("utf-8")) if raw else {}
    return status, out_headers, decoded


def registration_payload(request_id: str) -> dict[str, Any]:
    return {
        "email": "web-runtime@learner.invalid",
        "personal_data_consent": True,
        "marketing_consent": False,
        "personal_data_document_version": "pd-doc-v1",
        "personal_data_text_version": "pd-text-v1",
        "marketing_document_version": "marketing-doc-v1",
        "marketing_text_version": "marketing-text-v1",
        "client_request_id": request_id,
    }


def practice_envelope() -> dict[str, Any]:
    return {
        "adapter_id": RussianExceptionsPracticeAdapter.adapter_id,
        "payload": {
            "card_id": FIRST_SLICE_CARD_ID,
            "session_started_at_ms": 1788710400000,
            "session_mode": "practice",
            "answer": "сочитание",
            "occurred_at_client": "2026-09-06T12:00:00+00:00",
            "client_request_id": "web-runtime-practice-0001",
        },
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
            store = PostgresPeisPersistenceStore(
                dsn,
                evidence_schema=evidence,
                nba_schema=nba,
            )
            runtime = build_runtime(
                store,
                writes_enabled=True,
                allowed_origin=ORIGIN,
                contact_hmac_key=b"c" * 32,
                verification_hmac_key=b"v" * 32,
                host_signing_key=b"h" * 32,
                delivery_provider=delivery,
                registration_begin_enabled=True,
                identity_required_for_ready=True,
            )
            server = HTTPServer(("127.0.0.1", 0), make_handler(runtime))
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

    thread = threading.Thread(target=server_thread, name="eksamio-web-runtime-ci", daemon=True)
    thread.start()
    require(ready.wait(timeout=10), "runtime server did not become ready")
    if "error" in shared:
        raise shared["error"]
    port = int(shared["port"])
    server = shared["server"]

    try:
        status, headers, _payload = request_json(
            port,
            "OPTIONS",
            "/v1/registration/begin",
            preflight=True,
        )
        require(status == 204, "registration CORS preflight succeeds")
        require(headers.get("Access-Control-Allow-Origin") == ORIGIN, "registration CORS is exact-origin")
        require(headers.get("Access-Control-Allow-Credentials") == "true", "registration CORS allows credentialed cookie flow")

        status, _headers, payload = request_json(
            port,
            "POST",
            "/v0/checked-card",
            payload=practice_envelope(),
        )
        require(status == 401 and payload.get("error") == "AUTHENTICATION_REQUIRED", "PEIS write rejects missing session")

        status, _headers, begin = request_json(
            port,
            "POST",
            "/v1/registration/begin",
            payload=registration_payload("web-runtime-registration-0001"),
        )
        require(status == 202 and begin.get("status") == "CHALLENGE_SENT", "registration begin succeeds on web runtime")
        challenge_id = str(begin["challenge_id"])
        require(challenge_id in delivery.codes, "registration uses injected delivery provider")

        status, headers, verified = request_json(
            port,
            "POST",
            "/v1/registration/verify",
            payload={"challenge_id": challenge_id, "code": delivery.code_for(challenge_id)},
        )
        require(status == 200 and verified.get("status") == "AUTHENTICATED", "registration verify authenticates")
        require("token" not in json.dumps(verified).lower(), "browser JSON contains no session token")
        set_cookie = str(headers.get("Set-Cookie", ""))
        require(
            set_cookie.startswith("eksamio_pro_session=")
            and "HttpOnly" in set_cookie
            and "Secure" in set_cookie
            and "SameSite=Lax" in set_cookie,
            "web runtime returns protected server session cookie",
        )
        cookie = set_cookie.split(";", 1)[0]

        status, _headers, session = request_json(
            port,
            "GET",
            "/v1/session",
            cookie=cookie,
        )
        require(status == 200 and session.get("authenticated") is True, "session endpoint resolves the server cookie")
        require(session.get("identity_owner") == "server", "browser session truth stays server-owned")

        status, headers, result = request_json(
            port,
            "POST",
            "/v0/checked-card",
            payload=practice_envelope(),
            cookie=cookie,
        )
        require(status == 200 and result.get("status") == "ACCEPTED", "authenticated session reaches PEIS write")
        require(
            result.get("directive", {}).get("canonical_state_owner") == "shared_peis",
            "authenticated write preserves shared PEIS ownership",
        )
        require(headers.get("Access-Control-Allow-Origin") == ORIGIN, "PEIS response keeps exact credentialed CORS")

        status, _headers, blocked = request_json(
            port,
            "POST",
            "/v0/checked-card",
            payload=practice_envelope(),
            cookie=cookie,
            origin="https://attacker.invalid",
        )
        require(status == 403 and blocked.get("error") == "ORIGIN_NOT_ALLOWED", "wrong-origin PEIS write is rejected")
    finally:
        server.shutdown()
        thread.join(timeout=10)

    if "error" in shared:
        raise shared["error"]

    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        sessions = connection.execute(
            "SELECT learner_profile_id, user_identity_ref, session_hash FROM identity_sessions"
        ).fetchall()
        events = connection.execute(
            "SELECT learner_profile_id, event_id FROM evidence_events"
        ).fetchall()
        identities = connection.execute(
            "SELECT identity_kind, learner_profile_id FROM identity_links"
        ).fetchall()

    require(len(sessions) == 1, "one verification creates one session row")
    require(len(events) == 1, "one authenticated checked-card creates one canonical event")
    require(
        sessions[0]["learner_profile_id"] == events[0]["learner_profile_id"],
        "registration session learner_profile_id is the exact PEIS event owner",
    )
    require(
        {row["identity_kind"] for row in identities} == {"USER"},
        "web registration creates no anonymous identity link",
    )
    require("@" not in str(sessions[0]["user_identity_ref"]), "session persistence contains no raw email")
    require(
        not str(sessions[0]["session_hash"]).startswith("sid."),
        "raw session token is not persisted",
    )

    print("AUTHENTICATED_WEB_RUNTIME_POSTGRES=PASS")
    print("registration_to_session_to_peis=PASS")
    print("same_runtime_same_postgres=PASS")
    print("anonymous_identity=0")
    print("browser_owned_identity=0")
    print("raw_session_token_persisted=0")
    print("wrong_origin_write=BLOCKED")


if __name__ == "__main__":
    main()
