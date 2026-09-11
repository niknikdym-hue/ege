#!/usr/bin/env python3
"""Fail-closed exact object-binding review for OGE COD p.21 4.1.6 RU02 orthoepy.

This review starts from the CI-proven current-v28 aggregate. It verifies that
exactly one RU02 object remains in the shared normative-pronunciation-and-stress
review group, binds that remainder to the deterministic object-review queue,
reuses only already accepted component owners plus their exact component-level
evidence, and deliberately does not accept the OGE object. Sibling object
acceptance is never inherited.
"""
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
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v28.py"
QUEUE_BUILDER = OBJECT_REVIEW / "build_object_level_review_queue.py"
PRON_ACCEPTANCE = HERE / "RU02-NORMATIVE-PRONUNCIATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
STRESS_ACCEPTANCE = HERE / "RU02-NORMATIVE-STRESS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
P187_ACCEPTANCE = HERE / "RU02-EDSOO59-P187-4-1-6-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
P190_ACCEPTANCE = HERE / "RU02-EDSOO59-P190-5-1-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

CURRENT_HEAD = "f050dfa7ecf69e371839c6693f68b18928a2fef2"
CURRENT_RUN_ID = 34600017223
CURRENT_SHA = "be4b747386c4dadd52b152b65fed60a9a76e585c6501a6080fd214025748eb8a"

GROUP = "RUS-SEM-REVIEW-047"
TARGET_UNIT = "RAU-475d1c2a36040b45e190"
TARGET_REQUIREMENT = "RSK-OGE_COD-4-1-6-P021"
TARGET_SOURCE = "FIPI-OGE-RU-2026-FINAL"
TARGET_DOCUMENT = "OGE_COD"
TARGET_PAGE = 21
TARGET_CODE = "4.1.6"
TARGET_LOCATOR = "FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.6"
TARGET_GRADE = ["9"]
TARGET_MEANING = "Применять нормативное произношение и ударение."
TARGET_MODULE = "RU-PROG-02"
TARGET_ROUTE = "oge"

PRON_REF = "ru-orthoepy-normative-pronunciation-selection"
STRESS_REF = "ru-orthoepy-normative-stress-selection"
COMPONENTS = [PRON_REF, STRESS_REF]
PRON_EVIDENCE = ["p02-u4-v1", "p02-u4-v2", "p02-u4-v3", "p02-u4-v4", "p02-u4-v5"]
STRESS_EVIDENCE = ["p02-u3-v1", "p02-u3-v2", "p02-u3-v3", "p02-u3-v4"]
EVIDENCE = {PRON_REF: PRON_EVIDENCE, STRESS_REF: STRESS_EVIDENCE}

