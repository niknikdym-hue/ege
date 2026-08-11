#!/usr/bin/env python3
"""Pure reference reducer for Russian Exceptions learner state.

Aggregates one attempt event into anonymous local learner state with event-id
idempotency. It deliberately does NOT define mastery thresholds or due intervals.
No production storage writes are performed by this module.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StateError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise StateError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StateError(f"Invalid JSON in {path}: {exc}") from exc


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_profile(profile: Any) -> dict[str, Any]:
    if profile is None:
        profile = {}
    if not isinstance(profile, dict):
        raise StateError("Profile must be object")
    result = copy.deepcopy(profile)
    result.setdefault("schema_version", 1)
    result.setdefault("profile_id", f"local-{uuid.uuid4()}")
    result.setdefault("created_at", iso_now())
    result.setdefault("updated_at", result["created_at"])
    result.setdefault("exceptions", {})
    result.setdefault("processed_event_ids", [])
    result.setdefault("state_revision", 0)
    if not isinstance(result["exceptions"], dict):
        raise StateError("profile.exceptions must be object")
    if not isinstance(result["processed_event_ids"], list) or not all(
        isinstance(x, str) for x in result["processed_event_ids"]
    ):
        raise StateError("profile.processed_event_ids must be string array")
    if not isinstance(result["state_revision"], int) or result["state_revision"] < 0:
        raise StateError("profile.state_revision must be non-negative integer")
    return result


def validate_event(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise StateError("Attempt event must be object")
    required = (
        "event_id",
        "practice_item_id",
        "exception_id",
        "mode",
        "started_at",
        "answered_at",
        "is_correct",
        "response",
        "source",
    )
    missing = [field for field in required if field not in event]
    if missing:
        raise StateError(f"Attempt event missing fields: {missing}")
    for field in ("event_id", "practice_item_id", "exception_id", "mode", "started_at", "answered_at", "source"):
        if not isinstance(event.get(field), str) or not event[field]:
            raise StateError(f"event.{field} must be non-empty string")
    if not isinstance(event.get("is_correct"), bool):
        raise StateError("event.is_correct must be boolean")
    transfer = event.get("transfer_level")
    if transfer is not None and transfer not in {
        "recognition",
        "guided_recall",
        "independent_context",
        "transfer",
    }:
        raise StateError(f"invalid transfer_level: {transfer!r}")
    return copy.deepcopy(event)


def origin_from_source(source: str) -> str:
    return {
        "exceptions_all":"manual_practice",
        "my_exceptions":"manual_practice",
        "retry":"manual_practice",
        "retention":"retention_failure",
        "main_trainer_handoff":"main_trainer_exact_error",
    }.get(source, "manual_practice")


def new_exception_state(exception_id: str, answered_at: str, origin: str) -> dict[str, Any]:
    return {
        "exception_id": exception_id,
        "status": "new",
        "seen_count": 0,
        "correct_count": 0,
        "wrong_count": 0,
        "consecutive_correct": 0,
        "last_seen_at": None,
        "last_wrong_at": None,
        "last_correct_at": None,
        "last_result": None,
        "last_mode": None,
        "last_transfer_level": None,
        "next_due_at": None,
        "retention_stage": "new",
        "transfer_passed": False,
        "retention_passed": False,
        "origin": origin,
        "origin_ref": None,
        "active_error_count": 0,
        "last_practice_item_id": None,
        "recent_context_signatures": [],
        "updated_at": answered_at,
    }


def apply_event(profile: Any, event: Any) -> tuple[dict[str, Any], bool]:
    result = ensure_profile(profile)
    event = validate_event(event)

    event_id = event["event_id"]
    if event_id in result["processed_event_ids"]:
        return result, False

    exception_id = event["exception_id"]
    answered_at = event["answered_at"]
    state = result["exceptions"].get(exception_id)
    if state is None:
        state = new_exception_state(
            exception_id, answered_at, origin_from_source(event["source"])
        )
    elif not isinstance(state, dict):
        raise StateError(f"profile.exceptions[{exception_id!r}] must be object")
    else:
        state = copy.deepcopy(state)

    state.setdefault("seen_count", 0)
    state.setdefault("correct_count", 0)
    state.setdefault("wrong_count", 0)
    state.setdefault("consecutive_correct", 0)
    state.setdefault("active_error_count", 0)
    state.setdefault("transfer_passed", False)
    state.setdefault("retention_passed", False)
    state.setdefault("recent_context_signatures", [])
    if not isinstance(state["recent_context_signatures"], list):
        raise StateError(f"{exception_id}: recent_context_signatures must be array")

    state["seen_count"] += 1
    state["last_seen_at"] = answered_at
    state["last_mode"] = event["mode"]
    state["last_transfer_level"] = event.get("transfer_level")
    state["last_practice_item_id"] = event["practice_item_id"]
    state["updated_at"] = answered_at

    signature = event.get("context_signature")
    if isinstance(signature, str) and signature:
        signatures = [x for x in state["recent_context_signatures"] if x != signature]
        signatures.append(signature)
        state["recent_context_signatures"] = signatures[-12:]

    if event["is_correct"]:
        state["correct_count"] += 1
        state["consecutive_correct"] += 1
        state["last_correct_at"] = answered_at
        state["last_result"] = "correct"
        if state.get("status") == "new":
            state["status"] = "active"
        if event.get("transfer_level") in {"independent_context", "transfer"}:
            state["transfer_passed"] = True
            state["status"] = "stabilizing"
            if state.get("retention_stage") in {None, "new", "learning"}:
                state["retention_stage"] = "short_review"
        if event.get("source") == "retention" and event.get("transfer_level") in {
            "independent_context",
            "transfer",
        }:
            state["retention_passed"] = True
            state["status"] = "stabilizing"
            state["retention_stage"] = "delayed_review"
        # Do not decrement active_error_count or mark stabilized here: that belongs
        # to the separate mastery/retention policy.
    else:
        state["wrong_count"] += 1
        state["consecutive_correct"] = 0
        state["last_wrong_at"] = answered_at
        state["last_result"] = "wrong"
        state["active_error_count"] += 1
        state["status"] = "active"
        state["retention_stage"] = "learning"
        if event.get("transfer_level") in {"independent_context", "transfer"}:
            state["transfer_passed"] = False
        if event.get("source") == "retention":
            state["retention_passed"] = False

    if state.get("origin_ref") is None:
        state["origin_ref"] = event.get("practice_item_id")

    result["exceptions"][exception_id] = state
    result["processed_event_ids"].append(event_id)
    result["state_revision"] += 1
    result["updated_at"] = answered_at
    return result, True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, default=None)
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        profile = load_json(args.profile) if args.profile else None
        event = load_json(args.event)
        updated, applied = apply_event(profile, event)
    except StateError as exc:
        print(f"STATE ERROR: {exc}", file=sys.stderr)
        return 2

    payload = {"applied": applied, "profile": updated}
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
