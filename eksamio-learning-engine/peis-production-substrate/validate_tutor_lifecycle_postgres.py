#!/usr/bin/env python3
"""Real PostgreSQL acceptance for durable Tutor lineage in the learner web runtime."""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from http.server import HTTPServer
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
import learner_tutor_web_runtime as tutor_web  # noqa: E402
from entitlement_read import ProEntitlementReader  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from russian_exceptions_practice_adapter import (  # noqa: E402
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)
from tutor_lifecycle import (  # noqa: E402
    DeterministicNoNetworkTutorProvider,
    PostgresTutorLifecycle,
    build_tutor_aware_bridge,
)
from validate_learner_web_runtime_postgres import (  # noqa: E402
    CaptureDelivery,
    grant_fixture_entitlement,
    registration_payload,
    request_json,
)

ORIGIN = "https://eksamio.ru"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def database_rows(dsn: str) -> list[dict[str, Any]]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        rows = connection.execute(
            """
            SELECT context_id, learner_profile_id, card_id, lineage,
                   error_event_id, help_event_id, provider_id, status,
                   verified_event_id
            FROM tutor_contexts
            ORDER BY lineage
            """
        ).fetchall()
        return [dict(row) for row in rows]


def event_json(dsn: str, event_id: str) -> dict[str, Any]:
    import psycopg
    from psycopg.rows import dict_row

    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        row = connection.execute(
            "SELECT event_json FROM evidence_events WHERE event_id = %s",
            (event_id,),
        ).fetchone()
    require(row is not None, f"missing evidence event {event_id}")
    value = row["event_json"]
    if isinstance(value, str):
        value = json.loads(value)
    require(isinstance(value, dict), f"event {event_id} is not an object")
    return value


