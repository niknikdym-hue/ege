#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    scope = json.loads((HERE / "RUSSIAN-OFFICIAL-SOURCE-COVERAGE-v1.0.json").read_text(encoding="utf-8"))
    state = json.loads((HERE / "RUSSIAN-SOURCE-ARCHIVE-STATE-v1.0.json").read_text(encoding="utf-8"))

    if state.get("status") != "DRIVE_SOURCE_ARCHIVE_VERIFIED_KNOWLEDGE_EXTRACTION_PENDING":
        raise AssertionError("source archive state must remain explicit about pending knowledge extraction")
    if state.get("scope_snapshot") != "RUSSIAN-OFFICIAL-SOURCE-COVERAGE-v1.0.json":
        raise AssertionError("archive state must reference the canonical 16-module scope snapshot")

    scope_ids = {row["source_id"] for row in scope.get("source_records", [])}
    archived_ids = state.get("drive_archive", {}).get("official_scope_record_ids", [])
    if len(archived_ids) != 4 or len(set(archived_ids)) != 4:
        raise AssertionError(f"expected exactly four archived launch source records, got {archived_ids}")
    if set(archived_ids) - scope_ids:
        raise AssertionError("archive state references source ids absent from the scope snapshot")
    expected_archived = {
        "EDSOO-RU-5-9-2025",
        "EDSOO-RU-10-11-BASIC-2025",
        "FIPI-OGE-RU-2026-FINAL",
        "FIPI-EGE-RU-2026-FINAL",
    }
    if set(archived_ids) != expected_archived:
        raise AssertionError(f"archived launch authority drift: {archived_ids}")
    if state["drive_archive"].get("official_scope_records_archived") != 4:
        raise AssertionError("official source-record archive count drift")
    if state["drive_archive"].get("official_scope_files_archived") != 8:
        raise AssertionError("official launch scope must contain 2 EDSOO + 3 OGE + 3 EGE files")
    if state["drive_archive"].get("official_exam_reference_files_archived") != 1:
        raise AssertionError("EGE 2026 open KIM reference must be recorded separately")
    if state["drive_archive"].get("inbox_empty_after_sort") is not True:
        raise AssertionError("source archive INBOX must be empty after classification")
    if state["drive_archive"].get("redistribution_authorized_by_this_record") is not False:
        raise AssertionError("archive verification must not grant redistribution rights")

    provisional = state["drive_archive"].get("provisional_scope_record_ids_not_archived", [])
    if provisional != ["FIPI-OGE-RU-2027-PROJECT"]:
        raise AssertionError("OGE 2027 project must remain outside launch archive authority")

    inventory = state.get("official_scope_file_inventory", {})
    if sum(len(files) for files in inventory.values()) != 8:
        raise AssertionError("official scope file inventory count drift")
    if set(inventory) != expected_archived:
        raise AssertionError("official scope inventory/source-record mismatch")

    textbooks = state.get("textbook_archive", {})
    if textbooks.get("owner_reported_purchased_and_uploaded") is not True:
        raise AssertionError("textbook archive must retain the owner-provided purchase/upload boundary")
    if textbooks.get("files_archived") != 11:
        raise AssertionError("Russian textbook archive must contain 11 deduplicated files")
    if textbooks.get("core_files") != 9 or textbooks.get("supplemental_files") != 2:
        raise AssertionError("Russian textbook core/supplemental counts drift")
    if len(textbooks.get("core_set", [])) != 9 or len(textbooks.get("supplemental_set", [])) != 2:
        raise AssertionError("Russian textbook inventory/count mismatch")
    if textbooks.get("knowledge_extraction_complete") is not False:
        raise AssertionError("archived textbook bytes must not be reported as extracted knowledge")
    if textbooks.get("full_bytes_committed_to_git") is not False:
        raise AssertionError("commercial textbook full bytes must never be committed to Git")
    if textbooks.get("redistribution_authorized") is not False:
        raise AssertionError("purchase/upload does not establish redistribution authority")

    methodical = state.get("methodical_support", {})
    required_methodical_flags = [
        "fipi_oge_2026_expert_materials_archived",
        "fipi_ege_2026_expert_materials_archived",
        "fipi_oge_2026_self_preparation_archived",
        "fipi_ege_2026_self_preparation_archived",
        "fipi_oge_2026_navigator_complete_01_11",
        "fipi_ege_2026_navigator_archived",
        "final_interview_2026_methodical_materials_archived",
        "final_interview_2026_audio_bank_archived",
        "edsoo_information_methodical_letter_2026_2027_archived",
        "russian_5_9_assessment_methodology_archived",
        "russian_10_11_assessment_methodology_archived",
    ]
    missing_methodical = [key for key in required_methodical_flags if methodical.get(key) is not True]
    if missing_methodical:
        raise AssertionError(f"methodical archive gaps: {missing_methodical}")

    extraction = state.get("knowledge_extraction", {})
    if extraction.get("full_knowledge_extraction_complete") is not False:
        raise AssertionError("archive completion must not be misreported as full knowledge extraction")
    if extraction.get("commercial_textbook_bytes_ingested_into_knowledge_base") != 0:
        raise AssertionError("textbook knowledge ingestion must remain zero until bounded extraction is performed")

    launch_truth = state.get("launch_truth", {})
    if launch_truth.get("source_archive_ready_for_controlled_extraction") is not True:
        raise AssertionError("verified Drive archive must be ready for controlled extraction")
    if launch_truth.get("full_source_knowledge_base_ready") is not False:
        raise AssertionError("full source knowledge base is not ready before extraction/crosswalk")
    if launch_truth.get("production_content_admission_implied") is not False:
        raise AssertionError("source archive state must not auto-admit learner content")

    print("RUSSIAN_SOURCE_ARCHIVE_STATE_002=PASS")
    print("official_scope_records_archived=4")
    print("official_scope_files_archived=8")
    print("official_exam_reference_files_archived=1")
    print("textbook_files_archived=11")
    print("inbox_empty_after_sort=1")
    print("full_knowledge_extraction_complete=0")
    print("production_content_admission_implied=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
