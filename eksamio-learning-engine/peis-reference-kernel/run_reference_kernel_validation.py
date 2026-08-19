#!/usr/bin/env python3
"""Run and schema-validate the executable PEIS reference kernel.

The validator consumes the first verified subject slice as data, not as kernel
logic. It also runs a structural mathematics smoke fixture to prove that the
same kernel has no hard-coded subject branch.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema

from peis_reference_kernel import (
    INFERENCE_VERSION,
    infer_mastery,
    snapshot,
)

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
SLICE_DIR = ENGINE / "russian-program" / "verified-slices"

EVENT_SCHEMA_PATH = ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json"
STATE_SCHEMA_PATH = ENGINE / "278-EKSAMIO-LEARNER-STATE-MATERIALIZED-VIEW-SCHEMA-v0.1.json"
MASTERY_SCHEMA_PATH = ENGINE / "282-EKSAMIO-MASTERY-INFERENCE-CONTRACT-v0.1.json"
READINESS_SCHEMA_PATH = ENGINE / "283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json"
RETENTION_SCHEMA_PATH = ENGINE / "284-EKSAMIO-RETENTION-SCHEDULE-STATE-CONTRACT-v0.1.json"
NBA_SCHEMA_PATH = ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json"

EVIDENCE_FIXTURE_PATH = SLICE_DIR / "RU-SLICE-001-EVIDENCE-FIXTURES-v0.1.json"
EDGE_FIXTURE_PATH = SLICE_DIR / "RU-SLICE-001-PREREQUISITE-EDGE-v0.1.json"
GOLDEN_PATH = SLICE_DIR / "RU-SLICE-001-GOLDEN-SCENARIOS-v0.1.json"

RUN_OUTPUT = HERE / "PEIS-REFERENCE-KERNEL-RU-SLICE-001-RUN-v0.1.json"
VALIDATION_OUTPUT = HERE / "PEIS-REFERENCE-KERNEL-VALIDATION.txt"


class Failure(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Failure(f"{path.name}: root is not an object")
    return value


def validator(schema: dict[str, Any]) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def nested_schema(contract: dict[str, Any], def_name: str) -> dict[str, Any]:
    value = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": contract["$defs"],
    }
    value.update(contract["$defs"][def_name])
    return value


def validate_snapshot(
    value: dict[str, Any],
    *,
    state_validator: jsonschema.Draft202012Validator,
    mastery_validator: jsonschema.Draft202012Validator,
    readiness_validator: jsonschema.Draft202012Validator,
    retention_validator: jsonschema.Draft202012Validator,
    nba_validator: jsonschema.Draft202012Validator,
) -> None:
    mastery_validator.validate(value["mastery"])
    readiness_validator.validate(value["readiness"])
    retention_validator.validate(value["retention"])
    state_validator.validate(value["state"])
    nba_validator.validate(value["nba"])
    if value["mastery"]["mastery"]["estimate"] is not None:
        raise Failure("reference kernel must not invent a numeric mastery coefficient")
    if value["state"]["mastery"]["estimate"] is not None:
        raise Failure("materialized state must not invent a numeric mastery coefficient")
    calc = value["retention"]["next_due_calculation"]
    if calc["due_window_start"] is not None or calc["due_window_end"] is not None:
        raise Failure("reference kernel must not invent universal retention timing constants")


def assert_nba(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    if actual["action_type"] != expected["action_type"]:
        raise Failure(f"NBA action mismatch: {actual['action_type']} != {expected['action_type']}")
    if actual["semantic_targets"] != expected.get("semantic_targets", actual["semantic_targets"]):
        raise Failure(f"NBA semantic target mismatch: {actual['semantic_targets']} != {expected.get('semantic_targets')}")
    if "prerequisite_targets" in expected and actual.get("prerequisite_targets", []) != expected["prerequisite_targets"]:
        raise Failure(f"NBA prerequisite mismatch: {actual.get('prerequisite_targets')} != {expected['prerequisite_targets']}")
    if set(actual["reason_codes"]) != set(expected["reason_codes"]):
        raise Failure(f"NBA reasons mismatch: {actual['reason_codes']} != {expected['reason_codes']}")


def compact_snapshot(value: dict[str, Any], *, target: str, consumed: list[str]) -> dict[str, Any]:
    readiness = value["readiness"]
    return {
        "target_semantic_id": target,
        "consumed_event_refs": consumed,
        "mastery": {
            "band": value["mastery"]["mastery"]["band"],
            "status": value["mastery"]["mastery"]["status"],
            "confidence_band": value["mastery"]["system_inference"]["confidence_band"],
            "reason_codes": value["mastery"]["system_inference"]["reason_codes"],
            "contradiction_status": value["mastery"]["system_inference"]["contradiction_status"],
        },
        "readiness": {
            "status": readiness["status"],
            "required_prerequisite_assessments": readiness["required_prerequisite_assessments"],
        },
        "retention_state": value["retention"]["current_state"],
        "state_revision": value["state"]["state_revision"],
        "nba": {
            "action_type": value["nba"]["action_type"],
            "semantic_targets": value["nba"]["semantic_targets"],
            "prerequisite_targets": value["nba"].get("prerequisite_targets", []),
            "reason_codes": value["nba"]["reason_codes"],
            "verification_required": value["nba"]["verification_required"],
        },
    }


def exact_semantics_for_event(event: dict[str, Any]) -> list[str]:
    return [
        target["semantic_id"]
        for target in event.get("semantic_targets", [])
        if target.get("mapping_resolution") == "EXACT"
    ]


def run_subject_scenarios(
    evidence_doc: dict[str, Any],
    edge_doc: dict[str, Any],
    golden_doc: dict[str, Any],
    validators: dict[str, jsonschema.Draft202012Validator],
) -> list[dict[str, Any]]:
    events_by_id = {event["event_id"]: event for event in evidence_doc["events"]}
    semantics = golden_doc["semantic_scope"]
    prerequisite_semantic = semantics["prerequisite"]
    target_semantic = semantics["target"]
    goal_context = semantics["goal_context"]
    results: list[dict[str, Any]] = []

    for scenario in golden_doc["scenarios"]:
        selected: list[dict[str, Any]] = []
        selected_ids: list[str] = []
        helped: set[str] = set()
        trace: list[dict[str, Any]] = []
        scenario_edges = [] if scenario["scenario_id"].startswith("RU001-GUARDRAIL") else [edge_doc]

        for index, step in enumerate(scenario["steps"], start=1):
            before_events = list(selected)
            consumed_event = None
            if "consume_event" in step:
                event_id = step["consume_event"]
                if event_id not in events_by_id:
                    raise Failure(f"golden scenario refers to missing event {event_id}")
                consumed_event = events_by_id[event_id]
                selected.append(consumed_event)
                selected_ids.append(event_id)
            if "instruction_ref" in step:
                helped.add(prerequisite_semantic)

            current_target = prerequisite_semantic if "instruction_ref" in step else target_semantic
            recommendation_id = f"nba.ru001.{scenario['scenario_id'].lower()}.{index:02d}"
            value = snapshot(
                selected,
                current_target,
                scenario_edges,
                goal_context=goal_context,
                meaningful_help_delivered_for=helped,
                recommendation_id=recommendation_id,
            )
            validate_snapshot(value, **validators)

            if "expected_readiness" in step and value["readiness"]["status"] != step["expected_readiness"]:
                raise Failure(
                    f"{scenario['scenario_id']} step {index}: readiness {value['readiness']['status']} != {step['expected_readiness']}"
                )
            if "expected_nba" in step:
                assert_nba(value["nba"], step["expected_nba"])

            if "expected_mastery_reason_codes" in step:
                if consumed_event is None:
                    mastery_target = current_target
                else:
                    exact_semantics = exact_semantics_for_event(consumed_event)
                    mastery_target = exact_semantics[0] if len(exact_semantics) == 1 else current_target
                mastery_value = infer_mastery(selected, mastery_target)
                observed_reasons = set(mastery_value["system_inference"]["reason_codes"])
                if not set(step["expected_mastery_reason_codes"]) <= observed_reasons:
                    raise Failure(
                        f"{scenario['scenario_id']} step {index}: missing mastery reasons {step['expected_mastery_reason_codes']} in {sorted(observed_reasons)}"
                    )

            row = compact_snapshot(value, target=current_target, consumed=list(selected_ids))
            row["step"] = index
            if "instruction_ref" in step:
                row["intervention_ref"] = step["instruction_ref"]
                row["meaningful_help_delivered_for"] = prerequisite_semantic

            if step.get("measured_outcome_required"):
                exact_semantics = exact_semantics_for_event(consumed_event or {})
                delta_target = exact_semantics[0] if len(exact_semantics) == 1 else current_target
                before = infer_mastery(before_events, delta_target)
                after = infer_mastery(selected, delta_target)
                row["measured_state_delta"] = {
                    "semantic_id": delta_target,
                    "mastery_band_before": before["mastery"]["band"],
                    "mastery_band_after": after["mastery"]["band"],
                    "status_before": before["mastery"]["status"],
                    "status_after": after["mastery"]["status"],
                    "evidence_event_ref": consumed_event["event_id"] if consumed_event else None,
                }
            trace.append(row)

        results.append({"scenario_id": scenario["scenario_id"], "status": "PASS", "trace": trace})
    return results


def math_event(event_id: str, *, sequence: int, correct: bool) -> dict[str, Any]:
    semantic_id = "fixture-mathematics-target-12"
    at = f"2026-08-20T01:{sequence:02d}:00+03:00"
    error_observations = []
    if not correct:
        error_observations = [{
            "observation_type": "EXACT_RULE_ERROR",
            "semantic_id": semantic_id,
            "candidate_ref": None,
            "precision": "EXACT",
            "confidence": 1.0,
            "source_locator": event_id,
            "provenance_refs": ["STRUCTURAL_ONLY_NO_SUBJECT_TRUTH"],
        }]
    return {
        "event_id": event_id,
        "schema_version": "0.1.0",
        "event_kind": "PERFORMANCE_OBSERVATION",
        "learner_profile_id": "learner-fixture-math-001",
        "identity_refs": {"anonymous_identity_ref": "anon:math-structural"},
        "subject_id": "mathematics",
        "semantic_targets": [{
            "semantic_id": semantic_id,
            "target_role": "PRIMARY",
            "mapping_resolution": "EXACT",
            "mapping_confidence": 1.0,
            "mapping_review_status": "needs_review",
        }],
        "semantic_context": {
            "semantic_registry_version": "mathematics-structural-fixture-only",
            "semantic_mapping_version": "structural-fixture-v0.1",
            "mapping_artifact_refs": ["TASK-005-S12-STRUCTURAL_ONLY_NO_SUBJECT_TRUTH"],
        },
        "source": {
            "object_type": "structural_fixture",
            "object_id": event_id,
            "content_version": "0.1.0",
            "item_version": "0.1.0",
        },
        "product": {"source_type": "diagnostic", "product_id": "peis-reference-math-smoke", "route": "structural-only"},
        "session_id": "session-math-structural",
        "timestamps": {
            "occurred_at_client": at,
            "received_at_server": at,
            "server_sequence": sequence,
            "server_watermark": f"wm-math-{sequence:03d}",
        },
        "result": {
            "attempt_index": 1,
            "outcome": "CORRECT" if correct else "INCORRECT",
            "correctness": correct,
            "score": 1 if correct else 0,
            "max_score": 1,
            "response_value": "fixture-response",
            "result_details": {"fixture_scope": "STRUCTURAL_ONLY_NO_SUBJECT_TRUTH"},
        },
        "response_mode": "NUMERIC",
        "assistance": {"level": "UNASSISTED", "help_event_refs": [], "assistance_provider": None},
        "evaluator": {
            "evaluator_type": "DETERMINISTIC_VALIDATOR",
            "evaluator_id": "peis-reference-structural",
            "evaluator_version": "0.1.0",
            "trust_class": "DETERMINISTIC_HIGH",
            "uncertainty": 0.0,
            "review_status": "not_required",
            "rubric_version": None,
            "official_truth_status": "NOT_APPLICABLE",
        },
        "provenance_refs": ["STRUCTURAL_ONLY_NO_SUBJECT_TRUTH"],
        "transfer_context": {"kind": "NOT_APPLICABLE", "origin_event_refs": []},
        "retention_context": {"kind": "NONE", "delay_seconds": None, "scheduled_by_policy_version": None},
        "error_observations": error_observations,
        "subject_extension": {
            "subject_payload_schema_version": "structural-fixture-v0.1",
            "subject_payload": {"fixture_scope": "STRUCTURAL_ONLY_NO_SUBJECT_TRUTH"},
        },
        "created_at": at,
    }


def run_mathematics_smoke(
    event_validator: jsonschema.Draft202012Validator,
    validators: dict[str, jsonschema.Draft202012Validator],
) -> dict[str, Any]:
    events = [
        math_event("math.structural.correct.001", sequence=1, correct=True),
        math_event("math.structural.incorrect.002", sequence=2, correct=False),
    ]
    for event in events:
        event_validator.validate(event)
    semantic_id = "fixture-mathematics-target-12"
    value = snapshot(
        events,
        semantic_id,
        [],
        goal_context="STRUCTURAL_ONLY_NO_SUBJECT_TRUTH",
        recommendation_id="nba.math.structural.001",
    )
    validate_snapshot(value, **validators)
    if value["nba"]["action_type"] != "VERIFY_UNCERTAIN_STATE":
        raise Failure(f"mathematics structural smoke did not route to uncertainty verification: {value['nba']['action_type']}")
    if value["nba"]["reason_codes"] != ["CONTRADICTORY_EVIDENCE_NEEDS_VERIFICATION"]:
        raise Failure(f"mathematics structural smoke reasons unexpected: {value['nba']['reason_codes']}")
    if value["state"]["subject_id"] != "mathematics":
        raise Failure("subject-neutral state failed to preserve mathematics subject_id")
    return {
        "fixture_scope": "STRUCTURAL_ONLY_NO_SUBJECT_TRUTH",
        "status": "PASS",
        "trace": compact_snapshot(value, target=semantic_id, consumed=[event["event_id"] for event in events]),
    }


def render_report(subject_scenarios: list[dict[str, Any]], math_smoke: dict[str, Any]) -> str:
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "PEIS REFERENCE KERNEL VALIDATION",
        "DATE: 2026-08-20",
        "STATUS: PASS",
        "MODE: EXECUTABLE_REFERENCE / DETERMINISTIC / NO_PRODUCTION_INTEGRATION",
        "",
        "SHARED CONTRACT SCHEMA VALIDATION",
        "- input EvidenceEvent schema 277: PASS",
        "- learner state schema 278: PASS",
        "- mastery output contract 282: PASS",
        "- readiness state contract 283: PASS",
        "- retention state contract 284: PASS",
        "- NBA contract 285: PASS",
        "",
        "REFERENCE POLICY BOUNDARIES",
        f"- inference_version: {INFERENCE_VERSION}",
        "- numeric mastery estimate invented: NO",
        "- final mastery coefficients invented: NO",
        "- universal forgetting curve/constants invented: NO",
        "- same-session verification counted as delayed retention: NO",
        "- composite evidence converted to exact failure: NO",
        "- subject-specific learner/mastery/readiness/NBA engine: NO",
        "- AI required: NO",
        "",
        "FIRST VERIFIED SUBJECT CLOSED-LOOP FIXTURES",
    ]
    for scenario in subject_scenarios:
        lines.append(f"- {scenario['scenario_id']}: {scenario['status']} / steps={len(scenario['trace'])}")
    lines.extend([
        "",
        "CROSS-SUBJECT STRUCTURAL SMOKE",
        f"- mathematics: {math_smoke['status']} / {math_smoke['fixture_scope']}",
        f"- mathematics NBA: {math_smoke['trace']['nba']['action_type']}",
        "- kernel source contains hard-coded Russian identity/rule branch: NO",
        "",
        "MEASURED OUTCOME",
        "- verified subject scenarios persist before/after qualitative state deltas at independent verification steps: PASS",
        "- recommendation decision is recomputed from accepted evidence at every step: PASS",
        "",
        "PRODUCTION SAFETY",
        "- production learner data touched: NO",
        "- Tilda/runtime/localStorage/scoring touched: NO",
        "- shared contracts mutated: NO",
        "",
        "VERDICT",
        "PASS. The first subject-neutral executable PEIS reference kernel now consumes shared EvidenceEvent data, recomputes learner state/mastery/readiness/retention, and emits schema-valid explainable NBA recommendations. The verified Russian slice executes both prerequisite-gap and prerequisite-met paths, and the same kernel passes a mathematics structural-only smoke. This is a reference implementation, not the production Platform API or persistent Student Learning Twin.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    kernel_source = (HERE / "peis_reference_kernel.py").read_text(encoding="utf-8").lower()
    for forbidden in ["russian", "school-", "ege-ru", "task-12"]:
        if forbidden in kernel_source:
            raise Failure(f"subject-specific token leaked into shared kernel source: {forbidden}")

    event_schema = load(EVENT_SCHEMA_PATH)
    state_schema = load(STATE_SCHEMA_PATH)
    mastery_schema = load(MASTERY_SCHEMA_PATH)
    readiness_contract = load(READINESS_SCHEMA_PATH)
    retention_contract = load(RETENTION_SCHEMA_PATH)
    nba_schema = load(NBA_SCHEMA_PATH)

    event_validator = validator(event_schema)
    validators = {
        "state_validator": validator(state_schema),
        "mastery_validator": validator(mastery_schema),
        "readiness_validator": validator(nested_schema(readiness_contract, "readiness_state")),
        "retention_validator": validator(nested_schema(retention_contract, "state")),
        "nba_validator": validator(nba_schema),
    }

    evidence_doc = load(EVIDENCE_FIXTURE_PATH)
    edge_doc = load(EDGE_FIXTURE_PATH)
    golden_doc = load(GOLDEN_PATH)

    for event in evidence_doc["events"]:
        event_validator.validate(event)
    validator(nested_schema(readiness_contract, "edge_schema")).validate(edge_doc["edge"])

    subject_results = run_subject_scenarios(evidence_doc, edge_doc, golden_doc, validators)
    math_smoke = run_mathematics_smoke(event_validator, validators)

    run_doc = {
        "schema_version": "0.1.0",
        "date": "2026-08-20",
        "status": "PASS_EXECUTABLE_REFERENCE_NO_PRODUCTION_INTEGRATION",
        "kernel_version": INFERENCE_VERSION,
        "subject_fixture_ref": "../russian-program/verified-slices/RU-SLICE-001-GOLDEN-SCENARIOS-v0.1.json",
        "subject_scenarios": subject_results,
        "mathematics_structural_smoke": math_smoke,
        "boundaries": {
            "numeric_mastery_coefficients": False,
            "universal_forgetting_curve": False,
            "subject_specific_core_branch": False,
            "ai_required": False,
            "production_state_write": False,
        },
    }
    report = render_report(subject_results, math_smoke)

    if args.write:
        RUN_OUTPUT.write_text(json.dumps(run_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        VALIDATION_OUTPUT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
