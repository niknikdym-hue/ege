#!/usr/bin/env python3
"""Deterministic reference session selector for the Russian Exceptions Trainer.

This is a data-layer reference implementation for local validation/design work.
It does not write learner state and is not connected to Tilda or the current EGE
trainer.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_COUNT = 10
ALLOWED_SOURCES = {"all_exceptions", "my_exceptions", "work_on_errors", "handoff"}
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
TRANSFER_RANK = {
    "recognition": 0,
    "guided_recall": 1,
    "independent_context": 2,
    "transfer": 3,
}


class SelectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    exception_id: str
    queue_bucket: str
    queue_rank: int
    due_at: str
    last_wrong_at: str
    launch_rank: int


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise SelectionError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SelectionError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        text = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def resolve_now(value: str | None) -> datetime:
    if value:
        parsed = parse_time(value)
        if parsed is None:
            raise SelectionError(f"Invalid --now timestamp: {value}")
        return parsed
    return datetime.now(timezone.utc)


def index_exceptions(data: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise SelectionError("Canonical exceptions file must contain items[]")
    result: dict[str, dict[str, Any]] = {}
    for item in data["items"]:
        if not isinstance(item, dict):
            continue
        exception_id = item.get("exception_id")
        if not isinstance(exception_id, str) or not exception_id:
            continue
        if exception_id in result:
            raise SelectionError(f"Duplicate exception_id: {exception_id}")
        result[exception_id] = item
    return result


def index_practice(data: Any) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise SelectionError("Canonical practice file must contain items[]")
    by_id: dict[str, dict[str, Any]] = {}
    by_exception: dict[str, list[dict[str, Any]]] = {}
    for item in data["items"]:
        if not isinstance(item, dict):
            continue
        pid = item.get("practice_item_id")
        exception_id = item.get("exception_id")
        if not isinstance(pid, str) or not pid or not isinstance(exception_id, str):
            continue
        if pid in by_id:
            raise SelectionError(f"Duplicate practice_item_id: {pid}")
        by_id[pid] = item
        by_exception.setdefault(exception_id, []).append(item)
    for rows in by_exception.values():
        rows.sort(key=lambda row: str(row.get("practice_item_id", "")))
    return by_id, by_exception


def learner_exception_states(state: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(state, dict):
        return {}
    exceptions = state.get("exceptions")
    if not isinstance(exceptions, dict):
        return {}
    return {str(k): v for k, v in exceptions.items() if isinstance(v, dict)}


def bucket_for(
    exception_id: str,
    state: dict[str, Any] | None,
    *,
    now: datetime,
    source: str,
    handoff: set[str],
) -> tuple[str, int]:
    if exception_id in handoff and source in {"handoff", "work_on_errors"}:
        return "Q4_HANDOFF", 0

    if state:
        due_at = parse_time(state.get("next_due_at"))
        if due_at is not None and due_at <= now:
            return "Q1_DUE", 1 if source in {"handoff", "work_on_errors"} else 0

        status = state.get("status")
        if status in {"active", "due"} or int(state.get("active_error_count") or 0) > 0:
            return "Q2_ACTIVE_ERROR", 2 if source in {"handoff", "work_on_errors"} else 1

        if state.get("transfer_passed") is False and int(state.get("seen_count") or 0) > 0:
            return "Q3_FAILED_TRANSFER", 3 if source in {"handoff", "work_on_errors"} else 2

        if status == "stabilized":
            return "Q7_STABILIZED", 7

    if exception_id in handoff:
        return "Q4_HANDOFF", 3

    return "Q5_NEW", 5


def launch_rank(exception: dict[str, Any]) -> int:
    value = exception.get("launch_priority")
    return PRIORITY_RANK.get(value, PRIORITY_RANK["P2"])


def build_candidates(
    exceptions: dict[str, dict[str, Any]],
    by_exception: dict[str, list[dict[str, Any]]],
    states: dict[str, dict[str, Any]],
    *,
    now: datetime,
    source: str,
    handoff: set[str],
) -> list[Candidate]:
    result: list[Candidate] = []
    for exception_id, exception in exceptions.items():
        practices = [
            row
            for row in by_exception.get(exception_id, [])
            if row.get("status") in {"source_verified", "reviewed"}
        ]
        if not practices:
            continue

        state = states.get(exception_id)
        if source == "my_exceptions" and not state:
            continue
        if source in {"handoff", "work_on_errors"} and handoff and exception_id not in handoff:
            # Narrow sessions remain focused on exact handoff IDs.
            continue

        bucket, rank = bucket_for(
            exception_id,
            state,
            now=now,
            source=source,
            handoff=handoff,
        )
        due_at = str(state.get("next_due_at") or "") if state else ""
        last_wrong_at = str(state.get("last_wrong_at") or "") if state else ""
        result.append(
            Candidate(
                exception_id=exception_id,
                queue_bucket=bucket,
                queue_rank=rank,
                due_at=due_at,
                last_wrong_at=last_wrong_at,
                launch_rank=launch_rank(exception),
            )
        )

    def key(row: Candidate) -> tuple[Any, ...]:
        due_key = row.due_at or "9999-12-31T23:59:59+00:00"
        # More recent wrong timestamp first: invert lexically by converting to epoch when parseable.
        parsed_wrong = parse_time(row.last_wrong_at)
        wrong_rank = -parsed_wrong.timestamp() if parsed_wrong else 0.0
        return (
            row.queue_rank,
            due_key,
            wrong_rank,
            row.launch_rank,
            row.exception_id,
        )

    result.sort(key=key)
    return result


def desired_transfer_level(state: dict[str, Any] | None) -> list[str]:
    if not state or int(state.get("seen_count") or 0) == 0:
        return ["recognition", "guided_recall", "independent_context", "transfer"]

    if state.get("last_result") == "wrong":
        return ["guided_recall", "independent_context", "recognition", "transfer"]

    if state.get("last_transfer_level") == "recognition":
        return ["guided_recall", "independent_context", "transfer", "recognition"]

    if state.get("transfer_passed") is False:
        return ["independent_context", "transfer", "guided_recall", "recognition"]

    if state.get("retention_passed") is False:
        return ["transfer", "independent_context", "guided_recall", "recognition"]

    return ["independent_context", "transfer", "guided_recall", "recognition"]


def practice_sort_key(
    row: dict[str, Any],
    state: dict[str, Any] | None,
    used_contexts: set[str],
    recent_contexts: set[str],
) -> tuple[Any, ...]:
    desired = desired_transfer_level(state)
    transfer = str(row.get("transfer_level") or "recognition")
    try:
        transfer_rank = desired.index(transfer)
    except ValueError:
        transfer_rank = 99

    signature = str(row.get("context_signature") or "")
    repeat_penalty = 1 if signature and (signature in used_contexts or signature in recent_contexts) else 0
    return (
        repeat_penalty,
        transfer_rank,
        TRANSFER_RANK.get(transfer, 99),
        str(row.get("practice_item_id", "")),
    )


def domain_for_exception(exception: dict[str, Any]) -> str:
    skills = exception.get("skill_ids")
    if isinstance(skills, list) and skills:
        return str(skills[0])
    return "unknown"


def select_session(
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

    candidates = build_candidates(
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

    # Multiple passes allow a second context for the same exception after other cards.
    max_passes = 4
    for _pass in range(max_passes):
        made_progress = False
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

            # Minimum 2-card gap for same exception when alternatives exist.
            if exception_id in last_exception_ids[-2:]:
                continue

            domain = domain_for_exception(exception)
            if len(last_domains) >= 3 and all(x == domain for x in last_domains[-3:]):
                # Soft constraint: skip for now; a later pass may use it if needed.
                continue

            practices.sort(
                key=lambda row: practice_sort_key(row, state, used_contexts, recent_contexts)
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
                }
            )
            used_practice.add(pid)
            if signature:
                used_contexts.add(signature)
            last_exception_ids.append(exception_id)
            last_domains.append(domain)
            made_progress = True

        if len(selected) >= count or not made_progress:
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
    parser.add_argument("--source", choices=sorted(ALLOWED_SOURCES), default="all_exceptions")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--now", type=str, default=None)
    parser.add_argument("--exception-id", action="append", default=[])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        exceptions = index_exceptions(load_json(args.exceptions))
        _, by_exception = index_practice(load_json(args.practice))
        state_data = load_json(args.state) if args.state else {}
        states = learner_exception_states(state_data)
        now = resolve_now(args.now)
        handoff = {str(x) for x in args.exception_id if x}
        session = select_session(
            exceptions,
            by_exception,
            states,
            count=args.count,
            now=now,
            source=args.source,
            handoff=handoff,
        )
    except SelectionError as exc:
        print(f"SELECTION ERROR: {exc}", file=sys.stderr)
        return 2

    payload = {
        "schema_version":"1.0.0",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
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
