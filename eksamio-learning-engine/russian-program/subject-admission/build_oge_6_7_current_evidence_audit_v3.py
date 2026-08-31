#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
PRIOR_BUILDER = HERE / "build_oge_6_7_current_evidence_audit_v2.py"
WAVE_VALIDATOR = HERE / "validate_oge_6_7_component_evidence_wave_003.py"
WAVE_PACK = ENGINE / "russian-program" / "production-learning-content" / "RU-PROG-08-OGE-6.7-COMPONENT-EVIDENCE-WAVE-003-v0.1.json"
TARGET_OWNERS = {
    "school-noun-case-ending-base",
    "school-noun-case-ending-special-paradigms",
    "school-noun-genitive-plural-ending-system",
    "school-noun-special-suffix-gender-endings",
    "school-proper-name-instrumental-ending-boundary",
}
MINIMUM_EXACT_ITEMS_PER_OWNER = 3


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _current_item(item: dict[str, Any], owner: str) -> dict[str, Any]:
    return {
        "source_system": "current_launch_original_eksamio_component_evidence",
        "source_id": str(item["id"]),
        "review_status": "validated_current_launch_component_evidence_wave_003",
        "school_semantic_refs": [owner],
        "evidence_provenance_refs": [
            "russian-program/production-learning-content/RU-PROG-08-OGE-6.7-COMPONENT-EVIDENCE-WAVE-003-v0.1.json",
            "russian-program/subject-admission/validate_oge_6_7_component_evidence_wave_003.py",
        ],
        "reuse_scope": "OGE_2026_6_7_ENDINGS_ONLY",
    }


