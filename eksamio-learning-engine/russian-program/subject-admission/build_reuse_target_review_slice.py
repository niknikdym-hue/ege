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
TARGET_MODULES = {"RU-PROG-08", "RU-PROG-09", "RU-PROG-10", "RU-PROG-14"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_slice() -> dict[str, Any]:
    namespace = runpy.run_path(str(BASE_BUILDER))
    namespace["TARGET_MODULES"] = set(TARGET_MODULES)
    payload = namespace["build_slice"]()
    payload["status"] = "EXACT_REUSE_TARGET_REVIEW_SLICE_NOT_ADMISSION_DECISION"
    payload["reuse_policy"] = {
        "reuse_pool_required_before_new_content": True,
        "asset_presence_is_not_coverage": True,
        "module_membership_is_not_semantic_mapping": True,
        "new_content_allowed_only_after_exact_reuse_gap": True,
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
        print("RU08_RU09_RU10_RU14_EXACT_REVIEW_SLICE=PASS")
        print(f"normalized_sha256={payload['normalized_sha256']}")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        for module, counts in payload["by_module"].items():
            print(f"{module}.admission_units={counts['admission_units']}")
            print(f"{module}.requirements={counts['requirements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
