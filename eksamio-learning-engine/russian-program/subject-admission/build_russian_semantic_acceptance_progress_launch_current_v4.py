#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress with one exact RU01 phonetics object acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v3.py"
BINDING = HERE / "build_ru01_phonetics_exact_object_binding_review.py"
BOUNDED = HERE / "RU01-PHONETICS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
AUTHORITY = HERE / "RU01-PHONETICS-P181-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
CONTENT = HERE.parent / "production-learning-content" / "RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"

BASE_HEAD_SHA = "e35c7d1ef49194c7fe59ec1e3bff8164ff36ac08"
BASE_BUILDER_GIT_BLOB_SHA1 = "6458189e4c57f32f08af1a20dfb50d7cb68e7532"
BINDING_SHA = "9e903409896463f350eb06e7bf5874eaaf9f1e21037c76f7c9c4b9e53831613e"
BINDING_INPUT_SHA = "39f8c5974c3b2fff4e397595655146e78a52ce9119a939cf86bf925f618a51b2"
AUTHORITY_SHA = "b7c82f0621d629a06604a43251b1a67dc551ea9280518299505596270809e798"
AUTHORITY_ID = "RU01_PHONETICS_P181_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
TARGET_UNIT = "RAU-043ae3d307ad5fd95639"
TARGET_REQUIREMENT = "RSK-EDSOO59-4-2-P181"
TARGET_GROUP = "RUS-SEM-REVIEW-001"
TARGET_SOURCE = "EDSOO-RU-5-9-2025"
TARGET_DOCUMENT = "EDSOO59"
TARGET_PAGE = 181
TARGET_CODE = "4.2"
TARGET_LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.181 4.2"
TARGET_SIGNATURE = "PHONETIC_WORD_ANALYSIS"
COMPONENT = "ru-phonetics-word-analysis-sequence"
EVIDENCE_ITEMS = ["p01-u3-v1", "p01-u3-v2"]


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
        raise ValueError("current-v3 builder blob drift")

    base = runpy.run_path(str(BASE))["build_progress"]()
    summary = base.get("progress_summary") or {}
    expected = {
        "semantic_units_with_accepted_component_sets": 29,
        "semantic_requirements_with_accepted_component_sets": 29,
        "semantic_units_remaining_without_accepted_component_set": 1287,
        "semantic_requirements_remaining_without_accepted_component_set": 1362,
        "subject_disposed_units_total": 30,
        "subject_disposed_requirements_total": 30,
        "subject_review_units_remaining": 1286,
        "subject_review_requirements_remaining": 1361,
        "canonical_component_refs_reused_unique": 117,
        "review_groups_with_accepted_component_sets": 13,
        "accepted_bounded_ru_route_semantics": 9,
        "accepted_bounded_ru_subject_semantics": 66,
        "accepted_bounded_ru_semantics_total": 75,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"current-v3 aggregate drift: {key}")
    if len(base.get("accepted_authorities", [])) != 50:
        raise ValueError("current-v3 accepted authority count drift")
    if base.get("schema_version") != "0.6.0":
        raise ValueError("current-v3 schema drift")

    binding = runpy.run_path(str(BINDING))["build_review"]()
    if binding.get("normalized_sha256") != BINDING_SHA:
        raise ValueError("RU01 exact binding review fingerprint drift")
    if binding.get("source_review_input_sha256") != BINDING_INPUT_SHA:
        raise ValueError("RU01 exact binding source input drift")
    if binding.get("status") != "CENTRAL_BRAIN_RU01_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("RU01 exact binding review status drift")
    if (binding.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("RU01 exact binding review introduced false exact mastery")
    ready = binding.get("exact_reuse_ready") or {}
    if ready.get("semantic_id") != COMPONENT:
        raise ValueError("RU01 exact reuse semantic owner drift")
    if ready.get("separate_object_acceptance_required") is not True:
        raise ValueError("RU01 separate object acceptance guard weakened")
    if ready.get("object_closures_by_this_review") != 0:
        raise ValueError("RU01 review self-admitted object closure")
    if TARGET_UNIT not in ready.get("admission_unit_ids", []) or TARGET_REQUIREMENT not in ready.get("requirement_ids", []):
        raise ValueError("RU01 P181 object is no longer exact-reuse-ready")
    records = [
        row for row in binding.get("records", [])
        if isinstance(row, dict)
        and row.get("admission_unit_id") == TARGET_UNIT
        and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(records) != 1:
        raise ValueError("RU01 P181 exact binding record is not unique")
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
            raise ValueError(f"RU01 P181 exact binding identity drift: {key}")

    bounded = json.loads(BOUNDED.read_text(encoding="utf-8"))
    if bounded.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU01_PHONETICS_BOUNDED_SUBJECT_SEMANTICS":
        raise ValueError("RU01 bounded subject authority status drift")
    if (bounded.get("policy") or {}).get("component_specific_independent_evidence_required") is not True:
        raise ValueError("RU01 bounded evidence guard weakened")
    if (bounded.get("policy") or {}).get("broad_domain_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("RU01 broad-domain attempt can emit exact mastery")
    decisions = [
        row for row in bounded.get("decisions", [])
        if isinstance(row, dict) and row.get("accepted_semantic_id") == COMPONENT
    ]
    if len(decisions) != 1:
        raise ValueError("RU01 canonical word-analysis semantic owner missing or duplicated")

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
        raise ValueError("RU01 accepted authority must be an object")
    verify_embedded_sha(authority, AUTHORITY_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_PHONETICS_WORD_ANALYSIS_CANONICAL_COMPONENT_SET":
        raise ValueError("RU01 accepted authority status drift")
    if authority.get("current_launch_progress_v3_base_head_sha") != BASE_HEAD_SHA:
        raise ValueError("RU01 accepted authority current-v3 head binding drift")
    if authority.get("current_launch_progress_v3_builder_git_blob_sha1") != BASE_BUILDER_GIT_BLOB_SHA1:
        raise ValueError("RU01 accepted authority current-v3 builder binding drift")
    if authority.get("exact_object_binding_review_sha256") != BINDING_SHA:
        raise ValueError("RU01 accepted authority binding-review drift")
    if authority.get("exact_source_review_input_sha256") != BINDING_INPUT_SHA:
        raise ValueError("RU01 accepted authority source-review input drift")
    decision = authority.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("RU01 accepted decision missing")
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
            raise ValueError(f"RU01 accepted authority identity drift: {key}")
    mastery = decision.get("mastery_boundary") or {}
    required_true = (
        "component_specific_independent_evidence_required",
        "validated_word_analysis_item_may_support_only_its_single_canonical_ref",
    )
    if any(mastery.get(key) is not True for key in required_true):
        raise ValueError("RU01 component-specific evidence guard weakened")
    required_false = (
        "generic_ru01_attempt_can_emit_exact_component_mastery",
        "spelling_or_morphemic_evidence_can_substitute_for_word_analysis",
        "shared_evidence_can_close_sibling_source_objects_without_separate_acceptance",
    )
    if any(mastery.get(key) is not False for key in required_false):
        raise ValueError("RU01 exact mastery boundary weakened")
    policy = authority.get("policy") or {}
    if policy.get("separate_object_acceptance_required") is not True:
        raise ValueError("RU01 authority separate object guard weakened")
    if policy.get("whole_group_acceptance_allowed") is not False:
        raise ValueError("RU01 authority whole-group guard weakened")
    if (authority.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("RU01 accepted authority introduced false exact mastery")
    if (authority.get("summary") or {}).get("sibling_ru01_source_objects_accepted") != 0:
        raise ValueError("RU01 authority accepted sibling source objects")

    groups = [
        group for group in base.get("semantic_review_groups", [])
        if isinstance(group, dict) and group.get("group_id") == TARGET_GROUP
    ]
    if len(groups) != 1:
        raise ValueError("RU01 target review group is not unique")
    group = groups[0]
    if group.get("accepted_component_set_count") != 0:
        raise ValueError("RU01 target group already has accepted component sets in current-v3")
    if TARGET_UNIT not in set(map(str, group.get("admission_unit_ids", []))):
        raise ValueError("RU01 target unit missing from group")
    rows = [
        row for row in group.get("requirements", [])
        if isinstance(row, dict) and row.get("requirement_id") == TARGET_REQUIREMENT
    ]
    if len(rows) != 1:
        raise ValueError("RU01 target requirement is not unique")
    row = rows[0]
    for source_key, expected_value in (
        ("source_id", TARGET_SOURCE),
        ("document_id", TARGET_DOCUMENT),
        ("page", TARGET_PAGE),
        ("code", TARGET_CODE),
        ("source_locator", TARGET_LOCATOR),
    ):
        if row.get(source_key) != expected_value:
            raise ValueError(f"RU01 source identity drift: {source_key}")
    if any(
        isinstance(item, dict)
        and (item.get("admission_unit_id") == TARGET_UNIT or item.get("requirement_id") == TARGET_REQUIREMENT)
        for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for item in g.get("accepted_component_sets", [])
    ):
        raise ValueError("RU01 P181 target already accepted in current-v3")
    if any(
        isinstance(item, dict)
        and (item.get("admission_unit_id") == TARGET_UNIT or item.get("requirement_id") == TARGET_REQUIREMENT)
        for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for item in g.get("accepted_nonsemantic_object_dispositions", [])
    ):
        raise ValueError("RU01 P181 target already disposed nonsemantically")
    if any(isinstance(item, dict) and item.get("id") == AUTHORITY_ID for item in base.get("accepted_authorities", [])):
        raise ValueError("RU01 P181 authority already integrated")

    existing_component_refs = {
        ref
        for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for item in g.get("accepted_component_sets", []) if isinstance(item, dict)
        for ref in item.get("canonical_component_refs", [])
    }
    if COMPONENT in existing_component_refs:
        raise ValueError("RU01 word-analysis component is already reused by an accepted exact object")

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
    if group["accepted_component_set_count"] != 1:
        raise ValueError("RU01 P181 accepted component set duplicated")
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
    summary["review_groups_with_accepted_component_sets"] += 1
    summary["canonical_component_refs_reused_unique"] += 1

    expected_after = {
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
    for key, value in expected_after.items():
        if summary.get(key) != value:
            raise ValueError(f"RU01 P181 post-acceptance aggregate drift: {key}")
    if len(base["accepted_authorities"]) != 51:
        raise ValueError("RU01 P181 post-acceptance authority count drift")

    sibling_ready_units = set(ready.get("admission_unit_ids", [])) - {TARGET_UNIT}
    sibling_ready_requirements = set(ready.get("requirement_ids", [])) - {TARGET_REQUIREMENT}
    accepted_rows = [
        item
        for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for item in g.get("accepted_component_sets", []) if isinstance(item, dict)
    ]
    if any(
        item.get("accepted_authority_id") == AUTHORITY_ID
        and (
            item.get("admission_unit_id") in sibling_ready_units
            or item.get("requirement_id") in sibling_ready_requirements
        )
        for item in accepted_rows
    ):
        raise ValueError("RU01 P181 authority leaked to sibling exact-ready objects")

    base["schema_version"] = "0.7.0"
    base["base_current_launch_progress_v3_head_sha"] = BASE_HEAD_SHA
    base["base_current_launch_progress_v3_builder_git_blob_sha1"] = BASE_BUILDER_GIT_BLOB_SHA1
    base["base_current_launch_progress_v3_normalized_sha256"] = base.get("normalized_sha256")
    base["policy"]["exact_ru01_phonetics_object_acceptance_requires_source_backed_component_set"] = True
    base["policy"]["exact_ru01_phonetics_object_acceptance_requires_component_specific_independent_evidence"] = True
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
        print("RUSSIAN_RU01_P181_EXACT_OBJECT_ACCEPTANCE=PASS")
        print(f"ACCEPTED_UNIT={TARGET_UNIT}")
        print(f"ACCEPTED_REQUIREMENT={TARGET_REQUIREMENT}")
        print("EXACT_COMPONENT_REFS=1")
        print("INDEPENDENT_EVIDENCE_ITEMS=2")
        print("SIBLING_RU01_OBJECTS_ACCEPTED=0")
        print(f"ACCEPTED_AUTHORITIES={len(result['accepted_authorities'])}")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={summary['subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['subject_review_requirements_remaining']}")
        print(f"FALSE_EXACT_MASTERY={summary['false_exact_mastery_admissions']}")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
