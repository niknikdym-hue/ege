#!/usr/bin/env python3
"""Fail-closed exact object-binding review for EDSOO59 p.222 code 8.1.

This gate binds one exact official-source object to the two bounded semantics
already admitted by exact-head CI. It does not accept/close the object, mutate
the aggregate, create current-v30, or emit mastery.
"""
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
REVIEW = HERE / "RU09-EDSOO59-P222-8-1-EXACT-OBJECT-BINDING-REVIEW-v0.1.json"
SEMANTIC = HERE / "RU09-EDSOO59-P222-8-1-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
CURRENT = HERE / "build_russian_semantic_acceptance_progress_launch_current_v29.py"
MANIFEST = ENGINE / "russian-program/source-knowledge/RUSSIAN-OFFICIAL-SOURCE-MANIFEST-v1.0.json"

EXPECTED_REVIEW_SHA = "6426cc3204a3e44163d0e091a6ec3a288aa7ad0cc79c661c8d12c0ccfdae4c8c"
EXPECTED_CURRENT_SHA = "7e7b74ddf4aa4fc9df9744ec74191d8893b6ae251b703c36dcd2ef911273d8e4"
EXPECTED_SEMANTIC_HEAD = "a05cdc663753af46846952d9e05ea82ae0bfed1b"
EXPECTED_SEMANTIC_RUN = 34682168590
GROUP = "RUS-SEM-REVIEW-048"
UNIT = "RAU-3ceb45ca22608d520ddf"
REQ = "RSK-EDSOO59-8-1-P222"
SOURCE = "EDSOO-RU-5-9-2025"
DOCUMENT = "EDSOO59"
PAGE = 222
CODE = "8.1"
LOCATOR = "EDSOO-RU-5-9-2025/EDSOO59 p.222 8.1"
DOC_SHA = "1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d"
STALE_MEANING = (
    "Применять нормативное произношение и ударение. "
    "Анализировать синтаксическую конструкцию и её нормативность."
)
COMPONENTS = [
    (
        "edsoo59-p222-8-1-sentence-formulation-means",
        "ru-syntax-sentence-formulation-means",
        "Средства оформления предложения в устной и письменной речи "
        "(интонация, логическое ударение, знаки препинания)",
        [f"p09-u6-v{i}" for i in range(1, 5)],
    ),
    (
        "edsoo59-p222-8-1-inversion-norm",
        "ru-syntax-inversion-norm",
        "Нормы использования инверсии",
        [f"p09-u7-v{i}" for i in range(1, 5)],
    ),
]
OFFICIAL_TEXT = ". ".join(row[2] for row in COMPONENTS)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def verify_manifest() -> None:
    manifest = load(MANIFEST)
    rows = [
        row
        for row in manifest.get("documents", [])
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


def verify_current_v29() -> None:
    current = runpy.run_path(str(CURRENT))["build_progress"]()
    if current.get("schema_version") != "0.31.0":
        raise ValueError("current-v29 schema drift")
    if current.get("normalized_sha256") != EXPECTED_CURRENT_SHA:
        raise ValueError("current-v29 normalized SHA drift")
    summary = current.get("progress_summary") or {}
    expected_summary = {
        "semantic_units_with_accepted_component_sets": 45,
        "semantic_requirements_with_accepted_component_sets": 45,
        "subject_disposed_units_total": 46,
        "subject_disposed_requirements_total": 46,
        "subject_review_units_remaining": 1270,
        "subject_review_requirements_remaining": 1345,
        "accepted_bounded_ru_subject_semantics": 75,
        "accepted_bounded_ru_semantics_total": 84,
        "false_exact_mastery_admissions": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            raise ValueError(f"current-v29 summary drift: {key}")
    if len(current.get("accepted_authorities") or []) != 75:
        raise ValueError("current-v29 authority count drift")

    groups = [
        row
        for row in current.get("semantic_review_groups", [])
        if isinstance(row, dict) and row.get("group_id") == GROUP
    ]
    if len(groups) != 1:
        raise ValueError("target current-v29 group missing or duplicated")
    group = groups[0]
    if group.get("admission_unit_ids") != [UNIT]:
        raise ValueError("target admission-unit identity drift")
    if group.get("admission_unit_count") != 1 or group.get("requirement_count") != 1:
        raise ValueError("target group denominator drift")
    if group.get("accepted_component_set_count") not in (None, 0):
        raise ValueError("target unexpectedly already has an accepted component set")
    if group.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("target object is no longer pending exact subject acceptance")
    if norm(group.get("normalized_meaning")) != norm(STALE_MEANING):
        raise ValueError("known stale repository meaning drift")

    requirements = [
        row
        for row in group.get("requirements", [])
        if isinstance(row, dict) and row.get("requirement_id") == REQ
    ]
    if len(requirements) != 1:
        raise ValueError("target requirement missing or duplicated")
    req = requirements[0]
    exact = {
        "source_id": SOURCE,
        "document_id": DOCUMENT,
        "page": PAGE,
        "code": CODE,
        "source_locator": LOCATOR,
        "grades": ["8"],
    }
    for key, expected in exact.items():
        if req.get(key) != expected:
            raise ValueError(f"target repository source identity drift: {key}")


def verify_semantic_acceptance() -> None:
    semantic = load(SEMANTIC)
    if (
        semantic.get("status")
        != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTICS_OBJECT_BINDING_STILL_REQUIRED"
    ):
        raise ValueError("bounded semantic acceptance status drift")
    target = semantic.get("target_object") or {}
    if (
        target.get("admission_unit_id"),
        target.get("requirement_id"),
        target.get("review_group_id"),
        target.get("source_locator"),
    ) != (UNIT, REQ, GROUP, LOCATOR):
        raise ValueError("bounded semantic target identity drift")
    source = semantic.get("official_source") or {}
    if source.get("document_sha256") != DOC_SHA:
        raise ValueError("bounded semantic source SHA drift")
    if norm(source.get("exact_object_text")) != norm(OFFICIAL_TEXT):
        raise ValueError("bounded semantic official object text drift")

    rows = semantic.get("accepted_semantics") or []
    if len(rows) != 2:
        raise ValueError("expected exactly two bounded semantics")
    by_id = {row.get("semantic_id"): row for row in rows if isinstance(row, dict)}
    if len(by_id) != 2:
        raise ValueError("bounded semantic identities missing or duplicated")
    for source_component_id, semantic_id, exact_text, evidence in COMPONENTS:
        row = by_id.get(semantic_id)
        if not row:
            raise ValueError(f"missing bounded semantic: {semantic_id}")
        if row.get("source_component_id") != source_component_id:
            raise ValueError(f"source component drift: {semantic_id}")
        if norm(row.get("exact_source_text")) != norm(exact_text):
            raise ValueError(f"exact source text drift: {semantic_id}")
        if row.get("state") != "ADMITTED":
            raise ValueError(f"semantic no longer admitted: {semantic_id}")
        if row.get("independent_component_evidence_ids") != evidence:
            raise ValueError(f"component evidence drift: {semantic_id}")
        if row.get("object_closure_effect") != "NONE_UNTIL_SEPARATE_EXACT_OBJECT_BINDING_REVIEW":
            raise ValueError(f"semantic object boundary weakened: {semantic_id}")
        if row.get("exact_mastery_effect") != "NONE":
            raise ValueError(f"semantic mastery boundary weakened: {semantic_id}")
        if row.get("false_exact_mastery") != 0:
            raise ValueError(f"false exact mastery opened: {semantic_id}")

    joined = ". ".join(
        by_id[semantic_id]["exact_source_text"] for _, semantic_id, _, _ in COMPONENTS
    )
    if norm(joined) != norm(OFFICIAL_TEXT):
        raise ValueError("bounded semantic component set does not exactly cover official object")


def verify_review() -> None:
    review = load(REVIEW)
    body = dict(review)
    actual_sha = body.pop("normalized_sha256", None)
    calculated = hashlib.sha256(canonical_bytes(body)).hexdigest()
    if actual_sha != EXPECTED_REVIEW_SHA or calculated != EXPECTED_REVIEW_SHA:
        raise ValueError("object-binding review normalized SHA drift")
    if (
        review.get("status")
        != "CENTRAL_BRAIN_RU09_EDSOO59_P222_8_1_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED"
    ):
        raise ValueError("object-binding review status drift")
    gate = review.get("base_exact_head") or {}
    if (
        gate.get("head_sha") != EXPECTED_SEMANTIC_HEAD
        or gate.get("semantic_acceptance_run_id") != EXPECTED_SEMANTIC_RUN
        or gate.get("semantic_acceptance_conclusion") != "SUCCESS"
    ):
        raise ValueError("semantic acceptance exact-head gate drift")

    target = review.get("target_object") or {}
    expected_target = {
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
    for key, expected in expected_target.items():
        if target.get(key) != expected:
            raise ValueError(f"review target drift: {key}")

    source = review.get("official_source") or {}
    if source.get("document_sha256") != DOC_SHA or norm(source.get("exact_object_text")) != norm(OFFICIAL_TEXT):
        raise ValueError("review official source identity drift")

    rows = review.get("bound_component_set") or []
    if len(rows) != 2:
        raise ValueError("review must bind exactly two semantics")
    for row, expected in zip(rows, COMPONENTS):
        source_component_id, semantic_id, exact_text, evidence = expected
        if row.get("source_component_id") != source_component_id:
            raise ValueError("review source component drift")
        if row.get("semantic_id") != semantic_id:
            raise ValueError("review semantic identity drift")
        if norm(row.get("exact_source_text")) != norm(exact_text):
            raise ValueError("review component text drift")
        if row.get("semantic_state") != "ADMITTED_BY_EXACT_HEAD_CI":
            raise ValueError("review semantic CI state drift")
        if row.get("independent_component_evidence_ids") != evidence:
            raise ValueError("review evidence identity drift")

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
            raise ValueError(f"review binding readiness drift: {key}")
    for key in (
        "keyword_fuzzy_embedding_inference_used",
        "route_module_title_task_number_inference_used",
        "object_accepted_by_this_review",
    ):
        if binding.get(key) is not False:
            raise ValueError(f"review fail-closed binding boundary drift: {key}")
    if binding.get("missing_source_components") != [] or binding.get("overlapping_component_boundaries") != []:
        raise ValueError("review component set is incomplete or overlapping")

    policy = review.get("policy") or {}
    for key in (
        "semantic_acceptance_alone_can_close_object",
        "this_review_can_close_object",
        "this_review_can_dispose_requirement",
        "this_review_can_emit_exact_mastery",
        "this_review_can_mutate_aggregate",
        "this_review_can_create_current_v30",
        "generic_ru09_score_can_grant_exact_mastery",
    ):
        if policy.get(key) is not False:
            raise ValueError(f"review policy weakened: {key}")
    for key in (
        "separate_exact_object_acceptance_required",
        "aggregate_source_correction_requires_separate_acceptance",
        "registered_user_identity_ref_required_for_future_canonical_learner_evidence",
        "assistance_must_be_recorded_for_future_canonical_learner_evidence",
        "fail_closed_on_source_semantic_or_evidence_identity_drift",
    ):
        if policy.get(key) is not True:
            raise ValueError(f"review required safeguard missing: {key}")
    if policy.get("false_exact_mastery") != 0:
        raise ValueError("review false exact mastery drift")

    effect = review.get("progress_effect") or {}
    expected_zero = {
        "semantic_admissions": 0,
        "object_level_closures": 0,
        "requirement_disposals": 0,
        "mastery_admissions": 0,
        "aggregate_mutated": False,
        "current_v30_created": False,
        "current_v29_remainder_units_preserved": 1270,
        "current_v29_remainder_requirements_preserved": 1345,
        "false_exact_mastery": 0,
    }
    for key, expected in expected_zero.items():
        if effect.get(key) != expected:
            raise ValueError(f"review progress effect drift: {key}")


def main() -> int:
    verify_manifest()
    verify_current_v29()
    verify_semantic_acceptance()
    verify_review()
    print("RU09_EDSOO59_P222_8_1_EXACT_OBJECT_BINDING_REVIEW=PASS")
    print(f"TARGET_UNIT={UNIT}")
    print(f"TARGET_REQUIREMENT={REQ}")
    print("BOUND_COMPONENTS=2")
    print("INDEPENDENT_EVIDENCE_ITEMS=8")
    print("OBJECT_CLOSURES_BY_REVIEW=0")
    print("CURRENT_V30_CREATED=0")
    print("FALSE_EXACT_MASTERY=0")
    print(f"NORMALIZED_SHA256={EXPECTED_REVIEW_SHA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
