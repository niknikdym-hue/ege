#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
WAVE_B = ENGINE / "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json"
WAVE_C = ENGINE / "253-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-C-O26-O35-v0.1.json"
FIPI_REOPEN = ENGINE / "263-RUSSIAN-SCHOOL-FIPI-REOPEN-MATERIALIZATION-v0.1.json"
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

TARGET_CODE = "6.7"
TARGET_TOPIC = "endings of nouns, adjectives, verbs, numerals, participles"
FIPI_NAVIGATOR_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"

EXPECTED_HISTORICAL_OVERLAY_OWNERS = [
    "school-noun-case-ending-base",
    "special noun-ending families from file 252",
    "school-adjective-ending-inflection-and-special-forms with participle scope expansion from file 263",
    "school-verb-personal-ending-conjugation-base",
    "school-numeral-case-ending-inflection-base",
    "special numeral paradigm identities",
]
LEGACY_PLACEHOLDERS = [
    "special noun-ending families from file 252",
    "school-adjective-ending-inflection-and-special-forms with participle scope expansion from file 263",
    "special numeral paradigm identities",
]
EXPECTED_CURRENT_ROUTE_REFS = [
    "school-adjective-ending-inflection-and-special-forms with participle scope expansion from file 263",
    "school-noun-case-ending-base",
    "school-numeral-case-ending-inflection-base",
    "school-verb-personal-ending-conjugation-base",
]

NOUN_ENDING_OWNERS = [
    "school-noun-case-ending-base",
    "school-noun-case-ending-special-paradigms",
    "school-noun-genitive-plural-ending-system",
    "school-proper-name-instrumental-ending-boundary",
    "school-noun-special-suffix-gender-endings",
]
O_E_ENDING_OWNERS = [
    "school-o-e-after-sibilants-suffix-ending",
    "school-vowels-after-ts-suffix-ending",
]
ADJECTIVE_PARTICIPLE_ENDING_OWNER = "school-adjective-ending-inflection-and-special-forms"
VERB_ENDING_OWNER = "school-verb-personal-ending-conjugation-base"
NUMERAL_ENDING_OWNERS = [
    "school-numeral-case-ending-inflection-base",
    "school-numerals-two-form-paradigm-40-90-100",
    "school-numerals-both-parts-decline-50-80-200-900",
]
SOURCE_BOUND_EXACT_OWNER_CANDIDATES = sorted(
    set(
        NOUN_ENDING_OWNERS
        + O_E_ENDING_OWNERS
        + [ADJECTIVE_PARTICIPLE_ENDING_OWNER, VERB_ENDING_OWNER]
        + NUMERAL_ENDING_OWNERS
    )
)
CURRENT_SOURCE_SUPPORTED_EXACT_CANDIDATES = sorted(
    [
        "school-noun-case-ending-base",
        "school-numeral-case-ending-inflection-base",
        "school-verb-personal-ending-conjugation-base",
    ]
)
CURRENT_NONEXACT_ROUTE_REFS = [
    "school-adjective-ending-inflection-and-special-forms with participle scope expansion from file 263"
]
MISSING_EXACT_OWNER_CANDIDATES = sorted(
    set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES) - set(CURRENT_SOURCE_SUPPORTED_EXACT_CANDIDATES)
)

