#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACCEPTANCE = HERE / "RU01-SOUND-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
ADEQUACY = HERE / "build_ru01_sound_system_content_adequacy_review.py"
OWNER = HERE / "RU01-SOUND-SYSTEM-OWNER-RESOLUTION-v0.1.json"

SEMANTIC = "ru-phonetics-sound-system"
TAXONOMY = "sound_system"
VERIFICATION_IDS = [f"p01-u12-v{i}" for i in range(1, 6)]
FORBIDDEN_COMPONENT_EVIDENCE = [
    *[f"p01-u9-v{i}" for i in range(1, 6)],
    *[f"p01-u10-v{i}" for i in range(1, 6)],
]
ADEQUACY_GATE = {
    "workflow": "Russian RU01 sound system content adequacy",
    "run_id": 34534813456,
    "head_sha": "bfdb31555860858f9bad8f0ad74021637764fbb6",
    "conclusion": "SUCCESS",
}
SOURCE_CLAUSES = [{
    "clause_id": "EDSOO59-P181-4.1-C",
    "admission_unit_id": "RAU-5a6511267f156745f93c",
    "requirement_id": "RSK-EDSOO59-4-1-P181",
    "source_locator": "EDSOO-RU-5-9-2025/EDSOO59 p.181 4.1",
    "official_requirement": "характеризовать систему звуков",
}]
COVERED_SKILLS = [
    "integrate_vowel_consonant_partition",
    "preserve_subsystem_feature_boundaries",
    "require_integrated_parent_evidence",
    "preserve_sound_letter_boundary_in_system",
    "preserve_sound_system_vs_orthoepy_boundary",
]


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path.name}")
    return value


