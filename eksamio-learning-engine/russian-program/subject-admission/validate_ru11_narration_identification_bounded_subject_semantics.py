#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

ACCEPTANCE = HERE / "RU11-NARRATION-IDENTIFICATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
REVIEW = HERE / "RU11-NARRATION-IDENTIFICATION-CONTENT-ADEQUACY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
BROADER_CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
EXACT_CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-NARRATION-IDENTIFICATION-WAVE-006-v0.1.json"

CANDIDATE = "candidate-044"
TAXONOMY = "narration_identification"
SEMANTIC = "ru-text-narration-identification"
SOURCE_LABEL = "Определение повествования"
CANONICAL_LABEL = "Распознавание повествования"
BROADER_SEMANTIC = "ru-text-speech-type-reasoning-description-narration"
EXPECTED_CHECK_IDS = {"p11-nar-v1", "p11-nar-v2"}
EXPECTED_CANDIDATES = {
    "candidate-001", "candidate-002", "candidate-003", "candidate-004", "candidate-005",
    "candidate-006", "candidate-007", "candidate-043", "candidate-044", "candidate-045",
    "candidate-046", "candidate-047",
}
ADJACENT = sorted(EXPECTED_CANDIDATES - {CANDIDATE})


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def mentions_narration(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return "повеств" in text or "narration" in text


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    broader = json.loads(BROADER_CONTENT.read_text(encoding="utf-8"))
    content = json.loads(EXACT_CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU11_NARRATION_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU11 candidate-044 acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("RU11 candidate-044 authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU11 candidate-044 acceptance mutated/duplicated registry")

    source_guard = acceptance.get("source_truth_guard") or {}
    if (
        source_guard.get("inventory_candidate_review_status") != "draft"
        or source_guard.get("inventory_candidate_status_silently_upgraded") is not False
        or source_guard.get("taxonomy_backing_review_status") != "source_verified"
        or source_guard.get("skill_graph_evidence_status") != "confirmed"
        or source_guard.get("accepted_positive_scope") != ["event sequence", "change of states over time"]
        or source_guard.get("description_mastery_admitted") is not False
        or source_guard.get("reasoning_mastery_admitted") is not False
        or source_guard.get("generic_combined_speech_type_mastery_admitted") is not False
    ):
        raise AssertionError("RU11 candidate-044 source-truth guard drift")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_current_source_identity_required",
        "source_verified_taxonomy_backing_required",
        "confirmed_skill_graph_evidence_required",
        "current_missing_subject_candidate_required",
        "draft_candidate_status_must_be_preserved",
        "content_adequacy_review_required",
        "exact_school_meaning_collision_forbidden",
        "reuse_first",
        "component_specific_independent_evidence_required",
        "school_duplicate_forbidden",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU11 candidate-044 acceptance policy weakened: {key}")
    if policy.get("minimum_component_specific_independent_checks") != 2:
        raise AssertionError("RU11 candidate-044 minimum independent checks drift")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "description_mastery_admitted_by_this_authority",
        "reasoning_mastery_admitted_by_this_authority",
        "semantic_relation_mastery_admitted_by_this_authority",
        "generic_task24_result_can_emit_exact_component_mastery",
        "combined_speech_type_result_can_emit_exact_component_mastery",
        "verb_count_or_marker_word_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU11 candidate-044 fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU11 candidate-044 namespace drift")

    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get("RU-PROG-11")
    if not isinstance(module, dict) or module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING":
        raise AssertionError("RU11 module/binding drift")
    if set(module.get("candidate_refs") or []) != EXPECTED_CANDIDATES:
        raise AssertionError("RU11 candidate-set drift")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    candidate = one([
        row for row in objects
        if row.get("source_system") == "semantic_candidate"
        and row.get("source_id") == CANDIDATE
        and row.get("authority_status") == "current"
    ], "RU11 candidate-044 current inventory")
    if (
        candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
        or candidate.get("candidate_canonical_owner") != CANDIDATE
        or candidate.get("current_semantic_refs") != [TAXONOMY]
        or candidate.get("review_status") != "draft"
        or candidate.get("observed_label") != SOURCE_LABEL
    ):
        raise AssertionError("RU11 candidate-044 inventory boundary drift")

    backing = one([
        row for row in objects
        if row.get("source_system") == "ege_skill_graph"
        and row.get("source_id") == TAXONOMY
        and row.get("authority_status") == "current"
        and row.get("candidate_canonical_owner") == CANDIDATE
    ], "RU11 candidate-044 taxonomy backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU11 candidate-044 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate/backing meaning mismatch")

    skill = one([
        row for row in graph.get("skills", [])
        if isinstance(row, dict) and row.get("skill_id") == TAXONOMY
    ], "RU11 candidate-044 graph node")
    if (
        skill.get("evidence_status") != "confirmed"
        or skill.get("parent_skill_id") != "speech_type_analysis"
        or skill.get("exam_task_numbers") != [24]
        or skill.get("name_ru") != SOURCE_LABEL
        or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning"))
    ):
        raise AssertionError("RU11 candidate-044 confirmed graph boundary drift")

    collisions = [
        row for row in objects
        if row.get("authority_status") == "current"
        and SEMANTIC in {str(ref) for ref in (row.get("current_semantic_refs") or [])}
    ]
    if collisions:
        raise AssertionError("RU11 candidate-044 semantic id collides with current inventory")
    exact_school_meaning = [
        row for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and normalized(row.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
    ]
    if exact_school_meaning:
        raise AssertionError("RU11 candidate-044 exact school meaning already exists; reuse required")

    if review.get("status") != "CENTRAL_BRAIN_RU11_NARRATION_IDENTIFICATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU11 narration adequacy review status drift")
    review_source = review.get("source_identity") or {}
    if (
        review_source.get("candidate_ref") != CANDIDATE
        or review_source.get("source_taxonomy_id") != TAXONOMY
        or review_source.get("inventory_review_status") != "draft"
        or review_source.get("skill_graph_evidence_status") != "confirmed"
        or review_source.get("taxonomy_backing_review_status") != "source_verified"
    ):
        raise AssertionError("RU11 narration adequacy source truth drift")
    review_decision = review.get("review_decision") or {}
    if (
        review_decision.get("content_exact_for_current_candidate_044_source_meaning") is not True
        or review_decision.get("source_candidate_inventory_status_preserved_as_draft") is not True
        or review_decision.get("semantic_admission_by_this_review") is not False
        or review_decision.get("object_level_admission_units_closed") != 0
        or review_decision.get("object_level_requirements_closed") != 0
        or review_decision.get("false_exact_mastery_admissions") != 0
        or review_decision.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_WITH_DRAFT_CANDIDATE_GUARD"
    ):
        raise AssertionError("RU11 narration adequacy decision drift")

    if broader.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or broader.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 broader-content authority drift")
    broader_unit = one([
        row for row in broader.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == BROADER_SEMANTIC
    ], "RU11 broader speech-type unit")
    broader_checks = [row for row in broader_unit.get("independent_verification", []) if isinstance(row, dict)]
    direct_narration_checks = sum(1 for row in broader_checks if mentions_narration(row))
    if direct_narration_checks != 0:
        raise AssertionError(f"RU11 narration reuse-gap proof drift: expected 0 direct checks, got {direct_narration_checks}")

    reuse = acceptance.get("reuse_first_decision") or {}
    if (
        reuse.get("broader_existing_unit_present") is not True
        or reuse.get("broader_existing_unit_reused_as_scope_and_explanation_evidence") is not True
        or reuse.get("broader_existing_unit_is_exact_candidate_044_mastery_evidence") is not False
        or reuse.get("broader_existing_unit_direct_narration_independent_checks") != 0
        or reuse.get("minimum_component_specific_independent_checks_for_this_acceptance") != 2
        or reuse.get("new_content_materialized_only_for_proven_component_verification_gap") is not True
    ):
        raise AssertionError("RU11 candidate-044 reuse-gap decision drift")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 candidate-044 learner-content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU11 candidate-044 learner-content provenance boundary weakened")
    unit = one([
        row for row in content.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == SEMANTIC
    ], "RU11 candidate-044 exact learner unit")
    if unit.get("title_ru") != CANONICAL_LABEL:
        raise AssertionError("RU11 candidate-044 learner-unit title drift")
    for key, minimum in (
        ("decision_algorithm", 6),
        ("worked_examples", 4),
        ("misconceptions", 4),
        ("guided_practice", 3),
        ("independent_practice", 3),
        ("mixed_transfer_practice", 2),
        ("retention_items", 2),
        ("independent_verification", 2),
    ):
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"RU11 candidate-044 learner section incomplete: {key}")
    checks = [row for row in unit.get("independent_verification", []) if isinstance(row, dict)]
    if {row.get("id") for row in checks} != EXPECTED_CHECK_IDS or len(checks) != 2:
        raise AssertionError("RU11 candidate-044 exact verification set drift")
    if any(row.get("type") != "constructed_response" for row in checks) or not all(mentions_narration(row) for row in checks):
        raise AssertionError("RU11 candidate-044 verification no longer directly tests narration")
    if any((row.get("scoring") or {}).get("max_points") != 3 for row in checks):
        raise AssertionError("RU11 candidate-044 verification scoring drift")

    peis = unit.get("peis_evidence") or {}
    if (
        peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL"
        or peis.get("source_candidate_review_status") != "draft"
        or peis.get("independent_verification_required") is not True
        or peis.get("assistance_must_be_recorded") is not True
        or peis.get("exact_mastery_requires_two_component_specific_narration_checks") is not True
        or peis.get("generic_task24_result_can_emit_exact_component_mastery") is not False
        or peis.get("combined_speech_type_unit_result_can_emit_exact_component_mastery") is not False
        or peis.get("description_or_reasoning_result_can_emit_this_mastery") is not False
        or peis.get("object_closure_implied") is not False
    ):
        raise AssertionError("RU11 candidate-044 PEIS mastery boundary weakened")
    tutor = unit.get("tutor_grounding") or {}
    forbidden = " ".join(tutor.get("forbidden") or []).lower()
    if not tutor.get("allowed") or not tutor.get("forbidden") or ("verb" not in forbidden and "глаг" not in forbidden) or "task-24" not in forbidden:
        raise AssertionError("RU11 candidate-044 Tutor grounding guard drift")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU11 candidate-044 acceptance must contain exactly one decision")
    decision = decisions[0]
    if (
        decision.get("candidate_ref") != CANDIDATE
        or decision.get("source_taxonomy_id") != TAXONOMY
        or decision.get("accepted_semantic_id") != SEMANTIC
        or decision.get("canonical_label_ru") != CANONICAL_LABEL
        or decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC"
        or decision.get("source_evidence_status") != "confirmed"
        or decision.get("source_candidate_inventory_review_status") != "draft"
        or decision.get("excluded_adjacent_candidate_refs") != ADJACENT
        or decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    ):
        raise AssertionError("RU11 candidate-044 acceptance crosswalk/boundary drift")

    summary = acceptance.get("summary") or {}
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1:
        raise AssertionError("RU11 candidate-044 accepted semantic count drift")
    if summary.get("adjacent_candidates_admitted") != 0 or summary.get("new_school_canonical_identities") != 0:
        raise AssertionError("RU11 candidate-044 acceptance leaked adjacent/parallel identities")
    if summary.get("object_level_admission_units_closed") != 0 or summary.get("object_level_requirements_closed") != 0 or summary.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU11 candidate-044 acceptance falsely closes object mastery")

    digest = hashlib.sha256(json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU11_NARRATION_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"SOURCE_CANDIDATE_REVIEW_STATUS={candidate.get('review_status')}")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print(f"BROADER_EXISTING_DIRECT_NARRATION_CHECKS={direct_narration_checks}")
    print(f"EXACT_COMPONENT_CHECKS={len(checks)}")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
