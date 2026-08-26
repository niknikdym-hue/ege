#!/usr/bin/env python3
"""Provider-neutral passwordless identity/session reference for Eksamio Pro.

This module deliberately owns authentication/session state, not PEIS academic
truth. It reuses the already merged trusted-host + PEIS identity-link boundary:

transient contact -> one-time challenge -> opaque ``user:`` ref -> existing
anonymous learner profile (when eligible) -> server-only session -> HostIdentity.

Raw e-mail/phone values and raw session tokens are never persisted. Production
message delivery is intentionally outside this reference; a provider adapter is
injected at runtime.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from peis_persistence import IntegrityConflict
from peis_service_bridge import HostIdentity, MissingHostIdentity
from peis_trusted_host import TrustedHostIdentityResolver


class IdentityError(ValueError):
    """Base class for bounded passwordless identity failures."""


class InvalidIdentityRequest(IdentityError):
    pass


class InvalidChallenge(IdentityError):
    pass


class ChallengeExpired(IdentityError):
    pass


class ChallengeReplay(IdentityError):
    pass


class InvalidVerificationCode(IdentityError):
    pass


class InvalidSession(IdentityError):
    pass


class AnonymousHistoryConflict(IdentityError):
    """Returning account has anonymous evidence that cannot be silently merged."""


class DeliveryProvider(Protocol):
    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        """Deliver a one-time code and return an opaque provider/delivery ref."""


@dataclass(frozen=True)
class ChallengeReceipt:
    challenge_id: str
    channel: str
    expires_at_epoch: int
    delivery_ref: str


@dataclass(frozen=True)
class AuthenticatedSession:
    host_identity: HostIdentity
    token: str
    set_cookie: str
    user_identity_ref: str
    expires_at_epoch: int
    anonymous_link_status: str


class IdentityAuthStore:
    """Small mutable auth-state store over the existing DB connection contract."""

    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self._create_schema()

    def _create_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS passwordless_challenges (
                challenge_id TEXT PRIMARY KEY,
                user_identity_ref TEXT NOT NULL,
                channel TEXT NOT NULL,
                verification_hash TEXT NOT NULL,
                anonymous_identity_ref TEXT,
                created_at_epoch BIGINT NOT NULL,
                expires_at_epoch BIGINT NOT NULL,
                consumed_at_epoch BIGINT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS identity_sessions (
                session_hash TEXT PRIMARY KEY,
                user_identity_ref TEXT NOT NULL,
                learner_profile_id TEXT NOT NULL,
                created_at_epoch BIGINT NOT NULL,
                expires_at_epoch BIGINT NOT NULL,
                revoked_at_epoch BIGINT
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_identity_sessions_user ON identity_sessions(user_identity_ref)",
            "CREATE INDEX IF NOT EXISTS idx_identity_sessions_learner ON identity_sessions(learner_profile_id)",
        ]
        with self.connection:
            for statement in statements:
                self.connection.execute(statement)

    def create_challenge(
        self,
        *,
        challenge_id: str,
        user_identity_ref: str,
        channel: str,
        verification_hash: str,
        anonymous_identity_ref: str | None,
        created_at_epoch: int,
        expires_at_epoch: int,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO passwordless_challenges(
                    challenge_id, user_identity_ref, channel, verification_hash,
                    anonymous_identity_ref, created_at_epoch, expires_at_epoch, consumed_at_epoch
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    challenge_id,
                    user_identity_ref,
                    channel,
                    verification_hash,
                    anonymous_identity_ref,
                    created_at_epoch,
                    expires_at_epoch,
                ),
            )

    def challenge(self, challenge_id: str) -> Mapping[str, Any] | None:
        return self.connection.execute(
            "SELECT * FROM passwordless_challenges WHERE challenge_id = ?",
            (challenge_id,),
        ).fetchone()

    def consume_challenge(self, challenge_id: str, consumed_at_epoch: int) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE passwordless_challenges
                SET consumed_at_epoch = ?
                WHERE challenge_id = ? AND consumed_at_epoch IS NULL
                """,
                (consumed_at_epoch, challenge_id),
            )
        return cursor.rowcount == 1

    def create_session(
        self,
        *,
        session_hash: str,
        user_identity_ref: str,
        learner_profile_id: str,
        created_at_epoch: int,
        expires_at_epoch: int,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO identity_sessions(
                    session_hash, user_identity_ref, learner_profile_id,
                    created_at_epoch, expires_at_epoch, revoked_at_epoch
                ) VALUES (?, ?, ?, ?, ?, NULL)
                """,
                (session_hash, user_identity_ref, learner_profile_id, created_at_epoch, expires_at_epoch),
            )

    def session(self, session_hash: str) -> Mapping[str, Any] | None:
        return self.connection.execute(
            "SELECT * FROM identity_sessions WHERE session_hash = ?",
            (session_hash,),
        ).fetchone()

    def revoke_session(self, session_hash: str, revoked_at_epoch: int) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE identity_sessions
                SET revoked_at_epoch = ?
                WHERE session_hash = ? AND revoked_at_epoch IS NULL
                """,
                (revoked_at_epoch, session_hash),
            )
        return cursor.rowcount == 1


