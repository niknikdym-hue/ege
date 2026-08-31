#!/usr/bin/env python3
"""Build deterministic fail-closed source-bound truth for OGE-2026 code 6.2.

No 6.2 admission is produced here. The reviewer resolves every reusable branch that
can be proved from current repository authorities and exposes any real canonical gap
instead of stretching a neighbouring identity or preserving a false closure claim.
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

FIPI_SOURCE = "https://doc.fipi.ru/navigator-podgotovki/navigator-oge/ru-9_6_orfografija.pdf"
LOPATIN_UNCHECKABLE_CONSONANTS = "https://orthographia.ru/orf.php?paragraph=pp80.php"
LOPATIN_DOUBLE_JUNCTION = "https://orthographia.ru/orf.php?paragraph=pp95.php"
ROSENTHAL_ROOT_CONSONANTS = "https://www.old-rozental.ru/orfografia.php?sid=10"
PROPOSED_UNCHECKABLE_OWNER = "school-root-consonant-dictionary-unverifiable"

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


def canonical_matches(inventory: object, source_id: str) -> list[dict]:
    return [
        row
        for row in walk(inventory)
        if row.get("source_system") == "school_canonical" and row.get("source_id") == source_id
    ]


def canonical_record(inventory: object, source_id: str) -> dict:
    matches = canonical_matches(inventory, source_id)
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

    routes = [row for row in overlay["orthography_codifier_overlay"] if row.get("position") == "6.2"]
    assert len(routes) == 1
    owners = routes[0].get("owners", [])
    assert all(ref in owners for ref in EXPECTED_OVERLAY_EXACT)
    assert all(ref in owners for ref in EXPECTED_PLACEHOLDERS)

    # Alternating roots: resolve the official 15-family list only through the
    # structured normalization authority and current reviewed canonical records.
    assert len(ALTERNATING_FAMILY_OWNER) == 15
    alternating_unique_owners = sorted(set(ALTERNATING_FAMILY_OWNER.values()))
    assert len(alternating_unique_owners) == 8
    for owner in alternating_unique_owners:
        canonical_record(inventory, owner)

    expansions = alternating["existing_id_scope_expansions"]
    assert source_record(expansions, "unit_id", "school-lag-lozh-polog-exception")["new_semantic_scope"].startswith("LAG/LOG/LOZH")
    assert source_record(expansions, "unit_id", "school-rast-rashch-ros-exception-set")["new_semantic_scope"].startswith("RAST/RASHCH/ROS")
    assert source_record(expansions, "unit_id", "school-gor-gar-rare-exception-set")["new_semantic_scope"].startswith("GAR/GOR")
    whole = alternating["already_whole_existing_owners"]
    assert source_record(whole, "owner", "school-skak-skoch-exception-set")["source_branch"] == "СКАК/СКОК/СКАЧ/СКОЧ"
    new_units = alternating["new_canonical_units"]
    for owner in ["school-zar-zor-stress-alternation", "school-klan-klon-stress-alternation", "school-kas-kos-a-suffix-alternation"]:
        source_record(new_units, "unit_id", owner)
    ie_group = source_record(new_units, "unit_id", "school-i-e-alternating-verb-roots-stressed-a")
    for token in ["БЕР/БИР", "БЛЕСТ/БЛИСТ", "ДЕР/ДИР", "ЖЕГ/ЖИГ", "МЕР/МИР", "ПЕР/ПИР", "СТЕЛ/СТИЛ", "ТЕР/ТИР"]:
        assert token in ie_group["source_branch"]

    # Uncheckable root consonants: prove that the two nearby verification identities
    # explicitly exclude the dictionary-controlled branch. No current canonical
    # record exists for the bounded dictionary decision itself.
    voiced = source_record(wave_a1["canonical_units"], "unit_id", "school-root-voiced-voiceless-consonant-verification")
    unpron = source_record(wave_a1["canonical_units"], "unit_id", "school-unpronounceable-consonant-verification")
    assert "dictionary-control nonverifiable cases remain separate" in voiced["decision_model"]
    assert "lexical nonverifiable spellings remain dictionary-controlled" in unpron["decision_model"]
    assert canonical_matches(inventory, PROPOSED_UNCHECKABLE_OWNER) == []

    # Numeral doubles: file 249's productive morpheme-junction owner explicitly
    # includes stem+suffix and cites Lopatin §§93-95. Lopatin §95 explicitly names
    # одиннадцать as double-н in a numeral. That is exact reuse, not the broad
    # Russian-root or borrowed-root double-consonant systems and not numeral-base.
    double_units = doubles["resolution_O08"]["canonical_units"]
    assert [row["unit_id"] for row in double_units] == EXPECTED_DOUBLE_SYSTEMS
    double_junction = source_record(double_units, "unit_id", "school-double-consonants-morpheme-junction")
    assert "stem + suffix" in double_junction["branches"]
    assert "Лопатин §§93-95" in double_junction["current_norm_locators"]
    canonical_record(inventory, "school-double-consonants-morpheme-junction")

    numeral = source_record(numerals["O25_numeral_orthography"]["new_units"], "unit_id", "school-numeral-orthography-base")
    numeral_branches = numeral["branches"]
    assert not any("double" in branch.lower() or "двойн" in branch.lower() for branch in numeral_branches)
    canonical_record(inventory, "school-numeral-orthography-base")

    # The old final-refreeze claims are retained as historical authority but are now
    # contradicted by the exact frontier: one official school decision has no exact
    # current owner. Do not silently preserve the 185 claim by stretching identities.
    assert refreeze["final_source_closure"]["final_unowned_official_school_orthography_topics"] == 0
    assert refreeze["oge_2026_overlay_summary"]["school_reopen_candidates"] == 0

    exact_6_2 = [row for row in exact.get("decisions", []) if row.get("content_code") == "6.2"]
    assert exact_6_2 == [], "6.2 must remain unaccepted while the canonical gap exists"

    result = {
        "schema_version": "0.3.0",
        "status": "SOURCE_BOUND_FRONTIER_ONE_CANONICAL_GAP_NO_ADMISSION",
        "target": {"exam": "OGE-2026 Russian", "content_code": "6.2", "topic": "root spelling"},
        "official_source_truth": {
            "fipi_source": FIPI_SOURCE,
            "alternating_root_family_count": 15,
            "root_consonant_scope": ["checkable consonants", "uncheckable consonants", "unpronounceable consonants"],
            "double_consonant_scope": "double consonants in numeral names",
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
        "numeral_double_consonant_owner_audit": {
            "status": "RESOLVED_EXACT_REUSE_FIRST",
            "exact_owner": "school-double-consonants-morpheme-junction",
            "repository_authority": "249-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A3-E-E-Y-DOUBLE-CONSONANTS-v0.1.json#resolution_O08",
            "current_norm_source": LOPATIN_DOUBLE_JUNCTION,
            "current_norm_fact": "Lopatin §95 explicitly gives double н in the numeral одиннадцать; file 249 includes §95 and stem+suffix in the exact productive owner scope.",
            "generic_russian_root_double_owner_used": False,
            "borrowed_root_double_owner_used": False,
            "numeral_orthography_base_used": False,
        },
        "uncheckable_consonant_gap": {
            "status": "PROVEN_CANONICAL_GAP_REQUIRES_BOUNDED_REOPEN_REVIEW",
            "official_fipi_branch_present": True,
            "nearby_verification_ids_explicitly_exclude_nonverifiable_cases": True,
            "exact_current_canonical_owner_count": 0,
            "proposed_identity": PROPOSED_UNCHECKABLE_OWNER,
            "proposed_identity_admitted": False,
            "source_locators": [ROSENTHAL_ROOT_CONSONANTS, LOPATIN_UNCHECKABLE_CONSONANTS],
            "current_norm_fact": "Lopatin §80 states that spelling of uncheckable consonants in roots is determined in dictionary order.",
            "refreeze_185_zero-gap_claim_can_be_treated_as_current_exact_truth": False,
        },
        "remaining_source_boundary": {
            "unresolved_branch_count": 1,
            "unresolved_branches": ["uncheckable_consonants"],
            "legacy_alternating_placeholder_resolved_but_not_removed_before_atomic_sync": True,
            "legacy_double_placeholder_resolved_but_not_removed_before_atomic_sync": True,
        },
        "admission_policy": {
            "semantic_admissions": 0,
            "object_closures": 0,
            "false_exact_mastery_admissions": 0,
            "accept_6_2_exact_component_now": False,
            "remove_6_2_placeholders_now": False,
            "route_attempt_can_emit_exact_component_mastery": False,
            "component_specific_independent_evidence_required": True,
        },
        "next_atomic_gate": {
            "required": [
                "audit denominator/authority impact of the proven uncheckable-consonant canonical gap",
                "materialize an exact current owner only if that bounded reopen passes source/current-norm and governance checks",
                "then atomically synchronize 265/273/exact-component authority and remove both legacy 6.2 placeholders",
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
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("OGE_6_2_SOURCE_BOUND_FRONTIER_REVIEW=PASS")
    print("STATUS=" + result["status"])
    print("ALTERNATING_FAMILIES_RESOLVED=15")
    print("ALTERNATING_UNIQUE_REUSED_OWNERS=8")
    print("NUMERAL_DOUBLE_BRANCH_RESOLVED=1")
    print("SOURCE_BOUND_UNRESOLVED_BRANCHES=1")
    print("PROVEN_CANONICAL_GAPS=1")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")


if __name__ == "__main__":
    main()
