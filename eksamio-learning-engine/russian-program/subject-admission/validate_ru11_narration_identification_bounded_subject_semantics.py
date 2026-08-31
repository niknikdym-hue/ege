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
BROADER = PROGRAM / "production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-11-NARRATION-IDENTIFICATION-WAVE-006-v0.1.json"

CANDIDATE = "candidate-044"
TAXONOMY = "narration_identification"
SEMANTIC = "ru-text-narration-identification"
CANONICAL_LABEL = "Распознавание повествования"
EXPECTED_CHECK_IDS = {"p11-nar-v1", "p11-nar-v2"}
EXPECTED_CANDIDATES = {"candidate-001","candidate-002","candidate-003","candidate-004","candidate-005","candidate-006","candidate-007","candidate-043","candidate-044","candidate-045","candidate-046","candidate-047"}
ADJACENT = sorted(EXPECTED_CANDIDATES - {CANDIDATE})


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def direct_narration_check(item: dict[str, Any]) -> bool:
    prompt = str(item.get("prompt") or "").lower()
    return "повеств" in prompt or "narration" in prompt


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    broader = json.loads(BROADER.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU11_NARRATION_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC" or acceptance.get("authority_issue") != 161:
        raise AssertionError("RU11 candidate-044 acceptance authority/status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU11 candidate-044 registry boundary drift")

    sg = acceptance.get("source_truth_guard") or {}
    if sg.get("inventory_candidate_review_status") != "draft" or sg.get("inventory_candidate_status_silently_upgraded") is not False or sg.get("taxonomy_backing_review_status") != "source_verified" or sg.get("skill_graph_evidence_status") != "confirmed" or sg.get("accepted_positive_scope") != ["event sequence", "change of states over time"] or sg.get("description_mastery_admitted") is not False or sg.get("reasoning_mastery_admitted") is not False or sg.get("generic_combined_speech_type_mastery_admitted") is not False:
        raise AssertionError("RU11 candidate-044 source guard drift")

    policy = acceptance.get("policy") or {}
    for key in ("exact_current_source_identity_required","source_verified_taxonomy_backing_required","confirmed_skill_graph_evidence_required","current_missing_subject_candidate_required","draft_candidate_status_must_be_preserved","content_adequacy_review_required","exact_school_meaning_collision_forbidden","reuse_first","component_specific_independent_evidence_required","school_duplicate_forbidden"):
        if policy.get(key) is not True:
            raise AssertionError(f"RU11 candidate-044 policy weakened: {key}")
    if policy.get("minimum_component_specific_independent_checks") != 2 or policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU11 candidate-044 component/namespace policy drift")
    for key in ("ege_taxonomy_id_promoted_unchanged","candidate_id_used_as_semantic_id","adjacent_candidates_admitted","description_mastery_admitted_by_this_authority","reasoning_mastery_admitted_by_this_authority","semantic_relation_mastery_admitted_by_this_authority","generic_task24_result_can_emit_exact_component_mastery","combined_speech_type_result_can_emit_exact_component_mastery","verb_count_or_marker_word_can_emit_exact_component_mastery","subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding","content_presence_alone_is_semantic_admission"):
        if policy.get(key) is not False:
            raise AssertionError(f"RU11 candidate-044 fail-closed policy drift: {key}")

    module = {str(r.get("module_id")): r for r in program.get("modules", []) if isinstance(r, dict)}.get("RU-PROG-11")
    if not isinstance(module, dict) or module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING" or set(module.get("candidate_refs") or []) != EXPECTED_CANDIDATES:
        raise AssertionError("RU11 module/candidate-set drift")

    objects = [r for r in inventory.get("objects", []) if isinstance(r, dict)]
    candidate = one([r for r in objects if r.get("source_system") == "semantic_candidate" and r.get("source_id") == CANDIDATE and r.get("authority_status") == "current"], "RU11 candidate-044")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE" or candidate.get("candidate_canonical_owner") != CANDIDATE or candidate.get("current_semantic_refs") != [TAXONOMY] or candidate.get("review_status") != "draft":
        raise AssertionError("RU11 candidate-044 inventory ownership/status drift")

    backing = one([r for r in objects if r.get("source_system") == "ege_skill_graph" and r.get("source_id") == TAXONOMY and r.get("authority_status") == "current" and r.get("candidate_canonical_owner") == CANDIDATE], "RU11 candidate-044 backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE" or normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 candidate-044 taxonomy backing drift")
    skill = one([r for r in graph.get("skills", []) if isinstance(r, dict) and r.get("skill_id") == TAXONOMY], "RU11 narration graph node")
    if skill.get("evidence_status") != "confirmed" or skill.get("parent_skill_id") != "speech_type_analysis" or skill.get("exam_task_numbers") != [24] or skill.get("name_ru") != CANONICAL_LABEL or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU11 narration graph/source meaning drift")

    if any(SEMANTIC in {str(ref) for ref in (r.get("current_semantic_refs") or [])} for r in objects if r.get("authority_status") == "current"):
        raise AssertionError("RU11 candidate-044 semantic collision")
    if any(r.get("source_system") == "school_canonical" and r.get("authority_status") == "current" and normalized(r.get("observed_meaning")) == normalized(candidate.get("observed_meaning")) for r in objects):
        raise AssertionError("RU11 candidate-044 exact school meaning exists; reuse required")

    if review.get("status") != "CENTRAL_BRAIN_RU11_NARRATION_IDENTIFICATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU11 narration review status drift")
    rd = review.get("review_decision") or {}
    if rd.get("content_exact_for_current_candidate_044_source_meaning") is not True or rd.get("source_candidate_inventory_status_preserved_as_draft") is not True or rd.get("semantic_admission_by_this_review") is not False or rd.get("object_level_admission_units_closed") != 0 or rd.get("object_level_requirements_closed") != 0 or rd.get("false_exact_mastery_admissions") != 0 or rd.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_WITH_DRAFT_CANDIDATE_GUARD":
        raise AssertionError("RU11 narration content review decision drift")

    broad_unit = one([r for r in broader.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == "ru-text-speech-type-reasoning-description-narration"], "RU11 broader speech-type unit")
    direct_broader = sum(1 for r in (broad_unit.get("independent_verification") or []) if isinstance(r, dict) and direct_narration_check(r))
    if direct_broader != 0:
        raise AssertionError(f"RU11 candidate-044 reuse-gap drift: expected 0 direct prompt checks, got {direct_broader}")
    reuse = acceptance.get("reuse_first_decision") or {}
    if reuse.get("broader_existing_unit_present") is not True or reuse.get("broader_existing_unit_reused_as_scope_and_explanation_evidence") is not True or reuse.get("broader_existing_unit_is_exact_candidate_044_mastery_evidence") is not False or reuse.get("broader_existing_unit_direct_narration_independent_checks") != 0 or reuse.get("minimum_component_specific_independent_checks_for_this_acceptance") != 2 or reuse.get("new_content_materialized_only_for_proven_component_verification_gap") is not True:
        raise AssertionError("RU11 candidate-044 reuse decision drift")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-11":
        raise AssertionError("RU11 narration content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU11 narration copyright guard drift")
    unit = one([r for r in content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == SEMANTIC], "RU11 narration learner unit")
    if unit.get("title_ru") != CANONICAL_LABEL:
        raise AssertionError("RU11 narration learner title drift")
    for key, minimum in (("decision_algorithm",6),("worked_examples",4),("misconceptions",4),("guided_practice",3),("independent_practice",3),("mixed_transfer_practice",2),("retention_items",2),("independent_verification",2)):
        if not isinstance(unit.get(key), list) or len(unit[key]) < minimum:
            raise AssertionError(f"RU11 narration learner section incomplete: {key}")
    checks = [r for r in (unit.get("independent_verification") or []) if isinstance(r, dict)]
    if {r.get("id") for r in checks} != EXPECTED_CHECK_IDS or len(checks) != 2 or any(r.get("type") != "constructed_response" for r in checks) or not all(direct_narration_check(r) for r in checks) or any((r.get("scoring") or {}).get("max_points") != 3 for r in checks):
        raise AssertionError("RU11 narration exact verification drift")
    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("source_candidate_review_status") != "draft" or peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True or peis.get("exact_mastery_requires_two_component_specific_narration_checks") is not True or peis.get("generic_task24_result_can_emit_exact_component_mastery") is not False or peis.get("combined_speech_type_unit_result_can_emit_exact_component_mastery") is not False or peis.get("description_or_reasoning_result_can_emit_this_mastery") is not False or peis.get("object_closure_implied") is not False:
        raise AssertionError("RU11 narration PEIS boundary drift")
    forbidden = " ".join((unit.get("tutor_grounding") or {}).get("forbidden") or []).lower()
    if ("verb" not in forbidden and "глаг" not in forbidden) or "task-24" not in forbidden:
        raise AssertionError("RU11 narration Tutor guard drift")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU11 narration acceptance must contain one decision")
    d = decisions[0]
    if d.get("candidate_ref") != CANDIDATE or d.get("source_taxonomy_id") != TAXONOMY or d.get("accepted_semantic_id") != SEMANTIC or d.get("canonical_label_ru") != CANONICAL_LABEL or d.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC" or d.get("source_evidence_status") != "confirmed" or d.get("source_candidate_inventory_review_status") != "draft" or d.get("excluded_adjacent_candidate_refs") != ADJACENT or d.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU11 narration acceptance crosswalk drift")
    summary = acceptance.get("summary") or {}
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1 or summary.get("adjacent_candidates_admitted") != 0 or summary.get("new_school_canonical_identities") != 0 or summary.get("object_level_admission_units_closed") != 0 or summary.get("object_level_requirements_closed") != 0 or summary.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU11 narration acceptance summary drift")

    digest = hashlib.sha256(json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU11_NARRATION_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"SOURCE_CANDIDATE_REVIEW_STATUS={candidate.get('review_status')}")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print(f"BROADER_EXISTING_DIRECT_NARRATION_CHECKS={direct_broader}")
    print(f"EXACT_COMPONENT_CHECKS={len(checks)}")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
