#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
REVIEW = HERE / "RU16-ESSAY-COMPONENT-BOUNDARY-REVIEW-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
WAVE = PROGRAM / "production-learning-content" / "RU-PROG-16-EGE-ESSAY-WAVE-001-v0.1.json"

SOURCE_VERIFIED = {
    "candidate-048": ("author_position_formulation", "ru-ege-essay-author-position", "K1"),
    "candidate-049": ("textual_comment_examples", "ru-ege-essay-source-examples-explanation", "K2_COMPONENT"),
    "candidate-050": ("example_relation_explanation", "ru-ege-essay-example-semantic-relation", "K2_COMPONENT"),
    "candidate-051": ("own_position_argumentation", "ru-ege-essay-own-relation-justification", "K3"),
    "candidate-052": ("essay_composition_coherence", "ru-ege-essay-logical-composition-cohesion", "K5"),
}
CRITERION_PROVEN = {
    "candidate-054": (
        "essay_factual_accuracy",
        "ru-ege-essay-factual-accuracy",
        "K4",
        {
            "53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[K4]",
            "55-RUSSIAN-ESSAY-27-EXPLANATION-COMPONENTS-v0.1.json#essay_fact_logic_review",
        },
    ),
    "candidate-055": (
        "essay_ethical_compliance",
        "ru-ege-essay-ethical-norm",
        "K6",
        {
            "53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[K6]",
            "55-RUSSIAN-ESSAY-27-EXPLANATION-COMPONENTS-v0.1.json#essay_ethics_review",
        },
    ),
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


def main() -> int:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    wave = json.loads(WAVE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = _objects(inventory)

    if review.get("status") != "CENTRAL_BRAIN_COMPONENT_BOUNDARY_REVIEW_PARTIAL":
        raise AssertionError("RU16 review status drift")
    if review.get("route") != "EGE_2026_TASK_27":
        raise AssertionError("RU16 route drift")
    if review.get("admission_effect") != "NONE_UNTIL_EXPLICIT_CANONICAL_SEMANTIC_ACCEPTANCE":
        raise AssertionError("RU16 review admission effect weakened")

    summary = review.get("summary")
    expected_summary = {
        "route_criteria": 10,
        "explicit_assessment_components": 11,
        "candidate_bound_learner_components": 7,
        "cross_module_quality_dimensions": 4,
        "canonical_semantic_admissions": 0,
        "ru_proposal_admissions": 0,
        "new_essay_specific_quality_identities": 0,
    }
    if summary != expected_summary:
        raise AssertionError(f"RU16 review summary drift: {summary}")

    policy = review.get("policy")
    if not isinstance(policy, dict):
        raise AssertionError("RU16 review policy missing")
    expected_true = {
        "reuse_existing_semantics_first",
        "criterion_label_is_not_semantic_identity",
        "component_specific_independent_evidence_required",
        "k2_components_must_remain_separate",
        "k7_k10_must_reuse_cross_module_semantics",
    }
    for key in expected_true:
        if policy.get(key) is not True:
            raise AssertionError(f"RU16 policy weakened: {key}")
    for key in ("content_presence_implies_admission", "candidate_presence_implies_admission", "generic_essay_attempt_can_emit_component_mastery"):
        if policy.get(key) is not False:
            raise AssertionError(f"RU16 fail-closed policy weakened: {key}")

    components = review.get("candidate_bound_components")
    if not isinstance(components, list) or len(components) != 7:
        raise AssertionError("RU16 must expose exactly seven candidate-bound learner components")
    by_candidate = {str(row.get("candidate_ref")): row for row in components if isinstance(row, dict)}
    if set(by_candidate) != set(SOURCE_VERIFIED) | set(CRITERION_PROVEN):
        raise AssertionError("RU16 candidate component set drift")

    for candidate_ref, (source_id, semantic_id, criterion) in SOURCE_VERIFIED.items():
        row = by_candidate[candidate_ref]
        if (row.get("source_id"), row.get("proposed_semantic_id"), row.get("criterion_route")) != (source_id, semantic_id, criterion):
            raise AssertionError(f"RU16 source-verified binding drift: {candidate_ref}")
        if row.get("status") != "SOURCE_VERIFIED_BOUNDARY_READY_FOR_SUBJECT_ACCEPTANCE_NOT_ADMITTED":
            raise AssertionError(f"RU16 source-verified component self-admitted: {candidate_ref}")
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

    for candidate_ref, (source_id, semantic_id, criterion, authority_refs) in CRITERION_PROVEN.items():
        row = by_candidate[candidate_ref]
        if (row.get("source_id"), row.get("proposed_semantic_id"), row.get("criterion_route")) != (source_id, semantic_id, criterion):
            raise AssertionError(f"RU16 criterion-proven binding drift: {candidate_ref}")
        if row.get("status") != "CRITERION_PROVEN_BOUNDARY_READY_FOR_SUBJECT_ACCEPTANCE_NOT_ADMITTED":
            raise AssertionError(f"RU16 criterion-proven component self-admitted: {candidate_ref}")
        if set(row.get("authority_refs") or []) != authority_refs:
            raise AssertionError(f"RU16 criterion authority refs drift: {candidate_ref}")
        matches = [obj for obj in objects if obj.get("object_key") == f"semantic_candidate::{candidate_ref}"]
        if len(matches) != 1:
            raise AssertionError(f"RU16 semantic candidate evidence mismatch: {candidate_ref}")
        candidate = matches[0]
        if candidate.get("authority_status") != "current" or candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise AssertionError(f"RU16 criterion candidate classification drift: {candidate_ref}")
        if set(candidate.get("current_semantic_refs") or []) != {source_id}:
            raise AssertionError(f"RU16 criterion candidate semantic ref drift: {candidate_ref}")
        if not authority_refs.issubset(set(candidate.get("evidence_provenance_refs") or [])):
            raise AssertionError(f"RU16 criterion candidate provenance incomplete: {candidate_ref}")

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
    if {str(row.get("proposed_semantic_id")) for row in units if isinstance(row, dict)} != {item[1] for item in SOURCE_VERIFIED.values()} | {item[1] for item in CRITERION_PROVEN.values()}:
        raise AssertionError("RU16 learner-unit semantic set drift")

    k2 = review.get("k2_decomposition")
    if not isinstance(k2, dict) or k2.get("criterion_route") != "K2":
        raise AssertionError("RU16 K2 decomposition missing")
    if set(k2.get("components") or []) != {"ru-ege-essay-source-examples-explanation", "ru-ege-essay-example-semantic-relation"}:
        raise AssertionError("RU16 K2 components collapsed")

    cross = review.get("cross_module_quality_dimensions")
    if not isinstance(cross, list) or len(cross) != 4:
        raise AssertionError("RU16 K7-K10 cross-module dimensions missing")
    actual_cross = {
        str(row.get("criterion_route")): (str(row.get("quality_dimension")), set(str(value) for value in row.get("module_refs") or []))
        for row in cross if isinstance(row, dict)
    }
    if actual_cross != EXPECTED_CROSS:
        raise AssertionError(f"RU16 K7-K10 cross-module binding drift: {actual_cross}")
    for row in cross:
        if row.get("status") != "REUSE_EXACT_ADMITTED_COMPONENTS_REQUIRED_NOT_ADMITTED":
            raise AssertionError(f"RU16 cross-module dimension self-admitted: {row.get('criterion_route')}")

    candidate_053 = review.get("candidate_053_guard")
    if not isinstance(candidate_053, dict) or candidate_053.get("candidate_ref") != "candidate-053":
        raise AssertionError("RU16 candidate-053 guard missing")
    if candidate_053.get("status") != "NARROW_GRAMMAR_CONTRIBUTOR_ONLY_NOT_K9_OWNER":
        raise AssertionError("RU16 candidate-053 was broadened")
    c53_rows = [obj for obj in objects if obj.get("object_key") == "semantic_candidate::candidate-053"]
    if len(c53_rows) != 1 or set(c53_rows[0].get("current_semantic_refs") or []) != {"comparison_degree_forms"}:
        raise AssertionError("RU16 candidate-053 exact narrow source truth drift")
    if c53_rows[0].get("review_status") != "needs_review":
        raise AssertionError("candidate-053 open granularity review was silently closed")

    guards = review.get("cross_boundary_guards")
    if not isinstance(guards, list) or len(guards) != 6:
        raise AssertionError("RU16 cross-boundary guard inventory drift")

    serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
    forbidden = (
        '"canonical_semantic_admissions": 1',
        '"ru_proposal_admissions": 1',
        '"status": "CANONICAL"',
        "ru-essay-language-correctness",
    )
    if any(marker in serialized for marker in forbidden):
        raise AssertionError("RU16 component review contains semantic self-admission or broad duplicate identity")

    print("RU16_ESSAY_COMPONENT_BOUNDARY_REVIEW=PASS")
    print("ROUTE_CRITERIA=10")
    print("EXPLICIT_ASSESSMENT_COMPONENTS=11")
    print("CANDIDATE_BOUND_LEARNER_COMPONENTS=7")
    print("SOURCE_VERIFIED_COMPONENTS=5")
    print("CRITERION_PROVEN_COMPONENTS=2")
    print("K7_K10_CROSS_MODULE_REUSE_DIMENSIONS=4")
    print("NEW_ESSAY_SPECIFIC_QUALITY_IDENTITIES=0")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
