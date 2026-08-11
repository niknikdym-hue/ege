#!/usr/bin/env python3
"""Run error->exception handoff validation against corrected current exceptions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import validate_russian_error_exception_handoff as base

CURRENT_MANIFEST = "118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    original_flatten = base.flatten_exception_ids

    def active_flatten(root_path: Path, manifest: Any):
        result = original_flatten(root_path, manifest)
        disabled = manifest.get("disabled_exception_ids", []) if isinstance(manifest, dict) else []
        if not isinstance(disabled, list) or not all(isinstance(x, str) for x in disabled):
            raise base.ValidationError("disabled_exception_ids must be string array")
        for exception_id in disabled:
            result.pop(exception_id, None)
        return result

    base.EXCEPTIONS_MANIFEST = CURRENT_MANIFEST
    base.flatten_exception_ids = active_flatten
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
