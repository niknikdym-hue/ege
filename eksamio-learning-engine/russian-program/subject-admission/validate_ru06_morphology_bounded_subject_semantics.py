#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ACCEPTANCE = HERE / "RU06-MORPHOLOGY-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
REVIEW_BUILDER = HERE / "build_ru06_morphology_subject_boundary_review.py"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-06-MORPHOLOGY-WAVE-002-v0.1.json"

EXPECTED_IDS = {
    "ru-morphology-part-of-speech-identification",
    "ru-morphology-permanent-variable-features",
    "ru-morphology-analysis-sequence",
}
EXPECTED_REVIEW_SHA = "a327e34d3ca2a10d82cc4c9a7d0f7b86ea76f00c66af042af6b67f04c6b6b9a7"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    review = runpy.run_path(str(REVIEW_BUILDER))["build_review"]()
    content = json.loads(CONTENT.read_text(encoding="utf-8"))

    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU06_MORPHOLOGY_BOUNDED_SUBJECT_SEMANTICS":
        raise AssertionError("RU06 acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False or acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU06 acceptance must remain an overlay")

    authority = acceptance.get("authority") or {}
    if authority.get("subject_program_binding_mode") != "MIXED_EXISTING_AND_EXPANSION_BINDING":
        raise AssertionError("RU06 program binding-mode drift")
    if authority.get("subject_program_candidate_refs") != []:
        raise AssertionError("RU06 acceptance unexpectedly claims candidate refs")
    if authority.get("official_broad_domain_meaning") != "Распознавать части речи и их грамматические признаки.":
        raise AssertionError("RU06 official broad meaning drift")
    if authority.get("exact_broad_domain_admission_units") != 172 or authority.get("exact_broad_domain_requirements") != 178:
        raise AssertionError("RU06 broad-domain counts drift")
    if authority.get("boundary_review_normalized_sha256") != EXPECTED_REVIEW_SHA:
        raise AssertionError("RU06 pinned boundary-review SHA drift")
    if review.get("normalized_sha256") != EXPECTED_REVIEW_SHA:
        raise AssertionError("RU06 live boundary review no longer matches accepted authority")
    if len(review.get("exact_broad_domain_admission_unit_ids") or []) != 172:
        raise AssertionError("RU06 live admission-unit count drift")
    if len(review.get("exact_broad_domain_requirement_ids") or []) != 178:
        raise AssertionError("RU06 live requirement count drift")
    if set(review.get("proposed_subject_semantic_ids") or []) != EXPECTED_IDS:
        raise AssertionError("RU06 reviewed semantic set drift")

    reuse = review.get("reuse_review") or {}
    if reuse.get("current_inventory_id_collisions") != 0:
        raise AssertionError("RU06 accepted semantic id collides with current inventory")
    if reuse.get("school_registry_mutation_required") is not False or reuse.get("new_parallel_registry_required") is not False:
        raise AssertionError("RU06 review now requires registry mutation/parallel registry")
    if reuse.get("decision") != authority.get("reuse_decision"):
        raise AssertionError("RU06 reuse decision drift")

    policy = acceptance.get("policy") or {}
    required_false = (
        "content_presence_alone_implies_acceptance",
        "module_membership_implies_object_binding",
        "broad_domain_attempt_can_emit_exact_component_mastery",
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "keyword_or_fuzzy_inference_allowed",
        "morphology_mastery_implies_morphological_norm_mastery",
        "morphology_mastery_implies_orthography_mastery",
        "school_registry_replacement_or_mutation_allowed",
    )
    if any(policy.get(key) is not False for key in required_false):
        raise AssertionError("RU06 fail-closed policy weakened")
    if policy.get("reuse_first") is not True or policy.get("component_specific_independent_evidence_required") is not True:
        raise AssertionError("RU06 reuse/evidence guard missing")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 3:
        raise AssertionError("RU06 acceptance must contain exactly three decisions")
    decision_by_id = {str(row.get("accepted_semantic_id")): row for row in decisions if isinstance(row, dict)}
    if set(decision_by_id) != EXPECTED_IDS:
        raise AssertionError("RU06 accepted semantic set drift")
    if any(row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC" for row in decisions):
        raise AssertionError("RU06 decision not explicitly accepted")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-06":
        raise AssertionError("RU06 learner content self-admitted or module drifted")
    units = content.get("units")
    if not isinstance(units, list) or len(units) != 3:
        raise AssertionError("RU06 learner content unit count drift")
    units_by_id = {str(row.get("proposed_semantic_id")): row for row in units if isinstance(row, dict)}
    if set(units_by_id) != EXPECTED_IDS:
        raise AssertionError("RU06 content semantic set drift")

    for sid in sorted(EXPECTED_IDS):
        decision = decision_by_id[sid]
        unit = units_by_id[sid]
        expected_ref = f"russian-program/production-learning-content/RU-PROG-06-MORPHOLOGY-WAVE-002-v0.1.json#{sid}"
        if decision.get("content_ref") != expected_ref:
            raise AssertionError(f"RU06 content ref mismatch: {sid}")
        if len(str(decision.get("boundary_guard", "")).strip()) < 120:
            raise AssertionError(f"RU06 decision boundary too weak: {sid}")
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
            raise AssertionError(f"RU06 source content was mutated to self-admit: {sid}")
        if peis.get("independent_verification_required") is not True:
            raise AssertionError(f"RU06 independent verification weakened: {sid}")
        verification = unit.get("independent_verification")
        if not isinstance(verification, list) or len(verification) < 2:
            raise AssertionError(f"RU06 independent verification missing: {sid}")
        tutor = unit.get("tutor_grounding") or {}
        if not tutor.get("allowed") or not tutor.get("forbidden"):
            raise AssertionError(f"RU06 Tutor grounding boundary missing: {sid}")

    summary = acceptance.get("summary") or {}
    expected_summary = {
        "accepted_bounded_subject_semantics": 3,
        "accepted_ru_subject_semantics": 3,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise AssertionError(f"RU06 acceptance summary drift: {summary}")

    print("RU06_MORPHOLOGY_BOUNDED_SUBJECT_SEMANTICS=PASS")
    print("ACCEPTED_BOUNDED_SUBJECT_SEMANTICS=3")
    print("EXACT_BROAD_DOMAIN_ADMISSION_UNITS=172")
    print("EXACT_BROAD_DOMAIN_REQUIREMENTS=178")
    print("OBJECT_LEVEL_ADMISSION_UNITS_CLOSED=0")
    print("OBJECT_LEVEL_REQUIREMENTS_CLOSED=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("ACCEPTANCE_SHA256=" + hashlib.sha256(canonical_json(acceptance)).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
