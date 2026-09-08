#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress after exact RU01 phonetic-transcription object acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v11.py"
SEMANTIC_AUTH = HERE / "RU01-PHONETIC-TRANSCRIPTION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
OBJECT_AUTH = HERE / "RU01-PHONETIC-TRANSCRIPTION-P187-4-1-4-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
READINESS = HERE / "build_ru01_phonetic_transcription_content_readiness.py"

BASE_HEAD = "a537f7426c122e14c4d5bc903ed3787bc1ebe7a3"
BASE_BLOB = "68a7902bd4fef33d6328a5b02c7ec973ff59e9a4"
BASE_SHA = "26f33c517b3c7015be48d42fdb08b1a68569931d33cbcef198da4d84aeccce58"
SEMANTIC_AUTH_SHA = "3b93a6e68a7cca7ca3effb3a31eba70c92d22fc99fa6bd2f7cf991d82e88d0e8"
OBJECT_AUTH_SHA = "7d90a25e64255362900d6778aef524147e4adda4de5a47da16dec61549da667e"

AUTH_ID = "RU01_PHONETIC_TRANSCRIPTION_P187_4_1_4_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-phonetic-transcription-elements"
UNIT = "RAU-2725ee5b709b70502748"
REQ = "RSK-EDSOO59-4-1-4-P187"
GROUP = "RUS-SEM-REVIEW-001"
SOURCE = "EDSOO-RU-5-9-2025"
DOC = "EDSOO59"
DOC_SHA = "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d"
PAGE = 187
CODE = "4.1.4"
LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.4"
SIGNATURE = "PHONETIC_TRANSCRIPTION"
EVID = [f"p01-u4-v{i}" for i in range(1, 6)]

