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
CONTENT = PROGRAM / "production-learning-content/RU-PROG-07-GRAMMAR-NORMS-WAVE-002-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

TARGET_MODULE = "RU-PROG-07"
EXPECTED_CANDIDATES = {
    "candidate-025": "Нормативные формы рода, числа и падежа существительных",
    "candidate-026": "Нормативное образование и склонение числительных",
    "candidate-027": "Нормативные формы глагола, включая инфинитив и повелительное наклонение",
    "candidate-053": "Нормативные формы степеней сравнения прилагательных и наречий",
}
EXPECTED_CONTENT_IDS = {
    "ru-grammar-numeral-oblique-case",
    "ru-grammar-comparative-degree-norm",
    "ru-grammar-form-selection-common-norms",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get(TARGET_MODULE)
    if not isinstance(module, dict):
        raise ValueError("RU07 missing from full-subject program")
    if module.get("semantic_binding_mode") != "DRAFT_CANDIDATE_BINDING":
        raise ValueError("RU07 candidate-binding mode drift")
    if set(module.get("candidate_refs") or []) != set(EXPECTED_CANDIDATES):
        raise ValueError("RU07 program candidate set drift")
    if set(module.get("domains") or []) != {"morphological_norms", "grammatical_norms"}:
        raise ValueError("RU07 domain boundary drift")

    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != TARGET_MODULE:
        raise ValueError("RU07 learner content self-admitted or module drifted")
    provenance = content.get("source_provenance") or []
    if not any(isinstance(row, dict) and row.get("kind") == "official_program" and row.get("access") == "PUBLIC_OFFICIAL_PDF" for row in provenance):
        raise ValueError("RU07 lacks public official-program provenance")
    if not any(isinstance(row, dict) and row.get("kind") == "official_exam_methodology" and row.get("access") == "PUBLIC_OFFICIAL_PDF" for row in provenance):
        raise ValueError("RU07 lacks public official exam-methodology provenance")
    units = content.get("units")
    if not isinstance(units, list) or len(units) != 3:
        raise ValueError("RU07 must contain exactly three learner units")
    content_ids = {str(row.get("proposed_semantic_id", "")) for row in units if isinstance(row, dict)}
    if content_ids != EXPECTED_CONTENT_IDS:
        raise ValueError(f"RU07 proposed semantic set drift: {sorted(content_ids)}")
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("invalid RU07 learner unit")
        sid = str(unit.get("proposed_semantic_id"))
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
            raise ValueError(f"RU07 content self-admitted: {sid}")
        if peis.get("independent_verification_required") is not True:
            raise ValueError(f"RU07 independent-verification guard missing: {sid}")
        verification = unit.get("independent_verification")
        if not isinstance(verification, list) or len(verification) < 2:
            raise ValueError(f"RU07 independent verification missing: {sid}")
        tutor = unit.get("tutor_grounding") or {}
        if not isinstance(tutor.get("allowed"), list) or not tutor["allowed"] or not isinstance(tutor.get("forbidden"), list) or not tutor["forbidden"]:
            raise ValueError(f"RU07 Tutor grounding boundary missing: {sid}")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = inventory.get("objects")
    if not isinstance(objects, list):
        raise ValueError("semantic inventory objects missing")

    candidate_rows: dict[str, dict[str, Any]] = {}
    current_refs: set[str] = set()
    proposed_collisions: dict[str, list[str]] = {sid: [] for sid in EXPECTED_CONTENT_IDS}
    for row in objects:
        if not isinstance(row, dict) or row.get("authority_status") != "current":
            continue
        refs = {str(ref) for ref in (row.get("current_semantic_refs") or [])}
        current_refs.update(refs)
        for sid in EXPECTED_CONTENT_IDS & refs:
            proposed_collisions[sid].append(str(row.get("object_key")))
        if row.get("source_system") == "semantic_candidate" and row.get("source_id") in EXPECTED_CANDIDATES:
            candidate_id = str(row["source_id"])
            if candidate_id in candidate_rows:
                raise ValueError(f"duplicate current RU07 candidate row: {candidate_id}")
            candidate_rows[candidate_id] = row

    if any(proposed_collisions.values()):
        raise ValueError(f"RU07 proposed id collides with current semantic inventory: {proposed_collisions}")
    if set(candidate_rows) != set(EXPECTED_CANDIDATES):
        raise ValueError("RU07 current candidate inventory incomplete")

    candidate_snapshot: list[dict[str, Any]] = []
    for candidate_id in sorted(EXPECTED_CANDIDATES):
        row = candidate_rows[candidate_id]
        if row.get("candidate_canonical_owner") != candidate_id:
            raise ValueError(f"RU07 candidate owner drift: {candidate_id}")
        if row.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise ValueError(f"RU07 candidate classification drift: {candidate_id}")
        if row.get("review_status") != "draft":
            raise ValueError(f"RU07 candidate unexpectedly ceased to be draft: {candidate_id}")
        if row.get("observed_label") != EXPECTED_CANDIDATES[candidate_id]:
            raise ValueError(f"RU07 candidate observed-label drift: {candidate_id}")
        refs = [str(ref) for ref in (row.get("current_semantic_refs") or [])]
        if not refs:
            raise ValueError(f"RU07 candidate lacks source semantic refs: {candidate_id}")
        candidate_snapshot.append({
            "candidate_ref": candidate_id,
            "observed_label": str(row.get("observed_label")),
            "observed_meaning": str(row.get("observed_meaning")),
            "current_semantic_refs": refs,
            "review_status": str(row.get("review_status")),
            "provenance_refs": list(row.get("evidence_provenance_refs") or []),
        })

    relation_decisions = [
        {
            "candidate_ref": "candidate-026",
            "content_semantic_id": "ru-grammar-numeral-oblique-case",
            "relation": "CONTENT_IS_BOUNDED_SUBSET_OF_DRAFT_CANDIDATE",
            "acceptance_effect": "NONE",
            "reason": "The content unit is specifically about numeral inflection in oblique cases, while the draft candidate owns the broader normative formation and declension of numerals; subset evidence cannot silently admit the broader candidate or claim exact equivalence.",
        },
        {
            "candidate_ref": "candidate-053",
            "content_semantic_id": "ru-grammar-comparative-degree-norm",
            "relation": "MEANING_ALIGNMENT_CANDIDATE_EXACT_ACCEPTANCE_REVIEW_REQUIRED",
            "acceptance_effect": "NONE",
            "reason": "The draft candidate explicitly names normative comparative-degree forms, but candidate refs are not canonical ids; exact semantic admission requires a separate acceptance authority bound to source evidence and the content boundary.",
        },
        {
            "candidate_ref": "candidate-025+candidate-027+other_RU07_norm_families",
            "content_semantic_id": "ru-grammar-form-selection-common-norms",
            "relation": "COMPOSITE_CROSS_CANDIDATE_CONTENT_NO_SINGLE_EXACT_OWNER",
            "acceptance_effect": "NONE",
            "reason": "The common form-selection procedure spans noun, verb and other norm-sensitive forms; no single draft candidate can be promoted as its exact owner from module membership or examples alone.",
        },
    ]

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU07_GRAMMAR_NORMS_REUSE_FIRST_BOUNDARY_REVIEW_ACCEPTANCE_NOT_ADMITTED",
        "authority_issue": 161,
        "module_id": TARGET_MODULE,
        "module_binding_mode": str(module["semantic_binding_mode"]),
        "program_candidate_refs": sorted(EXPECTED_CANDIDATES),
        "proposed_subject_semantic_ids": sorted(EXPECTED_CONTENT_IDS),
        "candidate_inventory_snapshot": candidate_snapshot,
        "candidate_relation_decisions": relation_decisions,
        "reuse_review": {
            "current_proposed_id_collisions": 0,
            "exact_existing_owner_reuses_admitted": 0,
            "meaning_alignment_candidates_requiring_separate_acceptance": 1,
            "bounded_subset_relations": 1,
            "composite_no_single_owner_relations": 1,
            "school_registry_mutation_required": False,
            "new_parallel_registry_required": False,
        },
        "policy": {
            "reuse_first": True,
            "candidate_ref_is_canonical_id": False,
            "content_presence_implies_acceptance": False,
            "module_membership_implies_exact_owner": False,
            "subset_evidence_can_admit_broader_candidate": False,
            "composite_content_can_emit_single_candidate_mastery": False,
            "candidate_alignment_requires_explicit_acceptance_authority": True,
            "component_specific_independent_evidence_required": True,
            "semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
            "keyword_or_fuzzy_inference_allowed": False,
        },
        "summary": {
            "draft_candidates_reviewed": 4,
            "content_semantics_reviewed": 3,
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
        print("RU07_GRAMMAR_NORMS_REUSE_FIRST_BOUNDARY_REVIEW=PASS")
        print("DRAFT_CANDIDATES_REVIEWED=4")
        print("CONTENT_SEMANTICS_REVIEWED=3")
        print("EXACT_EXISTING_OWNER_REUSES_ADMITTED=0")
        print("MEANING_ALIGNMENT_CANDIDATES_REQUIRING_SEPARATE_ACCEPTANCE=1")
        print("BOUNDED_SUBSET_RELATIONS=1")
        print("COMPOSITE_NO_SINGLE_OWNER_RELATIONS=1")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
