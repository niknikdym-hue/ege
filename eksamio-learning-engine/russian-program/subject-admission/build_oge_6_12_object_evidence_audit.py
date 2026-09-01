#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_oge_6_12_component_evidence.py"
OWNER_REVIEW = HERE / "build_oge_6_12_proper_names_exact_owner_resolution.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"
ENGINE = HERE.parent.parent
ROUTE = ENGINE / "282-RUSSIAN-FIPI-2026-OGE-6.12-CURRENT-ROUTE-SUPERSESSION-v0.1.json"

EXPECTED_OWNERS = [
    "school-capitalization-astronomical-names",
    "school-capitalization-awards-orders-medals",
    "school-capitalization-documents-works-media-objects",
    "school-capitalization-geographic-administrative-names",
    "school-capitalization-historical-calendar-public-events",
    "school-capitalization-organizations-authorities-institutions",
    "school-capitalization-person-animal-name-and-derivatives",
    "school-capitalization-religious-names",
    "school-capitalization-trademarks-breeds-varieties-products",
]


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object: {path}")
    return data


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def resolve_target() -> dict[str, Any]:
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()

    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for group in packet.get("semantic_review_groups") or []:
        if not isinstance(group, dict):
            continue
        for req in group.get("requirements") or []:
            if not isinstance(req, dict):
                continue
            if (
                req.get("source_id") == "FIPI-OGE-RU-2026-FINAL"
                and req.get("document_id") == "OGE_COD"
                and str(req.get("code")) == "6.12"
            ):
                matches.append((group, req))
    if len(matches) != 1:
        raise ValueError(f"expected one exact OGE_COD 6.12 requirement, got {len(matches)}")
    group, requirement = matches[0]
    requirement_id = str(requirement.get("requirement_id") or "")
    if not requirement_id.startswith("RSK-"):
        raise ValueError("invalid resolved 6.12 requirement id")

    accounting_matches = [
        row
        for row in accounting.get("dispositions") or []
        if isinstance(row, dict)
        and any(
            isinstance(member, dict) and str(member.get("requirement_id")) == requirement_id
            for member in row.get("members") or []
        )
    ]
    if len(accounting_matches) != 1:
        raise ValueError("OGE 6.12 requirement must map to exactly one accounting unit")
    accounting_row = accounting_matches[0]
    if len(accounting_row.get("members") or []) != 1:
        raise ValueError("OGE 6.12 accounting unit must remain single-member before component acceptance")
    if accounting_row.get("disposition") != "PARTIAL_OR_COMPOSITE":
        raise ValueError("OGE 6.12 pre-acceptance disposition drift")
    if accounting_row.get("semantic_identity_ref") is not None:
        raise ValueError("OGE 6.12 must not already carry a singular semantic identity")
    admission_unit_id = str(accounting_row.get("admission_unit_id") or "")
    if not admission_unit_id.startswith("RAU-"):
        raise ValueError("invalid resolved 6.12 admission unit id")

    return {
        "source_id": "FIPI-OGE-RU-2026-FINAL",
        "document_id": "OGE_COD",
        "content_code": "6.12",
        "requirement_id": requirement_id,
        "admission_unit_id": admission_unit_id,
        "source_locator": str(requirement.get("source_locator") or ""),
        "packet_group": str(group.get("group_id") or ""),
        "normalized_meaning": str(accounting_row.get("normalized_meaning") or ""),
        "modules": list(accounting_row.get("modules") or []),
        "routes": list(accounting_row.get("routes") or []),
        "current_disposition": str(accounting_row.get("disposition") or ""),
    }


