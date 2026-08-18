#!/usr/bin/env python3
"""Build corrected current Russian Exceptions Bank — hardened v3 content gate.

Verifies explicitly disabled source exceptions, filters superseded historical
entries, and applies the reviewed current-rule source overlay declared by the
current manifest. Data-only; no production/Tilda mutation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import build_russian_exceptions_bank as base

CURRENT_MANIFEST = "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json"
ORIGINAL_FLATTEN = base.flatten_bank


def _clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def load_source_overlay(root: Path, manifest: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict):
        raise base.BuildError(f"{CURRENT_MANIFEST} must be object")
    rel = manifest.get("source_content_overlay")
    if rel is None:
        return {}
    if not isinstance(rel, str) or not rel.strip():
        raise base.BuildError("source_content_overlay must be non-empty string")
    data = base.load_json(root / rel)
    patches = data.get("exception_patches") if isinstance(data, dict) else None
    if not isinstance(patches, list):
        raise base.BuildError(f"{rel}: exception_patches must be array")
    result: dict[str, dict[str, Any]] = {}
    for idx, patch in enumerate(patches):
        if not isinstance(patch, dict):
            raise base.BuildError(f"{rel}: exception_patches[{idx}] must be object")
        exception_id = patch.get("exception_id")
        replace = patch.get("replace")
        if not isinstance(exception_id, str) or not exception_id:
            raise base.BuildError(f"{rel}: patch {idx} missing exception_id")
        if exception_id in result:
            raise base.BuildError(f"{rel}: duplicate patch for {exception_id}")
        if not isinstance(replace, dict) or not replace:
            raise base.BuildError(f"{rel}: patch {exception_id} missing replace object")
        result[exception_id] = _clone(replace)
    return result


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
        overlay = load_source_overlay(root, manifest)

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
        missing_overlay = sorted(set(overlay) - source_ids)
        if missing_overlay:
            raise base.BuildError(
                f"source-content overlay targets not found in registered source banks: {missing_overlay}"
            )
        bad_overlap = sorted(disabled & set(overlay))
        if bad_overlap:
            raise base.BuildError(
                f"source-content overlay targets disabled exceptions: {bad_overlap}"
            )

        applied: set[str] = set()

        def filtered_flatten(data: Any, source_name: str):
            rows = ORIGINAL_FLATTEN(data, source_name)
            result: list[dict[str, Any]] = []
            for row in rows:
                exception_id = row.get("exception_id")
                if exception_id in disabled:
                    continue
                if isinstance(exception_id, str) and exception_id in overlay:
                    patched = _clone(row)
                    patched.update(_clone(overlay[exception_id]))
                    patched["source_content_overlay"] = manifest.get("source_content_overlay")
                    row = patched
                    applied.add(exception_id)
                result.append(row)
            return result

        base.MANIFEST_FILE = CURRENT_MANIFEST
        base.flatten_bank = filtered_flatten
        code = base.build(root, output, audit)
        missing_applied = sorted(set(overlay) - applied)
        if missing_applied:
            raise base.BuildError(f"source-content overlay was not applied: {missing_applied}")
        return code
    except base.BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
