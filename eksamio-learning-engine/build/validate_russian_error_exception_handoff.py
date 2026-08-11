#!/usr/bin/env python3
"""Validate exact error -> exception handoff mappings against source routing tags.

Data-only validator. It does not modify the trainer or learner state.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HANDOFF_FILE = "114-RUSSIAN-ERROR-EXCEPTION-HANDOFF-MAP-v0.1.json"
ROUTING_INDEX = "75-RUSSIAN-EXPLANATION-ROUTING-TAG-INDEX.json"
EXCEPTIONS_MANIFEST = "83-RUSSIAN-EXCEPTIONS-MASTER-MANIFEST.json"

TAG_ARRAY_TO_TYPE = {
    "word_tags": "word",
    "position_tags": "position",
    "option_tags": "option",
    "match_tags": "match_position",
}


class ValidationError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def routing_files(index: Any) -> list[str]:
    if not isinstance(index, dict) or not isinstance(index.get("files"), list):
        raise ValidationError(f"{ROUTING_INDEX}: files[] missing")
    result: list[str] = []
    for row in index["files"]:
        if isinstance(row, dict) and isinstance(row.get("path"), str):
            result.append(row["path"])
    if not result:
        raise ValidationError("No routing tag files found")
    return result


def collect_exact_evidence(root: Path, paths: list[str]) -> tuple[set[tuple[str, str, str]], set[str]]:
    evidence: set[tuple[str, str, str]] = set()
    trainer_items: set[str] = set()

    for rel in paths:
        data = load_json(root / rel)
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            trainer_item_id = item.get("trainer_item_id")
            if not isinstance(trainer_item_id, str) or not trainer_item_id:
                continue
            trainer_items.add(trainer_item_id)

            for field, evidence_type in TAG_ARRAY_TO_TYPE.items():
                tags = item.get(field)
                if not isinstance(tags, list):
                    continue
                for tag in tags:
                    if not isinstance(tag, dict):
                        continue
                    key = tag.get("position_id")
                    confidence = tag.get("diagnostic_confidence")
                    if isinstance(key, str) and key and confidence == "exact":
                        evidence.add((trainer_item_id, evidence_type, key))

            # Item-level exact mapping support if future map uses evidence_key `item`.
            if item.get("exact_subskill_id") and item.get("routing_precision") == "item":
                evidence.add((trainer_item_id, "item", "item"))

    return evidence, trainer_items


def flatten_exception_ids(root: Path, manifest: Any) -> dict[str, str]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("source_banks"), list):
        raise ValidationError(f"{EXCEPTIONS_MANIFEST}: source_banks[] missing")

    result: dict[str, str] = {}
    for row in manifest["source_banks"]:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            continue
        rel = row["path"]
        data = load_json(root / rel)
        if not isinstance(data, dict):
            continue

        rows: list[dict[str, Any]] = []
        direct = data.get("items", [])
        if isinstance(direct, list):
            rows.extend(x for x in direct if isinstance(x, dict))
        clusters = data.get("clusters", [])
        if isinstance(clusters, list):
            for cluster in clusters:
                if not isinstance(cluster, dict):
                    continue
                nested = cluster.get("items", [])
                if isinstance(nested, list):
                    rows.extend(x for x in nested if isinstance(x, dict))

        for item in rows:
            exception_id = item.get("exception_id")
            status = item.get("status")
            if not isinstance(exception_id, str) or not exception_id:
                continue
            if exception_id in result:
                raise ValidationError(f"Duplicate exception_id across source banks: {exception_id}")
            result[exception_id] = str(status or "")
    return result


def validate(root: Path) -> tuple[list[str], list[str], dict[str, int]]:
    handoff = load_json(root / HANDOFF_FILE)
    index = load_json(root / ROUTING_INDEX)
    exceptions_manifest = load_json(root / EXCEPTIONS_MANIFEST)

    exact_evidence, trainer_items = collect_exact_evidence(root, routing_files(index))
    exception_status = flatten_exception_ids(root, exceptions_manifest)

    mappings = handoff.get("mappings") if isinstance(handoff, dict) else None
    if not isinstance(mappings, list):
        raise ValidationError(f"{HANDOFF_FILE}: mappings[] missing")

    errors: list[str] = []
    warnings: list[str] = []
    mapping_ids: set[str] = set()
    enabled = 0

    for mapping in mappings:
        if not isinstance(mapping, dict):
            errors.append("non-object mapping row")
            continue

        mapping_id = mapping.get("mapping_id")
        if not isinstance(mapping_id, str) or not mapping_id:
            errors.append("mapping without mapping_id")
            continue
        if mapping_id in mapping_ids:
            errors.append(f"duplicate mapping_id: {mapping_id}")
        mapping_ids.add(mapping_id)

        trainer_item_id = mapping.get("trainer_item_id")
        evidence_type = mapping.get("evidence_type")
        evidence_key = mapping.get("evidence_key")
        exception_id = mapping.get("exception_id")
        precision = mapping.get("evidence_precision")
        activation = mapping.get("activation_allowed") is True

        if trainer_item_id not in trainer_items:
            errors.append(f"{mapping_id}: unknown/unindexed trainer_item_id {trainer_item_id!r}")

        evidence_tuple = (str(trainer_item_id), str(evidence_type), str(evidence_key))
        if evidence_tuple not in exact_evidence:
            errors.append(
                f"{mapping_id}: exact routing evidence not found: {evidence_tuple}"
            )

        status = exception_status.get(str(exception_id))
        if status is None:
            errors.append(f"{mapping_id}: unknown exception_id {exception_id!r}")
        elif status not in {"source_verified", "reviewed"}:
            errors.append(
                f"{mapping_id}: exception {exception_id} has ineligible status {status!r}"
            )

        if activation:
            enabled += 1
            if precision != "exact":
                errors.append(
                    f"{mapping_id}: activation_allowed requires evidence_precision='exact'"
                )
            if mapping.get("status") not in {"source_verified", "reviewed"}:
                errors.append(
                    f"{mapping_id}: activation_allowed mapping has status {mapping.get('status')!r}"
                )

        if not mapping.get("source_locator"):
            warnings.append(f"{mapping_id}: source_locator missing")

    stats = {
        "mappings_total": len(mappings),
        "activation_allowed": enabled,
        "routing_exact_evidence_keys": len(exact_evidence),
        "exception_ids": len(exception_status),
    }
    return errors, warnings, stats


def write_report(path: Path, errors: list[str], warnings: list[str], stats: dict[str, int]) -> None:
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN ERROR -> EXCEPTION HANDOFF VALIDATION",
        "",
        f"STATUS: {'PASS' if not errors else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
    ]
    for key, value in stats.items():
        lines.append(f"{key.upper()}: {value}")
    lines.extend(["", "ERRORS"])
    lines.extend(["- none"] if not errors else [f"- {x}" for x in errors])
    lines.extend(["", "WARNINGS"])
    lines.extend(["- none"] if not warnings else [f"- {x}" for x in warnings])
    lines.extend(
        [
            "",
            "SAFETY",
            "- PASS validates data links only; it does not enable production handoff.",
            "- Current EGE trainer remains unchanged.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
    )
    args = parser.parse_args()

    root = args.root.resolve()
    report = args.report or root / "audits" / "RUSSIAN-ERROR-EXCEPTION-HANDOFF-VALIDATION.txt"
    try:
        errors, warnings, stats = validate(root)
    except ValidationError as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2

    write_report(report, errors, warnings, stats)
    if errors:
        print(f"FAIL: {len(errors)} handoff error(s); report={report}")
        return 1
    print(f"PASS: {stats['mappings_total']} mappings; {len(warnings)} warning(s).")
    print(f"Report: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
