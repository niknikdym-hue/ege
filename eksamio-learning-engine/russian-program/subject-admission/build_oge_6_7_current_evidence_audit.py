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
BASE_AUDITOR = HERE / "build_oge_6_7_object_evidence_audit.py"
WAVE_VALIDATOR = HERE / "validate_oge_6_7_component_evidence_wave_001.py"
WAVE_PACK = (
    ENGINE
    / "russian-program"
    / "production-learning-content"
    / "RU-PROG-08-OGE-6.7-COMPONENT-EVIDENCE-WAVE-001-v0.1.json"
)

TARGET_OWNER = "school-o-e-after-sibilants-suffix-ending"
TARGET_NEW_ITEM_ID = "oge67-shib-end-v3"
EXPECTED_BASE_READY_OWNER = "school-vowels-after-ts-suffix-ending"
MINIMUM_EXACT_ITEMS_PER_OWNER = 3


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _validate_base(base: dict[str, Any]) -> None:
    if base.get("status") != "CENTRAL_BRAIN_OGE_6_7_COMPONENT_EVIDENCE_GAPS_PROVEN_NO_OBJECT_ACCEPTANCE":
        raise ValueError("unexpected base OGE 6.7 evidence audit status")
    summary = base.get("summary") or {}
    expected = {
        "exact_owner_frontier": 12,
        "owners_with_explicit_component_specific_independent_evidence": 1,
        "owners_with_insufficient_exact_evidence": 1,
        "owners_with_mixed_semantic_evidence_only": 0,
        "owners_with_no_inventoried_independent_evidence": 10,
        "reused_route_scoped_independent_items": 5,
        "ready_for_separate_exact_object_acceptance": False,
        "semantic_admissions": 0,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
    }
    for key, expected_value in expected.items():
        if summary.get(key) != expected_value:
            raise ValueError(f"base OGE 6.7 evidence audit drift: {key}")
    if (base.get("safety") or {}).get("learner_audio_persistence") != 0:
        raise ValueError("base audit learner-audio persistence guard weakened")


def _validated_wave_item() -> tuple[dict[str, Any], dict[str, Any]]:
    validation = runpy.run_path(str(WAVE_VALIDATOR))["validate"]()
    if validation.get("status") != "COMPLETE":
        raise ValueError("OGE 6.7 wave 001 is not validated complete")
    if validation.get("owner") != TARGET_OWNER:
        raise ValueError("OGE 6.7 wave 001 owner drift")
    if validation.get("validated_reused_route_scoped_items") != 2:
        raise ValueError("OGE 6.7 wave 001 reused-item count drift")
    if validation.get("validated_new_route_scoped_items") != 1:
        raise ValueError("OGE 6.7 wave 001 new-item count drift")
    if validation.get("combined_exact_items_for_owner") != MINIMUM_EXACT_ITEMS_PER_OWNER:
        raise ValueError("OGE 6.7 wave 001 no longer completes the exact-item floor")
    if validation.get("object_closures") != 0 or validation.get("false_exact_mastery_admissions") != 0:
        raise ValueError("OGE 6.7 wave 001 weakened the no-admission boundary")
    if validation.get("learner_audio_persistence") != 0:
        raise ValueError("OGE 6.7 wave 001 learner-audio persistence guard weakened")

    pack = load(WAVE_PACK)
    rows = [row for row in pack.get("owner_evidence") or [] if isinstance(row, dict)]
    if len(rows) != 1 or rows[0].get("canonical_ref") != TARGET_OWNER:
        raise ValueError("OGE 6.7 wave 001 pack owner accounting drift")
    items = [item for item in rows[0].get("independent_verification") or [] if isinstance(item, dict)]
    if len(items) != 1:
        raise ValueError("OGE 6.7 wave 001 must contribute exactly one new item")
    item = items[0]
    if item.get("id") != TARGET_NEW_ITEM_ID:
        raise ValueError("OGE 6.7 wave 001 item identity drift")
    if item.get("evidence_mode") != "INDEPENDENT" or item.get("school_semantic_refs") != [TARGET_OWNER]:
        raise ValueError("OGE 6.7 wave 001 item lost exact single-owner independence")
    return validation, item


def _wave_item_for_audit(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_system": "current_launch_original_eksamio_component_evidence",
        "source_id": str(item["id"]),
        "review_status": "validated_current_launch_component_evidence_wave_001",
        "school_semantic_refs": [TARGET_OWNER],
        "evidence_provenance_refs": [
            "russian-program/production-learning-content/RU-PROG-08-OGE-6.7-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
            "russian-program/subject-admission/validate_oge_6_7_component_evidence_wave_001.py",
        ],
        "reuse_scope": "OGE_2026_6_7_ENDINGS_ONLY",
    }


