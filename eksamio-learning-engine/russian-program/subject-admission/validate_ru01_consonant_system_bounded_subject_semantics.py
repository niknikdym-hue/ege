#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE / "RU01-CONSONANT-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
ADEQUACY = HERE / "build_ru01_consonant_system_content_adequacy_review.py"

SEMANTIC = "ru-phonetics-consonant-system"
TAXONOMY = "consonant_system"
VERIFICATION_IDS = [f"p01-u10-v{i}" for i in range(1, 6)]
COVERED_SKILLS = [
    "recognize_consonant_system_members",
    "separate_consonant_sounds_from_letters",
    "identify_voicing_pair_relation",
    "identify_hardness_pair_relation",
    "preserve_consonant_system_boundary",
]
ADEQUACY_GATE = {
    "workflow": "Russian RU01 consonant system content adequacy",
    "run_id": 34421078487,
    "head_sha": "d3cc6d3fa08c902a9f123d9364e6bdb6b95ad784",
    "conclusion": "SUCCESS",
}
SOURCE_CLAUSES = [
    {
        "clause_id": "EDSOO59-P187-4.1.2",
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "requirement_id": "RSK-EDSOO59-4-1-P187",
        "source_locator": "EDSOO59 p.187 4.1 / clause 4.1.2",
        "official_requirement": "Система согласных звуков",
    },
    {
        "clause_id": "OGE-COD-P020-4.1.2",
        "admission_unit_id": "RAU-3916b5e3da77ed038830",
        "requirement_id": "RSK-OGE_COD-4-1-P020",
        "source_locator": "OGE_COD p.20 4.1 / clause 4.1.2",
        "official_requirement": "Система согласных звуков",
    },
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def main() -> int:
    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_CONSONANT_SYSTEM_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("consonant-system adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate != {
        "semantic_id": SEMANTIC,
        "source_taxonomy_id": TAXONOMY,
        "source_clause_ids": ["EDSOO59-P187-4.1.2", "OGE-COD-P020-4.1.2"],
        "semantic_ref_status": "PROPOSED_NOT_CANONICAL",
    }:
        raise AssertionError("consonant-system candidate identity/source drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "3fd8716766da403ccd3bcfd3cca2d97af5631db6":
        raise AssertionError("consonant-system learner-content blob drift")
    if learner.get("component_specific_verification_ids") != VERIFICATION_IDS:
        raise AssertionError("consonant-system evidence identity drift")
    for key in (
        "registered_user_identity_required",
        "exact_item_identity_required",
        "server_owned_received_at_required",
        "durable_evidence_event_required_before_future_canonical_write",
    ):
        if learner.get(key) is not True:
            raise AssertionError(f"consonant-system PEIS boundary weakened: {key}")

    decision0 = adequacy.get("adequacy_decision") or {}
    for key in (
        "content_exact_for_bounded_consonant_system_candidate",
        "official_clause_scope_covered",
        "consonant_sounds_and_letters_separated",
        "voicing_and_devoicing_system_covered",
        "hardness_and_softness_system_covered",
        "paired_and_unpaired_cases_covered",
        "partial_vowel_consonant_feature_owner_not_promoted_to_full_system",
        "vowel_system_separated",
        "stress_and_normative_pronunciation_separated",
        "sound_composition_and_sound_letter_relation_do_not_substitute",
    ):
        if decision0.get(key) is not True:
            raise AssertionError(f"consonant-system adequacy boundary drift: {key}")
    if decision0.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("consonant-system adequacy predecessor self-admitted semantic")
    if decision0.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("consonant-system adequacy next-state drift")
    for key in (
        "object_level_admission_units_closed",
        "object_level_requirements_closed",
        "exact_mastery_admissions",
        "false_exact_mastery_admissions",
    ):
        if decision0.get(key) != 0:
            raise AssertionError(f"consonant-system adequacy admission drift: {key}")

    acceptance = load(ACCEPTANCE)
    if acceptance.get("schema_version") != "0.1.0":
        raise AssertionError("consonant-system acceptance schema drift")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_CONSONANT_SYSTEM_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("consonant-system acceptance status drift")
    if acceptance.get("authority_pr") != 164:
        raise AssertionError("consonant-system authority PR drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("consonant-system acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("consonant-system acceptance created parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("owner_resolution_builder") != "russian-program/subject-admission/build_ru01_phonetics_broad_header_owner_resolution_review.py":
        raise AssertionError("consonant-system owner-resolution authority drift")
    if authority.get("content_adequacy_builder") != "russian-program/subject-admission/build_ru01_consonant_system_content_adequacy_review.py":
        raise AssertionError("consonant-system adequacy authority drift")
    if authority.get("learner_content") != "russian-program/production-learning-content/RU-PROG-01-CONSONANT-SYSTEM-WAVE-008-v0.1.json":
        raise AssertionError("consonant-system learner-content authority drift")
    if authority.get("learner_content_git_blob_sha1") != "3fd8716766da403ccd3bcfd3cca2d97af5631db6":
        raise AssertionError("consonant-system learner-content authority blob drift")
    if authority.get("content_adequacy_exact_head_gate") != ADEQUACY_GATE:
        raise AssertionError("consonant-system exact-head adequacy gate drift")
    if authority.get("source_clauses") != SOURCE_CLAUSES:
        raise AssertionError("consonant-system exact source-clause authority drift")

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
            raise AssertionError(f"consonant-system acceptance policy weakened: {key}")
    for key in (
        "partial_vowel_consonant_feature_semantic_may_substitute",
        "vowel_system_semantic_may_substitute",
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
        "shared_consonant_system_evidence_can_close_sibling_clauses_or_objects",
        "whole_group_acceptance_allowed",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"consonant-system acceptance policy opened: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("consonant-system acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("consonant-system semantic crosswalk drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("consonant-system semantic not explicitly accepted")
    if decision.get("owner_search_result") != "NO_EXACT_CURRENT_FULL_CONSONANT_SYSTEM_OWNER_BEFORE_BOUNDED_CANDIDATE":
        raise AssertionError("consonant-system owner-search result drift")
    if decision.get("source_evidence_status") != "CONFIRMED_FOR_TWO_EXACT_OFFICIAL_4_1_2_CLAUSES":
        raise AssertionError("consonant-system source evidence drift")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("accepted consonant-system evidence drift")
    if decision.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("accepted consonant-system skill boundary drift")
    if decision.get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_EITHER_BROAD_4_1_PARENT_OBJECT":
        raise AssertionError("consonant-system acceptance improperly closes parent object")
    guard = str(decision.get("boundary_guard") or "").lower()
    for fragment in ("consonant letters", "narrower", "vowel system", "sound composition", "normative pronunciation", "stress", "task-number"):
        if fragment not in guard:
            raise AssertionError(f"consonant-system boundary guard drift: {fragment}")

    if acceptance.get("summary") != {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "parent_object_admission_units_closed": 0,
        "parent_object_requirements_closed": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("consonant-system acceptance summary drift")

    next_work = acceptance.get("next_exact_work") or {}
    expected_pending = [
        {
            "admission_unit_id": "RAU-5a6511267f156745f93c",
            "requirement_id": "RSK-EDSOO59-4-1-P187",
            "consonant_system_clause_id": "EDSOO59-P187-4.1.2",
        },
        {
            "admission_unit_id": "RAU-3916b5e3da77ed038830",
            "requirement_id": "RSK-OGE_COD-4-1-P020",
            "consonant_system_clause_id": "OGE-COD-P020-4.1.2",
        },
    ]
    if next_work.get("parent_objects_remain_pending") != expected_pending:
        raise AssertionError("consonant-system parent-object frontier drift")
    if next_work.get("consonant_system_component_specific_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("consonant-system next evidence set drift")
    if next_work.get("partial_feature_vowel_sound_letter_composition_stress_and_pronunciation_remain_separate") is not True:
        raise AssertionError("consonant-system adjacent-component separation weakened")
    if next_work.get("remaining_broad_header_components_must_be_resolved_independently") is not True:
        raise AssertionError("consonant-system sibling-component independence weakened")
    if next_work.get("parent_objects_remain_pending_until_every_required_clause_has_exact_accepted_owner_and_component_specific_evidence_and_its_own_exact_head_object_gate_passes") is not True:
        raise AssertionError("consonant-system parent-object fail-closed boundary drift")

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
        raise AssertionError(f"duplicate consonant-system semantic acceptance: {duplicates}")

    print("RU01_CONSONANT_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SUBJECT_SEMANTICS=1")
    print("PARENT_OBJECTS_PENDING=2")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("INDEPENDENT_EVIDENCE_ITEMS=5")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
