#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

TARGET_CODE = "6.6"
TARGET_TOPIC = "suffix spelling across parts of speech"
FIPI_NAVIGATOR_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"

LEGACY_PLACEHOLDERS = [
    "noun suffix families from file 252",
    "adjective suffix families from file 252",
]
EXPECTED_CURRENT_ROUTE_REFS = [
    "school-adverb-final-vowel-a-o",
    "school-gerund-forming-suffix-system",
    "school-o-e-after-sibilants-suffix-ending",
    "school-participle-vowel-suffix-conjugation-base",
    "school-unstressed-suffix-vowel-verification-fixed-patterns",
    "school-verb-enet-derived-from-noun",
    "school-verb-infinitive-past-nonfinite-stem-vowel",
    "school-verb-stressed-va-boundary",
    "school-verb-suffix-ova-eva-yva-iva-base",
    "school-vowels-after-ts-suffix-ending",
]
SOURCE_BOUND_EXACT_OWNER_CANDIDATES = [
    "school-adverb-final-vowel-a-o",
    "school-adjective-k-sk-derivational-boundary",
    "school-gerund-forming-suffix-system",
    "school-noun-agent-suffix-chik-shchik-soft-sign",
    "school-noun-suffix-ek-ik-vowel-retention",
    "school-o-e-after-sibilants-suffix-ending",
    "school-participle-vowel-suffix-conjugation-base",
    "school-verb-infinitive-past-nonfinite-stem-vowel",
    "school-verb-suffix-ova-eva-yva-iva-base",
    "school-vowels-after-ts-suffix-ending",
]
CURRENT_NONEXACT_ROUTE_REFS = [
    "school-unstressed-suffix-vowel-verification-fixed-patterns",
    "school-verb-enet-derived-from-noun",
    "school-verb-stressed-va-boundary",
]
MISSING_EXACT_OWNER_CANDIDATES = [
    "school-adjective-k-sk-derivational-boundary",
    "school-noun-agent-suffix-chik-shchik-soft-sign",
    "school-noun-suffix-ek-ik-vowel-retention",
]

