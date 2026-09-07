#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress with exact RU02 orthoepy object acceptance."""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v2.py"
BINDING = HERE / "build_ru02_orthoepy_exact_object_binding_review.py"
AUTHORITY = HERE / "RU02-ORTHOEPY-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

BASE_SHA = "f25202c09baf0452fce2392726ddb02ce8a17dd111851f25f58e5334e873a4c7"
BINDING_SHA = "60c0465cf74090388732a0d010043a77b6856597b8e022d93e0b074ee70ad666"
AUTHORITY_SHA = "5d4233f6919cd3857ed6320f304a2c332e8a075f0e4e34a5e2f4680600f7f1cc"
AUTHORITY_ID = "RU02_ORTHOEPY_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
TARGET_UNIT = "RAU-a8f2ad0b357c9e369c51"
TARGET_REQUIREMENT = "RSK-EDSOO1011-2-2-4-P074"
TARGET_GROUP = "RUS-SEM-REVIEW-047"
TARGET_SOURCE = "EDSOO-RU-10-11-BASIC-2025"
TARGET_DOCUMENT = "EDSOO1011"
TARGET_CODE = "2.2.4"
TARGET_LOCATOR = "EDSOO-RU-10-11-BASIC-2025/EDSOO1011 p.74 2.2.4"
COMPONENTS = [
    "ru-orthoepy-normative-pronunciation-selection",
    "ru-orthoepy-normative-stress-selection",
]


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
    base = runpy.run_path(str(BASE))["build_progress"]()
    if base.get("normalized_sha256") != BASE_SHA:
        raise ValueError("current-v2 launch fingerprint drift")
    summary = base.get("progress_summary") or {}
    expected = {
        "semantic_units_with_accepted_component_sets": 28,
        "semantic_requirements_with_accepted_component_sets": 28,
        "semantic_units_remaining_without_accepted_component_set": 1288,
        "semantic_requirements_remaining_without_accepted_component_set": 1363,
        "subject_disposed_units_total": 29,
        "subject_disposed_requirements_total": 29,
        "subject_review_units_remaining": 1287,
        "subject_review_requirements_remaining": 1362,
        "canonical_component_refs_reused_unique": 115,
        "review_groups_with_accepted_component_sets": 12,
        "false_exact_mastery_admissions": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            raise ValueError(f"current-v2 aggregate drift: {key}")
    if len(base.get("accepted_authorities", [])) != 49:
        raise ValueError("current-v2 accepted authority count drift")

    binding = runpy.run_path(str(BINDING))["build_review"]()
    if binding.get("normalized_sha256") != BINDING_SHA:
        raise ValueError("RU02 exact binding review fingerprint drift")
    if binding.get("status") != "CENTRAL_BRAIN_RU02_ORTHOEPY_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED":
        raise ValueError("RU02 exact binding review status drift")
    readiness = binding.get("acceptance_readiness") or {}
    required_flags = (
        "exact_source_identity_verified",
        "target_still_in_current_v2_remainder",
        "all_source_components_have_independently_accepted_semantic_owners",
        "all_components_have_component_specific_independent_evidence",
        "separate_object_acceptance_required",
    )
    if any(readiness.get(key) is not True for key in required_flags):
        raise ValueError("RU02 binding review is not acceptance-ready")
    if readiness.get("object_accepted_by_this_review") is not False:
        raise ValueError("RU02 binding review self-admitted")
    decomposition = binding.get("source_backed_exact_component_decomposition") or {}
    if decomposition.get("exact_component_refs") != COMPONENTS:
        raise ValueError("RU02 exact component set drift")
    if decomposition.get("independent_evidence_items") != 9:
        raise ValueError("RU02 independent evidence denominator drift")
    if decomposition.get("missing_source_components") != [] or decomposition.get("overlapping_component_boundaries") != []:
        raise ValueError("RU02 component decomposition incomplete or overlapping")

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if not isinstance(authority, dict):
        raise ValueError("RU02 accepted authority must be an object")
    verify_embedded_sha(authority, AUTHORITY_SHA)
    if authority.get("status") != "CENTRAL_BRAIN_ACCEPTED_EXACT_RU02_ORTHOEPY_CANONICAL_COMPONENT_SET":
        raise ValueError("RU02 accepted authority status drift")
    if authority.get("current_launch_progress_v2_sha256") != BASE_SHA:
        raise ValueError("RU02 accepted authority current-v2 binding drift")
    if authority.get("exact_object_binding_review_sha256") != BINDING_SHA:
        raise ValueError("RU02 accepted authority binding-review drift")
    decision = authority.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("RU02 accepted decision missing")
    exact_identity = {
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQUIREMENT,
        "packet_group": TARGET_GROUP,
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "content_code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "module_id": "RU-PROG-02",
        "normalized_meaning": "Применять нормативное произношение и ударение.",
        "disposition": "PARTIAL_OR_COMPOSITE",
        "canonical_component_refs": COMPONENTS,
        "component_count": 2,
        "independent_evidence_items": 9,
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    for key, value in exact_identity.items():
        if decision.get(key) != value:
            raise ValueError(f"RU02 accepted authority identity drift: {key}")
    mastery = decision.get("mastery_boundary") or {}
    if mastery.get("component_specific_independent_evidence_required") is not True:
        raise ValueError("RU02 component-specific evidence guard weakened")
    if mastery.get("generic_orthoepy_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("RU02 generic orthoepy attempt can emit exact mastery")
    if mastery.get("stress_evidence_can_substitute_for_pronunciation") is not False:
        raise ValueError("RU02 stress can substitute for pronunciation")
    if mastery.get("pronunciation_evidence_can_substitute_for_stress") is not False:
        raise ValueError("RU02 pronunciation can substitute for stress")
    if (authority.get("summary") or {}).get("false_exact_mastery_admissions") != 0:
        raise ValueError("RU02 accepted authority introduced false exact mastery")

    groups = [g for g in base.get("semantic_review_groups", []) if isinstance(g, dict) and g.get("group_id") == TARGET_GROUP]
    if len(groups) != 1:
        raise ValueError("RU02 target review group is not unique")
    group = groups[0]
    if TARGET_UNIT not in set(map(str, group.get("admission_unit_ids", []))):
        raise ValueError("RU02 target unit missing from group")
    rows = [r for r in group.get("requirements", []) if isinstance(r, dict) and r.get("requirement_id") == TARGET_REQUIREMENT]
    if len(rows) != 1:
        raise ValueError("RU02 target requirement is not unique")
    row = rows[0]
    for source_key, expected_value in (
        ("source_id", TARGET_SOURCE),
        ("document_id", TARGET_DOCUMENT),
        ("code", TARGET_CODE),
        ("source_locator", TARGET_LOCATOR),
    ):
        if row.get(source_key) != expected_value:
            raise ValueError(f"RU02 source identity drift: {source_key}")
    if any(
        isinstance(r, dict) and (r.get("admission_unit_id") == TARGET_UNIT or r.get("requirement_id") == TARGET_REQUIREMENT)
        for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for r in g.get("accepted_component_sets", [])
    ):
        raise ValueError("RU02 target already accepted in current-v2")
    if any(
        isinstance(r, dict) and (r.get("admission_unit_id") == TARGET_UNIT or r.get("requirement_id") == TARGET_REQUIREMENT)
        for g in base.get("semantic_review_groups", []) if isinstance(g, dict)
        for r in g.get("accepted_nonsemantic_object_dispositions", [])
    ):
        raise ValueError("RU02 target already disposed nonsemantically")
    if any(isinstance(r, dict) and r.get("id") == AUTHORITY_ID for r in base.get("accepted_authorities", [])):
        raise ValueError("RU02 authority already integrated")

    projection = {
        "accepted_authority_id": AUTHORITY_ID,
        "admission_unit_id": TARGET_UNIT,
        "requirement_id": TARGET_REQUIREMENT,
        "packet_group": TARGET_GROUP,
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "content_code": TARGET_CODE,
        "source_locator": TARGET_LOCATOR,
        "modules": ["RU-PROG-02"],
        "canonical_component_refs": COMPONENTS,
        "component_count": 2,
        "authority": {
            "exact_object_binding_review_normalized_sha256": BINDING_SHA,
            "accepted_authority_normalized_sha256": AUTHORITY_SHA,
            "component_specific_independent_evidence_items": 9,
        },
        "mastery_boundary": deepcopy(mastery),
        "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
    }
    group.setdefault("accepted_component_sets", []).append(deepcopy(projection))
    group["accepted_component_set_count"] = len(group["accepted_component_sets"])
    if group["accepted_component_set_count"] != 1:
        raise ValueError("RU02 accepted component set duplicated")
    group["status"] = "SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
    group["remaining_group_action"] = "CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"

    base["accepted_authorities"].append({
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

    summary["semantic_units_with_accepted_component_sets"] += 1
    summary["semantic_requirements_with_accepted_component_sets"] += 1
    summary["semantic_units_remaining_without_accepted_component_set"] -= 1
    summary["semantic_requirements_remaining_without_accepted_component_set"] -= 1
    summary["subject_disposed_units_total"] += 1
    summary["subject_disposed_requirements_total"] += 1
    summary["subject_review_units_remaining"] -= 1
    summary["subject_review_requirements_remaining"] -= 1
    summary["review_groups_with_accepted_component_sets"] += 1
    summary["canonical_component_refs_reused_unique"] += 2

    expected_after = {
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
    for key, value in expected_after.items():
        if summary.get(key) != value:
            raise ValueError(f"RU02 post-acceptance aggregate drift: {key}")
    if len(base["accepted_authorities"]) != 50:
        raise ValueError("RU02 post-acceptance authority count drift")

    base["schema_version"] = "0.6.0"
    base["base_current_launch_progress_v2_sha256"] = BASE_SHA
    base["policy"]["exact_ru02_object_acceptance_requires_source_backed_full_component_set"] = True
    base["policy"]["exact_ru02_object_acceptance_requires_component_specific_independent_evidence"] = True
    base["policy"]["generic_ru02_attempt_can_emit_exact_component_mastery"] = False
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
        print("RUSSIAN_RU02_EXACT_OBJECT_ACCEPTANCE=PASS")
        print(f"ACCEPTED_UNIT={TARGET_UNIT}")
        print("EXACT_COMPONENT_REFS=2")
        print("INDEPENDENT_EVIDENCE_ITEMS=9")
        print(f"ACCEPTED_AUTHORITIES={len(result['accepted_authorities'])}")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={summary['subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={summary['subject_review_requirements_remaining']}")
        print(f"FALSE_EXACT_MASTERY={summary['false_exact_mastery_admissions']}")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
