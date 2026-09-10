#!/usr/bin/env python3
"""Current Russian launch progress after bounded RU01 sound-characterization semantic acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v23.py"
ADEQUACY = HERE / "build_ru01_sound_characterization_content_adequacy_review.py"
ACCEPTANCE = HERE / "RU01-SOUND-CHARACTERIZATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

AUTHORITY_ID = "RU01_SOUND_CHARACTERIZATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-sound-characterization"
VERIFICATION_IDS = [f"p01-u11-v{i}" for i in range(1, 6)]
TARGET = {
    "admission_unit_id": "RAU-5a6511267f156745f93c",
    "requirement_id": "RSK-EDSOO59-4-1-P181",
    "sound_characterization_clause_id": "EDSOO59-P181-4.1-A",
    "source_locator": "EDSOO-RU-5-9-2025/EDSOO59 p.181 4.1",
}
EXPECTED_BASE = {
    "semantic_units_with_accepted_component_sets": 41,
    "semantic_requirements_with_accepted_component_sets": 41,
    "semantic_units_remaining_without_accepted_component_set": 1275,
    "semantic_requirements_remaining_without_accepted_component_set": 1350,
    "subject_disposed_units_total": 42,
    "subject_disposed_requirements_total": 42,
    "subject_review_units_remaining": 1274,
    "subject_review_requirements_remaining": 1349,
    "canonical_component_refs_reused_unique": 122,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 73,
    "accepted_bounded_ru_semantics_total": 82,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER["accepted_bounded_ru_subject_semantics"] = 74
EXPECTED_AFTER["accepted_bounded_ru_semantics_total"] = 83


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_progress() -> dict[str, Any]:
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.25.0":
        raise ValueError("current-v23 schema drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v23 aggregate drift: {key}")
    accepted_authorities = data.get("accepted_authorities") or []
    if len(accepted_authorities) != 69:
        raise ValueError("current-v23 accepted authority count drift")
    predecessor = data.get("newly_accepted_bounded_subject_semantic") or {}
    if predecessor.get("semantic_id") != "ru-phonetics-consonant-system":
        raise ValueError("current-v23 predecessor semantic drift")
    if predecessor.get("independent_verification_item_ids") != [f"p01-u10-v{i}" for i in range(1, 6)]:
        raise ValueError("current-v23 predecessor evidence drift")
    if predecessor.get("parent_object_count_requiring_future_complete_component_set_acceptance") != 2:
        raise ValueError("current-v23 parent-object frontier drift")

    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_SOUND_CHARACTERIZATION_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise ValueError("sound-characterization adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate.get("semantic_id") != SEMANTIC or candidate.get("source_taxonomy_id") != "sound_characterization":
        raise ValueError("sound-characterization candidate identity drift")
    if candidate.get("source_clause_ids") != ["EDSOO59-P181-4.1-A"]:
        raise ValueError("sound-characterization candidate source-clause drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "b150eb27fa112034b96d4bdb7c6d2f631c2b5979":
        raise ValueError("sound-characterization learner content blob drift")
    if learner.get("component_specific_verification_ids") != VERIFICATION_IDS:
        raise ValueError("sound-characterization evidence identity drift")
    for key in (
        "registered_user_identity_required",
        "exact_item_identity_required",
        "server_owned_received_at_required",
        "durable_evidence_event_required_before_future_canonical_write",
    ):
        if learner.get(key) is not True:
            raise ValueError(f"sound-characterization PEIS boundary drift: {key}")
    adequacy_decision = adequacy.get("adequacy_decision") or {}
    if adequacy_decision.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise ValueError("sound-characterization adequacy next-state drift")
    if adequacy_decision.get("semantic_admission_by_this_review") is not False:
        raise ValueError("sound-characterization adequacy self-admitted semantic")
    if adequacy_decision.get("object_level_admission_units_closed") != 0 or adequacy_decision.get("object_level_requirements_closed") != 0:
        raise ValueError("sound-characterization adequacy self-closed parent object")
    if adequacy_decision.get("false_exact_mastery_admissions") != 0:
        raise ValueError("sound-characterization adequacy false exact mastery drift")
    for key in (
        "explicit_sound_object_required_before_characterization",
        "vowel_and_consonant_feature_paths_distinguished",
        "sound_letter_boundary_preserved",
        "partial_vowel_consonant_feature_owner_not_promoted_to_exact_owner",
        "vowel_system_not_substituted",
        "consonant_system_not_substituted",
        "whole_sound_system_not_substituted",
        "normative_pronunciation_not_inferred",
    ):
        if adequacy_decision.get(key) is not True:
            raise ValueError(f"sound-characterization adequacy boundary weakened: {key}")

    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_SOUND_CHARACTERIZATION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("sound-characterization semantic acceptance status drift")
    authority = acceptance.get("authority") or {}
    if authority.get("content_adequacy_exact_head_gate") != {
        "workflow": "Russian RU01 sound characterization content adequacy",
        "run_id": 34482234747,
        "head_sha": "e3d79a08bf9f539a62fbf164b6e9c1b4e3d6f7cf",
        "conclusion": "SUCCESS",
    }:
        raise ValueError("sound-characterization exact-head adequacy authority drift")
    decisions = acceptance.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("sound-characterization semantic decision drift")
    if decisions[0].get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise ValueError("sound-characterization accepted evidence drift")
    if decisions[0].get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_BROAD_EDSOO59_P181_4_1_PARENT_OBJECT":
        raise ValueError("sound-characterization semantic acceptance improperly binds parent object")
    policy = acceptance.get("policy") or {}
    if policy.get("subject_semantic_acceptance_can_reduce_parent_object_counts") is not False:
        raise ValueError("sound-characterization object-count boundary weakened")
    if policy.get("separate_exact_parent_object_component_set_acceptance_required") is not True:
        raise ValueError("separate sound-characterization parent-object acceptance no longer required")
    if policy.get("parent_object_can_close_before_all_required_clauses_have_exact_accepted_owners_and_component_specific_evidence") is not False:
        raise ValueError("sound-characterization parent-object early closure opened")
    if policy.get("generic_ru01_result_can_emit_exact_component_mastery") is not False:
        raise ValueError("generic RU01 exact sound-characterization mastery opened")
    for key in (
        "partial_vowel_consonant_feature_semantic_may_substitute",
        "vowel_system_semantic_may_substitute",
        "consonant_system_semantic_may_substitute",
        "sound_system_semantic_may_substitute",
        "sound_letter_relation_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
    ):
        if policy.get(key) is not False:
            raise ValueError(f"sound-characterization adjacent semantic substitution opened: {key}")
    if (acceptance.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("sound-characterization semantic false exact mastery drift")

    if any(row.get("id") == AUTHORITY_ID for row in accepted_authorities if isinstance(row, dict)):
        raise ValueError("sound-characterization semantic authority already integrated")

    accepted_sets = [
        row
        for group in data.get("semantic_review_groups") or []
        if isinstance(group, dict)
        for row in group.get("accepted_component_sets") or []
        if isinstance(row, dict)
    ]
    if any(
        row.get("admission_unit_id") == TARGET["admission_unit_id"]
        or row.get("requirement_id") == TARGET["requirement_id"]
        for row in accepted_sets
    ):
        raise ValueError("sound-characterization parent object exact-bound before sound-system clause is resolved")

    all_requirements = [
        row
        for group in data.get("semantic_review_groups") or []
        if isinstance(group, dict)
        for row in group.get("requirements") or []
        if isinstance(row, dict)
    ]
    matches = [row for row in all_requirements if row.get("requirement_id") == TARGET["requirement_id"]]
    if len(matches) != 1:
        raise ValueError("sound-characterization parent requirement missing or duplicated")
    if matches[0].get("source_locator") != TARGET["source_locator"]:
        raise ValueError("sound-characterization parent source locator drift")

    authority_sha = hashlib.sha256(canonical_json(acceptance)).hexdigest()
    accepted_authorities.append({
        "id": AUTHORITY_ID,
        "authority_kind": "BOUNDED_SUBJECT_SEMANTIC",
        "sha256": authority_sha,
        "status": acceptance["status"],
        "accepted_admission_units": 0,
        "accepted_requirements": 0,
        "canonical_component_refs": 0,
        "accepted_route_semantics": 0,
        "accepted_subject_semantics": 1,
        "semantic_identity_admissions": 1,
    })

    summary["accepted_bounded_ru_subject_semantics"] += 1
    summary["accepted_bounded_ru_semantics_total"] += 1
    for key, expected in EXPECTED_AFTER.items():
        if summary.get(key) != expected:
            raise ValueError(f"post-sound-characterization aggregate drift: {key}")
    if len(accepted_authorities) != 70:
        raise ValueError("post-sound-characterization authority count drift")

    base_sha = data.get("normalized_sha256")
    if not isinstance(base_sha, str) or len(base_sha) != 64:
        raise ValueError("current-v23 normalized SHA missing")
    data["schema_version"] = "0.26.0"
    data["base_current_launch_progress_v23_normalized_sha256"] = base_sha
    data["newly_accepted_bounded_subject_semantic"] = {
        "authority_id": AUTHORITY_ID,
        "semantic_id": SEMANTIC,
        "authority_sha256": authority_sha,
        "independent_verification_item_ids": VERIFICATION_IDS,
        "source_clause_ids": [TARGET["sound_characterization_clause_id"]],
        "parent_object_count_requiring_future_complete_component_set_acceptance": 1,
        "parent_objects_remain_pending": [{
            "admission_unit_id": TARGET["admission_unit_id"],
            "requirement_id": TARGET["requirement_id"],
            "sound_characterization_clause_id": TARGET["sound_characterization_clause_id"],
        }],
        "adjacent_semantics_remain_separate": [
            "ru-phonetics-vowel-consonant-features",
            "ru-phonetics-vowel-system",
            "ru-phonetics-consonant-system",
            "ru-phonetics-sound-system",
            "ru-phonetics-sound-letter-relation",
            "ru-orthoepy-normative-pronunciation",
        ],
        "object_acceptance_effect": "NONE_UNTIL_EDSOO59_P181_4_1_SOUND_SYSTEM_CLAUSE_HAS_AN_EXACT_ACCEPTED_OWNER_AND_COMPONENT_SPECIFIC_EVIDENCE_AND_SEPARATE_EXACT_HEAD_OBJECT_GATE_PASSES",
    }
    data.setdefault("policy", {})["ru01_sound_characterization_semantic_acceptance_requires_component_specific_evidence"] = True
    data["policy"]["ru01_sound_characterization_semantic_acceptance_can_close_parent_object"] = False
    data["policy"]["generic_ru01_attempt_can_emit_exact_sound_characterization_mastery"] = False
    data["policy"]["partial_vowel_consonant_feature_can_substitute_for_sound_characterization"] = False
    data["policy"]["vowel_consonant_or_whole_sound_system_can_substitute_for_sound_characterization"] = False
    data["policy"]["sound_characterization_can_substitute_for_whole_sound_system"] = False
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
        print("RUSSIAN_RU01_SOUND_CHARACTERIZATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
        print("ACCEPTED_SUBJECT_SEMANTICS=1")
        print("PARENT_OBJECTS_PENDING=1")
        print("OBJECT_LEVEL_CLOSURES=0")
        print(f"ACCEPTED_AUTHORITIES={len(data['accepted_authorities'])}")
        print(f"ACCEPTED_BOUNDED_RU_SUBJECT_SEMANTICS={summary['accepted_bounded_ru_subject_semantics']}")
        print(f"ACCEPTED_BOUNDED_RU_SEMANTICS_TOTAL={summary['accepted_bounded_ru_semantics_total']}")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={summary['subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['subject_review_requirements_remaining']}")
        print(f"FALSE_EXACT_MASTERY={summary['false_exact_mastery_admissions']}")
        print(f"NORMALIZED_SHA256={data['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
