#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from build_oge_6_11_service_words_source_bound_frontier_review import build_review as build_frontier_review

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
PRIMARY_WAVE_D = ENGINE / "255-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-D-O36-O45-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

EXACT_OWNERS = [
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-preposition-solid-hyphen-separate-base",
]
PLACEHOLDER = "service-word homonym/function branches"

EXPECTED_PRIMARY = {
    "school-preposition-solid-hyphen-separate-base": {
        "section": "O36_prepositions",
        "source": "Rosenthal Section 15",
        "required_branch_fragments": [
            "hyphenated complex prepositions",
            "solid derived prepositions",
            "separate multiword prepositions",
            "functional distinction of derived preposition",
        ],
    },
    "school-conjunction-solid-separate-spelling-base": {
        "section": "O37_conjunctions",
        "source": "Rosenthal Section 16",
        "required_branch_fragments": [
            "чтобы / что бы",
            "тоже / то же",
            "также / так же",
            "зато / за то",
            "compound conjunctions",
        ],
    },
    "school-nonnegative-particle-separate-hyphen-spelling-base": {
        "section": "O38_nonnegative_particles",
        "source": "Rosenthal §55",
        "required_branch_fragments": [
            "бы/б, же/ж, ли/ль",
            "-де, -ка, -те, -то, -с",
            "-таки",
            "кое-/кой-, -то, -либо, -нибудь",
        ],
    },
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def require_branch_fragments(branches: list[str], fragments: list[str], owner: str) -> None:
    joined = "\n".join(branches)
    for fragment in fragments:
        if fragment not in joined:
            raise ValueError(f"missing primary branch proof for {owner}: {fragment}")


def build_resolution() -> dict[str, Any]:
    frontier = build_frontier_review()
    if frontier["status"] != "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION":
        raise ValueError("6.11 source-bound frontier is not in expected state")
    source = frontier["official_source"]
    if source["content_code"] != "6.11" or source["explicit_source_object_count"] != 1:
        raise ValueError("6.11 official source-object boundary drift")
    if source["explicit_subbranches_in_fipi_row"] != 0:
        raise ValueError("6.11 must not manufacture FIPI subbranches")
    if frontier["identity_inventory_truth"]["current_semantic_refs"] != EXACT_OWNERS:
        raise ValueError("6.11 current route candidates drift")
    if frontier["historical_overlay_truth"]["legacy_placeholders"] != [PLACEHOLDER]:
        raise ValueError("6.11 historical placeholder drift")

    wave = load_json(PRIMARY_WAVE_D)
    inventory = load_json(IDENTITY_INVENTORY)
    normalization = str(wave.get("normalization_rule") or "")
    required_normalization_fragments = [
        "Service-word and НЕ spelling is normalized by current learner decision engines",
        "Function/homonym examples become branches of the productive owner",
        "unless they retain an independent semantic decision not covered by that owner",
    ]
    for fragment in required_normalization_fragments:
        if fragment not in normalization:
            raise ValueError(f"service-word normalization authority drift: {fragment}")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    canonical_rows = {
        str(item.get("source_id")): item
        for item in objects
        if item.get("source_system") == "school_canonical"
        and item.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
    }

    owner_proofs: list[dict[str, Any]] = []
    for owner in EXACT_OWNERS:
        cfg = EXPECTED_PRIMARY[owner]
        section = wave.get(cfg["section"])
        if not isinstance(section, dict):
            raise ValueError(f"missing primary wave section: {cfg['section']}")
        new_unit = section.get("new_unit")
        if not isinstance(new_unit, dict) or new_unit.get("unit_id") != owner:
            raise ValueError(f"primary owner identity drift: {owner}")
        if new_unit.get("source") != cfg["source"]:
            raise ValueError(f"primary owner source drift: {owner}")
        branches = [str(v) for v in new_unit.get("branches") or []]
        require_branch_fragments(branches, cfg["required_branch_fragments"], owner)

        inv = canonical_rows.get(owner)
        if not isinstance(inv, dict):
            raise ValueError(f"canonical inventory owner missing: {owner}")
        if inv.get("authority_status") != "current" or inv.get("review_status") != "reviewed":
            raise ValueError(f"canonical owner is not current/reviewed: {owner}")
        if inv.get("current_semantic_refs") != [owner] or inv.get("candidate_canonical_owner") != owner:
            raise ValueError(f"canonical owner self-identity drift: {owner}")

        owner_proofs.append(
            {
                "owner": owner,
                "primary_section": cfg["section"],
                "primary_source": cfg["source"],
                "current_norm": str(new_unit.get("current_norm")),
                "canonical_label": str(new_unit.get("canonical_label")),
                "branch_count": len(branches),
                "inventory_review_status": str(inv.get("review_status")),
                "inventory_provenance_refs": [str(x) for x in inv.get("evidence_provenance_refs") or []],
            }
        )

    preposition = wave["O36_prepositions"]["new_unit"]
    conjunction = wave["O37_conjunctions"]["new_unit"]
    particle = wave["O38_nonnegative_particles"]["new_unit"]

    preposition_branches = "\n".join(str(x) for x in preposition.get("branches") or [])
    conjunction_label = str(conjunction.get("canonical_label") or "")
    conjunction_branches = "\n".join(str(x) for x in conjunction.get("branches") or [])
    particle_label = str(particle.get("canonical_label") or "")

    if "functional distinction" not in preposition_branches:
        raise ValueError("preposition owner does not prove function/free-combination boundary")
    if "омонимическая граница" not in conjunction_label:
        raise ValueError("conjunction owner does not prove homonym boundary")
    if not any(token in conjunction_branches for token in ("что бы", "то же", "так же", "за то")):
        raise ValueError("conjunction owner does not materialize homonym contrasts")
    if "Неотрицательные частицы" not in particle_label:
        raise ValueError("particle owner must remain explicitly nonnegative to avoid false overlap with OGE 6.9")

    route_key = "oge_2026_orthography_route::oge-2026-orthography-6-11"
    route_rows = [item for item in objects if item.get("object_key") == route_key]
    if len(route_rows) != 1:
        raise ValueError("6.11 current route row missing")
    current_route = route_rows[0]
    if current_route.get("current_semantic_refs") != EXACT_OWNERS:
        raise ValueError("6.11 inventory route is not already the exact proved owner set")

    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_EVIDENCE_REQUIRED",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_11_SERVICE_WORDS_EXACT_OWNER_RESOLUTION",
        "official_source_boundary": {
            "content_code": source["content_code"],
            "exact_fipi_wording": source["exact_fipi_wording"],
            "official_atomic_source_objects": 1,
            "official_explicit_subbranches": 0,
            "policy": "The official row stays one broad object; owner exhaustiveness is proven from current canonical service-word authority, not by inventing FIPI subcodes.",
        },
        "exact_owner_resolution": {
            "exact_current_canonical_owners": EXACT_OWNERS,
            "exact_owner_count": len(EXACT_OWNERS),
            "owner_proofs": owner_proofs,
            "historical_placeholder": PLACEHOLDER,
            "historical_placeholder_disposition": "ABSORBED_BY_PROVED_FUNCTION_AND_HOMONYM_BRANCHES_NO_INDEPENDENT_OWNER",
            "placeholder_reason": (
                "Primary canonical authority explicitly normalizes function/homonym examples into productive owners unless an independent decision remains. "
                "The preposition owner contains the derived-preposition vs free-combination functional boundary; the conjunction owner contains explicit homonymic contrasts. "
                "No independent service-word homonym/function semantic is left outside these owners."
            ),
            "negative_particle_overlap_policy": (
                "The particle owner is explicitly nonnegative. НЕ/НИ remains under the separately accepted OGE 6.9 owner system and is not duplicated into 6.11."
            ),
            "exact_owner_set_proven": True,
            "unresolved_owner_candidates": 0,
            "unresolved_placeholders": 0,
            "new_school_identities_required": 0,
            "current_route_supersession_required": False,
            "current_inventory_route_already_matches_exact_owner_set": True,
            "evidence_gate_required_before_object_acceptance": True,
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
            "Audit independent current reviewed/source-verified learner trainer/practice evidence separately for each of the three exact 6.11 owners. "
            "Do not count generic route evidence or mixed-owner evidence as exact component proof. Object acceptance remains forbidden until that evidence gate passes."
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

    print("OGE_6_11_SERVICE_WORDS_EXACT_OWNER_RESOLUTION=PASS")
    print(f"EXACT_CURRENT_CANONICAL_OWNERS={r['exact_owner_count']}")
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
