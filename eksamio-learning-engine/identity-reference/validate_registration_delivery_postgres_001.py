#!/usr/bin/env python3
"""Real PostgreSQL regression for registration delivery idempotency and ambiguity."""
from __future__ import annotations

import json
import os
import sys
import threading
import time
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

from passwordless_identity import IdentityAuthStore, PasswordlessIdentityService  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from peis_trusted_host import TrustedHostIdentityResolver  # noqa: E402
from registration_consent import (  # noqa: E402
    RegistrationConsentStore,
    RegistrationDeliveryOutcomeUnknown,
    RegistrationDeliveryUnavailable,
    RegistrationService,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def payload(*, email: str, request_id: str) -> dict[str, object]:
    return {
        "email": email,
        "personal_data_consent": True,
        "marketing_consent": False,
        "personal_data_document_version": "pd-doc-v1",
        "personal_data_text_version": "pd-text-v1",
        "marketing_document_version": "marketing-doc-v1",
        "marketing_text_version": "marketing-text-v1",
        "client_request_id": request_id,
    }


class CountingProvider:
    def __init__(self, *, delay_seconds: float = 0.0) -> None:
        self.delay_seconds = delay_seconds
        self.lock = threading.Lock()
        self.calls: list[tuple[str, str]] = []

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        require(channel == "email", "registration delivery remains email-only")
        with self.lock:
            self.calls.append((challenge_id, code))
            sequence = len(self.calls)
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        return f"capture:{sequence}:{challenge_id}"


class AmbiguousAfterSendProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        self.calls.append((challenge_id, code))
        raise TimeoutError("provider may have accepted the message before timeout")


class ExplicitNotSent(Exception):
    delivery_outcome = "NOT_SENT"


class NotSentThenSuccessProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def deliver(self, *, channel: str, contact: str, code: str, challenge_id: str) -> str:
        self.calls.append((challenge_id, code))
        if len(self.calls) == 1:
            raise ExplicitNotSent("fixture proves message was not handed to provider")
        return "capture:not-sent-retry:" + challenge_id


def make_service(dsn: str, provider, suffix: str):
    evidence = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8")
    )
    nba = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(encoding="utf-8")
    )
    store = PostgresPeisPersistenceStore(dsn, evidence_schema=evidence, nba_schema=nba)
    trusted = TrustedHostIdentityResolver(
        store=store,
        signing_keys={"registration-v1": b"h" * 32},
        active_key_id="registration-v1",
    )
    counter = {"value": 0}

    def challenge_id() -> str:
        counter["value"] += 1
        return f"ch:delivery-{suffix}-{counter['value']:04d}"

    identity = PasswordlessIdentityService(
        peis_store=store,
        trusted_host_resolver=trusted,
        auth_store=IdentityAuthStore(store.connection),
        delivery_provider=provider,
        contact_hmac_key=b"c" * 32,
        verification_hmac_key=b"v" * 32,
        challenge_id_factory=challenge_id,
    )
    service = RegistrationService(
        identity_service=identity,
        consent_store=RegistrationConsentStore(store.connection),
    )
    return store, service


