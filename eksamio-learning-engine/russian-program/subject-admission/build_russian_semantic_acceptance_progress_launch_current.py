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
NEW_6_13_AUTHORITY = (
    HERE / "RUSSIAN-OGE-6.13-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_13_CANONICAL_COMPONENT_SET",
    1,
    "RUSSIAN_OGE_6_13_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)

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
    NEW_6_13_AUTHORITY,
):
    if any(existing[3] == spec[3] for existing in _current):
        raise RuntimeError(f"current launch authority duplicated: {spec[3]}")
    _current = _current + (spec,)
_base_build_progress.__globals__["OBJECT_AUTHORITIES"] = _current


def build_progress() -> dict[str, Any]:
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
