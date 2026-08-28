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
TASK_RELATION = PROGRAM / "ege-task-code-relation"
sys.path.insert(0, str(OBJECT_REVIEW))
sys.path.insert(0, str(TASK_RELATION))
from build_object_level_review_queue import build_queue  # noqa: E402
from build_fipi_ege_task_code_relation import build_relation  # noqa: E402

CROSSWALK_PATH = ENGINE / "274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json"
BASELINE_MAIN = "06157de40df8faf59355a05950da761ce26aa7e7"
EXPECTED_EGE_UNITS = 259
EXPECTED_EGE_REQUIREMENTS = 275
SOURCE_TASK_ID_RE = re.compile(r"^ege-2026-task-([1-9]|1[0-9]|2[0-7])$")
DOTTED_CODE_RE = re.compile(r"^\d+(?:\.\d+)+$")


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


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


def relation_indexes(relation: dict[str, Any]) -> dict[str, dict[str, set[int]]]:
    indexes: dict[str, dict[str, set[int]]] = {
        "content": defaultdict(set),
        "requirement": defaultdict(set),
    }
    for row in relation["rows"]:
        task = int(row["task"])
        for code in row["content_codes_expanded"]:
            indexes["content"][str(code)].add(task)
        for code in row["requirement_codes_expanded"]:
            indexes["requirement"][str(code)].add(task)
    return indexes


def proven_tasks_for_unit(document_id: str, section: str, code: str, indexes: dict[str, dict[str, set[int]]]) -> list[int]:
    if document_id != "EGE_COD" or not DOTTED_CODE_RE.fullmatch(code):
        return []
    if section == "section_1_checked_requirements":
        return sorted(indexes["requirement"].get(code, set()))
    if section == "section_2_content_elements":
        return sorted(indexes["content"].get(code, set()))
    return []


def classify_tasks(tasks: list[int], authority: dict[int, dict[str, Any]]) -> tuple[str, list[str], list[dict[str, Any]]]:
    if not tasks:
        return "TASK_ID_NOT_PROVEN", [], []
    targets: set[str] = set()
    refs: list[dict[str, Any]] = []
    for task in tasks:
        row = authority.get(task, {"canonical_targets": [], "authority_refs": []})
        targets.update(str(target) for target in row["canonical_targets"])
        refs.append({
            "task": task,
            "canonical_targets": list(row["canonical_targets"]),
            "authority_refs": list(row["authority_refs"]),
        })
    ordered_targets = sorted(targets)
    if len(tasks) == 1:
        if len(ordered_targets) == 1:
            return "EXACT_SINGLE_TASK_SINGLE_CANONICAL_CANDIDATE", ordered_targets, refs
        if len(ordered_targets) > 1:
            return "EXACT_SINGLE_TASK_COMPOSITE_CANONICAL_SET", ordered_targets, refs
        return "EXACT_SINGLE_TASK_ROUTE_WITHOUT_CANONICAL_TARGET", [], refs
    if ordered_targets:
        return "EXACT_MULTI_TASK_CANONICAL_CANDIDATE_SET", ordered_targets, refs
    return "EXACT_MULTI_TASK_ROUTE_WITHOUT_CANONICAL_TARGET", [], refs


def build_bridge() -> dict[str, Any]:
    queue = build_queue()
    units = [unit for unit in queue["admission_units"] if unit["priority_route"] == "EGE"]
    if len(units) != EXPECTED_EGE_UNITS:
        raise ValueError(f"EGE admission-unit drift: {len(units)}")
    if sum(int(unit["member_count"]) for unit in units) != EXPECTED_EGE_REQUIREMENTS:
        raise ValueError("EGE requirement-member drift")

    relation = build_relation()
    indexes = relation_indexes(relation)
    authority = reviewed_task_authority()

    records: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    doc_counts: Counter[str] = Counter()
    task_counts: Counter[str] = Counter()
    proven_unit_count = 0
    proven_requirement_count = 0
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
        tasks = proven_tasks_for_unit(document_id, section, code, indexes)
        candidate_class, targets, refs = classify_tasks(tasks, authority)
        if tasks:
            proven_unit_count += 1
            proven_requirement_count += int(unit["member_count"])
            for task in tasks:
                task_counts[str(task)] += 1
        doc_counts[document_id] += 1
        class_counts[candidate_class] += 1
        records.append({
            "admission_unit_id": unit_id,
            "member_count": int(unit["member_count"]),
            "source_id": str(signature["source_id"]),
            "document_id": document_id,
            "section": section,
            "code": code,
            "proven_tasks": tasks,
            "task_relation_authority": {
                "source_document_id": relation["source"]["document_id"],
                "source_sha256": relation["source"]["sha256"],
                "relation_hash": relation["normalized_sha256"],
            } if tasks else None,
            "candidate_class": candidate_class,
            "canonical_candidate_targets": targets,
            "reviewed_task_authority_refs": refs,
            "admission_status": "SUBJECT_REVIEW_REQUIRED",
        })

    records.sort(key=lambda row: row["admission_unit_id"])
    payload: dict[str, Any] = {
        "schema_version": "2.0.0",
        "status": "EGE_OFFICIAL_TASK_CODE_RELATION_BRIDGE_CANDIDATES",
        "baseline_main": BASELINE_MAIN,
        "source_object_review_state": "RUSSIAN-OBJECT-REVIEW-STATE-v1.0.json",
        "task_code_relation": {
            "path": "../ege-task-code-relation/FIPI-EGE-2026-TASK-CODE-RELATION-v1.0.json",
            "normalized_sha256": relation["normalized_sha256"],
            "tasks": 27,
        },
        "matching_policy": {
            "task_identity_source": "EXPLICIT_FIPI_EGE_2026_TASK_CODE_TABLE",
            "codifier_section_and_exact_code_required": True,
            "dotted_codifier_code_is_not_itself_a_task_id": True,
            "module_meaning_keyword_inference_allowed": False,
            "candidate_is_admission": False,
        },
        "summary": {
            "ege_admission_units": len(records),
            "ege_requirements": sum(int(row["member_count"]) for row in records),
            "task_proven_units": proven_unit_count,
            "task_proven_requirements": proven_requirement_count,
            "task_unproven_units": len(records) - proven_unit_count,
            "task_unproven_requirements": sum(int(row["member_count"]) for row in records) - proven_requirement_count,
            "candidate_classes": dict(sorted(class_counts.items())),
            "by_document": dict(sorted(doc_counts.items())),
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
        for key, value in bridge["summary"].items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
