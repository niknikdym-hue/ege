#!/usr/bin/env python3
"""Fail-closed exact object-binding review for EDSOO59 p.190 5.1 RU02 orthoepy."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
OBJECT_REVIEW = PROGRAM / "object-review"
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v27.py"
QUEUE_BUILDER = OBJECT_REVIEW / "build_object_level_review_queue.py"
PRON_ACCEPTANCE = HERE / "RU02-NORMATIVE-PRONUNCIATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
STRESS_ACCEPTANCE = HERE / "RU02-NORMATIVE-STRESS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
P187_ACCEPTANCE = HERE / "RU02-EDSOO59-P187-4-1-6-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

CURRENT_HEAD = "bb6e31986c2f7adf07c2d5e46ca4ba71270d33ba"
CURRENT_RUN_ID = 34555338230
CURRENT_SHA = "4e5e6018b8fa832a6115074291c722cd7862388aecbd78ef633e0e2b61864b82"

GROUP = "RUS-SEM-REVIEW-047"
TARGET_UNIT = "RAU-475d1c2a36040b45e190"
TARGET_REQUIREMENT = "RSK-EDSOO59-5-1-P190"
TARGET_SOURCE = "EDSOO-RU-5-9-2025"
TARGET_DOCUMENT = "EDSOO59"
TARGET_PAGE = 190
TARGET_CODE = "5.1"
TARGET_LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.190 5.1"
TARGET_SECTION = "grade_5_distributed_codifier"
TARGET_CLASS = "learning_outcome"
TARGET_GRADE = ["5"]
TARGET_ROUTES = ["school"]
TARGET_MODULES = ["RU-PROG-02"]
TARGET_MEANING = "Применять нормативное произношение и ударение."

PRON_REF = "ru-orthoepy-normative-pronunciation-selection"
STRESS_REF = "ru-orthoepy-normative-stress-selection"
COMPONENTS = [PRON_REF, STRESS_REF]
PRON_EVIDENCE = ["p02-u4-v1", "p02-u4-v2", "p02-u4-v3", "p02-u4-v4", "p02-u4-v5"]
STRESS_EVIDENCE = ["p02-u3-v1", "p02-u3-v2", "p02-u3-v3", "p02-u3-v4"]
EVIDENCE = {PRON_REF: PRON_EVIDENCE, STRESS_REF: STRESS_EVIDENCE}

PRIOR_SIBLINGS = {
    ("RAU-a8f2ad0b357c9e369c51", "RSK-EDSOO1011-2-2-4-P074"),
    ("RAU-da83bb720dea792b3afb", "RSK-EDSOO59-4-1-6-P187"),
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def one_semantic_decision(doc: dict[str, Any], semantic_ref: str) -> dict[str, Any]:
    rows = [
        row
        for row in doc.get("decisions", [])
        if isinstance(row, dict) and row.get("accepted_semantic_id") == semantic_ref
    ]
    if len(rows) != 1:
        raise ValueError(f"accepted semantic decision missing or duplicated: {semantic_ref}")
    return rows[0]


def build_review() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("schema_version") != "0.29.0":
        raise ValueError("current-v27 schema drift")
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v27 normalized SHA drift")
    summary = current.get("progress_summary") or {}
    expected_summary = {
        "semantic_units_with_accepted_component_sets": 43,
        "semantic_requirements_with_accepted_component_sets": 43,
        "subject_disposed_units_total": 44,
        "subject_disposed_requirements_total": 44,
        "subject_review_units_remaining": 1272,
        "subject_review_requirements_remaining": 1347,
        "accepted_bounded_ru_subject_semantics": 75,
        "accepted_bounded_ru_semantics_total": 84,
        "canonical_component_refs_reused_unique": 125,
        "false_exact_mastery_admissions": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v27 aggregate drift: {key}")
    if len(current.get("accepted_authorities") or []) != 73:
        raise ValueError("current-v27 accepted authority count drift")

    groups = [
        row
        for row in current.get("semantic_review_groups", [])
        if isinstance(row, dict) and row.get("group_id") == GROUP
    ]
    if len(groups) != 1:
        raise ValueError("RU02 review group missing or duplicated")
    group = groups[0]
    if group.get("normalized_meaning") != TARGET_MEANING:
        raise ValueError("RU02 group normalized meaning drift")
    if group.get("accepted_component_set_count") != 2:
        raise ValueError("RU02 group accepted-set count drift")
    if group.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET":
        raise ValueError("RU02 group status drift")

    requirements = [
        row
        for row in group.get("requirements", [])
        if isinstance(row, dict) and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(requirements) != 1:
        raise ValueError("target requirement missing or duplicated in current-v27")
    req = requirements[0]
    expected_req = {
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "page": TARGET_PAGE,
        "code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "grades": TARGET_GRADE,
        "confidence": "HIGH",
    }
    for key, expected in expected_req.items():
        if req.get(key) != expected:
            raise ValueError(f"target requirement source drift: {key}")

    accepted_sets = [
        row
        for row in group.get("accepted_component_sets", [])
        if isinstance(row, dict)
    ]
    if len(accepted_sets) != 2:
        raise ValueError("expected exactly two prior RU02 accepted objects")
    actual_prior = {
        (str(row.get("admission_unit_id")), str(row.get("requirement_id")))
        for row in accepted_sets
    }
    if actual_prior != PRIOR_SIBLINGS:
        raise ValueError("prior RU02 exact siblings drift")
    for prior in accepted_sets:
        if prior.get("canonical_component_refs") != COMPONENTS:
            raise ValueError("prior RU02 component set drift")
        if (prior.get("authority") or {}).get("component_specific_independent_evidence_items") != 9:
            raise ValueError("prior RU02 evidence count drift")
    if any(
        row.get("admission_unit_id") == TARGET_UNIT or row.get("requirement_id") == TARGET_REQUIREMENT
        for row in accepted_sets
    ):
        raise ValueError("target sibling is already accepted")

    queue = runpy.run_path(str(QUEUE_BUILDER))["build_queue"]()
    target_units = [
        unit
        for unit in queue.get("admission_units", [])
        if any(
            isinstance(member, dict) and member.get("requirement_id") == TARGET_REQUIREMENT
            for member in unit.get("members", [])
        )
    ]
    if len(target_units) != 1:
        raise ValueError("target requirement missing or duplicated in object queue")
    unit = target_units[0]
    if unit.get("admission_unit_id") != TARGET_UNIT:
        raise ValueError("target admission-unit identity drift")
    if unit.get("member_count") != 1:
        raise ValueError("target must remain one-member admission unit")
    if unit.get("admission_status") != "SUBJECT_REVIEW_REQUIRED":
        raise ValueError("target unexpectedly auto-resolved")
    if unit.get("exact_canonical_semantic_id") is not None:
        raise ValueError("target unexpectedly has a direct canonical semantic id")

    signature = unit.get("admission_signature") or {}
    review = signature.get("review_signature") or {}
    expected_signature = {
        "normalized_meaning": TARGET_MEANING,
        "requirement_class": TARGET_CLASS,
        "modules": TARGET_MODULES,
        "routes": TARGET_ROUTES,
    }
    if review != expected_signature:
        raise ValueError("target exact review signature drift")
    for key, expected in (
        ("source_id", TARGET_SOURCE),
        ("document_id", TARGET_DOCUMENT),
        ("section", TARGET_SECTION),
        ("code", TARGET_CODE),
    ):
        if signature.get(key) != expected:
            raise ValueError(f"target admission signature drift: {key}")

    member = unit.get("members", [None])[0] or {}
    for key, expected in (
        ("requirement_id", TARGET_REQUIREMENT),
        ("source_id", TARGET_SOURCE),
        ("document_id", TARGET_DOCUMENT),
        ("page", TARGET_PAGE),
        ("code", TARGET_CODE),
        ("section", TARGET_SECTION),
        ("grades", TARGET_GRADE),
        ("confidence", "HIGH"),
    ):
        if member.get(key) != expected:
            raise ValueError(f"target exact source member drift: {key}")

    pronunciation = load(PRON_ACCEPTANCE)
    if pronunciation.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_PRONUNCIATION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("pronunciation semantic is not accepted")
    pron = one_semantic_decision(pronunciation, PRON_REF)
    if pron.get("source_taxonomy_id") != "normative_pronunciation_selection":
        raise ValueError("pronunciation taxonomy drift")
    if pron.get("source_evidence_status") != "confirmed":
        raise ValueError("pronunciation source evidence is not confirmed")
    if pron.get("independent_verification_item_ids") != PRON_EVIDENCE:
        raise ValueError("pronunciation evidence drift")
    if pron.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("pronunciation semantic boundary drift")
    if (pronunciation.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("pronunciation semantic opened false exact mastery")

    stress = load(STRESS_ACCEPTANCE)
    if stress.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU02_NORMATIVE_STRESS_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("stress semantic is not accepted")
    stress_decision = one_semantic_decision(stress, STRESS_REF)
    if stress_decision.get("candidate_ref") != "candidate-018":
        raise ValueError("stress candidate identity drift")
    if stress_decision.get("source_taxonomy_id") != "normative_stress_selection":
        raise ValueError("stress taxonomy drift")
    if stress_decision.get("source_evidence_status") != "confirmed":
        raise ValueError("stress source evidence is not confirmed")
    if stress_decision.get("independent_verification_item_ids") != STRESS_EVIDENCE:
        raise ValueError("stress evidence drift")
    if stress_decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("stress semantic boundary drift")
    if (stress.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("stress semantic opened false exact mastery")

    p187 = load(P187_ACCEPTANCE)
    if p187.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU02_EDSOO59_P187_4_1_6_CANONICAL_COMPONENT_SET":
        raise ValueError("p187 sibling acceptance status drift")
    p187_decision = p187.get("decision") or {}
    if p187_decision.get("admission_unit_id") != "RAU-da83bb720dea792b3afb":
        raise ValueError("p187 sibling unit drift")
    if p187_decision.get("requirement_id") != "RSK-EDSOO59-4-1-6-P187":
        raise ValueError("p187 sibling requirement drift")
    if p187_decision.get("canonical_component_refs") != COMPONENTS:
        raise ValueError("p187 sibling component refs drift")
    if p187_decision.get("component_specific_independent_evidence") != EVIDENCE:
        raise ValueError("p187 sibling component evidence drift")
    if p187_decision.get("independent_evidence_items") != 9:
        raise ValueError("p187 sibling evidence count drift")
    if (p187.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("p187 sibling opened false exact mastery")

    if set(PRON_EVIDENCE) & set(STRESS_EVIDENCE):
        raise ValueError("pronunciation and stress evidence lineages overlap")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU02_EDSOO59_P190_5_1_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED",
        "current_v27_exact_head_gate": {
            "workflow": "Russian RU02 EDSOO59 p187 4.1.6 current exact acceptance",
            "run_id": CURRENT_RUN_ID,
            "head_sha": CURRENT_HEAD,
            "conclusion": "SUCCESS",
            "normalized_sha256": CURRENT_SHA,
        },
        "selected_object": {
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "packet_group": GROUP,
            "source_id": TARGET_SOURCE,
            "document_id": TARGET_DOCUMENT,
            "page": TARGET_PAGE,
            "code": TARGET_CODE,
            "source_locator": TARGET_LOCATOR,
            "section": TARGET_SECTION,
            "requirement_class": TARGET_CLASS,
            "grades": TARGET_GRADE,
            "routes": TARGET_ROUTES,
            "modules": TARGET_MODULES,
            "normalized_meaning": TARGET_MEANING,
            "confidence": "HIGH",
        },
        "reuse_first_owner_resolution": {
            "resolution": "EXACT_CURRENT_BOUNDED_RU02_COMPONENT_OWNERS_EXIST",
            "source_backing": (
                "The exact current EDSOO59 p.190 5.1 source row is a grade-5 learning outcome "
                "in RU-PROG-02 with the official normalized meaning "
                "'Применять нормативное произношение и ударение.'; the current accepted bounded "
                "RU02 owners independently cover normative pronunciation selection and normative stress selection. "
                "This source-backed decomposition is review-only and does not inherit acceptance from siblings."
            ),
            "canonical_component_refs": COMPONENTS,
            "components": [
                {
                    "semantic_ref": PRON_REF,
                    "source_taxonomy_id": "normative_pronunciation_selection",
                    "independent_evidence_refs": PRON_EVIDENCE,
                    "evidence_count": len(PRON_EVIDENCE),
                },
                {
                    "semantic_ref": STRESS_REF,
                    "source_taxonomy_id": "normative_stress_selection",
                    "candidate_ref": "candidate-018",
                    "independent_evidence_refs": STRESS_EVIDENCE,
                    "evidence_count": len(STRESS_EVIDENCE),
                },
            ],
            "component_count": 2,
            "independent_evidence_items": 9,
            "missing_source_components": [],
            "overlapping_component_boundaries": [],
        },
        "sibling_reuse_boundary": {
            "prior_accepted_siblings": [
                {
                    "admission_unit_id": "RAU-a8f2ad0b357c9e369c51",
                    "requirement_id": "RSK-EDSOO1011-2-2-4-P074",
                },
                {
                    "admission_unit_id": "RAU-da83bb720dea792b3afb",
                    "requirement_id": "RSK-EDSOO59-4-1-6-P187",
                },
            ],
            "same_review_group": True,
            "same_exact_normalized_meaning": True,
            "prior_sibling_acceptance_auto_closes_target": False,
            "shared_component_owner_evidence_is_object_acceptance": False,
            "separate_exact_object_acceptance_required": True,
        },
        "acceptance_readiness": {
            "exact_source_identity_verified": True,
            "target_still_in_current_v27_remainder": True,
            "exact_current_component_owners_verified": True,
            "all_components_have_component_specific_independent_evidence": True,
            "source_backed_two_component_decomposition_verified": True,
            "separate_object_acceptance_required": True,
            "object_accepted_by_this_review": False,
        },
        "policy": {
            "review_is_acceptance": False,
            "review_can_reduce_object_counts": False,
            "review_can_create_school_identity": False,
            "review_can_create_ru_semantic_identity": False,
            "title_route_task_keyword_fuzzy_or_embedding_inference_allowed": False,
            "shared_sibling_evidence_can_auto_close_target": False,
            "generic_orthoepy_attempt_can_emit_exact_component_mastery": False,
            "stress_evidence_can_substitute_for_pronunciation": False,
            "pronunciation_evidence_can_substitute_for_stress": False,
            "component_specific_independent_evidence_required": True,
            "registered_user_identity_required_for_future_canonical_learner_evidence": True,
            "exact_versioned_item_and_action_required_for_future_canonical_learner_evidence": True,
            "server_owned_received_at_required_for_future_canonical_learner_evidence": True,
            "durable_evidence_event_required_for_future_canonical_learner_evidence": True,
            "anonymous_or_device_only_canonical_progress_allowed": False,
        },
        "summary": {
            "reviewed_admission_units": 1,
            "reviewed_requirements": 1,
            "exact_component_set_ready_units": 1,
            "exact_component_set_ready_requirements": 1,
            "exact_component_refs": 2,
            "independent_evidence_items": 9,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "new_school_canonical_identities": 0,
            "new_ru_semantic_identities": 0,
            "exact_mastery_admissions": 0,
            "false_exact_mastery_admissions": 0,
            "current_subject_review_units_remaining": 1272,
            "current_subject_review_requirements_remaining": 1347,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_review()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        summary = result["summary"]
        print("RU02_EDSOO59_P190_5_1_EXACT_OBJECT_BINDING_REVIEW=PASS")
        print(f"SELECTED_UNIT={TARGET_UNIT}")
        print(f"SELECTED_REQUIREMENT={TARGET_REQUIREMENT}")
        print("EXACT_COMPONENT_REFS=2")
        print("INDEPENDENT_EVIDENCE_ITEMS=9")
        print("OBJECT_CLOSURES_BY_REVIEW=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"CURRENT_SUBJECT_REVIEW_UNITS_REMAINING={summary['current_subject_review_units_remaining']}")
        print(f"CURRENT_SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['current_subject_review_requirements_remaining']}")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
