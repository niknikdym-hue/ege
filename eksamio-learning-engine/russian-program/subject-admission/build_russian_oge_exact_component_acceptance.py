#!/usr/bin/env python3
"""Build a fail-closed exact OGE canonical-component acceptance slice.

Only OGE codifier positions whose final 2026 route overlay enumerates a complete
owner list made exclusively of exact current reviewed canonical ``school-*``
identities are eligible. Family placeholders, descriptive groups, partial
overlap, broad all-applicable sets and module/keyword inference are rejected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from collections import defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
ACCOUNTING_BUILDER = HERE / "build_russian_subject_accounting_complete.py"
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
SCHOOL_FREEZE = ENGINE / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

# Exact complete owner lists from the final OGE-2026 orthography overlay.
# Positions containing any family/other/all-applicable placeholder are deliberately absent.
EXPECTED_EXACT: dict[str, tuple[str, ...]] = {
    "6.3": (
        "school-invariable-prefix-spelling-base",
        "school-prefix-z-s-selection",
        "school-pre-pri-semantic-base",
        "school-pre-pri-lexical-contrast-family",
    ),
    "6.4": (
        "school-separating-hard-soft-sign-boundary",
        "school-verb-soft-sign-forms",
        "school-numeral-orthography-base",
        "school-adverb-final-soft-sign-after-sibilant-base",
    ),
    "6.5": (
        "school-i-y-after-russian-prefix-base",
        "school-i-y-after-prefix-vzimat-exception",
        "school-i-y-after-prefix-retain-i-boundary",
    ),
    "6.10": (
        "school-denominal-adjective-n-nn-base",
        "school-participle-verbal-adjective-n-nn-base",
        "school-nn-derived-noun-adverb-inheritance",
    ),
    "6.13": (
        "school-compound-linking-vowel",
        "school-compound-first-part-without-linking-vowel-system",
        "school-compound-noun-solid-hyphen-system",
        "school-compound-adjective-solid-hyphen-separate-system",
        "school-abbreviations-capitalization-formation",
    ),
}
EXPECTED_CLASSIFICATION = {
    "6.3": "SCHOOL_IDENTITY_ROUTE",
    "6.4": "SCHOOL_IDENTITY_ROUTE",
    "6.5": "SCHOOL_IDENTITY_ROUTE",
    "6.10": "EXAM_ONLY_COMPOSITE",
    "6.13": "EXAM_ONLY_COMPOSITE",
}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_school_objects(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for obj in inventory.get("objects", []):
        if not isinstance(obj, dict) or obj.get("source_system") != "school_canonical":
            continue
        if obj.get("authority_status") != "current" or obj.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            continue
        if obj.get("review_status") != "reviewed":
            continue
        source_id = str(obj.get("source_id", ""))
        if not source_id or obj.get("current_semantic_refs") != [source_id]:
            raise ValueError(f"canonical school identity self-ref drift: {source_id}")
        rows[source_id] = obj
    return rows


def build_acceptance() -> dict[str, Any]:
    overlay = json.loads(OGE_OVERLAY.read_text(encoding="utf-8"))
    freeze = json.loads(SCHOOL_FREEZE.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    accounting = runpy.run_path(str(ACCOUNTING_BUILDER))["build_accounting"]()
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()

    if overlay.get("status") != "OGE_2026_FIPI_ROUTE_OVERLAY_COMPLETE / ZERO_SCHOOL_REOPEN_CANDIDATES":
        raise ValueError("final OGE overlay status drift")
    if int(overlay.get("school_baseline_for_overlay", 0)) != 185:
        raise ValueError("OGE overlay school denominator drift")
    if overlay.get("second_pass_result", {}).get("school_reopen_candidates") != 0:
        raise ValueError("OGE overlay has reopened school candidates")
    if freeze.get("final_school_canonical_denominator") != 185 or freeze.get("final_source_closure", {}).get("open_holds") != 0:
        raise ValueError("frozen 185 school denominator is not closed")
    if packet.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("semantic packet is not fail-closed")

    canonical = _canonical_school_objects(inventory)
    if len(canonical) != 185:
        raise ValueError(f"expected 185 current reviewed school identities, got {len(canonical)}")

    rows = overlay.get("orthography_codifier_overlay")
    if not isinstance(rows, list):
        raise ValueError("OGE orthography overlay missing")
    by_position = {str(row.get("position")): row for row in rows if isinstance(row, dict)}

    for position, expected_owners in EXPECTED_EXACT.items():
        row = by_position.get(position)
        if row is None:
            raise ValueError(f"expected OGE position missing: {position}")
        if row.get("classification") != EXPECTED_CLASSIFICATION[position]:
            raise ValueError(f"exact OGE position classification drift: {position}")
        owners = row.get("owners")
        if not isinstance(owners, list) or tuple(owners) != expected_owners:
            raise ValueError(f"exact OGE owner list drift: {position}")
        if any(not isinstance(owner, str) or owner not in canonical for owner in owners):
            raise ValueError(f"OGE exact owner list contains non-current/noncanonical ref: {position}")

    skipped = {"6.1", "6.2", "6.6", "6.7", "6.8", "6.9", "6.11", "6.12", "6.14"}
    if set(by_position) != set(EXPECTED_EXACT) | skipped:
        raise ValueError("OGE orthography position inventory drift")

    packet_requirements = {
        str(req["requirement_id"]): (group, req)
        for group in packet["semantic_review_groups"]
        for req in group["requirements"]
    }
    accounting_by_requirement: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in accounting["dispositions"]:
        for member in row.get("members", []):
            accounting_by_requirement[str(member["requirement_id"])].append(row)

    decisions: list[dict[str, Any]] = []
    for code, owner_tuple in sorted(EXPECTED_EXACT.items()):
        matches = [
            (rid, group, req)
            for rid, (group, req) in packet_requirements.items()
            if req.get("source_id") == "FIPI-OGE-RU-2026-FINAL"
            and req.get("document_id") == "OGE_COD"
            and str(req.get("code")) == code
        ]
        if len(matches) != 1:
            continue
        requirement_id, group, req = matches[0]
        units = accounting_by_requirement.get(requirement_id, [])
        if len(units) != 1 or len(units[0].get("members", [])) != 1:
            continue
        unit = units[0]
        if unit.get("disposition") != "PARTIAL_OR_COMPOSITE" or unit.get("semantic_identity_ref") is not None:
            raise ValueError(f"unexpected pre-acceptance state for {requirement_id}")
        components = list(owner_tuple)
        decisions.append(
            {
                "admission_unit_id": str(unit["admission_unit_id"]),
                "requirement_id": requirement_id,
                "source_id": str(req["source_id"]),
                "document_id": str(req["document_id"]),
                "source_locator": str(req["source_locator"]),
                "content_code": code,
                "overlay_classification": EXPECTED_CLASSIFICATION[code],
                "normalized_meaning": str(unit["normalized_meaning"]),
                "modules": list(unit.get("modules", [])),
                "routes": list(unit.get("routes", [])),
                "disposition": "PARTIAL_OR_COMPOSITE",
                "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
                "canonical_component_refs": components,
                "component_count": len(components),
                "authority": {
                    "final_oge_overlay": f"265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#orthography_codifier_overlay[position={code}]",
                    "school_denominator": "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json#final_school_canonical_denominator=185",
                    "packet_group": str(group["group_id"]),
                },
                "acceptance_reason": "The final OGE-2026 overlay provides a complete owner list made only of exact current reviewed canonical school identities from the frozen 185 denominator, with no family/other/all-applicable placeholder. SCHOOL_IDENTITY_ROUTE and EXAM_ONLY_COMPOSITE remain route classifications; neither turns the composite into atomic mastery.",
                "mastery_boundary": {
                    "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
                    "component_specific_independent_evidence_required": True,
                    "accepted_mapping_can_emit_partial_or_composite_evidence": True,
                },
            }
        )

    actual_codes = {row["content_code"] for row in decisions}
    if actual_codes != set(EXPECTED_EXACT):
        raise ValueError(f"exact safe OGE code acceptance set drift: {sorted(actual_codes)}")
    if len({row["admission_unit_id"] for row in decisions}) != len(decisions):
        raise ValueError("duplicate admission unit in OGE exact acceptance set")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_CANONICAL_COMPONENT_SLICE",
        "scope": "FIPI_OGE_2026_EXACT_ORTHOGRAPHY_CODES_WITH_COMPLETE_CANONICAL_OWNER_LISTS",
        "object_accounting_sha256": str(accounting["normalized_sha256"]),
        "semantic_packet_sha256": str(packet["normalized_sha256"]),
        "policy": {
            "final_oge_overlay_required": True,
            "all_owners_must_be_exact_current_reviewed_canonical_school_ids": True,
            "school_identity_route_allowed_with_complete_exact_owners": True,
            "exam_only_composite_allowed_with_complete_exact_owners": True,
            "family_placeholders_allowed": False,
            "all_applicable_placeholders_allowed": False,
            "keyword_or_fuzzy_mapping_allowed": False,
            "module_only_mapping_allowed": False,
            "generic_composite_attempt_can_exact_master_components": False,
        },
        "summary": {
            "accepted_admission_units": len(decisions),
            "accepted_requirements": len(decisions),
            "accepted_content_codes": len(decisions),
            "canonical_component_refs_unique": len({ref for row in decisions for ref in row["canonical_component_refs"]}),
            "new_semantic_identities_created": 0,
            "ru_proposal_identities_admitted": 0,
            "false_exact_mastery_admissions": 0,
        },
        "decisions": sorted(decisions, key=lambda row: row["content_code"]),
    }
    result["normalized_sha256"] = hashlib.sha256(canonical_json(result)).hexdigest()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    result = build_acceptance()
    if args.output:
        Path(args.output).write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if args.emit:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("RUSSIAN_OGE_EXACT_CANONICAL_COMPONENT_ACCEPTANCE=PASS")
        for key, value in result["summary"].items():
            print(f"{key}={value}")
        print("accepted_content_codes=" + ",".join(row["content_code"] for row in result["decisions"]))
        print(f"NORMALIZED_ACCEPTANCE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
