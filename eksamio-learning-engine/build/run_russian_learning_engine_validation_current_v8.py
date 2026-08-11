#!/usr/bin/env python3
"""Current v8 aggregate local validation runner for Russian Learning Engine.

Current local checkpoint gate: corrected canonical data, both runtimes, independent
Skill Graph audit, session selector tests, explanation resolver tests and exact
handoff validation. No network or production mutation.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CHECKS = [
    ("SKILL_GRAPH_VS_TRAINER", "build/validate_russian_skill_graph_against_trainer.py"),
    ("EXPLANATIONS", "build/build_russian_explanation_bank.py"),
    ("EXPLANATION_RUNTIME", "build/build_russian_explanation_runtime.py"),
    ("EXPLANATION_RESOLVER_SYNTHETIC_TESTS", "build/tests/test_russian_explanation_resolver.py"),
    ("EXCEPTIONS_CURRENT_CORRECTED_V2", "build/build_russian_exceptions_bank_current_v2.py"),
    ("EXCEPTIONS_PRACTICE_CURRENT_CORRECTED_72_V2", "build/build_russian_exceptions_practice_current_corrected_v2.py"),
    ("EXCEPTIONS_LAUNCH_PRIORITY", "build/build_russian_exceptions_launch_priority.py"),
    ("EXCEPTIONS_RUNTIME", "build/build_russian_exceptions_runtime.py"),
    ("SESSION_SELECTOR_SYNTHETIC_TESTS", "build/tests/test_russian_exceptions_session_selector.py"),
    ("SESSION_PRIORITY_SYNTHETIC_TESTS", "build/tests/test_russian_exceptions_priority_selector.py"),
    ("ERROR_TO_EXCEPTION_HANDOFF_CURRENT", "build/validate_russian_error_exception_handoff_current.py"),
]

SUMMARY_REL = Path("audits/RUSSIAN-LEARNING-ENGINE-VALIDATION-CURRENT-V8-SUMMARY.txt")


def run(root: Path, label: str, rel: str) -> dict[str, object]:
    script = root / rel
    if not script.is_file():
        return {"label":label,"script":rel,"exit_code":2,"stdout":"","stderr":f"Missing script: {rel}"}
    proc = subprocess.run(
        [sys.executable, str(script)], cwd=str(root), capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False,
    )
    return {"label":label,"script":rel,"exit_code":proc.returncode,"stdout":proc.stdout.strip(),"stderr":proc.stderr.strip()}


def write_summary(root: Path, rows: list[dict[str, object]]) -> Path:
    passed = all(int(row["exit_code"]) == 0 for row in rows)
    path = root / SUMMARY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN LEARNING ENGINE — CURRENT V8 AGGREGATE VALIDATION",
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
        "EXPECTED BUILD OUTPUTS",
        "- build/RUSSIAN-EXPLANATION-BANK-CANONICAL.json",
        "- build/RUSSIAN-EXPLANATION-RUNTIME.json",
        "- build/RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json",
        "- build/RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json",
        "- build/RUSSIAN-EXCEPTIONS-LAUNCH-PRIORITY.json",
        "- build/RUSSIAN-EXCEPTIONS-RUNTIME.json",
        "",
        "EXPLANATION RESOLVER INVARIANTS",
        "- external resolver never owns/replaces current answer or score",
        "- exact error evidence may resolve exact explanation",
        "- partial evidence remains partial",
        "- no safe route preserves current feedback only",
        "- demo/control suppress learning feedback until completion",
        "",
        "CURRENT CORRECTION INVARIANTS",
        "- superseded `introductory_v_kontse_kontsov_dual_function` excluded",
        "- superseded `ex-practice-end-finally-001` excluded",
        "- corrected replacement included",
        "- active practice total exactly 72",
        "",
        "SAFETY",
        "- Current EGE trainer remains frozen/unchanged.",
        "- No Tilda/public write is performed.",
        "- PASS is the local source/data/runtime checkpoint, not publication authorization.",
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