EXPECTED_BASE = {
    "semantic_units_with_accepted_component_sets": 36,
    "semantic_requirements_with_accepted_component_sets": 36,
    "semantic_units_remaining_without_accepted_component_set": 1280,
    "semantic_requirements_remaining_without_accepted_component_set": 1355,
    "subject_disposed_units_total": 37,
    "subject_disposed_requirements_total": 37,
    "subject_review_units_remaining": 1279,
    "subject_review_requirements_remaining": 1354,
    "canonical_component_refs_reused_unique": 118,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 67,
    "accepted_bounded_ru_semantics_total": 76,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER.update({
    "semantic_units_with_accepted_component_sets": 37,
    "semantic_requirements_with_accepted_component_sets": 37,
    "semantic_units_remaining_without_accepted_component_set": 1279,
    "semantic_requirements_remaining_without_accepted_component_set": 1354,
    "subject_disposed_units_total": 38,
    "subject_disposed_requirements_total": 38,
    "subject_review_units_remaining": 1278,
    "subject_review_requirements_remaining": 1353,
    "canonical_component_refs_reused_unique": 119,
})


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def git_blob_sha(path: Path) -> str:
    b = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


def verify_embedded_sha(data: dict[str, Any], expected: str) -> None:
    if data.get("normalized_sha256") != expected:
        raise ValueError("object authority normalized SHA drift")
    copy = deepcopy(data)
    copy.pop("normalized_sha256", None)
    if hashlib.sha256(canonical_json(copy)).hexdigest() != expected:
        raise ValueError("object authority embedded SHA mismatch")


def build_progress() -> dict[str, Any]:
    if git_blob_sha(BASE) != BASE_BLOB:
        raise ValueError("current-v11 builder blob drift")
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.14.0" or data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v11 authority drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v11 aggregate drift: {key}")
    if len(data.get("accepted_authorities") or []) != 58:
        raise ValueError("current-v11 accepted authority count drift")

    semantic_auth = json.loads(SEMANTIC_AUTH.read_text(encoding="utf-8"))
    if hashlib.sha256(canonical_json(semantic_auth)).hexdigest() != SEMANTIC_AUTH_SHA:
        raise ValueError("transcription semantic authority SHA drift")
    if semantic_auth.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("transcription semantic acceptance status drift")
    decisions = semantic_auth.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("transcription semantic identity drift")
    if decisions[0].get("independent_verification_item_ids") != EVID:
        raise ValueError("transcription semantic evidence drift")
    next_work = semantic_auth.get("next_exact_work") or {}
    if next_work.get("target_admission_unit_id") != UNIT or next_work.get("target_requirement_id") != REQ:
        raise ValueError("transcription next exact object target drift")
    if next_work.get("component_specific_evidence_ids") != EVID:
        raise ValueError("transcription next exact object evidence drift")
    if next_work.get("separate_exact_object_acceptance_required") is not True:
        raise ValueError("separate exact object gate no longer required")

    readiness = runpy.run_path(str(READINESS))["build_readiness"]()
    if readiness.get("status") != "CENTRAL_BRAIN_RU01_PHONETIC_TRANSCRIPTION_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED":
        raise ValueError("transcription content-readiness predecessor drift")
    if readiness.get("candidate_semantic_id") != SEMANTIC:
        raise ValueError("transcription content semantic drift")
    if (readiness.get("learner_content") or {}).get("independent_verification_ids") != EVID:
        raise ValueError("transcription readiness evidence drift")
    if (readiness.get("evidence_independence") or {}).get("word_analysis_evidence_reused") is not False:
        raise ValueError("word-analysis evidence reuse opened")

    authority = json.loads(OBJECT_AUTH.read_text(encoding="utf-8"))
    verify_embedded_sha(authority, OBJECT_AUTH_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_PHONETIC_TRANSCRIPTION_CANONICAL_COMPONENT_SET":
        raise ValueError("transcription object authority status drift")
    if authority.get("current_launch_progress_v11_base_head_sha") != BASE_HEAD:
        raise ValueError("transcription object base head drift")
    if authority.get("current_launch_progress_v11_normalized_sha256") != BASE_SHA:
        raise ValueError("transcription object base normalized SHA drift")
    if authority.get("semantic_acceptance_authority_sha256") != SEMANTIC_AUTH_SHA:
        raise ValueError("transcription semantic authority binding drift")

    decision = authority.get("decision") or {}
    exact = {
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SOURCE,
        "document_id": DOC,
        "document_sha256": DOC_SHA,
        "page": PAGE,
        "content_code": CODE,
        "source_locator": LOCATOR,
        "normalized_source_signature": SIGNATURE,
        "module_id": "RU-PROG-01",
        "disposition": "PARTIAL_OR_COMPOSITE",
        "canonical_component_refs": [SEMANTIC],
        "component_count": 1,
        "component_specific_independent_evidence": {SEMANTIC: EVID},
        "independent_evidence_items": 5,
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    for key, expected in exact.items():
        if decision.get(key) != expected:
            raise ValueError(f"transcription object authority identity drift: {key}")

    mastery = decision.get("mastery_boundary") or {}
    required_true = (
        "accepted_bounded_subject_semantic_required",
        "component_specific_independent_evidence_required",
        "validated_transcription_item_may_support_only_its_single_canonical_ref",
    )
    for key in required_true:
        if mastery.get(key) is not True:
            raise ValueError(f"transcription mastery boundary weakened: {key}")
    required_false = (
        "generic_ru01_attempt_can_emit_exact_component_mastery",
        "word_analysis_evidence_can_substitute_for_transcription",
        "normative_pronunciation_or_stress_evidence_can_substitute_for_transcription",
        "shared_evidence_can_close_sibling_source_objects_without_separate_acceptance",
    )
    for key in required_false:
        if mastery.get(key) is not False:
            raise ValueError(f"transcription mastery boundary weakened: {key}")
    policy = authority.get("policy") or {}
    if policy.get("whole_group_acceptance_allowed") is not False:
        raise ValueError("whole-group acceptance opened")
    if policy.get("task_module_route_title_keyword_fuzzy_or_embedding_inference_allowed") is not False:
        raise ValueError("inference admission opened")
    if (authority.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("object authority false exact mastery drift")
    if (authority.get("summary") or {}).get("sibling_ru01_source_objects_accepted") != 0:
        raise ValueError("object authority sibling leakage drift")

    groups = [g for g in data.get("semantic_review_groups") or [] if g.get("group_id") == GROUP]
    if len(groups) != 1:
        raise ValueError("RU01 review group not unique")
    group = groups[0]
    if group.get("accepted_component_set_count") != 7:
        raise ValueError("current-v11 RU01 accepted set count drift")
    if UNIT not in set(map(str, group.get("admission_unit_ids") or [])):
        raise ValueError("transcription target unit missing from RU01 group")
    rows = [r for r in group.get("requirements") or [] if r.get("requirement_id") == REQ]
    if len(rows) != 1:
        raise ValueError("transcription target requirement not unique")
    row = rows[0]
    for key, expected in (
        ("source_id", SOURCE),
        ("document_id", DOC),
        ("page", PAGE),
        ("code", CODE),
        ("source_locator", LOCATOR),
    ):
        if row.get(key) != expected:
            raise ValueError(f"transcription source identity drift: {key}")

    accepted_sets = [
        item
        for g in data.get("semantic_review_groups") or []
        for item in g.get("accepted_component_sets") or []
        if isinstance(item, dict)
    ]
    if any(item.get("admission_unit_id") == UNIT or item.get("requirement_id") == REQ for item in accepted_sets):
        raise ValueError("transcription object already accepted")
    if any(item.get("id") == AUTH_ID for item in data.get("accepted_authorities") or [] if isinstance(item, dict)):
        raise ValueError("transcription object authority already integrated")
    semantic_authorities = [
        item for item in data.get("accepted_authorities") or []
        if isinstance(item, dict) and item.get("id") == "RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
    ]
    if len(semantic_authorities) != 1 or semantic_authorities[0].get("sha256") != SEMANTIC_AUTH_SHA:
        raise ValueError("accepted transcription semantic authority missing from current-v11")

    projection = {
        "accepted_authority_id": AUTH_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SOURCE,
        "document_id": DOC,
        "content_code": CODE,
        "source_locator": LOCATOR,
        "modules": ["RU-PROG-01"],
        "canonical_component_refs": [SEMANTIC],
        "component_count": 1,
        "authority": {
            "base_current_v11_normalized_sha256": BASE_SHA,
            "accepted_subject_semantic_authority_sha256": SEMANTIC_AUTH_SHA,
            "accepted_authority_normalized_sha256": OBJECT_AUTH_SHA,
            "component_specific_independent_evidence_items": 5,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    group.setdefault("accepted_component_sets", []).append(projection)
    group["accepted_component_set_count"] = len(group["accepted_component_sets"])
    if group["accepted_component_set_count"] != 8:
        raise ValueError("transcription object accepted-set count drift")
    group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
    group["remaining_group_action"] = (
        "CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"
    )

    data["accepted_authorities"].append({
        "id": AUTH_ID,
        "authority_kind": "OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET",
        "sha256": OBJECT_AUTH_SHA,
        "status": authority["status"],
        "accepted_admission_units": 1,
        "accepted_requirements": 1,
        "canonical_component_refs": 1,
        "accepted_route_semantics": 0,
        "accepted_subject_semantics": 0,
        "semantic_identity_admissions": 0,
    })

    for key, delta in (
        ("semantic_units_with_accepted_component_sets", 1),
        ("semantic_requirements_with_accepted_component_sets", 1),
        ("semantic_units_remaining_without_accepted_component_set", -1),
        ("semantic_requirements_remaining_without_accepted_component_set", -1),
        ("subject_disposed_units_total", 1),
        ("subject_disposed_requirements_total", 1),
        ("subject_review_units_remaining", -1),
        ("subject_review_requirements_remaining", -1),
    ):
        summary[key] += delta

    refs = {
        ref
        for g in data.get("semantic_review_groups") or []
        for item in g.get("accepted_component_sets") or []
        for ref in item.get("canonical_component_refs") or []
    }
    summary["canonical_component_refs_reused_unique"] = len(refs)
    for key, expected in EXPECTED_AFTER.items():
        if summary.get(key) != expected:
            raise ValueError(f"post-transcription-object aggregate drift: {key}")
    if len(data["accepted_authorities"]) != 59:
        raise ValueError("post-transcription-object authority count drift")

    new = [x for x in group["accepted_component_sets"] if x.get("accepted_authority_id") == AUTH_ID]
    if len(new) != 1 or new[0].get("admission_unit_id") != UNIT or new[0].get("requirement_id") != REQ:
        raise ValueError("transcription exact object projection drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery must remain zero")

    data["schema_version"] = "0.15.0"
    data["base_current_launch_progress_v11_head_sha"] = BASE_HEAD
    data["base_current_launch_progress_v11_builder_git_blob_sha1"] = BASE_BLOB
    data["base_current_launch_progress_v11_normalized_sha256"] = BASE_SHA
    data["newly_accepted_exact_object"] = {
        "accepted_authority_id": AUTH_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "accepted_semantic_ref": SEMANTIC,
        "component_specific_independent_evidence_ids": EVID,
        "sibling_source_objects_accepted": 0,
    }
    data.setdefault("policy", {})["ru01_transcription_object_requires_prior_bounded_subject_semantic_acceptance"] = True
    data["policy"]["ru01_transcription_object_requires_component_specific_independent_evidence"] = True
    data["policy"]["generic_ru01_attempt_can_emit_exact_transcription_mastery"] = False
    data["policy"]["ru01_shared_evidence_can_close_sibling_source_objects_without_separate_acceptance"] = False
    data.pop("normalized_sha256", None)
    data["normalized_sha256"] = hashlib.sha256(canonical_json(data)).hexdigest()
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    data = build_progress()
    if args.output:
        Path(args.output).write_text(
            json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if args.emit:
        print(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        summary = data["progress_summary"]
        print("RUSSIAN_RU01_PHONETIC_TRANSCRIPTION_P187_4_1_4_EXACT_OBJECT_ACCEPTANCE=PASS")
        print("ACCEPTED_UNIT=" + UNIT)
        print("ACCEPTED_REQUIREMENT=" + REQ)
        print("EXACT_COMPONENT_REFS=1")
        print("INDEPENDENT_EVIDENCE_ITEMS=5")
        print("ADDITIONAL_SIBLING_RU01_OBJECTS_ACCEPTED=0")
        print(f"ACCEPTED_AUTHORITIES={len(data['accepted_authorities'])}")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={summary['subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['subject_review_requirements_remaining']}")
        print(f"FALSE_EXACT_MASTERY={summary['false_exact_mastery_admissions']}")
        print("NORMALIZED_SHA256=" + data["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
