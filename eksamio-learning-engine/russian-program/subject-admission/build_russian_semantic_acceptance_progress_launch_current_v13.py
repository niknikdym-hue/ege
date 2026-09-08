#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress after exact OGE P021 RU01 transcription object acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v12.py"
RESOLUTION = HERE / "build_ru01_oge_p021_phonetic_transcription_exact_owner_reuse_resolution.py"
SEMANTIC_AUTH = HERE / "RU01-PHONETIC-TRANSCRIPTION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
OBJECT_AUTH = HERE / "RU01-OGE-P021-PHONETIC-TRANSCRIPTION-4-1-4-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

BASE_HEAD = "a1ab7c475535b8b904fecc1fe915e64c9ace1eac"
BASE_BLOB = "872b08739081224bafc7576e90b8c5fc7082869b"
BASE_SHA = "dfe5bd5ccf1f87c75691d5adc57ad6aff96525384c3fccae4fe1eebb50ebdebf"
RESOLUTION_SHA = "60196b61d4d4f1ff47cac309fdb1fe7b8f542296de1572836fe8c8da267f4f9c"
SEMANTIC_AUTH_SHA = "3b93a6e68a7cca7ca3effb3a31eba70c92d22fc99fa6bd2f7cf991d82e88d0e8"
OBJECT_AUTH_SHA = "e2ea8199848d59446618652e226bf4069a63068c631613578b743803b54a4605"

AUTH_ID = "RU01_OGE_P021_PHONETIC_TRANSCRIPTION_4_1_4_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-phonetic-transcription-elements"
UNIT = "RAU-f12c55d19d60877d22ef"
REQ = "RSK-OGE_COD-4-1-4-P021"
GROUP = "RUS-SEM-REVIEW-001"
SOURCE = "FIPI-OGE-RU-2026-FINAL"
DOC = "OGE_COD"
DOC_SHA = "2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a"
PAGE = 21
CODE = "4.1.4"
LOCATOR = "FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.4"
SIGNATURE = "PHONETIC_TRANSCRIPTION"
EVID = [f"p01-u4-v{i}" for i in range(1, 6)]

