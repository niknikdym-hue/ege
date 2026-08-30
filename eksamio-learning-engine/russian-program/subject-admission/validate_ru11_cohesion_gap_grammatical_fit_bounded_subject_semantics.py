#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
ACCEPTANCE = HERE / "RU11-COHESION-GAP-GRAMMATICAL-FIT-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
BROADER = PROGRAM / "production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-COHESION-GAP-GRAMMATICAL-FIT-WAVE-008-v0.1.json"

CANDIDATE = "candidate-001"
TAXONOMY = "cohesion_gap_grammatical_fit"
SEMANTIC = "ru-text-cohesion-gap-grammatical-fit"
CANONICAL_LABEL = "Подбор средства связи по смыслу и грамматической форме"
EXPECTED_CHECK_IDS = {"p11-coh-gap-v1", "p11-coh-gap-v2", "p11-coh-gap-v3"}
EXPECTED_BROADER_CHECK_IDS = {"p11-u2-v1", "p11-u2-v2"}
EXPECTED_CANDIDATES = {
    "candidate-001", "candidate-002", "candidate-003", "candidate-004",
    "candidate-005", "candidate-006", "candidate-007", "candidate-043",
    "candidate-044", "candidate-045", "candidate-046", "candidate-047",
}
ADJACENT = sorted(EXPECTED_CANDIDATES - {CANDIDATE})


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    broader = json.loads(BROADER.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU11_COHESION_GAP_GRAMMATICAL_FIT_BOUNDED_SUBJECT_SEMANTIC" or acceptance.get("authority_issue") != 161:
        raise AssertionError("RU11 candidate-001 acceptance authority/status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU11 candidate-001 registry boundary drift")

    sg = acceptance.get("source_truth_guard") or {}
    if sg.get("inventory_candidate_review_status") != "draft" or sg.get("inventory_candidate_status_silently_upgraded") is not False:
        raise AssertionError("RU11 candidate-001 inventory source guard drift")
    if sg.get("taxonomy_backing_review_status") != "source_verified" or sg.get("skill_graph_evidence_status") != "confirmed":
        raise AssertionError("RU11 candidate-001 taxonomy/graph guard drift")
    if len(sg.get("accepted_positive_scope") or []) != 3:
        raise AssertionError("RU11 candidate-001 positive boundary drift")
    for key in ("specific_device_family_mastery_admitted", "generic_task1_mastery_admitted", "generic_task26_mastery_admitted"):
        if sg.get(key) is not False:
            raise AssertionError(f"RU11 candidate-001 source guard weakened: {key}")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_current_source_identity_required",
        "source_verified_taxonomy_backing_required",
        "confirmed_skill_graph_evidence_required",
        "current_missing_subject_candidate_required",
        "draft_candidate_status_must_be_preserved",
        "exact_school_meaning_collision_forbidden",
        "reuse_first",
        "component_specific_independent_evidence_required",
        "school_duplicate_forbidden",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU11 candidate-001 policy weakened: {key}")
    if policy.get("minimum_component_specific_independent_checks") != 2 or policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU11 candidate-001 component/namespace policy drift")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "specific_device_family_mastery_admitted_by_this_authority",
        "generic_task1_result_can_emit_exact_component_mastery",
        "generic_task26_result_can_emit_exact_component_mastery",
        "broader_link_means_result_can_emit_exact_gap_selection_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU11 candidate-001 fail-closed policy drift: {key}")

    module = {str(r.get("module_id")): r for r in program.get("modules", []) if isinstance(r, dict)}.get("RU-PROG-11")
    if not isinstance(module, dict) or module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING" or set(module.get("candidate_refs") or []) != EXPECTED_CANDIDATES:
        raise AssertionError("RU11 module/candidate-set drift")

    objects = [r for r in inventory.get("objects", []) if isinstance(r, dict)]
    candidate = one([
        r for r in objects
        if r.get("source_system") == "semantic_candidate"
        and r.get("source_id") == CANDIDATE
        and r.get("authority_status") == "current"
    ], "RU11 candidate-001")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE" or candidate.get("candidate_canonical_owner") != CANDIDATE:
        raise AssertionError("RU11 candidate-001 inventory ownership drift")
    if candidate.get("current_semantic_refs") != [TAXONOMY] or candidate.get("review_status") != "draft" or normalized(candidate.get("observed_meaning")) != CANONICAL_LABEL:
        raise AssertionError("RU11 candidate-001 inventory meaning/status drift")

    backing = one([
        r for r in objects
        if r.get("source_system") == "ege_skill_graph"
        and r.get("source_id") == TAXONOMY
        and r.get("authority_status") == "current"
        and r.get("candidate_canonical_owner") == CANDIDATE
    ], "RU11 candidate-001 backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU11 candidate-001 taxonomy backing status drift")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate-001 taxonomy meaning drift")

    skill = one([r for r in graph.get("skills", []) if isinstance(r, dict) and r.get("skill_id") == TAXONOMY], "RU11 cohesion-gap graph node")
    if skill.get("evidence_status") != "confirmed" or skill.get("parent_skill_id") != "text_cohesion" or skill.get("exam_task_numbers") != [1]:
        raise AssertionError("RU11 cohesion-gap graph evidence/route drift")
    if skill.get("name_ru") != CANONICAL_LABEL or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 cohesion-gap graph/source meaning drift")

    if any(SEMANTIC in {str(ref) for ref in (r.get("current_semantic_refs") or [])} for r in objects if r.get("authority_status") == "current"):
        raise AssertionError("RU11 candidate-001 semantic collision")
    if any(
        r.get("source_system") == "school_canonical"
        and r.get("authority_status") == "current"
        and normalized(r.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
        for r in objects
    ):
        raise AssertionError("RU11 candidate-001 exact school meaning exists; reuse required")

    broad_unit = one([
        r for r in broader.get("units", [])
        if isinstance(r, dict) and r.get("proposed_semantic_id") == "ru-text-cohesion-link-means"
    ], "RU11 broader cohesion-link-means unit")
    broad_checks = [r for r in (broad_unit.get("independent_verification") or []) if isinstance(r, dict)]
    if {str(r.get("id")) for r in broad_checks} != EXPECTED_BROADER_CHECK_IDS:
        raise AssertionError("RU11 broader cohesion independent-check set drift")
    if any("пропуск" in str(r.get("prompt") or "").lower() for r in broad_checks):
        raise AssertionError("RU11 broader cohesion unit gained direct gap-selection verification; reuse review must be redone")

    reuse = acceptance.get("reuse_first_decision") or {}
    if reuse.get("broader_existing_unit_present") is not True or reuse.get("broader_existing_unit_reused_as_scope_and_explanation_evidence") is not True:
        raise AssertionError("RU11 candidate-001 reuse-first guard drift")
    if reuse.get("broader_existing_unit_is_exact_candidate_001_mastery_evidence") is not False or reuse.get("broader_existing_unit_direct_gap_selection_independent_checks") != 0:
        raise AssertionError("RU11 candidate-001 broader-unit exact-evidence drift")
    if reuse.get("minimum_component_specific_independent_checks_for_this_acceptance") != 2 or reuse.get("exact_new_unit_component_specific_gap_selection_checks") != 3:
        raise AssertionError("RU11 candidate-001 verification-count drift")
    if reuse.get("new_content_materialized_only_for_proven_component_verification_gap") is not True:
        raise AssertionError("RU11 candidate-001 new-content justification drift")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 cohesion-gap content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU11 cohesion-gap copyright guard drift")
    content_reuse = content.get("reuse_review") or {}
    if content_reuse.get("broader_existing_unit_direct_gap_selection_independent_checks") != 0 or content_reuse.get("broader_existing_unit_reused_as_exact_candidate_001_mastery_evidence") is not False or content_reuse.get("new_content_materialized_only_for_proven_gap_selection_verification_gap") is not True:
        raise AssertionError("RU11 cohesion-gap content reuse guard drift")

    unit = one([r for r in content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == SEMANTIC], "RU11 cohesion-gap learner unit")
    if unit.get("title_ru") != CANONICAL_LABEL:
        raise AssertionError("RU11 cohesion-gap learner title drift")
    for key, minimum in (
        ("decision_algorithm", 6),
        ("worked_examples", 4),
        ("misconceptions", 4),
        ("guided_practice", 3),
        ("independent_practice", 4),
        ("mixed_transfer_practice", 2),
        ("retention_items", 2),
        ("independent_verification", 3),
    ):
        if not isinstance(unit.get(key), list) or len(unit[key]) < minimum:
            raise AssertionError(f"RU11 cohesion-gap learner section incomplete: {key}")

    checks = [r for r in (unit.get("independent_verification") or []) if isinstance(r, dict)]
    if {str(r.get("id")) for r in checks} != EXPECTED_CHECK_IDS or len(checks) != 3:
        raise AssertionError("RU11 cohesion-gap exact verification ids drift")
    if any(r.get("type") != "constructed_response" for r in checks):
        raise AssertionError("RU11 cohesion-gap verification must remain constructed-response")
    if any((r.get("scoring") or {}).get("max_points") != 3 or len((r.get("scoring") or {}).get("criteria") or []) != 3 for r in checks):
        raise AssertionError("RU11 cohesion-gap verification scoring drift")

    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("source_candidate_ref") != CANDIDATE or peis.get("source_candidate_review_status") != "draft":
        raise AssertionError("RU11 cohesion-gap PEIS source identity drift")
    if peis.get("independent_verification_required") is not True or peis.get("exact_mastery_requires_two_or_more_component_specific_gap_selection_checks") is not True:
        raise AssertionError("RU11 cohesion-gap PEIS independent-evidence guard drift")
    for key in (
        "generic_task1_result_can_emit_exact_component_mastery",
        "generic_task26_result_can_emit_exact_component_mastery",
        "specific_device_family_mastery_admitted",
        "broader_link_means_unit_can_emit_exact_gap_selection_mastery",
    ):
        if peis.get(key) is not False:
            raise AssertionError(f"RU11 cohesion-gap PEIS fail-closed drift: {key}")

    forbidden = " ".join((unit.get("tutor_grounding") or {}).get("forbidden") or []).lower()
    for needle in ("task-1", "task-26", "determinative", "conjunction"):
        if needle not in forbidden:
            raise AssertionError(f"RU11 cohesion-gap Tutor guard missing: {needle}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU11 candidate-001 acceptance must contain one decision")
    d = decisions[0]
    if d.get("candidate_ref") != CANDIDATE or d.get("source_taxonomy_id") != TAXONOMY or d.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("RU11 candidate-001 acceptance crosswalk identity drift")
    if d.get("canonical_label_ru") != CANONICAL_LABEL or d.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU11 candidate-001 accepted semantic status drift")
    if d.get("source_evidence_status") != "confirmed" or d.get("source_candidate_inventory_review_status") != "draft":
        raise AssertionError("RU11 candidate-001 accepted source status drift")
    if d.get("excluded_adjacent_candidate_refs") != ADJACENT or d.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU11 candidate-001 adjacent/object boundary drift")

    summary = acceptance.get("summary") or {}
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1 or summary.get("source_backed_candidates_consumed") != 1:
        raise AssertionError("RU11 candidate-001 acceptance count drift")
    if summary.get("adjacent_candidates_admitted") != 0 or summary.get("specific_device_family_masteries_admitted") != 0 or summary.get("new_school_canonical_identities") != 0:
        raise AssertionError("RU11 candidate-001 false neighboring admission")
    if summary.get("object_level_admission_units_closed") != 0 or summary.get("object_level_requirements_closed") != 0 or summary.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU11 candidate-001 false object/mastery closure")

    digest = hashlib.sha256(json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU11_COHESION_GAP_GRAMMATICAL_FIT_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"SOURCE_CANDIDATE_REVIEW_STATUS={candidate.get('review_status')}")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("BROADER_EXISTING_DIRECT_GAP_SELECTION_CHECKS=0")
    print(f"EXACT_COMPONENT_CHECKS={len(checks)}")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
