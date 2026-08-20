#!/usr/bin/env python3
"""Validate the executable subject-neutral PEIS service/transport boundary."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "peis-persistence-reference"))
sys.path.insert(0, str(ROOT / "peis-reference-kernel"))
sys.path.insert(0, str(ROOT / "peis-integration-reference"))
sys.path.insert(0, str(HERE))

from peis_persistence import IntegrityConflict, PeisPersistenceStore  # noqa: E402
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_service_bridge import (  # noqa: E402
    AdapterRegistry,
    HostIdentity,
    MissingHostIdentity,
    PeisServiceBridge,
    ServiceRequestError,
    make_reference_http_handler,
)
from russian_checked_card_adapter import RussianEgeTrainerTask12Adapter  # noqa: E402


LEARNER = "learner-service-bridge-001"
IDENTITY = HostIdentity(
    learner_profile_id=LEARNER,
    identity_refs={"anonymous_identity_ref": "anon:service-bridge-001"},
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def request_payload(answer: list[str] | None = None) -> dict[str, Any]:
    return {
        "card_id": "ege-ru-12-2026-12-01",
        "session_started_at_ms": 1787238000000,
        "session_mode": "practice",
        "answer": answer if answer is not None else ["2", "5"],
        "occurred_at_client": "2026-08-20T17:00:00+03:00",
        "client_request_id": "browser-attempt-001",
    }


def http_json(
    url: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=data, method=method)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def main() -> int:
    service_source = (HERE / "peis_service_bridge.py").read_text(encoding="utf-8")
    for forbidden_literal in (
        "school-verb-personal-ending-conjugation-base",
        "school-participle-vowel-suffix-conjugation-base",
        "ege-ru-12-2026-12-01",
    ):
        require(forbidden_literal not in service_source, f"generic service core does not embed subject truth literal {forbidden_literal}")

    runtime_path = ROOT / "russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-10.txt"
    bank_path = ROOT / "russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-06.txt"
    runtime_before = runtime_path.read_bytes()
    bank_before = bank_path.read_bytes()

    evidence_schema = load_json(ROOT / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json")
    nba_schema = load_json(ROOT / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json")
    adapter = RussianEgeTrainerTask12Adapter(ROOT)
    registry = AdapterRegistry()
    registry.register(adapter)
    require(registry.adapter_ids() == ["russian-ege-trainer-task12-v0.1"], "Russian subject adapter is registered separately from the generic service core")

    fixed_now = "2026-08-20T17:00:01+03:00"
    with tempfile.TemporaryDirectory(prefix="peis-service-bridge-001-") as temp_dir:
        db_path = Path(temp_dir) / "service.sqlite"
        with PeisPersistenceStore(db_path, evidence_schema=evidence_schema, nba_schema=nba_schema) as store:
            bridge = PeisServiceBridge(
                store=store,
                registry=registry,
                kernel_snapshot=kernel_snapshot,
                now_provider=lambda: fixed_now,
            )

            # Browser cannot assert canonical truth or transport position.
            forbidden_examples = {
                "score": 1,
                "correctness": True,
                "semantic_targets": [{"semantic_id": "client-guess"}],
                "evaluator": {"trust_class": "OFFICIAL_SOURCE_HIGH"},
                "mastery": {"band": "STRONG"},
                "nba": {"action_type": "STOP_SESSION_COMPLETE"},
                "server_sequence": 999,
                "server_watermark": "client-owned",
            }
            for field, value in forbidden_examples.items():
                malicious = request_payload()
                malicious[field] = value
                try:
                    bridge.submit_checked_card(
                        adapter_id=adapter.adapter_id,
                        payload=malicious,
                        host_identity=IDENTITY,
                    )
                except ServiceRequestError:
                    pass
                else:
                    raise AssertionError(f"client truth field was accepted: {field}")
                require(store.event_count(learner_profile_id=LEARNER, subject_id="russian") == 0, f"rejected client field {field} creates no evidence")

            first = bridge.submit_checked_card(
                adapter_id=adapter.adapter_id,
                payload=request_payload(),
                host_identity=IDENTITY,
            )
            require(first["status"] == "ACCEPTED", "browser-safe checked-card payload is accepted through the service")
            receipt = first["event_receipt"]
            require(receipt["server_sequence"] == 1, "server allocates the first evidence sequence")
            require(str(receipt["server_watermark"]).startswith("svcwm."), "server allocates the evidence watermark")
            require(receipt["received_at_server"] == fixed_now, "server owns received_at_server")
            require(first["directive"]["action_type"] == "DIAGNOSE_TARGET", "broad Task 12 failure returns shared PEIS DIAGNOSE_TARGET")
            require(first["directive"]["canonical_state_owner"] == "shared_peis", "service response keeps canonical state ownership in shared PEIS")
            require(first["recommendation_persistence_status"] == "ACCEPTED", "shared NBA proposal is persisted by the service")

            raw = store.raw_event(receipt["event_id"])
            require(raw is not None, "canonical event is persisted in the shared store")
            assert raw is not None
            require(raw["result"]["score"] == 0 and raw["result"]["correctness"] is False, "server recomputes wrong whole-card score from the pinned card key")
            require(all(target["mapping_resolution"] == "COMPOSITE" for target in raw["semantic_targets"]), "server adapter emits source-owned COMPOSITE semantic mapping")
            require(raw["error_observations"][0]["precision"] == "UNKNOWN", "server adapter does not invent exact semantic error from broad failure")
            require(raw["evaluator"]["trust_class"] == "DETERMINISTIC_HIGH", "evaluator trust comes from the server adapter, not the browser")

            duplicate = bridge.submit_checked_card(
                adapter_id=adapter.adapter_id,
                payload=copy.deepcopy(request_payload()),
                host_identity=IDENTITY,
            )
            require(duplicate["status"] == "ALREADY_APPLIED", "identical service retry is idempotent")
            require(duplicate["event_receipt"]["server_sequence"] == receipt["server_sequence"], "idempotent retry preserves original server sequence")
            require(duplicate["event_receipt"]["server_watermark"] == receipt["server_watermark"], "idempotent retry preserves original server watermark")
            require(duplicate["recommendation_persistence_status"] == "ALREADY_APPLIED", "idempotent retry reuses the same persisted NBA proposal")
            require(store.event_count(learner_profile_id=LEARNER, subject_id="russian") == 1, "retry creates no duplicate evidence")

            try:
                bridge.submit_checked_card(
                    adapter_id=adapter.adapter_id,
                    payload=request_payload(["1", "3", "4"]),
                    host_identity=IDENTITY,
                )
            except IntegrityConflict:
                pass
            else:
                raise AssertionError("changed educational payload under stable session/card identity was accepted")
            require(store.event_count(learner_profile_id=LEARNER, subject_id="russian") == 1, "conflicting retry cannot rewrite or append duplicate evidence")
            require(store.raw_event(receipt["event_id"])["result"]["correctness"] is False, "conflicting retry leaves original canonical evidence unchanged")

            try:
                HostIdentity(LEARNER, {"user_identity_ref": "student@example.com"}).validate()
            except MissingHostIdentity:
                pass
            else:
                raise AssertionError("email was accepted as academic-history identity")
            require(True, "email is rejected as academic-history identity")

            handler = make_reference_http_handler(bridge)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_port}"
                health_status, health = http_json(base_url + "/healthz")
                require(health_status == 200 and health["status"] == "ok", "real loopback HTTP health endpoint works")
                require(health["mode"] == "REFERENCE_NOT_PUBLIC_PRODUCTION", "health endpoint explicitly avoids production deployment claim")

                status, body = http_json(
                    base_url + "/v0/checked-card",
                    method="POST",
                    body={"adapter_id": adapter.adapter_id, "payload": request_payload()},
                    headers={
                        "X-Eksamio-Learner-Profile": LEARNER,
                        "X-Eksamio-Anonymous-Identity": "anon:service-bridge-001",
                    },
                )
                require(status == 200, "real loopback HTTP checked-card endpoint works")
                require(body["status"] == "ALREADY_APPLIED", "HTTP replay reaches the same canonical event idempotently")
                require(body["event_receipt"]["event_id"] == receipt["event_id"], "HTTP transport returns the canonical event receipt")
                require(body["directive"]["action_type"] == "DIAGNOSE_TARGET", "HTTP transport returns shared PEIS read-side directive")

                missing_status, missing_body = http_json(
                    base_url + "/v0/checked-card",
                    method="POST",
                    body={"adapter_id": adapter.adapter_id, "payload": request_payload()},
                )
                require(missing_status == 401 and missing_body["error"] == "HOST_IDENTITY_REQUIRED", "HTTP checked-card rejects missing host identity")

                email_status, email_body = http_json(
                    base_url + "/v0/checked-card",
                    method="POST",
                    body={"adapter_id": adapter.adapter_id, "payload": request_payload()},
                    headers={
                        "X-Eksamio-Learner-Profile": LEARNER,
                        "X-Eksamio-User-Identity": "user:service-bridge-001",
                        "X-Eksamio-Email": "student@example.com",
                    },
                )
                require(email_status == 401 and email_body["error"] == "HOST_IDENTITY_REQUIRED", "reference HTTP identity resolver rejects email identity header")
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    require(runtime_path.read_bytes() == runtime_before, "service validation leaves current Russian trainer runtime byte-identical")
    require(bank_path.read_bytes() == bank_before, "service validation leaves current Russian trainer bank byte-identical")

    summary = {
        "task": "PEIS-SERVICE-BRIDGE-001",
        "result": "PASS",
        "service_core": {
            "subject_neutral": True,
            "registered_adapter": adapter.adapter_id,
            "reference_http": True,
            "production_deployment_claimed": False,
            "public_authentication_claimed": False,
        },
        "trust_boundary": {
            "client_truth_fields_rejected": sorted(forbidden_examples),
            "server_owned_score": True,
            "server_owned_semantic_mapping": True,
            "server_owned_evaluator_trust": True,
            "server_owned_position": True,
            "email_identity_rejected": True,
        },
        "first_response": {
            "event_status": first["status"],
            "server_sequence": receipt["server_sequence"],
            "initial_nba": first["directive"]["action_type"],
            "mapping_resolution": "COMPOSITE",
        },
        "retry": {
            "identical": "ALREADY_APPLIED",
            "changed_payload": "INTEGRITY_CONFLICT",
            "raw_event_count": 1,
        },
        "shared_invariants": {
            "shared_persistence_reused": True,
            "shared_kernel_reused": True,
            "subject_specific_learner_engine_created": False,
            "trainer_runtime_mutated": False,
            "trainer_local_storage_mutated": False,
        },
        "implementation_status": "REFERENCE_HTTP_SERVICE_VALIDATED_NOT_DEPLOYED_PRODUCTION",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    print("PEIS-SERVICE-BRIDGE-001 VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
