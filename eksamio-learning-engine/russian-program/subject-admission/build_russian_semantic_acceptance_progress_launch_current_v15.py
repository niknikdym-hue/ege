#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress after exact EDSOO59 P187 RU01 sound-changes object acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v14.py"
SEMANTIC_AUTH = HERE / "RU01-SOUND-CHANGES-IN-SPEECH-FLOW-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
OBJECT_AUTH = HERE / "RU01-SOUND-CHANGES-P187-4-1-3-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

BASE_HEAD = "7a02c9f3a1a3516981b289a2c106ae3e07437e4c"
BASE_BLOB = "fbad60c5a754ca8bfc526b04e093ff717e888f8e"
BASE_SHA = "8fdbddca8834effcddd3fa5b5095537e397d973d49bae5941361aaf1399e5d40"
SEMANTIC_AUTH_SHA = "f2583aea8da9b3b79e68ba30a9a68559b9cbe1b6fb6e0aeafc4bf3c0d653c63d"
OBJECT_AUTH_SHA = "992c07da724f734a28cdbd4bf058c1240826b5a3c94ee1eef55b2c8791d43de7"

AUTH_ID = "RU01_SOUND_CHANGES_P187_4_1_3_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-sound-changes-in-speech-flow"
UNIT = "RAU-b1ba48cb81e96255122a"
REQ = "RSK-EDSOO59-4-1-3-P187"
SIBLING_UNIT = "RAU-f709f1855bb0b8d104bc"
SIBLING_REQ = "RSK-OGE_COD-4-1-3-P021"
GROUP = "RUS-SEM-REVIEW-001"
SOURCE = "EDSOO-RU-5-9-2025"
DOC = "EDSOO59"
DOC_SHA = "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d"
PAGE = 187
CODE = "4.1.3"
LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.3"
SIGNATURE = "SOUND_CHANGES_IN_SPEECH_FLOW"
EVID = ['p01-u5-v1', 'p01-u5-v2', 'p01-u5-v3', 'p01-u5-v4', 'p01-u5-v5', 'p01-u5-v6']

