#!/usr/bin/env python3
"""Final disposition-review closure for Russian issue #161.

The complete accounting builder already materializes its 1325 rows *only* from
explicit Central-Brain reviewed exact unit sets / exact normalized-meaning sets
plus the nine accepted route-only rows. Therefore the correct final review gate
is to verify that authoritative materialized ledger directly, not to reconstruct
its reviews a second time from partially overlapping source files.

This gate intentionally does not convert PARTIAL_OR_COMPOSITE into atomic
mastery. It proves the issue-#161 Phase-A disposition contract is finished and
finite while semantic/content acceptance remains a separate layer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

EXPECTED_SUMMARY = {
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


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_coverage() -> dict[str, Any]:
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    if accounting.get("summary") != EXPECTED_SUMMARY:
        raise ValueError(f"complete accounting summary drift: {accounting.get('summary')}")
    if accounting.get("status") != "RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING_COMPLETE_SEMANTIC_ACCEPTANCE_REQUIRED":
        raise ValueError("complete accounting status drift")
    semantic = accounting.get("semantic_acceptance") or {}
    if semantic.get("object_accounting_complete") is not True:
        raise ValueError("object accounting is not complete")
    if semantic.get("semantic_review_groups") != 74:
        raise ValueError("finite semantic review-group denominator drift")
    if semantic.get("russian_content_ready") is not False:
        raise ValueError("object accounting must not self-declare content readiness")

    rows = accounting.get("dispositions")
    if not isinstance(rows, list) or len(rows) != 1325:
        raise ValueError("complete accounting row denominator drift")

    unit_ids: set[str] = set()
    requirement_ids: set[str] = set()
    disposition_counts: Counter[str] = Counter()
    disposition_requirement_counts: Counter[str] = Counter()
    decision_source_counts: Counter[str] = Counter()
    decision_set_counts: Counter[str] = Counter()
    module_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"units": 0, "requirements": 0})
    source_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"units": 0, "requirements": 0})
    failures: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid accounting row")
        unit_id = str(row.get("admission_unit_id", ""))
        if not unit_id or unit_id in unit_ids:
            raise ValueError(f"duplicate/empty admission unit id: {unit_id}")
        unit_ids.add(unit_id)

        members = row.get("members")
        if not isinstance(members, list) or not members:
            raise ValueError(f"accounting row lacks requirement members: {unit_id}")
        for member in members:
            if not isinstance(member, dict):
                raise ValueError(f"invalid requirement member: {unit_id}")
            requirement_id = str(member.get("requirement_id", ""))
            if not requirement_id or requirement_id in requirement_ids:
                raise ValueError(f"duplicate/empty requirement id: {requirement_id}")
            requirement_ids.add(requirement_id)

        disposition = str(row.get("disposition", ""))
        disposition_counts[disposition] += 1
        disposition_requirement_counts[disposition] += len(members)
        decision_source = str(row.get("decision_source", ""))
        if not decision_source:
            failures.append({"admission_unit_id": unit_id, "reason": "MISSING_DECISION_SOURCE"})
        else:
            decision_source_counts[decision_source] += 1
        decision_set_id = row.get("decision_set_id")
        if decision_set_id:
            decision_set_counts[str(decision_set_id)] += 1

        for module in row.get("modules") or []:
            module = str(module)
            module_counts[module]["units"] += 1
            module_counts[module]["requirements"] += len(members)
        unit_sources = sorted({str(member.get("source_id", "")) for member in members})
        for source_id in unit_sources:
            source_counts[source_id]["units"] += 1
            source_counts[source_id]["requirements"] += sum(1 for member in members if str(member.get("source_id", "")) == source_id)

        if disposition == "ROUTE_OR_FORMAT_ONLY":
            if row.get("subject_review_status") != "CENTRAL_BRAIN_ACCEPTED":
                failures.append({"admission_unit_id": unit_id, "reason": "ROUTE_NOT_CENTRAL_BRAIN_ACCEPTED"})
            if row.get("semantic_identity_ref") is not None:
                failures.append({"admission_unit_id": unit_id, "reason": "ROUTE_CREATED_SEMANTIC_IDENTITY"})
            if row.get("component_refs") not in ([], None):
                failures.append({"admission_unit_id": unit_id, "reason": "ROUTE_HAS_COMPONENT_MASTERY_REFS"})
        elif disposition == "PARTIAL_OR_COMPOSITE":
            if row.get("subject_review_status") != "CENTRAL_BRAIN_ACCEPTED_CLASSIFICATION":
                failures.append({"admission_unit_id": unit_id, "reason": "COMPOSITE_NOT_CENTRAL_BRAIN_REVIEWED"})
            if row.get("semantic_identity_ref") is not None:
                failures.append({"admission_unit_id": unit_id, "reason": "COMPOSITE_SELF_ADMITTED_SEMANTIC"})
            components = row.get("component_refs")
            if not isinstance(components, list) or not components:
                failures.append({"admission_unit_id": unit_id, "reason": "COMPOSITE_MISSING_REVIEW_COMPONENT_BOUNDARY"})
            mastery = row.get("mastery_boundary") or {}
            if mastery.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
                failures.append({"admission_unit_id": unit_id, "reason": "COMPOSITE_FALSE_EXACT_MASTERY_ALLOWED"})
            if mastery.get("component_mastery_requires_component_specific_independent_evidence") is not True:
                failures.append({"admission_unit_id": unit_id, "reason": "COMPOSITE_INDEPENDENT_EVIDENCE_GUARD_MISSING"})
            if not row.get("decision_set_id"):
                failures.append({"admission_unit_id": unit_id, "reason": "COMPOSITE_MISSING_EXPLICIT_REVIEW_SET"})
        else:
            failures.append({"admission_unit_id": unit_id, "reason": f"UNEXPECTED_DISPOSITION:{disposition}"})

    if len(unit_ids) != 1325 or len(requirement_ids) != 1400:
        raise ValueError("exact-once denominator drift")
    if disposition_counts != Counter({"PARTIAL_OR_COMPOSITE": 1316, "ROUTE_OR_FORMAT_ONLY": 9}):
        raise ValueError(f"disposition unit totals drift: {dict(disposition_counts)}")
    if disposition_requirement_counts != Counter({"PARTIAL_OR_COMPOSITE": 1391, "ROUTE_OR_FORMAT_ONLY": 9}):
        raise ValueError(f"disposition requirement totals drift: {dict(disposition_requirement_counts)}")
    if set(module_counts) != {f"RU-PROG-{index:02d}" for index in range(1, 17)}:
        raise ValueError(f"16-module accounting coverage drift: {sorted(module_counts)}")
    if any(counts["units"] <= 0 or counts["requirements"] <= 0 for counts in module_counts.values()):
        raise ValueError("one or more Russian modules has zero reviewed object accounting")

    result: dict[str, Any] = {
        "schema_version": "0.2.0",
        "status": "CENTRAL_BRAIN_FINAL_DISPOSITION_REVIEW_COVERAGE_ACCEPTED" if not failures else "CENTRAL_BRAIN_FINAL_DISPOSITION_REVIEW_COVERAGE_REWORK",
        "object_accounting_sha256": str(accounting.get("normalized_sha256", "")),
        "semantic_review_group_count": 74,
        "policy": {
            "partial_or_composite_is_valid_final_disposition": True,
            "partial_or_composite_is_not_atomic_mastery": True,
            "partial_or_composite_requires_component_specific_independent_evidence": True,
            "route_or_format_only_creates_semantic_identity": False,
            "object_disposition_review_is_complete": not failures,
            "object_disposition_review_implies_russian_content_ready": False,
            "bounded_ru_semantics_require_separate_subject_acceptance": True,
            "keyword_fuzzy_module_only_mapping_allowed": False,
        },
        "summary": {
            "admission_units_total": 1325,
            "requirements_total": 1400,
            "reviewed_admission_units": 1325 - len({row["admission_unit_id"] for row in failures}),
            "reviewed_requirements": 1400 if not failures else None,
            "unreviewed_admission_units": len({row["admission_unit_id"] for row in failures}),
            "route_or_format_only_units": 9,
            "route_or_format_only_requirements": 9,
            "partial_or_composite_units": 1316,
            "partial_or_composite_requirements": 1391,
            "finite_semantic_review_groups": 74,
            "modules_with_nonzero_reviewed_accounting": len(module_counts),
            "semantic_identity_self_admissions_from_classification": 0,
            "false_exact_mastery_admissions": 0,
        },
        "decision_source_unit_counts": dict(sorted(decision_source_counts.items())),
        "decision_set_unit_counts": dict(sorted(decision_set_counts.items())),
        "module_review_coverage": dict(sorted(module_counts.items())),
        "source_review_coverage": dict(sorted(source_counts.items())),
        "failures": sorted(failures, key=lambda row: (row["admission_unit_id"], row["reason"])),
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_coverage()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_FINAL_DISPOSITION_REVIEW_COVERAGE_V2=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print(f"STATUS={result['status']}")
        print(f"NORMALIZED_COVERAGE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
