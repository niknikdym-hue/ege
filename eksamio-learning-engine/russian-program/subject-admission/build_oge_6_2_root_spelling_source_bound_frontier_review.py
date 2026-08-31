#!/usr/bin/env python3
"""Build a deterministic, fail-closed source-bound review for OGE-2026 code 6.2.

The official FIPI 2026 frontier is narrower than the historical route placeholders.
This reviewer resolves the complete 15-family alternating-root placeholder to exact
current reviewed school owners, while refusing to stretch existing identities over
still-unproven uncheckable-consonant and numeral-double branches.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]
ADMISSION = Path(__file__).resolve().parent
OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
WAVE_A1 = ENGINE / "247-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A1-MATERIALIZATION-v0.1.json"
ALTERNATING = ENGINE / "248-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A2-ALTERNATING-ROOTS-NORMALIZATION-v0.1.json"
DOUBLES = ENGINE / "249-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A3-E-E-Y-DOUBLE-CONSONANTS-v0.1.json"
NUMERALS = ENGINE / "252-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-B-O17-O25-v0.1.json"
REFREEZE = ENGINE / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"
EXACT = ADMISSION / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"

OFFICIAL_SOURCE = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"
ALTERNATING_FAMILY_OWNER = {
    "lag-lozh": "school-lag-lozh-polog-exception",
    "rast-rashch-ros": "school-rast-rashch-ros-exception-set",
    "gar-gor": "school-gor-gar-rare-exception-set",
    "zar-zor": "school-zar-zor-stress-alternation",
    "klan-klon": "school-klan-klon-stress-alternation",
    "skak-skoch": "school-skak-skoch-exception-set",
    "ber-bir": "school-i-e-alternating-verb-roots-stressed-a",
    "blest-blist": "school-i-e-alternating-verb-roots-stressed-a",
    "der-dir": "school-i-e-alternating-verb-roots-stressed-a",
    "zheg-zhig": "school-i-e-alternating-verb-roots-stressed-a",
    "mer-mir": "school-i-e-alternating-verb-roots-stressed-a",
    "per-pir": "school-i-e-alternating-verb-roots-stressed-a",
    "stel-stil": "school-i-e-alternating-verb-roots-stressed-a",
    "ter-tir": "school-i-e-alternating-verb-roots-stressed-a",
    "kas-kos": "school-kas-kos-a-suffix-alternation",
}
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
EXPECTED_DOUBLE_SYSTEMS = [
    "school-double-consonants-russian-root-lexical",
    "school-double-consonants-morpheme-junction",
    "school-double-consonants-borrowed-root-dictionary",
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


def source_record(rows: list[dict], key: str, value: str) -> dict:
    matches = [row for row in rows if row.get(key) == value]
    assert len(matches) == 1, f"expected one source record {key}={value}, got {len(matches)}"
    return matches[0]


def build() -> dict:
    overlay = load(OVERLAY)
    inventory = load(INVENTORY)
    wave_a1 = load(WAVE_A1)
    alternating = load(ALTERNATING)
    doubles = load(DOUBLES)
    numerals = load(NUMERALS)
    refreeze = load(REFREEZE)
    exact = load(EXACT)

    positions = [row for row in overlay["orthography_codifier_overlay"] if row.get("position") == "6.2"]
    assert len(positions) == 1
    route = positions[0]
    owners = route.get("owners", [])
    assert all(ref in owners for ref in EXPECTED_OVERLAY_EXACT)
    assert all(ref in owners for ref in EXPECTED_PLACEHOLDERS)

    assert len(ALTERNATING_FAMILY_OWNER) == 15
    alternating_unique_owners = sorted(set(ALTERNATING_FAMILY_OWNER.values()))
    assert len(alternating_unique_owners) == 8
    for owner in alternating_unique_owners:
        canonical_record(inventory, owner)

    # Prove the eight exact current owners from the structured source-normalization file,
    # not from lexical/fuzzy similarity.
    expansions = alternating["existing_id_scope_expansions"]
    assert source_record(expansions, "unit_id", "school-lag-lozh-polog-exception")["new_semantic_scope"].startswith("LAG/LOG/LOZH")
    assert source_record(expansions, "unit_id", "school-rast-rashch-ros-exception-set")["new_semantic_scope"].startswith("RAST/RASHCH/ROS")
    assert source_record(expansions, "unit_id", "school-gor-gar-rare-exception-set")["new_semantic_scope"].startswith("GAR/GOR")
    whole = alternating["already_whole_existing_owners"]
    skak = source_record(whole, "owner", "school-skak-skoch-exception-set")
    assert skak["source_branch"] == "СКАК/СКОК/СКАЧ/СКОЧ"
    new_units = alternating["new_canonical_units"]
    for owner in [
        "school-zar-zor-stress-alternation",
        "school-klan-klon-stress-alternation",
        "school-kas-kos-a-suffix-alternation",
    ]:
        source_record(new_units, "unit_id", owner)
    ie_group = source_record(new_units, "unit_id", "school-i-e-alternating-verb-roots-stressed-a")
    for token in ["БЕР/БИР", "БЛЕСТ/БЛИСТ", "ДЕР/ДИР", "ЖЕГ/ЖИГ", "МЕР/МИР", "ПЕР/ПИР", "СТЕЛ/СТИЛ", "ТЕР/ТИР"]:
        assert token in ie_group["source_branch"]

    voiced = source_record(wave_a1["canonical_units"], "unit_id", "school-root-voiced-voiceless-consonant-verification")
    unpron = source_record(wave_a1["canonical_units"], "unit_id", "school-unpronounceable-consonant-verification")
    assert "dictionary-control nonverifiable cases remain separate" in voiced["decision_model"]
    assert "lexical nonverifiable spellings remain dictionary-controlled" in unpron["decision_model"]

    double_units = doubles["resolution_O08"]["canonical_units"]
    assert [row["unit_id"] for row in double_units] == EXPECTED_DOUBLE_SYSTEMS
    for owner in EXPECTED_DOUBLE_SYSTEMS:
        canonical_record(inventory, owner)

    numeral = source_record(numerals["O25_numeral_orthography"]["new_units"], "unit_id", "school-numeral-orthography-base")
    numeral_branches = numeral["branches"]
    assert numeral_branches == [
        "solid complex vs separate composite quantitative numerals",
        "internal Ь in 50–80 and 500–900",
        "ноль/нуль lexical distribution",
        "compound/composite ordinal writing",
        "fractional numeral writing",
    ]
    assert not any("double" in branch.lower() or "двойн" in branch.lower() for branch in numeral_branches)
    canonical_record(inventory, "school-numeral-orthography-base")

    assert refreeze["final_source_closure"]["final_unowned_official_school_orthography_topics"] == 0
    assert refreeze["oge_2026_overlay_summary"]["school_reopen_candidates"] == 0

    exact_6_2 = [row for row in exact.get("decisions", []) if row.get("content_code") == "6.2"]
    assert exact_6_2 == [], "6.2 must remain unaccepted while two exact owner branches are unresolved"

    unresolved = [
        {
            "branch": "uncheckable_consonants",
            "status": "NO_EXPLICIT_EXACT_CURRENT_OWNER_PROVEN",
            "reason": "Current verification identities explicitly keep nonverifiable consonant spellings outside their mastered decision scope; the route overlay does not name a separate exact owner.",
        },
        {
            "branch": "double_consonants_in_numeral_names",
            "status": "NO_EXPLICIT_EXACT_CURRENT_OWNER_PROVEN",
            "reason": "The official FIPI branch is numeral-specific, while file 249 owns broader double-consonant systems and the current numeral-orthography identity has no double-consonant branch.",
        },
    ]

    result = {
        "schema_version": "0.2.0",
        "status": "SOURCE_BOUND_FRONTIER_PARTIALLY_RESOLVED_NO_ADMISSION",
        "target": {
            "exam": "OGE-2026 Russian",
            "content_code": "6.2",
            "topic": "root spelling",
        },
        "official_source_truth": {
            "source": OFFICIAL_SOURCE,
            "alternating_root_families_exact": list(ALTERNATING_FAMILY_OWNER),
            "alternating_root_family_count": len(ALTERNATING_FAMILY_OWNER),
            "other_root_vowel_scope": ["checked unstressed vowels", "unchecked/dictionary vowels"],
            "root_consonant_scope": ["checkable consonants", "uncheckable consonants", "unpronounceable consonants"],
            "special_root_scope": ["O/YO after sibilants in the root", "Y/I after TS in the root"],
            "double_consonant_scope": "double consonants in numeral names",
            "generic_double_consonant_scope_claimed": False,
        },
        "current_repository_truth": {
            "overlay_explicit_exact_refs": EXPECTED_OVERLAY_EXACT,
            "overlay_unresolved_placeholders": EXPECTED_PLACEHOLDERS,
            "exact_component_acceptance_present": False,
            "refreeze_claims_zero_unowned_orthography_topics": True,
            "refreeze_claims_zero_oge_school_reopen_candidates": True,
        },
        "alternating_root_owner_audit": {
            "status": "RESOLVED_EXACT_REUSE_FIRST",
            "official_family_count": 15,
            "resolved_family_count": 15,
            "unresolved_family_count": 0,
            "unique_current_reviewed_owner_count": 8,
            "family_owner_map": ALTERNATING_FAMILY_OWNER,
            "exact_current_reviewed_owner_refs": alternating_unique_owners,
            "keyword_or_fuzzy_mapping_used": False,
        },
        "remaining_source_boundary": {
            "unresolved_branch_count": len(unresolved),
            "unresolved_branches": unresolved,
            "uncheckable_consonant_verification_identities_may_not_be_stretched": True,
            "numeral_orthography_has_double_consonant_branch": False,
            "generic_double_system_refs": EXPECTED_DOUBLE_SYSTEMS,
            "legacy_double_consonant_placeholder_is_source_inexact": True,
        },
        "admission_policy": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0,
            "remove_alternating_placeholder_now": False,
            "remove_double_placeholder_now": False,
            "accept_6_2_exact_component_now": False,
            "keyword_or_fuzzy_owner_mapping_allowed": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
        },
        "next_atomic_gate": {
            "required": [
                "resolve the official uncheckable-consonant branch without stretching verification identities beyond their explicit boundary",
                "resolve numeral-specific double consonants without treating generic double-consonant scope as exact numeral ownership",
                "only then atomically synchronize 265/273/exact-component authority and remove both legacy placeholders",
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
    print("ALTERNATING_FAMILIES_RESOLVED=15")
    print("ALTERNATING_UNIQUE_REUSED_OWNERS=8")
    print("SOURCE_BOUND_UNRESOLVED_BRANCHES=2")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")


if __name__ == "__main__":
    main()
