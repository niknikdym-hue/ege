#!/usr/bin/env python3
"""Refresh RU01 broad-header owner resolution against exact current-v23.

This review is fail-closed and creates no semantic admission, object closure, or
mastery. It exists because the original broad-header owner search was pinned to
current-v19, before syllable, generic phonetic stress, vowel-system, and
consonant-system semantics were accepted on this remote branch.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v23.py"
OLD_OWNER = HERE / "build_ru01_phonetics_broad_header_owner_resolution_review.py"

EXPECTED_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 41,
    "semantic_requirements_with_accepted_component_sets": 41,
    "semantic_units_remaining_without_accepted_component_set": 1275,
    "semantic_requirements_remaining_without_accepted_component_set": 1350,
    "subject_disposed_units_total": 42,
    "subject_disposed_requirements_total": 42,
    "subject_review_units_remaining": 1274,
    "subject_review_requirements_remaining": 1349,
    "canonical_component_refs_reused_unique": 122,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 73,
    "accepted_bounded_ru_semantics_total": 82,
    "false_exact_mastery_admissions": 0,
}

NOW_ACCEPTED = {
    "ru-phonetics-syllable": "RU01-PHONETIC-SYLLABLE-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
    "ru-phonetics-stress": "RU01-PHONETIC-STRESS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
    "ru-phonetics-vowel-system": "RU01-VOWEL-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
    "ru-phonetics-consonant-system": "RU01-CONSONANT-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
}

UNRESOLVED = {
    "ru-phonetics-sound-characterization",
    "ru-phonetics-sound-system",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _all_accepted_semantics() -> set[str]:
    accepted: set[str] = set()
    for path in sorted(HERE.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        for row in data.get("decisions") or []:
            if isinstance(row, dict) and row.get("accepted_semantic_id"):
                accepted.add(str(row["accepted_semantic_id"]))
    return accepted


def build_review() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    summary = current.get("progress_summary") or {}
    for key, expected in EXPECTED_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v23 aggregate drift: {key}")
    if len(current.get("accepted_authorities") or []) != 69:
        raise ValueError("current-v23 accepted authority count drift")
    predecessor = current.get("newly_accepted_bounded_subject_semantic") or {}
    if predecessor.get("semantic_id") != "ru-phonetics-consonant-system":
        raise ValueError("current-v23 predecessor semantic drift")
    if predecessor.get("independent_verification_item_ids") != [f"p01-u10-v{i}" for i in range(1, 6)]:
        raise ValueError("current-v23 consonant evidence drift")

    old = runpy.run_path(str(OLD_OWNER))["build_review"]()
    if old.get("status") != "CENTRAL_BRAIN_RU01_BROAD_HEADER_EXACT_OWNER_RESOLUTION_READY_NOT_ACCEPTED":
        raise ValueError("old owner-resolution status drift")
    old_candidates = {row["candidate_semantic_id"]: row for row in old.get("proposed_owner_candidates") or []}
    expected_old = set(NOW_ACCEPTED) | UNRESOLVED
    if set(old_candidates) != expected_old:
        raise ValueError("old candidate set drift")

    accepted_semantics = _all_accepted_semantics()
    for semantic_id, filename in NOW_ACCEPTED.items():
        path = HERE / filename
        if not path.exists():
            raise ValueError(f"accepted authority file missing: {filename}")
        data = json.loads(path.read_text(encoding="utf-8"))
        ids = {
            str(row.get("accepted_semantic_id"))
            for row in data.get("decisions") or []
            if isinstance(row, dict) and row.get("accepted_semantic_id")
        }
        if semantic_id not in ids or semantic_id not in accepted_semantics:
            raise ValueError(f"current accepted owner not proven: {semantic_id}")

    for semantic_id in UNRESOLVED:
        if semantic_id in accepted_semantics:
            raise ValueError(f"unresolved semantic unexpectedly already accepted: {semantic_id}")

    characterization_old = old_candidates["ru-phonetics-sound-characterization"]
    if characterization_old.get("exact_current_owner_search_result") != "PARTIAL_ONLY_NO_EXACT_CURRENT_OWNER":
        raise ValueError("sound-characterization old search status drift")
    if characterization_old.get("partial_current_owner_refs") != ["ru-phonetics-vowel-consonant-features"]:
        raise ValueError("sound-characterization partial owner drift")

    sound_system_old = old_candidates["ru-phonetics-sound-system"]
    if sound_system_old.get("exact_current_owner_search_result") != "NO_EXACT_CURRENT_OWNER":
        raise ValueError("sound-system old search status drift")
    if sound_system_old.get("partial_current_owner_refs") != []:
        raise ValueError("sound-system old partial-owner drift")

    records = [
        {
            "semantic_id": semantic_id,
            "old_candidate_status": old_candidates[semantic_id]["candidate_status"],
            "source_clause_ids": old_candidates[semantic_id]["source_clause_ids"],
            "current_owner_status": "EXACT_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC",
            "authority_file": filename,
            "object_closure_effect": "NONE_BY_THIS_REVIEW",
        }
        for semantic_id, filename in sorted(NOW_ACCEPTED.items())
    ]
    records.extend([
        {
            "semantic_id": "ru-phonetics-sound-characterization",
            "source_clause_ids": characterization_old["source_clause_ids"],
            "source_scope_ru": characterization_old["source_scope_ru"],
            "current_owner_status": "PARTIAL_CURRENT_OWNER_ONLY_REMAINS_UNRESOLVED",
            "partial_current_owner_refs": characterization_old["partial_current_owner_refs"],
            "next_required_action": "BUILD_OR_LOCATE_SOURCE_BOUNDED_COMPONENT_SPECIFIC_EVIDENCE_FOR_SOUND_CHARACTERIZATION_THEN_RUN_SEPARATE_ADEQUACY_AND_SEMANTIC_ACCEPTANCE",
            "object_closure_effect": "NONE_BY_THIS_REVIEW",
        },
        {
            "semantic_id": "ru-phonetics-sound-system",
            "source_clause_ids": sound_system_old["source_clause_ids"],
            "source_scope_ru": sound_system_old["source_scope_ru"],
            "current_owner_status": "NO_SINGLE_EXACT_ACCEPTED_OWNER",
            "newly_available_exact_component_refs": [
                "ru-phonetics-vowel-system",
                "ru-phonetics-consonant-system",
            ],
            "component_set_is_exact_owner_by_this_review": False,
            "next_required_action": "RUN_SEPARATE_SOURCE_BOUND_COMPONENT_SET_REVIEW_FOR_SOUND_SYSTEM; DO_NOT INFER WHOLE-SYSTEM CLOSURE FROM TWO COMPONENT TITLES",
            "object_closure_effect": "NONE_BY_THIS_REVIEW",
        },
    ])

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_BROAD_HEADER_OWNER_RESOLUTION_CURRENT_V23_REVIEW_COMPLETE_NO_ADMISSION",
        "base_current_label": "current-v23",
        "base_current_normalized_sha256": current.get("normalized_sha256"),
        "old_owner_resolution_normalized_sha256": old.get("normalized_sha256"),
        "owner_search_basis": "EXACT_REMOTE_CURRENT_V23_ACCEPTED_AUTHORITIES_PLUS_ORIGINAL_EXACT_SOURCE_CLAUSE_DECOMPOSITION; NO TITLE_ROUTE_TASK_KEYWORD_FUZZY_OR_EMBEDDING INFERENCE",
        "records": records,
        "remaining_unresolved_semantics": sorted(UNRESOLVED),
        "explicit_non_inference": {
            "new_vowel_and_consonant_system_acceptances_auto_create_sound_system_owner": False,
            "partial_vowel_consonant_feature_owner_auto_becomes_sound_characterization_owner": False,
            "candidate_name_or_route_or_task_number_can_create_semantic_acceptance": False,
            "component_presence_can_close_broad_parent_object_without_exact_component_set_gate": False,
            "generic_ru01_attempt_can_emit_exact_mastery": False,
        },
        "next_required_action": {
            "first": "RESOLVE_SOUND_CHARACTERIZATION_WITH_COMPONENT_SPECIFIC_CONTENT_EVIDENCE_OR_PROVE_AN_EXACT_CURRENT OWNER",
            "second": "REVIEW_SOUND_SYSTEM_AS_AN_EXACT_SOURCE_BOUND COMPONENT SET USING ACCEPTED VOWEL_AND_CONSONANT_SYSTEM SEMANTICS; DO_NOT AUTO_ACCEPT",
            "parent_object_acceptance": "FORBIDDEN_UNTIL EVERY SOURCE CLAUSE HAS EXACT ACCEPTED OWNER AND COMPONENT_SPECIFIC EVIDENCE AND A SEPARATE EXACT_HEAD OBJECT GATE PASSES",
        },
        "current_aggregate_guard": EXPECTED_SUMMARY,
        "summary": {
            "original_proposed_owner_candidates": 6,
            "candidates_now_exact_accepted": 4,
            "remaining_unresolved_candidates": 2,
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
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU01_BROAD_HEADER_OWNER_RESOLUTION_CURRENT_V23=PASS")
        for key, value in result["summary"].items():
            print(f"{key.upper()}={value}")
        print("NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
