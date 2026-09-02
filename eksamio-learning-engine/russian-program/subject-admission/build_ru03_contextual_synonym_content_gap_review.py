#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
SOURCE_RESOLVER = HERE / "build_ru03_contextual_synonym_source_identity_resolution.py"

CANDIDATE = "candidate-015"
TAXONOMY = "contextual_synonym_selection"
PROPOSED_SEMANTIC = "ru-lexis-contextual-synonym-text-fit"
BROAD_SEMANTIC = "ru-lexis-contextual-meaning-polysemy"

PREEXISTING_RU03_CONTENT = [
    PROGRAM / "production-learning-content/RU-PROG-03-LEXIS-PARONYMS-PHRASEOLOGY-WAVE-002-v0.1.json",
    PROGRAM / "production-learning-content/RU-PROG-03-DICTIONARY-SENSE-SELECTION-WAVE-003-v0.1.json",
    PROGRAM / "production-learning-content/RU-PROG-03-DEFINITION-CONTEXT-MATCHING-WAVE-004-v0.1.json",
    PROGRAM / "production-learning-content/RU-PROG-03-LEXICAL-REDUNDANCY-WAVE-005-v0.1.json",
    PROGRAM / "production-learning-content/RU-PROG-03-LEXICAL-COLLOCATION-CORRECTION-WAVE-006-v0.1.json",
    PROGRAM / "production-learning-content/RU-PROG-03-PHRASEOLOGISM-IDENTIFICATION-WAVE-007-v0.1.json",
]


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    source = runpy.run_path(str(SOURCE_RESOLVER))["build_resolution"]()
    if source.get("status") != "CENTRAL_BRAIN_RU03_CONTEXTUAL_SYNONYM_CURRENT_2026_SOURCE_IDENTITY_RESOLVED_NO_ADMISSION":
        raise ValueError("candidate-015 source-resolution prerequisite drift")
    if (source.get("resolution") or {}).get("source_identity_status") != "EXACT_CURRENT_2026_OFFICIAL_SOURCE_CONFIRMED":
        raise ValueError("candidate-015 current source identity is not confirmed")
    if int((source.get("summary") or {}).get("semantic_admissions", -1)) != 0:
        raise ValueError("candidate-015 source resolution unexpectedly admitted a semantic")

    files: list[dict[str, Any]] = []
    units: list[dict[str, Any]] = []
    for path in PREEXISTING_RU03_CONTENT:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("subject") != "russian" or data.get("module_id") != "RU-PROG-03":
            raise ValueError(f"RU03 content module drift: {path.name}")
        guard = data.get("copyright_guard") or {}
        if guard.get("source_passages_copied") != 0:
            raise ValueError(f"RU03 source-passage copy guard drift: {path.name}")
        file_units = [row for row in data.get("units", []) if isinstance(row, dict)]
        files.append(
            {
                "path": f"russian-program/production-learning-content/{path.name}",
                "status": str(data.get("status") or ""),
                "unit_count": len(file_units),
            }
        )
        for row in file_units:
            units.append(
                {
                    "path": path.name,
                    "proposed_semantic_id": str(row.get("proposed_semantic_id") or ""),
                    "candidate_ref": row.get("candidate_ref"),
                    "source_taxonomy_id": row.get("source_taxonomy_id"),
                    "title_ru": str(row.get("title_ru") or ""),
                }
            )

    exact_crosswalk_matches = [
        row for row in units
        if row["candidate_ref"] == CANDIDATE or row["source_taxonomy_id"] == TAXONOMY
    ]
    proposed_id_collisions = [row for row in units if row["proposed_semantic_id"] == PROPOSED_SEMANTIC]
    if exact_crosswalk_matches:
        raise ValueError("candidate-015 already has an exact pre-existing learner-content crosswalk")
    if proposed_id_collisions:
        raise ValueError("candidate-015 proposed semantic id collides with pre-existing RU03 content")

    broad = [row for row in units if row["proposed_semantic_id"] == BROAD_SEMANTIC]
    if len(broad) != 1:
        raise ValueError("expected exactly one broader contextual-meaning unit")
    if broad[0]["title_ru"] != "Лексическое значение в контексте и многозначность":
        raise ValueError("broader contextual-meaning unit title drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU03_CONTEXTUAL_SYNONYM_CONTENT_GAP_REVIEW_COMPLETE_NO_ADMISSION",
        "authority_issue": 161,
        "module_id": "RU-PROG-03",
        "candidate_ref": CANDIDATE,
        "source_taxonomy_id": TAXONOMY,
        "source_identity_prerequisite": {
            "status": source["status"],
            "source_identity_status": source["resolution"]["source_identity_status"],
            "current_official_authority": source["current_official_source_resolution"]["authority"],
            "current_official_source_url": source["current_official_source_resolution"]["url"],
        },
        "reuse_first_inventory": {
            "preexisting_ru03_content_files_reviewed": files,
            "preexisting_ru03_units_reviewed": len(units),
            "exact_candidate_or_taxonomy_crosswalk_matches": 0,
            "proposed_semantic_id_collisions": 0,
            "broader_neighbor": {
                "semantic_id": BROAD_SEMANTIC,
                "title_ru": broad[0]["title_ru"],
                "relation": "ADJACENT_BUT_NOT_EXACT",
                "reason": "This existing unit determines the lexical meaning of a word from context and handles polysemy. Candidate-015 requires selecting or producing a synonym that can replace the target in the supplied text while preserving contextual meaning; proving one skill does not prove the other.",
            },
        },
        "decision": {
            "exact_preexisting_learner_content_reusable": False,
            "candidate_specific_content_gap_proven": True,
            "new_original_learner_content_required": True,
            "proposed_bounded_semantic_id": PROPOSED_SEMANTIC,
            "semantic_admission_by_this_review": False,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "false_exact_mastery_admissions": 0,
        },
        "policy": {
            "adjacent_contextual_meaning_unit_can_emit_contextual_synonym_mastery": False,
            "historical_task25_product_card_is_sufficient_new_content": False,
            "official_fipi_wording_may_be_copied_into_learner_content": False,
            "learner_examples_must_be_original_eksamio": True,
            "generic_task25_result_can_emit_exact_component_mastery": False,
            "component_specific_independent_verification_required": True,
            "content_gap_review_is_subject_semantic_admission": False,
        },
        "summary": {
            "preexisting_ru03_content_files_reviewed": len(files),
            "preexisting_ru03_units_reviewed": len(units),
            "exact_candidate_content_matches": 0,
            "candidate_specific_content_gaps": 1,
            "semantic_admissions": 0,
            "new_school_canonical_identities": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "false_exact_mastery_admissions": 0,
        },
        "next_exact_work": {
            "required_step": "CREATE_ORIGINAL_EXACT_CANDIDATE_015_LEARNER_UNIT_THEN_VALIDATE_THEN_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE",
            "semantic_admission_allowed_from_gap_review_alone": False,
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
        print("RU03_CONTEXTUAL_SYNONYM_CONTENT_GAP_REVIEW=PASS")
        print(f"PREEXISTING_RU03_CONTENT_FILES_REVIEWED={result['summary']['preexisting_ru03_content_files_reviewed']}")
        print(f"PREEXISTING_RU03_UNITS_REVIEWED={result['summary']['preexisting_ru03_units_reviewed']}")
        print("EXACT_CANDIDATE_CONTENT_MATCHES=0")
        print("CANDIDATE_SPECIFIC_CONTENT_GAPS=1")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_CLOSURES=0/0")
        print("FALSE_EXACT_MASTERY=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
