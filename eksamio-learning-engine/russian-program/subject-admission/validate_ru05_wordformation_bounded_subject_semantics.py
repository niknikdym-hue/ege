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
ACCEPTANCE = HERE / "RU05-WORDFORMATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
REVIEW_BUILDER = HERE / "build_ru05_wordformation_subject_boundary_review.py"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-05-WORD-FORMATION-WAVE-001-v0.1.json"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXPECTED_IDS = {
    "ru-wordformation-word-vs-form-building",
    "ru-wordformation-method-identification",
    "ru-wordformation-analysis-chain",
}
EXPECTED_STATUS = "CENTRAL_BRAIN_ACCEPTED_RU05_WORDFORMATION_BOUNDED_SUBJECT_SEMANTICS"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    review = runpy.run_path(str(REVIEW_BUILDER))["build_review"]()
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))

    if acceptance.get("status") != EXPECTED_STATUS:
        raise AssertionError("RU05 acceptance status drift")
    if acceptance.get("canonical_school_registry_mutated") is not False:
        raise AssertionError("RU05 acceptance mutated school registry")
    if acceptance.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU05 acceptance created a parallel registry")

    authority = acceptance.get("authority") or {}
    if authority.get("subject_program_binding_mode") != "SOURCE_BACKED_SUBJECT_EXPANSION_REQUIRED":
        raise AssertionError("RU05 authority lost source-backed expansion boundary")
    if authority.get("subject_program_candidate_refs") != []:
        raise AssertionError("RU05 authority silently reused an unrelated candidate")
    if authority.get("official_broad_domain_meaning") != review.get("official_broad_domain_meaning"):
        raise AssertionError("RU05 official broad-domain meaning drift")
    if set(authority.get("exact_broad_domain_admission_unit_ids") or []) != set(review["exact_broad_domain_admission_unit_ids"]):
        raise AssertionError("RU05 exact broad-domain admission-unit set drift")
    if set(authority.get("exact_broad_domain_requirement_ids") or []) != set(review["exact_broad_domain_requirement_ids"]):
        raise AssertionError("RU05 exact broad-domain requirement set drift")
    if authority.get("boundary_review_normalized_sha256") != review.get("normalized_sha256"):
        raise AssertionError("RU05 acceptance is not pinned to current exact boundary review")
    if authority.get("learner_content") != "russian-program/production-learning-content/RU-PROG-05-WORD-FORMATION-WAVE-001-v0.1.json":
        raise AssertionError("RU05 learner-content authority drift")

    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get("RU-PROG-05") or {}
    if module.get("semantic_binding_mode") != "SOURCE_BACKED_SUBJECT_EXPANSION_REQUIRED" or module.get("candidate_refs") != []:
        raise AssertionError("RU05 program duplicate/source-expansion boundary drift")

    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != "RU-PROG-05":
        raise AssertionError("RU05 source content was mutated to self-admit")
    units = content.get("units")
    if not isinstance(units, list) or len(units) != 3:
        raise AssertionError("RU05 learner-content unit count drift")
    units_by_id = {str(row.get("proposed_semantic_id")): row for row in units if isinstance(row, dict)}
    if set(units_by_id) != EXPECTED_IDS:
        raise AssertionError("RU05 content semantic-id set drift")
    for sid, unit in units_by_id.items():
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
            raise AssertionError(f"RU05 content self-admitted: {sid}")
        if peis.get("independent_verification_required") is not True:
            raise AssertionError(f"RU05 independent-verification guard missing: {sid}")
        explanation = unit.get("canonical_explanation") or {}
        if not isinstance(explanation.get("boundaries"), list) or not explanation["boundaries"]:
            raise AssertionError(f"RU05 component boundary missing: {sid}")
        verification = unit.get("independent_verification")
        if not isinstance(verification, list) or len(verification) < 2:
            raise AssertionError(f"RU05 independent verification content missing: {sid}")
        tutor = unit.get("tutor_grounding") or {}
        if not isinstance(tutor.get("allowed"), list) or not tutor["allowed"] or not isinstance(tutor.get("forbidden"), list) or not tutor["forbidden"]:
            raise AssertionError(f"RU05 Tutor grounding boundary missing: {sid}")

    decisions = acceptance.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 3:
        raise AssertionError("RU05 acceptance must contain exactly three decisions")
    decisions_by_id = {str(row.get("accepted_semantic_id")): row for row in decisions if isinstance(row, dict)}
    if set(decisions_by_id) != EXPECTED_IDS:
        raise AssertionError("RU05 accepted semantic-id set drift")
    for sid, decision in decisions_by_id.items():
        if decision.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            raise AssertionError(f"RU05 semantic not explicitly accepted: {sid}")
        expected_ref = f"russian-program/production-learning-content/RU-PROG-05-WORD-FORMATION-WAVE-001-v0.1.json#{sid}"
        if decision.get("content_ref") != expected_ref:
            raise AssertionError(f"RU05 content ref mismatch: {sid}")
        if len(str(decision.get("boundary_guard", "")).strip()) < 100:
            raise AssertionError(f"RU05 accepted semantic is insufficiently bounded: {sid}")

    current_refs: set[str] = set()
    for row in inventory.get("objects") or []:
        if isinstance(row, dict) and row.get("authority_status") == "current":
            current_refs.update(str(ref) for ref in (row.get("current_semantic_refs") or []))
    if EXPECTED_IDS & current_refs:
        raise AssertionError("RU05 acceptance duplicates a current inventory semantic id")

    policy = acceptance.get("policy") or {}
    required_policy = {
        "source_backed_subject_expansion_required": True,
        "content_presence_alone_implies_acceptance": False,
        "module_membership_implies_object_binding": False,
        "broad_domain_attempt_can_emit_exact_component_mastery": False,
        "component_specific_independent_evidence_required": True,
        "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        "keyword_or_fuzzy_inference_allowed": False,
        "morphemic_analysis_implies_wordformation_mastery": False,
        "school_registry_replacement_or_mutation_allowed": False,
    }
    if policy != required_policy:
        raise AssertionError(f"RU05 acceptance policy drift: {policy}")

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
        raise AssertionError(f"RU05 acceptance summary drift: {summary}")

    if len(review["exact_broad_domain_admission_unit_ids"]) != 6:
        raise AssertionError("RU05 exact broad-domain admission-unit count drift")
    if len(review["exact_broad_domain_requirement_ids"]) != 7:
        raise AssertionError("RU05 exact broad-domain requirement count drift")
    if review.get("summary", {}).get("semantic_admissions") != 0:
        raise AssertionError("RU05 review builder itself self-admitted semantics")
    if review.get("summary", {}).get("object_level_admission_units_closed") != 0:
        raise AssertionError("RU05 review builder falsely closed objects")

    print("RU05_WORDFORMATION_BOUNDED_SUBJECT_SEMANTICS=PASS")
    print("ACCEPTED_BOUNDED_SUBJECT_SEMANTICS=3")
    print("BROAD_DOMAIN_ADMISSION_UNITS=6")
    print("BROAD_DOMAIN_REQUIREMENTS=7")
    print("OBJECT_LEVEL_ADMISSION_UNITS_CLOSED=0")
    print("OBJECT_LEVEL_REQUIREMENTS_CLOSED=0")
    print("NEW_SCHOOL_CANONICAL_IDENTITIES=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("ACCEPTANCE_SHA256=" + hashlib.sha256(canonical_json(acceptance)).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
