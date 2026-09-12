#!/usr/bin/env python3
"""Real PostgreSQL acceptance for registration -> identity -> canonical learner state."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
SUBSTRATE = ENGINE / "peis-production-substrate"
sys.path[:0] = [
    str(HERE),
    str(SUBSTRATE),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-trusted-host-reference"),
]

from passwordless_identity import (  # noqa: E402
    IdentityAuthStore,
    NonProductionCaptureDeliveryProvider,
    PasswordlessIdentityService,
)
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from peis_trusted_host import TrustedHostIdentityResolver  # noqa: E402
from registration_consent import RegistrationConsentStore, RegistrationService  # noqa: E402
from registration_http import RegistrationHttpBoundary  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def session_token(set_cookie: str) -> str:
    pair = set_cookie.split(";", 1)[0]
    name, token = pair.split("=", 1)
    require(name == "eksamio_pro_session" and bool(token), "secure session cookie names a non-empty server token")
    return token


def begin_payload(client_request_id: str) -> dict[str, object]:
    return {
        "email": "postgres-registration@learner.invalid",
        "personal_data_consent": True,
        "marketing_consent": False,
        "personal_data_document_version": "pd-doc-v1",
        "personal_data_text_version": "pd-text-v1",
        "marketing_document_version": "marketing-doc-v1",
        "marketing_text_version": "marketing-text-v1",
        "client_request_id": client_request_id,
    }


def main() -> None:
    dsn = os.environ.get("EKSAMIO_TEST_POSTGRES_DSN", "")
    require(bool(dsn), "EKSAMIO_TEST_POSTGRES_DSN is required")

    evidence = json.loads((ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8"))
    nba = json.loads((ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(encoding="utf-8"))
    store = PostgresPeisPersistenceStore(dsn, evidence_schema=evidence, nba_schema=nba)
    try:
        require(store.readiness(), "Postgres PEIS + identity/registration migrations are ready")

        migration_rows = store.connection.execute(
            "SELECT version FROM peis_schema_migrations ORDER BY version"
        ).fetchall()
        migration_versions = {str(row["version"]) for row in migration_rows}
        require(
            {"0001_peis_postgres", "0002_identity_registration_postgres"}.issubset(migration_versions),
            "both production migrations are present",
        )

        trusted_host = TrustedHostIdentityResolver(
            store=store,
            signing_keys={"registration-v1": b"s" * 32},
            active_key_id="registration-v1",
        )
        delivery = NonProductionCaptureDeliveryProvider()
        auth_store = IdentityAuthStore(store.connection)
        challenge_ids = iter(("ch:postgres-registration-0001", "ch:postgres-registration-0002"))
        session_tokens = iter(("sid.postgres-registration-session-0001", "sid.postgres-registration-session-0002"))
        identity = PasswordlessIdentityService(
            peis_store=store,
            trusted_host_resolver=trusted_host,
            auth_store=auth_store,
            delivery_provider=delivery,
            contact_hmac_key=b"c" * 32,
            verification_hmac_key=b"v" * 32,
            challenge_id_factory=lambda: next(challenge_ids),
            code_factory=lambda: "314159",
            session_token_factory=lambda: next(session_tokens),
            learner_profile_factory=lambda: "learner:postgres-registration-0001",
        )
        consent = RegistrationConsentStore(
            store.connection,
            event_id_factory=iter(
                (
                    "consent:postgres-pd-0001",
                    "consent:postgres-marketing-0001",
                    "consent:postgres-pd-0002",
                    "consent:postgres-marketing-0002",
                )
            ).__next__,
        )
        registration = RegistrationService(identity_service=identity, consent_store=consent)
        boundary = RegistrationHttpBoundary(
            registration_service=registration,
            allowed_origin="https://eksamio.ru",
        )
        headers = {
            "Origin": "https://eksamio.ru",
            "Content-Type": "application/json",
        }

        first_begin = boundary.handle(
            method="POST",
            path=boundary.BEGIN_PATH,
            headers=headers,
            payload=begin_payload("registration-request-0001"),
        )
        require(first_begin.status_code == 202 and first_begin.body.get("ok") is True, "first HTTP registration begin succeeds")
        first_challenge = str(first_begin.body["challenge_id"])
        require(first_challenge == "ch:postgres-registration-0001", "first challenge is server-owned")

        exact_retry = boundary.handle(
            method="POST",
            path=boundary.BEGIN_PATH,
            headers=headers,
            payload=begin_payload("registration-request-0001"),
        )
        require(exact_retry.status_code == 202 and exact_retry.body.get("challenge_id") == first_challenge, "exact begin retry is idempotent")
        require(len(delivery.deliveries) == 1, "exact retry does not send a second verification code")

        first_verify = boundary.handle(
            method="POST",
            path=boundary.VERIFY_PATH,
            headers=headers,
            payload={"challenge_id": first_challenge, "code": delivery.code_for(first_challenge)},
        )
        require(first_verify.status_code == 200 and first_verify.body.get("status") == "AUTHENTICATED", "first HTTP verification authenticates")
        require("token" not in json.dumps(first_verify.body).lower(), "session token is absent from browser JSON")
        first_cookie = str(first_verify.headers.get("Set-Cookie", ""))
        require(all(flag in first_cookie for flag in ("HttpOnly", "Secure", "SameSite=Lax")), "HTTP verify returns protected session cookie")
        first_host = identity.resolve_session(session_token(first_cookie))
        first_user_ref = str(first_host.identity_refs["user_identity_ref"])
        require(store.resolve_identity(first_user_ref) == first_host.learner_profile_id, "verified session resolves through canonical PEIS identity link")
        require("anonymous_identity_ref" not in first_host.identity_refs, "registered path creates no anonymous learner identity")

        second_begin = boundary.handle(
            method="POST",
            path=boundary.BEGIN_PATH,
            headers=headers,
            payload=begin_payload("registration-request-0002"),
        )
        second_challenge = str(second_begin.body["challenge_id"])
        require(second_begin.status_code == 202 and second_challenge != first_challenge, "new registration attempt gets a new challenge")
        second_verify = boundary.handle(
            method="POST",
            path=boundary.VERIFY_PATH,
            headers=headers,
            payload={"challenge_id": second_challenge, "code": delivery.code_for(second_challenge)},
        )
        require(second_verify.status_code == 200, "second verification authenticates")
        second_host = identity.resolve_session(session_token(str(second_verify.headers["Set-Cookie"])))
        require(second_host.learner_profile_id == first_host.learner_profile_id, "same registered email resolves to one server-owned learner profile across sessions")

        consent_rows = store.connection.execute(
            "SELECT event_seq, user_identity_ref, consent_type, action FROM registration_consent_events ORDER BY event_seq"
        ).fetchall()
        require(len(consent_rows) == 4, "two registration attempts produce exactly four append-only consent events")
        require([int(row["event_seq"]) for row in consent_rows] == sorted(int(row["event_seq"]) for row in consent_rows), "Postgres sequence owns total consent ordering")
        require(all("@" not in str(row["user_identity_ref"]) for row in consent_rows), "consent ledger stores no raw email PII")

        identity_kinds = {
            str(row["identity_kind"])
            for row in store.connection.execute("SELECT identity_kind FROM identity_links").fetchall()
        }
        require(identity_kinds == {"USER"}, "registration creates USER identity links only")

        append_only_blocked = False
        try:
            with store.connection:
                store.connection.execute(
                    "UPDATE registration_consent_events SET action='REVOKE' WHERE event_seq = %s",
                    (int(consent_rows[0]["event_seq"]),),
                )
        except Exception:
            append_only_blocked = True
        require(append_only_blocked, "Postgres blocks mutation of consent history")

        print("REGISTRATION_POSTGRES_REAL_INTEGRATION=PASS")
        print("canonical_state_owner=shared_postgres_peis")
        print("same_registered_email_same_learner_profile=PASS")
        print("anonymous_learner_identity=0")
        print("raw_email_in_consent_ledger=0")
        print("consent_append_only=PASS")
        print("http_session_cookie=SECURE_HTTPONLY_SAMESITE_LAX")
    finally:
        store.close()


if __name__ == "__main__":
    main()
