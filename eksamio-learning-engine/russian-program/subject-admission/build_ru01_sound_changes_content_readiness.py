#!/usr/bin/env python3
"""Fail-closed learner-content and evidence readiness for RU01 sound changes in speech flow."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REVIEW = HERE / "RU01-SOUND-CHANGES-EXACT-SOURCE-BINDING-REVIEW-v0.1.json"
CONTENT = HERE.parent / "production-learning-content" / "RU-PROG-01-SOUND-CHANGES-WAVE-003-v0.1.json"
BASE_CONTENT = HERE.parent / "production-learning-content" / "RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"
TRANSCRIPTION_CONTENT = HERE.parent / "production-learning-content" / "RU-PROG-01-PHONETIC-TRANSCRIPTION-WAVE-002-v0.1.json"
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v13.py"

CANDIDATE = "ru-phonetics-sound-changes-in-speech-flow"
TARGETS = {
    ("RAU-b1ba48cb81e96255122a", "RSK-EDSOO59-4-1-3-P187", "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.3"),
    ("RAU-f709f1855bb0b8d104bc", "RSK-OGE_COD-4-1-3-P021", "FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.3"),
}
EXPECTED_VERIFICATION_IDS = [f"p01-u5-v{i}" for i in range(1, 7)]
EXPECTED_SKILLS = {
    "identify_contextual_sound_change",
    "compare_base_and_realized_sound",
    "explain_trigger_and_result",
    "distinguish_change_from_static_feature",
    "distinguish_sound_change_from_adjacent_semantics",
    "recognize_fail_closed_normative_boundary",
}
ADJACENT_EVIDENCE_IDS = {
    "p01-u1-v1", "p01-u1-v2",
    "p01-u2-v1", "p01-u2-v2",
    "p01-u3-v1", "p01-u3-v2",
    "p01-u4-v1", "p01-u4-v2", "p01-u4-v3", "p01-u4-v4", "p01-u4-v5",
}
CURRENT_SHA = "f8c8c1f060eb596fc92c317b38d1c12e572a8827cb56042390ed08b0f681a426"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_readiness() -> dict[str, Any]:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    if review.get("status") != "CENTRAL_BRAIN_RU01_SOUND_CHANGES_NO_EXACT_CURRENT_OWNER_SOURCE_BACKED_CANDIDATE_NOT_ACCEPTED":
        raise ValueError("source-binding review status drift")
    if review.get("source_signature") != "SOUND_CHANGES_IN_SPEECH_FLOW":
        raise ValueError("source signature drift")
    search = review.get("current_exact_owner_search") or {}
    if search.get("workflow_run") != 34209909668 or search.get("workflow_conclusion") != "SUCCESS":
        raise ValueError("exact-owner search is not proven")
    if search.get("artifact_normalized_sha256") != "3856594b8952f73d49bb1ce0f952e9ae408be5d1ee9ea5c19c80baf8ac5bef08":
        raise ValueError("exact-owner search artifact drift")
    resolution = review.get("resolution") or {}
    if resolution.get("exact_current_canonical_owner_with_component_specific_evidence_found") is not False:
        raise ValueError("unexpected exact current owner")
    if resolution.get("candidate_semantic_id") != CANDIDATE or resolution.get("candidate_status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("source-backed candidate drift")
    target_rows = {
        (str(row.get("admission_unit_id")), str(row.get("requirement_id")), str(row.get("source_locator")))
        for row in review.get("targets") or [] if isinstance(row, dict)
    }
    if target_rows != TARGETS:
        raise ValueError("source target drift")
    boundary = review.get("decision_boundary") or {}
    if boundary.get("review_is_semantic_acceptance") is not False or boundary.get("review_is_object_acceptance") is not False:
        raise ValueError("source review unexpectedly accepts")
    if boundary.get("false_exact_mastery") != 0:
        raise ValueError("source review false exact mastery drift")

    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v13 normalized sha drift")
    summary = current.get("progress_summary") or {}
    expected_current = {
        "accepted_authorities": 60,
        "subject_disposed_units_total": 39,
        "subject_disposed_requirements_total": 39,
        "subject_review_units_remaining": 1277,
        "subject_review_requirements_remaining": 1352,
        "accepted_bounded_ru_subject_semantics": 67,
        "accepted_bounded_ru_semantics_total": 76,
        "false_exact_mastery_admissions": 0,
    }
    if len(current.get("accepted_authorities") or []) != expected_current["accepted_authorities"]:
        raise ValueError("accepted authority count drift")
    for key, value in expected_current.items():
        if key == "accepted_authorities":
            continue
        if summary.get(key) != value:
            raise ValueError(f"current-v13 aggregate drift: {key}")

    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    if data.get("schema_version") != "0.1.0" or data.get("status") != "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED":
        raise ValueError("content status/schema drift")
    if data.get("subject") != "russian" or data.get("module_id") != "RU-PROG-01":
        raise ValueError("content module drift")

    official = [row for row in data.get("source_provenance") or [] if isinstance(row, dict) and row.get("kind") in {"official_program", "official_codifier"}]
    if len(official) != 2:
        raise ValueError("sound-changes content must pin both exact official source objects")
    official_by_doc = {str(row.get("document_id")): row for row in official}
    expected_official = {
        "EDSOO59": {
            "document_sha256": "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d",
            "page": 187,
            "code": "4.1.3",
            "official_requirement": "Изменения звуков в речевом потоке",
        },
        "OGE_COD": {
            "document_sha256": "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a",
            "page": 21,
            "code": "4.1.3",
            "official_requirement": "Изменения звуков в речевом потоке",
        },
    }
    if set(official_by_doc) != set(expected_official):
        raise ValueError("official source document set drift")
    for document_id, expected in expected_official.items():
        for key, value in expected.items():
            if official_by_doc[document_id].get(key) != value:
                raise ValueError(f"official source pin drift: {document_id}:{key}")

    identity = data.get("identity_boundary") or {}
    if identity.get("proposed_semantic_id") != CANDIDATE or identity.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise ValueError("candidate identity drift")
    for key in (
        "sound_letter_relation_semantic_may_substitute",
        "vowel_consonant_features_semantic_may_substitute",
        "word_analysis_semantic_may_substitute",
        "phonetic_transcription_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "normative_stress_semantic_may_substitute",
        "generic_ru01_result_can_emit_exact_component_mastery",
    ):
        if identity.get(key) is not False:
            raise ValueError(f"fail-closed identity boundary opened: {key}")

    units = [row for row in data.get("units") or [] if isinstance(row, dict)]
    if len(units) != 1 or units[0].get("proposed_semantic_id") != CANDIDATE:
        raise ValueError("sound-changes learner unit must be singular and exact")
    unit = units[0]
    verification = [row for row in unit.get("independent_verification") or [] if isinstance(row, dict)]
    verification_ids = [str(row.get("id")) for row in verification]
    if verification_ids != EXPECTED_VERIFICATION_IDS or len(set(verification_ids)) != len(verification_ids):
        raise ValueError("sound-changes verification identity drift")
    skills = {str(row.get("skill")) for row in verification}
    if skills != EXPECTED_SKILLS:
        raise ValueError("sound-changes verification skill coverage drift")
    if sum(1 for row in verification if row.get("type") == "constructed_response") < 4:
        raise ValueError("sound-changes evidence needs at least four constructed responses")
    overlap = sorted(set(verification_ids) & ADJACENT_EVIDENCE_IDS)
    if overlap:
        raise ValueError("adjacent RU01 evidence reused for sound changes")

    base = json.loads(BASE_CONTENT.read_text(encoding="utf-8"))
    base_ids = {
        str(item.get("id"))
        for row in base.get("units") or [] if isinstance(row, dict)
        for item in row.get("independent_verification") or [] if isinstance(item, dict)
    }
    transcription = json.loads(TRANSCRIPTION_CONTENT.read_text(encoding="utf-8"))
    transcription_ids = {
        str(item.get("id"))
        for row in transcription.get("units") or [] if isinstance(row, dict)
        for item in row.get("independent_verification") or [] if isinstance(item, dict)
    }
    if not {"p01-u1-v1", "p01-u1-v2", "p01-u2-v1", "p01-u2-v2", "p01-u3-v1", "p01-u3-v2"}.issubset(base_ids):
        raise ValueError("base RU01 evidence identity drift")
    if transcription_ids != {"p01-u4-v1", "p01-u4-v2", "p01-u4-v3", "p01-u4-v4", "p01-u4-v5"}:
        raise ValueError("transcription evidence identity drift")
    all_adjacent = base_ids | transcription_ids
    if set(verification_ids) & all_adjacent:
        raise ValueError("existing RU01 verification IDs overlap new evidence")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("verification_ids") != EXPECTED_VERIFICATION_IDS:
        raise ValueError("PEIS evidence identity/status drift")
    if peis.get("mastery_emission_before_semantic_acceptance") is not False:
        raise ValueError("semantic mastery emitted before acceptance")
    if peis.get("object_mastery_emission_before_exact_object_acceptance") is not False:
        raise ValueError("object mastery emitted before exact object acceptance")
    if peis.get("false_exact_mastery_admissions") != 0:
        raise ValueError("PEIS false exact mastery drift")

    forbidden = [str(x).lower() for x in ((unit.get("tutor_grounding") or {}).get("forbidden") or [])]
    required_forbidden_fragments = [
        "normative-pronunciation authority",
        "normative stress",
        "p01-u1-v1",
        "semantic acceptance",
        "rsk-edsoo59-4-1-3-p187",
        "rsk-oge_cod-4-1-3-p021",
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
        "status": "CENTRAL_BRAIN_RU01_SOUND_CHANGES_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED",
        "module_id": "RU-PROG-01",
        "candidate_semantic_id": CANDIDATE,
        "source_binding_review_sha256": sha256_path(REVIEW),
        "content_sha256": sha256_path(CONTENT),
        "targets": [
            {"admission_unit_id": unit_id, "requirement_id": requirement_id, "source_locator": locator}
            for unit_id, requirement_id, locator in sorted(TARGETS)
        ],
        "learner_content": {
            "dedicated_candidate_content_unit_present": True,
            "original_eksamio_content": True,
            "independent_verification_ids": verification_ids,
            "independent_verification_count": len(verification_ids),
            "covered_skills": sorted(skills),
        },
        "evidence_independence": {
            "adjacent_existing_evidence_ids_checked": sorted(ADJACENT_EVIDENCE_IDS),
            "sound_changes_evidence_ids": verification_ids,
            "overlap": overlap,
            "adjacent_semantic_evidence_reused": False,
            "generic_ru01_evidence_can_substitute": False,
        },
        "policy": {
            "content_readiness_is_semantic_acceptance": False,
            "content_readiness_is_object_acceptance": False,
            "candidate_is_canonical_before_separate_acceptance": False,
            "shared_future_evidence_can_close_both_source_objects_without_separate_object_acceptance": False,
            "normative_pronunciation_or_stress_inferred": False,
            "sibling_source_objects_auto_closed": False,
            "false_exact_mastery_admissions": 0,
        },
        "current_launch_aggregate_unchanged": expected_current,
        "summary": {
            "dedicated_candidate_content_units": 1,
            "component_specific_independent_verification_items": len(verification_ids),
            "adjacent_semantic_evidence_reused": 0,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "new_school_canonical_identities": 0,
            "false_exact_mastery_admissions": 0,
        },
        "next_exact_work": {
            "separate_semantic_acceptance_required": True,
            "semantic_acceptance_must_bind_only_component_specific_evidence": True,
            "separate_object_acceptance_required_after_semantic_acceptance_for_each_target": True,
            "target_count_requiring_separate_object_acceptance": 2,
            "targets_remain_pending_until_their_own_acceptance_gates_pass": True,
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
        print("RU01_SOUND_CHANGES_CONTENT_READINESS=PASS")
        print("DEDICATED_CONTENT_UNITS=1")
        print("COMPONENT_SPECIFIC_INDEPENDENT_VERIFICATION_ITEMS=6")
        print("ADJACENT_SEMANTIC_EVIDENCE_REUSED=0")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
