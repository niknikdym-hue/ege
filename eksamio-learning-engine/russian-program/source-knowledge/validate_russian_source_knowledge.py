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

CANONICAL_SOURCES = {
    "EDSOO-RU-5-9-2025",
    "EDSOO-RU-10-11-BASIC-2025",
    "FIPI-OGE-RU-2026-FINAL",
    "FIPI-EGE-RU-2026-FINAL",
}
FORBIDDEN_SOURCE = "FIPI-OGE-RU-2027-PROJECT"
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_REQUIREMENTS = 1400
EXPECTED_DECLARED_NORMALIZED_SHA = "92edb2734612733d5b5d7e76b4b19fcc74447134c17ae2fd8c7f7f036bd4e245"


def _load_rows(index: dict[str, object]) -> list[list[object]]:
    rows: list[list[object]] = []
    for shard in index["shards"]:
        path = HERE / shard["path"]
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != shard["sha256"]:
            raise AssertionError(f"fingerprint drift: {shard['path']}")
        payload = json.loads(raw)
        if len(payload["records"]) != shard["record_count"]:
            raise AssertionError(f"count drift: {shard['path']}")
        rows.extend(payload["records"])
    return rows


def validate_manifest(manifest: dict[str, object]) -> None:
    if set(manifest["canonical_launch_sources"]) != CANONICAL_SOURCES:
        raise AssertionError("canonical launch source set drift")
    if manifest.get("forbidden_launch_source") != FORBIDDEN_SOURCE:
        raise AssertionError("2027 provisional guard missing")
    if int(manifest.get("commercial_textbook_ingestion", -1)) != 0:
        raise AssertionError("commercial textbook ingestion must remain zero")
    docs = manifest.get("documents", [])
    if len(docs) != 8:
        raise AssertionError("expected exactly 8 concrete launch documents")
    ids: set[str] = set()
    for doc in docs:
        source_id = str(doc["canonical_source_id"])
        if source_id == FORBIDDEN_SOURCE or source_id not in CANONICAL_SOURCES:
            raise AssertionError(f"forbidden/noncanonical source admitted: {source_id}")
        doc_id = str(doc["document_id"])
        if doc_id in ids:
            raise AssertionError(f"duplicate document id: {doc_id}")
        ids.add(doc_id)
        if not SHA_RE.fullmatch(str(doc.get("sha256", ""))):
            raise AssertionError(f"missing/invalid document fingerprint: {doc_id}")
        if int(doc.get("size_bytes", 0)) <= 0:
            raise AssertionError(f"invalid document size: {doc_id}")
        resolution = str(doc.get("resolution_path", ""))
        if "verified Source Archive Drive file" not in resolution:
            raise AssertionError(f"non-deterministic resolution path: {doc_id}")
        if not str(doc.get("public_authority_url", "")).startswith("https://"):
            raise AssertionError(f"missing public authority URL: {doc_id}")
        filename = str(doc.get("filename", "")).casefold()
        if any(token in filename for token in ("ладыжен", "бархударов", "рыбченкова", "гусарова")):
            raise AssertionError("commercial textbook bytes must not enter source manifest")


