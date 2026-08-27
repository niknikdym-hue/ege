#!/usr/bin/env python3
from __future__ import annotations

import sqlite3

from payments import (
    FiscalItemPolicy,
    InvalidPaymentSignature,
    InvalidProviderNotification,
    Offer,
    PaymentAmountMismatch,
    PaymentStore,
    UnsafePaymentMode,
)
from robokassa_production import (
    ProductionAdmission,
    RobokassaAdapter,
    RobokassaCredentialSet,
    RobokassaMode,
)


def expect(exc_type: type[BaseException], fn) -> None:
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def main() -> int:
    offer = Offer(
        code="sep1-local-30d",
        product_code="eksamio-pro-russian",
        duration_days=30,
        amount_kopecks=12345,
        title_ru="Eksamio Pro — Русский — 30 дней",
    )
    fiscal = FiscalItemPolicy(tax="fixture_tax", payment_method="fixture_method", payment_object="fixture_object")
    test_credentials = RobokassaCredentialSet(
        merchant_login="eksamio-fixture",
        password1="TEST_PASSWORD_ONE_ONLY_FOR_LOCAL_VALIDATION",
        password2="TEST_PASSWORD_TWO_ONLY_FOR_LOCAL_VALIDATION",
    )
    production_credentials = RobokassaCredentialSet(
        merchant_login="eksamio-fixture",
        password1="PROD_PASSWORD_ONE_ONLY_FOR_LOCAL_VALIDATION",
        password2="PROD_PASSWORD_TWO_ONLY_FOR_LOCAL_VALIDATION",
    )

    expect(
        UnsafePaymentMode,
        lambda: RobokassaAdapter(
            mode=RobokassaMode.PRODUCTION_CANDIDATE,
            credentials=production_credentials,
            fiscal_policy=fiscal,
            admission=ProductionAdmission(),
        ),
    )

    test_adapter = RobokassaAdapter(
        mode=RobokassaMode.TEST,
        credentials=test_credentials,
        fiscal_policy=fiscal,
    )
    prod_adapter = RobokassaAdapter(
        mode=RobokassaMode.PRODUCTION_CANDIDATE,
        credentials=production_credentials,
        fiscal_policy=fiscal,
        admission=ProductionAdmission(
            enabled=True,
            fiscal_policy_admitted=True,
            npd_fns_accepted=True,
            robocheki_accepted=True,
        ),
    )

    test_fields = dict(test_adapter.build_initiation(inv_id=7001, offer=offer, payment_method="SBP"))
    prod_fields = dict(prod_adapter.build_initiation(inv_id=7001, offer=offer, payment_method="SBP"))
    assert test_fields["IsTest"] == "1"
    assert "IsTest" not in prod_fields
    assert test_fields["SignatureValue"] != prod_fields["SignatureValue"]
    assert test_fields["PaymentMethods"] == "SBP"
    assert prod_fields["PaymentMethods"] == "SBP"
    assert not ({"Token", "Recurring", "StepByStep"} & set(prod_fields))

    secret_values = {
        test_credentials.password1,
        test_credentials.password2,
        production_credentials.password1,
        production_credentials.password2,
    }
    exposed = "\n".join((repr(test_credentials), repr(production_credentials), repr(prod_adapter), repr(prod_fields)))
    assert not any(secret in exposed for secret in secret_values)

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    store = PaymentStore(connection)
    store.create_order(
        order_id="order:prod-local-1",
        inv_id=7001,
        user_identity_ref="user:fixture",
        learner_profile_id="learner:fixture",
        offer=offer,
        payment_method="SBP",
        now=1_780_000_000,
    )
    store.mark_initiated("order:prod-local-1", now=1_780_000_001)

    out_sum = "123.45"
    signature = prod_adapter.sign_result_for_local_validation(out_sum_text=out_sum, inv_id=7001)
    payload = {
        "OutSum": out_sum,
        "InvId": "7001",
        "SignatureValue": signature,
        "PaymentMethod": "SBP",
        "OpKey": "provider-fixture-7001",
    }
    first = prod_adapter.process_result_url(payload, store=store, now=1_780_000_010)
    second = prod_adapter.process_result_url(payload, store=store, now=1_780_000_011)
    assert first.acknowledgement == "OK7001"
    assert first.entitlement.replay is False
    assert second.entitlement.replay is True
    assert first.entitlement.entitlement_id == second.entitlement.entitlement_id

    bad_signature = dict(payload)
    bad_signature["SignatureValue"] = "0" * len(signature)
    expect(InvalidPaymentSignature, lambda: prod_adapter.process_result_url(bad_signature, store=store, now=1_780_000_012))

    bad_amount = dict(payload)
    bad_amount["OutSum"] = "123.46"
    bad_amount["SignatureValue"] = prod_adapter.sign_result_for_local_validation(out_sum_text="123.46", inv_id=7001)
    expect(PaymentAmountMismatch, lambda: prod_adapter.process_result_url(bad_amount, store=store, now=1_780_000_013))

    bad_inv = dict(payload)
    bad_inv["InvId"] = "7002"
    bad_inv["SignatureValue"] = prod_adapter.sign_result_for_local_validation(out_sum_text=out_sum, inv_id=7002)
    expect(InvalidProviderNotification, lambda: prod_adapter.process_result_url(bad_inv, store=store, now=1_780_000_014))

    assert store.order(order_id="order:prod-local-1")["status"] == "PAID"
    store.update_receipt_status(
        "order:prod-local-1",
        status="REGISTERED",
        provider_receipt_ref="receipt-fixture",
        now=1_780_000_020,
    )
    assert store.order(order_id="order:prod-local-1")["receipt_status"] == "REGISTERED"
    assert store.refund_confirmed(
        "order:prod-local-1",
        provider_ref="refund-fixture",
        payload_sha256="a" * 64,
        now=1_780_000_030,
    ) is True
    assert store.entitlement_for_order("order:prod-local-1")["state"] == "REVOKED"

    print("SEP1_ROBOKASSA_PRODUCTION_ADMISSION=PASS")
    print("production_disabled_by_default=PASS")
    print("production_initiation_omits_IsTest=PASS")
    print("test_initiation_IsTest_1=PASS")
    print("credentials_isolated_and_redacted=PASS")
    print("resulturl_amount_inv_signature=PASS")
    print("exactly_once_entitlement=PASS")
    print("receipt_refund_revoke=PASS")
    print("outbound_provider_requests=0")
    print("real_charges=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
