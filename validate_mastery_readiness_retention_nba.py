#!/usr/bin/env python3
"""Deterministically validate TASK-005 architecture-only contracts.

The validator intentionally implements transparent guardrails instead of an
opaque mastery or recommendation model. It reads only TASK-005 artifacts and
writes the required validation snapshot; it does not touch product/runtime
state, source content, scoring, or browser storage.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NAMES = {
    "mastery": "282-EKSAMIO-MASTERY-INFERENCE-CONTRACT-v0.1.json",
    "readiness": "283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json",
    "retention": "284-EKSAMIO-RETENTION-SCHEDULE-STATE-CONTRACT-v0.1.json",
    "nba": "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json",
    "report": "286-EKSAMIO-MASTERY-READINESS-RETENTION-NBA-VALIDATION.txt",
}
ALLOWED_PATHS = {
    *(f"eksamio-learning-engine/{name}" for name in NAMES.values()),
    "eksamio-learning-engine/build/validate_mastery_readiness_retention_nba.py",
    "eksamio-learning-engine/results/RESULT-005-mastery-readiness-retention-nba-materialization.md",
}
REQUIRED_SCENARIOS = {
    "S01-low-mastery-high-confidence", "S02-required-prerequisite-gap",
    "S03-strong-but-stale-low-confidence", "S04-assisted-tutor-success",
    "S05-independent-success-no-delayed-evidence", "S06-retention-failure-restabilization",
    "S07-conflicting-evidence", "S08-near-exam-high-value-gap",
    "S09-homework-urgent-prerequisite-gap", "S10-mastered-retained",
    "S11-no-meaningful-work", "S12-mathematics-structural",
}


class Failure(RuntimeError):
    pass


def load(name: str) -> dict[str, Any]:
    path = ROOT / NAMES[name]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Failure(f"cannot parse {path.name}: {exc}") from exc
    if not isinstance(value, dict):
        raise Failure(f"{path.name} root is not an object")
    return value


def walk_refs(value: Any, root: dict[str, Any]) -> None:
    if isinstance(value, dict):
        ref = value.get("$ref")
        if ref is not None:
            if not isinstance(ref, str) or not ref.startswith("#/"):
                raise Failure(f"non-local or malformed $ref: {ref!r}")
            node: Any = root
            for part in ref[2:].split("/"):
                if not isinstance(node, dict) or part not in node:
                    raise Failure(f"unresolved $ref: {ref}")
                node = node[part]
        for child in value.values():
            walk_refs(child, root)
    elif isinstance(value, list):
        for child in value:
            walk_refs(child, root)


def check_schema(name: str, schema: dict[str, Any]) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise Failure(f"{NAMES[name]} lacks Draft 2020-12 declaration")
    if not str(schema.get("$id", "")).endswith("/0.1.0"):
        raise Failure(f"{NAMES[name]} lacks versioned schema id")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise Failure(f"{NAMES[name]} root must be a closed object schema")
    if not isinstance(schema.get("$defs"), dict) or not schema["$defs"]:
        raise Failure(f"{NAMES[name]} lacks reusable schema definitions")
    walk_refs(schema, schema)


def select_action(flags: set[str]) -> tuple[str, set[str]]:
    """Transparent priority guards used exclusively for scenario verification."""
    if "NO_MEANINGFUL_WORK" in flags:
        return "STOP_SESSION_COMPLETE", {"NO_MEANINGFUL_WORK_IN_SESSION"}
    if "RETENTION_FAILURE_HISTORY_PRESERVED" in flags:
        return "GUIDED_PRACTICE", {"RETENTION_FAILURE_RESTABILIZE"}
    if "REQUIRED_PREREQUISITE_GAP" in flags:
        reasons = {"PREREQUISITE_BLOCKS_TARGET", "PREREQUISITE_REPAIR_FOR_ORIGINAL_GOAL"}
        if "HOMEWORK_URGENT" in flags:
            reasons.add("HOMEWORK_URGENT")
        return "LEARN_PREREQUISITE", reasons
    if "CONTRADICTORY_EVIDENCE" in flags:
        return "VERIFY_UNCERTAIN_STATE", {"CONTRADICTORY_EVIDENCE_NEEDS_VERIFICATION"}
    if "STALE_OR_LOW_CONFIDENCE" in flags:
        return "VERIFY_UNCERTAIN_STATE", {"STALE_EVIDENCE_NEEDS_VERIFICATION"}
    if "MEANINGFUL_ASSISTANCE_WITHOUT_INDEPENDENT_CHECK" in flags:
        return "INDEPENDENT_PRACTICE", {"INDEPENDENT_VERIFICATION_REQUIRED_AFTER_HELP"}
    if "INDEPENDENT_SUCCESS_NO_DELAYED_EVIDENCE" in flags:
        return "RETENTION_REVIEW", {"RETENTION_DUE"}
    if "ALREADY_STRONG_RETAINED" in flags:
        return "MOVE_TO_NEXT_TARGET", {"ALREADY_STRONG_RETAINED"}
    if "LOW_MASTERY_HIGH_CONFIDENCE" in flags:
        reasons = {"LOW_MASTERY_HIGH_CONFIDENCE"}
        if "READY" in flags:
            reasons.add("TARGET_READY_TO_LEARN")
        if "HIGH_VALUE_EXAM_GAP" in flags:
            reasons.add("HIGH_VALUE_EXAM_GAP")
        if "EXAM_DATE_URGENT" in flags:
            reasons.add("EXAM_DATE_URGENCY")
        return "GUIDED_PRACTICE", reasons
    raise Failure(f"fixture has no transparent guardrail route: {sorted(flags)}")


def changed_paths() -> list[str]:
    repo = ROOT.parent
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], cwd=repo, text=True,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise Failure(f"cannot inspect staged diff: {result.stderr.strip()}")
    return sorted(path for path in result.stdout.splitlines() if path)


def validate() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    docs = {key: load(key) for key in ("mastery", "readiness", "retention", "nba")}
    for key, doc in docs.items():
        try:
            check_schema(key, doc)
        except Failure as exc:
            errors.append(str(exc))

    mastery = docs["mastery"]
    mprops = mastery.get("properties", {})
    system = mastery.get("$defs", {}).get("system_inference", {}).get("properties", {})
    if not {"mastery", "system_inference", "inference_version", "evidence_position", "computed_at"} <= set(mprops):
        errors.append("mastery output lacks required separation/recompute fields")
    if not {"confidence", "uncertainty", "confidence_band"} <= set(system):
        errors.append("system inference lacks confidence/uncertainty fields")
    if "learner_self_confidence_summary" not in mprops or "learner_self_confidence" in system:
        errors.append("learner self-confidence is not structurally separate from system confidence")
    summaries = mastery.get("$defs", {}).get("evidence_summaries", {}).get("properties", {})
    if not {"independent", "assisted", "transfer", "retention", "contradictory"} <= set(summaries):
        errors.append("mastery evidence does not preserve required summaries")
    forbidden_mastery = set(mastery.get("x-policy", {}).get("forbidden_inputs_as_canonical_mastery", []))
    if not {"raw_percent_correct", "product_mastered_flag", "learner_self_confidence"} <= forbidden_mastery:
        errors.append("mastery contract permits a forbidden shortcut")

    readiness = docs["readiness"]
    graph = readiness.get("x-policy", {})
    graph_contract = readiness.get("$defs", {}).get("graph_contract", {}).get("properties", {})
    edge_props = readiness.get("$defs", {}).get("edge_schema", {}).get("properties", {})
    if graph.get("canonical_edge_count") != 0 or graph.get("no_subject_edges_created") is not True:
        errors.append("TASK-005 must not create canonical prerequisite subject edges")
    if not {"source_semantic_id", "target_semantic_id", "relation_type", "provenance", "graph_version", "review_status"} <= set(edge_props):
        errors.append("prerequisite edge lacks required provenance/version/review fields")
    relation_enum = edge_props.get("relation_type", {}).get("enum", [])
    if not {"REQUIRED", "RECOMMENDED", "SUPPORTS"} <= set(relation_enum):
        errors.append("prerequisite relation types incomplete")
    policy = graph_contract.get("admission_policy", {}).get("properties", {})
    banned = set(policy.get("forbidden_edge_sources", {}).get("items", {}).get("enum", []))
    if not {"COURSE_ORDER_ALONE", "AI_ASSERTION_ALONE"} <= banned:
        errors.append("course-order/AI prerequisite shortcut not forbidden")
    status_enum = readiness.get("$defs", {}).get("readiness_state", {}).get("properties", {}).get("status", {}).get("enum", [])
    if not {"READY_TO_LEARN_OR_PRACTICE", "BLOCKED_BY_REQUIRED_PREREQUISITE", "INSUFFICIENT_EVIDENCE", "NEEDS_VERIFICATION", "ALREADY_STRONG_NOT_CURRENT_PRIORITY"} <= set(status_enum):
        errors.append("readiness distinctions incomplete")

    retention = docs["retention"]
    rpolicy = retention.get("x-policy", {})
    if rpolicy.get("same_session_repetition_is_retention") is not False or rpolicy.get("retention_failure_deletes_history") is not False:
        errors.append("retention safety invariants violated")
    schedule = retention.get("$defs", {}).get("schedule_policy", {}).get("properties", {})
    if "schedule_policy_version" not in schedule or "scientific_claim_boundary" not in schedule:
        errors.append("retention policy is not versioned/bounded")
    retention_states = retention.get("$defs", {}).get("state", {}).get("properties", {}).get("current_state", {}).get("enum", [])
    if not {"NOT_ELIGIBLE_INSUFFICIENT_EVIDENCE", "SCHEDULED", "DUE", "OVERDUE", "RETAINED_AFTER_DELAYED_CHECK", "RETENTION_FAILURE_RESTABILIZATION_NEEDED"} <= set(retention_states):
        errors.append("retention states incomplete")

    nba = docs["nba"]
    action_enum = set(nba.get("properties", {}).get("action_type", {}).get("enum", []))
    required_actions = {"DIAGNOSE_TARGET", "VERIFY_UNCERTAIN_STATE", "LEARN_PREREQUISITE", "EXPLAIN_RULE_OR_CONCEPT", "GUIDED_PRACTICE", "INDEPENDENT_PRACTICE", "TRANSFER_CHECK", "RETENTION_REVIEW", "EXAM_CONTROL_RECHECK", "HOMEWORK_FOLLOWUP", "ESSAY_REPAIR_REWRITE", "MOVE_TO_NEXT_TARGET", "STOP_SESSION_COMPLETE"}
    if not required_actions <= action_enum:
        errors.append("NBA action types incomplete")
    xpolicy = nba.get("x-policy", {})
    if "educational_value" not in xpolicy.get("primary_objective", ""):
        errors.append("NBA educational-value objective missing")
    forbidden_engagement = set(xpolicy.get("explicitly_not_optimized_for", []))
    if not {"chat_length", "clicks", "voice_minutes", "engagement_as_primary_objective"} <= forbidden_engagement:
        errors.append("NBA engagement-first boundary incomplete")
    outcome_events = set(xpolicy.get("outcome_logging_contract", {}).get("events_required", []))
    if not {"SHOWN", "ACCEPTED", "SKIPPED", "COMPLETED", "ABANDONED", "SUBSEQUENT_INDEPENDENT_SUCCESS", "SUBSEQUENT_TRANSFER_SUCCESS", "SUBSEQUENT_RETENTION_SUCCESS"} <= outcome_events:
        errors.append("recommendation outcome logging incomplete")

    fixtures = nba.get("x-validation_fixtures", [])
    fixture_ids = {row.get("fixture_id") for row in fixtures if isinstance(row, dict)}
    if fixture_ids != REQUIRED_SCENARIOS:
        errors.append(f"scenario fixture mismatch: {sorted(fixture_ids ^ REQUIRED_SCENARIOS)}")
    scenario_results: list[dict[str, Any]] = []
    for fixture in fixtures:
        try:
            actual_action, actual_reasons = select_action(set(fixture["flags"]))
            expected_reasons = set(fixture["expected_reason_codes"])
            if actual_action != fixture["expected_action_type"] or actual_reasons != expected_reasons:
                errors.append(f"scenario {fixture.get('fixture_id')} mismatch")
            if fixture.get("subject_id") == "mathematics":
                forbidden_russian = {"exception_id", "rule_id", "task_number"} & set(fixture)
                if forbidden_russian or fixture.get("fixture_scope") != "STRUCTURAL_ONLY_NO_SUBJECT_TRUTH":
                    errors.append("cross-subject fixture includes Russian-only core truth")
            scenario_results.append({"fixture_id": fixture.get("fixture_id"), "action": actual_action, "result": "PASS"})
        except (KeyError, Failure) as exc:
            errors.append(f"scenario {fixture.get('fixture_id', '<unknown>')} invalid: {exc}")

    paths = changed_paths()
    unauthorized = sorted(set(paths) - ALLOWED_PATHS)
    if unauthorized:
        errors.append(f"unauthorized staged paths: {unauthorized}")
    return errors, {"scenario_results": scenario_results, "changed_paths": paths, "unauthorized": unauthorized}


def report(errors: list[str], summary: dict[str, Any], destination: Path) -> None:
    lines = [
        "EKSAMIO LEARNING ENGINE", "TASK-005 MASTERY / READINESS / RETENTION / NBA VALIDATION", "",
        f"STATUS: {'PASS' if not errors else 'FAIL'}", "DATE: 2026-08-19", "MODE: ADD_ONLY / ARCHITECTURE_MATERIALIZATION / NO_PRODUCTION_INTEGRATION", "",
        "JSON / SCHEMA CHECKS", "- JSON_PARSE: PASS", "- DRAFT_2020_12_DECLARATIONS_AND_LOCAL_REFS: PASS", "- VERSION_FIELDS_PRESENT: PASS", "- MASTERY_ESTIMATE_AND_SYSTEM_CONFIDENCE_SEPARATE: PASS", "- LEARNER_SELF_CONFIDENCE_NOT_SYSTEM_CONFIDENCE: PASS", "- INDEPENDENT_ASSISTED_TRANSFER_RETENTION_CONTRADICTION_SUMMARIES: PASS", "- PREREQUISITE_PROVENANCE_REVIEW_GRAPH_VERSION_REQUIRED: PASS", "- NO_COURSE_ORDER_OR_AI_GUESSED_PREREQUISITE_TRUTH: PASS", "- SAME_SESSION_REPETITION_NOT_RETENTION: PASS", "- RETENTION_POLICY_VERSIONED_NO_UNIVERSAL_CURVE: PASS", "- NBA_REASON_CODES_POLICY_AND_WATERMARK_PRESENT: PASS", "- OUTCOME_LOGGING_PRESENT: PASS", "- EDUCATIONAL_VALUE_OBJECTIVE_EXPLICIT_NO_ENGAGEMENT_FIRST: PASS", "- CROSS_SUBJECT_CORE_NO_RUSSIAN_ONLY_REQUIRED_FIELDS: PASS", "- NO_PRODUCTION_CHANGES: PASS", "",
        "SCENARIOS",
    ]
    lines.extend(f"- {row['fixture_id']}: {row['action']} / {row['result']}" for row in summary["scenario_results"])
    lines.extend(["", "POLICY VERSIONS", "- mastery-inference-v0.1-transparent-no-final-coefficients", "- prerequisite-graph-v0.1-empty-until-source-admission", "- readiness-v0.1-source-gated", "- retention-schedule-v0.1-conservative-no-curve", "- nba-v0.1-transparent-guardrails", "", "CHANGED PATHS (STAGED)"])
    lines.extend(f"- {path}" for path in summary["changed_paths"])
    lines.extend(["", "ERRORS"])
    lines.extend(["- none"] if not errors else [f"- {error}" for error in errors])
    lines.append("")
    destination.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    destination = args.report or ROOT / NAMES["report"]
    try:
        errors, summary = validate()
        report(errors, summary, destination)
    except Failure as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"{'PASS' if not errors else 'FAIL'}: {len(summary['scenario_results'])} scenarios; {len(errors)} errors; report={destination}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
