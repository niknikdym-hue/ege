#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BUILDER = HERE / "build_russian_subject_ledger_extended.py"
MEANING_AUTHORITY = HERE / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITE-MEANINGS-v0.1.json"
EXPECTED_SUMMARY = {
    "admission_units_total": 1325,
    "requirements_total": 1400,
    "accepted_classification_units": 495,
    "accepted_classification_requirements": 522,
    "remaining_subject_review_units": 830,
    "remaining_subject_review_requirements": 878,
    "canonical_semantic_admissions": 0,
    "ru_proposal_admissions": 0,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_DISPOSITIONS = {
    "PARTIAL_OR_COMPOSITE": {"admission_units": 486, "requirements": 513},
    "ROUTE_OR_FORMAT_ONLY": {"admission_units": 9, "requirements": 9},
}
EXPECTED_MATERIALIZED = {
    "reviewed_meanings": 39,
    "accepted_classification_units": 373,
    "accepted_classification_requirements": 397,
    "semantic_admissions": 0,
}


def main() -> int:
    authority = json.loads(MEANING_AUTHORITY.read_text(encoding="utf-8"))
    if authority.get("expected_materialized_summary") != EXPECTED_MATERIALIZED:
        raise AssertionError("reuse composite meaning authority expected totals drift")
    meanings = authority.get("exact_normalized_meanings")
    if not isinstance(meanings, list) or len(meanings) != 39 or len(set(meanings)) != 39:
        raise AssertionError("reuse composite meaning authority coverage drift")
    if any(not isinstance(meaning, str) or ". " not in meaning for meaning in meanings):
        raise AssertionError("reuse composite meaning authority contains an atomic/non-exact review meaning")
    if authority.get("selection_rule") != "EXACT_NORMALIZED_MEANING_EQUALITY_WITHIN_PINNED_REVIEW_SLICE_ONLY":
        raise AssertionError("reuse composite meaning selection rule weakened")
    policy = authority.get("policy", {})
    if policy.get("keyword_or_fuzzy_inference_allowed") is not False:
        raise AssertionError("keyword/fuzzy review inference was enabled")
    if policy.get("classification_only_no_semantic_admission") is not True:
        raise AssertionError("reuse composite meaning authority escaped classification-only mode")

    namespace = runpy.run_path(str(BUILDER))
    materialize = namespace["materialize_reviewed_sets"]
    # The materializer itself needs the existing base ledger solely to subtract
    # already dispositioned exact units before selecting exact normalized meanings.
    base_namespace = runpy.run_path(str(HERE / "build_russian_subject_ledger.py"))
    base_ledger = base_namespace["build_ledger"]()
    materialized: dict[str, Any] = materialize(base_ledger)
    if materialized.get("summary") != EXPECTED_MATERIALIZED:
        raise AssertionError(f"reuse composite materialized totals drift: {materialized.get('summary')}")
    materialized_sets = materialized.get("reviewed_sets")
    if not isinstance(materialized_sets, list) or len(materialized_sets) != 39:
        raise AssertionError("reuse composite materialization set count drift")
    expected_set_ids = {f"CB-REUSE-COMPOSITE-{number:03d}" for number in range(1, 40)}
    if {str(row.get("set_id")) for row in materialized_sets} != expected_set_ids:
        raise AssertionError("reuse composite materialization set ids drift")
    if {str(row.get("expected_normalized_meaning")) for row in materialized_sets} != set(meanings):
        raise AssertionError("reuse composite materialization escaped exact accepted meanings")

    ledger: dict[str, Any] = namespace["build_ledger"]()
    if ledger.get("summary") != EXPECTED_SUMMARY:
        raise AssertionError(f"extended exact ledger totals drift: {ledger.get('summary')}")
    if ledger.get("by_disposition") != EXPECTED_DISPOSITIONS:
        raise AssertionError(f"extended exact ledger disposition totals drift: {ledger.get('by_disposition')}")

    rows = ledger.get("dispositions")
    if not isinstance(rows, list) or len(rows) != 495:
        raise AssertionError("extended ledger must contain exactly 495 exact classification rows")
    unit_ids = [str(row.get("admission_unit_id", "")) for row in rows]
    if len(unit_ids) != len(set(unit_ids)):
        raise AssertionError("extended ledger duplicates admission units")
    requirement_ids = [
        str(member.get("requirement_id", ""))
        for row in rows
        for member in row.get("members", [])
    ]
    if len(requirement_ids) != 522 or len(requirement_ids) != len(set(requirement_ids)):
        raise AssertionError("extended ledger duplicates or misses exact requirements")

    reuse_rows = [
        row for row in rows
        if str(row.get("decision_set_id", "")).startswith("CB-REUSE-COMPOSITE-")
    ]
    if len(reuse_rows) != 373:
        raise AssertionError(f"reviewed reuse composite row count drift: {len(reuse_rows)}")
    if sum(len(row.get("members", [])) for row in reuse_rows) != 397:
        raise AssertionError("reviewed reuse composite requirement count drift")
    if {str(row.get("decision_set_id")) for row in reuse_rows} != expected_set_ids:
        raise AssertionError("extended ledger omitted a reviewed reuse composite set")

    for row in reuse_rows:
        if row.get("disposition") != "PARTIAL_OR_COMPOSITE":
            raise AssertionError("reviewed reuse row escaped PARTIAL_OR_COMPOSITE")
        if row.get("semantic_identity_ref") is not None:
            raise AssertionError("reviewed reuse classification admitted a semantic identity")
        meaning = str(row.get("normalized_meaning", ""))
        if meaning not in set(meanings):
            raise AssertionError("reviewed reuse ledger row escaped exact accepted meaning authority")
        components = row.get("component_refs")
        if not isinstance(components, list) or len(components) < 2:
            raise AssertionError("reviewed reuse row lacks derived capability boundaries")
        for component in components:
            if component.get("ref_kind") != "review_capability_boundary":
                raise AssertionError("reviewed reuse component became semantic authority")
            if component.get("status") != "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION":
                raise AssertionError("reviewed reuse component admission guard weakened")
        boundary = row.get("mastery_boundary")
        if not isinstance(boundary, dict):
            raise AssertionError("reviewed reuse mastery boundary missing")
        if boundary.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
            raise AssertionError("reviewed reuse generic evidence can emit false exact mastery")
        if boundary.get("generic_domain_attempt_can_emit_partial_or_composite_evidence") is not True:
            raise AssertionError("reviewed reuse partial/composite evidence boundary drift")
        if boundary.get("component_mastery_requires_component_specific_independent_evidence") is not True:
            raise AssertionError("reviewed reuse component-specific evidence guard weakened")

    print("RUSSIAN_SUBJECT_LEDGER_EXTENDED=PASS")
    for key, value in EXPECTED_SUMMARY.items():
        print(f"{key}={value}")
    print("ROUTE_OR_FORMAT_ONLY_UNITS=9")
    print("PARTIAL_OR_COMPOSITE_UNITS=486")
    print("REUSE_TARGET_COMPOSITE_UNITS=373")
    print("REUSE_TARGET_COMPOSITE_REQUIREMENTS=397")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("FALSE_MASTERY_ADMISSIONS=0")
    print(f"NORMALIZED_LEDGER_SHA256={ledger['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