def _recount(owner_reviews: list[dict[str, Any]]) -> dict[str, int | bool]:
    exact_ready = 0
    insufficient = 0
    mixed_only = 0
    no_evidence = 0
    for row in owner_reviews:
        exact_count = int(row.get("exact_component_independent_item_count") or 0)
        mixed_count = int(row.get("mixed_semantic_independent_item_count") or 0)
        if exact_count >= MINIMUM_EXACT_ITEMS_PER_OWNER:
            expected_status = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
            exact_ready += 1
        elif exact_count:
            expected_status = "INSUFFICIENT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE"
            insufficient += 1
        elif mixed_count:
            expected_status = "MIXED_SEMANTIC_LEARNER_EVIDENCE_ONLY_NOT_EXACT_ENOUGH"
            mixed_only += 1
        else:
            expected_status = "NO_INVENTORIED_INDEPENDENT_LEARNER_EVIDENCE"
            no_evidence += 1
        if row.get("evidence_status") != expected_status:
            raise ValueError(f"current OGE 6.7 owner evidence status drift: {row.get('canonical_ref')}")
    ready = exact_ready == len(owner_reviews) and insufficient == 0 and mixed_only == 0 and no_evidence == 0
    return {
        "owners_with_explicit_component_specific_independent_evidence": exact_ready,
        "owners_with_insufficient_exact_evidence": insufficient,
        "owners_with_mixed_semantic_evidence_only": mixed_only,
        "owners_with_no_inventoried_independent_evidence": no_evidence,
        "ready_for_separate_exact_object_acceptance": ready,
    }


