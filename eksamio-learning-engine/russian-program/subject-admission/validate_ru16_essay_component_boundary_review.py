#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
REVIEW = HERE / "RU16-ESSAY-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
ACCEPTANCE = HERE / "RU16-TASK27-BOUNDED-ROUTE-SEMANTIC-ACCEPTANCE-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
WAVE = PROGRAM / "production-learning-content" / "RU-PROG-16-EGE-ESSAY-WAVE-001-v0.1.json"

ACCEPTED = {
    "candidate-048": ("author_position_formulation", "ru-ege-essay-author-position", "K1"),
    "candidate-049": ("textual_comment_examples", "ru-ege-essay-source-examples-explanation", "K2_COMPONENT"),
    "candidate-050": ("example_relation_explanation", "ru-ege-essay-example-semantic-relation", "K2_COMPONENT"),
    "candidate-051": ("own_position_argumentation", "ru-ege-essay-own-relation-justification", "K3"),
}
PENDING_SOURCE_VERIFIED = {
    "candidate-052": ("essay_composition_coherence", "ru-ege-essay-logical-composition-cohesion", "K5"),
}
PENDING_CRITERION = {
    "candidate-054": ("essay_factual_accuracy", "ru-ege-essay-factual-accuracy", "K4"),
    "candidate-055": ("essay_ethical_compliance", "ru-ege-essay-ethical-norm", "K6"),
}
EXPECTED_CROSS = {
    "K7": ("orthographic_norms", {"RU-PROG-08"}),
    "K8": ("punctuation_norms", {"RU-PROG-10"}),
    "K9": ("grammar_norms", {"RU-PROG-07", "RU-PROG-09"}),
    "K10": ("speech_norms", {"RU-PROG-14"}),
}


