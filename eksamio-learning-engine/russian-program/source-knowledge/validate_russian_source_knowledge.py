#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from build_source_semantic_crosswalk import build as build_crosswalk

HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "RUSSIAN-OFFICIAL-SOURCE-MANIFEST-v1.0.json"
REQ_INDEX_PATH = HERE / "RUSSIAN-OFFICIAL-REQUIREMENTS-INDEX-v1.0.json"
CROSSWALK_INDEX_PATH = HERE / "RUSSIAN-SOURCE-SEMANTIC-CROSSWALK-INDEX-v1.0.json"
EXPECTED_COLUMNS = [
    "record_id", "document_ref", "page", "code", "section_ref", "class_ref",
    "grades_ref", "routes_ref", "module_mask", "meaning_ref", "confidence_ref", "status_ref",
]
CANONICAL_SOURCES = {
    "EDSOO-RU-5-9-2025",
    "EDSOO-RU-10-11-BASIC-2025",
    "FIPI-OGE-RU-2026-FINAL",
    "FIPI-EGE-RU-2026-FINAL",
}
FORBIDDEN_SOURCE = "FIPI-OGE-RU-2027-PROJECT"
EXPECTED_REQUIREMENTS = 1400
DECLARED_EXTRACTION_HASH = "92edb2734612733d5b5d7e76b4b19fcc74447134c17ae2fd8c7f7f036bd4e245"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def load_rows(index: dict[str, object]) -> list[list[object]]:
    rows: list[list[object]] = []
    shards = index.get("shards", [])
    if len(shards) != 14:
        raise AssertionError("expected exactly 14 requirement shards")
    for shard in shards:
        payload = json.loads((HERE / str(shard["path"])).read_text(encoding="utf-8"))
        if payload.get("columns") != EXPECTED_COLUMNS:
            raise AssertionError(f"requirement shard schema drift: {shard['path']}")
        records = payload.get("records", [])
        if len(records) != int(shard["record_count"]) or len(records) != 100:
            raise AssertionError(f"requirement shard count drift: {shard['path']}")
        rows.extend(records)
    return rows


def validate_manifest(manifest: dict[str, object]) -> None:
    if set(manifest.get("canonical_launch_sources", [])) != CANONICAL_SOURCES:
        raise AssertionError("canonical launch source set drift")
    if manifest.get("forbidden_launch_source") != FORBIDDEN_SOURCE:
        raise AssertionError("2027 provisional source guard missing")
    if int(manifest.get("commercial_textbook_ingestion", -1)) != 0:
        raise AssertionError("commercial textbook ingestion must remain zero")
    documents = manifest.get("documents", [])
    if len(documents) != 8:
        raise AssertionError("expected exactly 8 concrete launch documents")
    seen: set[str] = set()
    for doc in documents:
        source_id = str(doc.get("canonical_source_id", ""))
        if source_id not in CANONICAL_SOURCES or source_id == FORBIDDEN_SOURCE:
            raise AssertionError(f"nonlaunch source admitted: {source_id}")
        document_id = str(doc.get("document_id", ""))
        if not document_id or document_id in seen:
            raise AssertionError(f"duplicate/missing document id: {document_id}")
        seen.add(document_id)
        if not SHA_RE.fullmatch(str(doc.get("sha256", ""))):
            raise AssertionError(f"missing/invalid source fingerprint: {document_id}")
        if int(doc.get("size_bytes", 0)) <= 0:
            raise AssertionError(f"invalid source size: {document_id}")
        if "verified Source Archive Drive file" not in str(doc.get("resolution_path", "")):
            raise AssertionError(f"non-deterministic source resolution: {document_id}")
        if not str(doc.get("public_authority_url", "")).startswith("https://"):
            raise AssertionError(f"missing official authority URL: {document_id}")
        filename = str(doc.get("filename", "")).casefold()
        if any(token in filename for token in ("ладыжен", "бархударов", "рыбченкова", "гусарова")):
            raise AssertionError("commercial textbook bytes entered source manifest")


