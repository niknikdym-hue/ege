#!/usr/bin/env python3
"""Real PostgreSQL acceptance for the authenticated Eksamio Pro browser routes."""
from __future__ import annotations

import http.client
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
PAYMENTS = ENGINE / "payments-reference"
sys.path[:0] = [
    str(HERE),
    str(PAYMENTS),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
    str(ENGINE / "peis-trusted-host-reference"),
    str(ENGINE / "identity-reference"),
]

import runtime as core  # noqa: E402
import learner_web_runtime as learner_runtime  # noqa: E402
from entitlement_read import ProEntitlementReader  # noqa: E402
from learner_views import RegisteredLearnerViews  # noqa: E402
from payments import Offer, PaymentStore  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore, _PsycopgQmarkConnection  # noqa: E402
from russian_exceptions_practice_adapter import (  # noqa: E402
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)
from http.server import HTTPServer  # noqa: E402

ORIGIN = "https://eksamio.ru"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class CaptureDelivery:
    def __init__(self) -> None:
        self.codes: dict[str, str] = {}
        self.calls = 0

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        require(channel == "email", "browser registration is email-only")
        require(contact.endswith("@learner.invalid"), "CI delivery remains synthetic")
        self.calls += 1
        self.codes[challenge_id] = code
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
):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    headers = {"Origin": origin, "Content-Type": "application/json"}
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


def registration_payload() -> dict[str, Any]:
    return {
        "email": "learner-web@learner.invalid",
        "personal_data_consent": True,
        "marketing_consent": True,
        "personal_data_document_version": "pd-doc-v1",
        "personal_data_text_version": "pd-text-v1",
        "marketing_document_version": "marketing-doc-v1",
        "marketing_text_version": "marketing-text-v1",
        "client_request_id": "learner-web-registration-0001",
    }


def grant_fixture_entitlement(dsn: str) -> tuple[str, int]:
    import psycopg
    from psycopg.rows import dict_row

    raw = psycopg.connect(dsn, row_factory=dict_row)
    try:
        connection = _PsycopgQmarkConnection(raw)
        identity = connection.execute(
            """
            SELECT user_identity_ref, learner_profile_id
            FROM identity_sessions
            WHERE revoked_at_epoch IS NULL
            ORDER BY created_at_epoch DESC LIMIT 1
            """
        ).fetchone()
        require(identity is not None, "verified browser session is persisted before entitlement fixture")
        store = PaymentStore(connection)
        offer = Offer(
            code="RU_PRO_30_TEST",
            product_code="EKSAMIO_PRO_RUSSIAN",
            duration_days=30,
            amount_kopecks=12300,
            title_ru="Eksamio Pro — Русский — 30 дней (CI fixture)",
        )
        now = int(time.time())
        store.create_order(
            order_id="ord:learner-web-entitlement-0001",
            inv_id=990001,
            user_identity_ref=str(identity["user_identity_ref"]),
            learner_profile_id=str(identity["learner_profile_id"]),
            offer=offer,
            payment_method="SBP",
            now=now,
        )
        store.mark_initiated("ord:learner-web-entitlement-0001", now=now)
        grant = store.grant_paid_exactly_once(
            inv_id=990001,
            provider_payment_ref="ci-provider-ref-no-network",
            payload_sha256="a" * 64,
            now=now,
        )
        require(grant.replay is False and grant.state == "ACTIVE", "accepted payment state grants entitlement exactly once")
        return str(identity["learner_profile_id"]), int(grant.expires_at_epoch)
    finally:
        raw.close()


