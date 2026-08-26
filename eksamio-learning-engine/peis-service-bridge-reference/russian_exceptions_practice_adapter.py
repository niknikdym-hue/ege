#!/usr/bin/env python3
"""Server-side adapter for the reviewed 121-card Russian Exceptions bank.

The first admitted production-shaped slice intentionally exercises one real
reviewed practice item while loading semantic truth from the merged 121-row
mapping. Browser/product payloads contain observations only; score, semantic
mapping, learner identity and PEIS state remain server-owned.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from peis_service_bridge import AdaptedObservation, HostIdentity, ServerEventPosition, ServiceRequestError


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
    "learner_profile_id",
    "identity_refs",
}
FIRST_SLICE_CARD_ID = "ex-practice-alt-sochetat-001"
SOURCE_NAMESPACE = "eksamio:russian-exceptions:checked-card:v1"


def _digest(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _schema_resolution(value: str) -> str:
    if value == "EXACT":
        return "EXACT"
    if value == "PARTIAL_COMPOSITE":
        return "COMPOSITE"
    raise ServiceRequestError(f"unsupported admitted mapping resolution: {value}")


class RussianExceptionsPracticeAdapter:
    """Bounded adapter for the first real reviewed Exceptions practice slice."""

    adapter_id = "russian-exceptions-practice-v1.0"
    subject_id = "russian"

    def __init__(self, repo_root: str | Path) -> None:
        root = Path(repo_root)
        self.mapping_path = root / "russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json"
        self.manifest_path = root / "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json"
        self.practice_path = root / "92-RUSSIAN-EXCEPTIONS-PRACTICE-PILOT-v0.1.json"
        self.mapping = json.loads(self.mapping_path.read_text(encoding="utf-8"))
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        practice = json.loads(self.practice_path.read_text(encoding="utf-8"))

        counts = self.mapping.get("counts", {})
        expected_counts = {
            "active_cards": 121,
            "integration_ready": 121,
            "blocked": 0,
            "exact": 116,
            "partial_composite": 5,
            "represented_exception_ids": 88,
        }
        for key, expected in expected_counts.items():
            if counts.get(key) != expected:
                raise ServiceRequestError(f"121 mapping invariant drift: {key}={counts.get(key)!r}, expected {expected}")
        if self.manifest.get("expected_active_items") != 121:
            raise ServiceRequestError("current Russian Exceptions manifest is not the reviewed 121-card checkpoint")

        rows = self.mapping.get("rows")
        if not isinstance(rows, list) or len(rows) != 121:
            raise ServiceRequestError("merged Russian Exceptions mapping must contain exactly 121 rows")
        self.mapping_by_card = {row.get("practice_item_id"): row for row in rows}
        if len(self.mapping_by_card) != 121 or None in self.mapping_by_card:
            raise ServiceRequestError("merged Russian Exceptions mapping practice_item_id values must be unique")

        items = practice.get("items")
        if not isinstance(items, list):
            raise ServiceRequestError("reviewed pilot practice bank is malformed")
        self.practice_by_card = {item.get("practice_item_id"): item for item in items}
        if FIRST_SLICE_CARD_ID not in self.practice_by_card:
            raise ServiceRequestError(f"reviewed first-slice practice item is missing: {FIRST_SLICE_CARD_ID}")
        if FIRST_SLICE_CARD_ID not in self.mapping_by_card:
            raise ServiceRequestError(f"merged 121 mapping is missing first-slice item: {FIRST_SLICE_CARD_ID}")

        first = self.practice_by_card[FIRST_SLICE_CARD_ID]
        row = self.mapping_by_card[FIRST_SLICE_CARD_ID]
        if first.get("exception_id") != row.get("exception_id"):
            raise ServiceRequestError("practice item exception_id disagrees with merged semantic mapping")
        if first.get("status") not in {"source_verified", "reviewed"}:
            raise ServiceRequestError("first-slice practice item is not source-verified/reviewed")
        if first.get("response_kind") not in {"short_text", "normalize_form"}:
            raise ServiceRequestError("first slice requires deterministic typed-text evaluation")

    def _validate_payload(self, payload: Mapping[str, Any]) -> None:
        if not isinstance(payload, Mapping):
            raise ServiceRequestError("payload must be an object")
        keys = set(payload)
        forbidden = keys & FORBIDDEN_TRUTH_FIELDS
        if forbidden:
            raise ServiceRequestError(f"client may not assert canonical truth fields: {sorted(forbidden)}")
        extras = keys - ALLOWED_CLIENT_FIELDS
        if extras:
            raise ServiceRequestError(f"unexpected checked-card payload fields: {sorted(extras)}")
        required = {"card_id", "session_started_at_ms", "session_mode", "answer", "occurred_at_client"}
        missing = required - keys
        if missing:
            raise ServiceRequestError(f"missing checked-card payload fields: {sorted(missing)}")
        if payload.get("card_id") != FIRST_SLICE_CARD_ID:
            raise ServiceRequestError(f"first vertical slice admits only {FIRST_SLICE_CARD_ID}")
        if not isinstance(payload.get("session_started_at_ms"), int) or payload["session_started_at_ms"] <= 0:
            raise ServiceRequestError("session_started_at_ms must be a positive integer")
        if payload.get("session_mode") != "practice":
            raise ServiceRequestError("Russian Exceptions first slice admits practice mode only")
        if not isinstance(payload.get("answer"), str):
            raise ServiceRequestError("first-slice answer must be text")
        if not isinstance(payload.get("occurred_at_client"), str) or not payload["occurred_at_client"]:
            raise ServiceRequestError("occurred_at_client is required")
        request_id = payload.get("client_request_id")
        if request_id is not None and (not isinstance(request_id, str) or len(request_id) < 3):
            raise ServiceRequestError("client_request_id must be a stable string when supplied")

    def stable_event_id(self, payload: Mapping[str, Any]) -> str:
        self._validate_payload(payload)
        source_tuple = f"{SOURCE_NAMESPACE}|{payload['session_started_at_ms']}|{payload['card_id']}"
        return f"ruex.ev.{_digest(source_tuple)}"

    def _semantic_targets(self, row: Mapping[str, Any]) -> list[dict[str, Any]]:
        ids = row.get("semantic_target_ids")
        if not isinstance(ids, list) or not ids:
            raise ServiceRequestError("admitted mapping row lacks semantic targets")
        resolution = _schema_resolution(str(row.get("mapping_resolution")))
        return [
            {
                "semantic_id": semantic_id,
                "target_role": "PRIMARY" if index == 0 else "SECONDARY",
                "mapping_resolution": resolution,
                "mapping_confidence": None,
                "mapping_review_status": "accepted",
            }
            for index, semantic_id in enumerate(ids)
        ]

    def build_observation(
        self,
        payload: Mapping[str, Any],
        *,
        host_identity: HostIdentity,
        server_position: ServerEventPosition,
    ) -> AdaptedObservation:
        self._validate_payload(payload)
        card_id = str(payload["card_id"])
        item = self.practice_by_card[card_id]
        row = self.mapping_by_card[card_id]
        expected = item.get("answer", {}).get("text")
        if not isinstance(expected, str) or not expected:
            raise ServiceRequestError("reviewed first-slice answer is not machine-comparable text")
        supplied = str(payload["answer"])
        correct = _normalize_text(supplied) == _normalize_text(expected)
        semantic_targets = self._semantic_targets(row)
        mapping_resolution = str(row["mapping_resolution"])
        event_id = self.stable_event_id(payload)

        error_observations: list[dict[str, Any]] = []
        if not correct:
            if mapping_resolution == "EXACT" and len(semantic_targets) == 1:
                error_observations.append(
                    {
                        "observation_type": "EXACT_RULE_ERROR",
                        "semantic_id": semantic_targets[0]["semantic_id"],
                        "candidate_ref": None,
                        "precision": "EXACT",
                        "confidence": None,
                        "source_locator": card_id,
                        "provenance_refs": [
                            "russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json",
                            "92-RUSSIAN-EXCEPTIONS-PRACTICE-PILOT-v0.1.json",
                        ],
                    }
                )
            else:
                error_observations.append(
                    {
                        "observation_type": "UNKNOWN_OR_INSUFFICIENT_PRECISION",
                        "semantic_id": None,
                        "candidate_ref": None,
                        "precision": "UNKNOWN",
                        "confidence": 1.0,
                        "source_locator": card_id,
                        "provenance_refs": ["russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json"],
                    }
                )

        event = {
            "event_id": event_id,
            "idempotency_key": f"ruex.idem.{event_id.removeprefix('ruex.ev.')}",
            "schema_version": "0.1.0",
            "event_kind": "PERFORMANCE_OBSERVATION",
            "learner_profile_id": host_identity.learner_profile_id,
            "identity_refs": copy.deepcopy(host_identity.identity_refs),
            "subject_id": self.subject_id,
            "semantic_targets": semantic_targets,
            "semantic_context": {
                "semantic_registry_version": "russian-school-185+ru1-12-current",
                "semantic_mapping_version": self.mapping["mapping_version"],
                "mapping_artifact_refs": ["russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json"],
            },
            "source": {
                "object_type": "practice_card",
                "object_id": card_id,
                "content_version": "russian-exceptions-reviewed-121-current",
                "item_version": "reviewed-v1",
                "route_metadata": {
                    "exam": "EGE",
                    "exam_year": None,
                    "task_route": None,
                    "historical_format": False,
                },
            },
            "product": {
                "source_type": "thematic_trainer",
                "product_id": "russian-exceptions-trainer",
                "route": "/trenazhery/russkiy/isklyucheniya/",
            },
            "session_id": f"ruex.session.{payload['session_started_at_ms']}",
            "timestamps": {
                "occurred_at_client": str(payload["occurred_at_client"]),
                "received_at_server": server_position.received_at_server,
                "server_sequence": server_position.server_sequence,
                "server_watermark": server_position.server_watermark,
            },
            "result": {
                "attempt_index": 1,
                "outcome": "CORRECT" if correct else "INCORRECT",
                "correctness": correct,
                "score": 1 if correct else 0,
                "max_score": 1,
                "response_value": supplied,
                "result_details": {
                    "sensor_contract": "russian-exceptions-reviewed-121-v1",
                    "session_mode": payload["session_mode"],
                    "response_kind": item["response_kind"],
                    "exception_id": row["exception_id"],
                    "mapping_resolution": mapping_resolution,
                },
            },
            "response_mode": "TYPED_TEXT",
            "assistance": {"level": "UNASSISTED", "help_event_refs": [], "assistance_provider": None},
            "evaluator": {
                "evaluator_type": "DETERMINISTIC_VALIDATOR",
                "evaluator_id": "russian-exceptions-reviewed-answer-key",
                "evaluator_version": "121-current-v1",
                "trust_class": "DETERMINISTIC_HIGH",
                "uncertainty": 0.0,
                "review_status": "not_required",
                "rubric_version": None,
                "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
            },
            "provenance_refs": [
                "119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json",
                "russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json",
                "92-RUSSIAN-EXCEPTIONS-PRACTICE-PILOT-v0.1.json",
            ],
            "transfer_context": {"kind": "NOT_APPLICABLE", "origin_event_refs": []},
            "retention_context": {"kind": "NONE", "delay_seconds": None, "scheduled_by_policy_version": None},
            "error_observations": error_observations,
            "subject_extension": {
                "subject_payload_schema_version": "russian-exceptions-practice-sensor-v1.0",
                "subject_payload": {
                    "practice_item_id": card_id,
                    "exception_id": row["exception_id"],
                    "session_started_at_ms": payload["session_started_at_ms"],
                    "session_mode": payload["session_mode"],
                    "mapping_resolution": mapping_resolution,
                    "client_request_id": payload.get("client_request_id"),
                },
            },
            "created_at": server_position.received_at_server,
        }

        return AdaptedObservation(
            event=event,
            target_semantic_id=semantic_targets[0]["semantic_id"],
            goal_context=item.get("context_signature"),
            admitted_edges=[],
        )
