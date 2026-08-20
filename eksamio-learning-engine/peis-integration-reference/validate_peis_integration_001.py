#!/usr/bin/env python3
"""Validate the first current-product-shaped Russian trainer -> shared PEIS loop."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "peis-reference-kernel"))
sys.path.insert(0, str(ROOT / "peis-persistence-reference"))
sys.path.insert(0, str(HERE))

from peis_persistence import PeisPersistenceStore  # noqa: E402
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from russian_trainer_sensor import (  # noqa: E402
    RussianTrainerSensorAdapter,
    find_card,
    load_trainer_bank_chunk,
    product_directive,
)


PREQ = "school-verb-personal-ending-conjugation-base"
TARGET = "school-participle-vowel-suffix-conjugation-base"
GOAL_CONTEXT = "present-tense participle suffix selection"
LEARNER = "learner-peis-integration-001"
IDENTITY = {"anonymous_identity_ref": "anon:peis-integration-001"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    material = f"blob {len(payload)}\0".encode("utf-8") + payload
    return hashlib.sha1(material).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def fixture_by_id(fixtures: dict[str, Any], event_id: str) -> dict[str, Any]:
    for event in fixtures["events"]:
        if event["event_id"] == event_id:
            return event
    raise AssertionError(f"missing fixture event {event_id}")


def clone_fixture_event(
    template: dict[str, Any],
    *,
    event_id: str,
    session_id: str,
    sequence: int,
    occurred_at: str,
    watermark: str,
    origin_ref_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    event = copy.deepcopy(template)
    old_event_id = event["event_id"]
    event["event_id"] = event_id
    event.pop("idempotency_key", None)
    event["learner_profile_id"] = LEARNER
    event["identity_refs"] = copy.deepcopy(IDENTITY)
    event["session_id"] = session_id
    event["timestamps"] = {
        "occurred_at_client": occurred_at,
        "received_at_server": occurred_at,
        "server_sequence": sequence,
        "server_watermark": watermark,
    }
    event["created_at"] = occurred_at

    mapping = dict(origin_ref_map or {})
    mapping[old_event_id] = event_id
    transfer = event.get("transfer_context") or {}
    transfer["origin_event_refs"] = [mapping.get(ref, ref) for ref in transfer.get("origin_event_refs", [])]
    assistance = event.get("assistance") or {}
    assistance["help_event_refs"] = [mapping.get(ref, ref) for ref in assistance.get("help_event_refs", [])]
    return event


def outcome_event(
    *,
    outcome_id: str,
    recommendation_id: str,
    event_type: str,
    occurred_at: str,
    evidence_refs: list[str],
) -> dict[str, Any]:
    return {
        "outcome_event_id": outcome_id,
        "recommendation_id": recommendation_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "outcome_log_policy_version": "nba-outcome-v0.1",
        "evidence_event_refs": evidence_refs,
        "notes": None,
    }


def main() -> int:
    mapping_path = HERE / "RUSSIAN-EGE-TRAINER-SENSOR-MAP-v0.1.json"
    mapping = load_json(mapping_path)
    runtime_path = ROOT / "russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-10.txt"
    bank_path = ROOT / "russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-06.txt"
    runtime_before = runtime_path.read_bytes()
    bank_before = bank_path.read_bytes()

    require(git_blob_sha(runtime_path) == mapping["source_runtime"]["trainer_runtime_blob_sha"], "sensor map is pinned to the actual current trainer runtime blob")
    require(git_blob_sha(bank_path) == mapping["source_runtime"]["task12_bank_blob_sha"], "sensor map is pinned to the actual current Task 12 bank blob")
    runtime_text = runtime_before.decode("utf-8")
    require("function checkCurrent(card)" in runtime_text, "actual current runtime exposes checkCurrent(card)")
    require("function recordCard(card,checked)" in runtime_text, "actual current runtime exposes recordCard(card,checked)")
    require("session.checked[card.id]=checked" in runtime_text, "actual current runtime stores checked {score,max,answer} per card")

    bank = load_trainer_bank_chunk(bank_path)
    card = find_card(bank, "ege-ru-12-2026-12-01")
    require(card["task"] == 12 and card["kind"] == "unordered_digits", "actual current Task 12 card is loaded from repository bank")
    require(card["maxScore"] == 1, "actual current Task 12 card uses deterministic whole-card maxScore=1")

    wrong_answer = ["2", "5"]
    expected = sorted(str(card["answer"]))
    require(sorted(wrong_answer) != expected, "validation product response is genuinely wrong against the current card key")
    session = {
        "version": 1,
        "status": "running",
        "mode": "practice",
        "ids": [card["id"]],
        "current": 0,
        "answers": {card["id"]: wrong_answer},
        "checked": {},
        "recorded": {},
        "startedAt": 1787238000000,
        "endsAt": None,
        "completedAt": None,
        "config": {"mode": "practice", "tasks": [12]},
    }
    checked = {"score": 0, "max": 1, "answer": wrong_answer}

    adapter = RussianTrainerSensorAdapter(mapping)
    trainer_event = adapter.build_checked_event(
        card=card,
        session=session,
        checked=checked,
        learner_profile_id=LEARNER,
        identity_refs=IDENTITY,
        occurred_at_client="2026-08-20T17:00:00+03:00",
        received_at_server="2026-08-20T17:00:01+03:00",
        server_sequence=1,
        server_watermark="wm-peisint-001",
    )
    require(all(t["mapping_resolution"] == "COMPOSITE" for t in trainer_event["semantic_targets"]), "real trainer Task 12 event remains COMPOSITE across semantic targets")
    require(trainer_event["error_observations"][0]["precision"] == "UNKNOWN", "whole-card failure does not invent exact semantic error")
    require(not any(obs["precision"] == "EXACT" for obs in trainer_event["error_observations"]), "no exact error observation is emitted from broad Task 12 failure")

    evidence_schema = load_json(ROOT / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json")
    nba_schema = load_json(ROOT / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json")
    edge = load_json(ROOT / "russian-program/verified-slices/RU-SLICE-001-PREREQUISITE-EDGE-v0.1.json")
    fixtures = load_json(ROOT / "russian-program/verified-slices/RU-SLICE-001-EVIDENCE-FIXTURES-v0.1.json")

    with tempfile.TemporaryDirectory(prefix="peis-integration-001-") as temp_dir:
        db_path = Path(temp_dir) / "integration.sqlite"
        with PeisPersistenceStore(db_path, evidence_schema=evidence_schema, nba_schema=nba_schema) as store:
            appended = store.append_event(trainer_event)
            require(appended["status"] == "ACCEPTED", "current trainer-shaped event is accepted by shared persistence")
            duplicate = store.append_event(copy.deepcopy(trainer_event))
            require(duplicate["status"] == "ALREADY_APPLIED", "duplicate current trainer sensor delivery is idempotent")
            require(store.event_count(learner_profile_id=LEARNER, subject_id="russian") == 1, "idempotent retry creates no duplicate learner evidence")

            snap1 = store.recompute_snapshot(
                learner_profile_id=LEARNER,
                subject_id="russian",
                semantic_id=TARGET,
                admitted_edges=[edge],
                goal_context=GOAL_CONTEXT,
                kernel_snapshot=kernel_snapshot,
                recommendation_id="nba.peisint.001",
            )
            d1 = product_directive(snap1)
            require(snap1["readiness"]["status"] == "INSUFFICIENT_EVIDENCE", "composite real trainer failure leaves prerequisite evidence insufficient")
            require(d1["action_type"] == "DIAGNOSE_TARGET", "shared PEIS routes broad Task 12 failure to exact diagnosis")
            require(d1["semantic_targets"] == [PREQ], "diagnostic NBA targets the unknown prerequisite rather than guessing target mastery")
            require(snap1["mastery"]["mastery"]["estimate"] is None, "integration does not invent numeric mastery")
            store.append_recommendation(snap1["nba"])
            store.append_recommendation_outcome(
                outcome_event(
                    outcome_id="out.peisint.001.shown",
                    recommendation_id=snap1["nba"]["recommendation_id"],
                    event_type="SHOWN",
                    occurred_at="2026-08-20T17:00:02+03:00",
                    evidence_refs=[trainer_event["event_id"]],
                )
            )

            preq_fail = clone_fixture_event(
                fixture_by_id(fixtures, "ru001.ev.preq.diag.failure"),
                event_id="peisint.ev.preq.diag.failure",
                session_id="peisint.session.diagnostic",
                sequence=2,
                occurred_at="2026-08-20T17:01:00+03:00",
                watermark="wm-peisint-002",
                origin_ref_map={trainer_event["event_id"]: trainer_event["event_id"]},
            )
            store.append_event(preq_fail)
            snap2 = store.recompute_snapshot(
                learner_profile_id=LEARNER,
                subject_id="russian",
                semantic_id=TARGET,
                admitted_edges=[edge],
                goal_context=GOAL_CONTEXT,
                kernel_snapshot=kernel_snapshot,
                recommendation_id="nba.peisint.002",
            )
            d2 = product_directive(snap2)
            require(snap2["readiness"]["status"] == "BLOCKED_BY_REQUIRED_PREREQUISITE", "exact prerequisite failure blocks the target through canonical graph")
            require(d2["action_type"] == "LEARN_PREREQUISITE", "shared NBA selects prerequisite repair after exact prerequisite failure")
            require(d2["prerequisite_targets"] == [PREQ], "prerequisite repair directive names the canonical prerequisite identity")

            preq_reverify = clone_fixture_event(
                fixture_by_id(fixtures, "ru001.ev.preq.reverify.success"),
                event_id="peisint.ev.preq.reverify.success",
                session_id="peisint.session.prereq-reverify",
                sequence=3,
                occurred_at="2026-08-20T17:03:00+03:00",
                watermark="wm-peisint-003",
                origin_ref_map={
                    "ru001.ev.preq.diag.failure": preq_fail["event_id"],
                },
            )
            preq_reverify["transfer_context"]["kind"] = "SAME_SESSION_VERIFICATION"
            preq_reverify["transfer_context"]["origin_event_refs"] = [preq_fail["event_id"]]
            store.append_event(preq_reverify)
            snap3 = store.recompute_snapshot(
                learner_profile_id=LEARNER,
                subject_id="russian",
                semantic_id=TARGET,
                admitted_edges=[edge],
                goal_context=GOAL_CONTEXT,
                kernel_snapshot=kernel_snapshot,
                recommendation_id="nba.peisint.003",
            )
            d3 = product_directive(snap3)
            require(snap3["readiness"]["status"] == "READY_TO_LEARN_OR_PRACTICE", "independent prerequisite re-verification reopens the target")
            require(d3["action_type"] == "GUIDED_PRACTICE", "shared NBA returns learner to the original target after prerequisite repair")

            target_assisted = clone_fixture_event(
                fixture_by_id(fixtures, "ru001.ev.target.assisted.success"),
                event_id="peisint.ev.target.assisted.success",
                session_id="peisint.session.target-guided",
                sequence=4,
                occurred_at="2026-08-20T17:04:00+03:00",
                watermark="wm-peisint-004",
            )
            store.append_event(target_assisted)
            snap4 = store.recompute_snapshot(
                learner_profile_id=LEARNER,
                subject_id="russian",
                semantic_id=TARGET,
                admitted_edges=[edge],
                goal_context=GOAL_CONTEXT,
                kernel_snapshot=kernel_snapshot,
                recommendation_id="nba.peisint.004",
            )
            d4 = product_directive(snap4)
            require(d4["action_type"] == "INDEPENDENT_PRACTICE", "assisted target success requires independent verification")
            require(d4["verification_required"] is True, "product directive preserves the shared verification requirement")
            store.append_recommendation(snap4["nba"])
            store.append_recommendation_outcome(
                outcome_event(
                    outcome_id="out.peisint.004.accepted",
                    recommendation_id=snap4["nba"]["recommendation_id"],
                    event_type="ACCEPTED",
                    occurred_at="2026-08-20T17:04:01+03:00",
                    evidence_refs=[target_assisted["event_id"]],
                )
            )

            target_verify = clone_fixture_event(
                fixture_by_id(fixtures, "ru001.ev.target.verify.success"),
                event_id="peisint.ev.target.verify.success",
                session_id="peisint.session.target-verify",
                sequence=5,
                occurred_at="2026-08-20T17:05:00+03:00",
                watermark="wm-peisint-005",
                origin_ref_map={
                    "ru001.ev.target.assisted.success": target_assisted["event_id"],
                },
            )
            target_verify["transfer_context"]["origin_event_refs"] = [target_assisted["event_id"]]
            store.append_event(target_verify)
            snap5 = store.recompute_snapshot(
                learner_profile_id=LEARNER,
                subject_id="russian",
                semantic_id=TARGET,
                admitted_edges=[edge],
                goal_context=GOAL_CONTEXT,
                kernel_snapshot=kernel_snapshot,
                recommendation_id="nba.peisint.005",
            )
            d5 = product_directive(snap5)
            require(snap5["mastery"]["mastery"]["band"] == "DEVELOPING", "fresh independent target verification produces measured DEVELOPING mastery")
            require(d5["action_type"] == "RETENTION_REVIEW", "closed loop advances to retention after independent verification")
            require(snap5["retention"]["next_due_calculation"]["due_window_start"] is None, "integration does not invent a retention due time")

            store.append_recommendation_outcome(
                outcome_event(
                    outcome_id="out.peisint.004.independent-success",
                    recommendation_id=snap4["nba"]["recommendation_id"],
                    event_type="SUBSEQUENT_INDEPENDENT_SUCCESS",
                    occurred_at="2026-08-20T17:05:01+03:00",
                    evidence_refs=[target_verify["event_id"]],
                )
            )
            outcomes = store.recommendation_outcomes(snap4["nba"]["recommendation_id"])
            require(any(row["event_type"] == "SUBSEQUENT_INDEPENDENT_SUCCESS" and target_verify["event_id"] in row["evidence_event_refs"] for row in outcomes), "recommendation outcome log links independent success to the prior NBA")
            require(store.event_count(learner_profile_id=LEARNER, subject_id="russian") == 5, "shared persistence holds the five-step integration evidence history")

            target_telemetry = store.telemetry_summary(LEARNER, "russian", TARGET)
            require(target_verify["event_id"] in target_telemetry["verification_event_refs"], "read-side telemetry preserves final same-session verification provenance")
            require(d5["canonical_state_owner"] == "shared_peis", "product read-side directive explicitly leaves canonical state ownership in shared PEIS")

    require(runtime_path.read_bytes() == runtime_before, "validation leaves current trainer runtime byte-identical")
    require(bank_path.read_bytes() == bank_before, "validation leaves current trainer Task 12 bank byte-identical")

    summary = {
        "task": "PEIS-INTEGRATION-001",
        "result": "PASS",
        "real_product_sensor": {
            "runtime": "ege-russkiy-trenazher-T123-10.txt",
            "card": card["id"],
            "initial_mapping_resolution": "COMPOSITE",
            "initial_nba": d1["action_type"],
            "exact_error_invented": False,
        },
        "closed_loop": {
            "after_exact_prerequisite_failure": d2["action_type"],
            "after_prerequisite_reverification": d3["action_type"],
            "after_assisted_target_success": d4["action_type"],
            "final_mastery": snap5["mastery"]["mastery"]["band"],
            "final_nba": d5["action_type"],
            "recommendation_outcome_linked": True,
        },
        "shared_invariants": {
            "shared_persistence_reused": True,
            "shared_kernel_reused": True,
            "trainer_scoring_mutated": False,
            "trainer_local_storage_mutated": False,
            "subject_specific_learner_engine_created": False,
        },
        "implementation_status": "REFERENCE_INTEGRATION_VALIDATED_NOT_LIVE_TILDA_WIRING",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    print("PEIS-INTEGRATION-001 VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
