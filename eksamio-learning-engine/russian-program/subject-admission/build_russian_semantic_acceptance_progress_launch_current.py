#!/usr/bin/env python3
"""Current Sep-1 launch semantic-progress view layered over the historical progress builder."""
from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LEGACY = HERE / "build_russian_semantic_acceptance_progress.py"
LEGACY_OGE_AUTHORITY = HERE / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
NEW_6_2_AUTHORITY = (
    HERE / "RUSSIAN-OGE-6.2-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_2_CANONICAL_COMPONENT_SET",
    1,
    "RUSSIAN_OGE_6_2_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)
NEW_6_6_AUTHORITY = (
    HERE / "RUSSIAN-OGE-6.6-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_6_CANONICAL_COMPONENT_SET",
    1,
    "RUSSIAN_OGE_6_6_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)
NEW_6_7_AUTHORITY = (
    HERE / "RUSSIAN-OGE-6.7-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_7_CANONICAL_COMPONENT_SET",
    1,
    "RUSSIAN_OGE_6_7_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)
NEW_6_8_AUTHORITY = (
    HERE / "RUSSIAN-OGE-6.8-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_8_CANONICAL_COMPONENT_SET",
    1,
    "RUSSIAN_OGE_6_8_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)
NEW_6_9_AUTHORITY = (
    HERE / "RUSSIAN-OGE-6.9-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_9_CANONICAL_COMPONENT_SET",
    1,
    "RUSSIAN_OGE_6_9_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)
NEW_6_11_AUTHORITY = (
    HERE / "RUSSIAN-OGE-6.11-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_11_CANONICAL_COMPONENT_SET",
    1,
    "RUSSIAN_OGE_6_11_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)
NEW_6_12_AUTHORITY = (
    HERE / "RUSSIAN-OGE-6.12-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_12_CANONICAL_COMPONENT_SET",
    1,
    "RUSSIAN_OGE_6_12_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)
RECONFIRMED_6_13_AUTHORITY = HERE / "RUSSIAN-OGE-6.13-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

_namespace: dict[str, Any] = runpy.run_path(str(LEGACY))
_base_build_progress = _namespace["_base_build_progress"]
_current = tuple(_base_build_progress.__globals__["OBJECT_AUTHORITIES"])
for spec in (
    NEW_6_2_AUTHORITY,
    NEW_6_6_AUTHORITY,
    NEW_6_7_AUTHORITY,
    NEW_6_8_AUTHORITY,
    NEW_6_9_AUTHORITY,
    NEW_6_11_AUTHORITY,
    NEW_6_12_AUTHORITY,
):
    if any(existing[3] == spec[3] for existing in _current):
        raise RuntimeError(f"current launch authority duplicated: {spec[3]}")
    _current = _current + (spec,)
_base_build_progress.__globals__["OBJECT_AUTHORITIES"] = _current


def _accepted_rows(authority: dict[str, Any]) -> list[dict[str, Any]]:
    rows = authority.get("decisions")
    if rows is None and isinstance(authority.get("decision"), dict):
        rows = [authority["decision"]]
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("accepted authority decisions missing")
    return rows


def _validate_6_13_reconfirmation_without_double_count() -> None:
    """6.13 was already object-bound in the historical OGE exact authority.

    The new authority adds current owner/evidence proof, but it must not be appended
    to OBJECT_AUTHORITIES because that would count the same admission unit and
    requirement twice. Fail closed unless the reconfirmed decision is the same
    object and the same five canonical owners with the same exact-mastery guard.
    """

    current = json.loads(RECONFIRMED_6_13_AUTHORITY.read_text(encoding="utf-8"))
    legacy = json.loads(LEGACY_OGE_AUTHORITY.read_text(encoding="utf-8"))
    current_rows = _accepted_rows(current)
    if len(current_rows) != 1:
        raise ValueError("OGE 6.13 reconfirmation must contain exactly one decision")
    current_row = current_rows[0]
    unit_id = str(current_row.get("admission_unit_id", ""))
    requirement_id = str(current_row.get("requirement_id", ""))
    legacy_matches = [
        row
        for row in _accepted_rows(legacy)
        if str(row.get("admission_unit_id", "")) == unit_id
        or str(row.get("requirement_id", "")) == requirement_id
    ]
    if len(legacy_matches) != 1:
        raise ValueError("OGE 6.13 reconfirmation is not uniquely present in legacy object acceptance")
    legacy_row = legacy_matches[0]
    for key in ("admission_unit_id", "requirement_id", "document_id", "content_code", "source_id", "source_locator"):
        if current_row.get(key) != legacy_row.get(key):
            raise ValueError(f"OGE 6.13 reconfirmation identity drift: {key}")
    if current_row.get("canonical_component_refs") != legacy_row.get("canonical_component_refs"):
        raise ValueError("OGE 6.13 reconfirmation owner-set drift")
    if current_row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET":
        raise ValueError("OGE 6.13 reconfirmation is not Central-Brain accepted")
    mastery = current_row.get("mastery_boundary") or {}
    if mastery.get("route_or_broad_composite_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("OGE 6.13 reconfirmation weakened false-mastery guard")
    if mastery.get("component_specific_independent_evidence_required") is not True:
        raise ValueError("OGE 6.13 reconfirmation lacks independent-evidence guard")
    summary = current.get("summary") or {}
    if summary.get("accepted_admission_units") != 1 or summary.get("accepted_requirements") != 1:
        raise ValueError("OGE 6.13 reconfirmation summary drift")


def build_progress() -> dict[str, Any]:
    _validate_6_13_reconfirmation_without_double_count()
    return _base_build_progress()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_progress()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = result["progress_summary"]
        print("RUSSIAN_SEMANTIC_ACCEPTANCE_PROGRESS_CURRENT=PASS")
        print("OGE_6_13_ACCEPTANCE=LEGACY_OBJECT_RECONFIRMED_NO_COUNT_DELTA")
        print(f"accepted_authorities={len(result['accepted_authorities'])}")
        for key in (
            "semantic_units_with_accepted_component_sets",
            "semantic_requirements_with_accepted_component_sets",
            "semantic_units_remaining_without_accepted_component_set",
            "semantic_requirements_remaining_without_accepted_component_set",
            "canonical_component_refs_reused_unique",
            "accepted_bounded_ru_route_semantics",
            "accepted_bounded_ru_subject_semantics",
            "accepted_bounded_ru_semantics_total",
            "false_exact_mastery_admissions",
        ):
            print(f"{key}={s[key]}")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
