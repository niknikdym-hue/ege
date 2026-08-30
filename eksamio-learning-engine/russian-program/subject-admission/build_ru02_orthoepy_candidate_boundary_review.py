#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-02-ORTHOEPY-STRESS-WAVE-002-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

TARGET_MODULE = "RU-PROG-02"
EXPECTED_CANDIDATES = {
    "candidate-018": "Определение нормативной позиции ударения",
    "candidate-019": "Ударение в существительных и их формах",
    "candidate-020": "Ударение в прилагательных, кратких формах и степенях сравнения",
    "candidate-021": "Ударение в глаголах и личных/родовых формах",
    "candidate-022": "Ударение в причастиях и кратких причастиях",
    "candidate-023": "Ударение в деепричастиях",
    "candidate-024": "Ударение в наречиях",
}
EXPECTED_CONTENT_IDS = {
    "ru-orthoepy-stress-form-sensitive",
    "ru-orthoepy-norm-source-check",
}
ALLOWED_CANDIDATE_REVIEW_STATES = {"draft", "needs_review"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get(TARGET_MODULE)
    if not isinstance(module, dict):
        raise ValueError("RU02 missing from full-subject program")
    if module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING":
        raise ValueError("RU02 candidate-binding mode drift")
    if set(module.get("candidate_refs") or []) != set(EXPECTED_CANDIDATES):
        raise ValueError("RU02 program candidate set drift")
    if set(module.get("domains") or []) != {"orthoepy", "stress"}:
        raise ValueError("RU02 domain boundary drift")

    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != TARGET_MODULE:
        raise ValueError("RU02 learner content self-admitted or module drifted")
    provenance = content.get("source_provenance") or []
    if not any(isinstance(row, dict) and row.get("kind") == "official_program" and row.get("access") == "PUBLIC_OFFICIAL_PDF" for row in provenance):
        raise ValueError("RU02 lacks public official-program provenance")
    if not any(isinstance(row, dict) and row.get("kind") == "official_exam_methodology" and row.get("access") == "PUBLIC_OFFICIAL_PDF" for row in provenance):
        raise ValueError("RU02 lacks public official exam-methodology provenance")
    units = content.get("units")
    if not isinstance(units, list) or len(units) != 2:
        raise ValueError("RU02 must contain exactly two learner units")
    content_ids = {str(row.get("proposed_semantic_id", "")) for row in units if isinstance(row, dict)}
    if content_ids != EXPECTED_CONTENT_IDS:
        raise ValueError(f"RU02 proposed semantic set drift: {sorted(content_ids)}")
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("invalid RU02 learner unit")
        sid = str(unit.get("proposed_semantic_id"))
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
            raise ValueError(f"RU02 content self-admitted: {sid}")
        if peis.get("independent_verification_required") is not True:
            raise ValueError(f"RU02 independent-verification guard missing: {sid}")
        verification = unit.get("independent_verification")
        if not isinstance(verification, list) or len(verification) < 2:
            raise ValueError(f"RU02 independent verification missing: {sid}")
        tutor = unit.get("tutor_grounding") or {}
        if not isinstance(tutor.get("allowed"), list) or not tutor["allowed"] or not isinstance(tutor.get("forbidden"), list) or not tutor["forbidden"]:
            raise ValueError(f"RU02 Tutor grounding boundary missing: {sid}")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = inventory.get("objects")
    if not isinstance(objects, list):
        raise ValueError("semantic inventory objects missing")

    candidate_rows: dict[str, dict[str, Any]] = {}
    proposed_collisions: dict[str, list[str]] = {sid: [] for sid in EXPECTED_CONTENT_IDS}
    for row in objects:
        if not isinstance(row, dict) or row.get("authority_status") != "current":
            continue
        refs = {str(ref) for ref in (row.get("current_semantic_refs") or [])}
        for sid in EXPECTED_CONTENT_IDS & refs:
            proposed_collisions[sid].append(str(row.get("object_key")))
        if row.get("source_system") == "semantic_candidate" and row.get("source_id") in EXPECTED_CANDIDATES:
            candidate_id = str(row["source_id"])
            if candidate_id in candidate_rows:
                raise ValueError(f"duplicate current RU02 candidate row: {candidate_id}")
            candidate_rows[candidate_id] = row

    if any(proposed_collisions.values()):
        raise ValueError(f"RU02 proposed id collides with current semantic inventory: {proposed_collisions}")
    if set(candidate_rows) != set(EXPECTED_CANDIDATES):
        raise ValueError("RU02 current candidate inventory incomplete")

    candidate_snapshot: list[dict[str, Any]] = []
    status_counts = {status: 0 for status in sorted(ALLOWED_CANDIDATE_REVIEW_STATES)}
    for candidate_id in sorted(EXPECTED_CANDIDATES):
        row = candidate_rows[candidate_id]
        if row.get("candidate_canonical_owner") != candidate_id:
            raise ValueError(f"RU02 candidate owner drift: {candidate_id}")
        if row.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise ValueError(f"RU02 candidate classification drift: {candidate_id}")
        review_status = str(row.get("review_status"))
        if review_status not in ALLOWED_CANDIDATE_REVIEW_STATES:
            raise ValueError(f"RU02 candidate has unsupported review state {review_status}: {candidate_id}")
        status_counts[review_status] += 1
        if row.get("observed_label") != EXPECTED_CANDIDATES[candidate_id]:
            raise ValueError(f"RU02 candidate observed-label drift: {candidate_id}")
        refs = [str(ref) for ref in (row.get("current_semantic_refs") or [])]
        if not refs:
            raise ValueError(f"RU02 candidate lacks source semantic refs: {candidate_id}")
        candidate_snapshot.append({
            "candidate_ref": candidate_id,
            "observed_label": str(row.get("observed_label")),
            "observed_meaning": str(row.get("observed_meaning")),
            "current_semantic_refs": refs,
            "review_status": review_status,
            "provenance_refs": list(row.get("evidence_provenance_refs") or []),
        })

    relation_decisions = [
        {
            "candidate_ref": "candidate-018+candidate-021",
            "content_semantic_id": "ru-orthoepy-stress-form-sensitive",
            "relation": "FORM_SENSITIVE_GENERIC_STRESS_WITH_VERB_EXAMPLE_OVERLAP_NO_EXACT_OWNER",
            "acceptance_effect": "NONE",
            "reason": "The learner unit teaches the cross-cutting operation 'identify the exact form, then verify its normative stress'. Its worked and independent normative-form examples are verb forms, so it overlaps the generic stress-selection candidate and the verb-form candidate only. It does not prove the full identity of either candidate and provides no direct noun, adjectival, participial, gerund or adverb component coverage.",
            "no_direct_content_evidence_for_candidate_refs": [
                "candidate-019",
                "candidate-020",
                "candidate-022",
                "candidate-023",
                "candidate-024",
            ],
        },
        {
            "candidate_ref": "none_exact",
            "content_semantic_id": "ru-orthoepy-norm-source-check",
            "relation": "SOURCE_VERIFICATION_PROCEDURE_NO_EXACT_DRAFT_CANDIDATE_OWNER",
            "acceptance_effect": "NONE",
            "reason": "The unit is a fail-closed normative-source verification procedure. The seven RU02 draft candidates describe stress-selection subject targets, not the meta-procedure of checking an uncertain norm, so module co-location cannot create an exact owner relation.",
        },
    ]

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU02_ORTHOEPY_REUSE_FIRST_BOUNDARY_REVIEW_ACCEPTANCE_NOT_ADMITTED",
        "authority_issue": 161,
        "module_id": TARGET_MODULE,
        "module_binding_mode": str(module["semantic_binding_mode"]),
        "program_candidate_refs": sorted(EXPECTED_CANDIDATES),
        "proposed_subject_semantic_ids": sorted(EXPECTED_CONTENT_IDS),
        "candidate_inventory_snapshot": candidate_snapshot,
        "candidate_review_status_counts": status_counts,
        "candidate_relation_decisions": relation_decisions,
        "reuse_review": {
            "current_proposed_id_collisions": 0,
            "exact_existing_owner_reuses_admitted": 0,
            "cross_candidate_content_relations": 1,
            "source_verification_procedure_relations": 1,
            "exact_candidate_equivalence_proven": 0,
            "school_registry_mutation_required": False,
            "new_parallel_registry_required": False,
        },
        "next_exact_work": {
            "draft_candidates_requiring_source_identity_resolution": 7,
            "content_units_requiring_exact_candidate_adequacy_review": 2,
            "candidate_level_content_gap_may_be_declared_without_separate_review": False,
        },
        "policy": {
            "reuse_first": True,
            "candidate_ref_is_canonical_id": False,
            "content_presence_implies_acceptance": False,
            "module_membership_implies_exact_owner": False,
            "cross_cutting_content_can_admit_granular_candidates": False,
            "source_check_procedure_can_substitute_for_subject_component": False,
            "component_specific_independent_evidence_required": True,
            "semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
            "keyword_or_fuzzy_inference_allowed": False,
        },
        "summary": {
            "candidate_records_reviewed": 7,
            "content_semantics_reviewed": 2,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "false_exact_mastery_admissions": 0,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_review()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU02_ORTHOEPY_REUSE_FIRST_BOUNDARY_REVIEW=PASS")
        print("CANDIDATE_RECORDS_REVIEWED=7")
        print("CONTENT_SEMANTICS_REVIEWED=2")
        print("DRAFT_CANDIDATE_RECORDS=" + str(result["candidate_review_status_counts"].get("draft", 0)))
        print("NEEDS_REVIEW_CANDIDATE_RECORDS=" + str(result["candidate_review_status_counts"].get("needs_review", 0)))
        print("EXACT_EXISTING_OWNER_REUSES_ADMITTED=0")
        print("EXACT_CANDIDATE_EQUIVALENCE_PROVEN=0")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
