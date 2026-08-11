#!/usr/bin/env python3
"""Derive conservative launch priority metadata for canonical Russian exceptions.

Priority is scheduling metadata, never difficulty. The builder uses only explicit
canonical source evidence and leaves ambiguous cases at core P2 rather than
inventing recent-frequency evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CURRENT_YEAR = 2026
RECENT_YEARS = {2024, 2025, 2026}
YEAR_RE = re.compile(r"\b(20\d{2})\b")


class BuildError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise BuildError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(f"Invalid JSON in {path}: {exc}") from exc


def text_of_ref(ref: dict[str, Any]) -> str:
    return " ".join(
        str(ref.get(key) or "") for key in ("source_type", "source_path", "locator", "purpose")
    ).lower()


def explicit_years(refs: list[dict[str, Any]]) -> set[int]:
    years: set[int] = set()
    for ref in refs:
        for match in YEAR_RE.findall(text_of_ref(ref)):
            years.add(int(match))
    return years


def derive(item: dict[str, Any]) -> dict[str, Any]:
    exception_id = item.get("exception_id")
    refs = [x for x in item.get("source_refs", []) if isinstance(x, dict)]
    combined = " ".join(text_of_ref(x) for x in refs)
    years = explicit_years(refs)
    reasons: list[str] = []
    evidence: list[dict[str, Any]] = []

    for ref in refs:
        source_type = ref.get("source_type")
        txt = text_of_ref(ref)
        if source_type == "official_fipi" and ("2026" in txt or "current" in txt):
            reasons.append("current_official_list")
            evidence.append(ref)
        if source_type in {"existing_trainer", "internal_verified_source"} and (
            "2026" in txt or "current" in txt
        ):
            reasons.append("current_2026_trainer_exact")
            evidence.append(ref)

    if reasons:
        priority = "P0"
    elif len(years & RECENT_YEARS) >= 2:
        priority = "P1"
        reasons.append("repeated_recent_years")
        evidence = refs
    elif item.get("legacy") is True or "historical-only" in combined or "legacy-only" in combined:
        priority = "P3"
        reasons.append("historical_only")
        evidence = refs
    elif item.get("exam_priority") == "low":
        priority = "P3"
        reasons.append("rare_reference_case")
        evidence = refs
    else:
        priority = "P2"
        reasons.append("core_rozental_current_skill")
        evidence = refs

    # Deduplicate while preserving order.
    reasons = list(dict.fromkeys(reasons))
    return {
        "exception_id": exception_id,
        "launch_priority": priority,
        "priority_reason_codes": reasons,
        "explicit_source_years": sorted(years),
        "evidence": evidence,
        "status": "derived",
        "difficulty": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--exceptions",
        type=Path,
        default=root / "build" / "RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "build" / "RUSSIAN-EXCEPTIONS-LAUNCH-PRIORITY.json",
    )
    args = parser.parse_args()

    try:
        data = load_json(args.exceptions)
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            raise BuildError("Canonical Exceptions Bank must contain items[]")
        rows = []
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                raise BuildError("Non-object exception item")
            exception_id = item.get("exception_id")
            if not isinstance(exception_id, str) or not exception_id:
                raise BuildError("Exception without exception_id")
            if exception_id in seen:
                raise BuildError(f"Duplicate exception_id: {exception_id}")
            seen.add(exception_id)
            rows.append(derive(item))
        rows.sort(key=lambda row: row["exception_id"])
        counts = {p: sum(1 for row in rows if row["launch_priority"] == p) for p in ("P0","P1","P2","P3")}
        payload = {
            "schema_version":"1.0.0",
            "subject":"russian",
            "exam":"ege",
            "purpose":"derived_exceptions_launch_priority",
            "generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "priority_is_not_difficulty":True,
            "difficulty_policy":"null/not guessed",
            "items":rows,
            "counts":counts,
            "production_integration":"not_connected",
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"PASS: {len(rows)} priorities; counts={counts}")
        print(f"Output: {args.output}")
        return 0
    except BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
