#!/usr/bin/env python3
"""Current Russian launch progress after exact EDSOO59 p.222 8.1 RU09 source-corrected acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v29.py"
SEMANTIC = HERE / "RU09-EDSOO59-P222-8-1-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
REVIEW = HERE / "RU09-EDSOO59-P222-8-1-EXACT-OBJECT-BINDING-REVIEW-v0.1.json"
AUTHORITY = HERE / "RU09-EDSOO59-P222-8-1-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
MANIFEST = ENGINE / "russian-program/source-knowledge/RUSSIAN-OFFICIAL-SOURCE-MANIFEST-v1.0.json"

BASE_HEAD = "cb90377c4ebe00e88e22c39824b7c484651ebcc4"
BASE_RUN_ID = 34624859121
BASE_SHA = "7e7b74ddf4aa4fc9df9744ec74191d8893b6ae251b703c36dcd2ef911273d8e4"
SEMANTIC_HEAD = "a05cdc663753af46846952d9e05ea82ae0bfed1b"
SEMANTIC_RUN_ID = 34682168590
REVIEW_HEAD = "8ac4b15bc7c5989c79cc83a2e6d6afc91f96b192"
REVIEW_RUN_ID = 34696726331
REVIEW_SHA = "6426cc3204a3e44163d0e091a6ec3a288aa7ad0cc79c661c8d12c0ccfdae4c8c"
AUTHORITY_SHA = "b0c80b807b54959ff842b0a5b6182415641b9cab08b96c64fccd7741d4bcaa97"

GROUP = "RUS-SEM-REVIEW-048"
UNIT = "RAU-3ceb45ca22608d520ddf"
REQ = "RSK-EDSOO59-8-1-P222"
SOURCE = "EDSOO-RU-5-9-2025"
DOCUMENT = "EDSOO59"
PAGE = 222
CODE = "8.1"
LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.222 8.1"
DOC_SHA = "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d"
STALE = "Применять нормативное произношение и ударение. Анализировать синтаксическую конструкцию и её нормативность."
OFFICIAL = "Средства оформления предложения в устной и письменной речи (интонация, логическое ударение, знаки препинания). Нормы использования инверсии"
COMPONENTS = ["ru-syntax-sentence-formulation-means", "ru-syntax-inversion-norm"]
EVIDENCE = {
    COMPONENTS[0]: [f"p09-u6-v{i}" for i in range(1, 5)],
    COMPONENTS[1]: [f"p09-u7-v{i}" for i in range(1, 5)],
}
SEMANTIC_AUTHORITY_ID = "RA-RU09-edsoo59-p222-8-1-bounded-subject-semantic-acceptance-v0.1"
OBJECT_AUTHORITY_ID = "RU09_EDSOO59_P222_8_1_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"

BASE_SUMMARY = {
    "semantic_units_with_accepted_component_sets": 45,
    "semantic_requirements_with_accepted_component_sets": 45,
    "semantic_units_remaining_without_accepted_component_set": 1271,
    "semantic_requirements_remaining_without_accepted_component_set": 1346,
    "subject_disposed_units_total": 46,
    "subject_disposed_requirements_total": 46,
    "subject_review_units_remaining": 1270,
    "subject_review_requirements_remaining": 1345,
    "canonical_component_refs_reused_unique": 125,
    "review_groups_with_accepted_component_sets": 14,
    "fully_accepted_semantic_groups": 1,
    "accepted_bounded_ru_route_semantics": 9,
    "accepted_bounded_ru_subject_semantics": 75,
    "accepted_bounded_ru_semantics_total": 84,
    "false_exact_mastery_admissions": 0,
}
AFTER = dict(BASE_SUMMARY)
AFTER.update({
    "semantic_units_with_accepted_component_sets": 46,
    "semantic_requirements_with_accepted_component_sets": 46,
    "semantic_units_remaining_without_accepted_component_set": 1270,
    "semantic_requirements_remaining_without_accepted_component_set": 1345,
    "subject_disposed_units_total": 47,
    "subject_disposed_requirements_total": 47,
    "subject_review_units_remaining": 1269,
    "subject_review_requirements_remaining": 1344,
    "canonical_component_refs_reused_unique": 127,
    "review_groups_with_accepted_component_sets": 15,
    "fully_accepted_semantic_groups": 2,
    "accepted_bounded_ru_subject_semantics": 77,
    "accepted_bounded_ru_semantics_total": 86,
})


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def embedded_sha(doc: dict[str, Any], expected: str) -> None:
    body = deepcopy(doc)
    actual = body.pop("normalized_sha256", None)
    calculated = hashlib.sha256(canonical_bytes(body)).hexdigest()
    if actual != expected or calculated != expected:
        raise ValueError("embedded normalized SHA drift")


def verify_manifest() -> None:
    manifest = load(MANIFEST)
    rows = [
        row for row in manifest.get("documents", [])
        if isinstance(row, dict)
        and row.get("canonical_source_id") == SOURCE
        and row.get("document_id") == DOCUMENT
    ]
    if len(rows) != 1:
        raise ValueError("official EDSOO59 manifest row missing or duplicated")
    row = rows[0]
    if row.get("sha256") != DOC_SHA:
        raise ValueError("official EDSOO59 document SHA drift")
    if row.get("final_status") != "CURRENT_2025_FEDERAL_PROGRAM":
        raise ValueError("official EDSOO59 source is no longer current")


def build_progress() -> dict[str, Any]:
    verify_manifest()
    data = runpy.run_path(str(BASE))["build_progress"]()
    if data.get("schema_version") != "0.31.0":
        raise ValueError("current-v29 schema drift")
    if data.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v29 normalized SHA drift")
    summary = data.get("progress_summary") or {}
    for key, expected in BASE_SUMMARY.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v29 aggregate drift: {key}")
    accepted_authorities = data.get("accepted_authorities") or []
    if len(accepted_authorities) != 75:
        raise ValueError("current-v29 accepted authority count drift")
    existing_ids = {row.get("id") for row in accepted_authorities if isinstance(row, dict)}
    if SEMANTIC_AUTHORITY_ID in existing_ids or OBJECT_AUTHORITY_ID in existing_ids:
        raise ValueError("p222 authority already integrated")

    semantic = load(SEMANTIC)
    if semantic.get("status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTICS_OBJECT_BINDING_STILL_REQUIRED":
        raise ValueError("p222 bounded semantic acceptance status drift")
    if semantic.get("authority_id") != SEMANTIC_AUTHORITY_ID:
        raise ValueError("p222 bounded semantic authority id drift")
    target = semantic.get("target_object") or {}
    if (target.get("admission_unit_id"), target.get("requirement_id"), target.get("review_group_id"), target.get("source_locator")) != (UNIT, REQ, GROUP, LOCATOR):
        raise ValueError("p222 bounded semantic target drift")
    source = semantic.get("official_source") or {}
    if source.get("document_sha256") != DOC_SHA or norm(source.get("exact_object_text")) != norm(OFFICIAL):
        raise ValueError("p222 bounded semantic official source drift")
    upstream = semantic.get("upstream_authorities") or {}
    content_gate = upstream.get("candidate_content_readiness") or {}
    if content_gate != {
        "workflow": "Russian RU09 EDSOO59 p222 8.1 candidate content readiness",
        "run_id": 34679263408,
        "head_sha": "e4085a3f556abb0a077358b2e968b5b4fd320847",
        "conclusion": "SUCCESS",
    }:
        raise ValueError("p222 content/evidence exact-head provenance drift")
    rows = semantic.get("accepted_semantics") or []
    by_id = {row.get("semantic_id"): row for row in rows if isinstance(row, dict)}
    if set(by_id) != set(COMPONENTS) or len(rows) != 2:
        raise ValueError("p222 bounded semantic set drift")
    for semantic_id in COMPONENTS:
        row = by_id[semantic_id]
        if row.get("state") != "ADMITTED":
            raise ValueError(f"semantic not admitted: {semantic_id}")
        if row.get("independent_component_evidence_ids") != EVIDENCE[semantic_id]:
            raise ValueError(f"semantic evidence drift: {semantic_id}")
        if row.get("exact_mastery_effect") != "NONE" or row.get("false_exact_mastery") != 0:
            raise ValueError(f"semantic mastery boundary weakened: {semantic_id}")
    effect = semantic.get("progress_effect") or {}
    if effect.get("semantic_admissions") != 2 or effect.get("object_level_closures") != 0 or effect.get("requirement_disposals") != 0 or effect.get("mastery_admissions") != 0 or effect.get("false_exact_mastery") != 0:
        raise ValueError("bounded semantic progress boundary drift")
    semantic_sha = hashlib.sha256(canonical_bytes(semantic)).hexdigest()

    review = load(REVIEW)
    embedded_sha(review, REVIEW_SHA)
    if review.get("status") != "CENTRAL_BRAIN_RU09_EDSOO59_P222_8_1_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("p222 exact object review status drift")
    review_target = review.get("target_object") or {}
    exact_review_target = {
        "packet_group": GROUP,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "source_id": SOURCE,
        "document_id": DOCUMENT,
        "printed_page": PAGE,
        "content_code": CODE,
        "source_locator": LOCATOR,
        "grades": ["8"],
    }
    for key, expected in exact_review_target.items():
        if review_target.get(key) != expected:
            raise ValueError(f"p222 exact object review target drift: {key}")
    binding = review.get("binding_result") or {}
    for key in (
        "official_source_identity_verified",
        "target_current_v29_identity_verified",
        "repository_current_meaning_is_known_stale",
        "component_texts_join_exact_official_object_text",
        "exact_component_set_complete",
        "semantic_acceptance_exact_head_ci_proven",
        "exact_object_binding_ready_for_separate_acceptance",
    ):
        if binding.get(key) is not True:
            raise ValueError(f"p222 exact object readiness drift: {key}")
    if binding.get("object_accepted_by_this_review") is not False:
        raise ValueError("p222 review self-accepted object")
    if (review.get("progress_effect") or {}).get("false_exact_mastery") != 0:
        raise ValueError("p222 review false exact mastery drift")
    if (review.get("next_required_gate") or {}).get("kind") != "SEPARATE_EXACT_OBJECT_ACCEPTANCE_AND_AGGREGATE_SOURCE_CORRECTION":
        raise ValueError("p222 next-gate drift")

    authority = load(AUTHORITY)
    embedded_sha(authority, AUTHORITY_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU09_EDSOO59_P222_8_1_CANONICAL_COMPONENT_SET":
        raise ValueError("p222 accepted authority status drift")
    if authority.get("current_launch_progress_v29_exact_head_gate") != {
        "workflow": "Russian RU02 OGE p21 4.1.6 current exact acceptance",
        "run_id": BASE_RUN_ID,
        "head_sha": BASE_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": BASE_SHA,
    }:
        raise ValueError("p222 current-v29 provenance drift")
    if authority.get("bounded_semantic_acceptance_exact_head_gate") != {
        "workflow": "Russian RU09 EDSOO59 p222 8.1 bounded semantic acceptance",
        "run_id": SEMANTIC_RUN_ID,
        "head_sha": SEMANTIC_HEAD,
        "conclusion": "SUCCESS",
        "semantic_admissions": 2,
    }:
        raise ValueError("p222 semantic exact-head provenance drift")
    if authority.get("exact_object_binding_review_exact_head_gate") != {
        "workflow": "Russian RU09 EDSOO59 p222 8.1 exact object binding review",
        "run_id": REVIEW_RUN_ID,
        "head_sha": REVIEW_HEAD,
        "conclusion": "SUCCESS",
        "normalized_sha256": REVIEW_SHA,
    }:
        raise ValueError("p222 object-review exact-head provenance drift")
    decision = authority.get("decision") or {}
    exact_identity = {
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SOURCE,
        "document_id": DOCUMENT,
        "page": PAGE,
        "content_code": CODE,
        "source_locator": LOCATOR,
        "grades": ["8"],
        "module_id": "RU-PROG-09",
        "route": "school",
        "repository_meaning_before_correction": STALE,
        "normalized_meaning": OFFICIAL,
        "canonical_component_refs": COMPONENTS,
        "component_count": 2,
        "component_specific_independent_evidence": EVIDENCE,
        "independent_evidence_items": 8,
        "semantic_acceptance_authority_id": SEMANTIC_AUTHORITY_ID,
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    for key, expected in exact_identity.items():
        if decision.get(key) != expected:
            raise ValueError(f"p222 accepted authority identity drift: {key}")
    correction = decision.get("source_correction") or {}
    if norm(correction.get("from_repository_meaning")) != norm(STALE) or norm(correction.get("to_official_source_text")) != norm(OFFICIAL):
        raise ValueError("p222 source-correction wording drift")
    if correction.get("official_document_sha256") != DOC_SHA:
        raise ValueError("p222 source-correction document SHA drift")
    mastery = decision.get("mastery_boundary") or {}
    for key in (
        "registered_user_identity_ref_required_for_future_canonical_learner_evidence",
        "exact_versioned_item_and_action_required_for_future_canonical_learner_evidence",
        "server_owned_received_at_required_for_future_canonical_learner_evidence",
        "durable_evidence_event_required_for_future_canonical_learner_evidence",
        "assistance_must_be_recorded_for_future_canonical_learner_evidence",
        "component_specific_independent_evidence_required",
    ):
        if mastery.get(key) is not True:
            raise ValueError(f"p222 mastery safeguard missing: {key}")
    for key in (
        "anonymous_or_device_only_canonical_progress_allowed",
        "generic_ru09_score_can_emit_exact_component_mastery",
        "sentence_formulation_evidence_can_substitute_for_inversion",
        "inversion_evidence_can_substitute_for_sentence_formulation",
        "object_acceptance_itself_emits_mastery",
    ):
        if mastery.get(key) is not False:
            raise ValueError(f"p222 mastery boundary weakened: {key}")
    if (authority.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("p222 accepted authority opened false exact mastery")

    groups = [
        row for row in data.get("semantic_review_groups", [])
        if isinstance(row, dict) and row.get("group_id") == GROUP
    ]
    if len(groups) != 1:
        raise ValueError("p222 current-v29 group missing or duplicated")
    group = groups[0]
    if group.get("admission_unit_ids") != [UNIT] or group.get("admission_unit_count") != 1 or group.get("requirement_count") != 1:
        raise ValueError("p222 current-v29 group identity drift")
    if group.get("accepted_component_set_count") not in (None, 0):
        raise ValueError("p222 target already accepted")
    if group.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("p222 target no longer pending exact acceptance")
    if norm(group.get("normalized_meaning")) != norm(STALE):
        raise ValueError("p222 known stale group meaning drift")
    requirements = [
        row for row in group.get("requirements", [])
        if isinstance(row, dict) and row.get("requirement_id") == REQ
    ]
    if len(requirements) != 1:
        raise ValueError("p222 target requirement missing or duplicated")
    requirement = requirements[0]
    for key, expected in (
        ("source_id", SOURCE), ("document_id", DOCUMENT), ("page", PAGE),
        ("code", CODE), ("source_locator", LOCATOR),
    ):
        if requirement.get(key) != expected:
            raise ValueError(f"p222 target requirement source drift: {key}")
    if "normalized_meaning" in requirement and norm(requirement.get("normalized_meaning")) != norm(STALE):
        raise ValueError("p222 requirement meaning drift before correction")

    accepted_sets = [
        row for g in data.get("semantic_review_groups", [])
        if isinstance(g, dict)
        for row in g.get("accepted_component_sets", []) or []
        if isinstance(row, dict)
    ]
    if any(row.get("admission_unit_id") == UNIT or row.get("requirement_id") == REQ for row in accepted_sets):
        raise ValueError("p222 exact object already present in accepted component sets")
    refs_before = {ref for row in accepted_sets for ref in row.get("canonical_component_refs", []) or []}
    if any(ref in refs_before for ref in COMPONENTS):
        raise ValueError("p222 component refs unexpectedly already used by exact object sets")

    accepted_authorities.append({
        "id": SEMANTIC_AUTHORITY_ID,
        "authority_kind": "BOUNDED_SUBJECT_SEMANTIC",
        "sha256": semantic_sha,
        "status": semantic["status"],
        "accepted_admission_units": 0,
        "accepted_requirements": 0,
        "canonical_component_refs": 0,
        "accepted_route_semantics": 0,
        "accepted_subject_semantics": 2,
        "semantic_identity_admissions": 2,
    })
    accepted_authorities.append({
        "id": OBJECT_AUTHORITY_ID,
        "authority_kind": "OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET_WITH_SOURCE_CORRECTION",
        "sha256": AUTHORITY_SHA,
        "status": authority["status"],
        "accepted_admission_units": 1,
        "accepted_requirements": 1,
        "canonical_component_refs": 2,
        "accepted_route_semantics": 0,
        "accepted_subject_semantics": 0,
        "semantic_identity_admissions": 0,
    })

    group.setdefault("accepted_component_sets", []).append({
        "accepted_authority_id": OBJECT_AUTHORITY_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "packet_group": GROUP,
        "source_id": SOURCE,
        "document_id": DOCUMENT,
        "content_code": CODE,
        "source_locator": LOCATOR,
        "modules": ["RU-PROG-09"],
        "canonical_component_refs": COMPONENTS,
        "component_count": 2,
        "authority": {
            "base_current_v29_head_sha": BASE_HEAD,
            "base_current_v29_normalized_sha256": BASE_SHA,
            "bounded_semantic_acceptance_head_sha": SEMANTIC_HEAD,
            "bounded_semantic_acceptance_run_id": SEMANTIC_RUN_ID,
            "bounded_semantic_acceptance_sha256": semantic_sha,
            "exact_object_binding_review_head_sha": REVIEW_HEAD,
            "exact_object_binding_review_run_id": REVIEW_RUN_ID,
            "exact_object_binding_review_normalized_sha256": REVIEW_SHA,
            "accepted_authority_normalized_sha256": AUTHORITY_SHA,
            "component_specific_independent_evidence_items": 8,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
        "source_correction": deepcopy(correction),
    })
    group["accepted_component_set_count"] = 1
    group["normalized_meaning"] = OFFICIAL
    if "normalized_meaning" in requirement:
        requirement["normalized_meaning"] = OFFICIAL
    group["status"] = "SUBJECT_ACCEPTED_COMPONENT_SET_COMPLETE"
    group["remaining_group_action"] = "NONE; EXACT OFFICIAL SOURCE OBJECT ACCEPTED WITH SOURCE CORRECTION"

    deltas = (
        ("semantic_units_with_accepted_component_sets", 1),
        ("semantic_requirements_with_accepted_component_sets", 1),
        ("semantic_units_remaining_without_accepted_component_set", -1),
        ("semantic_requirements_remaining_without_accepted_component_set", -1),
        ("subject_disposed_units_total", 1),
        ("subject_disposed_requirements_total", 1),
        ("subject_review_units_remaining", -1),
        ("subject_review_requirements_remaining", -1),
        ("canonical_component_refs_reused_unique", 2),
        ("review_groups_with_accepted_component_sets", 1),
        ("fully_accepted_semantic_groups", 1),
        ("accepted_bounded_ru_subject_semantics", 2),
        ("accepted_bounded_ru_semantics_total", 2),
    )
    for key, delta in deltas:
        summary[key] += delta
    for key, expected in AFTER.items():
        if summary.get(key) != expected:
            raise ValueError(f"post-p222 aggregate drift: {key}")
    if len(accepted_authorities) != 77:
        raise ValueError("post-p222 accepted authority count drift")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("post-p222 false exact mastery opened")

    data["schema_version"] = "0.32.0"
    data["base_current_launch_progress_v29_head_sha"] = BASE_HEAD
    data["base_current_launch_progress_v29_run_id"] = BASE_RUN_ID
    data["base_current_launch_progress_v29_normalized_sha256"] = BASE_SHA
    data["newly_integrated_bounded_subject_semantics"] = {
        "authority_id": SEMANTIC_AUTHORITY_ID,
        "authority_sha256": semantic_sha,
        "semantic_ids": COMPONENTS,
        "semantic_identity_admissions": 2,
        "object_level_closures_by_semantic_acceptance": 0,
        "exact_mastery_admissions": 0,
    }
    data["newly_accepted_exact_object"] = {
        "accepted_authority_id": OBJECT_AUTHORITY_ID,
        "admission_unit_id": UNIT,
        "requirement_id": REQ,
        "accepted_component_refs": COMPONENTS,
        "component_specific_independent_evidence": EVIDENCE,
        "independent_evidence_items": 8,
        "semantic_identity_admissions_by_object_acceptance": 0,
        "exact_mastery_admissions": 0,
        "source_correction": {
            "from_repository_meaning": STALE,
            "to_official_source_text": OFFICIAL,
            "official_document_sha256": DOC_SHA,
        },
        "completed_review_group": GROUP,
    }
    data.setdefault("policy", {})["ru09_p222_exact_official_source_text_controls_object_identity"] = True
    data["policy"]["ru09_p222_source_correction_required_for_object_disposal"] = True
    data["policy"]["ru09_p222_generic_score_can_emit_exact_mastery"] = False
    data["policy"]["ru09_p222_anonymous_or_device_only_progress_can_be_canonical"] = False
    data["policy"]["ru09_p222_assistance_record_required_for_future_canonical_evidence"] = True
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
        print("RUSSIAN_RU09_EDSOO59_P222_8_1_EXACT_OBJECT_ACCEPTANCE=PASS")
        print("SOURCE_CORRECTIONS=1")
        print("INTEGRATED_SUBJECT_SEMANTICS=2")
        print("OBJECT_LEVEL_CLOSURES=1")
        print("REQUIREMENT_DISPOSALS=1")
        print("EXACT_MASTERY_ADMISSIONS=0")
        print(f"ACCEPTED_AUTHORITIES={len(data['accepted_authorities'])}")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={summary['subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['subject_review_requirements_remaining']}")
        print(f"ACCEPTED_BOUNDED_RU_SUBJECT_SEMANTICS={summary['accepted_bounded_ru_subject_semantics']}")
        print(f"FALSE_EXACT_MASTERY={summary['false_exact_mastery_admissions']}")
        print(f"NORMALIZED_SHA256={data['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
