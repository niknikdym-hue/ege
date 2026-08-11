#!/usr/bin/env python3
"""Current v4 aggregate local validation runner for Russian Learning Engine.

Uses the corrected current Exceptions source/practice manifests, independent
Skill Graph validation, selector tests and handoff cross-link checks.
No network or production mutation.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHECKS = [
    ("SKILL_GRAPH_VS_TRAINER", "build/validate_russian_skill_graph_against_trainer.py"),
    ("EXPLANATIONS", "build/build_russian_explanation_bank.py"),
    ("EXCEPTIONS_CURRENT_CORRECTED", "build/build_russian_exceptions_bank_current.py"),
    ("EXCEPTIONS_PRACTICE_CURRENT_CORRECTED_72", "build/build_russian_exceptions_practice_current_corrected.py"),
    ("SESSION_SELECTOR_SYNTHETIC_TESTS", "build/tests/test_russian_exceptions_session_selector.py"),
    ("ERROR_TO_EXCEPTION_HANDOFF", "build/validate_russian_error_exception_handoff.py"),
]

SUMMARY_REL = Path("audits/RUSSIAN-LEARNING-ENGINE-VALIDATION-CURRENT-V4-SUMMARY.txt")


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
    return {"label":label,"script":rel,"exit_code":proc.returncode,"stdout":proc.stdout.strip(),"stderr":proc.stderr.strip()}


def write_summary(root: Path, rows: list[dict[str, object]]) -> Path:
    passed = all(int(row["exit_code"]) == 0 for row in rows)
    path = root / SUMMARY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN LEARNING ENGINE — CURRENT V4 AGGREGATE VALIDATION",
        "",
        f"OVERALL_STATUS: {'PASS' if passed else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"CHECKS_TOTAL: {len(rows)}",
        "CURRENT_EXCEPTIONS_MANIFEST: 118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json",
        "CURRENT_PRACTICE_MANIFEST: 119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json",
        "EXPECTED_ACTIVE_PRACTICE_ITEMS: 72",
        "",
        "CHECKS",
    ]
    for row in rows:
        code = int(row["exit_code"])
        lines.extend([f"- {row['label']}: {'PASS' if code == 0 else 'FAIL'}",f"  SCRIPT: {row['script']}",f"  EXIT_CODE: {code}"])
        if row.get("stdout"):
            lines.append("  STDOUT:")
            lines.extend(f"    {line}" for line in str(row["stdout"]).splitlines())
        if row.get("stderr"):
            lines.append("  STDERR:")
            lines.extend(f"    {line}" for line in str(row["stderr"]).splitlines())
    lines.extend([
        "",
        "CORRECTION GATE",
        "- superseded `introductory_v_kontse_kontsov_dual_function` must not enter current canonical Exceptions Bank",
        "- superseded `ex-practice-end-finally-001` must not enter current canonical Practice Bank",
        "- replacement `false_introductory_v_kontse_kontsov` and corrected practice card must resolve",
        "",
        "EXPECTED AUDITS",
        "- audits/RUSSIAN-SKILL-GRAPH-INDEPENDENT-VALIDATION.txt",
        "- audits/RUSSIAN-EXPLANATION-CANONICAL-VALIDATION.txt",
        "- audits/RUSSIAN-EXCEPTIONS-CANONICAL-VALIDATION.txt",
        "- audits/RUSSIAN-EXCEPTIONS-PRACTICE-VALIDATION.txt",
        "- audits/RUSSIAN-ERROR-EXCEPTION-HANDOFF-VALIDATION.txt",
        "",
        "SAFETY",
        "- Current EGE trainer remains frozen/unchanged.",
        "- PASS is a source/data checkpoint, not Tilda publication authorization.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    rows = []
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
