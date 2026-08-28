#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OBJECT_REVIEW = HERE.parent / "object-review"
sys.path.insert(0, str(OBJECT_REVIEW))
from build_object_level_review_queue import build_queue  # noqa: E402


def code_shape(code: str) -> str:
    value = code.strip()
    value = re.sub(r"\d+", "N", value)
    return value[:120]


def main() -> int:
    queue = build_queue()
    ege_units = [unit for unit in queue["admission_units"] if unit["priority_route"] == "EGE"]
    if len(ege_units) != 259:
        raise AssertionError(f"expected 259 EGE admission units, got {len(ege_units)}")
    if sum(int(unit["member_count"]) for unit in ege_units) != 275:
        raise AssertionError("expected 275 EGE requirement members")

    by_document: Counter[str] = Counter()
    by_section: Counter[str] = Counter()
    by_shape: Counter[str] = Counter()
    unique_codes: dict[str, set[str]] = defaultdict(set)
    section_codes: dict[str, set[str]] = defaultdict(set)

    for unit in ege_units:
        signature = unit["admission_signature"]
        document_id = str(signature["document_id"])
        section = str(signature["section"])
        code = str(signature["code"])
        by_document[document_id] += 1
        by_section[f"{document_id}::{section}"] += 1
        by_shape[f"{document_id}::{code_shape(code)}"] += 1
        unique_codes[document_id].add(code)
        section_codes[f"{document_id}::{section}"].add(code)

    report = {
        "ege_admission_units": len(ege_units),
        "ege_requirements": sum(int(unit["member_count"]) for unit in ege_units),
        "by_document": dict(sorted(by_document.items())),
        "by_section": dict(sorted(by_section.items())),
        "by_code_shape": dict(sorted(by_shape.items())),
        "codes_by_document": {key: sorted(values) for key, values in sorted(unique_codes.items())},
        "codes_by_section": {key: sorted(values) for key, values in sorted(section_codes.items())},
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
