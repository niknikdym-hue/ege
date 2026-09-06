#!/usr/bin/env python3
"""Fail-closed adapter for assets observed on the live Eksamio site.

The live site is factual authority for what currently exists and works.  This
module only reconciles that surface with canonical learner/PEIS rules; it does
not make live route names, task numbers, trainer names, browser progress or
reference-reading into mastery evidence.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "LIVE-EDUCATIONAL-ASSET-RECONCILIATION-v0.1.json"


@dataclass(frozen=True)
class EvidenceAdmission:
    admitted: bool
    mastery_eligible: bool
    reason: str


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def asset_by_id(asset_id: str, *, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    data = registry or load_registry()
    matches = [asset for asset in data["assets"] if asset["asset_id"] == asset_id]
    if len(matches) != 1:
        raise KeyError(f"asset_id must resolve exactly once: {asset_id}")
    return matches[0]


def asset_by_live_url(live_url: str, *, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    data = registry or load_registry()
    matches = [asset for asset in data["assets"] if asset["live_url"] == live_url]
    if len(matches) != 1:
        raise KeyError(f"live_url must resolve exactly once: {live_url}")
    return matches[0]


def admit_future_canonical_evidence(
    *,
    asset_id: str,
    user_identity_ref: str | None,
    exact_item_identity: str | None,
    semantic_binding_status: str | None,
    observation_kind: str,
    registry: dict[str, Any] | None = None,
) -> EvidenceAdmission:
    """Return a deterministic fail-closed PEIS admission decision.

    `observation_kind` is intentionally explicit.  Reading/reference navigation
    never creates mastery, and a score/route/task/trainer label cannot substitute
    for an accepted exact semantic binding.
    """
    data = registry or load_registry()
    policy = data["mastery_policy"]
    identity_policy = data["learner_identity_policy"]
    asset = asset_by_id(asset_id, registry=data)

    if identity_policy["future_canonical_evidence_requires_registered_user_identity_ref"]:
        if not user_identity_ref or not user_identity_ref.strip():
            return EvidenceAdmission(False, False, "REGISTERED_USER_IDENTITY_REF_REQUIRED")

    if observation_kind in {"REFERENCE_READ", "PAGE_VIEW", "ROUTE_VISIT"}:
        return EvidenceAdmission(True, False, "READING_OR_NAVIGATION_NEVER_CREATES_MASTERY")

    if not exact_item_identity or not exact_item_identity.strip():
        return EvidenceAdmission(False, False, "EXACT_ITEM_IDENTITY_REQUIRED")

    identity_status = str(asset.get("canonical_item_identity_status", "UNKNOWN_BLOCKER"))
    if identity_status.startswith("UNKNOWN_BLOCKER"):
        return EvidenceAdmission(False, False, "ASSET_ITEM_IDENTITIES_UNRESOLVED")

    if policy["accepted_exact_semantic_binding_required"] and semantic_binding_status != "ACCEPTED_EXACT":
        return EvidenceAdmission(True, False, "ACCEPTED_EXACT_SEMANTIC_BINDING_REQUIRED")

    return EvidenceAdmission(True, True, "EXACT_REGISTERED_EVIDENCE_ADMITTED")


def assert_invariants(registry: dict[str, Any] | None = None) -> None:
    data = registry or load_registry()
    mastery = data["mastery_policy"]
    identity = data["learner_identity_policy"]

    assert mastery["false_exact_mastery"] == 0
    for field in (
        "mastery_from_route_name",
        "mastery_from_task_number",
        "mastery_from_trainer_name",
        "mastery_from_page_name",
        "reference_reading_creates_mastery",
    ):
        assert mastery[field] is False, field
    assert mastery["accepted_exact_semantic_binding_required"] is True
    assert mastery["unknown_item_identity_is_mastery_blocker"] is True

    assert identity["future_canonical_evidence_requires_registered_user_identity_ref"] is True
    assert identity["anonymous_learner_evidence_allowed"] is False
    assert identity["device_only_progress_is_canonical"] is False
    assert identity["anon_to_account_continuity_allowed"] is False

    assets = data["assets"]
    ids = [asset["asset_id"] for asset in assets]
    urls = [asset["live_url"] for asset in assets]
    assert len(ids) == len(set(ids))
    assert len(urls) == len(set(urls))


if __name__ == "__main__":
    registry = load_registry()
    assert_invariants(registry)
    print("LIVE_ASSET_REGISTRY=PASS")
