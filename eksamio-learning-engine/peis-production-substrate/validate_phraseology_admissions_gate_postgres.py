#!/usr/bin/env python3
"""Exact-head PostgreSQL acceptance for registered phraseology fragment Admissions Gate."""
from __future__ import annotations

import http.client
import json
import os
import sys
import threading
from datetime import datetime, timezone
from http.server import HTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(ENGINE / "payments-reference"),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
    str(ENGINE / "peis-trusted-host-reference"),
    str(ENGINE / "identity-reference"),
]

import learner_admissions_tutor_web_runtime as admissions_web  # noqa: E402
import runtime as core  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from peis_service_bridge import HostIdentity, ServerEventPosition, ServiceRequestError  # noqa: E402
from russian_phraseology_fragment_adapter import (  # noqa: E402
    ACTION_ID,
    ADAPTER_ID,
    SEMANTIC_ID,
    RussianPhraseologyFragmentAdmissionAdapter,
)

ORIGIN = "https://eksamio.ru"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class CaptureDelivery:
    def __init__(self) -> None:
        self.codes: dict[str, str] = {}
        self.calls = 0

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        require(channel == "email", "Admissions Gate CI registration is email-only")
        require(contact.endswith("@learner.invalid"), "CI delivery stays synthetic/no-network")
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
        "email": "phraseology-admissions@learner.invalid",
        "personal_data_consent": True,
        "marketing_consent": False,
        "personal_data_document_version": "pd-doc-v1",
        "personal_data_text_version": "pd-text-v1",
        "marketing_document_version": "marketing-doc-v1",
        "marketing_text_version": "marketing-text-v1",
        "client_request_id": "phraseology-admissions-registration-0001",
    }


def evidence_payload(
    *,
    request_id: str,
    response_text: str = "альфа и омега",
    action_id: str = ACTION_ID,
    item_id: str = "f001-alfa-i-omega",
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "action_id": action_id,
        "response_text": response_text,
        "session_started_at_ms": 1788764400000,
        "occurred_at_client": "2026-09-07T07:00:00+00:00",
        "client_request_id": request_id,
    }


