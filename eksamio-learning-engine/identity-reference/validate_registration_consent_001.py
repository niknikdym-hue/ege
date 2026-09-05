#!/usr/bin/env python3
"""Deterministic acceptance checks for authenticated registration consent."""
from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from registration_consent import (  # noqa: E402
    ACTION_DECLINE,
    ACTION_GRANT,
    ACTION_REVOKE,
    CONSENT_MARKETING,
    CONSENT_PERSONAL_DATA,
    ConsentReplayConflict,
    MissingConsentEvidence,
    PersonalDataConsentRequired,
    RegistrationConsentStore,
    RegistrationService,
)


class FakeAuthStore:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, object]] = {}

    def challenge(self, challenge_id: str):
        return self.rows.get(challenge_id)


class FakeIdentityService:
    def __init__(self) -> None:
        self.auth_store = FakeAuthStore()
        self.begin_calls: list[dict[str, object]] = []
        self.sessions: dict[str, SimpleNamespace] = {}
        self.counter = 0

    @staticmethod
    def _normalize_contact(channel: str, contact: str) -> str:
        assert channel == "email"
        value = contact.strip().casefold()
        if value.count("@") != 1 or "." not in value.split("@", 1)[1]:
            raise ValueError("invalid e-mail")
        return value

    @staticmethod
    def _user_identity_ref(channel: str, normalized_contact: str) -> str:
        digest = hashlib.sha256(
            f"fixture|{channel}|{normalized_contact}".encode("utf-8")
        ).hexdigest()
        return "user:" + digest[:48]

    def begin(self, payload, *, anonymous_host_token=None):
        self.begin_calls.append(
            {
                "payload": dict(payload),
                "anonymous_host_token": anonymous_host_token,
            }
        )
        self.counter += 1
        challenge_id = f"challenge:{self.counter:04d}"
        normalized = self._normalize_contact("email", payload["contact"])
        user_ref = self._user_identity_ref("email", normalized)
        self.auth_store.rows[challenge_id] = {
            "challenge_id": challenge_id,
            "user_identity_ref": user_ref,
        }
        return SimpleNamespace(
            challenge_id=challenge_id,
            channel="email",
            expires_at_epoch=1_800_000_000,
            delivery_ref=f"delivery:{self.counter:04d}",
        )

    def verify(self, payload):
        row = self.auth_store.challenge(payload["challenge_id"])
        if row is None or payload["code"] != "123456":
            raise ValueError("invalid fixture verification")
        token = f"sid.fixture.{self.counter:04d}.abcdefghijklmnopqrstuvwxyz"
        host = SimpleNamespace(
            learner_profile_id=f"learner:{self.counter:04d}",
            identity_refs={"user_identity_ref": row["user_identity_ref"]},
        )
        self.sessions[token] = host
        return SimpleNamespace(token=token, host_identity=host)

    def resolve_session(self, token: str):
        if token not in self.sessions:
            raise ValueError("invalid fixture session")
        return self.sessions[token]


def payload(
    email: str = "Learner@Example.invalid",
    *,
    pd: bool = True,
    marketing: bool = False,
    request_id: str = "reg-request-0001",
):
    return {
        "email": email,
        "personal_data_consent": pd,
        "marketing_consent": marketing,
        "personal_data_document_version": "pd-consent-v0.1",
        "personal_data_text_version": "pd-text-v0.1",
        "marketing_document_version": "marketing-consent-v0.1",
        "marketing_text_version": "marketing-text-v0.1",
        "client_request_id": request_id,
    }


def row_values(connection):
    return connection.execute(
        """
        SELECT event_id, user_identity_ref, consent_type, action,
               captured_at_epoch, document_version, text_version,
               client_request_id
        FROM registration_consent_events
        ORDER BY captured_at_epoch, event_id
        """
    ).fetchall()


