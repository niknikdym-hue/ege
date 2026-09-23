#!/usr/bin/env python3
"""Loopback-only, production-shaped Eksamio learner loop.

This runtime composes the accepted identity, EvidenceEvent, shared PEIS and NBA
boundaries into one executable owner-test slice.  It is deliberately unable to
bind publicly and uses the repository's non-production delivery provider.  It
is therefore STAGING evidence, never a production endpoint or mock PEIS state.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import secrets
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from http import cookies
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
REPO = ENGINE.parent
PRO_CLIENT = REPO / "eksamio-pro-client"
TRAINER = ENGINE / "russkiy-knigi" / "ege-russkiy-trenazher"

sys.path[:0] = [
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-reference-kernel"),
    str(ENGINE / "peis-integration-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-trusted-host-reference"),
    str(ENGINE / "identity-reference"),
]

from passwordless_identity import (  # noqa: E402
    IdentityAuthStore,
    InvalidSession,
    NonProductionCaptureDeliveryProvider,
    PasswordlessIdentityService,
)
from peis_persistence import IntegrityConflict, PeisPersistenceStore  # noqa: E402
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_service_bridge import (  # noqa: E402
    AdapterRegistry,
    HostIdentity,
    PeisServiceBridge,
    ServiceRequestError,
    UnknownAdapter,
)
from peis_trusted_host import InvalidHostToken, TrustedHostIdentityResolver  # noqa: E402
from russian_checked_card_adapter import RussianEgeTrainerTask12Adapter  # noqa: E402
from russian_exceptions_practice_adapter import (  # noqa: E402
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)

ANON_COOKIE = TrustedHostIdentityResolver.COOKIE_NAME
SESSION_COOKIE = PasswordlessIdentityService.SESSION_COOKIE_NAME
EXACT_SEMANTIC_ID = "school-i-e-alternating-verb-roots-stressed-a"
EXACT_SEMANTIC_TITLE = "Чередование Е/И: исключение «сочетать»"
MAX_BODY_BYTES = 64 * 1024
TILDA_BLOCKS = ("01", "02", "03", "04", "05", "06", "07", "08", "10", "11")


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cookie_value(header: str | None, name: str) -> str | None:
    jar = cookies.SimpleCookie()
    try:
        jar.load(header or "")
    except cookies.CookieError:
        return None
    morsel = jar.get(name)
    return morsel.value if morsel else None


def _loopback_cookie(name: str, value: str, *, max_age: int) -> str:
    return f"{name}={value}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax"


class VerificationAwarePracticeAdapter:
    """Server-only wrapper that marks a post-Tutor attempt as verification."""

    adapter_id = RussianExceptionsPracticeAdapter.adapter_id
    subject_id = "russian"

    def __init__(self, base: RussianExceptionsPracticeAdapter, app: "LiveStudentLoop") -> None:
        self.base = base
        self.app = app

    def stable_event_id(self, payload: Mapping[str, Any]) -> str:
        return self.base.stable_event_id(payload)

    def build_observation(self, payload: Mapping[str, Any], *, host_identity: HostIdentity, server_position: Any):
        adapted = self.base.build_observation(payload, host_identity=host_identity, server_position=server_position)
        pending = self.app.tutor_context_for_attempt(
            host_identity.learner_profile_id,
            str(payload.get("card_id", "")),
            self.base.stable_event_id(payload),
        )
        if pending:
            adapted.event["transfer_context"] = {
                "kind": "SAME_SESSION_VERIFICATION",
                "origin_event_refs": [pending["help_event_id"]],
            }
            adapted.event["retention_context"] = {
                "kind": "SAME_SESSION",
                "delay_seconds": max(0, int(time.time()) - int(pending["helped_at_epoch"])),
                "scheduled_by_policy_version": None,
            }
            adapted.event["subject_extension"]["subject_payload"]["independent_verification"] = True
        return adapted


@dataclass(frozen=True)
class ResolvedRequestIdentity:
    host: HostIdentity
    authenticated: bool


class LiveStudentLoop:
    """Composes accepted components without introducing a second learner model."""

    def __init__(self, database_path: Path, secret: bytes, *, owner_test: bool = True) -> None:
        if len(secret) < 32:
            raise ValueError("EKSAMIO_STAGING_HMAC_KEY must be at least 32 bytes")
        self.owner_test = bool(owner_test)
        evidence_schema = json.loads((ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text())
        nba_schema = json.loads((ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text())
        self.store = PeisPersistenceStore(database_path, evidence_schema=evidence_schema, nba_schema=nba_schema)
        self._create_loop_schema()
        signing = hashlib.sha256(secret + b"|host-signing").digest()
        contact = hashlib.sha256(secret + b"|contact-hmac").digest()
        verify = hashlib.sha256(secret + b"|verification-hmac").digest()
        self.host_identity = TrustedHostIdentityResolver(
            store=self.store,
            signing_keys={"staging-v1": signing},
            active_key_id="staging-v1",
        )
        self.delivery = NonProductionCaptureDeliveryProvider()
        self.identity = PasswordlessIdentityService(
            peis_store=self.store,
            trusted_host_resolver=self.host_identity,
            auth_store=IdentityAuthStore(self.store.connection),
            delivery_provider=self.delivery,
            contact_hmac_key=contact,
            verification_hmac_key=verify,
        )
        registry = AdapterRegistry()
        registry.register(RussianEgeTrainerTask12Adapter(ENGINE))
        registry.register(VerificationAwarePracticeAdapter(RussianExceptionsPracticeAdapter(ENGINE), self))
        self.bridge = PeisServiceBridge(store=self.store, registry=registry, kernel_snapshot=kernel_snapshot)
        practice = json.loads((ENGINE / "92-RUSSIAN-EXCEPTIONS-PRACTICE-PILOT-v0.1.json").read_text())
        self.practice = next(row for row in practice["items"] if row["practice_item_id"] == FIRST_SLICE_CARD_ID)

    def close(self) -> None:
        self.store.close()

    def _create_loop_schema(self) -> None:
        self.store.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tutor_contexts (
                context_id TEXT PRIMARY KEY,
                learner_profile_id TEXT NOT NULL,
                card_id TEXT NOT NULL,
                error_event_id TEXT NOT NULL,
                help_event_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                helped_at_epoch BIGINT NOT NULL,
                verified_event_id TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tutor_context_error
                ON tutor_contexts(learner_profile_id, error_event_id);
            """
        )
        self.store.connection.commit()

    def ensure_anonymous(self, token: str | None) -> tuple[HostIdentity, str | None]:
        if token:
            try:
                return self.host_identity.resolve(token), None
            except InvalidHostToken:
                pass
        issued = self.host_identity.issue_anonymous()
        return issued.host_identity, _loopback_cookie(ANON_COOKIE, issued.token, max_age=30 * 24 * 60 * 60)

    def resolve(self, session_token: str | None, anonymous_token: str | None) -> ResolvedRequestIdentity:
        if session_token:
            try:
                return ResolvedRequestIdentity(self.identity.resolve_session(session_token), True)
            except InvalidSession:
                pass
        host, _ = self.ensure_anonymous(anonymous_token)
        return ResolvedRequestIdentity(host, False)

    def test_login(self, anonymous_token: str) -> tuple[dict[str, Any], str]:
        if not self.owner_test:
            raise PermissionError("owner test login is disabled")
        receipt = self.identity.begin(
            {"channel": "email", "contact": "owner-test@learner.invalid"},
            anonymous_host_token=anonymous_token,
        )
        auth = self.identity.verify({"challenge_id": receipt.challenge_id, "code": self.delivery.code_for(receipt.challenge_id)})
        return (
            {
                "authenticated": True,
                "display_label": "Тестовый ученик",
                "anonymous_link_status": auth.anonymous_link_status,
                "identity_owner": "server",
            },
            _loopback_cookie(SESSION_COOKIE, auth.token, max_age=30 * 24 * 60 * 60),
        )

    def logout(self, token: str | None) -> str:
        if token:
            self.identity.logout(token)
        return _loopback_cookie(SESSION_COOKIE, "", max_age=0)

    def submit_trainer(self, request: Mapping[str, Any], host: HostIdentity) -> dict[str, Any]:
        result = self.bridge.submit_checked_card(
            adapter_id=str(request.get("adapter_id", "")),
            payload=request.get("payload", {}),
            host_identity=host,
        )
        result["owner_diagnostic"] = self.diagnostics(host.learner_profile_id)
        return result

    def pending_tutor_context(self, learner_profile_id: str, card_id: str) -> Mapping[str, Any] | None:
        return self.store.connection.execute(
            """
            SELECT * FROM tutor_contexts
            WHERE learner_profile_id = ? AND card_id = ? AND status = 'VERIFICATION_REQUIRED'
            ORDER BY helped_at_epoch DESC LIMIT 1
            """,
            (learner_profile_id, card_id),
        ).fetchone()

    def tutor_context_for_attempt(self, learner_profile_id: str, card_id: str, event_id: str) -> Mapping[str, Any] | None:
        return self.store.connection.execute(
            """
            SELECT * FROM tutor_contexts
            WHERE learner_profile_id = ? AND card_id = ?
              AND (status = 'VERIFICATION_REQUIRED' OR verified_event_id = ?)
            ORDER BY helped_at_epoch DESC LIMIT 1
            """,
            (learner_profile_id, card_id, event_id),
        ).fetchone()

    def _position(self, host: HostIdentity, event_id: str):
        return self.bridge._position_for_new_event(  # shared service sequencing contract
            learner_profile_id=host.learner_profile_id,
            subject_id="russian",
            event_id=event_id,
        )

    def _append_tutor_help(self, host: HostIdentity, error_event: Mapping[str, Any], context_id: str) -> str:
        event_id = "tutorhelp.ev." + _digest(context_id)
        if self.store.raw_event(event_id):
            return event_id
        position = self._position(host, event_id)
        event = {
            "event_id": event_id,
            "idempotency_key": "tutorhelp.idem." + _digest(context_id),
            "schema_version": "0.1.0",
            "event_kind": "PERFORMANCE_OBSERVATION",
            "learner_profile_id": host.learner_profile_id,
            "identity_refs": dict(host.identity_refs),
            "subject_id": "russian",
            "semantic_targets": [{
                "semantic_id": EXACT_SEMANTIC_ID,
                "target_role": "PRIMARY",
                "mapping_resolution": "EXACT",
                "mapping_confidence": None,
                "mapping_review_status": "accepted",
            }],
            "semantic_context": {
                "semantic_registry_version": "russian-school-185+ru1-12-current",
                "semantic_mapping_version": "russian-exceptions-121-semantic-mapping-v1.0",
                "mapping_artifact_refs": ["russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json"],
            },
            "source": {
                "object_type": "tutor_turn",
                "object_id": context_id,
                "content_version": "grounded-owner-test-v1",
                "item_version": "reviewed-v1",
                "route_metadata": {"exam": "EGE", "exam_year": None, "task_route": None, "historical_format": False},
            },
            "product": {"source_type": "tutor", "product_id": "eksamio-tutor", "route": "/pro/#tutor"},
            "session_id": context_id,
            "timestamps": {
                "occurred_at_client": _utc_now(),
                "received_at_server": position.received_at_server,
                "server_sequence": position.server_sequence,
                "server_watermark": position.server_watermark,
            },
            "result": {
                "attempt_index": None,
                "outcome": "NOT_APPLICABLE",
                "correctness": None,
                "score": None,
                "max_score": None,
                "response_value": None,
                "result_details": {"error_event_id": error_event["event_id"], "verification_required": True},
            },
            "response_mode": "NO_RESPONSE",
            "assistance": {"level": "RULE_EXPLANATION", "help_event_refs": [], "assistance_provider": "DETERMINISTIC_STAGING_NO_AI"},
            "evaluator": {
                "evaluator_type": "DETERMINISTIC_VALIDATOR",
                "evaluator_id": "eksamio-grounded-tutor-context",
                "evaluator_version": "owner-test-v1",
                "trust_class": "DETERMINISTIC_HIGH",
                "uncertainty": 0.0,
                "review_status": "not_required",
                "rubric_version": None,
                "official_truth_status": "EDUCATIONAL_NON_OFFICIAL",
            },
            "provenance_refs": [
                "92-RUSSIAN-EXCEPTIONS-PRACTICE-PILOT-v0.1.json",
                "russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json",
            ],
            "transfer_context": {"kind": "NOT_APPLICABLE", "origin_event_refs": [error_event["event_id"]]},
            "retention_context": {"kind": "NONE", "delay_seconds": None, "scheduled_by_policy_version": None},
            "error_observations": [],
            "subject_extension": {
                "subject_payload_schema_version": "russian-tutor-help-v1",
                "subject_payload": {"context_id": context_id, "error_event_id": error_event["event_id"]},
            },
            "created_at": position.received_at_server,
        }
        self.store.append_event(event)
        recommendation_id = "nba.loop." + _digest(host.learner_profile_id + "|" + event_id)
        snapshot = self.store.recompute_snapshot(
            learner_profile_id=host.learner_profile_id,
            subject_id="russian",
            semantic_id=EXACT_SEMANTIC_ID,
            admitted_edges=[],
            goal_context=self.practice.get("context_signature"),
            kernel_snapshot=kernel_snapshot,
            meaningful_help_delivered_for=[EXACT_SEMANTIC_ID],
            recommendation_id=recommendation_id,
        )
        self.store.append_recommendation(snapshot["nba"])
        return event_id

    def tutor_turn(self, host: HostIdentity, message: str) -> dict[str, Any]:
        if not isinstance(message, str) or not message.strip():
            raise ServiceRequestError("Tutor message is required")
        events = self.store.list_events(host.learner_profile_id, "russian", semantic_id=EXACT_SEMANTIC_ID)
        wrong = next(
            (event for event in reversed(events) if event["source"]["object_id"] == FIRST_SLICE_CARD_ID and event["result"]["outcome"] == "INCORRECT"),
            None,
        )
        if wrong is None:
            raise ServiceRequestError("No exact accepted error is available for Tutor context")
        context_id = "tutorctx." + _digest(host.learner_profile_id + "|" + wrong["event_id"])
        help_event_id = self._append_tutor_help(host, wrong, context_id)
        now_epoch = int(time.time())
        with self.store.connection:
            self.store.connection.execute(
                """
                INSERT INTO tutor_contexts(
                    context_id, learner_profile_id, card_id, error_event_id,
                    help_event_id, status, created_at, helped_at_epoch, verified_event_id
                ) VALUES (?, ?, ?, ?, ?, 'VERIFICATION_REQUIRED', ?, ?, NULL)
                ON CONFLICT(context_id) DO NOTHING
                """,
                (context_id, host.learner_profile_id, FIRST_SLICE_CARD_ID, wrong["event_id"], help_event_id, _utc_now(), now_epoch),
            )
        answer = wrong["result"].get("response_value")
        explanation = self.practice["feedback"]["why"]
        correct_answer = self.practice["answer"]["text"]
        return {
            "status": "TUTOR_ADVISORY_STAGING",
            "provider_mode": "DETERMINISTIC_STAGING_NO_AI",
            "context_id": context_id,
            "card_id": FIRST_SLICE_CARD_ID,
            "answer_received": answer,
            "error_event_id": wrong["event_id"],
            "accepted_source_refs": [f"source:russian-reviewed-card:{FIRST_SLICE_CARD_ID}"],
            "verification_required": True,
            "text": f"Вижу вашу ошибку в слове «{answer or '—'}». {explanation} Проверочный ориентир — «{correct_answer}». Теперь выполните новое задание самостоятельно.",
        }

    def submit_practice(self, host: HostIdentity, payload: Mapping[str, Any]) -> dict[str, Any]:
        allowed = {"card_id", "answer", "attempt_started_at_ms", "client_request_id"}
        if set(payload) != allowed:
            raise ServiceRequestError("practice payload fields are invalid")
        request = {
            "card_id": payload["card_id"],
            "answer": payload["answer"],
            "session_started_at_ms": payload["attempt_started_at_ms"],
            "session_mode": "practice",
            "occurred_at_client": datetime.fromtimestamp(
                int(payload["attempt_started_at_ms"]) / 1000,
                tz=timezone.utc,
            ).isoformat(),
            "client_request_id": payload["client_request_id"],
        }
        result = self.bridge.submit_checked_card(
            adapter_id=RussianExceptionsPracticeAdapter.adapter_id,
            payload=request,
            host_identity=host,
        )
        event = self.store.raw_event(result["event_receipt"]["event_id"])
        if event is None:
            raise RuntimeError("accepted practice event unavailable")
        correct = event["result"]["outcome"] == "CORRECT"
        pending = self.pending_tutor_context(host.learner_profile_id, str(payload["card_id"]))
        if pending and correct:
            with self.store.connection:
                self.store.connection.execute(
                    """
                    UPDATE tutor_contexts SET status='VERIFIED', verified_event_id=?
                    WHERE context_id=? AND status='VERIFICATION_REQUIRED'
                    """,
                    (event["event_id"], pending["context_id"]),
                )
        feedback = (
            "Верно. Сервер принял независимую проверку."
            if correct else
            f"Пока неверно. Проверенный ответ: {self.practice['answer']['text']}. {self.practice['feedback']['why']}"
        )
        return {
            "status": result["status"],
            "correct": correct,
            "score": event["result"].get("score"),
            "max_score": event["result"].get("max_score"),
            "feedback": feedback,
            "event": {"event_id": event["event_id"], "server_sequence": event["timestamps"]["server_sequence"]},
            "next_best_action": result["directive"]["action_type"],
            "verification_completed": bool(correct and event["transfer_context"]["kind"] == "SAME_SESSION_VERIFICATION"),
            "directive": result["directive"],
        }

    def practice_card(self, learner_profile_id: str) -> dict[str, Any]:
        pending = self.pending_tutor_context(learner_profile_id, FIRST_SLICE_CARD_ID)
        return {
            "card_id": FIRST_SLICE_CARD_ID,
            "semantic_id": EXACT_SEMANTIC_ID,
            "rule_title": EXACT_SEMANTIC_TITLE,
            "explanation": self.practice["feedback"]["why"],
            "prompt": self.practice["prompt"]["text"],
            "worked": self.practice["feedback"].get("rule", self.practice["feedback"]["why"]),
            "source_ref": f"source:russian-reviewed-card:{FIRST_SLICE_CARD_ID}",
            "verification_required": bool(pending),
        }

    def _snapshot(self, learner_profile_id: str) -> dict[str, Any] | None:
        return self.store.load_materialized_snapshot(
            learner_profile_id,
            "russian",
            EXACT_SEMANTIC_ID,
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

    def profile(self, learner_profile_id: str, *, grade: int, route: str) -> dict[str, Any]:
        events = self.store.list_events(learner_profile_id, "russian")
        attempts = [e for e in events if e["result"]["outcome"] in {"CORRECT", "INCORRECT", "PARTIAL"}]
        correct = sum(e["result"]["outcome"] == "CORRECT" for e in attempts)
        errors = sum(e["result"]["outcome"] == "INCORRECT" for e in attempts)
        exact_events = [e for e in events if any(t["semantic_id"] == EXACT_SEMANTIC_ID and t["mapping_resolution"] == "EXACT" for t in e["semantic_targets"])]
        pending = self.pending_tutor_context(learner_profile_id, FIRST_SLICE_CARD_ID)
        snapshot = self._snapshot(learner_profile_id)
        action = snapshot["nba"]["action_type"] if snapshot else "DIAGNOSE_TARGET"
        action_title, action_reason = self._human_action(action)
        mastery = snapshot["state"]["mastery"] if snapshot else {"band": "NOT_ESTABLISHED", "status": "INSUFFICIENT_EVIDENCE"}
        if not exact_events:
            skill_status = "Недостаточно данных"
        elif pending:
            skill_status = "Нужно повторить"
        elif mastery["band"] in {"STRONG", "ESTABLISHED"}:
            skill_status = "Уверенно"
        else:
            skill_status = "Требует внимания"
        changes = []
        for event in reversed(events[-6:]):
            outcome = event["result"]["outcome"]
            if event["product"]["source_type"] == "tutor":
                text = "Tutor объяснил правило; требуется независимая проверка"
            elif outcome == "CORRECT":
                text = f"{EXACT_SEMANTIC_TITLE}: самостоятельный ответ верный"
            elif outcome == "INCORRECT" and any(t["mapping_resolution"] == "EXACT" for t in event["semantic_targets"]):
                text = f"{EXACT_SEMANTIC_TITLE}: требуется повторение"
            else:
                text = "Задание 12: попытка сохранена без точного вывода о навыке"
            changes.append({"title": text, "timestamp": event["timestamps"]["received_at_server"]})
        return {
            "grade": grade,
            "route": route,
            "today": {"solved": len(attempts), "correct": correct, "errors": errors, "review": errors},
            "readiness": None,
            "readiness_label": skill_status,
            "focus_count": 1 if events else 0,
            "retention_due": 1 if action == "RETENTION_REVIEW" else 0,
            "skills": [{"title": EXACT_SEMANTIC_TITLE, "status": skill_status}],
            "latest_changes": changes,
            "next_best_action": {
                "action_type": action,
                "title": action_title,
                "reason": action_reason,
                "canonical_state_owner": "shared_peis",
                "verification_required": bool(snapshot and snapshot["nba"]["verification_required"]),
                "revision": snapshot["nba"]["learner_state_watermark"] if snapshot else None,
            },
        }

    def plan(self, learner_profile_id: str, *, grade: int, route: str) -> list[dict[str, str]]:
        profile = self.profile(learner_profile_id, grade=grade, route=route)
        action = profile["next_best_action"]
        first_state = "сейчас" if profile["today"]["errors"] else "готово"
        return [
            {"title": "Сохранить попытку", "detail": "Ответ и проверка принимаются сервером", "state": first_state},
            {"title": action["title"], "detail": action["reason"], "state": "сейчас"},
            {"title": "Вернуться по расписанию", "detail": "Retention появится только после независимого evidence", "state": "далее"},
        ]

    def history(self, learner_profile_id: str) -> list[dict[str, Any]]:
        rows = []
        for event in reversed(self.store.list_events(learner_profile_id, "russian")[-20:]):
            outcome = event["result"]["outcome"]
            if event["product"]["source_type"] == "tutor":
                next_step = "Пройти независимую проверку"
            elif event["transfer_context"]["kind"] == "SAME_SESSION_VERIFICATION" and outcome == "CORRECT":
                next_step = "Вернуться к навыку позже"
            elif any(target["mapping_resolution"] == "EXACT" for target in event["semantic_targets"]):
                next_step = "Разобрать ошибку" if outcome == "INCORRECT" else "Вернуться к навыку позже"
            else:
                next_step = "Уточнить слабое место"
            rows.append({
                "timestamp": event["timestamps"]["received_at_server"],
                "session": event["session_id"],
                "kind": "Tutor" if event["product"]["source_type"] == "tutor" else "Тренировка",
                "solved": 0 if outcome == "NOT_APPLICABLE" else 1,
                "correct": 1 if outcome == "CORRECT" else 0,
                "errors": 1 if outcome == "INCORRECT" else 0,
                "next": next_step,
            })
        return rows

    def diagnostics(self, learner_profile_id: str) -> dict[str, Any]:
        events = self.store.list_events(learner_profile_id, "russian")
        snapshot = self._snapshot(learner_profile_id)
        context = self.store.connection.execute(
            "SELECT * FROM tutor_contexts WHERE learner_profile_id=? ORDER BY helped_at_epoch DESC LIMIT 1",
            (learner_profile_id,),
        ).fetchone()
        latest = events[-1] if events else None
        steps = [
            ("Attempt captured", bool(events)),
            ("EvidenceEvent sent", bool(events)),
            ("Server accepted", bool(events)),
            ("PEIS updated", snapshot is not None),
            ("Next action recalculated", bool(snapshot and snapshot.get("nba"))),
            ("Tutor context available", context is not None),
            ("Independent verification completed", bool(context and context["status"] == "VERIFIED")),
        ]
        return {
            "mode": "OWNER_TEST_LOOPBACK_ONLY",
            "steps": [{"label": label, "status": "PASS" if passed else "NOT_APPLICABLE"} for label, passed in steps],
            "detail": {
                "event_id": latest["event_id"] if latest else None,
                "attempt_id": latest["session_id"] if latest else None,
                "peis_revision": snapshot["state"]["state_revision"] if snapshot else None,
                "nba_revision": snapshot["nba"]["learner_state_watermark"] if snapshot else None,
                "timestamp": latest["timestamps"]["received_at_server"] if latest else None,
                "tutor_context_id": context["context_id"] if context else None,
                "verification_status": context["status"] if context else None,
            },
        }


class LiveLoopHandler(BaseHTTPRequestHandler):
    server_version = "EksamioLiveStudentLoop/0.1"

    @property
    def app(self) -> LiveStudentLoop:
        return self.server.app  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _send(self, status: int, body: bytes, content_type: str, *, set_cookies: list[str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        for value in set_cookies or []:
            self.send_header("Set-Cookie", value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, value: Any, *, set_cookies: list[str] | None = None) -> None:
        self._send(status, _json_bytes(value), "application/json; charset=utf-8", set_cookies=set_cookies)

    def _cookies(self) -> tuple[str | None, str | None]:
        header = self.headers.get("Cookie")
        return _cookie_value(header, SESSION_COOKIE), _cookie_value(header, ANON_COOKIE)

    def _ensure_anon_cookie(self) -> tuple[HostIdentity, list[str]]:
        _, anon = self._cookies()
        host, new_cookie = self.app.ensure_anonymous(anon)
        return host, [new_cookie] if new_cookie else []

    def _identity(self, *, require_auth: bool = False) -> ResolvedRequestIdentity:
        session, anon = self._cookies()
        resolved = self.app.resolve(session, anon)
        if require_auth and not resolved.authenticated:
            raise PermissionError("AUTHENTICATION_REQUIRED")
        return resolved

    def _body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ServiceRequestError("invalid body length") from exc
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ServiceRequestError("invalid body length")
        value = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value, dict):
            raise ServiceRequestError("JSON object required")
        return value

    def _check_origin(self) -> None:
        origin = self.headers.get("Origin")
        if not origin:
            return
        expected = f"http://{self.headers.get('Host')}"
        if origin != expected:
            raise PermissionError("ORIGIN_REJECTED")

    def _serve_pro(self, relative: str) -> None:
        _host, set_cookies = self._ensure_anon_cookie()
        relative = relative or "index.html"
        if relative == "index.html":
            html = (PRO_CLIENT / "index.html").read_text(encoding="utf-8")
            config = '<script>window.EKSAMIO_PRO_RUNTIME_CONFIG={mode:"http",baseUrl:"",ownerTest:true};</script>'
            html = html.replace('<script src="adapters.js"></script>', config + '<script src="adapters.js"></script>')
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8", set_cookies=set_cookies)
            return
        path = (PRO_CLIENT / relative).resolve()
        if PRO_CLIENT.resolve() not in path.parents or not path.is_file():
            self._json(404, {"error": "NOT_FOUND"})
            return
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self._send(200, path.read_bytes(), mime, set_cookies=set_cookies)

    def _serve_trainer(self) -> None:
        _host, set_cookies = self._ensure_anon_cookie()
        config = '<script>window.EKSAMIO_LEARNER_LOOP_CONFIG={enabled:true,baseUrl:"",proUrl:"/pro/?owner_test=1",ownerTest:true};</script>'
        blocks = []
        for number in TILDA_BLOCKS:
            path = TRAINER / f"ege-russkiy-trenazher-T123-{number}.txt"
            blocks.append(path.read_text(encoding="utf-8").strip())
        html = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Тренажёр ЕГЭ — owner test</title></head><body style="margin:0">' + config + "\n".join(blocks) + "</body></html>"
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8", set_cookies=set_cookies)

    def _do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/trainer", "/trainer/"}:
            self._serve_trainer()
            return
        if parsed.path.startswith("/pro/"):
            self._serve_pro(parsed.path.removeprefix("/pro/"))
            return
        if parsed.path == "/healthz":
            self._json(200, {"status": "ok", "mode": "STAGING_LOOPBACK_ONLY", "canonical_state_owner": "server"})
            return
        if parsed.path == "/api/identity/session":
            resolved = self._identity()
            self._json(200, {"authenticated": resolved.authenticated, "display_label": "Тестовый ученик" if resolved.authenticated else "Гостевой режим", "identity_owner": "server"})
            return
        if parsed.path == "/api/russian/program":
            self._send(200, (PRO_CLIENT / "program-catalog.json").read_bytes(), "application/json; charset=utf-8")
            return
        if parsed.path in {"/api/russian/profile", "/api/russian/plan", "/api/russian/history", "/api/owner/diagnostics", "/api/russian/practice/next", "/api/payments/entitlement"}:
            resolved = self._identity(require_auth=True)
            query = parse_qs(parsed.query)
            grade = int(query.get("grade", ["10"])[0])
            route = query.get("route", ["ege"])[0]
            if parsed.path == "/api/russian/profile":
                value = self.app.profile(resolved.host.learner_profile_id, grade=grade, route=route)
            elif parsed.path == "/api/russian/plan":
                value = self.app.plan(resolved.host.learner_profile_id, grade=grade, route=route)
            elif parsed.path == "/api/russian/history":
                value = self.app.history(resolved.host.learner_profile_id)
            elif parsed.path == "/api/owner/diagnostics":
                if not self.app.owner_test:
                    raise PermissionError("OWNER_MODE_DISABLED")
                value = self.app.diagnostics(resolved.host.learner_profile_id)
            elif parsed.path == "/api/russian/practice/next":
                value = self.app.practice_card(resolved.host.learner_profile_id)
            else:
                value = {"active": True, "test_account": True, "commercial_entitlement": False, "state": "OWNER_TEST_ONLY"}
            self._json(200, value)
            return
        self._json(404, {"error": "NOT_FOUND"})

    def do_GET(self) -> None:  # noqa: N802
        try:
            self._do_GET()
        except PermissionError as exc:
            self._json(401, {"error": str(exc)})
        except (ServiceRequestError, ValueError, KeyError, TypeError) as exc:
            self._json(400, {"error": "INVALID_REQUEST", "detail": str(exc)})
        except Exception:
            self._json(503, {"error": "PROGRESS_TEMPORARILY_NOT_SYNCED"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._check_origin()
            parsed = urlparse(self.path)
            if parsed.path == "/api/identity/demo-continuity":
                _host, anon_cookies = self._ensure_anon_cookie()
                _, anon = self._cookies()
                if not anon:
                    anon = _cookie_value(anon_cookies[0], ANON_COOKIE)
                if not anon:
                    raise RuntimeError("anonymous token unavailable")
                value, session_cookie = self.app.test_login(anon)
                self._json(200, value, set_cookies=anon_cookies + [session_cookie])
                return
            if parsed.path == "/api/identity/logout":
                session, _ = self._cookies()
                self._json(200, {"status": self.app.logout(session)}, set_cookies=[_loopback_cookie(SESSION_COOKIE, "", max_age=0)])
                return
            if parsed.path in {"/v0/checked-card", "/api/peis/checked-card"}:
                resolved = self._identity()
                self._json(200, self.app.submit_trainer(self._body(), resolved.host))
                return
            if parsed.path == "/api/russian/practice/submit":
                resolved = self._identity(require_auth=True)
                self._json(200, self.app.submit_practice(resolved.host, self._body()))
                return
            if parsed.path == "/api/tutor/turn":
                resolved = self._identity(require_auth=True)
                payload = self._body()
                if set(payload) != {"message", "card_id"} or payload.get("card_id") != FIRST_SLICE_CARD_ID:
                    raise ServiceRequestError("Tutor client may send only message and admitted card_id")
                self._json(200, self.app.tutor_turn(resolved.host, str(payload["message"])))
                return
            self._json(404, {"error": "NOT_FOUND"})
        except PermissionError as exc:
            self._json(401, {"error": str(exc)})
        except (ServiceRequestError, UnknownAdapter, ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._json(400, {"error": "INVALID_REQUEST", "detail": str(exc)})
        except IntegrityConflict:
            self._json(409, {"error": "INTEGRITY_CONFLICT"})
        except Exception:
            self._json(503, {"error": "PROGRESS_TEMPORARILY_NOT_SYNCED"})


class LiveLoopServer(HTTPServer):
    def __init__(self, address: tuple[str, int], app: LiveStudentLoop):
        if address[0] not in {"127.0.0.1", "localhost"}:
            raise ValueError("owner-test server may bind only to loopback")
        super().__init__(address, LiveLoopHandler)
        self.app = app


def main() -> int:
    key = os.environ.get("EKSAMIO_STAGING_HMAC_KEY", "").encode("utf-8")
    database = os.environ.get("EKSAMIO_STAGING_DB", "")
    if len(key) < 32 or not database:
        print("EKSAMIO_STAGING_HMAC_KEY (32+ bytes) and EKSAMIO_STAGING_DB are required", file=sys.stderr)
        return 2
    port = int(os.environ.get("EKSAMIO_STAGING_PORT", "8782"))
    app = LiveStudentLoop(Path(database), key, owner_test=True)
    server = LiveLoopServer(("127.0.0.1", port), app)
    print(f"EKSAMIO_LIVE_STUDENT_LOOP_STAGING=http://127.0.0.1:{port}/trainer/")
    try:
        server.serve_forever()
    finally:
        server.server_close()
        app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
