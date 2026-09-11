#!/usr/bin/env python3
"""Fail-closed official-source identity audit for EDSOO59 printed p.222 code 8.1.

The current Russian acceptance aggregate carries one review object whose repository
source locator says EDSOO59 p.222 8.1, while its normalized meaning is an
orthoepy+syntax composite. The official 2025 EDSOO Russian 5–9 federal working
program does not support that binding: printed p.222 code 8.1 is the content
element about sentence-formulation means and inversion.

This audit deliberately makes no semantic admission, object closure, candidate
selection, or mastery claim. It exists only to freeze the source contradiction
fail-closed before any current-v30 acceptance can be built.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v29.py"

CURRENT_HEAD = "cb90377c4ebe00e88e22c39824b7c484651ebcc4"
CURRENT_RUN_ID = 34624859121
CURRENT_SHA = "7e7b74ddf4aa4fc9df9744ec74191d8893b6ae251b703c36dcd2ef911273d8e4"

GROUP = "RUS-SEM-REVIEW-048"
TARGET_UNIT = "RAU-3ceb45ca22608d520ddf"
TARGET_REQUIREMENT = "RSK-EDSOO59-8-1-P222"
TARGET_SOURCE = "EDSOO-RU-5-9-2025"
TARGET_DOCUMENT = "EDSOO59"
TARGET_PAGE = 222
TARGET_CODE = "8.1"
TARGET_LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.222 8.1"
TARGET_GRADES = ["8"]

REPOSITORY_MEANING = (
    "Применять нормативное произношение и ударение. "
    "Анализировать синтаксическую конструкцию и её нормативность."
)

OFFICIAL_SOURCE_URL = (
    "https://edsoo.ru/wp-content/uploads/2025/07/"
    "2025_ooo_frp_russkij-yazyk_5-9.pdf"
)
OFFICIAL_SOURCE_TITLE = "Федеральная рабочая программа | Русский язык. 5–9 классы"
OFFICIAL_SOURCE_EDITION = "Москва — 2025"
OFFICIAL_PRINTED_PAGE = 222
OFFICIAL_PDF_PAGE_INDEX_ZERO_BASED = 221
OFFICIAL_CODE = "8.1"
OFFICIAL_TEXT = (
    "Средства оформления предложения в устной и письменной речи "
    "(интонация, логическое ударение, знаки препинания). "
    "Нормы использования инверсии"
)
OFFICIAL_SOURCE_VERIFIED_DATE = "2026-09-11"

EXPECTED_CURRENT_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 45,
    "semantic_requirements_with_accepted_component_sets": 45,
    "subject_disposed_units_total": 46,
    "subject_disposed_requirements_total": 46,
    "subject_review_units_remaining": 1270,
    "subject_review_requirements_remaining": 1345,
    "accepted_bounded_ru_subject_semantics": 75,
    "accepted_bounded_ru_semantics_total": 84,
    "canonical_component_refs_reused_unique": 125,
    "fully_accepted_semantic_groups": 1,
    "false_exact_mastery_admissions": 0,
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def build_audit() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("schema_version") != "0.31.0":
        raise ValueError("current-v29 schema drift")
    if current.get("normalized_sha256") != CURRENT_SHA:
        raise ValueError("current-v29 normalized SHA drift")

    summary = current.get("progress_summary") or {}
    for key, expected in EXPECTED_CURRENT_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v29 summary drift: {key}")
    if len(current.get("accepted_authorities") or []) != 75:
        raise ValueError("current-v29 accepted authority count drift")

    groups = [
        row
        for row in current.get("semantic_review_groups", [])
        if isinstance(row, dict) and row.get("group_id") == GROUP
    ]
    if len(groups) != 1:
        raise ValueError("target review group missing or duplicated")
    group = groups[0]

    if group.get("admission_unit_ids") != [TARGET_UNIT]:
        raise ValueError("target admission-unit identity drift")
    if group.get("admission_unit_count") != 1 or group.get("requirement_count") != 1:
        raise ValueError("target group denominator drift")
    if group.get("accepted_component_set_count") not in (None, 0):
        raise ValueError("target group unexpectedly has accepted component set")
    if group.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("target group unexpectedly changed status")
    if norm(group.get("normalized_meaning")) != REPOSITORY_MEANING:
        raise ValueError("repository target meaning drift")

    requirements = [
        row
        for row in group.get("requirements", [])
        if isinstance(row, dict) and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(requirements) != 1:
        raise ValueError("target requirement missing or duplicated")
    req = requirements[0]

    exact_repo_binding = {
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "page": TARGET_PAGE,
        "code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "grades": TARGET_GRADES,
        "confidence": "MEDIUM",
    }
    for key, expected in exact_repo_binding.items():
        if req.get(key) != expected:
            raise ValueError(f"repository source binding drift: {key}")

    if norm(OFFICIAL_TEXT) == norm(REPOSITORY_MEANING):
        raise ValueError("official source unexpectedly equals repository meaning")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_EDSOO59_P222_8_1_BLOCKED_OFFICIAL_SOURCE_IDENTITY_MISMATCH",
        "current_v29_exact_head_gate": {
            "workflow": "Russian RU02 OGE p21 4.1.6 current exact acceptance",
            "run_id": CURRENT_RUN_ID,
            "head_sha": CURRENT_HEAD,
            "conclusion": "SUCCESS",
            "normalized_sha256": CURRENT_SHA,
        },
        "repository_object": {
            "packet_group": GROUP,
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "source_id": TARGET_SOURCE,
            "document_id": TARGET_DOCUMENT,
            "page": TARGET_PAGE,
            "code": TARGET_CODE,
            "source_locator": TARGET_LOCATOR,
            "grades": TARGET_GRADES,
            "confidence": "MEDIUM",
            "normalized_meaning": REPOSITORY_MEANING,
        },
        "official_source_observation": {
            "publisher": "Единое содержание общего образования (EDSOO)",
            "title": OFFICIAL_SOURCE_TITLE,
            "edition": OFFICIAL_SOURCE_EDITION,
            "url": OFFICIAL_SOURCE_URL,
            "verified_date": OFFICIAL_SOURCE_VERIFIED_DATE,
            "printed_page": OFFICIAL_PRINTED_PAGE,
            "pdf_page_index_zero_based": OFFICIAL_PDF_PAGE_INDEX_ZERO_BASED,
            "code": OFFICIAL_CODE,
            "text": OFFICIAL_TEXT,
        },
        "source_identity_resolution": {
            "same_printed_page": TARGET_PAGE == OFFICIAL_PRINTED_PAGE,
            "same_code": TARGET_CODE == OFFICIAL_CODE,
            "repository_meaning_matches_official_text": False,
            "repository_object_binding_is_safe_for_semantic_acceptance": False,
            "previous_component_owner_mapping_may_be_reused_for_this_object": False,
            "previous_bounded_candidate_mapping_may_be_selected_for_this_object": False,
            "required_next_resolution": (
                "Correct or re-derive the exact source object from the official EDSOO59 "
                "2025 codifier before any owner resolution or current-v30 acceptance."
            ),
        },
        "blocker": {
            "kind": "OFFICIAL_SOURCE_IDENTITY_MISMATCH",
            "severity": "FAIL_CLOSED",
            "object_remains_subject_review_required": True,
            "current_v30_allowed": False,
            "reason": (
                "The repository locator EDSOO59 p.222 8.1 is bound to an "
                "orthoepy+syntax composite, but the official 2025 source at the "
                "same printed page and code is a sentence/inversion content element."
            ),
        },
        "policy": {
            "official_source_overrides_repository_inferred_binding": True,
            "source_identity_must_be_exact_before_owner_resolution": True,
            "keyword_or_fuzzy_owner_inference_allowed": False,
            "module_route_title_or_task_number_inference_allowed": False,
            "nearby_semantic_candidate_auto_selection_allowed": False,
            "object_acceptance_allowed_by_this_audit": False,
            "semantic_admission_allowed_by_this_audit": False,
            "mastery_admission_allowed_by_this_audit": False,
            "registered_user_identity_required_for_future_canonical_learner_evidence": True,
            "anonymous_or_device_only_canonical_progress_allowed": False,
        },
        "summary": {
            "semantic_admissions": 0,
            "object_level_closures": 0,
            "exact_mastery_admissions": 0,
            "false_exact_mastery_admissions": 0,
            "current_v29_remainder_units_preserved": EXPECTED_CURRENT_SUMMARY[
                "subject_review_units_remaining"
            ],
            "current_v29_remainder_requirements_preserved": EXPECTED_CURRENT_SUMMARY[
                "subject_review_requirements_remaining"
            ],
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()

    result = build_audit()
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    if args.emit:
        print(payload, end="")

    print(
        "RUSSIAN_EDSOO59_P222_8_1_SOURCE_IDENTITY_AUDIT="
        f"{result['status']} "
        f"sha256={result['normalized_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