class PasswordlessIdentityService:
    """One bounded verified-contact -> server-owned learner identity path."""

    SESSION_COOKIE_NAME = "eksamio_pro_session"
    BEGIN_ALLOWED_FIELDS = {"channel", "contact"}
    VERIFY_ALLOWED_FIELDS = {"challenge_id", "code"}

    def __init__(
        self,
        *,
        peis_store: Any,
        trusted_host_resolver: TrustedHostIdentityResolver,
        auth_store: IdentityAuthStore,
        delivery_provider: DeliveryProvider,
        contact_hmac_key: bytes,
        verification_hmac_key: bytes,
        now_provider: Callable[[], int] | None = None,
        challenge_ttl_seconds: int = 10 * 60,
        session_ttl_seconds: int = 30 * 24 * 60 * 60,
        challenge_id_factory: Callable[[], str] | None = None,
        code_factory: Callable[[], str] | None = None,
        session_token_factory: Callable[[], str] | None = None,
        learner_profile_factory: Callable[[], str] | None = None,
    ) -> None:
        for name, key in {
            "contact_hmac_key": contact_hmac_key,
            "verification_hmac_key": verification_hmac_key,
        }.items():
            if not isinstance(key, bytes) or len(key) < 32:
                raise ValueError(f"{name} must be runtime bytes of at least 32 bytes")
        if not 60 <= challenge_ttl_seconds <= 3600:
            raise ValueError("challenge_ttl_seconds must be between 60 and 3600")
        if session_ttl_seconds < 300:
            raise ValueError("session_ttl_seconds must be at least 300")
        self.peis_store = peis_store
        self.trusted_host_resolver = trusted_host_resolver
        self.auth_store = auth_store
        self.delivery_provider = delivery_provider
        self.contact_hmac_key = contact_hmac_key
        self.verification_hmac_key = verification_hmac_key
        self.now_provider = now_provider or (lambda: int(time.time()))
        self.challenge_ttl_seconds = int(challenge_ttl_seconds)
        self.session_ttl_seconds = int(session_ttl_seconds)
        self.challenge_id_factory = challenge_id_factory or (lambda: "ch:" + secrets.token_urlsafe(18))
        self.code_factory = code_factory or (lambda: f"{secrets.randbelow(1_000_000):06d}")
        self.session_token_factory = session_token_factory or (lambda: "sid." + secrets.token_urlsafe(32))
        self.learner_profile_factory = learner_profile_factory or (lambda: "learner:" + secrets.token_urlsafe(18))

    @staticmethod
    def _normalize_contact(channel: str, contact: str) -> str:
        if channel == "email":
            normalized = contact.strip().casefold()
            if len(normalized) > 254 or normalized.count("@") != 1:
                raise InvalidIdentityRequest("invalid e-mail contact")
            local, domain = normalized.split("@", 1)
            if not local or not domain or "." not in domain:
                raise InvalidIdentityRequest("invalid e-mail contact")
            return normalized
        if channel == "phone":
            raw = re.sub(r"[\s()\-]", "", contact)
            if raw.startswith("8") and len(raw) == 11:
                raw = "+7" + raw[1:]
            if not re.fullmatch(r"\+[1-9][0-9]{7,14}", raw):
                raise InvalidIdentityRequest("invalid phone contact")
            return raw
        raise InvalidIdentityRequest("channel must be email or phone")

    def _user_identity_ref(self, channel: str, normalized_contact: str) -> str:
        digest = hmac.new(
            self.contact_hmac_key,
            f"eksamio-user-v1|{channel}|{normalized_contact}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return "user:" + digest[:48]

    def _verification_hash(self, challenge_id: str, code: str) -> str:
        return hmac.new(
            self.verification_hmac_key,
            f"eksamio-challenge-v1|{challenge_id}|{code}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _session_hash(token: str) -> str:
        if not isinstance(token, str) or not token.startswith("sid.") or len(token) < 30:
            raise InvalidSession("invalid session token")
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def begin(self, payload: Mapping[str, Any], *, anonymous_host_token: str | None = None) -> ChallengeReceipt:
        if not isinstance(payload, Mapping) or set(payload) != self.BEGIN_ALLOWED_FIELDS:
            raise InvalidIdentityRequest("browser challenge payload may contain only channel and contact")
        channel = payload.get("channel")
        contact = payload.get("contact")
        if not isinstance(channel, str) or not isinstance(contact, str):
            raise InvalidIdentityRequest("channel and contact must be strings")
        normalized = self._normalize_contact(channel, contact)
        user_identity_ref = self._user_identity_ref(channel, normalized)

        anonymous_identity_ref: str | None = None
        if anonymous_host_token is not None:
            host_identity = self.trusted_host_resolver.resolve(anonymous_host_token)
            anonymous_identity_ref = host_identity.identity_refs.get("anonymous_identity_ref")
            if not anonymous_identity_ref:
                raise MissingHostIdentity("verified anonymous host token lacks anonymous identity ref")

        now = int(self.now_provider())
        challenge_id = self.challenge_id_factory()
        if not isinstance(challenge_id, str) or len(challenge_id) < 12:
            raise IdentityError("challenge id factory produced an invalid id")
        code = self.code_factory()
        if not isinstance(code, str) or not re.fullmatch(r"[0-9]{6}", code):
            raise IdentityError("verification code factory must produce six digits")
        expires = now + self.challenge_ttl_seconds
        self.auth_store.create_challenge(
            challenge_id=challenge_id,
            user_identity_ref=user_identity_ref,
            channel=channel,
            verification_hash=self._verification_hash(challenge_id, code),
            anonymous_identity_ref=anonymous_identity_ref,
            created_at_epoch=now,
            expires_at_epoch=expires,
        )
        delivery_ref = self.delivery_provider.deliver(
            channel=channel,
            contact=normalized,
            code=code,
            challenge_id=challenge_id,
        )
        if not isinstance(delivery_ref, str) or not delivery_ref:
            raise IdentityError("delivery provider must return an opaque delivery ref")
        return ChallengeReceipt(
            challenge_id=challenge_id,
            channel=channel,
            expires_at_epoch=expires,
            delivery_ref=delivery_ref,
        )

    def _verified_challenge(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if not isinstance(payload, Mapping) or set(payload) != self.VERIFY_ALLOWED_FIELDS:
            raise InvalidIdentityRequest("browser verification payload may contain only challenge_id and code")
        challenge_id = payload.get("challenge_id")
        code = payload.get("code")
        if not isinstance(challenge_id, str) or not isinstance(code, str):
            raise InvalidIdentityRequest("challenge_id and code must be strings")
        row = self.auth_store.challenge(challenge_id)
        if row is None:
            raise InvalidChallenge("unknown challenge")
        if row["consumed_at_epoch"] is not None:
            raise ChallengeReplay("challenge was already consumed")
        now = int(self.now_provider())
        if now >= int(row["expires_at_epoch"]):
            raise ChallengeExpired("challenge expired")
        supplied = self._verification_hash(challenge_id, code)
        if not hmac.compare_digest(str(row["verification_hash"]), supplied):
            raise InvalidVerificationCode("verification code mismatch")
        return row

    def verify(self, payload: Mapping[str, Any]) -> AuthenticatedSession:
        row = self._verified_challenge(payload)
        now = int(self.now_provider())
        challenge_id = str(row["challenge_id"])
        if not self.auth_store.consume_challenge(challenge_id, now):
            raise ChallengeReplay("challenge was consumed concurrently")

        user_identity_ref = str(row["user_identity_ref"])
        anonymous_ref = row["anonymous_identity_ref"]
        existing_profile = self.peis_store.resolve_identity(user_identity_ref)
        anonymous_profile = self.peis_store.resolve_identity(anonymous_ref) if anonymous_ref else None
        link_status = "NO_ANONYMOUS_CONTEXT"

        if existing_profile is None:
            if anonymous_profile is not None:
                learner_profile_id = anonymous_profile
                link_result = self.peis_store.link_identity(
                    user_identity_ref,
                    learner_profile_id,
                    identity_kind="USER",
                )
                link_status = "ANONYMOUS_PROFILE_LINKED_TO_USER" if link_result["status"] == "LINKED" else "ALREADY_LINKED"
            else:
                learner_profile_id = self.learner_profile_factory()
                if not isinstance(learner_profile_id, str) or len(learner_profile_id) < 12 or "@" in learner_profile_id:
                    raise IdentityError("learner profile factory produced an invalid opaque id")
                self.peis_store.link_identity(user_identity_ref, learner_profile_id, identity_kind="USER")
                link_status = "NEW_USER_PROFILE_CREATED"
        else:
            learner_profile_id = existing_profile
            if anonymous_profile is not None:
                if anonymous_profile == learner_profile_id:
                    link_status = "ANONYMOUS_ALREADY_SAME_PROFILE"
                elif self.peis_store.event_count(learner_profile_id=anonymous_profile) > 0:
                    raise AnonymousHistoryConflict(
                        "returning account has separate anonymous evidence; silent profile merge is forbidden"
                    )
                else:
                    link_status = "EMPTY_ANONYMOUS_PROFILE_NOT_MERGED"
            else:
                link_status = "EXISTING_USER_RESOLVED"

        return self._issue_session(
            user_identity_ref=user_identity_ref,
            learner_profile_id=learner_profile_id,
            anonymous_link_status=link_status,
        )

    def _issue_session(
        self,
        *,
        user_identity_ref: str,
        learner_profile_id: str,
        anonymous_link_status: str,
    ) -> AuthenticatedSession:
        now = int(self.now_provider())
        token = self.session_token_factory()
        token_hash = self._session_hash(token)
        expires = now + self.session_ttl_seconds
        self.auth_store.create_session(
            session_hash=token_hash,
            user_identity_ref=user_identity_ref,
            learner_profile_id=learner_profile_id,
            created_at_epoch=now,
            expires_at_epoch=expires,
        )
        host_identity = HostIdentity(
            learner_profile_id=learner_profile_id,
            identity_refs={"user_identity_ref": user_identity_ref},
        )
        host_identity.validate()
        return AuthenticatedSession(
            host_identity=host_identity,
            token=token,
            set_cookie=self.serialize_session_cookie(token),
            user_identity_ref=user_identity_ref,
            expires_at_epoch=expires,
            anonymous_link_status=anonymous_link_status,
        )

    def serialize_session_cookie(self, token: str) -> str:
        self._session_hash(token)
        return (
            f"{self.SESSION_COOKIE_NAME}={token}; Path=/; Max-Age={self.session_ttl_seconds}; "
            "HttpOnly; Secure; SameSite=Lax"
        )

    def resolve_session(self, token: str) -> HostIdentity:
        session_hash = self._session_hash(token)
        row = self.auth_store.session(session_hash)
        if row is None or row["revoked_at_epoch"] is not None:
            raise InvalidSession("session is unknown or revoked")
        now = int(self.now_provider())
        if now >= int(row["expires_at_epoch"]):
            raise InvalidSession("session expired")
        user_identity_ref = str(row["user_identity_ref"])
        learner_profile_id = str(row["learner_profile_id"])
        canonical = self.peis_store.resolve_identity(user_identity_ref)
        if canonical is None or canonical != learner_profile_id:
            raise InvalidSession("session identity no longer matches canonical server identity")
        host_identity = HostIdentity(
            learner_profile_id=learner_profile_id,
            identity_refs={"user_identity_ref": user_identity_ref},
        )
        host_identity.validate()
        return host_identity

    def rotate_session(self, token: str) -> AuthenticatedSession:
        host_identity = self.resolve_session(token)
        session_hash = self._session_hash(token)
        now = int(self.now_provider())
        if not self.auth_store.revoke_session(session_hash, now):
            raise InvalidSession("session was revoked concurrently")
        return self._issue_session(
            user_identity_ref=host_identity.identity_refs["user_identity_ref"],
            learner_profile_id=host_identity.learner_profile_id,
            anonymous_link_status="SESSION_ROTATED",
        )

    def logout(self, token: str) -> str:
        session_hash = self._session_hash(token)
        row = self.auth_store.session(session_hash)
        if row is None:
            return "ALREADY_LOGGED_OUT"
        self.auth_store.revoke_session(session_hash, int(self.now_provider()))
        return "LOGGED_OUT"

    @classmethod
    def clear_session_cookie(cls) -> str:
        return f"{cls.SESSION_COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Lax"


class NonProductionCaptureDeliveryProvider:
    """CI/staging-only provider that is structurally incapable of real delivery."""

    def __init__(self) -> None:
        self.deliveries: dict[str, dict[str, str]] = {}

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        if channel == "email":
            if not contact.endswith(".invalid"):
                raise IdentityError("non-production provider refuses non-.invalid e-mail destinations")
        elif channel == "phone":
            if contact != "+70000000000":
                raise IdentityError("non-production provider refuses non-fixture phone destinations")
        else:
            raise IdentityError("unsupported delivery channel")
        self.deliveries[challenge_id] = {"channel": channel, "contact": contact, "code": code}
        return "nonprod-delivery:" + hashlib.sha256(challenge_id.encode("utf-8")).hexdigest()[:20]

    def code_for(self, challenge_id: str) -> str:
        return self.deliveries[challenge_id]["code"]


__all__ = [
    "AnonymousHistoryConflict",
    "AuthenticatedSession",
    "ChallengeExpired",
    "ChallengeReceipt",
    "ChallengeReplay",
    "IdentityAuthStore",
    "IdentityError",
    "InvalidChallenge",
    "InvalidIdentityRequest",
    "InvalidSession",
    "InvalidVerificationCode",
    "NonProductionCaptureDeliveryProvider",
    "PasswordlessIdentityService",
]
