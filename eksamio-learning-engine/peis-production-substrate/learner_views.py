#!/usr/bin/env python3
"""Authenticated learner views over the canonical PostgreSQL PEIS store.

This module contains no second learner state. It renders the existing accepted
EvidenceEvent/materialized-snapshot truth into the HTTP shapes already consumed
by the Eksamio Pro client. Tutor execution is intentionally outside this module.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping
from zoneinfo import ZoneInfo

from peis_service_bridge import HostIdentity, PeisServiceBridge, ServiceRequestError
from russian_exceptions_practice_adapter import (
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)

REPORTING_TIMEZONE = ZoneInfo("Europe/Moscow")
RULE_TITLE = "Чередование Е/И: исключение «сочетать»"


class RegisteredLearnerViews:
    """Read/write learner facade backed only by the shared PEIS store/bridge."""

    def __init__(
        self,
        *,
        store: Any,
        bridge: PeisServiceBridge,
        adapter: RussianExceptionsPracticeAdapter,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self.store = store
        self.bridge = bridge
        self.adapter = adapter
        self.practice = adapter.practice_by_card[FIRST_SLICE_CARD_ID]
        mapping = adapter.mapping_by_card[FIRST_SLICE_CARD_ID]
        semantic_ids = mapping.get("semantic_target_ids")
        if mapping.get("mapping_resolution") != "EXACT" or not isinstance(semantic_ids, list) or len(semantic_ids) != 1:
            raise ServiceRequestError("first learner web slice requires one accepted EXACT semantic owner")
        self.semantic_id = str(semantic_ids[0])
        self.now_provider = now_provider or (lambda: datetime.now(REPORTING_TIMEZONE))

    def _snapshot(self, learner_profile_id: str) -> dict[str, Any] | None:
        return self.store.load_materialized_snapshot(
            learner_profile_id,
            self.adapter.subject_id,
            self.semantic_id,
            goal_context=self.practice.get("context_signature"),
        )

    @staticmethod
    def _human_action(action: str) -> tuple[str, str]:
        table = {
            "DIAGNOSE_TARGET": ("Уточнить слабое место", "Данных пока недостаточно для вывода о навыке."),
            "GUIDED_PRACTICE": ("Разобрать ошибку", "Последний самостоятельный ответ был неверным."),
            "INDEPENDENT_PRACTICE": ("Пройти независимую проверку", "После помощи Tutor нужен новый ответ без подсказки."),
            "VERIFY_UNCERTAIN_STATE": ("Проверить навык ещё раз", "Evidence противоречиво и требует проверки."),
            "RETENTION_REVIEW": ("Вернуться к навыку позже", "Независимая проверка пройдена; следующий шаг — удержание."),
            "MOVE_TO_NEXT_TARGET": ("Перейти к следующей цели", "Текущая цель подтверждена и удерживается."),
        }
        return table.get(action, ("Продолжить практику", "План пересчитан по принятому evidence."))

    def _today_attempts(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        reporting_day = self.now_provider().astimezone(REPORTING_TIMEZONE).date()
        attempts: list[dict[str, Any]] = []
        for event in events:
            if event.get("result", {}).get("outcome") not in {"CORRECT", "INCORRECT", "PARTIAL"}:
                continue
            raw = event.get("timestamps", {}).get("received_at_server")
            if not isinstance(raw, str) or not raw:
                continue
            received = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if received.tzinfo is None:
                received = received.replace(tzinfo=timezone.utc)
            if received.astimezone(REPORTING_TIMEZONE).date() == reporting_day:
                attempts.append(event)
        return attempts

    def profile(self, learner_profile_id: str, *, grade: int, route: str) -> dict[str, Any]:
        if grade not in {10, 11} or route != "ege":
            raise ServiceRequestError("launch learner profile admits only EGE Russian grades 10-11")
        events = self.store.list_events(learner_profile_id, self.adapter.subject_id)
        today = self._today_attempts(events)
        snapshot = self._snapshot(learner_profile_id)
        action = snapshot["nba"]["action_type"] if snapshot else "DIAGNOSE_TARGET"
        title, reason = self._human_action(action)
        exact_events = [
            event
            for event in events
            if any(
                target.get("semantic_id") == self.semantic_id
                and target.get("mapping_resolution") == "EXACT"
                for target in event.get("semantic_targets", [])
            )
        ]
        mastery = snapshot["state"].get("mastery", {}) if snapshot else {}
        if not exact_events:
            skill_status = "Недостаточно данных"
        elif mastery.get("band") in {"STRONG", "ESTABLISHED"}:
            skill_status = "Уверенно"
        else:
            skill_status = "Требует внимания"

        changes: list[dict[str, str]] = []
        for event in reversed(events[-6:]):
            outcome = event.get("result", {}).get("outcome")
            if outcome == "CORRECT":
                text = f"{RULE_TITLE}: самостоятельный ответ верный"
            elif outcome == "INCORRECT":
                text = f"{RULE_TITLE}: требуется повторение"
            else:
                text = "Попытка сохранена без точного вывода о навыке"
            changes.append(
                {
                    "title": text,
                    "timestamp": str(event.get("timestamps", {}).get("received_at_server") or event.get("created_at") or ""),
                }
            )

        correct = sum(event["result"]["outcome"] == "CORRECT" for event in today)
        errors = sum(event["result"]["outcome"] == "INCORRECT" for event in today)
        nba = snapshot.get("nba", {}) if snapshot else {}
        return {
            "grade": grade,
            "route": route,
            "today": {
                "solved": len(today),
                "correct": correct,
                "errors": errors,
                "review": errors,
            },
            "reporting_timezone": REPORTING_TIMEZONE.key,
            "readiness": None,
            "readiness_label": skill_status,
            "focus_count": 1 if events else 0,
            "retention_due": 1 if action == "RETENTION_REVIEW" else 0,
            "skills": [{"title": RULE_TITLE, "status": skill_status}],
            "latest_changes": changes,
            "next_best_action": {
                "action_type": action,
                "title": title,
                "reason": reason,
                "canonical_state_owner": "shared_peis",
                "verification_required": bool(nba.get("verification_required", False)),
                "revision": nba.get("learner_state_watermark"),
            },
        }

    def plan(self, learner_profile_id: str, *, grade: int, route: str) -> list[dict[str, str]]:
        profile = self.profile(learner_profile_id, grade=grade, route=route)
        action = profile["next_best_action"]
        return [
            {
                "title": "Сохранить попытку",
                "detail": "Ответ и проверка принимаются сервером",
                "state": "готово" if profile["today"]["solved"] else "сейчас",
            },
            {"title": action["title"], "detail": action["reason"], "state": "сейчас"},
            {
                "title": "Вернуться по расписанию",
                "detail": "Retention появляется только из принятого evidence",
                "state": "далее",
            },
        ]

    def history(self, learner_profile_id: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for event in reversed(self.store.list_events(learner_profile_id, self.adapter.subject_id)[-20:]):
            outcome = event.get("result", {}).get("outcome")
            if outcome == "CORRECT":
                next_step = "Вернуться к навыку позже"
            elif outcome == "INCORRECT":
                next_step = "Разобрать ошибку"
            else:
                next_step = "Продолжить практику"
            rows.append(
                {
                    "timestamp": event.get("timestamps", {}).get("received_at_server"),
                    "session": event.get("session_id"),
                    "kind": "Тренировка",
                    "solved": 0 if outcome == "NOT_APPLICABLE" else 1,
                    "correct": 1 if outcome == "CORRECT" else 0,
                    "errors": 1 if outcome == "INCORRECT" else 0,
                    "next": next_step,
                }
            )
        return rows

    def practice_card(self, learner_profile_id: str) -> dict[str, Any]:
        snapshot = self._snapshot(learner_profile_id)
        return {
            "card_id": FIRST_SLICE_CARD_ID,
            "semantic_id": self.semantic_id,
            "rule_title": RULE_TITLE,
            "explanation": self.practice["feedback"]["why"],
            "prompt": self.practice["prompt"]["text"],
            "worked": self.practice["feedback"].get("rule", self.practice["feedback"]["why"]),
            "source_ref": f"source:russian-reviewed-card:{FIRST_SLICE_CARD_ID}",
            "verification_required": bool(snapshot and snapshot.get("nba", {}).get("verification_required")),
        }

    def submit_practice(self, host: HostIdentity, payload: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {"card_id", "answer", "attempt_started_at_ms", "client_request_id"}
        if not isinstance(payload, Mapping) or set(payload) != allowed:
            raise ServiceRequestError("practice payload fields are invalid")
        started = payload.get("attempt_started_at_ms")
        if not isinstance(started, int) or started <= 0:
            raise ServiceRequestError("attempt_started_at_ms must be a positive integer")
        request = {
            "card_id": payload["card_id"],
            "answer": payload["answer"],
            "session_started_at_ms": started,
            "session_mode": "practice",
            "occurred_at_client": datetime.fromtimestamp(started / 1000, tz=timezone.utc).isoformat(),
            "client_request_id": payload["client_request_id"],
        }
        result = self.bridge.submit_checked_card(
            adapter_id=self.adapter.adapter_id,
            payload=request,
            host_identity=host,
        )
        event = self.store.raw_event(result["event_receipt"]["event_id"])
        if event is None:
            raise RuntimeError("accepted practice event unavailable")
        correct = event["result"]["outcome"] == "CORRECT"
        feedback = (
            "Верно. Сервер принял самостоятельный ответ."
            if correct
            else f"Пока неверно. Проверенный ответ: {self.practice['answer']['text']}. {self.practice['feedback']['why']}"
        )
        return {
            "status": result["status"],
            "correct": correct,
            "score": event["result"].get("score"),
            "max_score": event["result"].get("max_score"),
            "feedback": feedback,
            "event": {
                "event_id": event["event_id"],
                "server_sequence": event["timestamps"].get("server_sequence"),
            },
            "next_best_action": result["directive"]["action_type"],
            "verification_completed": bool(
                correct
                and event.get("transfer_context", {}).get("kind") == "SAME_SESSION_VERIFICATION"
            ),
            "directive": result["directive"],
        }
