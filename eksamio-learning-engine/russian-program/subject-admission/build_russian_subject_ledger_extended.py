#!/usr/bin/env python3
"""Build the exact Russian subject ledger including the reviewed reuse-target composite slice.

This wrapper deliberately reuses the existing aggregate builder instead of duplicating
its admission rules.  It extends only the reviewed-set input list, and does so by
mutating the loaded function's actual globals so the additional authority is consumed
by the same exact unit/requirement validation path.
"""
from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE_BUILDER = HERE / "build_russian_subject_ledger.py"
REUSE_COMPOSITES = HERE / "RUSSIAN-SUBJECT-REVIEWED-REUSE-COMPOSITES-v0.1.json"


def build_ledger() -> dict[str, Any]:
    namespace = runpy.run_path(str(BASE_BUILDER))
    build_fn = namespace["build_ledger"]
    globals_dict = build_fn.__globals__
    base_paths = tuple(globals_dict["SET_PATHS"])
    if REUSE_COMPOSITES in base_paths:
        raise ValueError("reuse composite reviewed set unexpectedly already present in base builder")
    globals_dict["SET_PATHS"] = (*base_paths, REUSE_COMPOSITES)
    payload = build_fn()
    if not any(
        row.get("decision_source") == REUSE_COMPOSITES.name
        for row in payload.get("dispositions", [])
    ):
        raise ValueError("extended builder failed to consume the reviewed reuse composite set")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_ledger()
    if args.output:
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_SUBJECT_LEDGER_EXTENDED_BUILD=PASS")
        print(f"normalized_sha256={payload['normalized_sha256']}")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        for disposition, counts in payload["by_disposition"].items():
            print(f"{disposition}.admission_units={counts['admission_units']}")
            print(f"{disposition}.requirements={counts['requirements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
