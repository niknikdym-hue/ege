#!/usr/bin/env python3
"""Exact-head PostgreSQL acceptance for registered paronym context-choice Admissions Gate."""
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
from russian_paronym_context_adapter import (  # noqa: E402
    ACTION_ID,
    SEMANTIC_ID,
    RussianParonymContextChoiceAdmissionAdapter,
)

ORIGIN = "https://eksamio.ru"
ITEM_ID = "p001-abonement-abonent-abonement"
CORRECT_WORD = "абонемент"
OTHER_PINNED_CHOICE = "абонент"


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
        "email": "paronym-admissions@learner.invalid",
        "personal_data_consent": True,
        "marketing_consent": False,
        "personal_data_document_version": "pd-doc-v1",
        "personal_data_text_version": "pd-text-v1",
        "marketing_document_version": "marketing-doc-v1",
        "marketing_text_version": "marketing-text-v1",
        "client_request_id": "paronym-admissions-registration-0001",
    }


def evidence_payload(
    *,
    request_id: str,
    item_id: str = ITEM_ID,
    selected_word: str = CORRECT_WORD,
    action_id: str = ACTION_ID,
) -> dict[str, Any]:
    return {
        "item_id": item_id,
        "action_id": action_id,
        "selected_word": selected_word,
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

    adapter = RussianParonymContextChoiceAdmissionAdapter(ENGINE)
    require(len(adapter.entry_by_id) == 334, "authority exposes exact 334 paronym entries")
    require(len(adapter.choices_by_group) == 144, "authority exposes exact 144 paronym groups")
    require(adapter.entry_by_id[ITEM_ID] == ("p001-abonement-abonent", CORRECT_WORD), "first deterministic server key is pinned")
    require(set(adapter.choices_by_group["p001-abonement-abonent"]) == {CORRECT_WORD, OTHER_PINNED_CHOICE}, "first choice group is pinned")
    for boundary in (
        "meaning_match_admitted",
        "independent_paronym_recall_admitted",
        "exam_error_correction_admitted",
        "generic_trainer_completion_mastery",
        "browser_local_progress_mastery",
        "asset_wide_mastery",
    ):
        require(adapter.authority["boundaries"][boundary] is False, f"{boundary} remains blocked")
    require(adapter.authority["boundaries"]["false_exact_mastery"] == 0, "false_exact_mastery remains zero")

    try:
        adapter.build_observation(
            evidence_payload(request_id="paronym-direct-anon-reject-0001"),
            host_identity=HostIdentity(
                learner_profile_id="learner-anonymous-forbidden",
                identity_refs={"anonymous_identity_ref": "anon-forbidden"},
            ),
            server_position=ServerEventPosition(
                received_at_server=datetime.now(timezone.utc).isoformat(),
                server_sequence=1,
                server_watermark="wm.paronym-direct-anon-reject",
            ),
        )
    except ServiceRequestError:
        pass
    else:
        raise AssertionError("anonymous identity must be rejected by paronym Admissions Gate adapter")

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
            runtime.bridge.registry.register(RussianParonymContextChoiceAdmissionAdapter(ENGINE))
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

    thread = threading.Thread(target=server_thread, name="paronym-admissions-gate-ci", daemon=True)
    thread.start()
    require(ready.wait(timeout=10), "paronym Admissions Gate runtime did not become ready")
    if "error" in shared:
        raise shared["error"]
    port = int(shared["port"])
    server = shared["server"]

    inspection = None
    try:
        status, _headers, unauth = request_json(
            port,
            "POST",
            admissions_web.PARONYM_ADMISSION_PATH,
            payload=evidence_payload(request_id="paronym-unauth-reject-0001"),
        )
        require(status == 401 and unauth.get("error") == "AUTHENTICATION_REQUIRED", "paronym admission requires authenticated session")

        status, _headers, wrong_origin = request_json(
            port,
            "POST",
            admissions_web.PARONYM_ADMISSION_PATH,
            origin="https://attacker.invalid",
            payload=evidence_payload(request_id="paronym-wrong-origin-reject-0001"),
        )
        require(status == 403 and wrong_origin.get("error") == "ORIGIN_NOT_ALLOWED", "foreign Origin is blocked before paronym mutation")

        status, _headers, begin = request_json(port, "POST", "/v1/registration/begin", payload=registration_payload())
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
            ("wrong-action", {**evidence_payload(request_id="paronym-wrong-action-0001"), "action_id": "meaning_match"}),
            ("unknown-item", {**evidence_payload(request_id="paronym-unknown-item-0001"), "item_id": "not-a-live-id"}),
            ("foreign-choice", {**evidence_payload(request_id="paronym-foreign-choice-0001"), "selected_word": "случайный"}),
            ("client-semantic", {**evidence_payload(request_id="paronym-client-semantic-0001"), "semantic_id": SEMANTIC_ID}),
            ("client-mastery", {**evidence_payload(request_id="paronym-client-mastery-0001"), "mastery": 1.0}),
            ("generic-completion", {**evidence_payload(request_id="paronym-completion-0001"), "trainer_completed": True}),
        ]
        for label, payload in invalid_cases:
            status, _headers, body = request_json(
                port,
                "POST",
                admissions_web.PARONYM_ADMISSION_PATH,
                cookie=cookie,
                payload=payload,
            )
            require(status == 400 and body.get("error") == "INVALID_REQUEST", f"{label} must fail closed")

        accepted_payload = evidence_payload(request_id="paronym-accepted-0001")
        status, _headers, accepted = request_json(
            port,
            "POST",
            admissions_web.PARONYM_ADMISSION_PATH,
            cookie=cookie,
            payload=accepted_payload,
        )
        require(status == 200 and accepted.get("status") == "ACCEPTED", "registered exact paronym item/action event is accepted")
        require(accepted.get("canonical_state_owner") == "shared_peis", "accepted paronym evidence remains shared-PEIS-owned")
        event_id = str(accepted["event_receipt"]["event_id"])
        require(event_id.startswith("rupar.ev."), "server owns stable paronym event identity")

        inspection = PostgresPeisPersistenceStore(dsn, evidence_schema=evidence_schema, nba_schema=nba_schema)
        event = inspection.raw_event(event_id)
        require(event is not None, "accepted paronym event is durable in PostgreSQL")
        require(event["learner_profile_id"].startswith("learner:"), "event belongs to one server-owned learner profile")
        require(set(event["identity_refs"]) == {"user_identity_ref"}, "canonical event has registered user identity only")
        require(event["semantic_targets"] == [{
            "semantic_id": SEMANTIC_ID,
            "target_role": "PRIMARY",
            "mapping_resolution": "EXACT",
            "mapping_confidence": 1.0,
            "mapping_review_status": "accepted",
        }], "semantic target is server-selected exact paronym action component")
        require(event["source"]["object_id"] == ITEM_ID, "exact live paronym item identity is preserved")
        require(event["result"]["correctness"] is True and event["result"]["score"] == 1, "server deterministically scores correct pinned choice")
        require(event["result"]["response_value"] == CORRECT_WORD, "observed selected word is preserved")
        require(event["response_mode"] == "SELECTED_OPTION", "paronym observation uses canonical selected-option response mode")
        require(event["evaluator"]["evaluator_type"] == "DETERMINISTIC_VALIDATOR", "browser never owns evaluator truth")
        require(event["timestamps"]["received_at_server"] == event["created_at"], "server owns received_at_server/created_at")
        require("mastery" not in event, "raw paronym event contains observation, not client mastery")

        status, _headers, replay = request_json(
            port,
            "POST",
            admissions_web.PARONYM_ADMISSION_PATH,
            cookie=cookie,
            payload=accepted_payload,
        )
        require(status == 200 and replay.get("status") == "REPLAY", "exact paronym request replay is idempotent")
        require(replay["event_receipt"]["event_id"] == event_id, "paronym replay returns same canonical event identity")

        mutated = dict(accepted_payload)
        mutated["selected_word"] = OTHER_PINNED_CHOICE
        status, _headers, conflict = request_json(
            port,
            "POST",
            admissions_web.PARONYM_ADMISSION_PATH,
            cookie=cookie,
            payload=mutated,
        )
        require(status == 409 and conflict.get("error") == "INTEGRITY_CONFLICT", "mutated paronym replay fails closed")
        require(inspection.raw_event(event_id) == event, "mutated paronym replay cannot alter durable canonical event")

        status, _headers, incorrect = request_json(
            port,
            "POST",
            admissions_web.PARONYM_ADMISSION_PATH,
            cookie=cookie,
            payload=evidence_payload(request_id="paronym-incorrect-0002", selected_word=OTHER_PINNED_CHOICE),
        )
        require(status == 200 and incorrect.get("status") == "ACCEPTED", "wrong but pinned choice remains valid learner evidence")
        incorrect_event = inspection.raw_event(str(incorrect["event_receipt"]["event_id"]))
        require(incorrect_event is not None, "incorrect paronym observation is durable")
        require(incorrect_event["result"]["correctness"] is False and incorrect_event["result"]["score"] == 0, "server deterministically scores wrong pinned choice")
        require(len(incorrect_event["error_observations"]) == 1, "incorrect choice emits one exact rule-error observation")

        print("PARONYM_CONTEXT_ADMISSIONS_GATE_POSTGRES=PASS")
        print("registered_user_identity_ref_required=PASS")
        print("exact_paronym_entries=334")
        print("exact_paronym_groups=144")
        print("exact_action=context_collocation_choice")
        print("semantic_id=ru-lexis-paronym-collocation-choice")
        print("deterministic_server_scoring=PASS")
        print("replay_integrity=PASS")
        print("false_exact_mastery=0")
        print("production_writes=0")
    finally:
        if inspection is not None:
            inspection.close()
        server.shutdown()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
