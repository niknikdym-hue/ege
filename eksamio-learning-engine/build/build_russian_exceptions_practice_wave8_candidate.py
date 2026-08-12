#!/usr/bin/env python3
"""Build the 145-card reviewed Wave 8 candidate without changing current manifest 119.

Reuses the current course-grade loader so current 133 keeps all established audit/review
layers, then adds reviewed Wave 8 file 154 through candidate manifest 155. Output stays
under build/candidate-wave8. No Tilda/current-trainer mutation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import build_russian_exceptions_practice as base
import build_russian_exceptions_practice_current_corrected_v2 as current
import build_russian_exceptions_practice_course_grade as course_grade

CURRENT_EXCEPTION_MANIFEST = "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json"
CANDIDATE_PRACTICE_MANIFEST = "155-RUSSIAN-EXCEPTIONS-PRACTICE-WAVE8-CANDIDATE-MANIFEST.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--audit", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "build" / "candidate-wave8" / "RUSSIAN-EXCEPTIONS-PRACTICE-WAVE8-CANDIDATE.json"
    audit = args.audit or root / "audits" / "candidate-wave8" / "RUSSIAN-EXCEPTIONS-PRACTICE-WAVE8-VALIDATION.txt"

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
