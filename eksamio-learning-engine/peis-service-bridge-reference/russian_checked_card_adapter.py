#!/usr/bin/env python3
"""Server-side Russian current-trainer adapter for the generic PEIS service bridge.

Subject truth stays here, outside the generic service core. The adapter loads the
pinned current trainer card, recomputes deterministic whole-card correctness
server-side, then delegates canonical EvidenceEvent construction to the already
validated RussianTrainerSensorAdapter from PEIS-INTEGRATION-001.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from peis_service_bridge import AdaptedObservation, HostIdentity, ServerEventPosition, ServiceRequestError
from russian_trainer_sensor import RussianTrainerSensorAdapter, find_card, load_trainer_bank_chunk


ALLOWED_CLIENT_FIELDS = {
    "card_id",
    "session_started_at_ms",
    "session_mode",
    "answer",
    "occurred_at_client",
    "client_request_id",
}

FORBIDDEN_TRUTH_FIELDS = {
    "score",
    "max_score",
    "correctness",
    "subject_id",
    "semantic_targets",
    "semantic_id",
    "mapping_resolution",
    "evaluator",
    "evaluator_type",
    "trust_class",
    "mastery",
    "readiness",
    "retention",
    "nba",
    "reason_codes",
    "server_sequence",
    "server_watermark",
    "received_at_server",
    "prerequisite_edges",
}


def _digest(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _same_set(actual: Any, expected: list[str]) -> bool:
    if not isinstance(actual, list):
        return False
    actual_strings = [str(value) for value in actual]
    # Mirrors current trainer sameSet(): duplicates make the response invalid.
    if len(set(actual_strings)) != len(actual_strings):
        return False
    if len(set(expected)) != len(expected):
        return False
    return sorted(actual_strings) == sorted(expected)


class RussianEgeTrainerTask12Adapter:
    adapter_id = "russian-ege-trainer-task12-v0.1"
    subject_id = "russian"

    def __init__(self, repo_root: str | Path) -> None:
        root = Path(repo_root)
        self.mapping_path = root / "peis-integration-reference/RUSSIAN-EGE-TRAINER-SENSOR-MAP-v0.1.json"
        self.bank_path = root / "russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-06.txt"
        self.edge_path = root / "russian-program/verified-slices/RU-SLICE-001-PREREQUISITE-EDGE-v0.1.json"
        self.mapping = json.loads(self.mapping_path.read_text(encoding="utf-8"))
        self.bank = load_trainer_bank_chunk(self.bank_path)
        self.edge = json.loads(self.edge_path.read_text(encoding="utf-8"))
        self.sensor = RussianTrainerSensorAdapter(self.mapping)

    def _validate_payload(self, payload: Mapping[str, Any]) -> None:
        keys = set(payload)
        forbidden = keys & FORBIDDEN_TRUTH_FIELDS
        if forbidden:
            raise ServiceRequestError(f"client may not assert canonical truth fields: {sorted(forbidden)}")
        extras = keys - ALLOWED_CLIENT_FIELDS
        if extras:
            raise ServiceRequestError(f"unexpected checked-card payload fields: {sorted(extras)}")
        required = {
            "card_id",
            "session_started_at_ms",
            "session_mode",
            "answer",
            "occurred_at_client",
        }
        missing = required - keys
        if missing:
            raise ServiceRequestError(f"missing checked-card payload fields: {sorted(missing)}")
        if not isinstance(payload["card_id"], str) or not payload["card_id"]:
            raise ServiceRequestError("card_id must be a non-empty string")
        if not isinstance(payload["session_started_at_ms"], int) or payload["session_started_at_ms"] <= 0:
            raise ServiceRequestError("session_started_at_ms must be a positive integer")
        if payload["session_mode"] not in {"practice", "exam"}:
            raise ServiceRequestError("session_mode must be practice or exam")
        if not isinstance(payload["occurred_at_client"], str) or not payload["occurred_at_client"]:
            raise ServiceRequestError("occurred_at_client is required")
        request_id = payload.get("client_request_id")
        if request_id is not None and (not isinstance(request_id, str) or len(request_id) < 3):
            raise ServiceRequestError("client_request_id must be a stable string when supplied")

    def stable_event_id(self, payload: Mapping[str, Any]) -> str:
        self._validate_payload(payload)
        source_tuple = (
            f"{self.mapping['source_namespace']}|"
            f"{payload['session_started_at_ms']}|{payload['card_id']}"
        )
        return f"egrt.ev.{_digest(source_tuple)}"

    def _checked_truth(self, card: dict[str, Any], answer: Any) -> dict[str, Any]:
        if card.get("kind") != "unordered_digits":
            raise ServiceRequestError("first service adapter admits unordered_digits cards only")
        if card.get("answerTokens"):
            expected = [str(value) for value in card["answerTokens"]]
        else:
            expected = list(str(card.get("answer") or ""))
        maximum = int(card.get("maxScore") or 1)
        score = maximum if _same_set(answer, expected) else 0
        return {"score": score, "max": maximum, "answer": answer}

    def build_observation(
        self,
        payload: Mapping[str, Any],
        *,
        host_identity: HostIdentity,
        server_position: ServerEventPosition,
    ) -> AdaptedObservation:
        self._validate_payload(payload)
        card_id = str(payload["card_id"])
        card_mapping = self.mapping.get("card_mappings", {}).get(card_id)
        if card_mapping is None:
            raise ServiceRequestError(f"card is not admitted by this server adapter: {card_id}")
        card = find_card(self.bank, card_id)
        if card.get("task") != 12:
            raise ServiceRequestError("first Russian service adapter admits the verified Task 12 route only")

        session = {
            "version": 1,
            "status": "running",
            "mode": payload["session_mode"],
            "ids": [card_id],
            "current": 0,
            "answers": {card_id: payload["answer"]},
            "checked": {},
            "recorded": {},
            "startedAt": payload["session_started_at_ms"],
            "endsAt": None,
            "completedAt": None,
            "config": {"mode": payload["session_mode"], "tasks": [12]},
        }
        checked = self._checked_truth(card, payload["answer"])
        event = self.sensor.build_checked_event(
            card=card,
            session=session,
            checked=checked,
            learner_profile_id=host_identity.learner_profile_id,
            identity_refs=host_identity.identity_refs,
            occurred_at_client=str(payload["occurred_at_client"]),
            received_at_server=server_position.received_at_server,
            server_sequence=server_position.server_sequence,
            server_watermark=server_position.server_watermark,
        )
        # Preserve request correlation only as product/transport metadata, never truth.
        if payload.get("client_request_id"):
            event["subject_extension"]["subject_payload"]["client_request_id"] = payload["client_request_id"]

        stable = self.stable_event_id(payload)
        if event["event_id"] != stable:
            raise ServiceRequestError("underlying Russian sensor identity disagrees with service adapter")

        return AdaptedObservation(
            event=event,
            target_semantic_id="school-participle-vowel-suffix-conjugation-base",
            goal_context=card_mapping["goal_context"],
            admitted_edges=[self.edge],
        )
