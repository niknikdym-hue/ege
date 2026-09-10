#!/usr/bin/env python3
"""Current Russian launch progress after bounded RU01 sound-system semantic acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v24.py"
ADEQUACY = HERE / "build_ru01_sound_system_content_adequacy_review.py"
ACCEPTANCE = HERE / "RU01-SOUND-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

AUTHORITY_ID = "RU01_SOUND_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-sound-system"
VERIFICATION_IDS = [f"p01-u12-v{i}" for i in range(1, 6)]
FORBIDDEN_COMPONENT_EVIDENCE = [
    *[f"p01-u9-v{i}" for i in range(1, 6)],
    *[f"p01-u10-v{i}" for i in range(1, 6)],
]
TARGET = {
    "admission_unit_id": "RAU-5a6511267f156745f93c",
    "requirement_id": "RSK-EDSOO59-4-1-P181",
    "sound_characterization_clause_id": "EDSOO59-P181-4.1-A",
    "sound_letter_relation_clause_id": "EDSOO59-P181-4.1-B",
    "sound_system_clause_id": "EDSOO59-P181-4.1-C",
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
    "accepted_bounded_ru_subject_semantics": 74,
    "accepted_bounded_ru_semantics_total": 83,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER["accepted_bounded_ru_subject_semantics"] = 75
EXPECTED_AFTER["accepted_bounded_ru_semantics_total"] = 84


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_progress() -> dict[str, Any]:
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.26.0":
        raise ValueError("current-v24 schema drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v24 aggregate drift: {key}")
    accepted_authorities = data.get("accepted_authorities") or []
    if len(accepted_authorities) != 70:
        raise ValueError("current-v24 accepted authority count drift")
    predecessor = data.get("newly_accepted_bounded_subject_semantic") or {}
    if predecessor.get("semantic_id") != "ru-phonetics-sound-characterization":
        raise ValueError("current-v24 predecessor semantic drift")
    if predecessor.get("independent_verification_item_ids") != [f"p01-u11-v{i}" for i in range(1, 6)]:
        raise ValueError("current-v24 predecessor evidence drift")
    if predecessor.get("parent_object_count_requiring_future_complete_component_set_acceptance") != 1:
        raise ValueError("current-v24 parent-object frontier drift")

    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_SOUND_SYSTEM_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise ValueError("sound-system adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate != {
        "semantic_id": SEMANTIC,
        "source_taxonomy_id": "sound_system",
        "source_clause_ids": [TARGET["sound_system_clause_id"]],
        "semantic_ref_status": "PROPOSED_NOT_CANONICAL",
    }:
        raise ValueError("sound-system candidate identity drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "aeba08fe00dbe5626748427e2792e196976b8256":
        raise ValueError("sound-system learner content blob drift")
    if learner.get("new_integrated_verification_ids") != VERIFICATION_IDS:
        raise ValueError("sound-system integrated evidence identity drift")
    if learner.get("forbidden_component_parent_evidence_ids") != FORBIDDEN_COMPONENT_EVIDENCE:
        raise ValueError("sound-system forbidden component evidence drift")
    for key in (
        "registered_user_identity_required",
        "exact_item_identity_required",
        "server_owned_received_at_required",
        "durable_evidence_event_required_before_future_canonical_write",
    ):
        if learner.get(key) is not True:
            raise ValueError(f"sound-system PEIS boundary drift: {key}")
    adequacy_decision = adequacy.get("adequacy_decision") or {}
    if adequacy_decision.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise ValueError("sound-system adequacy next-state drift")
    if adequacy_decision.get("semantic_admission_by_this_review") is not False:
        raise ValueError("sound-system adequacy self-admitted semantic")
    for key in (
        "vowel_and_consonant_subsystems_integrated",
        "subsystem_feature_boundaries_preserved",
        "new_parent_specific_evidence_required",
        "old_component_evidence_not_reused_as_parent_evidence",
        "sound_letter_boundary_preserved",
        "normative_pronunciation_not_inferred",
        "normative_stress_not_inferred",
    ):
        if adequacy_decision.get(key) is not True:
            raise ValueError(f"sound-system adequacy boundary weakened: {key}")
    for key in (
        "object_level_admission_units_closed",
        "object_level_requirements_closed",
        "exact_mastery_admissions",
        "false_exact_mastery_admissions",
    ):
        if adequacy_decision.get(key) != 0:
            raise ValueError(f"sound-system adequacy admission drift: {key}")

    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_SOUND_SYSTEM_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("sound-system semantic acceptance status drift")
    authority = acceptance.get("authority") or {}
    if authority.get("content_adequacy_exact_head_gate") != {
        "workflow": "Russian RU01 sound system content adequacy",
        "run_id": 34534813456,
        "head_sha": "bfdb31555860858f9bad8f0ad74021637764fbb6",
        "conclusion": "SUCCESS",
    }:
        raise ValueError("sound-system exact-head adequacy authority drift")
    if authority.get("source_clauses") != [{
        "clause_id": TARGET["sound_system_clause_id"],
        "admission_unit_id": TARGET["admission_unit_id"],
        "requirement_id": TARGET["requirement_id"],
        "source_locator": TARGET["source_locator"],
        "official_requirement": "характеризовать систему звуков",
    }]:
        raise ValueError("sound-system source-clause authority drift")
    decisions = acceptance.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("sound-system semantic decision drift")
    if decisions[0].get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise ValueError("sound-system accepted evidence drift")
    if decisions[0].get("forbidden_reused_component_evidence_item_ids") != FORBIDDEN_COMPONENT_EVIDENCE:
        raise ValueError("sound-system forbidden component-evidence reuse drift")
    if decisions[0].get("parent_object_binding_status") != "NOT_BOUND_UNTIL_SEPARATE_EXACT_HEAD_PARENT_OBJECT_GATE":
        raise ValueError("sound-system semantic acceptance improperly binds parent object")
    policy = acceptance.get("policy") or {}
    if policy.get("subject_semantic_acceptance_can_reduce_parent_object_counts") is not False:
        raise ValueError("sound-system object-count boundary weakened")
    if policy.get("separate_exact_parent_object_component_set_acceptance_required") is not True:
        raise ValueError("separate sound-system parent-object acceptance no longer required")
    if policy.get("parent_object_can_close_without_separate_exact_head_object_gate") is not False:
        raise ValueError("sound-system parent-object early closure opened")
    if policy.get("generic_ru01_result_can_emit_exact_component_mastery") is not False:
        raise ValueError("generic RU01 exact sound-system mastery opened")
    if policy.get("p01_u9_or_u10_component_evidence_may_be_reused_as_parent_evidence") is not False:
        raise ValueError("component evidence auto-promotion opened")
    if (acceptance.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("sound-system semantic false exact mastery drift")

    if any(row.get("id") == AUTHORITY_ID for row in accepted_authorities if isinstance(row, dict)):
        raise ValueError("sound-system semantic authority already integrated")

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
        raise ValueError("sound-system parent object exact-bound before separate object gate")

    all_requirements = [
        row
        for group in data.get("semantic_review_groups") or []
        if isinstance(group, dict)
        for row in group.get("requirements") or []
        if isinstance(row, dict)
    ]
    matches = [row for row in all_requirements if row.get("requirement_id") == TARGET["requirement_id"]]
    if len(matches) != 1:
        raise ValueError("sound-system parent requirement missing or duplicated")
    if matches[0].get("source_locator") != TARGET["source_locator"]:
        raise ValueError("sound-system parent source locator drift")

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
            raise ValueError(f"post-sound-system aggregate drift: {key}")
    if len(accepted_authorities) != 71:
        raise ValueError("post-sound-system authority count drift")

    base_sha = data.get("normalized_sha256")
    if not isinstance(base_sha, str) or len(base_sha) != 64:
        raise ValueError("current-v24 normalized SHA missing")
    data["schema_version"] = "0.27.0"
    data["base_current_launch_progress_v24_normalized_sha256"] = base_sha
    data["newly_accepted_bounded_subject_semantic"] = {
        "authority_id": AUTHORITY_ID,
        "semantic_id": SEMANTIC,
        "authority_sha256": authority_sha,
        "independent_verification_item_ids": VERIFICATION_IDS,
        "forbidden_reused_component_evidence_item_ids": FORBIDDEN_COMPONENT_EVIDENCE,
        "source_clause_ids": [TARGET["sound_system_clause_id"]],
        "parent_object_count_requiring_future_complete_component_set_acceptance": 1,
        "parent_objects_remain_pending": [{
            "admission_unit_id": TARGET["admission_unit_id"],
            "requirement_id": TARGET["requirement_id"],
            "sound_characterization_clause_id": TARGET["sound_characterization_clause_id"],
            "sound_letter_relation_clause_id": TARGET["sound_letter_relation_clause_id"],
            "sound_system_clause_id": TARGET["sound_system_clause_id"],
        }],
        "adjacent_semantics_remain_separate": [
            "ru-phonetics-sound-characterization",
            "ru-phonetics-sound-letter-relation",
            "ru-phonetics-vowel-system",
            "ru-phonetics-consonant-system",
            "ru-orthoepy-normative-pronunciation",
            "ru-orthoepy-normative-stress",
        ],
        "object_acceptance_effect": "NONE_PENDING_SEPARATE_EXACT_HEAD_PARENT_OBJECT_COMPONENT_SET_GATE",
    }
    data.setdefault("policy", {})["ru01_sound_system_semantic_acceptance_requires_new_integrated_parent_evidence"] = True
    data["policy"]["ru01_sound_system_semantic_acceptance_can_close_parent_object"] = False
    data["policy"]["generic_ru01_attempt_can_emit_exact_sound_system_mastery"] = False
    data["policy"]["p01_u9_or_u10_component_evidence_can_substitute_for_integrated_sound_system_evidence"] = False
    data["policy"]["sound_system_acceptance_can_substitute_for_orthoepy"] = False
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
        print("RUSSIAN_RU01_SOUND_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
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