def main() -> int:
    owner = load(OWNER)
    if owner.get("status") != "CENTRAL_BRAIN_RU01_SOUND_SYSTEM_OWNER_RESOLUTION_CANDIDATE_NOT_ACCEPTED":
        raise AssertionError("sound-system owner-resolution status drift")
    if (owner.get("existing_owner_search") or {}).get("resolution") != "NO_EXACT_CURRENT_SINGLE_SOUND_SYSTEM_OWNER":
        raise AssertionError("sound-system exact owner-search result drift")
    proposed = owner.get("proposed_owner") or {}
    if proposed.get("semantic_id") != SEMANTIC or proposed.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("sound-system proposed owner identity drift")
    if proposed.get("status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("sound-system owner-resolution self-admitted semantic")
    if (owner.get("acceptance_boundary") or {}).get("separate_bounded_semantic_acceptance_required") is not True:
        raise AssertionError("sound-system separate semantic gate requirement weakened")
    if (owner.get("acceptance_boundary") or {}).get("separate_exact_parent_object_gate_required") is not True:
        raise AssertionError("sound-system separate parent-object gate requirement weakened")
    if (owner.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise AssertionError("sound-system owner-resolution false exact mastery drift")

    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_SOUND_SYSTEM_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("sound-system adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate != {
        "semantic_id": SEMANTIC,
        "source_taxonomy_id": TAXONOMY,
        "source_clause_ids": ["EDSOO59-P181-4.1-C"],
        "semantic_ref_status": "PROPOSED_NOT_CANONICAL",
    }:
        raise AssertionError("sound-system candidate identity/source drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "aeba08fe00dbe5626748427e2792e196976b8256":
        raise AssertionError("sound-system learner-content blob drift")
    if learner.get("new_integrated_verification_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-system integrated evidence identity drift")
    if learner.get("forbidden_component_parent_evidence_ids") != FORBIDDEN_COMPONENT_EVIDENCE:
        raise AssertionError("sound-system forbidden component evidence inventory drift")
    for key in (
        "registered_user_identity_required",
        "exact_item_identity_required",
 "server_owned_received_at_required",
        "durable_evidence_event_required_before_future_canonical_write",
    ):
        if learner.get(key) is not True:
            raise AssertionError(f"sound-system PEIS boundary weakened: {key}")

    decision0 = adequacy.get("adequacy_decision") or {}
    for key in (
        "content_exact_for_bounded_sound_system_candidate",
        "official_clause_scope_covered",
        "vowel_and_consonant_subsystems_integrated",
        "subsystem_feature_boundaries_preserved",
        "new_parent_specific_evidence_required",
        "old_component_evidence_not_reused_as_parent_evidence",
        "sound_letter_boundary_preserved",
        "normative_pronunciation_not_inferred",
        "normative_stress_not_inferred",
    ):
        if decision0.get(key) is not True:
            raise AssertionError(f"sound-system adequacy boundary drift: {key}")
    if decision0.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("sound-system adequacy predecessor self-admitted semantic")
    if decision0.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("sound-system adequacy next-state drift")
    for key in (
        "object_level_admission_units_closed",
        "object_level_requirements_closed",
        "exact_mastery_admissions",
        "false_exact_mastery_admissions",
    ):
        if decision0.get(key) != 0:
            raise AssertionError(f"sound-system adequacy admission drift: {key}")

    acceptance = load(ACCEPTANCE)
    if acceptance.get("schema_version") != "0.1.0":
        raise AssertionError("sound-system acceptance schema drift")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_SOUND_SYSTEM_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("sound-system acceptance status drift")
    if acceptance.get("authority_pr") != 164:
        raise AssertionError("sound-system authority PR drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("sound-system acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("sound-system acceptance created parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("owner_resolution") != "russian-program/subject-admission/RU01-SOUND-SYSTEM-OWNER-RESOLUTION-v0.1.json":
        raise AssertionError("sound-system owner-resolution authority drift")
    if authority.get("content_adequacy_builder") != "russian-program/subject-admission/build_ru01_sound_system_content_adequacy_review.py":
        raise AssertionError("sound-system adequacy authority drift")
    if authority.get("learner_content") != "russian-program/production-learning-content/RU-PROG-01-SOUND-SYSTEM-INTEGRATION-WAVE-010-v0.1.json":
        raise AssertionError("sound-system learner-content authority drift")
    if authority.get("learner_content_git_blob_sha1") != "aeba08fe00dbe5626748427e2792e196976b8256":
        raise AssertionError("sound-system learner-content authority blob drift")
    if authority.get("content_adequacy_exact_head_gate") != ADEQUACY_GATE:
        raise AssertionError("sound-system exact-head adequacy gate drift")
    if authority.get("source_clauses") != SOURCE_CLAUSES:
        raise AssertionError("sound-system exact source-clause authority drift")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_source_backed_owner_resolution_required",
        "successful_content_adequacy_gate_required",
        "original_integrated_learner_content_required",
        "parent_specific_independent_evidence_required",
        "parallel_registry_creation_forbidden",
        "separate_exact_parent_object_component_set_acceptance_required",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"sound-system acceptance policy weakened: {key}")
    for key in (
        "vowel_system_semantic_may_substitute_parent",
        "consonant_system_semantic_may_substitute_parent",
        "sound_characterization_semantic_may_substitute_parent",
        "sound_letter_relation_semantic_may_substitute_parent",
        "normative_pronunciation_semantic_may_substitute_parent",
        "normative_stress_semantic_may_substitute_parent",
        "p01_u9_or_u10_component_evidence_may_be_reused_as_parent_evidence",
        "route_title_task_number_keyword_fuzzy_or_embedding_can_admit_semantics",
        "canonical_school_registry_mutation_required",
        "content_or_evidence_presence_alone_is_semantic_admission",
        "subject_semantic_acceptance_can_reduce_parent_object_counts",
        "generic_ru01_result_can_emit_exact_component_mastery",
        "parent_object_can_close_without_separate_exact_head_object_gate",
        "shared_sound_system_evidence_can_close_sibling_objects",
        "whole_group_acceptance_allowed",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"sound-system acceptance policy opened: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("sound-system acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("sound-system semantic crosswalk drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("sound-system semantic not explicitly accepted")
    if decision.get("owner_search_result") != "NO_EXACT_CURRENT_SINGLE_OWNER_THEN_BOUNDED_INTEGRATED_CANDIDATE":
        raise AssertionError("sound-system owner-search result drift")
    if decision.get("source_evidence_status") != "CONFIRMED_FOR_EXACT_OFFICIAL_EDSOO59_P181_4_1_C_CLAUSE":
        raise AssertionError("sound-system source evidence drift")
    if decision.get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise AssertionError("accepted sound-system evidence drift")
    if decision.get("forbidden_reused_component_evidence_item_ids") != FORBIDDEN_COMPONENT_EVIDENCE:
        raise AssertionError("sound-system reused component evidence drift")
    if decision.get("covered_skills") != COVERED_SKILLS:
        raise AssertionError("accepted sound-system skill boundary drift")
    if decision.get("parent_object_binding_status") != "NOT_BOUND_UNTIL_SEPARATE_EXACT_HEAD_PARENT_OBJECT_GATE":
        raise AssertionError("sound-system acceptance improperly closes parent object")
    guard = str(decision.get("boundary_guard") or "").lower()
    for fragment in ("p01-u12", "p01-u9", "p01-u10", "supporting context only", "sound-letter", "pronunciation", "stress", "separate exact-head object gate"):
        if fragment not in guard:
            raise AssertionError(f"sound-system boundary guard drift: {fragment}")

    if acceptance.get("summary") != {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "new_school_canonical_identities": 0,
        "parent_object_admission_units_closed": 0,
        "parent_object_requirements_closed": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }:
        raise AssertionError("sound-system acceptance summary drift")

    next_work = acceptance.get("next_exact_work") or {}
    if next_work.get("sound_system_parent_specific_evidence_ids") != VERIFICATION_IDS:
        raise AssertionError("sound-system next evidence set drift")
    if next_work.get("component_evidence_auto_promotion_forbidden") is not True:
        raise AssertionError("sound-system component evidence auto-promotion boundary weakened")
    if next_work.get("separate_exact_head_parent_object_gate_required") is not True:
        raise AssertionError("sound-system separate parent-object gate no longer required")
    pending = next_work.get("parent_objects_remain_pending") or []
    if pending != [{
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "requirement_id": "RSK-EDSOO59-4-1-P181",
        "sound_characterization_clause_id": "EDSOO59-P181-4.1-A",
        "sound_letter_relation_clause_id": "EDSOO59-P181-4.1-B",
        "sound_system_clause_id": "EDSOO59-P181-4.1-C",
    }]:
        raise AssertionError("sound-system parent-object frontier drift")

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
        raise AssertionError(f"duplicate sound-system semantic acceptance: {duplicates}")

    print("RU01_SOUND_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SUBJECT_SEMANTICS=1")
    print("PARENT_OBJECTS_PENDING=1")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("INDEPENDENT_PARENT_EVIDENCE_ITEMS=5")
    print("FORBIDDEN_REUSED_COMPONENT_EVIDENCE_ITEMS=10")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
