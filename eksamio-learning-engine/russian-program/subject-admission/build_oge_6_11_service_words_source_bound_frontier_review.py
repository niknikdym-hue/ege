#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CURRENT_SCHOOL = ENGINE / "277-RUSSIAN-SCHOOL-CURRENT-LAUNCH-REFREEZE-v1.1.json"

TARGET_CODE = "6.11"
TARGET_TOPIC = "spelling of service words"
FIPI_WORDING = "Правописание служебных частей речи"
FIPI_NAVIGATOR_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"

EXPECTED_HISTORICAL_OVERLAY_OWNERS = [
    "school-preposition-solid-hyphen-separate-base",
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "service-word homonym/function branches",
]
LEGACY_PLACEHOLDERS = ["service-word homonym/function branches"]
EXPECTED_CURRENT_ROUTE_REFS = [
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-preposition-solid-hyphen-separate-base",
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def build_review() -> dict[str, Any]:
    overlay = load_json(OGE_OVERLAY)
    inventory = load_json(IDENTITY_INVENTORY)
    current_school = load_json(CURRENT_SCHOOL)

    route_rows = [
        row
        for row in overlay.get("orthography_codifier_overlay") or []
        if isinstance(row, dict) and str(row.get("position")) == TARGET_CODE
    ]
    if len(route_rows) != 1:
        raise ValueError("OGE 6.11 overlay row must exist exactly once")
    historical_route = route_rows[0]
    if historical_route.get("topic") != TARGET_TOPIC:
        raise ValueError("OGE 6.11 historical route topic drift")
    if historical_route.get("classification") != "EXAM_ONLY_COMPOSITE":
        raise ValueError("OGE 6.11 historical route classification drift")
    historical_owners = [str(value) for value in historical_route.get("owners") or []]
    if historical_owners != EXPECTED_HISTORICAL_OVERLAY_OWNERS:
        raise ValueError("OGE 6.11 historical owner/placeholder frontier drift")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    route_key = "oge_2026_orthography_route::oge-2026-orthography-6-11"
    current_rows = [item for item in objects if item.get("object_key") == route_key]
    if len(current_rows) != 1:
        raise ValueError("OGE 6.11 identity-inventory route must exist exactly once")
    current_route = current_rows[0]
    if current_route.get("authority_status") != "current":
        raise ValueError("OGE 6.11 route is not current")
    if current_route.get("review_status") != "reviewed":
        raise ValueError("OGE 6.11 route is not reviewed")
    if current_route.get("audit_classification") != "EXAM_ROUTE_ONLY":
        raise ValueError("OGE 6.11 route classification drift")
    if current_route.get("observed_label") != TARGET_TOPIC:
        raise ValueError("OGE 6.11 inventory route label drift")
    current_refs = [str(ref) for ref in current_route.get("current_semantic_refs") or []]
    if current_refs != EXPECTED_CURRENT_ROUTE_REFS:
        raise ValueError("OGE 6.11 current inventory route refs drifted")

    canonical_rows = {
        str(item.get("source_id")): item
        for item in objects
        if item.get("source_system") == "school_canonical"
        and str(item.get("source_id") or "").startswith("school-")
    }
    missing = [ref for ref in EXPECTED_CURRENT_ROUTE_REFS if ref not in canonical_rows]
    if missing:
        raise ValueError("OGE 6.11 route candidate missing canonical inventory: " + ",".join(missing))

    candidate_details = []
    for ref in EXPECTED_CURRENT_ROUTE_REFS:
        row = canonical_rows[ref]
        if row.get("authority_status") != "current" or row.get("review_status") != "reviewed":
            raise ValueError(f"OGE 6.11 candidate not current/reviewed: {ref}")
        if row.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            raise ValueError(f"OGE 6.11 candidate not canonical: {ref}")
        if row.get("current_semantic_refs") != [ref]:
            raise ValueError(f"OGE 6.11 candidate self-ref drift: {ref}")
        if row.get("candidate_canonical_owner") != ref:
            raise ValueError(f"OGE 6.11 candidate owner drift: {ref}")
        candidate_details.append(
            {
                "ref": ref,
                "observed_label": str(row.get("observed_label")),
                "observed_meaning": str(row.get("observed_meaning")),
                "evidence_provenance_refs": [str(x) for x in row.get("evidence_provenance_refs") or []],
            }
        )

    school_denominator = current_school.get("current_school_canonical_denominator")
    if school_denominator != 186:
        raise ValueError("current school denominator drift")

    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_11_SERVICE_WORDS_SOURCE_BOUND_FRONTIER",
        "official_source": {
            "document": "ФИПИ. Навигатор самостоятельной подготовки к ОГЭ-2026. Русский язык. Орфография",
            "url": FIPI_NAVIGATOR_URL,
            "retrieved_for_review": "2026-09-01",
            "content_code": TARGET_CODE,
            "exact_fipi_wording": FIPI_WORDING,
            "explicit_source_object_count": 1,
            "explicit_subbranches_in_fipi_row": 0,
            "source_boundary_policy": (
                "FIPI 6.11 is one broad codifier object and does not enumerate subbranches in the navigator row. "
                "Do not manufacture a finer official decomposition. Preposition, conjunction and nonnegative-particle "
                "canonical identities are therefore inventory candidates only until a separate exact-owner proof shows "
                "that their combined semantics exhaust the official 6.11 object without importing nearby 6.8 or 6.9 scope."
            ),
        },
        "historical_overlay_truth": {
            "classification": str(historical_route.get("classification")),
            "owners": historical_owners,
            "legacy_placeholders": LEGACY_PLACEHOLDERS,
            "placeholder_count": len(LEGACY_PLACEHOLDERS),
            "historical_overlay_mutated_by_this_review": False,
        },
        "identity_inventory_truth": {
            "source_id": str(current_route.get("source_id")),
            "audit_classification": str(current_route.get("audit_classification")),
            "review_status": str(current_route.get("review_status")),
            "current_semantic_refs": current_refs,
            "candidate_details": candidate_details,
        },
        "source_bound_frontier": {
            "official_atomic_source_objects": 1,
            "official_explicit_subbranches": 0,
            "current_inventory_candidate_refs": current_refs,
            "current_inventory_candidate_count": len(current_refs),
            "unresolved_historical_placeholder_count": len(LEGACY_PLACEHOLDERS),
            "school_reopen_required": False,
            "new_school_identities_required_now": 0,
            "current_route_supersession_required_now": False,
            "exact_owner_resolution_required": True,
            "exact_route_ready_now": False,
            "interpretation": (
                "The current inventory already points 6.11 at three current reviewed canonical service-word identities, "
                "while the older overlay also carried one noncanonical homonym/function placeholder. Because the official "
                "FIPI 6.11 row itself is not branch-decomposed, this review freezes those three refs as reuse-first candidates "
                "and forbids treating them as an exact accepted owner set until a separate semantic exhaustiveness proof passes."
            ),
        },
        "current_school_truth": {
            "canonical_denominator": school_denominator,
            "school_reopen_required": False,
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
            "Prove or reject exact-owner exhaustiveness for the three current 6.11 inventory refs against the single broad "
            "FIPI source object, including the historical homonym/function placeholder. Only after that proof may current-route "
            "truth be superseded if needed; component-specific independent learner evidence remains mandatory before object acceptance."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    review = build_review()
    emitted = json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(emitted, encoding="utf-8")
    normalized = json.dumps(review, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(normalized).hexdigest()
    frontier = review["source_bound_frontier"]
    safety = review["safety"]

    print("OGE_6_11_SERVICE_WORDS_SOURCE_BOUND_FRONTIER=PASS")
    print(f"OFFICIAL_ATOMIC_SOURCE_OBJECTS={frontier['official_atomic_source_objects']}")
    print(f"OFFICIAL_EXPLICIT_SUBBRANCHES={frontier['official_explicit_subbranches']}")
    print(f"CURRENT_INVENTORY_CANDIDATE_REFS={frontier['current_inventory_candidate_count']}")
    print(f"UNRESOLVED_HISTORICAL_PLACEHOLDERS={frontier['unresolved_historical_placeholder_count']}")
    print(f"SCHOOL_REOPEN_REQUIRED={int(frontier['school_reopen_required'])}")
    print(f"CURRENT_ROUTE_SUPERSESSION_REQUIRED_NOW={int(frontier['current_route_supersession_required_now'])}")
    print(f"EXACT_OWNER_RESOLUTION_REQUIRED={int(frontier['exact_owner_resolution_required'])}")
    print(f"EXACT_ROUTE_READY_NOW={int(frontier['exact_route_ready_now'])}")
    print(f"SEMANTIC_ADMISSIONS={safety['semantic_admissions']}")
    print(f"OBJECT_CLOSURES={safety['object_closures']}")
    print(f"NEW_SCHOOL_IDENTITIES={safety['new_school_identities']}")
    print(f"FALSE_EXACT_MASTERY={safety['false_exact_mastery']}")
    print(f"LEARNER_AUDIO_PERSISTENCE={safety['learner_audio_persistence']}")
    print(f"NORMALIZED_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
