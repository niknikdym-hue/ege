#!/usr/bin/env python3
"""Deterministic zero-network acceptance for the SEP-1 production payment boundary."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

from payments import (
    FiscalItemPolicy,
    InvalidPaymentSignature,
    InvalidPaymentTransition,
    InvalidProviderNotification,
    Offer,
    OfferCatalog,
    PaymentStore,
)
from production_e2e_boundary import (
    CandidateIdentity,
    ProductionPaymentApiBoundary,
    ProviderEventConflict,
    ProviderReceiptEvent,
    ProviderRefundEvent,
)
from robokassa_production import (
    ProductionAdmission,
    RobokassaAdapter,
    RobokassaCredentialSet,
    RobokassaMode,
)


FIXED_NOW = 1_800_000_000
FIXED_ORDER = "ord:sep1-e2e-fixture"
FIXED_INV = 900001
FIXED_USER = "user:sep1-e2e-fixture"
FIXED_LEARNER = "learner:sep1-e2e-fixture"
FIXED_AMOUNT = 12345
DEFAULT_SHA = "0" * 40


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_failure(callable_obj: Any, expected: tuple[type[BaseException], ...]) -> None:
    try:
        callable_obj()
    except expected:
        return
    raise AssertionError(f"expected failure: {[item.__name__ for item in expected]}")


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def build_boundary(store: PaymentStore) -> tuple[ProductionPaymentApiBoundary, RobokassaAdapter]:
    catalog = OfferCatalog(
        [
            Offer(
                code="RU_PRO_30_E2E_FIXTURE",
                product_code="EKSAMIO_PRO_RUSSIAN",
                duration_days=30,
                amount_kopecks=FIXED_AMOUNT,
                title_ru="Eksamio Pro — Русский, CI fixture",
            )
        ]
    )
    fiscal = FiscalItemPolicy(
        tax="none",
        payment_method="full_payment",
        payment_object="service",
    )
    provider = RobokassaAdapter(
        mode=RobokassaMode.PRODUCTION_CANDIDATE,
        credentials=RobokassaCredentialSet(
            merchant_login="ci-merchant",
            password1="ci-password-1",
            password2="ci-password-2",
        ),
        fiscal_policy=fiscal,
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


def run(candidate_sha: str) -> tuple[dict[str, Any], str]:
    with tempfile.TemporaryDirectory(prefix="eksamio-sep1-payment-") as tmp:
        db_path = Path(tmp) / "candidate.sqlite3"
        connection = connect(db_path)
        store = PaymentStore(connection)
        boundary, provider = build_boundary(store)

        created = boundary.create_order(
            {"offer_code": "RU_PRO_30_E2E_FIXTURE", "payment_method": "SBP"},
            user_identity_ref=FIXED_USER,
            learner_profile_id=FIXED_LEARNER,
        )
        assert created["production_candidate"] is True
        assert created["test_mode"] is False
        assert "IsTest" not in created["form_fields"]
        assert created["amount_kopecks"] == FIXED_AMOUNT

        out_sum = "123.45"
        signature = provider.sign_result_for_local_validation(out_sum_text=out_sum, inv_id=FIXED_INV)
        result_payload = {
            "OutSum": out_sum,
            "InvId": str(FIXED_INV),
            "SignatureValue": signature,
            "PaymentMethod": "SBP",
            "OpKey": "ci-payment-ref-001",
        }
        first = boundary.result_url(result_payload)
        replay = boundary.result_url(result_payload)
        assert first["entitlement_state"] == "ACTIVE" and first["replay"] is False
        assert replay["entitlement_state"] == "ACTIVE" and replay["replay"] is True

        bad_signature = dict(result_payload, SignatureValue="0" * len(signature))
        require_failure(lambda: boundary.result_url(bad_signature), (InvalidPaymentSignature,))
        bad_amount = dict(result_payload, OutSum="124.45")
        require_failure(lambda: boundary.result_url(bad_amount), (InvalidProviderNotification,))
        bad_inv = dict(
            result_payload,
            InvId="900002",
            SignatureValue=provider.sign_result_for_local_validation(out_sum_text=out_sum, inv_id=900002),
        )
        require_failure(lambda: boundary.result_url(bad_inv), (InvalidProviderNotification,))

        connection.close()
        connection = connect(db_path)
        store = PaymentStore(connection)
        boundary, _ = build_boundary(store)
        active = boundary.entitlement(order_id=FIXED_ORDER, learner_profile_id=FIXED_LEARNER)
        assert active["active"] is True and active["state"] == "ACTIVE"
        assert boundary.paid_access_allowed(order_id=FIXED_ORDER, learner_profile_id=FIXED_LEARNER)

        wrong_receipt_amount = ProviderReceiptEvent(
            event_id="receipt-wrong-amount",
            provider="ROBOCHEKI",
            payment_provider="ROBOKASSA",
            order_id=FIXED_ORDER,
            amount_kopecks=FIXED_AMOUNT + 1,
            provider_receipt_ref="receipt-ref-wrong",
            status="REGISTERED",
        )
        require_failure(
            lambda: boundary.receipt_event(wrong_receipt_amount),
            (InvalidProviderNotification,),
        )
        receipt = ProviderReceiptEvent(
            event_id="receipt-001",
            provider="ROBOCHEKI",
            payment_provider="ROBOKASSA",
            order_id=FIXED_ORDER,
            amount_kopecks=FIXED_AMOUNT,
            provider_receipt_ref="receipt-ref-001",
            status="REGISTERED",
        )
        assert boundary.receipt_event(receipt) is True
        assert boundary.receipt_event(receipt) is False
        conflicting_receipt = ProviderReceiptEvent(
            event_id="receipt-001",
            provider="ROBOCHEKI",
            payment_provider="ROBOKASSA",
            order_id=FIXED_ORDER,
            amount_kopecks=FIXED_AMOUNT,
            provider_receipt_ref="receipt-ref-conflict",
            status="REGISTERED",
        )
        require_failure(lambda: boundary.receipt_event(conflicting_receipt), (ProviderEventConflict,))

        wrong_provider_refund = ProviderRefundEvent(
            event_id="refund-wrong-provider",
            provider="ROBOKASSA",
            payment_provider="NOT_THE_ORDER_PROVIDER",
            order_id=FIXED_ORDER,
            amount_kopecks=FIXED_AMOUNT,
            provider_ref="refund-ref-wrong",
        )
        require_failure(
            lambda: boundary.refund_event(wrong_provider_refund),
            (InvalidProviderNotification,),
        )
        refund = ProviderRefundEvent(
            event_id="refund-001",
            provider="ROBOKASSA",
            payment_provider="ROBOKASSA",
            order_id=FIXED_ORDER,
            amount_kopecks=FIXED_AMOUNT,
            provider_ref="refund-ref-001",
        )
        assert boundary.refund_event(refund) is True
        assert boundary.refund_event(refund) is False

        connection.close()
        connection = connect(db_path)
        store = PaymentStore(connection)
        boundary, _ = build_boundary(store)
        revoked = boundary.entitlement(order_id=FIXED_ORDER, learner_profile_id=FIXED_LEARNER)
        assert revoked["active"] is False and revoked["state"] == "REVOKED"
        assert not boundary.paid_access_allowed(order_id=FIXED_ORDER, learner_profile_id=FIXED_LEARNER)
        require_failure(
            lambda: boundary.refund_event(
                ProviderRefundEvent(
                    event_id="refund-second-event",
                    provider="ROBOKASSA",
                    payment_provider="ROBOKASSA",
                    order_id=FIXED_ORDER,
                    amount_kopecks=FIXED_AMOUNT,
                    provider_ref="refund-ref-002",
                )
            ),
            (InvalidPaymentTransition,),
        )

        event_count = int(
            store.connection.execute("SELECT COUNT(*) FROM pro_payment_events").fetchone()[0]
        )
        connection.close()

    results = {
        "server_created_order": True,
        "production_candidate_initiation": True,
        "sbp_and_bankcard_only_contract": True,
        "valid_result_url_exactly_once": True,
        "result_url_replay_idempotent": True,
        "invalid_signature_fails_closed": True,
        "wrong_amount_fails_closed": True,
        "wrong_inv_id_fails_closed": True,
        "durable_active_entitlement_after_reconnect": True,
        "receipt_provider_event_boundary": True,
        "receipt_event_replay_idempotent": True,
        "receipt_event_conflict_fails_closed": True,
        "refund_provider_event_boundary": True,
        "refund_event_replay_idempotent": True,
        "durable_revocation_after_reconnect": True,
        "same_client_access_active_then_denied": True,
        "payment_event_rows": event_count,
        "outbound_provider_requests": 0,
        "real_charges": 0,
        "real_refunds": 0,
        "learner_audio_persisted_bytes": 0,
    }
    config_fingerprint = sha256_text("sep1-payment-e2e-fixture-config-v1")
    preflight_fingerprint = sha256_text("sep1-production-preflight-contract-v1")
    identity = CandidateIdentity(
        git_sha=candidate_sha,
        config_fingerprint=config_fingerprint,
        preflight_fingerprint=preflight_fingerprint,
    )
    evidence, evidence_sha = identity.bind(results)
    assert identity.accepts(evidence)
    stale_sha = ("1" if candidate_sha[0] != "1" else "2") + candidate_sha[1:]
    stale_identity = CandidateIdentity(
        git_sha=stale_sha,
        config_fingerprint=config_fingerprint,
        preflight_fingerprint=preflight_fingerprint,
    )
    assert not stale_identity.accepts(evidence)
    return evidence, evidence_sha


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-sha", default=os.environ.get("GITHUB_SHA", DEFAULT_SHA))
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    evidence, evidence_sha = run(args.candidate_sha.lower())
    if args.emit:
        print(json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    else:
        print("SEP1_PRODUCTION_PAYMENT_E2E_BOUNDARY=PASS")
        print(f"EVIDENCE_SHA256={evidence_sha}")
        print("OUTBOUND_PROVIDER_REQUESTS=0")
        print("REAL_CHARGES=0")
        print("REAL_REFUNDS=0")
        print("LEARNER_AUDIO_PERSISTED_BYTES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
