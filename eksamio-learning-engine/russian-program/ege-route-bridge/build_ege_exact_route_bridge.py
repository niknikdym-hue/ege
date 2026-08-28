#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
OBJECT_REVIEW = PROGRAM / "object-review"
sys.path.insert(0, str(OBJECT_REVIEW))
from build_object_level_review_queue import build_queue  # noqa: E402

CROSSWALK_PATH = ENGINE / "274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json"
BASELINE_MAIN = "33b9f296128f644dfda4f02da34fb70ac8026b75"
EXPECTED_EGE_UNITS = 259
EXPECTED_EGE_REQUIREMENTS = 275
TASK_ID_RE = re.compile(r"^(?:EGE-2026-)?TASK[-:]([1-9]|1[0-9]|2[0-7])$", re.IGNORECASE)
SOURCE_TASK_ID_RE = re.compile(r"^ege-2026-task-([1-9]|1[0-9]|2[0-7])$")
DOTTED_CODE_RE = re.compile(r"^\d+(?:\.\d+)+$")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def parse_explicit_task_id(document_id: str, section: str, code: str) -> int | None:
    del document_id, section  # Task identity must be explicit in the code itself.
    value = code.strip()
    if DOTTED_CODE_RE.fullmatch(value):
        return None
    match = TASK_ID_RE.fullmatch(value)
    if not match:
        return None
    return int(match.group(1))


def reviewed_task_authority() -> dict[int, dict[str, Any]]:
    payload = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    task_targets: dict[int, set[str]] = defaultdict(set)
    task_refs: dict[int, list[dict[str, Any]]] = defaultdict(list)
    tasks_seen: set[int] = set()
    for row in payload.get("mappings", []):
        if row.get("source_system") != "ege_2026_overlay":
            continue
        source_id = row.get("source_id")
        if not isinstance(source_id, str):
            continue
        match = SOURCE_TASK_ID_RE.fullmatch(source_id)
        if not match:
            continue
        task = int(match.group(1))
        tasks_seen.add(task)
        if row.get("review_status") != "reviewed":
            continue
        target = row.get("target_semantic_id")
        if isinstance(target, str):
            if not target.startswith("school-"):
                raise ValueError(f"reviewed EGE task mapping targets noncanonical namespace: {target}")
            task_targets[task].add(target)
        task_refs[task].append({
            "mapping_id": row.get("mapping_id"),
            "relation": row.get("relation"),
            "target_semantic_id": target,
            "provenance_refs": row.get("provenance_refs") or [],
            "review_status": "reviewed",
        })
    return {
        task: {
            "canonical_targets": sorted(task_targets.get(task, set())),
            "authority_refs": task_refs.get(task, []),
        }
        for task in sorted(tasks_seen)
    }


def classify(task: int | None, authority: dict[int, dict[str, Any]]) -> tuple[str, list[str], list[dict[str, Any]]]:
    if task is None:
        return "TASK_ID_NOT_PROVEN", [], []
    row = authority.get(task)
    if row is None:
        return "ROUTE_WITHOUT_CANONICAL_TARGET", [], []
    targets = list(row["canonical_targets"])
    refs = list(row["authority_refs"])
    if len(targets) == 1:
        return "EXACT_SINGLE_CANONICAL_CANDIDATE", targets, refs
    if len(targets) > 1:
        return "COMPOSITE_CANONICAL_SET", targets, refs
    return "ROUTE_WITHOUT_CANONICAL_TARGET", [], refs


def build_bridge() -> dict[str, Any]:
    queue = build_queue()
    units = [unit for unit in queue["admission_units"] if unit["priority_route"] == "EGE"]
    if len(units) != EXPECTED_EGE_UNITS:
        raise ValueError(f"EGE admission-unit drift: {len(units)}")
    if sum(int(unit["member_count"]) for unit in units) != EXPECTED_EGE_REQUIREMENTS:
        raise ValueError("EGE requirement-member drift")
    authority = reviewed_task_authority()

    records: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    doc_counts: Counter[str] = Counter()
    pattern_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()
    seen: set[str] = set()

    for unit in units:
        unit_id = str(unit["admission_unit_id"])
        if unit_id in seen:
            raise ValueError(f"duplicate EGE admission unit: {unit_id}")
        seen.add(unit_id)
        signature = unit["admission_signature"]
        document_id = str(signature["document_id"])
        section = str(signature["section"])
        code = str(signature["code"])
        task = parse_explicit_task_id(document_id, section, code)
        candidate_class, targets, refs = classify(task, authority)
        if task is not None:
            task_counts[str(task)] += 1
        doc_counts[document_id] += 1
        shape = "DOTTED_REQUIREMENT_CODE" if DOTTED_CODE_RE.fullmatch(code) else code
        pattern_counts[f"{document_id}::{shape}"] += 1
        class_counts[candidate_class] += 1
        records.append({
            "admission_unit_id": unit_id,
            "member_count": int(unit["member_count"]),
            "source_id": str(signature["source_id"]),
            "document_id": document_id,
            "section": section,
            "code": code,
            "proven_task": task,
            "candidate_class": candidate_class,
            "canonical_candidate_targets": targets,
            "reviewed_authority_refs": refs,
            "admission_status": "SUBJECT_REVIEW_REQUIRED",
        })

    records.sort(key=lambda row: row["admission_unit_id"])
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "status": "EGE_EXACT_ROUTE_BRIDGE_CANDIDATES_FAIL_CLOSED",
        "baseline_main": BASELINE_MAIN,
        "source_object_review_state": "RUSSIAN-OBJECT-REVIEW-STATE-v1.0.json",
        "matching_policy": {
            "task_identity_source": "EXPLICIT_CODE_ONLY",
            "dotted_codifier_codes_are_task_ids": False,
            "module_meaning_keyword_inference_allowed": False,
            "candidate_is_admission": False,
        },
        "summary": {
            "ege_admission_units": len(records),
            "ege_requirements": sum(int(row["member_count"]) for row in records),
            "candidate_classes": dict(sorted(class_counts.items())),
            "by_document": dict(sorted(doc_counts.items())),
            "by_code_pattern": dict(sorted(pattern_counts.items())),
            "proven_task_distribution": dict(sorted(task_counts.items(), key=lambda item: int(item[0]))),
            "semantic_admissions": 0,
        },
        "reviewed_task_authority_task_count": len(authority),
        "records": records,
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    bridge = build_bridge()
    if args.emit:
        print(json.dumps(bridge, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_EGE_EXACT_ROUTE_BRIDGE=PASS")
        print(f"normalized_sha256={bridge['normalized_sha256']}")
        print(f"ege_admission_units={bridge['summary']['ege_admission_units']}")
        print(f"ege_requirements={bridge['summary']['ege_requirements']}")
        for key, value in bridge["summary"]["candidate_classes"].items():
            print(f"candidate[{key}]={value}")
        print(f"proven_tasks={sum(bridge['summary']['proven_task_distribution'].values())}")
        print("semantic_admissions=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
