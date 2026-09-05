#!/usr/bin/env python3
"""Authenticated Eksamio registration and consent boundary.

The public learner path is intentionally narrow: registration is e-mail only,
personal-data consent is separate and mandatory, marketing consent is separate
and optional, and the new path never supplies anonymous learner context.

Consent evidence is append-only, server-timestamped, versioned and stored
against an opaque user identity reference. Initial registration consent is also
bound to the exact passwordless challenge that follows from that submission,
so stale or unrelated consent cannot authorize another challenge.

This module does not send marketing messages and does not own final legal copy.
"""
from __future__ import annotations

import re
import secrets
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping


class RegistrationError(ValueError):
    """Base class for bounded registration/consent failures."""


class InvalidRegistrationRequest(RegistrationError):
    pass


class PersonalDataConsentRequired(RegistrationError):
    pass


class ConsentReplayConflict(RegistrationError):
    pass


class MissingConsentEvidence(RegistrationError):
    pass


CONSENT_PERSONAL_DATA = "PERSONAL_DATA"
CONSENT_MARKETING = "MARKETING"
ACTION_GRANT = "GRANT"
ACTION_DECLINE = "DECLINE"
ACTION_REVOKE = "REVOKE"
_CONSENT_TYPES = {CONSENT_PERSONAL_DATA, CONSENT_MARKETING}
_ACTIONS = {ACTION_GRANT, ACTION_DECLINE, ACTION_REVOKE}
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,159}$")
_CHALLENGE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{3,191}$")


@dataclass(frozen=True)
class RegistrationReceipt:
    challenge_id: str
    channel: str
    expires_at_epoch: int
    marketing_consent: bool


