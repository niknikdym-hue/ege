#!/usr/bin/env python3
"""Fail-closed exact owner resolution for the last RU01 broad phonetics headers.

The exact-clause decomposition is already the remote accepted current-owner search
boundary. This review deduplicates only the partial/unbound source scopes and
creates one source-backed PROPOSED_NOT_CANONICAL owner candidate per unmatched
semantic scope. It creates no semantic admission, object closure or mastery.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

H = Path(__file__).resolve().parent
DECOMPOSITION = H / "build_ru01_phonetics_broad_header_clause_decomposition_review.py"

EXPECTED_AGGREGATE = {
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

# One candidate per distinct unmatched semantic scope. Duplicated EDSOO/FIPI
# clauses map to the same candidate only where their exact official clause text
# is the same semantic scope.
CANDIDATE_SPECS = {
    "ru-phonetics-sound-characterization": {
        "source_clauses": ["EDSOO59-P181-4.1-A"],
        "source_scope_ru": "Характеризовать звуки",
        "expected_search_statuses": ["PARTIAL_CURRENT_OWNER_NOT_ENOUGH_FOR_CLAUSE_CLOSURE"],
        "partial_current_owner_refs": ["ru-phonetics-vowel-consonant-features"],
        "boundary": "CHARACTERIZATION_OF_SOUNDS_ONLY; DOES_NOT_MEAN_FULL_SOUND_SYSTEM",
    },
    "ru-phonetics-sound-system": {
        "source_clauses": ["EDSOO59-P181-4.1-C"],
        "source_scope_ru": "характеризовать систему звуков",
        "expected_search_statuses": ["UNBOUND_EXACT_CLAUSE"],
        "partial_current_owner_refs": [],
        "boundary": "SOUND_SYSTEM_SCOPE_ONLY; NOT INFERRED FROM INDIVIDUAL_SOUND_FEATURES",
    },
    "ru-phonetics-vowel-system": {
        "source_clauses": ["EDSOO59-P187-4.1.1", "OGE-COD-P020-4.1.1"],
        "source_scope_ru": "Система гласных звуков",
        "expected_search_statuses": ["PARTIAL_CURRENT_OWNER_NOT_ENOUGH_FOR_CLAUSE_CLOSURE"],
        "partial_current_owner_refs": ["ru-phonetics-vowel-consonant-features"],
        "boundary": "FULL_VOWEL_SYSTEM_SCOPE; INDIVIDUAL_VOWEL_CONSONANT_FEATURES_ARE_PARTIAL_ONLY",
    },
    "ru-phonetics-consonant-system": {
        "source_clauses": ["EDSOO59-P187-4.1.2", "OGE-COD-P020-4.1.2"],
        "source_scope_ru": "Система согласных звуков",
        "expected_search_statuses": ["PARTIAL_CURRENT_OWNER_NOT_ENOUGH_FOR_CLAUSE_CLOSURE"],
        "partial_current_owner_refs": ["ru-phonetics-vowel-consonant-features"],
        "boundary": "FULL_CONSONANT_SYSTEM_SCOPE; INDIVIDUAL_VOWEL_CONSONANT_FEATURES_ARE_PARTIAL_ONLY",
    },
    "ru-phonetics-syllable": {
        "source_clauses": ["EDSOO59-P187-4.1.5", "OGE-COD-P020-4.1.5"],
        "source_scope_ru": "Слог",
        "expected_search_statuses": ["UNBOUND_EXACT_CLAUSE"],
        "partial_current_owner_refs": [],
        "boundary": "PHONETIC_SYLLABLE_SCOPE_ONLY",
    },
    "ru-phonetics-stress": {
        "source_clauses": ["EDSOO59-P187-4.1.6", "OGE-COD-P020-4.1.6"],
        "source_scope_ru": "Ударение",
        "expected_search_statuses": ["UNBOUND_EXACT_CLAUSE"],
        "partial_current_owner_refs": [],
        "boundary": "GENERIC_PHONETIC_STRESS_SCOPE; NORMATIVE_ORTHOEPY_STRESS_SELECTION_MUST_NOT_SUBSTITUTE",
    },
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    decomposition = runpy.run_path(str(DECOMPOSITION))["build_review"]()
    if decomposition.get("status") != "CENTRAL_BRAIN_RU01_BROAD_HEADER_EXACT_CLAUSE_DECOMPOSITION_REVIEW_READY_NOT_ACCEPTED":
        raise ValueError("exact clause decomposition status drift")
    if decomposition.get("current_aggregate_guard") != EXPECTED_AGGREGATE:
        raise ValueError("current-v19 aggregate drift")
    summary = decomposition.get("summary") or {}
    if summary.get("exact_official_clauses") != 17:
        raise ValueError("exact clause count drift")
    if summary.get("clauses_with_exact_current_owner") != 7:
        raise ValueError("exact current owner count drift")
    if summary.get("clauses_with_partial_current_owner_only") != 5:
        raise ValueError("partial current owner count drift")
    if summary.get("unbound_exact_clauses") != 5:
        raise ValueError("unbound current owner count drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery drift")

    records = {row["clause_id"]: row for row in decomposition.get("records") or []}
    unresolved = {
        clause_id
        for clause_id, row in records.items()
        if row["owner_match_status"] != "EXACT_CURRENT_OWNER"
    }
    candidate_clause_ids = {
        clause_id
        for spec in CANDIDATE_SPECS.values()
        for clause_id in spec["source_clauses"]
    }
    if candidate_clause_ids != unresolved:
        raise ValueError("candidate scopes must cover every and only unresolved exact clause")

    candidates = []
    for candidate_id, spec in sorted(CANDIDATE_SPECS.items()):
        rows = [records[clause_id] for clause_id in spec["source_clauses"]]
        statuses = sorted({row["owner_match_status"] for row in rows})
        if statuses != sorted(spec["expected_search_statuses"]):
            raise ValueError(f"current exact-owner search status drift: {candidate_id}")
        observed_partial_refs = sorted({ref for row in rows for ref in row.get("current_owner_refs") or []})
        if observed_partial_refs != sorted(spec["partial_current_owner_refs"]):
            raise ValueError(f"partial owner ref drift: {candidate_id}")
        candidates.append({
            "candidate_semantic_id": candidate_id,
            "candidate_status": "PROPOSED_NOT_CANONICAL",
            "source_scope_ru": spec["source_scope_ru"],
            "source_clause_ids": spec["source_clauses"],
            "source_requirements": sorted({row["requirement_id"] for row in rows}),
            "source_admission_units": sorted({row["admission_unit_id"] for row in rows}),
            "exact_current_owner_search_result": (
                "PARTIAL_ONLY_NO_EXACT_CURRENT_OWNER"
                if observed_partial_refs else "NO_EXACT_CURRENT_OWNER"
            ),
            "partial_current_owner_refs": observed_partial_refs,
            "semantic_boundary": spec["boundary"],
            "semantic_admission": False,
            "object_closure": False,
            "mastery_admission": False,
        })

    target_objects = [
        {"admission_unit_id": "RAU-5a6511267f156745f93c", "requirement_id": "RSK-EDSOO59-4-1-P181"},
        {"admission_unit_id": "RAU-5a6511267f156745f93c", "requirement_id": "RSK-EDSOO59-4-1-P187"},
        {"admission_unit_id": "RAU-3916b5e3da77ed038830", "requirement_id": "RSK-OGE_COD-4-1-P020"},
    ]

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_BROAD_HEADER_EXACT_OWNER_RESOLUTION_READY_NOT_ACCEPTED",
        "base_current_label": "current-v19",
        "base_current_normalized_sha256": decomposition.get("base_current_normalized_sha256"),
        "clause_decomposition_normalized_sha256": decomposition.get("normalized_sha256"),
        "owner_search_basis": "EXACT_CURRENT_ACCEPTED_CLAUSE_DECOMPOSITION_ON_CURRENT_V19; NO_TITLE_ROUTE_TASK_KEYWORD_FUZZY_OR_EMBEDDING_INFERENCE",
        "exact_current_owner_clauses_reused_without_new_admission": [
            row for row in decomposition["records"] if row["owner_match_status"] == "EXACT_CURRENT_OWNER"
        ],
        "proposed_owner_candidates": candidates,
        "target_objects": [dict(row, status="PENDING_EXACT_OWNER_AND_COMPONENT_EVIDENCE") for row in target_objects],
        "explicit_non_inference": {
            "partial_owner_can_be_promoted_to_exact_without_new_source_bounded_acceptance": False,
            "normative_orthoepy_stress_can_substitute_for_generic_phonetic_stress": False,
            "sound_features_can_substitute_for_full_sound_vowel_or_consonant_system": False,
            "candidate_name_or_route_or_task_number_can_create_semantic_acceptance": False,
            "candidate_can_create_mastery_before_acceptance_and_independent_evidence": False,
        },
        "next_required_action": {
            "candidate_semantics": "FOR_EACH_PROPOSED_CANDIDATE_BUILD_OR_LOCATE_COMPONENT_SPECIFIC_LEARNER_EVIDENCE_THEN_RUN_SEPARATE_BOUNDED_SEMANTIC_ACCEPTANCE",
            "object_acceptance": "FORBIDDEN_UNTIL_EVERY_REQUIRED_CLAUSE_HAS_AN_EXACT_ACCEPTED_OWNER_AND_COMPONENT_SPECIFIC_EVIDENCE",
        },
        "current_aggregate_guard": EXPECTED_AGGREGATE,
        "summary": {
            "source_requirements": 3,
            "exact_official_clauses": 17,
            "clauses_with_exact_current_owner": 7,
            "unresolved_clauses_resolved_to_distinct_candidate_scopes": 10,
            "distinct_proposed_owner_candidates": 6,
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "exact_mastery_admissions": 0,
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
        print("RU01_PHONETICS_BROAD_HEADER_OWNER_RESOLUTION_REVIEW=PASS")
        for key, value in result["summary"].items():
            print(f"{key.upper()}={value}")
        print("NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
