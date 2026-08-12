#!/usr/bin/env python3
"""Current v10 aggregate local validation runner for Russian Learning Engine.

Validates current corrected canonical/runtime data, Skill Graph, explanation resolver,
session/state logic, deterministic Exceptions T123 chunking, coverage/size and handoff checks.
Uses the audited course-grade 80-card practice builder so aggregate validation cannot
silently overwrite reviewed learner feedback with an older checkpoint.
No network or production mutation.
"""

from __future__ import annotations

import json
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
    ("EXCEPTIONS_PRACTICE_COURSE_GRADE", "build/build_russian_exceptions_practice_course_grade.py"),
    ("EXCEPTIONS_LAUNCH_PRIORITY", "build/build_russian_exceptions_launch_priority.py"),
    ("EXCEPTIONS_RUNTIME", "build/build_russian_exceptions_runtime.py"),
    ("EXCEPTIONS_T123_CHUNKS", "build/build_russian_exceptions_t123_chunks.py"),
    ("EXCEPTIONS_PRACTICE_COVERAGE", "build/audit_russian_exceptions_practice_coverage.py"),
    ("RUNTIME_SIZE_AUDIT", "build/audit_russian_runtime_sizes.py"),
    ("SESSION_SELECTOR_SYNTHETIC_TESTS", "build/tests/test_russian_exceptions_session_selector.py"),
    ("SESSION_PRIORITY_SYNTHETIC_TESTS", "build/tests/test_russian_exceptions_priority_selector.py"),
    ("LEARNER_STATE_REDUCER_SYNTHETIC_TESTS", "build/tests/test_russian_exceptions_state_reducer.py"),
    ("ERROR_TO_EXCEPTION_HANDOFF_CURRENT", "build/validate_russian_error_exception_handoff_current.py"),
]

SUMMARY_REL = Path("audits/RUSSIAN-LEARNING-ENGINE-VALIDATION-CURRENT-V10-SUMMARY.txt")


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
    practice_manifest = json.loads((root / "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json").read_text(encoding="utf-8"))
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN LEARNING ENGINE — CURRENT V10 AGGREGATE VALIDATION",
        "",
        f"OVERALL_STATUS: {'PASS' if passed else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"CHECKS_TOTAL: {len(rows)}",
        "CURRENT_EXCEPTIONS_MANIFEST: 118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json",
        "CURRENT_PRACTICE_MANIFEST: 119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json",
        "CURRENT_PRACTICE_BUILDER: build/build_russian_exceptions_practice_course_grade.py",
        f"EXPECTED_ACTIVE_PRACTICE_ITEMS: {practice_manifest['expected_active_items']}",
        "",
        "CHECKS",
    ]
    for row in rows:
        code = int(row["exit_code"])
        lines.extend([f"- {row['label']}: {'PASS' if code == 0 else 'FAIL'}",f"  SCRIPT: {row['script']}",f"  EXIT_CODE: {code}"])
        stdout = str(row.get("stdout", "")).strip()
        stderr = str(row.get("stderr", "")).strip()
        if stdout:
            lines.append("  STDOUT:")
            lines.extend(f"    {line}" for line in stdout.splitlines())
        if stderr:
            lines.append("  STDERR:")
            lines.extend(f"    {line}" for line in stderr.splitlines())
    lines.extend([
        "",
        "STATE INVARIANTS",
        "- replayed event_id must be idempotent",
        "- one recognition correct never means stabilized/mastered",
        "- independent context may set transfer evidence but not permanent mastery",
        "- retention evidence remains separate from same-session success",
        "- state reducer does not invent due intervals/mastery thresholds",
        "",
        "EXPECTED BUILD/AUDIT OUTPUTS",
        "- build/RUSSIAN-EXPLANATION-BANK-CANONICAL.json",
        "- build/RUSSIAN-EXPLANATION-RUNTIME.json",
        "- build/RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json",
        "- build/RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json",
        "- build/RUSSIAN-EXCEPTIONS-LAUNCH-PRIORITY.json",
        "- build/RUSSIAN-EXCEPTIONS-RUNTIME.json",
        "- build/RUSSIAN-EXCEPTIONS-T123-CHUNKS-MANIFEST.json",
        "- audits/RUSSIAN-EXCEPTIONS-PRACTICE-COVERAGE.json",
        "- audits/RUSSIAN-RUNTIME-SIZE-AUDIT.txt",
        "",
        "CONTENT INVARIANT",
        "- Aggregate validation MUST rebuild practice with the audited course-grade builder; older corrected_v2 checkpoints must not overwrite learner feedback.",
        "",
        "SAFETY",
        "- Current EGE trainer remains frozen/unchanged.",
        "- No Tilda/localStorage production write is performed.",
        "- PASS is the local source/data/runtime/state checkpoint, not publication authorization.",
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
