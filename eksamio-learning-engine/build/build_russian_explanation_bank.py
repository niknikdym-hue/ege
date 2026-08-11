#!/usr/bin/env python3
"""Build and validate the canonical Eksamio Russian explanation bank.

This script is intentionally data-only. It reads Learning Engine source files and
writes build/audit artifacts. It MUST NOT modify trainer T123/JS/HTML/CSS,
answers, scoring, localStorage, URLs, or production behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0.0"

BASE_FILES = [
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
]

SPLIT_FILES = [
    "61-RUSSIAN-EXPLANATION-TASK11-SUFFIX-SPLITS-v0.1.json",
    "62-RUSSIAN-EXPLANATION-TASK14-WRITING-SPLITS-v0.1.json",
    "67-RUSSIAN-EXPLANATION-TASK21-RULE-SPLITS-v0.1.json",
    "72-RUSSIAN-EXPLANATION-TASK14-HYPHEN-ADVERB-SPLITS-v0.1.json",
    "80-RUSSIAN-EXPLANATION-TASK14-POL-SPLIT-v0.1.json",
]

OVERLAY_FILE = "63-RUSSIAN-EXPLANATION-WAVE1-EXAMPLES-OVERLAY-v0.1.json"
SKILL_GRAPH_FILE = "03-RUSSIAN-SKILL-GRAPH.json"
ROUTING_MAP_FILE = "59-RUSSIAN-EXPLANATION-TASK-ROUTING-MAP.json"
ROUTING_INDEX_FILE = "75-RUSSIAN-EXPLANATION-ROUTING-TAG-INDEX.json"

REQUIRED_FIELDS = [
    "explanation_id",
    "skill_ids",
    "subskill_ids",
    "exam_task_numbers",
    "short_rule",
    "rule",
    "algorithm",
    "common_traps",
    "examples",
    "source_refs",
    "status",
]

ALLOWED_SOURCE_TYPES = {
    "official_fipi",
    "book",
    "existing_trainer",
    "internal_verified_source",
}

# Explicitly accepted exceptions to the usual non-empty-array policy.
ALLOW_EMPTY_SUBSKILLS = {"essay_ethics_review"}
ALLOW_EMPTY_EXAMPLES = {"essay_source_volume_gate", "essay_ethics_review"}


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


class BuildError(RuntimeError):
    pass


def require_units(data: Any, path: Path) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or not isinstance(data.get("units"), list):
        raise BuildError(f"Expected top-level units[] in {path}")
    units = data["units"]
    if not all(isinstance(unit, dict) for unit in units):
        raise BuildError(f"Non-object entry found in units[] of {path}")
    return units


def walk(obj: Any) -> Iterable[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from walk(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value)


def collect_graph_ids(graph: Any) -> tuple[set[str], set[str]]:
    """Collect all Skill Graph IDs without assuming a fragile nesting shape.

    Accepted graph nodes use `skill_id`; nodes with a non-null parent_skill_id
    are treated as subskills. Top-level nodes have parent_skill_id=null.
    """
    all_ids: set[str] = set()
    subskill_ids: set[str] = set()
    for node in walk(graph):
        if not isinstance(node, dict):
            continue
        skill_id = node.get("skill_id")
        if isinstance(skill_id, str) and skill_id:
            all_ids.add(skill_id)
            if node.get("parent_skill_id") is not None:
                subskill_ids.add(skill_id)
    if not all_ids:
        raise BuildError("No skill_id values found in Skill Graph")
    return all_ids, subskill_ids


def collect_string_values_for_key(obj: Any, key: str) -> list[str]:
    values: list[str] = []
    for node in walk(obj):
        if isinstance(node, dict) and key in node:
            value = node[key]
            if isinstance(value, str):
                values.append(value)
            elif isinstance(value, list):
                values.extend(x for x in value if isinstance(x, str))
    return values


def append_units(
    units_by_id: dict[str, dict[str, Any]],
    source_by_id: dict[str, str],
    units: list[dict[str, Any]],
    source_name: str,
) -> None:
    for unit in units:
        explanation_id = unit.get("explanation_id")
        if not isinstance(explanation_id, str) or not explanation_id:
            raise BuildError(f"Unit without explanation_id in {source_name}")
        if explanation_id in units_by_id:
            raise BuildError(
                f"Duplicate explanation_id {explanation_id!r}: "
                f"{source_by_id[explanation_id]} and {source_name}"
            )
        # Deep-copy through JSON to ensure build output contains only JSON-safe data.
        units_by_id[explanation_id] = json.loads(json.dumps(unit, ensure_ascii=False))
        source_by_id[explanation_id] = source_name


def apply_examples_overlay(
    units_by_id: dict[str, dict[str, Any]], overlay: dict[str, Any]
) -> list[str]:
    targets = overlay.get("targets")
    if not isinstance(targets, list):
        raise BuildError(f"Expected targets[] in {OVERLAY_FILE}")

    seen: set[str] = set()
    applied: list[str] = []
    for row in targets:
        if not isinstance(row, dict):
            raise BuildError(f"Non-object overlay target in {OVERLAY_FILE}")
        explanation_id = row.get("explanation_id")
        examples = row.get("examples")
        if not isinstance(explanation_id, str) or not explanation_id:
            raise BuildError(f"Overlay target without explanation_id in {OVERLAY_FILE}")
        if explanation_id in seen:
            raise BuildError(f"Duplicate overlay target: {explanation_id}")
        seen.add(explanation_id)
        if explanation_id not in units_by_id:
            raise BuildError(f"Overlay target not found in base bank: {explanation_id}")
        if not isinstance(examples, list):
            raise BuildError(f"Overlay examples is not an array for {explanation_id}")
        units_by_id[explanation_id]["examples"] = json.loads(
            json.dumps(examples, ensure_ascii=False)
        )
        applied.append(explanation_id)
    return applied


def validate_unit_contract(
    units_by_id: dict[str, dict[str, Any]],
    graph_ids: set[str],
    graph_subskill_ids: set[str],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for explanation_id, unit in sorted(units_by_id.items()):
        missing = [field for field in REQUIRED_FIELDS if field not in unit]
        if missing:
            errors.append(f"{explanation_id}: missing fields {', '.join(missing)}")
            continue

        skill_ids = unit.get("skill_ids")
        subskill_ids = unit.get("subskill_ids")
        task_numbers = unit.get("exam_task_numbers")
        examples = unit.get("examples")
        source_refs = unit.get("source_refs")

        if not isinstance(skill_ids, list) or not all(
            isinstance(x, str) and x for x in skill_ids
        ):
            errors.append(f"{explanation_id}: invalid skill_ids")
        else:
            for skill_id in skill_ids:
                if skill_id not in graph_ids:
                    errors.append(
                        f"{explanation_id}: unknown Skill Graph skill_id {skill_id}"
                    )

        if not isinstance(subskill_ids, list):
            errors.append(f"{explanation_id}: invalid subskill_ids")
        else:
            if not subskill_ids and explanation_id not in ALLOW_EMPTY_SUBSKILLS:
                errors.append(f"{explanation_id}: empty subskill_ids is not whitelisted")
            for subskill_id in subskill_ids:
                if not isinstance(subskill_id, str) or not subskill_id:
                    errors.append(f"{explanation_id}: invalid subskill_id value")
                elif subskill_id not in graph_ids:
                    errors.append(
                        f"{explanation_id}: unknown Skill Graph subskill_id {subskill_id}"
                    )
                elif graph_subskill_ids and subskill_id not in graph_subskill_ids:
                    warnings.append(
                        f"{explanation_id}: {subskill_id} exists in graph but is not marked as a child node"
                    )

        if not isinstance(task_numbers, list) or not task_numbers:
            errors.append(f"{explanation_id}: invalid/empty exam_task_numbers")
        else:
            for task in task_numbers:
                if not isinstance(task, int) or not 1 <= task <= 27:
                    errors.append(f"{explanation_id}: invalid task number {task!r}")

        for field in ("algorithm", "common_traps"):
            value = unit.get(field)
            if not isinstance(value, list) or not value:
                errors.append(f"{explanation_id}: {field} must be a non-empty array")

        if not isinstance(examples, list):
            errors.append(f"{explanation_id}: examples must be an array")
        elif not examples and explanation_id not in ALLOW_EMPTY_EXAMPLES:
            warnings.append(f"{explanation_id}: examples is empty and needs editorial review")

        if not isinstance(source_refs, list) or not source_refs:
            errors.append(f"{explanation_id}: source_refs must be a non-empty array")
        else:
            for idx, ref in enumerate(source_refs):
                if not isinstance(ref, dict):
                    errors.append(f"{explanation_id}: source_refs[{idx}] is not an object")
                    continue
                source_type = ref.get("source_type")
                if source_type not in ALLOWED_SOURCE_TYPES:
                    warnings.append(
                        f"{explanation_id}: source_refs[{idx}] has noncanonical source_type {source_type!r}"
                    )
                source_path = ref.get("source_path")
                if not isinstance(source_path, str) or not source_path.strip():
                    errors.append(
                        f"{explanation_id}: source_refs[{idx}] missing source_path"
                    )
                elif source_path.strip().lower() in {"verified corpus", "verified source"}:
                    warnings.append(
                        f"{explanation_id}: vague source_path {source_path!r}"
                    )

    return errors, warnings


def collect_coverage(units_by_id: dict[str, dict[str, Any]]) -> dict[int, list[str]]:
    coverage: dict[int, list[str]] = {task: [] for task in range(1, 28)}
    for explanation_id, unit in units_by_id.items():
        for task in unit.get("exam_task_numbers", []):
            if isinstance(task, int) and task in coverage:
                coverage[task].append(explanation_id)
    for ids in coverage.values():
        ids.sort()
    return coverage


def load_routing_tag_files(root: Path, index: dict[str, Any]) -> list[tuple[str, Any]]:
    result: list[tuple[str, Any]] = []
    rows = index.get("files")
    if not isinstance(rows, list):
        raise BuildError(f"Expected files[] in {ROUTING_INDEX_FILE}")
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str):
            raise BuildError(f"Invalid file row in {ROUTING_INDEX_FILE}")
        rel = row["path"]
        result.append((rel, load_json(root / rel)))
    return result


def validate_routing_links(
    root: Path,
    units_by_id: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts = {"routing_files": 0, "needs_followup": 0, "partial": 0}
    canonical_ids = set(units_by_id)

    routing_map = load_json(root / ROUTING_MAP_FILE)
    for explanation_id in collect_string_values_for_key(
        routing_map, "candidate_explanation_ids"
    ):
        if explanation_id not in canonical_ids:
            errors.append(
                f"Routing map references missing candidate explanation_id {explanation_id}"
            )

    index = load_json(root / ROUTING_INDEX_FILE)
    for rel, data in load_routing_tag_files(root, index):
        counts["routing_files"] += 1
        for explanation_id in collect_string_values_for_key(data, "explanation_id"):
            if explanation_id not in canonical_ids:
                errors.append(f"{rel}: references missing explanation_id {explanation_id}")
        for node in walk(data):
            if isinstance(node, dict):
                confidence = node.get("diagnostic_confidence")
                if confidence == "needs_followup":
                    counts["needs_followup"] += 1
                elif confidence == "partial":
                    counts["partial"] += 1

    # Generation specs and support files named by the index must exist even though
    # they are not JSON routing-tag payloads.
    for section in ("generation_specs", "supporting_explanation_splits", "audits"):
        rows = index.get(section, [])
        if not isinstance(rows, list):
            errors.append(f"{ROUTING_INDEX_FILE}: {section} must be an array")
            continue
        for row in rows:
            if isinstance(row, dict) and isinstance(row.get("path"), str):
                if not (root / row["path"]).exists():
                    errors.append(
                        f"{ROUTING_INDEX_FILE}: referenced file missing: {row['path']}"
                    )

    if index.get("current_standard_routing_first_pass_complete") is not True:
        warnings.append("Routing index does not mark first-part first pass complete")

    tagged = index.get("current_tagged_or_autotag_ready_tasks")
    if tagged != list(range(1, 27)):
        errors.append(
            "Routing index current_tagged_or_autotag_ready_tasks must equal tasks 1..26"
        )

    return errors, warnings, counts


def write_audit(
    path: Path,
    *,
    units_total: int,
    source_files: list[str],
    overlay_applied: list[str],
    coverage: dict[int, list[str]],
    errors: list[str],
    warnings: list[str],
    routing_counts: dict[str, int],
) -> None:
    missing_tasks = [str(task) for task, ids in coverage.items() if not ids]
    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN EXPLANATION CANONICAL BUILD VALIDATION",
        "",
        f"STATUS: {'PASS' if not errors else 'FAIL'}",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        f"UNITS_TOTAL: {units_total}",
        f"SOURCE_FILES_PARSED: {len(source_files)}",
        f"OVERLAY_TARGETS_APPLIED: {len(overlay_applied)}",
        f"TASK_COVERAGE: {'27/27' if not missing_tasks else 'MISSING ' + ','.join(missing_tasks)}",
        f"ROUTING_TAG_FILES_PARSED: {routing_counts.get('routing_files', 0)}",
        f"ROUTING_NEEDS_FOLLOWUP_TAGS: {routing_counts.get('needs_followup', 0)}",
        f"ROUTING_PARTIAL_TAGS: {routing_counts.get('partial', 0)}",
        f"ERRORS: {len(errors)}",
        f"WARNINGS: {len(warnings)}",
        "",
        "SOURCE FILES",
    ]
    lines.extend(f"- {name}" for name in source_files)
    lines.extend(["", "ERRORS"])
    lines.extend(["- none"] if not errors else [f"- {item}" for item in errors])
    lines.extend(["", "WARNINGS"])
    lines.extend(["- none"] if not warnings else [f"- {item}" for item in warnings])
    lines.extend(["", "TASK COVERAGE"])
    for task in range(1, 28):
        lines.append(f"- {task}: {', '.join(coverage[task]) or 'MISSING'}")
    lines.extend(
        [
            "",
            "PRODUCTION SAFETY",
            "- This build reads Learning Engine data only.",
            "- It does not modify current trainer T123/JS/HTML/CSS/localStorage/answers/scoring.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build(root: Path, output: Path, audit: Path) -> int:
    root = root.resolve()
    source_names = BASE_FILES + SPLIT_FILES

    units_by_id: dict[str, dict[str, Any]] = {}
    source_by_id: dict[str, str] = {}

    for rel in BASE_FILES:
        data = load_json(root / rel)
        append_units(units_by_id, source_by_id, require_units(data, root / rel), rel)

    overlay = load_json(root / OVERLAY_FILE)
    overlay_applied = apply_examples_overlay(units_by_id, overlay)

    for rel in SPLIT_FILES:
        data = load_json(root / rel)
        append_units(units_by_id, source_by_id, require_units(data, root / rel), rel)

    graph = load_json(root / SKILL_GRAPH_FILE)
    graph_ids, graph_subskill_ids = collect_graph_ids(graph)

    errors, warnings = validate_unit_contract(
        units_by_id, graph_ids, graph_subskill_ids
    )

    coverage = collect_coverage(units_by_id)
    missing_tasks = [task for task, ids in coverage.items() if not ids]
    if missing_tasks:
        errors.append(f"Missing explanation coverage for tasks: {missing_tasks}")

    routing_errors, routing_warnings, routing_counts = validate_routing_links(
        root, units_by_id
    )
    errors.extend(routing_errors)
    warnings.extend(routing_warnings)

    # Stable output ordering makes diffs and reproducibility checks useful.
    canonical_units = [units_by_id[key] for key in sorted(units_by_id)]
    output_payload = {
        "schema_version": SCHEMA_VERSION,
        "subject": "russian",
        "exam": "ege",
        "build_version": "0.1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_from": source_names + [OVERLAY_FILE],
        "units": canonical_units,
        "coverage": {str(task): coverage[task] for task in range(1, 28)},
        "validation": {
            "source_files_parsed": len(source_names) + 1,
            "units_total": len(canonical_units),
            "explanation_ids_unique": True,
            "skill_links_valid": not any("skill_id" in e for e in errors),
            "subskill_links_valid": not any("subskill_id" in e for e in errors),
            "required_fields_valid": not any("missing fields" in e for e in errors),
            "routing_links_valid": not bool(routing_errors),
            "task_coverage_1_27": not missing_tasks,
            "errors": errors,
            "warnings": warnings,
            "routing_needs_followup": routing_counts.get("needs_followup", 0),
            "routing_partial": routing_counts.get("partial", 0),
        },
        "integration_status": "not_connected_to_production",
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    write_audit(
        audit,
        units_total=len(canonical_units),
        source_files=source_names + [OVERLAY_FILE],
        overlay_applied=overlay_applied,
        coverage=coverage,
        errors=errors,
        warnings=warnings,
        routing_counts=routing_counts,
    )

    if errors:
        print(f"FAIL: canonical bank built with {len(errors)} validation error(s).")
        print(f"See: {audit}")
        return 1

    print(
        f"PASS: {len(canonical_units)} explanation units; 27/27 task coverage; "
        f"{len(warnings)} warning(s)."
    )
    print(f"Canonical bank: {output}")
    print(f"Audit: {audit}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    default_root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--root",
        type=Path,
        default=default_root,
        help="Path to eksamio-learning-engine directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Canonical JSON output path",
    )
    parser.add_argument(
        "--audit",
        type=Path,
        default=None,
        help="Human-readable validation report path",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or root / "build" / "RUSSIAN-EXPLANATION-BANK-CANONICAL.json"
    audit = args.audit or root / "audits" / "RUSSIAN-EXPLANATION-CANONICAL-VALIDATION.txt"

    try:
        return build(root, output, audit)
    except BuildError as exc:
        print(f"BUILD ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
