#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from build_oge_6_13_compound_words_source_bound_frontier_review import build_review as build_frontier_review

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
WAVE_B = ENGINE / "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json"
CAPITALIZATION_WAVE = ENGINE / "250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXACT_OWNERS = [
    "school-compound-linking-vowel",
    "school-compound-first-part-without-linking-vowel-system",
    "school-compound-noun-solid-hyphen-system",
    "school-compound-adjective-solid-hyphen-separate-system",
    "school-abbreviations-capitalization-formation",
]

WAVE_B_BINDINGS = {
    "school-compound-linking-vowel": ("O21_compound_linking_vowel", "Rosenthal §36"),
    "school-compound-first-part-without-linking-vowel-system": ("O22_compounds_without_linking_vowel", "Rosenthal §37"),
    "school-compound-noun-solid-hyphen-system": ("O23_compound_nouns", "Rosenthal §38"),
    "school-compound-adjective-solid-hyphen-separate-system": ("O24_compound_adjectives", "Rosenthal §39"),
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _single_new_unit(section: dict[str, Any], owner: str) -> dict[str, Any]:
    units = [row for row in section.get("new_units") or [] if isinstance(row, dict)]
    matches = [row for row in units if row.get("unit_id") == owner]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one Wave-B unit for {owner}, got {len(matches)}")
    return matches[0]


def build_resolution() -> dict[str, Any]:
    frontier = build_frontier_review()
    if frontier.get("status") != "SOURCE_BOUND_FRONTIER_ONLY_EXACT_OWNER_REVIEW_REQUIRED":
        raise ValueError("6.13 source-bound frontier is not in expected state")
    source = frontier.get("official_source") or {}
    if source.get("source_system") != "OGE_COD" or source.get("cycle") != 2026 or source.get("code") != "6.13":
        raise ValueError("6.13 official source identity drift")
    if source.get("label") != "Правописание сложных и сложносокращённых слов":
        raise ValueError("6.13 official wording drift")
    if source.get("explicit_subbranches") != [] or source.get("fabricated_subcodes") != 0:
        raise ValueError("6.13 must remain one broad FIPI object with zero manufactured subbranches")

    frontier_data = frontier.get("frontier") or {}
    candidates = [str(x) for x in frontier_data.get("candidate_refs") or []]
    if candidates != EXACT_OWNERS:
        raise ValueError("6.13 candidate frontier drift")
    if frontier_data.get("exact_owner_acceptance_count") != 0 or frontier_data.get("unresolved_candidate_count") != 5:
        raise ValueError("6.13 source frontier unexpectedly pre-admits owners")

    wave_b = load_json(WAVE_B)
    capitalization = load_json(CAPITALIZATION_WAVE)
    inventory = load_json(IDENTITY_INVENTORY)

    if wave_b.get("primary_source") != "rosenthal/rozental.doc":
        raise ValueError("Wave-B primary authority drift")
    if "Rosenthal orthography §§32–40" not in str(wave_b.get("primary_scope") or ""):
        raise ValueError("Wave-B source scope drift")
    if "Full Academic Guide" not in str(wave_b.get("current_norm_gate") or ""):
        raise ValueError("Wave-B current norm gate drift")

    cap_norm = capitalization.get("current_norm_authority") or {}
    if cap_norm.get("source") != "Правила русской орфографии и пунктуации. Полный академический справочник / под ред. В. В. Лопатина":
        raise ValueError("abbreviation current norm authority drift")
    if "аббревиатуры" not in str(cap_norm.get("section") or ""):
        raise ValueError("abbreviation current norm section drift")

    objects = [row for row in inventory.get("objects") or [] if isinstance(row, dict)]
    canonical_inventory = {
        str(row.get("source_id")): row
        for row in objects
        if row.get("source_system") == "school_canonical"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
    }

    exact_owner_proofs: list[dict[str, Any]] = []
    for owner in EXACT_OWNERS:
        inv = canonical_inventory.get(owner)
        if not isinstance(inv, dict):
            raise ValueError(f"6.13 owner missing canonical inventory authority: {owner}")
        if inv.get("authority_status") != "current" or inv.get("review_status") != "reviewed":
            raise ValueError(f"6.13 owner not current/reviewed: {owner}")
        if inv.get("current_semantic_refs") != [owner] or inv.get("candidate_canonical_owner") != owner:
            raise ValueError(f"6.13 owner self-identity drift: {owner}")

        provenance = [str(x) for x in inv.get("evidence_provenance_refs") or []]
        if owner in WAVE_B_BINDINGS:
            section_name, expected_source = WAVE_B_BINDINGS[owner]
            section = wave_b.get(section_name) or {}
            unit = _single_new_unit(section, owner)
            if unit.get("source") != expected_source:
                raise ValueError(f"6.13 primary source locator drift: {owner}")
            current_norm = str(unit.get("current_norm") or "")
            if "Lopatin" not in current_norm:
                raise ValueError(f"6.13 current norm gate missing for {owner}")
            if not any("252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25" in x for x in provenance):
                raise ValueError(f"6.13 Wave-B provenance missing for {owner}")
            proof = {
                "owner": owner,
                "canonical_label": str(unit.get("canonical_label") or ""),
                "primary_source_locator": expected_source,
                "current_norm_scope": current_norm,
                "ownership_boundary": unit.get("ownership_boundary"),
                "inventory_review_status": str(inv.get("review_status")),
                "inventory_provenance_refs": provenance,
                "disposition": "EXACT_REUSE_OWNER",
            }
        else:
            units = [
                row for row in capitalization.get("canonical_units") or []
                if isinstance(row, dict) and row.get("unit_id") == owner
            ]
            if len(units) != 1:
                raise ValueError("6.13 abbreviation canonical unit missing")
            unit = units[0]
            if unit.get("domain") != "orthography_abbreviations" or unit.get("unit_type") != "structured_abbreviation_system":
                raise ValueError("6.13 abbreviation unit boundary drift")
            if unit.get("source_locator") != "Розенталь §25":
                raise ValueError("6.13 abbreviation source locator drift")
            scope = str(unit.get("current_norm_scope") or "")
            if not all(fragment in scope for fragment in ("Letter abbreviations", "sound abbreviations", "suffixal derivatives")):
                raise ValueError("6.13 abbreviation current scope drift")
            if not any("250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION" in x for x in provenance):
                raise ValueError("6.13 abbreviation primary provenance missing")
            proof = {
                "owner": owner,
                "canonical_label": str(unit.get("canonical_label") or ""),
                "primary_source_locator": str(unit.get("source_locator")),
                "current_norm_scope": scope,
                "inventory_review_status": str(inv.get("review_status")),
                "inventory_provenance_refs": provenance,
                "disposition": "EXACT_REUSE_OWNER",
            }
        exact_owner_proofs.append(proof)

    route_key = "oge_2026_orthography_route::oge-2026-orthography-6-13"
    route_rows = [row for row in objects if row.get("object_key") == route_key]
    if len(route_rows) != 1:
        raise ValueError("6.13 current inventory route missing")
    current_route = route_rows[0]
    if current_route.get("authority_status") != "current":
        raise ValueError("6.13 route is not current")
    current_refs = [str(x) for x in current_route.get("current_semantic_refs") or []]
    if len(current_refs) != len(EXACT_OWNERS) or set(current_refs) != set(EXACT_OWNERS):
        raise ValueError(
            "6.13 current inventory route does not already equal the proved exact-owner set; "
            "do not silently supersede it inside owner resolution"
        )

    adjacent = [str(x) for x in frontier_data.get("explicit_adjacent_exclusions") or []]
    if set(adjacent) & set(EXACT_OWNERS):
        raise ValueError("6.13 adjacent exclusions overlap exact owner set")

    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_AUDIT_REQUIRED",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_13_COMPOUND_AND_ABBREVIATED_WORDS_EXACT_OWNER_RESOLUTION",
        "official_source_boundary": {
            "source_system": source["source_system"],
            "cycle": source["cycle"],
            "code": source["code"],
            "exact_fipi_wording": source["label"],
            "official_atomic_source_objects": 1,
            "official_explicit_subbranches": 0,
            "policy": (
                "FIPI 6.13 remains one broad source object. Exact ownership is proved from the existing canonical compound-word "
                "and abbreviation authorities; no FIPI subcodes are manufactured and no neighboring solid/hyphen/separate system "
                "is admitted by spelling-form similarity alone."
            ),
        },
        "exact_owner_resolution": {
            "frontier_candidates_reviewed": len(candidates),
            "exact_current_canonical_owners": EXACT_OWNERS,
            "exact_owner_count": len(EXACT_OWNERS),
            "exact_owner_proofs": exact_owner_proofs,
            "rejected_or_deferred_adjacent_refs": adjacent,
            "unresolved_owner_candidates": 0,
            "new_school_identities_required": 0,
            "current_inventory_route_refs": current_refs,
            "current_inventory_route_already_matches_exact_owner_set": True,
            "current_route_supersession_required": False,
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
            "Audit independent current reviewed/source-verified exact single-owner learner evidence for all five proved 6.13 owners. "
            "Because the current inventory route already equals the proved owner set, do not create a redundant route supersession. "
            "Only after the evidence gate is independently green may a separate exact object-acceptance authority be considered."
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

    print("OGE_6_13_COMPOUND_WORDS_EXACT_OWNER_RESOLUTION=PASS")
    print(f"FRONTIER_CANDIDATES_REVIEWED={r['frontier_candidates_reviewed']}")
    print(f"EXACT_CURRENT_CANONICAL_OWNERS={r['exact_owner_count']}")
    print(f"UNRESOLVED_OWNER_CANDIDATES={r['unresolved_owner_candidates']}")
    print(f"NEW_SCHOOL_IDENTITIES_REQUIRED={r['new_school_identities_required']}")
    print(f"CURRENT_ROUTE_ALREADY_EXACT={int(r['current_inventory_route_already_matches_exact_owner_set'])}")
    print(f"CURRENT_ROUTE_SUPERSESSION_REQUIRED={int(r['current_route_supersession_required'])}")
    print(f"EVIDENCE_GATE_REQUIRED={int(r['evidence_gate_required_before_object_acceptance'])}")
    print(f"SEMANTIC_ADMISSIONS={s['semantic_admissions']}")
    print(f"OBJECT_CLOSURES={s['object_closures']}")
    print(f"FALSE_EXACT_MASTERY={s['false_exact_mastery']}")
    print(f"LEARNER_AUDIO_PERSISTENCE={s['learner_audio_persistence']}")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
