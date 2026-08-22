#!/usr/bin/env python3
"""Reference trusted-host identity boundary for Eksamio PEIS.

This module is intentionally NOT a production account/authentication system.
It proves only the server-side identity handoff required by the already merged
browser hook and PEIS service bridge:

signed opaque host token -> shared persistence identity link -> HostIdentity.

No learner profile id is placed in the browser-facing token. The signing secret
must be supplied by the server runtime and is never defined in this module.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from peis_persistence import IntegrityConflict, PeisPersistenceStore
from peis_service_bridge import HostIdentity, MissingHostIdentity


class TrustedHostError(ValueError):
    """Base class for rejected trusted-host identity input."""


class InvalidHostToken(TrustedHostError):
    """Host token is absent, malformed, untrusted, expired, or otherwise invalid."""


class UntrustedBrowserIdentity(TrustedHostError):
    """Browser tried to assert identity fields owned by the trusted host."""


@dataclass(frozen=True)
class IssuedHostIdentity:
    host_identity: HostIdentity
    token: str
    set_cookie: str
    identity_ref: str


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise InvalidHostToken("empty base64url component")
    try:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)
    except Exception as exc:  # noqa: BLE001 - normalize malformed token errors
        raise InvalidHostToken("invalid base64url component") from exc


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _opaque_ref(prefix: str, token_bytes: int = 18) -> str:
    return prefix + secrets.token_urlsafe(token_bytes)


class TrustedHostIdentityResolver:
    """Issue/verify opaque host identity and resolve it through shared persistence."""

    COOKIE_NAME = "eksamio_peis_host"
    TOKEN_VERSION = 1
    ALLOWED_CLAIMS = {"v", "kid", "identity_ref", "iat", "exp"}
    BROWSER_FORBIDDEN_IDENTITY_FIELDS = {
        "learner_profile_id",
        "identity_refs",
        "anonymous_identity_ref",
        "user_identity_ref",
        "email",
    }

    def __init__(
        self,
        *,
        store: PeisPersistenceStore,
        signing_keys: Mapping[str, bytes],
        active_key_id: str,
        now_provider: Callable[[], int] | None = None,
        ttl_seconds: int = 30 * 24 * 60 * 60,
        future_iat_skew_seconds: int = 30,
        anonymous_ref_factory: Callable[[], str] | None = None,
        learner_profile_factory: Callable[[], str] | None = None,
    ) -> None:
        if not signing_keys or active_key_id not in signing_keys:
            raise ValueError("active signing key must be supplied by server runtime")
        normalized: dict[str, bytes] = {}
        for key_id, secret in signing_keys.items():
            if not isinstance(key_id, str) or not key_id:
                raise ValueError("signing key id must be non-empty")
            if not isinstance(secret, bytes) or len(secret) < 32:
                raise ValueError("signing secret must be runtime bytes of at least 32 bytes")
            normalized[key_id] = secret
        if ttl_seconds < 60:
            raise ValueError("ttl_seconds must be at least 60")
        if not 0 <= future_iat_skew_seconds <= 300:
            raise ValueError("future_iat_skew_seconds must be between 0 and 300")
        self.store = store
        self.signing_keys = normalized
        self.active_key_id = active_key_id
        self.now_provider = now_provider or (lambda: int(time.time()))
        self.ttl_seconds = int(ttl_seconds)
        self.future_iat_skew_seconds = int(future_iat_skew_seconds)
        self.anonymous_ref_factory = anonymous_ref_factory or (lambda: _opaque_ref("anon:"))
        self.learner_profile_factory = learner_profile_factory or (lambda: _opaque_ref("learner:"))

    @staticmethod
    def reject_browser_identity_assertions(payload: Mapping[str, Any]) -> None:
        if not isinstance(payload, Mapping):
            raise UntrustedBrowserIdentity("browser payload must be a mapping")
        asserted = sorted(TrustedHostIdentityResolver.BROWSER_FORBIDDEN_IDENTITY_FIELDS.intersection(payload))
        if asserted:
            raise UntrustedBrowserIdentity(
                "browser cannot assert trusted identity fields: " + ", ".join(asserted)
            )

    @staticmethod
    def _validate_identity_ref(identity_ref: str, *, expected_prefix: str | None = None) -> None:
        if not isinstance(identity_ref, str) or len(identity_ref) < 12:
            raise TrustedHostError("identity_ref must be opaque and non-empty")
        if "@" in identity_ref:
            raise TrustedHostError("email is forbidden as academic-history identity ref")
        if expected_prefix and not identity_ref.startswith(expected_prefix):
            raise TrustedHostError(f"identity_ref must start with {expected_prefix}")

    def _sign_claims(self, claims: Mapping[str, Any]) -> str:
        body = _b64url_encode(_canonical_json(claims))
        secret = self.signing_keys[self.active_key_id]
        signature = hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest()
        return body + "." + _b64url_encode(signature)

    def _claims_for(self, identity_ref: str, *, issued_at: int | None = None) -> dict[str, Any]:
        self._validate_identity_ref(identity_ref, expected_prefix="anon:")
        now = int(self.now_provider() if issued_at is None else issued_at)
        return {
            "v": self.TOKEN_VERSION,
            "kid": self.active_key_id,
            "identity_ref": identity_ref,
            "iat": now,
            "exp": now + self.ttl_seconds,
        }

    def issue_token(self, identity_ref: str, *, issued_at: int | None = None) -> str:
        return self._sign_claims(self._claims_for(identity_ref, issued_at=issued_at))

    def serialize_cookie(self, token: str) -> str:
        if not isinstance(token, str) or not token:
            raise ValueError("token is required")
        return (
            f"{self.COOKIE_NAME}={token}; Path=/; Max-Age={self.ttl_seconds}; "
            "HttpOnly; Secure; SameSite=Lax"
        )

    def issue_anonymous(self) -> IssuedHostIdentity:
        identity_ref = self.anonymous_ref_factory()
        learner_profile_id = self.learner_profile_factory()
        self._validate_identity_ref(identity_ref, expected_prefix="anon:")
        if not isinstance(learner_profile_id, str) or len(learner_profile_id) < 12:
            raise TrustedHostError("server-generated learner_profile_id is invalid")
        if "@" in learner_profile_id:
            raise TrustedHostError("learner_profile_id must be opaque, not email")
        self.store.link_identity(
            identity_ref,
            learner_profile_id,
            identity_kind="ANONYMOUS",
        )
        host_identity = HostIdentity(
            learner_profile_id=learner_profile_id,
            identity_refs={"anonymous_identity_ref": identity_ref},
        )
        host_identity.validate()
        token = self.issue_token(identity_ref)
        return IssuedHostIdentity(
            host_identity=host_identity,
            token=token,
            set_cookie=self.serialize_cookie(token),
            identity_ref=identity_ref,
        )

    def parse_and_verify(self, token: str) -> dict[str, Any]:
        if not isinstance(token, str) or not token:
            raise InvalidHostToken("host token is required")
        pieces = token.split(".")
        if len(pieces) != 2:
            raise InvalidHostToken("host token must contain payload and signature")
        body, signature_text = pieces
        try:
            claims_raw = _b64url_decode(body)
            claims = json.loads(claims_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise InvalidHostToken("host token payload is not valid canonical JSON") from exc
        if not isinstance(claims, dict) or set(claims) != self.ALLOWED_CLAIMS:
            raise InvalidHostToken("host token claims do not match the reference contract")
        if claims.get("v") != self.TOKEN_VERSION:
            raise InvalidHostToken("unsupported host token version")
        key_id = claims.get("kid")
        if not isinstance(key_id, str) or key_id not in self.signing_keys:
            raise InvalidHostToken("unknown host token key id")
        secret = self.signing_keys[key_id]
        expected = hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest()
        supplied = _b64url_decode(signature_text)
        if not hmac.compare_digest(expected, supplied):
            raise InvalidHostToken("host token signature mismatch")
        identity_ref = claims.get("identity_ref")
        try:
            self._validate_identity_ref(identity_ref, expected_prefix="anon:")
        except TrustedHostError as exc:
            raise InvalidHostToken(str(exc)) from exc
        iat = claims.get("iat")
        exp = claims.get("exp")
        if not isinstance(iat, int) or isinstance(iat, bool) or not isinstance(exp, int) or isinstance(exp, bool):
            raise InvalidHostToken("host token time claims must be integer epoch seconds")
        if exp <= iat:
            raise InvalidHostToken("host token expiry must be after issue time")
        now = int(self.now_provider())
        if iat > now + self.future_iat_skew_seconds:
            raise InvalidHostToken("host token issue time is too far in the future")
        if now >= exp:
            raise InvalidHostToken("host token is expired")
        return claims

    def resolve(self, token: str) -> HostIdentity:
        claims = self.parse_and_verify(token)
        identity_ref = claims["identity_ref"]
        learner_profile_id = self.store.resolve_identity(identity_ref)
        if learner_profile_id is None:
            raise MissingHostIdentity("verified host identity has no shared persistence link")
        host_identity = HostIdentity(
            learner_profile_id=learner_profile_id,
            identity_refs={"anonymous_identity_ref": identity_ref},
        )
        host_identity.validate()
        return host_identity

    def link_user_identity(self, token: str, user_identity_ref: str) -> HostIdentity:
        host_identity = self.resolve(token)
        self._validate_identity_ref(user_identity_ref, expected_prefix="user:")
        self.store.link_identity(
            user_identity_ref,
            host_identity.learner_profile_id,
            identity_kind="USER",
        )
        linked = HostIdentity(
            learner_profile_id=host_identity.learner_profile_id,
            identity_refs={
                "anonymous_identity_ref": host_identity.identity_refs["anonymous_identity_ref"],
                "user_identity_ref": user_identity_ref,
            },
        )
        linked.validate()
        return linked

    def resolve_user_identity(self, user_identity_ref: str) -> HostIdentity:
        self._validate_identity_ref(user_identity_ref, expected_prefix="user:")
        learner_profile_id = self.store.resolve_identity(user_identity_ref)
        if learner_profile_id is None:
            raise MissingHostIdentity("user identity has no shared persistence link")
        host_identity = HostIdentity(
            learner_profile_id=learner_profile_id,
            identity_refs={"user_identity_ref": user_identity_ref},
        )
        host_identity.validate()
        return host_identity


__all__ = [
    "InvalidHostToken",
    "IssuedHostIdentity",
    "TrustedHostError",
    "TrustedHostIdentityResolver",
    "UntrustedBrowserIdentity",
    "IntegrityConflict",
]
