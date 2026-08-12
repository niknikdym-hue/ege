#!/usr/bin/env python3
"""Full pre-Tilda-preview gate for the standalone Russian Exceptions Trainer.

Runs core/source validation, rebuilds the deterministic Tilda package, and then runs
real Chromium interaction/mobile/fail-closed smoke against the generated preview.
No network/publication/current-trainer mutation.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHECKS = [
    ("STANDALONE_CORE_GATE", [sys.executable, "build/run_russian_exceptions_standalone_validation.py"]),
    ("TILDA_PACKAGE_BUILD", [sys.executable, "build/build_russian_exceptions_standalone_package.py"]),
    ("CHROMIUM_PREVIEW_SMOKE", [sys.executable, "build/tests/test_russian_exceptions_standalone_preview.py"]),
]
SUMMARY_REL = Path("audits/RUSSIAN-EXCEPTIONS-STANDALONE-PREVIEW-VALIDATION.txt")


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
        "RUSSIAN EXCEPTIONS TRAINER — STANDALONE PREVIEW VALIDATION",
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
            lines += [f"    {line}" for line in stdout.splitlines()]
        if stderr:
            lines.append("  STDERR:")
            lines += [f"    {line}" for line in stderr.splitlines()]
    lines += [
        "",
        "INTERPRETATION",
        "- PASS means the local standalone package is ready for a Tilda preview/hidden test page.",
        "- PASS does NOT authorize public publication or /trenazhery/ catalog changes.",
        "- Current /ege/russkiy/trenazher/ remains out of scope and unchanged.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    package_dir = root / "build" / "standalone-exceptions-tilda"
    if package_dir.is_dir():
        package_result = package_dir / "trenazhery-russkiy-isklyucheniya-TEST-RESULT.txt"
        package_lines = [
            "EKSAMIO / TILDA PREVIEW PACKAGE TEST RESULT",
            f"STATUS: {'PASS' if passed else 'FAIL'}",
            f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
            "",
            "CHECKS",
        ]
        for label, code, _, _ in rows:
            package_lines.append(f"- {label}: {'PASS' if code == 0 else 'FAIL'}")
        package_lines += [
            "",
            "PASS MEANS",
            "- current Learning Engine source/data/runtime gate passed;",
            "- browser-core parity tests passed;",
            "- deterministic Tilda package build passed;",
            "- Chromium interaction/mobile/corrupt-state/runtime-failure smoke passed;",
            "- package is ready for a Tilda preview/hidden test page, NOT public publication.",
            "",
            "SAFETY",
            "- /ege/russkiy/trenazher/ was not modified by this package build;",
            "- /trenazhery/ catalog was not modified;",
            "- publication remains HOLD until a Tilda preview/hidden-page smoke passes.",
            "",
        ]
        package_result.write_text("\n".join(package_lines), encoding="utf-8")
    print(f"Preview summary: {path}")
    print(f"STATUS={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
