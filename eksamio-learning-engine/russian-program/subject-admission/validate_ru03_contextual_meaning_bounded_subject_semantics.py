#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
BOUNDARY = HERE / "RU03-LEXIS-CANDIDATE-BOUNDARY-REVIEW-v0.1.json"
REVIEW = HERE / "RU03-CONTEXTUAL-MEANING-CONTENT-ADEQUACY-REVIEW-v0.1.json"
ACCEPTANCE = HERE / "RU03-CONTEXTUAL-MEANING-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-CONTEXTUAL-MEANING-DETERMINATION-WAVE-009-v0.1.json"

CANDIDATE = "candidate-008"
TAXONOMY = "lexical_meaning_in_context"
SEMANTIC = "ru-lexis-contextual-meaning-determination"
LABEL = "Определение значения слова в данном контексте"
ADJACENT = {
    "candidate-009",
    "candidate-010",
    "candidate-011",
    "candidate-012",
    "candidate-013",
    "candidate-014",
    "candidate-015",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    boundary = load(BOUNDARY)
    review = load(REVIEW)
    acceptance = load(ACCEPTANCE)
    content = load(CONTENT)

    if boundary.get("status") != "CENTRAL_BRAIN_RU03_LEXIS_CANDIDATE_BOUNDARY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU03 candidate boundary review status drift")
    candidate = one(
        [row for row in boundary.get("candidate_review", []) if isinstance(row, dict) and row.get("candidate_ref") == CANDIDATE],
        "candidate-008 boundary row",
    )
    if candidate.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("candidate-008 taxonomy drift")
    if candidate.get("skill_graph_evidence_status") != "confirmed":
        raise AssertionError("candidate-008 confirmed source evidence missing")
    if candidate.get("learner_content_ref") != "ru-lexis-contextual-meaning-polysemy":
        raise AssertionError("candidate-008 broader reuse reference drift")
    if candidate.get("content_boundary") != "BROADER_THAN_EXACT_CANDIDATE_COMBINES_CONTEXTUAL_MEANING_AND_POLYSEMY":
        raise AssertionError("candidate-008 broader-content boundary drift")
    if candidate.get("disposition") != "REVIEWED_NOT_ADMITTED":
        raise AssertionError("candidate-008 antecedent review unexpectedly admitted semantic")

    if review.get("status") != "CENTRAL_BRAIN_RU03_CONTEXTUAL_MEANING_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("candidate-008 content review status drift")
    source_identity = review.get("source_identity") or {}
    if (
        source_identity.get("candidate_ref") != CANDIDATE
        or source_identity.get("source_taxonomy_id") != TAXONOMY
        or source_identity.get("label_ru") != LABEL
        or source_identity.get("skill_graph_evidence_status") != "confirmed"
        or source_identity.get("inventory_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
    ):
        raise AssertionError("candidate-008 source identity review drift")
    reuse = review.get("reuse_first_result") or {}
    if reuse.get("existing_content_exact_for_candidate_008") is not False:
        raise AssertionError("candidate-008 broader existing content falsely treated as exact")
    if reuse.get("silent_reuse_as_exact_mastery_forbidden") is not True:
        raise AssertionError("candidate-008 silent reuse guard weakened")
    rd = review.get("review_decision") or {}
    if rd.get("new_content_exact_for_candidate_008") is not True:
        raise AssertionError("candidate-008 exact new learner content not proven")
    if rd.get("new_content_duplicate_of_existing_ru03_unit") is not False:
        raise AssertionError("candidate-008 new content duplicate boundary drift")
    if rd.get("exact_school_meaning_collision_observed") is not False:
        raise AssertionError("candidate-008 school collision detected")
    if rd.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("candidate-008 content review must remain non-admitting")
    if rd.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("candidate-008 content-review next state drift")
    for key in ("object_level_admission_units_closed", "object_level_requirements_closed", "false_exact_mastery_admissions"):
        if rd.get(key) != 0:
            raise AssertionError(f"candidate-008 content review false closure: {key}")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("subject") != "russian" or content.get("module_id") != "RU-PROG-03":
        raise AssertionError("candidate-008 learner bundle identity drift")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("commercial_textbook_bytes") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("candidate-008 copyright guard drift")
    unit = one(
        [row for row in content.get("units", []) if isinstance(row, dict) and row.get("proposed_semantic_id") == SEMANTIC],
        "candidate-008 learner unit",
    )
    if unit.get("candidate_ref") != CANDIDATE or unit.get("source_taxonomy_id") != TAXONOMY or unit.get("title_ru") != LABEL:
        raise AssertionError("candidate-008 learner crosswalk drift")
    for key, minimum in (
        ("decision_algorithm", 6),
        ("worked_examples", 4),
        ("misconceptions", 4),
        ("guided_practice", 2),
        ("independent_practice", 4),
        ("mixed_transfer_practice", 2),
        ("retention_items", 2),
        ("independent_verification", 3),
    ):
        rows = unit.get(key)
        if not isinstance(rows, list) or len(rows) < minimum:
            raise AssertionError(f"candidate-008 learner coverage too small: {key}")
    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("candidate-008 content layer self-admitted semantic")
    if peis.get("independent_verification_required") is not True or peis.get("component_specific_independent_evidence_required") is not True:
        raise AssertionError("candidate-008 independent evidence guard missing")
    if peis.get("generic_task_result_can_emit_exact_mastery") is not False:
        raise AssertionError("candidate-008 generic Task-2 mastery leakage")
    if peis.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("candidate-008 object binding drift")

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU03_CONTEXTUAL_MEANING_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("candidate-008 acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("candidate-008 authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("candidate-008 registry mutation/duplication forbidden")
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
            raise AssertionError(f"candidate-008 policy weakened: {key}")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "generic_task2_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
        "broader_existing_content_can_emit_exact_candidate_mastery",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"candidate-008 fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("candidate-008 namespace drift")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("candidate-008 acceptance must contain exactly one decision")
    decision = decisions[0]
    if (
        decision.get("candidate_ref") != CANDIDATE
        or decision.get("source_taxonomy_id") != TAXONOMY
        or decision.get("accepted_semantic_id") != SEMANTIC
        or decision.get("canonical_label_ru") != LABEL
        or decision.get("entity_type") != "CONTEXTUAL_LEXICAL_MEANING_DETERMINATION_SKILL"
        or decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC"
        or decision.get("source_evidence_status") != "confirmed"
        or decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    ):
        raise AssertionError("candidate-008 acceptance decision drift")
    if set(decision.get("excluded_adjacent_candidate_refs") or []) != ADJACENT:
        raise AssertionError("candidate-008 adjacent exclusions drift")
    boundary_guard = str(decision.get("boundary_guard") or "").lower()
    for token in ("active lexical meaning", "supplied context", "dictionary-sense", "polysemy", "contextual synonym", "task-2"):
        if token not in boundary_guard:
            raise AssertionError(f"candidate-008 boundary missing token: {token}")

    summary = acceptance.get("summary") or {}
    expected = {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "source_backed_candidates_consumed": 1,
        "new_original_production_content_units_used": 1,
        "adjacent_candidates_admitted": 0,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise AssertionError(f"candidate-008 summary drift: {key}")

    digest = hashlib.sha256(
        json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU03_CONTEXTUAL_MEANING_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("REUSE_FIRST_EXISTING_CONTENT=BROADER_NOT_EXACT")
    print("SOURCE_EVIDENCE=CONFIRMED")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
