#!/usr/bin/env python3
"""Fail-closed learner-content and evidence readiness for RU01 phonetic transcription."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
OWNER_RESOLUTION = HERE / "build_ru01_phonetic_transcription_owner_resolution.py"
CONTENT = HERE.parent / "production-learning-content" / "RU-PROG-01-PHONETIC-TRANSCRIPTION-WAVE-002-v0.1.json"
BASE_CONTENT = HERE.parent / "production-learning-content" / "RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"

CANDIDATE = "ru-phonetics-phonetic-transcription-elements"
TARGET_UNIT = "RAU-2725ee5b709b70502748"
TARGET_REQUIREMENT = "RSK-EDSOO59-4-1-4-P187"
EXPECTED_VERIFICATION_IDS = [f"p01-u4-v{i}" for i in range(1, 6)]
WORD_ANALYSIS_VERIFICATION_IDS = ["p01-u3-v1", "p01-u3-v2"]
EXPECTED_SKILLS = {
    "sound_not_letter",
    "iotated_fragment",
    "softness_marker",
    "explain_spelling_pronunciation_relation",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_readiness() -> dict[str, Any]:
    predecessor = runpy.run_path(str(OWNER_RESOLUTION))["build_resolution"]()
    if predecessor.get("status") != "CENTRAL_BRAIN_RU01_PHONETIC_TRANSCRIPTION_SOURCE_BACKED_CANDIDATE_RESOLVED_NOT_ACCEPTED":
        raise ValueError("owner-resolution predecessor status drift")
    target = predecessor.get("target") or {}
    if target.get("admission_unit_id") != TARGET_UNIT or target.get("requirement_id") != TARGET_REQUIREMENT:
        raise ValueError("owner-resolution target drift")
    candidate = predecessor.get("candidate_resolution") or {}
    if candidate.get("candidate_semantic_id") != CANDIDATE:
        raise ValueError("owner-resolution candidate drift")
    if candidate.get("canonical_subject_semantic_admitted") is not False:
        raise ValueError("candidate unexpectedly canonical before content readiness")
    if predecessor.get("summary", {}).get("semantic_admissions") != 0:
        raise ValueError("predecessor already admits semantic")
    if predecessor.get("summary", {}).get("object_level_admission_units_closed") != 0:
        raise ValueError("predecessor already closes object")

    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    if data.get("schema_version") != "0.1.0":
        raise ValueError("content schema drift")
    if data.get("status") != "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED":
        raise ValueError("content status drift")
    if data.get("subject") != "russian" or data.get("module_id") != "RU-PROG-01":
        raise ValueError("content module drift")

    boundary = data.get("identity_boundary") or {}
    if boundary.get("proposed_semantic_id") != CANDIDATE:
        raise ValueError("content candidate id drift")
    if boundary.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("content became canonical without semantic acceptance")
    if boundary.get("word_analysis_semantic_may_substitute") is not False:
        raise ValueError("word-analysis substitution opened")
    if boundary.get("normative_pronunciation_semantic_may_substitute") is not False:
        raise ValueError("pronunciation substitution opened")
    if boundary.get("normative_stress_semantic_may_substitute") is not False:
        raise ValueError("stress substitution opened")
    if boundary.get("generic_ru01_result_can_emit_exact_component_mastery") is not False:
        raise ValueError("generic RU01 exact mastery opened")

    official = [
        row for row in data.get("source_provenance") or []
        if isinstance(row, dict) and row.get("kind") == "official_program"
    ]
    if len(official) != 1:
        raise ValueError("official transcription source pin must be unique")
    official = official[0]
    expected_official = {
        "document_id": "EDSOO59",
        "document_sha256": "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d",
        "page": 187,
        "code": "4.1.4",
        "official_requirement": "Элементы фонетической транскрипции",
        "official_learning_action": "Объяснять с помощью элементов транскрипции особенности произношения и написания слов.",
    }
    for key, value in expected_official.items():
        if official.get(key) != value:
            raise ValueError(f"official source pin drift: {key}")

    units = [row for row in data.get("units") or [] if isinstance(row, dict)]
    if len(units) != 1 or units[0].get("proposed_semantic_id") != CANDIDATE:
        raise ValueError("transcription learner unit must be singular and exact")
    unit = units[0]

    verification = [row for row in unit.get("independent_verification") or [] if isinstance(row, dict)]
    verification_ids = [str(row.get("id")) for row in verification]
    if verification_ids != EXPECTED_VERIFICATION_IDS:
        raise ValueError("transcription independent verification identity drift")
    if len(set(verification_ids)) != len(verification_ids):
        raise ValueError("duplicate transcription verification ids")
    skills = {str(row.get("skill")) for row in verification}
    if skills != EXPECTED_SKILLS:
        raise ValueError("transcription verification skill coverage drift")
    if sum(1 for row in verification if row.get("type") == "constructed_response") < 2:
        raise ValueError("transcription evidence needs independent constructed responses")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("PEIS semantic status drift")
    if peis.get("verification_ids") != EXPECTED_VERIFICATION_IDS:
        raise ValueError("PEIS evidence ids drift")
    if peis.get("mastery_emission_before_semantic_acceptance") is not False:
        raise ValueError("semantic mastery emitted before acceptance")
    if peis.get("object_mastery_emission_before_exact_object_acceptance") is not False:
        raise ValueError("object mastery emitted before exact acceptance")

    base = json.loads(BASE_CONTENT.read_text(encoding="utf-8"))
    word_analysis = [
        row for row in base.get("units") or []
        if isinstance(row, dict) and row.get("proposed_semantic_id") == "ru-phonetics-word-analysis-sequence"
    ]
    if len(word_analysis) != 1:
        raise ValueError("word-analysis learner unit drift")
    old_ids = [
        str(row.get("id"))
        for row in word_analysis[0].get("independent_verification") or []
        if isinstance(row, dict)
    ]
    if old_ids != WORD_ANALYSIS_VERIFICATION_IDS:
        raise ValueError("word-analysis evidence identity drift")
    overlap = sorted(set(old_ids) & set(verification_ids))
    if overlap:
        raise ValueError("word-analysis evidence reused for transcription")

    forbidden = [str(x).lower() for x in ((unit.get("tutor_grounding") or {}).get("forbidden") or [])]
    required_forbidden_fragments = [
        "disputed pronunciation",
        "normative stress",
        "p01-u3-v1",
        "semantic acceptance",
        TARGET_REQUIREMENT.lower(),
    ]
    for fragment in required_forbidden_fragments:
        if not any(fragment in item for item in forbidden):
            raise ValueError(f"tutor fail-closed boundary missing: {fragment}")

    release = data.get("release_boundary") or {}
    if release != {
        "semantic_acceptance_effect": "NONE",
        "object_acceptance_effect": "NONE",
        "school_canonical_identity_created": False,
        "false_exact_mastery_admissions": 0,
        "public_runtime_change": False,
        "production_peis_write": False,
    }:
        raise ValueError("release boundary drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_PHONETIC_TRANSCRIPTION_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED",
        "module_id": "RU-PROG-01",
        "candidate_semantic_id": CANDIDATE,
        "owner_resolution_normalized_sha256": predecessor.get("normalized_sha256"),
        "content_sha256": sha256_path(CONTENT),
        "target": {
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "source_locator": "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.4",
        },
        "learner_content": {
            "dedicated_candidate_content_unit_present": True,
            "original_eksamio_content": True,
            "independent_verification_ids": verification_ids,
            "independent_verification_count": len(verification_ids),
            "covered_skills": sorted(skills),
        },
        "evidence_independence": {
            "word_analysis_evidence_ids_checked": old_ids,
            "transcription_evidence_ids": verification_ids,
            "overlap": overlap,
            "word_analysis_evidence_reused": False,
            "generic_ru01_evidence_can_substitute": False,
        },
        "policy": {
            "content_readiness_is_semantic_acceptance": False,
            "content_readiness_is_object_acceptance": False,
            "candidate_is_canonical_before_separate_acceptance": False,
            "shared_word_analysis_evidence_can_close_transcription": False,
            "normative_pronunciation_or_stress_inferred": False,
            "sibling_source_objects_auto_closed": False,
            "false_exact_mastery_admissions": 0,
        },
        "current_launch_aggregate_unchanged": {
            "accepted_authorities": 57,
            "subject_disposed_units_total": 37,
            "subject_review_units_remaining": 1279,
            "subject_review_requirements_remaining": 1354,
            "false_exact_mastery_admissions": 0,
        },
        "summary": {
            "dedicated_candidate_content_units": 1,
            "component_specific_independent_verification_items": len(verification_ids),
            "word_analysis_evidence_reused": 0,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "new_school_canonical_identities": 0,
            "false_exact_mastery_admissions": 0,
        },
        "next_exact_work": {
            "separate_semantic_acceptance_required": True,
            "semantic_acceptance_must_bind_only_component_specific_evidence": True,
            "separate_object_acceptance_required_after_semantic_acceptance": True,
            "target_remains_pending_until_both_acceptance_gates_pass": True,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_readiness()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU01_PHONETIC_TRANSCRIPTION_CONTENT_READINESS=PASS")
        print("DEDICATED_CONTENT_UNITS=1")
        print("COMPONENT_SPECIFIC_INDEPENDENT_VERIFICATION_ITEMS=5")
        print("WORD_ANALYSIS_EVIDENCE_REUSED=0")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
