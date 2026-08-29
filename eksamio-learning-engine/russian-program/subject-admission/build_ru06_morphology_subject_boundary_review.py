#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
SLICE_BUILDER = HERE / "build_launch_critical_review_slice.py"
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-06-MORPHOLOGY-WAVE-002-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
SKILL_GRAPH = ENGINE / "03-RUSSIAN-SKILL-GRAPH.json"

TARGET_MODULE = "RU-PROG-06"
BROAD_MEANING = "Распознавать части речи и их грамматические признаки."
EXPECTED_IDS = {
    "ru-morphology-part-of-speech-identification",
    "ru-morphology-permanent-variable-features",
    "ru-morphology-analysis-sequence",
}
RELATED_EXISTING_REFS = {
    "morphological_norms",
    "noun_form_norms",
    "numeral_form_norms",
    "verb_form_norms",
    "orthographic_norms",
    "suffix_spelling_by_part_of_speech",
    "ne_contextual_spelling",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get(TARGET_MODULE)
    if not isinstance(module, dict):
        raise ValueError("RU06 missing from full-subject program")
    if module.get("semantic_binding_mode") != "MIXED_EXISTING_AND_EXPANSION_BINDING":
        raise ValueError("RU06 mixed reuse/expansion boundary drift")
    if module.get("candidate_refs") != []:
        raise ValueError("RU06 unexpectedly acquired candidate refs; exact owner review required")
    if set(module.get("domains") or []) != {"morphology", "parts_of_speech"}:
        raise ValueError("RU06 domain boundary drift")

    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != TARGET_MODULE:
        raise ValueError("RU06 learner content self-admitted or module drifted")
    provenance = content.get("source_provenance") or []
    if not any(
        isinstance(row, dict)
        and row.get("kind") == "official_program"
        and row.get("access") == "PUBLIC_OFFICIAL_PDF"
        for row in provenance
    ):
        raise ValueError("RU06 lacks public official-program provenance")
    units = content.get("units")
    if not isinstance(units, list) or len(units) != 3:
        raise ValueError("RU06 must contain exactly three bounded learner units")
    content_ids = {str(row.get("proposed_semantic_id", "")) for row in units if isinstance(row, dict)}
    if content_ids != EXPECTED_IDS:
        raise ValueError(f"RU06 proposed semantic set drift: {sorted(content_ids)}")
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("invalid RU06 learner unit")
        sid = str(unit.get("proposed_semantic_id"))
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL":
            raise ValueError(f"RU06 content self-admitted: {sid}")
        if peis.get("independent_verification_required") is not True:
            raise ValueError(f"RU06 independent-verification guard missing: {sid}")
        explanation = unit.get("canonical_explanation") or {}
        if not isinstance(explanation.get("boundaries"), list) or not explanation["boundaries"]:
            raise ValueError(f"RU06 semantic boundary missing: {sid}")
        verification = unit.get("independent_verification")
        if not isinstance(verification, list) or len(verification) < 2:
            raise ValueError(f"RU06 independent verification missing: {sid}")
        tutor = unit.get("tutor_grounding") or {}
        if not isinstance(tutor.get("allowed"), list) or not tutor["allowed"] or not isinstance(tutor.get("forbidden"), list) or not tutor["forbidden"]:
            raise ValueError(f"RU06 Tutor grounding boundary missing: {sid}")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    inventory_objects = inventory.get("objects")
    if not isinstance(inventory_objects, list):
        raise ValueError("semantic inventory objects missing")
    id_collisions: dict[str, list[str]] = {sid: [] for sid in EXPECTED_IDS}
    related_rows: list[dict[str, Any]] = []
    for row in inventory_objects:
        if not isinstance(row, dict) or row.get("authority_status") != "current":
            continue
        refs = {str(ref) for ref in (row.get("current_semantic_refs") or [])}
        for sid in EXPECTED_IDS & refs:
            id_collisions[sid].append(str(row.get("object_key")))
        hit = sorted(refs & RELATED_EXISTING_REFS)
        if hit and row.get("source_system") in {"ege_skill_graph", "semantic_candidate"}:
            related_rows.append({
                "object_key": str(row.get("object_key")),
                "source_system": str(row.get("source_system")),
                "source_id": str(row.get("source_id")),
                "observed_label": str(row.get("observed_label")),
                "observed_meaning": str(row.get("observed_meaning")),
                "current_semantic_refs": sorted(refs),
                "audit_classification": str(row.get("audit_classification")),
                "review_status": str(row.get("review_status")),
            })
    if any(id_collisions.values()):
        raise ValueError(f"RU06 proposed id collides with current semantic inventory: {id_collisions}")

    skill_graph = json.loads(SKILL_GRAPH.read_text(encoding="utf-8"))
    graph_by_id = {str(row.get("skill_id")): row for row in skill_graph.get("skills", []) if isinstance(row, dict)}
    morph_norms = graph_by_id.get("morphological_norms")
    if not isinstance(morph_norms, dict) or morph_norms.get("evidence_status") != "confirmed":
        raise ValueError("current morphological_norms taxonomy node missing")
    if morph_norms.get("description") != "Образование нормативных грамматических форм слов разных частей речи.":
        raise ValueError("morphological_norms meaning drift; reuse decision must be revisited")
    for ref in ("noun_form_norms", "numeral_form_norms", "verb_form_norms"):
        row = graph_by_id.get(ref)
        if not isinstance(row, dict) or row.get("evidence_status") != "confirmed":
            raise ValueError(f"expected current norm taxonomy node missing: {ref}")

    namespace = runpy.run_path(str(SLICE_BUILDER))
    review_slice = namespace["build_slice"]({TARGET_MODULE})
    exact_units = [
        row
        for row in review_slice.get("admission_units", [])
        if row.get("normalized_meaning") == BROAD_MEANING and TARGET_MODULE in set(row.get("modules") or [])
    ]
    if not exact_units:
        raise ValueError("RU06 exact broad-domain official rows missing")
    if any(row.get("admission_status") != "SUBJECT_REVIEW_REQUIRED" for row in exact_units):
        raise ValueError("RU06 broad-domain rows unexpectedly auto-admitted")
    requirement_ids = sorted(
        str(member["requirement_id"])
        for row in exact_units
        for member in (row.get("members") or [])
    )
    admission_unit_ids = sorted(str(row["admission_unit_id"]) for row in exact_units)

    related_rows.sort(key=lambda row: row["object_key"])
    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU06_MORPHOLOGY_REUSE_FIRST_BOUNDARY_READY_ACCEPTANCE_NOT_ADMITTED",
        "authority_issue": 161,
        "module_id": TARGET_MODULE,
        "module_binding_mode": module["semantic_binding_mode"],
        "official_broad_domain_meaning": BROAD_MEANING,
        "exact_broad_domain_admission_unit_ids": admission_unit_ids,
        "exact_broad_domain_requirement_ids": requirement_ids,
        "exact_broad_domain_rows": exact_units,
        "proposed_subject_semantic_ids": sorted(EXPECTED_IDS),
        "reuse_review": {
            "program_candidate_refs": [],
            "current_inventory_id_collisions": 0,
            "related_existing_semantic_refs_reviewed": sorted(RELATED_EXISTING_REFS),
            "related_existing_inventory_rows": related_rows,
            "decision": "EXISTING_EGE_NORM_OR_ORTHOGRAPHY_REFS_ARE_RELATED_PREREQUISITE_OR_DOWNSTREAM_SEMANTICS_NOT_EXACT_OWNERS_OF_THE_THREE_RU06_DECISIONS",
            "morphological_norms_boundary": "normative form production/correction; not generic part-of-speech identification, stable-vs-form-dependent feature classification, or the complete morphology-analysis sequence",
            "orthography_boundary": "part-of-speech recognition may be prerequisite evidence for spelling rules but does not make orthographic semantics owners of morphology mastery",
            "school_registry_mutation_required": False,
            "new_parallel_registry_required": False,
        },
        "policy": {
            "reuse_first": True,
            "content_presence_implies_acceptance": False,
            "module_membership_implies_object_binding": False,
            "broad_domain_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
            "keyword_or_fuzzy_inference_allowed": False,
            "morphology_mastery_implies_morphological_norm_mastery": False,
            "morphology_mastery_implies_orthography_mastery": False,
        },
        "summary": {
            "bounded_semantics_reviewed": 3,
            "exact_existing_owner_reuses_for_proposed_ids": 0,
            "related_existing_semantic_families_reviewed": len(RELATED_EXISTING_REFS),
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
        print("RU06_MORPHOLOGY_REUSE_FIRST_BOUNDARY_REVIEW=PASS")
        print(f"EXACT_BROAD_DOMAIN_ADMISSION_UNITS={len(result['exact_broad_domain_admission_unit_ids'])}")
        print(f"EXACT_BROAD_DOMAIN_REQUIREMENTS={len(result['exact_broad_domain_requirement_ids'])}")
        print("PROPOSED_BOUNDED_SEMANTICS=3")
        print("EXACT_EXISTING_OWNER_REUSES=0")
        print(f"RELATED_EXISTING_SEMANTIC_FAMILIES_REVIEWED={result['summary']['related_existing_semantic_families_reviewed']}")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
        print("ADMISSION_UNIT_IDS=" + ",".join(result["exact_broad_domain_admission_unit_ids"]))
        print("REQUIREMENT_IDS=" + ",".join(result["exact_broad_domain_requirement_ids"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
