#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
OWNER_REVIEW = HERE / "build_oge_6_13_compound_words_exact_owner_resolution.py"
PREEXISTING_AUDITOR = HERE / "build_oge_6_13_object_evidence_audit.py"
COMPONENT_VALIDATOR = HERE / "validate_oge_6_13_component_evidence.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"

EXPECTED_OWNERS = [
    "school-compound-linking-vowel",
    "school-compound-first-part-without-linking-vowel-system",
    "school-compound-noun-solid-hyphen-system",
    "school-compound-adjective-solid-hyphen-separate-system",
    "school-abbreviations-capitalization-formation",
]
TARGET_SOURCE = "FIPI-OGE-RU-2026-FINAL"
TARGET_DOCUMENT = "OGE_COD"
TARGET_CODE = "6.13"
ROUTE_OBJECT_KEY = "oge_2026_orthography_route::oge-2026-orthography-6-13"


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
                req.get("source_id") == TARGET_SOURCE
                and req.get("document_id") == TARGET_DOCUMENT
                and str(req.get("code")) == TARGET_CODE
            ):
                matches.append((group, req))
    if len(matches) != 1:
        raise ValueError(f"expected one exact OGE_COD 6.13 requirement, got {len(matches)}")
    group, requirement = matches[0]
    requirement_id = str(requirement.get("requirement_id") or "")
    rows = [
        row for row in accounting.get("dispositions") or []
        if isinstance(row, dict)
        and any(
            isinstance(member, dict) and str(member.get("requirement_id")) == requirement_id
            for member in row.get("members") or []
        )
    ]
    if len(rows) != 1:
        raise ValueError("OGE 6.13 requirement must map to exactly one accounting unit")
    row = rows[0]
    if len(row.get("members") or []) != 1:
        raise ValueError("OGE 6.13 accounting unit must remain single-member before component acceptance")
    if row.get("disposition") != "PARTIAL_OR_COMPOSITE":
        raise ValueError("OGE 6.13 pre-acceptance disposition drift")
    if row.get("semantic_identity_ref") is not None:
        raise ValueError("OGE 6.13 must not already carry a singular semantic identity")
    admission_unit_id = str(row.get("admission_unit_id") or "")
    if not requirement_id.startswith("RSK-") or not admission_unit_id.startswith("RAU-"):
        raise ValueError("OGE 6.13 target identities invalid")
    return {
        "source_id": TARGET_SOURCE,
        "document_id": TARGET_DOCUMENT,
        "content_code": TARGET_CODE,
        "requirement_id": requirement_id,
        "admission_unit_id": admission_unit_id,
        "source_locator": str(requirement.get("source_locator") or ""),
        "packet_group": str(group.get("group_id") or ""),
        "normalized_meaning": str(row.get("normalized_meaning") or ""),
        "modules": list(row.get("modules") or []),
        "routes": list(row.get("routes") or []),
        "current_disposition": str(row.get("disposition") or ""),
    }


