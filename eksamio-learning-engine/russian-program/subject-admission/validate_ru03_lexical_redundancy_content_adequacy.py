#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent

REVIEW = HERE / "RU03-LEXICAL-REDUNDANCY-CONTENT-ADEQUACY-REVIEW-v0.1.json"
BOUNDARY = HERE / "RU03-LEXIS-CANDIDATE-BOUNDARY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-03-LEXICAL-REDUNDANCY-WAVE-005-v0.1.json"

CANDIDATE = "candidate-012"
TAXONOMY = "lexical_redundancy"
SEMANTIC = "ru-lexis-redundancy-extra-word"


def normalized(value: Any) -> str:
    return str(value or "").strip().rstrip(".").strip()


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if review.get("status") != "CENTRAL_BRAIN_RU03_LEXICAL_REDUNDANCY_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU03 lexical-redundancy content review status drift")
    if review.get("authority_issue") != 161:
        raise AssertionError("RU03 lexical-redundancy authority issue drift")

    if boundary.get("status") != "CENTRAL_BRAIN_RU03_LEXIS_CANDIDATE_BOUNDARY_REVIEW_COMPLETE_NO_ADMISSION":
        raise AssertionError("RU03 boundary prerequisite drift")
    brow = one(
        [r for r in boundary.get("candidate_review", []) if r.get("candidate_ref") == CANDIDATE],
        "RU03 boundary candidate-012",
    )
    if brow.get("source_taxonomy_id") != TAXONOMY or brow.get("skill_graph_evidence_status") != "confirmed":
        raise AssertionError("RU03 candidate-012 antecedent source boundary drift")
    if brow.get("disposition") != "REVIEWED_NOT_ADMITTED" or brow.get("content_boundary") != "NO_DEDICATED_EXACT_LEARNER_UNIT":
        raise AssertionError("RU03 candidate-012 antecedent content-gap truth drift")

    source = review.get("source_identity") or {}
    if (
        source.get("candidate_ref") != CANDIDATE
        or source.get("source_taxonomy_id") != TAXONOMY
        or source.get("skill_graph_evidence_status") != "confirmed"
        or source.get("inventory_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
    ):
        raise AssertionError("RU03 lexical-redundancy content-review source drift")

    rd = review.get("review_decision") or {}
    if rd.get("content_exact_for_candidate_012") is not True:
        raise AssertionError("RU03 lexical-redundancy content exactness not proven")
    if rd.get("content_duplicate_of_existing_ru03_unit") is not False or rd.get("exact_school_meaning_collision_observed") is not False:
        raise AssertionError("RU03 lexical-redundancy duplicate/reuse boundary drift")
    if rd.get("semantic_admission_by_this_review") is not False:
        raise AssertionError("RU03 lexical-redundancy content review self-admitted semantic")
    if (
        rd.get("object_level_admission_units_closed") != 0
        or rd.get("object_level_requirements_closed") != 0
        or rd.get("false_exact_mastery_admissions") != 0
    ):
        raise AssertionError("RU03 lexical-redundancy content review falsely closed mastery")
    if rd.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise AssertionError("RU03 lexical-redundancy next-status drift")

    objects = [r for r in inventory.get("objects", []) if isinstance(r, dict)]
    candidate = one(
        [
            r
            for r in objects
            if r.get("source_system") == "semantic_candidate"
            and r.get("source_id") == CANDIDATE
            and r.get("authority_status") == "current"
        ],
        "RU03 candidate-012 current inventory",
    )
    if (
        candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE"
        or candidate.get("candidate_canonical_owner") != CANDIDATE
        or candidate.get("current_semantic_refs") != [TAXONOMY]
    ):
        raise AssertionError("RU03 candidate-012 inventory ownership/classification drift")

    backing = one(
        [
            r
            for r in objects
            if r.get("source_system") == "ege_skill_graph"
            and r.get("source_id") == TAXONOMY
            and r.get("authority_status") == "current"
            and r.get("candidate_canonical_owner") == CANDIDATE
        ],
        "RU03 candidate-012 taxonomy backing",
    )
    if backing.get("review_status") != "source_verified" or backing.get("audit_classification") != "EGE_TAXONOMY_NODE":
        raise AssertionError("RU03 candidate-012 taxonomy backing not source-verified")
    if normalized(backing.get("observed_meaning")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU03 candidate-012 inventory meaning mismatch")

    skill = one(
        [r for r in graph.get("skills", []) if isinstance(r, dict) and r.get("skill_id") == TAXONOMY],
        "RU03 candidate-012 graph node",
    )
    if (
        skill.get("evidence_status") != "confirmed"
        or skill.get("parent_skill_id") != "lexical_norms_and_semantics"
        or skill.get("exam_task_numbers") != [6]
    ):
        raise AssertionError("RU03 candidate-012 confirmed Task-6 graph boundary drift")
    if skill.get("name_ru") != candidate.get("observed_label") or normalized(skill.get("description")) != normalized(candidate.get("observed_meaning")):
        raise AssertionError("RU03 candidate-012 graph label/meaning drift")

    if any(
        SEMANTIC in {str(ref) for ref in (r.get("current_semantic_refs") or [])}
        for r in objects
        if r.get("authority_status") == "current"
    ):
        raise AssertionError("RU03 lexical-redundancy proposed semantic id collides with current inventory")
    if any(
        r.get("source_system") == "school_canonical"
        and r.get("authority_status") == "current"
        and normalized(r.get("observed_meaning")) == normalized(candidate.get("observed_meaning"))
        for r in objects
    ):
        raise AssertionError("RU03 candidate-012 exact school meaning already exists; reuse required")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-03":
        raise AssertionError("RU03 lexical-redundancy content status/module drift")
    guard = content.get("copyright_guard") or {}
    if (
        guard.get("source_passages_copied") != 0
        or guard.get("commercial_textbook_bytes") != 0
        or guard.get("learner_examples") != "ORIGINAL_EKSAMIO"
    ):
        raise AssertionError("RU03 lexical-redundancy provenance boundary weakened")

    unit = one(
        [r for r in content.get("units", []) if isinstance(r, dict) and r.get("proposed_semantic_id") == SEMANTIC],
        "RU03 lexical-redundancy learner unit",
    )
    if unit.get("candidate_ref") != CANDIDATE or unit.get("source_taxonomy_id") != TAXONOMY:
        raise AssertionError("RU03 lexical-redundancy content crosswalk drift")

    serialized = json.dumps(unit, ensure_ascii=False).lower()
    for token in ("плеоназ", "лишн", "избыточ"):
        if token not in serialized:
            raise AssertionError(f"RU03 lexical-redundancy content missing target token: {token}")

    for key, minimum in (
        ("decision_algorithm", 6),
        ("worked_examples", 3),
        ("misconceptions", 3),
        ("guided_practice", 2),
        ("independent_practice", 3),
        ("mixed_transfer_practice", 2),
        ("retention_items", 2),
        ("independent_verification", 2),
    ):
        value = unit.get(key)
        if not isinstance(value, list) or len(value) < minimum:
            raise AssertionError(f"RU03 lexical-redundancy learner section incomplete: {key}")

    boundaries = " ".join((unit.get("canonical_explanation") or {}).get("boundaries") or [])
    if "lexical_collocation_correction" not in boundaries or "Task-6" not in boundaries:
        raise AssertionError("RU03 lexical-redundancy adjacent/generic-task exclusions missing")

    peis = unit.get("peis_evidence") or {}
    if (
        peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL"
        or peis.get("independent_verification_required") is not True
        or peis.get("assistance_must_be_recorded") is not True
    ):
        raise AssertionError("RU03 lexical-redundancy PEIS boundary weakened")
    if (
        peis.get("generic_task_result_can_emit_exact_mastery") is not False
        or peis.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    ):
        raise AssertionError("RU03 lexical-redundancy exact-mastery boundary weakened")

    tutor = unit.get("tutor_grounding") or {}
    if not tutor.get("allowed") or not tutor.get("forbidden") or not tutor.get("source_refs"):
        raise AssertionError("RU03 lexical-redundancy Tutor grounding incomplete")

    digest = hashlib.sha256(
        json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU03_LEXICAL_REDUNDANCY_CONTENT_ADEQUACY=PASS")
    print(f"PROPOSED_SEMANTIC={SEMANTIC}")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