def refund_fixture_entitlement(dsn: str) -> None:
    import psycopg
    from psycopg.rows import dict_row

    raw = psycopg.connect(dsn, row_factory=dict_row)
    try:
        store = PaymentStore(_PsycopgQmarkConnection(raw))
        changed = store.refund_confirmed(
            "ord:learner-web-entitlement-0001",
            provider_ref="ci-refund-ref-no-network",
            payload_sha256="b" * 64,
            now=int(time.time()),
        )
        require(changed, "provider-confirmed refund fixture revokes entitlement")
    finally:
        raw.close()


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
                writes_enabled=True,
                allowed_origin=ORIGIN,
                contact_hmac_key=b"c" * 32,
                verification_hmac_key=b"v" * 32,
                host_signing_key=b"h" * 32,
                delivery_provider=delivery,
                registration_begin_enabled=True,
                identity_required_for_ready=True,
            )
            adapter = RussianExceptionsPracticeAdapter(ENGINE)
            views = RegisteredLearnerViews(store=store, bridge=runtime.bridge, adapter=adapter)
            entitlements = ProEntitlementReader(store.connection)
            server = HTTPServer(
                ("127.0.0.1", 0),
                learner_runtime.make_handler(runtime, views, entitlements),
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

    thread = threading.Thread(target=server_thread, name="learner-web-runtime-ci", daemon=True)
    thread.start()
    require(ready.wait(timeout=10), "learner web runtime did not become ready")
    if "error" in shared:
        raise shared["error"]
    port = int(shared["port"])
    server = shared["server"]

    try:
        status, _headers, unauth = request_json(
            port, "GET", "/api/russian/profile?grade=10&route=ege"
        )
        require(status == 401 and unauth.get("error") == "AUTHENTICATION_REQUIRED", "learner reads require session")
        status, _headers, unauth_entitlement = request_json(
            port, "GET", "/api/payments/entitlement"
        )
        require(status == 401 and unauth_entitlement.get("error") == "AUTHENTICATION_REQUIRED", "entitlement read requires session")

        status, _headers, begin = request_json(
            port,
            "POST",
            "/v1/registration/begin",
            payload=registration_payload(),
        )
        require(status == 202 and begin.get("status") == "CHALLENGE_SENT", "browser registration begin succeeds")
        challenge = str(begin["challenge_id"])
        require(delivery.calls == 1, "registration emits one synthetic delivery")

        status, headers, verified = request_json(
            port,
            "POST",
            "/v1/registration/verify",
            payload={"challenge_id": challenge, "code": delivery.code_for(challenge)},
        )
        require(status == 200 and verified.get("status") == "AUTHENTICATED", "browser registration verifies")
        set_cookie = str(headers.get("Set-Cookie", ""))
        require(set_cookie.startswith("eksamio_pro_session="), "verify returns session cookie")
        cookie = set_cookie.split(";", 1)[0]

        status, _headers, session = request_json(port, "GET", "/api/identity/session", cookie=cookie)
        require(status == 200 and session.get("authenticated") is True, "Pro identity route resolves session")
        require(session.get("identity_owner") == "server", "session truth remains server-owned")

        status, _headers, inactive = request_json(
            port, "GET", "/api/payments/entitlement", cookie=cookie
        )
        require(status == 200 and inactive == {
            "active": False,
            "product_code": "EKSAMIO_PRO_RUSSIAN",
            "state": "INACTIVE",
        }, "registered learner without payment has no active entitlement")

        entitled_learner, entitled_until = grant_fixture_entitlement(dsn)
        status, _headers, active = request_json(
            port, "GET", "/api/payments/entitlement", cookie=cookie
        )
        require(status == 200 and active.get("active") is True, "accepted server payment state activates Pro read")
        require(active.get("product_code") == "EKSAMIO_PRO_RUSSIAN", "entitlement product is server-owned Russian Pro")
        require(active.get("state") == "ACTIVE", "active entitlement state is returned")
        require(active.get("expires_at_epoch") == entitled_until, "entitlement expiry is server-owned")

        status, _headers, before = request_json(
            port, "GET", "/api/russian/profile?grade=10&route=ege", cookie=cookie
        )
        require(status == 200 and before["today"]["solved"] == 0, "empty registered profile is readable")
        require(before["next_best_action"]["canonical_state_owner"] == "shared_peis", "profile reads shared PEIS")

        status, _headers, card = request_json(port, "GET", "/api/russian/practice/next", cookie=cookie)
        require(status == 200 and card.get("card_id") == FIRST_SLICE_CARD_ID, "accepted practice card is server-provided")

        started_ms = int(time.time() * 1000)
        status, _headers, practice = request_json(
            port,
            "POST",
            "/api/russian/practice/submit",
            cookie=cookie,
            payload={
                "card_id": FIRST_SLICE_CARD_ID,
                "answer": "сочитание",
                "attempt_started_at_ms": started_ms,
                "client_request_id": "learner-web-practice-0001",
            },
        )
        require(status == 200 and practice.get("status") == "ACCEPTED", "authenticated Pro practice reaches PEIS")
        require(practice.get("correct") is False, "server evaluates the intentionally wrong answer")
        require(practice.get("directive", {}).get("canonical_state_owner") == "shared_peis", "practice NBA remains shared-PEIS-owned")

        status, _headers, after = request_json(
            port, "GET", "/api/russian/profile?grade=10&route=ege", cookie=cookie
        )
        require(status == 200 and after["today"]["solved"] == 1, "profile reflects accepted evidence")
        require(after["today"]["errors"] == 1, "profile reflects exact error")
        require(after.get("reporting_timezone") == "Europe/Moscow", "today uses Moscow reporting day")

        status, _headers, history = request_json(port, "GET", "/api/russian/history", cookie=cookie)
        require(status == 200 and isinstance(history, list) and len(history) == 1, "history reflects canonical event")

        status, _headers, plan = request_json(
            port, "GET", "/api/russian/plan?grade=10&route=ege", cookie=cookie
        )
        require(status == 200 and isinstance(plan, list) and len(plan) == 3, "plan renders server NBA")

        status, _headers, program = request_json(port, "GET", "/api/russian/program", cookie=cookie)
        require(status == 503 and program.get("error") == "RUSSIAN_FULL_SUBJECT_NOT_ADMITTED", "full Russian program remains fail-closed")

        status, _headers, tutor = request_json(
            port,
            "POST",
            "/api/tutor/turn",
            cookie=cookie,
            payload={"card_id": FIRST_SLICE_CARD_ID, "message": "Помоги"},
        )
        require(status == 503 and tutor.get("error") == "TUTOR_PROVIDER_NOT_ADMITTED", "production Tutor remains fail-closed")

        status, _headers, revoked = request_json(
            port,
            "POST",
            "/api/consent/marketing/revoke",
            cookie=cookie,
            payload={
                "document_version": "marketing-doc-v1",
                "text_version": "marketing-text-v1",
                "client_request_id": "learner-web-marketing-revoke-0001",
            },
        )
        require(status == 200 and revoked.get("status") == "RECORDED", "authenticated marketing revoke is persisted")

        refund_fixture_entitlement(dsn)
        status, _headers, after_refund = request_json(
            port, "GET", "/api/payments/entitlement", cookie=cookie
        )
        require(status == 200 and after_refund.get("active") is False, "provider-confirmed refund removes active entitlement")

        status, _headers, wrong_origin = request_json(
            port,
            "GET",
            "/api/russian/history",
            cookie=cookie,
            origin="https://attacker.invalid",
        )
        require(status == 403 and wrong_origin.get("error") == "ORIGIN_NOT_ALLOWED", "wrong-origin learner read is blocked")

        status, logout_headers, logged_out = request_json(
            port,
            "POST",
            "/api/identity/logout",
            cookie=cookie,
            payload={},
        )
        require(status == 200 and logged_out.get("status") in {"LOGGED_OUT", "ALREADY_LOGGED_OUT"}, "logout revokes server session")
        cleared = str(logout_headers.get("Set-Cookie", ""))
        require("Max-Age=0" in cleared and "HttpOnly" in cleared and "Secure" in cleared, "logout clears protected cookie")

        status, _headers, after_logout = request_json(
            port, "GET", "/api/russian/history", cookie=cookie
        )
        require(status == 401 and after_logout.get("error") == "AUTHENTICATION_REQUIRED", "revoked session cannot read learner state")
    finally:
        server.shutdown()
        thread.join(timeout=10)

    if "error" in shared:
        raise shared["error"]

    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        session = connection.execute(
            "SELECT learner_profile_id, user_identity_ref, revoked_at_epoch FROM identity_sessions"
        ).fetchone()
        event = connection.execute(
            "SELECT learner_profile_id, event_id FROM evidence_events"
        ).fetchone()
        marketing = connection.execute(
            """
            SELECT action FROM registration_consent_events
            WHERE consent_type='MARKETING'
            ORDER BY event_seq DESC LIMIT 1
            """
        ).fetchone()
        entitlement = connection.execute(
            "SELECT learner_profile_id, state FROM pro_entitlements WHERE order_id='ord:learner-web-entitlement-0001'"
        ).fetchone()
        identities = connection.execute(
            "SELECT identity_kind FROM identity_links"
        ).fetchall()

    require(session is not None and event is not None, "session and evidence are persisted")
    require(session["learner_profile_id"] == event["learner_profile_id"], "session and PEIS event have the same learner_profile_id")
    require(session["learner_profile_id"] == entitled_learner, "payment entitlement uses the same learner_profile_id")
    require(session["revoked_at_epoch"] is not None, "logout is durable")
    require(marketing is not None and marketing["action"] == "REVOKE", "marketing revoke is latest durable state")
    require(entitlement is not None and entitlement["state"] == "REVOKED", "refund durably revokes entitlement")
    require({row["identity_kind"] for row in identities} == {"USER"}, "registered browser path creates no anonymous identity")
    require("@" not in str(session["user_identity_ref"]), "persisted session contains no raw email")

    print("LEARNER_WEB_RUNTIME_POSTGRES=PASS")
    print("registration_session_profile_history_plan=PASS")
    print("server_owned_entitlement_read=PASS")
    print("entitlement_same_learner_profile=PASS")
    print("refund_revokes_entitlement=PASS")
    print("practice_to_same_learner_peis=PASS")
    print("logout_durable=PASS")
    print("marketing_revoke_append_only=PASS")
    print("full_russian_program=BLOCKED_UNTIL_SUBJECT_ACCEPTANCE")
    print("production_tutor=BLOCKED_UNTIL_PROVIDER_ADMISSION")
    print("production_payment_execution=0")
    print("anonymous_identity=0")
    print("real_provider_calls=0")


if __name__ == "__main__":
    main()