def build_audit() -> dict[str, Any]:
    validation = runpy.run_path(str(VALIDATOR))["validate"]()
    resolution = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()
    route = load(ROUTE)
    target = resolve_target()

    if validation.get("status") != "CENTRAL_BRAIN_OGE_6_12_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION":
        raise ValueError("6.12 component evidence is not in expected materialized no-admission state")
    if validation.get("exact_owner_refs") != EXPECTED_OWNERS:
        raise ValueError("6.12 component evidence owner set drift")
    summary = validation.get("summary") or {}
    if summary.get("exact_owner_frontier") != 9 or summary.get("owners_with_valid_component_evidence") != 9:
        raise ValueError("6.12 component evidence owner denominator incomplete")
    if summary.get("independent_items_total") != 27 or summary.get("minimum_items_per_owner") != 3:
        raise ValueError("6.12 independent evidence denominator drift")
    if summary.get("selected_response_items") != 18 or summary.get("constructed_response_items") != 9:
        raise ValueError("6.12 evidence response-mode arithmetic drift")
    if summary.get("existing_exact_inventory_items") != 0 or summary.get("materialized_new_items") != 27:
        raise ValueError("6.12 reuse/materialization arithmetic drift")
    if summary.get("semantic_admissions") != 0 or summary.get("object_closures") != 0:
        raise ValueError("6.12 evidence validator already claims forbidden admission")
    if summary.get("false_exact_mastery_admissions") != 0:
        raise ValueError("6.12 false-mastery boundary weakened")

    if resolution.get("status") != "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_ROUTE_SUPERSESSION_REQUIRED":
        raise ValueError("6.12 exact owner authority drift")
    owners = resolution.get("exact_owner_resolution") or {}
    if owners.get("exact_current_canonical_owners") != EXPECTED_OWNERS or owners.get("exact_owner_count") != 9:
        raise ValueError("6.12 exact owner authority set/count drift")
    if owners.get("unresolved_owner_candidates") != 0 or owners.get("unresolved_placeholders") != 0:
        raise ValueError("6.12 exact owner authority is unresolved")
    if owners.get("new_school_identities_required") != 0:
        raise ValueError("6.12 evidence cannot create new canonical identity")

    if route.get("status") != "CURRENT_OGE_2026_6_12_ROUTE_SUPERSESSION_EXACT_OWNER_FRONTIER_NO_OBJECT_ADMISSION":
        raise ValueError("6.12 route supersession authority drift")
    if route.get("exact_owner_refs") != EXPECTED_OWNERS:
        raise ValueError("6.12 current route no longer equals exact owner set")
    route_account = route.get("owner_accounting") or {}
    if route_account.get("official_fipi_objects") != 1 or route_account.get("official_explicit_subbranches") != 0:
        raise ValueError("6.12 official FIPI object boundary drift")
    if route_account.get("owner_count") != 9 or route_account.get("unresolved_owners") != 0:
        raise ValueError("6.12 current route owner accounting drift")
    if route_account.get("newly_materialized_current_canonical") != 0:
        raise ValueError("6.12 route materialized forbidden new identities")
    mastery = route.get("mastery_boundary") or {}
    if mastery.get("route_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("6.12 generic route exact mastery boundary weakened")
    if mastery.get("component_specific_independent_evidence_required") is not True:
        raise ValueError("6.12 component evidence requirement weakened")

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
        raise ValueError("6.12 evidence safety drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "date": "2026-09-01",
        "status": "CENTRAL_BRAIN_OGE_6_12_COMPONENT_EVIDENCE_FRONTIER_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE",
        "scope": "OGE_2026_CONTENT_CODE_6_12_EXPLICIT_COMPONENT_EVIDENCE_AUDIT",
        "policy": {
            "reuse_first": True,
            "exact_source_content_identity_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_or_packet_meaning_equivalence_allowed": False,
            "current_route_matches_superseded_exact_owner_set": True,
            "component_specific_independent_evidence_required": True,
            "mixed_semantic_item_can_prove_exact_component_evidence": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "evidence_readiness_is_object_acceptance": False,
            "manufactured_fipi_subbranches_allowed": False
        },
        "target": target,
        "exact_owner_refs": EXPECTED_OWNERS,
        "summary": {
            "official_fipi_source_objects": 1,
            "official_fipi_explicit_subbranches": 0,
            "exact_owner_frontier": 9,
            "owners_with_explicit_component_specific_independent_evidence": 9,
            "owners_with_insufficient_exact_evidence": 0,
            "owners_with_mixed_semantic_evidence_only": 0,
            "owners_with_no_independent_evidence": 0,
            "materialized_exact_independent_items": 27,
            "reused_preexisting_exact_inventory_items": 0,
            "ready_for_separate_exact_object_acceptance": true,
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0
        },
        "safety": expected_safety
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
    print("OGE_6_12_OBJECT_EVIDENCE_AUDIT=PASS")
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
