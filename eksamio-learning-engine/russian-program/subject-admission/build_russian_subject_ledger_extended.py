#!/usr/bin/env python3
"""Build the exact Russian subject ledger with reviewed reuse-target composites.

Compact Central Brain authority pins exact normalized meanings rather than hand-
transcribing hundreds of admission-unit ids. This builder materializes those meanings
only inside the fingerprinted RU08/RU09/RU10/RU14 exact review slice, subtracts rows
already dispositioned by the base ledger, and then sends the resulting explicit
unit/requirement sets through the existing fail-closed aggregate builder.

Two classification-only authorities are consumed:
- 39 exact multi-capability meanings;
- 4 exact broad domains that are not atomic mastery targets.

No keyword/fuzzy/module semantic mapping is performed and no semantic identity or
learner-content bundle is admitted by this wrapper.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE_BUILDER = HERE / "build_russian_subject_ledger.py"
REUSE_SLICE_BUILDER = HERE / "build_reuse_target_review_slice.py"
MULTI_AUTHORITY = HERE / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITE-MEANINGS-v0.1.json"
BROAD_AUTHORITY = HERE / "RUSSIAN-SUBJECT-REVIEWED-BROAD-DOMAIN-MEANINGS-v0.1.json"
EXPECTED_TARGET_MODULES = ["RU-PROG-08", "RU-PROG-09", "RU-PROG-10", "RU-PROG-14"]
EXPECTED_QUEUE_SHA256 = "aa334efc455c68707d2d31de48b4364c879a619cf18dd07c9183d53890be5309"
EXPECTED_SLICE_SHA256 = "4a46ddc0dca08f91295e93a59f98b2f08f234425da6a4d7b611a61b8455ab7cb"
DERIVED_STATUS = "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION"
EXPECTED_MULTI = {
    "reviewed_meanings": 39,
    "accepted_classification_units": 373,
    "accepted_classification_requirements": 397,
    "semantic_admissions": 0,
}
EXPECTED_BROAD = {
    "reviewed_meanings": 4,
    "accepted_classification_units": 344,
    "accepted_classification_requirements": 361,
    "semantic_admissions": 0,
}


def _load_review_slice() -> dict[str, Any]:
    namespace = runpy.run_path(str(REUSE_SLICE_BUILDER))
    review_slice = namespace["build_slice"]()
    if review_slice.get("normalized_sha256") != EXPECTED_SLICE_SHA256:
        raise ValueError("current reuse-target exact review slice drift")
    if review_slice.get("target_modules") != EXPECTED_TARGET_MODULES:
        raise ValueError("current reuse-target exact review slice targets drift")
    return review_slice


def _validate_authority(
    authority: dict[str, Any],
    *,
    expected: dict[str, int],
    require_multi_clause: bool,
) -> list[str]:
    if authority.get("object_review_queue_sha256") != EXPECTED_QUEUE_SHA256:
        raise ValueError("reviewed meaning authority queue fingerprint drift")
    if authority.get("source_review_slice_sha256") != EXPECTED_SLICE_SHA256:
        raise ValueError("reviewed meaning authority review-slice fingerprint drift")
    if authority.get("target_modules") != EXPECTED_TARGET_MODULES:
        raise ValueError("reviewed meaning authority target-module drift")
    if authority.get("selection_rule") != "EXACT_NORMALIZED_MEANING_EQUALITY_WITHIN_PINNED_REVIEW_SLICE_ONLY":
        raise ValueError("reviewed meaning authority selection rule weakened")
    if authority.get("expected_materialized_summary") != expected:
        raise ValueError("reviewed meaning authority expected totals drift")
    meanings = authority.get("exact_normalized_meanings")
    expected_count = int(expected["reviewed_meanings"])
    if not isinstance(meanings, list) or len(meanings) != expected_count or len(set(meanings)) != expected_count:
        raise ValueError("reviewed meaning authority count/uniqueness drift")
    if any(not isinstance(meaning, str) or not meaning.strip() for meaning in meanings):
        raise ValueError("reviewed meaning authority contains an invalid exact meaning")
    if require_multi_clause and any(". " not in meaning for meaning in meanings):
        raise ValueError("multi-capability authority contains a non-multi-clause meaning")
    policy = authority.get("policy", {})
    if policy.get("keyword_or_fuzzy_inference_allowed") is not False:
        raise ValueError("keyword/fuzzy review inference is forbidden")
    if policy.get("classification_only_no_semantic_admission") is not True:
        raise ValueError("reviewed meaning authority escaped classification-only mode")
    return [str(meaning) for meaning in meanings]


def _broad_components(meaning: str) -> list[dict[str, str]]:
    digest = hashlib.sha256(meaning.encode("utf-8")).hexdigest()[:12]
    return [
        {
            "ref_kind": "review_capability_boundary",
            "ref": f"review-boundary:broad-domain-{digest}",
            "label": meaning,
            "status": DERIVED_STATUS,
        },
        {
            "ref_kind": "review_capability_boundary",
            "ref": f"review-boundary:broad-domain-{digest}-decomposition-required",
            "label": "Exact component decomposition and component-specific independent evidence required.",
            "status": DERIVED_STATUS,
        },
    ]


def materialize_reviewed_sets(
    base_payload: dict[str, Any],
    *,
    authority_path: Path,
    set_prefix: str,
    expected: dict[str, int],
    require_multi_clause: bool,
    broad_domain: bool,
) -> dict[str, Any]:
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    meanings = _validate_authority(authority, expected=expected, require_multi_clause=require_multi_clause)
    review_slice = _load_review_slice()

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
    rationale_map = authority.get("rationale_by_meaning", {}) if broad_domain else {}
    for index, meaning in enumerate(meanings, 1):
        exact_rows = by_meaning.get(meaning, [])
        if not exact_rows:
            raise ValueError(f"reviewed exact meaning has no remaining source rows: {meaning}")
        unit_ids = sorted(str(row["admission_unit_id"]) for row in exact_rows)
        if materialized_unit_ids.intersection(unit_ids):
            raise ValueError(f"exact meaning materialization duplicated an admission unit: {meaning}")
        requirement_ids = sorted(
            {
                str(member["requirement_id"])
                for row in exact_rows
                for member in row.get("members", [])
            }
        )
        if materialized_requirement_ids.intersection(requirement_ids):
            raise ValueError(f"exact meaning materialization duplicated an official requirement: {meaning}")
        materialized_unit_ids.update(unit_ids)
        materialized_requirement_ids.update(requirement_ids)
        if broad_domain:
            rationale = str(rationale_map.get(meaning, "")).strip()
            if not rationale:
                raise ValueError(f"broad-domain rationale missing: {meaning}")
            components = _broad_components(meaning)
        else:
            rationale = (
                "Exact pinned normalized meaning contains multiple independently assessable "
                "capability clauses. Classification only: generic evidence cannot emit exact "
                "component mastery and no semantic identity/content bundle is admitted."
            )
            components = None
        decision: dict[str, Any] = {
            "set_id": f"{set_prefix}-{index:03d}",
            "subject_review_status": "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION",
            "disposition": "PARTIAL_OR_COMPOSITE",
            "rationale": rationale,
            "expected_normalized_meaning": meaning,
            "exact_admission_unit_ids": unit_ids,
            "exact_requirement_ids": requirement_ids,
            "mastery_boundary": {
                "generic_domain_attempt_can_emit_exact_component_mastery": False,
                "generic_domain_attempt_can_emit_partial_or_composite_evidence": True,
                "component_mastery_requires_component_specific_independent_evidence": True,
            },
        }
        if components is not None:
            decision["components"] = components
        reviewed_sets.append(decision)

    summary = {
        "reviewed_meanings": len(reviewed_sets),
        "accepted_classification_units": len(materialized_unit_ids),
        "accepted_classification_requirements": len(materialized_requirement_ids),
        "semantic_admissions": 0,
    }
    if summary != expected:
        raise ValueError(f"exact meaning materialization totals drift: {summary}")
    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_REVIEWED_EXACT_MEANINGS_MATERIALIZED",
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

    base_payload = build_fn()
    multi = materialize_reviewed_sets(
        base_payload,
        authority_path=MULTI_AUTHORITY,
        set_prefix="CB-REUSE-COMPOSITE",
        expected=EXPECTED_MULTI,
        require_multi_clause=True,
        broad_domain=False,
    )
    broad = materialize_reviewed_sets(
        base_payload,
        authority_path=BROAD_AUTHORITY,
        set_prefix="CB-BROAD-DOMAIN",
        expected=EXPECTED_BROAD,
        require_multi_clause=False,
        broad_domain=True,
    )

    with tempfile.TemporaryDirectory(prefix="eksamio-russian-subject-") as tmp:
        multi_path = Path(tmp) / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITES-MATERIALIZED.json"
        broad_path = Path(tmp) / "RUSSIAN-SUBJECT-REVIEWED-BROAD-DOMAINS-MATERIALIZED.json"
        for path, payload in ((multi_path, multi), (broad_path, broad)):
            path.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
        globals_dict["SET_PATHS"] = (*base_paths, multi_path, broad_path)
        payload = build_fn()

    expected_multi_ids = {f"CB-REUSE-COMPOSITE-{number:03d}" for number in range(1, 40)}
    expected_broad_ids = {f"CB-BROAD-DOMAIN-{number:03d}" for number in range(1, 5)}
    actual_ids = {str(row.get("decision_set_id")) for row in payload.get("dispositions", [])}
    if not expected_multi_ids.issubset(actual_ids):
        raise ValueError("extended ledger failed to consume every reviewed reuse composite set")
    if not expected_broad_ids.issubset(actual_ids):
        raise ValueError("extended ledger failed to consume every reviewed broad-domain set")
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
