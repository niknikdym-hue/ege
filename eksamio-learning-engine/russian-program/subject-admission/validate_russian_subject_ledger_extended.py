#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BUILDER = HERE / "build_russian_subject_ledger_extended.py"
MULTI_AUTHORITY = HERE / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITE-MEANINGS-v0.1.json"
BROAD_AUTHORITY = HERE / "RUSSIAN-SUBJECT-REVIEWED-BROAD-DOMAIN-MEANINGS-v0.1.json"
EXPECTED_SUMMARY = {
    "admission_units_total": 1325,
    "requirements_total": 1400,
    "accepted_classification_units": 839,
    "accepted_classification_requirements": 883,
    "remaining_subject_review_units": 486,
    "remaining_subject_review_requirements": 517,
    "canonical_semantic_admissions": 0,
    "ru_proposal_admissions": 0,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_DISPOSITIONS = {
    "PARTIAL_OR_COMPOSITE": {"admission_units": 830, "requirements": 874},
    "ROUTE_OR_FORMAT_ONLY": {"admission_units": 9, "requirements": 9},
}
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
EXPECTED_BROAD_MEANINGS = {
    "Анализировать синтаксическую конструкцию и её нормативность.": (153, 160),
    "Выбирать нормативные знаки препинания в конструкции.": (7, 7),
    "Контролировать речевую нормативность и исправлять нарушения.": (160, 167),
    "Применять орфографическое правило к слову или форме.": (24, 27),
}


def _assert_mastery_boundary(row: dict[str, Any]) -> None:
    boundary = row.get("mastery_boundary")
    if not isinstance(boundary, dict):
        raise AssertionError("partial/composite mastery boundary missing")
    if boundary.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
        raise AssertionError("generic domain evidence can emit false exact mastery")
    if boundary.get("generic_domain_attempt_can_emit_partial_or_composite_evidence") is not True:
        raise AssertionError("partial/composite evidence boundary drift")
    if boundary.get("component_mastery_requires_component_specific_independent_evidence") is not True:
        raise AssertionError("component-specific evidence guard weakened")


def main() -> int:
    multi_authority = json.loads(MULTI_AUTHORITY.read_text(encoding="utf-8"))
    if multi_authority.get("expected_materialized_summary") != EXPECTED_MULTI:
        raise AssertionError("reuse composite meaning authority expected totals drift")
    multi_meanings = multi_authority.get("exact_normalized_meanings")
    if not isinstance(multi_meanings, list) or len(multi_meanings) != 39 or len(set(multi_meanings)) != 39:
        raise AssertionError("reuse composite meaning authority coverage drift")
    if any(not isinstance(meaning, str) or ". " not in meaning for meaning in multi_meanings):
        raise AssertionError("reuse composite meaning authority contains an atomic/non-exact review meaning")

    broad_authority = json.loads(BROAD_AUTHORITY.read_text(encoding="utf-8"))
    if broad_authority.get("expected_materialized_summary") != EXPECTED_BROAD:
        raise AssertionError("broad-domain authority expected totals drift")
    broad_meanings = broad_authority.get("exact_normalized_meanings")
    if set(broad_meanings or []) != set(EXPECTED_BROAD_MEANINGS):
        raise AssertionError("broad-domain exact meaning authority drift")
    broad_policy = broad_authority.get("policy", {})
    if broad_policy.get("broad_domain_is_not_atomic_mastery") is not True:
        raise AssertionError("broad-domain non-atomic mastery guard weakened")
    if broad_policy.get("generic_domain_attempt_can_emit_exact_component_mastery") is not False:
        raise AssertionError("broad-domain generic evidence may emit exact mastery")

    for authority in (multi_authority, broad_authority):
        if authority.get("selection_rule") != "EXACT_NORMALIZED_MEANING_EQUALITY_WITHIN_PINNED_REVIEW_SLICE_ONLY":
            raise AssertionError("exact meaning selection rule weakened")
        policy = authority.get("policy", {})
        if policy.get("keyword_or_fuzzy_inference_allowed") is not False:
            raise AssertionError("keyword/fuzzy review inference was enabled")
        if policy.get("classification_only_no_semantic_admission") is not True:
            raise AssertionError("reviewed meaning authority escaped classification-only mode")

    namespace = runpy.run_path(str(BUILDER))
    materialize = namespace["materialize_reviewed_sets"]
    base_namespace = runpy.run_path(str(HERE / "build_russian_subject_ledger.py"))
    base_ledger = base_namespace["build_ledger"]()

    multi_materialized: dict[str, Any] = materialize(
        base_ledger,
        authority_path=MULTI_AUTHORITY,
        set_prefix="CB-REUSE-COMPOSITE",
        expected=namespace["EXPECTED_MULTI"],
        require_multi_clause=True,
        broad_domain=False,
    )
    if multi_materialized.get("summary") != EXPECTED_MULTI:
        raise AssertionError(f"reuse composite materialized totals drift: {multi_materialized.get('summary')}")
    multi_sets = multi_materialized.get("reviewed_sets")
    expected_multi_ids = {f"CB-REUSE-COMPOSITE-{number:03d}" for number in range(1, 40)}
    if not isinstance(multi_sets, list) or {str(row.get("set_id")) for row in multi_sets} != expected_multi_ids:
        raise AssertionError("reuse composite materialization set coverage drift")
    if {str(row.get("expected_normalized_meaning")) for row in multi_sets} != set(multi_meanings):
        raise AssertionError("reuse composite materialization escaped exact accepted meanings")

    broad_materialized: dict[str, Any] = materialize(
        base_ledger,
        authority_path=BROAD_AUTHORITY,
        set_prefix="CB-BROAD-DOMAIN",
        expected=namespace["EXPECTED_BROAD"],
        require_multi_clause=False,
        broad_domain=True,
    )
    if broad_materialized.get("summary") != EXPECTED_BROAD:
        raise AssertionError(f"broad-domain materialized totals drift: {broad_materialized.get('summary')}")
    broad_sets = broad_materialized.get("reviewed_sets")
    expected_broad_ids = {f"CB-BROAD-DOMAIN-{number:03d}" for number in range(1, 5)}
    if not isinstance(broad_sets, list) or {str(row.get("set_id")) for row in broad_sets} != expected_broad_ids:
        raise AssertionError("broad-domain materialization set coverage drift")
    for row in broad_sets:
        meaning = str(row.get("expected_normalized_meaning", ""))
        expected_counts = EXPECTED_BROAD_MEANINGS.get(meaning)
        if expected_counts is None:
            raise AssertionError("broad-domain materialization escaped exact authority")
        unit_count = len(row.get("exact_admission_unit_ids", []))
        req_count = len(row.get("exact_requirement_ids", []))
        if (unit_count, req_count) != expected_counts:
            raise AssertionError(f"broad-domain exact counts drift for {meaning}: {(unit_count, req_count)}")
        components = row.get("components")
        if not isinstance(components, list) or len(components) != 2:
            raise AssertionError("broad-domain set must carry two non-semantic audit boundaries")
        if any(component.get("ref_kind") != "review_capability_boundary" for component in components):
            raise AssertionError("broad-domain audit boundary became semantic authority")
        if any(component.get("status") != "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION" for component in components):
            raise AssertionError("broad-domain non-semantic boundary status weakened")
        _assert_mastery_boundary(row)

    ledger: dict[str, Any] = namespace["build_ledger"]()
    if ledger.get("summary") != EXPECTED_SUMMARY:
        raise AssertionError(f"extended exact ledger totals drift: {ledger.get('summary')}")
    if ledger.get("by_disposition") != EXPECTED_DISPOSITIONS:
        raise AssertionError(f"extended exact ledger disposition totals drift: {ledger.get('by_disposition')}")

    rows = ledger.get("dispositions")
    if not isinstance(rows, list) or len(rows) != 839:
        raise AssertionError("extended ledger must contain exactly 839 exact classification rows")
    unit_ids = [str(row.get("admission_unit_id", "")) for row in rows]
    if len(unit_ids) != len(set(unit_ids)):
        raise AssertionError("extended ledger duplicates admission units")
    requirement_ids = [
        str(member.get("requirement_id", ""))
        for row in rows
        for member in row.get("members", [])
    ]
    if len(requirement_ids) != 883 or len(requirement_ids) != len(set(requirement_ids)):
        raise AssertionError("extended ledger duplicates or misses exact requirements")

    multi_rows = [row for row in rows if str(row.get("decision_set_id", "")).startswith("CB-REUSE-COMPOSITE-")]
    if len(multi_rows) != 373 or sum(len(row.get("members", [])) for row in multi_rows) != 397:
        raise AssertionError("reviewed reuse composite exact totals drift")
    if {str(row.get("decision_set_id")) for row in multi_rows} != expected_multi_ids:
        raise AssertionError("extended ledger omitted a reviewed reuse composite set")

    broad_rows = [row for row in rows if str(row.get("decision_set_id", "")).startswith("CB-BROAD-DOMAIN-")]
    if len(broad_rows) != 344 or sum(len(row.get("members", [])) for row in broad_rows) != 361:
        raise AssertionError("reviewed broad-domain exact totals drift")
    if {str(row.get("decision_set_id")) for row in broad_rows} != expected_broad_ids:
        raise AssertionError("extended ledger omitted a reviewed broad-domain set")

    for row in multi_rows + broad_rows:
        if row.get("disposition") != "PARTIAL_OR_COMPOSITE":
            raise AssertionError("reviewed exact classification escaped PARTIAL_OR_COMPOSITE")
        if row.get("semantic_identity_ref") is not None:
            raise AssertionError("reviewed exact classification admitted a semantic identity")
        components = row.get("component_refs")
        if not isinstance(components, list) or len(components) < 2:
            raise AssertionError("reviewed exact classification lacks non-semantic review boundaries")
        for component in components:
            if component.get("ref_kind") != "review_capability_boundary":
                raise AssertionError("review boundary became semantic authority")
            if component.get("status") != "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION":
                raise AssertionError("review boundary admission guard weakened")
        _assert_mastery_boundary(row)

    print("RUSSIAN_SUBJECT_LEDGER_EXTENDED=PASS")
    for key, value in EXPECTED_SUMMARY.items():
        print(f"{key}={value}")
    print("ROUTE_OR_FORMAT_ONLY_UNITS=9")
    print("PARTIAL_OR_COMPOSITE_UNITS=830")
    print("REUSE_TARGET_MULTI_COMPOSITE_UNITS=373")
    print("REUSE_TARGET_MULTI_COMPOSITE_REQUIREMENTS=397")
    print("BROAD_DOMAIN_COMPOSITE_UNITS=344")
    print("BROAD_DOMAIN_COMPOSITE_REQUIREMENTS=361")
    print("CANONICAL_SEMANTIC_ADMISSIONS=0")
    print("RU_PROPOSAL_ADMISSIONS=0")
    print("FALSE_MASTERY_ADMISSIONS=0")
    print(f"NORMALIZED_LEDGER_SHA256={ledger['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
