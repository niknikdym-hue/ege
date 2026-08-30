#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

ACCEPTANCE = HERE / "RU03-PARONYM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
BOUNDARY = HERE / "RU03-LEXIS-CANDIDATE-BOUNDARY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-LEXIS-PARONYMS-PHRASEOLOGY-WAVE-002-v0.1.json"

CANDIDATE = "candidate-011"
TAXONOMY = "paronym_context_choice"
SEMANTIC = "ru-lexis-paronym-collocation-choice"
ADJACENT = {"candidate-008", "candidate-009", "candidate-010", "candidate-012", "candidate-013", "candidate-014", "candidate-015"}


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], message: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{message}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU03_PARONYM_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU03 paronym acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU03 paronym acceptance mutated/duplicated registry")

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
            raise AssertionError(f"RU03 paronym acceptance policy weakened: {key}")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "generic_task5_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU03 paronym fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU03 paronym namespace drift")

    if boundary.get("status") != "CENTRAL_BRAIN_RU03_LEXIS_CANDIDATE_BOUNDARY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU03 candidate-boundary prerequisite drift")
    bsummary = boundary.get("summary") or {}
    if bsummary.get("semantic_admissions") != 0 or bsummary.get("object_level_admission_units_closed") != 0 or bsummary.get("object_level_requirements_closed") != 0:
        raise AssertionError("RU03 boundary review self-admitted semantics or objects")
    ready = boundary.get("admission_ready") or {}
    if ready.get("candidate_ref") != CANDIDATE or ready.get("source_taxonomy_id") != TAXONOMY or ready.get("proposed_semantic_id") != SEMANTIC:
        raise AssertionError("RU03 admission-ready prerequisite drift")
    if ready.get("status") != "READY_FOR_SEPARATE_BOUNDED_SEMANTIC_ACCEPTANCE_NOT_ACCEPTED_BY_THIS_REVIEW":
        raise AssertionError("RU03 boundary did not leave candidate-011 ready for separate acceptance")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    candidate = one([
        row for row in objects
        if row.get("source_system") == "semantic_candidate"
        and row.get("source_id") == CANDIDATE
        and row.get("authority_status") == "current"
    ], "RU03 candidate-011 current inventory")
    if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE" or candidate.get("candidate_canonical_owner") != CANDIDATE:
        raise AssertionError("RU03 candidate-011 inventory ownership/classification drift")
    if candidate.get("current_semantic_refs") != [TAXONOMY]:
        raise AssertionError("RU03 candidate-011 taxonomy ref drift")
    if candidate.get("review_status") not in {"draft", "needs_review"}:
        raise AssertionError("RU03 candidate-011 inventory review status unexpectedly promoted")

    backing = one([
        row for row in objects
        if row.get("source_system") == "ege_skill_graph"
        and row.get("source_id") == TAXONOMY
        and row.get("authority_status") == "current"
        and row.get("candidate_canonical_owner") == CANDIDATE
    ], "RU03 candidate-011 taxonomy backing")
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU03 candidate-011 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU03 candidate-011 inventory meaning mismatch")

    skill = one([row for row in graph.get("skills", []) if isinstance(row, dict) and row.get("skill_id") == TAXONOMY], "RU03 candidate-011 graph node")
    if skill.get("evidence_status") != "confirmed" or skill.get("parent_skill_id") != "lexical_norms_and_semantics" or skill.get("exam_task_numbers") != [5]:
        raise AssertionError("RU03 candidate-011 confirmed Task-5 graph boundary drift")
    if skill.get("name_ru") != candidate.get("observed_label") or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU03 candidate-011 graph label/meaning drift")

    collisions = [
        row for row in objects
        if row.get("authority_status") == "current"
        and SEMANTIC in {str(ref) for ref in (row.get("current_semantic_refs") or [])}
    ]
    if collisions:
        raise AssertionError("RU03 paronym semantic id collides with current inventory")
    exact_school_meaning = [
        row for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and normalized(row.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
    ]
    if exact_school_meaning:
        raise AssertionError("RU03 candidate-011 exact school meaning already exists; reuse required")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-03":
        raise AssertionError("RU03 learner content status/module drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU03 learner-content provenance boundary weakened")
    units = [row for row in content.get("units", []) if isinstance(row, dict)]
    unit = one([row for row in units if row.get("proposed_semantic_id") == SEMANTIC], "RU03 paronym learner unit")
    serialized = json.dumps(unit, ensure_ascii=False).lower()
    if "пароним" not in serialized or "значен" not in serialized or "сочетаем" not in serialized:
        raise AssertionError("RU03 paronym exact meaning/collocation boundary missing")
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
            raise AssertionError(f"RU03 paronym learner section incomplete: {key}")
    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError("RU03 paronym PEIS evidence boundary weakened")
    tutor = unit.get("tutor_grounding") or {}
    if not tutor.get("allowed") or not tutor.get("forbidden"):
        raise AssertionError("RU03 paronym Tutor grounding missing")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("RU03 paronym acceptance must contain exactly one decision")
    decision = decisions[0]
    if decision.get("candidate_ref") != CANDIDATE or decision.get("source_taxonomy_id") != TAXONOMY or decision.get("accepted_semantic_id") != SEMANTIC:
        raise AssertionError("RU03 paronym acceptance crosswalk drift")
    if decision.get("canonical_label_ru") != candidate.get("observed_label"):
        raise AssertionError("RU03 paronym acceptance label drift")
    if decision.get("entity_type") != "PARONYM_CONTEXT_CHOICE_SKILL" or decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU03 paronym bounded acceptance type/status drift")
    if decision.get("source_evidence_status") != "confirmed" or decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("RU03 paronym source/object boundary drift")
    if set(decision.get("excluded_adjacent_candidate_refs") or []) != ADJACENT:
        raise AssertionError("RU03 paronym adjacent exclusions drift")

    summary = acceptance.get("summary") or {}
    if summary.get("accepted_bounded_subject_semantics") != 1 or summary.get("accepted_ru_subject_semantics") != 1:
        raise AssertionError("RU03 paronym accepted semantic count drift")
    if summary.get("adjacent_candidates_admitted") != 0 or summary.get("new_school_canonical_identities") != 0:
        raise AssertionError("RU03 paronym acceptance leaked adjacent/parallel identities")
    if summary.get("object_level_admission_units_closed") != 0 or summary.get("object_level_requirements_closed") != 0 or summary.get("false_exact_mastery_admissions") != 0:
        raise AssertionError("RU03 paronym acceptance falsely closes object mastery")

    digest = hashlib.sha256(json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    print("RU03_PARONYM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_SEMANTIC=ru-lexis-paronym-collocation-choice")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
