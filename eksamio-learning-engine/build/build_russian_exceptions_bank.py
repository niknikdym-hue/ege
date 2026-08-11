#!/usr/bin/env python3
"""Build and validate the canonical Russian exceptions/special-cases bank.

Data-only build. This script MUST NOT modify the current trainer, answers,
scoring, storage, URLs, or Tilda production files.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SOURCE_BANKS = [
    "33-RUSSIAN-EXCEPTIONS-BANK-v0.1.json",
    "35-RUSSIAN-EXCEPTIONS-ROOTS-PREFIXES-v0.1.json",
    "37-RUSSIAN-EXCEPTIONS-SUFFIXES-CONJUGATION-v0.1.json",
    "39-RUSSIAN-EXCEPTIONS-NE-NI-SOLID-v0.1.json",
    "42-RUSSIAN-PUNCTUATION-CONTRAST-BANK-v0.1.json",
    "48-RUSSIAN-EXCEPTIONS-WAVE2-NORMS-v0.1.json",
    "84-RUSSIAN-EXCEPTIONS-INTRODUCTORY-WORDS-v0.1.json",
]

SKILL_GRAPH_FILE = "03-RUSSIAN-SKILL-GRAPH.json"
SCHEMA_FILE = "29-RUSSIAN-EXCEPTIONS-BANK-SCHEMA.json"
MANIFEST_FILE = "83-RUSSIAN-EXCEPTIONS-MASTER-MANIFEST.json"

EXPLANATION_SOURCE_FILES = [
    "32-RUSSIAN-EXPLANATION-BANK-v0.1.json",
    "34-RUSSIAN-EXPLANATION-ORTHOGRAPHY-9-10-v0.1.json",
    "36-RUSSIAN-EXPLANATION-ORTHOGRAPHY-11-12-v0.1.json",
    "38-RUSSIAN-EXPLANATION-ORTHOGRAPHY-13-14-v0.1.json",
    "40-RUSSIAN-EXPLANATION-PUNCTUATION-16-18-v0.1.json",
    "41-RUSSIAN-EXPLANATION-PUNCTUATION-19-21-v0.1.json",
    "45-RUSSIAN-EXPLANATION-WAVE2-TEXT-LEXICAL-1-3-v0.1.json",
    "46-RUSSIAN-EXPLANATION-WAVE2-NORMS-4-8-v0.1.json",
    "47-RUSSIAN-EXPLANATION-WAVE2-TEXT-22-26-v0.1.json",
    "55-RUSSIAN-ESSAY-27-EXPLANATION-COMPONENTS-v0.1.json",
    "61-RUSSIAN-EXPLANATION-TASK11-SUFFIX-SPLITS-v0.1.json",
    "62-RUSSIAN-EXPLANATION-TASK14-WRITING-SPLITS-v0.1.json",
    "67-RUSSIAN-EXPLANATION-TASK21-RULE-SPLITS-v0.1.json",
    "72-RUSSIAN-EXPLANATION-TASK14-HYPHEN-ADVERB-SPLITS-v0.1.json",
    "80-RUSSIAN-EXPLANATION-TASK14-POL-SPLIT-v0.1.json",
]

CANONICAL_SOURCE_TYPES = {
    "official_fipi",
    "book",
    "existing_trainer",
    "internal_verified_source",
}


class BuildError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise BuildError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BuildError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def walk(obj: Any) -> Iterable[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def collect_graph_ids(graph: Any) -> tuple[set[str], set[str]]:
    all_ids: set[str] = set()
    child_ids: set[str] = set()
    for node in walk(graph):
        if not isinstance(node, dict):
            continue
        value = node.get("skill_id")
        if isinstance(value, str) and value:
            all_ids.add(value)
            if node.get("parent_skill_id") is not None:
                child_ids.add(value)
    if not all_ids:
        raise BuildError("No skill_id values found in Skill Graph")
    return all_ids, child_ids


def flatten_bank(data: Any, source_name: str) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        raise BuildError(f"Top-level JSON must be object: {source_name}")

    result: list[dict[str, Any]] = []

    top_items = data.get("items", [])
    if top_items is not None:
        if not isinstance(top_items, list):
            raise BuildError(f"items must be array: {source_name}")
        for item in top_items:
            if not isinstance(item, dict):
                raise BuildError(f"Non-object item in {source_name}")
            copy = json.loads(json.dumps(item, ensure_ascii=False))
            copy.setdefault("source_bank", source_name)
            result.append(copy)

    clusters = data.get("clusters", [])
    if clusters is not None:
        if not isinstance(clusters, list):
            raise BuildError(f"clusters must be array: {source_name}")
        for cluster in clusters:
            if not isinstance(cluster, dict):
                raise BuildError(f"Non-object cluster in {source_name}")
            cluster_id = cluster.get("cluster_id")
            cluster_items = cluster.get("items", [])
            if not isinstance(cluster_items, list):
                raise BuildError(f"cluster items must be array: {source_name}/{cluster_id}")
            for item in cluster_items:
                if not isinstance(item, dict):
                    raise BuildError(f"Non-object item in {source_name}/{cluster_id}")
                copy = json.loads(json.dumps(item, ensure_ascii=False))
                copy.setdefault("skill_ids", cluster.get("skill_ids", []))
                copy.setdefault("subskill_ids", cluster.get("subskill_ids", []))
                copy.setdefault("exam_task_numbers", cluster.get("exam_task_numbers", []))
                copy.setdefault("cluster_id", cluster_id)
                copy.setdefault("source_bank", source_name)
                result.append(copy)

    if not result:
        raise BuildError(f"No items found in {source_name}")
    return result


def collect_explanation_ids(root: Path) -> set[str]:
    ids: set[str] = set()
    for rel in EXPLANATION_SOURCE_FILES:
        data = load_json(root / rel)
        units = data.get("units") if isinstance(data, dict) else None
        if not isinstance(units, list):
            raise BuildError(f"Expected units[] in explanation source {rel}")
        for unit in units:
            if isinstance(unit, dict) and isinstance(unit.get("explanation_id"), str):
                ids.add(unit["explanation_id"])
    return ids


def validate_items(
    items: list[dict[str, Any]],
    *,
    required_fields: list[str],
    practice_modes: set[str],
    graph_ids: set[str],
    graph_child_ids: set[str],
    explanation_ids: set[str],
) -> tuple[list[str], list[str], dict[int, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    coverage = {task: 0 for task in range(1, 28)}

    seen: set[str] = set()
    for item in items:
        exception_id = item.get("exception_id")
        if not isinstance(exception_id, str) or not exception_id:
            errors.append(f"{item.get('source_bank')}: item without exception_id")
            continue
        if exception_id in seen:
            errors.append(f"duplicate exception_id: {exception_id}")
        seen.add(exception_id)

        missing = [field for field in required_fields if field not in item]
        if missing:
            errors.append(f"{exception_id}: missing fields {', '.join(missing)}")
            continue

        skill_ids = item.get("skill_ids")
        if not isinstance(skill_ids, list) or not skill_ids:
            errors.append(f"{exception_id}: invalid/empty skill_ids")
        else:
            for skill_id in skill_ids:
                if skill_id not in graph_ids:
                    errors.append(f"{exception_id}: unknown skill_id {skill_id}")

        subskill_ids = item.get("subskill_ids")
        if not isinstance(subskill_ids, list) or not subskill_ids:
            errors.append(f"{exception_id}: invalid/empty subskill_ids")
        else:
            for subskill_id in subskill_ids:
                if subskill_id not in graph_ids:
                    errors.append(f"{exception_id}: unknown subskill_id {subskill_id}")
                elif graph_child_ids and subskill_id not in graph_child_ids:
                    warnings.append(
                        f"{exception_id}: {subskill_id} exists but is not marked as child Skill Graph node"
                    )

        task_numbers = item.get("exam_task_numbers", [])
        if not isinstance(task_numbers, list):
            errors.append(f"{exception_id}: exam_task_numbers must be array")
        else:
            for task in task_numbers:
                if not isinstance(task, int) or not 1 <= task <= 27:
                    errors.append(f"{exception_id}: invalid task number {task!r}")
                else:
                    coverage[task] += 1

        modes = item.get("practice_modes")
        if not isinstance(modes, list) or not modes:
            errors.append(f"{exception_id}: practice_modes must be non-empty array")
        else:
            for mode in modes:
                if mode not in practice_modes:
                    errors.append(f"{exception_id}: unsupported practice mode {mode!r}")

        refs = item.get("source_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{exception_id}: source_refs must be non-empty array")
        else:
            for idx, ref in enumerate(refs):
                if not isinstance(ref, dict):
                    errors.append(f"{exception_id}: source_refs[{idx}] is not object")
                    continue
                source_type = ref.get("source_type")
                if source_type not in CANONICAL_SOURCE_TYPES:
                    errors.append(
                        f"{exception_id}: noncanonical source_type {source_type!r}"
                    )
                source_path = ref.get("source_path")
                if not isinstance(source_path, str) or not source_path.strip():
                    errors.append(f"{exception_id}: source_refs[{idx}] missing source_path")
                elif source_path.strip().lower() in {"verified corpus", "verified source"}:
                    warnings.append(f"{exception_id}: vague source_path {source_path!r}")
                if ref.get("verification_status") not in {"verified", "partial", "needs_review"}:
                    errors.append(
                        f"{exception_id}: source_refs[{idx}] invalid verification_status"
                    )

        rule_ref = item.get("rule_ref")
        if isinstance(rule_ref, str) and rule_ref and rule_ref not in explanation_ids:
            # Schema explicitly permits a stable rule identifier, so this is a warning.
            warnings.append(
                f"{exception_id}: rule_ref {rule_ref!r} is not a current explanation_id; treat as stable rule id or review link"
            )

    return errors, warnings, coverage


def write_audit(
    path: Path,
    *,
    total: int,
    errors: list[str],
    warnings: list[str],
    coverage: dict[int, int],
) -> None:
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN EXCEPTIONS / SPECIAL CASES CANONICAL VALIDATION",
        "",
        f"STATUS: {'PASS' if not errors else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"ITEMS_TOTAL: {total}",
        f"SOURCE_BANKS: {len(SOURCE_BANKS)}",
        f"ERRORS: {len(errors)}",
        f"WARNINGS: {len(warnings)}",
        "",
        "TASK COVERAGE (NUMBER OF EXCEPTION/SPECIAL-CASE ITEMS; ZERO IS ALLOWED)",
    ]
    for task in range(1, 28):
        lines.append(f"- {task}: {coverage[task]}")
    lines.extend(["", "ERRORS"])
    lines.extend(["- none"] if not errors else [f"- {x}" for x in errors])
    lines.extend(["", "WARNINGS"])
    lines.extend(["- none"] if not warnings else [f"- {x}" for x in warnings])
    lines.extend(
        [
            "",
            "NOTE",
            "- Zero exception coverage for a task is not a build failure: not every task has an exception-type learning need.",
            "- Full orthoepic source bank is intentionally not duplicated here.",
            "- Current trainer is not modified by this build.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build(root: Path, output: Path, audit: Path) -> int:
    root = root.resolve()
    schema = load_json(root / SCHEMA_FILE)
    manifest = load_json(root / MANIFEST_FILE)
    graph = load_json(root / SKILL_GRAPH_FILE)

    contract = schema.get("exception_contract") if isinstance(schema, dict) else None
    if not isinstance(contract, dict) or not isinstance(contract.get("required"), list):
        raise BuildError(f"Invalid exception contract in {SCHEMA_FILE}")
    required_fields = [x for x in contract["required"] if isinstance(x, str)]

    practice_enum = schema.get("practice_mode_enum")
    if not isinstance(practice_enum, list):
        raise BuildError(f"Missing practice_mode_enum in {SCHEMA_FILE}")
    practice_modes = {x for x in practice_enum if isinstance(x, str)}

    graph_ids, graph_child_ids = collect_graph_ids(graph)
    explanation_ids = collect_explanation_ids(root)

    source_rows = manifest.get("source_banks") if isinstance(manifest, dict) else None
    if not isinstance(source_rows, list):
        raise BuildError(f"Missing source_banks[] in {MANIFEST_FILE}")
    manifest_paths = [row.get("path") for row in source_rows if isinstance(row, dict)]
    if manifest_paths != SOURCE_BANKS:
        raise BuildError(
            "Builder SOURCE_BANKS and master manifest source_banks are out of sync"
        )

    items: list[dict[str, Any]] = []
    for rel in SOURCE_BANKS:
        items.extend(flatten_bank(load_json(root / rel), rel))

    errors, warnings, coverage = validate_items(
        items,
        required_fields=required_fields,
        practice_modes=practice_modes,
        graph_ids=graph_ids,
        graph_child_ids=graph_child_ids,
        explanation_ids=explanation_ids,
    )

    items.sort(key=lambda row: row.get("exception_id", ""))
    payload = {
        "schema_version":"1.0.0",
        "subject":"russian",
        "exam":"ege",
        "purpose":"canonical_exceptions_and_special_cases_bank",
        "build_version":"0.1.0",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "generated_from":SOURCE_BANKS,
        "items":items,
        "coverage":{str(task):coverage[task] for task in range(1,28)},
        "validation":{
            "items_total":len(items),
            "exception_ids_unique":not any("duplicate exception_id" in e for e in errors),
            "skill_links_valid":not any("unknown skill_id" in e for e in errors),
            "subskill_links_valid":not any("unknown subskill_id" in e for e in errors),
            "source_refs_valid":not any("source_refs" in e or "source_type" in e for e in errors),
            "practice_modes_valid":not any("practice mode" in e for e in errors),
            "errors":errors,
            "warnings":warnings,
        },
        "integration_status":"not_connected_to_production",
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    write_audit(audit, total=len(items), errors=errors, warnings=warnings, coverage=coverage)

    if errors:
        print(f"FAIL: {len(errors)} validation error(s); see {audit}")
        return 1
    print(f"PASS: {len(items)} exception/special-case items; {len(warnings)} warning(s).")
    print(f"Canonical bank: {output}")
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
    output = args.output or root / "build" / "RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json"
    audit = args.audit or root / "audits" / "RUSSIAN-EXCEPTIONS-CANONICAL-VALIDATION.txt"
    try:
        return build(root, output, audit)
    except BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
