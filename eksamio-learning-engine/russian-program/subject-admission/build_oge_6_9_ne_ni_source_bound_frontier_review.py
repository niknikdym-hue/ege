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

TARGET_CODE = "6.9"
TARGET_TOPIC = "НЕ/НИ"
FIPI_NAVIGATOR_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"

EXPECTED_HISTORICAL_OVERLAY_OWNERS = [
    "active НЕ spelling systems",
    "active NI semantic/spelling systems",
    "school-ni-fixed-idioms",
]
LEGACY_PLACEHOLDERS = [
    "active НЕ spelling systems",
    "active NI semantic/spelling systems",
]
EXPECTED_CURRENT_ROUTE_REFS = ["school-ni-fixed-idioms"]

OFFICIAL_BRANCHES = [
    {
        "branch": "ne_with_nouns",
        "fipi_wording": "слитное и раздельное написание не с именами существительными",
        "candidate_owner_refs": ["school-ne-noun-adjective-o-adverb-spelling-system"],
    },
    {
        "branch": "ne_with_adjectives",
        "fipi_wording": "слитное и раздельное написание не с именами прилагательными",
        "candidate_owner_refs": ["school-ne-noun-adjective-o-adverb-spelling-system"],
    },
    {
        "branch": "ne_with_verbs",
        "fipi_wording": "слитное и раздельное написание не с глаголами",
        "candidate_owner_refs": ["school-ne-verb-gerund-spelling-base"],
    },
    {
        "branch": "pronouns_with_ne_ni",
        "fipi_wording": "правописание местоимений с не и ни",
        "candidate_owner_refs": [
            "school-ne-numeral-pronoun-spelling-base",
            "school-negative-pronouns-ne-ni-stress-preposition-boundary",
            "school-ne-kto-inoy-vs-nikto-inoy",
        ],
    },
    {
        "branch": "ne_with_participles",
        "fipi_wording": "слитное и раздельное написание не с причастиями",
        "candidate_owner_refs": ["school-ne-participle-dependent-short-opposition-boundary"],
    },
    {
        "branch": "ne_with_gerunds",
        "fipi_wording": "слитное и раздельное написание не с деепричастиями",
        "candidate_owner_refs": ["school-ne-verb-gerund-spelling-base"],
    },
    {
        "branch": "ne_with_adverbs",
        "fipi_wording": "слитное и раздельное написание не с наречиями",
        "candidate_owner_refs": [
            "school-ne-noun-adjective-o-adverb-spelling-system",
            "school-ne-non-o-adverb-predicative-separate-system",
            "school-negative-adverbs-ne-ni-spelling",
            "school-pri-chem-ni-pri-chem-nipochem",
        ],
    },
    {
        "branch": "semantic_distinction_ne_ni",
        "fipi_wording": "смысловые различия частиц не и ни",
        "candidate_owner_refs": [
            "school-ni-particle-vs-repeating-conjunction",
            "school-ni-fixed-idioms",
            "school-ne-double-negation-affirmative-boundary",
            "school-ne-kto-inoy-vs-nikto-inoy",
            "school-ne-ni-ni-odin-ne-odin-ni-razu-ne-raz",
            "school-ne-ni-pronominal-exclamatory-vs-concessive-boundary",
            "school-negative-pronouns-ne-ni-stress-preposition-boundary",
            "school-negative-adverbs-ne-ni-spelling",
            "school-pri-chem-ni-pri-chem-nipochem",
        ],
    },
]

