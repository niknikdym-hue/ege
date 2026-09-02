#!/usr/bin/env python3
"""Build the exact accepted ROUTE_OR_FORMAT_ONLY disposition for OGE-2026 6.1.

This is deliberately a pre-integration builder: it consumes the green 6.1
identity/disposition candidate while current launch progress still excludes the
6.1 authority. The result accounts the exact FIPI object without inventing a
school-* or ru-* semantic identity and without creating learner mastery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE / "build_oge_6_1_nonsemantic_meta_operation_disposition_candidate.py"
ACCOUNTING = HERE / "build_russian_subject_accounting_complete.py"
PACKET = HERE / "build_russian_semantic_acceptance_packet.py"

EXPECTED_CANDIDATE_SHA = "dd7445928c49d80e86b62695595930933e27fd0d6e535b35532eccbf822774c4"
EXPECTED_IDENTITY_SHA = "ed0487188fae5cd233f02ac0b09f95b36b3134530f5ffc6a0cb22269fb11a6bf"
EXPECTED_ACCOUNTING_SHA = "f3aef83dab99b554a4cdec9ef8d8fbc8036d557182259ae69db182efa11b925c"
EXPECTED_PACKET_SHA = "b35fb420f7a6e96ea11f47e321cae0affe363dc5ed8d6fb79ea8640ac5ac94c4"
EXPECTED_ACCEPTANCE_SHA = "537309ed6eaaac11ade9dfb3f26b68c4d9595ce1393b7c24fea32fa1fd811874"
EXPECTED_UNIT = "RAU-532ee826fbf30b195484"
EXPECTED_REQUIREMENT = "RSK-OGE_COD-6-1-P024"
EXPECTED_GROUP = "RUS-SEM-REVIEW-001"
EXPECTED_LOCATOR = "FIPI-OGE-RU-2026-FINAL/OGE_COD p.24 6.1"
GROUP_MEANING = "Анализировать звуковую и буквенную форму языковых единиц."
ROUTE_TOPIC = "concept of orthogram / orthographic analysis premise"
ROUTE_MEANING = "Meta-operation over rules; not a new spelling identity."


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_acceptance() -> dict[str, Any]:
    candidate = runpy.run_path(str(CANDIDATE))["build_candidate"]()
    accounting = runpy.run_path(str(ACCOUNTING))["build_accounting"]()
    packet = runpy.run_path(str(PACKET))["build_packet"]()

    if candidate.get("normalized_sha256") != EXPECTED_CANDIDATE_SHA:
        raise ValueError("OGE 6.1 disposition-candidate fingerprint drift")
    if candidate.get("identity_review_sha256") != EXPECTED_IDENTITY_SHA:
        raise ValueError("OGE 6.1 identity-review fingerprint drift")
    if accounting.get("normalized_sha256") != EXPECTED_ACCOUNTING_SHA:
        raise ValueError("Russian object-accounting fingerprint drift")
    if packet.get("normalized_sha256") != EXPECTED_PACKET_SHA:
        raise ValueError("Russian semantic packet fingerprint drift")
    if candidate.get("status") != "OGE_6_1_OBJECT_BOUND_NONSEMANTIC_META_OPERATION_DISPOSITION_CANDIDATE":
        raise ValueError("OGE 6.1 candidate status drift")

    obj = candidate["official_object"]
    route = candidate["exact_route_truth"]
    guard = candidate["shared_review_group_contamination_guard"]
    proposed = candidate["proposed_disposition"]

    expected_obj = {
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "content_code": "6.1",
        "source_locator": EXPECTED_LOCATOR,
        "admission_unit_id": EXPECTED_UNIT,
        "requirement_id": EXPECTED_REQUIREMENT,
        "packet_group": EXPECTED_GROUP,
    }
    if obj != expected_obj:
        raise ValueError("OGE 6.1 exact object binding drift")
    if route != {
        "topic": ROUTE_TOPIC,
        "meaning": ROUTE_MEANING,
        "overlay_classification": "EXAM_ONLY_COMPOSITE",
        "inventory_classification": "EXAM_ROUTE_ONLY",
        "canonical_component_refs": [],
        "bounded_ru_semantic_refs": [],
        "new_school_identity": False,
        "new_subject_identity": False,
    }:
        raise ValueError("OGE 6.1 exact route truth drift")
    if guard != {
        "packet_group": EXPECTED_GROUP,
        "packet_group_admission_units": 21,
        "packet_group_requirements": 22,
        "packet_group_normalized_meaning": GROUP_MEANING,
        "packet_group_normalized_meaning_is_exact_6_1_semantic_authority": False,
        "packet_group_phonetics_meaning_in_6_1_exact_scope": False,
        "target_admission_units": 1,
        "target_requirements": 1,
        "non_target_admission_units_preserved_for_separate_review": 20,
        "non_target_requirements_preserved_for_separate_review": 21,
        "whole_group_acceptance_allowed": False,
        "review_boundaries_are_semantic_admissions": False,
    }:
        raise ValueError("OGE 6.1 shared-review-group contamination guard drift")
    if proposed.get("object_disposition_units") != 1 or proposed.get("object_disposition_requirements") != 1:
        raise ValueError("OGE 6.1 candidate exact object-disposition cardinality drift")
    if proposed.get("semantic_identity_admissions") != 0:
        raise ValueError("OGE 6.1 candidate performed a semantic identity admission")
    if proposed.get("canonical_component_refs") != [] or proposed.get("bounded_ru_semantic_refs") != []:
        raise ValueError("OGE 6.1 candidate acquired forbidden semantic refs")
    if proposed.get("exact_component_mastery_effect") != 0 or proposed.get("school_denominator_effect") != 0:
        raise ValueError("OGE 6.1 candidate changed mastery or school denominator")
    if proposed.get("integration_performed_now") is not False:
        raise ValueError("OGE 6.1 candidate unexpectedly integrated itself")

    decision = {
        "acceptance_reason": (
            "FIPI OGE-2026 code 6.1 is an exact exam-route meta-operation premise for orthographic analysis, but current "
            "reviewed route/inventory truth classifies it as EXAM_ROUTE_ONLY with no canonical school or bounded ru-* "
            "semantic refs. Historical object accounting placed this exact requirement inside RUS-SEM-REVIEW-001 under "
            "a broad phonetics normalized meaning; that shared group meaning is review-accounting context only and is "
            "explicitly quarantined from exact 6.1 subject truth. The object is therefore disposed exactly once as "
            "ROUTE_OR_FORMAT_ONLY without creating a semantic identity, changing the school denominator, or emitting "
            "learner mastery."
        ),
        "admission_unit_id": EXPECTED_UNIT,
        "authority_kind": "OBJECT_BOUND_ROUTE_OR_FORMAT_ONLY_EXAM_META_OPERATION",
        "content_code": "6.1",
        "disposition": "ROUTE_OR_FORMAT_ONLY",
        "document_id": "OGE_COD",
        "exact_route_boundary": {
            "bounded_ru_semantic_refs": [],
            "canonical_component_refs": [],
            "meaning": ROUTE_MEANING,
            "new_school_identity": False,
            "new_subject_identity": False,
            "overlay_classification": "EXAM_ONLY_COMPOSITE",
            "topic": ROUTE_TOPIC,
        },
        "mastery_boundary": {
            "bounded_ru_semantic_refs": [],
            "canonical_component_refs": [],
            "exact_component_mastery_effect": 0,
            "generic_group_attempt_can_emit_exact_component_mastery": False,
            "object_disposition_can_emit_exact_component_mastery": False,
            "semantic_identity_admissions": 0,
        },
        "packet_group": EXPECTED_GROUP,
        "requirement_id": EXPECTED_REQUIREMENT,
        "review_group_contamination_guard": guard,
        "route_inventory_classification": "EXAM_ROUTE_ONLY",
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "source_locator": EXPECTED_LOCATOR,
    }

    result: dict[str, Any] = {
        "candidate_disposition_sha256": EXPECTED_CANDIDATE_SHA,
        "decision": decision,
        "identity_review_sha256": EXPECTED_IDENTITY_SHA,
        "object_accounting_sha256": EXPECTED_ACCOUNTING_SHA,
        "policy": {
            "accepted_object_disposition_requires_exact_source_identity": True,
            "bounded_ru_semantic_refs_admitted": 0,
            "canonical_component_refs_admitted": 0,
            "generic_group_attempt_can_exact_master_components": False,
            "legacy_packet_is_not_rewritten": True,
            "new_school_identity_created": False,
            "new_subject_identity_created": False,
            "route_or_format_only_object_is_accounted_without_semantic_identity": True,
            "shared_review_group_meaning_used_as_exact_6_1_semantics": False,
            "whole_shared_group_acceptance_allowed": False,
        },
        "safety": {
            "accepted_demo_or_scorer_change": False,
            "false_exact_mastery_admissions": 0,
            "learner_audio_persistence": 0,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_message_delivery": False,
            "real_payment_or_refund": False,
            "tilda_change": False,
        },
        "schema_version": "0.1.0",
        "scope": "FIPI_OGE_2026_CONTENT_CODE_6_1_EXACT_ROUTE_OR_FORMAT_ONLY_META_OPERATION_OBJECT_DISPOSITION",
        "semantic_packet_sha256": EXPECTED_PACKET_SHA,
        "status": "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_1_ROUTE_OR_FORMAT_ONLY_META_OPERATION_OBJECT_DISPOSITION",
        "summary": {
            "bounded_ru_semantic_refs": 0,
            "canonical_component_refs_unique": 0,
            "disposed_admission_units": 1,
            "disposed_requirements": 1,
            "false_exact_mastery_admissions": 0,
            "route_or_format_only_dispositions": 1,
            "school_denominator_effect": 0,
            "semantic_identity_admissions": 0,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    if result["normalized_sha256"] != EXPECTED_ACCEPTANCE_SHA:
        raise ValueError("OGE 6.1 accepted authority deterministic fingerprint drift")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_acceptance()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        d = result["decision"]
        print("RUSSIAN_OGE_6_1_ROUTE_OR_FORMAT_ONLY_ACCEPTANCE=PASS")
        print(f"ADMISSION_UNIT_ID={d['admission_unit_id']}")
        print(f"REQUIREMENT_ID={d['requirement_id']}")
        print(f"PACKET_GROUP={d['packet_group']}")
        print(f"DISPOSITION={d['disposition']}")
        print(f"AUTHORITY_KIND={d['authority_kind']}")
        print("CANONICAL_COMPONENT_REFS=0")
        print("BOUNDED_RU_SEMANTIC_REFS=0")
        print("SEMANTIC_IDENTITY_ADMISSIONS=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
