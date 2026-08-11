#!/usr/bin/env python3
"""Deterministic reference resolver for Russian trainer explanations.

Reads a prebuilt Explanation Runtime plus a normalized result-adapter payload.
Never computes or changes the trainer answer/score. Intended for local fixtures
before any browser/Tilda implementation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ResolveError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ResolveError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ResolveError(f"Invalid JSON in {path}: {exc}") from exc


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def route_key(trainer_item_id: str, precision: str, key: str | None) -> str:
    return f"{trainer_item_id}::{precision}::{key or 'item'}"


def mode_allows_external(result: dict[str, Any]) -> tuple[bool, str]:
    mode = str(result.get("mode") or "practice")
    item_complete = result.get("item_is_complete") is True
    completion_complete = result.get("completion_complete") is True

    if not item_complete:
        return False, "item_not_complete"
    if mode in {"demo", "control"} and not completion_complete:
        return False, f"{mode}_not_complete"
    return True, "allowed"


def resolve(runtime: Any, result: Any) -> dict[str, Any]:
    if not isinstance(runtime, dict):
        raise ResolveError("Runtime must be object")
    if not isinstance(result, dict):
        raise ResolveError("Result payload must be object")

    units = runtime.get("units")
    routes = runtime.get("routes")
    defaults = runtime.get("task_defaults")
    if not isinstance(units, dict) or not isinstance(routes, dict) or not isinstance(defaults, dict):
        raise ResolveError("Runtime missing units/routes/task_defaults objects")

    trainer_item_id = result.get("trainer_item_id")
    task_number = result.get("task_number")
    if not isinstance(trainer_item_id, str) or not trainer_item_id:
        raise ResolveError("Result missing trainer_item_id")
    if not isinstance(task_number, int) or not 1 <= task_number <= 27:
        raise ResolveError("Result has invalid task_number")

    allowed, gate_reason = mode_allows_external(result)
    base_response = {
        "trainer_item_id": trainer_item_id,
        "task_number": task_number,
        "external_explanation_allowed": allowed,
        "gate_reason": gate_reason,
        "current_trainer_answer_authoritative": True,
        "current_trainer_score_authoritative": True,
        "current_feedback_preserved": True,
        "resolution": "none",
        "explanation_ids": [],
        "units": [],
    }
    if not allowed:
        return base_response

    resolved_ids: list[str] = []
    partial_ids: list[str] = []
    evidence = result.get("evidence", [])
    if evidence is None:
        evidence = []
    if not isinstance(evidence, list):
        raise ResolveError("result.evidence must be array")

    # Only incorrect evidence drives error-specific explanation.
    for ev in evidence:
        if not isinstance(ev, dict) or ev.get("is_correct") is not False:
            continue
        precision = ev.get("precision")
        key = ev.get("key")
        if not isinstance(precision, str):
            continue
        if key is not None and not isinstance(key, str):
            continue
        rid = route_key(trainer_item_id, precision, key)
        route = routes.get(rid)
        if not isinstance(route, dict):
            continue

        exact = route.get("exact_explanation_id")
        status = route.get("status")
        if status == "enabled" and isinstance(exact, str) and exact in units:
            resolved_ids.append(exact)
            continue

        candidates = route.get("candidate_explanation_ids", [])
        if status == "partial" and isinstance(candidates, list):
            for candidate in candidates:
                if isinstance(candidate, str) and candidate in units:
                    partial_ids.append(candidate)

    resolved_ids = unique(resolved_ids)
    partial_ids = unique(partial_ids)

    if resolved_ids:
        base_response["resolution"] = "exact"
        base_response["explanation_ids"] = resolved_ids
    elif partial_ids:
        base_response["resolution"] = "partial_safe"
        base_response["explanation_ids"] = partial_ids
    else:
        default = defaults.get(str(task_number))
        external_fallback = (
            default.get("external_fallback_explanation_id")
            if isinstance(default, dict)
            else None
        )
        candidates = default.get("candidate_explanation_ids", []) if isinstance(default, dict) else []
        if isinstance(external_fallback, str) and external_fallback in units:
            base_response["resolution"] = "task_fallback"
            base_response["explanation_ids"] = [external_fallback]
        elif result.get("item_is_correct") is False and isinstance(candidates, list):
            safe = [x for x in candidates if isinstance(x, str) and x in units]
            if safe:
                base_response["resolution"] = "task_candidates"
                base_response["explanation_ids"] = unique(safe)
        # If no safe external mapping, leave resolution=none and current feedback wins.

    base_response["units"] = [
        units[explanation_id]
        for explanation_id in base_response["explanation_ids"]
        if explanation_id in units
    ]
    return base_response


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--runtime",
        type=Path,
        default=root / "build" / "RUSSIAN-EXPLANATION-RUNTIME.json",
    )
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    try:
        response = resolve(load_json(args.runtime), load_json(args.result))
    except ResolveError as exc:
        print(f"RESOLVE ERROR: {exc}", file=sys.stderr)
        return 2

    text = json.dumps(response, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
