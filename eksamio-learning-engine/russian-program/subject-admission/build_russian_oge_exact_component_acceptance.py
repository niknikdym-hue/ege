#!/usr/bin/env python3
"""Build a fail-closed exact OGE canonical-component acceptance slice.

Only OGE codifier positions whose final 2026 route overlay enumerates a complete
owner list made exclusively of exact current canonical ``school-*`` identities
are eligible. Family placeholders, descriptive groups, partial overlap, broad
all-applicable sets and module/keyword inference are rejected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import runpy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
PACKET_BUILDER = HERE / "build_russian_semantic_acceptance_packet.py"
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
SCHOOL_FREEZE = ENGINE / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"

# Reviewed exact owner lists from the final OGE-2026 orthography overlay.
# Positions containing any family/other/all-applicable placeholder are deliberately absent.
EXPECTED_EXACT: dict[str, tuple[str, ...]] = {
    "6.3": (
        "school-invariable-prefix-spelling-base",
        "school-prefix-z-s-selection",
        "school-pre-pri-semantic-base",
        "school-pre-pri-lexical-contrast-family",
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


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _canonical_school_ids(freeze: dict[str, Any]) -> set[str]:
    for key in ("final_school_canonical_ids", "final_school_canonical_denominator_ids", "canonical_school_ids"):
        value = freeze.get(key)
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return set(value)
    raise ValueError("frozen school authority does not expose canonical school id list")


def build_acceptance() -> dict[str, Any]:
    packet = runpy.run_path(str(PACKET_BUILDER))["build_packet"]()
    overlay = json.loads(OGE_OVERLAY.read_text(encoding="utf-8"))
    freeze = json.loads(SCHOOL_FREEZE.read_text(encoding="utf-8"))

    if overlay.get("status") != "OGE_2026_FIPI_ROUTE_OVERLAY_COMPLETE / ZERO_SCHOOL_REOPEN_CANDIDATES":
        raise ValueError("final OGE overlay status drift")
    if int(overlay.get("school_baseline_for_overlay", 0)) != 185:
        raise ValueError("OGE overlay school denominator drift")
    if overlay.get("second_pass_result", {}).get("school_reopen_candidates") != 0:
        raise ValueError("OGE overlay has reopened school candidates")
    if packet.get("status") != "CENTRAL_BRAIN_SUBJECT_ACCEPTANCE_REQUIRED":
        raise ValueError("semantic packet is not fail-closed")

    canonical_ids = _canonical_school_ids(freeze)
    if len(canonical_ids) != 185:
        raise ValueError(f"frozen school denominator drift: {len(canonical_ids)}")

    rows = overlay.get("orthography_codifier_overlay")
    if not isinstance(rows, list):
        raise ValueError("OGE orthography overlay missing")
    by_position = {str(row.get("position")): row for row in rows if isinstance(row, dict)}

    for position, expected_owners in EXPECTED_EXACT.items():
        row = by_position.get(position)
        if row is None:
            raise ValueError(f"expected OGE position missing: {position}")
        if row.get("classification") != "SCHOOL_IDENTITY_ROUTE":
            raise ValueError(f"exact OGE position classification drift: {position}")
        owners = row.get("owners")
        if not isinstance(owners, list) or tuple(owners) != expected_owners:
            raise ValueError(f"exact OGE owner list drift: {position}")
        if any(not owner.startswith("school-") for owner in owners):
            raise ValueError(f"non-canonical placeholder in exact OGE owner list: {position}")
        unknown = set(owners) - canonical_ids
        if unknown:
            raise ValueError(f"OGE exact owner outside frozen 185 denominator: {position}: {sorted(unknown)}")

    # Guard the deliberately skipped positions: none may be accidentally admitted by this slice.
    skipped = {"6.1", "6.2", "6.4", "6.6", "6.7", "6.8", "6.9", "6.11", "6.12", "6.14"}
    if set(by_position) != set(EXPECTED_EXACT) | skipped:
        raise ValueError("OGE orthography position inventory drift")

    decisions: list[dict[str, Any]] = []
    seen_units: set[str] = set()
    seen_requirements: set[str] = set()
    for group in packet.get("semantic_review_groups", []):
        if not isinstance(group, dict):
            continue
        group_id = str(group.get("group_id", ""))
        unit_ids = [str(value) for value in group.get("admission_unit_ids", [])]
        for requirement in group.get("requirements", []):
            if not isinstance(requirement, dict):
                continue
            if requirement.get("document_id") != "OGE_COD":
                continue
            code = str(requirement.get("code", ""))
            if code not in EXPECTED_EXACT:
                continue
            requirement_id = str(requirement.get("requirement_id", ""))
            # Packet groups can contain multiple source-specific units. Select the unique unit
            # whose source/document/code membership is proved by the complete object accounting.
            matching_units = []
            accounting_rows = packet.get("object_accounting", {}).get("rows")
            if isinstance(accounting_rows, list):
                for row in accounting_rows:
                    if not isinstance(row, dict):
                        continue
                    if requirement_id in set(str(v) for v in row.get("requirement_ids", [])):
                        matching_units.append(str(row.get("admission_unit_id")))
            if not matching_units:
                # Current packet intentionally stores accounting summary, not rows; membership
                # is still exact when this packet group contains one admission unit for the exact
                # requirement. Refuse ambiguous groups.
                if len(unit_ids) != 1:
                    raise ValueError(f"cannot prove unique OGE admission unit for {requirement_id}")
                matching_units = unit_ids
            matching_units = list(dict.fromkeys(matching_units))
            if len(matching_units) != 1 or matching_units[0] not in unit_ids:
                raise ValueError(f"ambiguous OGE admission unit for {requirement_id}: {matching_units}")
            unit_id = matching_units[0]
            if unit_id in seen_units or requirement_id in seen_requirements:
                raise ValueError("duplicate exact OGE decision")
            owners = list(EXPECTED_EXACT[code])
            decisions.append(
                {
                    "admission_unit_id": unit_id,
                    "requirement_id": requirement_id,
                    "source_id": str(requirement.get("source_id")),
                    "document_id": "OGE_COD",
                    "source_locator": str(requirement.get("source_locator")),
                    "content_code": code,
                    "normalized_meaning": str(group.get("normalized_meaning")),
                    "modules": list(group.get("modules", [])),
                    "routes": list(group.get("routes", [])),
                    "disposition": "PARTIAL_OR_COMPOSITE",
                    "canonical_component_refs": owners,
                    "component_count": len(owners),
                    "subject_semantic_status": "CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET",
                    "acceptance_reason": "The final OGE-2026 overlay classifies this exact codifier position as SCHOOL_IDENTITY_ROUTE and enumerates only exact current canonical school owners from the frozen 185 denominator, with no family/other/all-applicable placeholder.",
                    "mastery_boundary": {
                        "accepted_mapping_can_emit_partial_or_composite_evidence": True,
                        "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
                        "component_specific_independent_evidence_required": True,
                    },
                    "authority": {
                        "final_oge_overlay": f"265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json#orthography_codifier_overlay[position={code}]",
                        "packet_group": group_id,
                        "school_denominator": "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json#final_school_canonical_denominator=185",
                    },
                }
            )
            seen_units.add(unit_id)
            seen_requirements.add(requirement_id)

    found_codes = {str(row["content_code"]) for row in decisions}
    if found_codes != set(EXPECTED_EXACT):
        raise ValueError(f"exact OGE accepted-code coverage drift: {sorted(found_codes)}")
    if len(decisions) != 4:
        raise ValueError(f"expected exactly four exact OGE decisions, got {len(decisions)}")

    result: dict[str, Any] = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_ACCEPTED_EXACT_OGE_CANONICAL_COMPONENT_SLICE",
        "scope": "FIPI_OGE_2026_EXACT_ORTHOGRAPHY_CODES_WITH_COMPLETE_CANONICAL_OWNER_LISTS",
        "semantic_packet_sha256": str(packet["normalized_sha256"]),
        "object_accounting_sha256": str(packet["object_accounting"]["normalized_sha256"]),
        "policy": {
            "final_oge_overlay_required": True,
            "all_owners_must_be_exact_current_reviewed_canonical_school_ids": True,
            "family_placeholders_allowed": False,
            "all_applicable_placeholders_allowed": False,
            "keyword_or_fuzzy_mapping_allowed": False,
            "module_only_mapping_allowed": False,
            "generic_composite_attempt_can_exact_master_components": False,
        },
        "summary": {
            "accepted_content_codes": len(decisions),
            "accepted_admission_units": len(decisions),
            "accepted_requirements": len(decisions),
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
        print(f"NORMALIZED_ACCEPTANCE_SHA256={result['normalized_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
