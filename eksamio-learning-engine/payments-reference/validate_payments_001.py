#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from payments import (  # noqa: E402
    FiscalItemPolicy,
    InvalidPaymentRequest,
    InvalidPaymentSignature,
    Offer,
    OfferCatalog,
    PaymentAmountMismatch,
    PaymentStore,
    ProPaymentService,
    RobokassaTestAdapter,
    UnsafePaymentMode,
)


def expect(exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def build_service():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    store = PaymentStore(connection)
    catalog = OfferCatalog(
        [
            Offer(
                code="RU_PRO_30_TEST",
                product_code="EKSAMIO_PRO_RUSSIAN",
                duration_days=30,
                amount_kopecks=12300,
                title_ru="Eksamio Pro — Русский — 30 дней (sandbox)",
            ),
            Offer(
                code="RU_PRO_90_TEST",
                product_code="EKSAMIO_PRO_RUSSIAN",
                duration_days=90,
                amount_kopecks=32100,
                title_ru="Eksamio Pro — Русский — 90 дней (sandbox)",
            ),
        ]
    )
    provider = RobokassaTestAdapter(
        merchant_login="eksamio-test-merchant",
        test_password1="TEST_PASSWORD_ONE_NOT_REAL",
        test_password2="TEST_PASSWORD_TWO_NOT_REAL",
        is_test=True,
        hash_name="md5",
    )
    fiscal_policy = FiscalItemPolicy(
        tax="none",
        payment_method="full_payment",
        payment_object="service",
    )
    clock = [1_800_000_000]
    order_ids = iter(["ord:test-30", "ord:test-90", "ord:test-retry"])
    inv_ids = iter([700001, 700002, 700003])
    service = ProPaymentService(
        store=store,
        catalog=catalog,
        provider=provider,
        fiscal_policy=fiscal_policy,
        now_provider=lambda: clock[0],
        order_id_factory=lambda: next(order_ids),
        inv_id_factory=lambda: next(inv_ids),
    )
    return connection, store, catalog, provider, service, clock


def validate_fail_closed() -> None:
    expect(
        UnsafePaymentMode,
        RobokassaTestAdapter,
        merchant_login="merchant",
        test_password1="one",
        test_password2="two",
        is_test=False,
    )


def validate_initiation_signature(provider, initiation, catalog) -> None:
    fields = initiation.form_fields
    assert initiation.test_mode is True
    assert fields["IsTest"] == "1"
    assert fields["IncCurrLabel"] == initiation.payment_method
    assert fields["PaymentMethods"] == initiation.payment_method
    assert fields["OutSum"] == "123.00"
    assert "Token" not in fields
    assert "Recurring" not in fields
    assert "StepByStep" not in fields
    offer = catalog.get(initiation.offer_code)
    receipt = fields["Receipt"]
    base = f"eksamio-test-merchant:123.00:{initiation.inv_id}:{receipt}:TEST_PASSWORD_ONE_NOT_REAL"
    assert fields["SignatureValue"] == hashlib.md5(base.encode("utf-8")).hexdigest()
    assert offer.duration_days == 30


def main() -> None:
    validate_fail_closed()
    connection, store, catalog, provider, service, clock = build_service()

    # Browser cannot assert amount, identity, duration, learner profile, or entitlement.
    expect(
        InvalidPaymentRequest,
        service.create_order,
        {"offer_code": "RU_PRO_30_TEST", "payment_method": "BankCard", "amount_kopecks": 1},
        user_identity_ref="user:test-1",
        learner_profile_id="learner:test-1",
    )

    first = service.create_order(
        {"offer_code": "RU_PRO_30_TEST", "payment_method": "BankCard"},
        user_identity_ref="user:test-1",
        learner_profile_id="learner:test-1",
    )
    validate_initiation_signature(provider, first, catalog)
    first_row = store.order(order_id=first.order_id)
    assert first_row is not None
    assert first_row["status"] == "PENDING"
    assert first_row["receipt_status"] == "REQUEST_PREPARED"
    assert first_row["attempt_count"] == 1

    # Invalid signature and wrong amount cannot mutate entitlement state.
    tampered = {
        "OutSum": "123.000000",
        "InvId": str(first.inv_id),
        "SignatureValue": "0" * 32,
        "PaymentMethod": "BankCard",
    }
    expect(InvalidPaymentSignature, service.result_url, tampered)
    assert store.entitlement_for_order(first.order_id) is None
    wrong_amount_text = "124.000000"
    wrong_amount = {
        "OutSum": wrong_amount_text,
        "InvId": str(first.inv_id),
        "SignatureValue": provider.sign_test_result(out_sum_text=wrong_amount_text, inv_id=first.inv_id),
        "PaymentMethod": "BankCard",
    }
    expect(PaymentAmountMismatch, service.result_url, wrong_amount)
    assert store.entitlement_for_order(first.order_id) is None

    # Correct ResultURL grants exactly one 30-day entitlement.
    paid_text = "123.000000"
    paid = {
        "OutSum": paid_text,
        "InvId": str(first.inv_id),
        "SignatureValue": provider.sign_test_result(out_sum_text=paid_text, inv_id=first.inv_id),
        "PaymentMethod": "BankCard",
        "OpKey": "sandbox-op-bankcard-1",
    }
    result = service.result_url(paid)
    assert result.acknowledgement == f"OK{first.inv_id}"
    assert result.status == "PAID"
    assert result.receipt_status == "AWAITING_PROVIDER_FISCALIZATION"
    assert result.entitlement.replay is False
    assert result.entitlement.expires_at_epoch - result.entitlement.starts_at_epoch == 30 * 86400

    replay = service.result_url(paid)
    assert replay.entitlement.replay is True
    assert replay.entitlement.entitlement_id == result.entitlement.entitlement_id
    assert replay.entitlement.expires_at_epoch == result.entitlement.expires_at_epoch
    assert connection.execute("SELECT COUNT(*) FROM pro_entitlements WHERE order_id = ?", (first.order_id,)).fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM pro_payment_events WHERE event_kind = 'PAID' AND order_id = ?", (first.order_id,)).fetchone()[0] == 1

    service.record_receipt(first.order_id, status="REGISTERED", provider_receipt_ref="sandbox-receipt-1")
    first_row = store.order(order_id=first.order_id)
    assert first_row["receipt_status"] == "REGISTERED"
    assert first_row["provider_receipt_ref"] == "sandbox-receipt-1"

    # 90-day SBP path is independent and uses the same exactly-once gate.
    second = service.create_order(
        {"offer_code": "RU_PRO_90_TEST", "payment_method": "SBP"},
        user_identity_ref="user:test-2",
        learner_profile_id="learner:test-2",
    )
    assert second.form_fields["IsTest"] == "1"
    assert second.form_fields["IncCurrLabel"] == "SBP"
    assert second.form_fields["OutSum"] == "321.00"
    second_paid_text = "321.00"
    second_result = service.result_url(
        {
            "OutSum": second_paid_text,
            "InvId": str(second.inv_id),
            "SignatureValue": provider.sign_test_result(out_sum_text=second_paid_text, inv_id=second.inv_id),
            "PaymentMethod": "SBP",
            "OpKey": "sandbox-op-sbp-1",
        }
    )
    assert second_result.entitlement.expires_at_epoch - second_result.entitlement.starts_at_epoch == 90 * 86400

    # Provider-confirmed refund deterministically revokes access and is idempotent.
    clock[0] += 100
    assert service.refund_confirmed(second.order_id, provider_ref="sandbox-refund-1") is True
    assert service.refund_confirmed(second.order_id, provider_ref="sandbox-refund-1") is False
    second_row = store.order(order_id=second.order_id)
    second_entitlement = store.entitlement_for_order(second.order_id)
    assert second_row["status"] == "REFUNDED"
    assert second_row["receipt_status"] == "REFUNDED"
    assert second_entitlement["state"] == "REVOKED"
    assert second_entitlement["revoke_reason"] == "PAYMENT_REFUNDED"

    # Failure -> retry does not grant access and reuses server-owned order facts.
    third = service.create_order(
        {"offer_code": "RU_PRO_30_TEST", "payment_method": "BankCard"},
        user_identity_ref="user:test-3",
        learner_profile_id="learner:test-3",
    )
    assert service.mark_failure(third.order_id, provider_reason_code="sandbox_declined") is True
    assert store.order(order_id=third.order_id)["status"] == "FAILED"
    assert store.entitlement_for_order(third.order_id) is None
    retry = service.retry(third.order_id)
    assert retry.order_id == third.order_id
    assert retry.inv_id == third.inv_id
    third_row = store.order(order_id=third.order_id)
    assert third_row["status"] == "PENDING"
    assert third_row["attempt_count"] == 2

    # Repository/test adapter must not persist secrets or expose recurring/card-token fields.
    persisted = "\n".join(
        str(tuple(row))
        for table in ("pro_payment_orders", "pro_payment_events", "pro_entitlements")
        for row in connection.execute(f"SELECT * FROM {table}").fetchall()
    )
    assert "TEST_PASSWORD_ONE_NOT_REAL" not in persisted
    assert "TEST_PASSWORD_TWO_NOT_REAL" not in persisted

    print("SEP1_PAYMENTS_001_VALIDATION=PASS")
    print("provider=ROBOKASSA_TEST_ONLY")
    print("methods=BankCard,SBP")
    print("offers=30d,90d_runtime_priced")
    print("result_url_signature=PASS")
    print("amount_inv_id_server_match=PASS")
    print("exactly_once_entitlement=PASS")
    print("receipt_state=PASS")
    print("failure_retry=PASS")
    print("refund_revoke=PASS")
    print("production_charge_capability=0")


if __name__ == "__main__":
    main()
