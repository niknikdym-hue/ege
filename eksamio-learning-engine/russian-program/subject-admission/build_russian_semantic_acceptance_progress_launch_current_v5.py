#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress with second exact RU01 phonetics object acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v4.py"
BINDING = HERE / "build_ru01_phonetics_exact_object_binding_review.py"
BOUNDED = HERE / "RU01-PHONETICS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
AUTHORITY = HERE / "RU01-PHONETICS-P187-4-1-7-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
CONTENT = HERE.parent / "production-learning-content" / "RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"

BASE_HEAD_SHA = "4ad0cc31aec2ed49bcf8a4268712242c811a6190"
BASE_BUILDER_GIT_BLOB_SHA1 = "dbb770f1f080c7a3195aaf9fe6fc76ff16f1f61e"
BASE_NORMALIZED_SHA256 = "488fd13c032badc3bfc5415e3efb58c1f5a8b71bdee999bd7199db8d22b91bad"
BINDING_SHA = "9e903409896463f350eb06e7bf5874eaaf9f1e21037c76f7c9c4b9e53831613e"
BINDING_INPUT_SHA = "39f8c5974c3b2fff4e397595655146e78a52ce9119a939cf86bf925f618a51b2"
AUTHORITY_SHA = "650f57bb8983df81804e063a443a96dfbeeecbad2eaf9e9f533476fe9650dada"
AUTHORITY_ID = "RU01_PHONETICS_P187_4_1_7_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"

TARGET_UNIT = "RAU-0985ee43535361c09cd9"
TARGET_REQUIREMENT = "RSK-EDSOO59-4-1-7-P187"
TARGET_GROUP = "RUS-SEM-REVIEW-001"
TARGET_SOURCE = "EDSOO-RU-5-9-2025"
TARGET_DOCUMENT = "EDSOO59"
TARGET_PAGE = 187
TARGET_CODE = "4.1.7"
TARGET_LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.7"
TARGET_SIGNATURE = "PHONETIC_WORD_ANALYSIS"
COMPONENT = "ru-phonetics-word-analysis-sequence"
EVIDENCE_ITEMS = ["p01-u3-v1", "p01-u3-v2"]

PREVIOUS_UNIT = "RAU-043ae3d307ad5fd95639"
PREVIOUS_REQUIREMENT = "RSK-EDSOO59-4-2-P181"
PREVIOUS_AUTHORITY = "RU01_PHONETICS_P181_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


def verify_embedded_sha(doc: dict[str, Any], expected: str) -> None:
    if doc.get("normalized_sha256") != expected:
        raise ValueError("authority normalized SHA drift")
    body = deepcopy(doc)
    body.pop("normalized_sha256", None)
    if hashlib.sha256(canonical_bytes(body)).hexdigest() != expected:
        raise ValueError("authority embedded normalized SHA mismatch")


