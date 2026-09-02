#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ACCEPTANCE = HERE / "RU03-CONTEXTUAL-SYNONYM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
SOURCE_RESOLVER = HERE / "build_ru03_contextual_synonym_source_identity_resolution.py"
CONTENT_REVIEWER = HERE / "build_ru03_contextual_synonym_content_adequacy_review.py"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-CONTEXTUAL-SYNONYM-SELECTION-WAVE-008-v0.1.json"

CANDIDATE = "candidate-015"
TAXONOMY = "contextual_synonym_selection"
SEMANTIC = "ru-lexis-contextual-synonym-text-fit"
LABEL = "Подбор контекстного синонима к слову исходного текста"
ADJACENT = {
    "candidate-008",
    "candidate-009",
    "candidate-010",
    "candidate-011",
    "candidate-012",
    "candidate-013",
    "candidate-014",
}


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    source = runpy.run_path(str(SOURCE_RESOLVER))["build_resolution"]()
    review = runpy.run_path(str(CONTENT_REVIEWER))["build_review"]()
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if source.get("status") != "CENTRAL_BRAIN_RU03_CONTEXTUAL_SYNONYM_CURRENT_2026_SOURCE_IDENTITY_RESOLVED_NO_ADMISSION":
        raise AssertionError("candidate-015 source resolution prerequisite drift")
    resolution = source.get("resolution") or {}
    official = source.get("current_official_source_resolution") or {}
    if resolution.get("source_identity_status") != "EXACT_CURRENT_2026_OFFICIAL_SOURCE_CONFIRMED":
        raise AssertionError("candidate-015 exact current source identity not proven")
    if official.get("authority") != "FGBNU FIPI" or official.get("source_identity_evidence_status") != "confirmed":
        raise AssertionError("candidate-015 current official authority drift")
    if int((source.get("summary") or {}).get("semantic_admissions", -1)) != 0:
        raise AssertionError("candidate-015 source-resolution layer self-admitted semantic")

    if review.get("status") != "CENTRAL_BRAIN_RU03_CONTEXTUAL_SYNONYM_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("candidate-015 content-adequacy prerequisite drift")
    rd = review.get("review_decision") or {}
    if rd.get("content_exact_for_candidate_015") is not True:
        raise AssertionError("candidate-015 exact learner content not proven")
    if rd.get("content_duplicate_of_existing_ru03_unit") is not False:
        raise AssertionError("candidate-015 reuse-first duplicate boundary drift")
    if rd.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("candidate-015 content review must remain non-admitting")
    if rd.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("candidate-015 prerequisite state drift")

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU03_CONTEXTUAL_SYNONYM_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("candidate-015 acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("candidate-015 authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("candidate-015 school registry mutation forbidden")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("candidate-015 parallel registry forbidden")

    policy = acceptance.get("policy") or {}
    for key in (
        "exact_current_source_identity_required",
        "current_official_2026_fipi_authority_required",
        "current_missing_subject_candidate_required",
        "exact_school_meaning_collision_forbidden",
        "original_exact_learner_content_required",
        "school_duplicate_forbidden",
        "component_specific_independent_evidence_required",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"candidate-015 policy weakened: {key}")
    for key in (
        "legacy_ege_taxonomy_id_promoted_unchanged",
        "candidate_id_used_as_semantic_id",
        "adjacent_candidates_admitted",
        "generic_task25_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "content_presence_alone_is_semantic_admission",
        "legacy_graph_or_inventory_needs_review_mutated",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"candidate-015 fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("candidate-015 namespace drift")

    unit = one(
        [row for row in content.get("units", []) if isinstance(row, dict) and row.get("proposed_semantic_id") == SEMANTIC],
        "candidate-015 learner unit",
    )
    if unit.get("candidate_ref") != CANDIDATE or unit.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("candidate-015 learner crosswalk drift")
    if unit.get("title_ru") != LABEL:
        raise AssertionError("candidate-015 learner label drift")
    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("candidate-015 content layer self-admitted semantic")
    if peis.get("generic_task_result_can_emit_exact_mastery") is not False:
        raise AssertionError("candidate-015 generic Task-25 mastery leakage")
    if peis.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("candidate-015 object binding drift")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 1:
        raise AssertionError("candidate-015 acceptance must contain exactly one decision")
    decision = decisions[0]
    if (
        decision.get("candidate_ref") != CANDIDATE
        or decision.get("source_taxonomy_id") != TAXONOMY
        or decision.get("accepted_semantic_id") != SEMANTIC
        or decision.get("canonical_label_ru") != LABEL
    ):
        raise AssertionError("candidate-015 acceptance crosswalk drift")
    if decision.get("entity_type") != "CONTEXTUAL_SYNONYM_TEXT_FIT_SKILL":
        raise AssertionError("candidate-015 entity type drift")
    if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("candidate-015 bounded acceptance status drift")
    if decision.get("source_evidence_status") != "confirmed_current_2026_official_fipi":
        raise AssertionError("candidate-015 source evidence drift")
    if decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise AssertionError("candidate-015 acceptance cannot self-bind objects")
    if set(decision.get("excluded_adjacent_candidate_refs") or []) != ADJACENT:
        raise AssertionError("candidate-015 adjacent exclusions drift")
    boundary = str(decision.get("boundary_guard") or "").lower()
    for token in ("supplied fragment", "contextual meaning", "grammatical fit", "stylistic fit", "phraseologism", "task-25"):
        if token not in boundary:
            raise AssertionError(f"candidate-015 acceptance boundary missing token: {token}")

    crosswalk = acceptance.get("crosswalk_policy") or {}
    if crosswalk.get("candidate_ref_preserved_as_legacy_ref") is not True:
        raise AssertionError("candidate-015 candidate ref must remain preserved")
    if crosswalk.get("source_taxonomy_ref_preserved") is not True:
        raise AssertionError("candidate-015 taxonomy ref must remain preserved")
    if crosswalk.get("source_taxonomy_id_replaced") is not False:
        raise AssertionError("candidate-015 taxonomy id replacement forbidden")
    if crosswalk.get("legacy_needs_review_records_preserved_as_audit_history") is not True:
        raise AssertionError("candidate-015 legacy audit history must remain preserved")
    if crosswalk.get("current_2026_source_resolution_overlays_legacy_review_state") is not True:
        raise AssertionError("candidate-015 overlay relation drift")
    if crosswalk.get("exam_task_number_is_semantic_identity") is not False:
        raise AssertionError("candidate-015 task number cannot be semantic identity")
    if crosswalk.get("generic_task25_result_can_emit_exact_component_mastery") is not False:
        raise AssertionError("candidate-015 crosswalk mastery leakage")

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
            raise AssertionError(f"candidate-015 summary drift: {key}")

    digest = hashlib.sha256(
        json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU03_CONTEXTUAL_SYNONYM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("SOURCE_IDENTITY=CURRENT_2026_OFFICIAL_FIPI_CONFIRMED")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
