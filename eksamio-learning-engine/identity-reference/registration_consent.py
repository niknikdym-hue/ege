#!/usr/bin/env python3
"""Registration-consent boundary for the authenticated Eksamio learner path.

The public product path is deliberately narrower than the historical identity
reference: registration is e-mail only, requires a separate personal-data
consent, never supplies anonymous learner context, and stores consent evidence
server-side against an opaque user identity reference.

This module does not send marketing messages and does not own final legal copy.
Document/text version identifiers are supplied by the host application so the
record can prove exactly which consent text the learner saw.
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
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,191}$")


@dataclass(frozen=True)
class RegistrationReceipt:
    challenge_id: str
    channel: str
    expires_at_epoch: int
    delivery_ref: str
    marketing_consent: bool


class RegistrationConsentStore:
    """Append-only server-owned consent evidence without raw contact PII."""

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
        statements = [
            """
            CREATE TABLE IF NOT EXISTS registration_consent_events (
                event_id TEXT PRIMARY KEY,
                user_identity_ref TEXT NOT NULL,
                consent_type TEXT NOT NULL,
                action TEXT NOT NULL,
                captured_at_epoch BIGINT NOT NULL,
                document_version TEXT NOT NULL,
                text_version TEXT NOT NULL,
                client_request_id TEXT NOT NULL
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
                user_identity_ref, consent_type, captured_at_epoch, event_id
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
        if (
            not isinstance(user_identity_ref, str)
            or not user_identity_ref.startswith("user:")
            or "@" in user_identity_ref
        ):
            raise InvalidRegistrationRequest("opaque user identity ref required")
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
                str(existing["action"]) == action
                and str(existing["document_version"]) == document_version
                and str(existing["text_version"]) == text_version
            ):
                return {"status": "ALREADY_RECORDED", "event_id": existing["event_id"]}
            raise ConsentReplayConflict(
                "consent retry changed action or legal-text version"
            )

        event_id = self.event_id_factory()
        if not isinstance(event_id, str) or len(event_id) < 12:
            raise InvalidRegistrationRequest("consent event id factory failed")
        captured_at_epoch = int(self.now_provider())
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO registration_consent_events(
                    event_id, user_identity_ref, consent_type, action,
                    captured_at_epoch, document_version, text_version,
                    client_request_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
            ORDER BY captured_at_epoch DESC, event_id DESC
            LIMIT 1
            """,
            (user_identity_ref, consent_type),
        ).fetchone()

    def personal_data_granted(self, *, user_identity_ref: str) -> bool:
        row = self.latest_state(
            user_identity_ref=user_identity_ref,
            consent_type=CONSENT_PERSONAL_DATA,
        )
        return row is not None and str(row["action"]) == ACTION_GRANT

    def marketing_allowed(self, *, user_identity_ref: str) -> bool:
        row = self.latest_state(
            user_identity_ref=user_identity_ref,
            consent_type=CONSENT_MARKETING,
        )
        return row is not None and str(row["action"]) == ACTION_GRANT


class RegistrationService:
    """E-mail registration facade over the existing passwordless identity service."""

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
        # The existing identity service intentionally owns normalization/HMAC.
        # Reuse it so consent evidence and the resulting account cannot diverge.
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
        if not isinstance(payload, Mapping) or set(payload) != RegistrationService.BEGIN_ALLOWED_FIELDS:
            raise InvalidRegistrationRequest(
                "registration payload must contain only the bounded registration fields"
            )
        if not isinstance(payload.get("email"), str):
            raise InvalidRegistrationRequest("email must be a string")
        if payload.get("personal_data_consent") is not True:
            raise PersonalDataConsentRequired(
                "personal-data consent is required for registration"
            )
        if not isinstance(payload.get("marketing_consent"), bool):
            raise InvalidRegistrationRequest("marketing_consent must be boolean")

    def begin_registration(self, payload: Mapping[str, Any]) -> RegistrationReceipt:
        self._validate_begin_payload(payload)
        email = str(payload["email"])
        user_ref = self._registration_user_identity_ref(email)
        client_request_id = RegistrationConsentStore._validate_client_request_id(
            payload["client_request_id"]
        )

        self.consent_store.append_event(
            user_identity_ref=user_ref,
            consent_type=CONSENT_PERSONAL_DATA,
            action=ACTION_GRANT,
            document_version=payload["personal_data_document_version"],
            text_version=payload["personal_data_text_version"],
            client_request_id=client_request_id + ":pd",
        )
        marketing_granted = bool(payload["marketing_consent"])
        self.consent_store.append_event(
            user_identity_ref=user_ref,
            consent_type=CONSENT_MARKETING,
            action=ACTION_GRANT if marketing_granted else ACTION_DECLINE,
            document_version=payload["marketing_document_version"],
            text_version=payload["marketing_text_version"],
            client_request_id=client_request_id + ":marketing",
        )

        # Owner decision: no guest learner and no anon->account continuity.
        receipt = self.identity_service.begin(
            {"channel": "email", "contact": email},
            anonymous_host_token=None,
        )
        return RegistrationReceipt(
            challenge_id=receipt.challenge_id,
            channel=receipt.channel,
            expires_at_epoch=int(receipt.expires_at_epoch),
            delivery_ref=receipt.delivery_ref,
            marketing_consent=marketing_granted,
        )

    def verify_registration(self, payload: Mapping[str, Any]) -> Any:
        if not isinstance(payload, Mapping) or set(payload) != self.VERIFY_ALLOWED_FIELDS:
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
        if not self.consent_store.personal_data_granted(
            user_identity_ref=user_ref
        ):
            raise MissingConsentEvidence(
                "personal-data consent evidence is required before account verification"
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
