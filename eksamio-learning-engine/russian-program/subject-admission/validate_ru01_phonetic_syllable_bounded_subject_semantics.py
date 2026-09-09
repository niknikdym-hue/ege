#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE / "RU01-PHONETIC-SYLLABLE-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
ADEQUACY = HERE / "build_ru01_phonetic_syllable_content_adequacy_review.py"

SEMANTIC = "ru-phonetics-syllable"
TAXONOMY = "phonetic_syllable"
VERIFICATION_IDS = [f"p01-u7-v{i}" for i in range(1, 6)]
COVERED_SKILLS = [
    "count_syllables_from_established_spoken_form",
    "identify_syllabic_centre",
    "distinguish_syllable_from_adjacent_semantics",
    "respect_ambiguous_syllable_boundary",
    "separate_syllable_from_normative_stress",
]
ADEQUACY_GATE = {
    "workflow": "Russian RU01 phonetic syllable content adequacy",
    "run_id": 34337083039,
    "head_sha": "874b8a57307c4cfc1ce11cd9ed22fd0970ffa552",
    "conclusion": "SUCCESS",
}
SOURCE_CLAUSES = [
    {
        "clause_id": "EDSOO59-P187-4.1.5",
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "requirement_id": "RSK-EDSOO59-4-1-P187",
        "source_locator": "EDSOO59 p.187 4.1 / clause 4.1.5",
        "official_requirement": "Слог",
    },
    {
        "clause_id": "OGE-COD-P020-4.1.5",
        "admission_unit_id": "RAU-3916b5e3da77ed038830",
        "requirement_id": "RSK-OGE_COD-4-1-P020",
        "source_locator": "OGE_COD p.20 4.1 / clause 4.1.5",
        "official_requirement": "Слог",
    },
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def main() -> int:
    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_PHONETIC_SYLLABLE_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("syllable adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate != {
        "semantic_id": SEMANTIC,
        "source_taxonomy_id": TAXONOMY,
        "source_clause_ids": ["EDSOO59-P187-4.1.5", "OGE-COD-P020-4.1.5"],
        "semantic_ref_status": "PROPOSED_NOT_CANONICAL",
    }:
        raise AssertionError("syllable candidate identity/source drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "24281db6ee3d5cea24656c1e5e0be9b787392a08":
        raise AssertionError("syllable learner-content blob drift")
    if learner.get("component_specific_verification_ids") != VERIFICATION_IDS:
        raise AssertionError("syllable evidence identity drift")
    for key in ("registered_user_identity_required", "exact_item_identity_required", "server_owned_received_at_required"):
        if learner.get(key) is not True:
            raise AssertionError(f"syllable PEIS evidence boundary weakened: {key}")
    decision0 = adequacy.get("adequacy_decision") or {}
    for key in (
        "content_exact_for_bounded_phonetic_syllable_candidate",
        "official_clause_scope_covered",
        "word_transfer_separated",
        "normative_stress_separated",
        "disputed_pronunciation_fail_closed",
        "ambiguous_consonant_cluster_boundary_fail_closed",
        "adjacent_ru01_semantics_do_not_substitute",
    ):
        if decision0.get(key) is not True:
            raise AssertionError(f"syllable adequacy boundary drift: {key}")
    if decision0.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("adequacy predecessor self-admitted semantic")
    if decision0.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("syllable adequacy next-state drift")
    for key in ("object_level_admission_units_closed", "object_level_requirements_closed", "exact_mastery_admissions", "false_exact_mastery_admissions"):
        if decision0.get(key) != 0:
            raise AssertionError(f"syllable adequacy predecessor admission drift: {key}")

    acceptance = load(ACCEPTANCE)
    if acceptance.get("schema_version") != "0.1.0":
        raise AssertionError("syllable acceptance schema drift")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETIC_SYLLABLE_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("syllable acceptance status drift")
    if acceptance.get("authority_pr") != 164:
        raise AssertionError("syllable authority PR drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("syllable acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("syllable acceptance created parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("owner_resolution_builder") != "russian-program/subject-admission/build_ru01_phonetics_broad_header_owner_resolution_review.py":
        raise AssertionError("syllable owner-resolution authority drift")
    if authority.get("content_adequacy_builder") != "russian-program/subject-admission/build_ru01_phonetic_syllable_content_adequacy_review.py":
        raise AssertionError("syllable adequacy authority drift")
    if authority.get("learner_content") != "russian-program/production-learning-content/RU-PROG-01-SYLLABLE-WAVE-005-v0.1.json":
        raise AssertionError("syllable learner-content authority drift")
    if authority.get("learner_content_git_blob_sha1") != "24281db6ee3d5cea24656c1e5e0be9b787392a08":
        raise AssertionError("syllable learner-content authority blob drift")
    if authority.get("content_adequacy_exact_head_gate") != ADEQUACY_GATE:
        raise AssertionError("syllable exact-head adequacy gate drift")
    if authority.get("source_clauses") != SOURCE_CLAUSES:
        raise AssertionError("syllable exact source-clause authority drift")

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
            raise AssertionError(f"syllable acceptance policy weakened: {key}")
    for key in (
        "word_transfer_rules_may_substitute",
        "normative_stress_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "phonetic_transcription_semantic_may_substitute",
        "word_analysis_semantic_may_substitute",
        "vowel_consonant_features_semantic_may_substitute",
        "route_title_task_number_keyword_fuzzy_or_embedding_can_admit_semantics",
        "ambiguous_syllable_boundary_can_be_guessed",
        "canonical_school_registry_mutation_required",
        "content_or_evidence_presence_alone_is_semantic_admission",
        "subject_semantic_acceptance_can_reduce_parent_object_counts",
        "generic_ru01_result_can_emit_exact_component_mastery",
        "parent_object_can_close_before_all_required_clauses_have_exact_accepted_owners_and_component_specific_evidence",
        "shared_syllable_evidence_can_close_sibling_clauses_or_objects",
        "whole_group_acceptance_allowed",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"syllable acceptance policy opened: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("syllable acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("syllable semantic crosswalk drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("syllable semantic not explicitly accepted")
    if decision.get("owner_search_result") != "NO_EXACT_CURRENT_SYLLABLE_OWNER_BEFORE_BOUNDED_CANDIDATE":
        raise AssertionError("syllable owner-search result drift")
    if decision.get("source_evidence_status") != "CONFIRMED_FOR_TWO_EXACT_OFFICIAL_4_1_5_CLAUSES":
        raise AssertionError("syllable source evidence status drift")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("accepted syllable evidence identity drift")
    if decision.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("accepted syllable skill boundary drift")
    if decision.get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_EITHER_BROAD_4_1_PARENT_OBJECT":
        raise AssertionError("syllable semantic acceptance improperly closes parent object")
    guard = str(decision.get("boundary_guard") or "").lower()
    for fragment in ("word transfer", "normative pronunciation", "normative stress", "transcription", "word analysis", "consonant-cluster"):
        if fragment not in guard:
            raise AssertionError(f"syllable boundary guard drift: {fragment}")

    if acceptance.get("summary") != {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "parent_object_admission_units_closed": 0,
        "parent_object_requirements_closed": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("syllable semantic acceptance summary drift")

    next_work = acceptance.get("next_exact_work") or {}
    expected_pending = [
        {
            "admission_unit_id": "RAU-5a6511267f156745f93c",
            "requirement_id": "RSK-EDSOO59-4-1-P187",
            "syllable_clause_id": "EDSOO59-P187-4.1.5",
        },
        {
            "admission_unit_id": "RAU-3916b5e3da77ed038830",
            "requirement_id": "RSK-OGE_COD-4-1-P020",
            "syllable_clause_id": "OGE-COD-P020-4.1.5",
        },
    ]
    if next_work.get("parent_objects_remain_pending") != expected_pending:
        raise AssertionError("syllable parent-object frontier drift")
    if next_work.get("syllable_component_specific_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("syllable next evidence set drift")
    if next_work.get("remaining_broad_header_components_must_be_resolved_independently") is not True:
        raise AssertionError("syllable sibling-component independence weakened")
    if next_work.get("parent_objects_remain_pending_until_every_required_clause_has_exact_accepted_owner_and_component_specific_evidence_and_its_own_exact_head_object_gate_passes") is not True:
        raise AssertionError("syllable parent-object fail-closed boundary drift")

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
        raise AssertionError(f"duplicate syllable semantic acceptance: {duplicates}")

    print("RU01_PHONETIC_SYLLABLE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SUBJECT_SEMANTICS=1")
    print("PARENT_OBJECTS_PENDING=2")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("INDEPENDENT_EVIDENCE_ITEMS=5")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
