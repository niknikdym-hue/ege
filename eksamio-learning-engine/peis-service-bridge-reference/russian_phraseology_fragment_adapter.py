#!/usr/bin/env python3
"""Registered-only Admissions Gate adapter for exact phraseology fragment identification.

The browser supplies an observation only: exact admitted item id, exact action,
typed response and client timing/idempotency material. Canonical semantic truth,
answer key, correctness, evaluator, learner identity and server position remain
server-owned. Only the bounded 199-item exact-in-example + exam-eligible subset
is admitted; variants and other phraseology modes are explicitly outside this slice.
"""
from __future__ import annotations

import copy
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Mapping

from peis_service_bridge import AdaptedObservation, HostIdentity, ServerEventPosition, ServiceRequestError

ADAPTER_ID = "russian-phraseology-fragment-admission-v1.0"
SUBJECT_ID = "russian"
ACTION_ID = "fragment_identification"
SEMANTIC_ID = "ru-lexis-phraseologism-fragment-identification"
SOURCE_NAMESPACE = "eksamio:live-phraseology:fragment-identification-admission:v1"
AUTHORITY_RELATIVE_PATH = (
    "peis-production-substrate/admissions/"
    "PHRASEOLOGY-FRAGMENT-IDENTIFICATION-ADMISSION-AUTHORITY-v0.1.json"
)

EXPECTED_ISSUE_185_HEAD = "c5592c212557b91578ed48e1bf778e30dd489dc7"
EXPECTED_BINDING_BLOB_SHA1 = "6b513376a3040dc28e9c869028687144ccf0ff87"
EXPECTED_CAPTURE_HEAD = "3378eca3707bcbdef66f856efefed86d7e53f5a9"
EXPECTED_CAPTURE_RUN = 34122288161
EXPECTED_CAPTURE_ARTIFACT_ID = 10018663491
EXPECTED_CAPTURE_ARTIFACT_DIGEST = "sha256:d78c987c6c253f43d2c3bbcb0674062ca99585078d3110f858a631fab1e08154"
EXPECTED_CAPTURE_JSON_SHA256 = "dfdc038a66bb887c487d6049f42359c2f8bfd1b331bee8f2ce598a155aaba2a2"
EXPECTED_LIVE_HTML_SHA256 = "69f69716dbad959b754354a0f3d1523dc4b05ae4732eeb234a68b3a43ebfe68b"
EXPECTED_PHRASEOLOGY_SCRIPT_SHA256 = "7d9cc134594456de3d36367bfce37fbe5ce0f855670ec550e0e71a8afa41cd10"
EXPECTED_ALL_285_ORDERED_ID_SHA256 = "22b33854b09b4b212310169f48c69237d4a4c8ee1ed0b5aed95b50f9ec63b534"
EXPECTED_ADMITTED_199_ORDERED_ID_SHA256 = "7190b651b1b9e279b695fd5cd766d00001c3a37e15f5b1765890fb4b21aea413"
EXPECTED_ORDERED_PRIMARY_EXPRESSION_SHA256 = "164c36f17178217b68dac9818fe4f7e2d63d9548a86cc157206ef66014014aad"
EXPECTED_ORDERED_EXAMPLE_SHA256 = "970d9ae5bba62a3cf2cd46322f48ae874560a08adb0a0394cca6b1b9d69de6bd"
EXPECTED_FIPI_LEXICON_SHA256 = "28c3dfd5266319e539025f4b25ce71724ec20c83c42820e1abe99f8fdeef66a8"
EXPECTED_ITEM_COUNT = 199

