#!/usr/bin/env python3
"""Hardened current selector for Russian Exceptions Trainer sessions.

Uses helper/indexing functions from select_russian_exceptions_session.py but
adds fail-closed handoff behavior and controlled relaxation of soft diversity
constraints when a focused or small candidate set would otherwise under-fill.
Not connected to production.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import select_russian_exceptions_session as base


def select_session_current(
    exceptions: dict[str, dict[str, Any]],
    by_exception: dict[str, list[dict[str, Any]]],
    states: dict[str, dict[str, Any]],
    *,
    count: int,
    now: datetime,
    source: str,
    handoff: set[str],
) -> list[dict[str, Any]]:
    if count <= 0:
        return []

    if source in {"handoff", "work_on_errors"} and not handoff:
        # Broad/empty handoff must never guess an exception.
        return []

    candidates = base.build_candidates(
        exceptions,
        by_exception,
        states,
        now=now,
        source=source,
        handoff=handoff,
    )

    selected: list[dict[str, Any]] = []
    used_practice: set[str] = set()
    used_contexts: set[str] = set()
    last_exception_ids: list[str] = []
    last_domains: list[str] = []

    # Four passes progressively relax only SOFT constraints, never source eligibility.
    # pass 0: strict diversity/gap
    # pass 1: relax domain diversity
    # pass 2+: allow same exception sooner if distinct practice/context is necessary
    for pass_index in range(4):
        made_progress = False
        relax_domain = pass_index >= 1
        relax_exception_gap = pass_index >= 2

        for candidate in candidates:
            if len(selected) >= count:
                break

            exception_id = candidate.exception_id
            exception = exceptions[exception_id]
            state = states.get(exception_id)
            recent_contexts = set(state.get("recent_context_signatures") or []) if state else set()

            practices = [
                row
                for row in by_exception.get(exception_id, [])
                if row.get("status") in {"source_verified", "reviewed"}
                and row.get("practice_item_id") not in used_practice
            ]
            if not practices:
                continue

            if not relax_exception_gap and exception_id in last_exception_ids[-2:]:
                continue

            domain = base.domain_for_exception(exception)
            if (
                not relax_domain
                and len(last_domains) >= 3
                and all(x == domain for x in last_domains[-3:])
            ):
                continue

            practices.sort(
                key=lambda row: base.practice_sort_key(
                    row, state, used_contexts, recent_contexts
                )
            )

            choice = None
            for row in practices:
                signature = str(row.get("context_signature") or "")
                if signature and signature in used_contexts:
                    continue
                choice = row
                break
            if choice is None:
                continue

            pid = str(choice["practice_item_id"])
            signature = str(choice.get("context_signature") or "")
            reason_code = {
                "Q1_DUE": "due_review",
                "Q2_ACTIVE_ERROR": "unresolved_error",
                "Q3_FAILED_TRANSFER": "failed_transfer",
                "Q4_HANDOFF": "exact_handoff",
                "Q5_NEW": "new_core_rule",
                "Q7_STABILIZED": "stabilized_maintenance",
            }.get(candidate.queue_bucket, "fallback_fill")

            selected.append(
                {
                    "position": len(selected) + 1,
                    "practice_item_id": pid,
                    "exception_id": exception_id,
                    "queue_bucket": candidate.queue_bucket,
                    "reason_code": reason_code,
                    "domain": domain,
                    "mode": choice.get("mode"),
                    "transfer_level": choice.get("transfer_level"),
                    "context_signature": signature,
                    "soft_constraints_relaxed": {
                        "domain": relax_domain,
                        "exception_gap": relax_exception_gap,
                    },
                }
            )
            used_practice.add(pid)
            if signature:
                used_contexts.add(signature)
            last_exception_ids.append(exception_id)
            last_domains.append(domain)
            made_progress = True

        if len(selected) >= count:
            break
        if not made_progress and pass_index >= 2:
            break

    return selected


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
    parser.add_argument("--state", type=Path, default=None)
    parser.add_argument("--source", choices=sorted(base.ALLOWED_SOURCES), default="all_exceptions")
    parser.add_argument("--count", type=int, default=base.DEFAULT_COUNT)
    parser.add_argument("--now", type=str, default=None)
    parser.add_argument("--exception-id", action="append", default=[])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        exceptions = base.index_exceptions(base.load_json(args.exceptions))
        _, by_exception = base.index_practice(base.load_json(args.practice))
        state_data = base.load_json(args.state) if args.state else {}
        states = base.learner_exception_states(state_data)
        now = base.resolve_now(args.now)
        handoff = {str(x) for x in args.exception_id if x}
        session = select_session_current(
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
        "schema_version":"1.0.1",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "selector":"current",
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
