#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    matrix = json.loads((HERE / "RUSSIAN-OFFICIAL-SOURCE-COVERAGE-v1.0.json").read_text(encoding="utf-8"))
    program = json.loads((HERE / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json").read_text(encoding="utf-8"))

    expected_ids = [f"RU-PROG-{number:02d}" for number in range(1, 17)]
    program_modules = program.get("modules", [])
    program_ids = [row.get("module_id") for row in program_modules]
    if program_ids != expected_ids:
        raise AssertionError(f"canonical RU-PROG module order drift: {program_ids}")

    rows = matrix.get("module_coverage", [])
    ids = [row.get("module_id") for row in rows]
    if ids != expected_ids:
        raise AssertionError(f"official source matrix must cover RU-PROG-01..16 exactly once: {ids}")
    if len(set(ids)) != 16:
        raise AssertionError("duplicate RU-PROG module in official source coverage")

    canonical_titles = {row["module_id"]: row["title_ru"] for row in program_modules}
    known_sources = {row["source_id"]: row for row in matrix.get("source_records", [])}
    if len(known_sources) != matrix.get("counts", {}).get("official_source_records"):
        raise AssertionError("official source record count drift")

    for row in rows:
        module_id = row["module_id"]
        if row.get("title_ru") != canonical_titles[module_id]:
            raise AssertionError(f"title drift for {module_id}")
        refs = row.get("official_scope_sources")
        if not isinstance(refs, list) or not refs:
            raise AssertionError(f"{module_id} lacks official scope source")
        unknown = sorted(set(refs) - set(known_sources))
        if unknown:
            raise AssertionError(f"{module_id} references unknown source ids: {unknown}")
        locators = row.get("locators")
        if not isinstance(locators, list) or not locators or not all(isinstance(x, str) and x.strip() for x in locators):
            raise AssertionError(f"{module_id} lacks deterministic human-readable source locators")
        if row.get("scope_status") != "EXTRACTED":
            raise AssertionError(f"{module_id} scope not extracted")

    for source_id, row in known_sources.items():
        retention = row.get("retention_status")
        if retention not in {"SOURCE_ARCHIVE_ALLOWED", "TEMPORARY_INGESTION_ONLY", "RIGHTS_NEEDS_REVIEW"}:
            raise AssertionError(f"{source_id} lacks explicit retention status")
        if row.get("bytes_archived") is True and retention == "RIGHTS_NEEDS_REVIEW":
            raise AssertionError(f"{source_id} cannot claim archived bytes while rights review is unresolved")
        if not str(row.get("url", "")).startswith("https://"):
            raise AssertionError(f"{source_id} lacks HTTPS authority URL")

    oge_project = known_sources["FIPI-OGE-RU-2027-PROJECT"]
    if "PROVISIONAL" not in oge_project.get("canonical_exam_status", ""):
        raise AssertionError("OGE 2027 project must remain explicitly provisional")
    if known_sources["FIPI-OGE-RU-2026-FINAL"].get("canonical_exam_status") != "FINAL_FOR_2026":
        raise AssertionError("final OGE 2026 authority drift")
    if known_sources["FIPI-EGE-RU-2026-FINAL"].get("canonical_exam_status") != "FINAL_FOR_2026":
        raise AssertionError("final EGE 2026 authority drift")

    counts = matrix.get("counts", {})
    if counts.get("ru_prog_modules") != 16 or counts.get("modules_with_official_scope_evidence") != 16:
        raise AssertionError("16-module official scope coverage count drift")
    if counts.get("source_bytes_archived_to_drive") != 0:
        raise AssertionError("matrix must not claim Drive byte ingestion before verified upload")
    if counts.get("full_knowledge_extraction_complete") != 0:
        raise AssertionError("scope extraction must not be misreported as full knowledge extraction")
    if counts.get("commercial_textbook_bytes_ingested") != 0:
        raise AssertionError("commercial textbook bytes must remain zero without license")
    if matrix.get("next_processing_gate", {}).get("full_source_base_ready") is not False:
        raise AssertionError("full source base cannot be marked ready by the scope matrix alone")

    print("RUSSIAN_OFFICIAL_SOURCE_COVERAGE_001=PASS")
    print("ru_prog_modules=16")
    print("modules_with_official_scope_evidence=16")
    print("drive_source_bytes_archived=0")
    print("full_knowledge_extraction_complete=0")
    print("commercial_textbook_bytes_ingested=0")
    print("oge_2027_project_canonicalized=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
