#!/usr/bin/env python3
from __future__ import annotations

import runpy
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BUILDER = HERE / "build_russian_subject_accounting_complete.py"
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


def main() -> int:
    namespace = runpy.run_path(str(BUILDER))
    payload: dict[str, Any] = namespace["build_accounting"]()
    if payload.get("status") != "RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING_COMPLETE_SEMANTIC_ACCEPTANCE_REQUIRED":
        raise AssertionError("full object-accounting status drift")
    if payload.get("summary") != EXPECTED_SUMMARY:
        raise AssertionError(f"full object-accounting totals drift: {payload.get('summary')}")
    if payload.get("by_disposition") != {
        "PARTIAL_OR_COMPOSITE": {"admission_units": 1316, "requirements": 1391},
        "ROUTE_OR_FORMAT_ONLY": {"admission_units": 9, "requirements": 9},
    }:
        raise AssertionError(f"full object-accounting disposition totals drift: {payload.get('by_disposition')}")

    rows = payload.get("dispositions")
    if not isinstance(rows, list) or len(rows) != 1325:
        raise AssertionError("full object accounting must contain exactly 1325 admission-unit rows")
    unit_ids = [str(row.get("admission_unit_id", "")) for row in rows]
    if len(unit_ids) != len(set(unit_ids)):
        raise AssertionError("full object accounting duplicates an admission unit")
    requirement_ids = [
        str(member.get("requirement_id", ""))
        for row in rows
        for member in row.get("members", [])
    ]
    if len(requirement_ids) != 1400 or len(requirement_ids) != len(set(requirement_ids)):
        raise AssertionError("full object accounting duplicates or misses an official requirement")

    partial = [row for row in rows if row.get("disposition") == "PARTIAL_OR_COMPOSITE"]
    route = [row for row in rows if row.get("disposition") == "ROUTE_OR_FORMAT_ONLY"]
    if len(partial) != 1316 or sum(len(row.get("members", [])) for row in partial) != 1391:
        raise AssertionError("partial/composite exact totals drift")
    if len(route) != 9 or sum(len(row.get("members", [])) for row in route) != 9:
        raise AssertionError("route/format exact totals drift")

    for row in partial:
        if row.get("semantic_identity_ref") is not None:
            raise AssertionError("object accounting admitted a semantic identity")
        components = row.get("component_refs")
        if not isinstance(components, list) or len(components) < 2:
            raise AssertionError(f"partial/composite row lacks non-semantic audit boundaries: {row.get('admission_unit_id')}")
        for component in components:
            kind = component.get("ref_kind")
            status = str(component.get("status", ""))
            if kind == "review_capability_boundary":
                if status != "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION":
                    raise AssertionError("review capability boundary admission guard weakened")
            elif kind == "existing_semantic_candidate":
                if not status.endswith("NOT_ADMITTED_BY_THIS_SET"):
                    raise AssertionError("existing semantic candidate was silently admitted")
            elif kind == "proposed_semantic_with_content":
                if status != "PROPOSED_NOT_CANONICAL":
                    raise AssertionError("proposed semantic with content was silently canonicalized")
            else:
                raise AssertionError(f"unsupported partial/composite component kind: {kind}")
        boundary = row.get("mastery_boundary")
        if not isinstance(boundary, dict):
            raise AssertionError("partial/composite row lacks mastery boundary")
        if boundary.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
            raise AssertionError("generic domain evidence can emit false exact mastery")
        if boundary.get("component_mastery_requires_component_specific_independent_evidence") is not True:
            raise AssertionError("component-specific evidence guard weakened")

    for row in route:
        if row.get("semantic_identity_ref") is not None or row.get("component_refs"):
            raise AssertionError("route/format metadata created learner semantics")

    semantic = payload.get("semantic_acceptance")
    if not isinstance(semantic, dict):
        raise AssertionError("full accounting lacks explicit semantic-acceptance boundary")
    if semantic.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise AssertionError("semantic acceptance was silently completed")
    if semantic.get("russian_content_ready") is not False:
        raise AssertionError("object accounting was misrepresented as Russian content readiness")
    if semantic.get("object_accounting_complete") is not True:
        raise AssertionError("object accounting completion flag drift")
    if semantic.get("canonical_semantic_admissions") != 0 or semantic.get("ru_proposal_admissions") != 0:
        raise AssertionError("semantic admissions are nonzero before subject acceptance")
    groups = semantic.get("groups")
    if not isinstance(groups, list) or len(groups) != 74:
        raise AssertionError("finite semantic review group count drift")
    meanings = [str(row.get("normalized_meaning", "")) for row in groups]
    if len(meanings) != len(set(meanings)):
        raise AssertionError("finite semantic review groups duplicate normalized meanings")
    if sum(int(row.get("admission_units", 0)) for row in groups) != 1316:
        raise AssertionError("semantic review groups do not cover every learner-semantic admission unit")
    if sum(int(row.get("requirements", 0)) for row in groups) != 1391:
        raise AssertionError("semantic review groups do not cover every learner-semantic requirement")
    if any(row.get("status") != "SEMANTIC_DECOMPOSITION_OR_EXACT_MAPPING_REQUIRED" for row in groups):
        raise AssertionError("semantic review group was silently accepted")

    decision_sources = Counter(str(row.get("decision_source", "")) for row in rows)
    if sum(decision_sources.values()) != 1325:
        raise AssertionError("decision-source accounting drift")

    print("RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING=PASS")
    print("ADMISSION_UNITS_ACCOUNTED=1325/1325")
    print("REQUIREMENTS_ACCOUNTED=1400/1400")
    print("PARTIAL_OR_COMPOSITE=1316/1391")
    print("ROUTE_OR_FORMAT_ONLY=9/9")
    print("SEMANTIC_REVIEW_GROUPS=74")
    print("SEMANTIC_ACCEPTANCE_REQUIRED=true")
    print("RUSSIAN_CONTENT_READY=false")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("FALSE_MASTERY_ADMISSIONS=0")
    print(f"NORMALIZED_ACCOUNTING_SHA256={payload['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
