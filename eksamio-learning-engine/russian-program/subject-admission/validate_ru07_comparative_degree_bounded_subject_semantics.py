#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
BOUNDARY_BUILDER = HERE / "build_ru07_grammar_norms_candidate_boundary_review.py"
ACCEPTANCE = HERE / "RU07-COMPARATIVE-DEGREE-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-07-GRAMMAR-NORMS-WAVE-002-v0.1.json"
GAP_REVIEW = ENGINE / "87A-RUSSIAN-MORPHOLOGY-GRAPH-GAP-CANDIDATES.txt"

CANDIDATE = "candidate-053"
SEMANTIC = "ru-grammar-comparative-degree-norm"
SOURCE_REF = "comparison_degree_forms"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def one(rows: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if len(rows) != 1:
        raise AssertionError(f"{label}: expected 1, got {len(rows)}")
    return rows[0]


def main() -> int:
    boundary = runpy.run_path(str(BOUNDARY_BUILDER))["build_review"]()
    acceptance = load(ACCEPTANCE)
    content = load(CONTENT)
    gap = GAP_REVIEW.read_text(encoding="utf-8")

    if boundary.get("status") != "CENTRAL_BRAIN_RU07_GRAMMAR_NORMS_REUSE_FIRST_BOUNDARY_REVIEW_ACCEPTANCE_NOT_ADMITTED":
        raise AssertionError("RU07 antecedent boundary status drift")
    if boundary.get("module_id") != "RU-PROG-07" or boundary.get("module_binding_mode") != "DRAFT_CANDIDATE_BINDING":
        raise AssertionError("RU07 module boundary drift")
    reuse = boundary.get("reuse_review") or {}
    if reuse.get("current_proposed_id_collisions") != 0:
        raise AssertionError("RU07 proposed semantic id collision detected")
    if reuse.get("needs_review_candidates_blocking_exact_alignment") != 1:
        raise AssertionError("RU07 candidate-053 needs-review blocker drift")
    policy0 = boundary.get("policy") or {}
    if policy0.get("needs_review_candidate_can_be_admitted") is not False:
        raise AssertionError("RU07 needs-review fail-closed guard weakened")
    if policy0.get("component_specific_independent_evidence_required") is not True:
        raise AssertionError("RU07 component-specific evidence guard missing")

    rel = one(
        [row for row in boundary.get("candidate_relation_decisions", []) if isinstance(row, dict) and row.get("candidate_ref") == CANDIDATE and row.get("content_semantic_id") == SEMANTIC],
        "candidate-053 antecedent relation",
    )
    if rel.get("relation") != "MEANING_ALIGNMENT_WITH_NEEDS_REVIEW_CANDIDATE_NO_ACCEPTANCE" or rel.get("acceptance_effect") != "NONE":
        raise AssertionError("candidate-053 antecedent relation drift")
    snapshot = one(
        [row for row in boundary.get("candidate_inventory_snapshot", []) if isinstance(row, dict) and row.get("candidate_ref") == CANDIDATE],
        "candidate-053 inventory snapshot",
    )
    if snapshot.get("review_status") != "needs_review" or snapshot.get("current_semantic_refs") != [SOURCE_REF]:
        raise AssertionError("candidate-053 source identity/review state drift")

    for token in (
        "LANGUAGE CONTENT: VERIFIED",
        "EXACT SKILL ROUTING: HOLD",
        "GRAPH CHANGE: NOT AUTHORIZED / REVIEW LATER",
        "CURRENT TRAINER: UNCHANGED",
        "более СТРОГО",
        "более строже",
    ):
        if token not in gap:
            raise AssertionError(f"RU07 comparison gap authority drift: {token}")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-07":
        raise AssertionError("RU07 content self-admitted or module drift")
    provenance = content.get("source_provenance") or []
    if not any(isinstance(row, dict) and row.get("kind") == "official_program" and row.get("access") == "PUBLIC_OFFICIAL_PDF" for row in provenance):
        raise AssertionError("RU07 public official-program provenance missing")
    if not any(isinstance(row, dict) and row.get("kind") == "official_exam_methodology" and row.get("access") == "PUBLIC_OFFICIAL_PDF" for row in provenance):
        raise AssertionError("RU07 public official exam-methodology provenance missing")
    guard = content.get("copyright_guard") or {}
    if guard.get("source_passages_copied") != 0 or guard.get("learner_examples") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU07 copyright/original-content guard drift")
    unit = one(
        [row for row in content.get("units", []) if isinstance(row, dict) and row.get("proposed_semantic_id") == SEMANTIC],
        "RU07 comparative-degree learner unit",
    )
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
        rows = unit.get(key)
        if not isinstance(rows, list) or len(rows) < minimum:
            raise AssertionError(f"RU07 comparative learner coverage too small: {key}")
    peis = unit.get("peis_evidence") or {}
    if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("independent_verification_required") is not True:
        raise AssertionError("RU07 comparative PEIS fail-closed state drift")
    tutor = unit.get("tutor_grounding") or {}
    if not tutor.get("allowed") or not tutor.get("forbidden"):
        raise AssertionError("RU07 comparative Tutor boundary missing")

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU07_COMPARATIVE_DEGREE_BOUNDED_SUBJECT_SEMANTIC":
        raise AssertionError("RU07 comparative acceptance status drift")
    if acceptance.get("authority_issue") != 161:
        raise AssertionError("RU07 comparative authority issue drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU07 comparative registry mutation/duplication forbidden")

    source_truth = acceptance.get("source_truth") or {}
    if source_truth.get("candidate_ref") != CANDIDATE or source_truth.get("candidate_source_taxonomy_ref") != SOURCE_REF:
        raise AssertionError("RU07 comparative source truth crosswalk drift")
    if source_truth.get("candidate_review_status") != "needs_review":
        raise AssertionError("RU07 candidate-053 must remain needs_review")
    if source_truth.get("gap_review_language_content_status") != "VERIFIED" or source_truth.get("gap_review_exact_skill_routing_status") != "HOLD":
        raise AssertionError("RU07 comparison gap-review disposition drift")
    if source_truth.get("accepted_semantic_is_exact_candidate_equivalent") is not False or source_truth.get("accepted_semantic_relation_to_candidate") != "BOUNDED_SUBSET":
        raise AssertionError("RU07 comparative subset boundary drift")

    official = acceptance.get("official_source_verification") or []
    if len(official) != 2:
        raise AssertionError("RU07 comparative official-source evidence set drift")
    by_url = {str(row.get("url")): row for row in official if isinstance(row, dict)}
    navigator_url = "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-3-grammatika-morfologija.pdf"
    methods_url = "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/MR_rus_yaz_ege_2026.pdf"
    if by_url.get(navigator_url, {}).get("pdf_page_index") != 0:
        raise AssertionError("RU07 comparison FIPI navigator evidence drift")
    if by_url.get(methods_url, {}).get("pdf_page_index") != 24:
        raise AssertionError("RU07 comparison FIPI methodology evidence drift")
    if "более СТРОГО" not in str(by_url.get(methods_url, {}).get("verified_fact")):
        raise AssertionError("RU07 comparison official Task-7 fact drift")

    policy = acceptance.get("policy") or {}
    for key in (
        "reuse_first",
        "current_semantic_inventory_collision_forbidden",
        "school_duplicate_forbidden",
        "component_specific_independent_evidence_required",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU07 comparative required policy weakened: {key}")
    for key in (
        "candidate_ref_is_canonical_id",
        "candidate_ref_admitted",
        "needs_review_candidate_can_be_silently_admitted",
        "subset_evidence_can_admit_broader_candidate",
        "module_membership_implies_exact_owner",
        "content_presence_implies_acceptance",
        "generic_task7_result_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "keyword_or_fuzzy_inference_allowed",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU07 comparative fail-closed policy drift: {key}")
    if policy.get("new_subject_identity_namespace") != "ru-*":
        raise AssertionError("RU07 comparative namespace drift")

    decision = one(acceptance.get("decisions") or [], "RU07 comparative acceptance decision")
    if (
        decision.get("candidate_ref") != CANDIDATE
        or decision.get("source_taxonomy_ref") != SOURCE_REF
        or decision.get("accepted_semantic_id") != SEMANTIC
        or decision.get("entity_type") != "COMPARATIVE_DEGREE_FORMATION_MODEL_SKILL"
        or decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC"
        or decision.get("relation_to_candidate") != "CONTENT_IS_BOUNDED_SUBSET_OF_NEEDS_REVIEW_CANDIDATE"
        or decision.get("broader_candidate_status_after_acceptance") != "REMAINS_NEEDS_REVIEW_NOT_ADMITTED"
        or decision.get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT"
    ):
        raise AssertionError("RU07 comparative acceptance decision drift")
    boundary_guard = str(decision.get("boundary_guard") or "").lower()
    for token in ("simple comparative", "compound comparative", "double-comparative", "superlative", "task-7"):
        if token not in boundary_guard:
            raise AssertionError(f"RU07 comparative boundary missing token: {token}")

    ag = acceptance.get("copyright_guard") or {}
    if ag.get("source_passages_copied") != 0 or ag.get("commercial_textbook_bytes") != 0:
        raise AssertionError("RU07 comparative acceptance copyright guard drift")
    summary = acceptance.get("summary") or {}
    expected = {
        "accepted_bounded_subject_semantics": 1,
        "accepted_ru_subject_semantics": 1,
        "broader_candidate_records_admitted": 0,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise AssertionError(f"RU07 comparative acceptance summary drift: {key}")

    digest = hashlib.sha256(
        json.dumps(acceptance, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("RU07_COMPARATIVE_DEGREE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
    print(f"ACCEPTED_SEMANTIC={SEMANTIC}")
    print("RELATION_TO_CANDIDATE_053=BOUNDED_SUBSET")
    print("CANDIDATE_053_STATUS=REMAINS_NEEDS_REVIEW_NOT_ADMITTED")
    print("OBJECT_CLOSURES=0/0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
