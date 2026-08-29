#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
SLICE_BUILDER = HERE / "build_launch_critical_review_slice.py"
REUSE_POOL_BUILDER = HERE / "build_ru08_09_10_14_reuse_pool.py"
PROGRESS_BUILDER = HERE / "build_russian_semantic_acceptance_progress.py"

TARGET_MODULE = "RU-PROG-08"
EXPECTED_BINDING_MODE = "CANONICAL_185_SCHOOL_SET_CROSSWALK_BINDING"
EXPECTED_DOMAIN = "orthography"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get(TARGET_MODULE)
    if not isinstance(module, dict):
        raise ValueError("RU08 missing from full-subject program")
    if module.get("semantic_binding_mode") != EXPECTED_BINDING_MODE:
        raise ValueError("RU08 canonical-school binding mode drift")
    if module.get("candidate_refs") != []:
        raise ValueError("RU08 unexpectedly acquired draft candidate refs")
    if set(module.get("domains") or []) != {EXPECTED_DOMAIN}:
        raise ValueError("RU08 domain boundary drift")

    reuse_pool = runpy.run_path(str(REUSE_POOL_BUILDER))["main_payload"]()
    if reuse_pool.get("status") != "REUSE_POOL_READY_NOT_COVERAGE_AUTHORITY":
        raise ValueError("RU08 reuse pool status drift")
    if TARGET_MODULE not in set(reuse_pool.get("target_modules") or []):
        raise ValueError("RU08 missing from reuse-pool target modules")
    school_pool = reuse_pool.get("canonical_school_pool") or {}
    practice_pool = reuse_pool.get("reviewed_exception_practice_pool") or {}
    if school_pool.get("count") != 185:
        raise ValueError("RU08 requires the frozen 185-school canonical reuse pool")
    if practice_pool.get("count") != 121:
        raise ValueError("RU08 reviewed exception-practice pool drift")
    invariants = reuse_pool.get("invariants") or {}
    if invariants.get("asset_presence_equals_requirement_coverage") is not False:
        raise ValueError("asset presence may not imply RU08 requirement coverage")
    if invariants.get("canonical_or_admitted_identity_requires_exact_object_mapping_for_coverage") is not True:
        raise ValueError("RU08 exact object mapping guard missing")
    if invariants.get("new_content_allowed_before_reuse_check") is not False:
        raise ValueError("RU08 must remain reuse-first")

    review_slice = runpy.run_path(str(SLICE_BUILDER))["build_slice"]({TARGET_MODULE})
    if review_slice.get("status") != "EXACT_REVIEW_SLICE_NOT_ADMISSION_DECISION":
        raise ValueError("RU08 review slice is not fail-closed")
    if review_slice.get("target_modules") != [TARGET_MODULE]:
        raise ValueError("RU08 review slice target drift")
    units = review_slice.get("admission_units")
    if not isinstance(units, list) or not units:
        raise ValueError("RU08 official review universe is empty")
    if any(TARGET_MODULE not in set(row.get("modules") or []) for row in units):
        raise ValueError("RU08 review slice contains a non-RU08 unit")

    progress = runpy.run_path(str(PROGRESS_BUILDER))["build_progress"]()
    if progress.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS":
        raise ValueError("global Russian semantic progress status drift")
    if progress.get("russian_content_ready") is not False:
        raise ValueError("global Russian content unexpectedly ready")

    accepted_by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in progress.get("semantic_review_groups") or []:
        if not isinstance(group, dict):
            continue
        for accepted in group.get("accepted_component_sets") or []:
            if not isinstance(accepted, dict):
                continue
            unit_id = str(accepted.get("admission_unit_id") or "")
            if unit_id:
                accepted_by_unit[unit_id].append(accepted)

    reviewed_units: list[dict[str, Any]] = []
    pending_meanings: dict[str, dict[str, Any]] = {}
    accepted_unit_ids: set[str] = set()
    accepted_requirement_ids: set[str] = set()
    accepted_refs: set[str] = set()
    requirement_ids: set[str] = set()

    for row in units:
        unit_id = str(row["admission_unit_id"])
        members = row.get("members") or []
        member_ids = [str(member["requirement_id"]) for member in members]
        requirement_ids.update(member_ids)
        accepted_sets = accepted_by_unit.get(unit_id, [])
        if len(accepted_sets) > 1:
            raise ValueError(f"RU08 unit has overlapping accepted component sets: {unit_id}")
        if accepted_sets:
            accepted = accepted_sets[0]
            if str(accepted.get("requirement_id")) not in set(member_ids):
                raise ValueError(f"RU08 accepted requirement is not a member of its unit: {unit_id}")
            refs = [str(ref) for ref in (accepted.get("canonical_component_refs") or [])]
            if not refs or any(not ref.startswith("school-") for ref in refs):
                raise ValueError(f"RU08 accepted object set is not canonical-school reuse: {unit_id}")
            accepted_unit_ids.add(unit_id)
            accepted_requirement_ids.add(str(accepted["requirement_id"]))
            accepted_refs.update(refs)
            disposition = "EXACT_OBJECT_BOUND_CANONICAL_REUSE_ALREADY_ACCEPTED"
        else:
            disposition = "PENDING_EXACT_REUSE_REVIEW"
            meaning = str(row.get("normalized_meaning") or "")
            bucket = pending_meanings.setdefault(
                meaning,
                {
                    "normalized_meaning": meaning,
                    "admission_unit_ids": [],
                    "requirement_ids": [],
                    "priority_routes": set(),
                },
            )
            bucket["admission_unit_ids"].append(unit_id)
            bucket["requirement_ids"].extend(member_ids)
            bucket["priority_routes"].add(str(row.get("priority_route")))
        reviewed_units.append(
            {
                "admission_unit_id": unit_id,
                "normalized_meaning": str(row.get("normalized_meaning") or ""),
                "priority_route": str(row.get("priority_route") or ""),
                "requirement_class": str(row.get("requirement_class") or ""),
                "source_id": str(row.get("source_id") or ""),
                "document_id": str(row.get("document_id") or ""),
                "section": str(row.get("section") or ""),
                "code": str(row.get("code") or ""),
                "requirement_ids": member_ids,
                "current_admission_status": str(row.get("admission_status") or ""),
                "review_disposition": disposition,
                "accepted_component_set": accepted_sets[0] if accepted_sets else None,
            }
        )

    if accepted_unit_ids - {str(row["admission_unit_id"]) for row in units}:
        raise ValueError("accepted RU08 unit escaped exact module slice")

    pending_rows = []
    for meaning, bucket in sorted(pending_meanings.items()):
        pending_rows.append(
            {
                "normalized_meaning": meaning,
                "admission_unit_ids": sorted(set(bucket["admission_unit_ids"])),
                "requirement_ids": sorted(set(bucket["requirement_ids"])),
                "priority_routes": sorted(bucket["priority_routes"]),
            }
        )

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU08_ORTHOGRAPHY_REUSE_FIRST_OBJECT_REVIEW_IN_PROGRESS_NO_NEW_ADMISSION",
        "authority_issue": 161,
        "module_id": TARGET_MODULE,
        "module_binding_mode": EXPECTED_BINDING_MODE,
        "official_review_slice_sha256": str(review_slice["normalized_sha256"]),
        "global_semantic_progress_sha256": str(progress["normalized_sha256"]),
        "reuse_pool_sha256": str(reuse_pool["normalized_sha256"]),
        "reuse_pool": {
            "canonical_school_identities": 185,
            "reviewed_active_exception_practice_cards": 121,
            "ru1_admitted_identities_available_for_cross-module_review": int((reuse_pool.get("ru1_admitted_pool") or {}).get("count") or 0),
            "asset_presence_is_coverage": False,
        },
        "summary": {
            "official_admission_units_in_module_slice": len(units),
            "official_unique_requirements_in_module_slice": len(requirement_ids),
            "normalized_meanings_in_module_slice": len({str(row.get("normalized_meaning") or "") for row in units}),
            "exact_object_bound_units_already_accepted": len(accepted_unit_ids),
            "exact_object_bound_requirements_already_accepted": len(accepted_requirement_ids),
            "unique_school_refs_already_reused": len(accepted_refs),
            "pending_exact_reuse_units": len(units) - len(accepted_unit_ids),
            "pending_exact_reuse_requirements": len(requirement_ids) - len(accepted_requirement_ids),
            "pending_normalized_meanings": len(pending_rows),
            "new_semantic_admissions": 0,
            "new_object_level_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
        "policy": {
            "reuse_first": True,
            "canonical_school_pool_is_authoritative_identity_pool_not_coverage_proof": True,
            "reviewed_exception_asset_is_practice_evidence_not_mastery_identity": True,
            "module_membership_implies_exact_mapping": False,
            "keyword_or_fuzzy_inference_allowed": False,
            "broad_or_composite_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
            "content_gap_may_be_materialized_only_after_exact_reuse_check": True,
            "semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        },
        "accepted_object_bound_unit_ids": sorted(accepted_unit_ids),
        "accepted_object_bound_requirement_ids": sorted(accepted_requirement_ids),
        "accepted_canonical_school_refs": sorted(accepted_refs),
        "pending_meaning_groups": pending_rows,
        "reviewed_units": reviewed_units,
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
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU08_ORTHOGRAPHY_REUSE_FIRST_BOUNDARY_REVIEW=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print("accepted_unit_ids=" + ",".join(result["accepted_object_bound_unit_ids"]))
        print("accepted_school_refs=" + ",".join(result["accepted_canonical_school_refs"]))
        print("PENDING_MEANING_GROUPS_BEGIN")
        for row in result["pending_meaning_groups"]:
            print(
                row["normalized_meaning"]
                + "\tunits=" + ",".join(row["admission_unit_ids"])
                + "\trequirements=" + ",".join(row["requirement_ids"])
                + "\troutes=" + ",".join(row["priority_routes"])
            )
        print("PENDING_MEANING_GROUPS_END")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
