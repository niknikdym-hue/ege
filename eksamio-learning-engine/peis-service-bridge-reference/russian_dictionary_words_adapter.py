#!/usr/bin/env python3
"""Registered-only Admissions Gate adapter for live Russian dictionary-word vowel items.

The browser supplies an observation only: exact item id, exact admitted action,
selected missing-root vowel and client timing/idempotency material. Canonical
semantic truth, answer key, score, evaluator, learner identity and server
position remain server-owned. Whole-word recall, five-row exam mode, browser
progress and aggregate trainer completion are explicitly outside this slice.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from peis_service_bridge import AdaptedObservation, HostIdentity, ServerEventPosition, ServiceRequestError

ADAPTER_ID = "russian-dictionary-words-admission-v1.0"
SUBJECT_ID = "russian"
ACTION_ID = "missing_root_vowel_insertion"
SEMANTIC_ID = "school-root-vowel-dictionary-unverifiable"
SOURCE_NAMESPACE = "eksamio:live-dictionary-words:missing-root-vowel-admission:v1"
AUTHORITY_RELATIVE_PATH = "peis-production-substrate/admissions/DICTIONARY-WORDS-ADMISSION-AUTHORITY-v0.1.json"
EXPECTED_ISSUE_185_HEAD = "c5592c212557b91578ed48e1bf778e30dd489dc7"
EXPECTED_BINDING_BLOB_SHA1 = "6b513376a3040dc28e9c869028687144ccf0ff87"
EXPECTED_LIVE_HTML_SHA256 = "610e866aad13c901b944c3fac9acfa840a01fecf89091cd0c7fc6e0dbb537d1a"
EXPECTED_WORDS_LITERAL_SHA256 = "f0794a22340fa3ff71c0a2b21b79ce6cc64bc120f3b0030431923e73c4a1a186"
EXPECTED_ORDERED_ID_SHA256 = "989ff8c27d3017bd3c5d3b7cb3a4a47979d7354a18daa0318589a6a01a116ea2"
EXPECTED_ORDERED_ANSWER_SHA256 = "08c6ef62b5d81b404d5a4a424673f27d285a8bc9c9b624cc2baf4c2568b11fdc"
EXPECTED_FIPI_ORTHOGRAPHY_SHA256 = "0a3ee8ce95e76c6f7280bb97a6f6c3e56442ff241b074d93d73642ca5c59b957"
EXPECTED_ROW_COUNT = 308
ALLOWED_ANSWER_LETTERS = frozenset("аеёиоуыэюя")

ALLOWED_CLIENT_FIELDS = {
    "item_id",
    "action_id",
    "letter",
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


def _ordered_sha(values: list[str]) -> str:
    return hashlib.sha256("\n".join(values).encode("utf-8")).hexdigest()


class RussianDictionaryWordsAdmissionAdapter:
    """Exact-item + exact missing-root-vowel action registered evidence admission."""

    adapter_id = ADAPTER_ID
    subject_id = SUBJECT_ID

    def __init__(self, engine_root: str | Path) -> None:
        root = Path(engine_root)
        self.authority_path = root / AUTHORITY_RELATIVE_PATH
        self.authority = json.loads(self.authority_path.read_text(encoding="utf-8"))
        self._validate_authority()
        self.answer_by_id = {
            str(item_id): str(letter)
            for item_id, letter in self.authority["answer_letter_by_item_id"].items()
        }

    def _validate_authority(self) -> None:
        authority = self.authority
        if authority.get("schema") != "eksamio.dictionary-words-admission-authority.v0.1":
            raise ServiceRequestError("dictionary admission authority schema drift")
        source = authority.get("source_authority")
        if not isinstance(source, Mapping):
            raise ServiceRequestError("dictionary admission source authority missing")
        expected_source = {
            "issue_185_exact_head": EXPECTED_ISSUE_185_HEAD,
            "action_binding_blob_sha1": EXPECTED_BINDING_BLOB_SHA1,
            "live_html_sha256": EXPECTED_LIVE_HTML_SHA256,
            "words_literal_sha256": EXPECTED_WORDS_LITERAL_SHA256,
            "ordered_id_sha256": EXPECTED_ORDERED_ID_SHA256,
            "ordered_answer_letters_sha256": EXPECTED_ORDERED_ANSWER_SHA256,
            "fipi_2026_orthography_pdf_sha256": EXPECTED_FIPI_ORTHOGRAPHY_SHA256,
            "source_backed_textual_provenance": "308/308",
        }
        for key, value in expected_source.items():
            if source.get(key) != value:
                raise ServiceRequestError(f"dictionary admission source invariant drift: {key}")

        admission = authority.get("admission")
        if not isinstance(admission, Mapping):
            raise ServiceRequestError("dictionary admission metadata missing")
        expected_admission = {
            "item_count": EXPECTED_ROW_COUNT,
            "action_id": ACTION_ID,
            "semantic_id": SEMANTIC_ID,
            "mapping_resolution": "EXACT",
            "registered_user_identity_ref_required": True,
            "anonymous_identity_ref_forbidden": True,
            "server_evaluator": "deterministic_missing_root_vowel_v1",
        }
        for key, value in expected_admission.items():
            if admission.get(key) != value:
                raise ServiceRequestError(f"dictionary admission invariant drift: {key}")

        ids = authority.get("ordered_item_ids")
        answers = authority.get("answer_letter_by_item_id")
        if not isinstance(ids, list) or len(ids) != EXPECTED_ROW_COUNT:
            raise ServiceRequestError("dictionary authority must contain exactly 308 ordered item ids")
        if len(set(ids)) != EXPECTED_ROW_COUNT or not all(isinstance(value, str) and value for value in ids):
            raise ServiceRequestError("dictionary item identities are invalid or duplicated")
        if _ordered_sha(ids) != EXPECTED_ORDERED_ID_SHA256:
            raise ServiceRequestError("dictionary ordered item identities drifted")
        if not isinstance(answers, Mapping) or set(answers) != set(ids):
            raise ServiceRequestError("dictionary answer key must cover the exact 308 item identities")
        ordered_answers = []
        for item_id in ids:
            value = answers[item_id]
            if not isinstance(value, str) or value not in ALLOWED_ANSWER_LETTERS:
                raise ServiceRequestError(f"dictionary answer key has invalid vowel for {item_id}")
            ordered_answers.append(value)
        if _ordered_sha(ordered_answers) != EXPECTED_ORDERED_ANSWER_SHA256:
            raise ServiceRequestError("dictionary ordered answer key drifted")

        boundaries = authority.get("boundaries")
        if not isinstance(boundaries, Mapping):
            raise ServiceRequestError("dictionary admission boundaries missing")
        for key in (
            "whole_word_recall_admitted",
            "five_row_exam_mode_admitted",
            "generic_trainer_completion_mastery",
            "browser_local_progress_mastery",
            "asset_wide_mastery",
        ):
            if boundaries.get(key) is not False:
                raise ServiceRequestError(f"dictionary admission boundary must remain false: {key}")
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
            raise ServiceRequestError(f"unexpected dictionary admission fields: {sorted(extras)}")
        missing = ALLOWED_CLIENT_FIELDS - keys
        if missing:
            raise ServiceRequestError(f"missing dictionary admission fields: {sorted(missing)}")
        if payload.get("action_id") != ACTION_ID:
            raise ServiceRequestError("only exact missing_root_vowel_insertion action is admitted")
        item_id = payload.get("item_id")
        if not isinstance(item_id, str) or item_id not in self.answer_by_id:
            raise ServiceRequestError("unknown or non-authoritative dictionary item_id")
        letter = payload.get("letter")
        if not isinstance(letter, str) or letter not in ALLOWED_ANSWER_LETTERS:
            raise ServiceRequestError("letter must be one lowercase Russian vowel")
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
        return f"rudict.ev.{_digest(source_tuple)}"

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
        selected = str(payload["letter"])
        expected = self.answer_by_id[item_id]
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
            "idempotency_key": f"rudict.idem.{event_id.removeprefix('rudict.ev.')}",
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
                "content_version": f"live-dictionary-308@{EXPECTED_LIVE_HTML_SHA256}",
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
                "product_id": "russian-dictionary-words-trainer",
                "route": "/trenazhery/russkiy/slovarnye-slova/",
            },
            "session_id": f"rudict.session.{payload['session_started_at_ms']}",
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
                    "sensor_contract": "registered-dictionary-missing-root-vowel-admission-v1",
                    "action_id": ACTION_ID,
                    "item_id": item_id,
                    "client_request_id": payload["client_request_id"],
                },
            },
            "response_mode": "SELECTED_OPTION",
            "assistance": {"level": "UNASSISTED", "help_event_refs": [], "assistance_provider": None},
            "evaluator": {
                "evaluator_type": "DETERMINISTIC_VALIDATOR",
                "evaluator_id": "pinned-live-dictionary-missing-root-vowel",
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
                f"fipi:2026:ru-5-orfografija.pdf@sha256:{EXPECTED_FIPI_ORTHOGRAPHY_SHA256}",
            ],
            "transfer_context": {"kind": "NOT_APPLICABLE", "origin_event_refs": []},
            "retention_context": {"kind": "NONE", "delay_seconds": None, "scheduled_by_policy_version": None},
            "error_observations": error_observations,
            "subject_extension": {
                "subject_payload_schema_version": "russian-dictionary-missing-root-vowel-admission-v1.0",
                "subject_payload": {
                    "item_id": item_id,
                    "action_id": ACTION_ID,
                    "selected_letter": selected,
                    "session_started_at_ms": payload["session_started_at_ms"],
                    "client_request_id": payload["client_request_id"],
                    "whole_word_recall_admitted": False,
                    "five_row_exam_mode_admitted": False,
                },
            },
            "created_at": server_position.received_at_server,
        }

        return AdaptedObservation(
            event=event,
            target_semantic_id=SEMANTIC_ID,
            goal_context="ege:russian:dictionary:missing-root-vowel-insertion",
            admitted_edges=[],
        )