ALLOWED_CLIENT_FIELDS = {
    "item_id",
    "action_id",
    "response_text",
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


def _normalize_response(value: str) -> str:
    # Technical normalization only: preserve lexical letters, including е/ё distinction.
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


class RussianPhraseologyFragmentAdmissionAdapter:
    """Exact-item + exact fragment-identification registered evidence admission."""

    adapter_id = ADAPTER_ID
    subject_id = SUBJECT_ID

    def __init__(self, engine_root: str | Path) -> None:
        root = Path(engine_root)
        self.authority_path = root / AUTHORITY_RELATIVE_PATH
        self.authority = json.loads(self.authority_path.read_text(encoding="utf-8"))
        self._validate_authority()
        self.answer_by_id = {
            str(item_id): str(expression)
            for item_id, expression in self.authority["answer_expression_by_item_id"].items()
        }

    def _validate_authority(self) -> None:
        authority = self.authority
        if authority.get("schema") != "eksamio.phraseology-fragment-identification-admission-authority.v0.1":
            raise ServiceRequestError("phraseology admission authority schema drift")
        if authority.get("status") != "BOUNDED_PRODUCTION_EVENT_ADMISSION_KEY":
            raise ServiceRequestError("phraseology admission authority status drift")

        source = authority.get("source_authority")
        if not isinstance(source, Mapping):
            raise ServiceRequestError("phraseology admission source authority missing")
        expected_source = {
            "issue_185_pr": 187,
            "issue_185_exact_head": EXPECTED_ISSUE_185_HEAD,
            "action_binding_blob_sha1": EXPECTED_BINDING_BLOB_SHA1,
            "capture_head": EXPECTED_CAPTURE_HEAD,
            "live_capture_workflow_run": EXPECTED_CAPTURE_RUN,
            "live_capture_artifact_id": EXPECTED_CAPTURE_ARTIFACT_ID,
            "live_capture_artifact_digest": EXPECTED_CAPTURE_ARTIFACT_DIGEST,
            "live_capture_json_sha256": EXPECTED_CAPTURE_JSON_SHA256,
            "live_html_sha256": EXPECTED_LIVE_HTML_SHA256,
            "phraseology_script_sha256": EXPECTED_PHRASEOLOGY_SCRIPT_SHA256,
            "all_285_ordered_id_sha256": EXPECTED_ALL_285_ORDERED_ID_SHA256,
            "fipi_2026_lexicon_phraseology_pdf_sha256": EXPECTED_FIPI_LEXICON_SHA256,
            "source_backed_textual_provenance": "285/285",
        }
        for key, value in expected_source.items():
            if source.get(key) != value:
                raise ServiceRequestError(f"phraseology admission source invariant drift: {key}")

        admission = authority.get("admission")
        if not isinstance(admission, Mapping):
            raise ServiceRequestError("phraseology admission metadata missing")
        expected_admission = {
            "item_count": EXPECTED_ITEM_COUNT,
            "selection_rule": "examEligible === true AND exactInExample === true",
            "action_id": ACTION_ID,
            "semantic_id": SEMANTIC_ID,
            "mapping_resolution": "EXACT",
            "registered_user_identity_ref_required": True,
            "anonymous_identity_ref_forbidden": True,
            "server_evaluator": "deterministic_phraseology_exact_fragment_v1",
        }
        for key, value in expected_admission.items():
            if admission.get(key) != value:
                raise ServiceRequestError(f"phraseology admission invariant drift: {key}")

        ids = authority.get("ordered_item_ids")
        answers = authority.get("answer_expression_by_item_id")
        if not isinstance(ids, list) or len(ids) != EXPECTED_ITEM_COUNT:
            raise ServiceRequestError("phraseology authority must contain exactly 199 admitted item ids")
        if len(set(ids)) != EXPECTED_ITEM_COUNT or not all(isinstance(value, str) and value for value in ids):
            raise ServiceRequestError("phraseology admitted item identities are invalid or duplicated")
        if _ordered_sha(ids) != EXPECTED_ADMITTED_199_ORDERED_ID_SHA256:
            raise ServiceRequestError("phraseology ordered admitted item identities drifted")
        if not isinstance(answers, Mapping) or set(answers) != set(ids):
            raise ServiceRequestError("phraseology answer key must cover exact admitted item identities")

        ordered_answers: list[str] = []
        normalized_answers: list[str] = []
        for item_id in ids:
            value = answers[item_id]
            if not isinstance(value, str) or not value.strip():
                raise ServiceRequestError(f"phraseology answer key has invalid expression for {item_id}")
            ordered_answers.append(value)
            normalized_answers.append(_normalize_response(value))
        if _ordered_sha(ordered_answers) != EXPECTED_ORDERED_PRIMARY_EXPRESSION_SHA256:
            raise ServiceRequestError("phraseology ordered primary-expression key drifted")
        if len(set(normalized_answers)) != EXPECTED_ITEM_COUNT:
            raise ServiceRequestError("phraseology normalized answer identities must remain unique")

        integrity = authority.get("integrity")
        if not isinstance(integrity, Mapping):
            raise ServiceRequestError("phraseology admission integrity block missing")
        expected_integrity = {
            "ordered_admitted_id_sha256": EXPECTED_ADMITTED_199_ORDERED_ID_SHA256,
            "ordered_primary_expression_sha256": EXPECTED_ORDERED_PRIMARY_EXPRESSION_SHA256,
            "ordered_example_sha256": EXPECTED_ORDERED_EXAMPLE_SHA256,
            "unique_primary_expression_count": EXPECTED_ITEM_COUNT,
            "primary_expression_occurs_in_example_after_bounded_normalization_count": EXPECTED_ITEM_COUNT,
            "admitted_rows_with_nonempty_variants": 13,
            "admitted_variant_strings_occurring_in_exact_example": 0,
        }
        for key, value in expected_integrity.items():
            if integrity.get(key) != value:
                raise ServiceRequestError(f"phraseology admission integrity drift: {key}")

        boundaries = authority.get("boundaries")
        if not isinstance(boundaries, Mapping):
            raise ServiceRequestError("phraseology admission boundaries missing")
        for key in (
            "all_285_items_admitted",
            "remaining_86_phraseology_rows_admitted",
            "variant_answers_admitted",
            "meaning_choice_admitted",
            "missing_component_admitted",
            "by_meaning_recall_admitted",
            "generic_trainer_completion_mastery",
            "browser_local_progress_mastery",
            "asset_wide_mastery",
        ):
            if boundaries.get(key) is not False:
                raise ServiceRequestError(f"phraseology admission boundary must remain false: {key}")
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
            raise ServiceRequestError(f"unexpected phraseology admission fields: {sorted(extras)}")
        missing = ALLOWED_CLIENT_FIELDS - keys
        if missing:
            raise ServiceRequestError(f"missing phraseology admission fields: {sorted(missing)}")
        if payload.get("action_id") != ACTION_ID:
            raise ServiceRequestError("only exact fragment_identification action is admitted")
        item_id = payload.get("item_id")
        if not isinstance(item_id, str) or item_id not in self.answer_by_id:
            raise ServiceRequestError("unknown or non-admitted phraseology item_id")
        response_text = payload.get("response_text")
        if not isinstance(response_text, str) or not response_text.strip() or len(response_text) > 256:
            raise ServiceRequestError("response_text must be a non-empty string of at most 256 characters")
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
        return f"ruphr.ev.{_digest(source_tuple)}"

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
        response_text = str(payload["response_text"])
        expected = self.answer_by_id[item_id]
        normalized_response = _normalize_response(response_text)
        normalized_expected = _normalize_response(expected)
        correct = normalized_response == normalized_expected
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
            "idempotency_key": f"ruphr.idem.{event_id.removeprefix('ruphr.ev.')}",
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
                "content_version": f"live-phraseology-285@{EXPECTED_LIVE_HTML_SHA256}",
                "item_version": "issue185-c5592c2-fragment-199",
                "route_metadata": {
                    "exam": "EGE",
                    "exam_year": 2026,
                    "task_route": None,
                    "historical_format": False,
                },
            },
            "product": {
                "source_type": "thematic_trainer",
                "product_id": "russian-phraseology-trainer",
                "route": "/trenazhery/russkiy/frazeologizmy/",
            },
            "session_id": f"ruphr.session.{payload['session_started_at_ms']}",
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
                "response_value": response_text,
                "result_details": {
                    "sensor_contract": "registered-phraseology-fragment-identification-admission-v1",
                    "action_id": ACTION_ID,
                    "item_id": item_id,
                    "client_request_id": payload["client_request_id"],
                    "normalization": "NFKC_WHITESPACE_CASEFOLD_ONLY",
                },
            },
            "response_mode": "TYPED_TEXT",
            "assistance": {"level": "UNASSISTED", "help_event_refs": [], "assistance_provider": None},
            "evaluator": {
                "evaluator_type": "DETERMINISTIC_VALIDATOR",
                "evaluator_id": "pinned-live-phraseology-exact-fragment",
                "evaluator_version": "issue185-c5592c2-fragment-199-v1",
                "trust_class": "DETERMINISTIC_HIGH",
                "uncertainty": 0.0,
                "review_status": "not_required",
                "rubric_version": None,
                "official_truth_status": "OFFICIAL_OR_DETERMINISTIC",
            },
            "provenance_refs": [
                AUTHORITY_RELATIVE_PATH,
                "issue185-pr187@c5592c212557b91578ed48e1bf778e30dd489dc7",
                f"fipi:2026:ru-2-leksika-i-frazeologija.pdf@sha256:{EXPECTED_FIPI_LEXICON_SHA256}",
            ],
            "transfer_context": {"kind": "NOT_APPLICABLE", "origin_event_refs": []},
            "retention_context": {"kind": "NONE", "delay_seconds": None, "scheduled_by_policy_version": None},
            "error_observations": error_observations,
            "subject_extension": {
                "subject_payload_schema_version": "russian-phraseology-fragment-identification-admission-v1.0",
                "subject_payload": {
                    "item_id": item_id,
                    "action_id": ACTION_ID,
                    "response_text": response_text,
                    "session_started_at_ms": payload["session_started_at_ms"],
                    "client_request_id": payload["client_request_id"],
                    "admitted_subset_count": EXPECTED_ITEM_COUNT,
                    "variant_answers_admitted": False,
                    "meaning_choice_admitted": False,
                    "missing_component_admitted": False,
                    "by_meaning_recall_admitted": False,
                },
            },
            "created_at": server_position.received_at_server,
        }

        return AdaptedObservation(
            event=event,
            target_semantic_id=SEMANTIC_ID,
            goal_context="ege:russian:phraseology:fragment-identification",
            admitted_edges=[],
        )
