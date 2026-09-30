#!/usr/bin/env python3
"""Full deterministic SEP-1 production-candidate smoke across merged boundaries.

CI only. This runner performs no live provider calls, no real charges/refunds,
no real e-mail/SMS, and no production PEIS writes. It proves that the existing
server-owned identity, payment, shared-PEIS and Tutor boundaries can be composed
into one exact-candidate chain before private live acceptance is authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(ENGINE / "payments-reference"),
    str(ENGINE / "identity-reference"),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-production-substrate"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
    str(ENGINE / "peis-trusted-host-reference"),
    str(ENGINE / "ai-tutor-reference"),
]

from passwordless_identity import (  # noqa: E402
    IdentityAuthStore,
    NonProductionCaptureDeliveryProvider,
    PasswordlessIdentityService,
)
from payments import FiscalItemPolicy, Offer, OfferCatalog, PaymentStore  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_service_bridge import AdapterRegistry, PeisServiceBridge  # noqa: E402
from peis_trusted_host import TrustedHostIdentityResolver  # noqa: E402
from production_e2e_boundary import (  # noqa: E402
    ProductionPaymentApiBoundary,
    ProviderReceiptEvent,
    ProviderRefundEvent,
)
from reliability_gateway import (  # noqa: E402
    FailureClass,
    ProviderPath,
    ReliabilityGateway,
)
from robokassa_production import (  # noqa: E402
    ProductionAdmission,
    RobokassaAdapter,
    RobokassaCredentialSet,
    RobokassaMode,
)
from russian_exceptions_practice_adapter import (  # noqa: E402
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)
from sep1_production_preflight import evaluate, legal_artifact_fingerprints  # noqa: E402
from sep1_russian_tutor import (  # noqa: E402
    GroundedTextProvider,
    MockSpeechProvider,
    RussianTutorVerticalSlice,
    VoiceGateway,
)

FIXED_NOW = 1_788_000_000
FIXED_ISO = "2026-08-29T12:00:00+00:00"
FIXED_ORDER = "ord:sep1-full-e2e-fixture"
FIXED_INV = 910001
FIXED_AMOUNT = 12345
DEFAULT_SHA = "0" * 40


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def next_factory(values: list[str]):
    iterator = iter(values)
    return lambda: next(iterator)


def payment_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def build_payment_boundary(store: PaymentStore) -> tuple[ProductionPaymentApiBoundary, RobokassaAdapter]:
    catalog = OfferCatalog(
        [
            Offer(
                code="RU_PRO_30_FULL_E2E_FIXTURE",
                product_code="EKSAMIO_PRO_RUSSIAN",
                duration_days=30,
                amount_kopecks=FIXED_AMOUNT,
                title_ru="Eksamio Pro — Русский, full E2E CI fixture",
            )
        ]
    )
    provider = RobokassaAdapter(
        mode=RobokassaMode.PRODUCTION_CANDIDATE,
        credentials=RobokassaCredentialSet(
            merchant_login="ci-full-e2e-merchant",
            password1="ci-full-e2e-password-1",
            password2="ci-full-e2e-password-2",
        ),
        fiscal_policy=FiscalItemPolicy(
            tax="none",
            payment_method="full_payment",
            payment_object="service",
        ),
        admission=ProductionAdmission(
            enabled=True,
            fiscal_policy_admitted=True,
            npd_fns_accepted=True,
            robocheki_accepted=True,
        ),
    )
    boundary = ProductionPaymentApiBoundary(
        store=store,
        catalog=catalog,
        provider=provider,
        now_provider=lambda: FIXED_NOW,
        order_id_factory=lambda: FIXED_ORDER,
        inv_id_factory=lambda: FIXED_INV,
    )
    return boundary, provider


def build_text_gateway() -> ReliabilityGateway:
    primary = GroundedTextProvider(
        "text-primary-mock",
        fail_once=FailureClass.CREDENTIAL_OR_ACCOUNT_FAILURE,
    )
    reserve = GroundedTextProvider("text-reserve-mock")
    registry = {
        ("text-primary-mock", "text"): ProviderPath(
            "text-primary-mock", "text", "fixture-v1", "PRODUCTION_ADMITTED", 1
        ),
        ("text-reserve-mock", "text"): ProviderPath(
            "text-reserve-mock", "text", "fixture-v1", "PRODUCTION_ADMITTED", 2
        ),
    }
    return ReliabilityGateway(registry, {primary.provider_id: primary, reserve.provider_id: reserve})


def build_evidence(candidate_sha: str, results: dict[str, Any]) -> dict[str, Any]:
    preflight_path = HERE / "sep1_production_preflight.py"
    legal = [
        {
            "id": str(row["id"]),
            "version": str(row["version"]),
            "sha256": str(row["sha256"]),
        }
        for row in legal_artifact_fingerprints()
    ]
    config_contract = {
        "payment_provider": "ROBOKASSA",
        "payment_methods": ["BankCard", "SBP"],
        "identity_delivery": "NONPRODUCTION_CAPTURE_ONLY",
        "peis_store": "POSTGRES_CI_FIXTURE",
        "tutor_text": "DETERMINISTIC_GROUNDED_MOCK",
        "tutor_voice": "DETERMINISTIC_PROVIDER_NEUTRAL_MOCK",
        "public_traffic": False,
        "production_charges": False,
    }
    return {
        "schema": "eksamio.sep1.production-e2e.v1",
        "evidence_class": "CI_SIMULATED_CONTRACT_EVIDENCE",
        "candidate": {
            "git_sha": candidate_sha,
            "config_fingerprint": canonical_sha256(config_contract),
            "preflight_fingerprint": sha256_bytes(preflight_path.read_bytes()),
            "legal_artifacts": legal,
            "russian_content_authority": {
                "status": "BLOCKED_SUBJECT",
                "fingerprint": None,
            },
            "ci": {
                "run_id": os.environ.get("GITHUB_RUN_ID"),
                "job": os.environ.get("GITHUB_JOB"),
            },
        },
        "results": results,
        "safety": {
            "outbound_provider_requests": 0,
            "real_charges": 0,
            "real_refunds": 0,
            "real_email_sms_deliveries": 0,
            "real_production_peis_writes": 0,
            "learner_audio_persisted_bytes": 0,
            "public_traffic_enabled": False,
            "owner_go_live_approved": False,
        },
    }


def run(*, peis_dsn: str, candidate_sha: str) -> dict[str, Any]:
    evidence_schema = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8")
    )
    nba_schema = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(encoding="utf-8")
    )
    peis_store = PostgresPeisPersistenceStore(
        peis_dsn,
        evidence_schema=evidence_schema,
        nba_schema=nba_schema,
    )
    if not peis_store.readiness():
        raise AssertionError("CI PostgreSQL PEIS store is not ready")

    trusted = TrustedHostIdentityResolver(
        store=peis_store,
        signing_keys={"ci": b"trusted-host-full-e2e-key-0000000001"},
        active_key_id="ci",
        now_provider=lambda: FIXED_NOW,
        ttl_seconds=3600,
        anonymous_ref_factory=lambda: "anon:sep1-full-e2e-fixture",
        learner_profile_factory=lambda: "learner:sep1-full-e2e-fixture",
    )
    anonymous = trusted.issue_anonymous()

    auth_store = IdentityAuthStore(peis_store.connection)
    delivery = NonProductionCaptureDeliveryProvider()
    identity_service = PasswordlessIdentityService(
        peis_store=peis_store,
        trusted_host_resolver=trusted,
        auth_store=auth_store,
        delivery_provider=delivery,
        contact_hmac_key=b"contact-hmac-full-e2e-ci-key-000000001",
        verification_hmac_key=b"verify-hmac-full-e2e-ci-key-0000000001",
        now_provider=lambda: FIXED_NOW,
        challenge_ttl_seconds=600,
        session_ttl_seconds=3600,
        challenge_id_factory=lambda: "ch:sep1-full-e2e-fixture-0001",
        code_factory=lambda: "123456",
        session_token_factory=lambda: "sid.sep1-full-e2e-session-token-0000000000000001",
        learner_profile_factory=lambda: "learner:unused-full-e2e-factory",
    )
    challenge = identity_service.begin(
        {"channel": "email", "contact": "learner@full-e2e.invalid"},
        anonymous_host_token=anonymous.token,
    )
    session = identity_service.verify(
        {"challenge_id": challenge.challenge_id, "code": delivery.code_for(challenge.challenge_id)}
    )
    if session.host_identity.learner_profile_id != anonymous.host_identity.learner_profile_id:
        raise AssertionError("anonymous learner continuity was not preserved")
    if session.anonymous_link_status != "ANONYMOUS_PROFILE_LINKED_TO_USER":
        raise AssertionError(f"unexpected anonymous-link status: {session.anonymous_link_status}")
    resolved = identity_service.resolve_session(session.token)
    if resolved.learner_profile_id != session.host_identity.learner_profile_id:
        raise AssertionError("server-owned session did not resolve the linked learner")

    with tempfile.TemporaryDirectory(prefix="eksamio-full-e2e-payment-") as tmp:
        payment_db = Path(tmp) / "payment.sqlite3"
        payment_conn = payment_connection(payment_db)
        payment_store = PaymentStore(payment_conn)
        payment, provider = build_payment_boundary(payment_store)
        created = payment.create_order(
            {"offer_code": "RU_PRO_30_FULL_E2E_FIXTURE", "payment_method": "SBP"},
            user_identity_ref=session.user_identity_ref,
            learner_profile_id=session.host_identity.learner_profile_id,
        )
        if created["production_candidate"] is not True or created["test_mode"] is not False:
            raise AssertionError("payment order is not production-candidate shaped")
        if "IsTest" in created["form_fields"]:
            raise AssertionError("production-candidate initiation leaked IsTest")

        out_sum = "123.45"
        result_payload = {
            "OutSum": out_sum,
            "InvId": str(FIXED_INV),
            "SignatureValue": provider.sign_result_for_local_validation(
                out_sum_text=out_sum,
                inv_id=FIXED_INV,
            ),
            "PaymentMethod": "SBP",
            "OpKey": "ci-full-e2e-payment-ref",
        }
        paid = payment.result_url(result_payload)
        replay = payment.result_url(dict(result_payload))
        if paid["entitlement_state"] != "ACTIVE" or paid["replay"] is not False:
            raise AssertionError("valid payment callback did not activate exactly once")
        if replay["replay"] is not True:
            raise AssertionError("payment callback replay was not idempotent")

        receipt = ProviderReceiptEvent(
            event_id="receipt-full-e2e-001",
            provider="ROBOCHEKI",
            payment_provider="ROBOKASSA",
            order_id=FIXED_ORDER,
            amount_kopecks=FIXED_AMOUNT,
            provider_receipt_ref="receipt-full-e2e-ref-001",
            status="REGISTERED",
        )
        if payment.receipt_event(receipt) is not True or payment.receipt_event(receipt) is not False:
            raise AssertionError("receipt provider event boundary is not idempotent")
        if not payment.paid_access_allowed(
            order_id=FIXED_ORDER,
            learner_profile_id=session.host_identity.learner_profile_id,
        ):
            raise AssertionError("paid entitlement did not open server-owned access")

        adapter = RussianExceptionsPracticeAdapter(ENGINE)
        registry = AdapterRegistry()
        registry.register(adapter)
        bridge = PeisServiceBridge(
            store=peis_store,
            registry=registry,
            kernel_snapshot=kernel_snapshot,
            now_provider=lambda: FIXED_ISO,
        )
        learning_payload = {
            "card_id": FIRST_SLICE_CARD_ID,
            "session_started_at_ms": FIXED_NOW * 1000,
            "session_mode": "practice",
            "answer": "сочетание",
            "occurred_at_client": "2026-08-29T11:59:59+00:00",
            "client_request_id": "req:sep1-full-e2e-learning-001",
        }
        learning = bridge.submit_checked_card(
            adapter_id=adapter.adapter_id,
            payload=learning_payload,
            host_identity=resolved,
        )
        learning_replay = bridge.submit_checked_card(
            adapter_id=adapter.adapter_id,
            payload=dict(learning_payload),
            host_identity=resolved,
        )
        if learning["status"] != "ACCEPTED" or learning_replay["status"] != "ALREADY_APPLIED":
            raise AssertionError("shared PEIS learning event/replay contract failed")
        if learning["directive"].get("canonical_state_owner") != "shared_peis":
            raise AssertionError("learning result is not owned by shared PEIS")
        if not learning["directive"].get("action_type"):
            raise AssertionError("shared PEIS did not return a next-best action")
        events = peis_store.list_events(resolved.learner_profile_id, "russian", effective=False)
        if len(events) != 1:
            raise AssertionError("learning replay duplicated canonical PEIS evidence")

        text_gateway = build_text_gateway()
        yandex_voice = MockSpeechProvider(
            "yandex-speechkit-mock",
            transcript="Почему в слове сочетание пишется е?",
            fail_asr_once=True,
        )
        reserve_voice = MockSpeechProvider(
            "openai-voice-reserve-mock",
            transcript="Почему в слове сочетание пишется е?",
        )
        voice_gateway = VoiceGateway([yandex_voice, reserve_voice])
        tutor = RussianTutorVerticalSlice(
            engine_root=ENGINE,
            text_gateway=text_gateway,
            voice_gateway=voice_gateway,
            session_ref_factory=lambda: "tutor:sep1-full-e2e-fixture",
        )
        tutor_state = tutor.open_session(
            learner_profile_id=resolved.learner_profile_id,
            card_id=FIRST_SLICE_CARD_ID,
        )
        if not payment.paid_access_allowed(
            order_id=FIXED_ORDER,
            learner_profile_id=resolved.learner_profile_id,
        ):
            raise AssertionError("Tutor was reached without active paid access")
        text_turn = tutor.text_turn(tutor_state.session_ref, "Объясни правило по проверенному материалу")
        transient_audio = b"TRANSIENT_FULL_E2E_LEARNER_AUDIO_DO_NOT_PERSIST"
        voice_turn = tutor.voice_turn(tutor_state.session_ref, transient_audio)
        if text_turn.reliable_result.status != "TUTOR_ADVISORY":
            raise AssertionError("grounded Tutor text path failed")
        if voice_turn.session_ref != text_turn.session_ref or voice_turn.modality != "voice":
            raise AssertionError("Tutor voice did not preserve the same logical session")
        if voice_turn.asr_provider_id != "openai-voice-reserve-mock":
            raise AssertionError("voice degraded-mode ASR fallback was not exercised")
        if voice_turn.tts_provider_id != "yandex-speechkit-mock":
            raise AssertionError("Yandex-preferred TTS path drifted")
        if tutor_state.raw_audio_persistence_count() != 0:
            raise AssertionError("learner audio entered persistent Tutor state")
        serialized_events = json.dumps(events, ensure_ascii=False, sort_keys=True)
        if "TRANSIENT_FULL_E2E_LEARNER_AUDIO_DO_NOT_PERSIST" in serialized_events or "MOCK_AUDIO|" in serialized_events:
            raise AssertionError("audio bytes leaked into shared PEIS evidence")

        voice_gateway.set_disabled("yandex-speechkit-mock", True)
        reserve_tts = voice_gateway.synthesize("Проверка kill switch", session_ref=tutor_state.session_ref)
        if reserve_tts.provider_id != "openai-voice-reserve-mock":
            raise AssertionError("voice provider kill switch did not preserve degraded service")
        voice_gateway.set_disabled("yandex-speechkit-mock", False)

        safe_preflight = evaluate({})
        if safe_preflight["kill_switch_failures"]:
            raise AssertionError("default preflight kill switches are not fail-closed")
        unsafe_preflight = evaluate({"PUBLIC_TRAFFIC_ENABLED": "true"})
        if unsafe_preflight["overall"] != "FAIL_UNSAFE_ACTIVATION":
            raise AssertionError("public-traffic kill switch did not hard-fail")

        refund = ProviderRefundEvent(
            event_id="refund-full-e2e-001",
            provider="ROBOKASSA",
            payment_provider="ROBOKASSA",
            order_id=FIXED_ORDER,
            amount_kopecks=FIXED_AMOUNT,
            provider_ref="refund-full-e2e-ref-001",
        )
        if payment.refund_event(refund) is not True or payment.refund_event(refund) is not False:
            raise AssertionError("refund provider event boundary is not idempotent")
        if payment.paid_access_allowed(
            order_id=FIXED_ORDER,
            learner_profile_id=resolved.learner_profile_id,
        ):
            raise AssertionError("refunded entitlement still allows paid access")
        if identity_service.resolve_session(session.token).learner_profile_id != resolved.learner_profile_id:
            raise AssertionError("refund corrupted account/session continuity")

        payment_conn.close()
        payment_conn = payment_connection(payment_db)
        durable_store = PaymentStore(payment_conn)
        durable_payment, _ = build_payment_boundary(durable_store)
        durable_entitlement = durable_payment.entitlement(
            order_id=FIXED_ORDER,
            learner_profile_id=resolved.learner_profile_id,
        )
        if durable_entitlement["state"] != "REVOKED" or durable_entitlement["active"] is not False:
            raise AssertionError("refund revocation was not durable after reconnect")
        payment_conn.close()

    results = {
        "anonymous_to_account_continuity": True,
        "server_owned_session_resolved": True,
        "payment_to_entitlement": True,
        "payment_callback_replay_idempotent": True,
        "provider_neutral_receipt_registered": True,
        "paid_access_allowed_before_learning": True,
        "learning_to_shared_peis": True,
        "shared_peis_replay_idempotent": True,
        "shared_peis_nba_persisted": True,
        "grounded_tutor_text": True,
        "same_session_voice": True,
        "voice_degraded_fallback": True,
        "voice_provider_kill_switch": True,
        "preflight_activation_kill_switch": True,
        "refund_to_durable_revoke": True,
        "same_client_access_denied_after_refund": True,
        "account_session_survives_refund": True,
        "full_simulated_chain": True,
        "private_staging_live_evidence": False,
        "learner_audio_persisted_bytes": 0,
        "outbound_provider_requests": 0,
        "real_charges": 0,
        "real_refunds": 0,
        "real_email_sms_deliveries": 0,
        "real_production_peis_writes": 0,
    }
    return build_evidence(candidate_sha, results)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha", default=os.environ.get("GITHUB_SHA", DEFAULT_SHA))
    parser.add_argument("--peis-dsn", default=os.environ.get("PEIS_DATABASE_DSN"))
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    if not isinstance(args.peis_dsn, str) or not args.peis_dsn:
        raise SystemExit("--peis-dsn or PEIS_DATABASE_DSN is required")
    candidate_sha = str(args.candidate_sha).lower()
    if len(candidate_sha) != 40 or any(ch not in "0123456789abcdef" for ch in candidate_sha):
        raise SystemExit("candidate sha must be full 40-char hexadecimal")
    evidence = run(peis_dsn=args.peis_dsn, candidate_sha=candidate_sha)
    if args.emit:
        print(json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("SEP1_FULL_PRODUCTION_CANDIDATE_SMOKE=PASS")
        print(f"EVIDENCE_SHA256={canonical_sha256(evidence)}")
        print("EVIDENCE_CLASS=CI_SIMULATED_CONTRACT_EVIDENCE")
        print("OUTBOUND_PROVIDER_REQUESTS=0")
        print("REAL_CHARGES=0")
        print("REAL_REFUNDS=0")
        print("REAL_EMAIL_SMS_DELIVERIES=0")
        print("REAL_PRODUCTION_PEIS_WRITES=0")
        print("LEARNER_AUDIO_PERSISTED_BYTES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
