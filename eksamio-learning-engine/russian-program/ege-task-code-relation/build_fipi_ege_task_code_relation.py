#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
SOURCE_KNOWLEDGE = PROGRAM / "source-knowledge"
RELATION_PATH = HERE / "FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json"
REQ_INDEX_PATH = SOURCE_KNOWLEDGE / "RUSSIAN-OFFICIAL-REQUIREMENTS-INDEX-v1.0.json"

EXPECTED_SPEC_SHA = "3b71ec81f954bc32b574a0b3b997ee37bb3bc19ae8825f11217fd7149198b476"
EXPECTED_TASKS = set(range(1, 28))
CODE_RE = re.compile(r"^\d+(?:\.\d+)*$")
RANGE_RE = re.compile(r"^(\d+(?:\.\d+)*)–(\d+(?:\.\d+)*)$")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def expand_expression(expression: str) -> list[str]:
    value = expression.strip()
    if CODE_RE.fullmatch(value):
        return [value]
    match = RANGE_RE.fullmatch(value)
    if not match:
        raise ValueError(f"unsupported FIPI code expression: {expression!r}")
    start = match.group(1).split(".")
    end = match.group(2).split(".")
    if len(start) != len(end) or start[:-1] != end[:-1]:
        raise ValueError(f"unsafe/nonlocal FIPI code range: {expression!r}")
    left = int(start[-1])
    right = int(end[-1])
    if left > right or right - left > 50:
        raise ValueError(f"invalid FIPI code range: {expression!r}")
    prefix = ".".join(start[:-1])
    return [f"{prefix}.{number}" if prefix else str(number) for number in range(left, right + 1)]


def expand_many(expressions: list[str]) -> list[str]:
    result: list[str] = []
    for expression in expressions:
        for code in expand_expression(expression):
            if code not in result:
                result.append(code)
    return result


def load_codifier_codes() -> dict[str, set[str]]:
    index = json.loads(REQ_INDEX_PATH.read_text(encoding="utf-8"))
    catalogs = index["catalogs"]
    codes: dict[str, set[str]] = defaultdict(set)
    for shard in index["shards"]:
        payload = json.loads((SOURCE_KNOWLEDGE / shard["path"]).read_text(encoding="utf-8"))
        for row in payload["records"]:
            document = catalogs["documents"][int(row[1])]
            if document["document_id"] != "EGE_COD":
                continue
            section = str(catalogs["sections"][int(row[4])])
            codes[section].add(str(row[3]))
    return codes


def build_relation() -> dict[str, Any]:
    source = json.loads(RELATION_PATH.read_text(encoding="utf-8"))
    source_meta = source["source"]
    if source_meta["source_id"] != "FIPI-EGE-RU-2026-FINAL":
        raise ValueError("wrong FIPI EGE launch source")
    if source_meta["document_id"] != "EGE_SPEC" or source_meta["sha256"] != EXPECTED_SPEC_SHA:
        raise ValueError("EGE specification fingerprint drift")

    seen: set[int] = set()
    rows: list[dict[str, Any]] = []
    for row in source["rows"]:
        task = int(row["task"])
        if task in seen or task not in EXPECTED_TASKS:
            raise ValueError(f"duplicate/out-of-range task: {task}")
        seen.add(task)
        content_expressions = [str(value) for value in row["content_code_expressions"]]
        requirement_expressions = [str(value) for value in row["requirement_code_expressions"]]
        content_codes = expand_many(content_expressions)
        requirement_codes = expand_many(requirement_expressions)
        if not content_codes or not requirement_codes:
            raise ValueError(f"task {task} lacks explicit task-to-code relation")
        rows.append({
            **row,
            "content_codes_expanded": content_codes,
            "requirement_codes_expanded": requirement_codes,
            "locator": {
                "document_id": "EGE_SPEC",
                "source_sha256": EXPECTED_SPEC_SHA,
                "table": source_meta["table"],
                "printed_page": int(row["printed_page"]),
                "pdf_physical_page": int(row["pdf_page"]),
                "panel": str(row["panel"]),
                "row": f"task-{task}",
            },
            "provenance_status": "EXPLICIT_FIPI_TABLE_ROW",
        })
    if seen != EXPECTED_TASKS:
        raise ValueError(f"task coverage incomplete: missing {sorted(EXPECTED_TASKS - seen)}")

    rows.sort(key=lambda item: int(item["task"]))
    relation: dict[str, Any] = {
        "schema_version": "1.0.0",
        "status": "OFFICIAL_FIPI_EGE_2026_TASK_TO_CODE_RELATION_VALIDATED",
        "source": source_meta,
        "relation_policy": source["relation_policy"],
        "summary": {
            "task_rows": len(rows),
            "tasks": [int(row["task"]) for row in rows],
            "basic_tasks": sum(row["difficulty"] == "Б" for row in rows),
            "advanced_tasks": sum(row["difficulty"] == "П" for row in rows),
            "max_primary_score_total": sum(int(row["max_primary_score"]) for row in rows),
            "content_code_atoms": len({code for row in rows for code in row["content_codes_expanded"]}),
            "requirement_code_atoms": len({code for row in rows for code in row["requirement_codes_expanded"]}),
        },
        "rows": rows,
    }
    relation["normalized_sha256"] = hashlib.sha256(canonical_json(relation)).hexdigest()
    return relation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    relation = build_relation()
    if args.emit:
        print(json.dumps(relation, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("FIPI_EGE_2026_TASK_CODE_RELATION=PASS")
        print(f"normalized_sha256={relation['normalized_sha256']}")
        for key, value in relation["summary"].items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
