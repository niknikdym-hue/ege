#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE / "RU01-SOUND-CHANGES-IN-SPEECH-FLOW-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
READINESS = HERE / "build_ru01_sound_changes_content_readiness.py"

SEMANTIC = "ru-phonetics-sound-changes-in-speech-flow"
TAXONOMY = "sound_changes_in_speech_flow"
VERIFICATION_IDS = [f"p01-u5-v{i}" for i in range(1, 7)]
COVERED_SKILLS = [
    "identify_contextual_sound_change",
    "compare_base_and_realized_sound",
    "explain_trigger_and_result",
    "distinguish_change_from_static_feature",
    "distinguish_sound_change_from_adjacent_semantics",
    "recognize_fail_closed_normative_boundary",
]
TARGETS = [
    {
        "admission_unit_id": "RAU-b1ba48cb81e96255122a",
        "requirement_id": "RSK-EDSOO59-4-1-3-P187",
        "source_locator": "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.3",
    },
    {
        "admission_unit_id": "RAU-f709f1855bb0b8d104bc",
        "requirement_id": "RSK-OGE_COD-4-1-3-P021",
        "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.3",
    },
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def main() -> int:
    readiness = runpy.run_path(str(READINESS))["build_readiness"]()
    if readiness.get("status") != "CENTRAL_BRAIN_RU01_SOUND_CHANGES_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED":
        raise AssertionError("sound-changes readiness predecessor drift")
    if readiness.get("candidate_semantic_id") != SEMANTIC:
        raise AssertionError("sound-changes candidate identity drift")
    if readiness.get("targets") != TARGETS:
        raise AssertionError("sound-changes target identity drift")

    learner = readiness.get("learner_content") or {}
    if learner.get("dedicated_candidate_content_unit_present") is not True:
        raise AssertionError("dedicated sound-changes learner content missing")
    if learner.get("original_eksamio_content") is not True:
        raise AssertionError("sound-changes learner content is not original Eksamio content")
    if learner.get("independent_verification_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-changes evidence identity drift")
    if learner.get("independent_verification_count") != 6:
        raise AssertionError("sound-changes evidence count drift")
    if set(learner.get("covered_skills") or []) != set(COVERED_SKILLS):
        raise AssertionError("sound-changes skill coverage drift")

    independence = readiness.get("evidence_independence") or {}
    if independence.get("sound_changes_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-changes evidence set drift")
    if independence.get("overlap") != [] or independence.get("adjacent_semantic_evidence_reused") is not False:
        raise AssertionError("adjacent RU01 evidence reused for sound changes")
    if independence.get("generic_ru01_evidence_can_substitute") is not False:
        raise AssertionError("generic RU01 evidence substitution opened")

    readiness_policy = readiness.get("policy") or {}
    for key in (
        "content_readiness_is_semantic_acceptance",
        "content_readiness_is_object_acceptance",
        "candidate_is_canonical_before_separate_acceptance",
        "shared_future_evidence_can_close_both_source_objects_without_separate_object_acceptance",
        "normative_pronunciation_or_stress_inferred",
        "sibling_source_objects_auto_closed",
    ):
        if readiness_policy.get(key) is not False:
            raise AssertionError(f"pre-acceptance fail-closed boundary drift: {key}")
    if readiness_policy.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("pre-acceptance false exact mastery drift")

    current = readiness.get("current_launch_aggregate_unchanged") or {}
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
    if current != expected_current:
        raise AssertionError("current-v13 predecessor aggregate drift")

    acceptance = load(ACCEPTANCE)
    if acceptance.get("schema_version") != "0.1.0":
        raise AssertionError("acceptance schema drift")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_SOUND_CHANGES_IN_SPEECH_FLOW_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("sound-changes semantic acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("sound-changes semantic authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("sound-changes acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("sound-changes acceptance created a parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("source_binding_review") != "russian-program/subject-admission/RU01-SOUND-CHANGES-EXACT-SOURCE-BINDING-REVIEW-v0.1.json":
        raise AssertionError("sound-changes source-binding authority drift")
    if authority.get("content_readiness_builder") != "russian-program/subject-admission/build_ru01_sound_changes_content_readiness.py":
        raise AssertionError("sound-changes readiness authority drift")
    if authority.get("learner_content") != "russian-program/production-learning-content/RU-PROG-01-SOUND-CHANGES-WAVE-003-v0.1.json":
        raise AssertionError("sound-changes learner-content authority drift")
    if authority.get("target_admission_unit_ids") != [row["admission_unit_id"] for row in TARGETS]:
        raise AssertionError("sound-changes target admission-unit list drift")
    if authority.get("target_requirement_ids") != [row["requirement_id"] for row in TARGETS]:
        raise AssertionError("sound-changes target requirement list drift")
    if authority.get("source_locators") != [row["source_locator"] for row in TARGETS]:
        raise AssertionError("sound-changes target source-locator list drift")

    policy = acceptance.get("policy") or {}
    required_true = (
        "exact_source_backed_owner_resolution_required",
        "original_dedicated_learner_content_required",
        "component_specific_independent_evidence_required",
        "parallel_registry_creation_forbidden",
        "separate_exact_object_acceptance_required_for_each_target",
    )
    for key in required_true:
        if policy.get(key) is not True:
            raise AssertionError(f"sound-changes acceptance policy weakened: {key}")
    required_false = (
        "sound_letter_relation_semantic_may_substitute",
        "vowel_consonant_features_semantic_may_substitute",
        "word_analysis_semantic_may_substitute",
        "phonetic_transcription_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "normative_stress_semantic_may_substitute",
        "route_title_task_number_keyword_fuzzy_or_embedding_can_admit_semantics",
        "canonical_school_registry_mutation_required",
        "content_or_evidence_presence_alone_is_semantic_admission",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "generic_ru01_result_can_emit_exact_component_mastery",
        "shared_evidence_can_close_both_source_objects_without_separate_acceptance",
        "whole_group_acceptance_allowed",
    )
    for key in required_false:
        if policy.get(key) is not False:
            raise AssertionError(f"sound-changes acceptance policy opened: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("sound-changes acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("sound-changes semantic crosswalk drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("sound-changes semantic not explicitly accepted")
    if decision.get("owner_search_result") != "NO_EXACT_CURRENT_SOUND_CHANGES_OWNER_WITH_COMPONENT_SPECIFIC_EVIDENCE":
        raise AssertionError("sound-changes owner-search result drift")
    if decision.get("source_evidence_status") != "confirmed_for_two_exact_official_source_objects":
        raise AssertionError("sound-changes source evidence not confirmed")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("accepted sound-changes evidence identity drift")
    if decision.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("accepted sound-changes skill boundary drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("semantic acceptance improperly closes exact object")
    guard = str(decision.get("boundary_guard") or "")
    for fragment in (
        "static sound/letter or vowel/consonant features",
        "generic phonetic word analysis",
        "phonetic transcription",
        "normative pronunciation or stress",
        "separate exact acceptance for each target",
    ):
        if fragment not in guard:
            raise AssertionError(f"sound-changes boundary guard drift: {fragment}")

    if acceptance.get("summary") != {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("sound-changes semantic acceptance summary drift")

    next_work = acceptance.get("next_exact_work") or {}
    if next_work.get("separate_exact_object_acceptance_required") is not True:
        raise AssertionError("separate sound-changes object acceptance requirement drift")
    if next_work.get("target_count") != 2 or next_work.get("targets") != TARGETS:
        raise AssertionError("sound-changes next target set drift")
    if next_work.get("component_specific_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-changes next evidence set drift")
    if next_work.get("each_target_remains_pending_until_its_own_exact_head_object_gate_passes") is not True:
        raise AssertionError("sound-changes sibling fail-closed boundary drift")

    duplicates = []
    for path in HERE.glob("*.json"):
        if path == ACCEPTANCE:
            continue
        try:
            value = load(path)
        except Exception:
            continue
        rows = value.get("decisions")
        if not isinstance(rows, list):
            continue
        if any(isinstance(row, dict) and row.get("accepted_semantic_id") == SEMANTIC for row in rows):
            duplicates.append(path.name)
    if duplicates:
        raise AssertionError(f"duplicate sound-changes semantic acceptance: {duplicates}")

    print("RU01_SOUND_CHANGES_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SUBJECT_SEMANTICS=1")
    print("TARGET_OBJECTS_PENDING=2")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("INDEPENDENT_EVIDENCE_ITEMS=6")
    print("ADJACENT_EVIDENCE_REUSED=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