def validate_requirements(index: dict[str, object], rows: list[list[object]]) -> tuple[dict[str, int], dict[str, int], str]:
    if int(index["counts"]["requirements_total"]) != EXPECTED_REQUIREMENTS:
        raise AssertionError("requirements_total drift")
    if str(index.get("normalized_content_sha256")) != EXPECTED_DECLARED_NORMALIZED_SHA:
        raise AssertionError("declared normalized source hash drift")
    if len(rows) != EXPECTED_REQUIREMENTS:
        raise AssertionError("not all official requirements materialized")

    catalogs = index["catalogs"]
    doc_catalog = catalogs["documents"]
    meanings = catalogs["meanings"]
    sections = catalogs["sections"]
    classes = catalogs["classes"]
    grades = catalogs["grades"]
    routes = catalogs["routes"]
    confidences = catalogs["confidences"]
    statuses = catalogs["statuses"]

    for meaning in meanings:
        text = str(meaning)
        if not text.strip() or "\n" in text or len(text) > 320:
            raise AssertionError("normalized meaning must stay concise and Eksamio-owned")

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
        doc_ref, page, code, section_ref, class_ref, grade_ref, route_ref, module_mask, meaning_ref, confidence_ref, status_ref = row[1:]
        for value, catalog, label in (
            (doc_ref, doc_catalog, "document"),
            (section_ref, sections, "section"),
            (class_ref, classes, "class"),
            (grade_ref, grades, "grade"),
            (route_ref, routes, "route"),
            (meaning_ref, meanings, "meaning"),
            (confidence_ref, confidences, "confidence"),
            (status_ref, statuses, "status"),
        ):
            if not isinstance(value, int) or value < 0 or value >= len(catalog):
                raise AssertionError(f"invalid {label} ref in {record_id}")
        if not isinstance(page, int) or page <= 0:
            raise AssertionError(f"missing precise page locator: {record_id}")
        if not isinstance(code, str) or not code.strip():
            raise AssertionError(f"missing code/locator: {record_id}")
        if not isinstance(module_mask, int) or module_mask <= 0 or module_mask >= (1 << 16):
            raise AssertionError(f"unknown/zero module mask: {record_id}")
        source_id = str(doc_catalog[doc_ref]["source_id"])
        if source_id not in CANONICAL_SOURCES:
            raise AssertionError(f"requirement uses nonlaunch source: {record_id}")
        by_source[source_id] += 1
        for bit in range(16):
            if module_mask & (1 << bit):
                by_module[f"RU-PROG-{bit + 1:02d}"] += 1

    expected_modules = {f"RU-PROG-{n:02d}" for n in range(1, 17)}
    if set(by_module) != expected_modules or any(by_module[module] <= 0 for module in expected_modules):
        raise AssertionError("every launch module must have nonzero official requirements")
    if dict(sorted(by_module.items())) != dict(sorted(index["counts"]["by_module"].items())):
        raise AssertionError("module accounting drift")
    if dict(sorted(by_source.items())) != dict(sorted(index["counts"]["by_source"].items())):
        raise AssertionError("source accounting drift")

    canonical = json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    package_hash = hashlib.sha256(canonical).hexdigest()
    # Same in-memory source package must deterministically hash identically on a repeated pass.
    package_hash_2 = hashlib.sha256(json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
    if package_hash != package_hash_2:
        raise AssertionError("requirement package is nondeterministic")
    return dict(by_source), dict(by_module), package_hash


def validate_crosswalk(index: dict[str, object]) -> dict[str, object]:
    if index.get("generator") != "build_source_semantic_crosswalk.py":
        raise AssertionError("executable crosswalk authority missing")
    if int(index.get("record_count", 0)) != EXPECTED_REQUIREMENTS:
        raise AssertionError("crosswalk expected count drift")
    if index.get("pr_139_read_only_head") != "f16884ec4f8992ee9ad01c2930c42349f579bc70":
        raise AssertionError("PR #139 evidence head drift")
    if index.get("classification_policy", {}).get("canonical_semantic_ids_emitted") is not False:
        raise AssertionError("source lane must never self-admit canonical semantic ids")
    for ref in index["catalogs"]["content_refs"]:
        if ref.get("ref_state") == "PR_139_ONLY_PROPOSED" and ref.get("pr_head") != index["pr_139_read_only_head"]:
            raise AssertionError("proposed content ref lacks exact PR #139 head")

    first = build_crosswalk()
    second = build_crosswalk()
    if first["record_count"] != EXPECTED_REQUIREMENTS or second["record_count"] != EXPECTED_REQUIREMENTS:
        raise AssertionError("crosswalk does not classify every requirement")
    if first["normalized_sha256"] != second["normalized_sha256"] or first["records"] != second["records"]:
        raise AssertionError("crosswalk generation is nondeterministic")
    if sum(first["counts"].values()) != EXPECTED_REQUIREMENTS:
        raise AssertionError("crosswalk status accounting drift")
    if "COVERED_CANONICAL" in first["counts"]:
        raise AssertionError("this lane has not proved exact canonical ownership")
    return first


def negative_tests(manifest: dict[str, object], req_index: dict[str, object], rows: list[list[object]], crosswalk_index: dict[str, object]) -> None:
    bad = copy.deepcopy(manifest)
    bad["canonical_launch_sources"].append(FORBIDDEN_SOURCE)
    try:
        validate_manifest(bad)
        raise AssertionError("2027 provisional source negative test did not fail")
    except AssertionError as exc:
        if "negative test" in str(exc):
            raise

    bad = copy.deepcopy(manifest)
    bad["documents"][0]["sha256"] = "0" * 63
    try:
        validate_manifest(bad)
        raise AssertionError("fingerprint negative test did not fail")
    except AssertionError as exc:
        if "negative test" in str(exc):
            raise

    bad_rows = copy.deepcopy(rows)
    bad_rows[0][2] = 0
    try:
        validate_requirements(req_index, bad_rows)
        raise AssertionError("locator negative test did not fail")
    except AssertionError as exc:
        if "negative test" in str(exc):
            raise

    bad_rows = copy.deepcopy(rows)
    bad_rows[0][8] = 1 << 16
    try:
        validate_requirements(req_index, bad_rows)
        raise AssertionError("unknown module negative test did not fail")
    except AssertionError as exc:
        if "negative test" in str(exc):
            raise

    bad = copy.deepcopy(crosswalk_index)
    bad["classification_policy"]["canonical_semantic_ids_emitted"] = True
    try:
        validate_crosswalk(bad)
        raise AssertionError("canonicalization negative test did not fail")
    except AssertionError as exc:
        if "negative test" in str(exc):
            raise

    bad = copy.deepcopy(manifest)
    bad["commercial_textbook_ingestion"] = 1
    try:
        validate_manifest(bad)
        raise AssertionError("commercial ingestion negative test did not fail")
    except AssertionError as exc:
        if "negative test" in str(exc):
            raise

    bad_index = copy.deepcopy(req_index)
    bad_index["catalogs"]["meanings"][0] = "x" * 400
    try:
        validate_requirements(bad_index, rows)
        raise AssertionError("long prose negative test did not fail")
    except AssertionError as exc:
        if "negative test" in str(exc):
            raise

    fake_module_counts = {f"RU-PROG-{n:02d}": 1 for n in range(1, 17)}
    fake_module_counts["RU-PROG-16"] = 0
    if all(fake_module_counts.values()):
        raise AssertionError("zero-module negative test did not fail")


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    req_index = json.loads(REQ_INDEX_PATH.read_text(encoding="utf-8"))
    crosswalk_index = json.loads(CROSSWALK_INDEX_PATH.read_text(encoding="utf-8"))
    rows = _load_rows(req_index)

    validate_manifest(manifest)
    by_source, by_module, package_hash = validate_requirements(req_index, rows)
    crosswalk = validate_crosswalk(crosswalk_index)
    negative_tests(manifest, req_index, rows, crosswalk_index)

    print("RUSSIAN_OFFICIAL_SOURCE_KNOWLEDGE=PASS")
    print(f"requirements={len(rows)}")
    print("launch_modules_with_requirements=16")
    print(f"declared_normalized_sha256={req_index['normalized_content_sha256']}")
    print(f"runtime_requirement_package_sha256={package_hash}")
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
