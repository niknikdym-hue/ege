#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQ_INDEX_PATH = HERE / "RUSSIAN-OFFICIAL-REQUIREMENTS-INDEX-v1.0.json"
CROSSWALK_INDEX_PATH = HERE / "RUSSIAN-SOURCE-SEMANTIC-CROSSWALK-INDEX-v1.0.json"

PROPOSED_MODULE_TO_REF = {
    1: 9,
    2: 4,
    3: 1,
    4: 10,
    5: 5,
    6: 6,
    7: 8,
    11: 0,
    12: 2,
    15: 3,
}
CANONICAL_MODULES = {8, 10}
CANONICAL_INVENTORY_REF = 7
UNRESOLVED_CONTENT_MODULES = {9, 13, 14, 16}
MISSING_IDENTITY_MODULES = {1, 4, 5, 15}
FORMAT_CLASSES = {"exam_format_constraint", "scoring_or_format_constraint"}


def decode_modules(mask: int) -> tuple[int, ...]:
    if not isinstance(mask, int) or mask <= 0 or mask >= (1 << 16):
        raise ValueError(f"invalid module mask: {mask!r}")
    return tuple(index + 1 for index in range(16) if mask & (1 << index))


def load_requirement_rows() -> tuple[dict[str, object], list[list[object]]]:
    index = json.loads(REQ_INDEX_PATH.read_text(encoding="utf-8"))
    rows: list[list[object]] = []
    for shard in index["shards"]:
        path = HERE / shard["path"]
        raw = path.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != shard["sha256"]:
            raise ValueError(f"requirement shard fingerprint drift: {shard['path']}")
        payload = json.loads(raw)
        if payload["columns"] != [
            "record_id", "document_ref", "page", "code", "section_ref", "class_ref",
            "grades_ref", "routes_ref", "module_mask", "meaning_ref", "confidence_ref", "status_ref",
        ]:
            raise ValueError(f"requirement shard schema drift: {shard['path']}")
        if len(payload["records"]) != shard["record_count"]:
            raise ValueError(f"requirement shard count drift: {shard['path']}")
        rows.extend(payload["records"])
    return index, rows


def classify(row: list[object], req_index: dict[str, object]) -> tuple[str, list[int]]:
    class_ref = int(row[5])
    module_mask = int(row[8])
    classes = req_index["catalogs"]["classes"]
    class_name = str(classes[class_ref])
    modules = set(decode_modules(module_mask))

    refs: list[int] = []
    for module in sorted(modules):
        ref = PROPOSED_MODULE_TO_REF.get(module)
        if ref is not None and ref not in refs:
            refs.append(ref)
    if modules & CANONICAL_MODULES:
        refs.append(CANONICAL_INVENTORY_REF)

    # Exam-level format/scoring rows are route constraints, not semantic mastery claims.
    if class_name in FORMAT_CLASSES:
        return "SUBJECT_REVIEW_REQUIRED", refs

    # Modules whose current main + PR #139 do not provide an admitted/precise learner-content
    # binding remain explicit gaps. Existing broad trainer material is not silently counted.
    if modules & UNRESOLVED_CONTENT_MODULES:
        return ("PARTIAL" if refs else "MISSING_CONTENT"), refs

    # PR #139 contains learner material for these modules, but its ru-* identities are still
    # PROPOSED_NOT_CANONICAL. Therefore content presence must not be promoted to canonical mastery.
    if modules & MISSING_IDENTITY_MODULES:
        return "MISSING_SEMANTIC_IDENTITY", refs

    proposed_modules = set(PROPOSED_MODULE_TO_REF)
    if modules <= proposed_modules:
        return "COVERED_PROPOSED", refs
    if modules <= CANONICAL_MODULES:
        return "PARTIAL", refs
    if refs:
        return "PARTIAL", refs
    return "SUBJECT_REVIEW_REQUIRED", refs


def build() -> dict[str, object]:
    req_index, req_rows = load_requirement_rows()
    crosswalk_index = json.loads(CROSSWALK_INDEX_PATH.read_text(encoding="utf-8"))
    statuses = crosswalk_index["catalogs"]["statuses"]
    status_to_ref = {status: index for index, status in enumerate(statuses)}

    records: list[list[object]] = []
    counts: Counter[str] = Counter()
    seen: set[str] = set()
    for row in req_rows:
        record_id = str(row[0])
        if record_id in seen:
            raise ValueError(f"duplicate requirement record: {record_id}")
        seen.add(record_id)
        status, refs = classify(row, req_index)
        if status not in status_to_ref:
            raise ValueError(f"crosswalk index lacks status: {status}")
        counts[status] += 1
        records.append([record_id, status_to_ref[status], refs])

    if len(records) != int(req_index["counts"]["requirements_total"]):
        raise ValueError("crosswalk does not cover every requirement")

    canonical = json.dumps(records, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    normalized_sha256 = hashlib.sha256(canonical).hexdigest()
    return {
        "schema_version": "1.0.0",
        "columns": ["record_id", "status_ref", "content_ref_refs"],
        "records": records,
        "counts": dict(sorted(counts.items())),
        "normalized_sha256": normalized_sha256,
        "record_count": len(records),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true", help="emit complete generated crosswalk")
    args = parser.parse_args()
    result = build()
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print("RUSSIAN_SOURCE_SEMANTIC_CROSSWALK=PASS")
        print(f"records={result['record_count']}")
        print(f"normalized_sha256={result['normalized_sha256']}")
        for key, value in result["counts"].items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