def build_current_audit() -> dict[str, Any]:
    base = runpy.run_path(str(BASE_AUDITOR))["build_audit"]()
    _validate_base(base)
    wave_validation, wave_item = _validated_wave_item()

    result = copy.deepcopy(base)
    owner_reviews = [row for row in result.get("owner_reviews") or [] if isinstance(row, dict)]
    if len(owner_reviews) != 12:
        raise ValueError("current OGE 6.7 owner-review denominator drift")

    target_rows = [row for row in owner_reviews if row.get("canonical_ref") == TARGET_OWNER]
    if len(target_rows) != 1:
        raise ValueError("current OGE 6.7 target owner missing or duplicated")
    target = target_rows[0]
    if target.get("evidence_status") != "INSUFFICIENT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE":
        raise ValueError("target owner is no longer the expected bounded completion case")
    if target.get("exact_component_independent_item_count") != 2:
        raise ValueError("target owner base exact-item count drift")
    existing_ids = {
        str(item.get("source_id"))
        for item in target.get("exact_component_independent_items") or []
        if isinstance(item, dict)
    }
    if existing_ids != {"oge66-shib-v1", "oge66-shib-v2"}:
        raise ValueError("target owner base route-scoped reuse set drift")

    current_item = _wave_item_for_audit(wave_item)
    if current_item["source_id"] in existing_ids:
        raise ValueError("current OGE 6.7 wave item duplicates existing exact evidence")
    target.setdefault("exact_component_independent_items", []).append(current_item)
    target["exact_component_independent_items"].sort(key=lambda row: (row["source_system"], row["source_id"]))
    target["exact_component_independent_item_count"] = len(target["exact_component_independent_items"])
    if target["exact_component_independent_item_count"] != MINIMUM_EXACT_ITEMS_PER_OWNER:
        raise ValueError("target owner did not reach the exact evidence floor")
    target["evidence_status"] = "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"

    ready_rows = [
        row for row in owner_reviews
        if row.get("evidence_status") == "EXPLICIT_COMPONENT_SPECIFIC_INDEPENDENT_EVIDENCE_PRESENT"
    ]
    ready_refs = {str(row.get("canonical_ref")) for row in ready_rows}
    if EXPECTED_BASE_READY_OWNER not in ready_refs or TARGET_OWNER not in ready_refs:
        raise ValueError("expected exact-ready owners are not both present")

    counts = _recount(owner_reviews)
    if counts != {
        "owners_with_explicit_component_specific_independent_evidence": 2,
        "owners_with_insufficient_exact_evidence": 0,
        "owners_with_mixed_semantic_evidence_only": 0,
        "owners_with_no_inventoried_independent_evidence": 10,
        "ready_for_separate_exact_object_acceptance": False,
    }:
        raise ValueError("current OGE 6.7 evidence totals are not the exact post-wave-001 truth")

    result.pop("normalized_sha256", None)
    result["schema_version"] = "0.3.0"
    result["status"] = "CENTRAL_BRAIN_OGE_6_7_CURRENT_COMPONENT_EVIDENCE_GAPS_PROVEN_NO_OBJECT_ACCEPTANCE"
    result["scope"] = "OGE_2026_CONTENT_CODE_6_7_CURRENT_COMPONENT_EVIDENCE_AUDIT_AFTER_WAVE_001"
    result["base_audit"] = {
        "builder": "russian-program/subject-admission/build_oge_6_7_object_evidence_audit.py",
        "role": "reuse-first inventory plus explicitly whitelisted OGE 6.6 route-scoped evidence",
        "object_acceptance": False,
    }
    result["validated_current_evidence_waves"] = [
        {
            "id": "OGE_6_7_COMPONENT_EVIDENCE_WAVE_001",
            "pack": "russian-program/production-learning-content/RU-PROG-08-OGE-6.7-COMPONENT-EVIDENCE-WAVE-001-v0.1.json",
            "validator": "russian-program/subject-admission/validate_oge_6_7_component_evidence_wave_001.py",
            "owner": TARGET_OWNER,
            "new_independent_items": 1,
            "combined_exact_items_for_owner": int(wave_validation["combined_exact_items_for_owner"]),
            "object_closures": 0,
        }
    ]
    result["owner_reviews"] = owner_reviews
    result["summary"] = {
        "exact_owner_frontier": 12,
        "owners_with_explicit_component_specific_independent_evidence": counts[
            "owners_with_explicit_component_specific_independent_evidence"
        ],
        "owners_with_insufficient_exact_evidence": counts["owners_with_insufficient_exact_evidence"],
        "owners_with_mixed_semantic_evidence_only": counts["owners_with_mixed_semantic_evidence_only"],
        "owners_with_no_inventoried_independent_evidence": counts[
            "owners_with_no_inventoried_independent_evidence"
        ],
        "reused_route_scoped_independent_items": 5,
        "current_wave_independent_items": 1,
        "total_exact_independent_items_added_or_reused_by_bounded_oge_6_7_audits": 6,
        "ready_for_separate_exact_object_acceptance": False,
        "semantic_admissions": 0,
        "object_closures": 0,
        "false_exact_mastery_admissions": 0,
    }
    if result.get("target", {}).get("admission_unit_id") != "RAU-2668e140328e4edee952":
        raise ValueError("OGE 6.7 target admission-unit drift")
    if result.get("target", {}).get("requirement_id") != "RSK-OGE_COD-6-7-P025":
        raise ValueError("OGE 6.7 target requirement drift")
    safety = result.get("safety") or {}
    if safety != {
        "accepted_demo_or_scorer_change": False,
        "tilda_change": False,
        "learner_audio_persistence": 0,
        "production_peis_write": False,
        "provider_execution": False,
        "public_traffic": False,
        "real_payment_or_refund": False,
        "real_message_delivery": False,
    }:
        raise ValueError("current OGE 6.7 safety boundary drift")
    result["normalized_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_current_audit()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        summary = result["summary"]
        print("OGE_6_7_CURRENT_EVIDENCE_AUDIT=PASS")
        print(f"REQUIREMENT_ID={result['target']['requirement_id']}")
        print(f"ADMISSION_UNIT_ID={result['target']['admission_unit_id']}")
        print(f"EXACT_OWNER_FRONTIER={summary['exact_owner_frontier']}")
        print(
            "OWNERS_WITH_EXACT_COMPONENT_EVIDENCE="
            + str(summary["owners_with_explicit_component_specific_independent_evidence"])
        )
        print("OWNERS_WITH_INSUFFICIENT_EXACT=" + str(summary["owners_with_insufficient_exact_evidence"]))
        print("OWNERS_WITH_MIXED_ONLY=" + str(summary["owners_with_mixed_semantic_evidence_only"]))
        print(
            "OWNERS_WITH_NO_INDEPENDENT_EVIDENCE="
            + str(summary["owners_with_no_inventoried_independent_evidence"])
        )
        print("REUSED_ROUTE_SCOPED_ITEMS=" + str(summary["reused_route_scoped_independent_items"]))
        print("CURRENT_WAVE_ITEMS=" + str(summary["current_wave_independent_items"]))
        print("READY_FOR_EXACT_OBJECT_ACCEPTANCE=0")
        print("OBJECT_CLOSURES=0")
        print("FALSE_EXACT_MASTERY=0")
        print("LEARNER_AUDIO_PERSISTENCE=0")
        print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
