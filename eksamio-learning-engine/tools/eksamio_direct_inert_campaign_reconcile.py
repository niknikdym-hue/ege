#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from typing import Any

import eksamio_direct_inert_campaign_setup as base


def get_campaign(token: str, campaign_id: int) -> dict[str, Any]:
    payload = base.direct_call(
        token,
        "campaigns",
        "get",
        {
            "SelectionCriteria": {"Ids": [campaign_id]},
            "FieldNames": ["Id", "Name", "Type", "State", "Status"],
            "UnifiedCampaignFieldNames": [
                "BiddingStrategy",
                "CounterIds",
                "TrackingParams",
                "AttributionModel",
                "Settings",
            ],
        },
    )
    campaigns = payload.get("result", {}).get("Campaigns") or []
    if len(campaigns) != 1:
        raise RuntimeError("Exact campaign read-back failed")
    return campaigns[0]


def verify_inert_campaign(campaign: dict[str, Any]) -> None:
    if campaign.get("Name") != base.CAMPAIGN_NAME:
        raise RuntimeError("Campaign name identity mismatch")
    unified = campaign.get("UnifiedCampaign")
    if not isinstance(unified, dict):
        raise RuntimeError("Campaign is not returned as a UnifiedCampaign")
    strategy = unified.get("BiddingStrategy") or {}
    for surface in ("Search", "Network"):
        item = strategy.get(surface) or {}
        if item.get("BiddingStrategyType") != "SERVING_OFF":
            raise RuntimeError(f"Refusing reconcile: {surface} is not SERVING_OFF")
    counters = unified.get("CounterIds") or {}
    items = counters.get("Items") or []
    if base.METRIKA_COUNTER_ID not in items:
        raise RuntimeError("Refusing reconcile: Eksamio Metrika counter is not attached")
    if unified.get("TrackingParams") != base.TRACKING_PARAMS:
        raise RuntimeError("Refusing reconcile: tracking params differ from canonical Eksamio contract")


def ensure_campaign(token: str) -> tuple[int, bool]:
    exact = [item for item in base.list_campaigns(token) if item.get("Name") == base.CAMPAIGN_NAME]
    if len(exact) > 1:
        raise RuntimeError(f"Duplicate exact Eksamio campaign names found: {len(exact)}")
    created = False
    if not exact:
        payload = base.direct_call(
            token,
            "campaigns",
            "add",
            base.campaign_payload(dt.date.today().isoformat()),
        )
        campaign_id = base.add_ids(payload, 1, "campaigns.add")[0]
        created = True
    else:
        campaign_id = int(exact[0]["Id"])
    verify_inert_campaign(get_campaign(token, campaign_id))
    return campaign_id, created


def list_groups(token: str, campaign_id: int) -> list[dict[str, Any]]:
    payload = base.direct_call(
        token,
        "adgroups",
        "get",
        {
            "SelectionCriteria": {"CampaignIds": [campaign_id]},
            "FieldNames": ["Id", "Name", "CampaignId"],
            "Page": {"Limit": 10000},
        },
    )
    groups = payload.get("result", {}).get("AdGroups")
    if not isinstance(groups, list):
        raise RuntimeError("adgroups.get returned invalid AdGroups list")
    return [item for item in groups if isinstance(item, dict)]


def ensure_groups(token: str, campaign_id: int) -> tuple[dict[str, int], list[str]]:
    current = list_groups(token, campaign_id)
    by_name: dict[str, list[dict[str, Any]]] = {}
    for item in current:
        by_name.setdefault(str(item.get("Name", "")), []).append(item)

    ids: dict[str, int] = {}
    created: list[str] = []
    for spec in base.GROUPS:
        matches = by_name.get(spec.name, [])
        if len(matches) > 1:
            raise RuntimeError(f"Duplicate ad group name found: {spec.name!r}")
        if matches:
            ids[spec.name] = int(matches[0]["Id"])
            continue
        item = {
            "Name": spec.name,
            "CampaignId": campaign_id,
            "RegionIds": [base.RUSSIA_REGION_ID],
            "NegativeKeywords": {"Items": list(spec.negatives)},
            "UnifiedAdGroup": {"OfferRetargeting": "NO"},
        }
        payload = base.direct_call(token, "adgroups", "add", {"AdGroups": [item]})
        ids[spec.name] = base.add_ids(payload, 1, f"adgroups.add:{spec.name}")[0]
        created.append(spec.name)
    return ids, created


def list_keywords(token: str, group_id: int) -> list[dict[str, Any]]:
    payload = base.direct_call(
        token,
        "keywords",
        "get",
        {
            "SelectionCriteria": {"AdGroupIds": [group_id]},
            "FieldNames": ["Id", "Keyword", "AdGroupId"],
            "Page": {"Limit": 10000},
        },
    )
    keywords = payload.get("result", {}).get("Keywords")
    if not isinstance(keywords, list):
        raise RuntimeError("keywords.get returned invalid Keywords list")
    return [item for item in keywords if isinstance(item, dict)]


