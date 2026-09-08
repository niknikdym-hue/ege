#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress after bounded RU01 transcription semantic acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v10.py"
READINESS = HERE / "build_ru01_phonetic_transcription_content_readiness.py"
ACCEPTANCE = HERE / "RU01-PHONETIC-TRANSCRIPTION-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"

BASE_SHA = "e770aa9528d4db14b3be8a703bc3f6fcbd195787a34e851532ebc4649c96f9b1"
AUTHORITY_ID = "RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
SEMANTIC = "ru-phonetics-phonetic-transcription-elements"
TARGET_UNIT = "RAU-2725ee5b709b70502748"
TARGET_REQUIREMENT = "RSK-EDSOO59-4-1-4-P187"
VERIFICATION_IDS = [f"p01-u4-v{i}" for i in range(1, 6)]

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
    "accepted_bounded_ru_subject_semantics": 66,
    "accepted_bounded_ru_semantics_total": 75,
    "false_exact_mastery_admissions": 0,
}
EXPECTED_AFTER = dict(EXPECTED_BASE)
EXPECTED_AFTER["accepted_bounded_ru_subject_semantics"] = 67
EXPECTED_AFTER["accepted_bounded_ru_semantics_total"] = 76


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_progress() -> dict[str, Any]:
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v10 normalized SHA drift")
    summary = data.get("progress_summary") or {}
    for key, expected in EXPECTED_BASE.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v10 aggregate drift: {key}")
    if len(data.get("accepted_authorities") or []) != 57:
        raise ValueError("current-v10 accepted authority count drift")

    readiness = runpy.run_path(str(READINESS))["build_readiness"]()
    if readiness.get("status") != "CENTRAL_BRAIN_RU01_PHONETIC_TRANSCRIPTION_CONTENT_AND_EVIDENCE_READY_NOT_ACCEPTED":
        raise ValueError("transcription content-readiness predecessor drift")
    if readiness.get("candidate_semantic_id") != SEMANTIC:
        raise ValueError("transcription candidate identity drift")
    if (readiness.get("learner_content") or {}).get("independent_verification_ids") != VERIFICATION_IDS:
        raise ValueError("transcription evidence identity drift")
    if (readiness.get("evidence_independence") or {}).get("word_analysis_evidence_reused") is not False:
        raise ValueError("word-analysis evidence reuse opened")
    if (readiness.get("summary") or {}).get("semantic_admissions") != 0:
        raise ValueError("content-readiness predecessor self-admitted semantic")
    if (readiness.get("summary") or {}).get("object_level_admission_units_closed") != 0:
        raise ValueError("content-readiness predecessor closed object")

    acceptance = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    if acceptance.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC":
        raise ValueError("transcription semantic acceptance status drift")
    decisions = acceptance.get("decisions") or []
    if len(decisions) != 1 or decisions[0].get("accepted_semantic_id") != SEMANTIC:
        raise ValueError("transcription semantic decision drift")
    if decisions[0].get("independent_verification_item_ids") != VERIFICATION_IDS:
        raise ValueError("transcription accepted evidence drift")
    if decisions[0].get("object_binding_status") != "NOT_BOUND_TO_ANY_EXACT_ADMISSION_UNIT_OR_REQUIREMENT":
        raise ValueError("transcription semantic acceptance improperly binds object")
    policy = acceptance.get("policy") or {}
    if policy.get("subject_semantic_acceptance_can_reduce_object_counts_without_exact_binding") is not False:
        raise ValueError("semantic acceptance object-count boundary weakened")
    if policy.get("separate_exact_object_acceptance_required") is not True:
        raise ValueError("separate exact object acceptance no longer required")
    if policy.get("generic_ru01_result_can_emit_exact_component_mastery") is not False:
        raise ValueError("generic RU01 exact mastery opened")
    if (acceptance.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("transcription semantic false exact mastery drift")

    accepted_authorities = data.get("accepted_authorities") or []
    if any(row.get("id") == AUTHORITY_ID for row in accepted_authorities if isinstance(row, dict)):
        raise ValueError("transcription semantic authority already integrated")
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
            raise ValueError(f"post-semantic-acceptance aggregate drift: {key}")
    if len(accepted_authorities) != 58:
        raise ValueError("post-semantic-acceptance authority count drift")

    # Semantic admission alone must not dispose or exact-bind the target source object.
    accepted_sets = [
        row
        for group in data.get("semantic_review_groups") or []
        if isinstance(group, dict)
        for row in group.get("accepted_component_sets") or []
        if isinstance(row, dict)
    ]
    if any(row.get("admission_unit_id") == TARGET_UNIT or row.get("requirement_id") == TARGET_REQUIREMENT for row in accepted_sets):
        raise ValueError("transcription target exact-bound before separate object acceptance")

    data["schema_version"] = "0.14.0"
    data["base_current_launch_progress_v10_normalized_sha256"] = BASE_SHA
    data["newly_accepted_bounded_subject_semantic"] = {
        "authority_id": AUTHORITY_ID,
        "semantic_id": SEMANTIC,
        "authority_sha256": authority_sha,
        "independent_verification_item_ids": VERIFICATION_IDS,
        "target_admission_unit_id": TARGET_UNIT,
        "target_requirement_id": TARGET_REQUIREMENT,
        "object_acceptance_effect": "NONE_UNTIL_SEPARATE_EXACT_OBJECT_ACCEPTANCE",
    }
    data.setdefault("policy", {})["ru01_transcription_semantic_acceptance_requires_component_specific_evidence"] = True
    data["policy"]["ru01_transcription_semantic_acceptance_can_close_exact_object"] = False
    data["policy"]["generic_ru01_attempt_can_emit_exact_transcription_mastery"] = False
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
        print("RUSSIAN_RU01_PHONETIC_TRANSCRIPTION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE=PASS")
        print("ACCEPTED_SUBJECT_SEMANTICS=1")
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
