#!/usr/bin/env python3
"""Current Russian launch progress after exact EDSOO59 p.190 5.1 RU02 object acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v27.py"
REVIEW = HERE / "build_ru02_orthoepy_edsoo59_p190_5_1_exact_object_binding_review_v2.py"
AUTHORITY = HERE / "RU02-EDSOO59-P190-5-1-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

BASE_HEAD = "bb6e31986c2f7adf07c2d5e46ca4ba71270d33ba"
BASE_RUN_ID = 34555338230
BASE_SHA = "4e5e6018b8fa832a6115074291c722cd7862388aecbd78ef633e0e2b61864b82"
REVIEW_HEAD = "78e0806768880875fe323f32993e6eb68b6642c5"
REVIEW_RUN_ID = 34569660342
REVIEW_SHA = "ff4cbe56aebff67f3f0269ceb84c66e361d24dfc5e8c9c91ed1d2195207b8bb4"
AUTHORITY_SHA = "2acf12fb660db7a927beb14343476786da418fb87b9ef084b2f4beef0ba72510"
AUTHORITY_ID = "RU02_EDSOO59_P190_5_1_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"

GROUP = "RUS-SEM-REVIEW-047"
UNIT = "RAU-f875ecae572d08cef520"
REQ = "RSK-EDSOO59-5-1-P190"
SRC = "EDSOO-RU-5-9-2025"
DOC = "EDSOO59"
LOC = "EDSOO-RU-5-9-2025/EDSOO59 p.190 5.1"
MEANING = "Применять нормативное произношение и ударение."
PRON = "ru-orthoepy-normative-pronunciation-selection"
STRESS = "ru-orthoepy-normative-stress-selection"
COMPONENTS = [PRON, STRESS]
EVIDENCE = {
    PRON: [f"p02-u4-v{i}" for i in range(1, 6)],
    STRESS: [f"p02-u3-v{i}" for i in range(1, 5)],
}
PRIOR_SIBLINGS = [
    {"admission_unit_id": "RAU-a8f2ad0b357c9e369c51", "requirement_id": "RSK-EDSOO1011-2-2-4-P074"},
    {"admission_unit_id": "RAU-da83bb720dea792b3afb", "requirement_id": "RSK-EDSOO59-4-1-6-P187"},
]

BASE_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 43,
    "semantic_requirements_with_accepted_component_sets": 43,
    "semantic_units_remaining_without_accepted_component_set": 1273,
    "semantic_requirements_remaining_without_accepted_component_set": 1348,
    "subject_disposed_units_total": 44,
    "subject_disposed_requirements_total": 44,
    "subject_review_units_remaining": 1272,
    "subject_review_requirements_remaining": 1347,
    "canonical_component_refs_reused_unique": 125,
    "review_groups_with_accepted_component_sets": 14,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 75,
    "accepted_bounded_ru_semantics_total": 84,
    "false_exact_mastery_admissions": 0,
}
AFTER = dict(BASE_SUMMARY)
AFTER.update({
    "semantic_units_with_accepted_component_sets": 44,
    "semantic_requirements_with_accepted_component_sets": 44,
    "semantic_units_remaining_without_accepted_component_set": 1272,
    "semantic_requirements_remaining_without_accepted_component_set": 1347,
    "subject_disposed_units_total": 45,
    "subject_disposed_requirements_total": 45,
    "subject_review_units_remaining": 1271,
    "subject_review_requirements_remaining": 1346,
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
    if data.get("schema_version") != "0.29.0":
        raise ValueError("current-v27 schema drift")
    if data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v27 normalized SHA drift")
    summary = data.get("progress_summary") or {}
    for key, expected in BASE_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v27 aggregate drift: {key}")
    accepted_authorities = data.get("accepted_authorities") or []
    if len(accepted_authorities) != 73:
        raise ValueError("current-v27 accepted authority count drift")

    review = runpy.run_path(str(REVIEW))["build_review"]()
    if review.get("normalized_sha256") != REVIEW_SHA:
        raise ValueError("p190 exact object-binding review v2 SHA drift")
    if review.get("status") != "CENTRAL_BRAIN_RU02_EDSOO59_P190_5_1_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("p190 exact object-binding review v2 status drift")
    if review.get("current_v27_exact_head_gate") != {
        "workflow": "Russian RU02 EDSOO59 p187 4.1.6 current exact acceptance",
        "run_id": BASE_RUN_ID,
        "head_sha": BASE_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": BASE_SHA,
    }:
        raise ValueError("p190 review current-v27 provenance drift")
    selected = review.get("selected_object") or {}
    expected_selected = {
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SRC,
        "document_id": DOC,
        "page": 190,
        "code": "5.1",
        "source_locator": LOC,
        "modules": ["RU-PROG-02"],
        "routes": ["school"],
        "normalized_meaning": MEANING,
    }
    for key, expected in expected_selected.items():
        if selected.get(key) != expected:
            raise ValueError(f"p190 review target identity drift: {key}")
    reuse = review.get("reuse_first_owner_resolution") or {}
    if reuse.get("resolution") != "EXACT_CURRENT_BOUNDED_RU02_COMPONENT_OWNERS_EXIST":
        raise ValueError("p190 exact owner resolution drift")
    if reuse.get("canonical_component_refs") != COMPONENTS:
        raise ValueError("p190 exact component refs drift")
    if reuse.get("independent_evidence_items") != 9:
        raise ValueError("p190 component evidence denominator drift")
    if reuse.get("missing_source_components") != [] or reuse.get("overlapping_component_boundaries") != []:
        raise ValueError("p190 component decomposition incomplete or overlapping")
    provenance = review.get("validation_provenance") or {}
    if provenance.get("target_admission_unit_identity_source") != "deterministic_current_object_review_queue":
        raise ValueError("p190 admission-unit provenance drift")
    if provenance.get("target_admission_unit_id") != UNIT:
        raise ValueError("p190 deterministic admission-unit identity drift")
    if provenance.get("canonical_authority_file_mutated") is not False:
        raise ValueError("p190 review mutated canonical authority")
    if provenance.get("sibling_acceptance_inherited_by_target") is not False:
        raise ValueError("p190 review inherited sibling acceptance")
    sibling = review.get("sibling_reuse_boundary") or {}
    if len(sibling.get("prior_accepted_siblings") or []) != 2:
        raise ValueError("p190 prior accepted sibling count drift")
    if sibling.get("prior_sibling_acceptance_auto_closes_target") is not False:
        raise ValueError("p190 sibling auto-close boundary weakened")
    if sibling.get("separate_exact_object_acceptance_required") is not True:
        raise ValueError("p190 separate acceptance requirement drift")
    readiness = review.get("acceptance_readiness") or {}
    if readiness.get("target_still_in_current_v27_remainder") is not True:
        raise ValueError("p190 target not proven in current-v27 remainder")
    if readiness.get("object_accepted_by_this_review") is not False:
        raise ValueError("p190 review self-admitted target")
    if (review.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("p190 review opened false exact mastery")

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if not isinstance(authority, dict):
        raise ValueError("p190 accepted authority must be a JSON object")
    verify_embedded_sha(authority, AUTHORITY_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU02_EDSOO59_P190_5_1_CANONICAL_COMPONENT_SET":
        raise ValueError("p190 accepted authority status drift")
    if authority.get("current_launch_progress_v27_exact_head_gate") != {
        "workflow": "Russian RU02 EDSOO59 p187 4.1.6 current exact acceptance",
        "run_id": BASE_RUN_ID,
        "head_sha": BASE_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": BASE_SHA,
    }:
        raise ValueError("p190 authority current-v27 provenance drift")
    if authority.get("exact_object_binding_review_v2_exact_head_gate") != {
        "workflow": "Russian RU02 EDSOO59 p190 5.1 exact object binding review v2",
        "run_id": REVIEW_RUN_ID,
        "head_sha": REVIEW_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": REVIEW_SHA,
    }:
        raise ValueError("p190 authority review-v2 provenance drift")
    decision = authority.get("decision") or {}
    exact_identity = {
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SRC,
        "document_id": DOC,
        "page": 190,
        "content_code": "5.1",
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
            raise ValueError(f"p190 accepted authority identity drift: {key}")
    sb = decision.get("sibling_binding_boundary") or {}
    if sb.get("prior_accepted_siblings") != PRIOR_SIBLINGS:
        raise ValueError("p190 accepted authority prior sibling set drift")
    if sb.get("prior_sibling_acceptance_auto_closes_target") is not False:
        raise ValueError("p190 accepted authority sibling auto-close boundary weakened")
    if sb.get("separate_exact_object_acceptance_performed") is not True:
        raise ValueError("p190 separate exact object acceptance not recorded")
    mastery = decision.get("mastery_boundary") or {}
    for key in (
        "component_specific_independent_evidence_required",
        "registered_user_identity_required_for_future_canonical_learner_evidence",
        "exact_versioned_item_and_action_required_for_future_canonical_learner_evidence",
        "server_owned_received_at_required_for_future_canonical_learner_evidence",
        "durable_evidence_event_required_for_future_canonical_learner_evidence",
    ):
        if mastery.get(key) is not True:
            raise ValueError(f"p190 mastery boundary weakened: {key}")
    for key in (
        "generic_orthoepy_attempt_can_emit_exact_component_mastery",
        "pronunciation_evidence_can_substitute_for_stress",
        "stress_evidence_can_substitute_for_pronunciation",
        "object_acceptance_itself_emits_mastery",
        "anonymous_or_device_only_canonical_progress_allowed",
        "shared_sibling_object_acceptance_can_close_target",
    ):
        if mastery.get(key) is not False:
            raise ValueError(f"p190 mastery boundary weakened: {key}")
    if (authority.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("p190 accepted authority opened false exact mastery")

    groups = [g for g in data.get("semantic_review_groups", []) if isinstance(g, dict) and g.get("group_id") == GROUP]
    if len(groups) != 1:
        raise ValueError("RU02 review group missing or duplicated")
    group = groups[0]
    if group.get("accepted_component_set_count") != 2:
        raise ValueError("RU02 current-v27 accepted-set count drift")
    for prior in PRIOR_SIBLINGS:
        rows = [
            row for row in group.get("accepted_component_sets", [])
            if isinstance(row, dict) and row.get("admission_unit_id") == prior["admission_unit_id"]
        ]
        if len(rows) != 1 or rows[0].get("requirement_id") != prior["requirement_id"]:
            raise ValueError("prior RU02 sibling acceptance drift")
    if any(
        isinstance(row, dict) and (row.get("admission_unit_id") == UNIT or row.get("requirement_id") == REQ)
        for row in group.get("accepted_component_sets", [])
    ):
        raise ValueError("p190 target already accepted in current-v27")
    req_rows = [r for r in group.get("requirements", []) if isinstance(r, dict) and r.get("requirement_id") == REQ]
    if len(req_rows) != 1:
        raise ValueError("p190 target requirement missing or duplicated")
    req_row = req_rows[0]
    for key, expected in (("source_id", SRC), ("document_id", DOC), ("page", 190), ("code", "5.1"), ("source_locator", LOC)):
        if req_row.get(key) != expected:
            raise ValueError(f"p190 target requirement source drift: {key}")

    group.setdefault("accepted_component_sets", []).append({
        "accepted_authority_id": AUTHORITY_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SRC,
        "document_id": DOC,
        "content_code": "5.1",
        "source_locator": LOC,
        "modules": ["RU-PROG-02"],
        "canonical_component_refs": COMPONENTS,
        "component_count": 2,
        "authority": {
            "base_current_v27_head_sha": BASE_HEAD,
            "base_current_v27_normalized_sha256": BASE_SHA,
            "exact_object_binding_review_v2_head_sha": REVIEW_HEAD,
            "exact_object_binding_review_v2_run_id": REVIEW_RUN_ID,
            "exact_object_binding_review_v2_normalized_sha256": REVIEW_SHA,
            "accepted_authority_normalized_sha256": AUTHORITY_SHA,
            "component_specific_independent_evidence_items": 9,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    })
    group["accepted_component_set_count"] = len(group["accepted_component_sets"])
    if group["accepted_component_set_count"] != 3:
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
    if len(accepted_authorities) != 74:
        raise ValueError("post-acceptance authority count drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("false exact mastery drift")

    data["schema_version"] = "0.30.0"
    data["base_current_launch_progress_v27_head_sha"] = BASE_HEAD
    data["base_current_launch_progress_v27_normalized_sha256"] = BASE_SHA
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
    data.setdefault("policy", {})["ru02_edsoo59_p190_5_1_requires_source_backed_full_component_set"] = True
    data["policy"]["ru02_edsoo59_p190_5_1_requires_component_specific_independent_evidence"] = True
    data["policy"]["shared_ru02_sibling_acceptance_can_auto_close_target"] = False
    data["policy"]["generic_ru02_attempt_can_emit_exact_edsoo59_p190_5_1_mastery"] = False
    data["policy"]["anonymous_or_device_only_progress_can_be_canonical_for_edsoo59_p190_5_1"] = False
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
        print("RUSSIAN_RU02_EDSOO59_P190_5_1_EXACT_OBJECT_ACCEPTANCE=PASS")
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
