#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress after bounded RU01 phonetic-syllable semantic acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v19.py"
ADEQUACY = HERE / "build_ru01_phonetic_syllable_content_adequacy_review.py"
ACCEPTANCE = HERE / "RU01-PHONETIC-SYLLABLE-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

AUTHORITY_ID = "RU01_PHONETIC_SYLLABLE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-syllable"
VERIFICATION_IDS = [f"p01-u7-v{i}" for i in range(1, 6)]
TARGETS = [
    {
        "admission_unit_id": "RAU-5a6511267f156745f93c",
        "requirement_id": "RSK-EDSOO59-4-1-P187",
        "syllable_clause_id": "EDSOO59-P187-4.1.5",
        "source_locator": "EDSOO59 p.187 4.1",
    },
    {
        "admission_unit_id": "RAU-3916b5e3da77ed038830",
        "requirement_id": "RSK-OGE_COD-4-1-P020",
        "syllable_clause_id": "OGE-COD-P020-4.1.5",
        "source_locator": "OGE_COD p.20 4.1",
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
    "accepted_bounded_ru_subject_semantics": 69,
    "accepted_bounded_ru_semantics_total": 78,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER["accepted_bounded_ru_subject_semantics"] = 70
EXPECTED_AFTER["accepted_bounded_ru_semantics_total"] = 79


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_progress() -> dict[str, Any]:
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.21.0":
        raise ValueError("current-v19 schema drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v19 aggregate drift: {key}")
    accepted_authorities = data.get("accepted_authorities") or []
    if len(accepted_authorities) != 65:
        raise ValueError("current-v19 accepted authority count drift")
    predecessor = data.get("newly_accepted_exact_object") or {}
    if predecessor.get("admission_unit_id") != "RAU-b6f5dff93864358672bc" or predecessor.get("requirement_id") != "RSK-OGE_COD-2-1-P010":
        raise ValueError("current-v19 predecessor exact object drift")
    if predecessor.get("accepted_component_refs") != [
        "ru-phonetics-vowel-consonant-features",
        "ru-phonetics-sound-composition-determination",
    ]:
        raise ValueError("current-v19 predecessor component set drift")

    adequacy = runpy.run_path(str(ADEQUACY))["build_review"]()
    if adequacy.get("status") != "CENTRAL_BRAIN_RU01_PHONETIC_SYLLABLE_CONTENT_ADEQUACY_REVIEW_COMPLETE_NO_ADMISSION":
        raise ValueError("syllable adequacy predecessor drift")
    candidate = adequacy.get("candidate") or {}
    if candidate.get("semantic_id") != SEMANTIC or candidate.get("source_taxonomy_id") != "phonetic_syllable":
        raise ValueError("syllable candidate identity drift")
    if candidate.get("source_clause_ids") != ["EDSOO59-P187-4.1.5", "OGE-COD-P020-4.1.5"]:
        raise ValueError("syllable candidate source-clause drift")
    learner = adequacy.get("learner_content") or {}
    if learner.get("git_blob_sha1") != "24281db6ee3d5cea24656c1e5e0be9b787392a08":
        raise ValueError("syllable learner content blob drift")
    if learner.get("component_specific_verification_ids") != VERIFICATION_IDS:
        raise ValueError("syllable evidence identity drift")
    adequacy_decision = adequacy.get("adequacy_decision") or {}
    if adequacy_decision.get("next_status") != "READY_FOR_SEPARATE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE":
        raise ValueError("syllable adequacy next-state drift")
    if adequacy_decision.get("semantic_admission_by_this_review") is not False:
        raise ValueError("syllable adequacy self-admitted semantic")
    if adequacy_decision.get("object_level_admission_units_closed") != 0 or adequacy_decision.get("object_level_requirements_closed") != 0:
        raise ValueError("syllable adequacy self-closed parent object")
    if adequacy_decision.get("false_exact_mastery_admissions") != 0:
        raise ValueError("syllable adequacy false exact mastery drift")

    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETIC_SYLLABLE_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("syllable semantic acceptance status drift")
    authority = acceptance.get("authority") or {}
    if authority.get("content_adequacy_exact_head_gate") != {
        "workflow": "Russian RU01 phonetic syllable content adequacy",
        "run_id": 34337083039,
        "head_sha": "874b8a57307c4cfc1ce11cd9ed22fd0970ffa552",
        "conclusion": "SUCCESS",
    }:
        raise ValueError("syllable exact-head adequacy authority drift")
    decisions = acceptance.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("syllable semantic decision drift")
    if decisions[0].get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise ValueError("syllable accepted evidence drift")
    if decisions[0].get("parent_object_binding_status") != "NOT_BOUND_AS_COMPLETE_COMPONENT_SET_TO_EITHER_BROAD_4_1_PARENT_OBJECT":
        raise ValueError("syllable semantic acceptance improperly binds parent object")
    policy = acceptance.get("policy") or {}
    if policy.get("subject_semantic_acceptance_can_reduce_parent_object_counts") is not False:
        raise ValueError("syllable semantic acceptance object-count boundary weakened")
    if policy.get("separate_exact_parent_object_component_set_acceptance_required") is not True:
        raise ValueError("separate syllable parent-object component-set acceptance no longer required")
    if policy.get("parent_object_can_close_before_all_required_clauses_have_exact_accepted_owners_and_component_specific_evidence") is not False:
        raise ValueError("syllable parent-object early closure opened")
    if policy.get("generic_ru01_result_can_emit_exact_component_mastery") is not False:
        raise ValueError("generic RU01 exact syllable mastery opened")
    if (acceptance.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("syllable semantic false exact mastery drift")

    if any(row.get("id") == AUTHORITY_ID for row in accepted_authorities if isinstance(row, dict)):
        raise ValueError("syllable semantic authority already integrated")

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
            raise ValueError("syllable parent object exact-bound before all broad-header components are accepted")

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
            raise ValueError(f"syllable parent requirement missing or duplicated: {target['requirement_id']}")
        if matches[0].get("source_locator") != target["source_locator"]:
            raise ValueError(f"syllable parent source locator drift: {target['requirement_id']}")

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
            raise ValueError(f"post-syllable-semantic aggregate drift: {key}")
    if len(accepted_authorities) != 66:
        raise ValueError("post-syllable-semantic authority count drift")

    base_sha = data.get("normalized_sha256")
    if not isinstance(base_sha, str) or len(base_sha) != 64:
        raise ValueError("current-v19 normalized SHA missing")
    data["schema_version"] = "0.22.0"
    data["base_current_launch_progress_v19_normalized_sha256"] = base_sha
    data["newly_accepted_bounded_subject_semantic"] = {
        "authority_id": AUTHORITY_ID,
        "semantic_id": SEMANTIC,
        "authority_sha256": authority_sha,
        "independent_verification_item_ids": VERIFICATION_IDS,
        "source_clause_ids": [target["syllable_clause_id"] for target in TARGETS],
        "parent_object_count_requiring_future_complete_component_set_acceptance": 2,
        "parent_objects_remain_pending": [
            {
                "admission_unit_id": target["admission_unit_id"],
                "requirement_id": target["requirement_id"],
                "syllable_clause_id": target["syllable_clause_id"],
            }
            for target in TARGETS
        ],
        "object_acceptance_effect": "NONE_UNTIL_ALL_REQUIRED_BROAD_HEADER_CLAUSES_HAVE_EXACT_ACCEPTED_OWNERS_AND_COMPONENT_SPECIFIC_EVIDENCE_AND_SEPARATE_EXACT_HEAD_OBJECT_GATE_PASSES",
    }
    data.setdefault("policy", {})["ru01_phonetic_syllable_semantic_acceptance_requires_component_specific_evidence"] = True
    data["policy"]["ru01_phonetic_syllable_semantic_acceptance_can_close_parent_object"] = False
    data["policy"]["generic_ru01_attempt_can_emit_exact_syllable_mastery"] = False
    data["policy"]["word_transfer_or_normative_stress_can_substitute_for_phonetic_syllable"] = False
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
        print("RUSSIAN_RU01_PHONETIC_SYLLABLE_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
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
