#!/usr/bin/env python3
"""Current Russian launch progress after bounded RU01 consonant-system semantic acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v22.py"
ADEQUACY = HERE / "build_ru01_consonant_system_content_adequacy_review.py"
ACCEPTANCE = HERE / "RU01-CONSONANT-SYSTEM-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

AUTHORITY_ID = "RU01_CONSONANT_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-consonant-system"
VERIFICATION_IDS = [f"p01-u10-v{i}" for i in range(1, 6)]
TARGETS = [
    {
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "requirement_id": "RSK-EDSOO59-4-1-P187",
        "consonant_system_clause_id": "EDSOO59-P187-4.1.2",
        "source_locator": "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1",
    },
    {
        "admission_unit_id": "RAU-3916b5e3da77ed038830",
        "requirement_id": "RSK-OGE_COD-4-1-P020",
        "consonant_system_clause_id": "OGE-COD-P020-4.1.2",
        "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.20 4.1",
    },
]
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
    "accepted_bounded_ru_subject_semantics": 72,
    "accepted_bounded_ru_semantics_total": 81,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER["accepted_bounded_ru_subject_semantics"] = 73
EXPECTED_AFTER["accepted_bounded_ru_semantics_total"] = 82


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_progress() -> dict[str, Any]:
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.24.0":
        raise ValueError("current-v22 schema drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v22 aggregate drift: {key}")
    accepted_authorities = data.get("accepted_authorities") or []
    if len(accepted_authorities) != 68:
        raise ValueError("current-v22 accepted authority count drift")
    predecessor = data.get("newly_accepted_bounded_subject_semantic") or {}
    if predecessor.get("semantic_id") != "ru-phonetics-vowel-system":
        raise ValueError("current-v22 predecessor semantic drift")
    if predecessor.get("independent_verification_item_ids") != [f"p01-u9-v{i}" for i in range(1, 6)]:
        raise ValueError("current-v22 predecessor evidence drift")
    if predecessor.get("parent_object_count_requiring_future_complete_component_set_acceptance") != 2:
        raise ValueError("current-v22 parent-object frontier drift")

    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_CONSONANT_SYSTEM_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise ValueError("consonant-system adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate.get("semantic_id") != SEMANTIC or candidate.get("source_taxonomy_id") != "consonant_system":
        raise ValueError("consonant-system candidate identity drift")
    if candidate.get("source_clause_ids") != ["EDSOO59-P187-4.1.2", "OGE-COD-P020-4.1.2"]:
        raise ValueError("consonant-system candidate source-clause drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "3fd8716766da403ccd3bcfd3cca2d97af5631db6":
        raise ValueError("consonant-system learner content blob drift")
    if learner.get("component_specific_verification_ids") != VERIFICATION_IDS:
        raise ValueError("consonant-system evidence identity drift")
    for key in (
        "registered_user_identity_required",
        "exact_item_identity_required",
        "server_owned_received_at_required",
        "durable_evidence_event_required_before_future_canonical_write",
    ):
        if learner.get(key) is not True:
            raise ValueError(f"consonant-system PEIS boundary drift: {key}")
    adequacy_decision = adequacy.get("adequacy_decision") or {}
    if adequacy_decision.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise ValueError("consonant-system adequacy next-state drift")
    if adequacy_decision.get("semantic_admission_by_this_review") is not False:
        raise ValueError("consonant-system adequacy self-admitted semantic")
    if adequacy_decision.get("object_level_admission_units_closed") != 0 or adequacy_decision.get("object_level_requirements_closed") != 0:
        raise ValueError("consonant-system adequacy self-closed parent object")
    if adequacy_decision.get("false_exact_mastery_admissions") != 0:
        raise ValueError("consonant-system adequacy false exact mastery drift")
    for key in (
        "consonant_sounds_and_letters_separated",
        "voicing_and_devoicing_system_covered",
        "hardness_and_softness_system_covered",
        "paired_and_unpaired_cases_covered",
        "partial_vowel_consonant_feature_owner_not_promoted_to_full_system",
        "vowel_system_separated",
        "stress_and_normative_pronunciation_separated",
        "sound_composition_and_sound_letter_relation_do_not_substitute",
    ):
        if adequacy_decision.get(key) is not True:
            raise ValueError(f"consonant-system adequacy boundary weakened: {key}")

    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_CONSONANT_SYSTEM_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("consonant-system semantic acceptance status drift")
    authority = acceptance.get("authority") or {}
    if authority.get("content_adequacy_exact_head_gate") != {
        "workflow": "Russian RU01 consonant system content adequacy",
        "run_id": 34421078487,
        "head_sha": "d3cc6d3fa08c902a9f123d9364e6bdb6b95ad784",
        "conclusion": "SUCCESS",
    }:
        raise ValueError("consonant-system exact-head adequacy authority drift")
    decisions = acceptance.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("consonant-system semantic decision drift")
    if decisions[0].get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise ValueError("consonant-system accepted evidence drift")
    if decisions[0].get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_EITHER_BROAD_4_1_PARENT_OBJECT":
        raise ValueError("consonant-system semantic acceptance improperly binds parent object")
    policy = acceptance.get("policy") or {}
    if policy.get("subject_semantic_acceptance_can_reduce_parent_object_counts") is not False:
        raise ValueError("consonant-system object-count boundary weakened")
    if policy.get("separate_exact_parent_object_component_set_acceptance_required") is not True:
        raise ValueError("separate consonant-system parent-object acceptance no longer required")
    if policy.get("parent_object_can_close_before_all_required_clauses_have_exact_accepted_owners_and_component_specific_evidence") is not False:
        raise ValueError("consonant-system parent-object early closure opened")
    if policy.get("generic_ru01_result_can_emit_exact_component_mastery") is not False:
        raise ValueError("generic RU01 exact consonant-system mastery opened")
    for key in (
        "partial_vowel_consonant_feature_semantic_may_substitute",
        "vowel_system_semantic_may_substitute",
        "sound_letter_relation_semantic_may_substitute",
        "sound_composition_semantic_may_substitute",
        "normative_pronunciation_semantic_may_substitute",
        "normative_stress_semantic_may_substitute",
    ):
        if policy.get(key) is not False:
            raise ValueError(f"consonant-system adjacent semantic substitution opened: {key}")
    if (acceptance.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("consonant-system semantic false exact mastery drift")

    if any(row.get("id") == AUTHORITY_ID for row in accepted_authorities if isinstance(row, dict)):
        raise ValueError("consonant-system semantic authority already integrated")

    accepted_sets = [
        row
        for group in data.get("semantic_review_groups") or []
        if isinstance(group, dict)
        for row in group.get("accepted_component_sets") or []
        if isinstance(row, dict)
    ]
    for target in TARGETS:
        if any(
            row.get("admission_unit_id") == target["admission_unit_id"]
            or row.get("requirement_id") == target["requirement_id"]
            for row in accepted_sets
        ):
            raise ValueError("consonant-system parent object exact-bound before all broad-header components are accepted")

    all_requirements = [
        row
        for group in data.get("semantic_review_groups") or []
        if isinstance(group, dict)
        for row in group.get("requirements") or []
        if isinstance(row, dict)
    ]
    for target in TARGETS:
        matches = [row for row in all_requirements if row.get("requirement_id") == target["requirement_id"]]
        if len(matches) != 1:
            raise ValueError(f"consonant-system parent requirement missing or duplicated: {target['requirement_id']}")
        if matches[0].get("source_locator") != target["source_locator"]:
            raise ValueError(f"consonant-system parent source locator drift: {target['requirement_id']}")

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
            raise ValueError(f"post-consonant-system aggregate drift: {key}")
    if len(accepted_authorities) != 69:
        raise ValueError("post-consonant-system authority count drift")

    base_sha = data.get("normalized_sha256")
    if not isinstance(base_sha, str) or len(base_sha) != 64:
        raise ValueError("current-v22 normalized SHA missing")
    data["schema_version"] = "0.25.0"
    data["base_current_launch_progress_v22_normalized_sha256"] = base_sha
    data["newly_accepted_bounded_subject_semantic"] = {
        "authority_id": AUTHORITY_ID,
        "semantic_id": SEMANTIC,
        "authority_sha256": authority_sha,
        "independent_verification_item_ids": VERIFICATION_IDS,
        "source_clause_ids": [target["consonant_system_clause_id"] for target in TARGETS],
        "parent_object_count_requiring_future_complete_component_set_acceptance": 2,
        "parent_objects_remain_pending": [
            {
                "admission_unit_id": target["admission_unit_id"],
                "requirement_id": target["requirement_id"],
                "consonant_system_clause_id": target["consonant_system_clause_id"],
            }
            for target in TARGETS
        ],
        "adjacent_semantics_remain_separate": [
            "ru-phonetics-vowel-consonant-features",
            "ru-phonetics-vowel-system",
            "sound-letter-relation",
            "ru-phonetics-sound-composition-determination",
            "ru-phonetics-stress",
            "ru-orthoepy-normative-pronunciation",
        ],
        "object_acceptance_effect": "NONE_UNTIL_ALL_REQUIRED_BROAD_HEADER_CLAUSES_HAVE_EXACT_ACCEPTED_OWNERS_AND_COMPONENT_SPECIFIC_EVIDENCE_AND_SEPARATE_EXACT_HEAD_OBJECT_GATE_PASSES",
    }
    data.setdefault("policy", {})["ru01_consonant_system_semantic_acceptance_requires_component_specific_evidence"] = True
    data["policy"]["ru01_consonant_system_semantic_acceptance_can_close_parent_object"] = False
    data["policy"]["generic_ru01_attempt_can_emit_exact_consonant_system_mastery"] = False
    data["policy"]["partial_vowel_consonant_feature_can_substitute_for_full_consonant_system"] = False
    data["policy"]["vowel_sound_letter_composition_stress_or_pronunciation_can_substitute_for_consonant_system"] = False
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
        print("RUSSIAN_RU01_CONSONANT_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
        print("ACCEPTED_SUBJECT_SEMANTICS=1")
        print("PARENT_OBJECTS_PENDING=2")
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
