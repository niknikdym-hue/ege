#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
BUILDER = HERE / "build_russian_subject_ledger.py"
TASK_RELATION = PROGRAM / "ege-task-code-relation" / "FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json"

EXPECTED = {
    "admission_units_total": 1325,
    "requirements_total": 1400,
    "accepted_classification_units": 14,
    "accepted_classification_requirements": 15,
    "remaining_subject_review_units": 1311,
    "remaining_subject_review_requirements": 1385,
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
EXPECTED_EXPRESSIVE_REQUIREMENTS = {
    "RSK-EDSOO59-8-1-P201",
    "RSK-OGE_COD-1-1-2-P002",
    "RSK-EDSOO59-8-1-P227",
    "RSK-EDSOO59-8-1-P231",
    "RSK-EGE_COD-3-12-P004",
    "RSK-EGE_COD-1-1-1-P002",
}


def main() -> int:
    namespace = runpy.run_path(str(BUILDER))
    ledger: dict[str, Any] = namespace["build_ledger"]()
    if ledger.get("status") != "RUSSIAN_FULL_SUBJECT_ACCEPTANCE_LEDGER_PARTIAL":
        raise AssertionError("aggregate ledger status drift")
    if ledger.get("summary") != EXPECTED:
        raise AssertionError(f"aggregate ledger progress drift: {ledger.get('summary')}")

    by_disposition = ledger.get("by_disposition")
    if by_disposition != {
        "PARTIAL_OR_COMPOSITE": {"admission_units": 5, "requirements": 6},
        "ROUTE_OR_FORMAT_ONLY": {"admission_units": 9, "requirements": 9},
    }:
        raise AssertionError(f"unexpected disposition totals: {by_disposition}")

    rows = ledger.get("dispositions")
    if not isinstance(rows, list) or len(rows) != 14:
        raise AssertionError("aggregate ledger must contain 14 exact unit rows")
    unit_ids = [str(row.get("admission_unit_id", "")) for row in rows]
    if len(unit_ids) != len(set(unit_ids)):
        raise AssertionError("aggregate ledger duplicates admission units")
    requirement_ids: list[str] = []
    for row in rows:
        members = row.get("members")
        if not isinstance(members, list) or not members:
            raise AssertionError(f"ledger row lacks exact members: {row.get('admission_unit_id')}")
        for member in members:
            if not isinstance(member, dict) or not str(member.get("source_locator", "")):
                raise AssertionError(f"ledger member lacks source locator: {row.get('admission_unit_id')}")
            requirement_ids.append(str(member.get("requirement_id", "")))
        if row.get("semantic_identity_ref") is not None:
            raise AssertionError("current aggregate slice must not directly admit a semantic identity")
    if len(requirement_ids) != len(set(requirement_ids)) or len(requirement_ids) != 15:
        raise AssertionError("aggregate ledger duplicates/misses exact requirements")

    expressive = [
        row for row in rows
        if row.get("decision_set_id") == "CB-RU13-EXPRESSIVE-BROAD-DOMAIN-001"
    ]
    if {str(row["admission_unit_id"]) for row in expressive} != EXPECTED_EXPRESSIVE_SET:
        raise AssertionError("RU13 expressive reviewed set unit drift")
    expressive_requirements = {
        str(member["requirement_id"])
        for row in expressive
        for member in row["members"]
    }
    if expressive_requirements != EXPECTED_EXPRESSIVE_REQUIREMENTS:
        raise AssertionError("RU13 expressive reviewed set requirement drift")
    if any(row.get("normalized_meaning") != "Распознавать и интерпретировать средства выразительности." for row in expressive):
        raise AssertionError("RU13 reviewed set escaped exact normalized meaning boundary")
    if any(row.get("disposition") != "PARTIAL_OR_COMPOSITE" for row in expressive):
        raise AssertionError("RU13 broad-domain set must remain PARTIAL_OR_COMPOSITE")

    component_signatures = {
        (
            str(component.get("ref_kind", "")),
            str(component.get("ref", "")),
            str(component.get("status", "")),
        )
        for row in expressive
        for component in row.get("component_refs", [])
    }
    if len(component_signatures) != 24:
        raise AssertionError(f"RU13 component inventory drift: {len(component_signatures)}")
    new_content = {
        ref
        for kind, ref, status in component_signatures
        if kind == "proposed_semantic_with_content" and status == "PROPOSED_NOT_CANONICAL"
    }
    if len(new_content) != 14:
        raise AssertionError("RU13 newly materialized component count drift")
    existing = {
        ref
        for kind, ref, status in component_signatures
        if kind == "existing_semantic_candidate" and status.endswith("NOT_ADMITTED_BY_THIS_SET")
    }
    if existing != {f"candidate-{number:03d}" for number in range(33, 43)}:
        raise AssertionError("RU13 existing candidate component inventory drift")
    if "candidate-039" not in existing:
        raise AssertionError("rhetorical-address existing boundary was lost")

    for row in expressive:
        boundary = row.get("mastery_boundary")
        if not isinstance(boundary, dict):
            raise AssertionError("RU13 composite mastery boundary missing")
        if boundary.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
            raise AssertionError("generic expressive-domain evidence may not emit exact component mastery")
        if boundary.get("component_mastery_requires_component_specific_independent_evidence") is not True:
            raise AssertionError("component-specific independent evidence guard weakened")

    relation = json.loads(TASK_RELATION.read_text(encoding="utf-8"))
    task22 = next(row for row in relation["rows"] if row["task"] == 22)
    if "3.12" not in task22["requirement_code_expressions"]:
        raise AssertionError("merged FIPI task-22 -> requirement-code 3.12 authority drift")
    ege_312 = next(row for row in expressive if row["admission_unit_id"] == "RAU-b5712ae284c6178d10fd")
    if ege_312["members"][0]["code"] != "3.12" or ege_312["members"][0]["source_id"] != "FIPI-EGE-RU-2026-FINAL":
        raise AssertionError("RU13 task-22 exact source binding drift")

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
    print("PARTIAL_OR_COMPOSITE_UNITS=5")
    print("RU13_BROAD_DOMAIN_COMPONENTS=24")
    print("RU13_NEW_CONTENT_COMPONENTS=14")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("FALSE_MASTERY_ADMISSIONS=0")
    print(f"NORMALIZED_LEDGER_SHA256={ledger['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
