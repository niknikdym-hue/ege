#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE / "RU01-PHONETIC-TRANSCRIPTION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
READINESS = HERE / "build_ru01_phonetic_transcription_content_readiness.py"

SEMANTIC = "ru-phonetics-phonetic-transcription-elements"
TAXONOMY = "phonetic_transcription_elements"
TARGET_UNIT = "RAU-2725ee5b709b70502748"
TARGET_REQUIREMENT = "RSK-EDSOO59-4-1-4-P187"
SOURCE_LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.4"
VERIFICATION_IDS = [f"p01-u4-v{i}" for i in range(1, 6)]
COVERED_SKILLS = [
    "sound_not_letter",
    "iotated_fragment",
    "softness_marker",
    "explain_spelling_pronunciation_relation",
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def main() -> int:
    readiness = runpy.run_path(str(READINESS))["build_readiness"]()
    if readiness.get("status") != "CENTRAL_BRAIN_RU01_PHONETIC_TRANSCRIPTION_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED":
        raise AssertionError("transcription readiness predecessor drift")
    if readiness.get("candidate_semantic_id") != SEMANTIC:
        raise AssertionError("transcription candidate identity drift")
    if readiness.get("target") != {
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQUIREMENT,
        "source_locator": SOURCE_LOCATOR,
    }:
        raise AssertionError("transcription target identity drift")

    learner = readiness.get("learner_content") or {}
    if learner.get("dedicated_candidate_content_unit_present") is not True:
        raise AssertionError("dedicated transcription learner content missing")
    if learner.get("original_eksamio_content") is not True:
        raise AssertionError("transcription learner content is not original Eksamio content")
    if learner.get("independent_verification_ids") != VERIFICATION_IDS:
        raise AssertionError("transcription evidence identity drift")
    if learner.get("independent_verification_count") != 5:
        raise AssertionError("transcription evidence count drift")
    if set(learner.get("covered_skills") or []) != set(COVERED_SKILLS):
        raise AssertionError("transcription skill coverage drift")

    independence = readiness.get("evidence_independence") or {}
    if independence.get("word_analysis_evidence_ids_checked") != ["p01-u3-v1", "p01-u3-v2"]:
        raise AssertionError("word-analysis predecessor evidence drift")
    if independence.get("transcription_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("transcription evidence set drift")
    if independence.get("overlap") != [] or independence.get("word_analysis_evidence_reused") is not False:
        raise AssertionError("word-analysis evidence reused for transcription")
    if independence.get("generic_ru01_evidence_can_substitute") is not False:
        raise AssertionError("generic RU01 evidence substitution opened")

    readiness_policy = readiness.get("policy") or {}
    for key in (
        "content_readiness_is_semantic_acceptance",
        "content_readiness_is_object_acceptance",
        "candidate_is_canonical_before_separate_acceptance",
        "shared_word_analysis_evidence_can_close_transcription",
        "normative_pronunciation_or_stress_inferred",
        "sibling_source_objects_auto_closed",
    ):
        if readiness_policy.get(key) is not False:
            raise AssertionError(f"pre-acceptance fail-closed boundary drift: {key}")
    if readiness_policy.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("pre-acceptance false exact mastery drift")
    if readiness.get("current_launch_aggregate_unchanged") != {
        "accepted_authorities": 57,
        "subject_disposed_units_total": 37,
        "subject_review_units_remaining": 1279,
        "subject_review_requirements_remaining": 1354,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("current-v10 predecessor aggregate drift")

    acceptance = load(ACCEPTANCE)
    if acceptance.get("schema_version") != "0.1.0":
        raise AssertionError("acceptance schema drift")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("transcription semantic acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("transcription semantic authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("transcription acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("transcription acceptance created a parallel registry")

    authority = acceptance.get("authority") or {}
    expected_authority = {
        "owner_resolution_builder": "russian-program/subject-admission/build_ru01_phonetic_transcription_owner_resolution.py",
        "content_readiness_builder": "russian-program/subject-admission/build_ru01_phonetic_transcription_content_readiness.py",
        "learner_content": "russian-program/production-learning-content/RU-PROG-01-PHONETIC-TRANSCRIPTION-WAVE-002-v0.1.json",
        "target_admission_unit_id": TARGET_UNIT,
        "target_requirement_id": TARGET_REQUIREMENT,
        "source_locator": SOURCE_LOCATOR,
    }
    if authority != expected_authority:
        raise AssertionError("transcription acceptance authority binding drift")

    policy = acceptance.get("policy") or {}
    required_true = (
        "exact_source_backed_owner_resolution_required",
        "original_dedicated_learner_content_required",
        "component_specific_independent_evidence_required",
        "parallel_registry_creation_forbidden",
        "separate_exact_object_acceptance_required",
    )
    for key in required_true:
        if policy.get(key) is not True:
            raise AssertionError(f"transcription acceptance policy weakened: {key}")
    required_false = (
        "word_analysis_evidence_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "normative_stress_semantic_may_substitute",
        "route_title_task_number_keyword_or_embedding_can_admit_semantics",
        "canonical_school_registry_mutation_required",
        "content_or_evidence_presence_alone_is_semantic_admission",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "generic_ru01_result_can_emit_exact_component_mastery",
        "shared_evidence_can_close_sibling_source_objects",
        "whole_group_acceptance_allowed",
    )
    for key in required_false:
        if policy.get(key) is not False:
            raise AssertionError(f"transcription acceptance policy opened: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("transcription acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("transcription semantic crosswalk drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("transcription semantic not explicitly accepted")
    if decision.get("owner_search_result") != "NO_EXACT_CURRENT_TRANSCRIPTION_OWNER":
        raise AssertionError("transcription owner-search result drift")
    if decision.get("source_evidence_status") != "confirmed":
        raise AssertionError("transcription source evidence not confirmed")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("accepted transcription evidence identity drift")
    if decision.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("accepted transcription skill boundary drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("semantic acceptance improperly closes exact object")
    guard = str(decision.get("boundary_guard") or "")
    for fragment in ("normative pronunciation or stress", "generic phonetic word-analysis substitution", "separate exact object-binding acceptance"):
        if fragment not in guard:
            raise AssertionError(f"transcription boundary guard drift: {fragment}")

    if acceptance.get("summary") != {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("transcription semantic acceptance summary drift")

    duplicates = []
    for path in HERE.glob("*.json"):
        if path == ACCEPTANCE:
            continue
        try:
            value = load(path)
        except Exception:
            continue
        decisions = value.get("decisions")
        if not isinstance(decisions, list):
            continue
        if any(isinstance(row, dict) and row.get("accepted_semantic_id") == SEMANTIC for row in decisions):
            duplicates.append(path.name)
    if duplicates:
        raise AssertionError(f"duplicate transcription semantic acceptance: {duplicates}")

    print("RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SUBJECT_SEMANTICS=1")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("INDEPENDENT_EVIDENCE_ITEMS=5")
    print("WORD_ANALYSIS_EVIDENCE_REUSED=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
