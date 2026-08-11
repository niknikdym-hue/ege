#!/usr/bin/env python3
"""Build minimal runtime payload for future Russian EGE trainer explanations.

Consumes canonical Explanation Bank plus reviewed external routing tags. It does
not modify current trainer cards, answers, scoring or storage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTING_INDEX = "75-RUSSIAN-EXPLANATION-ROUTING-TAG-INDEX.json"
TASK_ROUTING_MAP = "59-RUSSIAN-EXPLANATION-TASK-ROUTING-MAP.json"

TAG_FIELDS = {
    "word_tags": "word",
    "option_tags": "option",
    "position_tags": "position",
    "match_tags": "match_position",
}

UNIT_ALLOWED_FIELDS = (
    "explanation_id",
    "title",
    "short_rule",
    "rule",
    "algorithm",
    "common_traps",
    "examples",
    "contrast_examples",
    "learner_table",
    "semantic_link_table",
    "verification_question",
    "official_scope_note",
)


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


def canonical_units(data: Any) -> dict[str, dict[str, Any]]:
    units = data.get("units") if isinstance(data, dict) else None
    if not isinstance(units, list):
        raise BuildError("Canonical Explanation Bank must contain units[]")
    result: dict[str, dict[str, Any]] = {}
    for row in units:
        if not isinstance(row, dict):
            raise BuildError("Non-object explanation unit")
        explanation_id = row.get("explanation_id")
        if not isinstance(explanation_id, str) or not explanation_id:
            raise BuildError("Explanation unit without explanation_id")
        if explanation_id in result:
            raise BuildError(f"Duplicate explanation_id: {explanation_id}")
        if row.get("status") not in {"source_verified", "content_reviewed", "reviewed"}:
            # Canonical source may contain review-pending units; do not enable in runtime.
            continue
        compact = {
            key: row[key]
            for key in UNIT_ALLOWED_FIELDS
            if key in row
        }
        for required in ("short_rule", "rule", "algorithm", "common_traps", "examples"):
            if required not in compact:
                raise BuildError(f"{explanation_id}: runtime-required field missing: {required}")
        result[explanation_id] = compact
    return result


def routing_paths(index: Any) -> list[str]:
    rows = index.get("files") if isinstance(index, dict) else None
    if not isinstance(rows, list):
        raise BuildError(f"{ROUTING_INDEX}: files[] missing")
    paths: list[str] = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise BuildError(f"{ROUTING_INDEX}: invalid file row")
        paths.append(row["path"])
    return paths


def add_route(
    routes: dict[str, dict[str, Any]],
    *,
    trainer_item_id: str,
    task_number: int,
    precision: str,
    key: str | None,
    explanation_id: str | None,
    confidence: str | None,
    legacy: bool,
    units: dict[str, dict[str, Any]],
) -> None:
    if not explanation_id:
        return
    if explanation_id not in units:
        raise BuildError(
            f"routing {trainer_item_id}/{precision}/{key}: missing runtime explanation_id {explanation_id}"
        )
    suffix = key or "item"
    route_id = f"{trainer_item_id}::{precision}::{suffix}"
    if route_id in routes:
        raise BuildError(f"Duplicate runtime route_id: {route_id}")
    routes[route_id] = {
        "route_id": route_id,
        "trainer_item_id": trainer_item_id,
        "task_number": task_number,
        "precision": precision,
        "position_id": key if precision in {"position", "match_position"} else None,
        "option_id": key if precision == "option" else None,
        "word_id": key if precision == "word" else None,
        "candidate_explanation_ids": [explanation_id],
        "exact_explanation_id": explanation_id if confidence == "exact" else None,
        "fallback": "current_trainer_feedback",
        "legacy": bool(legacy),
        "status": "enabled" if confidence == "exact" else "partial",
    }


def collect_routes(
    root: Path,
    index: Any,
    units: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    routes: dict[str, dict[str, Any]] = {}
    for rel in routing_paths(index):
        data = load_json(root / rel)
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            trainer_item_id = item.get("trainer_item_id")
            task_number = item.get("task_number")
            if not isinstance(trainer_item_id, str) or not trainer_item_id:
                continue
            if not isinstance(task_number, int) or not 1 <= task_number <= 27:
                raise BuildError(f"{trainer_item_id}: invalid task_number {task_number!r}")
            legacy = item.get("legacy") is True

            # Exact item-level routes.
            if item.get("routing_precision") == "item" and isinstance(item.get("explanation_id"), str):
                add_route(
                    routes,
                    trainer_item_id=trainer_item_id,
                    task_number=task_number,
                    precision="item",
                    key=None,
                    explanation_id=item.get("explanation_id"),
                    confidence="exact" if item.get("exact_subskill_id") else "partial",
                    legacy=legacy,
                    units=units,
                )

            for field, precision in TAG_FIELDS.items():
                tags = item.get(field)
                if not isinstance(tags, list):
                    continue
                for tag in tags:
                    if not isinstance(tag, dict):
                        continue
                    key = tag.get("position_id")
                    if not isinstance(key, str) or not key:
                        continue
                    explanation_id = tag.get("explanation_id")
                    confidence = tag.get("diagnostic_confidence")
                    if isinstance(explanation_id, str):
                        add_route(
                            routes,
                            trainer_item_id=trainer_item_id,
                            task_number=task_number,
                            precision=precision,
                            key=key,
                            explanation_id=explanation_id,
                            confidence=str(confidence or "partial"),
                            legacy=legacy,
                            units=units,
                        )
    return routes


def task_defaults(data: Any, units: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    rows = data.get("tasks") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise BuildError(f"{TASK_ROUTING_MAP}: tasks[] missing")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        task = row.get("task")
        if not isinstance(task, int) or not 1 <= task <= 27:
            raise BuildError(f"Invalid task default row: {task!r}")
        candidates = [
            x for x in row.get("candidate_explanation_ids", [])
            if isinstance(x, str) and x in units
        ]
        fallback = row.get("fallback")
        external_fallback = fallback if isinstance(fallback, str) and fallback in units else None
        if external_fallback and external_fallback not in candidates:
            candidates.append(external_fallback)
        result[str(task)] = {
            "task_number": task,
            "precision": row.get("precision"),
            "candidate_explanation_ids": candidates,
            "external_fallback_explanation_id": external_fallback,
            "fallback": "current_trainer_feedback" if external_fallback is None else "external_then_current",
            "automatic_official_scoring": row.get("automatic_official_scoring"),
        }
    if set(result) != {str(i) for i in range(1, 28)}:
        missing = sorted({str(i) for i in range(1, 28)} - set(result))
        raise BuildError(f"Task defaults missing tasks: {missing}")
    return result


def stable_content_version(units: dict[str, Any], routes: dict[str, Any], defaults: dict[str, Any]) -> str:
    raw = json.dumps(
        {"units":units,"routes":routes,"task_defaults":defaults},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256-" + hashlib.sha256(raw).hexdigest()[:20]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--explanations",
        type=Path,
        default=root / "build" / "RUSSIAN-EXPLANATION-BANK-CANONICAL.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "build" / "RUSSIAN-EXPLANATION-RUNTIME.json",
    )
    args = parser.parse_args()

    try:
        units = canonical_units(load_json(args.explanations))
        index = load_json(root / ROUTING_INDEX)
        routes = collect_routes(root, index, units)
        defaults = task_defaults(load_json(root / TASK_ROUTING_MAP), units)
        version = stable_content_version(units, routes, defaults)
        payload = {
            "schema_version":"1.0.0",
            "subject":"russian",
            "exam":"ege",
            "content_version":version,
            "generated_at_utc":datetime.now(timezone.utc).isoformat(),
            "units":units,
            "routes":routes,
            "task_defaults":defaults,
            "build_meta":{
                "units_enabled":len(units),
                "exact_or_partial_routes":len(routes),
                "task_defaults":len(defaults),
                "production_integration":"not_connected",
                "current_trainer_answers_or_scoring_modified":False,
            },
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(f"PASS: units={len(units)}, routes={len(routes)}, tasks={len(defaults)}, version={version}")
        print(f"Output: {args.output}")
        return 0
    except BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
