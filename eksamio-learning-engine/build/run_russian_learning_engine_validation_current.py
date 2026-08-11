#!/usr/bin/env python3
"""Current aggregate local validation runner for Russian Learning Engine.

Runs all canonical data builders plus synthetic session-selector tests.
No network, Git, Tilda, or production mutation.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHECKS = [
    ("EXPLANATIONS", ["build/build_russian_explanation_bank.py"]),
    ("EXCEPTIONS", ["build/build_russian_exceptions_bank.py"]),
    ("EXCEPTIONS_PRACTICE_72", ["build/build_russian_exceptions_practice_current.py"]),
    ("SESSION_SELECTOR_SYNTHETIC_TESTS", ["build/tests/test_russian_exceptions_session_selector.py"]),
]

SUMMARY_REL = Path("audits/RUSSIAN-LEARNING-ENGINE-VALIDATION-CURRENT-SUMMARY.txt")


def run_check(root: Path, label: str, args: list[str]) -> dict[str, object]:
    script = root / args[0]
    if not script.is_file():
        return {
            "label": label,
            "command": " ".join(args),
            "exit_code": 2,
            "stdout": "",
            "stderr": f"Missing script: {args[0]}",
        }
    proc = subprocess.run(
        [sys.executable, *[str(root / args[0]), *args[1:]]],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "label": label,
        "command": f"{sys.executable} {' '.join(args)}",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def write_summary(root: Path, results: list[dict[str, object]]) -> Path:
    overall = all(int(row["exit_code"]) == 0 for row in results)
    path = root / SUMMARY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN LEARNING ENGINE — CURRENT AGGREGATE VALIDATION",
        "",
        f"OVERALL_STATUS: {'PASS' if overall else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"CHECKS_TOTAL: {len(results)}",
        "",
        "CHECKS",
    ]
    for row in results:
        code = int(row["exit_code"])
        lines.extend(
            [
                f"- {row['label']}: {'PASS' if code == 0 else 'FAIL'}",
                f"  EXIT_CODE: {code}",
                f"  COMMAND: {row['command']}",
            ]
        )
        if row.get("stdout"):
            lines.append("  STDOUT:")
            lines.extend(f"    {line}" for line in str(row["stdout"]).splitlines())
        if row.get("stderr"):
            lines.append("  STDERR:")
            lines.extend(f"    {line}" for line in str(row["stderr"]).splitlines())
    lines.extend(
        [
            "",
            "EXPECTED BUILD OUTPUTS",
            "- build/RUSSIAN-EXPLANATION-BANK-CANONICAL.json",
            "- build/RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json",
            "- build/RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json",
            "",
            "EXPECTED AUDITS",
            "- audits/RUSSIAN-EXPLANATION-CANONICAL-VALIDATION.txt",
            "- audits/RUSSIAN-EXCEPTIONS-CANONICAL-VALIDATION.txt",
            "- audits/RUSSIAN-EXCEPTIONS-PRACTICE-VALIDATION.txt",
            "",
            "SAFETY",
            "- Data/build validation only.",
            "- Current EGE trainer source/answers/scoring/localStorage unchanged.",
            "- PASS does not itself authorize Tilda publication.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    results: list[dict[str, object]] = []
    for label, args in CHECKS:
        print(f"== {label} ==")
        result = run_check(root, label, args)
        results.append(result)
        if result["stdout"]:
            print(result["stdout"])
        if result["stderr"]:
            print(result["stderr"], file=sys.stderr)
        print(f"exit={result['exit_code']}\n")
    summary = write_summary(root, results)
    overall = all(int(row["exit_code"]) == 0 for row in results)
    print(f"Current aggregate summary: {summary}")
    print(f"OVERALL_STATUS={'PASS' if overall else 'FAIL'}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
