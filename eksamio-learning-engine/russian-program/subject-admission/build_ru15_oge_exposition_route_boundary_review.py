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
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json"
OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
RIGHTS = HERE / "PR139-RIGHTS-BLOCKED-SALVAGE-v0.1.json"
SLICE_BUILDER = HERE / "build_launch_critical_review_slice.py"

TARGET_MODULE = "RU-PROG-15"
EXPECTED_IDS = {
    "ru-oge-exposition-microtheme-preservation",
    "ru-oge-exposition-compression-across-text",
    "ru-oge-exposition-logical-cohesion",
    "ru-oge-exposition-full-draft-verification",
}
EXPECTED_DOMAINS = {"oge_exposition", "compression", "written_response"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get(TARGET_MODULE)
    if not isinstance(module, dict):
        raise ValueError("RU15 missing from full-subject program")
    if module.get("semantic_binding_mode") != "SOURCE_BACKED_ROUTE_COMPETENCY_EXPANSION_REQUIRED":
        raise ValueError("RU15 route-competency binding mode drift")
    if module.get("candidate_refs") != []:
        raise ValueError("RU15 unexpectedly acquired draft candidate refs")
    if set(module.get("domains") or []) != EXPECTED_DOMAINS:
        raise ValueError("RU15 domain boundary drift")
    if "oge" not in set(module.get("route_relevance") or []):
        raise ValueError("RU15 lost OGE route relevance")

    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))
    task1 = [row for row in overlay.get("exam_task_map", []) if isinstance(row, dict) and row.get("task") == 1]
    if len(task1) != 1:
        raise ValueError("OGE 2026 Task-1 route row mismatch")
    task1 = task1[0]
    if task1.get("official_route") != "compressed exposition" or task1.get("classification") != "OUTSIDE_SCHOOL_DENOMINATOR":
        raise ValueError("OGE 2026 Task-1 route boundary drift")

    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    if content.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED" or content.get("module_id") != TARGET_MODULE:
        raise ValueError("RU15 content self-admitted or module drifted")
    provenance = content.get("source_provenance") or []
    if not any(isinstance(row, dict) and row.get("kind") == "official_program" and row.get("access") == "PUBLIC_OFFICIAL_PDF" for row in provenance):
        raise ValueError("RU15 lacks public official-program provenance")
    if not any(isinstance(row, dict) and row.get("kind") == "official_exam_methodology" and row.get("access") == "PUBLIC_OFFICIAL_PDF" for row in provenance):
        raise ValueError("RU15 lacks public official OGE methodology provenance")
    scoring = content.get("official_exam_scoring_overlay_2026") or {}
    if scoring.get("max_points_ik1_ik3") != 6:
        raise ValueError("RU15 OGE Task-1 IK1-IK3 score boundary drift")
    for key in ("IK1_content", "IK2_compression", "IK3_logic"):
        if (scoring.get(key) or {}).get("max_points") != 2:
            raise ValueError(f"RU15 OGE Task-1 criterion max drift: {key}")
    copyright_guard = content.get("copyright_guard") or {}
    if copyright_guard.get("official_source_passages_copied") != 0 or copyright_guard.get("practice_source_texts") != "ORIGINAL_EKSAMIO":
        raise ValueError("RU15 copyright/source-copy guard drift")

    units = content.get("units")
    if not isinstance(units, list) or len(units) != 4:
        raise ValueError("RU15 must contain exactly four bounded route learner units")
    content_ids = {str(row.get("proposed_semantic_id") or "") for row in units if isinstance(row, dict)}
    if content_ids != EXPECTED_IDS:
        raise ValueError(f"RU15 semantic set drift: {sorted(content_ids)}")
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("RU15 learner unit invalid")
        peis = unit.get("peis_evidence") or {}
        if peis.get("semantic_ref_status") != "PROPOSED_NOT_CANONICAL" or peis.get("independent_verification_required") is not True:
            raise ValueError(f"RU15 content self-admitted/verification guard missing: {unit.get('proposed_semantic_id')}")
        explanation = unit.get("canonical_explanation") or {}
        if not isinstance(explanation.get("boundaries"), list) or not explanation["boundaries"]:
            raise ValueError(f"RU15 semantic boundary missing: {unit.get('proposed_semantic_id')}")
        tutor = unit.get("tutor_grounding") or {}
        if not isinstance(tutor.get("allowed"), list) or not tutor["allowed"] or not isinstance(tutor.get("forbidden"), list) or not tutor["forbidden"]:
            raise ValueError(f"RU15 Tutor grounding boundary missing: {unit.get('proposed_semantic_id')}")
        verification = unit.get("independent_verification")
        if not isinstance(verification, list) or not verification:
            raise ValueError(f"RU15 independent verification missing: {unit.get('proposed_semantic_id')}")

    rights = json.loads(RIGHTS.read_text(encoding="utf-8"))
    decision = rights.get("decision") or {}
    if rights.get("status") != "RIGHTS_BLOCKED_SALVAGE_PINNED" or rights.get("expected_variant_count") != 5 or rights.get("expected_asset_count") != 10:
        raise ValueError("RU15 Task-1 rights-blocked salvage drift")
    if decision.get("authorship") != "NOT_PROVEN" or decision.get("production_admission") != "EXCLUDED_RIGHTS_BLOCKED":
        raise ValueError("RU15 Task-1 rights decision weakened")
    if decision.get("semantic_or_mastery_admission") is not False or decision.get("copy_assets_to_current_main_candidate") is not False:
        raise ValueError("RU15 Task-1 blocked assets were admitted")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    collisions: dict[str, list[str]] = {sid: [] for sid in EXPECTED_IDS}
    for row in inventory.get("objects", []):
        if not isinstance(row, dict) or row.get("authority_status") != "current":
            continue
        refs = {str(ref) for ref in (row.get("current_semantic_refs") or [])}
        for sid in EXPECTED_IDS & refs:
            collisions[sid].append(str(row.get("object_key") or ""))
    if any(collisions.values()):
        raise ValueError(f"RU15 proposed IDs collide with current semantic inventory: {collisions}")

    review_slice = runpy.run_path(str(SLICE_BUILDER))["build_slice"]({TARGET_MODULE})
    if review_slice.get("status") != "EXACT_REVIEW_SLICE_NOT_ADMISSION_DECISION":
        raise ValueError("RU15 official slice is not fail-closed")
    official_units = review_slice.get("admission_units")
    if not isinstance(official_units, list) or not official_units:
        raise ValueError("RU15 official review slice is empty")
    requirement_ids = sorted({str(member["requirement_id"]) for row in official_units for member in (row.get("members") or [])})

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU15_OGE_EXPOSITION_ROUTE_BOUNDARY_READY_ACCEPTANCE_NOT_ADMITTED",
        "authority_issue": 161,
        "module_id": TARGET_MODULE,
        "module_binding_mode": module["semantic_binding_mode"],
        "official_oge_task": 1,
        "official_route": "compressed exposition",
        "overlay_classification": "OUTSIDE_SCHOOL_DENOMINATOR",
        "proposed_route_semantic_ids": sorted(EXPECTED_IDS),
        "official_slice": {
            "admission_units": len(official_units),
            "unique_requirements": len(requirement_ids),
            "admission_unit_ids": sorted(str(row["admission_unit_id"]) for row in official_units),
            "requirement_ids": requirement_ids,
        },
        "rights_guard": {
            "blocked_variants": 5,
            "blocked_assets": 10,
            "authorship": "NOT_PROVEN",
            "production_admission": "EXCLUDED_RIGHTS_BLOCKED",
            "copied_assets": 0,
            "semantic_or_mastery_admission": False,
        },
        "duplicate_review": {
            "program_candidate_refs": [],
            "current_inventory_id_collisions": 0,
            "school_registry_mutation_required": False,
            "new_parallel_registry_required": False,
        },
        "policy": {
            "content_presence_implies_acceptance": False,
            "task1_score_implies_component_mastery": False,
            "generic_task1_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "route_semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
            "module_membership_implies_object_binding": False,
            "keyword_or_fuzzy_inference_allowed": False,
            "rights_blocked_assets_can_ground_content": False,
        },
        "summary": {
            "bounded_route_semantics_reviewed": 4,
            "semantic_admissions": 0,
            "object_level_admission_units_closed": 0,
            "object_level_requirements_closed": 0,
            "rights_blocked_assets_admitted": 0,
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
        print("RU15_OGE_EXPOSITION_ROUTE_BOUNDARY_REVIEW=PASS")
        print(f"OFFICIAL_ADMISSION_UNITS={result['official_slice']['admission_units']}")
        print(f"OFFICIAL_REQUIREMENTS={result['official_slice']['unique_requirements']}")
        print("PROPOSED_BOUNDED_ROUTE_SEMANTICS=4")
        print("SEMANTIC_ADMISSIONS=0")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("RIGHTS_BLOCKED_ASSETS_ADMITTED=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