SOURCE_BOUND_OWNER_CANDIDATES = sorted(
    {ref for branch in OFFICIAL_BRANCHES for ref in branch["candidate_owner_refs"]}
)


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
        raise ValueError("OGE 6.9 overlay row must exist exactly once")
    historical_route = route_rows[0]
    if historical_route.get("topic") != TARGET_TOPIC:
        raise ValueError("OGE 6.9 historical route topic drift")
    if historical_route.get("classification") != "EXAM_ONLY_COMPOSITE":
        raise ValueError("OGE 6.9 historical route classification drift")
    historical_owners = [str(value) for value in historical_route.get("owners") or []]
    if historical_owners != EXPECTED_HISTORICAL_OVERLAY_OWNERS:
        raise ValueError("OGE 6.9 historical owner/placeholder frontier drift")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    current_rows = [
        item
        for item in objects
        if item.get("object_key") == "oge_2026_orthography_route::oge-2026-orthography-6-9"
    ]
    if len(current_rows) != 1:
        raise ValueError("OGE 6.9 identity-inventory route must exist exactly once")
    current_route = current_rows[0]
    if current_route.get("authority_status") != "current":
        raise ValueError("OGE 6.9 route is not current")
    if current_route.get("review_status") != "reviewed":
        raise ValueError("OGE 6.9 route is not reviewed")
    if current_route.get("audit_classification") != "EXAM_ROUTE_ONLY":
        raise ValueError("OGE 6.9 route classification drift")
    current_refs = [str(ref) for ref in current_route.get("current_semantic_refs") or []]
    if current_refs != EXPECTED_CURRENT_ROUTE_REFS:
        raise ValueError("OGE 6.9 current inventory route refs drifted")

    canonical_rows = {
        str(item.get("source_id")): item
        for item in objects
        if item.get("source_system") == "school_canonical"
        and str(item.get("source_id") or "").startswith("school-")
    }
    missing_inventory = [ref for ref in SOURCE_BOUND_OWNER_CANDIDATES if ref not in canonical_rows]
    if missing_inventory:
        raise ValueError(
            "source-bound 6.9 candidate missing from canonical inventory: "
            + ",".join(missing_inventory)
        )
    for ref in SOURCE_BOUND_OWNER_CANDIDATES:
        row = canonical_rows[ref]
        if row.get("authority_status") != "current" or row.get("review_status") != "reviewed":
            raise ValueError(f"6.9 candidate not current/reviewed: {ref}")
        if row.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            raise ValueError(f"6.9 candidate is not canonical school identity: {ref}")
        if row.get("current_semantic_refs") != [ref]:
            raise ValueError(f"6.9 canonical self-ref drift: {ref}")
        if row.get("candidate_canonical_owner") != ref:
            raise ValueError(f"6.9 canonical owner drift: {ref}")

    branch_refs = {ref for branch in OFFICIAL_BRANCHES for ref in branch["candidate_owner_refs"]}
    if branch_refs != set(SOURCE_BOUND_OWNER_CANDIDATES):
        raise ValueError("official 6.9 branch-to-owner frontier mismatch")

    current_supported = sorted(set(current_refs) & set(SOURCE_BOUND_OWNER_CANDIDATES))
    current_nonexact = sorted(set(current_refs) - set(SOURCE_BOUND_OWNER_CANDIDATES))
    missing_candidates = sorted(set(SOURCE_BOUND_OWNER_CANDIDATES) - set(current_refs))
    if current_supported != EXPECTED_CURRENT_ROUTE_REFS:
        raise ValueError("OGE 6.9 supported current refs drift")
    if current_nonexact:
        raise ValueError("OGE 6.9 current route contains non-source-bound refs")

    school_denominator = current_school.get("current_school_canonical_denominator")
    if school_denominator != 186:
        raise ValueError("current school denominator drift")

    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_9_NE_NI_SOURCE_BOUND_FRONTIER",
        "official_source": {
            "document": "ФИПИ. Навигатор самостоятельной подготовки к ОГЭ-2026. Русский язык. Орфография",
            "url": FIPI_NAVIGATOR_URL,
            "retrieved_for_review": "2026-09-01",
            "content_code": TARGET_CODE,
            "source_boundary_policy": (
                "Only the eight explicit FIPI 6.9 branches are admitted to this frontier. "
                "Nearby 6.8 solid/hyphen/separate spelling and 6.11 service-word spelling are not imported."
            ),
            "branches": OFFICIAL_BRANCHES,
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
        "source_bound_frontier": {
            "official_branch_count": len(OFFICIAL_BRANCHES),
            "unique_owner_candidates": SOURCE_BOUND_OWNER_CANDIDATES,
            "unique_owner_candidate_count": len(SOURCE_BOUND_OWNER_CANDIDATES),
            "current_route_refs": current_refs,
            "current_source_supported_owner_candidates": current_supported,
            "missing_source_bound_owner_candidates": missing_candidates,
            "current_nonexact_route_refs": current_nonexact,
            "school_reopen_required": False,
            "new_school_identities_required_now": 0,
            "current_route_supersession_required": bool(missing_candidates),
            "exact_route_ready_now": False,
            "interpretation": (
                "The historical 6.9 overlay is under-resolved: two family placeholders collapse "
                "multiple current reviewed canonical identities, while the identity inventory retains "
                "only school-ni-fixed-idioms. This frontier resolves a finite source-bound candidate "
                "set but deliberately does not supersede the route or admit object mastery."
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
            "After this frontier is green, create a separate current-route supersession only if every "
            "candidate remains current/reviewed and branch-bound; then audit component-specific learner "
            "evidence before any exact object acceptance."
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

    print("OGE_6_9_NE_NI_SOURCE_BOUND_FRONTIER=PASS")
    print(f"OFFICIAL_BRANCHES={frontier['official_branch_count']}")
    print(f"UNIQUE_SOURCE_BOUND_OWNER_CANDIDATES={frontier['unique_owner_candidate_count']}")
    print(f"CURRENT_ROUTE_REFS={len(frontier['current_route_refs'])}")
    print(f"CURRENT_SOURCE_SUPPORTED_OWNER_CANDIDATES={len(frontier['current_source_supported_owner_candidates'])}")
    print(f"MISSING_SOURCE_BOUND_OWNER_CANDIDATES={len(frontier['missing_source_bound_owner_candidates'])}")
    print(f"CURRENT_NONEXACT_ROUTE_REFS={len(frontier['current_nonexact_route_refs'])}")
    print(f"LEGACY_PLACEHOLDERS={review['historical_overlay_truth']['placeholder_count']}")
    print(f"SCHOOL_REOPEN_REQUIRED={int(frontier['school_reopen_required'])}")
    print(f"CURRENT_ROUTE_SUPERSESSION_REQUIRED={int(frontier['current_route_supersession_required'])}")
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
