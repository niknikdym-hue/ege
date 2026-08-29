#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
REVIEW = HERE / "RU16-ESSAY-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
BASE_ACCEPTANCE = HERE / "RU16-TASK27-BOUNDED-ROUTE-SEMANTIC-ACCEPTANCE-v0.1.json"
K5_ACCEPTANCE = HERE / "RU16-TASK27-K5-BOUNDED-ROUTE-SEMANTIC-ACCEPTANCE-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
WAVE = ENGINE / "russian-program/production-learning-content/RU-PROG-16-EGE-ESSAY-WAVE-001-v0.1.json"

ACCEPTED = {
    "candidate-048": ("author_position_formulation", "ru-ege-essay-author-position", "K1", BASE_ACCEPTANCE.name),
    "candidate-049": ("textual_comment_examples", "ru-ege-essay-source-examples-explanation", "K2_COMPONENT", BASE_ACCEPTANCE.name),
    "candidate-050": ("example_relation_explanation", "ru-ege-essay-example-semantic-relation", "K2_COMPONENT", BASE_ACCEPTANCE.name),
    "candidate-051": ("own_position_argumentation", "ru-ege-essay-own-relation-justification", "K3", BASE_ACCEPTANCE.name),
    "candidate-052": ("essay_composition_coherence", "ru-ege-essay-logical-composition-cohesion", "K5", K5_ACCEPTANCE.name),
}
EXPECTED_CROSS = {
    "K7": ("orthographic_norms", {"RU-PROG-08"}),
    "K8": ("punctuation_norms", {"RU-PROG-10"}),
    "K9": ("grammar_norms", {"RU-PROG-07", "RU-PROG-09"}),
    "K10": ("speech_norms", {"RU-PROG-14"}),
}


