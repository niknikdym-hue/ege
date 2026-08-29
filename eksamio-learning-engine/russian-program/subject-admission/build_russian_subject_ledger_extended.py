#!/usr/bin/env python3
"""Build the exact Russian subject ledger with reviewed reuse-target composites.

The compact Central Brain authority pins 39 *exact normalized meanings* rather than
hand-transcribing hundreds of admission-unit ids.  This builder materializes those
meanings only inside the already pinned RU08/RU09/RU10/RU14 exact review slice,
subtracts rows already dispositioned by the base ledger, then sends the resulting
explicit unit/requirement sets through the existing fail-closed aggregate builder.
No keyword/fuzzy/module semantic mapping is performed and no semantic identity is
admitted by this wrapper.
"""
from __future__ import annotations

import argparse
import json
import runpy
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE_BUILDER = HERE / "build_russian_subject_ledger.py"
REUSE_SLICE_BUILDER = HERE / "build_reuse_target_review_slice.py"
MEANING_AUTHORITY = HERE / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITE-MEANINGS-v0.1.json"
MATERIALIZED_NAME = "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITES-MATERIALIZED.json"
EXPECTED_TARGET_MODULES = ["RU-PROG-08", "RU-PROG-09", "RU-PROG-10", "RU-PROG-14"]
EXPECTED_QUEUE_SHA256 = "aa334efc455c68707d2d31de48b4364c879a619cf18dd07c9183d53890be5309"
EXPECTED_SLICE_SHA256 = "4a46ddc0dca08f91295e93a59f98b2f08f234425da6a4d7b611a61b8455ab7cb"
EXPECTED_MATERIALIZED = {
    "reviewed_meanings": 39,
    "accepted_classification_units": 373,
    "accepted_classification_requirements": 397,
    "semantic_admissions": 0,
}


