#!/usr/bin/env python3
"""Fail-closed exact object-identity review for OGE-2026 6.14.

This review derives the 6.14 admission-unit/requirement binding from complete
object accounting and proves that current accepted object progress does not
already contain the same object. It does not accept 6.14 or change progress.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
CURRENT_PROGRESS = HERE / "build_russian_semantic_acceptance_progress_launch_current.py"
OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"

SOURCE_ID = "FIPI-OGE-RU-2026-FINAL"
DOCUMENT_ID = "OGE_COD"
CONTENT_CODE = "6.14"
LABEL_RU = "Орфографический анализ"
CLASSIFICATION = "EXAM_ONLY_COMPOSITE"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    progress = runpy.run_path(str(CURRENT_PROGRESS))["build_progress"]()
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))

    assert accounting["status"] == "CENTRAL_BRAIN_COMPLETE_OBJECT_ACCOUNTING_SUBJECT_ACCEPTANCE_REQUIRED"
    assert accounting["summary"]["canonical_semantic_admissions"] == 0
    assert accounting["summary"]["ru_proposal_admissions"] == 0
    assert packet["status"] == "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED"
    assert packet["russian_content_ready"] is False
    assert progress["status"] == "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_IN_PROGRESS"
    assert progress["russian_content_ready"] is False
    assert progress["progress_summary"]["false_exact_mastery_admissions"] == 0

    overlay_rows = [
        row for row in overlay["orthography_codifier_overlay"]
        if str(row.get("position")) == CONTENT_CODE
    ]
    assert len(overlay_rows) == 1
    overlay_row = overlay_rows[0]
    assert overlay_row["topic"] == "orthographic analysis"
    assert overlay_row["classification"] == CLASSIFICATION
    assert overlay_row["owners"] == ["all applicable active orthography identities"]
    assert "zero school-count effect" in overlay_row["note"]

    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for disposition in accounting["dispositions"]:
        for member in disposition.get("members", []):
            if (
                str(member.get("source_id")) == SOURCE_ID
                and str(member.get("document_id")) == DOCUMENT_ID
                and str(member.get("code")) == CONTENT_CODE
            ):
                matches.append((disposition, member))
    assert len(matches) == 1, f"expected exactly one accounting binding for 6.14, got {len(matches)}"
    disposition, member = matches[0]
    assert disposition["disposition"] == "PARTIAL_OR_COMPOSITE"
    assert "oge" in disposition["routes"]

    unit_id = str(disposition["admission_unit_id"])
    requirement_id = str(member["requirement_id"])
    source_locator = str(member["source_locator"])

    packet_groups = [
        group for group in packet["semantic_review_groups"]
        if unit_id in group.get("admission_unit_ids", [])
        and any(str(row.get("requirement_id")) == requirement_id for row in group.get("requirements", []))
    ]
    assert len(packet_groups) == 1, f"6.14 packet binding is not unique: {len(packet_groups)}"
    packet_group = packet_groups[0]
    packet_requirement = [
        row for row in packet_group["requirements"]
        if str(row.get("requirement_id")) == requirement_id
    ]
    assert len(packet_requirement) == 1
    packet_requirement = packet_requirement[0]
    assert str(packet_requirement["source_id"]) == SOURCE_ID
    assert str(packet_requirement["document_id"]) == DOCUMENT_ID
    assert str(packet_requirement["code"]) == CONTENT_CODE
    assert str(packet_requirement["source_locator"]) == source_locator

    accepted_matches: list[dict[str, Any]] = []
    accepted_identity_matches: list[dict[str, Any]] = []
    for group in progress["semantic_review_groups"]:
        for accepted in group.get("accepted_component_sets", []):
            if str(accepted.get("document_id")) == DOCUMENT_ID and str(accepted.get("content_code")) == CONTENT_CODE:
                accepted_matches.append(accepted)
            if str(accepted.get("admission_unit_id")) == unit_id or str(accepted.get("requirement_id")) == requirement_id:
                accepted_identity_matches.append(accepted)
    assert accepted_matches == [], "6.14 is already present in current accepted object progress"
    assert accepted_identity_matches == [], "6.14 object identity is already counted under another accepted code"

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "OGE_6_14_EXACT_OBJECT_IDENTITY_BOUND_NOT_ACCEPTED",
        "official_object": {
            "source_id": SOURCE_ID,
            "document_id": DOCUMENT_ID,
            "content_code": CONTENT_CODE,
            "label_ru": LABEL_RU,
            "classification": CLASSIFICATION,
            "source_locator": source_locator,
            "admission_unit_id": unit_id,
            "requirement_id": requirement_id,
            "packet_group": str(packet_group["group_id"]),
            "normalized_meaning": str(disposition["normalized_meaning"]),
        },
        "duplicate_accounting_review": {
            "accepted_rows_with_content_code_6_14": 0,
            "accepted_rows_with_same_admission_unit_or_requirement": 0,
            "historical_or_current_object_already_counted": False,
            "aggregate_delta_if_later_exact_acceptance_passes": 1,
        },
        "source_boundary": {
            "historical_placeholder_is_canonical_owner": False,
            "fabricated_subcodes": 0,
            "school_count_effect": 0,
            "new_school_identity_required": False,
        },
        "acceptance_boundary": {
            "semantic_admissions_now": 0,
            "object_closures_now": 0,
            "exact_component_mastery_admissions_now": 0,
            "separate_exact_component_and_evidence_proof_required": True,
        },
        "safety": {
            "false_exact_mastery_admissions": 0,
            "learner_audio_persistence": 0,
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
        dup = result["duplicate_accounting_review"]
        print("RUSSIAN_OGE_6_14_OBJECT_IDENTITY_BINDING_REVIEW=PASS")
        print(f"OGE_6_14_ADMISSION_UNIT_ID={obj['admission_unit_id']}")
        print(f"OGE_6_14_REQUIREMENT_ID={obj['requirement_id']}")
        print(f"OGE_6_14_PACKET_GROUP={obj['packet_group']}")
        print(f"OGE_6_14_ALREADY_COUNTED={int(dup['historical_or_current_object_already_counted'])}")
        print(f"OGE_6_14_LATER_ACCEPTANCE_COUNT_DELTA={dup['aggregate_delta_if_later_exact_acceptance_passes']}")
        print("OGE_6_14_SEMANTIC_ADMISSIONS_NOW=0")
        print("OGE_6_14_OBJECT_CLOSURES_NOW=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
