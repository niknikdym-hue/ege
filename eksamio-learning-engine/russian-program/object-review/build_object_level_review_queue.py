#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
ENGINE = PROGRAM.parent
SOURCE = PROGRAM / "source-knowledge"
REQ_INDEX_PATH = SOURCE / "RUSSIAN-OFFICIAL-REQUIREMENTS-INDEX-v1.0.json"
SEMANTIC_CROSSWALK_PATH = ENGINE / "274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json"

BASELINE_MAIN = "400736e1c6b19689ef9535e0d801639f01d4e96e"
PR139_HEAD = "f16884ec4f8992ee9ad01c2930c42349f579bc70"
FORBIDDEN_SOURCE = "FIPI-OGE-RU-2027-PROJECT"
EXPECTED_REQUIREMENTS = 1400
EXPECTED_COLUMNS = [
    "record_id", "document_ref", "page", "code", "section_ref", "class_ref",
    "grades_ref", "routes_ref", "module_mask", "meaning_ref", "confidence_ref", "status_ref",
]

PR139_CONTEXT_BY_MODULE: dict[int, str] = {
    1: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json",
    2: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-02-ORTHOEPY-STRESS-WAVE-002-v0.1.json",
    3: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-03-LEXIS-PARONYMS-PHRASEOLOGY-WAVE-002-v0.1.json",
    4: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-04-MORPHEMICS-WAVE-001-v0.1.json",
    5: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-05-WORD-FORMATION-WAVE-001-v0.1.json",
    6: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-06-MORPHOLOGY-WAVE-002-v0.1.json",
    7: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-07-GRAMMAR-NORMS-WAVE-002-v0.1.json",
    11: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-11-TEXT-COHESION-WAVE-002-v0.1.json",
    12: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-12-STYLES-GENRES-WAVE-002-v0.1.json",
    15: "eksamio-learning-engine/russian-program/production-learning-content/RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def decode_modules(mask: int) -> list[str]:
    if not isinstance(mask, int) or mask <= 0 or mask >= (1 << 16):
        raise ValueError(f"invalid RU-PROG module mask: {mask!r}")
    return [f"RU-PROG-{bit + 1:02d}" for bit in range(16) if mask & (1 << bit)]


def load_requirements() -> tuple[dict[str, Any], list[list[Any]]]:
    index = json.loads(REQ_INDEX_PATH.read_text(encoding="utf-8"))
    rows: list[list[Any]] = []
    for shard in index["shards"]:
        payload = json.loads((SOURCE / shard["path"]).read_text(encoding="utf-8"))
        if payload["columns"] != EXPECTED_COLUMNS:
            raise ValueError(f"source requirement schema drift: {shard['path']}")
        if len(payload["records"]) != int(shard["record_count"]):
            raise ValueError(f"source requirement shard count drift: {shard['path']}")
        rows.extend(payload["records"])
    if len(rows) != EXPECTED_REQUIREMENTS:
        raise ValueError(f"expected {EXPECTED_REQUIREMENTS} requirements, got {len(rows)}")
    return index, rows


def load_exact_canonical_authority() -> tuple[set[str], dict[str, set[str]]]:
    payload = json.loads(SEMANTIC_CROSSWALK_PATH.read_text(encoding="utf-8"))
    mappings = payload.get("mappings", [])
    canonical_targets: set[str] = {
        str(row["target_semantic_id"])
        for row in mappings
        if row.get("relation") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("review_status") == "reviewed"
        and isinstance(row.get("target_semantic_id"), str)
        and str(row["target_semantic_id"]).startswith("school-")
    }
    direct: dict[str, set[str]] = defaultdict(set)
    for row in mappings:
        target = row.get("target_semantic_id")
        if target not in canonical_targets or row.get("review_status") != "reviewed":
            continue
        for key in ("source_id", "source_object_key"):
            source_key = row.get(key)
            if isinstance(source_key, str) and source_key.startswith("RSK-"):
                direct[source_key].add(str(target))
        for provenance_ref in row.get("provenance_refs") or []:
            if isinstance(provenance_ref, str) and provenance_ref.startswith("RSK-"):
                direct[provenance_ref].add(str(target))
    return canonical_targets, direct


def review_signature(row: list[Any], index: dict[str, Any]) -> dict[str, Any]:
    catalogs = index["catalogs"]
    return {
        "normalized_meaning": str(catalogs["meanings"][int(row[9])]),
        "requirement_class": str(catalogs["classes"][int(row[5])]),
        "modules": decode_modules(int(row[8])),
        "routes": sorted(str(v) for v in catalogs["routes"][int(row[7])]),
    }


def admission_signature(row: list[Any], index: dict[str, Any]) -> dict[str, Any]:
    catalogs = index["catalogs"]
    document = catalogs["documents"][int(row[1])]
    return {
        "review_signature": review_signature(row, index),
        "source_id": str(document["source_id"]),
        "document_id": str(document["document_id"]),
        "section": str(catalogs["sections"][int(row[4])]),
        "code": str(row[3]),
    }


def review_batch_id(signature: dict[str, Any]) -> str:
    return "RRB-" + hashlib.sha256(canonical_json(signature)).hexdigest()[:20]


def admission_unit_id(signature: dict[str, Any]) -> str:
    return "RAU-" + hashlib.sha256(canonical_json(signature)).hexdigest()[:20]


def route_priority(routes: list[str]) -> tuple[int, str]:
    route_set = set(routes)
    if "ege" in route_set:
        return 0, "EGE"
    if "oge" in route_set:
        return 1, "OGE"
    return 2, "SCHOOL"


def proposed_context_refs(modules: list[str]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for module in modules:
        number = int(module.rsplit("-", 1)[1])
        path = PR139_CONTEXT_BY_MODULE.get(number)
        if path:
            refs.append({
                "pr_head": PR139_HEAD,
                "path": path,
                "authority": "CONTEXT_ONLY_PROPOSED_NOT_CANONICAL",
            })
    return refs


def exact_unit_resolution(member_ids: list[str], direct: dict[str, set[str]], canonical_targets: set[str]) -> str | None:
    targets: set[str] = set()
    for requirement_id in member_ids:
        direct_targets = direct.get(requirement_id, set())
        if len(direct_targets) != 1:
            return None
        target = next(iter(direct_targets))
        if target not in canonical_targets:
            return None
        targets.add(target)
    return next(iter(targets)) if len(targets) == 1 else None


def member_object(row: list[Any], index: dict[str, Any]) -> dict[str, Any]:
    catalogs = index["catalogs"]
    document = catalogs["documents"][int(row[1])]
    source_id = str(document["source_id"])
    if source_id == FORBIDDEN_SOURCE:
        raise ValueError("provisional 2027 source entered object review queue")
    return {
        "requirement_id": str(row[0]),
        "source_id": source_id,
        "document_id": str(document["document_id"]),
        "source_sha256": str(document["sha256"]),
        "page": int(row[2]),
        "code": str(row[3]),
        "section": str(catalogs["sections"][int(row[4])]),
        "grades": sorted(str(v) for v in catalogs["grades"][int(row[6])]),
        "confidence": str(catalogs["confidences"][int(row[10])]),
    }


def build_queue() -> dict[str, Any]:
    index, rows = load_requirements()
    canonical_targets, direct = load_exact_canonical_authority()

    unit_buckets: dict[bytes, list[list[Any]]] = defaultdict(list)
    unit_signatures: dict[bytes, dict[str, Any]] = {}
    for row in rows:
        signature = admission_signature(row, index)
        key = canonical_json(signature)
        unit_buckets[key].append(row)
        unit_signatures[key] = signature

    admission_units: list[dict[str, Any]] = []
    for key, member_rows in unit_buckets.items():
        signature = unit_signatures[key]
        review = signature["review_signature"]
        members = [member_object(row, index) for row in sorted(member_rows, key=lambda item: str(item[0]))]
        member_ids = [str(member["requirement_id"]) for member in members]
        exact_target = exact_unit_resolution(member_ids, direct, canonical_targets)
        priority_rank, priority_route = route_priority(review["routes"])
        unit = {
            "admission_unit_id": admission_unit_id(signature),
            "review_batch_id": review_batch_id(review),
            "admission_signature": signature,
            "priority_route": priority_route,
            "priority_rank": priority_rank,
            "member_count": len(members),
            "grades_represented": sorted({grade for member in members for grade in member["grades"]}, key=lambda value: int(value) if value.isdigit() else 999),
            "members": members,
            "exact_canonical_semantic_id": exact_target,
            "admission_status": "AUTO_RESOLVED_CANONICAL" if exact_target else "SUBJECT_REVIEW_REQUIRED",
            "proposed_context_refs": proposed_context_refs(review["modules"]),
        }
        admission_units.append(unit)

    admission_units.sort(key=lambda unit: (
        int(unit["priority_rank"]),
        -int(unit["member_count"]),
        str(unit["admission_unit_id"]),
    ))

    units_by_batch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in admission_units:
        units_by_batch[str(unit["review_batch_id"])].append(unit)

    review_batches: list[dict[str, Any]] = []
    for batch_id, units in units_by_batch.items():
        review = units[0]["admission_signature"]["review_signature"]
        if any(unit["admission_signature"]["review_signature"] != review for unit in units):
            raise ValueError("review batch mixed incompatible signatures")
        priority_rank, priority_route = route_priority(review["routes"])
        batch = {
            "review_batch_id": batch_id,
            "review_signature": review,
            "priority_route": priority_route,
            "priority_rank": priority_rank,
            "admission_unit_count": len(units),
            "requirement_count": sum(int(unit["member_count"]) for unit in units),
            "admission_unit_ids": sorted(str(unit["admission_unit_id"]) for unit in units),
            "proposed_context_refs": proposed_context_refs(review["modules"]),
            "authority": "BATCH_ONLY_NOT_ADMISSION_DECISION",
        }
        review_batches.append(batch)

    review_batches.sort(key=lambda batch: (
        int(batch["priority_rank"]),
        -int(batch["requirement_count"]),
        str(batch["review_batch_id"]),
    ))

    resolved_units = [unit for unit in admission_units if unit["admission_status"] == "AUTO_RESOLVED_CANONICAL"]
    context_units = [unit for unit in admission_units if unit["proposed_context_refs"]]
    context_batches = [batch for batch in review_batches if batch["proposed_context_refs"]]
    summary = {
        "requirements_total": len(rows),
        "review_batches_total": len(review_batches),
        "admission_units_total": len(admission_units),
        "auto_resolved_canonical_units": len(resolved_units),
        "auto_resolved_canonical_requirements": sum(int(unit["member_count"]) for unit in resolved_units),
        "proposed_context_batches": len(context_batches),
        "proposed_context_units": len(context_units),
        "proposed_context_requirements": sum(int(unit["member_count"]) for unit in context_units),
        "subject_review_required_units": sum(unit["admission_status"] == "SUBJECT_REVIEW_REQUIRED" for unit in admission_units),
        "subject_review_required_requirements": sum(int(unit["member_count"]) for unit in admission_units if unit["admission_status"] == "SUBJECT_REVIEW_REQUIRED"),
    }

    by_priority: dict[str, dict[str, int]] = defaultdict(lambda: {"review_batches": 0, "admission_units": 0, "requirements": 0})
    by_module: dict[str, dict[str, int]] = defaultdict(lambda: {"admission_units": 0, "requirements": 0})
    for batch in review_batches:
        by_priority[batch["priority_route"]]["review_batches"] += 1
    for unit in admission_units:
        by_priority[unit["priority_route"]]["admission_units"] += 1
        by_priority[unit["priority_route"]]["requirements"] += int(unit["member_count"])
        for module in unit["admission_signature"]["review_signature"]["modules"]:
            by_module[module]["admission_units"] += 1
            by_module[module]["requirements"] += int(unit["member_count"])

    payload: dict[str, Any] = {
        "schema_version": "1.1.0",
        "status": "OBJECT_LEVEL_SUBJECT_REVIEW_QUEUE",
        "baseline_main": BASELINE_MAIN,
        "source_requirement_state": "RUSSIAN-SOURCE-KNOWLEDGE-STATE-v1.0.json",
        "pr_139_read_only_head": PR139_HEAD,
        "review_batch_signature_fields": ["normalized_meaning", "requirement_class", "modules", "routes"],
        "admission_unit_signature_fields": ["review_signature", "source_id", "document_id", "section", "code"],
        "review_batch_authority": "WORK_BATCH_ONLY_NOT_SEMANTIC_ADMISSION",
        "auto_resolution_policy": "DIRECT_REVIEWED_REQUIREMENT_ID_TO_CANONICAL_SCHOOL_IDENTITY_ONLY",
        "module_or_keyword_auto_resolution_allowed": False,
        "summary": summary,
        "by_priority_route": dict(sorted(by_priority.items())),
        "by_module": dict(sorted(by_module.items())),
        "review_batches": review_batches,
        "admission_units": admission_units,
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    queue = build_queue()
    if args.emit:
        print(json.dumps(queue, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_OBJECT_LEVEL_REVIEW_QUEUE=PASS")
        print(f"normalized_sha256={queue['normalized_sha256']}")
        for key, value in queue["summary"].items():
            print(f"{key}={value}")
        for key, value in queue["by_priority_route"].items():
            print(f"priority[{key}].review_batches={value['review_batches']}")
            print(f"priority[{key}].admission_units={value['admission_units']}")
            print(f"priority[{key}].requirements={value['requirements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
