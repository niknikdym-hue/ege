#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parent
TRACKED = HERE / "RU15-OGE-EXPOSITION-BOUNDED-ROUTE-SEMANTIC-ACCEPTANCE-v0.1.json"
BUILDER = HERE / "build_ru15_oge_exposition_route_boundary_review.py"
CONTENT = PROGRAM / "production-learning-content/RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json"
RIGHTS = HERE / "PR139-RIGHTS-BLOCKED-SALVAGE-v0.1.json"
EXPECTED = {
    "ru-oge-exposition-microtheme-preservation": "IK1_CONTENT",
    "ru-oge-exposition-compression-across-text": "IK2_COMPRESSION",
    "ru-oge-exposition-logical-cohesion": "IK3_LOGIC",
    "ru-oge-exposition-full-draft-verification": "IK1_IK3_COMPOSITE_META_REVIEW",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def main() -> int:
    tracked = json.loads(TRACKED.read_text(encoding="utf-8"))
    review = runpy.run_path(str(BUILDER))["build_review"]()
    content = json.loads(CONTENT.read_text(encoding="utf-8"))
    rights = json.loads(RIGHTS.read_text(encoding="utf-8"))

    if tracked.get("status") != "CENTRAL_BRAIN_ACCEPTED_RU15_OGE_EXPOSITION_BOUNDED_ROUTE_SEMANTICS":
        raise AssertionError("RU15 acceptance status drift")
    if tracked.get("canonical_school_registry_mutated") is not False or tracked.get("new_parallel_registry_created") is not False:
        raise AssertionError("RU15 acceptance must remain an overlay")
    if review.get("status") != "CENTRAL_BRAIN_RU15_OGE_EXPOSITION_ROUTE_BOUNDARY_READY_ACCEPTANCE_NOT_ADMITTED":
        raise AssertionError("RU15 source/boundary review drift")
    if review.get("official_oge_task") != 1 or review.get("official_route") != "compressed exposition":
        raise AssertionError("RU15 OGE Task-1 route drift")
    if review.get("overlay_classification") != "OUTSIDE_SCHOOL_DENOMINATOR":
        raise AssertionError("RU15 school-denominator boundary drift")
    if review.get("duplicate_review", {}).get("current_inventory_id_collisions") != 0:
        raise AssertionError("RU15 semantic ID collision detected")

    decisions = tracked.get("decisions")
    if not isinstance(decisions, list) or len(decisions) != 4:
        raise AssertionError("RU15 accepted decision count drift")
    by_id = {str(row.get("accepted_semantic_id") or ""): row for row in decisions if isinstance(row, dict)}
    if set(by_id) != set(EXPECTED):
        raise AssertionError("RU15 accepted semantic set drift")
    content_ids = {str(row.get("proposed_semantic_id") or "") for row in content.get("units", []) if isinstance(row, dict)}
    if content_ids != set(EXPECTED):
        raise AssertionError("RU15 acceptance/content identity mismatch")
    if set(review.get("proposed_route_semantic_ids") or []) != set(EXPECTED):
        raise AssertionError("RU15 acceptance/review identity mismatch")

    for semantic_id, criterion_route in EXPECTED.items():
        row = by_id[semantic_id]
        if row.get("criterion_route") != criterion_route:
            raise AssertionError(f"RU15 criterion route drift: {semantic_id}")
        if row.get("subject_semantic_status") != "CENTRAL_BRAIN_ACCEPTED_BOUNDED_ROUTE_SEMANTIC":
            raise AssertionError(f"RU15 semantic not explicitly accepted: {semantic_id}")
        if row.get("content_ref") != "russian-program/production-learning-content/RU-PROG-15-OGE-COMPRESSED-EXPOSITION-WAVE-001-v0.1.json":
            raise AssertionError(f"RU15 content ref drift: {semantic_id}")
        if not str(row.get("boundary_guard") or "").strip() or not str(row.get("mastery_boundary") or "").strip():
            raise AssertionError(f"RU15 boundary/mastery guard missing: {semantic_id}")

    summary = tracked.get("summary") or {}
    expected_summary = {
        "accepted_route_semantics": 4,
        "accepted_criteria_routes": 3,
        "accepted_composite_meta_review_semantics": 1,
        "accepted_ru_route_semantics": 4,
        "new_school_canonical_identities": 0,
        "object_level_admission_units_closed": 0,
        "object_level_requirements_closed": 0,
        "rights_blocked_assets_admitted": 0,
        "false_exact_mastery_admissions": 0,
    }
    if summary != expected_summary:
        raise AssertionError("RU15 acceptance summary drift")

    policy = tracked.get("policy") or {}
    for key in (
        "task1_is_route_not_universal_semantic_identity",
        "criterion_label_is_not_semantic_identity",
        "component_specific_independent_evidence_required",
        "full_draft_verification_is_composite_meta_skill_not_component_mastery_substitute",
        "original_eksamio_practice_required",
    ):
        if policy.get(key) is not True:
            raise AssertionError(f"RU15 required policy weakened: {key}")
    for key in (
        "generic_task1_score_implies_exact_component_mastery",
        "generic_task1_attempt_can_emit_exact_component_mastery",
        "route_semantic_acceptance_can_reduce_object_counts_without_exact_binding",
        "rights_blocked_assets_can_ground_accepted_semantics",
    ):
        if policy.get(key) is not False:
            raise AssertionError(f"RU15 fail-closed policy weakened: {key}")
    if policy.get("rights_blocked_assets_admitted") != 0 or policy.get("official_source_passages_copied") != 0:
        raise AssertionError("RU15 rights/copyright count drift")

    rights_non_acceptance = tracked.get("rights_non_acceptance") or {}
    if rights_non_acceptance.get("pr139_task1_variants") != 5 or rights_non_acceptance.get("pr139_mp3_txt_assets") != 10:
        raise AssertionError("RU15 rights-blocked count drift")
    if rights_non_acceptance.get("authorship") != "NOT_PROVEN" or rights_non_acceptance.get("production_admission") != "EXCLUDED_RIGHTS_BLOCKED":
        raise AssertionError("RU15 rights-blocked status weakened")
    if rights_non_acceptance.get("copied_assets") != 0 or rights_non_acceptance.get("semantic_or_mastery_admission") is not False:
        raise AssertionError("RU15 rights-blocked assets admitted")
    source_decision = rights.get("decision") or {}
    if source_decision.get("production_admission") != "EXCLUDED_RIGHTS_BLOCKED" or source_decision.get("copy_assets_to_current_main_candidate") is not False:
        raise AssertionError("RU15 pinned rights authority drift")

    scoring = content.get("official_exam_scoring_overlay_2026") or {}
    if scoring.get("max_points_ik1_ik3") != 6:
        raise AssertionError("RU15 IK1-IK3 total drift")
    if sum(int((scoring.get(key) or {}).get("max_points", -100)) for key in ("IK1_content", "IK2_compression", "IK3_logic")) != 6:
        raise AssertionError("RU15 IK criterion decomposition drift")
    copyright_guard = content.get("copyright_guard") or {}
    if copyright_guard.get("official_source_passages_copied") != 0 or copyright_guard.get("practice_source_texts") != "ORIGINAL_EKSAMIO":
        raise AssertionError("RU15 content copyright guard drift")

    serialized = canonical_json(tracked).replace(b" ", b"")
    for forbidden in (
        b'"canonical_school_registry_mutated":true',
        b'"rights_blocked_assets_admitted":1',
        b'"generic_task1_attempt_can_emit_exact_component_mastery":true',
        b'"object_level_admission_units_closed":1',
    ):
        if forbidden in serialized:
            raise AssertionError("RU15 bounded route acceptance violated a hard boundary")

    print("RU15_OGE_EXPOSITION_BOUNDED_ROUTE_SEMANTIC_ACCEPTANCE=PASS")
    print("ACCEPTED_ROUTE_SEMANTICS=4")
    print("IK1_IK3_CRITERION_ROUTES=3")
    print("COMPOSITE_META_REVIEW_SEMANTICS=1")
    print("OBJECT_LEVEL_CLOSURES=0")
    print("RIGHTS_BLOCKED_ASSETS_ADMITTED=0")
    print("FALSE_EXACT_MASTERY_ADMISSIONS=0")
    print("TRACKED_ACCEPTANCE_SHA256=" + hashlib.sha256(canonical_json(tracked)).hexdigest())
    print("BOUNDARY_REVIEW_SHA256=" + str(review["normalized_sha256"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
