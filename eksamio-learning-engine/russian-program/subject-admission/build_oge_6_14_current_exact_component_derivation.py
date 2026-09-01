#!/usr/bin/env python3
"""Derive the OGE-2026 6.14 applicable component set from accepted exact authorities.

OGE_COD 6.14 is an exam-only orthographic-analysis composite.  This builder does
not turn the historical "all applicable" placeholder into an identity and does
not accept 6.14 itself.  It projects only already accepted exact OGE orthography
component sets from the current launch progress authority, then deduplicates the
canonical school refs with per-code provenance.  A separate reuse-first learner-
evidence audit is required before any 6.14 object acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CURRENT_PROGRESS = HERE / "build_russian_semantic_acceptance_progress_launch_current.py"

OFFICIAL_SOURCE_SYSTEM = "OGE_COD"
OFFICIAL_CODE = "6.14"
OFFICIAL_LABEL = "Орфографический анализ"
EXPECTED_SOURCE_CODES = tuple(f"6.{index}" for index in range(2, 14))
EXPECTED_SOURCE_CODE_COUNT = 12
EXPECTED_COMPONENT_MEMBERSHIPS = 90
EXPECTED_UNIQUE_COMPONENTS = 83
EXPECTED_SHARED_COMPONENTS = {
    "school-compound-adjective-solid-hyphen-separate-system": ("6.8", "6.13"),
    "school-conjunction-solid-separate-spelling-base": ("6.8", "6.11"),
    "school-nonnegative-particle-separate-hyphen-spelling-base": ("6.8", "6.11"),
    "school-numeral-orthography-base": ("6.4", "6.8"),
    "school-o-e-after-sibilants-suffix-ending": ("6.6", "6.7"),
    "school-preposition-solid-hyphen-separate-base": ("6.8", "6.11"),
    "school-vowels-after-ts-suffix-ending": ("6.6", "6.7"),
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _normalized_sha(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _current_progress() -> dict[str, Any]:
    namespace = runpy.run_path(str(CURRENT_PROGRESS))
    progress = namespace["build_progress"]()
    if progress.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS":
        raise RuntimeError("current launch semantic progress is not the accepted in-progress authority")
    if progress.get("russian_content_ready") is not False:
        raise RuntimeError("current launch semantic progress unexpectedly claims Russian content ready")
    summary = progress.get("progress_summary") or {}
    if summary.get("false_exact_mastery_admissions") != 0:
        raise RuntimeError("current launch progress contains false exact mastery")
    return progress


def build_derivation() -> dict[str, Any]:
    progress = _current_progress()
    authority_by_id = {
        str(row.get("id")): row
        for row in progress.get("accepted_authorities", [])
        if isinstance(row, dict)
    }

    rows_by_code: dict[str, list[dict[str, Any]]] = {code: [] for code in EXPECTED_SOURCE_CODES}
    for group in progress.get("semantic_review_groups", []):
        for row in group.get("accepted_component_sets", []):
            if row.get("document_id") != OFFICIAL_SOURCE_SYSTEM:
                continue
            code = str(row.get("content_code", ""))
            if code in rows_by_code:
                rows_by_code[code].append(row)

    missing_codes = [code for code in EXPECTED_SOURCE_CODES if not rows_by_code[code]]
    duplicate_codes = [code for code in EXPECTED_SOURCE_CODES if len(rows_by_code[code]) != 1 and rows_by_code[code]]
    if missing_codes:
        raise RuntimeError(f"6.14 derivation blocked: missing accepted exact orthography codes {missing_codes}")
    if duplicate_codes:
        raise RuntimeError(f"6.14 derivation blocked: duplicate accepted exact orthography codes {duplicate_codes}")

    source_sets: list[dict[str, Any]] = []
    ref_codes: dict[str, set[str]] = {}
    authority_ids: set[str] = set()
    component_memberships = 0

    for code in EXPECTED_SOURCE_CODES:
        row = rows_by_code[code][0]
        if row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET":
            raise RuntimeError(f"{code} is not an accepted canonical component set")
        mastery = row.get("mastery_boundary") or {}
        if mastery.get("route_or_broad_composite_attempt_can_emit_exact_component_mastery") is not False:
            raise RuntimeError(f"{code} weakened the broad-route exact-mastery guard")
        if mastery.get("component_specific_independent_evidence_required") is not True:
            raise RuntimeError(f"{code} lacks the independent-evidence guard")

        refs = row.get("canonical_component_refs")
        if not isinstance(refs, list) or not refs:
            raise RuntimeError(f"{code} has no exact canonical component refs")
        refs = [str(ref) for ref in refs]
        if len(refs) != len(set(refs)):
            raise RuntimeError(f"{code} contains duplicate component refs")
        if any(not ref.startswith("school-") for ref in refs):
            raise RuntimeError(f"{code} contains a noncanonical/non-school component ref")
        if int(row.get("component_count", -1)) != len(refs):
            raise RuntimeError(f"{code} component count drift")

        authority_id = str(row.get("accepted_authority_id", ""))
        authority = authority_by_id.get(authority_id)
        if authority is None:
            raise RuntimeError(f"{code} references an authority absent from current launch progress")
        if authority.get("authority_kind") != "OBJECT_BOUND_CANONICAL_COMPONENT_SET":
            raise RuntimeError(f"{code} is not backed by an object-bound exact authority")
        if int(authority.get("accepted_admission_units", 0)) < 1 or int(authority.get("accepted_requirements", 0)) < 1:
            raise RuntimeError(f"{code} authority is not accepted at object level")

        authority_ids.add(authority_id)
        component_memberships += len(refs)
        for ref in refs:
            ref_codes.setdefault(ref, set()).add(code)

        source_sets.append(
            {
                "content_code": code,
                "admission_unit_id": str(row.get("admission_unit_id", "")),
                "requirement_id": str(row.get("requirement_id", "")),
                "accepted_authority_id": authority_id,
                "accepted_authority_sha256": str(authority.get("sha256", "")),
                "component_count": len(refs),
                "canonical_component_refs": refs,
            }
        )

    if len(source_sets) != EXPECTED_SOURCE_CODE_COUNT:
        raise RuntimeError("6.14 source code count drift")
    applicable_refs = sorted(ref_codes)
    if component_memberships != EXPECTED_COMPONENT_MEMBERSHIPS:
        raise RuntimeError(
            f"6.14 exact-authority membership drift: expected={EXPECTED_COMPONENT_MEMBERSHIPS} actual={component_memberships}"
        )
    if len(applicable_refs) != EXPECTED_UNIQUE_COMPONENTS:
        raise RuntimeError(
            f"6.14 unique exact-component drift: expected={EXPECTED_UNIQUE_COMPONENTS} actual={len(applicable_refs)}"
        )

    shared = {
        ref: tuple(sorted(codes, key=lambda code: int(code.split(".")[1])))
        for ref, codes in ref_codes.items()
        if len(codes) > 1
    }
    if shared != EXPECTED_SHARED_COMPONENTS:
        raise RuntimeError(f"6.14 shared-component provenance drift: {shared!r}")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CURRENT_EXACT_COMPONENT_SET_DERIVED_REUSE_EVIDENCE_AUDIT_REQUIRED",
        "official_source": {
            "source_system": OFFICIAL_SOURCE_SYSTEM,
            "cycle": 2026,
            "code": OFFICIAL_CODE,
            "label": OFFICIAL_LABEL,
            "classification": "EXAM_ONLY_COMPOSITE",
            "fabricated_subcodes": 0,
        },
        "derivation": {
            "source_authority": CURRENT_PROGRESS.name,
            "source_progress_normalized_sha256": str(progress.get("normalized_sha256", "")),
            "source_codes": list(EXPECTED_SOURCE_CODES),
            "source_code_count": len(source_sets),
            "accepted_object_authority_ids": sorted(authority_ids),
            "accepted_object_authority_count": len(authority_ids),
            "source_component_sets": source_sets,
            "component_memberships_before_deduplication": component_memberships,
            "applicable_component_refs": applicable_refs,
            "applicable_component_count": len(applicable_refs),
            "shared_component_refs": {ref: list(codes) for ref, codes in sorted(shared.items())},
            "shared_component_ref_count": len(shared),
            "unresolved_source_codes": [],
            "placeholder_owner_used": False,
            "manual_broad_list_used": False,
            "keyword_or_fuzzy_inference_used": False,
            "all_school_identities_used": False,
            "component_set_status": "COMPLETE_CURRENT_ACCEPTED_EXACT_AUTHORITY_PROJECTION",
            "oge_6_13_current_reconfirmation_guard_executed_by_source_progress": True,
        },
        "acceptance_boundary": {
            "new_canonical_identity_required": False,
            "exact_component_refs_accepted_for_6_14_now": [],
            "exact_component_acceptance_count_for_6_14_now": 0,
            "object_closures_now": 0,
            "policy": (
                "These 83 refs are the deduplicated projection of already accepted exact OGE orthography component sets, "
                "not a new 6.14 mastery admission. A separate reuse-first audit must prove independent learner evidence "
                "for the derived component frontier before any 6.14 object acceptance."
            ),
        },
        "safety": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "new_school_identities": 0,
            "school_reopen": 0,
            "false_exact_mastery_admissions": 0,
            "learner_audio_persistence": 0,
            "accepted_demo_or_scorer_change": False,
            "tilda_change": False,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_payment_or_refund": False,
            "real_message_delivery": False,
        },
        "next_gate": (
            "Run a reuse-first independent learner-evidence audit for all 83 derived canonical refs. Do not materialize "
            "new evidence until the audit proves which refs already have qualifying exact evidence; do not accept 6.14 "
            "until every required ref is evidence-ready under the existing exact-mastery policy."
        ),
    }
    result["normalized_sha256"] = _normalized_sha(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_derivation()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        d = result["derivation"]
        print("RUSSIAN_OGE_6_14_CURRENT_EXACT_COMPONENT_DERIVATION=PASS")
        print(f"source_code_count={d['source_code_count']}")
        print(f"component_memberships_before_deduplication={d['component_memberships_before_deduplication']}")
        print(f"applicable_component_count={d['applicable_component_count']}")
        print(f"shared_component_ref_count={d['shared_component_ref_count']}")
        print("OGE_6_14_EXACT_COMPONENT_ADMISSIONS_NOW=0")
        print("OGE_6_14_OBJECT_CLOSURES_NOW=0")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
