#!/usr/bin/env python3
"""Canonical semantic-progress builder extended with exact OGE-2026 code 7.25."""
from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_base.py"
INDIRECT_AUTHORITY = (
    HERE / "RUSSIAN-OGE-INDIRECT-SPEECH-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json",
    "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_INDIRECT_SPEECH_CANONICAL_COMPONENT_SLICE",
    1,
    "RUSSIAN_OGE_INDIRECT_SPEECH_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1",
)

_namespace: dict[str, Any] = runpy.run_path(str(BASE))
_base_authorities = tuple(_namespace["OBJECT_AUTHORITIES"])
_namespace["OBJECT_AUTHORITIES"] = _base_authorities + (INDIRECT_AUTHORITY,)
_namespace["build_progress"].__globals__["OBJECT_AUTHORITIES"] = _namespace["OBJECT_AUTHORITIES"]
_namespace["main"].__globals__["OBJECT_AUTHORITIES"] = _namespace["OBJECT_AUTHORITIES"]
_base_build_progress = _namespace["build_progress"]
_base_main = _namespace["main"]


def build_progress() -> dict[str, Any]:
    return _base_build_progress()


def main() -> int:
    return _base_main()


if __name__ == "__main__":
    raise SystemExit(main())