def normalized_rows_hash(rows: list[list[object]]) -> str:
    raw = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_requirements(index: dict[str, object], rows: list[list[object]]) -> tuple[dict[str, int], dict[str, int], str]:
    if int(index.get("counts", {}).get("requirements_total", 0)) != EXPECTED_REQUIREMENTS:
        raise AssertionError("requirements_total drift")
    if str(index.get("normalized_content_sha256")) != DECLARED_EXTRACTION_HASH:
        raise AssertionError("declared extraction hash drift")
    if len(rows) != EXPECTED_REQUIREMENTS:
        raise AssertionError("not all official requirements materialized")

    catalogs = index["catalogs"]
    for meaning in catalogs["meanings"]:
        text = str(meaning)
        if not text.strip() or "\n" in text or len(text) > 320:
            raise AssertionError("normalized meaning must be concise Eksamio-owned wording")

    lookup_specs = (
        (1, "documents", "document"), (4, "sections", "section"), (5, "classes", "class"),
        (6, "grades", "grade"), (7, "routes", "route"), (9, "meanings", "meaning"),
        (10, "confidences", "confidence"), (11, "statuses", "status"),
    )
    seen: set[str] = set()
    by_source: Counter[str] = Counter()
    by_module: Counter[str] = Counter()
    for row in rows:
        if len(row) != 12:
            raise AssertionError("requirement row schema drift")
        record_id = str(row[0])
        if record_id in seen:
            raise AssertionError(f"duplicate requirement: {record_id}")
        seen.add(record_id)
        for position, catalog_name, label in lookup_specs:
            value = row[position]
            catalog = catalogs[catalog_name]
            if not isinstance(value, int) or value < 0 or value >= len(catalog):
                raise AssertionError(f"invalid {label} ref: {record_id}")
        page, code, module_mask = row[2], row[3], row[8]
        if not isinstance(page, int) or page <= 0:
            raise AssertionError(f"missing precise page locator: {record_id}")
        if not isinstance(code, str) or not code.strip():
            raise AssertionError(f"missing code/locator: {record_id}")
        if not isinstance(module_mask, int) or module_mask <= 0 or module_mask >= (1 << 16):
            raise AssertionError(f"unknown/zero module: {record_id}")
        source_id = str(catalogs["documents"][row[1]]["source_id"])
        if source_id not in CANONICAL_SOURCES:
            raise AssertionError(f"requirement uses nonlaunch source: {record_id}")
        by_source[source_id] += 1
        for bit in range(16):
            if module_mask & (1 << bit):
                by_module[f"RU-PROG-{bit + 1:02d}"] += 1

    expected_modules = {f"RU-PROG-{number:02d}" for number in range(1, 17)}
    if set(by_module) != expected_modules or any(by_module[module] <= 0 for module in expected_modules):
        raise AssertionError("every launch module must have nonzero official requirements")
    if dict(sorted(by_module.items())) != dict(sorted(index["counts"]["by_module"].items())):
        raise AssertionError("module accounting drift")
    if dict(sorted(by_source.items())) != dict(sorted(index["counts"]["by_source"].items())):
        raise AssertionError("source accounting drift")

    first = normalized_rows_hash(rows)
    second = normalized_rows_hash(copy.deepcopy(rows))
    if first != second:
        raise AssertionError("normalized requirement package is nondeterministic")
    return dict(by_source), dict(by_module), first


def validate_crosswalk(index: dict[str, object]) -> dict[str, object]:
    if index.get("generator") != "build_source_semantic_crosswalk.py":
        raise AssertionError("executable crosswalk authority missing")
    if int(index.get("record_count", 0)) != EXPECTED_REQUIREMENTS:
        raise AssertionError("crosswalk record count drift")
    if index.get("pr_139_read_only_head") != "f16884ec4f8992ee9ad01c2930c42349f579bc70":
        raise AssertionError("PR #139 evidence head drift")
    if index.get("classification_policy", {}).get("canonical_semantic_ids_emitted") is not False:
        raise AssertionError("source lane must not self-admit semantic ids")
    for ref in index["catalogs"]["content_refs"]:
        if ref.get("ref_state") == "PR_139_ONLY_PROPOSED" and ref.get("pr_head") != index["pr_139_read_only_head"]:
            raise AssertionError("proposed content ref not pinned to exact PR #139 head")
    first = build_crosswalk()
    second = build_crosswalk()
    if first != second or first["record_count"] != EXPECTED_REQUIREMENTS:
        raise AssertionError("crosswalk generation is incomplete or nondeterministic")
    if sum(first["counts"].values()) != EXPECTED_REQUIREMENTS:
        raise AssertionError("crosswalk accounting drift")
    if "COVERED_CANONICAL" in first["counts"]:
        raise AssertionError("source lane falsely claimed exact canonical ownership")
    return first


