#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE / "RU01-VOWEL-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
ADEQUACY = HERE / "build_ru01_vowel_system_content_adequacy_review.py"

SEMANTIC = "ru-phonetics-vowel-system"
TAXONOMY = "vowel_system"
VERIFICATION_IDS = [f"p01-u9-v{i}" for i in range(1, 6)]
COVERED_SKILLS = [
    "recognize_vowel_system_members",
    "identify_complete_school_vowel_inventory",
    "separate_vowel_sounds_from_letters",
    "separate_partial_feature_from_full_system",
    "preserve_pronunciation_stress_boundary",
]
ADEQUACY_GATE = {
    "workflow": "Russian RU01 vowel system content adequacy",
    "run_id": 34397793067,
    "head_sha": "711dc4ec4641874a11edadcebc9197c59aa39d3d",
    "conclusion": "SUCCESS",
}
SOURCE_CLAUSES = [
    {
        "clause_id": "EDSOO59-P187-4.1.1",
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "requirement_id": "RSK-EDSOO59-4-1-P187",
        "source_locator": "EDSOO59 p.187 4.1 / clause 4.1.1",
        "official_requirement": "Система гласных звуков",
    },
    {
        "clause_id": "OGE-COD-P020-4.1.1",
        "admission_unit_id": "RAU-3916b5e3da77ed038830",
        "requirement_id": "RSK-OGE_COD-4-1-P020",
        "source_locator": "OGE_COD p.20 4.1 / clause 4.1.1",
        "official_requirement": "Система гласных звуков",
    },
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def main() -> int:
    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_VOWEL_SYSTEM_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("vowel-system adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate != {
        "semantic_id": SEMANTIC,
        "source_taxonomy_id": TAXONOMY,
        "source_clause_ids": ["EDSOO59-P187-4.1.1", "OGE-COD-P020-4.1.1"],
        "semantic_ref_status": "PROPOSED_NOT_CANONICAL",
    }:
        raise AssertionError("vowel-system candidate identity/source drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "37bbbb2793915ab45142cbb758b201c5ac8129be":
        raise AssertionError("vowel-system learner-content blob drift")
    if learner.get("component_specific_verification_ids") != VERIFICATION_IDS:
        raise AssertionError("vowel-system evidence identity drift")
    for key in (
        "registered_user_identity_required",
        "exact_item_identity_required",
        "server_owned_received_at_required",
        "durable_evidence_event_required_before_future_canonical_write",
    ):
        if learner.get(key) is not True:
            raise AssertionError(f"vowel-system PEIS boundary weakened: {key}")

    adequacy_decision = adequacy.get("adequacy_decision") or {}
    for key in (
        "content_exact_for_bounded_vowel_system_candidate",
        "official_clause_scope_covered",
        "full_school_vowel_inventory_covered",
        "vowel_sounds_and_vowel_letters_separated",
        "partial_vowel_consonant_feature_owner_not_promoted_to_full_system",
        "consonant_system_separated",
        "stress_and_normative_pronunciation_separated",
        "sound_composition_and_sound_letter_relation_do_not_substitute",
    ):
        if adequacy_decision.get(key) is not True:
            raise AssertionError(f"vowel-system adequacy boundary drift: {key}")
    if adequacy_decision.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("vowel-system adequacy predecessor self-admitted semantic")
    if adequacy_decision.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("vowel-system adequacy next-state drift")
    for key in (
        "object_level_admission_units_closed",
        "object_level_requirements_closed",
        "exact_mastery_admissions",
        "false_exact_mastery_admissions",
    ):
        if adequacy_decision.get(key) != 0:
            raise AssertionError(f"vowel-system adequacy admission drift: {key}")

    acceptance = load(ACCEPTANCE)
    if acceptance.get("schema_version") != "0.1.0":
        raise AssertionError("vowel-system acceptance schema drift")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_VOWEL_SYSTEM_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("vowel-system acceptance status drift")
    if acceptance.get("authority_pr") != 164:
        raise AssertionError("vowel-system authority PR drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("vowel-system acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("vowel-system acceptance created parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("owner_resolution_builder") != "russian-program/subject-admission/build_ru01_phonetics_broad_header_owner_resolution_review.py":
        raise AssertionError("vowel-system owner-resolution authority drift")
    if authority.get("content_adequacy_builder") != "russian-program/subject-admission/build_ru01_vowel_system_content_adequacy_review.py":
        raise AssertionError("vowel-system adequacy authority drift")
    if authority.get("learner_content") != "russian-program/production-learning-content/RU-PROG-01-VOWEL-SYSTEM-WAVE-007-v0.1.json":
        raise AssertionError("vowel-system learner-content authority drift")
    if authority.get("learner_content_git_blob_sha1") != "37bbbb2793915ab45142cbb758b201c5ac8129be":
        raise AssertionError("vowel-system learner-content authority blob drift")
    if authority.get("content_adequacy_exact_head_gate") != ADEQUACY_GATE:
        raise AssertionError("vowel-system exact-head adequacy gate drift")
    if authority.get("source_clauses") != SOURCE_CLAUSES:
        raise AssertionError("vowel-system exact source-clause authority drift")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_source_backed_owner_resolution_required",
        "successful_content_adequacy_gate_required",
        "original_dedicated_learner_content_required",
        "component_specific_independent_evidence_required",
        "parallel_registry_creation_forbidden",
        "separate_exact_parent_object_component_set_acceptance_required",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"vowel-system acceptance policy weakened: {key}")
    for key in (
        "partial_vowel_consonant_feature_semantic_may_substitute",
        "consonant_system_semantic_may_substitute",
        "sound_letter_relation_semantic_may_substitute",
        "sound_composition_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "normative_stress_semantic_may_substitute",
        "route_title_task_number_keyword_fuzzy_or_embedding_can_admit_semantics",
        "canonical_school_registry_mutation_required",
        "content_or_evidence_presence_alone_is_semantic_admission",
        "subject_semantic_acceptance_can_reduce_parent_object_counts",
        "generic_ru01_result_can_emit_exact_component_mastery",
        "parent_object_can_close_before_all_required_clauses_have_exact_accepted_owners_and_component_specific_evidence",
        "shared_vowel_system_evidence_can_close_sibling_clauses_or_objects",
        "whole_group_acceptance_allowed",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"vowel-system acceptance policy opened: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("vowel-system acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("vowel-system semantic crosswalk drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("vowel-system semantic not explicitly accepted")
    if decision.get("owner_search_result") != "NO_EXACT_CURRENT_FULL_VOWEL_SYSTEM_OWNER_BEFORE_BOUNDED_CANDIDATE":
        raise AssertionError("vowel-system owner-search result drift")
    if decision.get("source_evidence_status") != "CONFIRMED_FOR_TWO_EXACT_OFFICIAL_4_1_1_CLAUSES":
        raise AssertionError("vowel-system source evidence drift")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("accepted vowel-system evidence drift")
    if decision.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("accepted vowel-system skill boundary drift")
    if decision.get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_EITHER_BROAD_4_1_PARENT_OBJECT":
        raise AssertionError("vowel-system acceptance improperly closes parent object")
    guard = str(decision.get("boundary_guard") or "").lower()
    for fragment in ("vowel letters", "narrower", "consonant system", "sound composition", "normative pronunciation", "stress", "task-number"):
        if fragment not in guard:
            raise AssertionError(f"vowel-system boundary guard drift: {fragment}")

    if acceptance.get("summary") != {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "parent_object_admission_units_closed": 0,
        "parent_object_requirements_closed": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("vowel-system acceptance summary drift")

    next_work = acceptance.get("next_exact_work") or {}
    expected_pending = [
        {
            "admission_unit_id": "RAU-5a6511267f156745f93c",
            "requirement_id": "RSK-EDSOO59-4-1-P187",
            "vowel_system_clause_id": "EDSOO59-P187-4.1.1",
        },
        {
            "admission_unit_id": "RAU-3916b5e3da77ed038830",
            "requirement_id": "RSK-OGE_COD-4-1-P020",
            "vowel_system_clause_id": "OGE-COD-P020-4.1.1",
        },
    ]
    if next_work.get("parent_objects_remain_pending") != expected_pending:
        raise AssertionError("vowel-system parent-object frontier drift")
    if next_work.get("vowel_system_component_specific_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("vowel-system next evidence set drift")
    if next_work.get("partial_feature_consonant_sound_letter_composition_stress_and_pronunciation_remain_separate") is not True:
        raise AssertionError("vowel-system adjacent-component separation weakened")
    if next_work.get("remaining_broad_header_components_must_be_resolved_independently") is not True:
        raise AssertionError("vowel-system sibling-component independence weakened")
    if next_work.get("parent_objects_remain_pending_until_every_required_clause_has_exact_accepted_owner_and_component_specific_evidence_and_its_own_exact_head_object_gate_passes") is not True:
        raise AssertionError("vowel-system parent-object fail-closed boundary drift")

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
        raise AssertionError(f"duplicate vowel-system semantic acceptance: {duplicates}")

    print("RU01_VOWEL_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SUBJECT_SEMANTICS=1")
    print("PARENT_OBJECTS_PENDING=2")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("INDEPENDENT_EVIDENCE_ITEMS=5")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
