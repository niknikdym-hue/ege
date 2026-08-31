#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DIRECT_BASE = "https://api.direct.yandex.com/json/v501"
KEYCHAIN_SERVICE = "ProfitEngine-YandexOAuth-Read"
KEYCHAIN_ACCOUNT = "profit-engine"
OPERATOR_LOGIN = "reklamadymova"
CLIENT_LOGIN = "dymova"
METRIKA_COUNTER_ID = 110348386
CAMPAIGN_NAME = "EKSAMIO_FREE_EGE_SEARCH_2026"
RUSSIA_REGION_ID = 225
TRACKING_PARAMS = (
    "utm_source=yandex&utm_medium=cpc&utm_campaign={campaign_id}"
    "&utm_content={source_type}.{ad_id}.{gbid}.{device_type}&utm_term={keyword}"
)


@dataclass(frozen=True)
class GroupSpec:
    name: str
    landing: str
    titles: tuple[str, ...]
    texts: tuple[str, ...]
    keywords: tuple[str, ...]
    negatives: tuple[str, ...]


GROUPS = (
    GroupSpec(
        name="Russian EGE 2026",
        landing="https://eksamio.ru/ege/russkiy/demoversiya/",
        titles=(
            "Демоверсия ЕГЭ по русскому 2026",
            "Русский ЕГЭ: полный вариант онлайн",
            "Проверьте знания перед ЕГЭ",
            "Демоверсии русского 2022–2026",
        ),
        texts=(
            "Пройдите полный вариант в экзаменационном режиме. Проверка после завершения.",
            "Демоверсии 2022–2026 и тренажёры по темам. Начните бесплатно.",
        ),
        keywords=(
            "демоверсия егэ русский 2026",
            "егэ русский демоверсия фипи",
            "пробник егэ русский онлайн",
            "пробный егэ русский онлайн",
            "демоверсия русский язык егэ",
            "тренажер егэ русский",
            "подготовка егэ русский демоверсия",
        ),
        negatives=("огэ", "впр", "скачать", "pdf", "ответы", "решебник", "варианты с ответами"),
    ),
    GroupSpec(
        name="Profile Mathematics EGE 2026",
        landing="https://eksamio.ru/ege/matematika-profil/demoversiya/",
        titles=(
            "ЕГЭ профиль: демоверсия 2026",
            "Профильная математика — полный вариант",
            "Проверьте профильную математику",
        ),
        texts=(
            "19 заданий по формату демоверсии ФИПИ. Краткая часть проверяется автоматически.",
            "Полный вариант профильной математики. Результат и критерии после завершения.",
        ),
        keywords=(
            "демоверсия егэ профильная математика 2026",
            "фипи профильная математика демоверсия",
            "пробник егэ профильная математика",
            "пробный егэ профиль математика онлайн",
            "егэ профиль математика полный вариант",
        ),
        negatives=("база", "базовая", "огэ", "скачать", "pdf", "ответы", "решебник"),
    ),
    GroupSpec(
        name="Basic Mathematics EGE 2026",
        landing="https://eksamio.ru/ege/matematika-baza/demoversiya/",
        titles=(
            "ЕГЭ база: демоверсия 2026",
            "Базовая математика — полный вариант",
            "Проверьте базовую математику",
        ),
        texts=(
            "21 задание, 180 минут. Полная попытка с проверкой только после завершения.",
            "Базовая математика по демоверсии ФИПИ. Пройдите вариант бесплатно.",
        ),
        keywords=(
            "демоверсия егэ базовая математика 2026",
            "фипи базовая математика демоверсия",
            "пробник егэ базовая математика",
            "пробный егэ база математика онлайн",
            "егэ базовая математика полный вариант",
        ),
        negatives=("профиль", "профильная", "огэ", "скачать", "pdf", "ответы", "решебник"),
    ),
    GroupSpec(
        name="Physics EGE 2026",
        landing="https://eksamio.ru/ege/fizika/demoversiya/",
        titles=(
            "Демоверсия ЕГЭ по физике 2026",
            "Физика ЕГЭ: полный вариант онлайн",
            "Проверьте знания по физике",
        ),
        texts=(
            "26 заданий, 235 минут. Проверка краткой части и критерии развёрнутых решений.",
            "Физика по демоверсии ФИПИ в экзаменационном режиме. Начните бесплатно.",
        ),
        keywords=(
            "демоверсия егэ физика 2026",
            "фипи физика егэ демоверсия",
            "пробник егэ физика онлайн",
            "пробный егэ физика 2026",
            "егэ физика полный вариант",
        ),
        negatives=("огэ", "впр", "скачать", "pdf", "ответы", "решебник"),
    ),
)


