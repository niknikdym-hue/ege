#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent.parent
PRONOUN_BANK = ENGINE / "172-RUSSIAN-SCHOOL-CANONICAL-BANK-CHUNK04-ADVERBS-PRONOUNS-HYPHEN-v0.1.json"
CURRENT_NORM_AUDIT = ENGINE / "221-RUSSIAN-SCHOOL-CANONICAL-COMPLETENESS-CURRENT-NORM-AUDIT-WAVE3-ADVERBS-PRONOUNS-HYPHEN-v0.1.json"
SEMANTIC_CONSOLIDATION = ENGINE / "239-RUSSIAN-SCHOOL-CANONICAL-SEMANTIC-CONSOLIDATION-AFTER-CURRENT-NORM-AUDIT-v0.1.json"
WAVE_D = ENGINE / "255-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-D-O36-O45-v0.1.json"
OGE_OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
IDENTITY_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"

TARGET_CODE = "6.8"
TARGET_TOPIC = "solid/hyphen/separate spelling across parts of speech"
FIPI_NAVIGATOR_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"

EXPECTED_HISTORICAL_OVERLAY_OWNERS = [
    "compound noun/adjective systems",
    "school-pol-polu-writing-boundary",
    "school-numeral-orthography-base",
    "negative/indefinite pronoun owners",
    "school-adverb-solid-hyphen-separate-system",
    "school-preposition-solid-hyphen-separate-base",
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
]
LEGACY_PLACEHOLDERS = [
    "compound noun/adjective systems",
    "negative/indefinite pronoun owners",
]
EXPECTED_CURRENT_ROUTE_REFS = [
    "school-adverb-solid-hyphen-separate-system",
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-numeral-orthography-base",
    "school-pol-polu-writing-boundary",
    "school-preposition-solid-hyphen-separate-base",
]

COMPOUND_ADJECTIVE_OWNER = "school-compound-adjective-solid-hyphen-separate-system"
ABSORBED_INDEFINITE_PRONOUN_ID = "school-indefinite-pronouns-hyphen-koe-preposition-boundary"
CURRENT_PRONOUN_PARTICLE_OWNER = "school-nonnegative-particle-separate-hyphen-spelling-base"
NEGATIVE_PRONOUN_NONOWNER = "school-negative-pronouns-ne-ni-stress-preposition-boundary"
COMPOUND_NOUN_NONOWNER = "school-compound-noun-solid-hyphen-system"

SOURCE_BOUND_EXACT_OWNER_CANDIDATES = sorted(
    set(EXPECTED_CURRENT_ROUTE_REFS + [COMPOUND_ADJECTIVE_OWNER])
)
MISSING_EXACT_OWNER_CANDIDATES = sorted(
    set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES) - set(EXPECTED_CURRENT_ROUTE_REFS)
)

