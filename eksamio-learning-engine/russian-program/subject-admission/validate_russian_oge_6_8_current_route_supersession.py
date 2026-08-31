#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
BASE_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CURRENT_FREEZE = ENGINE / "277-RUSSIAN-SCHOOL-CURRENT-LAUNCH-REFREEZE-v1.1.json"
CURRENT_ROUTE = ENGINE / "280-RUSSIAN-FIPI-2026-OGE-6.8-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
FRONTIER_BUILDER = HERE / "build_oge_6_8_solid_hyphen_separate_source_bound_frontier_review.py"

EXPECTED_OWNERS = [
    "school-adverb-solid-hyphen-separate-system",
    "school-compound-adjective-solid-hyphen-separate-system",
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-numeral-orthography-base",
    "school-pol-polu-writing-boundary",
    "school-preposition-solid-hyphen-separate-base",
]
EXPECTED_CURRENT_ROUTE_REFS = [
    "school-adverb-solid-hyphen-separate-system",
    "school-conjunction-solid-separate-spelling-base",
    "school-nonnegative-particle-separate-hyphen-spelling-base",
    "school-numeral-orthography-base",
    "school-pol-polu-writing-boundary",
    "school-preposition-solid-hyphen-separate-base",
]
EXPECTED_ADDED = ["school-compound-adjective-solid-hyphen-separate-system"]
ABSORBED_PRONOUN = "school-indefinite-pronouns-hyphen-koe-preposition-boundary"
CURRENT_PRONOUN_PARENT = "school-nonnegative-particle-separate-hyphen-spelling-base"


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
    assert ABSORBED_PRONOUN not in base_ids
    assert CURRENT_PRONOUN_PARENT in base_ids

    assert freeze["current_school_canonical_denominator"] == 186

    source_frontier = frontier["source_bound_frontier"]
    lineage = frontier["pronoun_authority_lineage"]
    assert frontier["status"] == "CENTRAL_BRAIN_SOURCE_BOUND_FRONTIER_PROVEN_NO_ADMISSION"
    assert source_frontier["official_branch_count"] == 9
    assert source_frontier["unique_exact_owner_candidates"] == EXPECTED_OWNERS
    assert source_frontier["unique_exact_owner_candidate_count"] == 7
    assert source_frontier["current_source_supported_exact_candidates"] == EXPECTED_CURRENT_ROUTE_REFS
    assert source_frontier["missing_exact_owner_candidates_from_current_route"] == EXPECTED_ADDED
    assert source_frontier["current_nonexact_route_refs"] == []
    assert source_frontier["school_reopen_required"] is False
    assert source_frontier["school_count_effect_if_route_is_corrected"] == 0
    assert source_frontier["exact_route_ready_now"] is True
    assert lineage["historical_identity"] == ABSORBED_PRONOUN
    assert lineage["current_canonical_parent"] == CURRENT_PRONOUN_PARENT
    assert lineage["historical_identity_is_current_inventory_member"] is False
    assert lineage["semantic_reopen_required"] is False

    assert route["status"] == "CURRENT_OGE_2026_6_8_ROUTE_SUPERSESSION_EXACT_OWNER_FRONTIER_NO_OBJECT_ADMISSION"
    assert route["position"] == "6.8"
    assert route["classification"] == "SCHOOL_IDENTITY_ROUTE"
    assert route["school_baseline_for_route"] == 186
    assert route["exact_owner_refs"] == EXPECTED_OWNERS
    assert len(route["exact_owner_refs"]) == len(set(route["exact_owner_refs"])) == 7
    assert ABSORBED_PRONOUN not in route["exact_owner_refs"]
    assert CURRENT_PRONOUN_PARENT in route["exact_owner_refs"]

    accounting = route["owner_accounting"]
    assert accounting["official_fipi_branches"] == 9
    assert accounting["owner_count"] == 7
    assert accounting["reused_current_canonical"] == 7
    assert accounting["newly_materialized_current_canonical"] == 0
    assert accounting["school_reopen_required"] == 0
    assert accounting["legacy_family_placeholders"] == 0
    assert accounting["unresolved_owners"] == 0
    assert accounting["absorbed_historical_refs_not_reopened"] == [ABSORBED_PRONOUN]
    assert accounting["added_source_supported_exact_refs"] == EXPECTED_ADDED

    route_lineage = route["pronoun_authority_lineage"]
    assert route_lineage["historical_identity"] == ABSORBED_PRONOUN
    assert route_lineage["current_canonical_parent"] == CURRENT_PRONOUN_PARENT
    assert route_lineage["reopen_required"] is False
    assert route_lineage["count_effect"] == 0

    supersession = route["supersedes_for_current_launch_truth"]
    assert supersession["historical_base_mutated"] is False
    assert supersession["scope"] == "OGE orthography route 6.8 owner refs only"

    mastery = route["mastery_boundary"]
    assert mastery["route_attempt_can_emit_exact_component_mastery"] is False
    assert mastery["component_specific_independent_evidence_required"] is True
    assert mastery["exact_owner_frontier_is_not_object_acceptance"] is True

    effect = route["admission_effect"]
    assert effect == {
        "semantic_admissions": 0,
        "object_closures": 0,
        "requirements_closed": 0,
        "school_identity_count_effect": 0,
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

    print("RUSSIAN_OGE_6_8_CURRENT_ROUTE_SUPERSESSION=PASS")
    print("CURRENT_SCHOOL_DENOMINATOR=186")
    print("OFFICIAL_BRANCHES=9")
    print("EXACT_OWNER_FRONTIER=7")
    print("CURRENT_ROUTE_REFS=6")
    print("ADDED_SOURCE_SUPPORTED_EXACT_REFS=1")
    print("ABSORBED_PRONOUN_REOPENED=0")
    print("LEGACY_PLACEHOLDERS=0")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("SCHOOL_IDENTITY_COUNT_EFFECT=0")
    print("FALSE_EXACT_MASTERY=0")
    print("READY_FOR_EXACT_OBJECT_ACCEPTANCE=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")


if __name__ == "__main__":
    main()