def materialize_reviewed_sets(base_payload: dict[str, Any]) -> dict[str, Any]:
    authority = json.loads(MEANING_AUTHORITY.read_text(encoding="utf-8"))
    if authority.get("object_review_queue_sha256") != EXPECTED_QUEUE_SHA256:
        raise ValueError("reuse composite meaning authority queue fingerprint drift")
    if authority.get("source_review_slice_sha256") != EXPECTED_SLICE_SHA256:
        raise ValueError("reuse composite meaning authority review-slice fingerprint drift")
    if authority.get("target_modules") != EXPECTED_TARGET_MODULES:
        raise ValueError("reuse composite meaning authority target-module drift")
    if authority.get("selection_rule") != "EXACT_NORMALIZED_MEANING_EQUALITY_WITHIN_PINNED_REVIEW_SLICE_ONLY":
        raise ValueError("reuse composite meaning authority selection rule weakened")
    if authority.get("expected_materialized_summary") != EXPECTED_MATERIALIZED:
        raise ValueError("reuse composite meaning authority expected totals drift")
    meanings = authority.get("exact_normalized_meanings")
    if not isinstance(meanings, list) or len(meanings) != 39 or len(set(meanings)) != 39:
        raise ValueError("reuse composite meaning authority must contain 39 unique exact meanings")
    if any(not isinstance(meaning, str) or ". " not in meaning for meaning in meanings):
        raise ValueError("every reviewed reuse meaning must contain multiple explicit capability clauses")

    slice_namespace = runpy.run_path(str(REUSE_SLICE_BUILDER))
    review_slice = slice_namespace["build_slice"]()
    if review_slice.get("normalized_sha256") != EXPECTED_SLICE_SHA256:
        raise ValueError("current reuse-target exact review slice drift")
    if review_slice.get("target_modules") != EXPECTED_TARGET_MODULES:
        raise ValueError("current reuse-target exact review slice targets drift")

    already_dispositioned = {
        str(row.get("admission_unit_id"))
        for row in base_payload.get("dispositions", [])
    }
    by_meaning: dict[str, list[dict[str, Any]]] = {}
    for row in review_slice.get("admission_units", []):
        if str(row.get("admission_unit_id")) in already_dispositioned:
            continue
        meaning = str(row.get("normalized_meaning", ""))
        by_meaning.setdefault(meaning, []).append(row)

    reviewed_sets: list[dict[str, Any]] = []
    materialized_unit_ids: set[str] = set()
    materialized_requirement_ids: set[str] = set()
    for index, meaning in enumerate(meanings, 1):
        exact_rows = by_meaning.get(meaning, [])
        if not exact_rows:
            raise ValueError(f"reviewed exact meaning has no remaining source rows: {meaning}")
        unit_ids = sorted(str(row["admission_unit_id"]) for row in exact_rows)
        if materialized_unit_ids.intersection(unit_ids):
            raise ValueError(f"reuse composite materialization duplicated an admission unit: {meaning}")
        requirement_ids = sorted(
            {
                str(member["requirement_id"])
                for row in exact_rows
                for member in row.get("members", [])
            }
        )
        if materialized_requirement_ids.intersection(requirement_ids):
            raise ValueError(f"reuse composite materialization duplicated an official requirement: {meaning}")
        materialized_unit_ids.update(unit_ids)
        materialized_requirement_ids.update(requirement_ids)
        reviewed_sets.append(
            {
                "set_id": f"CB-REUSE-COMPOSITE-{index:03d}",
                "subject_review_status": "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION",
                "disposition": "PARTIAL_OR_COMPOSITE",
                "rationale": (
                    "Exact pinned normalized meaning contains multiple independently assessable "
                    "capability clauses. Classification only: generic evidence cannot emit exact "
                    "component mastery and no semantic identity/content bundle is admitted."
                ),
                "expected_normalized_meaning": meaning,
                "exact_admission_unit_ids": unit_ids,
                "exact_requirement_ids": requirement_ids,
                "mastery_boundary": {
                    "generic_domain_attempt_can_emit_exact_component_mastery": False,
                    "generic_domain_attempt_can_emit_partial_or_composite_evidence": True,
                    "component_mastery_requires_component_specific_independent_evidence": True,
                },
            }
        )

    summary = {
        "reviewed_meanings": len(reviewed_sets),
        "accepted_classification_units": len(materialized_unit_ids),
        "accepted_classification_requirements": len(materialized_requirement_ids),
        "semantic_admissions": 0,
    }
    if summary != EXPECTED_MATERIALIZED:
        raise ValueError(f"reuse composite exact materialization totals drift: {summary}")
    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_REVIEWED_REUSE_TARGET_COMPOSITES_MATERIALIZED",
        "object_review_queue_sha256": EXPECTED_QUEUE_SHA256,
        "source_review_slice_sha256": EXPECTED_SLICE_SHA256,
        "selection_rule": "EXACT_NORMALIZED_MEANING_EQUALITY_WITHIN_PINNED_REVIEW_SLICE_ONLY",
        "summary": summary,
        "reviewed_sets": reviewed_sets,
    }


def build_ledger() -> dict[str, Any]:
    namespace = runpy.run_path(str(BASE_BUILDER))
    build_fn = namespace["build_ledger"]
    globals_dict = build_fn.__globals__
    base_paths = tuple(globals_dict["SET_PATHS"])

    # First build the already accepted base ledger so the new exact review slice
    # can exclude every unit that already has a fail-closed disposition.
    base_payload = build_fn()
    materialized = materialize_reviewed_sets(base_payload)

    with tempfile.TemporaryDirectory(prefix="eksamio-russian-subject-") as tmp:
        materialized_path = Path(tmp) / MATERIALIZED_NAME
        materialized_path.write_text(
            json.dumps(materialized, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        globals_dict["SET_PATHS"] = (*base_paths, materialized_path)
        payload = build_fn()

    expected_set_ids = {f"CB-REUSE-COMPOSITE-{number:03d}" for number in range(1, 40)}
    actual_set_ids = {
        str(row.get("decision_set_id"))
        for row in payload.get("dispositions", [])
        if str(row.get("decision_set_id", "")).startswith("CB-REUSE-COMPOSITE-")
    }
    if actual_set_ids != expected_set_ids:
        raise ValueError("extended ledger failed to consume every reviewed reuse composite set")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_ledger()
    if args.output:
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_SUBJECT_LEDGER_EXTENDED_BUILD=PASS")
        print(f"normalized_sha256={payload['normalized_sha256']}")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        for disposition, counts in payload["by_disposition"].items():
            print(f"{disposition}.admission_units={counts['admission_units']}")
            print(f"{disposition}.requirements={counts['requirements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
