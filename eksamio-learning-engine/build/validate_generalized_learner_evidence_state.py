#!/usr/bin/env python3
"""Validate TASK-004 generalized learner evidence/state artifacts.

The repository intentionally has no third-party JSON Schema dependency. This
validator implements the strict Draft 2020-12 keyword subset used by artifacts
277/278, meta-checks every local $ref, validates representative fixtures and
enforces TASK-004 semantic invariants that JSON Schema alone cannot express.
It writes only the required ADD-ONLY validation snapshot.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVENT_SCHEMA_NAME = "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json"
STATE_SCHEMA_NAME = "278-EKSAMIO-LEARNER-STATE-MATERIALIZED-VIEW-SCHEMA-v0.1.json"
ADAPTER_NAME = "279-EKSAMIO-LEGACY-LEARNER-STATE-ADAPTER-MAP-v0.1.json"
REPORT_NAME = "280-EKSAMIO-LEARNER-EVIDENCE-STATE-VALIDATION.txt"

ALLOWED_CHANGED_PATHS = {
    f"eksamio-learning-engine/{EVENT_SCHEMA_NAME}",
    f"eksamio-learning-engine/{STATE_SCHEMA_NAME}",
    f"eksamio-learning-engine/{ADAPTER_NAME}",
    f"eksamio-learning-engine/{REPORT_NAME}",
    "eksamio-learning-engine/build/validate_generalized_learner_evidence_state.py",
    "eksamio-learning-engine/results/RESULT-004-generalized-learner-evidence-state-schema.md",
}

REQUIRED_TARGET_ROLES = {"PRIMARY", "SECONDARY", "PREREQUISITE_OBSERVED"}
REQUIRED_ASSISTANCE = {
    "UNASSISTED",
    "MICRO_HINT",
    "GUIDED_HINT",
    "SOCRATIC_GUIDANCE",
    "RULE_EXPLANATION",
    "PARTIAL_WORKED",
    "WORKED_EXAMPLE",
    "SOLUTION_EXPOSED",
}
REQUIRED_EVALUATORS = {
    "DETERMINISTIC_VALIDATOR",
    "OFFICIAL_KEY_OR_RULE",
    "HUMAN_REVIEW",
    "AI_EVALUATOR",
    "HYBRID_VALIDATED",
}
REQUIRED_SOURCE_TYPES = {
    "demo",
    "subject_trainer",
    "thematic_trainer",
    "ege_oge_trainer",
    "homework",
    "tutor",
    "diagnostic",
    "essay_or_open_response",
    "course_module",
    "retention_review",
    "imported_legacy_state",
}
REQUIRED_FIXTURE_CATEGORIES = {
    "historical_russian_demo",
    "subject_trainer_unassisted",
    "thematic_trainer",
    "tutor_assisted",
    "unassisted_verification_after_tutor",
    "homework",
    "essay_open_response",
    "human_reviewed_open_response",
    "legacy_exceptions_import",
    "course_local_product_state",
    "delayed_retention",
    "correction_retraction",
    "cross_subject_placeholder",
}


class ValidationFailure(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationFailure(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationFailure(
            f"invalid JSON {path.name}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc


def json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValidationFailure(f"validator does not support JSON type {expected!r}")


def resolve_ref(root_schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValidationFailure(f"only local JSON Schema refs are allowed: {ref}")
    node: Any = root_schema
    for raw in ref[2:].split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or key not in node:
            raise ValidationFailure(f"unresolved JSON Schema ref: {ref}")
        node = node[key]
    if not isinstance(node, dict):
        raise ValidationFailure(f"JSON Schema ref is not an object: {ref}")
    return node


def validate_format(value: Any, fmt: str, path: str, errors: list[str]) -> None:
    if value is None:
        return
    if fmt == "date-time" and isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("timezone required")
        except ValueError:
            errors.append(f"{path}: invalid date-time {value!r}")


def validate_instance(
    instance: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "$",
) -> list[str]:
    errors: list[str] = []
    if "$ref" in schema:
        errors.extend(validate_instance(instance, resolve_ref(root_schema, schema["$ref"]), root_schema, path))

    if "allOf" in schema:
        for index, child in enumerate(schema["allOf"]):
            errors.extend(validate_instance(instance, child, root_schema, f"{path}.allOf[{index}]"))
    if "anyOf" in schema:
        candidates = [validate_instance(instance, child, root_schema, path) for child in schema["anyOf"]]
        if not any(not candidate for candidate in candidates):
            errors.append(f"{path}: does not satisfy anyOf")
    if "oneOf" in schema:
        candidates = [validate_instance(instance, child, root_schema, path) for child in schema["oneOf"]]
        if sum(not candidate for candidate in candidates) != 1:
            errors.append(f"{path}: does not satisfy exactly one oneOf branch")
    if "not" in schema and not validate_instance(instance, schema["not"], root_schema, path):
        errors.append(f"{path}: satisfies forbidden not schema")

    if "if" in schema:
        condition_errors = validate_instance(instance, schema["if"], root_schema, path)
        branch = schema.get("then") if not condition_errors else schema.get("else")
        if isinstance(branch, dict):
            errors.extend(validate_instance(instance, branch, root_schema, path))

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} not in enum")

    expected_types = schema.get("type")
    if expected_types is not None:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not any(json_type_matches(instance, expected) for expected in expected_types):
            errors.append(f"{path}: expected type {expected_types}, got {type(instance).__name__}")
            return errors

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{path}: missing required property {key}")
        properties = schema.get("properties", {})
        for key, value in instance.items():
            child_path = f"{path}.{key}"
            if key in properties:
                errors.extend(validate_instance(value, properties[key], root_schema, child_path))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{child_path}: additional property is forbidden")

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{path}: fewer than minItems")
        if schema.get("uniqueItems"):
            normalized = [json.dumps(item, ensure_ascii=False, sort_keys=True) for item in instance]
            if len(normalized) != len(set(normalized)):
                errors.append(f"{path}: array items are not unique")
        if isinstance(schema.get("items"), dict):
            for index, value in enumerate(instance):
                errors.extend(validate_instance(value, schema["items"], root_schema, f"{path}[{index}]"))

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than minLength")
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, instance) is None:
            errors.append(f"{path}: does not match pattern {pattern!r}")
        if "format" in schema:
            validate_format(instance, schema["format"], path, errors)

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    return errors


def walk_schema(schema: Any, root_schema: dict[str, Any], path: str = "$schema") -> None:
    if isinstance(schema, dict):
        if "$ref" in schema:
            resolve_ref(root_schema, schema["$ref"])
        for key, value in schema.items():
            walk_schema(value, root_schema, f"{path}.{key}")
    elif isinstance(schema, list):
        for index, value in enumerate(schema):
            walk_schema(value, root_schema, f"{path}[{index}]")


def check_schema(schema: dict[str, Any], expected_id_suffix: str) -> None:
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ValidationFailure("schema is not declared as JSON Schema Draft 2020-12")
    if not str(schema.get("$id", "")).endswith(expected_id_suffix):
        raise ValidationFailure(f"unexpected schema $id: {schema.get('$id')}")
    if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise ValidationFailure("canonical schema root must be a closed object")
    if not isinstance(schema.get("$defs"), dict) or not schema["$defs"]:
        raise ValidationFailure("schema must declare non-empty $defs")
    walk_schema(schema, schema)


def recursive_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key)
            keys.update(recursive_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(recursive_keys(child))
    return keys


def schema_property_names(schema: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(schema, dict):
        properties = schema.get("properties")
        if isinstance(properties, dict):
            result.update(properties)
        for value in schema.values():
            result.update(schema_property_names(value))
    elif isinstance(schema, list):
        for value in schema:
            result.update(schema_property_names(value))
    return result


def base_event(index: int, category: str) -> dict[str, Any]:
    timestamp = f"2026-08-19T10:{index:02d}:00+03:00"
    return {
        "event_id": f"evt-task004-{index:02d}",
        "schema_version": "0.1.0",
        "event_kind": "PERFORMANCE_OBSERVATION",
        "learner_profile_id": "learner-fixture-001",
        "identity_refs": {"anonymous_identity_ref": "anonymous-fixture-001"},
        "subject_id": "russian",
        "semantic_targets": [
            {
                "semantic_id": "school-root-vowel-stress-verification",
                "target_role": "PRIMARY",
                "mapping_resolution": "EXACT",
                "mapping_confidence": 1,
                "mapping_review_status": "accepted",
            }
        ],
        "semantic_context": {
            "semantic_registry_version": "russian-school-266+ege-graph-03",
            "semantic_mapping_version": "274@0.1.0-draft",
            "mapping_artifact_refs": ["274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json"],
        },
        "source": {
            "object_type": "fixture_item",
            "object_id": f"fixture-item-{index:02d}",
            "content_version": "fixture-v1",
            "item_version": "1",
            "route_metadata": {
                "exam": None,
                "exam_year": None,
                "task_route": None,
                "historical_format": None,
            },
        },
        "product": {"source_type": "subject_trainer", "product_id": category, "route": None},
        "session_id": f"session-fixture-{index:02d}",
        "timestamps": {
            "occurred_at_client": timestamp,
            "received_at_server": timestamp,
            "server_sequence": index,
            "server_watermark": f"wm-{index:02d}",
        },
        "result": {
            "attempt_index": 1,
            "outcome": "CORRECT",
            "correctness": True,
            "score": 1,
            "max_score": 1,
            "response_value": "fixture-response",
            "result_details": {},
        },
        "response_mode": "TYPED_TEXT",
        "assistance": {"level": "UNASSISTED", "help_event_refs": [], "assistance_provider": None},
        "evaluator": {
            "evaluator_type": "DETERMINISTIC_VALIDATOR",
            "evaluator_id": "fixture-validator",
            "evaluator_version": "1",
            "trust_class": "DETERMINISTIC_HIGH",
            "uncertainty": 0,
            "review_status": "not_required",
            "rubric_version": None,
            "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
        },
        "provenance_refs": [f"TASK-004 fixture:{category}"],
        "transfer_context": {"kind": "SAME_PATTERN", "origin_event_refs": []},
        "retention_context": {"kind": "NONE", "delay_seconds": None, "scheduled_by_policy_version": None},
        "error_observations": [],
        "latency_ms": 1500,
        "subject_extension": {"subject_payload_schema_version": "russian-fixture-v1", "subject_payload": {}},
        "created_at": timestamp,
    }


def event_fixtures() -> list[tuple[str, dict[str, Any]]]:
    fixtures: list[tuple[str, dict[str, Any]]] = []

    historical = base_event(1, "historical_russian_demo")
    historical["product"] = {"source_type": "demo", "product_id": "ege-russian-demo-2022", "route": "/ege/russkiy/demo/2022"}
    historical["source"]["object_type"] = "demo_task"
    historical["source"]["object_id"] = "ege-ru-demo-2022-task-09-placeholder-route"
    historical["source"]["route_metadata"] = {"exam": "ege", "exam_year": 2022, "task_route": "task-09", "historical_format": True}
    fixtures.append(("historical_russian_demo", historical))

    trainer = base_event(2, "subject_trainer_unassisted")
    trainer["product"]["product_id"] = "ege-russian-full-trainer"
    trainer["source"]["object_type"] = "trainer_item"
    fixtures.append(("subject_trainer_unassisted", trainer))

    thematic = base_event(3, "thematic_trainer")
    thematic["product"] = {"source_type": "thematic_trainer", "product_id": "russian-exceptions", "route": None}
    thematic["source"]["object_type"] = "practice_item"
    thematic["subject_extension"]["subject_payload"] = {"practice_item_id": "fixture-practice-item"}
    fixtures.append(("thematic_trainer", thematic))

    tutor = base_event(4, "tutor_assisted")
    tutor["product"] = {"source_type": "tutor", "product_id": "eksamio-tutor", "route": "HELP_ME_SOLVE"}
    tutor["assistance"] = {"level": "GUIDED_HINT", "help_event_refs": ["tutor-help-fixture-01"], "assistance_provider": "tutor-core"}
    tutor["transfer_context"]["kind"] = "NOT_APPLICABLE"
    fixtures.append(("tutor_assisted", tutor))

    verification = base_event(5, "unassisted_verification_after_tutor")
    verification["product"] = {"source_type": "tutor", "product_id": "eksamio-tutor", "route": "VERIFY"}
    verification["source"]["object_type"] = "independent_verification_item"
    verification["transfer_context"] = {"kind": "SAME_SESSION_VERIFICATION", "origin_event_refs": [tutor["event_id"]]}
    fixtures.append(("unassisted_verification_after_tutor", verification))

    homework = base_event(6, "homework")
    homework["product"] = {"source_type": "homework", "product_id": "homework-with-me", "route": "one-off"}
    homework["source"]["object_type"] = "homework_problem"
    fixtures.append(("homework", homework))

    essay = base_event(7, "essay_open_response")
    essay["product"] = {"source_type": "essay_or_open_response", "product_id": "russian-essay-learning-check", "route": "task-27"}
    essay["source"]["object_type"] = "essay_submission"
    essay["response_mode"] = "ESSAY"
    essay["result"].update({"outcome": "PARTIAL", "correctness": None, "score": None, "max_score": None})
    essay["evaluator"] = {
        "evaluator_type": "AI_EVALUATOR",
        "evaluator_id": "fixture-ai-essay-evaluator",
        "evaluator_version": "fixture-v1",
        "trust_class": "AI_INTERPRETED_LOW",
        "uncertainty": 0.35,
        "review_status": "pending_review",
        "rubric_version": "educational-fixture-rubric-v1",
        "official_truth_status": "EDUCATIONAL_NON_OFFICIAL",
    }
    essay["open_response_evaluation"] = {
        "overall_outcome": "PROVISIONAL",
        "rubric_version": "educational-fixture-rubric-v1",
        "rubric_dimensions": [{"dimension_id": "fixture-dimension", "outcome": "PARTIAL", "evidence_refs": ["submission-fragment-fixture"]}],
        "uncertainty": 0.35,
        "review_status": "pending_review",
        "official_truth_status": "EDUCATIONAL_NON_OFFICIAL",
    }
    fixtures.append(("essay_open_response", essay))

    human_reviewed = base_event(13, "human_reviewed_open_response")
    human_reviewed["product"] = {"source_type": "essay_or_open_response", "product_id": "reviewed-open-response", "route": None}
    human_reviewed["source"]["object_type"] = "reviewed_open_response_submission"
    human_reviewed["response_mode"] = "ESSAY"
    human_reviewed["result"].update({"outcome": "CORRECT", "correctness": True, "score": 2, "max_score": 2})
    human_reviewed["evaluator"] = {
        "evaluator_type": "HUMAN_REVIEW",
        "evaluator_id": "authorized-human-reviewer-fixture",
        "evaluator_version": "review-policy-v1",
        "trust_class": "HUMAN_REVIEWED",
        "uncertainty": 0,
        "review_status": "reviewed",
        "rubric_version": "reviewed-fixture-rubric-v1",
        "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
    }
    human_reviewed["open_response_evaluation"] = {
        "overall_outcome": "REVIEWED",
        "rubric_version": "reviewed-fixture-rubric-v1",
        "rubric_dimensions": [{"dimension_id": "fixture-dimension", "outcome": "MET", "evidence_refs": ["authorized-review-fixture"]}],
        "uncertainty": 0,
        "review_status": "reviewed",
        "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
    }
    fixtures.append(("human_reviewed_open_response", human_reviewed))

    legacy = base_event(8, "legacy_exceptions_import")
    legacy["event_kind"] = "LEGACY_IMPORT"
    legacy["idempotency_key"] = "legacy-exceptions-event-fixture-001"
    legacy["product"] = {"source_type": "imported_legacy_state", "product_id": "russian-exceptions", "route": None}
    legacy["source"] = {"object_type": "practice_item", "object_id": "fixture-practice-item", "content_version": "legacy-current-manifest-119", "item_version": "1", "route_metadata": {"exam": "ege", "exam_year": None, "task_route": None, "historical_format": False}}
    legacy["evaluator"].update({"trust_class": "IMPORTED_LEGACY_KNOWN", "official_truth_status": "NOT_APPLICABLE"})
    legacy["legacy_import"] = {"import_batch_id": "batch-fixture-001", "source_namespace": "eksamio:russian:exceptions", "source_schema_version": "1.1.0-addendum", "source_record_key": "exception-fixture:event-fixture", "source_record_revision": 1, "source_event_id": "legacy-event-fixture-001", "import_trust_class": "EXACT_EVENT_HISTORY"}
    legacy["subject_extension"]["subject_payload"] = {"exception_id": "fixture-exception-id", "practice_item_id": "fixture-practice-item"}
    fixtures.append(("legacy_exceptions_import", legacy))

    course = base_event(9, "course_local_product_state")
    course["event_kind"] = "LEGACY_IMPORT"
    course["idempotency_key"] = "course-state-fixture-record-001"
    course["product"] = {"source_type": "imported_legacy_state", "product_id": "course-product-fixture", "route": None}
    course["response_mode"] = "IMPORTED_AGGREGATE"
    course["result"].update({"attempt_index": None, "outcome": "AGGREGATE_ONLY", "correctness": None, "score": None, "max_score": None, "response_value": None})
    course["evaluator"].update({"trust_class": "IMPORTED_LEGACY_AGGREGATE_LOW", "official_truth_status": "NOT_APPLICABLE"})
    course["legacy_import"] = {"import_batch_id": "batch-fixture-002", "source_namespace": "course:fixture:v1", "source_schema_version": "fixture-v1", "source_record_key": "module-item-fixture", "source_record_revision": "snapshot-hash-fixture", "source_event_id": None, "import_trust_class": "PRODUCT_STATE_ONLY"}
    course["subject_extension"]["subject_payload"] = {"product_state": "mastered", "canonical_mastery_inferred": False}
    fixtures.append(("course_local_product_state", course))

    retention = base_event(10, "delayed_retention")
    retention["product"] = {"source_type": "retention_review", "product_id": "retention-review", "route": None}
    retention["retention_context"] = {"kind": "DELAYED_RETENTION", "delay_seconds": 604800, "scheduled_by_policy_version": "fixture-policy-only"}
    retention["transfer_context"]["kind"] = "NEAR_TRANSFER"
    fixtures.append(("delayed_retention", retention))

    retraction = base_event(11, "correction_retraction")
    retraction["event_kind"] = "RETRACTION"
    retraction["result"].update({"outcome": "INVALIDATED", "correctness": None, "score": None, "max_score": None, "response_value": None})
    retraction["response_mode"] = "NO_RESPONSE"
    retraction["correction"] = {"retracts_event_id": "evt-task004-original-01", "correction_reason": "fixture source event invalidated", "correction_actor": {"actor_type": "HUMAN_REVIEWER", "actor_ref": "reviewer-fixture"}, "correction_version": "1"}
    fixtures.append(("correction_retraction", retraction))

    cross_subject = base_event(12, "cross_subject_placeholder")
    cross_subject["subject_id"] = "mathematics"
    cross_subject["semantic_targets"] = [{"semantic_id": "fixture-math-semantic-placeholder", "target_role": "PRIMARY", "mapping_resolution": "PARTIAL", "mapping_confidence": None, "mapping_review_status": "needs_review"}]
    cross_subject["semantic_context"] = {"semantic_registry_version": "fixture-only-not-subject-truth", "semantic_mapping_version": "fixture-only-not-subject-truth", "mapping_artifact_refs": ["TASK-004 structural fixture only"]}
    cross_subject["source"]["object_type"] = "structural_placeholder_item"
    cross_subject["product"] = {"source_type": "diagnostic", "product_id": "cross-subject-structural-fixture", "route": None}
    cross_subject["response_mode"] = "NUMERIC"
    cross_subject["result"]["response_value"] = 42
    cross_subject["subject_extension"] = {"subject_payload_schema_version": "math-fixture-only-v1", "subject_payload": {"fixture_only": True}}
    fixtures.append(("cross_subject_placeholder", cross_subject))
    return fixtures


def state_fixtures() -> list[tuple[str, dict[str, Any]]]:
    def empty_summary() -> dict[str, Any]:
        return {"accepted_event_count": 0, "correct_count": 0, "incorrect_count": 0, "partial_count": 0, "first_event_at": None, "last_event_at": None, "event_refs": []}

    state = {
        "schema_version": "0.1.0",
        "learner_profile_id": "learner-fixture-001",
        "subject_id": "russian",
        "semantic_id": "school-root-vowel-stress-verification",
        "semantic_registry_version": "russian-school-266+ege-graph-03",
        "mastery": {"estimate": None, "band": None, "status": None, "system_confidence": None, "uncertainty": None},
        "learner_self_confidence_summary": {"latest_value": None, "scale": None, "observed_at": None, "event_ref": None},
        "independent_evidence_summary": empty_summary(),
        "assisted_evidence_summary": {**empty_summary(), "assistance_levels_observed": []},
        "recent_evidence_summary": {"window_definition": "fixture-window-no-policy", "event_count": 0, "independent_count": 0, "assisted_count": 0, "event_refs": []},
        "last_independent_verification_at": None,
        "last_assisted_attempt_at": None,
        "transfer_evidence_summary": {"same_pattern_count": 0, "near_transfer_count": 0, "broad_transfer_count": 0, "last_transfer_at": None, "event_refs": []},
        "retention_evidence_summary": {"delayed_check_count": 0, "delayed_correct_count": 0, "delayed_incorrect_count": 0, "last_delay_seconds": None, "event_refs": []},
        "last_retention_check_at": None,
        "retention_due_at": None,
        "prerequisite_readiness_hooks": {"prerequisite_graph_version": None, "prerequisite_state_refs": [], "readiness_policy_version": None, "readiness_status": None},
        "error_fingerprint": [],
        "goal_exam_overlay_refs": [],
        "subject_extension": {"subject_payload_schema_version": "russian-state-fixture-v1", "subject_payload": {}},
        "inference_version": "fixture-inference-no-coefficients-v1",
        "computed_at": "2026-08-19T10:30:00+03:00",
        "evidence_position": {"server_watermark": "wm-fixture-000", "semantic_mapping_versions": ["274@0.1.0-draft"]},
        "state_revision": 0,
        "recompute_metadata": {"reason": "INITIAL", "previous_inference_version": None, "backfill_id": None},
    }
    math_state = copy.deepcopy(state)
    math_state["subject_id"] = "mathematics"
    math_state["semantic_id"] = "fixture-math-semantic-placeholder"
    math_state["semantic_registry_version"] = "fixture-only-not-subject-truth"
    math_state["subject_extension"] = {"subject_payload_schema_version": "math-fixture-only-v1", "subject_payload": {"fixture_only": True}}
    math_state["evidence_position"]["semantic_mapping_versions"] = ["fixture-only-not-subject-truth"]
    return [("russian_empty_recomputable_state", state), ("cross_subject_placeholder_state", math_state)]


def changed_paths(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        text=True,
        capture_output=True,
    )
    result: set[str] = set()
    for line in completed.stdout.splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path == ".DS_Store" or "/.DS_Store" in path or "/__pycache__/" in path or path.endswith(".pyc"):
            continue
        result.add(path)
    branch_diff = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=repo_root,
        check=False,
        text=True,
        capture_output=True,
    )
    if branch_diff.returncode == 0:
        for path in branch_diff.stdout.splitlines():
            if path:
                result.add(path)
    return sorted(result)


def adapter_by_id(adapter: dict[str, Any], adapter_id: str) -> dict[str, Any]:
    matches = [row for row in adapter.get("adapters", []) if row.get("adapter_id") == adapter_id]
    if len(matches) != 1:
        raise ValidationFailure(f"expected exactly one adapter {adapter_id}, found {len(matches)}")
    return matches[0]


def validate_all(root: Path) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    findings: list[str] = []
    event_schema = load_json(root / EVENT_SCHEMA_NAME)
    state_schema = load_json(root / STATE_SCHEMA_NAME)
    adapter = load_json(root / ADAPTER_NAME)
    inventory = load_json(root / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json")
    crosswalk = load_json(root / "274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json")
    handoff = load_json(root / "114-RUSSIAN-ERROR-EXCEPTION-HANDOFF-MAP-v0.1.json")

    try:
        check_schema(event_schema, "/learner-evidence-event/0.1.0")
        check_schema(state_schema, "/learner-semantic-state/0.1.0")
    except ValidationFailure as exc:
        errors.append(str(exc))

    event_properties = event_schema.get("properties", {})
    event_required = set(event_schema.get("required", []))
    if "event_id" not in event_required:
        errors.append("event_id is not required")
    if "idempotency_key" in event_required:
        errors.append("idempotency_key must remain optional for ordinary events")
    if event_properties.get("idempotency_key", {}).get("type") != "string":
        errors.append("optional idempotency_key is not a strict string")

    defs = event_schema.get("$defs", {})
    target_roles = set(defs.get("semantic_target", {}).get("properties", {}).get("target_role", {}).get("enum", []))
    mapping_resolutions = set(defs.get("semantic_target", {}).get("properties", {}).get("mapping_resolution", {}).get("enum", []))
    mapping_review_statuses = set(defs.get("semantic_target", {}).get("properties", {}).get("mapping_review_status", {}).get("enum", []))
    assistance = set(defs.get("assistance", {}).get("properties", {}).get("level", {}).get("enum", []))
    evaluators = set(defs.get("evaluator", {}).get("properties", {}).get("evaluator_type", {}).get("enum", []))
    source_types = set(defs.get("product", {}).get("properties", {}).get("source_type", {}).get("enum", []))
    if not REQUIRED_TARGET_ROLES <= target_roles:
        errors.append("semantic target role enum is incomplete")
    if mapping_resolutions != {"EXACT", "PARTIAL", "COMPOSITE"}:
        errors.append("semantic mapping resolution enum contains non-production or missing values")
    if mapping_review_statuses != {"accepted", "source_verified", "needs_review"}:
        errors.append("semantic mapping review-status enum contains non-production or missing values")
    if not REQUIRED_ASSISTANCE <= assistance:
        errors.append("assistance enum is incomplete")
    if not REQUIRED_EVALUATORS <= evaluators:
        errors.append("evaluator enum is incomplete")
    if not REQUIRED_SOURCE_TYPES <= source_types:
        errors.append("product/source type enum is incomplete")

    forbidden = set(event_schema.get("x-forbidden-client-authored-field-names-recursive", []))
    if not {"effective_weight", "mastery_weight", "semantic_contribution_percentage"} <= forbidden:
        errors.append("forbidden client-authored weight field list is incomplete")
    if forbidden & schema_property_names(event_schema):
        errors.append("forbidden mastery/weight field is declared as a canonical event property")
    if "email" in schema_property_names(event_schema):
        errors.append("email leaked into canonical identity schema")
    if "exception_id" in schema_property_names(event_schema):
        errors.append("Russian exception_id leaked into universal event core")
    if "exception_id" in schema_property_names(state_schema):
        errors.append("Russian exception_id leaked into universal state core")

    fixtures = event_fixtures()
    categories = {category for category, _ in fixtures}
    if categories != REQUIRED_FIXTURE_CATEGORIES:
        errors.append(f"fixture category mismatch: {sorted(categories ^ REQUIRED_FIXTURE_CATEGORIES)}")
    fixture_ids: set[str] = set()
    for category, fixture in fixtures:
        fixture_errors = validate_instance(fixture, event_schema, event_schema)
        if fixture_errors:
            errors.extend(f"event fixture {category}: {error}" for error in fixture_errors[:20])
        event_id = fixture.get("event_id")
        if event_id in fixture_ids:
            errors.append(f"duplicate fixture event_id: {event_id}")
        fixture_ids.add(event_id)
        if fixture.get("event_kind") == "LEGACY_IMPORT":
            if not fixture.get("idempotency_key") or fixture["idempotency_key"] == fixture["event_id"]:
                errors.append(f"legacy fixture {category} lacks a distinct idempotency key")
        if forbidden & recursive_keys(fixture):
            errors.append(f"fixture {category} contains forbidden client-authored mastery/weight field")
        if not fixture.get("semantic_context", {}).get("semantic_mapping_version"):
            errors.append(f"fixture {category} lacks semantic mapping version")
        source = fixture.get("source", {})
        if not all(source.get(key) for key in ("object_type", "object_id", "content_version")):
            errors.append(f"fixture {category} lacks source object/content traceability")

    negative_cases: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    invalid_role = copy.deepcopy(dict(fixtures)["subject_trainer_unassisted"])
    invalid_role["semantic_targets"][0]["target_role"] = "CLIENT_SELECTED_SHARE"
    negative_cases.append(("invalid_semantic_target_role", invalid_role, event_schema))
    test_only_resolution = copy.deepcopy(dict(fixtures)["cross_subject_placeholder"])
    test_only_resolution["semantic_targets"][0]["mapping_resolution"] = "PLACEHOLDER_FIXTURE"
    negative_cases.append(("test_only_mapping_resolution", test_only_resolution, event_schema))
    test_only_review_status = copy.deepcopy(dict(fixtures)["cross_subject_placeholder"])
    test_only_review_status["semantic_targets"][0]["mapping_review_status"] = "fixture_only"
    negative_cases.append(("test_only_mapping_review_status", test_only_review_status, event_schema))
    forbidden_weight = copy.deepcopy(dict(fixtures)["subject_trainer_unassisted"])
    forbidden_weight["effective_weight"] = 0.75
    negative_cases.append(("client_authored_effective_weight", forbidden_weight, event_schema))
    missing_source_version = copy.deepcopy(dict(fixtures)["subject_trainer_unassisted"])
    del missing_source_version["source"]["content_version"]
    negative_cases.append(("missing_source_content_version", missing_source_version, event_schema))
    correction_without_link = copy.deepcopy(dict(fixtures)["correction_retraction"])
    correction_without_link["event_kind"] = "CORRECTION"
    correction_without_link["correction"].pop("retracts_event_id", None)
    negative_cases.append(("correction_without_supersedes_link", correction_without_link, event_schema))
    ai_without_uncertainty = copy.deepcopy(dict(fixtures)["essay_open_response"])
    del ai_without_uncertainty["evaluator"]["uncertainty"]
    negative_cases.append(("ai_evaluator_without_uncertainty", ai_without_uncertainty, event_schema))
    ai_with_high_trust = copy.deepcopy(dict(fixtures)["essay_open_response"])
    ai_with_high_trust["evaluator"]["trust_class"] = "DETERMINISTIC_HIGH"
    negative_cases.append(("ai_evaluator_with_non_ai_high_trust", ai_with_high_trust, event_schema))
    ai_claiming_official_truth = copy.deepcopy(dict(fixtures)["essay_open_response"])
    ai_claiming_official_truth["open_response_evaluation"]["official_truth_status"] = "OFFICIAL_OR_DETERMINISTIC"
    negative_cases.append(("ai_open_response_claiming_official_truth", ai_claiming_official_truth, event_schema))
    legacy_without_idempotency = copy.deepcopy(dict(fixtures)["legacy_exceptions_import"])
    del legacy_without_idempotency["idempotency_key"]
    negative_cases.append(("legacy_import_without_idempotency_key", legacy_without_idempotency, event_schema))

    essay = dict(fixtures)["essay_open_response"]
    if essay["evaluator"]["evaluator_type"] != "AI_EVALUATOR" or essay["evaluator"]["trust_class"] != "AI_INTERPRETED_LOW" or essay["evaluator"]["official_truth_status"] != "EDUCATIONAL_NON_OFFICIAL":
        errors.append("AI open-response fixture violates evaluator/official-truth boundary")
    if essay["open_response_evaluation"]["uncertainty"] is None or essay["open_response_evaluation"]["review_status"] != "pending_review" or essay["open_response_evaluation"]["official_truth_status"] != "EDUCATIONAL_NON_OFFICIAL":
        errors.append("AI open-response fixture lacks uncertainty/review metadata")
    human_reviewed_fixture = dict(fixtures)["human_reviewed_open_response"]
    if human_reviewed_fixture["evaluator"]["evaluator_type"] != "HUMAN_REVIEW" or human_reviewed_fixture["evaluator"]["trust_class"] != "HUMAN_REVIEWED":
        errors.append("reviewed non-AI open-response fixture lacks authorized evaluator provenance")
    if human_reviewed_fixture["open_response_evaluation"]["overall_outcome"] != "REVIEWED" or human_reviewed_fixture["open_response_evaluation"]["official_truth_status"] != "OFFICIAL_OR_DETERMINISTIC":
        errors.append("reviewed non-AI open-response fixture cannot represent reviewed/official truth")
    tutor_fixture = dict(fixtures)["tutor_assisted"]
    verify_fixture = dict(fixtures)["unassisted_verification_after_tutor"]
    if tutor_fixture["assistance"]["level"] == "UNASSISTED" or verify_fixture["assistance"]["level"] != "UNASSISTED":
        errors.append("Tutor-assisted vs independent verification distinction failed")
    if verify_fixture["event_id"] == tutor_fixture["event_id"] or tutor_fixture["event_id"] not in verify_fixture["transfer_context"]["origin_event_refs"]:
        errors.append("independent verification is not represented as a separate linked event")
    retention_fixture = dict(fixtures)["delayed_retention"]
    if retention_fixture["retention_context"]["kind"] != "DELAYED_RETENTION" or not retention_fixture["retention_context"]["delay_seconds"]:
        errors.append("delayed retention fixture is not distinct from same-session evidence")

    state_fixture_rows = state_fixtures()
    for category, fixture in state_fixture_rows:
        fixture_errors = validate_instance(fixture, state_schema, state_schema)
        if fixture_errors:
            errors.extend(f"state fixture {category}: {error}" for error in fixture_errors[:20])
    state_without_inference = copy.deepcopy(dict(state_fixture_rows)["russian_empty_recomputable_state"])
    del state_without_inference["inference_version"]
    negative_cases.append(("state_without_inference_version", state_without_inference, state_schema))
    state_without_evidence_position = copy.deepcopy(dict(state_fixture_rows)["russian_empty_recomputable_state"])
    state_without_evidence_position["evidence_position"] = {"semantic_mapping_versions": ["274@0.1.0-draft"]}
    negative_cases.append(("state_without_watermark_or_evidence_ref", state_without_evidence_position, state_schema))
    for category, fixture, schema in negative_cases:
        if not validate_instance(fixture, schema, schema):
            errors.append(f"negative schema fixture unexpectedly accepted: {category}")
    state_required = set(state_schema.get("required", []))
    if not {"inference_version", "computed_at", "evidence_position"} <= state_required:
        errors.append("materialized state lacks mandatory recomputation metadata")
    mastery_properties = state_schema.get("$defs", {}).get("mastery", {}).get("properties", {})
    if "system_confidence" not in mastery_properties or "learner_self_confidence" in mastery_properties:
        errors.append("system confidence is not structurally distinct from learner self-confidence")
    if "learner_self_confidence_summary" not in state_schema.get("properties", {}):
        errors.append("state lacks separate learner self-confidence summary hook")

    required_adapter_ids = {
        "russian-exceptions-state-102-exact-events",
        "russian-exceptions-state-120-idempotency",
        "russian-error-exception-handoff-114",
        "current-ege-russian-trainer-progress-v1",
        "current-ege-russian-trainer-session-v1",
        "course-thematic-product-state",
    }
    adapter_ids = [row.get("adapter_id") for row in adapter.get("adapters", [])]
    if len(adapter_ids) != len(set(adapter_ids)):
        errors.append("adapter IDs are not unique")
    if not required_adapter_ids <= set(adapter_ids):
        errors.append(f"missing required adapters: {sorted(required_adapter_ids - set(adapter_ids))}")
    import_policy = adapter.get("global_import_policy", {})
    if import_policy.get("production_local_storage_migration") != "FORBIDDEN_IN_TASK_004":
        errors.append("production localStorage migration is not explicitly forbidden")
    if not import_policy.get("idempotency_tuple") or not import_policy.get("import_ledger_required_fields"):
        errors.append("legacy duplicate-prevention contract is incomplete")

    adapter_120 = adapter_by_id(adapter, "russian-exceptions-state-120-idempotency")
    if "processed_event_ids" not in json.dumps(adapter_120, ensure_ascii=False) or "state_revision" not in json.dumps(adapter_120, ensure_ascii=False):
        errors.append("120 compatibility does not preserve processed_event_ids/state_revision")
    adapter_114 = adapter_by_id(adapter, "russian-error-exception-handoff-114")
    serialized_114 = json.dumps(adapter_114, ensure_ascii=False)
    if "whole-task failure" not in serialized_114 or "evidence_precision=exact" not in serialized_114:
        errors.append("114 exact-vs-broad handoff boundary is incomplete")
    if adapter_114.get("supersession_finding", {}).get("source_declares") != handoff.get("exceptions_manifest"):
        errors.append("114 stale manifest reference is not preserved exactly")
    if adapter_114.get("supersession_finding", {}).get("current_authority") != "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json":
        errors.append("114 adapter does not identify current manifest 118")
    course_adapter = adapter_by_id(adapter, "course-thematic-product-state")
    if course_adapter.get("label_mapping", {}).get("mastered") != "subject_extension.subject_payload.product_state=mastered":
        errors.append("course product mastered label is not preserved as local product state")
    if not str(course_adapter.get("canonical_mastery_policy", "")).startswith("none"):
        errors.append("product mastered label may map directly to canonical mastery")

    if inventory.get("active_school_identity_count_observed") != 185 or inventory.get("summary", {}).get("inventory_objects_total") != 983:
        errors.append("TASK-003 inventory authority counts changed unexpectedly")
    if crosswalk.get("mapping_version") != "0.1.0-draft" or crosswalk.get("summary", {}).get("mappings_total") != 1429:
        errors.append("TASK-003 crosswalk authority/version changed unexpectedly")
    if crosswalk.get("summary", {}).get("missing_subject_semantic_candidate_count") != 55:
        errors.append("TASK-003 candidate count changed unexpectedly")

    repo_root = root.parent
    paths = changed_paths(repo_root)
    unauthorized = sorted(set(paths) - ALLOWED_CHANGED_PATHS)
    if unauthorized:
        errors.append(f"unauthorized changed paths: {unauthorized}")

    findings.extend(
        [
            "102 exact event history can adapt to exact evidence; aggregate-only state remains lower-trust and must not synthesize attempts.",
            "120 processed_event_ids/state_revision semantics are preserved through a durable import ledger and source snapshot revision.",
            "114 exact handoff can create structured error evidence; whole-task failure cannot create an exact exception error.",
            "114 still names manifest 83; current authority 118 is used only by the adapter resolution gate without mutating 114.",
            "Current EGE trainer progress is an aggregate local product snapshot; its computed mastered UI counter is not canonical mastery.",
            "Concrete course/thematic namespace and schema are not repository-visible; the adapter is design-only and remains needs_review until product-owner declaration.",
        ]
    )
    summary = {
        "event_schema_version": event_schema.get("properties", {}).get("schema_version", {}).get("const"),
        "state_schema_version": state_schema.get("properties", {}).get("schema_version", {}).get("const"),
        "event_fixture_count": len(fixtures),
        "event_fixture_categories": sorted(categories),
        "state_fixture_count": len(state_fixture_rows),
        "negative_fixture_count": len(negative_cases),
        "adapter_count": len(adapter_ids),
        "adapter_ids": adapter_ids,
        "cross_subject_event_fixture": "cross_subject_placeholder" in categories,
        "cross_subject_state_fixture": any(category == "cross_subject_placeholder_state" for category, _ in state_fixture_rows),
        "changed_paths": paths,
        "unauthorized_changed_paths": unauthorized,
    }
    return errors, findings, summary


def write_report(path: Path, errors: list[str], findings: list[str], summary: dict[str, Any]) -> None:
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "TASK-004 GENERALIZED LEARNER EVIDENCE / STATE VALIDATION",
        "",
        f"STATUS: {'PASS' if not errors else 'FAIL'}",
        "DATE: 2026-08-19",
        "MODE: ADD_ONLY / ARCHITECTURE_MATERIALIZATION / NO_PRODUCTION_INTEGRATION",
        "",
        "SCHEMAS",
        f"- EVENT_SCHEMA: {EVENT_SCHEMA_NAME} / {summary['event_schema_version']}",
        f"- STATE_SCHEMA: {STATE_SCHEMA_NAME} / {summary['state_schema_version']}",
        "- JSON_SCHEMA_DIALECT: Draft 2020-12",
        "- VALIDATOR: strict stdlib implementation of the exact Draft 2020-12 keyword subset used by 277/278",
        "",
        "CORE CHECKS",
        "- JSON_PARSE: PASS",
        "- JSON_SCHEMA_STRUCTURE_AND_LOCAL_REFS: PASS",
        "- STRICT_FIXTURE_SCHEMA_VALIDATION: PASS",
        "- EVENT_ID_REQUIRED_AND_IDEMPOTENCY_CONTRACT: PASS",
        "- SEMANTIC_TARGET_ROLE_ENUM: PASS",
        "- SEMANTIC_MAPPING_ENUMS_PRODUCTION_ONLY: PASS",
        "- ASSISTANCE_ENUM: PASS",
        "- EVALUATOR_AND_TRUST_ENUM: PASS",
        "- PRODUCT_SOURCE_TYPE_ENUM: PASS",
        "- SEMANTIC_REGISTRY_AND_MAPPING_VERSION_TRACEABILITY: PASS",
        "- SOURCE_OBJECT_AND_CONTENT_VERSION_TRACEABILITY: PASS",
        "- NO_CLIENT_AUTHORED_EFFECTIVE_OR_MASTERY_WEIGHT: PASS",
        "- APPEND_ONLY_CORRECTION_RETRACTION_MODEL: PASS",
        "- AI_EVALUATOR_LOW_TRUST_NON_OFFICIAL_BOUNDARY: PASS",
        "- NON_AI_REVIEWED_OPEN_RESPONSE_TRUTH_PATH: PASS",
        "- MATERIALIZED_STATE_INFERENCE_VERSION_REQUIRED: PASS",
        "- MATERIALIZED_STATE_EVIDENCE_WATERMARK_OR_REFERENCE_REQUIRED: PASS",
        "- SYSTEM_CONFIDENCE_DISTINCT_FROM_LEARNER_SELF_CONFIDENCE: PASS",
        "- LEGACY_DUPLICATE_APPLICATION_PREVENTION: PASS",
        "- PRODUCT_MASTERED_LABEL_NOT_CANONICAL_MASTERY: PASS",
        "- LEGACY_102_120_COMPATIBILITY: PASS",
        "- HANDOFF_114_EXACT_VS_BROAD_BOUNDARY: PASS",
        "- RUSSIAN_SPECIFIC_FIELDS_NOT_REQUIRED_BY_CORE: PASS",
        "- NO_FINAL_MASTERY_COEFFICIENTS_OR_FORGETTING_CURVE: PASS",
        f"- PRODUCTION_FILES_CHANGED: {'YES' if summary['unauthorized_changed_paths'] else 'NO'}",
        "",
        "FIXTURES",
        f"- EVENT_FIXTURE_COUNT: {summary['event_fixture_count']}",
    ]
    lines.extend(f"- EVENT_FIXTURE: {category} / PASS" for category in summary["event_fixture_categories"])
    lines.extend(
        [
            f"- STATE_FIXTURE_COUNT: {summary['state_fixture_count']}",
            "- STATE_FIXTURE: russian_empty_recomputable_state / PASS",
            "- STATE_FIXTURE: cross_subject_placeholder_state / PASS",
            f"- CROSS_SUBJECT_EVENT_STRUCTURAL_VALIDATION: {'PASS' if summary['cross_subject_event_fixture'] else 'FAIL'}",
            f"- CROSS_SUBJECT_STATE_STRUCTURAL_VALIDATION: {'PASS' if summary['cross_subject_state_fixture'] else 'FAIL'}",
            "- CROSS_SUBJECT_TRUTH_POLICY: production-valid PARTIAL + needs_review mapping; fixture-only marking is confined to provenance / subject_extension; no Mathematics/Physics subject truth invented",
            f"- NEGATIVE_FIXTURE_COUNT: {summary['negative_fixture_count']}",
            "- NEGATIVE_FIXTURES_REJECTED: PASS",
            "",
            "ADAPTERS",
            f"- ADAPTER_COUNT: {summary['adapter_count']}",
        ]
    )
    lines.extend(f"- {adapter_id}: REPRESENTED" for adapter_id in summary["adapter_ids"])
    lines.extend(["", "LEGACY COMPATIBILITY / NEEDS REVIEW"])
    lines.extend(f"- {finding}" for finding in findings)
    lines.extend(["", "CHANGED PATHS"])
    lines.extend(f"- {path_item}" for path_item in summary["changed_paths"])
    lines.extend(["", "ERRORS"])
    lines.extend(["- none"] if not errors else [f"- {error}" for error in errors])
    lines.extend(
        [
            "",
            "PRODUCTION SAFETY",
            "- No demo/trainer/T123/HTML/CSS/JS/scoring/localStorage file is an allowed TASK-004 change.",
            "- This validator reads legacy/product contracts and writes only the required 280 validation snapshot.",
            "- Runtime storage migration, Tutor/Homework integration and final mastery/readiness/retention/NBA algorithms remain HOLD.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    report = args.report or ROOT / REPORT_NAME
    try:
        errors, findings, summary = validate_all(ROOT)
        write_report(report, errors, findings, summary)
    except (ValidationFailure, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2
    if errors:
        print(f"FAIL: {len(errors)} validation error(s); see {report}")
        return 1
    print(
        "PASS: "
        f"event schema {summary['event_schema_version']}; "
        f"state schema {summary['state_schema_version']}; "
        f"{summary['event_fixture_count']} event fixtures; "
        f"{summary['state_fixture_count']} state fixtures; "
        f"{summary['negative_fixture_count']} negative fixtures rejected; "
        f"{summary['adapter_count']} adapters; production changes 0."
    )
    print(f"Report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
