#!/usr/bin/env python3
"""Build a deterministic, fail-closed source-bound review for OGE-2026 code 6.2.

This review intentionally does not admit 6.2. It captures the exact official FIPI
frontier and proves that the legacy double-consonant placeholder is broader/different
than the current official wording, so canonical synchronization must wait for a
complete reuse-first owner audit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]
ADMISSION = Path(__file__).resolve().parent
OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
EXACT = ADMISSION / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

OFFICIAL_SOURCE = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"
ALTERNATING_FAMILIES = [
    "lag-lozh",
    "rast-rashch-ros",
    "gar-gor",
    "zar-zor",
    "klan-klon",
    "skak-skoch",
    "ber-bir",
    "blest-blist",
    "der-dir",
    "zheg-zhig",
    "mer-mir",
    "per-pir",
    "stel-stil",
    "ter-tir",
    "kas-kos",
]
EXPECTED_OVERLAY_EXACT = [
    "school-root-vowel-stress-verification",
    "school-root-vowel-dictionary-unverifiable",
    "school-root-o-yo-after-sibilants-base",
    "school-root-i-y-after-ts-base",
    "school-root-voiced-voiceless-consonant-verification",
    "school-unpronounceable-consonant-verification",
]
EXPECTED_PLACEHOLDERS = [
    "alternating-root families from file 248",
    "double-consonant root systems from file 249",
]


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def canonical_record(inventory: object, source_id: str) -> dict:
    matches = [
        row
        for row in walk(inventory)
        if row.get("source_system") == "school_canonical" and row.get("source_id") == source_id
    ]
    assert len(matches) == 1, f"expected one active canonical record for {source_id}, got {len(matches)}"
    row = matches[0]
    assert row.get("authority_status") == "current"
    assert row.get("review_status") == "reviewed"
    assert row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
    return row


def build() -> dict:
    overlay = load(OVERLAY)
    inventory = load(INVENTORY)
    exact = load(EXACT)

    positions = [row for row in overlay["orthography_codifier_overlay"] if row.get("position") == "6.2"]
    assert len(positions) == 1
    route = positions[0]
    owners = route.get("owners", [])
    assert all(ref in owners for ref in EXPECTED_OVERLAY_EXACT)
    assert all(ref in owners for ref in EXPECTED_PLACEHOLDERS)

    # Three concrete current identities anchor the reuse-first frontier. We do not
    # infer the remaining alternating-family owners from names or fuzzy matching.
    kas_kos = canonical_record(inventory, "school-kas-kos-a-suffix-alternation")
    russian_double = canonical_record(inventory, "school-double-consonants-russian-root-lexical")
    numeral_base = canonical_record(inventory, "school-numeral-orthography-base")

    exact_6_2 = [row for row in exact.get("decisions", []) if row.get("content_code") == "6.2"]
    assert exact_6_2 == [], "6.2 must remain unaccepted while source-bound frontier is incomplete"

    result = {
        "schema_version": "0.1.0",
        "status": "SOURCE_BOUND_FRONTIER_REVIEW_INCOMPLETE_NO_ADMISSION",
        "target": {
            "exam": "OGE-2026 Russian",
            "content_code": "6.2",
            "topic": "root spelling",
        },
        "official_source_truth": {
            "source": OFFICIAL_SOURCE,
            "alternating_root_families_exact": ALTERNATING_FAMILIES,
            "alternating_root_family_count": len(ALTERNATING_FAMILIES),
            "other_root_vowel_scope": ["checked unstressed vowels", "unchecked/dictionary vowels"],
            "root_consonant_scope": ["checkable consonants", "uncheckable consonants", "unpronounceable consonants"],
            "special_root_scope": ["O/YO after sibilants in the root", "Y/I after TS in the root"],
            "double_consonant_scope": "double consonants in numeral names",
            "generic_russian_root_double_consonant_scope_claimed": False,
        },
        "current_repository_truth": {
            "overlay_explicit_exact_refs": EXPECTED_OVERLAY_EXACT,
            "overlay_unresolved_placeholders": EXPECTED_PLACEHOLDERS,
            "exact_component_acceptance_present": False,
            "reuse_anchors": {
                "kas_kos": kas_kos["source_id"],
                "russian_root_double_consonants": russian_double["source_id"],
                "numeral_orthography": numeral_base["source_id"],
            },
        },
        "source_boundary_findings": {
            "alternating_placeholder_requires_exact_family_owner_audit": True,
            "alternating_placeholder_official_family_count": 15,
            "kas_kos_exact_reuse_anchor_proven": True,
            "legacy_double_consonant_placeholder_is_source_inexact": True,
            "legacy_double_consonant_placeholder_text": "double-consonant root systems from file 249",
            "official_double_consonant_boundary": "numeral names only within code 6.2",
            "school_double_consonants_russian_root_lexical_cannot_be_admitted_from_6_2_source": True,
            "school_numeral_orthography_base_is_reuse_candidate_not_yet_scope_proven_for_double_consonants": True,
            "uncheckable_consonant_owner_requires_explicit_reuse_audit": True,
        },
        "admission_policy": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0,
            "remove_6_2_placeholders_now": False,
            "accept_6_2_exact_component_now": False,
            "keyword_or_fuzzy_owner_mapping_allowed": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
        },
        "next_atomic_gate": {
            "required": [
                "map all 15 official alternating families to exact current reviewed school identities or prove an explicit bounded composite owner",
                "resolve the official uncheckable-consonant branch to exact current reviewed school ownership",
                "prove the exact active owner for double consonants in numeral names without reusing generic root-double scope",
                "reach zero source-bound unclassified branches before changing 265/273 or exact-component acceptance",
            ]
        },
        "safety": {
            "production_integration": "HOLD",
            "accepted_demo_or_scorer_change": False,
            "learner_audio_persistence": 0,
            "provider_execution": False,
            "production_peis_write": False,
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = build()
    rendered = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    Path(args.output).write_text(rendered, encoding="utf-8")
    print("OGE_6_2_SOURCE_BOUND_FRONTIER_REVIEW=PASS")
    print("STATUS=" + result["status"])
    print("OFFICIAL_ALTERNATING_FAMILIES=15")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")


if __name__ == "__main__":
    main()
