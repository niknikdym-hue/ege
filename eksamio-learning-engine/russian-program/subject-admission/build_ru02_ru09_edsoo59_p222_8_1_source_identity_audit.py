#!/usr/bin/env python3
"""Fail-closed official-source re-derivation for EDSOO59 printed p.222 code 8.1.

The current Russian aggregate binds EDSOO59 p.222 8.1 to an orthoepy+syntax
composite. The official 2025 EDSOO Russian 5–9 federal working program instead
states a sentence-formulation/inversion content element. This audit:
1) proves the repository/source mismatch;
2) re-derives the exact official source text without mutating the aggregate;
3) searches current canonical school identities and accepted RU09 bounded
   semantics by exact normalized text equality only;
4) keeps the object, semantic admission, and mastery fail-closed when no exact
   owner exists.

No keyword, route, module, title, task-number, fuzzy, or nearby-candidate
inference is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v29.py"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
RU09 = HERE / "RU09-SYNTAX-CANDIDATES-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

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
OFFICIAL_COMPONENTS = [
    {
        "source_component_id": "edsoo59-p222-8-1-sentence-formulation-means",
        "exact_source_text": (
            "Средства оформления предложения в устной и письменной речи "
            "(интонация, логическое ударение, знаки препинания)"
        ),
    },
    {
        "source_component_id": "edsoo59-p222-8-1-inversion-norm",
        "exact_source_text": "Нормы использования инверсии",
    },
]
OFFICIAL_TEXT = ". ".join(row["exact_source_text"] for row in OFFICIAL_COMPONENTS)
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


def _canonical_school_exact_matches(text: str) -> list[dict[str, Any]]:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    matches: list[dict[str, Any]] = []
    wanted = norm(text)
    for row in inventory.get("objects", []):
        if not isinstance(row, dict):
            continue
        if row.get("source_system") != "school_canonical":
            continue
        if row.get("authority_status") != "current":
            continue
        if row.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            continue
        fields = {
            "observed_label": norm(row.get("observed_label")),
            "observed_meaning": norm(row.get("observed_meaning")),
        }
        equal_fields = sorted(key for key, value in fields.items() if value == wanted)
        if not equal_fields:
            continue
        matches.append(
            {
                "source_id": row.get("source_id"),
                "current_semantic_refs": row.get("current_semantic_refs") or [],
                "exact_equal_fields": equal_fields,
            }
        )
    return matches


def _accepted_ru09_exact_matches(text: str) -> list[dict[str, Any]]:
    authority = json.loads(RU09.read_text(encoding="utf-8"))
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU09_SYNTAX_CANDIDATE_BOUNDED_SUBJECT_SEMANTICS":
        raise ValueError("RU09 accepted bounded-semantic authority status drift")
    wanted = norm(text)
    matches: list[dict[str, Any]] = []
    for row in authority.get("decisions", []):
        if not isinstance(row, dict):
            continue
        if row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC":
            continue
        if norm(row.get("canonical_label_ru")) != wanted:
            continue
        matches.append(
            {
                "candidate_ref": row.get("candidate_ref"),
                "accepted_semantic_id": row.get("accepted_semantic_id"),
                "canonical_label_ru": row.get("canonical_label_ru"),
            }
        )
    return matches


def _source_rederivation() -> dict[str, Any]:
    components: list[dict[str, Any]] = []
    for source_component in OFFICIAL_COMPONENTS:
        exact_text = source_component["exact_source_text"]
        school_matches = _canonical_school_exact_matches(exact_text)
        ru09_matches = _accepted_ru09_exact_matches(exact_text)

        # This artifact is a blocker artifact. If an exact owner emerges, fail
        # loudly so the lane is re-reviewed instead of silently preserving a
        # stale "no owner" claim.
        if school_matches or ru09_matches:
            raise ValueError(
                "exact current owner emerged for official p222 component; "
                "replace blocker audit with an explicit owner-binding review"
            )

        components.append(
            {
                **source_component,
                "exact_current_canonical_school_owner_matches": school_matches,
                "exact_current_accepted_ru09_owner_matches": ru09_matches,
                "exact_current_owner_count": 0,
                "owner_resolution_status": "BLOCKED_NO_EXACT_CURRENT_OWNER_BY_EXACT_TEXT_EQUALITY",
                "candidate_is_source_backed": True,
                "candidate_is_canonical_owner": False,
                "candidate_is_accepted_semantic": False,
                "selection_or_admission_performed": False,
            }
        )

    return {
        "status": "SOURCE_BACKED_REDERIVATION_COMPLETE_OWNER_BINDING_BLOCKED",
        "source_span": {
            "source_id": TARGET_SOURCE,
            "document_id": TARGET_DOCUMENT,
            "printed_page": OFFICIAL_PRINTED_PAGE,
            "pdf_page_index_zero_based": OFFICIAL_PDF_PAGE_INDEX_ZERO_BASED,
            "code": OFFICIAL_CODE,
            "url": OFFICIAL_SOURCE_URL,
        },
        "proposed_exact_source_meaning": OFFICIAL_TEXT,
        "aggregate_correction_candidate": {
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQUIREMENT,
            "old_repository_meaning": REPOSITORY_MEANING,
            "proposed_official_source_meaning": OFFICIAL_TEXT,
            "status": "SOURCE_BACKED_CORRECTION_CANDIDATE_NOT_APPLIED",
            "aggregate_mutated": False,
            "current_v30_created": False,
        },
        "owner_search": {
            "method": "EXACT_NORMALIZED_TEXT_EQUALITY_ONLY",
            "searched_authorities": [
                "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json current school_canonical CANONICAL_SCHOOL_IDENTITY rows",
                "RU09-SYNTAX-CANDIDATES-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json accepted decisions",
            ],
            "keyword_search_used_for_binding": False,
            "fuzzy_search_used_for_binding": False,
            "route_module_title_task_number_inference_used": False,
            "nearby_candidate_selection_used": False,
            "components": components,
            "exact_current_owner_count_total": 0,
        },
        "required_next_resolution": (
            "Locate or source-back exact current owners for both official p222 8.1 "
            "components, or explicitly admit new bounded semantics with independent "
            "component evidence; only then may a separate object-binding review "
            "consider aggregate correction and current-v30."
        ),
    }


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

    rederivation = _source_rederivation()

    result: dict[str, Any] = {
        "schema_version": "0.2.0",
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
        "official_source_rederivation": rederivation,
        "source_identity_resolution": {
            "same_printed_page": TARGET_PAGE == OFFICIAL_PRINTED_PAGE,
            "same_code": TARGET_CODE == OFFICIAL_CODE,
            "repository_meaning_matches_official_text": False,
            "repository_object_binding_is_safe_for_semantic_acceptance": False,
            "previous_component_owner_mapping_may_be_reused_for_this_object": False,
            "previous_bounded_candidate_mapping_may_be_selected_for_this_object": False,
            "official_source_rederived_for_exact_owner_search": True,
            "exact_current_owner_binding_complete": False,
            "required_next_resolution": rederivation["required_next_resolution"],
        },
        "blocker": {
            "kind": "OFFICIAL_SOURCE_IDENTITY_MISMATCH",
            "secondary_kind": "MISSING_EXACT_CURRENT_OWNER_FOR_OFFICIAL_SOURCE_COMPONENTS",
            "severity": "FAIL_CLOSED",
            "object_remains_subject_review_required": True,
            "current_v30_allowed": False,
            "reason": (
                "The repository locator EDSOO59 p.222 8.1 is bound to an "
                "orthoepy+syntax composite, while the official 2025 source at the "
                "same printed page and code is a sentence-formulation/inversion "
                "content element. Exact-text owner search finds no current exact "
                "canonical school or accepted RU09 owner for either official component."
            ),
        },
        "policy": {
            "official_source_overrides_repository_inferred_binding": True,
            "source_identity_must_be_exact_before_owner_resolution": True,
            "exact_current_owner_search_performed_first": True,
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
            "official_source_components_rederived": 2,
            "exact_current_owner_matches": 0,
            "source_backed_correction_candidates": 1,
            "aggregate_corrections_applied": 0,
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
