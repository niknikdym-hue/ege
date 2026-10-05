#!/usr/bin/env python3
"""Deterministic acceptance for issue #185 current live educational reconciliation."""
from __future__ import annotations

import json
from pathlib import Path

from live_asset_registry import admit_future_canonical_evidence, assert_invariants, load_registry

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
BANK_MANIFEST = ENGINE / "russkiy-knigi" / "ege-russkiy-trenazher" / "BANK-MANIFEST.json"
SENSOR_MAP = HERE / "RUSSIAN-EGE-TRAINER-SENSOR-MAP-v0.1.json"
THEMATIC = HERE / "THEMATIC-TRAINER-CANONICAL-RECONCILIATION-v0.1.json"
ACTIONS = HERE / "THEMATIC-TRAINER-ACTION-SCOPED-SEMANTIC-BINDINGS-v0.1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    registry = load_registry()
    assert_invariants(registry)
    thematic = json.loads(THEMATIC.read_text(encoding="utf-8"))
    actions = json.loads(ACTIONS.read_text(encoding="utf-8"))

    require(registry["authority_checked_at"] == "2026-09-07", "current live authority date is pinned")
    require(registry["status"] == "LIVE_AUTHORITY_RECONCILIATION_CURRENT_FAIL_CLOSED", "registry is current but fail-closed")
    require(registry["thematic_reconciliation_artifact"] == THEMATIC.name, "top-level registry points to current thematic reconciliation")
    require(registry["thematic_action_binding_artifact"] == ACTIONS.name, "top-level registry points to action bindings")
    require(registry["authority_policy"]["live_site_is_factual_authority_for_current_working_ux"] is True, "live site remains factual authority")
    require(registry["authority_policy"]["existing_live_local_state_is_future_canonical"] is False, "local live state is not future canonical")

    bank = json.loads(BANK_MANIFEST.read_text(encoding="utf-8"))
    require(bank["cards"] == 174 and bank["sources"] == 9, "full Russian trainer remains 174 cards / 9 sources")
    require(sum(bank["cardsPerTask"].values()) == 174, "cardsPerTask reconciles")
    assets = {asset["asset_id"]: asset for asset in registry["assets"]}
    full = assets["live-russian-ege-full-trainer"]
    require(full["canonical_source"]["cards"] == 174 and full["canonical_source"]["source_texts"] == 9, "registry denominator matches bank")
    require(full["whole_trainer_mastery"] == "FORBIDDEN", "composite trainer cannot be one mastery owner")
    sensor = json.loads(SENSOR_MAP.read_text(encoding="utf-8"))
    require(sensor["product"]["route"] == "/ege/russkiy/trenazher/", "sensor map route stays aligned")
    require(not full.get("accepted_exact_item_bindings"), "no unreviewed full-trainer exact binding imported")

    specs = {
        "live-russian-orthoepy-trainer": {
            "count_field": "canonical_item_count", "count": 291,
            "identity_status": "EXACT_LIVE_IDS_CAPTURED",
            "semantic_id": "ru-orthoepy-normative-stress-selection",
            "thematic_key": "orthoepy",
        },
        "live-russian-dictionary-words-trainer": {
            "count_field": "canonical_item_count", "count": 308,
            "identity_status": "EXACT_LIVE_IDS_CAPTURED",
            "semantic_id": "school-root-vowel-dictionary-unverifiable",
            "thematic_key": "dictionary_words",
        },
        "live-russian-paronyms-trainer": {
            "identity_status": "EXACT_LIVE_GROUP_AND_ENTRY_IDS_CAPTURED",
            "semantic_id": "ru-lexis-paronym-collocation-choice",
            "thematic_key": "paronyms",
        },
        "live-russian-phraseology-trainer": {
            "count_field": "canonical_item_count", "count": 285,
            "identity_status": "EXACT_LIVE_IDS_CAPTURED",
            "semantic_id": "ru-lexis-phraseologism-fragment-identification",
            "thematic_key": "phraseology",
        },
    }
    for asset_id, spec in specs.items():
        asset = assets[asset_id]
        require(asset["canonical_item_identity_status"] == spec["identity_status"], f"{asset_id} exact identity is current")
        if "count_field" in spec:
            require(asset[spec["count_field"]] == spec["count"], f"{asset_id} exact denominator is current")
        require(asset["accepted_action_scoped_semantic_id"] == spec["semantic_id"], f"{asset_id} action semantic is pinned")
        require(asset["production_event_admission"] == "BLOCKED_UNTIL_REGISTERED_EXACT_ITEM_ACTION_EVENT", f"{asset_id} production event stays blocked")
        require(asset["mastery_from_live_progress"] is False, f"{asset_id} local progress is never mastery")
        require(not asset.get("accepted_exact_item_bindings"), f"{asset_id} has no production event allowlist yet")
        detailed = thematic["assets"][spec["thematic_key"]]
        require("ACCEPTED_ACTION_SCOPED" in detailed["semantic_binding_status"], f"{asset_id} detailed semantic reconciliation agrees")
        action_detail = actions["bindings"][spec["thematic_key"]]["accepted_action_component"]
        require(action_detail["accepted_semantic_id"] == spec["semantic_id"], f"{asset_id} action artifact agrees")
        decision = admit_future_canonical_evidence(
            asset_id=asset_id,
            user_identity_ref="usr_registered_ci",
            exact_item_identity="invented-item",
            semantic_binding_status="ACCEPTED_EXACT",
            observation_kind="ANSWER_CHECKED",
            registry=registry,
        )
        require(not decision.admitted and not decision.mastery_eligible, f"{asset_id} cannot self-admit an event")
        require(decision.reason == "ITEM_NOT_IN_ACCEPTED_EXACT_BINDING_REGISTRY", f"{asset_id} is blocked by missing server event allowlist, not stale unknown identity")

    paronyms = assets["live-russian-paronyms-trainer"]
    require(paronyms["canonical_group_count"] == 144 and paronyms["canonical_entry_count"] == 334, "paronym exact denominator is 144 groups / 334 entries")
    require(thematic["accepted_action_scoped_authority_reuses"] == actions["admission_boundary"]["accepted_action_scoped_authority_reuses"] == 4, "all four thematic action mappings are current")
    require(thematic["false_exact_mastery"] == actions["admission_boundary"]["false_exact_mastery"] == registry["mastery_policy"]["false_exact_mastery"] == 0, "false exact mastery remains zero")
    require(actions["admission_boundary"]["production_event_semantic_admissions"] == 0, "no production event semantic admission is opened")
    require(actions["admission_boundary"]["mastery_admissions"] == 0, "no mastery admission is opened")

    demo = assets["live-ege-demo-catalog"]
    require(demo["browser_autosave_is_future_canonical_progress"] is False, "demo browser autosave is not canonical")
    require(demo["demo_completion_or_score_implies_mastery"] is False, "demo score cannot imply mastery")
    require(len(demo["verified_demo_routes"]) == 24, "live demo inventory has 24 verified routes")
    require([entry["year"] for entry in demo["russian_demo_routes"]] == [2026, 2025, 2024, 2023, 2022], "Russian demo years remain exact")
    route_keys = {(entry["subject"], entry["year"]) for entry in demo["verified_demo_routes"]}
    require(len(route_keys) == 24, "demo subject/year routes are unique")

    anonymous = admit_future_canonical_evidence(
        asset_id="live-russian-orthoepy-trainer",
        user_identity_ref=None,
        exact_item_identity="w001",
        semantic_binding_status="ACCEPTED_EXACT",
        observation_kind="ANSWER_CHECKED",
        registry=registry,
    )
    require(not anonymous.admitted and not anonymous.mastery_eligible, "anonymous evidence stays forbidden")
    reference_read = admit_future_canonical_evidence(
        asset_id="live-ege-demo-catalog",
        user_identity_ref="usr_registered_ci",
        exact_item_identity=None,
        semantic_binding_status=None,
        observation_kind="REFERENCE_READ",
        registry=registry,
    )
    require(reference_read.admitted and not reference_read.mastery_eligible, "reading/navigation never creates mastery")

    print("LIVE_ASSET_RECONCILIATION=PASS")
    print("full_russian_trainer=174_cards/9_sources")
    print("thematic_exact_mappings=4")
    print("thematic_production_event_admissions=0")
    print("verified_demo_routes=24")
    print("registered_user_identity_ref_required=PASS")
    print("false_exact_mastery=0")


if __name__ == "__main__":
    main()
