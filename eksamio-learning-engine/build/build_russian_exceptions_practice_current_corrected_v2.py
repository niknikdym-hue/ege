#!/usr/bin/env python3
"""Build current corrected 72-card Exceptions Practice Bank — hardened v2.

Fixes the recursive monkeypatch risk in the first corrected wrapper by capturing
original helper functions before replacing them. Data-only; no production mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_russian_exceptions_practice as base

CURRENT_EXCEPTION_MANIFEST = "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json"
CURRENT_PRACTICE_MANIFEST = "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json"

ORIGINAL_FLATTEN_EXCEPTIONS = base.flatten_exceptions


def load_active_practice_items(
    root: Path, manifest: Any
) -> tuple[list[dict[str, Any]], list[str], int]:
    if not isinstance(manifest, dict):
        raise base.BuildError(f"{CURRENT_PRACTICE_MANIFEST} must be an object")

    disabled_raw = manifest.get("disabled_practice_item_ids", [])
    if not isinstance(disabled_raw, list) or not all(isinstance(x, str) for x in disabled_raw):
        raise base.BuildError("disabled_practice_item_ids must be string array")
    disabled = set(disabled_raw)

    expected_active = manifest.get("expected_active_items")
    expected_raw = manifest.get("expected_total_items_raw")
    if not isinstance(expected_active, int) or expected_active < 0:
        raise base.BuildError("expected_active_items must be non-negative integer")
    if not isinstance(expected_raw, int) or expected_raw < 0:
        raise base.BuildError("expected_total_items_raw must be non-negative integer")

    items: list[dict[str, Any]] = []
    source_files: list[str] = []
    raw_count = 0
    disabled_seen: set[str] = set()

    for row in base.get_manifest_paths(manifest, "practice_banks"):
        rel = row["path"]
        data = base.load_json(root / rel)
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise base.BuildError(f"Expected items[] in practice bank {rel}")
        bank_items = data["items"]
        if not all(isinstance(x, dict) for x in bank_items):
            raise base.BuildError(f"Non-object practice item in {rel}")

        expected = row.get("expected_items")
        if not isinstance(expected, int) or expected != len(bank_items):
            raise base.BuildError(
                f"{rel}: expected_items={expected!r}, actual={len(bank_items)}"
            )
        raw_count += len(bank_items)

        for original in bank_items:
            pid = original.get("practice_item_id")
            if isinstance(pid, str) and pid in disabled:
                disabled_seen.add(pid)
                continue
            item = json.loads(json.dumps(original, ensure_ascii=False))
            item["source_practice_bank"] = rel
            items.append(item)
        source_files.append(rel)

    if raw_count != expected_raw:
        raise base.BuildError(
            f"raw practice total mismatch: manifest={expected_raw}, actual={raw_count}"
        )
    if len(items) != expected_active:
        raise base.BuildError(
            f"active practice total mismatch: manifest={expected_active}, actual={len(items)}"
        )
    missing_disabled = sorted(disabled - disabled_seen)
    if missing_disabled:
        raise base.BuildError(
            f"disabled practice IDs not found in source banks: {missing_disabled}"
        )
    if len(disabled_seen) != raw_count - len(items):
        raise base.BuildError(
            "disabled practice count does not match raw-active count delta"
        )

    return items, source_files, expected_active


def active_exceptions(root: Path, manifest: Any) -> dict[str, dict[str, Any]]:
    result = ORIGINAL_FLATTEN_EXCEPTIONS(root, manifest)
    disabled_raw = manifest.get("disabled_exception_ids", []) if isinstance(manifest, dict) else []
    if not isinstance(disabled_raw, list) or not all(isinstance(x, str) for x in disabled_raw):
        raise base.BuildError("disabled_exception_ids must be string array")
    missing = [exception_id for exception_id in disabled_raw if exception_id not in result]
    if missing:
        raise base.BuildError(f"disabled exception IDs not found before filtering: {missing}")
    for exception_id in disabled_raw:
        result.pop(exception_id, None)
    return result


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

    base.EXCEPTIONS_MANIFEST = CURRENT_EXCEPTION_MANIFEST
    base.PRACTICE_MANIFEST = CURRENT_PRACTICE_MANIFEST
    base.flatten_exceptions = active_exceptions
    base.load_practice_items = load_active_practice_items

    try:
        return base.build(root, output, audit)
    except base.BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
