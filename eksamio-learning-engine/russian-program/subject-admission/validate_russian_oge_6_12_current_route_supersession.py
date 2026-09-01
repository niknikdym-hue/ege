#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
BASE_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CURRENT_FREEZE = ENGINE / "277-RUSSIAN-SCHOOL-CURRENT-LAUNCH-REFREEZE-v1.1.json"
CURRENT_ROUTE = ENGINE / "282-RUSSIAN-FIPI-2026-OGE-6.12-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
OWNER_REVIEWER = HERE / "build_oge_6_12_proper_names_exact_owner_resolution.py"

EXPECTED_OWNERS = [
    "school-capitalization-astronomical-names",
    "school-capitalization-awards-orders-medals",
    "school-capitalization-documents-works-media-objects",
    "school-capitalization-geographic-administrative-names",
    "school-capitalization-historical-calendar-public-events",
    "school-capitalization-organizations-authorities-institutions",
    "school-capitalization-person-animal-name-and-derivatives",
    "school-capitalization-religious-names",
    "school-capitalization-trademarks-breeds-varieties-products",
]
EXPECTED_REJECTED = [
    "school-capitalization-conditional-special-proper-names",
    "school-capitalization-positions-titles",
]
EXPECTED_PREVIOUS_ROUTE_REFS: list[str] = []


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    inventory = load(BASE_INVENTORY)
    freeze = load(CURRENT_FREEZE)
    route = load(CURRENT_ROUTE)
    owner_review = runpy.run_path(str(OWNER_REVIEWER))["build_resolution"]()

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
    assert set(EXPECTED_REJECTED) <= base_ids

    oge_rows = [
        row for row in inventory["objects"]
        if row.get("object_key") == "oge_2026_orthography_route::oge-2026-orthography-6-12"
    ]
    assert len(oge_rows) == 1
    assert oge_rows[0]["authority_status"] == "current"
    assert oge_rows[0]["review_status"] == "reviewed"
    assert oge_rows[0]["audit_classification"] == "EXAM_ROUTE_ONLY"
    assert oge_rows[0]["current_semantic_refs"] == EXPECTED_PREVIOUS_ROUTE_REFS

    assert freeze["current_school_canonical_denominator"] == 186

    assert owner_review["status"] == "CENTRAL_BRAIN_EXACT_OWNER_SET_PROVEN_ROUTE_SUPERSESSION_REQUIRED"
    resolution = owner_review["exact_owner_resolution"]
    assert resolution["exact_current_canonical_owners"] == EXPECTED_OWNERS
    assert resolution["exact_owner_count"] == 9
    assert resolution["rejected_frontier_candidate_count"] == 2
    assert [row["candidate"] for row in resolution["rejected_frontier_candidates"]] == EXPECTED_REJECTED
    assert resolution["unresolved_owner_candidates"] == 0
    assert resolution["unresolved_placeholders"] == 0
    assert resolution["new_school_identities_required"] == 0
    assert resolution["current_inventory_route_refs"] == EXPECTED_PREVIOUS_ROUTE_REFS
    assert resolution["current_inventory_route_already_matches_exact_owner_set"] is False
    assert resolution["current_route_supersession_required"] is True
    assert resolution["current_route_supersession_authorized_after_this_gate_green"] is True
    assert resolution["evidence_gate_required_before_object_acceptance"] is True
    assert resolution["exact_owner_set_proven"] is True

    assert route["status"] == "CURRENT_OGE_2026_6_12_ROUTE_SUPERSESSION_EXACT_OWNER_FRONTIER_NO_OBJECT_ADMISSION"
    assert route["position"] == "6.12"
    assert route["topic"] == "Правописание собственных имён существительных"
    assert route["classification"] == "SCHOOL_IDENTITY_ROUTE"
    assert route["school_baseline_for_route"] == 186
    assert route["exact_owner_refs"] == EXPECTED_OWNERS
    assert len(route["exact_owner_refs"]) == len(set(route["exact_owner_refs"])) == 9

    accounting = route["owner_accounting"]
    assert accounting["official_fipi_objects"] == 1
    assert accounting["official_explicit_subbranches"] == 0
    assert accounting["owner_count"] == 9
    assert accounting["reused_current_canonical"] == 9
    assert accounting["newly_materialized_current_canonical"] == 0
    assert accounting["school_reopen_required"] == 0
    assert accounting["legacy_family_placeholders_resolved"] == 1
    assert accounting["rejected_frontier_candidates"] == 2
    assert accounting["unresolved_owners"] == 0
    assert accounting["previous_current_route_refs"] == EXPECTED_PREVIOUS_ROUTE_REFS
    assert accounting["added_source_supported_exact_refs"] == EXPECTED_OWNERS

    boundary = route["object_boundary"]
    assert boundary["official_object_count"] == 1
    assert boundary["official_explicit_subbranches"] == 0
    assert boundary["rejected_whole_identities"] == EXPECTED_REJECTED
    assert boundary["neighboring_6_13_imported"] is False
    assert boundary["generic_capitalization_route_is_atomic_mastery"] is False

    supersession = route["supersedes_for_current_launch_truth"]
    assert supersession["historical_base_mutated"] is False
    assert supersession["scope"] == "OGE orthography route 6.12 owner refs only"

    mastery = route["mastery_boundary"]
    assert mastery["route_attempt_can_emit_exact_component_mastery"] is False
    assert mastery["component_specific_independent_evidence_required"] is True
    assert mastery["exact_owner_frontier_is_not_object_acceptance"] is True
    assert mastery["route_supersession_is_not_semantic_admission"] is True

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

    print("RUSSIAN_OGE_6_12_CURRENT_ROUTE_SUPERSESSION=PASS")
    print("CURRENT_SCHOOL_DENOMINATOR=186")
    print("OFFICIAL_OBJECTS=1")
    print("OFFICIAL_EXPLICIT_SUBBRANCHES=0")
    print("EXACT_OWNER_FRONTIER=9")
    print("PREVIOUS_CURRENT_ROUTE_REFS=0")
    print("ADDED_SOURCE_SUPPORTED_EXACT_REFS=9")
    print("REJECTED_WHOLE_IDENTITIES=2")
    print("LEGACY_PLACEHOLDERS_RESOLVED=1")
    print("UNRESOLVED_OWNERS=0")
    print("SEMANTIC_ADMISSIONS=0")
    print("OBJECT_CLOSURES=0")
    print("SCHOOL_IDENTITY_COUNT_EFFECT=0")
    print("FALSE_EXACT_MASTERY=0")
    print("READY_FOR_COMPONENT_EVIDENCE_AUDIT=1")
    print("READY_FOR_EXACT_OBJECT_ACCEPTANCE=0")
    print("LEARNER_AUDIO_PERSISTENCE=0")


if __name__ == "__main__":
    main()