PRIOR_SIBLINGS = {
    ("RAU-a8f2ad0b357c9e369c51", "RSK-EDSOO1011-2-2-4-P074"),
    ("RAU-da83bb720dea792b3afb", "RSK-EDSOO59-4-1-6-P187"),
    ("RAU-f875ecae572d08cef520", "RSK-EDSOO59-5-1-P190"),
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


def verify_component_owner_semantics() -> None:
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
    if stress_decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("stress semantic boundary drift")
    if (stress.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("stress semantic opened false exact mastery")


def verify_accepted_sibling(path: Path, expected_status: str, unit_id: str, requirement_id: str) -> None:
    payload = load(path)
    if payload.get("status") != expected_status:
        raise ValueError(f"accepted sibling status drift: {path.name}")
    decision = payload.get("decision") or {}
    if decision.get("admission_unit_id") != unit_id:
        raise ValueError(f"accepted sibling unit drift: {path.name}")
    if decision.get("requirement_id") != requirement_id:
        raise ValueError(f"accepted sibling requirement drift: {path.name}")
    if decision.get("canonical_component_refs") != COMPONENTS:
        raise ValueError(f"accepted sibling component refs drift: {path.name}")
    if decision.get("component_specific_independent_evidence") != EVIDENCE:
        raise ValueError(f"accepted sibling component evidence drift: {path.name}")
    if decision.get("independent_evidence_items") != 9:
        raise ValueError(f"accepted sibling evidence count drift: {path.name}")
    if (payload.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError(f"accepted sibling opened false exact mastery: {path.name}")


def build_review() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("schema_version") != "0.30.0":
        raise ValueError("current-v28 schema drift")
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v28 normalized SHA drift")
    summary = current.get("progress_summary") or {}
    expected_summary = {
        "semantic_units_with_accepted_component_sets": 44,
        "semantic_requirements_with_accepted_component_sets": 44,
        "subject_disposed_units_total": 45,
        "subject_disposed_requirements_total": 45,
        "subject_review_units_remaining": 1271,
        "subject_review_requirements_remaining": 1346,
        "accepted_bounded_ru_subject_semantics": 75,
        "accepted_bounded_ru_semantics_total": 84,
        "canonical_component_refs_reused_unique": 125,
        "false_exact_mastery_admissions": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v28 aggregate drift: {key}")
    if len(current.get("accepted_authorities") or []) != 74:
        raise ValueError("current-v28 accepted authority count drift")

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
    if group.get("accepted_component_set_count") != 3:
        raise ValueError("RU02 group accepted-set count drift")
    if group.get("admission_unit_count") != 4 or group.get("requirement_count") != 4:
        raise ValueError("RU02 group denominator drift")
    if group.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET":
        raise ValueError("RU02 group status drift")

    requirements = [
        row
        for row in group.get("requirements", [])
        if isinstance(row, dict) and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(requirements) != 1:
        raise ValueError("target requirement missing or duplicated in current-v28")
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

    accepted_sets = [row for row in group.get("accepted_component_sets", []) if isinstance(row, dict)]
    if len(accepted_sets) != 3:
        raise ValueError("expected exactly three prior RU02 accepted objects")
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

    accepted_units = {str(row.get("admission_unit_id")) for row in accepted_sets}
    accepted_requirements = {str(row.get("requirement_id")) for row in accepted_sets}
    remaining_units = sorted(set(group.get("admission_unit_ids") or []) - accepted_units)
    remaining_requirements = sorted(
        str(row.get("requirement_id"))
        for row in group.get("requirements", [])
        if isinstance(row, dict) and str(row.get("requirement_id")) not in accepted_requirements
    )
    if remaining_units != [TARGET_UNIT]:
        raise ValueError("RU02 current-v28 remaining unit is not the exact OGE target")
    if remaining_requirements != [TARGET_REQUIREMENT]:
        raise ValueError("RU02 current-v28 remaining requirement is not the exact OGE target")

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
    review_signature = signature.get("review_signature") or {}
    if review_signature.get("normalized_meaning") != TARGET_MEANING:
        raise ValueError("target queue normalized meaning drift")
    if TARGET_MODULE not in (review_signature.get("modules") or []):
        raise ValueError("target queue RU02 module binding missing")
    if TARGET_ROUTE not in (review_signature.get("routes") or []):
        raise ValueError("target queue OGE route binding missing")
    for key, expected in (("source_id", TARGET_SOURCE), ("document_id", TARGET_DOCUMENT), ("code", TARGET_CODE)):
        if signature.get(key) != expected:
            raise ValueError(f"target admission signature drift: {key}")

    member = unit.get("members", [None])[0] or {}
    for key, expected in (
        ("requirement_id", TARGET_REQUIREMENT),
        ("source_id", TARGET_SOURCE),
        ("document_id", TARGET_DOCUMENT),
        ("page", TARGET_PAGE),
        ("code", TARGET_CODE),
        ("grades", TARGET_GRADE),
        ("confidence", "HIGH"),
    ):
        if member.get(key) != expected:
            raise ValueError(f"target exact source member drift: {key}")

    verify_component_owner_semantics()
    verify_accepted_sibling(
        P187_ACCEPTANCE,
        "CENTRAL_BRAIN_ACCEPTED_EXACT_RU02_EDSOO59_P187_4_1_6_CANONICAL_COMPONENT_SET",
        "RAU-da83bb720dea792b3afb",
        "RSK-EDSOO59-4-1-6-P187",
    )
    verify_accepted_sibling(
        P190_ACCEPTANCE,
        "CENTRAL_BRAIN_ACCEPTED_EXACT_RU02_EDSOO59_P190_5_1_CANONICAL_COMPONENT_SET",
        "RAU-f875ecae572d08cef520",
        "RSK-EDSOO59-5-1-P190",
    )
    if set(PRON_EVIDENCE) & set(STRESS_EVIDENCE):
        raise ValueError("pronunciation and stress evidence lineages overlap")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU02_OGE_P021_4_1_6_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED",
        "current_v28_exact_head_gate": {
            "workflow": "Russian RU02 EDSOO59 p190 5.1 current exact acceptance",
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
            "grades": TARGET_GRADE,
            "routes": list(review_signature.get("routes") or []),
            "modules": list(review_signature.get("modules") or []),
            "requirement_class": review_signature.get("requirement_class"),
            "section": signature.get("section"),
            "normalized_meaning": TARGET_MEANING,
            "confidence": "HIGH",
        },
        "reuse_first_owner_resolution": {
            "resolution": "EXACT_CURRENT_BOUNDED_RU02_COMPONENT_OWNERS_EXIST",
            "source_backing": (
                "The exact current FIPI OGE 2026 codifier p.21 code 4.1.6 row is the sole remaining "
                "object in RUS-SEM-REVIEW-047 after current-v28. The accepted bounded RU02 owners "
                "independently cover normative pronunciation selection and normative stress selection. "
                "Accepted sibling authorities pin the exact component-specific evidence lineages, but "
                "their object acceptance is not inherited by this OGE source object."
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
                {"admission_unit_id": unit_id, "requirement_id": requirement_id}
                for unit_id, requirement_id in sorted(PRIOR_SIBLINGS)
            ],
            "same_review_group": True,
            "same_exact_normalized_meaning": True,
            "prior_sibling_acceptance_auto_closes_target": False,
            "shared_component_owner_evidence_is_object_acceptance": False,
            "separate_exact_object_acceptance_required": True,
        },
        "acceptance_readiness": {
            "exact_source_identity_verified": True,
            "target_is_sole_remaining_object_in_current_v28_group": True,
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
        "validation_provenance": {
            "target_identity_source": "current_v28_single_remaining_group_member_plus_deterministic_object_review_queue",
            "target_admission_unit_id": TARGET_UNIT,
            "target_requirement_id": TARGET_REQUIREMENT,
            "component_owner_source": "accepted_bounded_ru02_semantic_authorities",
            "component_evidence_source": "accepted_exact_sibling_authorities",
            "component_evidence_refs": EVIDENCE,
            "canonical_authority_file_mutated": False,
            "sibling_acceptance_inherited_by_target": False,
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
            "current_subject_review_units_remaining": 1271,
            "current_subject_review_requirements_remaining": 1346,
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
        print("RU02_OGE_P021_4_1_6_EXACT_OBJECT_BINDING_REVIEW=PASS")
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
