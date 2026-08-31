#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

ACCEPTANCE = HERE / "RU03-DEFINITION-CONTEXT-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
CONTENT_REVIEW = HERE / "RU03-DEFINITION-CONTEXT-CONTENT-ADEQUACY-REVIEW-v0.1.json"
BOUNDARY = HERE / "RU03-LEXIS-CANDIDATE-BOUNDARY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-DEFINITION-CONTEXT-MATCHING-WAVE-004-v0.1.json"

CANDIDATE = "candidate-010"
TAXONOMY = "definition_context_matching"
SEMANTIC = "ru-lexis-definition-context-matching"
ADJACENT = {"candidate-008", "candidate-009", "candidate-011", "candidate-012", "candidate-013", "candidate-014", "candidate-015"}


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    review = json.loads(CONTENT_REVIEW.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU03_DEFINITION_CONTEXT_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU03 definition-context acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU03 definition-context registry boundary drift")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_current_source_identity_required",
        "confirmed_skill_graph_evidence_required",
        "current_missing_subject_candidate_required",
        "exact_school_meaning_collision_forbidden",
        "original_exact_learner_content_required",
        "school_duplicate_forbidden",
        "component_specific_independent_evidence_required",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU03 definition-context policy weakened: {key}")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "generic_task2_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU03 definition-context fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU03 definition-context namespace drift")

    if boundary.get("status") != "CENTRAL_BRAIN_RU03_LEXIS_CANDIDATE_BOUNDARY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU03 boundary prerequisite drift")
    brow = one([r for r in boundary.get("candidate_review", []) if r.get("candidate_ref") == CANDIDATE], "RU03 boundary candidate-010")
    if brow.get("source_taxonomy_id") != TAXONOMY or brow.get("skill_graph_evidence_status") != "confirmed":
        raise AssertionError("RU03 candidate-010 antecedent source boundary drift")
    if brow.get("disposition") != "REVIEWED_NOT_ADMITTED" or brow.get("content_boundary") != "NO_DEDICATED_EXACT_LEARNER_UNIT":
        raise AssertionError("RU03 candidate-010 antecedent gap truth drift")

    if review.get("status") != "CENTRAL_BRAIN_RU03_DEFINITION_CONTEXT_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU03 definition-context content review status drift")
    source = review.get("source_identity") or {}
    if source.get("candidate_ref") != CANDIDATE or source.get("source_taxonomy_id") != TAXONOMY or source.get("skill_graph_evidence_status") != "confirmed":
        raise AssertionError("RU03 definition-context content-review source drift")
    rd = review.get("review_decision") or {}
    if rd.get("content_exact_for_candidate_010") is not True or rd.get("content_duplicate_of_existing_ru03_unit") is not False:
        raise AssertionError("RU03 definition-context content adequacy not proven")
    if rd.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("RU03 definition-context content review self-admitted semantic")
    if rd.get("object_level_admission_units_closed") != 0 or rd.get("object_level_requirements_closed") != 0 or rd.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU03 definition-context content review falsely closed mastery")

    objects = [r for r in inventory.get("objects", []) if isinstance(r, dict)]
    candidate = one([
        r for r in objects
        if r.get("source_system") == "semantic_candidate"
        and r.get("source_id") == CANDIDATE
        and r.get("authority_status") == "current"
    ], "RU03 candidate-010 current inventory")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE" or candidate.get("candidate_canonical_owner") != CANDIDATE:
        raise AssertionError("RU03 candidate-010 inventory ownership/classification drift")
    if candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise AssertionError("RU03 candidate-010 taxonomy ref drift")

    backing = one([
        r for r in objects
        if r.get("source_system") == "ege_skill_graph"
        and r.get("source_id") == TAXONOMY
        and r.get("authority_status") == "current"
        and r.get("candidate_canonical_owner") == CANDIDATE
    ], "RU03 candidate-010 taxonomy backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU03 candidate-010 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU03 candidate-010 inventory meaning mismatch")

    skill = one([r for r in graph.get("skills", []) if isinstance(r, dict) and r.get("skill_id") == TAXONOMY], "RU03 candidate-010 graph node")
    if skill.get("evidence_status") != "confirmed" or skill.get("parent_skill_id") != "lexical_norms_and_semantics" or skill.get("exam_task_numbers") != [2]:
        raise AssertionError("RU03 candidate-010 confirmed Task-2 graph boundary drift")
    if skill.get("name_ru") != candidate.get("observed_label") or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU03 candidate-010 graph label/meaning drift")

    if any(SEMANTIC in {str(ref) for ref in (r.get("current_semantic_refs") or [])} for r in objects if r.get("authority_status") == "current"):
        raise AssertionError("RU03 definition-context semantic id collides with current inventory")
    if any(
        r.get("source_system") == "school_canonical"
        and r.get("authority_status") == "current"
        and normalized(r.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
        for r in objects
    ):
        raise AssertionError("RU03 candidate-010 exact school meaning already exists; reuse required")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-03":
        raise AssertionError("RU03 definition-context content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU03 definition-context provenance boundary weakened")
    unit = one([r for r in content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == SEMANTIC], "RU03 definition-context learner unit")
    if unit.get("candidate_ref") != CANDIDATE or unit.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("RU03 definition-context content crosswalk drift")
    serialized = json.dumps(unit, ensure_ascii=False).lower()
    for token in ("толкован", "контекст", "соответ"):
        if token not in serialized:
            raise AssertionError(f"RU03 definition-context content missing target token: {token}")
    for key, minimum in (
        ("decision_algorithm", 5),
        ("worked_examples", 3),
        ("misconceptions", 2),
        ("guided_practice", 2),
        ("independent_practice", 3),
        ("mixed_transfer_practice", 1),
        ("retention_items", 2),
        ("independent_verification", 2),
    ):
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"RU03 definition-context learner section incomplete: {key}")
    boundaries = " ".join((unit.get("canonical_explanation") or {}).get("boundaries") or [])
    if "dictionary_sense_selection" not in boundaries or "lexical_meaning_in_context" not in boundaries:
        raise AssertionError("RU03 definition-context adjacent semantic exclusions missing")
    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError("RU03 definition-context PEIS boundary weakened")
    if peis.get("generic_task_result_can_emit_exact_mastery") is not False or peis.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU03 definition-context exact-mastery boundary weakened")
    tutor = unit.get("tutor_grounding") or {}
    if not tutor.get("allowed") or not tutor.get("forbidden") or not tutor.get("source_refs"):
        raise AssertionError("RU03 definition-context Tutor grounding incomplete")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU03 definition-context acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("candidate_ref") != CANDIDATE or decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("RU03 definition-context acceptance crosswalk drift")
    if decision.get("canonical_label_ru") != candidate.get("observed_label"):
        raise AssertionError("RU03 definition-context acceptance label drift")
    if decision.get("entity_type") != "DEFINITION_CONTEXT_MATCHING_SKILL" or decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU03 definition-context acceptance type/status drift")
    if decision.get("source_evidence_status") != "confirmed" or decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU03 definition-context source/object boundary drift")
    if set(decision.get("excluded_adjacent_candidate_refs") or []) != ADJACENT:
        raise AssertionError("RU03 definition-context adjacent exclusions drift")

    summary = acceptance.get("summary") or {}
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1:
        raise AssertionError("RU03 definition-context accepted semantic count drift")
    if summary.get("adjacent_candidates_admitted") != 0 or summary.get("new_school_canonical_identities") != 0:
        raise AssertionError("RU03 definition-context acceptance leaked adjacent/parallel identities")
    if summary.get("object_level_admission_units_closed") != 0 or summary.get("object_level_requirements_closed") != 0 or summary.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU03 definition-context acceptance falsely closes object mastery")

    digest = hashlib.sha256(json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU03_DEFINITION_CONTEXT_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