def keychain_token() -> str:
    result = subprocess.run(
        [
            "security",
            "find-generic-password",
            "-s",
            KEYCHAIN_SERVICE,
            "-a",
            KEYCHAIN_ACCOUNT,
            "-w",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Yandex OAuth token is unavailable in macOS Keychain at "
            f"service={KEYCHAIN_SERVICE!r}, account={KEYCHAIN_ACCOUNT!r}"
        )
    token = result.stdout.strip()
    if not token:
        raise RuntimeError("Yandex OAuth token read from Keychain is empty")
    return token


def direct_call(
    token: str,
    service: str,
    method: str,
    params: dict[str, Any],
    *,
    client_login: str | None = CLIENT_LOGIN,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept-Language": "ru",
        "Content-Type": "application/json; charset=utf-8",
    }
    if client_login:
        headers["Client-Login"] = client_login

    body = json.dumps({"method": method, "params": params}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{DIRECT_BASE}/{service}",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Direct API HTTP {exc.code} on {service}.{method}: {text[:1600]}") from exc

    if payload.get("error"):
        raise RuntimeError(f"Direct API error on {service}.{method}: {json.dumps(payload['error'], ensure_ascii=False)}")
    if "result" not in payload:
        raise RuntimeError(f"Direct API response missing result on {service}.{method}")
    return payload


def add_ids(payload: dict[str, Any], expected: int, operation: str) -> list[int]:
    results = payload.get("result", {}).get("AddResults")
    if not isinstance(results, list) or len(results) != expected:
        raise RuntimeError(f"{operation}: unexpected AddResults shape/count")

    ids: list[int] = []
    for index, item in enumerate(results):
        if not isinstance(item, dict):
            raise RuntimeError(f"{operation}: result {index} is not an object")
        errors = item.get("Errors") or []
        if errors:
            raise RuntimeError(f"{operation}: item {index} errors: {json.dumps(errors, ensure_ascii=False)}")
        entity_id = item.get("Id")
        if not isinstance(entity_id, int):
            raise RuntimeError(f"{operation}: item {index} has no numeric Id")
        ids.append(entity_id)
    return ids


def verify_operator(token: str) -> None:
    payload = direct_call(
        token,
        "clients",
        "get",
        {"FieldNames": ["ClientId", "Login", "Type"]},
        client_login=None,
    )
    clients = payload.get("result", {}).get("Clients") or []
    logins = {str(item.get("Login", "")).casefold() for item in clients if isinstance(item, dict)}
    if OPERATOR_LOGIN.casefold() not in logins:
        raise RuntimeError(f"OAuth Direct identity mismatch: expected operator {OPERATOR_LOGIN!r}")


def list_campaigns(token: str) -> list[dict[str, Any]]:
    payload = direct_call(
        token,
        "campaigns",
        "get",
        {
            "SelectionCriteria": {},
            "FieldNames": ["Id", "Name", "Type", "State", "Status"],
            "Page": {"Limit": 10000},
        },
    )
    campaigns = payload.get("result", {}).get("Campaigns")
    if not isinstance(campaigns, list):
        raise RuntimeError("Direct campaigns.get returned invalid Campaigns list")
    return [item for item in campaigns if isinstance(item, dict)]


def campaign_payload(start_date: str) -> dict[str, Any]:
    return {
        "Campaigns": [
            {
                "Name": CAMPAIGN_NAME,
                "StartDate": start_date,
                "TimeZone": "Europe/Moscow",
                "UnifiedCampaign": {
                    "BiddingStrategy": {
                        "Search": {"BiddingStrategyType": "SERVING_OFF"},
                        "Network": {"BiddingStrategyType": "SERVING_OFF"},
                    },
                    "Settings": [
                        {"Option": "ADD_METRICA_TAG", "Value": "YES"},
                        {"Option": "ENABLE_SITE_MONITORING", "Value": "YES"},
                        {"Option": "ALTERNATIVE_TEXTS_ENABLED", "Value": "NO"},
                    ],
                    "CounterIds": {"Items": [METRIKA_COUNTER_ID]},
                    "TrackingParams": TRACKING_PARAMS,
                    "AttributionModel": "AUTO",
                },
            }
        ]
    }


def group_payloads(campaign_id: int) -> list[dict[str, Any]]:
    return [
        {
            "Name": spec.name,
            "CampaignId": campaign_id,
            "RegionIds": [RUSSIA_REGION_ID],
            "NegativeKeywords": {"Items": list(spec.negatives)},
            "UnifiedAdGroup": {"OfferRetargeting": "NO"},
        }
        for spec in GROUPS
    ]


def keyword_payloads(group_ids: list[int]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for group_id, spec in zip(group_ids, GROUPS, strict=True):
        for keyword in spec.keywords:
            result.append({"AdGroupId": group_id, "Keyword": keyword})
    return result


def ad_payloads(group_ids: list[int]) -> list[dict[str, Any]]:
    return [
        {
            "AdGroupId": group_id,
            "ResponsiveAd": {
                "Titles": list(spec.titles),
                "Texts": list(spec.texts),
                "Href": spec.landing,
            },
        }
        for group_id, spec in zip(group_ids, GROUPS, strict=True)
    ]


def dry_run_summary() -> dict[str, Any]:
    return {
        "status": "INERT_CANDIDATE_READY",
        "campaign_name": CAMPAIGN_NAME,
        "operator_login": OPERATOR_LOGIN,
        "client_login": CLIENT_LOGIN,
        "metrika_counter_id": METRIKA_COUNTER_ID,
        "strategy_search": "SERVING_OFF",
        "strategy_network": "SERVING_OFF",
        "spend_possible": False,
        "group_count": len(GROUPS),
        "keyword_count": sum(len(spec.keywords) for spec in GROUPS),
        "ad_count": len(GROUPS),
        "geography_region_id": RUSSIA_REGION_ID,
        "tracking_params": TRACKING_PARAMS,
        "token_value_printed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create an inert/non-serving Eksamio Yandex Direct campaign candidate. "
            "Both Search and Network are created as SERVING_OFF; this command cannot start paid delivery."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Perform Direct API creates. Without this flag no credential or network access is used.",
    )
    parser.add_argument(
        "--confirm-inert-create",
        action="store_true",
        help="Required with --apply. Confirms creation of provider objects with all serving disabled.",
    )
    args = parser.parse_args()

    if not args.apply:
        print(json.dumps(dry_run_summary(), ensure_ascii=False, sort_keys=True))
        return 0
    if not args.confirm_inert_create:
        parser.error("--apply requires --confirm-inert-create")

    token = keychain_token()
    verify_operator(token)

    campaigns = list_campaigns(token)
    existing = [item for item in campaigns if item.get("Name") == CAMPAIGN_NAME]
    if existing:
        raise RuntimeError(
            f"Refusing duplicate campaign creation: exact campaign name already exists ({len(existing)} match(es))"
        )

    today = dt.date.today().isoformat()
    campaign_add = direct_call(token, "campaigns", "add", campaign_payload(today))
    campaign_id = add_ids(campaign_add, 1, "campaigns.add")[0]

    # Campaign is created with Search=SERVING_OFF and Network=SERVING_OFF before any group/ad exists.
    # Any subsequent partial failure leaves a non-serving campaign and therefore cannot start paid traffic.
    groups_add = direct_call(
        token,
        "adgroups",
        "add",
        {"AdGroups": group_payloads(campaign_id)},
    )
    group_ids = add_ids(groups_add, len(GROUPS), "adgroups.add")

    keyword_items = keyword_payloads(group_ids)
    keywords_add = direct_call(token, "keywords", "add", {"Keywords": keyword_items})
    keyword_ids = add_ids(keywords_add, len(keyword_items), "keywords.add")

    ad_items = ad_payloads(group_ids)
    ads_add = direct_call(token, "ads", "add", {"Ads": ad_items})
    ad_ids = add_ids(ads_add, len(ad_items), "ads.add")

    readback = direct_call(
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
    returned = readback.get("result", {}).get("Campaigns") or []
    if len(returned) != 1 or returned[0].get("Id") != campaign_id:
        raise RuntimeError("Campaign read-back identity verification failed")

    print(
        json.dumps(
            {
                "status": "INERT_PROVIDER_OBJECTS_CREATED",
                "campaign_id": campaign_id,
                "campaign_name": CAMPAIGN_NAME,
                "group_ids": group_ids,
                "keyword_count": len(keyword_ids),
                "ad_ids": ad_ids,
                "operator_login_verified": True,
                "client_login": CLIENT_LOGIN,
                "metrika_counter_id": METRIKA_COUNTER_ID,
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
