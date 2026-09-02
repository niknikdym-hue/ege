#!/usr/bin/env python3
"""Build a fail-closed object-bound nonsemantic disposition candidate for OGE 6.1.

OGE_COD 6.1 is source-bound and independently reviewable, but current reviewed
route/inventory truth says it is an EXAM_ROUTE_ONLY meta-operation with no
canonical semantic refs. Historical object accounting placed the requirement in
a broad phonetics review group. That group meaning is review-accounting context,
not exact semantic authority for OGE 6.1. This builder therefore proposes one
object-level nonsemantic exam-meta-operation disposition without creating a
school-* or ru-* semantic identity and without emitting learner mastery.

The builder does not integrate the candidate into current launch progress.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
IDENTITY_REVIEW = HERE / "build_oge_6_1_meta_operation_identity_review.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
CURRENT_PROGRESS = HERE / "build_russian_semantic_acceptance_progress_launch_current.py"

TARGET_UNIT = "RAU-532ee826fbf30b195484"
TARGET_REQUIREMENT = "RSK-OGE_COD-6-1-P024"
TARGET_GROUP = "RUS-SEM-REVIEW-001"
TARGET_SOURCE = "FIPI-OGE-RU-2026-FINAL"
TARGET_DOCUMENT = "OGE_COD"
TARGET_CODE = "6.1"
TARGET_LOCATOR = "FIPI-OGE-RU-2026-FINAL/OGE_COD p.24 6.1"
ACCOUNTING_GROUP_MEANING = "Анализировать звуковую и буквенную форму языковых единиц."
ROUTE_TOPIC = "concept of orthogram / orthographic analysis premise"
ROUTE_NOTE = "Meta-operation over rules; not a new spelling identity."


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_candidate() -> dict[str, Any]:
    identity = runpy.run_path(str(IDENTITY_REVIEW))["build_review"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    progress = runpy.run_path(str(CURRENT_PROGRESS))["build_progress"]()

    if identity.get("status") != "OGE_6_1_META_OPERATION_IDENTITY_BOUND_NO_SEMANTIC_ADMISSION":
        raise ValueError("OGE 6.1 identity review is not at the no-admission boundary")
    if identity.get("normalized_sha256") != "ed0487188fae5cd233f02ac0b09f95b36b3134530f5ffc6a0cb22269fb11a6bf":
        raise ValueError("OGE 6.1 identity-review fingerprint drift")

    obj = identity["official_object"]
    route = identity["official_route_authority"]
    boundary = identity["decision_boundary"]
    if obj.get("admission_unit_id") != TARGET_UNIT or obj.get("requirement_id") != TARGET_REQUIREMENT:
        raise ValueError("OGE 6.1 exact object identity drift")
    if obj.get("packet_group") != TARGET_GROUP or obj.get("source_locator") != TARGET_LOCATOR:
        raise ValueError("OGE 6.1 packet/source binding drift")
    if obj.get("source_id") != TARGET_SOURCE or obj.get("document_id") != TARGET_DOCUMENT or obj.get("content_code") != TARGET_CODE:
        raise ValueError("OGE 6.1 official source identity drift")
    if obj.get("accounting_normalized_meaning") != ACCOUNTING_GROUP_MEANING:
        raise ValueError("OGE 6.1 historical accounting meaning drift")
    if route.get("overlay_topic") != ROUTE_TOPIC or route.get("overlay_note") != ROUTE_NOTE:
        raise ValueError("OGE 6.1 route meaning drift")
    if route.get("inventory_audit_classification") != "EXAM_ROUTE_ONLY":
        raise ValueError("OGE 6.1 inventory classification drift")
    if route.get("inventory_current_semantic_refs") != [] or route.get("overlay_owner_refs") != []:
        raise ValueError("OGE 6.1 unexpectedly acquired semantic owners")
    if boundary.get("new_school_identity_supported") is not False:
        raise ValueError("OGE 6.1 identity review unexpectedly supports a new school identity")

    groups = [group for group in packet.get("semantic_review_groups", []) if isinstance(group, dict) and group.get("group_id") == TARGET_GROUP]
    if len(groups) != 1:
        raise ValueError("OGE 6.1 packet group must exist exactly once")
    group = groups[0]
    if group.get("normalized_meaning") != ACCOUNTING_GROUP_MEANING:
        raise ValueError("OGE 6.1 shared packet group meaning drift")
    if group.get("admission_unit_count") != 21 or group.get("requirement_count") != 22:
        raise ValueError("OGE 6.1 shared packet group cardinality drift")
    if group.get("required_action") != "DECOMPOSE_AND_MAP_EXACT_COMPONENTS":
        raise ValueError("OGE 6.1 packet group review boundary drift")
    if group.get("explicit_semantic_candidates") != []:
        raise ValueError("OGE 6.1 shared packet group unexpectedly gained explicit candidates")
    review_boundaries = group.get("review_capability_boundaries") or []
    if len(review_boundaries) != 2:
        raise ValueError("OGE 6.1 broad packet review-boundary cardinality drift")
    if any(row.get("ref_kind") != "review_capability_boundary" or row.get("status") != "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION" for row in review_boundaries):
        raise ValueError("OGE 6.1 packet review boundary was promoted to semantic authority")

    target_requirements = [row for row in group.get("requirements", []) if isinstance(row, dict) and row.get("requirement_id") == TARGET_REQUIREMENT]
    if len(target_requirements) != 1:
        raise ValueError("OGE 6.1 exact requirement is not unique in shared packet group")
    target_requirement = target_requirements[0]
    if target_requirement.get("source_id") != TARGET_SOURCE or target_requirement.get("document_id") != TARGET_DOCUMENT:
        raise ValueError("OGE 6.1 shared-group source identity drift")
    if str(target_requirement.get("code")) != TARGET_CODE or target_requirement.get("source_locator") != TARGET_LOCATOR:
        raise ValueError("OGE 6.1 shared-group source locator drift")
    other_requirements = [row for row in group.get("requirements", []) if isinstance(row, dict) and row.get("requirement_id") != TARGET_REQUIREMENT]
    if len(other_requirements) != 21:
        raise ValueError("OGE 6.1 shared group must retain 21 unrelated/non-target requirements")
    other_units = [unit for unit in group.get("admission_unit_ids", []) if str(unit) != TARGET_UNIT]
    if len(other_units) != 20:
        raise ValueError("OGE 6.1 shared group must retain 20 non-target admission units")

    progress_summary = progress.get("progress_summary") or {}
    if len(progress.get("accepted_authorities", [])) != 48:
        raise ValueError("OGE 6.1 candidate must start from exact 48-authority launch truth")
    if progress_summary.get("semantic_units_with_accepted_component_sets") != 28 or progress_summary.get("semantic_requirements_with_accepted_component_sets") != 28:
        raise ValueError("OGE 6.1 candidate must start from exact 28/28 object-component progress")
    if progress_summary.get("semantic_units_remaining_without_accepted_component_set") != 1288 or progress_summary.get("semantic_requirements_remaining_without_accepted_component_set") != 1363:
        raise ValueError("OGE 6.1 candidate remaining-component baseline drift")
    if progress_summary.get("canonical_component_refs_reused_unique") != 115:
        raise ValueError("OGE 6.1 candidate canonical-ref baseline drift")
    if progress_summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery already present before OGE 6.1 disposition")

    current_group = [group for group in progress.get("semantic_review_groups", []) if isinstance(group, dict) and group.get("group_id") == TARGET_GROUP]
    if len(current_group) != 1:
        raise ValueError("OGE 6.1 current progress group must exist exactly once")
    current_group = current_group[0]
    target_acceptances = [
        row for row in current_group.get("accepted_component_sets", [])
        if isinstance(row, dict)
        and (row.get("admission_unit_id") == TARGET_UNIT or row.get("requirement_id") == TARGET_REQUIREMENT)
    ]
    if target_acceptances:
        raise ValueError("OGE 6.1 is already object-bound through a component-set authority")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "OGE_6_1_OBJECT_BOUND_NONSEMANTIC_META_OPERATION_DISPOSITION_CANDIDATE",
        "identity_review_sha256": identity["normalized_sha256"],
        "official_object": {
            "source_id": TARGET_SOURCE,
            "document_id": TARGET_DOCUMENT,
            "content_code": TARGET_CODE,
            "source_locator": TARGET_LOCATOR,
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "packet_group": TARGET_GROUP,
        },
        "exact_route_truth": {
            "topic": ROUTE_TOPIC,
            "meaning": ROUTE_NOTE,
            "overlay_classification": "EXAM_ONLY_COMPOSITE",
            "inventory_classification": "EXAM_ROUTE_ONLY",
            "canonical_component_refs": [],
            "bounded_ru_semantic_refs": [],
            "new_school_identity": False,
            "new_subject_identity": False,
        },
        "shared_review_group_contamination_guard": {
            "packet_group": TARGET_GROUP,
            "packet_group_admission_units": 21,
            "packet_group_requirements": 22,
            "packet_group_normalized_meaning": ACCOUNTING_GROUP_MEANING,
            "packet_group_normalized_meaning_is_exact_6_1_semantic_authority": False,
            "packet_group_phonetics_meaning_in_6_1_exact_scope": False,
            "target_admission_units": 1,
            "target_requirements": 1,
            "non_target_admission_units_preserved_for_separate_review": 20,
            "non_target_requirements_preserved_for_separate_review": 21,
            "whole_group_acceptance_allowed": False,
            "review_boundaries_are_semantic_admissions": False,
        },
        "proposed_disposition": {
            "authority_kind": "OBJECT_BOUND_NONSEMANTIC_EXAM_META_OPERATION",
            "subject_review_status": "CENTRAL_BRAIN_ACCEPTED_NONSEMANTIC_EXAM_META_OPERATION_OBJECT_DISPOSITION",
            "object_disposition_units": 1,
            "object_disposition_requirements": 1,
            "semantic_identity_admissions": 0,
            "canonical_component_refs": [],
            "bounded_ru_semantic_refs": [],
            "exact_component_mastery_effect": 0,
            "school_denominator_effect": 0,
            "generic_group_attempt_can_emit_exact_component_mastery": False,
            "integration_performed_now": False,
        },
        "expected_current_launch_effect_after_separate_integration": {
            "accepted_authorities": 49,
            "semantic_units_with_accepted_component_sets": 28,
            "semantic_requirements_with_accepted_component_sets": 28,
            "semantic_units_remaining_without_accepted_component_set": 1288,
            "semantic_requirements_remaining_without_accepted_component_set": 1363,
            "nonsemantic_object_disposition_units": 1,
            "nonsemantic_object_disposition_requirements": 1,
            "subject_disposed_units_total": 29,
            "subject_disposed_requirements_total": 29,
            "subject_review_units_remaining": 1287,
            "subject_review_requirements_remaining": 1362,
            "canonical_component_refs_reused_unique": 115,
            "false_exact_mastery_admissions": 0,
        },
        "safety": {
            "false_exact_mastery_admissions": 0,
            "learner_audio_persistence": 0,
            "accepted_demo_or_scorer_change": False,
            "tilda_change": False,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_payment_or_refund": False,
            "real_message_delivery": False,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_candidate()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        effect = result["expected_current_launch_effect_after_separate_integration"]
        guard = result["shared_review_group_contamination_guard"]
        print("RUSSIAN_OGE_6_1_NONSEMANTIC_META_OPERATION_DISPOSITION_CANDIDATE=PASS")
        print("ADMISSION_UNIT_ID=" + result["official_object"]["admission_unit_id"])
        print("REQUIREMENT_ID=" + result["official_object"]["requirement_id"])
        print("PACKET_GROUP=" + result["official_object"]["packet_group"])
        print("AUTHORITY_KIND=" + result["proposed_disposition"]["authority_kind"])
        print(f"PACKET_GROUP_UNITS={guard['packet_group_admission_units']}")
        print(f"PACKET_GROUP_REQUIREMENTS={guard['packet_group_requirements']}")
        print("PACKET_GROUP_MEANING_EXACT_6_1_AUTHORITY=0")
        print("NEW_SCHOOL_IDENTITY=0")
        print("NEW_SUBJECT_IDENTITY=0")
        print("SEMANTIC_IDENTITY_ADMISSIONS=0")
        print("AGGREGATE_DELTA_NOW=0")
        print(f"EXPECTED_POST_INTEGRATION_ACCEPTED_AUTHORITIES={effect['accepted_authorities']}")
        print(f"EXPECTED_POST_INTEGRATION_SUBJECT_DISPOSED_UNITS={effect['subject_disposed_units_total']}")
        print(f"EXPECTED_POST_INTEGRATION_SUBJECT_REVIEW_UNITS_REMAINING={effect['subject_review_units_remaining']}")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print("normalized_sha256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
