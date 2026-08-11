#!/usr/bin/env python3
"""Build corrected current Russian Exceptions Bank — hardened v2.

Verifies that every explicitly disabled source exception actually exists before
filtering it. Data-only; no production mutation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import build_russian_exceptions_bank as base

CURRENT_MANIFEST = "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json"
ORIGINAL_FLATTEN = base.flatten_bank


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--audit", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "build" / "RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json"
    audit = args.audit or root / "audits" / "RUSSIAN-EXCEPTIONS-CANONICAL-VALIDATION.txt"

    try:
        manifest = base.load_json(root / CURRENT_MANIFEST)
        disabled_raw = manifest.get("disabled_exception_ids", []) if isinstance(manifest, dict) else []
        if not isinstance(disabled_raw, list) or not all(isinstance(x, str) for x in disabled_raw):
            raise base.BuildError(f"{CURRENT_MANIFEST}: disabled_exception_ids must be string array")
        disabled = set(disabled_raw)

        source_banks = base.source_banks_from_manifest(manifest)
        source_ids: set[str] = set()
        for rel in source_banks:
            rows = ORIGINAL_FLATTEN(base.load_json(root / rel), rel)
            for row in rows:
                exception_id = row.get("exception_id")
                if isinstance(exception_id, str):
                    source_ids.add(exception_id)
        missing = sorted(disabled - source_ids)
        if missing:
            raise base.BuildError(
                f"disabled exception IDs not found in registered source banks: {missing}"
            )

        def filtered_flatten(data: Any, source_name: str):
            rows = ORIGINAL_FLATTEN(data, source_name)
            return [row for row in rows if row.get("exception_id") not in disabled]

        base.MANIFEST_FILE = CURRENT_MANIFEST
        base.flatten_bank = filtered_flatten
        return base.build(root, output, audit)
    except base.BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
