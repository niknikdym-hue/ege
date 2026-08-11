#!/usr/bin/env python3
"""Run all Russian Learning Engine data validators locally, without network."""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VALIDATORS = [
    ("EXPLANATIONS", "build/build_russian_explanation_bank.py"),
    ("EXCEPTIONS", "build/build_russian_exceptions_bank.py"),
    ("EXCEPTIONS_PRACTICE", "build/build_russian_exceptions_practice_current.py"),
]

SUMMARY_REL = Path("audits/RUSSIAN-LEARNING-ENGINE-VALIDATION-SUMMARY.txt")


def run_validator(root: Path, label: str, script_rel: str) -> dict[str, object]:
    script = root / script_rel
    if not script.is_file():
        return {
            "label": label,
            "script": script_rel,
            "exit_code": 2,
            "stdout": "",
            "stderr": f"Missing validator script: {script_rel}",
        }

    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "label": label,
        "script": script_rel,
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def write_summary(root: Path, results: list[dict[str, object]]) -> Path:
    overall_pass = all(row["exit_code"] == 0 for row in results)
    summary = root / SUMMARY_REL
    summary.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN LEARNING ENGINE — AGGREGATE VALIDATION",
        "",
        f"OVERALL_STATUS: {'PASS' if overall_pass else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"VALIDATORS_TOTAL: {len(results)}",
        "",
        "RESULTS",
    ]

    for row in results:
        code = int(row["exit_code"])
        lines.extend(
            [
                f"- {row['label']}: {'PASS' if code == 0 else 'FAIL'}",
                f"  SCRIPT: {row['script']}",
                f"  EXIT_CODE: {code}",
            ]
        )
        stdout = str(row.get("stdout", "")).strip()
        stderr = str(row.get("stderr", "")).strip()
        if stdout:
            lines.append("  STDOUT:")
            lines.extend(f"    {line}" for line in stdout.splitlines())
        if stderr:
            lines.append("  STDERR:")
            lines.extend(f"    {line}" for line in stderr.splitlines())

    lines.extend(
        [
            "",
            "EXPECTED INDIVIDUAL AUDITS",
            "- audits/RUSSIAN-EXPLANATION-CANONICAL-VALIDATION.txt",
            "- audits/RUSSIAN-EXCEPTIONS-CANONICAL-VALIDATION.txt",
            "- audits/RUSSIAN-EXCEPTIONS-PRACTICE-VALIDATION.txt",
            "",
            "SAFETY",
            "- This runner is data-only.",
            "- It does not publish to Tilda.",
            "- It does not modify the current EGE trainer source/answers/scoring/localStorage.",
            "",
        ]
    )
    summary.write_text("\n".join(lines), encoding="utf-8")
    return summary


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    results: list[dict[str, object]] = []

    for label, script in VALIDATORS:
        print(f"== {label} ==")
        row = run_validator(root, label, script)
        results.append(row)
        if row["stdout"]:
            print(row["stdout"])
        if row["stderr"]:
            print(row["stderr"], file=sys.stderr)
        print(f"exit={row['exit_code']}\n")

    summary = write_summary(root, results)
    overall_pass = all(row["exit_code"] == 0 for row in results)
    print(f"Aggregate summary: {summary}")
    print(f"OVERALL_STATUS={'PASS' if overall_pass else 'FAIL'}")
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
