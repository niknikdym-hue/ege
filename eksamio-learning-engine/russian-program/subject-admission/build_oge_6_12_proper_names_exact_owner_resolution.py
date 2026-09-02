#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from build_oge_6_12_proper_names_source_bound_frontier_review import build_review as build_frontier_review

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
CAPITALIZATION_WAVE = ENGINE / "250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXACT_OWNERS = [
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

REJECTED_FRONTIER_CANDIDATES = {
    "school-capitalization-conditional-special-proper-names": (
        "The canonical unit is a conditional/stylistic capitalization boundary and explicitly includes conventional official-document "
        "role names and expressive common-noun capitalization. As a whole identity it is broader than spelling of proper nouns, so it "
        "cannot be admitted to FIPI 6.12 by name similarity alone."
    ),
    "school-capitalization-positions-titles": (
        "The canonical unit decides uppercase/lowercase for positions, ranks and titles by status and context, including ordinary generic "
        "uses. As a whole identity it is not an exact proper-noun spelling owner and must not be admitted to FIPI 6.12 without a narrower "
        "independently proven component."
    ),
}

EXPECTED_EXACT_UNIT_TYPES = {
    "school-capitalization-astronomical-names": "astronomical_name_boundary",
    "school-capitalization-awards-orders-medals": "award_name_structure",
    "school-capitalization-documents-works-media-objects": "title_name_structure",
    "school-capitalization-geographic-administrative-names": "structured_geographic_name_family",
    "school-capitalization-historical-calendar-public-events": "event_period_name_structure",
    "school-capitalization-organizations-authorities-institutions": "institutional_name_structure",
    "school-capitalization-person-animal-name-and-derivatives": "structured_name_family",
    "school-capitalization-religious-names": "religious_name_system",
    "school-capitalization-trademarks-breeds-varieties-products": "brand_variety_name_system",
}

