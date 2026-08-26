#!/usr/bin/env python3
"""Acceptance gate for SEP1-IDENTITY-001 on the real PostgreSQL PEIS substrate."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-production-substrate"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
    str(ENGINE / "peis-trusted-host-reference"),
]

from passwordless_identity import (  # noqa: E402
    AnonymousHistoryConflict,
    ChallengeExpired,
    ChallengeReplay,
    IdentityAuthStore,
    IdentityError,
    InvalidChallenge,
    InvalidIdentityRequest,
    InvalidSession,
    InvalidVerificationCode,
    NonProductionCaptureDeliveryProvider,
    PasswordlessIdentityService,
)
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_service_bridge import AdapterRegistry, PeisServiceBridge  # noqa: E402
from peis_trusted_host import TrustedHostIdentityResolver  # noqa: E402
from russian_exceptions_practice_adapter import (  # noqa: E402
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)


class Clock:
    def __init__(self, value: int) -> None:
        self.value = value

    def now(self) -> int:
        return self.value


def _next(values: list[str]):
    iterator = iter(values)
    return lambda: next(iterator)


def _assert_raises(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def _stored_auth_material(store: PostgresPeisPersistenceStore) -> str:
    rows: list[object] = []
    for table in ("passwordless_challenges", "identity_sessions", "identity_links"):
        rows.extend(store.connection.execute(f"SELECT * FROM {table}").fetchall())
    return repr(rows)


def main() -> int:
    dsn = os.environ["PEIS_DATABASE_DSN"]
    evidence_schema = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8")
    )
    nba_schema = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(encoding="utf-8")
    )
    store = PostgresPeisPersistenceStore(dsn, evidence_schema=evidence_schema, nba_schema=nba_schema)
    if not store.readiness():
        raise AssertionError("PostgreSQL PEIS store is not ready")

    clock = Clock(1_787_770_000)
    anon_refs = _next(["anon:sep1-fixture-a-0001", "anon:sep1-fixture-b-0002"])
    learner_refs = _next(["learner:sep1-fixture-a-0001", "learner:sep1-fixture-b-0002"])
    trusted = TrustedHostIdentityResolver(
        store=store,
        signing_keys={"ci": b"trusted-host-ci-key-0000000000000001"},
        active_key_id="ci",
        now_provider=clock.now,
        ttl_seconds=3600,
        anonymous_ref_factory=anon_refs,
        learner_profile_factory=learner_refs,
    )

    # Seed real anonymous Russian evidence before account conversion.
    anonymous = trusted.issue_anonymous()
    adapter = RussianExceptionsPracticeAdapter(ENGINE)
    registry = AdapterRegistry()
    registry.register(adapter)
    bridge = PeisServiceBridge(
        store=store,
        registry=registry,
        kernel_snapshot=kernel_snapshot,
        now_provider=lambda: "2026-08-26T19:00:00+00:00",
    )
    attempt = bridge.submit_checked_card(
        adapter_id=adapter.adapter_id,
        payload={
            "card_id": FIRST_SLICE_CARD_ID,
            "session_started_at_ms": 1787770000000,
            "session_mode": "practice",
            "answer": "сочитание",
            "occurred_at_client": "2026-08-26T18:59:59+00:00",
            "client_request_id": "identity-fixture-attempt-a",
        },
        host_identity=anonymous.host_identity,
    )
    if attempt["status"] != "ACCEPTED":
        raise AssertionError("anonymous evidence seed was not accepted")
    if store.event_count(learner_profile_id=anonymous.host_identity.learner_profile_id) != 1:
        raise AssertionError("anonymous evidence is not owned by the expected learner profile")

    auth_store = IdentityAuthStore(store.connection)
    delivery = NonProductionCaptureDeliveryProvider()
    service = PasswordlessIdentityService(
        peis_store=store,
        trusted_host_resolver=trusted,
        auth_store=auth_store,
        delivery_provider=delivery,
        contact_hmac_key=b"contact-hmac-ci-key-00000000000000001",
        verification_hmac_key=b"verify-hmac-ci-key-00000000000000001",
        now_provider=clock.now,
        challenge_ttl_seconds=600,
        session_ttl_seconds=3600,
        challenge_id_factory=_next([
            "ch:sep1-fixture-00000001",
            "ch:sep1-fixture-00000002",
            "ch:sep1-fixture-00000003",
            "ch:sep1-fixture-00000004",
        ]),
        code_factory=_next(["123456", "234567", "345678", "456789"]),
        session_token_factory=_next([
            "sid.sep1-fixture-session-token-0000000000000001",
            "sid.sep1-fixture-session-token-0000000000000002",
            "sid.sep1-fixture-session-token-0000000000000003",
        ]),
        learner_profile_factory=lambda: "learner:sep1-new-account-fixture",
    )

    # Browser/localStorage cannot assert canonical identity fields at auth entry.
    _assert_raises(
        InvalidIdentityRequest,
        service.begin,
        {"channel": "email", "contact": "person@example.invalid", "learner_profile_id": "evil-browser-id"},
        anonymous_host_token=anonymous.token,
    )

    receipt = service.begin(
        {"channel": "email", "contact": "Person@Example.Invalid"},
        anonymous_host_token=anonymous.token,
    )
    if "person@example.invalid" in _stored_auth_material(store).casefold():
        raise AssertionError("raw contact leaked into persistent identity/auth tables")
    code = delivery.code_for(receipt.challenge_id)
    _assert_raises(
        InvalidVerificationCode,
        service.verify,
        {"challenge_id": receipt.challenge_id, "code": "000000"},
    )
    if auth_store.challenge(receipt.challenge_id)["consumed_at_epoch"] is not None:
        raise AssertionError("wrong verification code consumed the challenge")

    first_session = service.verify({"challenge_id": receipt.challenge_id, "code": code})
    if first_session.host_identity.learner_profile_id != anonymous.host_identity.learner_profile_id:
        raise AssertionError("anonymous learner profile/evidence was not retained on account conversion")
    if first_session.anonymous_link_status != "ANONYMOUS_PROFILE_LINKED_TO_USER":
        raise AssertionError(f"unexpected anonymous link status: {first_session.anonymous_link_status}")
    if store.event_count(learner_profile_id=first_session.host_identity.learner_profile_id) != 1:
        raise AssertionError("anonymous evidence disappeared or duplicated during account conversion")
    if store.resolve_identity(first_session.user_identity_ref) != anonymous.host_identity.learner_profile_id:
        raise AssertionError("verified user identity is not linked to the anonymous learner profile")
    _assert_raises(
        ChallengeReplay,
        service.verify,
        {"challenge_id": receipt.challenge_id, "code": code},
    )
    resolved = service.resolve_session(first_session.token)
    if resolved.learner_profile_id != anonymous.host_identity.learner_profile_id:
        raise AssertionError("server session did not resolve canonical learner identity")
    if first_session.token in _stored_auth_material(store):
        raise AssertionError("raw session token leaked into persistent auth tables")

    # Cross-browser sign-in from the same verified contact resolves the same server learner.
    cross_browser = service.begin({"channel": "email", "contact": "person@example.invalid"})
    cross_session = service.verify(
        {"challenge_id": cross_browser.challenge_id, "code": delivery.code_for(cross_browser.challenge_id)}
    )
    if cross_session.host_identity.learner_profile_id != first_session.host_identity.learner_profile_id:
        raise AssertionError("cross-browser verified login forked the learner profile")
    if cross_session.user_identity_ref != first_session.user_identity_ref:
        raise AssertionError("normalized verified contact did not resolve stable opaque user identity")

    rotated = service.rotate_session(cross_session.token)
    _assert_raises(InvalidSession, service.resolve_session, cross_session.token)
    if service.resolve_session(rotated.token).learner_profile_id != first_session.host_identity.learner_profile_id:
        raise AssertionError("session rotation changed canonical learner identity")
    if service.logout(rotated.token) != "LOGGED_OUT":
        raise AssertionError("logout did not revoke active session")
    _assert_raises(InvalidSession, service.resolve_session, rotated.token)
    if service.logout(rotated.token) != "LOGGED_OUT":
        # revoke is idempotent at the API contract: an existing row is already logged out.
        raise AssertionError("logout replay changed API behavior")

    # Expiry and unknown challenge rejection.
    expiring = service.begin({"channel": "email", "contact": "person@example.invalid"})
    expiring_code = delivery.code_for(expiring.challenge_id)
    clock.value = expiring.expires_at_epoch
    _assert_raises(
        ChallengeExpired,
        service.verify,
        {"challenge_id": expiring.challenge_id, "code": expiring_code},
    )
    _assert_raises(
        InvalidChallenge,
        service.verify,
        {"challenge_id": "ch:unknown-fixture-000000", "code": "123456"},
    )
    clock.value -= 1

    # A returning user with distinct anonymous evidence is never silently merged.
    second_anon = trusted.issue_anonymous()
    second_attempt = bridge.submit_checked_card(
        adapter_id=adapter.adapter_id,
        payload={
            "card_id": FIRST_SLICE_CARD_ID,
            "session_started_at_ms": 1787770001000,
            "session_mode": "practice",
            "answer": "сочитание",
            "occurred_at_client": "2026-08-26T19:00:01+00:00",
            "client_request_id": "identity-fixture-attempt-b",
        },
        host_identity=second_anon.host_identity,
    )
    if second_attempt["status"] != "ACCEPTED":
        raise AssertionError("second anonymous evidence seed was not accepted")
    conflict = service.begin(
        {"channel": "email", "contact": "person@example.invalid"},
        anonymous_host_token=second_anon.token,
    )
    _assert_raises(
        AnonymousHistoryConflict,
        service.verify,
        {"challenge_id": conflict.challenge_id, "code": delivery.code_for(conflict.challenge_id)},
    )
    if store.resolve_identity(first_session.user_identity_ref) != first_session.host_identity.learner_profile_id:
        raise AssertionError("conflicting anonymous history changed canonical user identity")

    # CI provider is structurally incapable of delivering to a real address.
    _assert_raises(
        IdentityError,
        delivery.deliver,
        channel="email",
        contact="real@example.com",
        code="999999",
        challenge_id="ch:must-not-deliver-0001",
    )

    output = {
        "task": "SEP1-IDENTITY-001",
        "result": "PASS",
        "baseline_main": "9e4354af83347a0952483976cfebdabd74cae0e3",
        "postgres_auth_state": True,
        "verified_contact_persisted_raw": False,
        "session_token_persisted_raw": False,
        "anonymous_evidence_retained": True,
        "anonymous_to_user_link_exactly_once": True,
        "challenge_invalid_rejected": True,
        "challenge_expiry_rejected": True,
        "challenge_replay_rejected": True,
        "cross_browser_same_learner": True,
        "session_rotation": True,
        "logout_revoke": True,
        "browser_identity_assertion_rejected": True,
        "unsafe_distinct_anonymous_history_merge_rejected": True,
        "real_delivery_performed": False,
        "provider_boundary": "email_or_phone",
        "final_status": "IDENTITY_VERTICAL_SLICE_READY_FOR_PROVIDER_ACCEPTANCE",
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