def _objects(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    rows = inventory.get("objects")
    if not isinstance(rows, list):
        raise AssertionError("semantic inventory objects missing")
    return [row for row in rows if isinstance(row, dict)]


def _taxonomy_evidence(objects: list[dict[str, Any]], candidate_ref: str, source_id: str) -> None:
    matches = [
        obj for obj in objects
        if obj.get("candidate_canonical_owner") == candidate_ref
        and obj.get("source_id") == source_id
        and obj.get("audit_classification") == "EGE_TAXONOMY_NODE"
    ]
    if len(matches) != 1:
        raise AssertionError(f"RU16 exact taxonomy evidence mismatch: {candidate_ref}/{source_id}")
    source = matches[0]
    if source.get("authority_status") != "current" or source.get("review_status") != "source_verified":
        raise AssertionError(f"RU16 taxonomy evidence is not current/source-verified: {candidate_ref}")
    expected_ref = f"03-RUSSIAN-SKILL-GRAPH.json#skills[{source_id}]"
    if expected_ref not in set(source.get("evidence_provenance_refs") or []):
        raise AssertionError(f"RU16 taxonomy provenance drift: {candidate_ref}")


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    wave = json.loads(WAVE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = _objects(inventory)

    if review.get("status") != "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_PARTIAL_WITH_K1_K3_ROUTE_SEMANTICS_ACCEPTED":
        raise AssertionError("RU16 review status drift")
    if review.get("route") != "EGE_2026_TASK_27":
        raise AssertionError("RU16 route drift")
    if review.get("admission_effect") != "FOUR_K1_K3_ROUTE_SEMANTICS_ACCEPTED_REMAINDER_FAIL_CLOSED":
        raise AssertionError("RU16 partial admission effect drift")
    if review.get("acceptance_overlay_ref") != ACCEPTANCE.name:
        raise AssertionError("RU16 acceptance overlay ref drift")

    expected_summary = {
        "route_criteria": 10,
        "explicit_assessment_components": 11,
        "candidate_bound_learner_components": 7,
        "cross_module_quality_dimensions": 4,
        "accepted_route_semantics": 4,
        "pending_candidate_bound_components": 3,
        "canonical_school_semantic_admissions": 0,
        "ru_proposal_admissions": 4,
        "new_essay_specific_quality_identities": 0,
    }
    if review.get("summary") != expected_summary:
        raise AssertionError(f"RU16 review summary drift: {review.get('summary')}")
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU16_TASK27_K1_K3_ROUTE_SEMANTICS":
        raise AssertionError("RU16 acceptance overlay not accepted")
    if acceptance.get("summary", {}).get("accepted_route_semantics") != 4:
        raise AssertionError("RU16 acceptance overlay count drift")

    policy = review.get("policy")
    if not isinstance(policy, dict):
        raise AssertionError("RU16 review policy missing")
    for key in (
        "reuse_existing_semantics_first",
        "criterion_label_is_not_semantic_identity",
        "component_specific_independent_evidence_required",
        "k2_components_must_remain_separate",
        "k7_k10_must_reuse_cross_module_semantics",
        "tier_b_may_refine_but_not_expand_tier_a",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU16 policy weakened: {key}")
    for key in ("content_presence_implies_admission", "candidate_presence_implies_admission", "generic_essay_attempt_can_emit_component_mastery"):
        if policy.get(key) is not False:
            raise AssertionError(f"RU16 fail-closed policy weakened: {key}")

    components = review.get("candidate_bound_components")
    if not isinstance(components, list) or len(components) != 7:
        raise AssertionError("RU16 must expose exactly seven candidate-bound learner components")
    by_candidate = {str(row.get("candidate_ref")): row for row in components if isinstance(row, dict)}
    expected_candidates = set(ACCEPTED) | set(PENDING_SOURCE_VERIFIED) | set(PENDING_CRITERION)
    if set(by_candidate) != expected_candidates:
        raise AssertionError("RU16 candidate component set drift")

    accepted_overlay = {
        str(row.get("candidate_ref")): row
        for row in acceptance.get("decisions", [])
        if isinstance(row, dict)
    }
    if set(accepted_overlay) != set(ACCEPTED):
        raise AssertionError("RU16 acceptance overlay candidate set drift")

    for candidate_ref, (source_id, semantic_id, criterion) in ACCEPTED.items():
        row = by_candidate[candidate_ref]
        if (row.get("source_id"), row.get("proposed_semantic_id"), row.get("criterion_route")) != (source_id, semantic_id, criterion):
            raise AssertionError(f"RU16 accepted binding drift: {candidate_ref}")
        if row.get("status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_ROUTE_SEMANTIC":
            raise AssertionError(f"RU16 accepted component lost acceptance: {candidate_ref}")
        if not str(row.get("acceptance_ref", "")).startswith(ACCEPTANCE.name + "#"):
            raise AssertionError(f"RU16 accepted component lacks durable overlay ref: {candidate_ref}")
        overlay = accepted_overlay[candidate_ref]
        if overlay.get("accepted_semantic_id") != semantic_id:
            raise AssertionError(f"RU16 overlay semantic drift: {candidate_ref}")
        _taxonomy_evidence(objects, candidate_ref, source_id)

    for candidate_ref, (source_id, semantic_id, criterion) in PENDING_SOURCE_VERIFIED.items():
        row = by_candidate[candidate_ref]
        if (row.get("source_id"), row.get("proposed_semantic_id"), row.get("criterion_route")) != (source_id, semantic_id, criterion):
            raise AssertionError(f"RU16 pending source binding drift: {candidate_ref}")
        if row.get("status") != "SOURCE_VERIFIED_BOUNDARY_READY_FOR_SUBJECT_ACCEPTANCE_NOT_ADMITTED":
            raise AssertionError(f"RU16 pending K5 status drift: {candidate_ref}")
        _taxonomy_evidence(objects, candidate_ref, source_id)

    k4 = by_candidate["candidate-054"]
    if k4.get("status") != "GRANULARITY_REVIEW_OPEN_NOT_ADMITTED":
        raise AssertionError("candidate-054 K4 granularity blocker was silently removed")
    c54 = [obj for obj in objects if obj.get("object_key") == "semantic_candidate::candidate-054"]
    if len(c54) != 1 or c54[0].get("review_status") != "needs_review":
        raise AssertionError("candidate-054 inventory granularity review is not open")

    k6 = by_candidate["candidate-055"]
    if k6.get("status") != "CRITERION_PROVEN_BOUNDARY_READY_FOR_SUBJECT_ACCEPTANCE_NOT_ADMITTED":
        raise AssertionError("candidate-055 K6 was silently admitted")

    wave_bindings = wave.get("candidate_bindings")
    units = wave.get("units")
    if not isinstance(wave_bindings, list) or not isinstance(units, list) or len(wave_bindings) != 7 or len(units) != 7:
        raise AssertionError("RU16 learner-content bundle must keep seven exact candidate bindings/units")
    wave_pairs = {
        (str(row.get("candidate_ref")), str(row.get("proposed_semantic_id")), str(row.get("criterion_route")))
        for row in wave_bindings if isinstance(row, dict)
    }
    review_pairs = {
        (str(row.get("candidate_ref")), str(row.get("proposed_semantic_id")), str(row.get("criterion_route")))
        for row in components if isinstance(row, dict)
    }
    if wave_pairs != review_pairs:
        raise AssertionError("RU16 review does not match learner-content candidate bindings")

    k2 = review.get("k2_decomposition")
    if not isinstance(k2, dict) or k2.get("criterion_route") != "K2":
        raise AssertionError("RU16 K2 decomposition missing")
    if set(k2.get("components") or []) != {"ru-ege-essay-source-examples-explanation", "ru-ege-essay-example-semantic-relation"}:
        raise AssertionError("RU16 K2 components collapsed")
    if k2.get("component_acceptance_status") != "BOTH_COMPONENTS_ACCEPTED_SEPARATELY":
        raise AssertionError("RU16 K2 accepted components were not kept separate")

    cross = review.get("cross_module_quality_dimensions")
    if not isinstance(cross, list) or len(cross) != 4:
        raise AssertionError("RU16 K7-K10 cross-module dimensions missing")
    actual_cross = {
        str(row.get("criterion_route")): (str(row.get("quality_dimension")), set(str(value) for value in row.get("module_refs") or []))
        for row in cross if isinstance(row, dict)
    }
    if actual_cross != EXPECTED_CROSS:
        raise AssertionError(f"RU16 K7-K10 cross-module binding drift: {actual_cross}")
    if any(row.get("status") != "REUSE_EXACT_ADMITTED_COMPONENTS_REQUIRED_NOT_ADMITTED" for row in cross):
        raise AssertionError("RU16 K7-K10 was silently admitted")

    c53_guard = review.get("candidate_053_guard")
    if not isinstance(c53_guard, dict) or c53_guard.get("status") != "NARROW_GRAMMAR_CONTRIBUTOR_ONLY_NOT_K9_OWNER":
        raise AssertionError("RU16 candidate-053 guard missing/broadened")
    c53 = [obj for obj in objects if obj.get("object_key") == "semantic_candidate::candidate-053"]
    if len(c53) != 1 or set(c53[0].get("current_semantic_refs") or []) != {"comparison_degree_forms"}:
        raise AssertionError("candidate-053 narrow semantic truth drift")

    serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
    if "ru-essay-language-correctness" in serialized or '"canonical_school_semantic_admissions": 1' in serialized:
        raise AssertionError("RU16 review introduced a broad duplicate identity or school-canonical mutation")

    print("RU16_ESSAY_COMPONENT_BOUNDARY_REVIEW=PASS")
    print("ROUTE_CRITERIA=10")
    print("EXPLICIT_ASSESSMENT_COMPONENTS=11")
    print("CANDIDATE_BOUND_LEARNER_COMPONENTS=7")
    print("ACCEPTED_ROUTE_SEMANTICS=4")
    print("K2_ACCEPTED_COMPONENTS=2")
    print("PENDING_CANDIDATE_BOUND_COMPONENTS=3")
    print("K7_K10_CROSS_MODULE_REUSE_DIMENSIONS=4")
    print("NEW_ESSAY_SPECIFIC_QUALITY_IDENTITIES=0")
    print("CANONICAL_SCHOOL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
