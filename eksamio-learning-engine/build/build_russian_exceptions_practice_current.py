#!/usr/bin/env python3
"""Run the shared Exceptions Practice validator against the current manifest.

The historical 48-card checkpoint remains in file 93. Current work uses file 99.
This wrapper changes no production data and only redirects the shared builder to
the current manifest.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import build_russian_exceptions_practice as base

CURRENT_MANIFEST = "99-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-MANIFEST.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--audit", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "build" / "RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json"
    audit = args.audit or root / "audits" / "RUSSIAN-EXCEPTIONS-PRACTICE-VALIDATION.txt"

    base.PRACTICE_MANIFEST = CURRENT_MANIFEST
    try:
        return base.build(root, output, audit)
    except base.BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
