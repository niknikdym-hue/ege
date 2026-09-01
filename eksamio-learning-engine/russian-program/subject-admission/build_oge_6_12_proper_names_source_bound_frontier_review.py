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
CAPITALIZATION_WAVE = ENGINE / "250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION-v0.1.json"

TARGET_CODE = "6.12"
TARGET_TOPIC = "proper names / capitalization"
FIPI_WORDING = "Правописание собственных имён существительных"
FIPI_APPROVED_ARCHIVE_URL = "https://doc.fipi.ru/oge/demoversii-specifikacii-kodifikatory/2026/ru_9_2026.zip"
FIPI_NAVIGATOR_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"

EXPECTED_HISTORICAL_OVERLAY_OWNERS = ["capitalization mastery families from file 250"]
LEGACY_PLACEHOLDERS = ["capitalization mastery families from file 250"]

# Reuse-first candidate frontier only. These are not accepted OGE 6.12 owners here.
EXPECTED_REUSE_FIRST_CANDIDATES = [
    "school-capitalization-astronomical-names",
    "school-capitalization-awards-orders-medals",
    "school-capitalization-conditional-special-proper-names",
    "school-capitalization-documents-works-media-objects",
    "school-capitalization-geographic-administrative-names",
    "school-capitalization-historical-calendar-public-events",
    "school-capitalization-organizations-authorities-institutions",
    "school-capitalization-person-animal-name-and-derivatives",
    "school-capitalization-positions-titles",
    "school-capitalization-religious-names",
    "school-capitalization-trademarks-breeds-varieties-products",
]

