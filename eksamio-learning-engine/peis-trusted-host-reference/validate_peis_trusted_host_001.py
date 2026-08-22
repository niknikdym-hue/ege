#!/usr/bin/env python3
"""Validate the reference trusted-host identity boundary for Eksamio PEIS."""

from __future__ import annotations

import base64
import copy
import hashlib
import hmac
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "peis-persistence-reference"))
sys.path.insert(0, str(ROOT / "peis-reference-kernel"))
sys.path.insert(0, str(ROOT / "peis-integration-reference"))
sys.path.insert(0, str(ROOT / "peis-service-bridge-reference"))
sys.path.insert(0, str(HERE))

from peis_persistence import IntegrityConflict, PeisPersistenceStore  # noqa: E402
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_service_bridge import AdapterRegistry, PeisServiceBridge  # noqa: E402
from peis_trusted_host import (  # noqa: E402
    InvalidHostToken,
    TrustedHostError,
    TrustedHostIdentityResolver,
    UntrustedBrowserIdentity,
)
from russian_checked_card_adapter import RussianEgeTrainerTask12Adapter  # noqa: E402


NOW = 1_787_240_400
KEY_ID = "test-key-v1"
TEST_SECRET_ENV = "EKSAMIO_PEIS_TRUSTED_HOST_TEST_SECRET"
ANON_REF = "anon:trusted-host-fixture-001"
LEARNER = "learner:trusted-host-fixture-001"
USER_REF = "user:trusted-account-fixture-001"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def resign_claims(claims: dict[str, Any], secret: bytes) -> str:
    body = b64url_encode(json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest()
    return body + "." + b64url_encode(signature)


def expect_invalid(action: Any, message: str) -> None:
    try:
        action()
    except (InvalidHostToken, TrustedHostError, UntrustedBrowserIdentity, IntegrityConflict):
        require(True, message)
    else:
        raise AssertionError(message)


def main() -> int:
    secret_text = os.environ.get(TEST_SECRET_ENV)
    require(isinstance(secret_text, str) and len(secret_text) >= 32, "validator signing secret is injected at runtime rather than committed in source")
    secret = secret_text.encode("utf-8")

    source_text = (HERE / "peis_trusted_host.py").read_text(encoding="utf-8")
    contract = load_json(HERE / "PEIS-TRUSTED-HOST-CONTRACT-v0.1.json")
    audit_text = (HERE / "PEIS-TRUSTED-HOST-REUSE-AUDIT.txt").read_text(encoding="utf-8")
    require("NO_REUSABLE_PROJECT_AUTH_HOST_FOUND" in audit_text, "reuse audit records that no project auth host was found before implementation")
    require(secret_text not in source_text, "runtime signing secret is absent from trusted-host source")
    require("learner_profile_id" not in contract["host_token"]["allowed_claims"], "host token contract forbids learner_profile_id claim")
    require(contract["cookie_projection"]["http_only"] is True and contract["cookie_projection"]["secure"] is True, "cookie projection requires HttpOnly and Secure")
    require(contract["identity"]["scope"] == "CROSS_SUBJECT", "identity contract is cross-subject rather than Russian-specific")

    evidence_schema = load_json(ROOT / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json")
    nba_schema = load_json(ROOT / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json")

    with tempfile.TemporaryDirectory(prefix="peis-trusted-host-001-") as temp_dir:
        db_path = Path(temp_dir) / "trusted-host.sqlite"
        with PeisPersistenceStore(db_path, evidence_schema=evidence_schema, nba_schema=nba_schema) as store:
            resolver = TrustedHostIdentityResolver(
                store=store,
                signing_keys={KEY_ID: secret},
                active_key_id=KEY_ID,
                now_provider=lambda: NOW,
                ttl_seconds=3600,
                anonymous_ref_factory=lambda: ANON_REF,
                learner_profile_factory=lambda: LEARNER,
            )

            # Browser identity assertions are rejected before trusted-host resolution.
            for field, value in {
                "learner_profile_id": "browser-choice",
                "identity_refs": {"anonymous_identity_ref": "anon:browser-choice"},
                "anonymous_identity_ref": "anon:browser-choice",
                "user_identity_ref": "user:browser-choice",
                "email": "student@example.com",
            }.items():
                expect_invalid(
                    lambda field=field, value=value: resolver.reject_browser_identity_assertions({field: value}),
                    f"browser-supplied identity field {field} is rejected",
                )

            issued = resolver.issue_anonymous()
            require(issued.identity_ref == ANON_REF, "anonymous identity ref is generated by the trusted host fixture")
            require(issued.host_identity.learner_profile_id == LEARNER, "learner_profile_id is generated/resolved by the trusted host fixture")
            require(store.resolve_identity(ANON_REF) == LEARNER, "anonymous identity is linked through shared persistence")
            issued.host_identity.validate()
            require(True, "issued identity satisfies the existing PEIS service HostIdentity contract")

            token_claims = resolver.parse_and_verify(issued.token)
            require(set(token_claims) == {"v", "kid", "identity_ref", "iat", "exp"}, "signed host token contains only allowlisted claims")
            require("learner_profile_id" not in token_claims, "browser-facing token contains no learner_profile_id")
            require("@" not in json.dumps(token_claims), "browser-facing token contains no email")
            require(token_claims["identity_ref"] == ANON_REF, "signed host token contains only the opaque anonymous identity ref")

            cookie = issued.set_cookie
            for fragment in ("HttpOnly", "Secure", "SameSite=Lax", "Path=/", "Max-Age=3600"):
                require(fragment in cookie, f"cookie projection contains {fragment}")
            require(LEARNER not in cookie, "cookie does not expose learner_profile_id")
            require("student@example.com" not in cookie, "cookie does not expose email")

            resolved1 = resolver.resolve(issued.token)
            resolved2 = resolver.resolve(issued.token)
            require(resolved1 == resolved2, "repeated verified token resolution is stable")
            require(resolved1.learner_profile_id == LEARNER, "verified token resolves to the original learner through shared persistence")

            # Record current-product-shaped Russian evidence before account linking.
            adapter = RussianEgeTrainerTask12Adapter(ROOT)
            registry = AdapterRegistry()
            registry.register(adapter)
            bridge = PeisServiceBridge(
                store=store,
                registry=registry,
                kernel_snapshot=kernel_snapshot,
                now_provider=lambda: "2026-08-20T18:00:00+03:00",
            )
            product_payload = {
                "card_id": "ege-ru-12-2026-12-01",
                "session_started_at_ms": 1787241600000,
                "session_mode": "practice",
                "answer": ["2", "5"],
                "occurred_at_client": "2026-08-20T17:59:59+03:00",
                "client_request_id": "trusted-host-evidence-fixture-001",
            }
            service_result = bridge.submit_checked_card(
                adapter_id=adapter.adapter_id,
                payload=product_payload,
                host_identity=resolved1,
            )
            require(service_result["status"] == "ACCEPTED", "trusted HostIdentity drives the existing PEIS service bridge")
            event_id = service_result["event_receipt"]["event_id"]
            event_before_link = copy.deepcopy(store.raw_event(event_id))
            require(event_before_link is not None and event_before_link["learner_profile_id"] == LEARNER, "evidence is persisted on the anonymous learner profile before account linking")
            require(store.event_count(learner_profile_id=LEARNER, subject_id="russian") == 1, "one Russian evidence event exists before account linking")

            linked = resolver.link_user_identity(issued.token, USER_REF)
            require(linked.learner_profile_id == LEARNER, "user identity links to the same learner_profile_id")
            require(linked.identity_refs["anonymous_identity_ref"] == ANON_REF and linked.identity_refs["user_identity_ref"] == USER_REF, "linked HostIdentity preserves anonymous and user refs")
            require(store.resolve_identity(ANON_REF) == LEARNER and store.resolve_identity(USER_REF) == LEARNER, "anonymous and user identity refs resolve to the same learner")
            require(resolver.resolve_user_identity(USER_REF).learner_profile_id == LEARNER, "trusted user identity independently resolves to the same learner")
            require(store.raw_event(event_id) == event_before_link, "account identity linking does not rewrite existing EvidenceEvent")
            require(store.event_count(learner_profile_id=LEARNER, subject_id="russian") == 1, "account linking does not duplicate or migrate existing evidence")

            cross_subject_context = {
                "russian": linked.learner_profile_id,
                "mathematics": resolver.resolve_user_identity(USER_REF).learner_profile_id,
            }
            require(len(set(cross_subject_context.values())) == 1, "the same learner_profile_id is usable across Russian and Mathematics contexts")

            # Stable identity collision protection must prevent reassignment.
            store.link_identity("anon:trusted-host-fixture-002", "learner:trusted-host-fixture-002", identity_kind="ANONYMOUS")
            expect_invalid(
                lambda: store.link_identity(USER_REF, "learner:trusted-host-fixture-002", identity_kind="USER"),
                "shared persistence rejects reassignment of an identity_ref to another learner",
            )
            require(store.resolve_identity(USER_REF) == LEARNER, "failed reassignment leaves the original user identity link intact")

            # Email cannot become an identity ref.
            expect_invalid(
                lambda: resolver.link_user_identity(issued.token, "user:student@example.com"),
                "email-like user identity ref is rejected",
            )

            # Token negative gates.
            expect_invalid(lambda: resolver.resolve(""), "missing token is rejected")
            expect_invalid(lambda: resolver.resolve("not-a-token"), "malformed token is rejected")

            body, signature = issued.token.split(".")
            claims = json.loads(b64url_decode(body).decode("utf-8"))

            tampered_claims = dict(claims)
            tampered_claims["identity_ref"] = "anon:tampered-fixture-0001"
            tampered_body = b64url_encode(json.dumps(tampered_claims, sort_keys=True, separators=(",", ":")).encode("utf-8"))
            tampered_payload_token = tampered_body + "." + signature
            expect_invalid(lambda: resolver.resolve(tampered_payload_token), "tampered payload with original signature is rejected")

            signature_bytes = bytearray(b64url_decode(signature))
            signature_bytes[0] ^= 1
            tampered_signature_token = body + "." + b64url_encode(bytes(signature_bytes))
            expect_invalid(lambda: resolver.resolve(tampered_signature_token), "tampered signature is rejected")

            expired = resolver.issue_token(ANON_REF, issued_at=NOW - 4000)
            expect_invalid(lambda: resolver.resolve(expired), "expired token is rejected")

            future = resolver.issue_token(ANON_REF, issued_at=NOW + 31)
            expect_invalid(lambda: resolver.resolve(future), "token issued beyond allowed future skew is rejected")

            unknown_kid_claims = dict(claims)
            unknown_kid_claims["kid"] = "unknown-key"
            unknown_kid = resign_claims(unknown_kid_claims, secret)
            expect_invalid(lambda: resolver.resolve(unknown_kid), "unknown key id is rejected before identity resolution")

            wrong_secret = hashlib.sha256((secret_text + "-wrong").encode("utf-8")).digest()
            wrong_resolver = TrustedHostIdentityResolver(
                store=store,
                signing_keys={KEY_ID: wrong_secret},
                active_key_id=KEY_ID,
                now_provider=lambda: NOW,
                ttl_seconds=3600,
            )
            expect_invalid(lambda: wrong_resolver.resolve(issued.token), "same key id with wrong signing secret is rejected")

            extra_claims = dict(claims)
            extra_claims["learner_profile_id"] = LEARNER
            extra_claim_token = resign_claims(extra_claims, secret)
            expect_invalid(lambda: resolver.resolve(extra_claim_token), "token with forbidden learner_profile_id claim is rejected")

    summary = {
        "task": "PEIS-TRUSTED-HOST-001",
        "result": "PASS",
        "reuse_audit": {
            "baseline_main": "24fc37e90d47f54206002de109d20f2e74eb1e29",
            "project_auth_host_found": False,
            "shared_identity_linking_reused": True,
            "service_host_identity_contract_reused": True,
        },
        "trusted_host": {
            "browser_owns_learner_profile_id": False,
            "browser_owns_identity_refs": False,
            "token_exposes_learner_profile_id": False,
            "token_signature": "HMAC-SHA256",
            "cookie_http_only": True,
            "cookie_secure": True,
            "cookie_same_site": "Lax",
            "runtime_secret_injected": True,
            "production_auth_claimed": False,
        },
        "continuity": {
            "anonymous_to_user_same_learner": True,
            "evidence_rewritten": False,
            "evidence_migrated": False,
            "cross_subject_learner_profile": True,
        },
        "negative_gates": {
            "browser_identity_assertions": "REJECTED",
            "missing_token": "REJECTED",
            "malformed_token": "REJECTED",
            "tampered_payload": "REJECTED",
            "tampered_signature": "REJECTED",
            "expired_token": "REJECTED",
            "future_iat": "REJECTED",
            "unknown_key_id": "REJECTED",
            "wrong_secret": "REJECTED",
            "forbidden_token_claim": "REJECTED",
            "email_identity": "REJECTED",
            "identity_reassignment": "REJECTED",
        },
        "implementation_status": "REFERENCE_TRUSTED_HOST_IDENTITY_VALIDATED_NOT_PRODUCTION_AUTH",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    print("PEIS-TRUSTED-HOST-001 VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
