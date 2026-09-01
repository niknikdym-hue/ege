#!/usr/bin/env python3
"""Fail-closed exact object-identity and semantic-scope review for OGE-2026 6.14.

The accounting review group that contains OGE_COD 6.14 also carries a punctuation
review-capability boundary. That grouping is useful for finite review accounting,
but its combined normalized meaning is NOT exact semantic authority for 6.14.
This builder therefore binds the unique source object and explicitly quarantines
the unrelated punctuation boundary before any exact 6.14 acceptance can exist.
It performs no object acceptance and does not change aggregate progress.
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
OVERLAY_TOPIC = "orthographic analysis"
OVERLAY_NOTE = "Rule identification/application over existing skills; zero school-count effect."
ORTHOGRAPHY_BOUNDARY_REF = "review-boundary:899bdadfe84d"
ORTHOGRAPHY_BOUNDARY_LABEL = "Применять орфографическое правило к слову или форме."
PUNCTUATION_BOUNDARY_REF = "review-boundary:cf5ab34773b8"
PUNCTUATION_BOUNDARY_LABEL = "Выбирать нормативные знаки препинания в конструкции."


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_review() -> dict[str, Any]:
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    progress = runpy.run_path(str(CURRENT_PROGRESS))["build_progress"]()
    overlay = json.loads(OVERLAY.read_text(encoding="utf-8"))

    assert accounting["status"] == "RUSSIAN_FULL_SUBJECT_OBJECT_ACCOUNTING_COMPLETE_SEMANTIC_ACCEPTANCE_REQUIRED"
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
    assert overlay_row["topic"] == OVERLAY_TOPIC
    assert overlay_row["classification"] == CLASSIFICATION
    assert overlay_row["owners"] == ["all applicable active orthography identities"]
    assert overlay_row["note"] == OVERLAY_NOTE

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
    assert disposition["routes"] == ["oge"]

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

    # The review-accounting group is intentionally broader than the exact 6.14
    # source object. Quarantine the punctuation boundary instead of propagating
    # the group's combined normalized meaning into exact acceptance.
    disposition_boundaries = {
        str(row.get("ref")): row
        for row in disposition.get("component_refs", [])
        if isinstance(row, dict)
    }
    packet_boundaries = {
        str(row.get("ref")): row
        for row in packet_group.get("review_capability_boundaries", [])
        if isinstance(row, dict)
    }
    assert set(disposition_boundaries) == {ORTHOGRAPHY_BOUNDARY_REF, PUNCTUATION_BOUNDARY_REF}
    assert set(packet_boundaries) == {ORTHOGRAPHY_BOUNDARY_REF, PUNCTUATION_BOUNDARY_REF}
    for boundaries in (disposition_boundaries, packet_boundaries):
        assert boundaries[ORTHOGRAPHY_BOUNDARY_REF]["label"] == ORTHOGRAPHY_BOUNDARY_LABEL
        assert boundaries[PUNCTUATION_BOUNDARY_REF]["label"] == PUNCTUATION_BOUNDARY_LABEL
        assert boundaries[ORTHOGRAPHY_BOUNDARY_REF]["status"] == "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION"
        assert boundaries[PUNCTUATION_BOUNDARY_REF]["status"] == "REVIEW_BOUNDARY_ONLY_NOT_SEMANTIC_ADMISSION"
    assert disposition["normalized_meaning"] == packet_group["normalized_meaning"]
    combined_review_meaning = str(disposition["normalized_meaning"])
    assert ORTHOGRAPHY_BOUNDARY_LABEL in combined_review_meaning
    assert PUNCTUATION_BOUNDARY_LABEL in combined_review_meaning

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
        "schema_version": "0.2.0",
        "status": "OGE_6_14_EXACT_OBJECT_IDENTITY_AND_ORTHOGRAPHY_SCOPE_BOUND_NOT_ACCEPTED",
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
            "exact_semantic_boundary": {
                "official_label_ru": LABEL_RU,
                "overlay_topic": OVERLAY_TOPIC,
                "overlay_note": OVERLAY_NOTE,
                "operation_scope": "ORTHOGRAPHY_RULE_IDENTIFICATION_AND_APPLICATION_OVER_EXISTING_SKILLS",
                "orthography_review_boundary_ref": ORTHOGRAPHY_BOUNDARY_REF,
                "orthography_review_boundary_label": ORTHOGRAPHY_BOUNDARY_LABEL,
                "punctuation_in_scope": False,
            },
        },
        "review_group_contamination_guard": {
            "packet_group": str(packet_group["group_id"]),
            "accounting_group_normalized_meaning": combined_review_meaning,
            "review_boundary_refs": [ORTHOGRAPHY_BOUNDARY_REF, PUNCTUATION_BOUNDARY_REF],
            "orthography_boundary_present": True,
            "punctuation_boundary_present": True,
            "punctuation_boundary_ref": PUNCTUATION_BOUNDARY_REF,
            "punctuation_boundary_label": PUNCTUATION_BOUNDARY_LABEL,
            "punctuation_boundary_excluded_from_6_14_exact_scope": True,
            "accounting_group_normalized_meaning_is_exact_6_14_semantic_authority": False,
            "policy": (
                "RUS-SEM-REVIEW-056 is a finite review-accounting group spanning orthography and punctuation capabilities. "
                "Its combined normalized meaning must never be copied as the exact semantic meaning of OGE_COD 6.14. "
                "Exact 6.14 scope is orthography only, bound by the official label and the OGE orthography overlay."
            ),
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
            "exact_scope_is_orthography_only": True,
        },
        "acceptance_boundary": {
            "semantic_admissions_now": 0,
            "object_closures_now": 0,
            "exact_component_mastery_admissions_now": 0,
            "separate_exact_component_and_evidence_proof_required": True,
            "combined_review_group_meaning_may_be_used_as_exact_object_semantics": False,
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
        guard = result["review_group_contamination_guard"]
        print("RUSSIAN_OGE_6_14_OBJECT_IDENTITY_AND_SEMANTIC_SCOPE_REVIEW=PASS")
        print(f"OGE_6_14_ADMISSION_UNIT_ID={obj['admission_unit_id']}")
        print(f"OGE_6_14_REQUIREMENT_ID={obj['requirement_id']}")
        print(f"OGE_6_14_PACKET_GROUP={obj['packet_group']}")
        print(f"OGE_6_14_ALREADY_COUNTED={int(dup['historical_or_current_object_already_counted'])}")
        print(f"OGE_6_14_LATER_ACCEPTANCE_COUNT_DELTA={dup['aggregate_delta_if_later_exact_acceptance_passes']}")
        print(f"OGE_6_14_PUNCTUATION_BOUNDARY_EXCLUDED={int(guard['punctuation_boundary_excluded_from_6_14_exact_scope'])}")
        print("OGE_6_14_EXACT_SCOPE_ORTHOGRAPHY_ONLY=1")
        print("OGE_6_14_SEMANTIC_ADMISSIONS_NOW=0")
        print("OGE_6_14_OBJECT_CLOSURES_NOW=0")
        print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"normalized_sha256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