OFFICIAL_BRANCHES = [
    {
        "branch": "vowels_after_ts_in_suffixes",
        "fipi_wording": "правописание ы и и после ц",
        "candidate_owner_refs": ["school-vowels-after-ts-suffix-ending"],
    },
    {
        "branch": "noun_suffix_o_e_yo_after_sibilants_ts",
        "fipi_wording": "правописание о и е (ё) после шипящих и ц в суффиксах имён существительных",
        "candidate_owner_refs": ["school-o-e-after-sibilants-suffix-ending"],
    },
    {
        "branch": "noun_chik_shchik",
        "fipi_wording": "правописание суффиксов -чик- и -щик-",
        "candidate_owner_refs": ["school-noun-agent-suffix-chik-shchik-soft-sign"],
    },
    {
        "branch": "noun_ek_ik_chik",
        "fipi_wording": "правописание -ек- и -ик- (-чик-) имён существительных",
        "candidate_owner_refs": ["school-noun-suffix-ek-ik-vowel-retention"],
    },
    {
        "branch": "adjective_suffix_o_e_after_sibilants_ts",
        "fipi_wording": "правописание о и е после шипящих и ц в суффиксах имён прилагательных",
        "candidate_owner_refs": ["school-o-e-after-sibilants-suffix-ending"],
    },
    {
        "branch": "verb_ova_eva_yva_iva",
        "fipi_wording": "правописание суффиксов -ова-, -ева-, -ыва-, -ива-",
        "candidate_owner_refs": ["school-verb-suffix-ova-eva-yva-iva-base"],
    },
    {
        "branch": "past_tense_vowel_before_l",
        "fipi_wording": "правописание гласной перед суффиксом -л- в формах прошедшего времени глагола",
        "candidate_owner_refs": ["school-verb-infinitive-past-nonfinite-stem-vowel"],
    },
    {
        "branch": "adjective_k_sk",
        "fipi_wording": "правописание суффиксов -к- и -ск- имён прилагательных",
        "candidate_owner_refs": ["school-adjective-k-sk-derivational-boundary"],
    },
    {
        "branch": "participle_suffix_vowels",
        "fipi_wording": "правописание гласных в суффиксах причастий",
        "candidate_owner_refs": ["school-participle-vowel-suffix-conjugation-base"],
    },
    {
        "branch": "gerund_suffix_vowels",
        "fipi_wording": "правописание гласных в суффиксах деепричастий",
        "candidate_owner_refs": ["school-gerund-forming-suffix-system"],
    },
    {
        "branch": "adverb_a_o_with_prefixes",
        "fipi_wording": "правописание суффиксов -а и -о наречий с приставками из-, до-, с-, в-, на-, за-",
        "candidate_owner_refs": ["school-adverb-final-vowel-a-o"],
    },
    {
        "branch": "adverb_o_e_after_sibilants",
        "fipi_wording": "правописание суффиксов наречий -о и -е после шипящих",
        "candidate_owner_refs": ["school-o-e-after-sibilants-suffix-ending"],
    },
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def build_review() -> dict[str, Any]:
    overlay = load_json(OGE_OVERLAY)
    inventory = load_json(IDENTITY_INVENTORY)

    rows = [
        row
        for row in overlay.get("orthography_codifier_overlay") or []
        if isinstance(row, dict) and str(row.get("position")) == TARGET_CODE
    ]
    if len(rows) != 1:
        raise ValueError("OGE 6.6 overlay row must exist exactly once")
    route = rows[0]
    if route.get("topic") != TARGET_TOPIC or route.get("classification") != "EXAM_ONLY_COMPOSITE":
        raise ValueError("OGE 6.6 route authority drift")

    overlay_owners = [str(value) for value in route.get("owners") or []]
    if not all(placeholder in overlay_owners for placeholder in LEGACY_PLACEHOLDERS):
        raise ValueError("OGE 6.6 legacy family placeholders unexpectedly changed")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    route_rows = [
        item
        for item in objects
        if item.get("object_key") == "oge_2026_orthography_route::oge-2026-orthography-6-6"
    ]
    if len(route_rows) != 1:
        raise ValueError("OGE 6.6 identity-inventory route must exist exactly once")
    inventory_route = route_rows[0]
    current_refs = [str(ref) for ref in inventory_route.get("current_semantic_refs") or []]
    if current_refs != EXPECTED_CURRENT_ROUTE_REFS:
        raise ValueError("OGE 6.6 current inventory route refs drifted")

    canonical_rows = {
        str(item.get("source_id")): item
        for item in objects
        if item.get("source_system") == "school_canonical"
        and str(item.get("source_id") or "").startswith("school-")
    }
    missing_canonical = [
        ref for ref in SOURCE_BOUND_EXACT_OWNER_CANDIDATES if ref not in canonical_rows
    ]
    if missing_canonical:
        raise ValueError("source-supported candidate missing from canonical school inventory: " + ",".join(missing_canonical))

    source_supported_current = sorted(set(current_refs) & set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES))
    missing_exact = sorted(set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES) - set(current_refs))
    nonexact_current = sorted(set(current_refs) - set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES))
    if missing_exact != MISSING_EXACT_OWNER_CANDIDATES:
        raise ValueError("OGE 6.6 missing exact-owner candidate set drifted")
    if nonexact_current != CURRENT_NONEXACT_ROUTE_REFS:
        raise ValueError("OGE 6.6 current nonexact route-ref set drifted")
    if len(source_supported_current) != 7:
        raise ValueError("OGE 6.6 supported-current count drifted")

    branch_refs = {
        ref
        for branch in OFFICIAL_BRANCHES
        for ref in branch["candidate_owner_refs"]
    }
    if branch_refs != set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES):
        raise ValueError("official branch-to-owner frontier does not match unique source-bound candidate set")

    result = {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_6_SUFFIX_SOURCE_BOUND_FRONTIER",
        "official_source": {
            "document": "ФИПИ. Навигатор самостоятельной подготовки к ОГЭ-2026. Русский язык. Орфография",
            "url": FIPI_NAVIGATOR_URL,
            "retrieved_for_review": "2026-08-31",
            "content_code": TARGET_CODE,
            "source_boundary_policy": "The explicit 6.6 enumeration is treated as the exact route frontier. Broader school suffix identities may support teaching, but they are not exact 6.6 owners unless they own an enumerated branch.",
            "branches": OFFICIAL_BRANCHES,
        },
        "historical_overlay_truth": {
            "classification": str(route.get("classification")),
            "owners": overlay_owners,
            "legacy_family_placeholders": LEGACY_PLACEHOLDERS,
            "placeholder_count": len(LEGACY_PLACEHOLDERS),
            "historical_overlay_mutated_by_this_review": False,
        },
        "identity_inventory_truth": {
            "source_id": str(inventory_route.get("source_id")),
            "audit_classification": str(inventory_route.get("audit_classification")),
            "review_status": str(inventory_route.get("review_status")),
            "current_semantic_refs": current_refs,
        },
        "source_bound_frontier": {
            "official_branch_count": len(OFFICIAL_BRANCHES),
            "unique_exact_owner_candidates": SOURCE_BOUND_EXACT_OWNER_CANDIDATES,
            "unique_exact_owner_candidate_count": len(SOURCE_BOUND_EXACT_OWNER_CANDIDATES),
            "current_source_supported_exact_candidates": source_supported_current,
            "current_source_supported_exact_candidate_count": len(source_supported_current),
            "missing_exact_owner_candidates_from_current_route": missing_exact,
            "missing_exact_owner_candidate_count": len(missing_exact),
            "current_nonexact_route_refs": nonexact_current,
            "current_nonexact_route_ref_count": len(nonexact_current),
            "school_reopen_required": False,
            "school_count_effect_if_route_is_corrected": 0,
            "exact_route_ready_now": False,
            "next_atomic_action": "Supersede current-launch 6.6 route truth by replacing the three nonexact current refs with the three source-supported canonical refs and eliminating the two historical family placeholders; do not mutate historical 265/273 evidence in place.",
        },
        "nonexact_ref_dispositions": [
            {
                "canonical_ref": "school-unstressed-suffix-vowel-verification-fixed-patterns",
                "disposition": "BROAD_SUPPORT_NOT_EXACT_6_6_OWNER",
                "reason": "The identity is a generic fallback for unstressed suffix vowels; FIPI 6.6 enumerates specific tested suffix branches for which exact canonical owners already exist.",
            },
            {
                "canonical_ref": "school-verb-enet-derived-from-noun",
                "disposition": "NO_EXACT_OGE_2026_6_6_BINDING_PROVEN",
                "reason": "The FIPI 6.6 enumeration does not name the -ЕНЕТЬ derivational family.",
            },
            {
                "canonical_ref": "school-verb-stressed-va-boundary",
                "disposition": "NO_EXACT_OGE_2026_6_6_BINDING_PROVEN",
                "reason": "The FIPI 6.6 enumeration names -ОВА-/-ЕВА-/-ЫВА-/-ИВА-, not the separate stressed -ВА- decision.",
            },
        ],
        "admission_effect": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "new_school_canonical_identities": 0,
            "false_exact_mastery_admissions": 0,
        },
        "mastery_guard": {
            "route_or_broad_composite_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required_before_exact_acceptance": True,
        },
        "safety": {
            "production_integration": "HOLD",
            "accepted_demo_or_scorer_change": False,
            "tilda_change": False,
            "learner_audio_persistence": 0,
            "production_peis_write": False,
            "provider_execution": False,
            "public_traffic": False,
            "real_payment_or_refund": False,
            "real_message_delivery": False,
        },
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    review = build_review()
    rendered = json.dumps(review, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    frontier = review["source_bound_frontier"]
    effect = review["admission_effect"]
    safety = review["safety"]
    print("OGE_6_6_SUFFIX_SOURCE_BOUND_FRONTIER=PASS")
    print(f"OFFICIAL_BRANCHES={frontier['official_branch_count']}")
    print(f"UNIQUE_EXACT_OWNER_CANDIDATES={frontier['unique_exact_owner_candidate_count']}")
    print(f"CURRENT_ROUTE_REFS={len(review['identity_inventory_truth']['current_semantic_refs'])}")
    print(f"CURRENT_SOURCE_SUPPORTED_EXACT_CANDIDATES={frontier['current_source_supported_exact_candidate_count']}")
    print(f"MISSING_EXACT_OWNER_CANDIDATES={frontier['missing_exact_owner_candidate_count']}")
    print(f"CURRENT_NONEXACT_ROUTE_REFS={frontier['current_nonexact_route_ref_count']}")
    print(f"LEGACY_PLACEHOLDERS={review['historical_overlay_truth']['placeholder_count']}")
    print(f"SCHOOL_REOPEN_REQUIRED={int(frontier['school_reopen_required'])}")
    print(f"SEMANTIC_ADMISSIONS={effect['semantic_admissions']}")
    print(f"OBJECT_CLOSURES={effect['object_closures']}")
    print(f"FALSE_EXACT_MASTERY={effect['false_exact_mastery_admissions']}")
    print(f"LEARNER_AUDIO_PERSISTENCE={safety['learner_audio_persistence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
