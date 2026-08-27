#!/usr/bin/env python3
"""Fail-closed Robokassa production-candidate adapter for Eksamio Pro.

This module adds production-shaped request/signature handling without performing
network I/O. Construction of a production candidate is impossible unless the
runtime explicitly enables it and external fiscal/NPD/Robocheki admission has
already been recorded by the caller.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Any, Mapping
from urllib.parse import quote

from payments import (
    EntitlementGrant,
    FiscalItemPolicy,
    InvalidPaymentMethod,
    InvalidPaymentSignature,
    InvalidProviderNotification,
    Offer,
    PaymentAmountMismatch,
    PaymentStore,
    UnsafePaymentMode,
)


class RobokassaMode(str, Enum):
    TEST = "TEST"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"


@dataclass(frozen=True)
class RobokassaCredentialSet:
    merchant_login: str
    password1: str = field(repr=False)
    password2: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.merchant_login or not self.password1 or not self.password2:
            raise ValueError("merchant login and Password #1/#2 are required")
        if self.password1 == self.password2:
            raise ValueError("Password #1 and Password #2 must be distinct")


@dataclass(frozen=True)
class ProductionAdmission:
    enabled: bool = False
    fiscal_policy_admitted: bool = False
    npd_fns_accepted: bool = False
    robocheki_accepted: bool = False

    @property
    def ready(self) -> bool:
        return all(
            (
                self.enabled,
                self.fiscal_policy_admitted,
                self.npd_fns_accepted,
                self.robocheki_accepted,
            )
        )


@dataclass(frozen=True)
class ProcessedResult:
    acknowledgement: str
    payment_method: str
    provider_ref: str
    entitlement: EntitlementGrant


class RobokassaAdapter:
    """Build/verify TEST or explicitly enabled PRODUCTION_CANDIDATE messages.

    The adapter never sends requests itself. Secrets are held only in private
    fields and are excluded from representations and returned form fields.
    """

    ACTION_URL = "https://auth.robokassa.ru/Merchant/Payment/Index"
    ALLOWED_METHODS = {"BankCard", "SBP"}
    FORBIDDEN_FIELDS = {"Token", "Recurring", "StepByStep"}

    def __init__(
        self,
        *,
        mode: RobokassaMode,
        credentials: RobokassaCredentialSet,
        fiscal_policy: FiscalItemPolicy,
        admission: ProductionAdmission | None = None,
        hash_name: str = "md5",
    ) -> None:
        if hash_name.lower() not in hashlib.algorithms_available:
            raise ValueError("unsupported signature hash")
        if mode is RobokassaMode.PRODUCTION_CANDIDATE:
            if admission is None or not admission.ready:
                raise UnsafePaymentMode(
                    "production candidate requires explicit enable plus fiscal/NPD/Robocheki admission"
                )
        self.mode = mode
        self.merchant_login = credentials.merchant_login
        self._password1 = credentials.password1
        self._password2 = credentials.password2
        self.fiscal_policy = fiscal_policy
        self.admission = admission
        self.hash_name = hash_name.lower()

    def __repr__(self) -> str:
        return (
            f"RobokassaAdapter(mode={self.mode.value!r}, merchant_login={self.merchant_login!r}, "
            f"hash_name={self.hash_name!r}, secrets='<redacted>')"
        )

    def _digest(self, value: str) -> str:
        return hashlib.new(self.hash_name, value.encode("utf-8")).hexdigest()

    @staticmethod
    def _amount_text(amount_kopecks: int) -> str:
        return f"{Decimal(amount_kopecks) / Decimal(100):.2f}"

    def build_receipt(self, *, offer: Offer) -> str:
        receipt = {
            "items": [
                {
                    "name": offer.title_ru,
                    "quantity": 1,
                    "sum": float(Decimal(offer.amount_kopecks) / Decimal(100)),
                    "tax": self.fiscal_policy.tax,
                    "payment_method": self.fiscal_policy.payment_method,
                    "payment_object": self.fiscal_policy.payment_object,
                }
            ]
        }
        raw = json.dumps(receipt, ensure_ascii=False, separators=(",", ":"))
        return quote(raw, safe="")

    def build_initiation(
        self,
        *,
        inv_id: int,
        offer: Offer,
        payment_method: str,
    ) -> Mapping[str, str]:
        if payment_method not in self.ALLOWED_METHODS:
            raise InvalidPaymentMethod("only BankCard and SBP are admitted at launch")
        if self.mode is RobokassaMode.PRODUCTION_CANDIDATE and (
            self.admission is None or not self.admission.ready
        ):
            raise UnsafePaymentMode("production candidate admission was revoked/not supplied")

        out_sum = self._amount_text(offer.amount_kopecks)
        receipt = self.build_receipt(offer=offer)
        signature = self._digest(
            f"{self.merchant_login}:{out_sum}:{inv_id}:{receipt}:{self._password1}"
        )
        fields: dict[str, str] = {
            "MerchantLogin": self.merchant_login,
            "OutSum": out_sum,
            "InvId": str(inv_id),
            "Description": offer.title_ru,
            "Receipt": receipt,
            "SignatureValue": signature,
            "IncCurrLabel": payment_method,
            "PaymentMethods": payment_method,
            "Culture": "ru",
        }
        if self.mode is RobokassaMode.TEST:
            fields["IsTest"] = "1"
        elif "IsTest" in fields:
            raise UnsafePaymentMode("production initiation must omit IsTest")

        if self.FORBIDDEN_FIELDS & set(fields):
            raise UnsafePaymentMode("saved-card/recurring/step-by-step parameters are forbidden")
        return fields

    def verify_result_url(
        self,
        payload: Mapping[str, Any],
        *,
        expected_inv_id: int,
        expected_amount_kopecks: int,
    ) -> tuple[str, str]:
        required = {"OutSum", "InvId", "SignatureValue"}
        if not isinstance(payload, Mapping) or not required <= set(payload):
            raise InvalidProviderNotification("ResultURL payload is incomplete")

        out_sum_raw = str(payload["OutSum"])
        inv_id_raw = str(payload["InvId"])
        signature = str(payload["SignatureValue"])
        try:
            inv_id = int(inv_id_raw)
        except ValueError as exc:
            raise InvalidProviderNotification("InvId must be numeric") from exc
        if inv_id != expected_inv_id:
            raise InvalidProviderNotification("InvId does not match server-owned order")

        try:
            amount = Decimal(out_sum_raw).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except InvalidOperation as exc:
            raise InvalidProviderNotification("OutSum is invalid") from exc
        expected_amount = (Decimal(expected_amount_kopecks) / Decimal(100)).quantize(Decimal("0.01"))
        if amount != expected_amount:
            raise PaymentAmountMismatch("OutSum does not match server-owned order")

        expected_signature = self._digest(f"{out_sum_raw}:{inv_id_raw}:{self._password2}")
        if not hmac.compare_digest(signature.casefold(), expected_signature.casefold()):
            raise InvalidPaymentSignature("ResultURL signature mismatch")

        payment_method = str(payload.get("PaymentMethod") or payload.get("IncCurrLabel") or "UNKNOWN")
        if payment_method != "UNKNOWN" and payment_method not in self.ALLOWED_METHODS:
            raise InvalidProviderNotification("unexpected payment method")
        provider_ref = str(payload.get("OpKey") or payload.get("PaymentId") or f"result:{inv_id}")
        return payment_method, provider_ref

    def sign_result_for_local_validation(self, *, out_sum_text: str, inv_id: int) -> str:
        """Return a digest only; useful for deterministic zero-network acceptance tests."""
        return self._digest(f"{out_sum_text}:{inv_id}:{self._password2}")

    def process_result_url(self, payload: Mapping[str, Any], *, store: PaymentStore, now: int) -> ProcessedResult:
        try:
            inv_id = int(str(payload.get("InvId", "")))
        except ValueError as exc:
            raise InvalidProviderNotification("InvId must be numeric") from exc
        order = store.order(inv_id=inv_id)
        if order is None:
            raise InvalidProviderNotification("unknown InvId")

        payment_method, provider_ref = self.verify_result_url(
            payload,
            expected_inv_id=inv_id,
            expected_amount_kopecks=int(order["amount_kopecks"]),
        )
        payload_hash = hashlib.sha256(
            json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        entitlement = store.grant_paid_exactly_once(
            inv_id=inv_id,
            provider_payment_ref=provider_ref,
            payload_sha256=payload_hash,
            now=now,
        )
        return ProcessedResult(
            acknowledgement=f"OK{inv_id}",
            payment_method=payment_method,
            provider_ref=provider_ref,
            entitlement=entitlement,
        )
