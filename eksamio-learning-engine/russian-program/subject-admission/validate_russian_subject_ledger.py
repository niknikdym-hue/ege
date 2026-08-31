#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
BUILDER = HERE / "build_russian_subject_ledger.py"
COMPOSITES = HERE / "RUSSIAN-SUBJECT-REVIEWED-COMPOSITES-v0.1.json"
TASK_RELATION = PROGRAM / "ege-task-code-relation" / "FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json"

EXPECTED = {
    "admission_units_total": 1325,
    "requirements_total": 1400,
    "accepted_classification_units": 122,
    "accepted_classification_requirements": 125,
    "remaining_subject_review_units": 1203,
    "remaining_subject_review_requirements": 1275,
    "canonical_semantic_admissions": 0,
    "ru_proposal_admissions": 0,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_EXPRESSIVE_SET = {
    "RAU-170745c79503b789e72b",
    "RAU-359cfc7d0ad59a2f6e95",
    "RAU-6a7b2dccf1d2430a2777",
    "RAU-b5712ae284c6178d10fd",
    "RAU-f8b3979c6b1889dbb949",
}
EXPECTED_BROAD_ESSAY_SET = {
    "RAU-c898f2a0d0a257786030",
    "RAU-f1a4cbdba923a06d22e5",
    "RAU-99c275cbfd99491d687b",
    "RAU-be06422d548c67f8956d",
    "RAU-e27c1a25ffdf42be7cad",
    "RAU-f5726a12a14447bfe44a",
}


def _assert_partial_boundary(row: dict[str, Any]) -> None:
    boundary = row.get("mastery_boundary")
    if not isinstance(boundary, dict):
        raise AssertionError("composite mastery boundary missing")
    if boundary.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
        raise AssertionError("composite evidence may not emit exact component mastery")
    if boundary.get("component_mastery_requires_component_specific_independent_evidence") is not True:
        raise AssertionError("component-specific evidence guard weakened")


def main() -> int:
    namespace = runpy.run_path(str(BUILDER))
    ledger: dict[str, Any] = namespace["build_ledger"]()
    if ledger.get("status") != "RUSSIAN_FULL_SUBJECT_ACCEPTANCE_LEDGER_PARTIAL":
        raise AssertionError("aggregate ledger status drift")
    if ledger.get("summary") != EXPECTED:
        raise AssertionError(f"aggregate ledger progress drift: {ledger.get('summary')}")
    if ledger.get("by_disposition") != {
        "PARTIAL_OR_COMPOSITE": {"admission_units": 113, "requirements": 116},
        "ROUTE_OR_FORMAT_ONLY": {"admission_units": 9, "requirements": 9},
    }:
        raise AssertionError(f"unexpected disposition totals: {ledger.get('by_disposition')}")

    rows = ledger.get("dispositions")
    if not isinstance(rows, list) or len(rows) != 122:
        raise AssertionError("aggregate ledger must contain 122 exact unit rows")
    unit_ids = [str(row.get("admission_unit_id", "")) for row in rows]
    if len(unit_ids) != len(set(unit_ids)):
        raise AssertionError("aggregate ledger duplicates admission units")
    requirement_ids: list[str] = []
    for row in rows:
        members = row.get("members")
        if not isinstance(members, list) or not members:
            raise AssertionError(f"ledger row lacks exact members: {row.get('admission_unit_id')}")
        requirement_ids.extend(str(member.get("requirement_id", "")) for member in members)
        if any(not str(member.get("source_locator", "")) for member in members):
            raise AssertionError(f"ledger member lacks source locator: {row.get('admission_unit_id')}")
        if row.get("semantic_identity_ref") is not None:
            raise AssertionError("current aggregate slice must not directly admit a semantic identity")
    if len(requirement_ids) != len(set(requirement_ids)) or len(requirement_ids) != 125:
        raise AssertionError("aggregate ledger duplicates/misses exact requirements")

    expressive = [row for row in rows if row.get("decision_set_id") == "CB-RU13-EXPRESSIVE-BROAD-DOMAIN-001"]
    if {str(row["admission_unit_id"]) for row in expressive} != EXPECTED_EXPRESSIVE_SET:
        raise AssertionError("RU13 expressive reviewed set unit drift")
    if any(row.get("normalized_meaning") != "Распознавать и интерпретировать средства выразительности." for row in expressive):
        raise AssertionError("RU13 reviewed set escaped exact normalized meaning boundary")
    component_signatures = {
        (str(component.get("ref_kind", "")), str(component.get("ref", "")), str(component.get("status", "")))
        for row in expressive
        for component in row.get("component_refs", [])
    }
    if len(component_signatures) != 24:
        raise AssertionError(f"RU13 component inventory drift: {len(component_signatures)}")
    for row in expressive:
        _assert_partial_boundary(row)

    broad_essay = [row for row in rows if row.get("decision_set_id") == "CB-RU16-BROAD-ESSAY-COMPOSITE-001"]
    if {str(row["admission_unit_id"]) for row in broad_essay} != EXPECTED_BROAD_ESSAY_SET:
        raise AssertionError("broad essay composite exact-unit set drift")
    if len(broad_essay) != 6 or sum(len(row["members"]) for row in broad_essay) != 6:
        raise AssertionError("broad essay composite count drift")
    if any(row.get("normalized_meaning") != "Анализировать исходный текст и строить сочинение маршрута ЕГЭ." for row in broad_essay):
        raise AssertionError("broad essay set escaped exact normalized meaning boundary")
    if {str(row.get("priority_route")) for row in broad_essay} != {"EGE", "OGE", "SCHOOL"}:
        raise AssertionError("broad essay route/source heterogeneity was lost")
    broad_component_signatures = {
        (str(component.get("ref_kind", "")), str(component.get("ref", "")), str(component.get("status", "")))
        for row in broad_essay
        for component in row.get("component_refs", [])
    }
    if broad_component_signatures != {
        ("review_capability_boundary", "review-boundary:source-text-analysis", "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION"),
        ("review_capability_boundary", "review-boundary:route-essay-construction", "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION"),
    }:
        raise AssertionError("broad essay review boundaries drifted or became semantic authority")
    for row in broad_essay:
        if row.get("disposition") != "PARTIAL_OR_COMPOSITE":
            raise AssertionError("broad essay set escaped PARTIAL_OR_COMPOSITE")
        _assert_partial_boundary(row)

    composite_source = json.loads(COMPOSITES.read_text(encoding="utf-8"))
    if composite_source.get("summary") != {
        "reviewed_sets": 26,
        "accepted_classification_units": 102,
        "accepted_classification_requirements": 104,
        "semantic_admissions": 0,
    }:
        raise AssertionError("composite source summary drift")
    expected_set_ids = {f"CB-COMPOSITE-{number:03d}" for number in range(1, 27)}
    composite_rows = [row for row in rows if row.get("decision_set_id") in expected_set_ids]
    if len(composite_rows) != 102:
        raise AssertionError(f"exact composite classification row count drift: {len(composite_rows)}")
    if sum(len(row["members"]) for row in composite_rows) != 104:
        raise AssertionError("exact composite requirement count drift")
    if {str(row.get("decision_set_id")) for row in composite_rows} != expected_set_ids:
        raise AssertionError("composite reviewed set coverage drift")
    for row in composite_rows:
        if row.get("disposition") != "PARTIAL_OR_COMPOSITE":
            raise AssertionError("composite exact set escaped PARTIAL_OR_COMPOSITE")
        if ". " not in str(row.get("normalized_meaning", "")):
            raise AssertionError("composite classification lost its multi-capability exact meaning")
        components = row.get("component_refs")
        if not isinstance(components, list) or len(components) < 2:
            raise AssertionError("composite row lacks independent review capability boundaries")
        for component in components:
            if component.get("ref_kind") != "review_capability_boundary":
                raise AssertionError("derived composite component became semantic authority")
            if component.get("status") != "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION":
                raise AssertionError("review capability boundary admission guard weakened")
        _assert_partial_boundary(row)

    relation = json.loads(TASK_RELATION.read_text(encoding="utf-8"))
    task22 = next(row for row in relation["rows"] if row["task"] == 22)
    if "3.12" not in task22["requirement_code_expressions"]:
        raise AssertionError("merged FIPI task-22 -> requirement-code 3.12 authority drift")

    if ledger.get("policy") != {
        "every_disposition_is_exact_admission_unit_specific": True,
        "keyword_or_module_fanout_allowed": False,
        "review_batch_is_admission_authority": False,
        "component_ref_implies_semantic_admission": False,
    }:
        raise AssertionError("aggregate ledger admission policy weakened")

    print("RUSSIAN_SUBJECT_LEDGER=PASS")
    for key, value in EXPECTED.items():
        print(f"{key}={value}")
    print("ROUTE_OR_FORMAT_ONLY_UNITS=9")
    print("PARTIAL_OR_COMPOSITE_UNITS=113")
    print("EXACT_MULTI_CAPABILITY_COMPOSITE_UNITS=102")
    print("EXACT_MULTI_CAPABILITY_COMPOSITE_REQUIREMENTS=104")
    print("BROAD_ESSAY_COMPOSITE_UNITS=6")
    print("BROAD_ESSAY_COMPOSITE_REQUIREMENTS=6")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("FALSE_MASTERY_ADMISSIONS=0")
    print(f"NORMALIZED_LEDGER_SHA256={ledger['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