def main() -> None:
    dsn = os.environ.get("EKSAMIO_TEST_POSTGRES_DSN", "")
    require(bool(dsn), "EKSAMIO_TEST_POSTGRES_DSN is required")
    evidence = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(
            encoding="utf-8"
        )
    )
    nba = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(
            encoding="utf-8"
        )
    )

    delivery = CaptureDelivery()
    provider = DeterministicNoNetworkTutorProvider()
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
            tutor = PostgresTutorLifecycle(
                store=store,
                position_bridge=runtime.bridge,
                adapter=adapter,
                provider=provider,
            )
            tutor_bridge = build_tutor_aware_bridge(
                store=store,
                base_adapter=adapter,
                lifecycle=tutor,
            )
            views = tutor_web.TutorAwareRegisteredLearnerViews(
                store=store,
                bridge=tutor_bridge,
                adapter=adapter,
                tutor_lifecycle=tutor,
            )
            entitlements = ProEntitlementReader(store.connection)
            server = HTTPServer(
                ("127.0.0.1", 0),
                tutor_web.make_handler(runtime, views, entitlements, tutor),
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

    thread = threading.Thread(
        target=server_thread,
        name="tutor-postgres-runtime-ci",
        daemon=True,
    )
    thread.start()
    require(ready.wait(timeout=10), "Tutor runtime did not become ready")
    if "error" in shared:
        raise shared["error"]
    port = int(shared["port"])
    server = shared["server"]

    try:
        status, _headers, unauth = request_json(
            port,
            "POST",
            "/api/tutor/turn",
            payload={"card_id": FIRST_SLICE_CARD_ID, "message": "Помоги"},
        )
        require(
            status == 401 and unauth.get("error") == "AUTHENTICATION_REQUIRED",
            "Tutor route requires the registered learner session",
        )

        status, _headers, begin = request_json(
            port,
            "POST",
            "/v1/registration/begin",
            payload=registration_payload(),
        )
        require(
            status == 202 and begin.get("status") == "CHALLENGE_SENT",
            "registration begin succeeds before Tutor",
        )
        challenge = str(begin["challenge_id"])
        status, headers, verified = request_json(
            port,
            "POST",
            "/v1/registration/verify",
            payload={
                "challenge_id": challenge,
                "code": delivery.code_for(challenge),
            },
        )
        require(
            status == 200 and verified.get("status") == "AUTHENTICATED",
            "registration verifies before Tutor",
        )
        cookie = str(headers["Set-Cookie"]).split(";", 1)[0]

        status, _headers, unpaid = request_json(
            port,
            "POST",
            "/api/tutor/turn",
            cookie=cookie,
            payload={"card_id": FIRST_SLICE_CARD_ID, "message": "Помоги"},
        )
        require(
            status == 403 and unpaid.get("error") == "PRO_ENTITLEMENT_REQUIRED",
            "Tutor cannot be bypassed without server-owned Pro entitlement",
        )

        entitled_learner, _expires = grant_fixture_entitlement(dsn)
        require(bool(entitled_learner), "payment fixture resolves one learner")

        started_ms = int(time.time() * 1000)
        status, _headers, wrong = request_json(
            port,
            "POST",
            "/api/russian/practice/submit",
            cookie=cookie,
            payload={
                "card_id": FIRST_SLICE_CARD_ID,
                "answer": "сочитание",
                "attempt_started_at_ms": started_ms,
                "client_request_id": "tutor-pg-error-0001",
            },
        )
        require(
            status == 200 and wrong.get("correct") is False,
            "accepted exact error exists before Tutor",
        )

        status, _headers, help_a = request_json(
            port,
            "POST",
            "/api/tutor/turn",
            cookie=cookie,
            payload={"card_id": FIRST_SLICE_CARD_ID, "message": "Объясни ошибку"},
        )
        require(
            status == 200
            and help_a.get("status") == "TUTOR_ADVISORY_ACCEPTANCE"
            and help_a.get("lineage") == 1,
            "first Tutor help is durable lineage 1",
        )
        context_a = str(help_a["context_id"])
        help_event_a = str(help_a["help_event_id"])
        require(provider.calls == 1, "first Tutor help uses one fake provider call")

        status, _headers, retry_a = request_json(
            port,
            "POST",
            "/api/tutor/turn",
            cookie=cookie,
            payload={"card_id": FIRST_SLICE_CARD_ID, "message": "Повтори"},
        )
        require(
            status == 200
            and retry_a.get("context_id") == context_a
            and retry_a.get("help_event_id") == help_event_a,
            "retry while verification is pending reuses immutable Tutor lineage",
        )
        require(
            provider.calls == 1,
            "pending Tutor retry does not create a second provider call",
        )

        status, _headers, verify_card = request_json(
            port,
            "GET",
            "/api/russian/practice/next",
            cookie=cookie,
        )
        require(
            status == 200 and verify_card.get("verification_required") is True,
            "server exposes pending independent verification",
        )

        status, _headers, verify_a = request_json(
            port,
            "POST",
            "/api/russian/practice/submit",
            cookie=cookie,
            payload={
                "card_id": FIRST_SLICE_CARD_ID,
                "answer": "сочетание",
                "attempt_started_at_ms": started_ms + 1000,
                "client_request_id": "tutor-pg-verify-a-0001",
            },
        )
        require(
            status == 200
            and verify_a.get("correct") is True
            and verify_a.get("verification_completed") is True
            and verify_a.get("verified_tutor_context_id") == context_a,
            "first independent answer verifies Tutor lineage A",
        )
        verify_event_a = str(verify_a["event"]["event_id"])

        status, _headers, help_b = request_json(
            port,
            "POST",
            "/api/tutor/turn",
            cookie=cookie,
            payload={"card_id": FIRST_SLICE_CARD_ID, "message": "Ещё раз коротко"},
        )
        require(
            status == 200
            and help_b.get("lineage") == 2
            and help_b.get("context_id") != context_a,
            "new Tutor help after verification creates fresh lineage B",
        )
        context_b = str(help_b["context_id"])
        help_event_b = str(help_b["help_event_id"])
        require(provider.calls == 2, "fresh lineage uses exactly one new provider call")

        status, _headers, verify_b = request_json(
            port,
            "POST",
            "/api/russian/practice/submit",
            cookie=cookie,
            payload={
                "card_id": FIRST_SLICE_CARD_ID,
                "answer": "сочетание",
                "attempt_started_at_ms": started_ms + 2000,
                "client_request_id": "tutor-pg-verify-b-0001",
            },
        )
        require(
            status == 200
            and verify_b.get("verification_completed") is True
            and verify_b.get("verified_tutor_context_id") == context_b,
            "second independent answer verifies Tutor lineage B",
        )
        verify_event_b = str(verify_b["event"]["event_id"])

        rows = database_rows(dsn)
        require(len(rows) == 2, "PostgreSQL stores exactly two Tutor lineages")
        require(
            [row["lineage"] for row in rows] == [1, 2],
            "Tutor lineage numbers are monotonic",
        )
        require(
            all(row["status"] == "VERIFIED" for row in rows),
            "both Tutor contexts end VERIFIED",
        )
        require(
            rows[0]["error_event_id"] == rows[1]["error_event_id"],
            "fresh Tutor lineage can re-ground on the same accepted exact error",
        )
        require(
            rows[0]["help_event_id"] != rows[1]["help_event_id"],
            "fresh lineages have distinct immutable help events",
        )
        require(
            rows[0]["verified_event_id"] == verify_event_a
            and rows[1]["verified_event_id"] == verify_event_b,
            "each lineage owns its own verification event",
        )

        help_event = event_json(dsn, help_event_a)
        require(
            help_event.get("product", {}).get("source_type") == "tutor",
            "Tutor help is persisted as PEIS evidence",
        )
        require(
            help_event.get("subject_extension", {})
            .get("subject_payload", {})
            .get("context_id")
            == context_a,
            "Tutor help event preserves immutable context lineage",
        )
        verification_event_a = event_json(dsn, verify_event_a)
        verification_event_b = event_json(dsn, verify_event_b)
        require(
            verification_event_a.get("transfer_context", {}).get("origin_event_refs")
            == [help_event_a],
            "verification A points only to help A",
        )
        require(
            verification_event_b.get("transfer_context", {}).get("origin_event_refs")
            == [help_event_b],
            "verification B points only to help B",
        )

        status, _headers, after = request_json(
            port,
            "GET",
            "/api/russian/practice/next",
            cookie=cookie,
        )
        require(
            status == 200 and after.get("verification_required") is False,
            "no verification remains pending after lineage B is verified",
        )

        status, _headers, history = request_json(
            port,
            "GET",
            "/api/russian/history",
            cookie=cookie,
        )
        tutor_rows = [row for row in history if row.get("kind") == "Tutor"]
        require(len(tutor_rows) == 2, "learner history renders both Tutor help events")

        print("EKSAMIO_TUTOR_POSTGRES_LIFECYCLE=PASS")
        print("registered_session_required=PASS")
        print("server_owned_pro_entitlement_required=PASS")
        print("error_helpA_verifyA_helpB_verifyB=PASS")
        print("fresh_tutor_lineage=PASS")
        print("pending_retry_provider_calls=1=PASS")
        print("immutable_help_event_lineage=PASS")
        print("same_session_verification_refs=PASS")
        print("deterministic_fake_provider_calls=2")
        print("live_network_provider_calls=0")
        print("paid_ai_calls=0")
    finally:
        server.shutdown()
        thread.join(timeout=10)
        require(not thread.is_alive(), "Tutor runtime server did not stop cleanly")
        if "error" in shared:
            raise shared["error"]


if __name__ == "__main__":
    main()
