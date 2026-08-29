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
ENGINE = PROGRAM.parent
PROGRAM_AUTHORITY = PROGRAM / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
SLICE_BUILDER = HERE / "build_launch_critical_review_slice.py"
REUSE_POOL_BUILDER = HERE / "build_ru08_09_10_14_reuse_pool.py"
PROGRESS_BUILDER = HERE / "build_russian_semantic_acceptance_progress.py"

TARGET_MODULE = "RU-PROG-09"
EXPECTED_BINDING_MODE = "MIXED_CANONICAL_AND_DRAFT_CANDIDATE_BINDING"
EXPECTED_DOMAINS = {"syntax", "syntactic_norms"}
EXPECTED_CANDIDATES = {
    "candidate-028",
    "candidate-029",
    "candidate-030",
    "candidate-031",
    "candidate-032",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    program = json.loads(PROGRAM_AUTHORITY.read_text(encoding="utf-8"))
    modules = {str(row.get("module_id")): row for row in program.get("modules", []) if isinstance(row, dict)}
    module = modules.get(TARGET_MODULE)
    if not isinstance(module, dict):
        raise ValueError("RU09 missing from full-subject program")
    if module.get("semantic_binding_mode") != EXPECTED_BINDING_MODE:
        raise ValueError("RU09 mixed binding mode drift")
    if set(module.get("domains") or []) != EXPECTED_DOMAINS:
        raise ValueError("RU09 domain boundary drift")
    if set(module.get("candidate_refs") or []) != EXPECTED_CANDIDATES:
        raise ValueError("RU09 candidate set drift")

    reuse_pool = runpy.run_path(str(REUSE_POOL_BUILDER))["main_payload"]()
    if reuse_pool.get("status") != "REUSE_POOL_READY_NOT_COVERAGE_AUTHORITY":
        raise ValueError("RU09 reuse pool status drift")
    if TARGET_MODULE not in set(reuse_pool.get("target_modules") or []):
        raise ValueError("RU09 missing from reuse-pool target modules")
    school_pool = reuse_pool.get("canonical_school_pool") or {}
    ru1_pool = reuse_pool.get("ru1_admitted_pool") or {}
    practice_pool = reuse_pool.get("reviewed_exception_practice_pool") or {}
    if school_pool.get("count") != 185:
        raise ValueError("RU09 requires frozen 185-school canonical pool")
    if ru1_pool.get("count") != 12:
        raise ValueError("RU09 RU1 admitted pool drift")
    if practice_pool.get("count") != 121:
        raise ValueError("RU09 reviewed practice pool drift")
    invariants = reuse_pool.get("invariants") or {}
    if invariants.get("asset_presence_equals_requirement_coverage") is not False:
        raise ValueError("asset presence may not imply RU09 coverage")
    if invariants.get("canonical_or_admitted_identity_requires_exact_object_mapping_for_coverage") is not True:
        raise ValueError("RU09 exact object mapping guard missing")
    if invariants.get("new_content_allowed_before_reuse_check") is not False:
        raise ValueError("RU09 must remain reuse-first")

    review_slice = runpy.run_path(str(SLICE_BUILDER))["build_slice"]({TARGET_MODULE})
    if review_slice.get("status") != "EXACT_REVIEW_SLICE_NOT_ADMISSION_DECISION":
        raise ValueError("RU09 review slice is not fail-closed")
    if review_slice.get("target_modules") != [TARGET_MODULE]:
        raise ValueError("RU09 review slice target drift")
    units = review_slice.get("admission_units")
    if not isinstance(units, list) or not units:
        raise ValueError("RU09 official review universe is empty")
    if any(TARGET_MODULE not in set(row.get("modules") or []) for row in units):
        raise ValueError("RU09 review slice contains a non-RU09 unit")

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    objects = [row for row in inventory.get("objects", []) if isinstance(row, dict)]

    # The frozen 185-school set is the authoritative reuse pool. Its canonical
    # inventory rows are current/reviewed (not source_verified). Exact string
    # matches are emitted only as review hints and can never self-admit a mapping.
    school_identities = school_pool.get("identities")
    if not isinstance(school_identities, list) or len(school_identities) != 185:
        raise ValueError("RU09 frozen school identity list drift")
    school_ids = [str(row.get("semantic_id") or "") for row in school_identities if isinstance(row, dict)]
    if len(school_ids) != 185 or len(set(school_ids)) != 185 or any(not semantic_id for semantic_id in school_ids):
        raise ValueError("RU09 frozen school identity IDs are invalid/non-unique")
    school_by_meaning: dict[str, list[str]] = defaultdict(list)
    reviewed_school_identities = 0
    for row in school_identities:
        if not isinstance(row, dict):
            raise ValueError("RU09 frozen school pool contains invalid row")
        if row.get("authority_status") != "current" or row.get("review_status") != "reviewed":
            continue
        reviewed_school_identities += 1
        school_by_meaning[str(row.get("observed_meaning") or "").strip()].append(str(row.get("semantic_id") or ""))

    candidate_rows: list[dict[str, Any]] = []
    for candidate_id in sorted(EXPECTED_CANDIDATES):
        matches = [
            row for row in objects
            if row.get("source_system") == "semantic_candidate" and row.get("source_id") == candidate_id
        ]
        if len(matches) != 1:
            raise ValueError(f"RU09 candidate inventory mismatch: {candidate_id}")
        candidate = matches[0]
        if candidate.get("authority_status") != "current":
            raise ValueError(f"RU09 candidate not current: {candidate_id}")
        if candidate.get("review_status") != "draft":
            raise ValueError(f"RU09 candidate unexpectedly admitted/review-state changed: {candidate_id}")
        if candidate.get("audit_classification") != "MISSING_SUBJECT_SEMANTIC_CANDIDATE":
            raise ValueError(f"RU09 candidate classification drift: {candidate_id}")
        if candidate.get("candidate_canonical_owner") != candidate_id:
            raise ValueError(f"RU09 candidate owner drift: {candidate_id}")
        refs = [str(ref) for ref in (candidate.get("current_semantic_refs") or [])]
        if len(refs) != 1:
            raise ValueError(f"RU09 candidate must have one exact EGE taxonomy ref: {candidate_id}")
        taxonomy_ref = refs[0]
        backing = [
            row for row in objects
            if row.get("source_system") == "ege_skill_graph"
            and row.get("source_id") == taxonomy_ref
            and row.get("candidate_canonical_owner") == candidate_id
        ]
        if len(backing) != 1:
            raise ValueError(f"RU09 exact taxonomy backing mismatch: {candidate_id}/{taxonomy_ref}")
        backing_row = backing[0]
        if backing_row.get("authority_status") != "current" or backing_row.get("review_status") != "source_verified":
            raise ValueError(f"RU09 taxonomy backing is not current/source-verified: {candidate_id}")
        if backing_row.get("audit_classification") != "EGE_TAXONOMY_NODE":
            raise ValueError(f"RU09 taxonomy backing classification drift: {candidate_id}")
        meaning = str(candidate.get("observed_meaning") or "").strip()
        exact_school_matches = sorted(set(school_by_meaning.get(meaning, [])))
        candidate_rows.append(
            {
                "candidate_ref": candidate_id,
                "label_ru": str(candidate.get("observed_label") or ""),
                "meaning_ru": meaning,
                "candidate_review_status": "draft",
                "taxonomy_ref": taxonomy_ref,
                "taxonomy_source_status": "current_source_verified",
                "taxonomy_provenance_refs": list(backing_row.get("evidence_provenance_refs") or []),
                "exact_school_meaning_matches": exact_school_matches,
                "review_disposition": "REUSE_FIRST_EXACT_BOUNDARY_REVIEW_REQUIRED_NOT_ADMITTED",
            }
        )

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
            raise ValueError(f"RU09 unit has overlapping accepted component sets: {unit_id}")
        if accepted_sets:
            accepted = accepted_sets[0]
            if str(accepted.get("requirement_id")) not in set(member_ids):
                raise ValueError(f"RU09 accepted requirement not in unit: {unit_id}")
            refs = [str(ref) for ref in (accepted.get("canonical_component_refs") or [])]
            if not refs or any(not ref.startswith("school-") for ref in refs):
                raise ValueError(f"RU09 accepted object set is not canonical-school reuse: {unit_id}")
            accepted_unit_ids.add(unit_id)
            accepted_requirement_ids.add(str(accepted["requirement_id"]))
            accepted_refs.update(refs)
            disposition = "EXACT_OBJECT_BOUND_CANONICAL_REUSE_ALREADY_ACCEPTED"
        else:
            disposition = "PENDING_EXACT_REUSE_OR_CANDIDATE_BOUNDARY_REVIEW"
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
            bucket["priority_routes"].add(str(row.get("priority_route") or ""))
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

    pending_rows = [
        {
            "normalized_meaning": meaning,
            "admission_unit_ids": sorted(set(bucket["admission_unit_ids"])),
            "requirement_ids": sorted(set(bucket["requirement_ids"])),
            "priority_routes": sorted(set(bucket["priority_routes"])),
            "candidate_exact_meaning_matches": sorted(
                row["candidate_ref"] for row in candidate_rows if row["meaning_ru"] == meaning
            ),
        }
        for meaning, bucket in sorted(pending_meanings.items())
    ]

    summary = {
        "official_admission_units_in_module_slice": len(units),
        "official_unique_requirements_in_module_slice": len(requirement_ids),
        "exact_normalized_meaning_groups": len({str(row.get("normalized_meaning") or "") for row in units}),
        "draft_subject_candidates": len(candidate_rows),
        "source_verified_taxonomy_backings": sum(row["taxonomy_source_status"] == "current_source_verified" for row in candidate_rows),
        "current_reviewed_school_identities_eligible_for_exact_meaning_hint": reviewed_school_identities,
        "candidate_exact_school_meaning_overlap_count": sum(bool(row["exact_school_meaning_matches"]) for row in candidate_rows),
        "exact_object_bound_units_already_accepted": len(accepted_unit_ids),
        "exact_object_bound_requirements_already_accepted": len(accepted_requirement_ids),
        "unique_already_reused_school_refs": len(accepted_refs),
        "pending_exact_review_units": len(units) - len(accepted_unit_ids),
        "pending_exact_review_requirements": len(requirement_ids) - len(accepted_requirement_ids),
        "new_semantic_admissions": 0,
        "new_object_level_closures": 0,
        "false_exact_mastery_admissions": 0,
    }

    payload: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU09_SYNTAX_REUSE_FIRST_BOUNDARY_REVIEW_IN_PROGRESS_NO_NEW_ADMISSION",
        "module_id": TARGET_MODULE,
        "module_binding_mode": EXPECTED_BINDING_MODE,
        "domains": sorted(EXPECTED_DOMAINS),
        "policy": {
            "reuse_first": True,
            "draft_candidate_is_canonical": False,
            "ege_taxonomy_node_is_universal_semantic_identity": False,
            "exact_taxonomy_backing_can_support_subject_review_but_not_self_admission": True,
            "canonical_school_pool_is_authoritative_identity_pool_not_coverage_proof": True,
            "school_exact_meaning_hint_requires_current_reviewed_identity": True,
            "reviewed_exception_asset_is_practice_evidence_not_mastery_identity": True,
            "module_membership_implies_exact_mapping": False,
            "keyword_or_fuzzy_inference_allowed": False,
            "semantic_acceptance_can_reduce_object_counts_without_exact_binding": False,
        },
        "reuse_pool": {
            "canonical_school_identities": int(school_pool["count"]),
            "ru1_admitted_identities": int(ru1_pool["count"]),
            "explicit_ru1_admitted_for_ru09": int((ru1_pool.get("explicit_target_module_counts") or {}).get(TARGET_MODULE, 0)),
            "reviewed_active_exception_practice_cards": int(practice_pool["count"]),
            "asset_presence_is_coverage": False,
        },
        "summary": summary,
        "candidate_boundary": candidate_rows,
        "pending_meaning_groups": pending_rows,
        "reviewed_units": reviewed_units,
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_review()
    if args.output:
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU09_SYNTAX_REUSE_FIRST_BOUNDARY_REVIEW=PASS")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        print(f"normalized_sha256={payload['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
