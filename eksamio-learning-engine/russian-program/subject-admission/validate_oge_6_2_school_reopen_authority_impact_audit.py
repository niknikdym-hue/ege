#!/usr/bin/env python3
"""Validate the bounded OGE-2026 6.2 school-reopen/denominator impact audit.

This gate proves that the single source-bound gap requires a governed school-layer
reopen, but deliberately does not admit the identity or mutate 265/273/exact-component
authority. It is a pre-materialization fail-closed gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[2]
ADMISSION = Path(__file__).resolve().parent
AUDIT = ADMISSION / "RUSSIAN-OGE-6.2-SCHOOL-REOPEN-AUTHORITY-IMPACT-AUDIT-v0.1.json"
WAVE_A1 = ENGINE / "247-RUSSIAN-SCHOOL-CANONICAL-PRIMARY-COMPLETENESS-WAVE-A1-MATERIALIZATION-v0.1.json"
REOPEN_AUDIT = ENGINE / "262-RUSSIAN-FIPI-2026-SCHOOL-REOPEN-GAP-AUDIT-v0.1.json"
REOPEN_MATERIALIZATION = ENGINE / "263-RUSSIAN-SCHOOL-FIPI-REOPEN-MATERIALIZATION-v0.1.json"
OVERLAY = ENGINE / "265-RUSSIAN-FIPI-2026-OGE-ROUTE-OVERLAY-v0.1.json"
REFREEZE = ENGINE / "266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"
INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
EXACT = ADMISSION / "RUSSIAN-OGE-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
PROPOSED = "school-root-consonant-dictionary-unverifiable"


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


def one(rows: list[dict], key: str, value: str) -> dict:
    matches = [row for row in rows if row.get(key) == value]
    assert len(matches) == 1, f"expected exactly one {key}={value}, got {len(matches)}"
    return matches[0]


def main() -> None:
    audit = load(AUDIT)
    wave = load(WAVE_A1)
    reopen = load(REOPEN_AUDIT)
    materialized = load(REOPEN_MATERIALIZATION)
    overlay = load(OVERLAY)
    refreeze = load(REFREEZE)
    inventory = load(INVENTORY)
    exact = load(EXACT)

    assert audit["status"] == "BOUNDED_SCHOOL_REOPEN_REQUIRED_NO_ADMISSION"
    assert audit["target"]["content_code"] == "6.2"
    assert audit["target"]["proposed_identity"] == PROPOSED

    # Existing canonical boundaries prove that no neighbouring verification identity
    # may be stretched to hide the dictionary-controlled consonant branch.
    voiced = one(wave["canonical_units"], "unit_id", "school-root-voiced-voiceless-consonant-verification")
    unpron = one(wave["canonical_units"], "unit_id", "school-unpronounceable-consonant-verification")
    assert "dictionary-control nonverifiable cases remain separate" in voiced["decision_model"]
    assert "lexical nonverifiable spellings remain dictionary-controlled" in unpron["decision_model"]
    gap = audit["gap_proof"]
    assert gap["official_fipi_branch_present"] is True
    assert gap["exact_current_canonical_owner_count"] == 0
    assert gap["scope_expansion_without_new_identity_is_exact"] is False
    assert gap["absorption_into_existing_identity_is_exact"] is False
    assert gap["new_bounded_school_identity_required"] is True

    # Apply the existing school-reopen governance rather than inventing a new policy.
    assert reopen["entry_school_denominator"] == 179
    assert "A school reopen candidate exists only when" in reopen["audit_principle"]
    assert materialized["count_assertion"]["school_denominator_before_reopen"] == 179
    assert materialized["count_assertion"]["interim_school_denominator_after_reopen"] == 185
    assert refreeze["final_school_canonical_denominator"] == 185
    assert refreeze["final_source_closure"]["final_unowned_official_school_orthography_topics"] == 0
    assert refreeze["oge_2026_overlay_summary"]["school_reopen_candidates"] == 0

    policy = audit["reopen_policy_application"]
    assert policy["policy_satisfied"] is True
    assert policy["decision"] == "REOPEN_REQUIRED"
    assert policy["current_185_zero_gap_claim_exact_for_6_2"] is False
    assert policy["historical_266_file_mutated_by_this_audit"] is False

    impact = audit["denominator_impact"]
    assert impact == {
        "school_denominator_before": 185,
        "new_independent_school_identities_if_materialized": 1,
        "absorptions": 0,
        "scope_only_expansions": 0,
        "projected_school_denominator_after_materialization": 186,
        "projected_denominator_is_current_authority": False,
        "count_effect_applied_now": 0,
    }

    contract = audit["proposed_identity_contract"]
    assert contract["unit_id"] == PROPOSED
    assert contract["unit_type"] == "dictionary_control_decision"
    assert contract["status"] == "PROPOSED_REOPEN_TARGET_NOT_ADMITTED"
    assert contract["fipi_routes"] == ["OGE-2026-orthography-6.2"]
    for forbidden in ["checkable voiced/voiceless", "unpronounceable-consonant", "double-consonant", "individual lexical-item"]:
        assert forbidden in contract["ownership_boundary"]

    # Pre-materialization truth must remain fail-closed in current branch authority.
    school_rows = [row for row in walk(inventory) if row.get("source_system") == "school_canonical"]
    assert inventory["active_school_identity_count_observed"] == 185
    assert len([row for row in school_rows if row.get("source_id") == PROPOSED]) == 0
    route = one(overlay["orthography_codifier_overlay"], "position", "6.2")
    assert "alternating-root families from file 248" in route["owners"]
    assert "double-consonant root systems from file 249" in route["owners"]
    assert PROPOSED not in route["owners"]
    assert [row for row in exact.get("decisions", []) if row.get("content_code") == "6.2"] == []

    atomic = audit["atomic_materialization_gate"]
    assert atomic["ready_to_materialize_after_this_audit"] is True
    assert atomic["must_be_one_atomic_authority_change"] is True
    assert atomic["partial_sync_allowed"] is False
    assert atomic["exact_6_2_acceptance_before_atomic_sync"] is False
    assert len(atomic["required_sync"]) == 5

    launch = audit["launch_accounting"]
    assert launch["semantic_admissions_this_audit"] == 0
    assert launch["object_closures_this_audit"] == 0
    assert launch["false_exact_mastery_admissions"] == 0
    assert launch["bounded_ru_semantic_count_change"] == 0
    assert launch["russian_content_status"] == "BLOCKED_SUBJECT"
    assert audit["safety"]["learner_audio_persistence"] == 0
    assert audit["safety"]["provider_execution"] is False
    assert audit["safety"]["production_peis_write"] is False
    assert audit["safety"]["public_traffic"] is False

    normalized = json.dumps(audit, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(normalized).hexdigest()
    print("OGE_6_2_SCHOOL_REOPEN_AUTHORITY_IMPACT_AUDIT=PASS")
    print("REOPEN_DECISION=REOPEN_REQUIRED")
    print("CURRENT_SCHOOL_DENOMINATOR=185")
    print("PROJECTED_AFTER_ATOMIC_MATERIALIZATION=186")
    print("COUNT_EFFECT_APPLIED_NOW=0")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("AUDIT_NORMALIZED_SHA256=" + digest)


if __name__ == "__main__":
    main()