class RegistrationConsentStore:
    """Append-only server-owned consent evidence without raw contact PII.

    `event_seq` is the database-owned total order. Legal/audit time remains in
    `captured_at_epoch`, but effective consent state never depends on a random
    event id or wall-clock ties.
    """

    def __init__(
        self,
        connection: Any,
        *,
        now_provider: Callable[[], int] | None = None,
        event_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.connection = connection
        self.now_provider = now_provider or (lambda: int(time.time()))
        self.event_id_factory = event_id_factory or (
            lambda: "consent:" + secrets.token_urlsafe(18)
        )
        self._create_schema()

    def _create_schema(self) -> None:
        # This reference store currently follows the repository's SQLite DB
        # contract. Production PostgreSQL gets an equivalent generated sequence
        # in the deployment adapter rather than relying on wall-clock ordering.
        statements = [
            """
            CREATE TABLE IF NOT EXISTS registration_consent_events (
                event_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                user_identity_ref TEXT NOT NULL,
                consent_type TEXT NOT NULL,
                action TEXT NOT NULL,
                captured_at_epoch BIGINT NOT NULL,
                document_version TEXT NOT NULL,
                text_version TEXT NOT NULL,
                client_request_id TEXT NOT NULL,
                registration_challenge_id TEXT
            )
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_registration_consent_request
            ON registration_consent_events(
                user_identity_ref, consent_type, client_request_id
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_registration_consent_latest
            ON registration_consent_events(
                user_identity_ref, consent_type, event_seq
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_registration_consent_challenge
            ON registration_consent_events(
                user_identity_ref, registration_challenge_id, consent_type
            )
            """,
        ]
        with self.connection:
            for statement in statements:
                self.connection.execute(statement)

    @staticmethod
    def _validate_version(value: Any, field: str) -> str:
        if not isinstance(value, str) or not _VERSION_RE.fullmatch(value):
            raise InvalidRegistrationRequest(f"{field} has invalid version id")
        return value

    @staticmethod
    def _validate_client_request_id(value: Any) -> str:
        if not isinstance(value, str) or not _REQUEST_ID_RE.fullmatch(value):
            raise InvalidRegistrationRequest("client_request_id is invalid")
        return value

    @staticmethod
    def _validate_user_identity_ref(value: Any) -> str:
        if (
            not isinstance(value, str)
            or not value.startswith("user:")
            or "@" in value
        ):
            raise InvalidRegistrationRequest("opaque user identity ref required")
        return value

    @staticmethod
    def _validate_challenge_id(value: Any) -> str:
        if not isinstance(value, str) or not _CHALLENGE_ID_RE.fullmatch(value):
            raise InvalidRegistrationRequest("registration challenge id is invalid")
        return value

    def _new_event_id(self) -> str:
        event_id = self.event_id_factory()
        if not isinstance(event_id, str) or len(event_id) < 12:
            raise InvalidRegistrationRequest("consent event id factory failed")
        return event_id

    def _rows_for_registration_request(
        self, *, user_identity_ref: str, client_request_id: str
    ) -> list[Mapping[str, Any]]:
        return list(
            self.connection.execute(
                """
                SELECT * FROM registration_consent_events
                WHERE user_identity_ref = ? AND client_request_id = ?
                  AND registration_challenge_id IS NOT NULL
                ORDER BY event_seq
                """,
                (user_identity_ref, client_request_id),
            ).fetchall()
        )

    def existing_registration_decision(
        self,
        *,
        user_identity_ref: str,
        client_request_id: str,
        personal_data_document_version: str,
        personal_data_text_version: str,
        marketing_document_version: str,
        marketing_text_version: str,
        marketing_granted: bool,
    ) -> Mapping[str, Any] | None:
        user_identity_ref = self._validate_user_identity_ref(user_identity_ref)
        client_request_id = self._validate_client_request_id(client_request_id)
        pd_doc = self._validate_version(
            personal_data_document_version, "personal_data_document_version"
        )
        pd_text = self._validate_version(
            personal_data_text_version, "personal_data_text_version"
        )
        marketing_doc = self._validate_version(
            marketing_document_version, "marketing_document_version"
        )
        marketing_text = self._validate_version(
            marketing_text_version, "marketing_text_version"
        )
        rows = self._rows_for_registration_request(
            user_identity_ref=user_identity_ref,
            client_request_id=client_request_id,
        )
        if not rows:
            return None
        if len(rows) != 2:
            raise ConsentReplayConflict("partial registration consent evidence exists")
        by_type = {str(row["consent_type"]): row for row in rows}
        if set(by_type) != {CONSENT_PERSONAL_DATA, CONSENT_MARKETING}:
            raise ConsentReplayConflict("registration consent evidence has wrong shape")
        pd_row = by_type[CONSENT_PERSONAL_DATA]
        marketing_row = by_type[CONSENT_MARKETING]
        challenge_ids = {
            str(pd_row["registration_challenge_id"]),
            str(marketing_row["registration_challenge_id"]),
        }
        expected_marketing_action = ACTION_GRANT if marketing_granted else ACTION_DECLINE
        if (
            len(challenge_ids) != 1
            or str(pd_row["action"]) != ACTION_GRANT
            or str(pd_row["document_version"]) != pd_doc
            or str(pd_row["text_version"]) != pd_text
            or str(marketing_row["action"]) != expected_marketing_action
            or str(marketing_row["document_version"]) != marketing_doc
            or str(marketing_row["text_version"]) != marketing_text
        ):
            raise ConsentReplayConflict(
                "registration retry changed consent choice or legal-text version"
            )
        return {
            "challenge_id": next(iter(challenge_ids)),
            "marketing_consent": marketing_granted,
        }

    def record_registration_decision(
        self,
        *,
        user_identity_ref: str,
        registration_challenge_id: str,
        client_request_id: str,
        personal_data_document_version: str,
        personal_data_text_version: str,
        marketing_document_version: str,
        marketing_text_version: str,
        marketing_granted: bool,
    ) -> Mapping[str, Any]:
        user_identity_ref = self._validate_user_identity_ref(user_identity_ref)
        registration_challenge_id = self._validate_challenge_id(
            registration_challenge_id
        )
        client_request_id = self._validate_client_request_id(client_request_id)
        pd_doc = self._validate_version(
            personal_data_document_version, "personal_data_document_version"
        )
        pd_text = self._validate_version(
            personal_data_text_version, "personal_data_text_version"
        )
        marketing_doc = self._validate_version(
            marketing_document_version, "marketing_document_version"
        )
        marketing_text = self._validate_version(
            marketing_text_version, "marketing_text_version"
        )

        existing = self.existing_registration_decision(
            user_identity_ref=user_identity_ref,
            client_request_id=client_request_id,
            personal_data_document_version=pd_doc,
            personal_data_text_version=pd_text,
            marketing_document_version=marketing_doc,
            marketing_text_version=marketing_text,
            marketing_granted=marketing_granted,
        )
        if existing is not None:
            if str(existing["challenge_id"]) != registration_challenge_id:
                raise ConsentReplayConflict(
                    "registration retry attempted to bind consent to a new challenge"
                )
            return {"status": "ALREADY_RECORDED", **existing}

        captured_at_epoch = int(self.now_provider())
        pd_event_id = self._new_event_id()
        marketing_event_id = self._new_event_id()
        marketing_action = ACTION_GRANT if marketing_granted else ACTION_DECLINE
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO registration_consent_events(
                    event_id, user_identity_ref, consent_type, action,
                    captured_at_epoch, document_version, text_version,
                    client_request_id, registration_challenge_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pd_event_id,
                    user_identity_ref,
                    CONSENT_PERSONAL_DATA,
                    ACTION_GRANT,
                    captured_at_epoch,
                    pd_doc,
                    pd_text,
                    client_request_id,
                    registration_challenge_id,
                ),
            )
            self.connection.execute(
                """
                INSERT INTO registration_consent_events(
                    event_id, user_identity_ref, consent_type, action,
                    captured_at_epoch, document_version, text_version,
                    client_request_id, registration_challenge_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    marketing_event_id,
                    user_identity_ref,
                    CONSENT_MARKETING,
                    marketing_action,
                    captured_at_epoch,
                    marketing_doc,
                    marketing_text,
                    client_request_id,
                    registration_challenge_id,
                ),
            )
        return {
            "status": "RECORDED",
            "challenge_id": registration_challenge_id,
            "marketing_consent": marketing_granted,
        }

    def append_event(
        self,
        *,
        user_identity_ref: str,
        consent_type: str,
        action: str,
        document_version: str,
        text_version: str,
        client_request_id: str,
    ) -> Mapping[str, Any]:
        user_identity_ref = self._validate_user_identity_ref(user_identity_ref)
        if consent_type not in _CONSENT_TYPES:
            raise InvalidRegistrationRequest("unknown consent_type")
        if action not in _ACTIONS:
            raise InvalidRegistrationRequest("unknown consent action")
        document_version = self._validate_version(
            document_version, "document_version"
        )
        text_version = self._validate_version(text_version, "text_version")
        client_request_id = self._validate_client_request_id(client_request_id)

        existing = self.connection.execute(
            """
            SELECT * FROM registration_consent_events
            WHERE user_identity_ref = ? AND consent_type = ?
              AND client_request_id = ?
            """,
            (user_identity_ref, consent_type, client_request_id),
        ).fetchone()
        if existing is not None:
            if (
                existing["registration_challenge_id"] is None
                and str(existing["action"]) == action
                and str(existing["document_version"]) == document_version
                and str(existing["text_version"]) == text_version
            ):
                return {
                    "status": "ALREADY_RECORDED",
                    "event_id": existing["event_id"],
                }
            raise ConsentReplayConflict(
                "consent retry changed action, scope or legal-text version"
            )

        event_id = self._new_event_id()
        captured_at_epoch = int(self.now_provider())
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO registration_consent_events(
                    event_id, user_identity_ref, consent_type, action,
                    captured_at_epoch, document_version, text_version,
                    client_request_id, registration_challenge_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    event_id,
                    user_identity_ref,
                    consent_type,
                    action,
                    captured_at_epoch,
                    document_version,
                    text_version,
                    client_request_id,
                ),
            )
        return {"status": "RECORDED", "event_id": event_id}

    def latest_state(
        self, *, user_identity_ref: str, consent_type: str
    ) -> Mapping[str, Any] | None:
        if consent_type not in _CONSENT_TYPES:
            raise InvalidRegistrationRequest("unknown consent_type")
        return self.connection.execute(
            """
            SELECT * FROM registration_consent_events
            WHERE user_identity_ref = ? AND consent_type = ?
            ORDER BY event_seq DESC
            LIMIT 1
            """,
            (user_identity_ref, consent_type),
        ).fetchone()

    def personal_data_granted_for_challenge(
        self, *, user_identity_ref: str, registration_challenge_id: str
    ) -> bool:
        row = self.connection.execute(
            """
            SELECT * FROM registration_consent_events
            WHERE user_identity_ref = ?
              AND registration_challenge_id = ?
              AND consent_type = ?
            ORDER BY event_seq DESC
            LIMIT 1
            """,
            (
                user_identity_ref,
                registration_challenge_id,
                CONSENT_PERSONAL_DATA,
            ),
        ).fetchone()
        return row is not None and str(row["action"]) == ACTION_GRANT

    def marketing_allowed(self, *, user_identity_ref: str) -> bool:
        row = self.latest_state(
            user_identity_ref=user_identity_ref,
            consent_type=CONSENT_MARKETING,
        )
        return row is not None and str(row["action"]) == ACTION_GRANT


class RegistrationService:
    """E-mail registration facade over the existing passwordless service."""

    BEGIN_ALLOWED_FIELDS = {
        "email",
        "personal_data_consent",
        "marketing_consent",
        "personal_data_document_version",
        "personal_data_text_version",
        "marketing_document_version",
        "marketing_text_version",
        "client_request_id",
    }
    VERIFY_ALLOWED_FIELDS = {"challenge_id", "code"}

    def __init__(
        self,
        *,
        identity_service: Any,
        consent_store: RegistrationConsentStore,
    ) -> None:
        self.identity_service = identity_service
        self.consent_store = consent_store

    def _registration_user_identity_ref(self, email: str) -> str:
        try:
            normalized = self.identity_service._normalize_contact("email", email)
            user_ref = self.identity_service._user_identity_ref("email", normalized)
        except (AttributeError, TypeError, ValueError) as exc:
            raise InvalidRegistrationRequest("invalid e-mail contact") from exc
        if not isinstance(user_ref, str) or not user_ref.startswith("user:"):
            raise InvalidRegistrationRequest("identity service returned invalid user ref")
        return user_ref

    @staticmethod
    def _validate_begin_payload(payload: Mapping[str, Any]) -> None:
        if (
            not isinstance(payload, Mapping)
            or set(payload) != RegistrationService.BEGIN_ALLOWED_FIELDS
        ):
            raise InvalidRegistrationRequest(
                "registration payload must contain only bounded registration fields"
            )
        if not isinstance(payload.get("email"), str):
            raise InvalidRegistrationRequest("email must be a string")
        if payload.get("personal_data_consent") is not True:
            raise PersonalDataConsentRequired(
                "personal-data consent is required for registration"
            )
        if not isinstance(payload.get("marketing_consent"), bool):
            raise InvalidRegistrationRequest("marketing_consent must be boolean")

    def _receipt_from_existing(
        self, existing: Mapping[str, Any]
    ) -> RegistrationReceipt:
        challenge_id = str(existing["challenge_id"])
        row = self.identity_service.auth_store.challenge(challenge_id)
        if row is None:
            raise ConsentReplayConflict(
                "consent evidence references a missing passwordless challenge"
            )
        return RegistrationReceipt(
            challenge_id=challenge_id,
            channel=str(row["channel"]),
            expires_at_epoch=int(row["expires_at_epoch"]),
            marketing_consent=bool(existing["marketing_consent"]),
        )

    def begin_registration(self, payload: Mapping[str, Any]) -> RegistrationReceipt:
        self._validate_begin_payload(payload)
        email = str(payload["email"])
        user_ref = self._registration_user_identity_ref(email)
        client_request_id = RegistrationConsentStore._validate_client_request_id(
            payload["client_request_id"]
        )
        marketing_granted = bool(payload["marketing_consent"])

        existing = self.consent_store.existing_registration_decision(
            user_identity_ref=user_ref,
            client_request_id=client_request_id,
            personal_data_document_version=payload["personal_data_document_version"],
            personal_data_text_version=payload["personal_data_text_version"],
            marketing_document_version=payload["marketing_document_version"],
            marketing_text_version=payload["marketing_text_version"],
            marketing_granted=marketing_granted,
        )
        if existing is not None:
            return self._receipt_from_existing(existing)

        # Owner decision: no guest learner and no anon->account continuity.
        identity_receipt = self.identity_service.begin(
            {"channel": "email", "contact": email},
            anonymous_host_token=None,
        )
        self.consent_store.record_registration_decision(
            user_identity_ref=user_ref,
            registration_challenge_id=identity_receipt.challenge_id,
            client_request_id=client_request_id,
            personal_data_document_version=payload["personal_data_document_version"],
            personal_data_text_version=payload["personal_data_text_version"],
            marketing_document_version=payload["marketing_document_version"],
            marketing_text_version=payload["marketing_text_version"],
            marketing_granted=marketing_granted,
        )
        return RegistrationReceipt(
            challenge_id=identity_receipt.challenge_id,
            channel=identity_receipt.channel,
            expires_at_epoch=int(identity_receipt.expires_at_epoch),
            marketing_consent=marketing_granted,
        )

    def verify_registration(self, payload: Mapping[str, Any]) -> Any:
        if (
            not isinstance(payload, Mapping)
            or set(payload) != self.VERIFY_ALLOWED_FIELDS
        ):
            raise InvalidRegistrationRequest(
                "verification payload may contain only challenge_id and code"
            )
        challenge_id = payload.get("challenge_id")
        code = payload.get("code")
        if not isinstance(challenge_id, str) or not isinstance(code, str):
            raise InvalidRegistrationRequest("challenge_id and code must be strings")
        row = self.identity_service.auth_store.challenge(challenge_id)
        if row is None:
            raise MissingConsentEvidence("challenge has no registration consent evidence")
        user_ref = str(row["user_identity_ref"])
        if not self.consent_store.personal_data_granted_for_challenge(
            user_identity_ref=user_ref,
            registration_challenge_id=challenge_id,
        ):
            raise MissingConsentEvidence(
                "this challenge lacks its own personal-data consent evidence"
            )
        return self.identity_service.verify(
            {"challenge_id": challenge_id, "code": code}
        )

    def revoke_marketing(
        self,
        *,
        session_token: str,
        document_version: str,
        text_version: str,
        client_request_id: str,
    ) -> Mapping[str, Any]:
        host_identity = self.identity_service.resolve_session(session_token)
        identity_refs = getattr(host_identity, "identity_refs", None)
        if not isinstance(identity_refs, Mapping):
            raise InvalidRegistrationRequest(
                "authenticated session lacks identity refs"
            )
        user_ref = identity_refs.get("user_identity_ref")
        if not isinstance(user_ref, str) or not user_ref.startswith("user:"):
            raise InvalidRegistrationRequest(
                "authenticated session lacks user identity ref"
            )
        return self.consent_store.append_event(
            user_identity_ref=user_ref,
            consent_type=CONSENT_MARKETING,
            action=ACTION_REVOKE,
            document_version=document_version,
            text_version=text_version,
            client_request_id=client_request_id,
        )

    def marketing_allowed_for_session(self, session_token: str) -> bool:
        host_identity = self.identity_service.resolve_session(session_token)
        identity_refs = getattr(host_identity, "identity_refs", None)
        if not isinstance(identity_refs, Mapping):
            return False
        user_ref = identity_refs.get("user_identity_ref")
        if not isinstance(user_ref, str):
            return False
        return self.consent_store.marketing_allowed(
            user_identity_ref=user_ref
        )
