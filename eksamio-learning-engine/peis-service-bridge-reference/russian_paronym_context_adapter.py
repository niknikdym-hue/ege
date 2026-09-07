#!/usr/bin/env python3
"""Registered-only Admissions Gate adapter for exact paronym context/collocation choice.

The browser supplies only the observed exact live item/action and one selected word
from the server-pinned exact group choices. Canonical semantic truth, correctness,
learner identity, evaluator and server position remain server-owned. Other paronym
modes and all aggregate/browser-local mastery remain outside this bounded slice.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from peis_service_bridge import AdaptedObservation, HostIdentity, ServerEventPosition, ServiceRequestError

ADAPTER_ID = "russian-paronym-context-choice-admission-v1.0"
SUBJECT_ID = "russian"
ACTION_ID = "context_collocation_choice"
SEMANTIC_ID = "ru-lexis-paronym-collocation-choice"
SOURCE_NAMESPACE = "eksamio:live-paronyms:context-choice-admission:v1"
AUTHORITY_RELATIVE_PATH = (
    "peis-production-substrate/admissions/"
    "PARONYM-CONTEXT-CHOICE-ADMISSION-AUTHORITY-v0.1.json"
)

EXPECTED_ISSUE_185_HEAD = "c5592c212557b91578ed48e1bf778e30dd489dc7"
EXPECTED_LIVE_HTML_SHA256 = "63ac66e839505930b2a9a2f3b5243d60e422226ec90890553aac5abc52b7cbda"
EXPECTED_GROUP_COUNT = 144
EXPECTED_ITEM_COUNT = 334
EXPECTED_ORDERED_GROUP_ID_SHA256 = "81c91d069a28cd9a2c1c7547c9fc92cb9df92c6cde38f3100750e2585c113813"
EXPECTED_ORDERED_ITEM_ID_SHA256 = "48eedc3e5f3751cec57152671456d314b7bcb6b13f2ee5002f35ec6660482c99"
EXPECTED_ORDERED_CORRECT_WORD_SHA256 = "75ed53cc846cc36009aa66220acb4e9959f3a88dd2068f5ef3b5ec057af569bc"
EXPECTED_ORDERED_CONTEXT_SHA256 = "491de4e281c06bbd93a7bdb2e5dbc659909e336b49d5fa316930f35c0943c3f8"
EXPECTED_ORDERED_GROUP_CHOICES_SHA256 = "4c96b0a49684a7d2988b527feabe831de1dfec60adfa4364ca927ff169b0b41e"

ALLOWED_CLIENT_FIELDS = {
    "item_id",
    "action_id",
    "selected_word",
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


class RussianParonymContextChoiceAdmissionAdapter:
    """Exact-item + exact context/collocation-choice registered evidence admission."""

    adapter_id = ADAPTER_ID
    subject_id = SUBJECT_ID

    def __init__(self, engine_root: str | Path) -> None:
        root = Path(engine_root)
        self.authority_path = root / AUTHORITY_RELATIVE_PATH
        self.authority = json.loads(self.authority_path.read_text(encoding="utf-8"))
        self._validate_authority()
        self.entry_by_id: dict[str, tuple[str, str]] = {}
        for row in self.authority["entries"]:
            item_id, group_id, correct_word = row
            self.entry_by_id[str(item_id)] = (str(group_id), str(correct_word))
        self.choices_by_group = {
            str(group_id): tuple(str(value) for value in values)
            for group_id, values in self.authority["groups"].items()
        }

    def _validate_authority(self) -> None:
        authority = self.authority
        if authority.get("schema") != "eksamio.paronym-context-choice-admission-authority.v0.1":
            raise ServiceRequestError("paronym admission authority schema drift")
        if authority.get("status") != "BOUNDED_PRODUCTION_EVENT_ADMISSION_KEY":
            raise ServiceRequestError("paronym admission authority status drift")

        source = authority.get("source_authority")
        if not isinstance(source, Mapping):
            raise ServiceRequestError("paronym source authority missing")
        expected_source = {
            "issue_185_pr": 187,
            "issue_185_exact_head": EXPECTED_ISSUE_185_HEAD,
            "live_html_sha256": EXPECTED_LIVE_HTML_SHA256,
            "group_count": EXPECTED_GROUP_COUNT,
            "entry_count": EXPECTED_ITEM_COUNT,
            "ordered_group_id_sha256": EXPECTED_ORDERED_GROUP_ID_SHA256,
            "ordered_entry_id_sha256": EXPECTED_ORDERED_ITEM_ID_SHA256,
            "fipi_2026_exact_group_correspondence": "144/144",
        }
        for key, value in expected_source.items():
            if source.get(key) != value:
                raise ServiceRequestError(f"paronym source invariant drift: {key}")

        admission = authority.get("admission")
        if not isinstance(admission, Mapping):
            raise ServiceRequestError("paronym admission metadata missing")
        expected_admission = {
            "item_count": EXPECTED_ITEM_COUNT,
            "selection_rule": "exact full-trainer entry with exactly one _____ context placeholder",
            "action_id": ACTION_ID,
            "semantic_id": SEMANTIC_ID,
            "mapping_resolution": "EXACT",
            "registered_user_identity_ref_required": True,
            "anonymous_identity_ref_forbidden": True,
            "server_evaluator": "deterministic_paronym_exact_context_choice_v1",
        }
        for key, value in expected_admission.items():
            if admission.get(key) != value:
                raise ServiceRequestError(f"paronym admission invariant drift: {key}")

        groups = authority.get("groups")
        entries = authority.get("entries")
        if not isinstance(groups, Mapping) or len(groups) != EXPECTED_GROUP_COUNT:
            raise ServiceRequestError("paronym authority must contain exactly 144 groups")
        if not isinstance(entries, list) or len(entries) != EXPECTED_ITEM_COUNT:
            raise ServiceRequestError("paronym authority must contain exactly 334 items")
        ordered_group_ids = list(groups)
        if _ordered_sha(ordered_group_ids) != EXPECTED_ORDERED_GROUP_ID_SHA256:
            raise ServiceRequestError("paronym ordered group identities drifted")

        ordered_item_ids: list[str] = []
        ordered_correct_words: list[str] = []
        seen: set[str] = set()
        for row in entries:
            if not isinstance(row, list) or len(row) != 3 or not all(isinstance(value, str) and value for value in row):
                raise ServiceRequestError("paronym authority entry row invalid")
            item_id, group_id, correct_word = row
            if item_id in seen:
                raise ServiceRequestError("paronym item identities are duplicated")
            seen.add(item_id)
            choices = groups.get(group_id)
            if not isinstance(choices, list) or len(choices) < 2 or correct_word not in choices:
                raise ServiceRequestError(f"paronym exact choice key invalid for {item_id}")
            ordered_item_ids.append(item_id)
            ordered_correct_words.append(correct_word)
        if _ordered_sha(ordered_item_ids) != EXPECTED_ORDERED_ITEM_ID_SHA256:
            raise ServiceRequestError("paronym ordered item identities drifted")
        if _ordered_sha(ordered_correct_words) != EXPECTED_ORDERED_CORRECT_WORD_SHA256:
            raise ServiceRequestError("paronym ordered correct-word key drifted")

        integrity = authority.get("integrity")
        expected_integrity = {
            "ordered_item_id_sha256": EXPECTED_ORDERED_ITEM_ID_SHA256,
            "ordered_correct_word_sha256": EXPECTED_ORDERED_CORRECT_WORD_SHA256,
            "ordered_context_sha256": EXPECTED_ORDERED_CONTEXT_SHA256,
            "ordered_group_choices_sha256": EXPECTED_ORDERED_GROUP_CHOICES_SHA256,
        }
        if not isinstance(integrity, Mapping):
            raise ServiceRequestError("paronym admission integrity block missing")
        for key, value in expected_integrity.items():
            if integrity.get(key) != value:
                raise ServiceRequestError(f"paronym admission integrity drift: {key}")

        boundaries = authority.get("boundaries")
        if not isinstance(boundaries, Mapping):
            raise ServiceRequestError("paronym admission boundaries missing")
        for key in (
            "meaning_match_admitted",
            "independent_paronym_recall_admitted",
            "exam_error_correction_admitted",
            "generic_trainer_completion_mastery",
            "browser_local_progress_mastery",
            "asset_wide_mastery",
        ):
            if boundaries.get(key) is not False:
                raise ServiceRequestError(f"paronym boundary must remain false: {key}")
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
            raise ServiceRequestError(f"unexpected paronym admission fields: {sorted(extras)}")
        missing = ALLOWED_CLIENT_FIELDS - keys
        if missing:
            raise ServiceRequestError(f"missing paronym admission fields: {sorted(missing)}")
        if payload.get("action_id") != ACTION_ID:
            raise ServiceRequestError("only exact context_collocation_choice action is admitted")
        item_id = payload.get("item_id")
        if not isinstance(item_id, str) or item_id not in self.entry_by_id:
            raise ServiceRequestError("unknown or non-admitted paronym item_id")
        selected_word = payload.get("selected_word")
        if not isinstance(selected_word, str) or not selected_word:
            raise ServiceRequestError("selected_word must be a non-empty exact choice")
        group_id, _correct = self.entry_by_id[item_id]
        if selected_word not in self.choices_by_group[group_id]:
            raise ServiceRequestError("selected_word must be an exact pinned choice for the item group")
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
        return f"rupar.ev.{_digest(source_tuple)}"

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
        selected_word = str(payload["selected_word"])
        group_id, correct_word = self.entry_by_id[item_id]
        choices = self.choices_by_group[group_id]
        correct = selected_word == correct_word
        event_id = self.stable_event_id(payload)

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

        semantic_targets = [
            {
                "semantic_id": SEMANTIC_ID,
                "target_role": "PRIMARY",
                "mapping_resolution": "EXACT",
                "mapping_confidence": 1.0,
                "mapping_review_status": "accepted",
            }
        ]
        event = {
            "event_id": event_id,
            "idempotency_key": f"rupar.idem.{event_id.removeprefix('rupar.ev.')}",
            "schema_version": "0.1.0",
            "event_kind": "PERFORMANCE_OBSERVATION",
            "learner_profile_id": host_identity.learner_profile_id,
            "identity_refs": copy.deepcopy(host_identity.identity_refs),
            "subject_id": SUBJECT_ID,
            "semantic_targets": semantic_targets,
            "semantic_context": {
                "semantic_registry_version": "russian-current-v2@7edddb9f9764b5e8cdf7e2653c425e5f90c4ffe9",
                "semantic_mapping_version": f"issue185-action-scoped@{EXPECTED_ISSUE_185_HEAD}",
                "mapping_artifact_refs": [AUTHORITY_RELATIVE_PATH],
            },
            "source": {
                "object_type": "thematic_trainer_item",
                "object_id": item_id,
                "content_version": f"live-paronyms-334@{EXPECTED_LIVE_HTML_SHA256}",
                "item_version": "issue185-c5592c2-context-choice-334",
                "route_metadata": {
                    "exam": "EGE",
                    "exam_year": 2026,
                    "task_route": None,
                    "historical_format": False,
                },
            },
            "product": {
                "source_type": "thematic_trainer",
                "product_id": "russian-paronyms-trainer",
                "route": "/trenazhery/russkiy/paronimy/",
            },
            "session_id": f"rupar.session.{payload['session_started_at_ms']}",
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
                "response_value": selected_word,
                "result_details": {
                    "sensor_contract": "registered-paronym-context-choice-admission-v1",
                    "action_id": ACTION_ID,
                    "item_id": item_id,
                    "group_id": group_id,
                    "client_request_id": payload["client_request_id"],
                    "choice_contract": "EXACT_PINNED_GROUP_MEMBER_ONLY",
                },
            },
            "response_mode": "SINGLE_SELECT",
            "assistance": {"level": "UNASSISTED", "help_event_refs": [], "assistance_provider": None},
            "evaluator": {
                "evaluator_type": "DETERMINISTIC_VALIDATOR",
                "evaluator_id": "pinned-live-paronym-context-choice",
                "evaluator_version": "issue185-c5592c2-context-choice-334-v1",
                "trust_class": "DETERMINISTIC_HIGH",
                "uncertainty": 0.0,
                "review_status": "not_required",
                "rubric_version": None,
                "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
            },
            "provenance_refs": [
                AUTHORITY_RELATIVE_PATH,
                f"issue185-pr187@{EXPECTED_ISSUE_185_HEAD}",
            ],
            "transfer_context": {"kind": "NOT_APPLICABLE", "origin_event_refs": []},
            "retention_context": {"kind": "NONE", "delay_seconds": None, "scheduled_by_policy_version": None},
            "error_observations": error_observations,
            "subject_extension": {
                "subject_payload_schema_version": "russian-paronym-context-choice-admission-v1.0",
                "subject_payload": {
                    "item_id": item_id,
                    "group_id": group_id,
                    "action_id": ACTION_ID,
                    "selected_word": selected_word,
                    "choice_count": len(choices),
                    "session_started_at_ms": payload["session_started_at_ms"],
                    "client_request_id": payload["client_request_id"],
                    "meaning_match_admitted": False,
                    "independent_paronym_recall_admitted": False,
                    "exam_error_correction_admitted": False,
                },
            },
            "created_at": server_position.received_at_server,
        }
        return AdaptedObservation(
            event=event,
            target_semantic_id=SEMANTIC_ID,
            goal_context="ege:russian:paronyms:context-collocation-choice",
            admitted_edges=[],
        )
