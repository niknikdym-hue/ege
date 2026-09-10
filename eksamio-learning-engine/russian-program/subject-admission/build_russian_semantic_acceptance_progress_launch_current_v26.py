#!/usr/bin/env python3
"""Current Russian launch progress after exact EDSOO59 p.181 4.1 RU01 component-set acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

H = Path(__file__).resolve().parent
P = H.parent
BASE = H / "build_russian_semantic_acceptance_progress_launch_current_v25.py"
AUTH = H / "RU01-EDSOO59-P181-4-1-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
PHONETICS_CONTENT = P / "production-learning-content" / "RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"

BASE_HEAD = "02344a6b8d90b62864fde48de4cf1b0a215a35bb"
BASE_SHA = "0a7bb82219f901ba7c145713122e5b1b57cecc015d6c236f489f7199a8b4034a"
AUTH_SHA = "f0636aa68487a4404755e45f50598570db612ffd9bfb8eb6c6ef850d230b1c95"
AID = "RU01_EDSOO59_P181_4_1_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
GROUP = "RUS-SEM-REVIEW-001"
UNIT = "RAU-5a6511267f156745f93c"
REQ = "RSK-EDSOO59-4-1-P181"
SRC = "EDSOO-RU-5-9-2025"
DOC = "EDSOO59"
LOC = "EDSOO-RU-5-9-2025/EDSOO59 p.181 4.1"

CHAR = "ru-phonetics-sound-characterization"
LETTER = "ru-phonetics-sound-letter-relation"
SYSTEM = "ru-phonetics-sound-system"
COMPONENTS = [CHAR, LETTER, SYSTEM]
EVIDENCE = {
    CHAR: [f"p01-u11-v{i}" for i in range(1, 6)],
    LETTER: ["p01-u1-v1", "p01-u1-v2"],
    SYSTEM: [f"p01-u12-v{i}" for i in range(1, 6)],
}
AUTHORITY_HASHES = {
    "RU01_PHONETICS_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1": "47c1ebe7ddb98c043b76367d19b700b5e9ff559d27c251487ab8bddd0b19bf29",
    "RU01_SOUND_CHARACTERIZATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1": "892f51286eebb3145a96ce8f13648a7c53929db5e0a8f30232b5a295433c18fc",
    "RU01_SOUND_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1": "6ebc5a07c54ea2bae760270272639a8190e8b7dc27182afed3ab5af83eeb10e3",
}
BASE_SUMMARY = {
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
    "accepted_bounded_ru_subject_semantics": 75,
    "accepted_bounded_ru_semantics_total": 84,
    "false_exact_mastery_admissions": 0,
}
AFTER = dict(BASE_SUMMARY)
AFTER.update({
    "semantic_units_with_accepted_component_sets": 42,
    "semantic_requirements_with_accepted_component_sets": 42,
    "semantic_units_remaining_without_accepted_component_set": 1274,
    "semantic_requirements_remaining_without_accepted_component_set": 1349,
    "subject_disposed_units_total": 43,
    "subject_disposed_requirements_total": 43,
    "subject_review_units_remaining": 1273,
    "subject_review_requirements_remaining": 1348,
    "canonical_component_refs_reused_unique": 125,
})


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def evidence_ids(path: Path, semantic: str) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = [u for u in data.get("units") or [] if u.get("proposed_semantic_id") == semantic]
    if len(rows) != 1:
        raise ValueError(f"learner-content semantic missing or duplicated: {semantic}")
    return [str(x.get("id")) for x in rows[0].get("independent_verification") or []]


def build_progress() -> dict[str, Any]:
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.27.0":
        raise ValueError("current-v25 schema drift")
    if data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v25 normalized SHA drift")
    summary = data.get("progress_summary") or {}
    for key, expected in BASE_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v25 aggregate drift: {key}")
    accepted_authorities = data.get("accepted_authorities") or []
    if len(accepted_authorities) != 71:
        raise ValueError("current-v25 accepted authority count drift")
    predecessor = data.get("newly_accepted_bounded_subject_semantic") or {}
    if predecessor.get("semantic_id") != SYSTEM:
        raise ValueError("current-v25 predecessor semantic drift")
    if predecessor.get("independent_verification_item_ids") != EVIDENCE[SYSTEM]:
        raise ValueError("current-v25 sound-system evidence drift")
    pending = predecessor.get("parent_objects_remain_pending") or []
    if pending != [{
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "sound_characterization_clause_id": "EDSOO59-P181-4.1-A",
        "sound_letter_relation_clause_id": "EDSOO59-P181-4.1-B",
        "sound_system_clause_id": "EDSOO59-P181-4.1-C",
    }]:
        raise ValueError("current-v25 parent-object frontier drift")

    indexed = {row.get("id"): row for row in accepted_authorities if isinstance(row, dict)}
    for authority_id, expected_sha in AUTHORITY_HASHES.items():
        row = indexed.get(authority_id) or {}
        if row.get("sha256") != expected_sha:
            raise ValueError(f"accepted component authority drift: {authority_id}")

    if evidence_ids(PHONETICS_CONTENT, LETTER) != EVIDENCE[LETTER]:
        raise ValueError("sound-letter component-specific evidence drift")

    authority = json.loads(AUTH.read_text(encoding="utf-8"))
    if hashlib.sha256(canonical_json(authority)).hexdigest() != AUTH_SHA:
        raise ValueError("exact parent-object authority SHA drift")
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_EDSOO59_P181_4_1_CANONICAL_COMPONENT_SET":
        raise ValueError("parent-object authority status drift")
    gate = authority.get("current_launch_progress_v25_exact_head_gate") or {}
    if gate != {
        "workflow": "Russian RU01 sound system semantic acceptance",
        "run_id": 34539055527,
        "head_sha": BASE_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": BASE_SHA,
    }:
        raise ValueError("exact-head current-v25 gate provenance drift")

    decision = authority.get("decision") or {}
    exact_identity = {
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SRC,
        "document_id": DOC,
        "page": 181,
        "content_code": "4.1",
        "source_locator": LOC,
        "module_id": "RU-PROG-01",
        "source_review_classification": "COMPOSITE_EXACT_CLAUSE_SET",
        "canonical_component_refs": COMPONENTS,
        "component_count": 3,
        "component_specific_independent_evidence": EVIDENCE,
        "independent_evidence_items": 12,
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    for key, expected in exact_identity.items():
        if decision.get(key) != expected:
            raise ValueError(f"parent-object identity drift: {key}")

    clauses = decision.get("source_clauses") or []
    expected_clauses = [
        ("EDSOO59-P181-4.1-A", "Характеризовать звуки", CHAR,
         "RU01_SOUND_CHARACTERIZATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"),
        ("EDSOO59-P181-4.1-B", "понимать различие между звуком и буквой", LETTER,
         "RU01_PHONETICS_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"),
        ("EDSOO59-P181-4.1-C", "характеризовать систему звуков", SYSTEM,
         "RU01_SOUND_SYSTEM_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"),
    ]
    if len(clauses) != 3:
        raise ValueError("exact source clause count drift")
    for row, (clause_id, official, component, authority_id) in zip(clauses, expected_clauses):
        if row.get("clause_id") != clause_id or row.get("official_requirement") != official:
            raise ValueError(f"source-clause identity drift: {clause_id}")
        if row.get("canonical_component_ref") != component:
            raise ValueError(f"source-clause owner drift: {clause_id}")
        if row.get("accepted_authority_id") != authority_id:
            raise ValueError(f"source-clause authority drift: {clause_id}")
        if row.get("accepted_authority_sha256") != AUTHORITY_HASHES[authority_id]:
            raise ValueError(f"source-clause authority SHA drift: {clause_id}")
        if row.get("component_specific_independent_evidence") != EVIDENCE[component]:
            raise ValueError(f"source-clause evidence drift: {clause_id}")

    flat_evidence = [item for component in COMPONENTS for item in EVIDENCE[component]]
    if len(flat_evidence) != 12 or len(set(flat_evidence)) != 12:
        raise ValueError("component evidence must be 12 distinct items")

    mastery = decision.get("mastery_boundary") or {}
    for key in (
        "all_three_exact_clause_owners_required",
        "component_specific_independent_evidence_required",
        "registered_user_identity_required_for_future_canonical_learner_evidence",
        "exact_versioned_item_and_action_required_for_future_canonical_learner_evidence",
        "server_owned_received_at_required_for_future_canonical_learner_evidence",
        "durable_evidence_event_required_for_future_canonical_learner_evidence",
    ):
        if mastery.get(key) is not True:
            raise ValueError(f"mastery boundary weakened: {key}")
    for key in (
        "single_clause_success_can_close_parent_object",
        "evidence_from_one_component_can_substitute_for_another",
        "generic_ru01_attempt_can_emit_exact_component_mastery",
        "object_acceptance_itself_emits_mastery",
        "anonymous_or_device_only_canonical_progress_allowed",
        "normative_pronunciation_or_orthoepy_stress_can_be_inferred_from_this_object",
        "sibling_source_objects_can_be_closed_by_shared_evidence",
    ):
        if mastery.get(key) is not False:
            raise ValueError(f"mastery boundary weakened: {key}")
    if (authority.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery opened")

    groups = [g for g in data.get("semantic_review_groups") or [] if g.get("group_id") == GROUP]
    if len(groups) != 1:
        raise ValueError("RU01 review group missing or duplicated")
    group = groups[0]
    if group.get("accepted_component_set_count") != 12:
        raise ValueError("RU01 accepted-set count drift")
    if UNIT not in set(map(str, group.get("admission_unit_ids") or [])):
        raise ValueError("target admission unit missing from RU01 group")
    requirements = [r for r in group.get("requirements") or [] if r.get("requirement_id") == REQ]
    if len(requirements) != 1:
        raise ValueError("target requirement missing or duplicated")
    requirement = requirements[0]
    for key, expected in (
        ("source_id", SRC), ("document_id", DOC), ("page", 181),
        ("code", "4.1"), ("source_locator", LOC),
    ):
        if requirement.get(key) != expected:
            raise ValueError(f"target requirement source drift: {key}")

    accepted_sets = [
        row for g in data.get("semantic_review_groups") or []
        for row in g.get("accepted_component_sets") or []
        if isinstance(row, dict)
    ]
    if any(row.get("admission_unit_id") == UNIT or row.get("requirement_id") == REQ for row in accepted_sets):
        raise ValueError("target parent object already accepted")
    refs_before = {
        ref for row in accepted_sets
        for ref in row.get("canonical_component_refs") or []
    }
    if any(ref in refs_before for ref in COMPONENTS):
        raise ValueError("expected three parent component refs to be new to exact object sets")

    group["accepted_component_sets"].append({
        "accepted_authority_id": AID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SRC,
        "document_id": DOC,
        "content_code": "4.1",
        "source_locator": LOC,
        "modules": ["RU-PROG-01"],
        "canonical_component_refs": COMPONENTS,
        "component_count": 3,
        "authority": {
            "base_current_v25_head_sha": BASE_HEAD,
            "base_current_v25_normalized_sha256": BASE_SHA,
            "accepted_authority_sha256": AUTH_SHA,
            "component_specific_independent_evidence_items": 12,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    })
    group["accepted_component_set_count"] = len(group["accepted_component_sets"])
    if group["accepted_component_set_count"] != 13:
        raise ValueError("post-parent RU01 accepted-set count drift")
    group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
    group["remaining_group_action"] = (
        "CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"
    )

    accepted_authorities.append({
        "id": AID,
        "authority_kind": "OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET",
        "sha256": AUTH_SHA,
        "status": authority["status"],
        "accepted_admission_units": 1,
        "accepted_requirements": 1,
        "canonical_component_refs": 3,
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
    summary["canonical_component_refs_reused_unique"] = len({
        ref for g in data.get("semantic_review_groups") or []
        for row in g.get("accepted_component_sets") or []
        for ref in row.get("canonical_component_refs") or []
    })
    for key, expected in AFTER.items():
        if summary.get(key) != expected:
            raise ValueError(f"post-parent aggregate drift: {key}")
    if len(accepted_authorities) != 72:
        raise ValueError("post-parent accepted authority count drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery drift")

    data["schema_version"] = "0.28.0"
    data["base_current_launch_progress_v25_head_sha"] = BASE_HEAD
    data["base_current_launch_progress_v25_normalized_sha256"] = BASE_SHA
    data["newly_accepted_exact_object"] = {
        "accepted_authority_id": AID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "accepted_component_refs": COMPONENTS,
        "component_specific_independent_evidence": EVIDENCE,
        "independent_evidence_items": 12,
        "source_clause_ids": ["EDSOO59-P181-4.1-A", "EDSOO59-P181-4.1-B", "EDSOO59-P181-4.1-C"],
        "source_review_classification": "COMPOSITE_EXACT_CLAUSE_SET",
        "sibling_source_objects_accepted": 0,
        "exact_mastery_admissions": 0,
    }
    data.setdefault("policy", {})["ru01_edsoo59_p181_4_1_requires_all_three_exact_clause_owners"] = True
    data["policy"]["ru01_edsoo59_p181_4_1_requires_component_specific_evidence_for_each_clause"] = True
    data["policy"]["ru01_edsoo59_p181_4_1_single_clause_success_can_close_parent"] = False
    data["policy"]["generic_ru01_attempt_can_emit_exact_edsoo59_p181_4_1_mastery"] = False
    data["policy"]["anonymous_or_device_only_progress_can_be_canonical_for_edsoo59_p181_4_1"] = False
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
        print("RUSSIAN_RU01_EDSOO59_P181_4_1_EXACT_COMPONENT_SET_ACCEPTANCE=PASS")
        print("ACCEPTED_UNIT=" + UNIT)
        print("ACCEPTED_REQUIREMENT=" + REQ)
        print("EXACT_COMPONENT_REFS=3")
        print("INDEPENDENT_EVIDENCE_ITEMS=12")
        print("ACCEPTED_AUTHORITIES=" + str(len(data["accepted_authorities"])))
        print("CANONICAL_COMPONENT_REFS_REUSED_UNIQUE=" + str(summary["canonical_component_refs_reused_unique"]))
        print("SUBJECT_REVIEW_UNITS_REMAINING=" + str(summary["subject_review_units_remaining"]))
        print("SUBJECT_REVIEW_REQUIREMENTS_REMAINING=" + str(summary["subject_review_requirements_remaining"]))
        print("FALSE_EXACT_MASTERY=" + str(summary["false_exact_mastery_admissions"]))
        print("NORMALIZED_SHA256=" + data["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