def expect_failure(fn, label: str) -> None:
    try:
        fn()
    except AssertionError:
        return
    raise AssertionError(f"negative test did not fail: {label}")


def negative_tests(manifest: dict[str, object], index: dict[str, object], rows: list[list[object]], crosswalk_index: dict[str, object]) -> None:
    bad = copy.deepcopy(manifest)
    bad["canonical_launch_sources"].append(FORBIDDEN_SOURCE)
    expect_failure(lambda: validate_manifest(bad), "provisional 2027 source")

    bad = copy.deepcopy(manifest)
    bad["documents"][0]["sha256"] = "0" * 63
    expect_failure(lambda: validate_manifest(bad), "source fingerprint")

    bad_rows = copy.deepcopy(rows)
    bad_rows[0][2] = 0
    expect_failure(lambda: validate_requirements(index, bad_rows), "missing locator")

    bad_rows = copy.deepcopy(rows)
    bad_rows[0][8] = 1 << 16
    expect_failure(lambda: validate_requirements(index, bad_rows), "unknown module")

    bad = copy.deepcopy(crosswalk_index)
    bad["classification_policy"]["canonical_semantic_ids_emitted"] = True
    expect_failure(lambda: validate_crosswalk(bad), "false canonicalization")

    bad = copy.deepcopy(manifest)
    bad["commercial_textbook_ingestion"] = 1
    expect_failure(lambda: validate_manifest(bad), "commercial textbook ingestion")

    bad_index = copy.deepcopy(index)
    bad_index["catalogs"]["meanings"][0] = "x" * 400
    expect_failure(lambda: validate_requirements(bad_index, rows), "long copied prose guard")

    without_module_16 = [row for row in rows if not (int(row[8]) & (1 << 15))]
    bad_index = copy.deepcopy(index)
    bad_index["counts"]["requirements_total"] = len(without_module_16)
    bad_index["counts"]["by_source"] = dict(Counter(str(bad_index["catalogs"]["documents"][row[1]]["source_id"]) for row in without_module_16))
    bad_index["counts"]["by_module"] = {
        module: count for module, count in bad_index["counts"]["by_module"].items() if module != "RU-PROG-16"
    }
    expect_failure(lambda: validate_requirements(bad_index, without_module_16), "zero-requirements module")


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    index = json.loads(REQ_INDEX_PATH.read_text(encoding="utf-8"))
    crosswalk_index = json.loads(CROSSWALK_INDEX_PATH.read_text(encoding="utf-8"))
    rows = load_rows(index)
    validate_manifest(manifest)
    by_source, _by_module, requirement_hash = validate_requirements(index, rows)
    crosswalk = validate_crosswalk(crosswalk_index)
    negative_tests(manifest, index, rows, crosswalk_index)

    print("RUSSIAN_OFFICIAL_SOURCE_KNOWLEDGE=PASS")
    print(f"requirements={len(rows)}")
    print("launch_modules_with_requirements=16")
    print(f"declared_extraction_sha256={index['normalized_content_sha256']}")
    print(f"runtime_requirement_package_sha256={requirement_hash}")
    print(f"crosswalk_normalized_sha256={crosswalk['normalized_sha256']}")
    for source_id in sorted(by_source):
        print(f"source[{source_id}]={by_source[source_id]}")
    for status, count in sorted(crosswalk["counts"].items()):
        print(f"crosswalk[{status}]={count}")
    print("negative_tests=PASS")
    print("commercial_textbook_bytes_ingested=0")
    print("canonical_semantic_ids_admitted=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