# Nearby capitalization identities are explicitly not candidates for 6.12.
EXPECTED_EXCLUDED_NEARBY = {
    "school-capitalization-sentence-text-start": (
        "Generic sentence/text-initial capitalization is not spelling of proper nouns."
    ),
    "school-abbreviations-capitalization-formation": (
        "Abbreviation capitalization/formation belongs to the separate FIPI 6.13 compound/abbreviated-word object."
    ),
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def build_review() -> dict[str, Any]:
    overlay = load_json(OGE_OVERLAY)
    inventory = load_json(IDENTITY_INVENTORY)
    current_school = load_json(CURRENT_SCHOOL)
    capitalization_wave = load_json(CAPITALIZATION_WAVE)

    route_rows = [
        row
        for row in overlay.get("orthography_codifier_overlay") or []
        if isinstance(row, dict) and str(row.get("position")) == TARGET_CODE
    ]
    if len(route_rows) != 1:
        raise ValueError("OGE 6.12 overlay row must exist exactly once")
    historical_route = route_rows[0]
    if historical_route.get("topic") != TARGET_TOPIC:
        raise ValueError("OGE 6.12 historical route topic drift")
    if historical_route.get("classification") != "EXAM_ONLY_COMPOSITE":
        raise ValueError("OGE 6.12 historical route classification drift")
    historical_owners = [str(value) for value in historical_route.get("owners") or []]
    if historical_owners != EXPECTED_HISTORICAL_OVERLAY_OWNERS:
        raise ValueError("OGE 6.12 historical capitalization placeholder drift")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    route_key = "oge_2026_orthography_route::oge-2026-orthography-6-12"
    current_rows = [item for item in objects if item.get("object_key") == route_key]
    if len(current_rows) != 1:
        raise ValueError("OGE 6.12 identity-inventory route must exist exactly once")
    current_route = current_rows[0]
    if current_route.get("authority_status") != "current":
        raise ValueError("OGE 6.12 route is not current")
    if current_route.get("review_status") != "reviewed":
        raise ValueError("OGE 6.12 route is not reviewed")
    if current_route.get("audit_classification") != "EXAM_ROUTE_ONLY":
        raise ValueError("OGE 6.12 route classification drift")
    if current_route.get("observed_label") != TARGET_TOPIC:
        raise ValueError("OGE 6.12 inventory route label drift")
    current_refs = [str(ref) for ref in current_route.get("current_semantic_refs") or []]
    if current_refs:
        raise ValueError("OGE 6.12 current inventory route unexpectedly has semantic refs")

    source_normalization = [
        row
        for row in capitalization_wave.get("source_to_mastery_normalization") or []
        if isinstance(row, dict)
    ]
    normalized_owners = [str(row.get("owner")) for row in source_normalization]
    if len(normalized_owners) != 13 or len(set(normalized_owners)) != 13:
        raise ValueError("capitalization source wave must expose exactly 13 unique normalized owners")

    expected_all = set(EXPECTED_REUSE_FIRST_CANDIDATES) | set(EXPECTED_EXCLUDED_NEARBY)
    if set(normalized_owners) != expected_all:
        missing = sorted(expected_all - set(normalized_owners))
        extra = sorted(set(normalized_owners) - expected_all)
        raise ValueError(f"capitalization wave owner frontier drift; missing={missing}; extra={extra}")

    canonical_rows = {
        str(item.get("source_id")): item
        for item in objects
        if item.get("source_system") == "school_canonical"
        and str(item.get("source_id") or "").startswith("school-")
    }

    candidate_details: list[dict[str, Any]] = []
    for ref in EXPECTED_REUSE_FIRST_CANDIDATES:
        row = canonical_rows.get(ref)
        if row is None:
            raise ValueError(f"OGE 6.12 reuse candidate missing canonical inventory: {ref}")
        if row.get("authority_status") != "current" or row.get("review_status") != "reviewed":
            raise ValueError(f"OGE 6.12 reuse candidate not current/reviewed: {ref}")
        if row.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            raise ValueError(f"OGE 6.12 reuse candidate not canonical: {ref}")
        if row.get("current_semantic_refs") != [ref]:
            raise ValueError(f"OGE 6.12 reuse candidate self-ref drift: {ref}")
        if row.get("candidate_canonical_owner") != ref:
            raise ValueError(f"OGE 6.12 reuse candidate owner drift: {ref}")
        provenance = [str(x) for x in row.get("evidence_provenance_refs") or []]
        if not any("250-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A4-CAPITALIZATION" in x for x in provenance):
            raise ValueError(f"OGE 6.12 reuse candidate lacks capitalization-wave provenance: {ref}")
        candidate_details.append(
            {
                "ref": ref,
                "observed_label": str(row.get("observed_label")),
                "observed_meaning": str(row.get("observed_meaning")),
                "evidence_provenance_refs": provenance,
                "status": "REUSE_FIRST_CANDIDATE_NOT_ACCEPTED_OWNER",
            }
        )

    excluded_details: list[dict[str, str]] = []
    for ref, reason in EXPECTED_EXCLUDED_NEARBY.items():
        row = canonical_rows.get(ref)
        if row is None:
            raise ValueError(f"OGE 6.12 excluded nearby identity missing canonical inventory: {ref}")
        if row.get("authority_status") != "current" or row.get("review_status") != "reviewed":
            raise ValueError(f"OGE 6.12 excluded nearby identity not current/reviewed: {ref}")
        excluded_details.append({"ref": ref, "reason": reason})

    school_denominator = current_school.get("current_school_canonical_denominator")
    if school_denominator != 186:
        raise ValueError("current school denominator drift")

    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_12_PROPER_NAMES_SOURCE_BOUND_FRONTIER",
        "official_source": {
            "document": "ФИПИ. ОГЭ-2026. Русский язык. Кодификатор проверяемых требований и элементов содержания",
            "approved_archive_url": FIPI_APPROVED_ARCHIVE_URL,
            "orthography_navigator_url": FIPI_NAVIGATOR_URL,
            "retrieved_for_review": "2026-09-01",
            "content_code": TARGET_CODE,
            "exact_fipi_wording": FIPI_WORDING,
            "explicit_source_object_count": 1,
            "explicit_subbranches_in_fipi_row": 0,
            "source_boundary_policy": (
                "FIPI 6.12 is one broad codifier object, 'Правописание собственных имён существительных', "
                "and the codifier row does not enumerate subbranches. Do not manufacture finer official subcodes. "
                "Current reviewed capitalization identities may be reused only after a separate exact-owner exhaustiveness proof."
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
        },
        "reuse_first_frontier": {
            "official_atomic_source_objects": 1,
            "official_explicit_subbranches": 0,
            "current_route_refs": current_refs,
            "current_route_ref_count": 0,
            "candidate_refs": EXPECTED_REUSE_FIRST_CANDIDATES,
            "candidate_count": len(EXPECTED_REUSE_FIRST_CANDIDATES),
            "candidate_details": candidate_details,
            "explicitly_excluded_nearby": excluded_details,
            "explicitly_excluded_nearby_count": len(excluded_details),
            "unresolved_historical_placeholder_count": len(LEGACY_PLACEHOLDERS),
            "school_reopen_required": False,
            "new_school_identities_required_now": 0,
            "current_route_supersession_required_now": False,
            "exact_owner_resolution_required": True,
            "exact_route_ready_now": False,
            "interpretation": (
                "The current 6.12 inventory route has no semantic refs, while the historical overlay points only to a broad "
                "file-250 capitalization-family placeholder. Eleven current reviewed capitalization identities are therefore "
                "frozen as reuse-first candidates, not accepted owners. Generic sentence-start capitalization and abbreviation "
                "capitalization are explicitly excluded from this candidate set."
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
            "Prove or reject exact-owner exhaustiveness for each of the eleven reuse-first candidate capitalization identities "
            "against the single broad FIPI 6.12 object. Only a separate exact-owner proof may authorize current-route supersession. "
            "Component-specific independent learner evidence remains mandatory before any 6.12 object acceptance."
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
    frontier = review["reuse_first_frontier"]
    safety = review["safety"]

    print("OGE_6_12_PROPER_NAMES_SOURCE_BOUND_FRONTIER=PASS")
    print(f"OFFICIAL_ATOMIC_SOURCE_OBJECTS={frontier['official_atomic_source_objects']}")
    print(f"OFFICIAL_EXPLICIT_SUBBRANCHES={frontier['official_explicit_subbranches']}")
    print(f"CURRENT_ROUTE_REFS={frontier['current_route_ref_count']}")
    print(f"REUSE_FIRST_CANDIDATE_REFS={frontier['candidate_count']}")
    print(f"EXPLICIT_REJECTED_NEARBY_CANONICALS={frontier['explicitly_excluded_nearby_count']}")
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
