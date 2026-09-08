#!/usr/bin/env python3
"""Fail-closed residual review for the last RU01 broad phonetics/graphics headers.

This review runs only after the exact OGE 2.1 composite acceptance (current-v19).
It does not admit a semantic or close an object. It proves which RU01 source
requirements remain broad/incompletely decomposed after the already accepted
transcription, sound-changes and sound-composition objects, and pins the next
required action to exact source-clause decomposition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

H = Path(__file__).resolve().parent
BINDING = H / "build_ru01_phonetics_exact_object_binding_review.py"
CURRENT = H / "build_russian_semantic_acceptance_progress_launch_current_v19.py"

TARGET_REQUIREMENTS = {
    "RSK-EDSOO59-4-1-P181": {
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "source_id": "EDSOO-RU-5-9-2025",
        "document_id": "EDSOO59",
        "page": 181,
        "code": "4.1",
        "normalized_source_signature": "SOUND_LETTER_AND_SOUND_SYSTEM",
        "review_classification": "PARTIAL",
        "accepted_semantic_refs": [
            "ru-phonetics-sound-letter-relation",
            "ru-phonetics-vowel-consonant-features",
        ],
        "blocker_or_reroute": "SIBLING_BROAD_HEADER",
    },
    "RSK-EDSOO59-4-1-P187": {
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "source_id": "EDSOO-RU-5-9-2025",
        "document_id": "EDSOO59",
        "page": 187,
        "code": "4.1",
        "normalized_source_signature": "PHONETICS_GRAPHICS_HEADER",
        "review_classification": "PENDING",
        "accepted_semantic_refs": [],
        "blocker_or_reroute": "BROAD_HEADER_INCOMPLETE",
    },
    "RSK-OGE_COD-4-1-P020": {
        "admission_unit_id": "RAU-3916b5e3da77ed038830",
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "page": 20,
        "code": "4.1",
        "normalized_source_signature": "PHONETICS_GRAPHICS_HEADER",
        "review_classification": "PENDING",
        "accepted_semantic_refs": [],
        "blocker_or_reroute": "BROAD_HEADER_INCOMPLETE",
    },
}

FORMER_PENDING_NOW_ACCEPTED = {
    "RSK-EDSOO59-4-1-4-P187",
    "RSK-OGE_COD-4-1-4-P021",
    "RSK-EDSOO59-4-1-3-P187",
    "RSK-OGE_COD-4-1-3-P021",
    "RSK-OGE_COD-2-1-P010",
}

EXPECTED_CURRENT_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 41,
    "semantic_requirements_with_accepted_component_sets": 41,
    "semantic_units_remaining_without_accepted_component_set": 1275,
    "semantic_requirements_remaining_without_accepted_component_set": 1350,
    "subject_disposed_units_total": 42,
    "subject_disposed_requirements_total": 42,
    "subject_review_units_remaining": 1274,
    "subject_review_requirements_remaining": 1349,
    "canonical_component_refs_reused_unique": 122,
    "accepted_bounded_ru_subject_semantics": 69,
    "accepted_bounded_ru_semantics_total": 78,
    "false_exact_mastery_admissions": 0,
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    binding = runpy.run_path(str(BINDING))["build_review"]()
    if binding.get("status") != "CENTRAL_BRAIN_RU01_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("RU01 exact binding review status drift")
    if (binding.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("binding review false exact mastery drift")

    current = runpy.run_path(str(CURRENT))["build_progress"]()
    summary = current.get("progress_summary") or {}
    for key, value in EXPECTED_CURRENT_SUMMARY.items():
        if summary.get(key) != value:
            raise ValueError(f"current-v19 aggregate drift: {key}")
    if len(current.get("accepted_authorities") or []) != 65:
        raise ValueError("current-v19 accepted authority count drift")

    accepted_sets = [
        item
        for group in current.get("semantic_review_groups") or []
        for item in (group.get("accepted_component_sets") or [])
        if isinstance(item, dict)
    ]
    accepted_requirement_ids = {str(item.get("requirement_id", "")) for item in accepted_sets}
    if not FORMER_PENDING_NOW_ACCEPTED <= accepted_requirement_ids:
        raise ValueError("formerly pending exact RU01 objects are not all accepted in current-v19")
    if set(TARGET_REQUIREMENTS) & accepted_requirement_ids:
        raise ValueError("broad-header residual was already accepted; re-review required")

    binding_rows = {str(row.get("requirement_id", "")): row for row in binding.get("records") or []}
    if set(TARGET_REQUIREMENTS) - set(binding_rows):
        raise ValueError("target broad-header binding records missing")

    residual_records: list[dict[str, Any]] = []
    for requirement_id in sorted(TARGET_REQUIREMENTS):
        expected = TARGET_REQUIREMENTS[requirement_id]
        row = binding_rows[requirement_id]
        for key, value in expected.items():
            if row.get(key) != value:
                raise ValueError(f"exact broad-header source binding drift: {requirement_id}:{key}")
        residual_records.append({
            "admission_unit_id": expected["admission_unit_id"],
            "requirement_id": requirement_id,
            "source_id": expected["source_id"],
            "document_id": expected["document_id"],
            "page": expected["page"],
            "code": expected["code"],
            "source_locator": row.get("source_locator"),
            "normalized_source_signature": expected["normalized_source_signature"],
            "review_classification": expected["review_classification"],
            "already_exact_component_refs": expected["accepted_semantic_refs"],
            "current_blocker": expected["blocker_or_reroute"],
            "admission_effect": "NONE_REVIEW_ONLY",
        })

    unit_to_requirements: dict[str, list[str]] = {}
    for row in residual_records:
        unit_to_requirements.setdefault(row["admission_unit_id"], []).append(row["requirement_id"])
    if {key: sorted(value) for key, value in unit_to_requirements.items()} != {
        "RAU-3916b5e3da77ed038830": ["RSK-OGE_COD-4-1-P020"],
        "RAU-5a6511267f156745f93c": ["RSK-EDSOO59-4-1-P181", "RSK-EDSOO59-4-1-P187"],
    }:
        raise ValueError("residual broad-header unit decomposition drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_BROAD_HEADER_RESIDUAL_SOURCE_DECOMPOSITION_REQUIRED_NOT_ACCEPTED",
        "base_current_label": "current-v19",
        "base_current_normalized_sha256": current.get("normalized_sha256"),
        "binding_review_normalized_sha256": binding.get("normalized_sha256"),
        "module_id": "RU-PROG-01",
        "residual_admission_units": sorted(unit_to_requirements),
        "residual_requirement_ids": sorted(TARGET_REQUIREMENTS),
        "records": residual_records,
        "resolution": {
            "exact_current_owner_search_result": "NO_SINGLE_EXACT_OWNER_FOR_BROAD_HEADER; SOURCE_REVIEW_ALREADY_CLASSIFIES_THE_RESIDUAL_AS_PARTIAL_OR_BROAD_HEADER_INCOMPLETE",
            "new_semantic_candidate_created": False,
            "reason": "A broad source header may contain several components. Creating or reusing one owner without exact clause-level source scope would be inference.",
            "next_required_action": "EXTRACT_EXACT_OFFICIAL_SOURCE_CLAUSES_FOR_EDSOO59_P181_4_1_EDSOO59_P187_4_1_AND_OGE_P020_4_1; MAP_EACH_CLAUSE_ONLY_TO_AN_EXACT_CURRENT_OWNER; FOR_ANY_UNMATCHED_CLAUSE_CREATE_A_SEPARATE_SOURCE_BACKED_BOUNDED_OWNER_CANDIDATE_BEFORE_OBJECT_ACCEPTANCE",
        },
        "policy": {
            "review_is_acceptance": False,
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "broad_header_can_be_closed_by_title_or_route": False,
            "partial_component_refs_can_close_sibling_broad_requirement": False,
            "keyword_fuzzy_embedding_or_task_number_inference_allowed": False,
            "unknown_component_scope_can_emit_mastery": False,
            "false_exact_mastery_admissions": 0,
        },
        "summary": {
            "residual_admission_units": 2,
            "residual_requirements": 3,
            "requirements_with_some_existing_exact_refs": 1,
            "requirements_with_no_exact_refs": 2,
            "new_semantic_candidates": 0,
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
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
        print("RU01_PHONETICS_BROAD_HEADER_RESIDUAL_REVIEW=PASS")
        for key, value in result["summary"].items():
            print(f"{key.upper()}={value}")
        print("NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
