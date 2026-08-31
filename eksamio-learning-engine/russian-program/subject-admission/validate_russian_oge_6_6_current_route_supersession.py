#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
BASE_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CURRENT_FREEZE = ENGINE / "277-RUSSIAN-SCHOOL-CURRENT-LAUNCH-REFREEZE-v1.1.json"
CURRENT_ROUTE = ENGINE / "278-RUSSIAN-FIPI-2026-OGE-6.6-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
FRONTIER_BUILDER = HERE / "build_oge_6_6_suffix_source_bound_frontier_review.py"

EXPECTED_OWNERS = [
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
EXPECTED_REPLACED = [
    "school-unstressed-suffix-vowel-verification-fixed-patterns",
    "school-verb-enet-derived-from-noun",
    "school-verb-stressed-va-boundary",
]
EXPECTED_ADDED = [
    "school-adjective-k-sk-derivational-boundary",
    "school-noun-agent-suffix-chik-shchik-soft-sign",
    "school-noun-suffix-ek-ik-vowel-retention",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    inventory = load(BASE_INVENTORY)
    freeze = load(CURRENT_FREEZE)
    route = load(CURRENT_ROUTE)
    frontier = runpy.run_path(str(FRONTIER_BUILDER))["build_review"]()

    assert inventory["active_school_identity_count_observed"] == 185
    base_rows = [
        row for row in inventory["objects"]
        if row.get("source_system") == "school_canonical"
        and row.get("authority_status") == "current"
        and row.get("audit_classification") == "CANONICAL_SCHOOL_IDENTITY"
        and row.get("review_status") == "reviewed"
    ]
    base_ids = {row["source_id"] for row in base_rows}
    assert len(base_ids) == 185
    assert set(EXPECTED_OWNERS) <= base_ids

    assert freeze["current_school_canonical_denominator"] == 186

    source_frontier = frontier["source_bound_frontier"]
    assert frontier["status"] == "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION"
    assert source_frontier["official_branch_count"] == 12
    assert source_frontier["unique_exact_owner_candidates"] == EXPECTED_OWNERS
    assert source_frontier["unique_exact_owner_candidate_count"] == 10
    assert source_frontier["missing_exact_owner_candidates_from_current_route"] == EXPECTED_ADDED
    assert source_frontier["current_nonexact_route_refs"] == EXPECTED_REPLACED
    assert source_frontier["school_reopen_required"] is False

    assert route["status"] == "CURRENT_OGE_2026_6_6_ROUTE_SUPERSESSION_EXACT_OWNER_FRONTIER_NO_OBJECT_ADMISSION"
    assert route["position"] == "6.6"
    assert route["classification"] == "SCHOOL_IDENTITY_ROUTE"
    assert route["school_baseline_for_route"] == 186
    assert route["exact_owner_refs"] == EXPECTED_OWNERS
    assert len(route["exact_owner_refs"]) == len(set(route["exact_owner_refs"])) == 10

    accounting = route["owner_accounting"]
    assert accounting["official_fipi_branches"] == 12
    assert accounting["owner_count"] == 10
    assert accounting["reused_current_canonical"] == 10
    assert accounting["newly_materialized_current_canonical"] == 0
    assert accounting["school_reopen_required"] == 0
    assert accounting["legacy_family_placeholders"] == 0
    assert accounting["unresolved_owners"] == 0
    assert accounting["replaced_nonexact_current_refs"] == EXPECTED_REPLACED
    assert accounting["added_source_supported_exact_refs"] == EXPECTED_ADDED

    supersession = route["supersedes_for_current_launch_truth"]
    assert supersession["historical_base_mutated"] is False
    assert supersession["scope"] == "OGE orthography route 6.6 owner refs only"

    mastery = route["mastery_boundary"]
    assert mastery["route_attempt_can_emit_exact_component_mastery"] is False
    assert mastery["component_specific_independent_evidence_required"] is True
    assert mastery["exact_owner_frontier_is_not_object_acceptance"] is True

    effect = route["admission_effect"]
    assert effect == {
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "false_exact_mastery_admissions": 0,
    }

    safety = route["safety"]
    assert safety["accepted_demo_or_scorer_change"] is False
    assert safety["tilda_change"] is False
    assert safety["learner_audio_persistence"] == 0
    assert safety["production_peis_write"] is False
    assert safety["provider_execution"] is False
    assert safety["public_traffic"] is False
    assert safety["real_payment_or_refund"] is False
    assert safety["real_message_delivery"] is False

    print("RUSSIAN_OGE_6_6_CURRENT_ROUTE_SUPERSESSION=PASS")
    print("CURRENT_SCHOOL_DENOMINATOR=186")
    print("OFFICIAL_BRANCHES=12")
    print("EXACT_OWNER_FRONTIER=10")
    print("REUSED_CURRENT_CANONICAL_OWNERS=10")
    print("NEW_SCHOOL_CANONICAL_IDENTITIES=0")
    print("OBJECT_CLOSURES=0")
    print("FALSE_EXACT_MASTERY=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")


if __name__ == "__main__":
    main()