def main() -> None:
    dsn = os.environ.get("EKSAMIO_TEST_POSTGRES_DSN", "")
    require(bool(dsn), "EKSAMIO_TEST_POSTGRES_DSN is required")

    provider = CountingProvider(delay_seconds=0.08)
    service_rows = [make_service(dsn, provider, f"concurrent-{index}") for index in range(8)]
    barrier = threading.Barrier(8)
    successes: list[str] = []
    bounded: list[str] = []
    failures: list[BaseException] = []
    lock = threading.Lock()

    def worker(service) -> None:
        try:
            barrier.wait(timeout=5)
            receipt = service.begin_registration(
                payload(email="concurrent@learner.invalid", request_id="delivery-concurrent-0001")
            )
            with lock:
                successes.append(receipt.challenge_id)
        except RegistrationDeliveryOutcomeUnknown:
            with lock:
                bounded.append("DELIVERY_IN_PROGRESS_OR_UNKNOWN")
        except BaseException as exc:
            with lock:
                failures.append(exc)

    threads = [
        threading.Thread(target=worker, args=(service,), name=f"registration-{index}")
        for index, (_store, service) in enumerate(service_rows)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    require(not failures, f"unexpected concurrent registration failure: {failures!r}")
    require(len(provider.calls) == 1, "concurrent exact duplicate provider calls must equal 1")

    canonical_store, canonical_service = service_rows[0]
    exact_retry = canonical_service.begin_registration(
        payload(email="concurrent@learner.invalid", request_id="delivery-concurrent-0001")
    )
    require(
        exact_retry.challenge_id == provider.calls[0][0],
        "exact retry reuses the one durable challenge",
    )
    require(len(provider.calls) == 1, "exact retry after concurrent begin must not resend")
    operation_count = canonical_store.connection.execute(
        "SELECT COUNT(*) AS n FROM registration_begin_operations WHERE user_identity_ref = ?",
        (
            canonical_service._registration_user_identity_ref("concurrent@learner.invalid"),
        ),
    ).fetchone()
    require(int(operation_count["n"]) == 1, "concurrent exact begin owns one durable operation")

    for store, _service in service_rows:
        store.close()

    ambiguous_provider = AmbiguousAfterSendProvider()
    ambiguous_store, ambiguous_service = make_service(dsn, ambiguous_provider, "ambiguous")
    ambiguous_payload = payload(
        email="ambiguous@learner.invalid",
        request_id="delivery-ambiguous-0001",
    )
    try:
        ambiguous_service.begin_registration(ambiguous_payload)
        raise AssertionError("ambiguous provider failure was accepted")
    except RegistrationDeliveryOutcomeUnknown:
        pass
    require(len(ambiguous_provider.calls) == 1, "ambiguous first attempt calls provider once")
    try:
        ambiguous_service.begin_registration(ambiguous_payload)
        raise AssertionError("ambiguous exact retry was accepted")
    except RegistrationDeliveryOutcomeUnknown:
        pass
    require(len(ambiguous_provider.calls) == 1, "ambiguous exact retry must not resend")
    ambiguous_row = ambiguous_store.connection.execute(
        "SELECT delivery_state FROM registration_begin_operations WHERE user_identity_ref = ?",
        (ambiguous_service._registration_user_identity_ref("ambiguous@learner.invalid"),),
    ).fetchone()
    require(str(ambiguous_row["delivery_state"]) == "UNKNOWN", "ambiguous delivery remains durably UNKNOWN")
    ambiguous_store.close()

    not_sent_provider = NotSentThenSuccessProvider()
    not_sent_store, not_sent_service = make_service(dsn, not_sent_provider, "not-sent")
    not_sent_payload = payload(
        email="not-sent@learner.invalid",
        request_id="delivery-not-sent-0001",
    )
    try:
        not_sent_service.begin_registration(not_sent_payload)
        raise AssertionError("explicit NOT_SENT fixture unexpectedly succeeded first time")
    except RegistrationDeliveryUnavailable:
        pass
    receipt = not_sent_service.begin_registration(not_sent_payload)
    require(len(not_sent_provider.calls) == 2, "explicit NOT_SENT is the only safe resend path")
    require(
        not_sent_provider.calls[0] == not_sent_provider.calls[1],
        "safe resend reuses exact challenge and exact verification code",
    )
    require(receipt.challenge_id == not_sent_provider.calls[0][0], "safe resend preserves durable challenge")
    not_sent_store.close()

    print("REGISTRATION_DELIVERY_POSTGRES=PASS")
    print("concurrent_duplicate_provider_calls=1")
    print("ambiguous_provider_retry_calls=1")
    print("ambiguous_state=UNKNOWN")
    print("explicit_not_sent_retry=SAFE_SAME_CHALLENGE")
    print("real_provider_calls=0")


if __name__ == "__main__":
    main()
