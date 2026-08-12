#!/usr/bin/env python3
"""Standalone Exceptions Trainer implementation gate.

First runs the current Learning Engine source/data/runtime gate, then validates the
browser core against the generated runtime. This runner is intentionally separate
from the general v10 gate because browser implementation tests require Node.js.
No network or production mutation.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHECKS = [
    ("LEARNING_ENGINE_CURRENT_V10", [sys.executable, "build/run_russian_learning_engine_validation_current_v10.py"]),
    ("BROWSER_CORE", [sys.executable, "build/tests/test_russian_exceptions_browser_core.py"]),
]
SUMMARY_REL = Path("audits/RUSSIAN-EXCEPTIONS-STANDALONE-VALIDATION.txt")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    rows = []
    for label, command in CHECKS:
        proc = subprocess.run(command, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        rows.append((label, proc.returncode, proc.stdout.strip(), proc.stderr.strip()))
        print(f"== {label} ==")
        if proc.stdout.strip(): print(proc.stdout.strip())
        if proc.stderr.strip(): print(proc.stderr.strip(), file=sys.stderr)
        print(f"exit={proc.returncode}\n")
    passed = all(code == 0 for _, code, _, _ in rows)
    path = root / SUMMARY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN EXCEPTIONS TRAINER — STANDALONE IMPLEMENTATION VALIDATION",
        "",
        f"STATUS: {'PASS' if passed else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"CHECKS_TOTAL: {len(rows)}",
        "",
    ]
    for label, code, stdout, stderr in rows:
        lines += [f"- {label}: {'PASS' if code == 0 else 'FAIL'}", f"  EXIT_CODE: {code}"]
        if stdout:
            lines.append("  STDOUT:")
            lines += [f"    {x}" for x in stdout.splitlines()]
        if stderr:
            lines.append("  STDERR:")
            lines += [f"    {x}" for x in stderr.splitlines()]
    lines += [
        "",
        "BROWSER CORE COVERAGE",
        "- deterministic runtime chunk assembly + fail-closed missing/duplicate/mixed-version checks",
        "- evaluator coverage for all current practice cards and exact orthographic distinctions",
        "- corrupt/unsupported learner-state fail-safe without silent overwrite",
        "- idempotent attempt reducer",
        "- JavaScript selector parity with accepted Python selector",
        "- focused handoff under-fills rather than padding duplicate cards",
        "- future Exceptions storage namespace does not collide with current EGE trainer keys",
        "",
        "SAFETY",
        "- Standalone source only; current EGE trainer is not modified.",
        "- PASS authorizes the next standalone page-shell/UI implementation step, not publication.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Standalone summary: {path}")
    print(f"STATUS={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
