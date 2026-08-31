#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

REVIEW = HERE / "RU03-LEXIS-CANDIDATE-BOUNDARY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-LEXIS-PARONYMS-PHRASEOLOGY-WAVE-002-v0.1.json"

EXPECTED = {
    "candidate-008": ("lexical_meaning_in_context", "confirmed"),
    "candidate-009": ("dictionary_sense_selection", "confirmed"),
    "candidate-010": ("definition_context_matching", "confirmed"),
    "candidate-011": ("paronym_context_choice", "confirmed"),
    "candidate-012": ("lexical_redundancy", "confirmed"),
    "candidate-013": ("lexical_collocation_correction", "confirmed"),
    "candidate-014": ("phraseologism_identification", "confirmed"),
    "candidate-015": ("contextual_synonym_selection", "needs_review"),
}
READY_CANDIDATE = "candidate-011"
READY_TAXONOMY = "paronym_context_choice"
READY_SEMANTIC = "ru-lexis-paronym-collocation-choice"


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], message: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{message}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if review.get("status") != "CENTRAL_BRAIN_RU03_LEXIS_CANDIDATE_BOUNDARY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU03 review status drift")
    if review.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("RU03 review mutated school registry")
    if review.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU03 review created a parallel registry")

    policy = review.get("policy") or {}
    required_true = (
        "exact_current_source_identity_required",
        "confirmed_skill_graph_evidence_required_for_admission_ready",
        "exact_school_meaning_collision_forbidden",
        "original_exact_learner_content_required",
        "component_specific_independent_evidence_required",
    )
    if any(policy.get(key) is not True for key in required_true):
        raise AssertionError("RU03 fail-closed review policy weakened")
    required_false = (
        "content_presence_alone_is_semantic_admission",
        "review_status_is_semantic_admission",
        "generic_exam_task_result_can_emit_exact_component_mastery",
        "object_counts_reduced",
    )
    if any(policy.get(key) is not False for key in required_false):
        raise AssertionError("RU03 no-admission policy weakened")

    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]
    skills = [row for row in graph.get("skills", []) if isinstance(row, dict)]
    review_rows = {
        str(row.get("candidate_ref")): row
        for row in review.get("candidate_review", [])
        if isinstance(row, dict)
    }
    if set(review_rows) != set(EXPECTED):
        raise AssertionError("RU03 candidate review set drift")

    candidate_rows: dict[str, dict[str, Any]] = {}
    graph_rows: dict[str, dict[str, Any]] = {}
    for candidate_ref, (taxonomy, expected_evidence) in EXPECTED.items():
        candidate = one([
            row for row in objects
            if row.get("source_system") == "semantic_candidate"
            and row.get("source_id") == candidate_ref
            and row.get("authority_status") == "current"
        ], f"{candidate_ref} current inventory")
        if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise AssertionError(f"{candidate_ref} is no longer a missing subject semantic candidate")
        if candidate.get("candidate_canonical_owner") != candidate_ref:
            raise AssertionError(f"{candidate_ref} canonical owner drift")
        if candidate.get("current_semantic_refs") != [taxonomy]:
            raise AssertionError(f"{candidate_ref} taxonomy ref drift")

        backing = one([
            row for row in objects
            if row.get("source_system") == "ege_skill_graph"
            and row.get("source_id") == taxonomy
            and row.get("authority_status") == "current"
            and row.get("candidate_canonical_owner") == candidate_ref
        ], f"{candidate_ref} taxonomy backing")
        if backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
            raise AssertionError(f"{candidate_ref} backing classification drift")
        expected_inventory_review = "source_verified" if expected_evidence == "confirmed" else "needs_review"
        if backing.get("review_status") != expected_inventory_review:
            raise AssertionError(f"{candidate_ref} inventory backing review status drift")
        if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
            raise AssertionError(f"{candidate_ref} inventory meaning mismatch")

        skill = one([row for row in skills if row.get("skill_id") == taxonomy], f"{candidate_ref} skill graph")
        if skill.get("parent_skill_id") != "lexical_norms_and_semantics":
            raise AssertionError(f"{candidate_ref} parent skill drift")
        if skill.get("evidence_status") != expected_evidence:
            raise AssertionError(f"{candidate_ref} graph evidence drift")
        if normalized(skill.get("description")) != normalized(candidate.get("observed_meaning")):
            raise AssertionError(f"{candidate_ref} graph meaning drift")
        if skill.get("name_ru") != candidate.get("observed_label"):
            raise AssertionError(f"{candidate_ref} graph label drift")

        row = review_rows[candidate_ref]
        if row.get("source_taxonomy_id") != taxonomy or row.get("skill_graph_evidence_status") != expected_evidence:
            raise AssertionError(f"{candidate_ref} review source/evidence drift")
        candidate_rows[candidate_ref] = candidate
        graph_rows[candidate_ref] = skill

    ready_candidate = candidate_rows[READY_CANDIDATE]
    if graph_rows[READY_CANDIDATE].get("exam_task_numbers") != [5]:
        raise AssertionError("candidate-011 Task-5 boundary drift")

    exact_school_meaning = [
        row for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and normalized(row.get("observed_meaning")) == normalized(ready_candidate.get("observed_meaning"))
    ]
    if exact_school_meaning:
        raise AssertionError("candidate-011 exact school meaning already exists; canonical reuse required")

    semantic_id_collisions = [
        row for row in objects
        if row.get("authority_status") == "current"
        and READY_SEMANTIC in {str(ref) for ref in (row.get("current_semantic_refs") or [])}
    ]
    if semantic_id_collisions:
        raise AssertionError("candidate-011 proposed ru-* id already collides in current inventory")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-03":
        raise AssertionError("RU03 learner content status/module drift")
    copyright_guard = content.get("copyright_guard") or {}
    if copyright_guard.get("source_passages_copied") != 0:
        raise AssertionError("RU03 source passage copy boundary weakened")
    if copyright_guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU03 learner examples are not marked original")

    units = [row for row in content.get("units", []) if isinstance(row, dict)]
    by_semantic = {str(row.get("proposed_semantic_id")): row for row in units}
    if set(by_semantic) != {
        "ru-lexis-contextual-meaning-polysemy",
        READY_SEMANTIC,
        "ru-lexis-phraseology-free-combination",
    }:
        raise AssertionError("RU03 learner-unit semantic set drift")

    ready_unit = by_semantic[READY_SEMANTIC]
    serialized_ready = json.dumps(ready_unit, ensure_ascii=False).lower()
    if "пароним" not in serialized_ready or "значен" not in serialized_ready or "сочетаем" not in serialized_ready:
        raise AssertionError("candidate-011 exact meaning/collocation learner boundary not present")
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
        value = ready_unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"candidate-011 learner section incomplete: {key}")
    peis = ready_unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
        raise AssertionError("candidate-011 learner content self-admitted")
    if peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise AssertionError("candidate-011 independent-evidence boundary weakened")
    tutor = ready_unit.get("tutor_grounding") or {}
    if not tutor.get("allowed") or not tutor.get("forbidden"):
        raise AssertionError("candidate-011 Tutor grounding missing")

    u008 = json.dumps(by_semantic["ru-lexis-contextual-meaning-polysemy"], ensure_ascii=False).lower()
    if "многознач" not in u008:
        raise AssertionError("candidate-008 broader-content reason no longer proven")
    u014 = json.dumps(by_semantic["ru-lexis-phraseology-free-combination"], ensure_ascii=False).lower()
    if "свободн" not in u014 or "фразеолог" not in u014:
        raise AssertionError("candidate-014 broader-content reason no longer proven")

    ready_rows = [
        row for row in review_rows.values()
        if row.get("disposition") == "EXACT_BOUNDED_SUBJECT_SEMANTIC_ADMISSION_READY_NOT_ADMITTED"
    ]
    ready_row = one(ready_rows, "RU03 exact admission-ready candidate")
    if ready_row.get("candidate_ref") != READY_CANDIDATE:
        raise AssertionError("RU03 wrong candidate marked admission-ready")
    if any(
        row.get("disposition") == "EXACT_BOUNDED_SUBJECT_SEMANTIC_ADMISSION_READY_NOT_ADMITTED"
        for key, row in review_rows.items() if key != READY_CANDIDATE
    ):
        raise AssertionError("RU03 review over-admitted another candidate")

    admission_ready = review.get("admission_ready") or {}
    if (
        admission_ready.get("candidate_ref") != READY_CANDIDATE
        or admission_ready.get("source_taxonomy_id") != READY_TAXONOMY
        or admission_ready.get("proposed_semantic_id") != READY_SEMANTIC
        or admission_ready.get("status") != "READY_FOR_SEPARATE_BOUNDED_SEMANTIC_ACCEPTANCE_NOT_ACCEPTED_BY_THIS_REVIEW"
    ):
        raise AssertionError("RU03 admission-ready handoff drift")

    summary = review.get("summary") or {}
    expected_summary = {
        "candidates_reviewed": 8,
        "confirmed_skill_graph_candidates": 7,
        "needs_review_skill_graph_candidates": 1,
        "exact_content_admission_ready_candidates": 1,
        "semantic_admissions": 0,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise AssertionError("RU03 review summary drift")

    digest = hashlib.sha256(
        json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU03_LEXIS_CANDIDATE_BOUNDARY_REVIEW=PASS")
    print(f"CANDIDATES_REVIEWED={summary['candidates_reviewed']}")
    print("EXACT_ADMISSION_READY=candidate-011")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
