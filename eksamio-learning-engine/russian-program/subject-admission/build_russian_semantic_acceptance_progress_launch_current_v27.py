#!/usr/bin/env python3
"""Current Russian launch progress after exact EDSOO59 p.187 4.1.6 RU02 object acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v26.py"
REVIEW = HERE / "build_ru02_orthoepy_edsoo59_p187_4_1_6_exact_object_binding_review.py"
AUTHORITY = HERE / "RU02-EDSOO59-P187-4-1-6-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

BASE_HEAD = "4f43c838e83639827a040f1d8a8d75048e19abf2"
BASE_RUN_ID = 34543590950
BASE_SHA = "2b2ac9e07a98ac6b988e26bacb5b6e1a22394233c4f83a123354f3dcbd9ec402"
REVIEW_HEAD = "e709bcbeec1e65c324ab43bb43f5a1023b2af30b"
REVIEW_RUN_ID = 34551630548
REVIEW_SHA = "65643b5d97b819ba97f026bf6aac0595b0ac0b4b4d2993623c916aa281013ab3"
AUTHORITY_SHA = "3c69f9267562fca011c97219f7cb837ce6aeae6085da18df8e9f6571f788f7c5"
AUTHORITY_ID = "RU02_EDSOO59_P187_4_1_6_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"

GROUP = "RUS-SEM-REVIEW-047"
UNIT = "RAU-da83bb720dea792b3afb"
REQ = "RSK-EDSOO59-4-1-6-P187"
SRC = "EDSOO-RU-5-9-2025"
DOC = "EDSOO59"
LOC = "EDSOO-RU-5-9-2025/EDSOO59 p.187 4.1.6"
MEANING = "Применять нормативное произношение и ударение."
PRIOR_UNIT = "RAU-a8f2ad0b357c9e369c51"
PRIOR_REQ = "RSK-EDSOO1011-2-2-4-P074"
PRON = "ru-orthoepy-normative-pronunciation-selection"
STRESS = "ru-orthoepy-normative-stress-selection"
COMPONENTS = [PRON, STRESS]
EVIDENCE = {
    PRON: [f"p02-u4-v{i}" for i in range(1, 6)],
    STRESS: [f"p02-u3-v{i}" for i in range(1, 5)],
}

BASE_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 42,
    "semantic_requirements_with_accepted_component_sets": 42,
    "semantic_units_remaining_without_accepted_component_set": 1274,
    "semantic_requirements_remaining_without_accepted_component_set": 1349,
    "subject_disposed_units_total": 43,
    "subject_disposed_requirements_total": 43,
    "subject_review_units_remaining": 1273,
    "subject_review_requirements_remaining": 1348,
    "canonical_component_refs_reused_unique": 125,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 75,
    "accepted_bounded_ru_semantics_total": 84,
    "false_exact_mastery_admissions": 0,
}
AFTER = dict(BASE_SUMMARY)
AFTER.update({
    "semantic_units_with_accepted_component_sets": 43,
    "semantic_requirements_with_accepted_component_sets": 43,
    "semantic_units_remaining_without_accepted_component_set": 1273,
    "semantic_requirements_remaining_without_accepted_component_set": 1348,
    "subject_disposed_units_total": 44,
    "subject_disposed_requirements_total": 44,
    "subject_review_units_remaining": 1272,
    "subject_review_requirements_remaining": 1347,
})


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_embedded_sha(doc: dict[str, Any], expected: str) -> None:
    if doc.get("normalized_sha256") != expected:
        raise ValueError("authority normalized SHA drift")
    body = deepcopy(doc)
    body.pop("normalized_sha256", None)
    if hashlib.sha256(canonical_bytes(body)).hexdigest() != expected:
        raise ValueError("authority embedded normalized SHA mismatch")


def build_progress() -> dict[str, Any]:
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.28.0":
        raise ValueError("current-v26 schema drift")
    if data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v26 normalized SHA drift")
    summary = data.get("progress_summary") or {}
    for key, expected in BASE_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v26 aggregate drift: {key}")
    accepted_authorities = data.get("accepted_authorities") or []
    if len(accepted_authorities) != 72:
        raise ValueError("current-v26 accepted authority count drift")

    review = runpy.run_path(str(REVIEW))["build_review"]()
    if review.get("normalized_sha256") != REVIEW_SHA:
        raise ValueError("exact object-binding review SHA drift")
    if review.get("status") != "CENTRAL_BRAIN_RU02_EDSOO59_P187_4_1_6_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("exact object-binding review status drift")
    gate = review.get("current_v26_exact_head_gate") or {}
    if gate != {
        "workflow": "Russian RU01 EDSOO59 P181 4.1 exact component set",
        "run_id": BASE_RUN_ID,
        "head_sha": BASE_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": BASE_SHA,
    }:
        raise ValueError("review current-v26 gate provenance drift")
    selected = review.get("selected_object") or {}
    expected_selected = {
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SRC,
        "document_id": DOC,
        "page": 187,
        "code": "4.1.6",
        "source_locator": LOC,
        "modules": ["RU-PROG-02"],
        "routes": ["school"],
        "normalized_meaning": MEANING,
    }
    for key, expected in expected_selected.items():
        if selected.get(key) != expected:
            raise ValueError(f"review target identity drift: {key}")
    reuse = review.get("reuse_first_owner_resolution") or {}
    if reuse.get("resolution") != "EXACT_CURRENT_BOUNDED_RU02_COMPONENT_OWNERS_EXIST":
        raise ValueError("exact owner resolution drift")
    if reuse.get("canonical_component_refs") != COMPONENTS:
        raise ValueError("exact component refs drift")
    if reuse.get("independent_evidence_items") != 9:
        raise ValueError("exact component evidence denominator drift")
    if reuse.get("missing_source_components") != [] or reuse.get("overlapping_component_boundaries") != []:
        raise ValueError("component decomposition incomplete or overlapping")
    sibling = review.get("sibling_reuse_boundary") or {}
    if sibling.get("prior_accepted_sibling_admission_unit_id") != PRIOR_UNIT:
        raise ValueError("prior sibling identity drift")
    if sibling.get("prior_sibling_acceptance_auto_closes_target") is not False:
        raise ValueError("sibling auto-close boundary weakened")
    readiness = review.get("acceptance_readiness") or {}
    for key in (
        "exact_source_identity_verified",
        "target_still_in_current_v26_remainder",
        "exact_current_component_owners_verified",
        "all_components_have_component_specific_independent_evidence",
        "source_backed_two_component_decomposition_verified",
        "separate_object_acceptance_required",
    ):
        if readiness.get(key) is not True:
            raise ValueError(f"review readiness not proven: {key}")
    if readiness.get("object_accepted_by_this_review") is not False:
        raise ValueError("review self-admitted the target")
    if (review.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("review opened false exact mastery")

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if not isinstance(authority, dict):
        raise ValueError("accepted authority must be a JSON object")
    verify_embedded_sha(authority, AUTHORITY_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU02_EDSOO59_P187_4_1_6_CANONICAL_COMPONENT_SET":
        raise ValueError("accepted authority status drift")
    if authority.get("current_launch_progress_v26_exact_head_gate") != {
        "workflow": "Russian RU01 EDSOO59 P181 4.1 exact component set",
        "run_id": BASE_RUN_ID,
        "head_sha": BASE_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": BASE_SHA,
    }:
        raise ValueError("authority current-v26 provenance drift")
    if authority.get("exact_object_binding_review_exact_head_gate") != {
        "workflow": "Russian RU02 EDSOO59 p187 4.1.6 exact object binding review",
        "run_id": REVIEW_RUN_ID,
        "head_sha": REVIEW_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": REVIEW_SHA,
    }:
        raise ValueError("authority review provenance drift")
    decision = authority.get("decision") or {}
    exact_identity = {
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SRC,
        "document_id": DOC,
        "page": 187,
        "content_code": "4.1.6",
        "source_locator": LOC,
        "module_id": "RU-PROG-02",
        "normalized_meaning": MEANING,
        "canonical_component_refs": COMPONENTS,
        "component_count": 2,
        "component_specific_independent_evidence": EVIDENCE,
        "independent_evidence_items": 9,
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    for key, expected in exact_identity.items():
        if decision.get(key) != expected:
            raise ValueError(f"accepted authority identity drift: {key}")
    sb = decision.get("sibling_binding_boundary") or {}
    if sb.get("prior_accepted_sibling_admission_unit_id") != PRIOR_UNIT or sb.get("prior_accepted_sibling_requirement_id") != PRIOR_REQ:
        raise ValueError("accepted authority prior sibling drift")
    if sb.get("prior_sibling_acceptance_auto_closes_target") is not False:
        raise ValueError("accepted authority sibling auto-close boundary weakened")
    if sb.get("separate_exact_object_acceptance_performed") is not True:
        raise ValueError("separate exact object acceptance not recorded")
    mastery = decision.get("mastery_boundary") or {}
    for key in (
        "component_specific_independent_evidence_required",
        "registered_user_identity_required_for_future_canonical_learner_evidence",
        "exact_versioned_item_and_action_required_for_future_canonical_learner_evidence",
        "server_owned_received_at_required_for_future_canonical_learner_evidence",
        "durable_evidence_event_required_for_future_canonical_learner_evidence",
    ):
        if mastery.get(key) is not True:
            raise ValueError(f"mastery boundary weakened: {key}")
    for key in (
        "generic_orthoepy_attempt_can_emit_exact_component_mastery",
        "pronunciation_evidence_can_substitute_for_stress",
        "stress_evidence_can_substitute_for_pronunciation",
        "object_acceptance_itself_emits_mastery",
        "anonymous_or_device_only_canonical_progress_allowed",
        "shared_sibling_object_acceptance_can_close_target",
    ):
        if mastery.get(key) is not False:
            raise ValueError(f"mastery boundary weakened: {key}")
    if (authority.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("accepted authority opened false exact mastery")

    groups = [g for g in data.get("semantic_review_groups", []) if isinstance(g, dict) and g.get("group_id") == GROUP]
    if len(groups) != 1:
        raise ValueError("RU02 review group missing or duplicated")
    group = groups[0]
    if group.get("accepted_component_set_count") != 1:
        raise ValueError("RU02 prior accepted-set count drift")
    prior_rows = [
        row for row in group.get("accepted_component_sets", [])
        if isinstance(row, dict) and row.get("admission_unit_id") == PRIOR_UNIT
    ]
    if len(prior_rows) != 1 or prior_rows[0].get("canonical_component_refs") != COMPONENTS:
        raise ValueError("prior RU02 sibling acceptance drift")
    if any(
        isinstance(row, dict) and (row.get("admission_unit_id") == UNIT or row.get("requirement_id") == REQ)
        for row in group.get("accepted_component_sets", [])
    ):
        raise ValueError("target already accepted in current-v26")
    req_rows = [r for r in group.get("requirements", []) if isinstance(r, dict) and r.get("requirement_id") == REQ]
    if len(req_rows) != 1:
        raise ValueError("target requirement missing or duplicated")
    req_row = req_rows[0]
    for key, expected in (("source_id", SRC), ("document_id", DOC), ("page", 187), ("code", "4.1.6"), ("source_locator", LOC)):
        if req_row.get(key) != expected:
            raise ValueError(f"target requirement source drift: {key}")

    group.setdefault("accepted_component_sets", []).append({
        "accepted_authority_id": AUTHORITY_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SRC,
        "document_id": DOC,
        "content_code": "4.1.6",
        "source_locator": LOC,
        "modules": ["RU-PROG-02"],
        "canonical_component_refs": COMPONENTS,
        "component_count": 2,
        "authority": {
            "base_current_v26_head_sha": BASE_HEAD,
            "base_current_v26_normalized_sha256": BASE_SHA,
            "exact_object_binding_review_head_sha": REVIEW_HEAD,
            "exact_object_binding_review_run_id": REVIEW_RUN_ID,
            "exact_object_binding_review_normalized_sha256": REVIEW_SHA,
            "accepted_authority_normalized_sha256": AUTHORITY_SHA,
            "component_specific_independent_evidence_items": 9,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    })
    group["accepted_component_set_count"] = len(group["accepted_component_sets"])
    if group["accepted_component_set_count"] != 2:
        raise ValueError("post-acceptance RU02 accepted-set count drift")
    group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
    group["remaining_group_action"] = "CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"

    accepted_authorities.append({
        "id": AUTHORITY_ID,
        "authority_kind": "OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET",
        "sha256": AUTHORITY_SHA,
        "status": authority["status"],
        "accepted_admission_units": 1,
        "accepted_requirements": 1,
        "canonical_component_refs": 2,
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
        ref
        for g in data.get("semantic_review_groups", []) if isinstance(g, dict)
        for row in g.get("accepted_component_sets", []) if isinstance(row, dict)
        for ref in row.get("canonical_component_refs", [])
    })
    for key, expected in AFTER.items():
        if summary.get(key) != expected:
            raise ValueError(f"post-acceptance aggregate drift: {key}")
    if len(accepted_authorities) != 73:
        raise ValueError("post-acceptance authority count drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery drift")

    data["schema_version"] = "0.29.0"
    data["base_current_launch_progress_v26_head_sha"] = BASE_HEAD
    data["base_current_launch_progress_v26_normalized_sha256"] = BASE_SHA
    data["newly_accepted_exact_object"] = {
        "accepted_authority_id": AUTHORITY_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "accepted_component_refs": COMPONENTS,
        "component_specific_independent_evidence": EVIDENCE,
        "independent_evidence_items": 9,
        "sibling_source_objects_accepted": 0,
        "semantic_identity_admissions": 0,
        "exact_mastery_admissions": 0,
    }
    data.setdefault("policy", {})["ru02_edsoo59_p187_4_1_6_requires_source_backed_full_component_set"] = True
    data["policy"]["ru02_edsoo59_p187_4_1_6_requires_component_specific_independent_evidence"] = True
    data["policy"]["shared_ru02_sibling_acceptance_can_auto_close_target"] = False
    data["policy"]["generic_ru02_attempt_can_emit_exact_edsoo59_p187_4_1_6_mastery"] = False
    data["policy"]["anonymous_or_device_only_progress_can_be_canonical_for_edsoo59_p187_4_1_6"] = False
    data.pop("normalized_sha256", None)
    data["normalized_sha256"] = hashlib.sha256(canonical_bytes(data)).hexdigest()
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
        print("RUSSIAN_RU02_EDSOO59_P187_4_1_6_EXACT_OBJECT_ACCEPTANCE=PASS")
        print("ACCEPTED_UNIT=" + UNIT)
        print("ACCEPTED_REQUIREMENT=" + REQ)
        print("EXACT_COMPONENT_REFS=2")
        print("INDEPENDENT_EVIDENCE_ITEMS=9")
        print("ACCEPTED_AUTHORITIES=" + str(len(data["accepted_authorities"])))
        print("SUBJECT_REVIEW_UNITS_REMAINING=" + str(summary["subject_review_units_remaining"]))
        print("SUBJECT_REVIEW_REQUIREMENTS_REMAINING=" + str(summary["subject_review_requirements_remaining"]))
        print("FALSE_EXACT_MASTERY=" + str(summary["false_exact_mastery_admissions"]))
        print("NORMALIZED_SHA256=" + data["normalized_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
