#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
KERNEL_DIR = ENGINE / "peis-reference-kernel"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(KERNEL_DIR))

from peis_persistence import IntegrityConflict, PeisPersistenceStore  # noqa: E402
from peis_reference_kernel import snapshot  # noqa: E402

MATH_TARGET = "math-probability-classical-equally-likely"
RU_PREQ = "school-verb-personal-ending-conjugation-base"
RU_TARGET = "school-participle-vowel-suffix-conjugation-base"
RU_GOAL = "present-tense participle suffix selection"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def expect_integrity_conflict(fn, message: str) -> None:
    try:
        fn()
    except IntegrityConflict:
        print(f"PASS assertion: {message}")
        return
    raise AssertionError(message)


def new_store(path: Path) -> PeisPersistenceStore:
    return PeisPersistenceStore(
        path,
        evidence_schema=load(ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json"),
        nba_schema=load(ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json"),
    )


def validate_math(base: Path) -> dict:
    fixtures = load(ENGINE / "mathematics-identity/verified-slices/MATH-SLICE-001-EVIDENCE-FIXTURES-v0.1.json")["events"]
    by_id = {event["event_id"]: event for event in fixtures}
    learner = fixtures[0]["learner_profile_id"]

    with new_store(base / "math.sqlite") as store:
        for event in [fixtures[2], fixtures[0], fixtures[1]]:
            result = store.append_event(event)
            require(result["status"] == "ACCEPTED", f"math out-of-order append accepted: {event['event_id']}")

        ordered = store.list_events(learner, "mathematics")
        require([event["event_id"] for event in ordered] == [
            "math001.ev.diag.failure.001",
            "math001.ev.guided.success.002",
            "math001.ev.verify.success.003",
        ], "math replay order follows server evidence order, not insertion order")

        duplicate = store.append_event(fixtures[0])
        require(duplicate["status"] == "ALREADY_APPLIED", "exact duplicate event_id is idempotent")
        require(store.event_count(learner_profile_id=learner, subject_id="mathematics") == 3, "duplicate append creates no extra evidence row")

        conflicting = copy.deepcopy(fixtures[0])
        conflicting["result"]["response_value"] = "0.99"
        expect_integrity_conflict(lambda: store.append_event(conflicting), "same event_id with different payload is rejected")

        semantic_events = store.list_events(learner, "mathematics", semantic_id=MATH_TARGET)
        require(len(semantic_events) == 3, "learner/subject/semantic query returns all three math events")

        final = store.recompute_snapshot(
            learner_profile_id=learner,
            subject_id="mathematics",
            semantic_id=MATH_TARGET,
            admitted_edges=[],
            goal_context="math-slice-001",
            kernel_snapshot=snapshot,
            recommendation_id="nba.persistence.math.final.001",
        )
        require(final["mastery"]["mastery"]["band"] == "DEVELOPING", "persisted math replay reproduces DEVELOPING mastery")
        require(final["nba"]["action_type"] == "RETENTION_REVIEW", "persisted math replay reproduces RETENTION_REVIEW NBA")
        require(final["state"]["mastery"]["estimate"] is None, "persistence layer does not invent numeric mastery")
        require(final["state"]["retention_due_at"] is None, "persistence layer does not invent retention due time")
        cached = store.load_materialized_snapshot(learner, "mathematics", MATH_TARGET, goal_context="math-slice-001")
        require(cached == final, "materialized snapshot cache exactly matches deterministic recompute")

        telemetry = store.telemetry_summary(learner, "mathematics", MATH_TARGET)
        require(telemetry["effective_event_count"] == 3, "math telemetry sees three effective events")
        require(telemetry["assistance_levels"].get("GUIDED_HINT") == 1, "assistance telemetry preserves guided hint")
        require(telemetry["same_session_verification_refs"] == ["math001.ev.verify.success.003"], "verification telemetry preserves same-session verification provenance")
        require(len(telemetry["provenance_refs"]) >= 2, "telemetry preserves source provenance refs")

        raw_before_link = store.raw_event("math001.ev.diag.failure.001")
        require(store.resolve_identity("anon:math-slice-001") == learner, "anonymous identity from evidence resolves to learner history")
        link = store.link_identity("user:math-fixture-account-001", learner, identity_kind="USER")
        require(link["status"] == "LINKED", "later authenticated identity can attach to existing learner profile")
        require(store.resolve_identity("user:math-fixture-account-001") == learner, "new user identity resolves to same academic history")
        raw_after_link = store.raw_event("math001.ev.diag.failure.001")
        require(raw_after_link == raw_before_link, "identity linking does not rewrite historical raw evidence")
        require("user_identity_ref" not in raw_after_link["identity_refs"], "historical anonymous event remains historically anonymous")

        recommendation = final["nba"]
        require(store.append_recommendation(recommendation)["status"] == "ACCEPTED", "NBA proposal persists as append-only recommendation")
        require(store.append_recommendation(recommendation)["status"] == "ALREADY_APPLIED", "duplicate NBA proposal is idempotent")
        outcome = {
            "outcome_event_id": "nbaout.math.final.001",
            "recommendation_id": recommendation["recommendation_id"],
            "event_type": "SUBSEQUENT_INDEPENDENT_SUCCESS",
            "occurred_at": "2026-08-20T16:16:00+03:00",
            "outcome_log_policy_version": "nba-outcome-log-v0.1",
            "evidence_event_refs": ["math001.ev.verify.success.003"],
            "notes": "fixture outcome linked to fresh independent verification",
        }
        require(store.append_recommendation_outcome(outcome)["status"] == "ACCEPTED", "recommendation outcome persists against contract 285")
        require(store.append_recommendation_outcome(outcome)["status"] == "ALREADY_APPLIED", "duplicate recommendation outcome is idempotent")
        altered_outcome = copy.deepcopy(outcome)
        altered_outcome["event_type"] = "SUBSEQUENT_INDEPENDENT_FAILURE"
        expect_integrity_conflict(lambda: store.append_recommendation_outcome(altered_outcome), "same outcome_event_id cannot be rewritten with a different result")
        require(store.recommendation_outcomes(recommendation["recommendation_id"]) == [outcome], "outcome query returns one immutable evaluation record")

        try:
            with store.connection:
                store.connection.execute(
                    "UPDATE evidence_events SET subject_id = 'tampered' WHERE event_id = ?",
                    ("math001.ev.diag.failure.001",),
                )
        except sqlite3.DatabaseError:
            print("PASS assertion: SQLite trigger blocks in-place evidence mutation")
        else:
            raise AssertionError("SQLite trigger blocks in-place evidence mutation")

    with new_store(base / "idempotency.sqlite") as store:
        first = copy.deepcopy(by_id["math001.ev.verify.success.003"])
        first["event_id"] = "math001.ev.idem.first.010"
        first["idempotency_key"] = "idem:math001:logical:010"
        first["learner_profile_id"] = "learner-fixture-idempotency"
        first["identity_refs"] = {"anonymous_identity_ref": "anon:math-idempotency"}
        first["timestamps"]["server_sequence"] = 10
        first["timestamps"]["server_watermark"] = "wm-idem-010"
        require(store.append_event(first)["status"] == "ACCEPTED", "first idempotency-key event is accepted")

        retry = copy.deepcopy(first)
        retry["event_id"] = "math001.ev.idem.retry.011"
        retry["created_at"] = "2026-08-20T16:15:02+03:00"
        retry["timestamps"]["received_at_server"] = "2026-08-20T16:15:02+03:00"
        retry["timestamps"]["server_sequence"] = 11
        retry["timestamps"]["server_watermark"] = "wm-idem-011"
        result = store.append_event(retry)
        require(result["status"] == "ALREADY_APPLIED" and result["reason"] == "IDEMPOTENCY_KEY_REPLAY", "idempotency_key suppresses regenerated transport identity")
        require(store.event_count() == 1, "idempotency-key retry creates no second event")

        bad_retry = copy.deepcopy(retry)
        bad_retry["result"]["response_value"] = "0.9"
        expect_integrity_conflict(lambda: store.append_event(bad_retry), "idempotency_key with changed educational payload is rejected")

    return {
        "final_mastery": "DEVELOPING",
        "final_nba": "RETENTION_REVIEW",
        "telemetry_assisted_count": 1,
        "idempotency": "PASS",
        "identity_continuity": "PASS",
        "nba_outcome_logging": "PASS",
    }


def validate_russian(base: Path) -> dict:
    all_events = load(ENGINE / "russian-program/verified-slices/RU-SLICE-001-EVIDENCE-FIXTURES-v0.1.json")["events"]
    by_id = {event["event_id"]: event for event in all_events}
    ids = [
        "ru001.ev.composite.error.001",
        "ru001.ev.preq.diag.success",
        "ru001.ev.target.diag.failure",
        "ru001.ev.target.assisted.success",
        "ru001.ev.target.verify.success",
    ]
    selected = [by_id[event_id] for event_id in ids]
    edge = load(ENGINE / "russian-program/verified-slices/RU-SLICE-001-PREREQUISITE-EDGE-v0.1.json")
    learner = selected[0]["learner_profile_id"]

    def build(db_name: str, insertion: list[dict]) -> dict:
        with new_store(base / db_name) as store:
            for event in insertion:
                require(store.append_event(event)["status"] == "ACCEPTED", f"Russian event accepted: {event['event_id']}")
            replayed = store.list_events(learner, "russian")
            require([event["event_id"] for event in replayed] == ids, f"{db_name} deterministic Russian replay order")
            result = store.recompute_snapshot(
                learner_profile_id=learner,
                subject_id="russian",
                semantic_id=RU_TARGET,
                admitted_edges=[edge],
                goal_context=RU_GOAL,
                kernel_snapshot=snapshot,
                recommendation_id="nba.persistence.ru.final.001",
            )
            require(result["readiness"]["status"] == "READY_TO_LEARN_OR_PRACTICE", f"{db_name} canonical prerequisite is met")
            require(result["readiness"]["required_prerequisite_assessments"][0]["state"] == "MET", f"{db_name} Russian prerequisite assessment is MET")
            require(result["mastery"]["mastery"]["band"] == "DEVELOPING", f"{db_name} Russian target reaches DEVELOPING")
            require(result["nba"]["action_type"] == "RETENTION_REVIEW", f"{db_name} Russian target reaches RETENTION_REVIEW")
            telemetry = store.telemetry_summary(learner, "russian", RU_TARGET)
            require("ru001.ev.target.assisted.success" in telemetry["assisted_event_refs"], f"{db_name} Russian assistance provenance survives persistence")
            require("ru001.ev.target.verify.success" in telemetry["same_session_verification_refs"], f"{db_name} Russian verification provenance survives persistence")
            return result

    forward = build("russian-forward.sqlite", selected)
    reverse = build("russian-reverse.sqlite", list(reversed(selected)))
    require(forward == reverse, "Russian snapshot is identical under reverse insertion order")

    return {
        "final_mastery": forward["mastery"]["mastery"]["band"],
        "final_readiness": forward["readiness"]["status"],
        "final_nba": forward["nba"]["action_type"],
        "reverse_replay_equal": True,
    }


def validate_correction_boundary(base: Path) -> dict:
    math_event = load(ENGINE / "mathematics-identity/verified-slices/MATH-SLICE-001-EVIDENCE-FIXTURES-v0.1.json")["events"][0]
    with new_store(base / "correction.sqlite") as store:
        base_event = copy.deepcopy(math_event)
        base_event["event_id"] = "math001.ev.correction.base.020"
        base_event["learner_profile_id"] = "learner-fixture-correction"
        base_event["identity_refs"] = {"anonymous_identity_ref": "anon:math-correction"}
        base_event["timestamps"]["server_sequence"] = 20
        base_event["timestamps"]["server_watermark"] = "wm-correction-020"
        require(store.append_event(base_event)["status"] == "ACCEPTED", "correction base evidence accepted")

        corrected = copy.deepcopy(base_event)
        corrected["event_id"] = "math001.ev.correction.fix.021"
        corrected["event_kind"] = "CORRECTION"
        corrected["timestamps"]["server_sequence"] = 21
        corrected["timestamps"]["server_watermark"] = "wm-correction-021"
        corrected["timestamps"]["received_at_server"] = "2026-08-20T16:17:00+03:00"
        corrected["created_at"] = "2026-08-20T16:17:00+03:00"
        corrected["result"]["outcome"] = "CORRECT"
        corrected["result"]["correctness"] = True
        corrected["result"]["score"] = 1
        corrected["result"]["response_value"] = "0.25"
        corrected["correction"] = {
            "supersedes_event_id": base_event["event_id"],
            "correction_reason": "fixture evaluator correction",
            "correction_actor": {"actor_type": "EVALUATOR_PIPELINE", "actor_ref": "fixture-corrector"},
            "correction_version": "0.1.0",
        }
        require(store.append_event(corrected)["status"] == "ACCEPTED", "append-only CORRECTION accepted against existing evidence")
        require(store.event_count() == 2, "correction preserves both raw historical records")
        effective = store.list_events("learner-fixture-correction", "mathematics")
        require([event["event_id"] for event in effective] == [corrected["event_id"]], "effective replay suppresses superseded event without deleting it")
        require(store.raw_event(base_event["event_id"]) is not None, "superseded raw event remains durable")

    return {"raw_event_count": 2, "effective_event_count": 1, "append_only_correction": "PASS"}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="peis-persistence-001-") as tmp:
        base = Path(tmp)
        math = validate_math(base)
        russian = validate_russian(base)
        correction = validate_correction_boundary(base)

    result = {
        "task": "PEIS-PERSISTENCE-001",
        "result": "PASS",
        "implementation_status": "REFERENCE_PERSISTENCE_BOUNDARY_NOT_LIVE_PRODUCTION",
        "math": math,
        "russian": russian,
        "correction_boundary": correction,
        "shared_invariants": {
            "raw_evidence_append_only": True,
            "materialized_state_rebuildable": True,
            "subject_specific_learner_engine_created": False,
            "production_database_claimed": False,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    print("PEIS-PERSISTENCE-001 VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