def ensure_keywords(token: str, group_ids: dict[str, int]) -> tuple[int, int]:
    created = 0
    total = 0
    for spec in base.GROUPS:
        group_id = group_ids[spec.name]
        current = list_keywords(token, group_id)
        by_phrase: dict[str, list[dict[str, Any]]] = {}
        for item in current:
            phrase = item.get("Keyword")
            if isinstance(phrase, str):
                by_phrase.setdefault(phrase, []).append(item)
        missing: list[dict[str, Any]] = []
        for phrase in spec.keywords:
            total += 1
            matches = by_phrase.get(phrase, [])
            if len(matches) > 1:
                raise RuntimeError(f"Duplicate keyword {phrase!r} in group {spec.name!r}")
            if not matches:
                missing.append({"AdGroupId": group_id, "Keyword": phrase})
        if missing:
            payload = base.direct_call(token, "keywords", "add", {"Keywords": missing})
            base.add_ids(payload, len(missing), f"keywords.add:{spec.name}")
            created += len(missing)
    return total, created


def list_ads(token: str, group_id: int) -> list[dict[str, Any]]:
    payload = base.direct_call(
        token,
        "ads",
        "get",
        {
            "SelectionCriteria": {"AdGroupIds": [group_id]},
            "FieldNames": ["Id", "AdGroupId", "Type", "State", "Status"],
            "ResponsiveAdFieldNames": ["Href"],
            "Page": {"Limit": 10000},
        },
    )
    ads = payload.get("result", {}).get("Ads")
    if not isinstance(ads, list):
        raise RuntimeError("ads.get returned invalid Ads list")
    return [item for item in ads if isinstance(item, dict)]


def ensure_ads(token: str, group_ids: dict[str, int]) -> tuple[dict[str, int], list[str]]:
    ids: dict[str, int] = {}
    created: list[str] = []
    for spec in base.GROUPS:
        group_id = group_ids[spec.name]
        current = list_ads(token, group_id)
        responsive = [item for item in current if item.get("Type") == "RESPONSIVE_AD"]
        matching = [
            item
            for item in responsive
            if isinstance(item.get("ResponsiveAd"), dict)
            and item["ResponsiveAd"].get("Href") == spec.landing
        ]
        if len(matching) > 1:
            raise RuntimeError(f"Duplicate canonical responsive ads in group {spec.name!r}")
        if matching:
            ids[spec.name] = int(matching[0]["Id"])
            continue
        if responsive:
            raise RuntimeError(
                f"Responsive ad exists in {spec.name!r} but its landing differs from canonical Eksamio landing"
            )
        item = {
            "AdGroupId": group_id,
            "ResponsiveAd": {
                "Titles": list(spec.titles),
                "Texts": list(spec.texts),
                "Href": spec.landing,
            },
        }
        payload = base.direct_call(token, "ads", "add", {"Ads": [item]})
        ids[spec.name] = base.add_ids(payload, 1, f"ads.add:{spec.name}")[0]
        created.append(spec.name)
    return ids, created


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Idempotently create or resume the inert Eksamio Direct Search campaign. "
            "Search and Network must remain SERVING_OFF throughout reconciliation."
        )
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-inert-create", action="store_true")
    args = parser.parse_args()

    if not args.apply:
        summary = base.dry_run_summary()
        summary["reconcile_mode"] = True
        summary["rerun_safe"] = True
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    if not args.confirm_inert_create:
        parser.error("--apply requires --confirm-inert-create")

    token = base.keychain_token()
    base.verify_operator(token)
    campaign_id, campaign_created = ensure_campaign(token)
    group_ids, groups_created = ensure_groups(token, campaign_id)
    keyword_total, keywords_created = ensure_keywords(token, group_ids)
    ad_ids, ads_created = ensure_ads(token, group_ids)
    verify_inert_campaign(get_campaign(token, campaign_id))

    print(
        json.dumps(
            {
                "status": "INERT_PROVIDER_OBJECTS_RECONCILED",
                "campaign_id": campaign_id,
                "campaign_name": base.CAMPAIGN_NAME,
                "campaign_created_this_run": campaign_created,
                "groups_total": len(group_ids),
                "groups_created_this_run": groups_created,
                "keywords_total": keyword_total,
                "keywords_created_this_run": keywords_created,
                "ads_total": len(ad_ids),
                "ads_created_this_run": ads_created,
                "operator_login_verified": True,
                "client_login": base.CLIENT_LOGIN,
                "metrika_counter_id": base.METRIKA_COUNTER_ID,
                "search_serving": "OFF",
                "network_serving": "OFF",
                "paid_delivery_started": False,
                "weekly_budget_set": False,
                "token_value_printed": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
