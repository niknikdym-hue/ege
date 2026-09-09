#!/usr/bin/env python3
"""Fail-closed content/evidence gap review for RU01 broad-header owner candidates.

Runs only after the exact owner-resolution gate succeeded. It inventories the
current production-learning-content tree for the six source-backed
PROPOSED_NOT_CANONICAL candidates. Presence is not semantic acceptance; absence
is an explicit blocker. No object closure or mastery is created here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
CONTENT_DIR = PROGRAM / "production-learning-content"
OWNER_BUILDER = HERE / "build_ru01_phonetics_broad_header_owner_resolution_review.py"

OWNER_GATE = {
    "run_id": 34306870268,
    "head_sha": "41dc6749d96697f393a11e67ca3da36ab73e6aa1",
    "conclusion": "SUCCESS",
}
EXPECTED_CANDIDATES = {
    "ru-phonetics-sound-characterization",
    "ru-phonetics-sound-system",
    "ru-phonetics-vowel-system",
    "ru-phonetics-consonant-system",
    "ru-phonetics-syllable",
    "ru-phonetics-stress",
}
EXPECTED_AGGREGATE = {
    "semantic_units_with_accepted_component_sets": 41,
    "semantic_requirements_with_accepted_component_sets": 41,
    "semantic_units_remaining_without_accepted_component_set": 1275,
    "semantic_requirements_remaining_without_accepted_component_set": 1350,
    "subject_disposed_units_total": 42,
    "subject_disposed_requirements_total": 42,
    "subject_review_units_remaining": 1274,
    "subject_review_requirements_remaining": 1349,
    "canonical_component_refs_reused_unique": 122,
    "accepted_bounded_ru_subject_semantics": 69,
    "accepted_bounded_ru_semantics_total": 78,
    "false_exact_mastery_admissions": 0,
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _candidate_refs(unit: dict[str, Any]) -> set[str]:
    refs = {
        str(unit.get(key))
        for key in ("proposed_semantic_id", "semantic_id", "canonical_semantic_id")
        if unit.get(key)
    }
    peis = unit.get("peis_evidence")
    if isinstance(peis, dict) and peis.get("semantic_ref"):
        refs.add(str(peis["semantic_ref"]))
    return refs


def _verification_ids(unit: dict[str, Any]) -> list[str]:
    return [
        str(row.get("id"))
        for row in unit.get("independent_verification") or []
        if isinstance(row, dict) and row.get("id")
    ]


def build_review() -> dict[str, Any]:
    owner = runpy.run_path(str(OWNER_BUILDER))["build_review"]()
    if owner.get("status") != "CENTRAL_BRAIN_RU01_BROAD_HEADER_EXACT_OWNER_RESOLUTION_READY_NOT_ACCEPTED":
        raise ValueError("owner-resolution status drift")
    if owner.get("current_aggregate_guard") != EXPECTED_AGGREGATE:
        raise ValueError("current-v19 aggregate drift")
    if (owner.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("owner-resolution false exact mastery drift")

    owner_candidates = owner.get("proposed_owner_candidates") or []
    candidate_ids = {str(row.get("candidate_semantic_id")) for row in owner_candidates}
    if candidate_ids != EXPECTED_CANDIDATES:
        raise ValueError("owner candidate set drift")
    if any(row.get("candidate_status") != "PROPOSED_NOT_CANONICAL" for row in owner_candidates):
        raise ValueError("candidate unexpectedly became canonical")
    if any(row.get("semantic_admission") or row.get("object_closure") or row.get("mastery_admission") for row in owner_candidates):
        raise ValueError("owner-resolution admission boundary opened")

    hits: dict[str, list[dict[str, Any]]] = {candidate: [] for candidate in EXPECTED_CANDIDATES}
    scanned_files = 0
    for path in sorted(CONTENT_DIR.glob("*.json")):
        scanned_files += 1
        data = json.loads(path.read_text(encoding="utf-8"))
        for index, unit in enumerate(data.get("units") or []):
            if not isinstance(unit, dict):
                continue
            refs = _candidate_refs(unit) & EXPECTED_CANDIDATES
            for candidate in sorted(refs):
                ids = _verification_ids(unit)
                hits[candidate].append({
                    "content_file": str(path.relative_to(PROGRAM)),
                    "unit_index": index,
                    "unit_identity_fields": sorted(_candidate_refs(unit) & {candidate}),
                    "independent_verification_ids": ids,
                    "independent_verification_count": len(ids),
                })

    rows = []
    for candidate in sorted(EXPECTED_CANDIDATES):
        spec = next(row for row in owner_candidates if row["candidate_semantic_id"] == candidate)
        candidate_hits = hits[candidate]
        if not candidate_hits:
            status = "NO_DEDICATED_CANDIDATE_CONTENT_FOUND"
        elif all(hit["independent_verification_count"] == 0 for hit in candidate_hits):
            status = "CONTENT_PRESENT_COMPONENT_EVIDENCE_MISSING"
        else:
            status = "CONTENT_AND_EVIDENCE_PRESENT_REQUIRES_SEPARATE_ADEQUACY_REVIEW"
        rows.append({
            "candidate_semantic_id": candidate,
            "candidate_status": "PROPOSED_NOT_CANONICAL",
            "source_clause_ids": spec["source_clause_ids"],
            "source_requirements": spec["source_requirements"],
            "partial_current_owner_refs": spec["partial_current_owner_refs"],
            "semantic_boundary": spec["semantic_boundary"],
            "content_evidence_status": status,
            "content_hits": candidate_hits,
            "semantic_admission": False,
            "object_closure": False,
            "mastery_admission": False,
        })

    missing = sum(row["content_evidence_status"] == "NO_DEDICATED_CANDIDATE_CONTENT_FOUND" for row in rows)
    content_without_evidence = sum(row["content_evidence_status"] == "CONTENT_PRESENT_COMPONENT_EVIDENCE_MISSING" for row in rows)
    present_for_review = sum(row["content_evidence_status"] == "CONTENT_AND_EVIDENCE_PRESENT_REQUIRES_SEPARATE_ADEQUACY_REVIEW" for row in rows)

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_BROAD_HEADER_CANDIDATE_CONTENT_EVIDENCE_GAP_REVIEW_READY_NOT_ACCEPTED",
        "owner_resolution_exact_head_gate": OWNER_GATE,
        "owner_resolution_normalized_sha256": owner.get("normalized_sha256"),
        "base_current_label": "current-v19",
        "candidates": rows,
        "explicit_non_inference": {
            "existing_partial_owner_can_substitute_for_candidate_content_or_evidence": False,
            "normative_orthoepy_stress_can_substitute_for_generic_phonetic_stress": False,
            "generic_or_adjacent_ru01_evidence_can_substitute_for_component_specific_evidence": False,
            "content_presence_is_semantic_acceptance": False,
            "candidate_name_or_title_or_route_or_task_can_create_mastery": False,
        },
        "next_required_action": {
            "missing_content": "BUILD_ORIGINAL_EKSAMIO_SOURCE_BOUNDED_LEARNER_CONTENT_WITH_COMPONENT_SPECIFIC_INDEPENDENT_VERIFICATION",
            "present_content": "RUN_SEPARATE_CANDIDATE_SPECIFIC_CONTENT_ADEQUACY_REVIEW_BEFORE_ANY_SEMANTIC_ACCEPTANCE",
            "semantic_acceptance": "FORBIDDEN_UNTIL_CANDIDATE_SPECIFIC_CONTENT_AND_INDEPENDENT_EVIDENCE_ARE_EXACT_AND_REVIEWED",
            "object_acceptance": "FORBIDDEN_UNTIL_EVERY_REQUIRED_CLAUSE_HAS_ACCEPTED_OWNER_AND_COMPONENT_SPECIFIC_EVIDENCE",
        },
        "current_aggregate_guard": EXPECTED_AGGREGATE,
        "summary": {
            "production_content_files_scanned": scanned_files,
            "proposed_owner_candidates": 6,
            "candidates_missing_dedicated_content": missing,
            "candidates_with_content_but_no_component_evidence": content_without_evidence,
            "candidates_with_content_and_evidence_requiring_review": present_for_review,
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "exact_mastery_admissions": 0,
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
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU01_PHONETICS_BROAD_HEADER_CANDIDATE_CONTENT_GAP_REVIEW=PASS")
        for key, value in result["summary"].items():
            print(f"{key.upper()}={value}")
        print("NORMALIZED_SHA256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