EXPECTED_REJECTED_UNIT_TYPES = {
    "school-capitalization-conditional-special-proper-names": "conditional_stylistic_boundary",
    "school-capitalization-positions-titles": "title_position_boundary",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def build_resolution() -> dict[str, Any]:
    frontier = build_frontier_review()
    if frontier.get("status") != "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION":
        raise ValueError("6.12 source-bound frontier is not in expected state")
    source = frontier.get("official_source") or {}
    if source.get("content_code") != "6.12":
        raise ValueError("6.12 official source code drift")
    if source.get("exact_fipi_wording") != "Правописание собственных имён существительных":
        raise ValueError("6.12 official wording drift")
    if source.get("explicit_source_object_count") != 1 or source.get("explicit_subbranches_in_fipi_row") != 0:
        raise ValueError("6.12 must remain one broad FIPI object with zero manufactured subbranches")

    frontier_data = frontier.get("reuse_first_frontier") or {}
    frontier_candidates = [str(x) for x in frontier_data.get("candidate_refs") or []]
    expected_partition = set(EXACT_OWNERS) | set(REJECTED_FRONTIER_CANDIDATES)
    if len(frontier_candidates) != 11 or set(frontier_candidates) != expected_partition:
        raise ValueError("6.12 candidate frontier no longer equals exact/rejected partition")
    if set(EXACT_OWNERS) & set(REJECTED_FRONTIER_CANDIDATES):
        raise ValueError("6.12 exact and rejected candidate sets overlap")
    if frontier_data.get("exact_route_ready_now") is not False:
        raise ValueError("6.12 source-bound frontier unexpectedly claims route readiness")

    wave = load_json(CAPITALIZATION_WAVE)
    inventory = load_json(IDENTITY_INVENTORY)

    norm_authority = wave.get("current_norm_authority") or {}
    if norm_authority.get("source") != "Правила русской орфографии и пунктуации. Полный академический справочник / под ред. В. В. Лопатина":
        raise ValueError("capitalization current-norm authority drift")
    norm_section = str(norm_authority.get("section") or "")
    if "Правила употребления прописных и строчных букв" not in norm_section:
        raise ValueError("capitalization current-norm section drift")

    canonical_units = {
        str(row.get("unit_id")): row
        for row in wave.get("canonical_units") or []
        if isinstance(row, dict) and row.get("unit_id")
    }
    if len(canonical_units) != 13:
        raise ValueError("capitalization canonical unit count drift")

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    canonical_inventory = {
        str(row.get("source_id")): row
        for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
    }

    exact_owner_proofs: list[dict[str, Any]] = []
    for owner in EXACT_OWNERS:
        unit = canonical_units.get(owner)
        inv = canonical_inventory.get(owner)
        if not isinstance(unit, dict) or not isinstance(inv, dict):
            raise ValueError(f"6.12 exact owner missing current canonical authority: {owner}")
        if unit.get("unit_type") != EXPECTED_EXACT_UNIT_TYPES[owner]:
            raise ValueError(f"6.12 exact owner unit-type drift: {owner}")
        domain = str(unit.get("domain") or "")
        if not domain.startswith("orthography_capitalization"):
            raise ValueError(f"6.12 exact owner escaped capitalization domain: {owner}")
        if inv.get("authority_status") != "current" or inv.get("review_status") != "reviewed":
            raise ValueError(f"6.12 exact owner not current/reviewed in inventory: {owner}")
        if inv.get("current_semantic_refs") != [owner] or inv.get("candidate_canonical_owner") != owner:
            raise ValueError(f"6.12 exact owner self-identity drift: {owner}")
        provenance = [str(x) for x in inv.get("evidence_provenance_refs") or []]
        if not any("250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION" in x for x in provenance):
            raise ValueError(f"6.12 exact owner lacks capitalization primary provenance: {owner}")
        exact_owner_proofs.append(
            {
                "owner": owner,
                "canonical_label": str(unit.get("canonical_label") or ""),
                "domain": domain,
                "unit_type": str(unit.get("unit_type") or ""),
                "source_locator": unit.get("source_locator") or unit.get("source_locators"),
                "current_norm_scope": str(unit.get("current_norm_scope") or ""),
                "inventory_review_status": str(inv.get("review_status")),
                "inventory_provenance_refs": provenance,
                "disposition": "EXACT_REUSE_OWNER",
            }
        )

    rejected_proofs: list[dict[str, Any]] = []
    for owner, reason in REJECTED_FRONTIER_CANDIDATES.items():
        unit = canonical_units.get(owner)
        inv = canonical_inventory.get(owner)
        if not isinstance(unit, dict) or not isinstance(inv, dict):
            raise ValueError(f"6.12 rejected candidate missing canonical authority: {owner}")
        if unit.get("unit_type") != EXPECTED_REJECTED_UNIT_TYPES[owner]:
            raise ValueError(f"6.12 rejected candidate unit-type drift: {owner}")
        if inv.get("authority_status") != "current" or inv.get("review_status") != "reviewed":
            raise ValueError(f"6.12 rejected candidate not current/reviewed: {owner}")

        scope = str(unit.get("current_norm_scope") or "")
        if owner == "school-capitalization-conditional-special-proper-names":
            required = ["official-document names", "special stylistic capitalization", "context/style controlled"]
            if not all(fragment in scope for fragment in required):
                raise ValueError("conditional/stylistic rejection proof drift")
        elif owner == "school-capitalization-positions-titles":
            required = ["official/high-title capitalization", "ordinary generic job/title usage"]
            if not all(fragment in scope for fragment in required):
                raise ValueError("positions/titles rejection proof drift")

        rejected_proofs.append(
            {
                "candidate": owner,
                "canonical_label": str(unit.get("canonical_label") or ""),
                "unit_type": str(unit.get("unit_type") or ""),
                "current_norm_scope": scope,
                "disposition": "REJECT_WHOLE_IDENTITY_AS_NOT_EXACT_6_12_OWNER",
                "reason": reason,
            }
        )

    route_key = "oge_2026_orthography_route::oge-2026-orthography-6-12"
    route_rows = [row for row in objects if row.get("object_key") == route_key]
    if len(route_rows) != 1:
        raise ValueError("6.12 current inventory route missing")
    current_route = route_rows[0]
    current_refs = [str(x) for x in current_route.get("current_semantic_refs") or []]
    if current_refs:
        raise ValueError("6.12 inventory route unexpectedly changed before supersession authority")

    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_ROUTE_SUPERSESSION_REQUIRED",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_12_PROPER_NAMES_EXACT_OWNER_RESOLUTION",
        "official_source_boundary": {
            "content_code": source["content_code"],
            "exact_fipi_wording": source["exact_fipi_wording"],
            "official_atomic_source_objects": 1,
            "official_explicit_subbranches": 0,
            "policy": (
                "FIPI 6.12 remains one broad object. Exact ownership is resolved against the current canonical capitalization authority "
                "without inventing FIPI subcodes or admitting an entire capitalization family by proximity."
            ),
        },
        "normative_authority": {
            "source": norm_authority.get("source"),
            "section": norm_authority.get("section"),
            "normalization_note": norm_authority.get("normalization_note"),
        },
        "exact_owner_resolution": {
            "frontier_candidates_reviewed": len(frontier_candidates),
            "exact_current_canonical_owners": EXACT_OWNERS,
            "exact_owner_count": len(EXACT_OWNERS),
            "exact_owner_proofs": exact_owner_proofs,
            "rejected_frontier_candidates": rejected_proofs,
            "rejected_frontier_candidate_count": len(rejected_proofs),
            "unresolved_owner_candidates": 0,
            "historical_placeholder": "capitalization mastery families from file 250",
            "historical_placeholder_disposition": "SUPERSEDED_BY_PROVED_EXACT_OWNER_SET_AFTER_ROUTE_AUTHORITY",
            "unresolved_placeholders": 0,
            "new_school_identities_required": 0,
            "current_inventory_route_refs": current_refs,
            "current_inventory_route_already_matches_exact_owner_set": False,
            "current_route_supersession_required": True,
            "current_route_supersession_authorized_after_this_gate_green": True,
            "evidence_gate_required_before_object_acceptance": True,
            "exact_owner_set_proven": True,
        },
        "safety": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "new_school_identities": 0,
            "false_exact_mastery": 0,
            "learner_audio_persistence": 0,
            "accepted_demo_or_scorer_change": False,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
        },
        "next": (
            "After this exact-owner gate is green, create a separate current-route supersession authority mapping FIPI 6.12 to exactly "
            "the nine proved current canonical owners. Do not admit the two rejected whole identities. Then audit independent exact "
            "single-owner learner evidence for all nine owners before any 6.12 object acceptance."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    resolution = build_resolution()
    emitted = json.dumps(resolution, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(emitted, encoding="utf-8")
    normalized = json.dumps(resolution, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(normalized).hexdigest()
    r = resolution["exact_owner_resolution"]
    s = resolution["safety"]

    print("OGE_6_12_PROPER_NAMES_EXACT_OWNER_RESOLUTION=PASS")
    print(f"FRONTIER_CANDIDATES_REVIEWED={r['frontier_candidates_reviewed']}")
    print(f"EXACT_CURRENT_CANONICAL_OWNERS={r['exact_owner_count']}")
    print(f"REJECTED_FRONTIER_CANDIDATES={r['rejected_frontier_candidate_count']}")
    print(f"UNRESOLVED_OWNER_CANDIDATES={r['unresolved_owner_candidates']}")
    print(f"UNRESOLVED_PLACEHOLDERS={r['unresolved_placeholders']}")
    print(f"NEW_SCHOOL_IDENTITIES_REQUIRED={r['new_school_identities_required']}")
    print(f"CURRENT_ROUTE_SUPERSESSION_REQUIRED={int(r['current_route_supersession_required'])}")
    print(f"CURRENT_INVENTORY_ROUTE_ALREADY_EXACT={int(r['current_inventory_route_already_matches_exact_owner_set'])}")
    print(f"EVIDENCE_GATE_REQUIRED={int(r['evidence_gate_required_before_object_acceptance'])}")
    print(f"SEMANTIC_ADMISSIONS={s['semantic_admissions']}")
    print(f"OBJECT_CLOSURES={s['object_closures']}")
    print(f"FALSE_EXACT_MASTERY={s['false_exact_mastery']}")
    print(f"LEARNER_AUDIO_PERSISTENCE={s['learner_audio_persistence']}")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
