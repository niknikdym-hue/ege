#!/usr/bin/env python3
"""Current Sep-1 launch semantic-progress view including batch wave 001."""
from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BATCH = HERE / "build_russian_batch_wave_001_exact_component_acceptance.py"
_namespace: dict[str, Any] = runpy.run_path(str(BATCH))
_build_batched_progress = _namespace["build_batched_progress"]


def build_progress() -> dict[str, Any]:
    _wave, progress = _build_batched_progress()
    return progress


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_progress()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = result["progress_summary"]
        wave = result.get("batch_wave_001") or {}
        print("RUSSIAN_SEMANTIC_ACCEPTANCE_PROGRESS_CURRENT=PASS")
        print(f"accepted_authorities={len(result['accepted_authorities'])}")
        print(f"batch_wave_001_status={wave.get('status')}")
        print(f"batch_wave_001_accepted_units={wave.get('accepted_admission_units', 0)}")
        print(f"batch_wave_001_accepted_requirements={wave.get('accepted_requirements', 0)}")
        for key in (
            "fully_accepted_semantic_groups",
            "review_groups_with_accepted_component_sets",
            "semantic_units_with_accepted_component_sets",
            "semantic_requirements_with_accepted_component_sets",
            "semantic_units_remaining_without_accepted_component_set",
            "semantic_requirements_remaining_without_accepted_component_set",
            "canonical_component_refs_reused_unique",
            "accepted_bounded_ru_route_semantics",
            "accepted_bounded_ru_subject_semantics",
            "accepted_bounded_ru_semantics_total",
            "false_exact_mastery_admissions",
        ):
            print(f"{key}={s[key]}")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
