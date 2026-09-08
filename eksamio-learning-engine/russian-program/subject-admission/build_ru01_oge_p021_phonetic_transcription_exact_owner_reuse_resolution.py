#!/usr/bin/env python3
"""Resolve the exact current owner for the residual OGE RU01 transcription object.

This is deliberately a no-admission gate. It proves only that the exact OGE
source object has the same source-backed PHONETIC_TRANSCRIPTION signature as
the already accepted RU01 transcription semantic, and that component-specific
independent evidence exists. A separate exact object acceptance remains
mandatory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v12.py"
BINDING = HERE / "build_ru01_phonetics_exact_object_binding_review.py"
READINESS = HERE / "build_ru01_phonetic_transcription_content_readiness.py"
SEMANTIC_AUTH = HERE / "RU01-PHONETIC-TRANSCRIPTION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
P187_AUTH = HERE / "RU01-PHONETIC-TRANSCRIPTION-P187-4-1-4-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

TARGET_UNIT = "RAU-f12c55d19d60877d22ef"
TARGET_REQ = "RSK-OGE_COD-4-1-4-P021"
GROUP = "RUS-SEM-REVIEW-001"
SOURCE = "FIPI-OGE-RU-2026-FINAL"
DOCUMENT = "OGE_COD"
DOCUMENT_SHA256 = "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a"
PAGE = 21
CODE = "4.1.4"
LOCATOR = "FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.4"
SIGNATURE = "PHONETIC_TRANSCRIPTION"
SEMANTIC = "ru-phonetics-phonetic-transcription-elements"
EVIDENCE = [f"p01-u4-v{i}" for i in range(1, 6)]
P187_UNIT = "RAU-2725ee5b709b70502748"
P187_REQ = "RSK-EDSOO59-4-1-4-P187"
P187_AUTH_SHA256 = "7d90a25e64255362900d6778aef524147e4adda4de5a47da16dec61549da667e"
SEMANTIC_AUTH_SHA256 = "3b93a6e68a7cca7ca3effb3a31eba70c92d22fc99fa6bd2f7cf991d82e88d0e8"

EXPECTED_CURRENT = {
    "semantic_units_with_accepted_component_sets": 37,
    "semantic_requirements_with_accepted_component_sets": 37,
    "semantic_units_remaining_without_accepted_component_set": 1279,
    "semantic_requirements_remaining_without_accepted_component_set": 1354,
    "subject_disposed_units_total": 38,
    "subject_disposed_requirements_total": 38,
    "subject_review_units_remaining": 1278,
    "subject_review_requirements_remaining": 1353,
    "canonical_component_refs_reused_unique": 119,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 67,
    "accepted_bounded_ru_semantics_total": 76,
    "false_exact_mastery_admissions": 0,
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_resolution() -> dict[str, Any]:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("schema_version") != "0.15.0":
        raise ValueError("current-v12 schema drift")
    if len(current.get("accepted_authorities") or []) != 59:
        raise ValueError("current-v12 accepted authority count drift")
    summary = current.get("progress_summary") or {}
    for key, expected in EXPECTED_CURRENT.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v12 aggregate drift: {key}")
    latest = current.get("newly_accepted_exact_object") or {}
    if latest.get("admission_unit_id") != P187_UNIT or latest.get("requirement_id") != P187_REQ:
        raise ValueError("current-v12 is not pinned after exact P187 transcription acceptance")
    if latest.get("component_specific_independent_evidence_ids") != EVIDENCE:
        raise ValueError("current-v12 P187 evidence drift")
    if latest.get("sibling_source_objects_accepted") != 0:
        raise ValueError("P187 acceptance leaked to sibling source objects")

    review = runpy.run_path(str(BINDING))["build_review"]()
    records = [r for r in review.get("records") or [] if r.get("requirement_id") == TARGET_REQ]
    if len(records) != 1:
        raise ValueError("target OGE transcription requirement is not unique in exact binding review")
    row = records[0]
    expected_row = {
        "admission_unit_id": TARGET_UNIT,
        "source_id": SOURCE,
        "document_id": DOCUMENT,
        "document_sha256": DOCUMENT_SHA256,
        "page": PAGE,
        "code": CODE,
        "source_locator": LOCATOR,
        "normalized_source_signature": SIGNATURE,
        "review_classification": "PENDING",
        "blocker_or_reroute": "TRANSCRIPTION_SEMANTIC_REQUIRED",
    }
    for key, expected in expected_row.items():
        if row.get(key) != expected:
            raise ValueError(f"target exact source identity drift: {key}")
    if row.get("accepted_semantic_refs") != []:
        raise ValueError("historical binding review unexpectedly pre-admitted target semantics")

    semantic_auth = json.loads(SEMANTIC_AUTH.read_text(encoding="utf-8"))
    if semantic_auth.get("normalized_sha256") != SEMANTIC_AUTH_SHA256:
        raise ValueError("accepted transcription semantic authority SHA drift")
    if semantic_auth.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("transcription semantic is not accepted")
    decisions = semantic_auth.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("accepted transcription semantic identity drift")
    if decisions[0].get("independent_verification_item_ids") != EVIDENCE:
        raise ValueError("accepted transcription semantic evidence drift")

    readiness = runpy.run_path(str(READINESS))["build_readiness"]()
    if readiness.get("candidate_semantic_id") != SEMANTIC:
        raise ValueError("transcription readiness semantic drift")
    if (readiness.get("learner_content") or {}).get("independent_verification_ids") != EVIDENCE:
        raise ValueError("transcription independent evidence drift")
    independence = readiness.get("evidence_independence") or {}
    if independence.get("word_analysis_evidence_reused") is not False:
        raise ValueError("word-analysis evidence substitution opened")

    p187 = json.loads(P187_AUTH.read_text(encoding="utf-8"))
    if p187.get("normalized_sha256") != P187_AUTH_SHA256:
        raise ValueError("accepted P187 object authority SHA drift")
    p187_decision = p187.get("decision") or {}
    if p187_decision.get("normalized_source_signature") != SIGNATURE:
        raise ValueError("accepted P187 source signature drift")
    if p187_decision.get("canonical_component_refs") != [SEMANTIC]:
        raise ValueError("accepted P187 semantic owner drift")
    if (p187_decision.get("component_specific_independent_evidence") or {}).get(SEMANTIC) != EVIDENCE:
        raise ValueError("accepted P187 component evidence drift")
    mastery = p187_decision.get("mastery_boundary") or {}
    if mastery.get("shared_evidence_can_close_sibling_source_objects_without_separate_acceptance") is not False:
        raise ValueError("sibling auto-closure boundary weakened")

    groups = [g for g in current.get("semantic_review_groups") or [] if g.get("group_id") == GROUP]
    if len(groups) != 1:
        raise ValueError("RU01 review group not unique in current-v12")
    accepted = groups[0].get("accepted_component_sets") or []
    if any(x.get("admission_unit_id") == TARGET_UNIT or x.get("requirement_id") == TARGET_REQ for x in accepted):
        raise ValueError("target OGE transcription object is already accepted")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_RU01_OGE_P021_PHONETIC_TRANSCRIPTION_EXACT_OWNER_REUSE_READY_NOT_ACCEPTED",
        "current_launch_state": {
            "schema_version": current["schema_version"],
            "accepted_authorities": len(current["accepted_authorities"]),
            "subject_review_units_remaining": summary["subject_review_units_remaining"],
            "subject_review_requirements_remaining": summary["subject_review_requirements_remaining"],
            "false_exact_mastery_admissions": summary["false_exact_mastery_admissions"],
        },
        "target_object": {
            "admission_unit_id": TARGET_UNIT,
            "requirement_id": TARGET_REQ,
            "packet_group": GROUP,
            "source_id": SOURCE,
            "document_id": DOCUMENT,
            "document_sha256": DOCUMENT_SHA256,
            "page": PAGE,
            "content_code": CODE,
            "source_locator": LOCATOR,
            "normalized_source_signature": SIGNATURE,
            "historical_binding_classification": "PENDING",
            "historical_blocker": "TRANSCRIPTION_SEMANTIC_REQUIRED",
        },
        "exact_current_owner_resolution": {
            "resolution": "EXACT_CURRENT_CANONICAL_OWNER_REUSE_READY",
            "canonical_component_refs": [SEMANTIC],
            "component_count": 1,
            "accepted_semantic_authority_sha256": SEMANTIC_AUTH_SHA256,
            "component_specific_independent_evidence": {SEMANTIC: EVIDENCE},
            "evidence_items": len(EVIDENCE),
            "source_signature_matches_already_accepted_exact_transcription_object": True,
            "already_accepted_reference_object": {
                "admission_unit_id": P187_UNIT,
                "requirement_id": P187_REQ,
                "authority_sha256": P187_AUTH_SHA256,
            },
        },
        "acceptance_boundary": {
            "review_is_acceptance": False,
            "semantic_admission_effect": "NONE",
            "object_closure_effect": "NONE",
            "exact_mastery_effect": "NONE",
            "new_school_canonical_identity_required": False,
            "new_ru_semantic_identity_required": False,
            "separate_exact_object_acceptance_required": True,
            "component_specific_independent_evidence_required": True,
            "shared_evidence_can_close_sibling_source_objects_without_separate_acceptance": False,
            "task_module_route_title_keyword_fuzzy_or_embedding_inference_allowed": False,
            "whole_group_acceptance_allowed": False,
            "false_exact_mastery": 0,
        },
        "next_exact_work": {
            "action": "BUILD_SEPARATE_EXACT_OBJECT_ACCEPTANCE",
            "target_admission_unit_id": TARGET_UNIT,
            "target_requirement_id": TARGET_REQ,
            "canonical_component_refs": [SEMANTIC],
            "component_specific_independent_evidence_ids": EVIDENCE,
        },
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_resolution()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RU01_OGE_P021_PHONETIC_TRANSCRIPTION_EXACT_OWNER_REUSE_RESOLUTION=PASS")
        print("STATUS=" + result["status"])
        print("TARGET=" + TARGET_UNIT + "/" + TARGET_REQ)
        print("CANONICAL_COMPONENT_REF=" + SEMANTIC)
        print("EVIDENCE_ITEMS=" + str(len(EVIDENCE)))
        print("OBJECT_CLOSURE_EFFECT=NONE")
        print("FALSE_EXACT_MASTERY=0")
        print("normalized_sha256=" + result["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
