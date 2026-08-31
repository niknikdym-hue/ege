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
    favorite: bool = False


GOALS = (
    GoalSpec("eks_demo_open", "Eksamio — demo open"),
    GoalSpec("eks_demo_start", "Eksamio — demo start"),
    GoalSpec("eks_demo_complete", "Eksamio — demo complete", True),
    GoalSpec("eks_result_to_practice", "Eksamio — result to practice", True),
    GoalSpec("eks_trainer_open", "Eksamio — trainer open"),
    GoalSpec("eks_trainer_start", "Eksamio — trainer start"),
    GoalSpec("eks_trainer_meaningful", "Eksamio — meaningful trainer practice", True),
    GoalSpec("eks_return_learning", "Eksamio — return learning", True),
    GoalSpec("eks_pro_intent", "Eksamio — Pro intent"),
    GoalSpec("eks_purchase", "Eksamio — purchase"),
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


def extract_exact_action(goals: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for goal in goals:
        if goal.get("type") != "action":
            continue
        conditions = goal.get("conditions") or []
        for condition in conditions:
            if not isinstance(condition, dict):
                continue
            if condition.get("type") != "exact":
                continue
            event_id = condition.get("url")
            if isinstance(event_id, str) and event_id:
                if event_id in result:
                    raise RuntimeError(f"Duplicate exact action goal already exists for {event_id!r}")
                result[event_id] = goal
    return result


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
        description="Verify and idempotently install canonical Eksamio JavaScript-event goals in Yandex Metrika"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Create missing goals. Without this flag the command is read-only.",
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

    existing = extract_exact_action(goals)
    missing = [spec for spec in GOALS if spec.event_id not in existing]
    created: list[dict] = []

    if args.apply:
        for spec in missing:
            result = create_goal(token, spec)
            goal = result.get("goal")
            if not isinstance(goal, dict) or not goal.get("id"):
                raise RuntimeError(f"Goal creation returned invalid response for {spec.event_id!r}")
            created.append({"event_id": spec.event_id, "goal_id": goal.get("id")})

        # Read back after mutation and require every canonical goal.
        verify_response = api_request(token, "GET", f"/counter/{COUNTER_ID}/goals")
        verify_goals = verify_response.get("goals")
        if not isinstance(verify_goals, list):
            raise RuntimeError("Metrika verification response is missing goals list")
        verified = extract_exact_action(verify_goals)
        unresolved = [spec.event_id for spec in GOALS if spec.event_id not in verified]
        if unresolved:
            raise RuntimeError(f"Metrika goal verification failed; still missing: {unresolved}")
    else:
        unresolved = [spec.event_id for spec in missing]

    print(
        json.dumps(
            {
                "status": "READY" if not unresolved else ("APPLIED" if args.apply else "MISSING_GOALS"),
                "mode": "APPLY" if args.apply else "READ_ONLY",
                "counter_id": COUNTER_ID,
                "counter_domain_verified": True,
                "token_source": f"macOS Keychain:{KEYCHAIN_SERVICE}/{KEYCHAIN_ACCOUNT}",
                "token_value_printed": False,
                "canonical_goal_count": len(GOALS),
                "existing_before": len(GOALS) - len(missing),
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
