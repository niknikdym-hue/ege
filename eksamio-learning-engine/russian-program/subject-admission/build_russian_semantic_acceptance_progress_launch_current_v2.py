#!/usr/bin/env python3
"""Current Sep-1 launch progress including nonsemantic object dispositions.

This v2 layer deliberately keeps the historical/current semantic-component
builder unchanged so pre-admission proofs (including OGE 6.14 and OGE 6.1)
remain byte-stable. It adds only exact object-bound dispositions that close a
subject-review object without creating a school-* or ru-* semantic identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE_CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current.py"
OGE_6_1_AUTHORITY = HERE / "RUSSIAN-OGE-6.1-ROUTE-OR-FORMAT-ONLY-META-OPERATION-DISPOSITION-v0.1.json"

BASE_CURRENT_SHA256 = "3ed606992d2a8d93cfe3797d4e34f8b8c77286c4b02d2bf8bbfa770eff248c72"
OGE_6_1_AUTHORITY_SHA256 = "537309ed6eaaac11ade9dfb3f26b68c4d9595ce1393b7c24fea32fa1fd811874"
OGE_6_1_AUTHORITY_ID = "RUSSIAN_OGE_6_1_ROUTE_OR_FORMAT_ONLY_META_OPERATION_DISPOSITION_v0.1"
OGE_6_1_STATUS = "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_6_1_ROUTE_OR_FORMAT_ONLY_META_OPERATION_OBJECT_DISPOSITION"
TARGET_UNIT = "RAU-532ee826fbf30b195484"
TARGET_REQUIREMENT = "RSK-OGE_COD-6-1-P024"
TARGET_GROUP = "RUS-SEM-REVIEW-001"
TARGET_SOURCE = "FIPI-OGE-RU-2026-FINAL"
TARGET_DOCUMENT = "OGE_COD"
TARGET_CODE = "6.1"
TARGET_LOCATOR = "FIPI-OGE-RU-2026-FINAL/OGE_COD p.24 6.1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _verify_normalized_sha(authority: dict[str, Any], expected: str) -> None:
    actual = str(authority.get("normalized_sha256", ""))
    if actual != expected:
        raise ValueError(f"authority normalized SHA drift: expected={expected} actual={actual}")
    body = deepcopy(authority)
    body.pop("normalized_sha256", None)
    if hashlib.sha256(canonical_bytes(body)).hexdigest() != expected:
        raise ValueError("authority embedded normalized SHA does not match canonical bytes")


def _load_oge_6_1_authority(base: dict[str, Any]) -> dict[str, Any]:
    authority = json.loads(OGE_6_1_AUTHORITY.read_text(encoding="utf-8"))
    if not isinstance(authority, dict):
        raise ValueError("OGE 6.1 authority must be a JSON object")
    if authority.get("status") != OGE_6_1_STATUS:
        raise ValueError("OGE 6.1 accepted disposition status drift")
    _verify_normalized_sha(authority, OGE_6_1_AUTHORITY_SHA256)
    if authority.get("semantic_packet_sha256") != base.get("base_packet_sha256"):
        raise ValueError("OGE 6.1 authority semantic-packet binding drift")
    if authority.get("object_accounting_sha256") != base.get("object_accounting_sha256"):
        raise ValueError("OGE 6.1 authority object-accounting binding drift")
    summary = authority.get("summary") or {}
    if summary != {
        "bounded_ru_semantic_refs": 0,
        "canonical_component_refs_unique": 0,
        "disposed_admission_units": 1,
        "disposed_requirements": 1,
        "false_exact_mastery_admissions": 0,
        "route_or_format_only_dispositions": 1,
        "school_denominator_effect": 0,
        "semantic_identity_admissions": 0,
    }:
        raise ValueError("OGE 6.1 accepted disposition summary drift")
    return authority


def _validate_decision(decision: dict[str, Any], group: dict[str, Any]) -> None:
    expected = {
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQUIREMENT,
        "packet_group": TARGET_GROUP,
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "content_code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "disposition": "ROUTE_OR_FORMAT_ONLY",
        "authority_kind": "OBJECT_BOUND_ROUTE_OR_FORMAT_ONLY_EXAM_META_OPERATION",
        "route_inventory_classification": "EXAM_ROUTE_ONLY",
    }
    for key, value in expected.items():
        if decision.get(key) != value:
            raise ValueError(f"OGE 6.1 accepted disposition identity drift: {key}")

    exact_route = decision.get("exact_route_boundary") or {}
    if exact_route.get("canonical_component_refs") != [] or exact_route.get("bounded_ru_semantic_refs") != []:
        raise ValueError("OGE 6.1 disposition acquired forbidden semantic refs")
    if exact_route.get("new_school_identity") is not False or exact_route.get("new_subject_identity") is not False:
        raise ValueError("OGE 6.1 disposition created a semantic identity")

    mastery = decision.get("mastery_boundary") or {}
    if mastery.get("semantic_identity_admissions") != 0:
        raise ValueError("OGE 6.1 disposition admitted a semantic identity")
    if mastery.get("canonical_component_refs") != [] or mastery.get("bounded_ru_semantic_refs") != []:
        raise ValueError("OGE 6.1 mastery boundary acquired semantic refs")
    if mastery.get("exact_component_mastery_effect") != 0:
        raise ValueError("OGE 6.1 disposition changed exact component mastery")
    if mastery.get("generic_group_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("OGE 6.1 disposition weakened generic-group mastery guard")
    if mastery.get("object_disposition_can_emit_exact_component_mastery") is not False:
        raise ValueError("OGE 6.1 disposition can emit exact mastery")

    guard = decision.get("review_group_contamination_guard") or {}
    if guard.get("packet_group") != TARGET_GROUP:
        raise ValueError("OGE 6.1 review-group guard drift")
    if guard.get("packet_group_normalized_meaning_is_exact_6_1_semantic_authority") is not False:
        raise ValueError("shared phonetics meaning was promoted to exact OGE 6.1 semantics")
    if guard.get("packet_group_phonetics_meaning_in_6_1_exact_scope") is not False:
        raise ValueError("phonetics meaning leaked into OGE 6.1 scope")
    if guard.get("whole_group_acceptance_allowed") is not False:
        raise ValueError("OGE 6.1 disposition would accept the whole shared group")
    if guard.get("non_target_admission_units_preserved_for_separate_review") != 20:
        raise ValueError("OGE 6.1 non-target unit preservation drift")
    if guard.get("non_target_requirements_preserved_for_separate_review") != 21:
        raise ValueError("OGE 6.1 non-target requirement preservation drift")

    if TARGET_UNIT not in {str(value) for value in group.get("admission_unit_ids", [])}:
        raise ValueError("OGE 6.1 target unit missing from packet group")
    source_rows = [
        row for row in group.get("requirements", [])
        if isinstance(row, dict) and str(row.get("requirement_id")) == TARGET_REQUIREMENT
    ]
    if len(source_rows) != 1:
        raise ValueError("OGE 6.1 target requirement is not unique in packet group")
    source_row = source_rows[0]
    for key, source_key, value in (
        ("source_id", "source_id", TARGET_SOURCE),
        ("document_id", "document_id", TARGET_DOCUMENT),
        ("content_code", "code", TARGET_CODE),
        ("source_locator", "source_locator", TARGET_LOCATOR),
    ):
        if str(source_row.get(source_key)) != value or str(decision.get(key)) != value:
            raise ValueError(f"OGE 6.1 source binding drift: {key}")


def build_progress() -> dict[str, Any]:
    base = runpy.run_path(str(BASE_CURRENT))["build_progress"]()
    if base.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS":
        raise ValueError("base current launch progress status drift")
    if base.get("russian_content_ready") is not False:
        raise ValueError("base current launch progress unexpectedly claims ready")
    if base.get("normalized_sha256") != BASE_CURRENT_SHA256:
        raise ValueError("pre-6.1 current launch progress fingerprint drift")

    s = base.get("progress_summary") or {}
    expected_base = {
        "semantic_units_with_accepted_component_sets": 28,
        "semantic_requirements_with_accepted_component_sets": 28,
        "semantic_units_remaining_without_accepted_component_set": 1288,
        "semantic_requirements_remaining_without_accepted_component_set": 1363,
        "canonical_component_refs_reused_unique": 115,
        "accepted_bounded_ru_route_semantics": 9,
        "accepted_bounded_ru_subject_semantics": 66,
        "accepted_bounded_ru_semantics_total": 75,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected_base.items():
        if s.get(key) != value:
            raise ValueError(f"pre-6.1 current launch aggregate drift: {key}")
    if len(base.get("accepted_authorities", [])) != 48:
        raise ValueError("pre-6.1 current launch authority count drift")

    authority = _load_oge_6_1_authority(base)
    decision = authority.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("OGE 6.1 accepted authority decision missing")

    groups = [
        group for group in base.get("semantic_review_groups", [])
        if isinstance(group, dict) and str(group.get("group_id")) == TARGET_GROUP
    ]
    if len(groups) != 1:
        raise ValueError("OGE 6.1 target packet group must exist exactly once")
    group = groups[0]
    _validate_decision(decision, group)

    existing_component_rows = [
        row
        for current_group in base.get("semantic_review_groups", [])
        if isinstance(current_group, dict)
        for row in current_group.get("accepted_component_sets", [])
        if isinstance(row, dict)
        and (
            str(row.get("admission_unit_id")) == TARGET_UNIT
            or str(row.get("requirement_id")) == TARGET_REQUIREMENT
            or (
                str(row.get("document_id")) == TARGET_DOCUMENT
                and str(row.get("content_code")) == TARGET_CODE
            )
        )
    ]
    if existing_component_rows:
        raise ValueError("OGE 6.1 is already closed by a semantic component-set authority")
    if any(str(row.get("id")) == OGE_6_1_AUTHORITY_ID for row in base.get("accepted_authorities", []) if isinstance(row, dict)):
        raise ValueError("OGE 6.1 route-or-format-only authority already integrated")

    projection = {
        "accepted_authority_id": OGE_6_1_AUTHORITY_ID,
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQUIREMENT,
        "packet_group": TARGET_GROUP,
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "content_code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "authority_kind": "OBJECT_BOUND_ROUTE_OR_FORMAT_ONLY_EXAM_META_OPERATION",
        "disposition": "ROUTE_OR_FORMAT_ONLY",
        "subject_review_status": "CENTRAL_BRAIN_ACCEPTED_NONSEMANTIC_EXAM_META_OPERATION_OBJECT_DISPOSITION",
        "canonical_component_refs": [],
        "bounded_ru_semantic_refs": [],
        "semantic_identity_admissions": 0,
        "mastery_boundary": deepcopy(decision["mastery_boundary"]),
        "exact_route_boundary": deepcopy(decision["exact_route_boundary"]),
        "review_group_contamination_guard": deepcopy(decision["review_group_contamination_guard"]),
    }

    group.setdefault("accepted_nonsemantic_object_dispositions", []).append(deepcopy(projection))
    group["accepted_nonsemantic_object_disposition_count"] = len(group["accepted_nonsemantic_object_dispositions"])
    if group["accepted_nonsemantic_object_disposition_count"] != 1:
        raise ValueError("OGE 6.1 nonsemantic object disposition duplicated")
    if int(group.get("accepted_component_set_count", 0)) > 0:
        group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET_AND_OBJECT_DISPOSITION"
    else:
        group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_OBJECT_DISPOSITION"
    group["remaining_group_action"] = (
        "CONTINUE_REVIEW_OF_NON_TARGET_OBJECTS; ROUTE_OR_FORMAT_ONLY DISPOSITION DOES NOT ACCEPT THE WHOLE SHARED GROUP"
    )

    base["accepted_authorities"].append({
        "id": OGE_6_1_AUTHORITY_ID,
        "authority_kind": "OBJECT_BOUND_ROUTE_OR_FORMAT_ONLY_EXAM_META_OPERATION",
        "sha256": OGE_6_1_AUTHORITY_SHA256,
        "status": OGE_6_1_STATUS,
        "accepted_admission_units": 0,
        "accepted_requirements": 0,
        "disposed_admission_units": 1,
        "disposed_requirements": 1,
        "route_or_format_only_dispositions": 1,
        "accepted_route_semantics": 0,
        "accepted_subject_semantics": 0,
        "semantic_identity_admissions": 0,
    })
    base["accepted_nonsemantic_object_dispositions"] = [deepcopy(projection)]

    summary = base["progress_summary"]
    summary["nonsemantic_object_disposition_units"] = 1
    summary["nonsemantic_object_disposition_requirements"] = 1
    summary["route_or_format_only_object_dispositions"] = 1
    summary["semantic_identity_admissions_from_nonsemantic_object_dispositions"] = 0
    summary["subject_disposed_units_total"] = summary["semantic_units_with_accepted_component_sets"] + 1
    summary["subject_disposed_requirements_total"] = summary["semantic_requirements_with_accepted_component_sets"] + 1
    summary["subject_review_units_remaining"] = summary["semantic_units_remaining_without_accepted_component_set"] - 1
    summary["subject_review_requirements_remaining"] = summary["semantic_requirements_remaining_without_accepted_component_set"] - 1

    if summary["subject_disposed_units_total"] != 29 or summary["subject_disposed_requirements_total"] != 29:
        raise ValueError("post-6.1 subject-disposition total drift")
    if summary["subject_review_units_remaining"] != 1287 or summary["subject_review_requirements_remaining"] != 1362:
        raise ValueError("post-6.1 subject-review remainder drift")
    if summary["false_exact_mastery_admissions"] != 0:
        raise ValueError("OGE 6.1 integration introduced false exact mastery")
    if summary["semantic_units_with_accepted_component_sets"] != 28 or summary["semantic_requirements_with_accepted_component_sets"] != 28:
        raise ValueError("OGE 6.1 nonsemantic disposition changed semantic component-set counts")
    if summary["canonical_component_refs_reused_unique"] != 115:
        raise ValueError("OGE 6.1 nonsemantic disposition changed canonical refs")
    if summary["accepted_bounded_ru_semantics_total"] != 75:
        raise ValueError("OGE 6.1 nonsemantic disposition changed bounded RU semantics")
    if len(base["accepted_authorities"]) != 49:
        raise ValueError("post-6.1 accepted authority count drift")

    base["schema_version"] = "0.5.0"
    base["base_current_launch_progress_sha256"] = BASE_CURRENT_SHA256
    base["policy"]["route_or_format_only_object_disposition_can_reduce_subject_review_remainder_without_semantic_identity"] = True
    base["policy"]["route_or_format_only_object_disposition_can_emit_exact_component_mastery"] = False
    base["policy"]["shared_review_group_meaning_can_be_promoted_by_object_disposition"] = False

    base.pop("normalized_sha256", None)
    base["normalized_sha256"] = hashlib.sha256(canonical_bytes(base)).hexdigest()
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_progress()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        s = result["progress_summary"]
        print("RUSSIAN_SEMANTIC_ACCEPTANCE_PROGRESS_CURRENT_V2=PASS")
        print("OGE_6_13_ACCEPTANCE=LEGACY_OBJECT_RECONFIRMED_NO_COUNT_DELTA")
        print("OGE_6_14_ACCEPTANCE=CURRENT_OBJECT_ACCEPTED_COMPONENT_SET_DELTA_1")
        print("OGE_6_1_DISPOSITION=CURRENT_OBJECT_ROUTE_OR_FORMAT_ONLY_DELTA_1")
        print(f"accepted_authorities={len(result['accepted_authorities'])}")
        for key in (
            "semantic_units_with_accepted_component_sets",
            "semantic_requirements_with_accepted_component_sets",
            "semantic_units_remaining_without_accepted_component_set",
            "semantic_requirements_remaining_without_accepted_component_set",
            "nonsemantic_object_disposition_units",
            "nonsemantic_object_disposition_requirements",
            "subject_disposed_units_total",
            "subject_disposed_requirements_total",
            "subject_review_units_remaining",
            "subject_review_requirements_remaining",
            "canonical_component_refs_reused_unique",
            "accepted_bounded_ru_route_semantics",
            "accepted_bounded_ru_subject_semantics",
            "accepted_bounded_ru_semantics_total",
            "false_exact_mastery_admissions",
        ):
            print(f"{key}={s[key]}")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
