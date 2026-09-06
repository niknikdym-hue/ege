#!/usr/bin/env python3
"""Durable PostgreSQL Tutor lifecycle over the canonical Eksamio PEIS store.

This module owns only Tutor execution state and immutable Tutor-help lineage.
Learner mastery remains in shared PEIS. A provider is injected behind a narrow
provider-neutral boundary; production can therefore remain fail-closed while CI
proves the lifecycle with a deterministic no-network provider.
"""
from __future__ import annotations

import hashlib
import threading
import time
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol

from peis_reference_kernel import snapshot as kernel_snapshot
from peis_service_bridge import (
    AdaptedObservation,
    AdapterRegistry,
    HostIdentity,
    PeisServiceBridge,
    ServerEventPosition,
    ServiceRequestError,
)
from russian_exceptions_practice_adapter import (
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)

SUBJECT_ID = "russian"
EXACT_SEMANTIC_ID = "school-i-e-alternating-verb-roots-stressed-a"


def _digest(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TutorProviderNotAdmitted(RuntimeError):
    """No production Tutor brain has passed the provider admission gate."""


class TutorProvider(Protocol):
    provider_id: str

    def respond(
        self,
        *,
        message: str,
        context_id: str,
        answer_received: str | None,
        explanation: str,
        correct_answer: str,
        accepted_source_refs: list[str],
    ) -> str:
        ...


class FailClosedTutorProvider:
    provider_id = "not-admitted"

    def respond(
        self,
        *,
        message: str,
        context_id: str,
        answer_received: str | None,
        explanation: str,
        correct_answer: str,
        accepted_source_refs: list[str],
    ) -> str:
        del message, context_id, answer_received, explanation, correct_answer, accepted_source_refs
        raise TutorProviderNotAdmitted("production Tutor provider is not admitted")


class DeterministicNoNetworkTutorProvider:
    """CI-only provider that proves orchestration without network or paid calls."""

    provider_id = "deterministic-no-network"

    def __init__(self) -> None:
        self.calls = 0

    def respond(
        self,
        *,
        message: str,
        context_id: str,
        answer_received: str | None,
        explanation: str,
        correct_answer: str,
        accepted_source_refs: list[str],
    ) -> str:
        if not message.strip():
            raise ServiceRequestError("Tutor message is required")
        if not context_id.startswith("tutorctx."):
            raise ServiceRequestError("Tutor context is invalid")
        if len(accepted_source_refs) != 1 or not accepted_source_refs[0].startswith(
            "source:russian-reviewed-card:"
        ):
            raise ServiceRequestError("Tutor grounding is not accepted")
        self.calls += 1
        return (
            f"Вижу вашу ошибку в слове «{answer_received or '—'}». "
            f"{explanation} Проверочный ориентир — «{correct_answer}». "
            "Теперь выполните новое задание самостоятельно."
        )


class VerificationAwarePracticeAdapter:
    """Mark the next independent attempt after Tutor help as verification evidence."""

    adapter_id = RussianExceptionsPracticeAdapter.adapter_id
    subject_id = RussianExceptionsPracticeAdapter.subject_id

    def __init__(
        self,
        base: RussianExceptionsPracticeAdapter,
        lifecycle: "PostgresTutorLifecycle",
    ) -> None:
        self.base = base
        self.lifecycle = lifecycle

    def stable_event_id(self, payload: Mapping[str, Any]) -> str:
        return self.base.stable_event_id(payload)

    def build_observation(
        self,
        payload: Mapping[str, Any],
        *,
        host_identity: HostIdentity,
        server_position: ServerEventPosition,
    ) -> AdaptedObservation:
        adapted = self.base.build_observation(
            payload,
            host_identity=host_identity,
            server_position=server_position,
        )
        pending = self.lifecycle.pending_context(
            host_identity.learner_profile_id,
            str(payload.get("card_id", "")),
        )
        if pending is None:
            return adapted

        help_event_id = str(pending["help_event_id"])
        helped_at_epoch = int(pending["helped_at_epoch"])
        adapted.event["transfer_context"] = {
            "kind": "SAME_SESSION_VERIFICATION",
            "origin_event_refs": [help_event_id],
        }
        adapted.event["retention_context"] = {
            "kind": "SAME_SESSION",
            "delay_seconds": max(0, int(time.time()) - helped_at_epoch),
            "scheduled_by_policy_version": None,
        }
        payload_extension = adapted.event["subject_extension"]["subject_payload"]
        payload_extension["independent_verification"] = True
        payload_extension["tutor_context_id"] = str(pending["context_id"])
        return adapted


class PostgresTutorLifecycle:
    """Server-owned Tutor context state + immutable PEIS help lineage."""

    def __init__(
        self,
        *,
        store: Any,
        position_bridge: PeisServiceBridge,
        adapter: RussianExceptionsPracticeAdapter,
        provider: TutorProvider,
    ) -> None:
        self.store = store
        self.position_bridge = position_bridge
        self.adapter = adapter
        self.provider = provider
        self._lock = threading.RLock()
        self.practice = adapter.practice_by_card[FIRST_SLICE_CARD_ID]
        mapping = adapter.mapping_by_card[FIRST_SLICE_CARD_ID]
        semantic_ids = mapping.get("semantic_target_ids")
        if (
            mapping.get("mapping_resolution") != "EXACT"
            or not isinstance(semantic_ids, list)
            or semantic_ids != [EXACT_SEMANTIC_ID]
        ):
            raise ServiceRequestError(
                "Tutor launch slice requires the accepted exact first-card semantic"
            )

    def pending_context(
        self,
        learner_profile_id: str,
        card_id: str,
    ) -> Mapping[str, Any] | None:
        return self.store.connection.execute(
            """
            SELECT *
            FROM tutor_contexts
            WHERE learner_profile_id = ?
              AND card_id = ?
              AND status = 'VERIFICATION_REQUIRED'
            ORDER BY lineage DESC
            LIMIT 1
            """,
            (learner_profile_id, card_id),
        ).fetchone()

    def contexts(self, learner_profile_id: str, card_id: str) -> list[Mapping[str, Any]]:
        return list(
            self.store.connection.execute(
                """
                SELECT *
                FROM tutor_contexts
                WHERE learner_profile_id = ? AND card_id = ?
                ORDER BY lineage
                """,
                (learner_profile_id, card_id),
            ).fetchall()
        )

    def _latest_wrong_event(self, learner_profile_id: str) -> Mapping[str, Any]:
        events = self.store.list_events(
            learner_profile_id,
            SUBJECT_ID,
            semantic_id=EXACT_SEMANTIC_ID,
        )
        wrong = next(
            (
                event
                for event in reversed(events)
                if event.get("source", {}).get("object_id") == FIRST_SLICE_CARD_ID
                and event.get("result", {}).get("outcome") == "INCORRECT"
            ),
            None,
        )
        if wrong is None:
            raise ServiceRequestError(
                "No exact accepted error is available for Tutor context"
            )
        return wrong

    def _next_lineage(self, learner_profile_id: str, card_id: str) -> int:
        row = self.store.connection.execute(
            """
            SELECT COALESCE(MAX(lineage), 0) AS max_lineage
            FROM tutor_contexts
            WHERE learner_profile_id = ? AND card_id = ?
            """,
            (learner_profile_id, card_id),
        ).fetchone()
        return int(row["max_lineage"]) + 1

    def _append_help_event(
        self,
        *,
        host: HostIdentity,
        wrong: Mapping[str, Any],
        context_id: str,
        tutor_text: str,
    ) -> str:
        event_id = "tutorhelp.ev." + _digest(context_id)
        if self.store.raw_event(event_id) is not None:
            return event_id

        position = self.position_bridge._position_for_new_event(
            learner_profile_id=host.learner_profile_id,
            subject_id=SUBJECT_ID,
            event_id=event_id,
        )
        provider_id = str(self.provider.provider_id)
        event = {
            "event_id": event_id,
            "idempotency_key": "tutorhelp.idem." + _digest(context_id),
            "schema_version": "0.1.0",
            "event_kind": "PERFORMANCE_OBSERVATION",
            "learner_profile_id": host.learner_profile_id,
            "identity_refs": dict(host.identity_refs),
            "subject_id": SUBJECT_ID,
            "semantic_targets": [
                {
                    "semantic_id": EXACT_SEMANTIC_ID,
                    "target_role": "PRIMARY",
                    "mapping_resolution": "EXACT",
                    "mapping_confidence": None,
                    "mapping_review_status": "accepted",
                }
            ],
            "semantic_context": {
                "semantic_registry_version": "russian-school-185+ru1-12-current",
                "semantic_mapping_version": "russian-exceptions-121-semantic-mapping-v1.0",
                "mapping_artifact_refs": [
                    "russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json"
                ],
            },
            "source": {
                "object_type": "tutor_turn",
                "object_id": context_id,
                "content_version": "grounded-postgres-tutor-v1",
                "item_version": "reviewed-v1",
                "route_metadata": {
                    "exam": "EGE",
                    "exam_year": None,
                    "task_route": None,
                    "historical_format": False,
                },
            },
            "product": {
                "source_type": "tutor",
                "product_id": "eksamio-tutor",
                "route": "/pro/#tutor",
            },
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
                "result_details": {
                    "error_event_id": str(wrong["event_id"]),
                    "verification_required": True,
                    "tutor_context_id": context_id,
                    "provider_id": provider_id,
                },
            },
            "response_mode": "NO_RESPONSE",
            "assistance": {
                "level": "RULE_EXPLANATION",
                "help_event_refs": [],
                "assistance_provider": provider_id,
            },
            "evaluator": {
                "evaluator_type": "DETERMINISTIC_VALIDATOR",
                "evaluator_id": "eksamio-grounded-tutor-context",
                "evaluator_version": "postgres-lifecycle-v1",
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
            "transfer_context": {
                "kind": "NOT_APPLICABLE",
                "origin_event_refs": [str(wrong["event_id"])],
            },
            "retention_context": {
                "kind": "NONE",
                "delay_seconds": None,
                "scheduled_by_policy_version": None,
            },
            "error_observations": [],
            "subject_extension": {
                "subject_payload_schema_version": "russian-tutor-help-v1",
                "subject_payload": {
                    "context_id": context_id,
                    "error_event_id": str(wrong["event_id"]),
                    "provider_id": provider_id,
                    "tutor_text_sha256": hashlib.sha256(
                        tutor_text.encode("utf-8")
                    ).hexdigest(),
                },
            },
            "created_at": position.received_at_server,
        }
        self.store.append_event(event)
        recommendation_id = "nba.tutor." + _digest(
            host.learner_profile_id + "|" + event_id
        )
        snapshot = self.store.recompute_snapshot(
            learner_profile_id=host.learner_profile_id,
            subject_id=SUBJECT_ID,
            semantic_id=EXACT_SEMANTIC_ID,
            admitted_edges=[],
            goal_context=self.practice.get("context_signature"),
            kernel_snapshot=kernel_snapshot,
            meaningful_help_delivered_for=[EXACT_SEMANTIC_ID],
            recommendation_id=recommendation_id,
        )
        self.store.append_recommendation(snapshot["nba"])
        return event_id

    def turn(
        self,
        host: HostIdentity,
        *,
        card_id: str,
        message: str,
    ) -> dict[str, Any]:
        if card_id != FIRST_SLICE_CARD_ID:
            raise ServiceRequestError("Tutor card is not admitted")
        if not isinstance(message, str) or not message.strip():
            raise ServiceRequestError("Tutor message is required")

        with self._lock:
            pending = self.pending_context(host.learner_profile_id, card_id)
            if pending is not None:
                return self._response_from_context(pending)

            wrong = self._latest_wrong_event(host.learner_profile_id)
            lineage = self._next_lineage(host.learner_profile_id, card_id)
            context_id = "tutorctx." + _digest(
                host.learner_profile_id
                + "|"
                + str(wrong["event_id"])
                + "|lineage:"
                + str(lineage)
            )
            explanation = str(self.practice["feedback"]["why"])
            correct_answer = str(self.practice["answer"]["text"])
            accepted_source_refs = [
                f"source:russian-reviewed-card:{FIRST_SLICE_CARD_ID}"
            ]
            tutor_text = self.provider.respond(
                message=message.strip(),
                context_id=context_id,
                answer_received=wrong.get("result", {}).get("response_value"),
                explanation=explanation,
                correct_answer=correct_answer,
                accepted_source_refs=accepted_source_refs,
            )
            if not isinstance(tutor_text, str) or not tutor_text.strip():
                raise RuntimeError("Tutor provider returned empty text")

            help_event_id = self._append_help_event(
                host=host,
                wrong=wrong,
                context_id=context_id,
                tutor_text=tutor_text,
            )
            created_at = _utc_now()
            helped_at_epoch = int(time.time())
            with self.store.connection:
                self.store.connection.execute(
                    """
                    INSERT INTO tutor_contexts(
                        context_id, learner_profile_id, card_id, lineage,
                        error_event_id, help_event_id, provider_id, tutor_text,
                        status, created_at, helped_at_epoch, verified_event_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'VERIFICATION_REQUIRED', ?, ?, NULL)
                    ON CONFLICT(context_id) DO NOTHING
                    """,
                    (
                        context_id,
                        host.learner_profile_id,
                        card_id,
                        lineage,
                        str(wrong["event_id"]),
                        help_event_id,
                        str(self.provider.provider_id),
                        tutor_text.strip(),
                        created_at,
                        helped_at_epoch,
                    ),
                )
            pending = self.pending_context(host.learner_profile_id, card_id)
            if pending is None:
                raise RuntimeError("Tutor context was not persisted")
            return self._response_from_context(pending)

    def _response_from_context(self, context: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "status": "TUTOR_ADVISORY_ACCEPTANCE",
            "provider_mode": str(context["provider_id"]),
            "context_id": str(context["context_id"]),
            "lineage": int(context["lineage"]),
            "card_id": str(context["card_id"]),
            "error_event_id": str(context["error_event_id"]),
            "help_event_id": str(context["help_event_id"]),
            "accepted_source_refs": [
                f"source:russian-reviewed-card:{FIRST_SLICE_CARD_ID}"
            ],
            "verification_required": True,
            "text": str(context["tutor_text"]),
        }

    def mark_verified(
        self,
        *,
        learner_profile_id: str,
        card_id: str,
        event_id: str,
    ) -> str | None:
        event = self.store.raw_event(event_id)
        if event is None:
            raise RuntimeError("verification event is unavailable")
        transfer = event.get("transfer_context", {})
        if transfer.get("kind") != "SAME_SESSION_VERIFICATION":
            return None
        refs = transfer.get("origin_event_refs")
        if not isinstance(refs, list) or len(refs) != 1:
            raise RuntimeError("verification event lacks one Tutor help origin")
        row = self.pending_context(learner_profile_id, card_id)
        if row is None:
            return None
        if str(row["help_event_id"]) != str(refs[0]):
            raise RuntimeError("verification event points to a different Tutor lineage")
        with self.store.connection:
            changed = self.store.connection.execute(
                """
                UPDATE tutor_contexts
                SET status = 'VERIFIED', verified_event_id = ?
                WHERE context_id = ? AND status = 'VERIFICATION_REQUIRED'
                RETURNING context_id
                """,
                (event_id, str(row["context_id"])),
            ).fetchone()
        return str(changed["context_id"]) if changed is not None else None


def build_tutor_aware_bridge(
    *,
    store: Any,
    base_adapter: RussianExceptionsPracticeAdapter,
    lifecycle: PostgresTutorLifecycle,
) -> PeisServiceBridge:
    registry = AdapterRegistry()
    registry.register(VerificationAwarePracticeAdapter(base_adapter, lifecycle))
    return PeisServiceBridge(
        store=store,
        registry=registry,
        kernel_snapshot=kernel_snapshot,
    )