EXPECTED_BASE = {
    "semantic_units_with_accepted_component_sets": 38,
    "semantic_requirements_with_accepted_component_sets": 38,
    "semantic_units_remaining_without_accepted_component_set": 1278,
    "semantic_requirements_remaining_without_accepted_component_set": 1353,
    "subject_disposed_units_total": 39,
    "subject_disposed_requirements_total": 39,
    "subject_review_units_remaining": 1277,
    "subject_review_requirements_remaining": 1352,
    "canonical_component_refs_reused_unique": 119,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 68,
    "accepted_bounded_ru_semantics_total": 77,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER.update({
    "semantic_units_with_accepted_component_sets": 39,
    "semantic_requirements_with_accepted_component_sets": 39,
    "semantic_units_remaining_without_accepted_component_set": 1277,
    "semantic_requirements_remaining_without_accepted_component_set": 1352,
    "subject_disposed_units_total": 40,
    "subject_disposed_requirements_total": 40,
    "subject_review_units_remaining": 1276,
    "subject_review_requirements_remaining": 1351,
    "canonical_component_refs_reused_unique": 120,
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
        raise ValueError("current-v14 builder blob drift")
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.17.0" or data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v14 authority drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v14 aggregate drift: {key}")
    if len(data.get("accepted_authorities") or []) != 61:
        raise ValueError("current-v14 accepted authority count drift")

    previous = data.get("newly_accepted_bounded_subject_semantic") or {}
    if previous.get("semantic_id") != SEMANTIC:
        raise ValueError("current-v14 predecessor semantic drift")
    if previous.get("authority_sha256") != SEMANTIC_AUTH_SHA:
        raise ValueError("current-v14 semantic authority SHA drift")
    if previous.get("independent_verification_item_ids") != EVID:
        raise ValueError("current-v14 semantic evidence drift")
    targets = previous.get("targets") or []
    expected_targets = [
        {
            "admission_unit_id": UNIT,
            "requirement_id": REQ,
            "source_locator": LOCATOR,
        },
        {
            "admission_unit_id": SIBLING_UNIT,
            "requirement_id": SIBLING_REQ,
            "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.3",
        },
    ]
    if targets != expected_targets:
        raise ValueError("current-v14 sound-changes target set drift")
    if previous.get("object_acceptance_effect") != "NONE_UNTIL_SEPARATE_EXACT_OBJECT_ACCEPTANCE_FOR_EACH_TARGET":
        raise ValueError("current-v14 object acceptance boundary weakened")

    semantic_auth = json.loads(SEMANTIC_AUTH.read_text(encoding="utf-8"))
    if hashlib.sha256(canonical_json(semantic_auth)).hexdigest() != SEMANTIC_AUTH_SHA:
        raise ValueError("sound-changes semantic authority SHA drift")
    if semantic_auth.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_SOUND_CHANGES_IN_SPEECH_FLOW_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("sound-changes semantic status drift")
    decisions = semantic_auth.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("sound-changes semantic identity drift")
    if decisions[0].get("independent_verification_item_ids") != EVID:
        raise ValueError("sound-changes semantic evidence drift")
    next_work = semantic_auth.get("next_exact_work") or {}
    if next_work.get("target_count") != 2:
        raise ValueError("sound-changes exact target count drift")
    if next_work.get("component_specific_evidence_ids") != EVID:
        raise ValueError("sound-changes exact evidence drift")
    if next_work.get("separate_exact_object_acceptance_required") is not True:
        raise ValueError("separate exact object acceptance boundary drift")

    authority = json.loads(OBJECT_AUTH.read_text(encoding="utf-8"))
    verify_embedded_sha(authority, OBJECT_AUTH_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_SOUND_CHANGES_CANONICAL_COMPONENT_SET":
        raise ValueError("sound-changes object authority status drift")
    if authority.get("current_launch_progress_v14_base_head_sha") != BASE_HEAD:
        raise ValueError("sound-changes object base head drift")
    if authority.get("current_launch_progress_v14_normalized_sha256") != BASE_SHA:
        raise ValueError("sound-changes object base normalized SHA drift")
    if authority.get("semantic_acceptance_authority_sha256") != SEMANTIC_AUTH_SHA:
        raise ValueError("sound-changes semantic authority binding drift")

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
        "independent_evidence_items": 6,
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    for key, expected in exact.items():
        if decision.get(key) != expected:
            raise ValueError(f"sound-changes object authority identity drift: {key}")

    mastery = decision.get("mastery_boundary") or {}
    for key in (
        "accepted_bounded_subject_semantic_required",
        "component_specific_independent_evidence_required",
        "validated_sound_changes_item_may_support_only_its_single_canonical_ref",
    ):
        if mastery.get(key) is not True:
            raise ValueError(f"sound-changes mastery boundary weakened: {key}")
    for key in (
        "generic_ru01_attempt_can_emit_exact_component_mastery",
        "sound_letter_relation_evidence_can_substitute_for_sound_changes",
        "vowel_consonant_features_evidence_can_substitute_for_sound_changes",
        "word_analysis_evidence_can_substitute_for_sound_changes",
        "phonetic_transcription_evidence_can_substitute_for_sound_changes",
        "normative_pronunciation_or_stress_evidence_can_substitute_for_sound_changes",
        "shared_evidence_can_close_sibling_source_objects_without_separate_acceptance",
    ):
        if mastery.get(key) is not False:
            raise ValueError(f"sound-changes mastery boundary weakened: {key}")
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
    if group.get("accepted_component_set_count") != 9:
        raise ValueError("current-v14 RU01 accepted set count drift")
    if UNIT not in set(map(str, group.get("admission_unit_ids") or [])):
        raise ValueError("sound-changes target unit missing from RU01 group")
    rows = [r for r in group.get("requirements") or [] if r.get("requirement_id") == REQ]
    if len(rows) != 1:
        raise ValueError("sound-changes target requirement not unique")
    row = rows[0]
    for key, expected in (
        ("source_id", SOURCE),
        ("document_id", DOC),
        ("page", PAGE),
        ("code", CODE),
        ("source_locator", LOCATOR),
    ):
        if row.get(key) != expected:
            raise ValueError(f"sound-changes source identity drift: {key}")

    accepted_sets = [
        item
        for g in data.get("semantic_review_groups") or []
        for item in g.get("accepted_component_sets") or []
        if isinstance(item, dict)
    ]
    if any(item.get("admission_unit_id") == UNIT or item.get("requirement_id") == REQ for item in accepted_sets):
        raise ValueError("sound-changes EDSOO object already accepted")
    if any(item.get("admission_unit_id") == SIBLING_UNIT or item.get("requirement_id") == SIBLING_REQ for item in accepted_sets):
        raise ValueError("sound-changes OGE sibling unexpectedly already accepted")
    if any(item.get("id") == AUTH_ID for item in data.get("accepted_authorities") or [] if isinstance(item, dict)):
        raise ValueError("sound-changes object authority already integrated")
    semantic_authorities = [
        item for item in data.get("accepted_authorities") or []
        if isinstance(item, dict) and item.get("id") == "RU01_SOUND_CHANGES_IN_SPEECH_FLOW_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
    ]
    if len(semantic_authorities) != 1 or semantic_authorities[0].get("sha256") != SEMANTIC_AUTH_SHA:
        raise ValueError("accepted sound-changes semantic authority missing from current-v14")

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
            "base_current_v14_normalized_sha256": BASE_SHA,
            "accepted_subject_semantic_authority_sha256": SEMANTIC_AUTH_SHA,
            "accepted_authority_normalized_sha256": OBJECT_AUTH_SHA,
            "component_specific_independent_evidence_items": 6,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    group.setdefault("accepted_component_sets", []).append(projection)
    group["accepted_component_set_count"] = len(group["accepted_component_sets"])
    if group["accepted_component_set_count"] != 10:
        raise ValueError("sound-changes EDSOO accepted-set count drift")
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
            raise ValueError(f"post-sound-changes-EDSOO-object aggregate drift: {key}")
    if len(data["accepted_authorities"]) != 62:
        raise ValueError("post-sound-changes-EDSOO authority count drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery must remain zero")

    all_sets = [
        item
        for g in data.get("semantic_review_groups") or []
        for item in g.get("accepted_component_sets") or []
        if isinstance(item, dict)
    ]
    if any(item.get("admission_unit_id") == SIBLING_UNIT or item.get("requirement_id") == SIBLING_REQ for item in all_sets):
        raise ValueError("sound-changes OGE sibling auto-closed")

    data["schema_version"] = "0.18.0"
    data["base_current_launch_progress_v14_head_sha"] = BASE_HEAD
    data["base_current_launch_progress_v14_builder_git_blob_sha1"] = BASE_BLOB
    data["base_current_launch_progress_v14_normalized_sha256"] = BASE_SHA
    data["newly_accepted_exact_object"] = {
        "accepted_authority_id": AUTH_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "accepted_semantic_ref": SEMANTIC,
        "component_specific_independent_evidence_ids": EVID,
        "sibling_source_objects_accepted": 0,
        "remaining_same_signature_target": {
            "admission_unit_id": SIBLING_UNIT,
            "requirement_id": SIBLING_REQ,
            "status": "PENDING_SEPARATE_EXACT_OBJECT_ACCEPTANCE",
        },
    }
    data.setdefault("policy", {})["ru01_sound_changes_object_requires_prior_bounded_subject_semantic_acceptance"] = True
    data["policy"]["ru01_sound_changes_object_requires_component_specific_independent_evidence"] = True
    data["policy"]["generic_ru01_attempt_can_emit_exact_sound_changes_mastery"] = False
    data["policy"]["ru01_shared_sound_changes_evidence_can_close_sibling_source_objects_without_separate_acceptance"] = False
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
        print("RUSSIAN_RU01_SOUND_CHANGES_P187_4_1_3_EXACT_OBJECT_ACCEPTANCE=PASS")
        print("ACCEPTED_UNIT=" + UNIT)
        print("ACCEPTED_REQUIREMENT=" + REQ)
        print("EXACT_COMPONENT_REFS=1")
        print("INDEPENDENT_EVIDENCE_ITEMS=6")
        print("ADDITIONAL_SIBLING_RU01_OBJECTS_ACCEPTED=0")
        print(f"ACCEPTED_AUTHORITIES={len(data['accepted_authorities'])}")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={summary['subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['subject_review_requirements_remaining']}")
        print(f"FALSE_EXACT_MASTERY={summary['false_exact_mastery_admissions']}")
        print("NORMALIZED_SHA256=" + data["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