EXPECTED_BASE = {
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
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER.update({
    "semantic_units_with_accepted_component_sets": 38,
    "semantic_requirements_with_accepted_component_sets": 38,
    "semantic_units_remaining_without_accepted_component_set": 1278,
    "semantic_requirements_remaining_without_accepted_component_set": 1353,
    "subject_disposed_units_total": 39,
    "subject_disposed_requirements_total": 39,
    "subject_review_units_remaining": 1277,
    "subject_review_requirements_remaining": 1352,
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
        raise ValueError("current-v12 builder blob drift")
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.15.0" or data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v12 authority drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v12 aggregate drift: {key}")
    if len(data.get("accepted_authorities") or []) != 59:
        raise ValueError("current-v12 accepted authority count drift")
    previous = data.get("newly_accepted_exact_object") or {}
    if previous.get("admission_unit_id") != "RAU-2725ee5b709b70502748":
        raise ValueError("current-v12 predecessor object drift")
    if previous.get("requirement_id") != "RSK-EDSOO59-4-1-4-P187":
        raise ValueError("current-v12 predecessor requirement drift")

    resolution = runpy.run_path(str(RESOLUTION))["build_resolution"]()
    if resolution.get("normalized_sha256") != RESOLUTION_SHA:
        raise ValueError("exact owner reuse resolution SHA drift")
    if resolution.get("status") != "CENTRAL_BRAIN_RU01_OGE_P021_PHONETIC_TRANSCRIPTION_EXACT_OWNER_REUSE_READY_NOT_ACCEPTED":
        raise ValueError("exact owner reuse resolution status drift")
    target = resolution.get("target_object") or {}
    for key, expected in {
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
    }.items():
        if target.get(key) != expected:
            raise ValueError(f"exact owner reuse target drift: {key}")
    owner = resolution.get("exact_current_owner_resolution") or {}
    if owner.get("resolution") != "EXACT_CURRENT_CANONICAL_OWNER_REUSE_READY":
        raise ValueError("exact owner reuse readiness drift")
    if owner.get("canonical_component_refs") != [SEMANTIC]:
        raise ValueError("exact owner reuse semantic drift")
    if (owner.get("component_specific_independent_evidence") or {}).get(SEMANTIC) != EVID:
        raise ValueError("exact owner reuse evidence drift")
    boundary = resolution.get("acceptance_boundary") or {}
    if boundary.get("review_is_acceptance") is not False:
        raise ValueError("owner resolution unexpectedly became acceptance")
    if boundary.get("separate_exact_object_acceptance_required") is not True:
        raise ValueError("separate exact object acceptance boundary drift")
    if boundary.get("shared_evidence_can_close_sibling_source_objects_without_separate_acceptance") is not False:
        raise ValueError("sibling auto-closure opened in owner resolution")
    if boundary.get("false_exact_mastery") != 0:
        raise ValueError("owner resolution false exact mastery drift")

    semantic_auth = json.loads(SEMANTIC_AUTH.read_text(encoding="utf-8"))
    if hashlib.sha256(canonical_json(semantic_auth)).hexdigest() != SEMANTIC_AUTH_SHA:
        raise ValueError("accepted transcription semantic authority SHA drift")
    if semantic_auth.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("accepted transcription semantic status drift")
    decisions = semantic_auth.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("accepted transcription semantic identity drift")
    if decisions[0].get("independent_verification_item_ids") != EVID:
        raise ValueError("accepted transcription semantic evidence drift")

    authority = json.loads(OBJECT_AUTH.read_text(encoding="utf-8"))
    verify_embedded_sha(authority, OBJECT_AUTH_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_PHONETIC_TRANSCRIPTION_CANONICAL_COMPONENT_SET":
        raise ValueError("OGE P021 object authority status drift")
    if authority.get("current_launch_progress_v12_base_head_sha") != BASE_HEAD:
        raise ValueError("OGE P021 object base head drift")
    if authority.get("current_launch_progress_v12_normalized_sha256") != BASE_SHA:
        raise ValueError("OGE P021 object base normalized SHA drift")
    if authority.get("owner_reuse_resolution_normalized_sha256") != RESOLUTION_SHA:
        raise ValueError("OGE P021 owner reuse binding drift")
    if authority.get("semantic_acceptance_authority_sha256") != SEMANTIC_AUTH_SHA:
        raise ValueError("OGE P021 semantic authority binding drift")

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
        "canonical_component_refs": [SEMANTIC],
        "component_count": 1,
        "component_specific_independent_evidence": {SEMANTIC: EVID},
        "independent_evidence_items": 5,
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    for key, expected in exact.items():
        if decision.get(key) != expected:
            raise ValueError(f"OGE P021 object authority identity drift: {key}")

    mastery = decision.get("mastery_boundary") or {}
    for key in (
        "accepted_bounded_subject_semantic_required",
        "exact_current_owner_resolution_required",
        "component_specific_independent_evidence_required",
        "validated_transcription_item_may_support_only_its_single_canonical_ref",
    ):
        if mastery.get(key) is not True:
            raise ValueError(f"OGE P021 mastery boundary weakened: {key}")
    for key in (
        "generic_ru01_attempt_can_emit_exact_component_mastery",
        "word_analysis_evidence_can_substitute_for_transcription",
        "normative_pronunciation_or_stress_evidence_can_substitute_for_transcription",
        "shared_evidence_can_close_sibling_source_objects_without_separate_acceptance",
    ):
        if mastery.get(key) is not False:
            raise ValueError(f"OGE P021 mastery boundary weakened: {key}")
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
    if group.get("accepted_component_set_count") != 8:
        raise ValueError("current-v12 RU01 accepted set count drift")
    if UNIT not in set(map(str, group.get("admission_unit_ids") or [])):
        raise ValueError("OGE P021 transcription target unit missing from RU01 group")
    rows = [r for r in group.get("requirements") or [] if r.get("requirement_id") == REQ]
    if len(rows) != 1:
        raise ValueError("OGE P021 transcription target requirement not unique")
    row = rows[0]
    for key, expected in (
        ("source_id", SOURCE),
        ("document_id", DOC),
        ("page", PAGE),
        ("code", CODE),
        ("source_locator", LOCATOR),
    ):
        if row.get(key) != expected:
            raise ValueError(f"OGE P021 source identity drift: {key}")

    accepted_sets = [
        item
        for g in data.get("semantic_review_groups") or []
        for item in g.get("accepted_component_sets") or []
        if isinstance(item, dict)
    ]
    if any(item.get("admission_unit_id") == UNIT or item.get("requirement_id") == REQ for item in accepted_sets):
        raise ValueError("OGE P021 transcription object already accepted")
    if any(item.get("id") == AUTH_ID for item in data.get("accepted_authorities") or [] if isinstance(item, dict)):
        raise ValueError("OGE P021 authority already integrated")

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
            "base_current_v12_normalized_sha256": BASE_SHA,
            "exact_owner_reuse_resolution_normalized_sha256": RESOLUTION_SHA,
            "accepted_subject_semantic_authority_sha256": SEMANTIC_AUTH_SHA,
            "accepted_authority_normalized_sha256": OBJECT_AUTH_SHA,
            "component_specific_independent_evidence_items": 5,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    group.setdefault("accepted_component_sets", []).append(projection)
    group["accepted_component_set_count"] = len(group["accepted_component_sets"])
    if group["accepted_component_set_count"] != 9:
        raise ValueError("OGE P021 transcription accepted-set count drift")
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
            raise ValueError(f"post-OGE-P021-transcription aggregate drift: {key}")
    if len(data["accepted_authorities"]) != 60:
        raise ValueError("post-OGE-P021-transcription authority count drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery must remain zero")

    new = [x for x in group["accepted_component_sets"] if x.get("accepted_authority_id") == AUTH_ID]
    if len(new) != 1 or new[0].get("admission_unit_id") != UNIT or new[0].get("requirement_id") != REQ:
        raise ValueError("OGE P021 exact object projection drift")

    data["schema_version"] = "0.16.0"
    data["base_current_launch_progress_v12_head_sha"] = BASE_HEAD
    data["base_current_launch_progress_v12_builder_git_blob_sha1"] = BASE_BLOB
    data["base_current_launch_progress_v12_normalized_sha256"] = BASE_SHA
    data["newly_accepted_exact_object"] = {
        "accepted_authority_id": AUTH_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "accepted_semantic_ref": SEMANTIC,
        "component_specific_independent_evidence_ids": EVID,
        "sibling_source_objects_accepted": 0,
    }
    data.setdefault("policy", {})["ru01_exact_owner_reuse_resolution_required_before_reused_object_acceptance"] = True
    data["policy"]["ru01_transcription_object_requires_prior_bounded_subject_semantic_acceptance"] = True
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
        print("RUSSIAN_RU01_OGE_P021_PHONETIC_TRANSCRIPTION_4_1_4_EXACT_OBJECT_ACCEPTANCE=PASS")
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
