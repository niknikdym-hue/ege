#!/usr/bin/env python3
"""Compatibility entrypoint for the OGE 6.14 structured branch-coverage gate.

The effective wave-002 evidence is the original 16-owner pack plus one bounded
replacement-only repair for exactly two structured owners. Delegate to the repair
validator so the historical gate name remains stable while the six superseded item
IDs can never be counted as effective evidence.
"""
from __future__ import annotations

import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_oge_6_14_wave_002_structured_repair.py"


def main() -> int:
    namespace = runpy.run_path(str(VALIDATOR))
    return int(namespace["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
