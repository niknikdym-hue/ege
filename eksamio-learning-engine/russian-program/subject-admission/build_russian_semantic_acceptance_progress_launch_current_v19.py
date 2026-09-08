#!/usr/bin/env python3
"""Infrastructure repair wrapper for exact OGE 2.1 RU01 composite acceptance.

The v18 builder correctly materializes two previously unseen canonical component
refs for the exact OGE 2.1 object, but its fail-closed expected aggregate used
+1 instead of +2 for canonical_component_refs_reused_unique. This wrapper keeps
all v18 semantic/evidence/object boundaries intact and repairs only that expected
cardinality before executing the v18 builder.
"""
from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path

H = Path(__file__).resolve().parent
BASE = H / "build_russian_semantic_acceptance_progress_launch_current_v18.py"
UNIT = "RAU-b6f5dff93864358672bc"
REQ = "RSK-OGE_COD-2-1-P010"
EXPECTED_REFS = [
    "ru-phonetics-vowel-consonant-features",
    "ru-phonetics-sound-composition-determination",
]


def build_progress():
    module = runpy.run_path(str(BASE))
    build = module["build_progress"]
    globals_ = build.__globals__
    after = globals_.get("AFTER")
    if not isinstance(after, dict):
        raise ValueError("v18 AFTER aggregate missing")
    if after.get("canonical_component_refs_reused_unique") != 121:
        raise ValueError("v18 expected unique-ref cardinality drift")

    # Exact repair: both component refs are absent from the v17 accepted object
    # sets, therefore accepting this two-component object introduces two unique
    # reused canonical refs (120 -> 122), not one.
    after["canonical_component_refs_reused_unique"] = 122
    d = build()

    s = d["progress_summary"]
    expected = {
        "semantic_units_with_accepted_component_sets": 41,
        "semantic_requirements_with_accepted_component_sets": 41,
        "semantic_units_remaining_without_accepted_component_set": 1275,
        "semantic_requirements_remaining_without_accepted_component_set": 1350,
        "subject_disposed_units_total": 42,
        "subject_disposed_requirements_total": 42,
        "subject_review_units_remaining": 1274,
        "subject_review_requirements_remaining": 1349,
        "canonical_component_refs_reused_unique": 122,
        "review_groups_with_accepted_component_sets": 14,
        "accepted_bounded_ru_route_semantics": 9,
        "accepted_bounded_ru_subject_semantics": 69,
        "accepted_bounded_ru_semantics_total": 78,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected.items():
        if s.get(key) != value:
            raise ValueError(f"v19 repaired aggregate drift: {key}")

    if d.get("schema_version") != "0.21.0":
        raise ValueError("v18 schema drift")
    if len(d.get("accepted_authorities") or []) != 65:
        raise ValueError("accepted authority count drift")

    new = d.get("newly_accepted_exact_object") or {}
    if new.get("admission_unit_id") != UNIT or new.get("requirement_id") != REQ:
        raise ValueError("exact OGE 2.1 target drift")
    if new.get("accepted_component_refs") != EXPECTED_REFS:
        raise ValueError("exact two-component set drift")
    if new.get("independent_evidence_items") != 8:
        raise ValueError("component-specific evidence cardinality drift")
    if new.get("sibling_source_objects_accepted") != 0:
        raise ValueError("sibling object leakage")
    return d


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    d = build_progress()
    if args.output:
        Path(args.output).write_text(
            json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = d["progress_summary"]
        print("RUSSIAN_RU01_OGE_2_1_SOUND_COMPOSITION_EXACT_OBJECT_ACCEPTANCE_V19=PASS")
        print("ACCEPTED_UNIT=" + UNIT)
        print("ACCEPTED_REQUIREMENT=" + REQ)
        print("EXACT_COMPONENT_REFS=2")
        print("INDEPENDENT_EVIDENCE_ITEMS=8")
        print("CANONICAL_COMPONENT_REFS_REUSED_UNIQUE=" + str(s["canonical_component_refs_reused_unique"]))
        print("SUBJECT_REVIEW_UNITS_REMAINING=" + str(s["subject_review_units_remaining"]))
        print("SUBJECT_REVIEW_REQUIREMENTS_REMAINING=" + str(s["subject_review_requirements_remaining"]))
        print("FALSE_EXACT_MASTERY=" + str(s["false_exact_mastery_admissions"]))
        print("NORMALIZED_SHA256=" + d["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
