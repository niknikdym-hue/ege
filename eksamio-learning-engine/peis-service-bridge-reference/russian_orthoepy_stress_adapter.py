#!/usr/bin/env python3
"""Registered-only Admissions Gate adapter for live Russian orthoepy stress items.

The browser supplies an observation only: exact item id, exact admitted action,
selected stress index and client timing/idempotency material. Canonical semantic
truth, answer key, score, evaluator, learner identity and server position remain
server-owned. This bounded slice admits only normative stress selection; it does
not admit broader non-stress normative pronunciation.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from peis_service_bridge import AdaptedObservation, HostIdentity, ServerEventPosition, ServiceRequestError

ADAPTER_ID = "russian-orthoepy-stress-admission-v1.0"
SUBJECT_ID = "russian"
ACTION_ID = "normative_stress_selection"
SEMANTIC_ID = "ru-orthoepy-normative-stress-selection"
SOURCE_NAMESPACE = "eksamio:live-orthoepy:stress-admission:v1"
AUTHORITY_RELATIVE_PATH = "peis-production-substrate/admissions/ORTHOEPY-STRESS-ADMISSION-AUTHORITY-v0.1.json"
EXPECTED_ISSUE_185_HEAD = "c5592c212557b91578ed48e1bf778e30dd489dc7"
EXPECTED_BINDING_BLOB_SHA1 = "6b513376a3040dc28e9c869028687144ccf0ff87"
EXPECTED_ORDERED_ID_SHA256 = "73a3c847ec79a9a1f98f4703aacadd81561d05f74bf3b12293fd60a27fe4f583"
EXPECTED_ROW_COUNT = 291

ALLOWED_CLIENT_FIELDS = {
    "item_id",
    "action_id",
    "stress_index",
    "session_started_at_ms",
    "occurred_at_client",
    "client_request_id",
}
FORBIDDEN_TRUTH_FIELDS = {
    "score",
    "max_score",
    "correctness",
    "outcome",
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
    "learner_profile_id",
    "identity_refs",
    "user_identity_ref",
    "anonymous_identity_ref",
}


def _digest(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _ordered_id_sha(ids: list[str]) -> str:
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


class RussianOrthoepyStressAdmissionAdapter:
    """Exact-item + exact-action registered server evidence admission."""

    adapter_id = ADAPTER_ID
    subject_id = SUBJECT_ID

    def __init__(self, engine_root: str | Path) -> None:
        root = Path(engine_root)
        self.authority_path = root / AUTHORITY_RELATIVE_PATH
        self.authority = json.loads(self.authority_path.read_text(encoding="utf-8"))
        self._validate_authority()
        stress = self.authority["stress_index_by_sequential_item"]
        self.rows_by_id = {f"w{index:03d}": {"stress_index": int(value)} for index, value in enumerate(stress, start=1)}

    def _validate_authority(self) -> None:
        authority = self.authority
        if authority.get("schema") != "eksamio.orthoepy-stress-admission-authority.v0.1":
            raise ServiceRequestError("orthoepy admission authority schema drift")
        source = authority.get("source_authority")
        if not isinstance(source, Mapping):
            raise ServiceRequestError("orthoepy admission source authority missing")
        if source.get("issue_185_exact_head") != EXPECTED_ISSUE_185_HEAD:
            raise ServiceRequestError("orthoepy admission authority is not pinned to accepted #185 exact head")
        if source.get("action_binding_blob_sha1") != EXPECTED_BINDING_BLOB_SHA1:
            raise ServiceRequestError("orthoepy action binding blob drift")
        if source.get("ordered_id_sha256") != EXPECTED_ORDERED_ID_SHA256:
            raise ServiceRequestError("orthoepy authority ordered-id hash drift")
        if source.get("fipi_correspondence") != "291/291":
            raise ServiceRequestError("orthoepy authority lacks exact 291/291 FIPI correspondence")

        admission = authority.get("admission")
        if not isinstance(admission, Mapping):
            raise ServiceRequestError("orthoepy admission metadata missing")
        expected = {
            "action_id": ACTION_ID,
            "semantic_id": SEMANTIC_ID,
            "mapping_resolution": "EXACT",
            "registered_user_identity_ref_required": True,
            "anonymous_identity_ref_forbidden": True,
            "server_evaluator": "deterministic_stress_index_v1",
        }
        for key, value in expected.items():
            if admission.get(key) != value:
                raise ServiceRequestError(f"orthoepy admission invariant drift: {key}")

        stress = authority.get("stress_index_by_sequential_item")
        if not isinstance(stress, list) or len(stress) != EXPECTED_ROW_COUNT:
            raise ServiceRequestError("orthoepy admission authority must contain exactly 291 stress keys")
        if not all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in stress):
            raise ServiceRequestError("orthoepy admission stress key vector is invalid")
        ids = [f"w{index:03d}" for index in range(1, EXPECTED_ROW_COUNT + 1)]
        if _ordered_id_sha(ids) != EXPECTED_ORDERED_ID_SHA256:
            raise ServiceRequestError("orthoepy admission item-id bytes do not match pinned authority")

        boundaries = authority.get("boundaries")
        if not isinstance(boundaries, Mapping):
            raise ServiceRequestError("orthoepy admission boundaries missing")
        if boundaries.get("nonstress_normative_pronunciation_admitted") is not False:
            raise ServiceRequestError("non-stress pronunciation must remain blocked")
        if boundaries.get("false_exact_mastery") != 0:
            raise ServiceRequestError("false_exact_mastery invariant violated")

    @staticmethod
    def _require_registered(host_identity: HostIdentity) -> None:
        host_identity.validate()
        refs = host_identity.identity_refs
        if "user_identity_ref" not in refs:
            raise ServiceRequestError("registered user_identity_ref is required for canonical learner evidence")
        if "anonymous_identity_ref" in refs:
            raise ServiceRequestError("anonymous identity is forbidden for canonical learner evidence")

    def _validate_payload(self, payload: Mapping[str, Any]) -> None:
        if not isinstance(payload, Mapping):
            raise ServiceRequestError("payload must be an object")
        keys = set(payload)
        forbidden = keys & FORBIDDEN_TRUTH_FIELDS
        if forbidden:
            raise ServiceRequestError(f"client may not assert canonical truth fields: {sorted(forbidden)}")
        extras = keys - ALLOWED_CLIENT_FIELDS
        if extras:
            raise ServiceRequestError(f"unexpected orthoepy admission fields: {sorted(extras)}")
        missing = ALLOWED_CLIENT_FIELDS - keys
        if missing:
            raise ServiceRequestError(f"missing orthoepy admission fields: {sorted(missing)}")
        if payload.get("action_id") != ACTION_ID:
            raise ServiceRequestError("only exact normative_stress_selection action is admitted")
        item_id = payload.get("item_id")
        if not isinstance(item_id, str) or item_id not in self.rows_by_id:
            raise ServiceRequestError("unknown or non-authoritative orthoepy item_id")
        stress = payload.get("stress_index")
        if not isinstance(stress, int) or isinstance(stress, bool):
            raise ServiceRequestError("stress_index must be an integer")
        if stress < 0 or stress > 63:
            raise ServiceRequestError("stress_index is outside the bounded stress-selection domain")
        started = payload.get("session_started_at_ms")
        if not isinstance(started, int) or isinstance(started, bool) or started <= 0:
            raise ServiceRequestError("session_started_at_ms must be a positive integer")
        occurred = payload.get("occurred_at_client")
        if not isinstance(occurred, str) or not occurred:
            raise ServiceRequestError("occurred_at_client is required")
        request_id = payload.get("client_request_id")
        if not isinstance(request_id, str) or len(request_id) < 8:
            raise ServiceRequestError("client_request_id must be a stable string of at least 8 characters")

    def stable_event_id(self, payload: Mapping[str, Any]) -> str:
        self._validate_payload(payload)
        source_tuple = "|".join(
            [
                SOURCE_NAMESPACE,
                str(payload["client_request_id"]),
                str(payload["session_started_at_ms"]),
                str(payload["item_id"]),
                str(payload["action_id"]),
            ]
        )
        return f"ruortho.ev.{_digest(source_tuple)}"

    def build_observation(
        self,
        payload: Mapping[str, Any],
        *,
        host_identity: HostIdentity,
        server_position: ServerEventPosition,
    ) -> AdaptedObservation:
        self._validate_payload(payload)
        self._require_registered(host_identity)

        item_id = str(payload["item_id"])
        row = self.rows_by_id[item_id]
        selected = int(payload["stress_index"])
        expected = int(row["stress_index"])
        correct = selected == expected
        event_id = self.stable_event_id(payload)

        semantic_targets = [
            {
                "semantic_id": SEMANTIC_ID,
                "target_role": "PRIMARY",
                "mapping_resolution": "EXACT",
                "mapping_confidence": 1.0,
                "mapping_review_status": "accepted",
            }
        ]
        error_observations: list[dict[str, Any]] = []
        if not correct:
            error_observations.append(
                {
                    "observation_type": "EXACT_RULE_ERROR",
                    "semantic_id": SEMANTIC_ID,
                    "candidate_ref": None,
                    "precision": "EXACT",
                    "confidence": 1.0,
                    "source_locator": item_id,
                    "provenance_refs": [AUTHORITY_RELATIVE_PATH],
                }
            )

        event = {
            "event_id": event_id,
            "idempotency_key": f"ruortho.idem.{event_id.removeprefix('ruortho.ev.')}",
            "schema_version": "0.1.0",
            "event_kind": "PERFORMANCE_OBSERVATION",
            "learner_profile_id": host_identity.learner_profile_id,
            "identity_refs": copy.deepcopy(host_identity.identity_refs),
            "subject_id": self.subject_id,
            "semantic_targets": semantic_targets,
            "semantic_context": {
                "semantic_registry_version": "russian-current-v2@7edddb9f9764b5e8cdf7e2653c425e5f90c4ffe9",
                "semantic_mapping_version": "issue185-action-scoped@c5592c212557b91578ed48e1bf778e30dd489dc7",
                "mapping_artifact_refs": [AUTHORITY_RELATIVE_PATH],
            },
            "source": {
                "object_type": "thematic_trainer_item",
                "object_id": item_id,
                "content_version": "live-orthoepy-291@be5aa80192b357ba4f53c1664ed17bde145221c34d7f6101ba381e84ce616d05",
                "item_version": "issue185-c5592c2",
                "route_metadata": {
                    "exam": "EGE",
                    "exam_year": 2026,
                    "task_route": None,
                    "historical_format": False,
                },
            },
            "product": {
                "source_type": "thematic_trainer",
                "product_id": "russian-orthoepy-stress-trainer",
                "route": "/trenazhery/russkiy/orfoepiya/",
            },
            "session_id": f"ruortho.session.{payload['session_started_at_ms']}",
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
                "response_value": selected,
                "result_details": {
                    "sensor_contract": "registered-orthoepy-stress-admission-v1",
                    "action_id": ACTION_ID,
                    "item_id": item_id,
                    "client_request_id": payload["client_request_id"],
                },
            },
            "response_mode": "NUMERIC",
            "assistance": {"level": "UNASSISTED", "help_event_refs": [], "assistance_provider": None},
            "evaluator": {
                "evaluator_type": "DETERMINISTIC_VALIDATOR",
                "evaluator_id": "pinned-live-fipi-orthoepy-stress-index",
                "evaluator_version": "issue185-c5592c2-v1",
                "trust_class": "DETERMINISTIC_HIGH",
                "uncertainty": 0.0,
                "review_status": "not_required",
                "rubric_version": None,
                "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
            },
            "provenance_refs": [
                AUTHORITY_RELATIVE_PATH,
                "issue185-pr187@c5592c212557b91578ed48e1bf778e30dd489dc7",
                "fipi:2026:ru-1-fonetika.pdf@sha256:6e1b6dcaf835f6b7294c9426de406dea3614bb81d9d28e25fc423c9c8036f389",
            ],
            "transfer_context": {"kind": "NOT_APPLICABLE", "origin_event_refs": []},
            "retention_context": {"kind": "NONE", "delay_seconds": None, "scheduled_by_policy_version": None},
            "error_observations": error_observations,
            "subject_extension": {
                "subject_payload_schema_version": "russian-orthoepy-stress-admission-v1.0",
                "subject_payload": {
                    "item_id": item_id,
                    "action_id": ACTION_ID,
                    "selected_stress_index": selected,
                    "session_started_at_ms": payload["session_started_at_ms"],
                    "client_request_id": payload["client_request_id"],
                    "broader_nonstress_pronunciation_admitted": False,
                },
            },
            "created_at": server_position.received_at_server,
        }

        return AdaptedObservation(
            event=event,
            target_semantic_id=SEMANTIC_ID,
            goal_context="ege:russian:orthoepy:normative-stress-selection",
            admitted_edges=[],
        )
