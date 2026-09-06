#!/usr/bin/env python3
"""Deterministic acceptance for issue #185 live educational asset reconciliation."""
from __future__ import annotations

import json
from pathlib import Path

from live_asset_registry import (
    admit_future_canonical_evidence,
    assert_invariants,
    load_registry,
)

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
BANK_MANIFEST = ENGINE / "russkiy-knigi" / "ege-russkiy-trenazher" / "BANK-MANIFEST.json"
SENSOR_MAP = HERE / "RUSSIAN-EGE-TRAINER-SENSOR-MAP-v0.1.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    registry = load_registry()
    assert_invariants(registry)

    require(registry["authority_checked_at"] == "2026-09-06", "live authority snapshot date is pinned")
    require(registry["authority_policy"]["live_site_is_factual_authority_for_current_working_ux"] is True, "live site remains factual authority")
    require(registry["authority_policy"]["github_is_canonical_reconciliation_target_not_live_invalidation"] is True, "GitHub reconciles rather than invalidates live UX")
    require(registry["authority_policy"]["preserve_existing_live_local_state_until_registered_replacement_ready"] is True, "working local UX is preserved until replacement")
    require(registry["authority_policy"]["existing_live_local_state_is_future_canonical"] is False, "local live state is not future canonical")

    # Exact repository authority for the full Russian trainer.
    bank = json.loads(BANK_MANIFEST.read_text(encoding="utf-8"))
    require(bank["cards"] == 174, "full Russian trainer exact card count must remain 174")
    require(bank["sources"] == 9, "full Russian trainer exact source-text count must remain 9")
    require(sum(bank["cardsPerTask"].values()) == 174, "cardsPerTask must reconcile to exact card denominator")
    require(sorted(int(task) for task in bank["cardsPerTask"]) == list(range(1, 28)), "full trainer covers task identities 1..27 without inventing semantic owners")

    assets = {asset["asset_id"]: asset for asset in registry["assets"]}
    full = assets["live-russian-ege-full-trainer"]
    require(full["canonical_source"]["cards"] == bank["cards"], "registry card denominator matches repository manifest")
    require(full["canonical_source"]["source_texts"] == bank["sources"], "registry source denominator matches repository manifest")
    require(full["live_observation"]["task_types"] == 27, "live trainer observed with 27 task types")
    require(full["whole_trainer_mastery"] == "FORBIDDEN", "composite trainer never becomes an exact mastery owner")

    sensor = json.loads(SENSOR_MAP.read_text(encoding="utf-8"))
    require(sensor["product"]["route"] == "/ege/russkiy/trenazher/", "existing sensor map points to the same live trainer")
    require(sensor["precision_policy"]["forbidden"] == "whole-card score must not become an exact semantic failure", "existing precision guard is preserved")
    # Existing map is composite/source-verified, not an accepted exact mastery allow-list.
    require(not full.get("accepted_exact_item_bindings"), "#185 imports no unreviewed exact mastery bindings")

    thematic_ids = [
        "live-russian-orthoepy-trainer",
        "live-russian-dictionary-words-trainer",
        "live-russian-paronyms-trainer",
        "live-russian-phraseology-trainer",
    ]
    require(len(thematic_ids) == 4, "exactly four owner-priority thematic trainers are reconciled")
    for asset_id in thematic_ids:
        asset = assets[asset_id]
        require(asset["canonical_item_identity_status"] == "UNKNOWN_BLOCKER", f"{asset_id} unknown identities remain explicit")
        require(asset["canonical_item_count"] is None, f"{asset_id} count is not guessed")
        require(asset["mastery_from_live_progress"] is False, f"{asset_id} local progress is not imported as mastery")
        decision = admit_future_canonical_evidence(
            asset_id=asset_id,
            user_identity_ref="usr_registered_ci",
            exact_item_identity="invented-item",
            semantic_binding_status="ACCEPTED_EXACT",
            observation_kind="ANSWER_CHECKED",
            registry=registry,
        )
        require(not decision.admitted and not decision.mastery_eligible, f"{asset_id} unknown item identity fails closed")

    demo = assets["live-ege-demo-catalog"]
    require(demo["browser_autosave_is_future_canonical_progress"] is False, "browser demo autosave is not future canonical progress")
    require(demo["demo_completion_or_score_implies_mastery"] is False, "demo score never implies mastery")
    russian_routes = demo["russian_demo_routes"]
    require([entry["year"] for entry in russian_routes] == [2026, 2025, 2024, 2023, 2022], "live Russian demo years are explicitly reconciled")
    require(len({entry["url"] for entry in russian_routes}) == 5, "Russian demo routes are unique")

    # Registration is mandatory for all future canonical learner evidence.
    anonymous = admit_future_canonical_evidence(
        asset_id="live-russian-ege-full-trainer",
        user_identity_ref=None,
        exact_item_identity="ege-ru-12-2026-12-01",
        semantic_binding_status="ACCEPTED_EXACT",
        observation_kind="ANSWER_CHECKED",
        registry=registry,
    )
    require(not anonymous.admitted and not anonymous.mastery_eligible, "anonymous evidence cannot enter future canonical learner state")

    # Route/view/reference activity may be observable but is never mastery.
    reference_read = admit_future_canonical_evidence(
        asset_id="live-ege-demo-catalog",
        user_identity_ref="usr_registered_ci",
        exact_item_identity=None,
        semantic_binding_status=None,
        observation_kind="REFERENCE_READ",
        registry=registry,
    )
    require(reference_read.admitted and not reference_read.mastery_eligible, "reading/navigation never creates mastery")

    # Even the known full-trainer card identity cannot self-assert exactness. The
    # existing repository mapping is composite, so no accepted exact allow-list
    # exists in this #185 slice.
    not_allowlisted = admit_future_canonical_evidence(
        asset_id="live-russian-ege-full-trainer",
        user_identity_ref="usr_registered_ci",
        exact_item_identity="ege-ru-12-2026-12-01",
        semantic_binding_status="ACCEPTED_EXACT",
        observation_kind="ANSWER_CHECKED",
        registry=registry,
    )
    require(not not_allowlisted.admitted and not not_allowlisted.mastery_eligible, "caller cannot promote a composite card to exact mastery")

    require(registry["mastery_policy"]["false_exact_mastery"] == 0, "false_exact_mastery remains zero")
    print("LIVE_ASSET_RECONCILIATION=PASS")
    print("full_russian_trainer=174_cards/9_sources")
    print("thematic_trainers=4_unknown_item_identity_blockers")
    print("russian_demo_years=2022-2026")
    print("registered_user_identity_ref_required=PASS")
    print("false_exact_mastery=0")


if __name__ == "__main__":
    main()
