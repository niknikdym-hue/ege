#!/usr/bin/env python3
"""Complete fail-closed object accounting for the Sep-1 Russian subject candidate.

This does NOT accept Russian semantics.  It proves that every official requirement
and every strict admission unit has exactly one disposition while preserving the
separate semantic-acceptance boundary.  The final 486 units are selected only by
exact normalized-meaning equality inside the fingerprinted remaining-module review
slice, after subtracting every already-dispositioned unit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE_BUILDER = HERE / "build_russian_subject_ledger.py"
EXTENDED_BUILDER = HERE / "build_russian_subject_ledger_extended.py"
REMAINING_SLICE_BUILDER = HERE / "build_remaining_module_review_slice.py"
REMAINING_AUTHORITY = HERE / "RUSSIAN-SUBJECT-REVIEWED-REMAINING-DOMAIN-MEANINGS-v0.1.json"

EXPECTED_QUEUE_SHA256 = "aa334efc455c68707d2d31de48b4364c879a619cf18dd07c9183d53890be5309"
EXPECTED_REMAINING_SLICE_SHA256 = "dfbe7e6ca5d8fc3c6de191d6204ab61874286de54524faef545ab56dec5cb56b"
EXPECTED_REMAINING_MODULES = [
    "RU-PROG-01", "RU-PROG-02", "RU-PROG-03", "RU-PROG-04", "RU-PROG-05",
    "RU-PROG-06", "RU-PROG-07", "RU-PROG-11", "RU-PROG-12", "RU-PROG-15",
]
EXPECTED_REMAINING = {
    "reviewed_meanings": 25,
    "accepted_classification_units": 486,
    "accepted_classification_requirements": 517,
    "semantic_admissions": 0,
}
DERIVED_STATUS = "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _audit_components(meaning: str) -> list[dict[str, str]]:
    digest = hashlib.sha256(meaning.encode("utf-8")).hexdigest()[:12]
    clauses = [clause.strip() for clause in meaning.split(". ") if clause.strip()]
    if len(clauses) >= 2:
        return [
            {
                "ref_kind": "review_capability_boundary",
                "ref": f"review-boundary:{hashlib.sha256(clause.encode('utf-8')).hexdigest()[:12]}",
                "label": clause if clause.endswith(".") else clause + ".",
                "status": DERIVED_STATUS,
            }
            for clause in clauses
        ]
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


def materialize_remaining(interim_payload: dict[str, Any]) -> dict[str, Any]:
    authority = json.loads(REMAINING_AUTHORITY.read_text(encoding="utf-8"))
    if authority.get("object_review_queue_sha256") != EXPECTED_QUEUE_SHA256:
        raise ValueError("remaining authority queue fingerprint drift")
    if authority.get("source_review_slice_sha256") != EXPECTED_REMAINING_SLICE_SHA256:
        raise ValueError("remaining authority review-slice fingerprint drift")
    if authority.get("target_modules") != EXPECTED_REMAINING_MODULES:
        raise ValueError("remaining authority target-module drift")
    if authority.get("selection_rule") != "EXACT_NORMALIZED_MEANING_EQUALITY_WITHIN_PINNED_REVIEW_SLICE_ONLY_AFTER_PREVIOUS_DISPOSITIONS":
        raise ValueError("remaining authority selection rule weakened")
    if authority.get("expected_materialized_summary") != EXPECTED_REMAINING:
        raise ValueError("remaining authority expected totals drift")
    policy = authority.get("policy", {})
    if policy.get("keyword_or_fuzzy_inference_allowed") is not False:
        raise ValueError("keyword/fuzzy remaining-unit inference is forbidden")
    if policy.get("classification_only_no_semantic_admission") is not True:
        raise ValueError("remaining authority escaped classification-only mode")
    if policy.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("remaining authority allows false exact mastery")

    meanings = authority.get("exact_normalized_meanings")
    if not isinstance(meanings, list) or len(meanings) != 25 or len(set(meanings)) != 25:
        raise ValueError("remaining authority must contain 25 unique exact meanings")

    slice_namespace = runpy.run_path(str(REMAINING_SLICE_BUILDER))
    review_slice = slice_namespace["build_slice"]()
    if review_slice.get("normalized_sha256") != EXPECTED_REMAINING_SLICE_SHA256:
        raise ValueError("current remaining-module review slice drift")
    if review_slice.get("target_modules") != EXPECTED_REMAINING_MODULES:
        raise ValueError("current remaining-module review targets drift")

    already = {str(row.get("admission_unit_id")) for row in interim_payload.get("dispositions", [])}
    by_meaning: dict[str, list[dict[str, Any]]] = {}
    for row in review_slice.get("admission_units", []):
        if str(row.get("admission_unit_id")) in already:
            continue
        by_meaning.setdefault(str(row.get("normalized_meaning", "")), []).append(row)

    if set(by_meaning) != set(meanings):
        missing = sorted(set(meanings) - set(by_meaning))
        unexpected = sorted(set(by_meaning) - set(meanings))
        raise ValueError(f"remaining exact meaning partition drift; missing={missing}; unexpected={unexpected}")

    reviewed_sets: list[dict[str, Any]] = []
    all_units: set[str] = set()
    all_requirements: set[str] = set()
    for index, meaning in enumerate(meanings, 1):
        rows = by_meaning[meaning]
        unit_ids = sorted(str(row["admission_unit_id"]) for row in rows)
        requirement_ids = sorted(
            {
                str(member["requirement_id"])
                for row in rows
                for member in row.get("members", [])
            }
        )
        if all_units.intersection(unit_ids):
            raise ValueError(f"remaining materialization duplicated unit: {meaning}")
        if all_requirements.intersection(requirement_ids):
            raise ValueError(f"remaining materialization duplicated requirement: {meaning}")
        all_units.update(unit_ids)
        all_requirements.update(requirement_ids)
        reviewed_sets.append(
            {
                "set_id": f"CB-REMAINING-DOMAIN-{index:03d}",
                "subject_review_status": "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION",
                "disposition": "PARTIAL_OR_COMPOSITE",
                "rationale": (
                    "Exact official review meaning is broad or multi-capability and is not an atomic "
                    "mastery target. This is classification/accounting only; exact semantic components "
                    "still require explicit subject acceptance and component-specific evidence."
                ),
                "expected_normalized_meaning": meaning,
                "exact_admission_unit_ids": unit_ids,
                "exact_requirement_ids": requirement_ids,
                "components": _audit_components(meaning),
                "mastery_boundary": {
                    "generic_domain_attempt_can_emit_exact_component_mastery": False,
                    "generic_domain_attempt_can_emit_partial_or_composite_evidence": True,
                    "component_mastery_requires_component_specific_independent_evidence": True,
                },
            }
        )

    summary = {
        "reviewed_meanings": len(reviewed_sets),
        "accepted_classification_units": len(all_units),
        "accepted_classification_requirements": len(all_requirements),
        "semantic_admissions": 0,
    }
    if summary != EXPECTED_REMAINING:
        raise ValueError(f"remaining exact materialization totals drift: {summary}")
    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_REVIEWED_REMAINING_DOMAINS_MATERIALIZED",
        "object_review_queue_sha256": EXPECTED_QUEUE_SHA256,
        "source_review_slice_sha256": EXPECTED_REMAINING_SLICE_SHA256,
        "selection_rule": authority["selection_rule"],
        "summary": summary,
        "reviewed_sets": reviewed_sets,
    }


def build_accounting() -> dict[str, Any]:
    base_namespace = runpy.run_path(str(BASE_BUILDER))
    base_fn = base_namespace["build_ledger"]
    base_globals = base_fn.__globals__
    base_paths = tuple(base_globals["SET_PATHS"])
    base_payload = base_fn()

    ext_namespace = runpy.run_path(str(EXTENDED_BUILDER))
    materialize = ext_namespace["materialize_reviewed_sets"]
    multi = materialize(
        base_payload,
        authority_path=ext_namespace["MULTI_AUTHORITY"],
        set_prefix="CB-REUSE-COMPOSITE",
        expected=ext_namespace["EXPECTED_MULTI"],
        require_multi_clause=True,
        broad_domain=False,
    )
    broad = materialize(
        base_payload,
        authority_path=ext_namespace["BROAD_AUTHORITY"],
        set_prefix="CB-BROAD-DOMAIN",
        expected=ext_namespace["EXPECTED_BROAD"],
        require_multi_clause=False,
        broad_domain=True,
    )

    with tempfile.TemporaryDirectory(prefix="eksamio-russian-accounting-") as tmp:
        tmp_root = Path(tmp)
        multi_path = tmp_root / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITES-MATERIALIZED.json"
        broad_path = tmp_root / "RUSSIAN-SUBJECT-REVIEWED-BROAD-DOMAINS-MATERIALIZED.json"
        for path, payload in ((multi_path, multi), (broad_path, broad)):
            path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

        base_globals["SET_PATHS"] = (*base_paths, multi_path, broad_path)
        interim = base_fn()
        if interim.get("summary", {}).get("accepted_classification_units") != 839:
            raise ValueError("interim 839-unit accounting boundary drift")

        remaining = materialize_remaining(interim)
        remaining_path = tmp_root / "RUSSIAN-SUBJECT-REVIEWED-REMAINING-DOMAINS-MATERIALIZED.json"
        remaining_path.write_text(json.dumps(remaining, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

        base_globals["SET_PATHS"] = (*base_paths, multi_path, broad_path, remaining_path)
        payload = base_fn()

    summary = payload.get("summary", {})
    expected_summary = {
        "admission_units_total": 1325,
        "requirements_total": 1400,
        "accepted_classification_units": 1325,
        "accepted_classification_requirements": 1400,
        "remaining_subject_review_units": 0,
        "remaining_subject_review_requirements": 0,
        "canonical_semantic_admissions": 0,
        "ru_proposal_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise ValueError(f"full object accounting did not close exactly: {summary}")

    partial_rows = [row for row in payload["dispositions"] if row["disposition"] == "PARTIAL_OR_COMPOSITE"]
    route_rows = [row for row in payload["dispositions"] if row["disposition"] == "ROUTE_OR_FORMAT_ONLY"]
    if len(partial_rows) != 1316 or sum(len(row["members"]) for row in partial_rows) != 1391:
        raise ValueError("full partial/composite accounting totals drift")
    if len(route_rows) != 9 or sum(len(row["members"]) for row in route_rows) != 9:
        raise ValueError("full route/format accounting totals drift")

    meaning_counts = Counter(str(row["normalized_meaning"]) for row in partial_rows)
    requirement_counts: Counter[str] = Counter()
    for row in partial_rows:
        requirement_counts[str(row["normalized_meaning"])] += len(row["members"])
    acceptance_groups = [
        {
            "normalized_meaning": meaning,
            "admission_units": meaning_counts[meaning],
            "requirements": requirement_counts[meaning],
            "status": "SEMANTIC_DECOMPOSITION_OR_EXACT_MAPPING_REQUIRED",
        }
        for meaning in sorted(meaning_counts)
    ]
    if len(acceptance_groups) != 74:
        raise ValueError(f"finite semantic review-group count drift: {len(acceptance_groups)}")

    payload["status"] = "RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING_COMPLETE_SEMANTIC_ACCEPTANCE_REQUIRED"
    payload["semantic_acceptance"] = {
        "status": "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED",
        "russian_content_ready": False,
        "object_accounting_complete": True,
        "semantic_review_groups": len(acceptance_groups),
        "canonical_semantic_admissions": 0,
        "ru_proposal_admissions": 0,
        "rule": "Object accounting must not be interpreted as semantic/content admission or launch readiness.",
        "groups": acceptance_groups,
    }
    payload.pop("normalized_sha256", None)
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_accounting()
    if args.output:
        Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING=PASS")
        print(f"status={payload['status']}")
        print(f"normalized_sha256={payload['normalized_sha256']}")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        print("PARTIAL_OR_COMPOSITE_UNITS=1316")
        print("PARTIAL_OR_COMPOSITE_REQUIREMENTS=1391")
        print("ROUTE_OR_FORMAT_ONLY_UNITS=9")
        print("SEMANTIC_REVIEW_GROUPS=74")
        print("RUSSIAN_CONTENT_READY=false")
        print("CANONICAL_SEMANTIC_ADMISSIONS=0")
        print("RU_PROPOSAL_ADMISSIONS=0")
        print("FALSE_MASTERY_ADMISSIONS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
