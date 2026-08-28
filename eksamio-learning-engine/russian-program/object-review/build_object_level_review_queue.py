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


def module_numbers(mask: int) -> list[int]:
    return [bit + 1 for bit in range(16) if mask & (1 << bit)]


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
        # The auto-resolution boundary is deliberately strict: the existing authority
        # must directly name the newly derived requirement ID as its source object.
        for key in ("source_id", "source_object_key"):
            source_key = row.get(key)
            if isinstance(source_key, str) and source_key.startswith("RSK-"):
                direct[source_key].add(str(target))
        for provenance_ref in row.get("provenance_refs") or []:
            if isinstance(provenance_ref, str) and provenance_ref.startswith("RSK-"):
                direct[provenance_ref].add(str(target))
    return canonical_targets, direct


def group_signature(row: list[Any], index: dict[str, Any]) -> dict[str, Any]:
    catalogs = index["catalogs"]
    return {
        "normalized_meaning": str(catalogs["meanings"][int(row[9])]),
        "requirement_class": str(catalogs["classes"][int(row[5])]),
        "modules": decode_modules(int(row[8])),
        "routes": sorted(str(v) for v in catalogs["routes"][int(row[7])]),
    }


def review_group_id(signature: dict[str, Any]) -> str:
    return "RRG-" + hashlib.sha256(canonical_json(signature)).hexdigest()[:20]


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


def exact_group_resolution(member_ids: list[str], direct: dict[str, set[str]], canonical_targets: set[str]) -> str | None:
    targets: set[str] = set()
    for requirement_id in member_ids:
        direct_targets = direct.get(requirement_id, set())
        if len(direct_targets) != 1:
            return None
        target = next(iter(direct_targets))
        if target not in canonical_targets:
            return None
        targets.add(target)
    if len(targets) != 1:
        return None
    return next(iter(targets))


def build_queue() -> dict[str, Any]:
    index, rows = load_requirements()
    catalogs = index["catalogs"]
    canonical_targets, direct = load_exact_canonical_authority()

    buckets: dict[bytes, list[list[Any]]] = defaultdict(list)
    signatures: dict[bytes, dict[str, Any]] = {}
    for row in rows:
        signature = group_signature(row, index)
        key = canonical_json(signature)
        buckets[key].append(row)
        signatures[key] = signature

    groups: list[dict[str, Any]] = []
    for key, members in buckets.items():
        signature = signatures[key]
        member_objects: list[dict[str, Any]] = []
        grades: set[str] = set()
        source_ids: set[str] = set()
        document_ids: set[str] = set()
        member_ids: list[str] = []

        for row in sorted(members, key=lambda item: str(item[0])):
            requirement_id = str(row[0])
            document = catalogs["documents"][int(row[1])]
            source_id = str(document["source_id"])
            if source_id == FORBIDDEN_SOURCE:
                raise ValueError("provisional 2027 source entered object review queue")
            row_grades = sorted(str(v) for v in catalogs["grades"][int(row[6])])
            grades.update(row_grades)
            source_ids.add(source_id)
            document_ids.add(str(document["document_id"]))
            member_ids.append(requirement_id)
            member_objects.append({
                "requirement_id": requirement_id,
                "source_id": source_id,
                "document_id": str(document["document_id"]),
                "source_sha256": str(document["sha256"]),
                "page": int(row[2]),
                "code": str(row[3]),
                "section": str(catalogs["sections"][int(row[4])]),
                "grades": row_grades,
                "confidence": str(catalogs["confidences"][int(row[10])]),
            })

        exact_target = exact_group_resolution(member_ids, direct, canonical_targets)
        priority_rank, priority_route = route_priority(signature["routes"])
        contexts = proposed_context_refs(signature["modules"])
        group = {
            "review_group_id": review_group_id(signature),
            "signature": signature,
            "priority_route": priority_route,
            "priority_rank": priority_rank,
            "member_count": len(member_objects),
            "grades_represented": sorted(grades, key=lambda value: int(value) if value.isdigit() else 999),
            "source_ids": sorted(source_ids),
            "document_ids": sorted(document_ids),
            "members": member_objects,
            "exact_canonical_semantic_id": exact_target,
            "admission_status": "AUTO_RESOLVED_CANONICAL" if exact_target else "SUBJECT_REVIEW_REQUIRED",
            "proposed_context_refs": contexts,
        }
        groups.append(group)

    groups.sort(key=lambda group: (
        int(group["priority_rank"]),
        -int(group["member_count"]),
        str(group["review_group_id"]),
    ))

    resolved_groups = [g for g in groups if g["admission_status"] == "AUTO_RESOLVED_CANONICAL"]
    proposed_context_groups = [g for g in groups if g["proposed_context_refs"]]
    summary = {
        "requirements_total": len(rows),
        "review_groups_total": len(groups),
        "auto_resolved_canonical_groups": len(resolved_groups),
        "auto_resolved_canonical_requirements": sum(int(g["member_count"]) for g in resolved_groups),
        "proposed_context_groups": len(proposed_context_groups),
        "proposed_context_requirements": sum(int(g["member_count"]) for g in proposed_context_groups),
        "subject_review_required_groups": sum(g["admission_status"] == "SUBJECT_REVIEW_REQUIRED" for g in groups),
        "subject_review_required_requirements": sum(int(g["member_count"]) for g in groups if g["admission_status"] == "SUBJECT_REVIEW_REQUIRED"),
    }

    by_priority = defaultdict(lambda: {"groups": 0, "requirements": 0})
    by_module = defaultdict(lambda: {"groups": 0, "requirements": 0})
    for group in groups:
        by_priority[group["priority_route"]]["groups"] += 1
        by_priority[group["priority_route"]]["requirements"] += int(group["member_count"])
        for module in group["signature"]["modules"]:
            by_module[module]["groups"] += 1
            by_module[module]["requirements"] += int(group["member_count"])

    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "status": "OBJECT_LEVEL_SUBJECT_REVIEW_QUEUE",
        "baseline_main": BASELINE_MAIN,
        "source_requirement_state": "RUSSIAN-SOURCE-KNOWLEDGE-STATE-v1.0.json",
        "pr_139_read_only_head": PR139_HEAD,
        "group_signature_fields": ["normalized_meaning", "requirement_class", "modules", "routes"],
        "auto_resolution_policy": "DIRECT_REVIEWED_REQUIREMENT_ID_TO_CANONICAL_SCHOOL_IDENTITY_ONLY",
        "module_or_keyword_auto_resolution_allowed": False,
        "summary": summary,
        "by_priority_route": dict(sorted(by_priority.items())),
        "by_module": dict(sorted(by_module.items())),
        "groups": groups,
    }
    digest_input = {key: value for key, value in payload.items() if key != "normalized_sha256"}
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(digest_input)).hexdigest()
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
            print(f"priority[{key}].groups={value['groups']}")
            print(f"priority[{key}].requirements={value['requirements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