def build_progress() -> dict[str, Any]:
    if git_blob_sha1(BASE) != BASE_BUILDER_GIT_BLOB_SHA1:
        raise ValueError("current-v4 builder blob drift")

    base = runpy.run_path(str(BASE))["build_progress"]()
    if base.get("normalized_sha256") != BASE_NORMALIZED_SHA256:
        raise ValueError("current-v4 normalized SHA drift")
    if base.get("schema_version") != "0.7.0":
        raise ValueError("current-v4 schema drift")
    summary = base.get("progress_summary") or {}
    expected = {
        "semantic_units_with_accepted_component_sets": 30,
        "semantic_requirements_with_accepted_component_sets": 30,
        "semantic_units_remaining_without_accepted_component_set": 1286,
        "semantic_requirements_remaining_without_accepted_component_set": 1361,
        "subject_disposed_units_total": 31,
        "subject_disposed_requirements_total": 31,
        "subject_review_units_remaining": 1285,
        "subject_review_requirements_remaining": 1360,
        "canonical_component_refs_reused_unique": 118,
        "review_groups_with_accepted_component_sets": 14,
        "accepted_bounded_ru_route_semantics": 9,
        "accepted_bounded_ru_subject_semantics": 66,
        "accepted_bounded_ru_semantics_total": 75,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"current-v4 aggregate drift: {key}")
    if len(base.get("accepted_authorities", [])) != 51:
        raise ValueError("current-v4 accepted authority count drift")

    binding = runpy.run_path(str(BINDING))["build_review"]()
    if binding.get("normalized_sha256") != BINDING_SHA:
        raise ValueError("RU01 exact binding review fingerprint drift")
    if binding.get("source_review_input_sha256") != BINDING_INPUT_SHA:
        raise ValueError("RU01 exact binding source input drift")
    if (binding.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("RU01 binding review introduced false exact mastery")
    ready = binding.get("exact_reuse_ready") or {}
    if ready.get("semantic_id") != COMPONENT:
        raise ValueError("RU01 exact reuse semantic owner drift")
    if ready.get("separate_object_acceptance_required") is not True:
        raise ValueError("RU01 separate object acceptance guard weakened")
    if TARGET_UNIT not in ready.get("admission_unit_ids", []):
        raise ValueError("RU01 P187 target no longer exact-reuse-ready")
    if TARGET_REQUIREMENT not in ready.get("requirement_ids", []):
        raise ValueError("RU01 P187 requirement no longer exact-reuse-ready")
    records = [
        row for row in binding.get("records", [])
        if isinstance(row, dict)
        and row.get("admission_unit_id") == TARGET_UNIT
        and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(records) != 1:
        raise ValueError("RU01 P187 exact binding record is not unique")
    record = records[0]
    record_expected = {
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "page": TARGET_PAGE,
        "code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "normalized_source_signature": TARGET_SIGNATURE,
        "review_classification": "READY",
        "accepted_semantic_refs": [COMPONENT],
        "blocker_or_reroute": None,
    }
    for key, value in record_expected.items():
        if record.get(key) != value:
            raise ValueError(f"RU01 P187 exact binding identity drift: {key}")

    bounded = json.loads(BOUNDED.read_text(encoding="utf-8"))
    if bounded.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETICS_BOUNDED_SUBJECT_SEMANTICS":
        raise ValueError("RU01 bounded subject authority status drift")
    decisions = [
        row for row in bounded.get("decisions", [])
        if isinstance(row, dict) and row.get("accepted_semantic_id") == COMPONENT
    ]
    if len(decisions) != 1:
        raise ValueError("RU01 canonical word-analysis semantic owner missing or duplicated")
    if (bounded.get("policy") or {}).get("component_specific_independent_evidence_required") is not True:
        raise ValueError("RU01 component-specific evidence guard weakened")
    if (bounded.get("policy") or {}).get("broad_domain_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("RU01 broad-domain attempt can emit exact mastery")

    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    units = [
        row for row in content.get("units", [])
        if isinstance(row, dict) and row.get("proposed_semantic_id") == COMPONENT
    ]
    if len(units) != 1:
        raise ValueError("RU01 production word-analysis learner unit missing or duplicated")
    learner_unit = units[0]
    verification = learner_unit.get("independent_verification")
    if not isinstance(verification, list):
        raise ValueError("RU01 word-analysis independent verification missing")
    verification_ids = [row.get("id") for row in verification if isinstance(row, dict)]
    if verification_ids != EVIDENCE_ITEMS:
        raise ValueError("RU01 word-analysis independent verification identity drift")
    peis = learner_unit.get("peis_evidence") or {}
    if peis.get("independent_verification_required") is not True:
        raise ValueError("RU01 word-analysis independent verification guard weakened")
    if peis.get("assistance_must_be_recorded") is not True:
        raise ValueError("RU01 word-analysis assistance evidence guard weakened")

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if not isinstance(authority, dict):
        raise ValueError("RU01 P187 accepted authority must be an object")
    verify_embedded_sha(authority, AUTHORITY_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_PHONETICS_WORD_ANALYSIS_CANONICAL_COMPONENT_SET":
        raise ValueError("RU01 P187 accepted authority status drift")
    if authority.get("current_launch_progress_v4_base_head_sha") != BASE_HEAD_SHA:
        raise ValueError("RU01 P187 accepted authority current-v4 head binding drift")
    if authority.get("current_launch_progress_v4_builder_git_blob_sha1") != BASE_BUILDER_GIT_BLOB_SHA1:
        raise ValueError("RU01 P187 accepted authority current-v4 builder binding drift")
    if authority.get("current_launch_progress_v4_normalized_sha256") != BASE_NORMALIZED_SHA256:
        raise ValueError("RU01 P187 accepted authority current-v4 normalized SHA drift")
    if authority.get("exact_object_binding_review_sha256") != BINDING_SHA:
        raise ValueError("RU01 P187 accepted authority binding-review drift")
    if authority.get("exact_source_review_input_sha256") != BINDING_INPUT_SHA:
        raise ValueError("RU01 P187 accepted authority source-review input drift")

    decision = authority.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("RU01 P187 accepted decision missing")
    exact_identity = {
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQUIREMENT,
        "packet_group": TARGET_GROUP,
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "page": TARGET_PAGE,
        "content_code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "normalized_source_signature": TARGET_SIGNATURE,
        "module_id": "RU-PROG-01",
        "disposition": "PARTIAL_OR_COMPOSITE",
        "canonical_component_refs": [COMPONENT],
        "component_count": 1,
        "component_specific_independent_evidence": {COMPONENT: EVIDENCE_ITEMS},
        "independent_evidence_items": 2,
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    for key, value in exact_identity.items():
        if decision.get(key) != value:
            raise ValueError(f"RU01 P187 accepted authority identity drift: {key}")
    mastery = decision.get("mastery_boundary") or {}
    required_true = (
        "component_specific_independent_evidence_required",
        "validated_word_analysis_item_may_support_only_its_single_canonical_ref",
    )
    if any(mastery.get(key) is not True for key in required_true):
        raise ValueError("RU01 P187 component-specific evidence guard weakened")
    required_false = (
        "generic_ru01_attempt_can_emit_exact_component_mastery",
        "spelling_or_morphemic_evidence_can_substitute_for_word_analysis",
        "shared_evidence_can_close_sibling_source_objects_without_separate_acceptance",
    )
    if any(mastery.get(key) is not False for key in required_false):
        raise ValueError("RU01 P187 exact mastery boundary weakened")
    policy = authority.get("policy") or {}
    if policy.get("separate_object_acceptance_required") is not True:
        raise ValueError("RU01 P187 separate object guard weakened")
    if policy.get("whole_group_acceptance_allowed") is not False:
        raise ValueError("RU01 P187 whole-group guard weakened")
    if (authority.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("RU01 P187 authority introduced false exact mastery")
    if (authority.get("summary") or {}).get("sibling_ru01_source_objects_accepted") != 0:
        raise ValueError("RU01 P187 authority accepted sibling source objects")

    groups = [
        group for group in base.get("semantic_review_groups", [])
        if isinstance(group, dict) and group.get("group_id") == TARGET_GROUP
    ]
    if len(groups) != 1:
        raise ValueError("RU01 target review group is not unique")
    group = groups[0]
    if group.get("accepted_component_set_count") != 1:
        raise ValueError("RU01 target group current-v4 accepted-set count drift")
    previous = [
        item for item in group.get("accepted_component_sets", [])
        if isinstance(item, dict)
        and item.get("accepted_authority_id") == PREVIOUS_AUTHORITY
        and item.get("admission_unit_id") == PREVIOUS_UNIT
        and item.get("requirement_id") == PREVIOUS_REQUIREMENT
    ]
    if len(previous) != 1:
        raise ValueError("previous P181 exact acceptance missing from current-v4")
    if TARGET_UNIT not in set(map(str, group.get("admission_unit_ids", []))):
        raise ValueError("RU01 P187 target unit missing from group")
    rows = [
        row for row in group.get("requirements", [])
        if isinstance(row, dict) and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(rows) != 1:
        raise ValueError("RU01 P187 target requirement is not unique")
    row = rows[0]
    for source_key, expected_value in (
        ("source_id", TARGET_SOURCE),
        ("document_id", TARGET_DOCUMENT),
        ("page", TARGET_PAGE),
        ("code", TARGET_CODE),
        ("source_locator", TARGET_LOCATOR),
    ):
        if row.get(source_key) != expected_value:
            raise ValueError(f"RU01 P187 source identity drift: {source_key}")

    accepted_rows = [
        item for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for item in g.get("accepted_component_sets", []) if isinstance(item, dict)
    ]
    if any(
        item.get("admission_unit_id") == TARGET_UNIT or item.get("requirement_id") == TARGET_REQUIREMENT
        for item in accepted_rows
    ):
        raise ValueError("RU01 P187 target already accepted in current-v4")
    if any(
        isinstance(item, dict)
        and (item.get("admission_unit_id") == TARGET_UNIT or item.get("requirement_id") == TARGET_REQUIREMENT)
        for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for item in g.get("accepted_nonsemantic_object_dispositions", [])
    ):
        raise ValueError("RU01 P187 target already disposed nonsemantically")
    if any(isinstance(item, dict) and item.get("id") == AUTHORITY_ID for item in base.get("accepted_authorities", [])):
        raise ValueError("RU01 P187 authority already integrated")

    existing_component_refs = {
        ref
        for item in accepted_rows
        for ref in item.get("canonical_component_refs", [])
    }
    if COMPONENT not in existing_component_refs:
        raise ValueError("RU01 word-analysis component must already be reused by P181 in current-v4")

    projection = {
        "accepted_authority_id": AUTHORITY_ID,
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQUIREMENT,
        "packet_group": TARGET_GROUP,
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "content_code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "modules": ["RU-PROG-01"],
        "canonical_component_refs": [COMPONENT],
        "component_count": 1,
        "authority": {
            "exact_object_binding_review_normalized_sha256": BINDING_SHA,
            "accepted_authority_normalized_sha256": AUTHORITY_SHA,
            "component_specific_independent_evidence_items": 2,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    group.setdefault("accepted_component_sets", []).append(deepcopy(projection))
    group["accepted_component_set_count"] = len(group["accepted_component_sets"])
    if group["accepted_component_set_count"] != 2:
        raise ValueError("RU01 P187 accepted component set duplicated or group count drift")
    group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
    group["remaining_group_action"] = "CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"

    base["accepted_authorities"].append({
        "id": AUTHORITY_ID,
        "authority_kind": "OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET",
        "sha256": AUTHORITY_SHA,
        "status": authority["status"],
        "accepted_admission_units": 1,
        "accepted_requirements": 1,
        "canonical_component_refs": 1,
        "accepted_route_semantics": 0,
        "accepted_subject_semantics": 0,
        "semantic_identity_admissions": 0,
    })

    summary["semantic_units_with_accepted_component_sets"] += 1
    summary["semantic_requirements_with_accepted_component_sets"] += 1
    summary["semantic_units_remaining_without_accepted_component_set"] -= 1
    summary["semantic_requirements_remaining_without_accepted_component_set"] -= 1
    summary["subject_disposed_units_total"] += 1
    summary["subject_disposed_requirements_total"] += 1
    summary["subject_review_units_remaining"] -= 1
    summary["subject_review_requirements_remaining"] -= 1
    expected_after = {
        "semantic_units_with_accepted_component_sets": 31,
        "semantic_requirements_with_accepted_component_sets": 31,
        "semantic_units_remaining_without_accepted_component_set": 1285,
        "semantic_requirements_remaining_without_accepted_component_set": 1360,
        "subject_disposed_units_total": 32,
        "subject_disposed_requirements_total": 32,
        "subject_review_units_remaining": 1284,
        "subject_review_requirements_remaining": 1359,
        "canonical_component_refs_reused_unique": 118,
        "review_groups_with_accepted_component_sets": 14,
        "accepted_bounded_ru_route_semantics": 9,
        "accepted_bounded_ru_subject_semantics": 66,
        "accepted_bounded_ru_semantics_total": 75,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected_after.items():
        if summary.get(key) != value:
            raise ValueError(f"RU01 P187 post-acceptance aggregate drift: {key}")
    if len(base["accepted_authorities"]) != 52:
        raise ValueError("RU01 P187 post-acceptance authority count drift")

    sibling_ready_units = set(ready.get("admission_unit_ids", [])) - {PREVIOUS_UNIT, TARGET_UNIT}
    sibling_ready_requirements = set(ready.get("requirement_ids", [])) - {PREVIOUS_REQUIREMENT, TARGET_REQUIREMENT}
    all_rows = [
        item
        for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for item in g.get("accepted_component_sets", []) if isinstance(item, dict)
    ]
    by_new_authority = [item for item in all_rows if item.get("accepted_authority_id") == AUTHORITY_ID]
    if len(by_new_authority) != 1:
        raise ValueError("RU01 P187 authority must accept exactly one object")
    if any(
        item.get("admission_unit_id") in sibling_ready_units
        or item.get("requirement_id") in sibling_ready_requirements
        for item in by_new_authority
    ):
        raise ValueError("RU01 P187 authority leaked to sibling exact-ready objects")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery must remain zero")

    base["schema_version"] = "0.8.0"
    base["base_current_launch_progress_v4_head_sha"] = BASE_HEAD_SHA
    base["base_current_launch_progress_v4_builder_git_blob_sha1"] = BASE_BUILDER_GIT_BLOB_SHA1
    base["base_current_launch_progress_v4_normalized_sha256"] = BASE_NORMALIZED_SHA256
    base["policy"]["exact_ru01_phonetics_reuse_requires_separate_object_acceptance_per_source_object"] = True
    base["policy"]["ru01_shared_evidence_can_close_sibling_source_objects_without_separate_acceptance"] = False
    base["policy"]["generic_ru01_attempt_can_emit_exact_component_mastery"] = False
    base.pop("normalized_sha256", None)
    base["normalized_sha256"] = hashlib.sha256(canonical_bytes(base)).hexdigest()
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_progress()
    if args.output:
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    summary = result["progress_summary"]
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_RU01_P187_4_1_7_EXACT_OBJECT_ACCEPTANCE=PASS")
        print(f"ACCEPTED_UNIT={TARGET_UNIT}")
        print(f"ACCEPTED_REQUIREMENT={TARGET_REQUIREMENT}")
        print("EXACT_COMPONENT_REFS=1")
        print("INDEPENDENT_EVIDENCE_ITEMS=2")
        print("ADDITIONAL_SIBLING_RU01_OBJECTS_ACCEPTED=0")
        print(f"ACCEPTED_AUTHORITIES={len(result['accepted_authorities'])}")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={summary['subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['subject_review_requirements_remaining']}")
        print(f"FALSE_EXACT_MASTERY={summary['false_exact_mastery_admissions']}")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