OFFICIAL_BRANCHES = [
    {
        "branch": "unstressed_noun_endings",
        "fipi_wording": "правописание безударных окончаний имён существительных",
        "candidate_owner_refs": NOUN_ENDING_OWNERS,
    },
    {
        "branch": "noun_endings_o_e_yo_after_sibilants_ts",
        "fipi_wording": "правописание о и е (ё) после шипящих и ц в окончаниях имён существительных",
        "candidate_owner_refs": O_E_ENDING_OWNERS,
    },
    {
        "branch": "unstressed_adjective_endings",
        "fipi_wording": "правописание безударных окончаний имён прилагательных",
        "candidate_owner_refs": [ADJECTIVE_PARTICIPLE_ENDING_OWNER],
    },
    {
        "branch": "adjective_endings_o_e_after_sibilants_ts",
        "fipi_wording": "правописание о и е после шипящих и ц в окончаниях имён прилагательных",
        "candidate_owner_refs": O_E_ENDING_OWNERS,
    },
    {
        "branch": "unstressed_personal_verb_endings",
        "fipi_wording": "правописание безударных личных окончаний глагола",
        "candidate_owner_refs": [VERB_ENDING_OWNER],
    },
    {
        "branch": "numeral_endings_norms",
        "fipi_wording": "нормы правописания окончаний числительных",
        "candidate_owner_refs": NUMERAL_ENDING_OWNERS,
    },
    {
        "branch": "participle_case_endings",
        "fipi_wording": "правописание падежных окончаний причастий",
        "candidate_owner_refs": [ADJECTIVE_PARTICIPLE_ENDING_OWNER],
    },
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def unit_ids(rows: Any) -> list[str]:
    if not isinstance(rows, list):
        raise ValueError("expected unit list")
    return [str(row.get("unit_id")) for row in rows if isinstance(row, dict)]


def build_review() -> dict[str, Any]:
    wave_b = load_json(WAVE_B)
    wave_c = load_json(WAVE_C)
    reopen = load_json(FIPI_REOPEN)
    overlay = load_json(OGE_OVERLAY)
    inventory = load_json(IDENTITY_INVENTORY)

    rows = [
        row
        for row in overlay.get("orthography_codifier_overlay") or []
        if isinstance(row, dict) and str(row.get("position")) == TARGET_CODE
    ]
    if len(rows) != 1:
        raise ValueError("OGE 6.7 overlay row must exist exactly once")
    route = rows[0]
    if route.get("topic") != TARGET_TOPIC or route.get("classification") != "EXAM_ONLY_COMPOSITE":
        raise ValueError("OGE 6.7 historical route authority drift")
    overlay_owners = [str(value) for value in route.get("owners") or []]
    if overlay_owners != EXPECTED_HISTORICAL_OVERLAY_OWNERS:
        raise ValueError("OGE 6.7 historical owner/placeholder frontier drift")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    route_rows = [
        item
        for item in objects
        if item.get("object_key") == "oge_2026_orthography_route::oge-2026-orthography-6-7"
    ]
    if len(route_rows) != 1:
        raise ValueError("OGE 6.7 identity-inventory route must exist exactly once")
    inventory_route = route_rows[0]
    current_refs = [str(ref) for ref in inventory_route.get("current_semantic_refs") or []]
    if current_refs != EXPECTED_CURRENT_ROUTE_REFS:
        raise ValueError("OGE 6.7 current inventory route refs drifted")

    canonical_rows = {
        str(item.get("source_id")): item
        for item in objects
        if item.get("source_system") == "school_canonical"
        and str(item.get("source_id") or "").startswith("school-")
    }
    missing_canonical = [ref for ref in SOURCE_BOUND_EXACT_OWNER_CANDIDATES if ref not in canonical_rows]
    if missing_canonical:
        raise ValueError("source-supported 6.7 candidate missing from canonical inventory: " + ",".join(missing_canonical))
    for ref in SOURCE_BOUND_EXACT_OWNER_CANDIDATES:
        row = canonical_rows[ref]
        if row.get("authority_status") != "current" or row.get("review_status") != "reviewed":
            raise ValueError(f"6.7 candidate not current/reviewed: {ref}")
        if row.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            raise ValueError(f"6.7 candidate is not canonical school identity: {ref}")
        if row.get("current_semantic_refs") != [ref]:
            raise ValueError(f"6.7 canonical self-ref drift: {ref}")

    o17 = wave_b.get("O17_noun_endings") or {}
    if unit_ids(o17.get("new_units")) != NOUN_ENDING_OWNERS[1:]:
        raise ValueError("file 252 O17 special noun-ending owner family drift")
    o19 = wave_b.get("O19_adjective_endings") or {}
    if unit_ids(o19.get("new_units")) != [ADJECTIVE_PARTICIPLE_ENDING_OWNER]:
        raise ValueError("file 252 O19 adjective-ending owner drift")

    o26 = wave_c.get("O26_verb_personal_endings") or {}
    verb_parent = o26.get("new_unit") or {}
    if verb_parent.get("unit_id") != VERB_ENDING_OWNER:
        raise ValueError("file 253 O26 verb-ending owner drift")
    if sorted(str(value) for value in verb_parent.get("absorbs") or []) != sorted(
        ["school-conjugation-i-exception-family", "school-conjugation-ii-exception-eleven"]
    ):
        raise ValueError("verb conjugation exception absorption drift")

    reopen_units = {
        str(row.get("unit_id")): row
        for row in reopen.get("canonical_units") or []
        if isinstance(row, dict)
    }
    for ref in ("school-noun-case-ending-base", "school-numeral-case-ending-inflection-base"):
        if ref not in reopen_units:
            raise ValueError(f"FIPI reopen 6.7 owner missing: {ref}")
        if "OGE-2026-orthography-6.7" not in (reopen_units[ref].get("fipi_routes") or []):
            raise ValueError(f"FIPI reopen route binding missing for {ref}")
    numeral_boundary = str(reopen_units["school-numeral-case-ending-inflection-base"].get("ownership_boundary") or "")
    for ref in NUMERAL_ENDING_OWNERS[1:]:
        if ref not in numeral_boundary:
            raise ValueError(f"special numeral owner not preserved by 263 boundary: {ref}")

    expansions = {
        str(row.get("unit_id")): row
        for row in reopen.get("scope_expansions") or []
        if isinstance(row, dict)
    }
    adjective_expansion = expansions.get(ADJECTIVE_PARTICIPLE_ENDING_OWNER)
    if not adjective_expansion or adjective_expansion.get("semantic_scope_after") != "adjective and participle case endings":
        raise ValueError("participle case-ending scope expansion drift")
    oe_expansion = expansions.get("school-o-e-after-sibilants-suffix-ending")
    if not oe_expansion or "ending" not in str(oe_expansion.get("semantic_scope_after") or ""):
        raise ValueError("O/E after-sibilants ending scope expansion drift")

    source_supported_current = sorted(set(current_refs) & set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES))
    nonexact_current = sorted(set(current_refs) - set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES))
    missing_exact = sorted(set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES) - set(current_refs))
    if source_supported_current != CURRENT_SOURCE_SUPPORTED_EXACT_CANDIDATES:
        raise ValueError("OGE 6.7 supported-current exact set drift")
    if nonexact_current != CURRENT_NONEXACT_ROUTE_REFS:
        raise ValueError("OGE 6.7 current nonexact route-ref set drift")
    if missing_exact != MISSING_EXACT_OWNER_CANDIDATES:
        raise ValueError("OGE 6.7 missing exact-owner set drift")

    branch_refs = {
        ref
        for branch in OFFICIAL_BRANCHES
        for ref in branch["candidate_owner_refs"]
    }
    if branch_refs != set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES):
        raise ValueError("official 6.7 branch-to-owner frontier does not match unique candidate set")

    return {
        "schema_version": "0.1.0",
        "status": "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_7_ENDINGS_SOURCE_BOUND_FRONTIER",
        "official_source": {
            "document": "ФИПИ. Навигатор самостоятельной подготовки к ОГЭ-2026. Русский язык. Орфография",
            "url": FIPI_NAVIGATOR_URL,
            "retrieved_for_review": "2026-08-31",
            "content_code": TARGET_CODE,
            "source_boundary_policy": "Only the seven explicit 6.7 ending branches are admitted to this review frontier. Related morphology, suffix and lexical families do not become 6.7 owners merely because they support form choice.",
            "branches": OFFICIAL_BRANCHES,
        },
        "historical_overlay_truth": {
            "classification": str(route.get("classification")),
            "owners": overlay_owners,
            "legacy_placeholders": LEGACY_PLACEHOLDERS,
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
            "next_atomic_action": "Create an additive current-launch 6.7 route supersession with exactly the 12 proven canonical owners and zero placeholders. Do not mutate historical 265/273 evidence in place; do not claim object/component acceptance until independent component evidence is separately audited.",
        },
        "boundary_notes": [
            {
                "boundary": "noun_endings",
                "decision": "BASE_PLUS_FOUR_SPECIAL_O17_OWNERS",
                "reason": "The current noun base explicitly routes special -ИЙ/-ИЕ/-ИЯ/-ЬЕ, genitive-plural, proper-name instrumental and other difficult ending families to independent current identities; file 252 O17 materializes those four ending owners.",
            },
            {
                "boundary": "adjective_and_participle_endings",
                "decision": "ONE_CURRENT_OWNER_WITH_FIPI_SCOPE_EXPANSION",
                "reason": "File 263 explicitly expands school-adjective-ending-inflection-and-special-forms to adjective and participle case endings with zero denominator effect.",
            },
            {
                "boundary": "verb_personal_endings",
                "decision": "ONE_CURRENT_PARENT_OWNER",
                "reason": "File 253 absorbs the old conjugation-exception lists into school-verb-personal-ending-conjugation-base, so they are not separate current owners.",
            },
            {
                "boundary": "numeral_endings",
                "decision": "BASE_PLUS_TWO_SEPARATELY_COUNTED_DIFFICULT_PARADIGMS",
                "reason": "File 263 explicitly preserves the 40/90/100 two-form paradigm and the 50–80/200–900 both-parts-decline paradigm as independent from the base numeral inflection router.",
            },
            {
                "boundary": "o_e_after_sibilants_and_ts_in_endings",
                "decision": "REUSE_TWO_EXISTING_CROSS_PART_OF_SPEECH_ORTHOGRAPHY_OWNERS",
                "reason": "The current school canon separately owns O/E(Ё) after sibilants and vowel selection after Ц in suffix/ending positions; no new ending-only school identity is created.",
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
    print("OGE_6_7_ENDINGS_SOURCE_BOUND_FRONTIER=PASS")
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
    print(f"NEW_SCHOOL_IDENTITIES={effect['new_school_canonical_identities']}")
    print(f"FALSE_EXACT_MASTERY={effect['false_exact_mastery_admissions']}")
    print(f"LEARNER_AUDIO_PERSISTENCE={safety['learner_audio_persistence']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