OFFICIAL_BRANCHES = [
    {
        "branch": "pol_polu",
        "fipi_wording": "нормы слитного и дефисного написания пол- и полу- со словами",
        "candidate_owner_refs": ["school-pol-polu-writing-boundary"],
    },
    {
        "branch": "compound_adjectives",
        "fipi_wording": "правописание сложных имён прилагательных",
        "candidate_owner_refs": [COMPOUND_ADJECTIVE_OWNER],
    },
    {
        "branch": "numerals",
        "fipi_wording": "слитное, раздельное, дефисное написание числительных",
        "candidate_owner_refs": ["school-numeral-orthography-base"],
    },
    {
        "branch": "pronouns",
        "fipi_wording": "слитное, раздельное и дефисное написание местоимений",
        "candidate_owner_refs": [CURRENT_PRONOUN_PARTICLE_OWNER],
        "authority_note": "The former narrow indefinite-pronoun identity was explicitly absorbed by this current canonical parent in authority 255; the parent retains кое-/кой-, -то/-либо/-нибудь and preposition-insertion branches.",
    },
    {
        "branch": "adverbs",
        "fipi_wording": "слитное, раздельное и дефисное написание наречий",
        "candidate_owner_refs": ["school-adverb-solid-hyphen-separate-system"],
    },
    {
        "branch": "derived_prepositions",
        "fipi_wording": "правописание производных предлогов",
        "candidate_owner_refs": ["school-preposition-solid-hyphen-separate-base"],
    },
    {
        "branch": "conjunctions",
        "fipi_wording": "правописание союзов",
        "candidate_owner_refs": ["school-conjunction-solid-separate-spelling-base"],
    },
    {
        "branch": "particles_by_li_zhe",
        "fipi_wording": "правописание частиц бы, ли, же с другими словами",
        "candidate_owner_refs": [CURRENT_PRONOUN_PARTICLE_OWNER],
    },
    {
        "branch": "particles_to_taki_ka",
        "fipi_wording": "дефисное написание частиц -то, -таки, -ка",
        "candidate_owner_refs": [CURRENT_PRONOUN_PARTICLE_OWNER],
    },
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _decision_by_unit(audit: dict[str, Any], unit_id: str) -> dict[str, Any]:
    rows = [
        row
        for row in audit.get("decisions") or []
        if isinstance(row, dict) and row.get("unit_id") == unit_id
    ]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one current-norm audit decision for {unit_id}")
    return rows[0]


def build_review() -> dict[str, Any]:
    pronoun_bank = load_json(PRONOUN_BANK)
    norm_audit = load_json(CURRENT_NORM_AUDIT)
    consolidation = load_json(SEMANTIC_CONSOLIDATION)
    wave_d = load_json(WAVE_D)
    overlay = load_json(OGE_OVERLAY)
    inventory = load_json(IDENTITY_INVENTORY)

    route_rows = [
        row
        for row in overlay.get("orthography_codifier_overlay") or []
        if isinstance(row, dict) and str(row.get("position")) == TARGET_CODE
    ]
    if len(route_rows) != 1:
        raise ValueError("OGE 6.8 overlay row must exist exactly once")
    historical_route = route_rows[0]
    if historical_route.get("topic") != TARGET_TOPIC or historical_route.get("classification") != "EXAM_ONLY_COMPOSITE":
        raise ValueError("OGE 6.8 historical route authority drift")
    historical_owners = [str(value) for value in historical_route.get("owners") or []]
    if historical_owners != EXPECTED_HISTORICAL_OVERLAY_OWNERS:
        raise ValueError("OGE 6.8 historical owner/placeholder frontier drift")

    objects = [item for item in inventory.get("objects") or [] if isinstance(item, dict)]
    current_rows = [
        item
        for item in objects
        if item.get("object_key") == "oge_2026_orthography_route::oge-2026-orthography-6-8"
    ]
    if len(current_rows) != 1:
        raise ValueError("OGE 6.8 identity-inventory route must exist exactly once")
    current_route = current_rows[0]
    current_refs = [str(ref) for ref in current_route.get("current_semantic_refs") or []]
    if current_refs != EXPECTED_CURRENT_ROUTE_REFS:
        raise ValueError("OGE 6.8 current inventory route refs drifted")

    canonical_rows = {
        str(item.get("source_id")): item
        for item in objects
        if item.get("source_system") == "school_canonical"
        and str(item.get("source_id") or "").startswith("school-")
    }
    missing_inventory = [ref for ref in SOURCE_BOUND_EXACT_OWNER_CANDIDATES if ref not in canonical_rows]
    if missing_inventory:
        raise ValueError("source-supported 6.8 candidate missing from canonical inventory: " + ",".join(missing_inventory))
    for ref in SOURCE_BOUND_EXACT_OWNER_CANDIDATES:
        row = canonical_rows[ref]
        if row.get("authority_status") != "current" or row.get("review_status") != "reviewed":
            raise ValueError(f"6.8 candidate not current/reviewed: {ref}")
        if row.get("audit_classification") != "CANONICAL_SCHOOL_IDENTITY":
            raise ValueError(f"6.8 candidate is not canonical school identity: {ref}")
        if row.get("current_semantic_refs") != [ref]:
            raise ValueError(f"6.8 canonical self-ref drift: {ref}")

    bank_units = {
        str(row.get("unit_id")): row
        for row in pronoun_bank.get("canonical_units") or []
        if isinstance(row, dict)
    }
    narrow_pronoun = bank_units.get(ABSORBED_INDEFINITE_PRONOUN_ID)
    if not narrow_pronoun:
        raise ValueError("historical indefinite-pronoun identity missing from canonical pronoun bank")
    members = {str(value) for value in narrow_pronoun.get("members") or []}
    contrasts = {str(value) for value in narrow_pronoun.get("contrast_members") or []}
    if not {"кое-кто", "кто-то", "кто-либо", "кто-нибудь"}.issubset(members):
        raise ValueError("historical indefinite-pronoun hyphen model drift")
    if not {"кое у кого", "кое с кем"}.issubset(contrasts):
        raise ValueError("historical indefinite-pronoun preposition boundary drift")

    norm_decision = _decision_by_unit(norm_audit, ABSORBED_INDEFINITE_PRONOUN_ID)
    if norm_decision.get("disposition") != "CONFIRMED_AND_NORMATIVE_SCOPE_BROADENED_NO_COUNT_CHANGE":
        raise ValueError("indefinite-pronoun current-norm confirmation drift")
    if norm_decision.get("keep_identity") is not True or norm_decision.get("count_effect") != 0:
        raise ValueError("indefinite-pronoun current-norm checkpoint semantics drift")

    scope = consolidation.get("scope") or {}
    if "221-RUSSIAN-SCHOOL-CANONICAL-COMPLETENESS-CURRENT-NORM-AUDIT-WAVE3-ADVERBS-PRONOUNS-HYPHEN-v0.1.json" not in (scope.get("audit_wave_refs") or []):
        raise ValueError("239 consolidation no longer consumes 221 pronoun audit")
    if (consolidation.get("count_arithmetic") or {}).get("active_school_canonical_total") != 137:
        raise ValueError("239 active semantic baseline drift")

    particle_parent = (wave_d.get("O38_nonnegative_particles") or {}).get("new_unit") or {}
    if particle_parent.get("unit_id") != CURRENT_PRONOUN_PARTICLE_OWNER:
        raise ValueError("255 particle parent identity drift")
    if particle_parent.get("absorbs") != [ABSORBED_INDEFINITE_PRONOUN_ID]:
        raise ValueError("255 indefinite-pronoun absorption lineage drift")
    branches = {str(value) for value in particle_parent.get("branches") or []}
    required_parent_branches = {
        "кое-/кой-, -то, -либо, -нибудь with pronominal words",
        "preposition inserted after кое-/кой- breaks the hyphenated form: кое у кого, кое с кем",
    }
    if not required_parent_branches.issubset(branches):
        raise ValueError("255 current parent no longer preserves pronoun branches")
    if ABSORBED_INDEFINITE_PRONOUN_ID in canonical_rows:
        raise ValueError("absorbed indefinite-pronoun identity unexpectedly reappeared as current canonical identity")

    negative = bank_units.get(NEGATIVE_PRONOUN_NONOWNER)
    if not negative:
        raise ValueError("negative-pronoun boundary identity missing from canonical pronoun bank")
    if COMPOUND_NOUN_NONOWNER not in canonical_rows:
        raise ValueError("compound-noun nonowner boundary missing from canonical inventory")

    source_supported_current = sorted(set(current_refs) & set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES))
    nonexact_current = sorted(set(current_refs) - set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES))
    missing_exact = sorted(set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES) - set(current_refs))
    if source_supported_current != sorted(EXPECTED_CURRENT_ROUTE_REFS):
        raise ValueError("OGE 6.8 supported-current exact set drift")
    if nonexact_current:
        raise ValueError("OGE 6.8 current route unexpectedly contains nonexact refs")
    if missing_exact != MISSING_EXACT_OWNER_CANDIDATES:
        raise ValueError("OGE 6.8 missing exact-owner set drift")

    branch_refs = {ref for branch in OFFICIAL_BRANCHES for ref in branch["candidate_owner_refs"]}
    if branch_refs != set(SOURCE_BOUND_EXACT_OWNER_CANDIDATES):
        raise ValueError("official 6.8 branch-to-owner frontier does not match unique candidate set")

    return {
        "schema_version": "0.2.0",
        "status": "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION",
        "authority_issue": 161,
        "scope": "OGE_2026_ORTHOGRAPHY_CODE_6_8_SOLID_HYPHEN_SEPARATE_SOURCE_BOUND_FRONTIER",
        "official_source": {
            "document": "ФИПИ. Навигатор самостоятельной подготовки к ОГЭ-2026. Русский язык. Орфография",
            "url": FIPI_NAVIGATOR_URL,
            "retrieved_for_review": "2026-09-01",
            "content_code": TARGET_CODE,
            "source_boundary_policy": "Only the nine explicit 6.8 branches are in this frontier. The official 6.9 line separately owns pronouns with НЕ/НИ, and 6.13 separately owns compound/abbreviated-word spelling; neither may be imported into 6.8 by a broad historical placeholder.",
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
        "pronoun_authority_lineage": {
            "historical_identity": ABSORBED_INDEFINITE_PRONOUN_ID,
            "current_norm_audit_authority": "221",
            "semantic_consolidation_authority": "239",
            "absorption_authority": "255",
            "current_canonical_parent": CURRENT_PRONOUN_PARTICLE_OWNER,
            "historical_identity_is_current_inventory_member": False,
            "semantic_reopen_required": False,
            "reason": "221 confirmed the narrow identity inside the 137 checkpoint; 239 retained that checkpoint semantic set; 255 explicitly absorbed the narrow identity into the current nonnegative-particle spelling parent while preserving the pronoun hyphen/preposition branches. The current inventory correctly contains the parent and not the absorbed child.",
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
            "exact_route_ready_now": True,
            "next_atomic_action": "Create an additive current-launch 6.8 route supersession with exactly the seven proven current canonical owners and zero placeholders. Do not mutate historical 265/273 evidence in place and do not claim object/component acceptance until independent component-specific evidence is separately audited.",
        },
        "boundary_notes": [
            {
                "boundary": "pronouns",
                "decision": "USE_CURRENT_ABSORPTION_PARENT_FOR_6_8",
                "historical_identity": ABSORBED_INDEFINITE_PRONOUN_ID,
                "owner": CURRENT_PRONOUN_PARTICLE_OWNER,
                "reason": "Authority 255 explicitly absorbed the formerly narrow indefinite-pronoun identity into the current canonical parent and preserved both the hyphenated кое-/кой-/-то/-либо/-нибудь branch and the preposition-insertion separation branch.",
            },
            {
                "boundary": "negative_pronouns",
                "decision": "NONOWNER_FOR_6_8_BELONGS_TO_6_9",
                "owner": NEGATIVE_PRONOUN_NONOWNER,
                "reason": "FIPI 6.9 explicitly places spelling of pronouns with НЕ and НИ under НЕ/НИ, so the historical combined negative/indefinite placeholder must not pull this identity into 6.8.",
            },
            {
                "boundary": "compound_nouns",
                "decision": "NONOWNER_FOR_6_8_BELONGS_TO_6_13",
                "owner": COMPOUND_NOUN_NONOWNER,
                "reason": "FIPI 6.8 explicitly names complex adjectives, while 6.13 separately names compound and abbreviated words. The broad historical compound noun/adjective placeholder therefore resolves to the adjective owner for 6.8, not the compound-noun owner.",
            },
        ],
        "acceptance_boundary": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "new_school_identities": 0,
            "false_exact_mastery": 0,
            "learner_audio_persisted_bytes": 0,
            "production_peis_writes": 0,
            "public_traffic": False,
            "provider_execution": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    review = build_review()
    payload = json.dumps(review, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    frontier = review["source_bound_frontier"]
    boundary = review["acceptance_boundary"]
    print("OGE_6_8_SOLID_HYPHEN_SEPARATE_SOURCE_BOUND_FRONTIER=PASS")
    print(f"OFFICIAL_BRANCHES={frontier['official_branch_count']}")
    print(f"UNIQUE_EXACT_OWNER_CANDIDATES={frontier['unique_exact_owner_candidate_count']}")
    print(f"CURRENT_ROUTE_REFS={len(review['identity_inventory_truth']['current_semantic_refs'])}")
    print(f"CURRENT_SOURCE_SUPPORTED_EXACT_CANDIDATES={frontier['current_source_supported_exact_candidate_count']}")
    print(f"MISSING_EXACT_OWNER_CANDIDATES={frontier['missing_exact_owner_candidate_count']}")
    print(f"CURRENT_NONEXACT_ROUTE_REFS={frontier['current_nonexact_route_ref_count']}")
    print(f"LEGACY_PLACEHOLDERS={review['historical_overlay_truth']['placeholder_count']}")
    print(f"SCHOOL_REOPEN_REQUIRED={int(frontier['school_reopen_required'])}")
    print(f"EXACT_ROUTE_READY_NOW={int(frontier['exact_route_ready_now'])}")
    print(f"ABSORBED_PRONOUN_ID_CURRENT={int(review['pronoun_authority_lineage']['historical_identity_is_current_inventory_member'])}")
    print(f"SEMANTIC_ADMISSIONS={boundary['semantic_admissions']}")
    print(f"OBJECT_CLOSURES={boundary['object_closures']}")
    print(f"NEW_SCHOOL_IDENTITIES={boundary['new_school_identities']}")
    print(f"FALSE_EXACT_MASTERY={boundary['false_exact_mastery']}")
    print(f"LEARNER_AUDIO_PERSISTENCE={boundary['learner_audio_persisted_bytes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