def _objects(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = data.get("objects")
    if not isinstance(rows, list):
        raise AssertionError("semantic inventory objects missing")
    return [row for row in rows if isinstance(row, dict)]


def _taxonomy(objects: list[dict[str, Any]], candidate_ref: str, source_id: str) -> None:
    rows = [row for row in objects if row.get("candidate_canonical_owner") == candidate_ref and row.get("source_id") == source_id and row.get("audit_classification") == "EGE_TAXONOMY_NODE"]
    if len(rows) != 1:
        raise AssertionError(f"taxonomy evidence mismatch: {candidate_ref}/{source_id}")
    row = rows[0]
    if row.get("authority_status") != "current" or row.get("review_status") != "source_verified":
        raise AssertionError(f"taxonomy not source-verified: {candidate_ref}")
    if f"03-RUSSIAN-SKILL-GRAPH.json#skills[{source_id}]" not in set(row.get("evidence_provenance_refs") or []):
        raise AssertionError(f"taxonomy provenance drift: {candidate_ref}")


def _criterion_candidate(objects: list[dict[str, Any]], candidate_ref: str, source_id: str, criterion: str) -> None:
    rows = [row for row in objects if row.get("object_key") == f"semantic_candidate::{candidate_ref}"]
    if len(rows) != 1:
        raise AssertionError(f"criterion candidate mismatch: {candidate_ref}")
    row = rows[0]
    if row.get("authority_status") != "current" or row.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE" or row.get("current_semantic_refs") != [source_id]:
        raise AssertionError(f"criterion candidate truth drift: {candidate_ref}")
    if f"53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[{criterion}]" not in set(row.get("evidence_provenance_refs") or []):
        raise AssertionError(f"criterion provenance missing: {candidate_ref}")


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    base = json.loads(BASE_ACCEPTANCE.read_text(encoding="utf-8"))
    k5 = json.loads(K5_ACCEPTANCE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    wave = json.loads(WAVE.read_text(encoding="utf-8"))
    objects = _objects(inventory)

    if review.get("status") != "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_PARTIAL_WITH_K1_K3_K5_ROUTE_SEMANTICS_ACCEPTED":
        raise AssertionError("RU16 boundary status drift")
    if review.get("admission_effect") != "FIVE_K1_K3_K5_ROUTE_SEMANTICS_ACCEPTED_REMAINDER_FAIL_CLOSED":
        raise AssertionError("RU16 admission effect drift")
    if review.get("acceptance_overlay_refs") != [BASE_ACCEPTANCE.name, K5_ACCEPTANCE.name]:
        raise AssertionError("RU16 acceptance overlay refs drift")
    expected_summary = {
        "route_criteria": 10,
        "explicit_assessment_components": 11,
        "candidate_bound_learner_components": 7,
        "cross_module_quality_dimensions": 4,
        "accepted_route_semantics": 5,
        "pending_candidate_bound_components": 2,
        "canonical_school_semantic_admissions": 0,
        "ru_proposal_admissions": 5,
        "new_essay_specific_quality_identities": 0,
    }
    if review.get("summary") != expected_summary:
        raise AssertionError(f"RU16 summary drift: {review.get('summary')}")
    if base.get("summary", {}).get("accepted_route_semantics") != 4 or k5.get("summary", {}).get("accepted_route_semantics") != 1:
        raise AssertionError("RU16 overlay acceptance counts drift")

    components = review.get("candidate_bound_components")
    if not isinstance(components, list) or len(components) != 7:
        raise AssertionError("RU16 candidate component count drift")
    by_candidate = {str(row.get("candidate_ref")): row for row in components if isinstance(row, dict)}
    if set(by_candidate) != {"candidate-048", "candidate-049", "candidate-050", "candidate-051", "candidate-052", "candidate-054", "candidate-055"}:
        raise AssertionError("RU16 candidate component set drift")

    for candidate_ref, (source_id, semantic_id, criterion, authority_file) in ACCEPTED.items():
        row = by_candidate[candidate_ref]
        if (row.get("source_id"), row.get("proposed_semantic_id"), row.get("criterion_route")) != (source_id, semantic_id, criterion):
            raise AssertionError(f"accepted binding drift: {candidate_ref}")
        if row.get("status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_ROUTE_SEMANTIC":
            raise AssertionError(f"accepted status drift: {candidate_ref}")
        if not str(row.get("acceptance_ref", "")).startswith(authority_file + "#"):
            raise AssertionError(f"accepted authority ref drift: {candidate_ref}")
        _taxonomy(objects, candidate_ref, source_id)

    if by_candidate["candidate-054"].get("status") != "CRITERION_PROVEN_BOUNDARY_READY_FOR_SUBJECT_ACCEPTANCE_NOT_ADMITTED":
        raise AssertionError("K4 was admitted or lost criterion-proven status")
    if by_candidate["candidate-055"].get("status") != "CRITERION_PROVEN_BOUNDARY_READY_FOR_SUBJECT_ACCEPTANCE_NOT_ADMITTED":
        raise AssertionError("K6 was admitted or lost criterion-proven status")
    _criterion_candidate(objects, "candidate-054", "essay_factual_accuracy", "K4")
    _criterion_candidate(objects, "candidate-055", "essay_ethical_compliance", "K6")

    bindings = {(str(row.get("candidate_ref")), str(row.get("proposed_semantic_id")), str(row.get("criterion_route"))) for row in wave.get("candidate_bindings", []) if isinstance(row, dict)}
    review_bindings = {(str(row.get("candidate_ref")), str(row.get("proposed_semantic_id")), str(row.get("criterion_route"))) for row in components}
    if bindings != review_bindings:
        raise AssertionError("RU16 learner-content bindings drift")

    k2 = review.get("k2_decomposition", {})
    if set(k2.get("components") or []) != {"ru-ege-essay-source-examples-explanation", "ru-ege-essay-example-semantic-relation"} or k2.get("component_acceptance_status") != "BOTH_COMPONENTS_ACCEPTED_SEPARATELY":
        raise AssertionError("RU16 K2 decomposition drift")

    cross = review.get("cross_module_quality_dimensions") or []
    actual_cross = {str(row.get("criterion_route")): (str(row.get("quality_dimension")), set(str(value) for value in row.get("module_refs") or [])) for row in cross if isinstance(row, dict)}
    if actual_cross != EXPECTED_CROSS or any(row.get("status") != "REUSE_EXACT_ADMITTED_COMPONENTS_REQUIRED_NOT_ADMITTED" for row in cross):
        raise AssertionError("RU16 K7-K10 cross-module boundary drift")
    if review.get("candidate_053_guard", {}).get("status") != "NARROW_GRAMMAR_CONTRIBUTOR_ONLY_NOT_K9_OWNER":
        raise AssertionError("candidate-053 guard broadened")

    serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
    if "ru-essay-language-correctness" in serialized or '"canonical_school_semantic_admissions": 1' in serialized:
        raise AssertionError("broad duplicate identity or school-canonical mutation introduced")

    print("RU16_ESSAY_COMPONENT_BOUNDARY_REVIEW=PASS")
    print("ACCEPTED_ROUTE_SEMANTICS=5")
    print("K1_K3_ACCEPTED_ROUTE_SEMANTICS=4")
    print("K5_ACCEPTED_ROUTE_SEMANTICS=1")
    print("K4_PENDING=1")
    print("K6_PENDING=1")
    print("K7_K10_CROSS_MODULE_REUSE_PENDING=4")
    print("CANONICAL_SCHOOL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
