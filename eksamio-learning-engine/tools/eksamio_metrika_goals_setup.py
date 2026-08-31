#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

COUNTER_ID = 110348386
EXPECTED_DOMAIN = "eksamio.ru"
KEYCHAIN_SERVICE = "ProfitEngine-YandexOAuth-Read"
KEYCHAIN_ACCOUNT = "profit-engine"
API_BASE = "https://api-metrika.yandex.net/management/v1"


@dataclass(frozen=True)
class GoalSpec:
    event_id: str
    name: str
    layer: str
    favorite: bool = False
    server_only: bool = False


GOALS = (
    # Learning funnel — quality signals before Pro and diagnostics afterwards.
    GoalSpec("eks_demo_open", "Eksamio — demo open", "learning"),
    GoalSpec("eks_demo_start", "Eksamio — demo start", "learning"),
    GoalSpec("eks_demo_complete", "Eksamio — demo complete", "learning", True),
    GoalSpec("eks_result_to_practice", "Eksamio — result to practice", "learning"),
    GoalSpec("eks_trainer_open", "Eksamio — trainer open", "learning"),
    GoalSpec("eks_trainer_start", "Eksamio — trainer start", "learning"),
    GoalSpec("eks_trainer_meaningful", "Eksamio — meaningful trainer practice", "learning", True),
    GoalSpec("eks_return_learning", "Eksamio — return learning", "learning"),
    # Commercial funnel. Purchase/refund truth is server-owned.
    GoalSpec("eks_pro_offer_view", "Eksamio — Pro offer viewed", "commercial"),
    GoalSpec("eks_pro_intent", "Eksamio — Pro intent", "commercial", True),
    GoalSpec("eks_checkout_start", "Eksamio — checkout started", "commercial", True),
    GoalSpec("eks_purchase", "Eksamio — verified Pro purchase", "commercial", True, True),
    GoalSpec("eks_entitlement_active", "Eksamio — paid entitlement active", "commercial", False, True),
    GoalSpec("eks_refund", "Eksamio — refund or paid entitlement revoke", "commercial", False, True),
    # Referral funnel. Only the visit is browser-eligible; qualification and rewards are server-owned.
    GoalSpec("eks_referral_visit", "Eksamio — referral visit", "referral"),
    GoalSpec("eks_referral_qualified", "Eksamio — referral qualified", "referral", False, True),
    GoalSpec("eks_referral_purchase_verified", "Eksamio — referred purchase verified", "referral", True, True),
    GoalSpec("eks_referral_reward_granted", "Eksamio — referral reward granted", "referral", False, True),
    GoalSpec("eks_referral_reward_reversed", "Eksamio — referral reward reversed", "referral", False, True),
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


def api_request(token: str, method: str, path: str, body: dict | None = None) -> dict:
    data = None
    headers = {
        "Authorization": f"OAuth {token}",
        "Accept": "application/json",
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{API_BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Metrika API HTTP {exc.code}: {payload[:1200]}") from exc


def counter_domain(counter: dict) -> str:
    site = counter.get("site")
    if isinstance(site, str) and site.strip():
        return site.strip().lower()
    site2 = counter.get("site2")
    if isinstance(site2, dict):
        for key in ("domain", "site"):
            value = site2.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
    return ""


def action_event_ids(goal: dict) -> set[str]:
    if goal.get("type") != "action":
        return set()
    result: set[str] = set()
    for condition in goal.get("conditions") or []:
        if not isinstance(condition, dict):
            continue
        # Current API represents the UI "matches" condition as exact. Accept action as
        # well for compatibility with older JavaScript-event representations.
        if condition.get("type") not in {"exact", "action"}:
            continue
        event_id = condition.get("url")
        if isinstance(event_id, str) and event_id:
            result.add(event_id)
    return result


def index_existing(goals: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for goal in goals:
        if not isinstance(goal, dict):
            continue
        for event_id in action_event_ids(goal):
            if event_id in result:
                raise RuntimeError(f"Duplicate JavaScript-event goal already exists for {event_id!r}")
            result[event_id] = goal
    return result


def public_goal_inventory(goals: list[dict]) -> list[dict[str, object]]:
    inventory: list[dict[str, object]] = []
    canonical_ids = {spec.event_id for spec in GOALS}
    for goal in goals:
        if not isinstance(goal, dict):
            continue
        event_ids = sorted(action_event_ids(goal))
        inventory.append(
            {
                "id": goal.get("id"),
                "name": goal.get("name"),
                "type": goal.get("type"),
                "event_ids": event_ids,
                "canonical_match": any(event_id in canonical_ids for event_id in event_ids),
            }
        )
    return inventory


def create_goal(token: str, spec: GoalSpec) -> dict:
    return api_request(
        token,
        "POST",
        f"/counter/{COUNTER_ID}/goals",
        {
            "goal": {
                "name": spec.name,
                "type": "action",
                "is_favorite": spec.favorite,
                "conditions": [{"type": "exact", "url": spec.event_id}],
            }
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory the existing Eksamio Metrika goals and idempotently install only "
            "missing canonical learning/commercial/referral goals"
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create missing canonical goals. Existing goals are never deleted or modified.",
    )
    args = parser.parse_args()

    token = keychain_token()

    counter_response = api_request(token, "GET", f"/counter/{COUNTER_ID}")
    counter = counter_response.get("counter")
    if not isinstance(counter, dict):
        raise RuntimeError("Metrika counter response is missing counter object")

    domain = counter_domain(counter)
    if EXPECTED_DOMAIN not in domain:
        raise RuntimeError(
            f"Counter identity mismatch: expected {EXPECTED_DOMAIN!r}, API returned domain/site {domain!r}"
        )

    goals_response = api_request(token, "GET", f"/counter/{COUNTER_ID}/goals")
    goals = goals_response.get("goals")
    if not isinstance(goals, list):
        raise RuntimeError("Metrika goals response is missing goals list")

    existing = index_existing(goals)
    missing = [spec for spec in GOALS if spec.event_id not in existing]
    created: list[dict[str, object]] = []

    if args.apply:
        for spec in missing:
            result = create_goal(token, spec)
            goal = result.get("goal")
            if not isinstance(goal, dict) or not goal.get("id"):
                raise RuntimeError(f"Goal creation returned invalid response for {spec.event_id!r}")
            created.append(
                {
                    "event_id": spec.event_id,
                    "goal_id": goal.get("id"),
                    "layer": spec.layer,
                    "server_only": spec.server_only,
                }
            )

        verify_response = api_request(token, "GET", f"/counter/{COUNTER_ID}/goals")
        verify_goals = verify_response.get("goals")
        if not isinstance(verify_goals, list):
            raise RuntimeError("Metrika verification response is missing goals list")
        verified = index_existing(verify_goals)
        unresolved = [spec.event_id for spec in GOALS if spec.event_id not in verified]
        final_goals = verify_goals
        if unresolved:
            raise RuntimeError(f"Metrika goal verification failed; still missing: {unresolved}")
    else:
        unresolved = [spec.event_id for spec in missing]
        final_goals = goals

    by_layer = {
        layer: [spec.event_id for spec in GOALS if spec.layer == layer]
        for layer in ("learning", "commercial", "referral")
    }
    server_only = [spec.event_id for spec in GOALS if spec.server_only]

    print(
        json.dumps(
            {
                "status": "READY" if not unresolved else ("APPLIED" if args.apply else "MISSING_GOALS"),
                "mode": "APPLY" if args.apply else "READ_ONLY",
                "counter_id": COUNTER_ID,
                "counter_domain_verified": True,
                "token_source": f"macOS Keychain:{KEYCHAIN_SERVICE}/{KEYCHAIN_ACCOUNT}",
                "token_value_printed": False,
                "existing_goal_inventory": public_goal_inventory(final_goals),
                "existing_goals_preserved": True,
                "canonical_goal_count": len(GOALS),
                "canonical_by_layer": by_layer,
                "server_only_goal_ids": server_only,
                "missing_before": [spec.event_id for spec in missing],
                "created": created,
                "unresolved_after": unresolved,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not unresolved or args.apply else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
