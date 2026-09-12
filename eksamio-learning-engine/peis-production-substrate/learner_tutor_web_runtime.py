#!/usr/bin/env python3
"""Production browser runtime with durable Tutor lifecycle and fail-closed AI.

The existing authenticated learner routes remain owned by learner_web_runtime.
This extension intercepts only /api/tutor/turn, keeps Tutor state in PostgreSQL,
requires the server-owned Pro entitlement, and injects a provider-neutral Tutor
boundary. The production entrypoint uses FailClosedTutorProvider until a real
brain provider passes admission; CI injects DeterministicNoNetworkTutorProvider.
"""
from __future__ import annotations

import json
import os
from http.server import HTTPServer
from typing import Any

import learner_web_runtime as base_web
import runtime as core
from entitlement_read import EntitlementReadError, ProEntitlementReader
from learner_views import RegisteredLearnerViews
from peis_service_bridge import ServiceRequestError
from russian_exceptions_practice_adapter import (
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)
from tutor_lifecycle import (
    FailClosedTutorProvider,
    PostgresTutorLifecycle,
    TutorProviderNotAdmitted,
    build_tutor_aware_bridge,
)


class TutorAwareRegisteredLearnerViews(RegisteredLearnerViews):
    """Render Tutor lineage without creating a second learner-state model."""

    def __init__(
        self,
        *,
        store: Any,
        bridge: Any,
        adapter: RussianExceptionsPracticeAdapter,
        tutor_lifecycle: PostgresTutorLifecycle,
        now_provider=None,
    ) -> None:
        super().__init__(
            store=store,
            bridge=bridge,
            adapter=adapter,
            now_provider=now_provider,
        )
        self.tutor_lifecycle = tutor_lifecycle

    def profile(self, learner_profile_id: str, *, grade: int, route: str) -> dict[str, Any]:
        profile = super().profile(learner_profile_id, grade=grade, route=route)
        pending = self.tutor_lifecycle.pending_context(
            learner_profile_id,
            FIRST_SLICE_CARD_ID,
        )
        if pending is not None:
            profile["readiness_label"] = "Нужно повторить"
            if profile.get("skills"):
                profile["skills"][0]["status"] = "Нужно повторить"
            profile["next_best_action"]["verification_required"] = True
        return profile

    def history(self, learner_profile_id: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        events = self.store.list_events(learner_profile_id, self.adapter.subject_id)
        for event in reversed(events[-20:]):
            outcome = event.get("result", {}).get("outcome")
            source_type = event.get("product", {}).get("source_type")
            transfer_kind = event.get("transfer_context", {}).get("kind")
            if source_type == "tutor":
                kind = "Tutor"
                next_step = "Пройти независимую проверку"
                solved = 0
            else:
                kind = "Тренировка"
                solved = 0 if outcome == "NOT_APPLICABLE" else 1
                if transfer_kind == "SAME_SESSION_VERIFICATION" and outcome == "CORRECT":
                    next_step = "Вернуться к навыку позже"
                elif outcome == "INCORRECT":
                    next_step = "Разобрать ошибку"
                elif outcome == "CORRECT":
                    next_step = "Вернуться к навыку позже"
                else:
                    next_step = "Продолжить практику"
            rows.append(
                {
                    "timestamp": event.get("timestamps", {}).get("received_at_server"),
                    "session": event.get("session_id"),
                    "kind": kind,
                    "solved": solved,
                    "correct": 1 if outcome == "CORRECT" else 0,
                    "errors": 1 if outcome == "INCORRECT" else 0,
                    "next": next_step,
                }
            )
        return rows

    def practice_card(self, learner_profile_id: str) -> dict[str, Any]:
        card = super().practice_card(learner_profile_id)
        card["verification_required"] = (
            self.tutor_lifecycle.pending_context(
                learner_profile_id,
                FIRST_SLICE_CARD_ID,
            )
            is not None
        )
        return card

    def submit_practice(self, host: Any, payload: Any) -> dict[str, Any]:
        result = super().submit_practice(host, payload)
        event_id = str(result["event"]["event_id"])
        event = self.store.raw_event(event_id)
        if (
            result.get("correct") is True
            and event is not None
            and event.get("transfer_context", {}).get("kind")
            == "SAME_SESSION_VERIFICATION"
        ):
            context_id = self.tutor_lifecycle.mark_verified(
                learner_profile_id=host.learner_profile_id,
                card_id=str(payload["card_id"]),
                event_id=event_id,
            )
            result["verification_completed"] = context_id is not None
            if context_id is not None:
                result["verified_tutor_context_id"] = context_id
                result["feedback"] = "Верно. Сервер принял независимую проверку."
        return result


def make_handler(
    runtime: core.Runtime,
    views: TutorAwareRegisteredLearnerViews | None,
    entitlements: ProEntitlementReader | None,
    tutor: PostgresTutorLifecycle | None,
):
    Base = base_web.make_handler(runtime, views, entitlements)

    class Handler(Base):
        server_version = "EksamioLearnerTutorWeb/0.1"

        def do_POST(self):  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path != "/api/tutor/turn":
                super().do_POST()
                return

            cors = self._cors()
            if cors is None:
                return
            host = self._host(cors)
            if host is None:
                return
            if entitlements is None:
                self.send_json(
                    503,
                    {"error": "ENTITLEMENT_UNAVAILABLE"},
                    extra_headers=cors,
                )
                return
            try:
                entitlement = entitlements.status(host.learner_profile_id)
            except EntitlementReadError:
                self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
                return
            except Exception:
                self.send_json(
                    503,
                    {"error": "ENTITLEMENT_UNAVAILABLE"},
                    extra_headers=cors,
                )
                return
            if entitlement.get("active") is not True:
                self.send_json(
                    403,
                    {"error": "PRO_ENTITLEMENT_REQUIRED"},
                    extra_headers=cors,
                )
                return
            if tutor is None:
                self.send_json(
                    503,
                    {"error": "TUTOR_PROVIDER_NOT_ADMITTED"},
                    extra_headers=cors,
                )
                return
            try:
                payload = self.read_json_object()
                if set(payload) != {"message", "card_id"}:
                    raise ServiceRequestError(
                        "Tutor client may send only message and admitted card_id"
                    )
                if payload.get("card_id") != FIRST_SLICE_CARD_ID:
                    raise ServiceRequestError("Tutor card is not admitted")
                result = tutor.turn(
                    host,
                    card_id=str(payload["card_id"]),
                    message=str(payload["message"]),
                )
                self.send_json(200, result, extra_headers=cors)
            except TutorProviderNotAdmitted:
                self.send_json(
                    503,
                    {"error": "TUTOR_PROVIDER_NOT_ADMITTED"},
                    extra_headers=cors,
                )
            except (
                ServiceRequestError,
                ValueError,
                TypeError,
                UnicodeDecodeError,
                json.JSONDecodeError,
            ):
                self.send_json(400, {"error": "INVALID_REQUEST"}, extra_headers=cors)
            except Exception:
                self.send_json(
                    503,
                    {"error": "TUTOR_TEMPORARILY_UNAVAILABLE"},
                    extra_headers=cors,
                )

    return Handler


def main() -> int:
    dsn = os.environ["PEIS_DATABASE_DSN"]
    evidence = json.loads(
        (core.ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text()
    )
    nba = json.loads(
        (core.ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text()
    )
    try:
        store: Any = core.PostgresPeisPersistenceStore(
            dsn,
            evidence_schema=evidence,
            nba_schema=nba,
        )
    except Exception:
        store = core.UnreadyStore()

    runtime = core.build_runtime_from_env(store)
    views: TutorAwareRegisteredLearnerViews | None = None
    entitlements: ProEntitlementReader | None = None
    tutor: PostgresTutorLifecycle | None = None
    if not isinstance(store, core.UnreadyStore):
        try:
            adapter = RussianExceptionsPracticeAdapter(core.ENGINE)
            tutor = PostgresTutorLifecycle(
                store=store,
                position_bridge=runtime.bridge,
                adapter=adapter,
                provider=FailClosedTutorProvider(),
            )
            tutor_bridge = build_tutor_aware_bridge(
                store=store,
                base_adapter=adapter,
                lifecycle=tutor,
            )
            views = TutorAwareRegisteredLearnerViews(
                store=store,
                bridge=tutor_bridge,
                adapter=adapter,
                tutor_lifecycle=tutor,
            )
            entitlements = ProEntitlementReader(store.connection)
        except Exception:
            views = None
            entitlements = None
            tutor = None

    server = HTTPServer(
        (
            os.getenv("PEIS_BIND_HOST", "0.0.0.0"),
            int(os.getenv("PEIS_PORT", "8080")),
        ),
        make_handler(runtime, views, entitlements, tutor),
    )
    server.host_identity = None
    try:
        server.serve_forever()
    finally:
        server.server_close()
        close = getattr(store, "close", None)
        if callable(close):
            close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
