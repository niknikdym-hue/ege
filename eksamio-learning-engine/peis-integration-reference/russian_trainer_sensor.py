#!/usr/bin/env python3
"""Reference adapter from the current Russian EGE trainer checked-card shape to PEIS.

This module is intentionally additive. It does not read or write browser
localStorage, does not change trainer scoring, and does not infer mastery.
It only converts an already-checked product observation into canonical
EvidenceEvent 277 and exposes a small read-side projection of a shared PEIS NBA.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


class SensorMappingError(ValueError):
    """Raised when a product observation cannot be mapped without guessing."""


def _stable_digest(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def load_trainer_bank_chunk(path: str | Path) -> dict[str, Any]:
    """Load the actual JSON bank object embedded in an er-bank-chunk script."""

    text = Path(path).read_text(encoding="utf-8")
    match = re.search(
        r'<script[^>]*class="er-bank-chunk"[^>]*>\s*(\{.*\})\s*</script>',
        text,
        flags=re.DOTALL,
    )
    if not match:
        raise SensorMappingError(f"no er-bank-chunk JSON found in {path}")
    return json.loads(match.group(1))


def find_card(bank: dict[str, Any], card_id: str) -> dict[str, Any]:
    for card in bank.get("cards", []):
        if card.get("id") == card_id:
            return card
    raise SensorMappingError(f"card {card_id} not found in trainer bank")


def _response_mode(card_kind: str) -> str:
    mapping = {
        "unordered_digits": "UNORDERED_SET",
        "ordered_sequence": "ORDERED_MATCH",
        "word_compact": "TYPED_TEXT",
        "word": "TYPED_TEXT",
        "numeric": "NUMERIC",
    }
    if card_kind not in mapping:
        raise SensorMappingError(f"unsupported checked-card response kind: {card_kind}")
    return mapping[card_kind]


def _outcome(score: Any, maximum: Any) -> tuple[str, bool | None]:
    if score is None or maximum is None:
        return "SUBMITTED", None
    if score == maximum:
        return "CORRECT", True
    if isinstance(score, (int, float)) and isinstance(maximum, (int, float)) and 0 < score < maximum:
        return "PARTIAL", None
    return "INCORRECT", False


class RussianTrainerSensorAdapter:
    """Build canonical EvidenceEvent from current trainer card/session/check result."""

    def __init__(self, mapping_doc: dict[str, Any]) -> None:
        self.mapping = copy.deepcopy(mapping_doc)
        self.namespace = self.mapping["source_namespace"]

    def build_checked_event(
        self,
        *,
        card: dict[str, Any],
        session: dict[str, Any],
        checked: dict[str, Any],
        learner_profile_id: str,
        identity_refs: dict[str, str],
        occurred_at_client: str,
        received_at_server: str,
        server_sequence: int | None,
        server_watermark: str | None,
        assistance_level: str = "UNASSISTED",
    ) -> dict[str, Any]:
        card_id = card.get("id")
        card_map = self.mapping.get("card_mappings", {}).get(card_id)
        if card_map is None:
            raise SensorMappingError(f"no admitted semantic mapping for card {card_id}")
        if card.get("task") != card_map.get("task"):
            raise SensorMappingError("card task disagrees with admitted sensor mapping")
        if not learner_profile_id or len(learner_profile_id) < 3:
            raise SensorMappingError("learner_profile_id must come from the shared host boundary")
        if not identity_refs or not ({"anonymous_identity_ref", "user_identity_ref"} & set(identity_refs)):
            raise SensorMappingError("shared host identity ref is required")
        if not isinstance(session.get("startedAt"), int):
            raise SensorMappingError("current trainer session.startedAt is required for stable source identity")
        if checked.get("max") is None:
            raise SensorMappingError("PEIS-INTEGRATION-001 supports deterministically checked non-essay cards only")

        source_tuple = f"{self.namespace}|{session['startedAt']}|{card_id}"
        digest = _stable_digest(source_tuple)
        event_id = f"egrt.ev.{digest}"
        idempotency_key = f"egrt.idem.{digest}"
        outcome, correctness = _outcome(checked.get("score"), checked.get("max"))

        semantic_targets = copy.deepcopy(card_map["semantic_targets"])
        exact_mapping = all(target.get("mapping_resolution") == "EXACT" for target in semantic_targets)
        error_observations: list[dict[str, Any]] = []
        if correctness is False:
            if exact_mapping and len(semantic_targets) == 1:
                target = semantic_targets[0]
                error_observations.append(
                    {
                        "observation_type": "EXACT_RULE_ERROR",
                        "semantic_id": target["semantic_id"],
                        "candidate_ref": None,
                        "precision": "EXACT",
                        "confidence": target.get("mapping_confidence"),
                        "source_locator": card_id,
                        "provenance_refs": copy.deepcopy(card_map["provenance_refs"]),
                    }
                )
            else:
                error_observations.append(
                    {
                        "observation_type": self.mapping["precision_policy"]["incorrect_observation_type"],
                        "semantic_id": None,
                        "candidate_ref": None,
                        "precision": "UNKNOWN",
                        "confidence": 1.0,
                        "source_locator": card_id,
                        "provenance_refs": copy.deepcopy(card_map["provenance_refs"]),
                    }
                )

        runtime = self.mapping["source_runtime"]
        semantic_context = self.mapping["semantic_context"]
        product = self.mapping["product"]
        item_version = f"{card.get('sourceYear', 'unknown')}-v{card.get('variant', 1)}"
        content_version = f"trainer-bank@{runtime['task12_bank_blob_sha']}"
        evaluator_version = f"trainer-runtime@{runtime['trainer_runtime_blob_sha']}"
        session_id = f"egrt.session.{session['startedAt']}"

        timestamps: dict[str, Any] = {
            "occurred_at_client": occurred_at_client,
            "received_at_server": received_at_server,
            "server_sequence": server_sequence,
            "server_watermark": server_watermark,
        }

        event = {
            "event_id": event_id,
            "idempotency_key": idempotency_key,
            "schema_version": "0.1.0",
            "event_kind": "PERFORMANCE_OBSERVATION",
            "learner_profile_id": learner_profile_id,
            "identity_refs": copy.deepcopy(identity_refs),
            "subject_id": "russian",
            "semantic_targets": semantic_targets,
            "semantic_context": {
                "semantic_registry_version": semantic_context["semantic_registry_version"],
                "semantic_mapping_version": semantic_context["semantic_mapping_version"],
                "mapping_artifact_refs": copy.deepcopy(semantic_context["mapping_artifact_refs"]),
            },
            "source": {
                "object_type": "trainer_card",
                "object_id": card_id,
                "content_version": content_version,
                "item_version": item_version,
                "route_metadata": {
                    "exam": "EGE",
                    "exam_year": card.get("sourceYear"),
                    "task_route": str(card.get("task")),
                    "historical_format": bool(card.get("legacyFormat")),
                },
            },
            "product": copy.deepcopy(product),
            "session_id": session_id,
            "timestamps": timestamps,
            "result": {
                "attempt_index": 1,
                "outcome": outcome,
                "correctness": correctness,
                "score": checked.get("score"),
                "max_score": checked.get("max"),
                "response_value": copy.deepcopy(checked.get("answer")),
                "result_details": {
                    "sensor_contract": "current-russian-trainer-checkCurrent-v1",
                    "session_mode": session.get("mode"),
                    "whole_card_result": True,
                },
            },
            "response_mode": _response_mode(str(card.get("kind"))),
            "assistance": {
                "level": assistance_level,
                "help_event_refs": [],
                "assistance_provider": None,
            },
            "evaluator": {
                "evaluator_type": "DETERMINISTIC_VALIDATOR",
                "evaluator_id": "ege-russian-trainer-scoreCard",
                "evaluator_version": evaluator_version,
                "trust_class": "DETERMINISTIC_HIGH",
                "uncertainty": 0.0,
                "review_status": "not_required",
                "rubric_version": None,
                "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
            },
            "provenance_refs": copy.deepcopy(card_map["provenance_refs"]) + [runtime["trainer_runtime_ref"]],
            "transfer_context": {
                "kind": "NOT_APPLICABLE",
                "origin_event_refs": [],
            },
            "retention_context": {
                "kind": "NONE",
                "delay_seconds": None,
                "scheduled_by_policy_version": None,
            },
            "error_observations": error_observations,
            "subject_extension": {
                "subject_payload_schema_version": "russian-ege-trainer-sensor-v0.1",
                "subject_payload": {
                    "integration_id": self.mapping["integration_id"],
                    "card_id": card_id,
                    "task": card.get("task"),
                    "source_year": card.get("sourceYear"),
                    "variant": card.get("variant"),
                    "session_started_at_ms": session.get("startedAt"),
                    "session_mode": session.get("mode"),
                    "legacy_progress_namespace": runtime["progress_key"],
                    "legacy_session_namespace": runtime["session_key"],
                    "goal_context": card_map["goal_context"],
                },
            },
            "created_at": received_at_server,
        }
        return event


def product_directive(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Read-side projection safe for a product UI/router.

    It intentionally exposes no product-owned mastery mutation API. The product
    receives the shared recommendation and state watermark as read-only routing
    information.
    """

    nba = snapshot["nba"]
    return {
        "recommendation_id": nba["recommendation_id"],
        "action_type": nba["action_type"],
        "semantic_targets": copy.deepcopy(nba["semantic_targets"]),
        "prerequisite_targets": copy.deepcopy(nba.get("prerequisite_targets", [])),
        "reason_codes": copy.deepcopy(nba["reason_codes"]),
        "verification_required": nba["verification_required"],
        "learner_state_watermark": nba["learner_state_watermark"],
        "route": copy.deepcopy(nba["route"]),
        "canonical_state_owner": "shared_peis",
    }
