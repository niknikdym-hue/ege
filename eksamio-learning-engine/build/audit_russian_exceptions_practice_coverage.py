#!/usr/bin/env python3
"""Audit practice coverage of canonical Russian Exceptions Bank.

Produces an actionable gap report so future practice waves close real source gaps
instead of increasing card count arbitrarily. Data-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise AuditError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AuditError(f"Invalid JSON in {path}: {exc}") from exc


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--exceptions",
        type=Path,
        default=root / "build" / "RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json",
    )
    parser.add_argument(
        "--practice",
        type=Path,
        default=root / "build" / "RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json",
    )
    parser.add_argument(
        "--priority",
        type=Path,
        default=root / "build" / "RUSSIAN-EXCEPTIONS-LAUNCH-PRIORITY.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root / "audits" / "RUSSIAN-EXCEPTIONS-PRACTICE-COVERAGE.json",
    )
    parser.add_argument(
        "--text-output",
        type=Path,
        default=root / "audits" / "RUSSIAN-EXCEPTIONS-PRACTICE-COVERAGE.txt",
    )
    args = parser.parse_args()

    try:
        exceptions_data = load_json(args.exceptions)
        practice_data = load_json(args.practice)
        priority_data = load_json(args.priority)
        exceptions = exceptions_data.get("items") if isinstance(exceptions_data, dict) else None
        practice = practice_data.get("items") if isinstance(practice_data, dict) else None
        priorities = priority_data.get("items") if isinstance(priority_data, dict) else None
        if not isinstance(exceptions, list) or not isinstance(practice, list) or not isinstance(priorities, list):
            raise AuditError("Expected items[] in exceptions, practice and priority files")

        priority_by_id = {
            row.get("exception_id"): row.get("launch_priority")
            for row in priorities
            if isinstance(row, dict) and isinstance(row.get("exception_id"), str)
        }
        practice_by_exception: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in practice:
            if isinstance(row, dict) and isinstance(row.get("exception_id"), str):
                practice_by_exception[row["exception_id"]].append(row)

        rows: list[dict[str, Any]] = []
        mode_counts_total: Counter[str] = Counter()
        priority_counts: Counter[str] = Counter()
        priority_uncovered: Counter[str] = Counter()

        for item in exceptions:
            if not isinstance(item, dict):
                raise AuditError("Non-object exception item")
            exception_id = item.get("exception_id")
            if not isinstance(exception_id, str) or not exception_id:
                raise AuditError("Exception without exception_id")
            cards = practice_by_exception.get(exception_id, [])
            modes = Counter(str(card.get("mode")) for card in cards)
            transfer_levels = Counter(str(card.get("transfer_level")) for card in cards)
            for mode, count in modes.items():
                mode_counts_total[mode] += count
            priority = priority_by_id.get(exception_id, "MISSING")
            priority_counts[priority] += 1
            if not cards:
                priority_uncovered[priority] += 1
            rows.append(
                {
                    "exception_id": exception_id,
                    "prompt_label": item.get("prompt_label"),
                    "skill_ids": item.get("skill_ids", []),
                    "subskill_ids": item.get("subskill_ids", []),
                    "launch_priority": priority,
                    "practice_count": len(cards),
                    "practice_modes": dict(sorted(modes.items())),
                    "transfer_levels": dict(sorted(transfer_levels.items())),
                    "practice_item_ids": sorted(
                        str(card.get("practice_item_id"))
                        for card in cards
                        if card.get("practice_item_id")
                    ),
                    "coverage_status": "covered" if cards else "uncovered",
                }
            )

        rows.sort(
            key=lambda row: (
                {"P0":0,"P1":1,"P2":2,"P3":3}.get(row["launch_priority"], 9),
                0 if row["practice_count"] == 0 else 1,
                row["practice_count"],
                row["exception_id"],
            )
        )

        total = len(rows)
        covered = sum(1 for row in rows if row["practice_count"] > 0)
        uncovered = total - covered
        p0p1_uncovered = [
            row for row in rows
            if row["launch_priority"] in {"P0","P1"} and row["practice_count"] == 0
        ]
        no_transfer = [
            row for row in rows
            if row["practice_count"] > 0
            and not any(level in row["transfer_levels"] for level in ("independent_context","transfer"))
        ]
        recognition_only = [
            row for row in rows
            if row["practice_count"] > 0
            and set(row["transfer_levels"]) <= {"recognition"}
        ]

        payload = {
            "schema_version":"1.0.0",
            "generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "exceptions_total":total,
            "exceptions_covered":covered,
            "exceptions_uncovered":uncovered,
            "coverage_ratio": round(covered / total, 4) if total else 0.0,
            "practice_items_total":len(practice),
            "priority_counts":dict(sorted(priority_counts.items())),
            "priority_uncovered":dict(sorted(priority_uncovered.items())),
            "practice_mode_counts":dict(sorted(mode_counts_total.items())),
            "p0_p1_uncovered_count":len(p0p1_uncovered),
            "covered_without_context_or_transfer_count":len(no_transfer),
            "recognition_only_exception_count":len(recognition_only),
            "rows":rows,
        }
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

        lines = [
            "EKSAMIO LEARNING ENGINE",
            "RUSSIAN EXCEPTIONS — PRACTICE COVERAGE AUDIT",
            "",
            f"GENERATED_AT_UTC: {payload['generated_at_utc']}",
            f"EXCEPTIONS_TOTAL: {total}",
            f"EXCEPTIONS_COVERED: {covered}",
            f"EXCEPTIONS_UNCOVERED: {uncovered}",
            f"COVERAGE_RATIO: {payload['coverage_ratio']}",
            f"PRACTICE_ITEMS_TOTAL: {len(practice)}",
            f"P0_P1_UNCOVERED: {len(p0p1_uncovered)}",
            f"COVERED_WITHOUT_CONTEXT_OR_TRANSFER: {len(no_transfer)}",
            f"RECOGNITION_ONLY_EXCEPTIONS: {len(recognition_only)}",
            "",
            "PRIORITY COUNTS",
        ]
        for key, value in sorted(priority_counts.items()):
            lines.append(f"- {key}: total={value}, uncovered={priority_uncovered.get(key,0)}")
        lines.extend(["", "TOP GAPS — P0/P1 WITHOUT PRACTICE"])
        if p0p1_uncovered:
            for row in p0p1_uncovered:
                lines.append(
                    f"- {row['launch_priority']} {row['exception_id']}: {row.get('prompt_label') or ''}"
                )
        else:
            lines.append("- none")
        lines.extend(["", "COVERED BUT NO INDEPENDENT_CONTEXT/TRANSFER"])
        if no_transfer:
            for row in no_transfer[:50]:
                lines.append(
                    f"- {row['launch_priority']} {row['exception_id']}: cards={row['practice_count']}, levels={','.join(row['transfer_levels'])}"
                )
            if len(no_transfer) > 50:
                lines.append(f"- ... plus {len(no_transfer)-50} more; see JSON audit")
        else:
            lines.append("- none")
        lines.extend([
            "",
            "NEXT WAVE RULE",
            "1. Close uncovered P0/P1 first.",
            "2. Then add transfer/context cards to covered P0/P1 that only have recognition/recall.",
            "3. Then close P2 core-rule gaps.",
            "4. Do not expand P3 merely to raise card count while higher-priority gaps remain.",
            "",
            "SAFETY",
            "- This audit does not change source/practice/runtime data.",
            "- Difficulty is not inferred.",
            "",
        ])
        args.text_output.parent.mkdir(parents=True, exist_ok=True)
        args.text_output.write_text("\n".join(lines), encoding="utf-8")
        print(
            f"PASS: exceptions={total}, covered={covered}, uncovered={uncovered}, P0/P1 uncovered={len(p0p1_uncovered)}"
        )
        print(f"JSON: {args.json_output}")
        print(f"TEXT: {args.text_output}")
        return 0
    except AuditError as exc:
        print(f"AUDIT ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
