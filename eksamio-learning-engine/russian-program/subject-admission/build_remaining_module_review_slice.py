#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE_BUILDER = HERE / "build_launch_critical_review_slice.py"
TARGET_MODULES = {
    "RU-PROG-01",
    "RU-PROG-02",
    "RU-PROG-03",
    "RU-PROG-04",
    "RU-PROG-05",
    "RU-PROG-06",
    "RU-PROG-07",
    "RU-PROG-11",
    "RU-PROG-12",
    "RU-PROG-15",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_slice() -> dict[str, Any]:
    namespace = runpy.run_path(str(BASE_BUILDER))
    payload = namespace["build_slice"](target_modules=TARGET_MODULES)
    if payload.get("target_modules") != sorted(TARGET_MODULES):
        raise ValueError(f"remaining-module review slice target drift: {payload.get('target_modules')}")
    foreign_modules = set(payload.get("by_module", {})) - TARGET_MODULES
    if foreign_modules:
        raise ValueError(f"remaining-module review slice contains foreign module counters: {sorted(foreign_modules)}")
    if any(not set(row.get("modules", [])).intersection(TARGET_MODULES) for row in payload.get("admission_units", [])):
        raise ValueError("remaining-module review slice contains a unit outside requested modules")
    payload["status"] = "EXACT_REMAINING_MODULE_REVIEW_SLICE_NOT_ADMISSION_DECISION"
    payload["review_policy"] = {
        "exact_source_rows_only": True,
        "module_membership_is_not_semantic_mapping": True,
        "keyword_or_fuzzy_admission_allowed": False,
        "classification_requires_separate_central_brain_authority": True,
    }
    payload.pop("normalized_sha256", None)
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_slice()
    if args.output:
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_REMAINING_MODULE_EXACT_REVIEW_SLICE=PASS")
        print(f"normalized_sha256={payload['normalized_sha256']}")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        for module, counts in payload["by_module"].items():
            print(f"{module}.admission_units={counts['admission_units']}")
            print(f"{module}.requirements={counts['requirements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
