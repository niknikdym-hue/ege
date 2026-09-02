#!/usr/bin/env python3
from __future__ import annotations

import json
import runpy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
BASE_INVENTORY = ENGINE / "273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json"
CURRENT_FREEZE = ENGINE / "277-RUSSIAN-SCHOOL-CURRENT-LAUNCH-REFREEZE-v1.1.json"
CURRENT_ROUTE = ENGINE / "281-RUSSIAN-FIPI-2026-OGE-6.9-CURRENT-ROUTE-SUPERSESSION-v0.1.json"
OWNER_REVIEWER = HERE / "build_oge_6_9_ne_ni_exact_owner_resolution_review.py"

EXPECTED_OWNERS = [
    "school-ne-double-negation-affirmative-boundary",
    "school-ne-kto-inoy-vs-nikto-inoy",
    "school-ne-ni-ni-odin-ne-odin-ni-razu-ne-raz",
    "school-ne-ni-pronominal-exclamatory-vs-concessive-boundary",
    "school-ne-non-o-adverb-predicative-separate-system",
    "school-ne-noun-adjective-o-adverb-spelling-system",
    "school-ne-numeral-pronoun-spelling-base",
    "school-ne-participle-dependent-short-opposition-boundary",
    "school-ne-verb-gerund-spelling-base",
    "school-negative-adverbs-ne-ni-spelling",
    "school-negative-pronouns-ne-ni-stress-preposition-boundary",
    "school-ni-fixed-idioms",
    "school-ni-particle-vs-repeating-conjunction",
    "school-pri-chem-ni-pri-chem-nipochem",
]
EXPECTED_PREVIOUS_ROUTE_REFS = ["school-ni-fixed-idioms"]
EXPECTED_ADDED = sorted(set(EXPECTED_OWNERS) - set(EXPECTED_PREVIOUS_ROUTE_REFS))


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    inventory = load(BASE_INVENTORY)
    freeze = load(CURRENT_FREEZE)
    route = load(CURRENT_ROUTE)
    owner_review = runpy.run_path(str(OWNER_REVIEWER))["build_review"]()

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

    oge_rows = [
        row for row in inventory["objects"]
        if row.get("object_key") == "oge_2026_orthography_route::oge-2026-orthography-6-9"
    ]
    assert len(oge_rows) == 1
    assert oge_rows[0]["authority_status"] == "current"
    assert oge_rows[0]["review_status"] == "reviewed"
    assert oge_rows[0]["audit_classification"] == "EXAM_ROUTE_ONLY"
    assert oge_rows[0]["current_semantic_refs"] == EXPECTED_PREVIOUS_ROUTE_REFS

    assert freeze["current_school_canonical_denominator"] == 186

    assert owner_review["status"] == "CENTRAL_BRAIN_OGE_6_9_EXACT_OWNER_RESOLUTION_ACCEPTED_NO_ROUTE_MUTATION"
    resolution = owner_review["exact_owner_resolution"]
    assert resolution["exact_owner_refs"] == EXPECTED_OWNERS
    assert resolution["exact_owner_count"] == 14
    assert resolution["exact_branch_owner_pair_count"] == 21
    assert resolution["rejected_source_bound_candidates"] == []
    assert resolution["unresolved_source_bound_candidates"] == []
    assert resolution["all_primary_authorities_present"] is True
    assert resolution["school_reopen_required"] is False
    assert resolution["new_school_identities_required"] == 0
    assert resolution["route_supersession_ready"] is True
    assert resolution["object_acceptance_ready"] is False
    assert resolution["component_evidence_required_before_object_acceptance"] is True
    assert owner_review["current_route_truth"]["current_route_refs"] == EXPECTED_PREVIOUS_ROUTE_REFS
    assert owner_review["current_route_truth"]["missing_exact_owner_refs"] == EXPECTED_ADDED
    assert owner_review["current_route_truth"]["route_mutated_by_this_review"] is False

    assert route["status"] == "CURRENT_OGE_2026_6_9_ROUTE_SUPERSESSION_EXACT_OWNER_FRONTIER_NO_OBJECT_ADMISSION"
    assert route["position"] == "6.9"
    assert route["topic"] == "НЕ/НИ"
    assert route["classification"] == "SCHOOL_IDENTITY_ROUTE"
    assert route["school_baseline_for_route"] == 186
    assert route["exact_owner_refs"] == EXPECTED_OWNERS
    assert len(route["exact_owner_refs"]) == len(set(route["exact_owner_refs"])) == 14

    accounting = route["owner_accounting"]
    assert accounting["official_fipi_branches"] == 8
    assert accounting["owner_count"] == 14
    assert accounting["branch_owner_pairs"] == 21
    assert accounting["reused_current_canonical"] == 14
    assert accounting["newly_materialized_current_canonical"] == 0
    assert accounting["school_reopen_required"] == 0
    assert accounting["legacy_family_placeholders_resolved"] == 2
    assert accounting["unresolved_owners"] == 0
    assert accounting["previous_current_route_refs"] == EXPECTED_PREVIOUS_ROUTE_REFS
    assert accounting["added_source_supported_exact_refs"] == EXPECTED_ADDED

    boundary = route["branch_boundary"]
    assert boundary["official_branch_count"] == 8
    assert boundary["neighboring_6_8_imported"] is False
    assert boundary["neighboring_6_11_imported"] is False
    assert boundary["generic_ne_ni_route_is_atomic_mastery"] is False

    supersession = route["supersedes_for_current_launch_truth"]
    assert supersession["historical_base_mutated"] is False
    assert supersession["scope"] == "OGE orthography route 6.9 owner refs only"

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

    print("RUSSIAN_OGE_6_9_CURRENT_ROUTE_SUPERSESSION=PASS")
    print("CURRENT_SCHOOL_DENOMINATOR=186")
    print("OFFICIAL_BRANCHES=8")
    print("EXACT_OWNER_FRONTIER=14")
    print("EXACT_BRANCH_OWNER_PAIRS=21")
    print("PREVIOUS_CURRENT_ROUTE_REFS=1")
    print("ADDED_SOURCE_SUPPORTED_EXACT_REFS=13")
    print("LEGACY_PLACEHOLDERS_RESOLVED=2")
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
