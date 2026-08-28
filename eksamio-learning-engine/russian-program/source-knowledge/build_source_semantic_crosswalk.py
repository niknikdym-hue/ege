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

# These refs are context only. Module overlap may point reviewers toward current/proposed
# learner material, but it must never be interpreted as object-level coverage.
PROPOSED_MODULE_TO_REF = {1: 9, 2: 4, 3: 1, 4: 10, 5: 5, 6: 6, 7: 8, 11: 0, 12: 2, 15: 3}
CANONICAL_MODULES = {8, 10}
CANONICAL_INVENTORY_REF = 7
EXPECTED_COLUMNS = [
    "record_id", "document_ref", "page", "code", "section_ref", "class_ref",
    "grades_ref", "routes_ref", "module_mask", "meaning_ref", "confidence_ref", "status_ref",
]


def decode_modules(mask: int) -> tuple[int, ...]:
    if not isinstance(mask, int) or mask <= 0 or mask >= (1 << 16):
        raise ValueError(f"invalid module mask: {mask!r}")
    return tuple(index + 1 for index in range(16) if mask & (1 << index))


def load_requirement_rows() -> tuple[dict[str, object], list[list[object]]]:
    index = json.loads(REQ_INDEX_PATH.read_text(encoding="utf-8"))
    rows: list[list[object]] = []
    for shard in index["shards"]:
        payload = json.loads((HERE / shard["path"]).read_text(encoding="utf-8"))
        if payload["columns"] != EXPECTED_COLUMNS:
            raise ValueError(f"requirement shard schema drift: {shard['path']}")
        if len(payload["records"]) != shard["record_count"]:
            raise ValueError(f"requirement shard count drift: {shard['path']}")
        rows.extend(payload["records"])
    return index, rows


def review_context_refs(row: list[object]) -> list[int]:
    modules = set(decode_modules(int(row[8])))
    refs: list[int] = []
    for module in sorted(modules):
        ref = PROPOSED_MODULE_TO_REF.get(module)
        if ref is not None and ref not in refs:
            refs.append(ref)
    if modules & CANONICAL_MODULES:
        refs.append(CANONICAL_INVENTORY_REF)
    return refs


def classify(row: list[object]) -> tuple[str, list[int]]:
    # Issue #152 requires requirement-level crosswalk truth. PR #139 source_provenance
    # currently establishes module/program scope, not an exact locator -> semantic/content
    # identity for each of the 1400 normalized official requirements. Therefore module
    # overlap is insufficient to claim COVERED_PROPOSED, PARTIAL, MISSING_CONTENT or
    # MISSING_SEMANTIC_IDENTITY. Until Russian subject authority performs object-level
    # admission, every requirement remains explicitly SUBJECT_REVIEW_REQUIRED.
    return "SUBJECT_REVIEW_REQUIRED", review_context_refs(row)


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
        status, refs = classify(row)
        if status not in status_to_ref:
            raise ValueError(f"crosswalk index lacks status: {status}")
        counts[status] += 1
        records.append([record_id, status_to_ref[status], refs])
    if len(records) != int(req_index["counts"]["requirements_total"]):
        raise ValueError("crosswalk does not cover every requirement")
    canonical = json.dumps(records, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": "1.1.0",
        "columns": ["record_id", "status_ref", "content_ref_refs"],
        "records": records,
        "counts": dict(sorted(counts.items())),
        "normalized_sha256": hashlib.sha256(canonical).hexdigest(),
        "record_count": len(records),
        "coverage_claims_emitted": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build()
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        print("RUSSIAN_SOURCE_SEMANTIC_CROSSWALK=PASS")
        print(f"records={result['record_count']}")
        print(f"normalized_sha256={result['normalized_sha256']}")
        print(f"coverage_claims_emitted={result['coverage_claims_emitted']}")
        for key, value in result["counts"].items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
