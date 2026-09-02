#!/usr/bin/env python3
"""Fail-closed source/object/packet identity review for OGE-2026 6.1.

OGE_COD 6.1 is the orthography meta-operation premise. Current reviewed
inventory classifies that route object as EXAM_ROUTE_ONLY with no canonical
school semantic refs. This review therefore binds the exact official object and
proves the no-invention boundary before any later object-level disposition is
considered. It does not admit semantics, close an object, or change progress.
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
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
CURRENT_PROGRESS = HERE / "build_russian_semantic_acceptance_progress_launch_current.py"
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

SOURCE_ID = "FIPI-OGE-RU-2026-FINAL"
DOCUMENT_ID = "OGE_COD"
CONTENT_CODE = "6.1"
OVERLAY_TOPIC = "concept of orthogram / orthographic analysis premise"
OVERLAY_CLASSIFICATION = "EXAM_ONLY_COMPOSITE"
OVERLAY_NOTE = "Meta-operation over rules; not a new spelling identity."
INVENTORY_OBJECT_KEY = "oge_2026_orthography_route::oge-2026-orthography-6-1"
INVENTORY_SOURCE_ID = "oge-2026-orthography-6-1"
INVENTORY_CLASSIFICATION = "EXAM_ROUTE_ONLY"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def build_review() -> dict[str, Any]:
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    progress = runpy.run_path(str(CURRENT_PROGRESS))["build_progress"]()
    overlay = load_json(OGE_OVERLAY)
    inventory = load_json(IDENTITY_INVENTORY)

    if accounting.get("status") != "RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING_COMPLETE_SEMANTIC_ACCEPTANCE_REQUIRED":
        raise ValueError("full object accounting is not at the fail-closed semantic boundary")
    if packet.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED" or packet.get("russian_content_ready") is not False:
        raise ValueError("semantic acceptance packet is not fail-closed")
    if progress.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS" or progress.get("russian_content_ready") is not False:
        raise ValueError("current launch progress boundary drift")
    summary = progress.get("progress_summary") or {}
    if summary.get("semantic_units_with_accepted_component_sets") != 28:
        raise ValueError("review must start from exact post-6.14 28-unit launch progress")
    if summary.get("semantic_requirements_with_accepted_component_sets") != 28:
        raise ValueError("review must start from exact post-6.14 28-requirement launch progress")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery already present before 6.1 review")

    overlay_rows = [
        row for row in overlay.get("orthography_codifier_overlay", [])
        if isinstance(row, dict) and str(row.get("position")) == CONTENT_CODE
    ]
    if len(overlay_rows) != 1:
        raise ValueError(f"expected exactly one OGE {CONTENT_CODE} overlay row")
    overlay_row = overlay_rows[0]
    if overlay_row.get("topic") != OVERLAY_TOPIC:
        raise ValueError("OGE 6.1 overlay topic drift")
    if overlay_row.get("classification") != OVERLAY_CLASSIFICATION:
        raise ValueError("OGE 6.1 overlay classification drift")
    if overlay_row.get("note") != OVERLAY_NOTE:
        raise ValueError("OGE 6.1 overlay note drift")
    if overlay_row.get("owners") not in (None, []):
        raise ValueError("OGE 6.1 unexpectedly acquired canonical owners")

    inventory_rows = [
        row for row in inventory.get("objects", [])
        if isinstance(row, dict) and str(row.get("object_key")) == INVENTORY_OBJECT_KEY
    ]
    if len(inventory_rows) != 1:
        raise ValueError("OGE 6.1 inventory identity is not unique")
    inventory_row = inventory_rows[0]
    if str(inventory_row.get("source_id")) != INVENTORY_SOURCE_ID:
        raise ValueError("OGE 6.1 inventory source identity drift")
    if inventory_row.get("authority_status") != "current" or inventory_row.get("review_status") != "reviewed":
        raise ValueError("OGE 6.1 inventory authority is not current/reviewed")
    if inventory_row.get("audit_classification") != INVENTORY_CLASSIFICATION:
        raise ValueError("OGE 6.1 inventory classification drift")
    if inventory_row.get("observed_label") != OVERLAY_TOPIC or inventory_row.get("observed_meaning") != OVERLAY_NOTE:
        raise ValueError("OGE 6.1 inventory meaning drift")
    if inventory_row.get("current_semantic_refs") != []:
        raise ValueError("OGE 6.1 inventory must remain ownerless at this review stage")
    if inventory_row.get("candidate_canonical_owner") is not None:
        raise ValueError("OGE 6.1 unexpectedly gained a canonical-owner candidate")

    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for disposition in accounting.get("dispositions", []):
        if not isinstance(disposition, dict):
            continue
        for member in disposition.get("members", []):
            if not isinstance(member, dict):
                continue
            if (
                str(member.get("source_id")) == SOURCE_ID
                and str(member.get("document_id")) == DOCUMENT_ID
                and str(member.get("code")) == CONTENT_CODE
            ):
                matches.append((disposition, member))
    if len(matches) != 1:
        raise ValueError(f"expected one exact accounting binding for OGE 6.1, got {len(matches)}")
    disposition, member = matches[0]
    if disposition.get("disposition") != "PARTIAL_OR_COMPOSITE":
        raise ValueError(f"unexpected OGE 6.1 accounting disposition: {disposition.get('disposition')}")

    unit_id = str(disposition["admission_unit_id"])
    requirement_id = str(member["requirement_id"])
    source_locator = str(member["source_locator"])
    normalized_meaning = str(disposition["normalized_meaning"])

    packet_groups = [
        group for group in packet.get("semantic_review_groups", [])
        if isinstance(group, dict)
        and unit_id in set(str(value) for value in group.get("admission_unit_ids", []))
        and any(str(row.get("requirement_id")) == requirement_id for row in group.get("requirements", []) if isinstance(row, dict))
    ]
    if len(packet_groups) != 1:
        raise ValueError(f"OGE 6.1 packet binding is not unique: {len(packet_groups)}")
    packet_group = packet_groups[0]
    packet_requirements = [
        row for row in packet_group.get("requirements", [])
        if isinstance(row, dict) and str(row.get("requirement_id")) == requirement_id
    ]
    if len(packet_requirements) != 1:
        raise ValueError("OGE 6.1 packet requirement identity drift")
    packet_requirement = packet_requirements[0]
    if str(packet_requirement.get("source_id")) != SOURCE_ID:
        raise ValueError("OGE 6.1 packet source drift")
    if str(packet_requirement.get("document_id")) != DOCUMENT_ID:
        raise ValueError("OGE 6.1 packet document drift")
    if str(packet_requirement.get("code")) != CONTENT_CODE:
        raise ValueError("OGE 6.1 packet code drift")
    if str(packet_requirement.get("source_locator")) != source_locator:
        raise ValueError("OGE 6.1 packet locator drift")
    if str(packet_group.get("normalized_meaning")) != normalized_meaning:
        raise ValueError("OGE 6.1 accounting/packet normalized-meaning drift")
    if packet_group.get("status") not in {
        "SUBJECT_ACCEPTANCE_REQUIRED",
        "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET",
    }:
        raise ValueError("OGE 6.1 packet group is outside the subject-acceptance boundary")

    accepted_by_identity: list[dict[str, Any]] = []
    for group in progress.get("semantic_review_groups", []):
        if not isinstance(group, dict):
            continue
        for accepted in group.get("accepted_component_sets", []):
            if not isinstance(accepted, dict):
                continue
            if (
                str(accepted.get("admission_unit_id")) == unit_id
                or str(accepted.get("requirement_id")) == requirement_id
                or (
                    str(accepted.get("document_id")) == DOCUMENT_ID
                    and str(accepted.get("content_code")) == CONTENT_CODE
                )
            ):
                accepted_by_identity.append(accepted)
    if accepted_by_identity:
        raise ValueError("OGE 6.1 already has an object-bound component-set admission")

    component_refs = [
        row for row in disposition.get("component_refs", [])
        if isinstance(row, dict)
    ]
    if any(str(row.get("ref_kind")) != "review_capability_boundary" for row in component_refs):
        raise ValueError("OGE 6.1 accounting contains an unexpected semantic-candidate ref")
    if any(str(row.get("status")) != "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION" for row in component_refs):
        raise ValueError("OGE 6.1 review boundary was treated as a semantic admission")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "OGE_6_1_META_OPERATION_IDENTITY_BOUND_NO_SEMANTIC_ADMISSION",
        "official_object": {
            "source_id": SOURCE_ID,
            "document_id": DOCUMENT_ID,
            "content_code": CONTENT_CODE,
            "source_locator": source_locator,
            "admission_unit_id": unit_id,
            "requirement_id": requirement_id,
            "packet_group": str(packet_group["group_id"]),
            "accounting_disposition": str(disposition["disposition"]),
            "accounting_normalized_meaning": normalized_meaning,
        },
        "official_route_authority": {
            "overlay_topic": OVERLAY_TOPIC,
            "overlay_classification": OVERLAY_CLASSIFICATION,
            "overlay_note": OVERLAY_NOTE,
            "overlay_owner_refs": [],
            "inventory_object_key": INVENTORY_OBJECT_KEY,
            "inventory_audit_classification": INVENTORY_CLASSIFICATION,
            "inventory_current_semantic_refs": [],
            "inventory_candidate_canonical_owner": None,
        },
        "packet_boundary": {
            "required_action": str(packet_group.get("required_action", "")),
            "explicit_semantic_candidates": list(packet_group.get("explicit_semantic_candidates", [])),
            "review_capability_boundaries": list(packet_group.get("review_capability_boundaries", [])),
            "generic_group_attempt_can_emit_exact_component_mastery": False,
        },
        "current_progress_review": {
            "accepted_authorities_before_review": len(progress.get("accepted_authorities", [])),
            "accepted_units_before_review": int(summary["semantic_units_with_accepted_component_sets"]),
            "accepted_requirements_before_review": int(summary["semantic_requirements_with_accepted_component_sets"]),
            "target_object_bound_acceptance_rows": 0,
            "target_already_object_bound": False,
            "aggregate_delta_now": 0,
        },
        "decision_boundary": {
            "canonical_component_set_supported_by_current_inventory": False,
            "new_school_identity_supported": False,
            "new_school_identity_allowed_by_this_review": False,
            "bounded_meta_operation_or_route_disposition_requires_separate_decision": True,
            "object_closures_now": 0,
            "semantic_admissions_now": 0,
            "exact_component_mastery_admissions_now": 0,
            "next_required_step": "REVIEW_OGE_6_1_AS_OWNERLESS_META_OPERATION_WITHOUT_INVENTING_CANONICAL_COMPONENTS",
        },
        "safety": {
            "false_exact_mastery_admissions": 0,
            "learner_audio_persistence": 0,
            "school_denominator_effect": 0,
            "accepted_demo_or_scorer_change": False,
            "tilda_change": False,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_payment_or_refund": False,
            "real_message_delivery": False,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_bytes(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_review()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        obj = result["official_object"]
        boundary = result["decision_boundary"]
        progress = result["current_progress_review"]
        print("RUSSIAN_OGE_6_1_META_OPERATION_IDENTITY_REVIEW=PASS")
        print(f"ADMISSION_UNIT_ID={obj['admission_unit_id']}")
        print(f"REQUIREMENT_ID={obj['requirement_id']}")
        print(f"PACKET_GROUP={obj['packet_group']}")
        print(f"ACCOUNTING_NORMALIZED_MEANING={obj['accounting_normalized_meaning']}")
        print(f"ACCEPTED_AUTHORITIES_BEFORE_REVIEW={progress['accepted_authorities_before_review']}")
        print("CURRENT_SEMANTIC_REFS=0")
        print("TARGET_ALREADY_OBJECT_BOUND=0")
        print("AGGREGATE_DELTA_NOW=0")
        print(f"NEW_SCHOOL_IDENTITY_SUPPORTED={int(boundary['new_school_identity_supported'])}")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