def main() -> int:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    now = {"value": 1_780_000_000}
    event_counter = {"value": 0}

    def event_id():
        event_counter["value"] += 1
        return f"consent:event:{event_counter['value']:06d}"

    store = RegistrationConsentStore(
        connection,
        now_provider=lambda: now["value"],
        event_id_factory=event_id,
    )
    identity = FakeIdentityService()
    service = RegistrationService(
        identity_service=identity,
        consent_store=store,
    )

    # 1. Required personal-data consent is a hard gate before delivery.
    try:
        service.begin_registration(payload(pd=False))
        raise AssertionError("registration without personal-data consent was accepted")
    except PersonalDataConsentRequired:
        pass
    assert identity.begin_calls == []

    # 2. Optional marketing consent may be false and registration still works.
    receipt = service.begin_registration(payload(marketing=False))
    assert receipt.channel == "email"
    assert receipt.marketing_consent is False
    assert identity.begin_calls[-1]["anonymous_host_token"] is None
    user_ref = identity.auth_store.challenge(receipt.challenge_id)["user_identity_ref"]
    assert store.personal_data_granted(user_identity_ref=user_ref) is True
    assert store.marketing_allowed(user_identity_ref=user_ref) is False
    marketing_row = store.latest_state(
        user_identity_ref=user_ref, consent_type=CONSENT_MARKETING
    )
    assert marketing_row["action"] == ACTION_DECLINE

    # 3. A positive marketing checkbox is recorded separately.
    now["value"] += 1
    receipt2 = service.begin_registration(
        payload(
            email="optin@example.invalid",
            marketing=True,
            request_id="reg-request-0002",
        )
    )
    user_ref2 = identity.auth_store.challenge(receipt2.challenge_id)["user_identity_ref"]
    assert store.personal_data_granted(user_identity_ref=user_ref2) is True
    assert store.marketing_allowed(user_identity_ref=user_ref2) is True
    pd_row = store.latest_state(
        user_identity_ref=user_ref2, consent_type=CONSENT_PERSONAL_DATA
    )
    marketing_row2 = store.latest_state(
        user_identity_ref=user_ref2, consent_type=CONSENT_MARKETING
    )
    assert pd_row["action"] == ACTION_GRANT
    assert marketing_row2["action"] == ACTION_GRANT
    assert pd_row["event_id"] != marketing_row2["event_id"]

    # 4. Consent evidence never stores the raw e-mail/contact.
    serialized = "\n".join(str(tuple(row)) for row in row_values(connection))
    assert "@" not in serialized
    assert "example.invalid" not in serialized.casefold()

    # 5. Timestamp is server-owned, not accepted from browser payload.
    assert int(pd_row["captured_at_epoch"]) == now["value"]

    # 6. Exact retry is idempotent at the append-only consent ledger.
    replay = store.append_event(
        user_identity_ref=user_ref2,
        consent_type=CONSENT_PERSONAL_DATA,
        action=ACTION_GRANT,
        document_version="pd-consent-v0.1",
        text_version="pd-text-v0.1",
        client_request_id="manual-replay-0001",
    )
    replay2 = store.append_event(
        user_identity_ref=user_ref2,
        consent_type=CONSENT_PERSONAL_DATA,
        action=ACTION_GRANT,
        document_version="pd-consent-v0.1",
        text_version="pd-text-v0.1",
        client_request_id="manual-replay-0001",
    )
    assert replay["status"] == "RECORDED"
    assert replay2["status"] == "ALREADY_RECORDED"
    assert replay["event_id"] == replay2["event_id"]

    # 7. A retry may not silently change choice or legal text.
    try:
        store.append_event(
            user_identity_ref=user_ref2,
            consent_type=CONSENT_PERSONAL_DATA,
            action=ACTION_DECLINE,
            document_version="pd-consent-v0.1",
            text_version="pd-text-v0.1",
            client_request_id="manual-replay-0001",
        )
        raise AssertionError("conflicting consent replay was accepted")
    except ConsentReplayConflict:
        pass

    # 8. Account verification requires the separate PD consent record.
    orphan = identity.begin(
        {"channel": "email", "contact": "orphan@example.invalid"},
        anonymous_host_token=None,
    )
    try:
        service.verify_registration(
            {"challenge_id": orphan.challenge_id, "code": "123456"}
        )
        raise AssertionError("verification without PD consent evidence was accepted")
    except MissingConsentEvidence:
        pass

    # 9. Normal registration verifies and yields an authenticated session.
    session = service.verify_registration(
        {"challenge_id": receipt2.challenge_id, "code": "123456"}
    )
    assert session.token.startswith("sid.")
    assert service.marketing_allowed_for_session(session.token) is True

    # 10. Marketing revocation is server-owned, authenticated and idempotent.
    now["value"] += 1
    revoke = service.revoke_marketing(
        session_token=session.token,
        document_version="marketing-consent-v0.1",
        text_version="marketing-text-v0.1",
        client_request_id="marketing-revoke-0001",
    )
    revoke2 = service.revoke_marketing(
        session_token=session.token,
        document_version="marketing-consent-v0.1",
        text_version="marketing-text-v0.1",
        client_request_id="marketing-revoke-0001",
    )
    assert revoke["status"] == "RECORDED"
    assert revoke2["status"] == "ALREADY_RECORDED"
    assert service.marketing_allowed_for_session(session.token) is False
    latest_marketing = store.latest_state(
        user_identity_ref=user_ref2, consent_type=CONSENT_MARKETING
    )
    assert latest_marketing["action"] == ACTION_REVOKE

    # 11. No path in this facade opts into anonymous continuity.
    assert all(call["anonymous_host_token"] is None for call in identity.begin_calls)

    print("registration consent acceptance: PASS (11 gates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
