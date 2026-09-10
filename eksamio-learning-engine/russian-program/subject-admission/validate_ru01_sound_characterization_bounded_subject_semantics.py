#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE / "RU01-SOUND-CHARACTERIZATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
ADEQUACY = HERE / "build_ru01_sound_characterization_content_adequacy_review.py"

SEMANTIC = "ru-phonetics-sound-characterization"
TAXONOMY = "sound_characterization"
VERIFICATION_IDS = [f"p01-u11-v{i}" for i in range(1, 6)]
COVERED_SKILLS = [
    "characterize_presented_consonant",
    "characterize_presented_vowel",
    "preserve_sound_letter_boundary",
    "select_type_specific_features",
    "preserve_characterization_scope_boundary",
]
ADEQUACY_GATE = {
    "workflow": "Russian RU01 sound characterization content adequacy",
    "run_id": 34482234747,
    "head_sha": "e3d79a08bf9f539a62fbf164b6e9c1b4e3d6f7cf",
    "conclusion": "SUCCESS",
}
SOURCE_CLAUSES = [
    {
        "clause_id": "EDSOO59-P181-4.1-A",
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "requirement_id": "RSK-EDSOO59-4-1-P181",
        "source_locator": "EDSOO59 p.181 4.1 / clause A",
        "official_requirement": "Характеризовать звуки",
    }
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def main() -> int:
    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_SOUND_CHARACTERIZATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("sound-characterization adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate != {
        "semantic_id": SEMANTIC,
        "source_taxonomy_id": TAXONOMY,
        "source_clause_ids": ["EDSOO59-P181-4.1-A"],
        "semantic_ref_status": "PROPOSED_NOT_CANONICAL",
    }:
        raise AssertionError("sound-characterization candidate identity/source drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "b150eb27fa112034b96d4bdb7c6d2f631c2b5979":
        raise AssertionError("sound-characterization learner-content blob drift")
    if learner.get("component_specific_verification_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-characterization evidence identity drift")
    for key in (
        "registered_user_identity_required",
        "exact_item_identity_required",
        "server_owned_received_at_required",
        "durable_evidence_event_required_before_future_canonical_write",
    ):
        if learner.get(key) is not True:
            raise AssertionError(f"sound-characterization PEIS boundary weakened: {key}")

    decision0 = adequacy.get("adequacy_decision") or {}
    for key in (
        "content_exact_for_bounded_sound_characterization_candidate",
        "official_clause_scope_covered",
        "explicit_sound_object_required_before_characterization",
        "vowel_and_consonant_feature_paths_distinguished",
        "sound_letter_boundary_preserved",
        "partial_vowel_consonant_feature_owner_not_promoted_to_exact_owner",
        "vowel_system_not_substituted",
        "consonant_system_not_substituted",
        "whole_sound_system_not_substituted",
        "normative_pronunciation_not_inferred",
    ):
        if decision0.get(key) is not True:
            raise AssertionError(f"sound-characterization adequacy boundary drift: {key}")
    if decision0.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("sound-characterization adequacy predecessor self-admitted semantic")
    if decision0.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("sound-characterization adequacy next-state drift")
    for key in (
        "object_level_admission_units_closed",
        "object_level_requirements_closed",
        "exact_mastery_admissions",
        "false_exact_mastery_admissions",
    ):
        if decision0.get(key) != 0:
            raise AssertionError(f"sound-characterization adequacy admission drift: {key}")

    acceptance = load(ACCEPTANCE)
    if acceptance.get("schema_version") != "0.1.0":
        raise AssertionError("sound-characterization acceptance schema drift")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_SOUND_CHARACTERIZATION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("sound-characterization acceptance status drift")
    if acceptance.get("authority_pr") != 164:
        raise AssertionError("sound-characterization authority PR drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("sound-characterization acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("sound-characterization acceptance created parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("owner_resolution_builder") != "russian-program/subject-admission/build_ru01_phonetics_broad_header_owner_resolution_current_v23.py":
        raise AssertionError("sound-characterization owner-resolution authority drift")
    if authority.get("content_adequacy_builder") != "russian-program/subject-admission/build_ru01_sound_characterization_content_adequacy_review.py":
        raise AssertionError("sound-characterization adequacy authority drift")
    if authority.get("learner_content") != "russian-program/production-learning-content/RU-PROG-01-SOUND-CHARACTERIZATION-WAVE-009-v0.1.json":
        raise AssertionError("sound-characterization learner-content authority drift")
    if authority.get("learner_content_git_blob_sha1") != "b150eb27fa112034b96d4bdb7c6d2f631c2b5979":
        raise AssertionError("sound-characterization learner-content authority blob drift")
    if authority.get("content_adequacy_exact_head_gate") != ADEQUACY_GATE:
        raise AssertionError("sound-characterization exact-head adequacy gate drift")
    if authority.get("source_clauses") != SOURCE_CLAUSES:
        raise AssertionError("sound-characterization exact source-clause authority drift")

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
            raise AssertionError(f"sound-characterization acceptance policy weakened: {key}")
    for key in (
        "partial_vowel_consonant_feature_semantic_may_substitute",
        "vowel_system_semantic_may_substitute",
        "consonant_system_semantic_may_substitute",
        "sound_system_semantic_may_substitute",
        "sound_letter_relation_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "route_title_task_number_keyword_fuzzy_or_embedding_can_admit_semantics",
        "canonical_school_registry_mutation_required",
        "content_or_evidence_presence_alone_is_semantic_admission",
        "subject_semantic_acceptance_can_reduce_parent_object_counts",
        "generic_ru01_result_can_emit_exact_component_mastery",
        "parent_object_can_close_before_all_required_clauses_have_exact_accepted_owners_and_component_specific_evidence",
        "shared_sound_characterization_evidence_can_close_sibling_clauses_or_objects",
        "whole_group_acceptance_allowed",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"sound-characterization acceptance policy opened: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("sound-characterization acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("sound-characterization semantic crosswalk drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("sound-characterization semantic not explicitly accepted")
    if decision.get("owner_search_result") != "PARTIAL_ONLY_NO_EXACT_CURRENT_OWNER_BEFORE_BOUNDED_CANDIDATE":
        raise AssertionError("sound-characterization owner-search result drift")
    if decision.get("source_evidence_status") != "CONFIRMED_FOR_EXACT_OFFICIAL_EDSOO59_P181_4_1_A_CLAUSE":
        raise AssertionError("sound-characterization source evidence drift")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("accepted sound-characterization evidence drift")
    if decision.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("accepted sound-characterization skill boundary drift")
    if decision.get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_BROAD_EDSOO59_P181_4_1_PARENT_OBJECT":
        raise AssertionError("sound-characterization acceptance improperly closes parent object")
    guard = str(decision.get("boundary_guard") or "").lower()
    for fragment in ("concrete sound", "letter", "narrower", "vowel", "consonant", "sound system", "normative pronunciation"):
        if fragment not in guard:
            raise AssertionError(f"sound-characterization boundary guard drift: {fragment}")

    if acceptance.get("summary") != {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "parent_object_admission_units_closed": 0,
        "parent_object_requirements_closed": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("sound-characterization acceptance summary drift")

    next_work = acceptance.get("next_exact_work") or {}
    if next_work.get("parent_objects_remain_pending") != [{
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "requirement_id": "RSK-EDSOO59-4-1-P181",
        "sound_characterization_clause_id": "EDSOO59-P181-4.1-A",
    }]:
        raise AssertionError("sound-characterization parent-object frontier drift")
    if next_work.get("sound_characterization_component_specific_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-characterization next evidence set drift")
    if next_work.get("sound_system_clause_remains_separate_and_unresolved") is not True:
        raise AssertionError("sound-system sibling boundary weakened")
    if next_work.get("remaining_broad_header_components_must_be_resolved_independently") is not True:
        raise AssertionError("sound-characterization sibling-component independence weakened")
    if next_work.get("parent_objects_remain_pending_until_every_required_clause_has_exact_accepted_owner_and_component_specific_evidence_and_its_own_exact_head_object_gate_passes") is not True:
        raise AssertionError("sound-characterization parent-object fail-closed boundary drift")

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
        raise AssertionError(f"duplicate sound-characterization semantic acceptance: {duplicates}")

    print("RU01_SOUND_CHARACTERIZATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SUBJECT_SEMANTICS=1")
    print("PARENT_OBJECTS_PENDING=1")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("INDEPENDENT_EVIDENCE_ITEMS=5")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
