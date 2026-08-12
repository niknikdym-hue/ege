#!/usr/bin/env python3
"""Build the reviewed 121-card Wave 6 candidate using the shared course-grade loader.

Review overlay 145 is now applied centrally by build_russian_exceptions_practice_course_grade,
so this historical isolated candidate wrapper only selects candidate manifest 143 and output paths.
No production/Tilda mutation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import build_russian_exceptions_practice as base
import build_russian_exceptions_practice_current_corrected_v2 as current
import build_russian_exceptions_practice_course_grade as course_grade

CURRENT_EXCEPTION_MANIFEST = "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json"
CANDIDATE_PRACTICE_MANIFEST = "143-RUSSIAN-EXCEPTIONS-PRACTICE-WAVE6-CANDIDATE-MANIFEST.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--audit", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "build" / "candidate-wave6" / "RUSSIAN-EXCEPTIONS-PRACTICE-WAVE6-CANDIDATE.json"
    audit = args.audit or root / "audits" / "candidate-wave6" / "RUSSIAN-EXCEPTIONS-PRACTICE-WAVE6-VALIDATION.txt"

    base.EXCEPTIONS_MANIFEST = CURRENT_EXCEPTION_MANIFEST
    base.PRACTICE_MANIFEST = CANDIDATE_PRACTICE_MANIFEST
    base.flatten_exceptions = current.active_exceptions
    base.load_practice_items = course_grade.load_course_grade_practice_items

    try:
        return base.build(root, output, audit)
    except base.BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