def build_audit() -> dict[str, Any]:
    inventory = load(INVENTORY)
    resolution = runpy.run_path(str(OWNER_REVIEW))["build_resolution"]()
    preexisting = runpy.run_path(str(PREEXISTING_AUDITOR))["build_audit"]()
    component = runpy.run_path(str(COMPONENT_VALIDATOR))["validate"]()
    target = resolve_target()

    if resolution.get("status") != "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_AUDIT_REQUIRED":
        raise ValueError("6.13 exact-owner authority drift")
    ores = resolution.get("exact_owner_resolution") or {}
    if ores.get("exact_current_canonical_owners") != EXPECTED_OWNERS or ores.get("exact_owner_count") != 5:
        raise ValueError("6.13 exact owner set/count drift")
    if ores.get("unresolved_owner_candidates") != 0 or ores.get("new_school_identities_required") != 0:
        raise ValueError("6.13 owner frontier unresolved")
    if ores.get("current_inventory_route_already_matches_exact_owner_set") is not True:
        raise ValueError("6.13 route no longer equals exact owner set")
    if ores.get("current_route_supersession_required") is not False:
        raise ValueError("6.13 redundant route supersession unexpectedly required")
    if ores.get("evidence_gate_required_before_object_acceptance") is not True:
        raise ValueError("6.13 evidence gate weakened")

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    route_rows = [row for row in objects if row.get("object_key") == ROUTE_OBJECT_KEY]
    if len(route_rows) != 1:
        raise ValueError("6.13 current route row missing")
    route_refs = [str(x) for x in route_rows[0].get("current_semantic_refs") or []]
    if len(route_refs) != 5 or set(route_refs) != set(EXPECTED_OWNERS):
        raise ValueError("6.13 current route refs drift")

    ps = preexisting.get("summary") or {}
    if preexisting.get("status") != "CENTRAL_BRAIN_OGE_6_13_COMPONENT_EVIDENCE_GAPS_PROVEN_NO_OBJECT_ACCEPTANCE":
        raise ValueError("6.13 preexisting reuse audit truth changed")
    if preexisting.get("exact_owner_refs") != EXPECTED_OWNERS:
        raise ValueError("6.13 preexisting audit owner set drift")
    if ps.get("exact_owner_frontier") != 5:
        raise ValueError("6.13 preexisting audit denominator drift")
    if ps.get("owners_with_preexisting_exact_component_evidence") != 0:
        raise ValueError("6.13 preexisting exact evidence appeared; materialization needs re-review")
    if ps.get("preexisting_exact_independent_items") != 0 or ps.get("ready_without_materialization") is not False:
        raise ValueError("6.13 reuse-first materialization premise changed")
    if ps.get("semantic_admissions") != 0 or ps.get("object_closures") != 0 or ps.get("false_exact_mastery_admissions") != 0:
        raise ValueError("6.13 preexisting audit made forbidden admission")

    cs = component.get("summary") or {}
    if component.get("status") != "CENTRAL_BRAIN_OGE_6_13_COMPONENT_EVIDENCE_MATERIALIZED_NO_OBJECT_ADMISSION":
        raise ValueError("6.13 component evidence not in materialized no-admission state")
    if component.get("exact_owner_refs") != EXPECTED_OWNERS:
        raise ValueError("6.13 component validator owner set drift")
    if cs.get("exact_owner_frontier") != 5 or cs.get("owners_with_valid_component_evidence") != 5:
        raise ValueError("6.13 component evidence owner denominator incomplete")
    if cs.get("independent_items_total") != 15 or cs.get("minimum_items_per_owner") != 3:
        raise ValueError("6.13 component evidence denominator drift")
    if cs.get("selected_response_items") != 10 or cs.get("constructed_response_items") != 5:
        raise ValueError("6.13 response-mode arithmetic drift")
    if cs.get("existing_exact_inventory_items") != 0 or cs.get("materialized_new_items") != 15:
        raise ValueError("6.13 reuse/materialization arithmetic drift")
    if cs.get("semantic_admissions") != 0 or cs.get("object_closures") != 0:
        raise ValueError("6.13 component validator already claims forbidden admission")
    if cs.get("false_exact_mastery_admissions") != 0:
        raise ValueError("6.13 false-mastery boundary weakened")
    if component.get("per_owner_independent_items") != {owner: 3 for owner in EXPECTED_OWNERS}:
        raise ValueError("6.13 per-owner evidence denominator drift")

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
    if component.get("safety") != expected_safety or preexisting.get("safety") != expected_safety:
        raise ValueError("6.13 evidence safety drift")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "date": "2026-09-01",
        "status": "CENTRAL_BRAIN_OGE_6_13_COMPONENT_EVIDENCE_FRONTIER_COMPLETE_READY_FOR_SEPARATE_OBJECT_ACCEPTANCE",
        "scope": "OGE_2026_CONTENT_CODE_6_13_EXPLICIT_COMPONENT_EVIDENCE_AUDIT",
        "policy": {
            "reuse_first": True,
            "exact_source_content_identity_required": True,
            "keyword_or_fuzzy_inference_allowed": False,
            "module_or_packet_meaning_equivalence_allowed": False,
            "current_inventory_route_matches_exact_owner_set": True,
            "current_route_supersession_required": False,
            "component_specific_independent_evidence_required": True,
            "mixed_semantic_item_can_prove_exact_component_evidence": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "evidence_readiness_is_object_acceptance": False,
            "manufactured_fipi_subbranches_allowed": False,
        },
        "target": target,
        "exact_owner_refs": EXPECTED_OWNERS,
        "evidence_chain": {
            "preexisting_audit_normalized_sha256": preexisting["normalized_sha256"],
            "component_validator_normalized_sha256": component["normalized_sha256"],
        },
        "summary": {
            "official_fipi_source_objects": 1,
            "official_fipi_explicit_subbranches": 0,
            "exact_owner_frontier": 5,
            "owners_with_explicit_component_specific_independent_evidence": 5,
            "owners_with_insufficient_exact_evidence": 0,
            "owners_with_mixed_semantic_evidence_only": 0,
            "owners_with_no_independent_evidence": 0,
            "materialized_exact_independent_items": 15,
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
    print("OGE_6_13_CURRENT_OBJECT_EVIDENCE_AUDIT=PASS")
    print(f"REQUIREMENT_ID={result['target']['requirement_id']}")
    print(f"ADMISSION_UNIT_ID={result['target']['admission_unit_id']}")
    print(f"PACKET_GROUP={result['target']['packet_group']}")
    print(f"OFFICIAL_FIPI_SOURCE_OBJECTS={s['official_fipi_source_objects']}")
    print(f"OFFICIAL_FIPI_EXPLICIT_SUBBRANCHES={s['official_fipi_explicit_subbranches']}")
    print(f"EXACT_OWNER_FRONTIER={s['exact_owner_frontier']}")
    print(f"OWNERS_WITH_EXACT_COMPONENT_EVIDENCE={s['owners_with_explicit_component_specific_independent_evidence']}")
    print(f"MATERIALIZED_EXACT_ITEMS={s['materialized_exact_independent_items']}")
    print(f"PREEXISTING_AUDIT_NORMALIZED_SHA256={result['evidence_chain']['preexisting_audit_normalized_sha256']}")
    print(f"COMPONENT_VALIDATOR_NORMALIZED_SHA256={result['evidence_chain']['component_validator_normalized_sha256']}")
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
