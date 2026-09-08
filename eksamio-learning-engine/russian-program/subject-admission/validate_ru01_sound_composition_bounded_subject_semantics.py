#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE / "RU01-SOUND-COMPOSITION-DETERMINATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
READINESS = HERE / "build_ru01_sound_composition_content_readiness.py"

SEMANTIC = "ru-phonetics-sound-composition-determination"
TAXONOMY = "sound_composition_determination"
TARGET = {
    "admission_unit_id": "RAU-b6f5dff93864358672bc",
    "requirement_id": "RSK-OGE_COD-2-1-P010",
    "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.10 2.1",
}
VERIFICATION_IDS = [f"p01-u6-v{i}" for i in range(1, 7)]
COVERED_SKILLS = [
    "count_sounds_without_counting_letters",
    "determine_ordered_sound_sequence",
    "distinguish_sound_composition_from_adjacent_semantics",
    "distinguish_sound_composition_from_letter_composition",
    "recognize_fail_closed_pronunciation_boundary",
    "separate_composition_from_feature_classification",
]
READINESS_GATE = {
    "workflow": "Russian RU01 sound composition content readiness",
    "run_id": 34255891455,
    "head_sha": "b4684caae27f1ff73a67b5e1cd176f567cfdc3e1",
    "conclusion": "SUCCESS",
}


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def main() -> int:
    readiness = runpy.run_path(str(READINESS))["build_readiness"]()
    if readiness.get("status") != "CENTRAL_BRAIN_RU01_SOUND_COMPOSITION_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED":
        raise AssertionError("sound-composition readiness predecessor drift")
    if readiness.get("candidate_semantic_id") != SEMANTIC:
        raise AssertionError("sound-composition candidate identity drift")

    target = readiness.get("target") or {}
    expected_target = {
        **TARGET,
        "already_bound_component_ref_preserved": "ru-phonetics-vowel-consonant-features",
        "remaining_component_candidate": SEMANTIC,
    }
    if target != expected_target:
        raise AssertionError("sound-composition exact target drift")

    learner = readiness.get("learner_content") or {}
    if learner.get("dedicated_candidate_content_unit_present") is not True:
        raise AssertionError("dedicated sound-composition learner content missing")
    if learner.get("original_eksamio_content") is not True:
        raise AssertionError("sound-composition learner content is not original Eksamio content")
    if learner.get("independent_verification_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-composition evidence identity drift")
    if learner.get("independent_verification_count") != 6:
        raise AssertionError("sound-composition evidence count drift")
    if learner.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("sound-composition skill coverage drift")

    independence = readiness.get("evidence_independence") or {}
    if independence.get("sound_composition_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-composition evidence set drift")
    if independence.get("overlap") != [] or independence.get("adjacent_semantic_evidence_reused") is not False:
        raise AssertionError("adjacent RU01 evidence reused for sound composition")
    if independence.get("generic_ru01_evidence_can_substitute") is not False:
        raise AssertionError("generic RU01 evidence substitution opened")

    readiness_policy = readiness.get("policy") or {}
    for key in (
        "content_readiness_is_semantic_acceptance",
        "content_readiness_is_object_acceptance",
        "candidate_is_canonical_before_separate_acceptance",
        "existing_partial_component_is_modified",
        "normative_pronunciation_or_stress_inferred",
    ):
        if readiness_policy.get(key) is not False:
            raise AssertionError(f"pre-acceptance fail-closed boundary drift: {key}")
    if readiness_policy.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("pre-acceptance false exact mastery drift")

    current = readiness.get("current_launch_aggregate_unchanged") or {}
    expected_current = {
        "accepted_authorities": 63,
        "subject_disposed_units_total": 41,
        "subject_disposed_requirements_total": 41,
        "subject_review_units_remaining": 1275,
        "subject_review_requirements_remaining": 1350,
        "accepted_bounded_ru_subject_semantics": 68,
        "accepted_bounded_ru_semantics_total": 77,
        "false_exact_mastery_admissions": 0,
    }
    if current != expected_current:
        raise AssertionError("current-v16 predecessor aggregate drift")

    acceptance = load(ACCEPTANCE)
    if acceptance.get("schema_version") != "0.1.0":
        raise AssertionError("acceptance schema drift")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_SOUND_COMPOSITION_DETERMINATION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("sound-composition semantic acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("sound-composition semantic authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("sound-composition acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("sound-composition acceptance created a parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("owner_resolution") != "russian-program/subject-admission/RU01-OGE-2-1-SOUND-COMPOSITION-OWNER-RESOLUTION-v0.1.json":
        raise AssertionError("sound-composition owner-resolution authority drift")
    if authority.get("content_readiness_builder") != "russian-program/subject-admission/build_ru01_sound_composition_content_readiness.py":
        raise AssertionError("sound-composition readiness authority drift")
    if authority.get("learner_content") != "russian-program/production-learning-content/RU-PROG-01-SOUND-COMPOSITION-WAVE-004-v0.1.json":
        raise AssertionError("sound-composition learner-content authority drift")
    if authority.get("content_readiness_exact_head_gate") != READINESS_GATE:
        raise AssertionError("sound-composition readiness exact-head gate drift")
    if authority.get("target_admission_unit_id") != TARGET["admission_unit_id"]:
        raise AssertionError("sound-composition target admission-unit drift")
    if authority.get("target_requirement_id") != TARGET["requirement_id"]:
        raise AssertionError("sound-composition target requirement drift")
    if authority.get("source_locator") != TARGET["source_locator"]:
        raise AssertionError("sound-composition source locator drift")
    if authority.get("already_bound_component_ref_preserved") != "ru-phonetics-vowel-consonant-features":
        raise AssertionError("existing partial component authority drift")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_source_backed_owner_resolution_required",
        "original_dedicated_learner_content_required",
        "component_specific_independent_evidence_required",
        "existing_partial_component_must_be_preserved",
        "parallel_registry_creation_forbidden",
        "separate_exact_object_component_set_acceptance_required",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"sound-composition acceptance policy weakened: {key}")
    for key in (
        "sound_letter_relation_semantic_may_substitute",
        "vowel_consonant_features_semantic_may_substitute_for_sound_composition",
        "word_analysis_semantic_may_substitute",
        "phonetic_transcription_semantic_may_substitute",
        "sound_changes_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "normative_stress_semantic_may_substitute",
        "route_title_task_number_keyword_fuzzy_or_embedding_can_admit_semantics",
        "canonical_school_registry_mutation_required",
        "content_or_evidence_presence_alone_is_semantic_admission",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "generic_ru01_result_can_emit_exact_component_mastery",
        "semantic_acceptance_modifies_existing_partial_component",
        "whole_group_acceptance_allowed",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"sound-composition acceptance policy opened: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("sound-composition acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("sound-composition semantic crosswalk drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("sound-composition semantic not explicitly accepted")
    if decision.get("owner_search_result") != "NO_EXACT_CURRENT_SOUND_COMPOSITION_OWNER":
        raise AssertionError("sound-composition owner-search result drift")
    if decision.get("source_evidence_status") != "confirmed_for_exact_official_source_object":
        raise AssertionError("sound-composition source evidence not confirmed")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("accepted sound-composition evidence identity drift")
    if decision.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("accepted sound-composition skill boundary drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("semantic acceptance improperly closes exact object")
    guard = str(decision.get("boundary_guard") or "")
    for fragment in (
        "sound-letter relation",
        "vowel/consonant feature classification",
        "full phonetic analysis",
        "normative pronunciation or stress",
        "separate component-set acceptance",
    ):
        if fragment not in guard:
            raise AssertionError(f"sound-composition boundary guard drift: {fragment}")

    if acceptance.get("summary") != {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "existing_partial_components_modified": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("sound-composition semantic acceptance summary drift")

    next_work = acceptance.get("next_exact_work") or {}
    if next_work.get("separate_exact_object_component_set_acceptance_required") is not True:
        raise AssertionError("separate sound-composition object acceptance requirement drift")
    if next_work.get("target") != TARGET:
        raise AssertionError("sound-composition next target drift")
    if next_work.get("required_component_refs") != [
        "ru-phonetics-vowel-consonant-features",
        SEMANTIC,
    ]:
        raise AssertionError("sound-composition next component set drift")
    if next_work.get("sound_composition_component_specific_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-composition next evidence set drift")
    if next_work.get("existing_vowel_consonant_component_must_retain_its_own_component_specific_evidence") is not True:
        raise AssertionError("existing partial component evidence requirement drift")
    if next_work.get("target_remains_pending_until_its_own_exact_head_object_gate_passes") is not True:
        raise AssertionError("sound-composition object fail-closed boundary drift")

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
        raise AssertionError(f"duplicate sound-composition semantic acceptance: {duplicates}")

    print("RU01_SOUND_COMPOSITION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SUBJECT_SEMANTICS=1")
    print("TARGET_OBJECTS_PENDING=1")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("EXISTING_PARTIAL_COMPONENTS_MODIFIED=0")
    print("INDEPENDENT_EVIDENCE_ITEMS=6")
    print("ADJACENT_EVIDENCE_REUSED=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
