#!/usr/bin/env python3
"""Fail-closed exact-clause decomposition for the last RU01 broad phonetics headers.

This review starts only after the current-v19 residual gate. It records exact
official clause scope and reuses a current semantic owner only where the owner
boundary is already exact. Broad, partial or unmatched clauses remain explicit
blockers. This file creates no semantic candidate, no object closure and no
mastery admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

H = Path(__file__).resolve().parent
RESIDUAL = H / "build_ru01_phonetics_broad_header_residual_review.py"

AUTHORITY_FILES = {
    "ru-phonetics-sound-letter-relation": H / "RU01-PHONETICS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
    "ru-phonetics-vowel-consonant-features": H / "RU01-PHONETICS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
    "ru-phonetics-word-analysis-sequence": H / "RU01-PHONETICS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
    "ru-phonetics-phonetic-transcription-elements": H / "RU01-PHONETIC-TRANSCRIPTION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
    "ru-phonetics-sound-changes-in-speech-flow": H / "RU01-SOUND-CHANGES-IN-SPEECH-FLOW-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json",
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

# Exact official source clauses. The EDSOO59 p.187 and OGE codifier 4.1 headers
# share the official 4.1.1-4.1.7 taxonomy, but remain distinct source objects.
CLAUSES = [
    {
        "requirement_id": "RSK-EDSOO59-4-1-P181",
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "source_id": "EDSOO-RU-5-9-2025",
        "source_locator": "EDSOO59 p.181 4.1",
        "clause_id": "EDSOO59-P181-4.1-A",
        "official_clause_ru": "Характеризовать звуки",
        "owner_match_status": "PARTIAL_CURRENT_OWNER_NOT_ENOUGH_FOR_CLAUSE_CLOSURE",
        "current_owner_refs": ["ru-phonetics-vowel-consonant-features"],
        "blocker": "BROAD_CHARACTERIZE_SOUNDS_SCOPE_EXCEEDS_CURRENT_FEATURE_OWNER",
    },
    {
        "requirement_id": "RSK-EDSOO59-4-1-P181",
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "source_id": "EDSOO-RU-5-9-2025",
        "source_locator": "EDSOO59 p.181 4.1",
        "clause_id": "EDSOO59-P181-4.1-B",
        "official_clause_ru": "понимать различие между звуком и буквой",
        "owner_match_status": "EXACT_CURRENT_OWNER",
        "current_owner_refs": ["ru-phonetics-sound-letter-relation"],
        "blocker": None,
    },
    {
        "requirement_id": "RSK-EDSOO59-4-1-P181",
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "source_id": "EDSOO-RU-5-9-2025",
        "source_locator": "EDSOO59 p.181 4.1",
        "clause_id": "EDSOO59-P181-4.1-C",
        "official_clause_ru": "характеризовать систему звуков",
        "owner_match_status": "UNBOUND_EXACT_CLAUSE",
        "current_owner_refs": [],
        "blocker": "NO_EXACT_CURRENT_SOUND_SYSTEM_OWNER",
    },
]

HEADER_SUBCLAUSES = [
    ("4.1.1", "Система гласных звуков", "PARTIAL_CURRENT_OWNER_NOT_ENOUGH_FOR_CLAUSE_CLOSURE", ["ru-phonetics-vowel-consonant-features"], "CURRENT_FEATURE_OWNER_DOES_NOT_PROVE_FULL_VOWEL_SYSTEM_SCOPE"),
    ("4.1.2", "Система согласных звуков", "PARTIAL_CURRENT_OWNER_NOT_ENOUGH_FOR_CLAUSE_CLOSURE", ["ru-phonetics-vowel-consonant-features"], "CURRENT_FEATURE_OWNER_DOES_NOT_PROVE_FULL_CONSONANT_SYSTEM_SCOPE"),
    ("4.1.3", "Изменение звуков в речевом потоке", "EXACT_CURRENT_OWNER", ["ru-phonetics-sound-changes-in-speech-flow"], None),
    ("4.1.4", "Элементы фонетической транскрипции", "EXACT_CURRENT_OWNER", ["ru-phonetics-phonetic-transcription-elements"], None),
    ("4.1.5", "Слог", "UNBOUND_EXACT_CLAUSE", [], "NO_EXACT_CURRENT_SYLLABLE_OWNER"),
    ("4.1.6", "Ударение", "UNBOUND_EXACT_CLAUSE", [], "NO_EXACT_CURRENT_GENERIC_PHONETIC_STRESS_OWNER; ORTHOEPIC_NORMATIVE_STRESS_MUST_NOT_SUBSTITUTE"),
    ("4.1.7", "Фонетический анализ слова", "EXACT_CURRENT_OWNER", ["ru-phonetics-word-analysis-sequence"], None),
]

for source_prefix, requirement_id, admission_unit_id, source_id, locator in [
    ("EDSOO59-P187", "RSK-EDSOO59-4-1-P187", "RAU-5a6511267f156745f93c", "EDSOO-RU-5-9-2025", "EDSOO59 p.187 4.1"),
    ("OGE-COD-P020", "RSK-OGE_COD-4-1-P020", "RAU-3916b5e3da77ed038830", "FIPI-OGE-RU-2026-FINAL", "OGE_COD p.20 4.1"),
]:
    for code, text, status, refs, blocker in HEADER_SUBCLAUSES:
        CLAUSES.append({
            "requirement_id": requirement_id,
            "admission_unit_id": admission_unit_id,
            "source_id": source_id,
            "source_locator": locator,
            "clause_id": f"{source_prefix}-{code}",
            "official_clause_ru": text,
            "official_clause_code": code,
            "owner_match_status": status,
            "current_owner_refs": refs,
            "blocker": blocker,
        })


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _verify_current_owner_authorities() -> None:
    for semantic_id, path in AUTHORITY_FILES.items():
        if not path.exists():
            raise ValueError(f"current owner authority missing: {path.name}")
        data = json.loads(path.read_text(encoding="utf-8"))
        accepted = {
            str(row.get("accepted_semantic_id", ""))
            for row in data.get("decisions") or []
            if isinstance(row, dict)
        }
        if semantic_id not in accepted:
            raise ValueError(f"semantic owner not accepted by exact authority: {semantic_id}")


def build_review() -> dict[str, Any]:
    residual = runpy.run_path(str(RESIDUAL))["build_review"]()
    if residual.get("status") != "CENTRAL_BRAIN_RU01_BROAD_HEADER_RESIDUAL_SOURCE_DECOMPOSITION_REQUIRED_NOT_ACCEPTED":
        raise ValueError("residual review status drift")
    if (residual.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("residual false exact mastery drift")
    if sorted(residual.get("residual_requirement_ids") or []) != [
        "RSK-EDSOO59-4-1-P181",
        "RSK-EDSOO59-4-1-P187",
        "RSK-OGE_COD-4-1-P020",
    ]:
        raise ValueError("residual requirement set drift")

    current = runpy.run_path(str(H / "build_russian_semantic_acceptance_progress_launch_current_v19.py"))["build_progress"]()
    current_summary = current.get("progress_summary") or {}
    for key, value in EXPECTED_CURRENT_SUMMARY.items():
        if current_summary.get(key) != value:
            raise ValueError(f"current-v19 aggregate drift: {key}")
    if len(current.get("accepted_authorities") or []) != 65:
        raise ValueError("current-v19 accepted authority count drift")

    _verify_current_owner_authorities()

    clause_ids = [row["clause_id"] for row in CLAUSES]
    if len(clause_ids) != len(set(clause_ids)) or len(clause_ids) != 17:
        raise ValueError("exact clause identity drift")

    requirement_counts: dict[str, int] = {}
    for row in CLAUSES:
        requirement_counts[row["requirement_id"]] = requirement_counts.get(row["requirement_id"], 0) + 1
    if requirement_counts != {
        "RSK-EDSOO59-4-1-P181": 3,
        "RSK-EDSOO59-4-1-P187": 7,
        "RSK-OGE_COD-4-1-P020": 7,
    }:
        raise ValueError("source clause decomposition drift")

    allowed_statuses = {
        "EXACT_CURRENT_OWNER",
        "PARTIAL_CURRENT_OWNER_NOT_ENOUGH_FOR_CLAUSE_CLOSURE",
        "UNBOUND_EXACT_CLAUSE",
    }
    for row in CLAUSES:
        if row["owner_match_status"] not in allowed_statuses:
            raise ValueError("unknown owner match status")
        if row["owner_match_status"] == "EXACT_CURRENT_OWNER" and not row["current_owner_refs"]:
            raise ValueError("exact current owner missing ref")
        if row["owner_match_status"] == "UNBOUND_EXACT_CLAUSE" and row["current_owner_refs"]:
            raise ValueError("unbound clause must not carry an owner ref")

    exact_count = sum(row["owner_match_status"] == "EXACT_CURRENT_OWNER" for row in CLAUSES)
    partial_count = sum(row["owner_match_status"].startswith("PARTIAL_") for row in CLAUSES)
    unbound_count = sum(row["owner_match_status"] == "UNBOUND_EXACT_CLAUSE" for row in CLAUSES)
    if (exact_count, partial_count, unbound_count) != (7, 5, 5):
        raise ValueError("clause owner classification count drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_BROAD_HEADER_EXACT_CLAUSE_DECOMPOSITION_REVIEW_READY_NOT_ACCEPTED",
        "base_current_label": "current-v19",
        "base_current_normalized_sha256": current.get("normalized_sha256"),
        "residual_review_normalized_sha256": residual.get("normalized_sha256"),
        "official_source_scope": [
            {
                "source_id": "EDSOO-RU-5-9-2025",
                "document_id": "EDSOO59",
                "locators": ["p.181 4.1", "p.187 4.1-4.1.7"],
                "source_role": "PUBLIC_OFFICIAL_PROGRAM_AUTHORITY",
            },
            {
                "source_id": "FIPI-OGE-RU-2026-FINAL",
                "document_id": "OGE_COD",
                "locators": ["p.20 4.1", "4.1.1-4.1.7 taxonomy"],
                "source_role": "PUBLIC_OFFICIAL_CODIFIER_AUTHORITY",
            },
        ],
        "records": sorted(CLAUSES, key=lambda row: row["clause_id"]),
        "explicit_non_inference": {
            "normative_orthoepy_stress_can_substitute_for_generic_phonetic_stress": False,
            "vowel_consonant_feature_owner_can_close_full_sound_system_or_full_vowel_consonant_system": False,
            "broad_header_can_be_closed_from_title_route_task_number_keyword_fuzzy_or_embedding": False,
            "partial_owner_match_is_exact_owner_match": False,
        },
        "next_required_action": {
            "exact_current_owner_clauses": "KEEP_AS_REUSE_CANDIDATES_ONLY_UNTIL_WHOLE_SOURCE_OBJECT_COMPONENT_SET_IS_COMPLETE",
            "partial_or_unbound_clauses": "SEARCH_EXACT_CURRENT_CANONICAL_OWNER_BY_SOURCE_SCOPE; IF_NONE_CREATE_ONE_SEPARATE_SOURCE_BACKED_BOUNDED_OWNER_CANDIDATE_PER_UNMATCHED_SEMANTIC_SCOPE",
            "object_acceptance": "FORBIDDEN_UNTIL_EVERY_REQUIRED_CLAUSE_HAS_AN_EXACT_ACCEPTED_OWNER_AND_COMPONENT_SPECIFIC_EVIDENCE",
        },
        "current_aggregate_guard": EXPECTED_CURRENT_SUMMARY,
        "summary": {
            "source_requirements_decomposed": 3,
            "exact_official_clauses": 17,
            "clauses_with_exact_current_owner": exact_count,
            "clauses_with_partial_current_owner_only": partial_count,
            "unbound_exact_clauses": unbound_count,
            "new_semantic_candidates": 0,
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
        print("RU01_PHONETICS_BROAD_HEADER_CLAUSE_DECOMPOSITION_REVIEW=PASS")
        for key, value in result["summary"].items():
            print(f"{key.upper()}={value}")
        print("NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
