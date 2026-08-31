#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

ACCEPTANCE = HERE / "RU11-SEMANTIC-RELATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
REVIEW = HERE / "RU11-SEMANTIC-RELATION-CONTENT-ADEQUACY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
BROADER_CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
EXACT_CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-SEMANTIC-RELATION-WAVE-005-v0.1.json"

CANDIDATE = "candidate-047"
TAXONOMY = "semantic_relation_between_sentences"
SEMANTIC = "ru-text-semantic-relation-between-sentences"
LABEL = "Определение причинных, следственных, пояснительных и противительных отношений между предложениями"
EXPECTED_CANDIDATES = {
    "candidate-001", "candidate-002", "candidate-003", "candidate-004", "candidate-005",
    "candidate-006", "candidate-007", "candidate-043", "candidate-044", "candidate-045",
    "candidate-046", "candidate-047",
}
ADJACENT = sorted(EXPECTED_CANDIDATES - {CANDIDATE})
EXPECTED_CHECK_IDS = {"p11-rel-v1", "p11-rel-v2", "p11-rel-v3", "p11-rel-v4"}


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], message: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{message}: expected 1, got {len(rows)}")
    return rows[0]


def has_relation_family(value: Any) -> bool:
    text = json.dumps(value, ensure_ascii=False).lower()
    return any(token in text for token in ("причин", "следств", "поясн", "против"))


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    broader = json.loads(BROADER_CONTENT.read_text(encoding="utf-8"))
    content = json.loads(EXACT_CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU11_SEMANTIC_RELATION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU11 candidate-047 acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("RU11 candidate-047 authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU11 candidate-047 acceptance mutated/duplicated registry")

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
            raise AssertionError(f"RU11 candidate-047 acceptance policy weakened: {key}")
    if policy.get("minimum_component_specific_independent_checks") != 4:
        raise AssertionError("RU11 candidate-047 minimum independent checks drift")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "out_of_scope_relation_families_admitted",
        "link_means_mastery_admitted_by_this_authority",
        "speech_type_mastery_admitted_by_this_authority",
        "narration_description_reasoning_mastery_admitted_by_this_authority",
        "generic_task24_result_can_emit_exact_component_mastery",
        "link_means_result_can_emit_exact_component_mastery",
        "speech_type_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU11 candidate-047 fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU11 candidate-047 namespace drift")

    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get("RU-PROG-11")
    if not isinstance(module, dict) or module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING":
        raise AssertionError("RU11 current program binding-mode drift")
    if set(module.get("candidate_refs") or []) != EXPECTED_CANDIDATES:
        raise AssertionError("RU11 current candidate set drift")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    candidate = one([
        row for row in objects
        if row.get("source_system") == "semantic_candidate"
        and row.get("source_id") == CANDIDATE
        and row.get("authority_status") == "current"
    ], "RU11 candidate-047 current inventory")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
        raise AssertionError("RU11 candidate-047 classification drift")
    if candidate.get("candidate_canonical_owner") != CANDIDATE or candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise AssertionError("RU11 candidate-047 inventory ownership/taxonomy drift")
    if candidate.get("review_status") != "draft":
        raise AssertionError("RU11 candidate-047 draft status was silently upgraded")
    if candidate.get("observed_label") != LABEL:
        raise AssertionError("RU11 candidate-047 label drift")

    backing = one([
        row for row in objects
        if row.get("source_system") == "ege_skill_graph"
        and row.get("source_id") == TAXONOMY
        and row.get("authority_status") == "current"
        and row.get("candidate_canonical_owner") == CANDIDATE
    ], "RU11 candidate-047 taxonomy backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU11 candidate-047 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate-047 inventory/backing meaning mismatch")

    skill = one([
        row for row in graph.get("skills", [])
        if isinstance(row, dict) and row.get("skill_id") == TAXONOMY
    ], "RU11 candidate-047 graph node")
    if skill.get("evidence_status") != "confirmed" or skill.get("parent_skill_id") != "speech_type_analysis" or skill.get("exam_task_numbers") != [24]:
        raise AssertionError("RU11 candidate-047 confirmed Task-24 graph boundary drift")
    if skill.get("name_ru") != LABEL or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate-047 graph meaning drift")

    collisions = [
        row for row in objects
        if row.get("authority_status") == "current"
        and SEMANTIC in {str(ref) for ref in (row.get("current_semantic_refs") or [])}
    ]
    if collisions:
        raise AssertionError("RU11 candidate-047 semantic id collides with current inventory")
    school_exact = [
        row for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and normalized(row.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
    ]
    if school_exact:
        raise AssertionError("RU11 candidate-047 exact school meaning already exists; reuse required")

    if review.get("status") != "CENTRAL_BRAIN_RU11_SEMANTIC_RELATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU11 candidate-047 content review status drift")
    rd = review.get("review_decision") or {}
    if rd.get("content_exact_for_current_candidate_047_source_meaning") is not True:
        raise AssertionError("RU11 candidate-047 content exactness not proven")
    if rd.get("source_candidate_inventory_status_preserved_as_draft") is not True:
        raise AssertionError("RU11 candidate-047 draft-source guard missing")
    if rd.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("RU11 candidate-047 content review self-admitted semantic")
    if rd.get("object_level_admission_units_closed") != 0 or rd.get("object_level_requirements_closed") != 0 or rd.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU11 candidate-047 content review falsely closed mastery")
    if rd.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_WITH_DRAFT_CANDIDATE_GUARD":
        raise AssertionError("RU11 candidate-047 content review next-status drift")

    broad_unit = one([
        row for row in broader.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == "ru-text-cohesion-link-means"
    ], "RU11 broader cohesion unit")
    direct_relation_checks = sum(1 for row in (broad_unit.get("independent_verification") or []) if isinstance(row, dict) and has_relation_family(row))
    if direct_relation_checks != 1:
        raise AssertionError(f"RU11 reuse-gap proof drift: expected 1 relation-bearing broader check, got {direct_relation_checks}")

    reuse = acceptance.get("reuse_first_decision") or {}
    if reuse.get("broader_existing_unit_present") is not True or reuse.get("broader_existing_unit_reused_as_scope_and_explanation_evidence") is not True:
        raise AssertionError("RU11 candidate-047 reuse-first evidence drift")
    if reuse.get("broader_existing_unit_is_exact_candidate_047_mastery_evidence") is not False:
        raise AssertionError("RU11 candidate-047 broader unit incorrectly treated as exact mastery")
    if reuse.get("broader_existing_unit_direct_relation_bearing_independent_checks") != 1:
        raise AssertionError("RU11 candidate-047 broader-check count drift")
    if reuse.get("minimum_component_specific_independent_checks_for_this_acceptance") != 4:
        raise AssertionError("RU11 candidate-047 exact-check threshold drift")
    if reuse.get("new_content_materialized_only_for_proven_component_verification_gap") is not True:
        raise AssertionError("RU11 candidate-047 gap-only materialization drift")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 candidate-047 exact learner-content status/module drift")
    provenance = content.get("source_provenance") or []
    draft_source = one([
        row for row in provenance
        if isinstance(row, dict) and row.get("kind") == "current_draft_subject_semantic_candidate"
    ], "RU11 candidate-047 draft provenance")
    if draft_source.get("review_status") != "draft" or draft_source.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
        raise AssertionError("RU11 candidate-047 exact content falsely upgrades draft source")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU11 candidate-047 provenance/copyright boundary weakened")

    unit = one([
        row for row in content.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == SEMANTIC
    ], "RU11 candidate-047 exact learner unit")
    checks = [row for row in (unit.get("independent_verification") or []) if isinstance(row, dict)]
    if {row.get("id") for row in checks} != EXPECTED_CHECK_IDS or len(checks) != 4:
        raise AssertionError("RU11 candidate-047 exact four-check verification set drift")
    if any(row.get("type") != "constructed_response" for row in checks):
        raise AssertionError("RU11 candidate-047 verification weakened from constructed response")
    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("source_candidate_review_status") != "draft":
        raise AssertionError("RU11 candidate-047 PEIS source/semantic boundary drift")
    if peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError("RU11 candidate-047 PEIS independent-evidence boundary weakened")
    for key in (
        "generic_task24_result_can_emit_exact_component_mastery",
        "link_means_unit_result_can_emit_exact_component_mastery",
        "speech_type_result_can_emit_this_mastery",
        "out_of_scope_relation_result_can_emit_this_mastery",
        "object_closure_implied",
    ):
        if peis.get(key) is not False:
            raise AssertionError(f"RU11 candidate-047 PEIS mastery leak: {key}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU11 candidate-047 acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("candidate_ref") != CANDIDATE or decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("RU11 candidate-047 acceptance crosswalk drift")
    if decision.get("canonical_label_ru") != LABEL:
        raise AssertionError("RU11 candidate-047 acceptance label drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC" or decision.get("source_evidence_status") != "confirmed":
        raise AssertionError("RU11 candidate-047 acceptance evidence/status drift")
    if decision.get("source_candidate_inventory_review_status") != "draft":
        raise AssertionError("RU11 candidate-047 acceptance silently upgrades source candidate")
    if decision.get("excluded_adjacent_candidate_refs") != ADJACENT:
        raise AssertionError("RU11 candidate-047 adjacent exclusion drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU11 candidate-047 object-binding boundary drift")

    summary = acceptance.get("summary") or {}
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1:
        raise AssertionError("RU11 candidate-047 accepted-semantic count drift")
    if summary.get("source_backed_candidates_consumed") != 1 or summary.get("new_original_production_content_units_used") != 1:
        raise AssertionError("RU11 candidate-047 source/content count drift")
    for key in (
        "adjacent_candidates_admitted",
        "out_of_scope_relation_families_admitted",
        "new_school_canonical_identities",
        "object_level_admission_units_closed",
        "object_level_requirements_closed",
        "false_exact_mastery_admissions",
    ):
        if summary.get(key) != 0:
            raise AssertionError(f"RU11 candidate-047 acceptance leak: {key}")

    digest = hashlib.sha256(json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU11_SEMANTIC_RELATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"SOURCE_CANDIDATE_REVIEW_STATUS={candidate.get('review_status')}")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("BROADER_DIRECT_RELATION_CHECKS=1")
    print("EXACT_COMPONENT_CHECKS=4")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
