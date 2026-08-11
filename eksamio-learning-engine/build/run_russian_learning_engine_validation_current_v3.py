#!/usr/bin/env python3
"""Current v3 aggregate local validation runner for Russian Learning Engine.

Adds independent Skill Graph vs repository-visible trainer validation to the
canonical data, selector and handoff checks. No production mutation.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHECKS = [
    ("SKILL_GRAPH_VS_TRAINER", "build/validate_russian_skill_graph_against_trainer.py"),
    ("EXPLANATIONS", "build/build_russian_explanation_bank.py"),
    ("EXCEPTIONS", "build/build_russian_exceptions_bank.py"),
    ("EXCEPTIONS_PRACTICE_72", "build/build_russian_exceptions_practice_current.py"),
    ("SESSION_SELECTOR_SYNTHETIC_TESTS", "build/tests/test_russian_exceptions_session_selector.py"),
    ("ERROR_TO_EXCEPTION_HANDOFF", "build/validate_russian_error_exception_handoff.py"),
]

SUMMARY_REL = Path("audits/RUSSIAN-LEARNING-ENGINE-VALIDATION-CURRENT-V3-SUMMARY.txt")


def run(root: Path, label: str, rel: str) -> dict[str, object]:
    script = root / rel
    if not script.is_file():
        return {"label": label, "script": rel, "exit_code": 2, "stdout": "", "stderr": f"Missing script: {rel}"}
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
        "script": rel,
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def write_summary(root: Path, rows: list[dict[str, object]]) -> Path:
    passed = all(int(row["exit_code"]) == 0 for row in rows)
    path = root / SUMMARY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN LEARNING ENGINE — CURRENT V3 AGGREGATE VALIDATION",
        "",
        f"OVERALL_STATUS: {'PASS' if passed else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"CHECKS_TOTAL: {len(rows)}",
        "",
        "CHECKS",
    ]
    for row in rows:
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
            "EXPECTED AUDITS",
            "- audits/RUSSIAN-SKILL-GRAPH-INDEPENDENT-VALIDATION.txt",
            "- audits/RUSSIAN-EXPLANATION-CANONICAL-VALIDATION.txt",
            "- audits/RUSSIAN-EXCEPTIONS-CANONICAL-VALIDATION.txt",
            "- audits/RUSSIAN-EXCEPTIONS-PRACTICE-VALIDATION.txt",
            "- audits/RUSSIAN-ERROR-EXCEPTION-HANDOFF-VALIDATION.txt",
            "",
            "CHECKPOINT MEANING",
            "- PASS proves current source/data structural gate including Skill Graph snapshot coverage.",
            "- PASS does not authorize Tilda/public integration by itself.",
            "",
            "SAFETY",
            "- Current EGE trainer remains frozen/unchanged.",
            "- No Git/Tilda/network write is performed by this runner.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    rows: list[dict[str, object]] = []
    for label, rel in CHECKS:
        print(f"== {label} ==")
        row = run(root, label, rel)
        rows.append(row)
        if row["stdout"]:
            print(row["stdout"])
        if row["stderr"]:
            print(row["stderr"], file=sys.stderr)
        print(f"exit={row['exit_code']}\n")
    summary = write_summary(root, rows)
    passed = all(int(row["exit_code"]) == 0 for row in rows)
    print(f"Aggregate summary: {summary}")
    print(f"OVERALL_STATUS={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