def main() -> None:
    dsn = os.environ.get("EKSAMIO_TEST_POSTGRES_DSN", "")
    require(bool(dsn), "EKSAMIO_TEST_POSTGRES_DSN is required")
    evidence_schema = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8")
    )
    nba_schema = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(encoding="utf-8")
    )

    adapter = RussianPhraseologyFragmentAdmissionAdapter(ENGINE)
    require(len(adapter.answer_by_id) == 199, "authority exposes exact bounded 199-item phraseology subset")
    require(adapter.answer_by_id["f001-alfa-i-omega"] == "альфа и омега", "first deterministic phraseology key is pinned")
    require("f008" not in adapter.answer_by_id, "non-admitted full-bank row cannot enter bounded phraseology key")
    for boundary in (
        "all_285_items_admitted",
        "remaining_86_phraseology_rows_admitted",
        "variant_answers_admitted",
        "meaning_choice_admitted",
        "missing_component_admitted",
        "by_meaning_recall_admitted",
        "generic_trainer_completion_mastery",
        "browser_local_progress_mastery",
        "asset_wide_mastery",
    ):
        require(adapter.authority["boundaries"][boundary] is False, f"{boundary} remains blocked")
    require(adapter.authority["boundaries"]["false_exact_mastery"] == 0, "false_exact_mastery remains zero")

    direct_payload = evidence_payload(request_id="phraseology-direct-anon-reject-0001")
    try:
        adapter.build_observation(
            direct_payload,
            host_identity=HostIdentity(
                learner_profile_id="learner-anonymous-forbidden",
                identity_refs={"anonymous_identity_ref": "anon-forbidden"},
            ),
            server_position=ServerEventPosition(
                received_at_server=datetime.now(timezone.utc).isoformat(),
                server_sequence=1,
                server_watermark="wm.phraseology-direct-anon-reject",
            ),
        )
    except ServiceRequestError:
        pass
    else:
        raise AssertionError("anonymous identity must be rejected by phraseology Admissions Gate adapter")

    delivery = CaptureDelivery()
    ready = threading.Event()
    shared: dict[str, Any] = {}

    def server_thread() -> None:
        store = None
        server = None
        try:
            store = PostgresPeisPersistenceStore(
                dsn,
                evidence_schema=evidence_schema,
                nba_schema=nba_schema,
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
            runtime.bridge.registry.register(RussianPhraseologyFragmentAdmissionAdapter(ENGINE))
            server = HTTPServer(
                ("127.0.0.1", 0),
                admissions_web.make_handler(runtime, None, None, None),
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

    thread = threading.Thread(target=server_thread, name="phraseology-admissions-gate-ci", daemon=True)
    thread.start()
    require(ready.wait(timeout=10), "phraseology Admissions Gate runtime did not become ready")
    if "error" in shared:
        raise shared["error"]
    port = int(shared["port"])
    server = shared["server"]

    inspection = None
    try:
        status, _headers, unauth = request_json(
            port,
            "POST",
            admissions_web.PHRASEOLOGY_ADMISSION_PATH,
            payload=evidence_payload(request_id="phraseology-unauth-reject-0001"),
        )
        require(status == 401 and unauth.get("error") == "AUTHENTICATION_REQUIRED", "phraseology admission requires authenticated session")

        status, _headers, wrong_origin = request_json(
            port,
            "POST",
            admissions_web.PHRASEOLOGY_ADMISSION_PATH,
            origin="https://attacker.invalid",
            payload=evidence_payload(request_id="phraseology-wrong-origin-reject-0001"),
        )
        require(status == 403 and wrong_origin.get("error") == "ORIGIN_NOT_ALLOWED", "foreign Origin is blocked before phraseology mutation")

        status, _headers, begin = request_json(
            port,
            "POST",
            "/v1/registration/begin",
            payload=registration_payload(),
        )
        require(status == 202 and begin.get("status") == "CHALLENGE_SENT", "synthetic passwordless begin succeeds")
        challenge = str(begin["challenge_id"])
        require(delivery.calls == 1, "one synthetic registration delivery is emitted")

        status, headers, verified = request_json(
            port,
            "POST",
            "/v1/registration/verify",
            payload={"challenge_id": challenge, "code": delivery.code_for(challenge)},
        )
        require(status == 200 and verified.get("status") == "AUTHENTICATED", "passwordless verify creates authenticated session")
        set_cookie = str(headers.get("Set-Cookie", ""))
        require(set_cookie.startswith("eksamio_pro_session="), "verified session is carried only by secure cookie")
        cookie = set_cookie.split(";", 1)[0]

        invalid_cases = [
            ("wrong-action", {**evidence_payload(request_id="phraseology-wrong-action-0001"), "action_id": "meaning_choice"}),
            ("unknown-item", {**evidence_payload(request_id="phraseology-unknown-item-0001"), "item_id": "f008-not-admitted"}),
            ("client-semantic", {**evidence_payload(request_id="phraseology-client-semantic-0001"), "semantic_id": SEMANTIC_ID}),
            ("client-mastery", {**evidence_payload(request_id="phraseology-client-mastery-0001"), "mastery": 1.0}),
            ("variant-answer", {**evidence_payload(request_id="phraseology-variant-0001"), "variant_answer": "вариант"}),
            ("meaning-choice", {**evidence_payload(request_id="phraseology-meaning-0001"), "meaning_choice": "значение"}),
            ("missing-component", {**evidence_payload(request_id="phraseology-component-0001"), "missing_component": "омега"}),
            ("generic-completion", {**evidence_payload(request_id="phraseology-completion-0001"), "trainer_completed": True}),
        ]
        for label, payload in invalid_cases:
            status, _headers, body = request_json(
                port,
                "POST",
                admissions_web.PHRASEOLOGY_ADMISSION_PATH,
                cookie=cookie,
                payload=payload,
            )
            require(status == 400 and body.get("error") == "INVALID_REQUEST", f"{label} must fail closed")

        accepted_payload = evidence_payload(request_id="phraseology-accepted-0001")
        status, _headers, accepted = request_json(
            port,
            "POST",
            admissions_web.PHRASEOLOGY_ADMISSION_PATH,
            cookie=cookie,
            payload=accepted_payload,
        )
        require(status == 200 and accepted.get("status") == "ACCEPTED", "registered exact phraseology item/action event is accepted")
        require(accepted.get("canonical_state_owner") == "shared_peis", "accepted phraseology evidence remains shared-PEIS-owned")
        event_id = str(accepted["event_receipt"]["event_id"])
        require(event_id.startswith("ruphr.ev."), "server owns stable phraseology event identity")

        inspection = PostgresPeisPersistenceStore(
            dsn,
            evidence_schema=evidence_schema,
            nba_schema=nba_schema,
        )
        event = inspection.raw_event(event_id)
        require(event is not None, "accepted phraseology event is durable in PostgreSQL")
        require(event["learner_profile_id"].startswith("learner:"), "event belongs to one server-owned learner profile")
        require(set(event["identity_refs"]) == {"user_identity_ref"}, "canonical event has registered user identity only")
        require(event["semantic_targets"] == [{
            "semantic_id": SEMANTIC_ID,
            "target_role": "PRIMARY",
            "mapping_resolution": "EXACT",
            "mapping_confidence": 1.0,
            "mapping_review_status": "accepted",
        }], "semantic target is server-selected exact phraseology fragment component")
        require(event["source"]["object_id"] == "f001-alfa-i-omega", "exact live phraseology item identity is preserved")
        require(event["result"]["correctness"] is True and event["result"]["score"] == 1, "server deterministically scores exact phraseology response")
        require(event["result"]["response_value"] == "альфа и омега", "observed typed response is preserved")
        require(event["evaluator"]["evaluator_type"] == "DETERMINISTIC_VALIDATOR", "browser never owns evaluator truth")
        require(event["timestamps"]["received_at_server"] == event["created_at"], "server owns received_at_server/created_at")
        extension = event["subject_extension"]["subject_payload"]
        require(extension["variant_answers_admitted"] is False, "variant answers cannot leak into accepted component")
        require(extension["meaning_choice_admitted"] is False, "meaning-choice mode cannot leak into accepted component")
        require(extension["missing_component_admitted"] is False, "missing-component mode cannot leak into accepted component")
        require(extension["by_meaning_recall_admitted"] is False, "by-meaning recall cannot leak into accepted component")
        require("mastery" not in event, "raw phraseology event contains observation, not client mastery")

        status, _headers, replay = request_json(
            port,
            "POST",
            admissions_web.PHRASEOLOGY_ADMISSION_PATH,
            cookie=cookie,
            payload=accepted_payload,
        )
        require(status == 200 and replay.get("status") == "REPLAY", "exact phraseology request replay is idempotent")
        require(replay["event_receipt"]["event_id"] == event_id, "phraseology replay returns same canonical event identity")

        mutated = dict(accepted_payload)
        mutated["response_text"] = "альфа и бета"
        status, _headers, conflict = request_json(
            port,
            "POST",
            admissions_web.PHRASEOLOGY_ADMISSION_PATH,
            cookie=cookie,
            payload=mutated,
        )
        require(status == 409 and conflict.get("error") == "INTEGRITY_CONFLICT", "mutated phraseology replay fails closed")
        require(inspection.raw_event(event_id) == event, "mutated phraseology replay cannot alter durable canonical event")

        wrong_payload = evidence_payload(request_id="phraseology-wrong-0002", response_text="альфа и бета")
        status, _headers, wrong = request_json(
            port,
            "POST",
            admissions_web.PHRASEOLOGY_ADMISSION_PATH,
            cookie=cookie,
            payload=wrong_payload,
        )
        require(status == 200 and wrong.get("status") == "ACCEPTED", "wrong text remains valid observed evidence")
        wrong_event = inspection.raw_event(str(wrong["event_receipt"]["event_id"]))
        require(wrong_event is not None and wrong_event["result"]["correctness"] is False, "server scores wrong phraseology response as incorrect")
        require(wrong_event["error_observations"][0]["semantic_id"] == SEMANTIC_ID, "incorrect exact phraseology action produces exact semantic error evidence")

        all_events = inspection.list_events(event["learner_profile_id"], "russian", effective=False)
        require(len(all_events) == 2, "only two admitted phraseology requests persisted; rejected probes mutated nothing")
        require(all(row["product"]["product_id"] == "russian-phraseology-trainer" for row in all_events), "unbound phraseology modes never entered canonical evidence")

        print("ADMISSIONS_GATE_PHRASEOLOGY_POSTGRES=PASS")
        print("registered_only=1 exact_item_ids=199 exact_action=fragment_identification")
        print("accepted_events=2 rejected_truth_or_unbound_mutations=8 replay_idempotent=1 mutated_replay_conflict=1")
        print("all_285_items_admitted=0 variants_admitted=0 unbound_modes_admitted=0 false_exact_mastery=0 provider_calls=0")
    finally:
        if inspection is not None:
            inspection.close()
        server.shutdown()
        thread.join(timeout=10)
        require(not thread.is_alive(), "phraseology Admissions Gate server thread must stop")
        if "error" in shared:
            raise shared["error"]


if __name__ == "__main__":
    main()