def build_current_audit_v3() -> dict[str, Any]:
    prior = runpy.run_path(str(PRIOR_BUILDER))["build_current_audit_v2"]()
    if prior.get("status") != "CENTRAL_BRAIN_OGE_6_7_CURRENT_COMPONENT_EVIDENCE_WAVE_002_INTEGRATED_NO_OBJECT_ACCEPTANCE":
        raise ValueError("unexpected prior OGE 6.7 v2 status")
    prior_summary = prior.get("summary") or {}
    expected_prior = {
        "exact_owner_frontier": 12,
        "owners_with_explicit_component_specific_independent_evidence": 7,
        "owners_with_insufficient_exact_evidence": 0,
        "owners_with_mixed_semantic_evidence_only": 0,
        "owners_with_no_inventoried_independent_evidence": 5,
        "ready_for_separate_exact_object_acceptance": False,
        "semantic_admissions": 0,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
    }
    for key, expected in expected_prior.items():
        if prior_summary.get(key) != expected:
            raise ValueError(f"prior OGE 6.7 v2 drift: {key}")
    if set(prior.get("remaining_no_evidence_owner_refs") or []) != TARGET_OWNERS:
        raise ValueError("prior remaining OGE 6.7 owner frontier drift")

    validation = runpy.run_path(str(WAVE_VALIDATOR))["validate"]()
    if validation.get("status") != "COMPLETE":
        raise ValueError("OGE 6.7 wave 003 is not validated complete")
    if validation.get("owners_completed_with_new_component_evidence") != 5 or validation.get("new_independent_items") != 15:
        raise ValueError("OGE 6.7 wave 003 denominator drift")
    if validation.get("object_closures") != 0 or validation.get("false_exact_mastery_admissions") != 0:
        raise ValueError("OGE 6.7 wave 003 weakened no-admission boundary")
    if validation.get("learner_audio_persistence") != 0:
        raise ValueError("OGE 6.7 wave 003 learner-audio guard weakened")

    pack = load(WAVE_PACK)
    pack_rows = {
        str(row.get("canonical_ref")): row
        for row in pack.get("owner_evidence") or []
        if isinstance(row, dict)
    }
    if set(pack_rows) != TARGET_OWNERS:
        raise ValueError("OGE 6.7 wave 003 owner set drift")

    result = copy.deepcopy(prior)
    owner_reviews = [row for row in result.get("owner_reviews") or [] if isinstance(row, dict)]
    by_owner = {str(row.get("canonical_ref")): row for row in owner_reviews}
    if len(owner_reviews) != 12 or len(by_owner) != 12:
        raise ValueError("OGE 6.7 v3 owner denominator drift")
    for owner in sorted(TARGET_OWNERS):
        row = by_owner[owner]
        if row.get("evidence_status") != "NO_INVENTORIED_INDEPENDENT_LEARNER_EVIDENCE":
            raise ValueError(f"wave 003 target is not a clean no-evidence gap: {owner}")
        if int(row.get("exact_component_independent_item_count") or 0) != 0:
            raise ValueError(f"wave 003 target already had exact evidence: {owner}")
        if int(row.get("mixed_semantic_independent_item_count") or 0) != 0:
            raise ValueError(f"wave 003 target already had mixed evidence: {owner}")
        items = [item for item in pack_rows[owner].get("independent_verification") or [] if isinstance(item, dict)]
        if len(items) != MINIMUM_EXACT_ITEMS_PER_OWNER:
            raise ValueError(f"wave 003 owner lost exact-item floor: {owner}")
        current_items = [_current_item(item, owner) for item in items]
        if len({item["source_id"] for item in current_items}) != MINIMUM_EXACT_ITEMS_PER_OWNER:
            raise ValueError(f"wave 003 duplicate item id: {owner}")
        row["exact_component_independent_items"] = sorted(current_items, key=lambda item: item["source_id"])
        row["exact_component_independent_item_count"] = MINIMUM_EXACT_ITEMS_PER_OWNER
        row["evidence_status"] = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"

    for row in owner_reviews:
        if row.get("evidence_status") != "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT":
            raise ValueError(f"OGE 6.7 v3 owner is not exact-evidence-ready: {row.get('canonical_ref')}")
        if int(row.get("exact_component_independent_item_count") or 0) < MINIMUM_EXACT_ITEMS_PER_OWNER:
            raise ValueError(f"OGE 6.7 v3 owner below exact-item floor: {row.get('canonical_ref')}")
        if int(row.get("mixed_semantic_independent_item_count") or 0) != 0:
            raise ValueError(f"OGE 6.7 v3 owner gained mixed evidence: {row.get('canonical_ref')}")

    result.pop("normalized_sha256", None)
    result["schema_version"] = "0.5.0"
    result["status"] = "CENTRAL_BRAIN_OGE_6_7_COMPONENT_EVIDENCE_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE_NOT_ACCEPTED"
    result["scope"] = "OGE_2026_CONTENT_CODE_6_7_CURRENT_COMPONENT_EVIDENCE_AUDIT_AFTER_WAVES_001_002_003"
    result["prior_current_audit"] = {
        "builder": "russian-program/subject-admission/build_oge_6_7_current_evidence_audit_v2.py",
        "exact_ready_owners_before_wave_003": 7,
        "object_acceptance": False,
    }
    result["validated_current_evidence_waves"] = list(result.get("validated_current_evidence_waves") or []) + [
        {
            "id": "OGE_6_7_COMPONENT_EVIDENCE_WAVE_003",
            "pack": "russian-program/production-learning-content/RU-PROG-08-OGE-6.7-COMPONENT-EVIDENCE-WAVE-003-v0.1.json",
            "validator": "russian-program/subject-admission/validate_oge_6_7_component_evidence_wave_003.py",
            "owners_completed": 5,
            "new_independent_items": 15,
            "object_closures": 0,
        }
    ]
    result["owner_reviews"] = owner_reviews
    result["remaining_no_evidence_owner_refs"] = []
    result["summary"] = {
        "exact_owner_frontier": 12,
        "owners_with_explicit_component_specific_independent_evidence": 12,
        "owners_with_insufficient_exact_evidence": 0,
        "owners_with_mixed_semantic_evidence_only": 0,
        "owners_with_no_inventoried_independent_evidence": 0,
        "reused_route_scoped_independent_items": 5,
        "wave_001_new_independent_items": 1,
        "wave_002_new_independent_items": 15,
        "wave_003_new_independent_items": 15,
        "total_exact_independent_items_added_or_reused_by_bounded_oge_6_7_audits": 36,
        "ready_for_separate_exact_object_acceptance": True,
        "semantic_admissions": 0,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
    }
    if result.get("target", {}).get("requirement_id") != "RSK-OGE_COD-6-7-P025":
        raise ValueError("OGE 6.7 requirement target drift")
    if result.get("target", {}).get("admission_unit_id") != "RAU-2668e140328e4edee952":
        raise ValueError("OGE 6.7 admission-unit target drift")
    expected_safety = {
        "accepted_demo_or_scorer_change": False,
        "tilda_change": False,
        "learner_audio_persistence": 0,
        "production_peis_write": False,
        "provider_execution": False,
        "public_traffic": False,
        "real_payment_or_refund": False,
        "real_message_delivery": False,
    }
    if result.get("safety") != expected_safety:
        raise ValueError("OGE 6.7 v3 safety boundary drift")
    result["normalized_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_current_audit_v3()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        summary = result["summary"]
        print("OGE_6_7_CURRENT_EVIDENCE_AUDIT_V3=PASS")
        print(f"REQUIREMENT_ID={result['target']['requirement_id']}")
        print(f"ADMISSION_UNIT_ID={result['target']['admission_unit_id']}")
        print(f"EXACT_OWNER_FRONTIER={summary['exact_owner_frontier']}")
        print(f"OWNERS_WITH_EXACT_COMPONENT_EVIDENCE={summary['owners_with_explicit_component_specific_independent_evidence']}")
        print(f"OWNERS_WITH_INSUFFICIENT_EXACT={summary['owners_with_insufficient_exact_evidence']}")
        print(f"OWNERS_WITH_MIXED_ONLY={summary['owners_with_mixed_semantic_evidence_only']}")
        print(f"OWNERS_WITH_NO_INDEPENDENT_EVIDENCE={summary['owners_with_no_inventoried_independent_evidence']}")
        print(f"WAVE_003_NEW_ITEMS={summary['wave_003_new_independent_items']}")
        print("READY_FOR_EXACT_OBJECT_ACCEPTANCE=1")
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
