#!/usr/bin/env python3
"""Fail-closed source-backed owner resolution for RU01 phonetic transcription."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v10.py"
BINDING = HERE / "build_ru01_phonetics_exact_object_binding_review.py"
CONTENT = HERE.parent / "production-learning-content" / "RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"

CURRENT_SHA = "e770aa9528d4db14b3be8a703bc3f6fcbd195787a34e851532ebc4649c96f9b1"
BINDING_SHA = "9e903409896463f350eb06e7bf5874eaaf9f1e21037c76f7c9c4b9e53831613e"
TARGET_UNIT = "RAU-2725ee5b709b70502748"
TARGET_REQUIREMENT = "RSK-EDSOO59-4-1-4-P187"
SOURCE_ID = "EDSOO-RU-5-9-2025"
DOCUMENT_ID = "EDSOO59"
DOCUMENT_SHA256 = "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d"
PAGE = 187
CODE = "4.1.4"
SOURCE_LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.4"
SOURCE_LABEL_RU = "Элементы фонетической транскрипции"
SOURCE_SIGNATURE = "PHONETIC_TRANSCRIPTION"
BLOCKER = "TRANSCRIPTION_SEMANTIC_REQUIRED"
CANDIDATE = "ru-phonetics-phonetic-transcription-elements"

EXPECTED_EXISTING_RU01 = {
    "ru-phonetics-sound-letter-relation",
    "ru-phonetics-vowel-consonant-features",
    "ru-phonetics-word-analysis-sequence",
}
EXPECTED_CONTENT_IDS = EXPECTED_EXISTING_RU01


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_resolution() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v10 normalized SHA drift")
    summary = current.get("progress_summary") or {}
    expected_summary = {
        "subject_disposed_units_total": 37,
        "subject_disposed_requirements_total": 37,
        "subject_review_units_remaining": 1279,
        "subject_review_requirements_remaining": 1354,
        "accepted_bounded_ru_semantics_total": 75,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            raise ValueError(f"current-v10 aggregate drift: {key}")
    if len(current.get("accepted_authorities") or []) != 57:
        raise ValueError("current-v10 accepted authority count drift")

    binding = runpy.run_path(str(BINDING))["build_review"]()
    if binding.get("normalized_sha256") != BINDING_SHA:
        raise ValueError("RU01 exact object-binding review drift")
    if set(binding.get("accepted_semantic_ids") or []) != EXPECTED_EXISTING_RU01:
        raise ValueError("RU01 accepted semantic owner set drift")
    records = [
        row for row in binding.get("records") or []
        if row.get("admission_unit_id") == TARGET_UNIT
        and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(records) != 1:
        raise ValueError("target transcription source object is not uniquely bound")
    record = records[0]
    exact_record = {
        "source_id": SOURCE_ID,
        "document_id": DOCUMENT_ID,
        "document_sha256": DOCUMENT_SHA256,
        "page": PAGE,
        "code": CODE,
        "source_locator": SOURCE_LOCATOR,
        "normalized_source_signature": SOURCE_SIGNATURE,
        "review_classification": "PENDING",
        "accepted_semantic_refs": [],
        "blocker_or_reroute": BLOCKER,
    }
    for key, value in exact_record.items():
        if record.get(key) != value:
            raise ValueError(f"target transcription source identity drift: {key}")

    outcomes = [
        row for row in binding.get("unit_outcomes") or []
        if row.get("admission_unit_id") == TARGET_UNIT
    ]
    if len(outcomes) != 1 or outcomes[0].get("unit_review_outcome") != "PENDING_EXACT_DECOMPOSITION":
        raise ValueError("target transcription object is no longer pending exact decomposition")
    if TARGET_REQUIREMENT not in (outcomes[0].get("requirement_ids") or []):
        raise ValueError("target transcription requirement missing from pending unit")

    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    units = [row for row in content.get("units") or [] if isinstance(row, dict)]
    content_ids = {str(row.get("proposed_semantic_id")) for row in units}
    if content_ids != EXPECTED_CONTENT_IDS:
        raise ValueError("RU01 production-learning semantic content set drift")
    if CANDIDATE in content_ids:
        raise ValueError("transcription candidate unexpectedly already has dedicated learner content")

    word_analysis = [row for row in units if row.get("proposed_semantic_id") == "ru-phonetics-word-analysis-sequence"]
    if len(word_analysis) != 1:
        raise ValueError("word-analysis learner unit drift")
    wa = word_analysis[0]
    verification = [row for row in wa.get("independent_verification") or [] if isinstance(row, dict)]
    if [row.get("id") for row in verification] != ["p01-u3-v1", "p01-u3-v2"]:
        raise ValueError("word-analysis independent evidence identity drift")
    verification_text = canonical_json(verification).decode("utf-8").lower()
    if "транскрип" in verification_text or "transcript" in verification_text:
        raise ValueError("word-analysis evidence unexpectedly became transcription-specific")
    forbidden = [str(x).lower() for x in ((wa.get("tutor_grounding") or {}).get("forbidden") or [])]
    if not any("транскрип" in x for x in forbidden):
        raise ValueError("word-analysis transcription safety boundary drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_PHONETIC_TRANSCRIPTION_SOURCE_BACKED_CANDIDATE_RESOLVED_NOT_ACCEPTED",
        "module_id": "RU-PROG-01",
        "current_launch_progress_v10_normalized_sha256": CURRENT_SHA,
        "exact_object_binding_review_normalized_sha256": BINDING_SHA,
        "target": {
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "source_id": SOURCE_ID,
            "document_id": DOCUMENT_ID,
            "document_sha256": DOCUMENT_SHA256,
            "page": PAGE,
            "code": CODE,
            "source_locator": SOURCE_LOCATOR,
            "source_label_ru": SOURCE_LABEL_RU,
            "normalized_source_signature": SOURCE_SIGNATURE,
            "prior_review_classification": "PENDING",
            "prior_blocker": BLOCKER,
        },
        "exact_current_owner_search": {
            "accepted_ru01_semantic_ids_checked": sorted(EXPECTED_EXISTING_RU01),
            "exact_current_owner_found": False,
            "reason": "Exact RU01 binding review has no accepted semantic ref for this source object and explicitly requires a transcription semantic; none of the three accepted RU01 owners is transcription-specific.",
            "keyword_title_route_task_or_embedding_inference_used": False,
        },
        "candidate_resolution": {
            "candidate_semantic_id": CANDIDATE,
            "candidate_label_ru": "Элементы фонетической транскрипции: объяснить произношение и написание с помощью учебной транскрипции",
            "resolution": "SOURCE_BACKED_NEW_SUBJECT_SEMANTIC_CANDIDATE_REQUIRED",
            "canonical_subject_semantic_admitted": False,
            "school_canonical_identity_created": False,
            "source_basis": {
                "official_requirement": SOURCE_LABEL_RU,
                "official_program_scope": "Изменение звуков в речевом потоке. Элементы фонетической транскрипции.",
                "official_learning_action": "Объяснять с помощью элементов транскрипции особенности произношения и написания слов.",
            },
        },
        "content_and_evidence_gap": {
            "dedicated_candidate_content_unit_present": False,
            "dedicated_candidate_independent_verification_present": False,
            "word_analysis_evidence_may_substitute": False,
            "word_analysis_evidence_ids_checked": ["p01-u3-v1", "p01-u3-v2"],
            "required_next_evidence": "Create original learner content and independent verification that requires reading/using elementary phonetic transcription to explain pronunciation-vs-spelling; then run separate semantic acceptance.",
        },
        "policy": {
            "resolution_is_semantic_acceptance": False,
            "resolution_is_object_acceptance": False,
            "source_prose_may_be_copied_into_learner_content": False,
            "candidate_id_is_canonical_before_separate_acceptance": False,
            "shared_word_analysis_evidence_can_close_transcription": False,
            "sibling_source_objects_auto_closed": False,
            "whole_group_acceptance_allowed": False,
            "false_exact_mastery_admissions": 0,
        },
        "summary": {
            "pending_source_objects_resolved_to_exact_existing_owner": 0,
            "source_backed_new_semantic_candidates": 1,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "new_school_canonical_identities": 0,
            "false_exact_mastery_admissions": 0,
            "current_subject_review_units_remaining": 1279,
            "current_subject_review_requirements_remaining": 1354,
        },
        "next_exact_work": {
            "candidate_semantic_id": CANDIDATE,
            "learner_content_required": True,
            "component_specific_independent_evidence_required": True,
            "separate_semantic_acceptance_required": True,
            "separate_object_acceptance_required_after_semantic_acceptance": True,
            "target_remains_pending_until_all_gates_pass": True,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_resolution()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU01_PHONETIC_TRANSCRIPTION_OWNER_RESOLUTION=PASS")
        print("EXACT_CURRENT_OWNER_FOUND=0")
        print("SOURCE_BACKED_NEW_SEMANTIC_CANDIDATES=1")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
