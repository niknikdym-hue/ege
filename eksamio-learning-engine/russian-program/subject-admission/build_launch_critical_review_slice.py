#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
OBJECT_REVIEW = PROGRAM / "object-review"
sys.path.insert(0, str(OBJECT_REVIEW))

from build_object_level_review_queue import build_queue, canonical_json  # noqa: E402

TARGET_MODULES = {"RU-PROG-13", "RU-PROG-16"}


def build_slice() -> dict[str, Any]:
    queue = build_queue()
    selected: list[dict[str, Any]] = []
    for unit in queue["admission_units"]:
        review = unit["admission_signature"]["review_signature"]
        modules = set(review["modules"])
        if not modules.intersection(TARGET_MODULES):
            continue
        selected.append(
            {
                "admission_unit_id": unit["admission_unit_id"],
                "priority_route": unit["priority_route"],
                "member_count": unit["member_count"],
                "normalized_meaning": review["normalized_meaning"],
                "requirement_class": review["requirement_class"],
                "modules": review["modules"],
                "routes": review["routes"],
                "source_id": unit["admission_signature"]["source_id"],
                "document_id": unit["admission_signature"]["document_id"],
                "section": unit["admission_signature"]["section"],
                "code": unit["admission_signature"]["code"],
                "members": [
                    {
                        "requirement_id": row["requirement_id"],
                        "page": row["page"],
                        "grades": row["grades"],
                        "confidence": row["confidence"],
                    }
                    for row in unit["members"]
                ],
                "admission_status": unit["admission_status"],
                "exact_canonical_semantic_id": unit["exact_canonical_semantic_id"],
            }
        )

    selected.sort(
        key=lambda row: (
            0 if row["priority_route"] == "EGE" else 1 if row["priority_route"] == "OGE" else 2,
            str(row["normalized_meaning"]),
            str(row["admission_unit_id"]),
        )
    )

    by_module: dict[str, dict[str, int]] = defaultdict(lambda: {"admission_units": 0, "requirements": 0})
    by_route: dict[str, dict[str, int]] = defaultdict(lambda: {"admission_units": 0, "requirements": 0})
    by_class: dict[str, dict[str, int]] = defaultdict(lambda: {"admission_units": 0, "requirements": 0})
    meanings: dict[str, list[str]] = defaultdict(list)
    requirement_ids: set[str] = set()
    for row in selected:
        for module in set(row["modules"]).intersection(TARGET_MODULES):
            by_module[module]["admission_units"] += 1
            by_module[module]["requirements"] += int(row["member_count"])
        by_route[row["priority_route"]]["admission_units"] += 1
        by_route[row["priority_route"]]["requirements"] += int(row["member_count"])
        by_class[row["requirement_class"]]["admission_units"] += 1
        by_class[row["requirement_class"]]["requirements"] += int(row["member_count"])
        meanings[str(row["normalized_meaning"])].append(str(row["admission_unit_id"]))
        for member in row["members"]:
            requirement_ids.add(str(member["requirement_id"]))

    payload: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "EXACT_REVIEW_SLICE_NOT_ADMISSION_DECISION",
        "source_queue_normalized_sha256": queue["normalized_sha256"],
        "target_modules": sorted(TARGET_MODULES),
        "selection_rule": "EXACT_MODULE_MEMBERSHIP_ONLY_NO_SEMANTIC_INFERENCE",
        "semantic_auto_mapping_allowed": False,
        "summary": {
            "admission_units": len(selected),
            "unique_requirements": len(requirement_ids),
            "normalized_meanings": len(meanings),
            "auto_resolved_canonical_units": sum(row["admission_status"] == "AUTO_RESOLVED_CANONICAL" for row in selected),
            "subject_review_required_units": sum(row["admission_status"] == "SUBJECT_REVIEW_REQUIRED" for row in selected),
        },
        "by_module": dict(sorted(by_module.items())),
        "by_priority_route": dict(sorted(by_route.items())),
        "by_requirement_class": dict(sorted(by_class.items())),
        "meaning_groups": [
            {
                "normalized_meaning": meaning,
                "admission_unit_ids": sorted(unit_ids),
                "admission_unit_count": len(unit_ids),
            }
            for meaning, unit_ids in sorted(meanings.items())
        ],
        "admission_units": selected,
    }
    payload["normalized_sha256"] = hashlib.sha256(canonical_json(payload)).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = build_slice()
    if args.output:
        Path(args.output).write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU13_RU16_EXACT_REVIEW_SLICE=PASS")
        print(f"normalized_sha256={payload['normalized_sha256']}")
        for key, value in payload["summary"].items():
            print(f"{key}={value}")
        for module, counts in payload["by_module"].items():
            print(f"{module}.admission_units={counts['admission_units']}")
            print(f"{module}.requirements={counts['requirements']}")
        print("MEANING_GROUPS_BEGIN")
        for row in payload["meaning_groups"]:
            unit_ids = ",".join(row["admission_unit_ids"])
            print(f"{row['normalized_meaning']}\t{unit_ids}")
        print("MEANING_GROUPS_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
