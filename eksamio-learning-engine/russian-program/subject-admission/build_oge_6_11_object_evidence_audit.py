#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_oge_6_11_component_evidence.py"
OWNER_REVIEW = HERE / "build_oge_6_11_service_words_exact_owner_resolution.py"

EXPECTED_OWNERS = [
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-preposition-solid-hyphen-separate-base",
]


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_audit() -> dict[str, Any]:
    validation = runpy.run_path(str(VALIDATOR))["validate"]()
    resolution = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()

    if validation.get("status") != "CENTRAL_BRAIN_OGE_6_11_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION":
        raise ValueError("6.11 component evidence is not in expected materialized no-admission state")
    if validation.get("exact_owner_refs") != EXPECTED_OWNERS:
        raise ValueError("6.11 component evidence owner set drift")
    summary = validation.get("summary") or {}
    if summary.get("exact_owner_frontier") != 3:
        raise ValueError("6.11 evidence owner denominator drift")
    if summary.get("owners_with_valid_component_evidence") != 3:
        raise ValueError("6.11 component evidence incomplete")
    if summary.get("independent_items_total") != 9 or summary.get("minimum_items_per_owner") != 3:
        raise ValueError("6.11 independent evidence denominator drift")
    if summary.get("selected_response_items") != 6 or summary.get("constructed_response_items") != 3:
        raise ValueError("6.11 evidence response-mode arithmetic drift")
    if summary.get("semantic_admissions") != 0 or summary.get("object_closures") != 0:
        raise ValueError("6.11 evidence validator already claims forbidden admission")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("6.11 evidence validator weakened false-mastery boundary")

    reuse = validation.get("reuse_first_inventory_audit") or {}
    if reuse.get("existing_exact_current_trainer_or_practice_items") != 0:
        raise ValueError("6.11 materialization ignored reusable exact inventory evidence")
    if reuse.get("mixed_or_route_scoped_items_counted") != 0:
        raise ValueError("6.11 mixed/route evidence counted as exact component evidence")

    if resolution.get("status") != "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_REQUIRED":
        raise ValueError("6.11 exact owner authority drift")
    owners = resolution.get("exact_owner_resolution") or {}
    if owners.get("exact_current_canonical_owners") != EXPECTED_OWNERS:
        raise ValueError("6.11 exact owner authority set drift")
    if owners.get("exact_owner_count") != 3:
        raise ValueError("6.11 exact owner authority count drift")
    if owners.get("unresolved_owner_candidates") != 0 or owners.get("unresolved_placeholders") != 0:
        raise ValueError("6.11 exact owner authority is unresolved")
    if owners.get("new_school_identities_required") != 0:
        raise ValueError("6.11 evidence cannot create new canonical identity")
    if owners.get("current_route_supersession_required") is not False:
        raise ValueError("6.11 route unexpectedly requires supersession")
    if owners.get("current_inventory_route_already_matches_exact_owner_set") is not True:
        raise ValueError("6.11 current route no longer equals exact owner set")
    if owners.get("evidence_gate_required_before_object_acceptance") is not True:
        raise ValueError("6.11 evidence gate requirement weakened")

    target = validation.get("target") or {}
    if target.get("source_id") != "FIPI-OGE-RU-2026-FINAL" or target.get("document_id") != "OGE_COD" or target.get("content_code") != "6.11":
        raise ValueError("6.11 exact source target drift")
    if not str(target.get("requirement_id") or "").startswith("RSK-"):
        raise ValueError("6.11 resolved requirement id missing")
    if not str(target.get("admission_unit_id") or "").startswith("RAU-"):
        raise ValueError("6.11 resolved admission unit id missing")
    if target.get("current_disposition") != "PARTIAL_OR_COMPOSITE":
        raise ValueError("6.11 pre-acceptance disposition drift")

    source_boundary = resolution.get("official_source_boundary") or {}
    if source_boundary.get("content_code") != "6.11":
        raise ValueError("6.11 source boundary code drift")
    if source_boundary.get("official_atomic_source_objects") != 1:
        raise ValueError("6.11 official source object denominator drift")
    if source_boundary.get("official_explicit_subbranches") != 0:
        raise ValueError("6.11 audit must not manufacture FIPI subbranches")

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
    if validation.get("safety") != expected_safety:
        raise ValueError("6.11 evidence safety drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "date": "2026-09-01",
        "status": "CENTRAL_BRAIN_OGE_6_11_COMPONENT_EVIDENCE_FRONTIER_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE",
        "scope": "OGE_2026_CONTENT_CODE_6_11_EXPLICIT_COMPONENT_EVIDENCE_AUDIT",
        "policy": {
            "reuse_first": True,
            "exact_source_content_identity_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_or_packet_meaning_equivalence_allowed": False,
            "current_route_already_matches_exact_owner_set": True,
            "current_route_supersession_required": False,
            "component_specific_independent_evidence_required": True,
            "mixed_semantic_item_can_prove_exact_component_evidence": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "evidence_readiness_is_object_acceptance": False,
        },
        "target": target,
        "exact_owner_refs": EXPECTED_OWNERS,
        "summary": {
            "official_fipi_source_objects": 1,
            "official_fipi_explicit_subbranches": 0,
            "exact_owner_frontier": 3,
            "owners_with_explicit_component_specific_independent_evidence": 3,
            "owners_with_insufficient_exact_evidence": 0,
            "owners_with_mixed_semantic_evidence_only": 0,
            "owners_with_no_independent_evidence": 0,
            "materialized_exact_independent_items": 9,
            "reused_preexisting_exact_inventory_items": 0,
            "ready_for_separate_exact_object_acceptance": True,
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0,
        },
        "safety": expected_safety,
    }
    result["normalized_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_audit()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    s = result["summary"]
    print("OGE_6_11_OBJECT_EVIDENCE_AUDIT=PASS")
    print(f"REQUIREMENT_ID={result['target']['requirement_id']}")
    print(f"ADMISSION_UNIT_ID={result['target']['admission_unit_id']}")
    print(f"OFFICIAL_FIPI_SOURCE_OBJECTS={s['official_fipi_source_objects']}")
    print(f"OFFICIAL_FIPI_EXPLICIT_SUBBRANCHES={s['official_fipi_explicit_subbranches']}")
    print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
    print(f"OWNERS_WITH_EXACT_COMPONENT_EVIDENCE={s['owners_with_explicit_component_specific_independent_evidence']}")
    print(f"MATERIALIZED_EXACT_ITEMS={s['materialized_exact_independent_items']}")
    print("REUSED_PREEXISTING_EXACT_ITEMS=0")
    print("READY_FOR_EXACT_OBJECT_ACCEPTANCE=1")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")
    print(f"NORMALIZED_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
