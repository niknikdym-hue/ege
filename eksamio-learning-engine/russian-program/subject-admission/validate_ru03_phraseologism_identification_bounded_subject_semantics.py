#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from validate_ru03_phraseologism_identification_content_adequacy import main as validate_content_adequacy

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent

ACCEPTANCE = HERE / "RU03-PHRASEOLOGISM-IDENTIFICATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
CONTENT_REVIEW = HERE / "RU03-PHRASEOLOGISM-IDENTIFICATION-CONTENT-ADEQUACY-REVIEW-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-PHRASEOLOGISM-IDENTIFICATION-WAVE-007-v0.1.json"

CANDIDATE = "candidate-014"
TAXONOMY = "phraseologism_identification"
SEMANTIC = "ru-lexis-phraseologism-fragment-identification"
LABEL = "Поиск фразеологизма в заданном фрагменте текста"
ADJACENT = {
    "candidate-008",
    "candidate-009",
    "candidate-010",
    "candidate-011",
    "candidate-012",
    "candidate-013",
    "candidate-015",
}


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    if validate_content_adequacy() != 0:
        raise AssertionError("RU03 phraseologism prerequisite content/source validation failed")

    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    review = json.loads(CONTENT_REVIEW.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU03_PHRASEOLOGISM_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("candidate-014 acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("candidate-014 authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("candidate-014 school registry mutation forbidden")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("candidate-014 parallel registry forbidden")

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
            raise AssertionError(f"candidate-014 policy weakened: {key}")
    for key in (
        "ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "generic_task25_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"candidate-014 fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("candidate-014 namespace drift")

    source = review.get("source_identity") or {}
    if (
        source.get("candidate_ref") != CANDIDATE
        or source.get("source_taxonomy_id") != TAXONOMY
        or source.get("label_ru") != LABEL
        or source.get("skill_graph_evidence_status") != "confirmed"
        or source.get("inventory_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
    ):
        raise AssertionError("candidate-014 source identity drift")
    rd = review.get("review_decision") or {}
    if rd.get("content_exact_for_candidate_014") is not True:
        raise AssertionError("candidate-014 exact learner content not proven")
    if rd.get("content_duplicate_of_existing_ru03_unit") is not False:
        raise AssertionError("candidate-014 content duplicate boundary drift")
    if rd.get("exact_school_meaning_collision_observed") is not False:
        raise AssertionError("candidate-014 reuse-first collision guard drift")
    if rd.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("candidate-014 content review must remain non-admitting")
    if rd.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("candidate-014 prerequisite state drift")

    unit = one(
        [r for r in content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == SEMANTIC],
        "candidate-014 learner unit",
    )
    if unit.get("candidate_ref") != CANDIDATE or unit.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("candidate-014 learner crosswalk drift")
    peis = unit.get("peis_evidence") or {}
    if peis.get("generic_task_result_can_emit_exact_mastery") is not False:
        raise AssertionError("candidate-014 generic Task-25 mastery leakage")
    if peis.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("candidate-014 object binding drift")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("candidate-014 acceptance must contain exactly one decision")
    decision = decisions[0]
    if (
        decision.get("candidate_ref") != CANDIDATE
        or decision.get("source_taxonomy_id") != TAXONOMY
        or decision.get("accepted_semantic_id") != SEMANTIC
        or decision.get("canonical_label_ru") != LABEL
    ):
        raise AssertionError("candidate-014 acceptance crosswalk drift")
    if decision.get("entity_type") != "PHRASEOLOGISM_FRAGMENT_IDENTIFICATION_SKILL":
        raise AssertionError("candidate-014 entity type drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("candidate-014 bounded acceptance status drift")
    if decision.get("source_evidence_status") != "confirmed":
        raise AssertionError("candidate-014 source evidence drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("candidate-014 acceptance cannot self-bind objects")
    if set(decision.get("excluded_adjacent_candidate_refs") or []) != ADJACENT:
        raise AssertionError("candidate-014 adjacent exclusions drift")
    boundary = str(decision.get("boundary_guard") or "").lower()
    for token in ("exact word boundaries", "supplied fragment", "contextual synonym", "task-25"):
        if token not in boundary:
            raise AssertionError(f"candidate-014 acceptance boundary missing token: {token}")

    crosswalk = acceptance.get("crosswalk_policy") or {}
    if crosswalk.get("candidate_ref_preserved_as_legacy_ref") is not True:
        raise AssertionError("candidate-014 candidate ref must remain preserved")
    if crosswalk.get("source_taxonomy_ref_preserved") is not True:
        raise AssertionError("candidate-014 taxonomy ref must remain preserved")
    if crosswalk.get("source_taxonomy_id_replaced") is not False:
        raise AssertionError("candidate-014 taxonomy id replacement forbidden")
    if crosswalk.get("exam_task_number_is_semantic_identity") is not False:
        raise AssertionError("candidate-014 task number cannot be semantic identity")
    if crosswalk.get("generic_task25_result_can_emit_exact_component_mastery") is not False:
        raise AssertionError("candidate-014 crosswalk mastery leakage")

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
            raise AssertionError(f"candidate-014 summary drift: {key}")

    digest = hashlib.sha256(
        json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU03_PHRASEOLOGISM_IDENTIFICATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
