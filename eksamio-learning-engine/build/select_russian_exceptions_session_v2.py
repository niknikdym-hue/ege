#!/usr/bin/env python3
"""Priority-aware current selector for Russian Exceptions Trainer sessions.

Loads canonical exceptions + derived launch-priority overlay before delegating to
the hardened selector. No learner-state writes and no production integration.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import select_russian_exceptions_session as base
import select_russian_exceptions_session_current as current


def apply_priorities(
    exceptions: dict[str, dict[str, Any]], priority_data: Any
) -> dict[str, dict[str, Any]]:
    rows = priority_data.get("items") if isinstance(priority_data, dict) else None
    if not isinstance(rows, list):
        raise base.SelectionError("Priority overlay must contain items[]")
    priorities: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        exception_id = row.get("exception_id")
        launch_priority = row.get("launch_priority")
        if not isinstance(exception_id, str) or not exception_id:
            continue
        if launch_priority not in base.PRIORITY_RANK:
            raise base.SelectionError(
                f"{exception_id}: invalid launch_priority {launch_priority!r}"
            )
        if exception_id in priorities:
            raise base.SelectionError(f"Duplicate priority row: {exception_id}")
        priorities[exception_id] = launch_priority

    missing = sorted(set(exceptions) - set(priorities))
    if missing:
        raise base.SelectionError(
            f"Priority overlay missing {len(missing)} canonical exception IDs; first={missing[:5]}"
        )

    merged: dict[str, dict[str, Any]] = {}
    for exception_id, row in exceptions.items():
        copy = json.loads(json.dumps(row, ensure_ascii=False))
        copy["launch_priority"] = priorities[exception_id]
        merged[exception_id] = copy
    return merged


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--exceptions",
        type=Path,
        default=root_default / "build" / "RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json",
    )
    parser.add_argument(
        "--practice",
        type=Path,
        default=root_default / "build" / "RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json",
    )
    parser.add_argument(
        "--priority",
        type=Path,
        default=root_default / "build" / "RUSSIAN-EXCEPTIONS-LAUNCH-PRIORITY.json",
    )
    parser.add_argument("--state", type=Path, default=None)
    parser.add_argument("--source", choices=sorted(base.ALLOWED_SOURCES), default="all_exceptions")
    parser.add_argument("--count", type=int, default=base.DEFAULT_COUNT)
    parser.add_argument("--now", type=str, default=None)
    parser.add_argument("--exception-id", action="append", default=[])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        exceptions = base.index_exceptions(base.load_json(args.exceptions))
        exceptions = apply_priorities(exceptions, base.load_json(args.priority))
        _, by_exception = base.index_practice(base.load_json(args.practice))
        state_data = base.load_json(args.state) if args.state else {}
        states = base.learner_exception_states(state_data)
        now = base.resolve_now(args.now)
        handoff = {str(x) for x in args.exception_id if x}
        session = current.select_session_current(
            exceptions,
            by_exception,
            states,
            count=args.count,
            now=now,
            source=args.source,
            handoff=handoff,
        )
    except base.SelectionError as exc:
        print(f"SELECTION ERROR: {exc}", file=sys.stderr)
        return 2

    payload = {
        "schema_version":"1.0.2",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "selector":"priority_aware_v2",
        "source":args.source,
        "requested_count":args.count,
        "selected_count":len(session),
        "handoff_exception_ids":sorted(handoff),
        "items":session,
        "production_integration":"not_connected",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
