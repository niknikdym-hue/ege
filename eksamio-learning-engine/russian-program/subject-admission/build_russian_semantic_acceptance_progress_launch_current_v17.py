#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress after bounded RU01 sound-composition semantic acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v16.py"
READINESS = HERE / "build_ru01_sound_composition_content_readiness.py"
ACCEPTANCE = HERE / "RU01-SOUND-COMPOSITION-DETERMINATION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

BASE_SHA = "43ccb3968f98540d32e54ef99c1c73b864c55caea22289b9e2764d77e32fc147"
BASE_HEAD = "5dad71b64577f0e51b94fc0191fb4b1c3b6fb543"
AUTHORITY_ID = "RU01_SOUND_COMPOSITION_DETERMINATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-sound-composition-determination"
EXISTING_PARTIAL_COMPONENT = "ru-phonetics-vowel-consonant-features"
VERIFICATION_IDS = [f"p01-u6-v{i}" for i in range(1, 7)]
TARGET = {
    "admission_unit_id": "RAU-b6f5dff93864358672bc",
    "requirement_id": "RSK-OGE_COD-2-1-P010",
    "source_locator": "FIPI-OGE-RU-2026-FINAL/OGE_COD p.10 2.1",
}

EXPECTED_BASE = {
    "semantic_units_with_accepted_component_sets": 40,
    "semantic_requirements_with_accepted_component_sets": 40,
    "semantic_units_remaining_without_accepted_component_set": 1276,
    "semantic_requirements_remaining_without_accepted_component_set": 1351,
    "subject_disposed_units_total": 41,
    "subject_disposed_requirements_total": 41,
    "subject_review_units_remaining": 1275,
    "subject_review_requirements_remaining": 1350,
    "canonical_component_refs_reused_unique": 120,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 68,
    "accepted_bounded_ru_semantics_total": 77,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER["accepted_bounded_ru_subject_semantics"] = 69
EXPECTED_AFTER["accepted_bounded_ru_semantics_total"] = 78


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_progress() -> dict[str, Any]:
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v16 normalized SHA drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v16 aggregate drift: {key}")
    if len(data.get("accepted_authorities") or []) != 63:
        raise ValueError("current-v16 accepted authority count drift")
    previous = data.get("newly_accepted_exact_object") or {}
    if previous.get("admission_unit_id") != "RAU-f709f1855bb0b8d104bc":
        raise ValueError("current-v16 predecessor exact object drift")
    if previous.get("requirement_id") != "RSK-OGE_COD-4-1-3-P021":
        raise ValueError("current-v16 predecessor exact requirement drift")

    readiness = runpy.run_path(str(READINESS))["build_readiness"]()
    if readiness.get("status") != "CENTRAL_BRAIN_RU01_SOUND_COMPOSITION_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED":
        raise ValueError("sound-composition content-readiness predecessor drift")
    if readiness.get("candidate_semantic_id") != SEMANTIC:
        raise ValueError("sound-composition candidate identity drift")
    target = readiness.get("target") or {}
    if target != {
        **TARGET,
        "already_bound_component_ref_preserved": EXISTING_PARTIAL_COMPONENT,
        "remaining_component_candidate": SEMANTIC,
    }:
        raise ValueError("sound-composition source-target drift")
    learner = readiness.get("learner_content") or {}
    if learner.get("independent_verification_ids") != VERIFICATION_IDS:
        raise ValueError("sound-composition evidence identity drift")
    if learner.get("independent_verification_count") != 6:
        raise ValueError("sound-composition evidence count drift")
    independence = readiness.get("evidence_independence") or {}
    if independence.get("adjacent_semantic_evidence_reused") is not False or independence.get("overlap") != []:
        raise ValueError("adjacent RU01 evidence reuse opened")
    if (readiness.get("summary") or {}).get("semantic_admissions") != 0:
        raise ValueError("content-readiness predecessor self-admitted semantic")
    if (readiness.get("summary") or {}).get("object_level_admission_units_closed") != 0:
        raise ValueError("content-readiness predecessor closed object")

    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_SOUND_COMPOSITION_DETERMINATION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("sound-composition semantic acceptance status drift")
    authority = acceptance.get("authority") or {}
    gate = authority.get("content_readiness_exact_head_gate") or {}
    if gate != {
        "workflow": "Russian RU01 sound composition content readiness",
        "run_id": 34255891455,
        "head_sha": "b4684caae27f1ff73a67b5e1cd176f567cfdc3e1",
        "conclusion": "SUCCESS",
    }:
        raise ValueError("sound-composition exact-head readiness gate drift")
    decisions = acceptance.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("sound-composition semantic decision drift")
    if decisions[0].get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise ValueError("sound-composition accepted evidence drift")
    if decisions[0].get("object_binding_status") != "NOT_BOUND_TO_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("sound-composition semantic acceptance improperly binds object")
    policy = acceptance.get("policy") or {}
    if policy.get("subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding") is not False:
        raise ValueError("semantic acceptance object-count boundary weakened")
    if policy.get("separate_exact_object_component_set_acceptance_required") is not True:
        raise ValueError("separate exact object component-set acceptance no longer required")
    if policy.get("semantic_acceptance_modifies_existing_partial_component") is not False:
        raise ValueError("existing partial component mutation opened")
    if policy.get("generic_ru01_result_can_emit_exact_component_mastery") is not False:
        raise ValueError("generic RU01 exact mastery opened")
    if (acceptance.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("sound-composition semantic false exact mastery drift")

    accepted_authorities = data.get("accepted_authorities") or []
    if any(row.get("id") == AUTHORITY_ID for row in accepted_authorities if isinstance(row, dict)):
        raise ValueError("sound-composition semantic authority already integrated")
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
            raise ValueError(f"post-sound-composition-semantic aggregate drift: {key}")
    if len(accepted_authorities) != 64:
        raise ValueError("post-sound-composition-semantic authority count drift")

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
        raise ValueError("sound-composition target exact-bound before separate object acceptance")

    groups = [
        group for group in data.get("semantic_review_groups") or []
        if isinstance(group, dict) and group.get("group_id") == "RUS-SEM-REVIEW-001"
    ]
    if len(groups) != 1:
        raise ValueError("RU01 review group drift")
    requirements = [
        row for row in groups[0].get("requirements") or []
        if isinstance(row, dict) and row.get("requirement_id") == TARGET["requirement_id"]
    ]
    if len(requirements) != 1:
        raise ValueError("sound-composition target requirement missing or duplicated")
    requirement = requirements[0]
    if requirement.get("source_locator") != TARGET["source_locator"]:
        raise ValueError("sound-composition target source locator drift")

    data["schema_version"] = "0.20.0"
    data["base_current_launch_progress_v16_head_sha"] = BASE_HEAD
    data["base_current_launch_progress_v16_normalized_sha256"] = BASE_SHA
    data["newly_accepted_bounded_subject_semantic"] = {
        "authority_id": AUTHORITY_ID,
        "semantic_id": SEMANTIC,
        "authority_sha256": authority_sha,
        "independent_verification_item_ids": VERIFICATION_IDS,
        "target_count_requiring_separate_exact_object_component_set_acceptance": 1,
        "target": TARGET,
        "existing_partial_component_ref_preserved": EXISTING_PARTIAL_COMPONENT,
        "required_component_refs_for_future_exact_object_acceptance": [
            EXISTING_PARTIAL_COMPONENT,
            SEMANTIC,
        ],
        "object_acceptance_effect": "NONE_UNTIL_SEPARATE_EXACT_OBJECT_COMPONENT_SET_ACCEPTANCE",
    }
    data.setdefault("policy", {})["ru01_sound_composition_semantic_acceptance_requires_component_specific_evidence"] = True
    data["policy"]["ru01_sound_composition_semantic_acceptance_can_close_exact_object"] = False
    data["policy"]["ru01_sound_composition_semantic_acceptance_modifies_existing_partial_component"] = False
    data["policy"]["generic_ru01_attempt_can_emit_exact_sound_composition_mastery"] = False
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
        print("RUSSIAN_RU01_SOUND_COMPOSITION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
        print("ACCEPTED_SUBJECT_SEMANTICS=1")
        print("TARGET_OBJECTS_PENDING=1")
        print("OBJECT_LEVEL_CLOSURES=0")
        print("EXISTING_PARTIAL_COMPONENTS_MODIFIED=0")
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
