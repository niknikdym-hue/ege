#!/usr/bin/env python3
"""Build and validate Russian Exceptions Trainer practice cards.

Data-only build. It resolves practice cards against the source Exceptions Bank
manifest and never changes the current EGE trainer or Tilda production files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXCEPTIONS_MANIFEST = "83-RUSSIAN-EXCEPTIONS-MASTER-MANIFEST.json"
PRACTICE_MANIFEST = "93-RUSSIAN-EXCEPTIONS-PRACTICE-MANIFEST.json"
PRACTICE_SCHEMA = "91-RUSSIAN-EXCEPTIONS-PRACTICE-SCHEMA.json"


class BuildError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise BuildError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def get_manifest_paths(data: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get(field), list):
        raise BuildError(f"Expected {field}[]")
    rows = data[field]
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise BuildError(f"Invalid {field}[{index}]")
    return rows


def flatten_exceptions(root: Path, manifest: Any) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in get_manifest_paths(manifest, "source_banks"):
        rel = row["path"]
        data = load_json(root / rel)
        if not isinstance(data, dict):
            raise BuildError(f"Exception bank must be object: {rel}")

        items: list[dict[str, Any]] = []
        direct = data.get("items", [])
        if direct is not None:
            if not isinstance(direct, list):
                raise BuildError(f"items[] invalid: {rel}")
            items.extend(x for x in direct if isinstance(x, dict))

        clusters = data.get("clusters", [])
        if clusters is not None:
            if not isinstance(clusters, list):
                raise BuildError(f"clusters[] invalid: {rel}")
            for cluster in clusters:
                if not isinstance(cluster, dict):
                    raise BuildError(f"cluster invalid: {rel}")
                cluster_items = cluster.get("items", [])
                if not isinstance(cluster_items, list):
                    raise BuildError(f"cluster items[] invalid: {rel}")
                for original in cluster_items:
                    if not isinstance(original, dict):
                        raise BuildError(f"cluster item invalid: {rel}")
                    item = json.loads(json.dumps(original, ensure_ascii=False))
                    item.setdefault("skill_ids", cluster.get("skill_ids", []))
                    item.setdefault("subskill_ids", cluster.get("subskill_ids", []))
                    item.setdefault("exam_task_numbers", cluster.get("exam_task_numbers", []))
                    items.append(item)

        for item in items:
            exception_id = item.get("exception_id")
            if not isinstance(exception_id, str) or not exception_id:
                raise BuildError(f"Exception item without exception_id: {rel}")
            if exception_id in by_id:
                raise BuildError(f"Duplicate exception_id across source banks: {exception_id}")
            item = json.loads(json.dumps(item, ensure_ascii=False))
            item["source_bank"] = rel
            by_id[exception_id] = item
    return by_id


def load_practice_items(
    root: Path, manifest: Any
) -> tuple[list[dict[str, Any]], list[str], int]:
    if not isinstance(manifest, dict):
        raise BuildError(f"{PRACTICE_MANIFEST} must be an object")

    items: list[dict[str, Any]] = []
    source_files: list[str] = []
    expected_sum = 0

    for row in get_manifest_paths(manifest, "practice_banks"):
        rel = row["path"]
        data = load_json(root / rel)
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise BuildError(f"Expected items[] in practice bank {rel}")
        bank_items = data["items"]
        if not all(isinstance(x, dict) for x in bank_items):
            raise BuildError(f"Non-object practice item in {rel}")

        expected = row.get("expected_items")
        if not isinstance(expected, int) or expected < 0:
            raise BuildError(f"{rel}: expected_items must be a non-negative integer")
        if expected != len(bank_items):
            raise BuildError(
                f"{rel}: expected_items={expected}, actual={len(bank_items)}"
            )
        expected_sum += expected

        for original in bank_items:
            item = json.loads(json.dumps(original, ensure_ascii=False))
            item["source_practice_bank"] = rel
            items.append(item)
        source_files.append(rel)

    manifest_total = manifest.get("expected_total_items")
    if not isinstance(manifest_total, int) or manifest_total < 0:
        raise BuildError(
            f"{PRACTICE_MANIFEST}: expected_total_items must be a non-negative integer"
        )
    if manifest_total != expected_sum:
        raise BuildError(
            f"{PRACTICE_MANIFEST}: expected_total_items={manifest_total}, "
            f"sum(expected_items)={expected_sum}"
        )
    if manifest_total != len(items):
        raise BuildError(
            f"{PRACTICE_MANIFEST}: expected_total_items={manifest_total}, "
            f"actual practice items={len(items)}"
        )

    return items, source_files, manifest_total


def nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def validate(
    items: list[dict[str, Any]],
    exceptions: dict[str, dict[str, Any]],
    schema: Any,
) -> tuple[list[str], list[str]]:
    if not isinstance(schema, dict):
        raise BuildError("Practice schema must be an object")
    contract = schema.get("practice_item_contract", {})
    required = contract.get("required")
    if not isinstance(required, list):
        raise BuildError("Practice schema missing required[]")

    allowed_modes = set(schema.get("practice_mode_enum", []))
    allowed_response = set(schema.get("response_kind_enum", []))
    allowed_transfer = set(schema.get("transfer_level_enum", []))

    errors: list[str] = []
    warnings: list[str] = []
    practice_ids: set[str] = set()
    context_keys: set[tuple[str, str, str]] = set()

    for item in items:
        pid = item.get("practice_item_id")
        label = pid if isinstance(pid, str) and pid else "<missing practice_item_id>"

        missing = [field for field in required if field not in item]
        if missing:
            errors.append(f"{label}: missing fields {', '.join(missing)}")
            continue

        if not isinstance(pid, str) or not pid:
            errors.append("practice item without valid practice_item_id")
        elif pid in practice_ids:
            errors.append(f"duplicate practice_item_id: {pid}")
        else:
            practice_ids.add(pid)

        exception_id = item.get("exception_id")
        source_exception = exceptions.get(exception_id) if isinstance(exception_id, str) else None
        if source_exception is None:
            errors.append(f"{label}: unknown exception_id {exception_id!r}")
            continue

        source_status = source_exception.get("status")
        if source_status not in {"source_verified", "reviewed"}:
            errors.append(
                f"{label}: source exception {exception_id} status {source_status!r} is not eligible"
            )

        mode = item.get("mode")
        if mode not in allowed_modes:
            errors.append(f"{label}: unsupported mode {mode!r}")
        source_modes = source_exception.get("practice_modes", [])
        if isinstance(source_modes, list) and mode not in source_modes:
            errors.append(
                f"{label}: mode {mode!r} not permitted by source exception {exception_id}"
            )

        response_kind = item.get("response_kind")
        if response_kind not in allowed_response:
            errors.append(f"{label}: unsupported response_kind {response_kind!r}")

        transfer_level = item.get("transfer_level")
        if transfer_level is not None and transfer_level not in allowed_transfer:
            errors.append(f"{label}: unsupported transfer_level {transfer_level!r}")

        if not nonempty(item.get("prompt")):
            errors.append(f"{label}: empty prompt")
        if not nonempty(item.get("answer")):
            errors.append(f"{label}: empty answer")

        feedback = item.get("feedback")
        if not isinstance(feedback, dict):
            errors.append(f"{label}: feedback must be object")
        else:
            for field in ("correct_answer", "why"):
                if not nonempty(feedback.get(field)):
                    errors.append(f"{label}: feedback.{field} is required")

        signature = item.get("context_signature")
        if not isinstance(signature, str) or not signature:
            warnings.append(f"{label}: missing context_signature")
        else:
            key = (str(exception_id), str(mode), signature)
            if key in context_keys:
                errors.append(
                    f"{label}: duplicate context_signature for exception/mode: {key}"
                )
            context_keys.add(key)

        if item.get("status") not in {"source_verified", "reviewed", "draft", "needs_review"}:
            errors.append(f"{label}: invalid status {item.get('status')!r}")

    return errors, warnings


def write_audit(
    path: Path,
    *,
    item_count: int,
    expected_total: int,
    source_files: list[str],
    exceptions_count: int,
    errors: list[str],
    warnings: list[str],
) -> None:
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN EXCEPTIONS PRACTICE VALIDATION",
        "",
        f"STATUS: {'PASS' if not errors else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"PRACTICE_ITEMS: {item_count}",
        f"EXPECTED_TOTAL_ITEMS: {expected_total}",
        f"PRACTICE_BANKS: {len(source_files)}",
        f"SOURCE_EXCEPTION_IDS: {exceptions_count}",
        f"ERRORS: {len(errors)}",
        f"WARNINGS: {len(warnings)}",
        "",
        "PRACTICE BANKS",
    ]
    lines.extend(f"- {rel}" for rel in source_files)
    lines.extend(["", "ERRORS"])
    lines.extend(["- none"] if not errors else [f"- {x}" for x in errors])
    lines.extend(["", "WARNINGS"])
    lines.extend(["- none"] if not warnings else [f"- {x}" for x in warnings])
    lines.extend(
        [
            "",
            "SAFETY",
            "- Practice validation is data-only.",
            "- Current EGE trainer/T123/answers/scoring/localStorage are unchanged.",
            "- PASS does not authorize production integration.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build(root: Path, output: Path, audit: Path) -> int:
    root = root.resolve()
    exception_manifest = load_json(root / EXCEPTIONS_MANIFEST)
    practice_manifest = load_json(root / PRACTICE_MANIFEST)
    practice_schema = load_json(root / PRACTICE_SCHEMA)

    exceptions = flatten_exceptions(root, exception_manifest)
    items, source_files, expected_total = load_practice_items(root, practice_manifest)
    errors, warnings = validate(items, exceptions, practice_schema)

    items.sort(key=lambda row: row.get("practice_item_id", ""))
    payload = {
        "schema_version":"1.0.1",
        "subject":"russian",
        "exam":"ege",
        "purpose":"canonical_exceptions_practice_bank",
        "build_version":"0.1.1",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "generated_from":source_files,
        "items":items,
        "validation":{
            "practice_items":len(items),
            "expected_total_items":expected_total,
            "manifest_total_valid":len(items) == expected_total,
            "source_exception_ids":len(exceptions),
            "errors":errors,
            "warnings":warnings,
        },
        "integration_status":"not_connected_to_production",
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    write_audit(
        audit,
        item_count=len(items),
        expected_total=expected_total,
        source_files=source_files,
        exceptions_count=len(exceptions),
        errors=errors,
        warnings=warnings,
    )

    if errors:
        print(f"FAIL: {len(errors)} error(s); see {audit}")
        return 1
    print(f"PASS: {len(items)} practice cards; {len(warnings)} warning(s).")
    print(f"Canonical practice bank: {output}")
    print(f"Audit: {audit}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--audit", type=Path, default=None)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "build" / "RUSSIAN-EXCEPTIONS-PRACTICE-CANONICAL.json"
    audit = args.audit or root / "audits" / "RUSSIAN-EXCEPTIONS-PRACTICE-VALIDATION.txt"
    try:
        return build(root, output, audit)
    except BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
