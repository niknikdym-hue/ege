#!/usr/bin/env python3
"""Eksamio Pro bounded payment/entitlement reference.

This module implements a non-production vertical slice for Robokassa test mode.
It deliberately does not perform outbound network requests and cannot silently
fall back to production payments. The browser may choose only an admitted offer
and a payment method; amount, duration, identity, entitlement and receipt state
remain server-owned.

Production merchant credentials, fiscal settings and NPD/FNS admission are
external launch gates and are not represented as repository defaults.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Callable, Mapping
from urllib.parse import quote


class PaymentError(ValueError):
    """Base class for bounded payment failures."""


class InvalidPaymentRequest(PaymentError):
    pass


class UnsafePaymentMode(PaymentError):
    pass


class UnknownOffer(PaymentError):
    pass


class InvalidPaymentMethod(PaymentError):
    pass


class InvalidProviderNotification(PaymentError):
    pass


class InvalidPaymentSignature(InvalidProviderNotification):
    pass


class PaymentAmountMismatch(InvalidProviderNotification):
    pass


class InvalidPaymentTransition(PaymentError):
    pass


class MissingFiscalConfiguration(PaymentError):
    pass


@dataclass(frozen=True)
class Offer:
    code: str
    product_code: str
    duration_days: int
    amount_kopecks: int
    title_ru: str

    def __post_init__(self) -> None:
        if not self.code or not self.product_code or not self.title_ru:
            raise ValueError("offer identifiers/title must be non-empty")
        if self.duration_days not in {30, 90}:
            raise ValueError("launch offers must be 30 or 90 days")
        if self.amount_kopecks <= 0:
            raise ValueError("offer amount must be positive")


class OfferCatalog:
    """Server-owned launch offer catalog; no production prices are hard-coded here."""

    def __init__(self, offers: list[Offer]) -> None:
        self._offers = {offer.code: offer for offer in offers}
        if len(self._offers) != len(offers) or not self._offers:
            raise ValueError("offer codes must be unique and catalog must not be empty")

    def get(self, code: str) -> Offer:
        try:
            return self._offers[code]
        except KeyError as exc:
            raise UnknownOffer("unknown or inactive offer") from exc


@dataclass(frozen=True)
class FiscalItemPolicy:
    """Runtime fiscal configuration admitted outside the repository.

    Values must match the merchant account/legal configuration. The reference
    intentionally has no default tax classification.
    """

    tax: str
    payment_method: str
    payment_object: str

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value for value in (self.tax, self.payment_method, self.payment_object)):
            raise MissingFiscalConfiguration("tax/payment_method/payment_object must be supplied at runtime")


@dataclass(frozen=True)
class PaymentInitiation:
    order_id: str
    inv_id: int
    offer_code: str
    payment_method: str
    amount_kopecks: int
    provider: str
    test_mode: bool
    action_url: str
    form_fields: Mapping[str, str]


@dataclass(frozen=True)
class EntitlementGrant:
    entitlement_id: str
    order_id: str
    learner_profile_id: str
    product_code: str
    starts_at_epoch: int
    expires_at_epoch: int
    state: str
    replay: bool


@dataclass(frozen=True)
class PaymentResult:
    acknowledgement: str
    order_id: str
    status: str
    receipt_status: str
    entitlement: EntitlementGrant


class PaymentStore:
    """Mutable payment state over the repository's existing DB connection style."""

    def __init__(self, connection: Any) -> None:
        self.connection = connection
        self._create_schema()

    def _create_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS pro_payment_orders (
                order_id TEXT PRIMARY KEY,
                inv_id BIGINT NOT NULL UNIQUE,
                user_identity_ref TEXT NOT NULL,
                learner_profile_id TEXT NOT NULL,
                offer_code TEXT NOT NULL,
                product_code TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                amount_kopecks BIGINT NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL,
                receipt_status TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_payment_ref TEXT,
                provider_receipt_ref TEXT,
                attempt_count INTEGER NOT NULL,
                created_at_epoch BIGINT NOT NULL,
                updated_at_epoch BIGINT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS pro_payment_events (
                event_key TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                event_kind TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                created_at_epoch BIGINT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS pro_entitlements (
                entitlement_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL UNIQUE,
                learner_profile_id TEXT NOT NULL,
                product_code TEXT NOT NULL,
                starts_at_epoch BIGINT NOT NULL,
                expires_at_epoch BIGINT NOT NULL,
                state TEXT NOT NULL,
                revoked_at_epoch BIGINT,
                revoke_reason TEXT
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_pro_orders_learner ON pro_payment_orders(learner_profile_id)",
            "CREATE INDEX IF NOT EXISTS idx_pro_entitlements_learner ON pro_entitlements(learner_profile_id)",
        ]
        with self.connection:
            for statement in statements:
                self.connection.execute(statement)

    def create_order(
        self,
        *,
        order_id: str,
        inv_id: int,
        user_identity_ref: str,
        learner_profile_id: str,
        offer: Offer,
        payment_method: str,
        now: int,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO pro_payment_orders(
                    order_id, inv_id, user_identity_ref, learner_profile_id,
                    offer_code, product_code, duration_days, amount_kopecks,
                    payment_method, status, receipt_status, provider,
                    provider_payment_ref, provider_receipt_ref, attempt_count,
                    created_at_epoch, updated_at_epoch
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'CREATED', 'NOT_REQUESTED',
                          'ROBOKASSA', NULL, NULL, 0, ?, ?)
                """,
                (
                    order_id,
                    inv_id,
                    user_identity_ref,
                    learner_profile_id,
                    offer.code,
                    offer.product_code,
                    offer.duration_days,
                    offer.amount_kopecks,
                    payment_method,
                    now,
                    now,
                ),
            )

    def order(self, *, order_id: str | None = None, inv_id: int | None = None) -> Mapping[str, Any] | None:
        if (order_id is None) == (inv_id is None):
            raise ValueError("provide exactly one of order_id or inv_id")
        if order_id is not None:
            return self.connection.execute("SELECT * FROM pro_payment_orders WHERE order_id = ?", (order_id,)).fetchone()
        return self.connection.execute("SELECT * FROM pro_payment_orders WHERE inv_id = ?", (inv_id,)).fetchone()

    def mark_initiated(self, order_id: str, *, now: int) -> None:
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE pro_payment_orders
                SET status = 'PENDING', receipt_status = 'REQUEST_PREPARED',
                    attempt_count = attempt_count + 1, updated_at_epoch = ?
                WHERE order_id = ? AND status IN ('CREATED', 'FAILED')
                """,
                (now, order_id),
            )
        if cursor.rowcount != 1:
            raise InvalidPaymentTransition("only CREATED/FAILED orders may be initiated")

    def mark_failed(self, order_id: str, *, payload_sha256: str, now: int) -> bool:
        event_key = f"failed:{order_id}:{payload_sha256}"
        with self.connection:
            existing = self.connection.execute("SELECT 1 FROM pro_payment_events WHERE event_key = ?", (event_key,)).fetchone()
            if existing is not None:
                return False
            row = self.connection.execute("SELECT status FROM pro_payment_orders WHERE order_id = ?", (order_id,)).fetchone()
            if row is None:
                raise InvalidPaymentTransition("unknown order")
            if row["status"] in {"PAID", "REFUNDED"}:
                raise InvalidPaymentTransition("paid/refunded order cannot become failed")
            self.connection.execute(
                "INSERT INTO pro_payment_events(event_key, order_id, event_kind, payload_sha256, created_at_epoch) VALUES (?, ?, 'FAILED', ?, ?)",
                (event_key, order_id, payload_sha256, now),
            )
            self.connection.execute(
                "UPDATE pro_payment_orders SET status = 'FAILED', updated_at_epoch = ? WHERE order_id = ?",
                (now, order_id),
            )
        return True

    def grant_paid_exactly_once(
        self,
        *,
        inv_id: int,
        provider_payment_ref: str,
        payload_sha256: str,
        now: int,
    ) -> EntitlementGrant:
        event_key = f"paid:{inv_id}"
        with self.connection:
            row = self.connection.execute("SELECT * FROM pro_payment_orders WHERE inv_id = ?", (inv_id,)).fetchone()
            if row is None:
                raise InvalidProviderNotification("unknown InvId")
            if row["status"] == "REFUNDED":
                raise InvalidPaymentTransition("refunded order cannot be paid again")

            entitlement_id = "ent:" + str(row["order_id"])
            existing_event = self.connection.execute(
                "SELECT 1 FROM pro_payment_events WHERE event_key = ?", (event_key,)
            ).fetchone()
            if existing_event is not None or row["status"] == "PAID":
                entitlement = self.connection.execute(
                    "SELECT * FROM pro_entitlements WHERE order_id = ?", (row["order_id"],)
                ).fetchone()
                if entitlement is None:
                    raise InvalidPaymentTransition("paid order is missing entitlement")
                return EntitlementGrant(
                    entitlement_id=str(entitlement["entitlement_id"]),
                    order_id=str(row["order_id"]),
                    learner_profile_id=str(entitlement["learner_profile_id"]),
                    product_code=str(entitlement["product_code"]),
                    starts_at_epoch=int(entitlement["starts_at_epoch"]),
                    expires_at_epoch=int(entitlement["expires_at_epoch"]),
                    state=str(entitlement["state"]),
                    replay=True,
                )

            if row["status"] != "PENDING":
                raise InvalidPaymentTransition("only a PENDING order may become paid")
            starts = now
            expires = now + int(row["duration_days"]) * 24 * 60 * 60
            self.connection.execute(
                "INSERT INTO pro_payment_events(event_key, order_id, event_kind, payload_sha256, created_at_epoch) VALUES (?, ?, 'PAID', ?, ?)",
                (event_key, row["order_id"], payload_sha256, now),
            )
            self.connection.execute(
                """
                INSERT INTO pro_entitlements(
                    entitlement_id, order_id, learner_profile_id, product_code,
                    starts_at_epoch, expires_at_epoch, state, revoked_at_epoch, revoke_reason
                ) VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', NULL, NULL)
                """,
                (entitlement_id, row["order_id"], row["learner_profile_id"], row["product_code"], starts, expires),
            )
            self.connection.execute(
                """
                UPDATE pro_payment_orders
                SET status = 'PAID', receipt_status = 'AWAITING_PROVIDER_FISCALIZATION',
                    provider_payment_ref = ?, updated_at_epoch = ?
                WHERE order_id = ?
                """,
                (provider_payment_ref, now, row["order_id"]),
            )
        return EntitlementGrant(
            entitlement_id=entitlement_id,
            order_id=str(row["order_id"]),
            learner_profile_id=str(row["learner_profile_id"]),
            product_code=str(row["product_code"]),
            starts_at_epoch=starts,
            expires_at_epoch=expires,
            state="ACTIVE",
            replay=False,
        )

    def update_receipt_status(self, order_id: str, *, status: str, provider_receipt_ref: str | None, now: int) -> None:
        allowed = {"AWAITING_PROVIDER_FISCALIZATION", "REGISTERED", "FAILED", "REFUNDED"}
        if status not in allowed:
            raise InvalidPaymentTransition("unsupported receipt status")
        row = self.order(order_id=order_id)
        if row is None or row["status"] not in {"PAID", "REFUNDED"}:
            raise InvalidPaymentTransition("receipt status belongs only to a paid/refunded order")
        with self.connection:
            self.connection.execute(
                "UPDATE pro_payment_orders SET receipt_status = ?, provider_receipt_ref = ?, updated_at_epoch = ? WHERE order_id = ?",
                (status, provider_receipt_ref, now, order_id),
            )

    def refund_confirmed(self, order_id: str, *, provider_ref: str, payload_sha256: str, now: int) -> bool:
        event_key = f"refund:{order_id}:{provider_ref}"
        with self.connection:
            row = self.connection.execute("SELECT * FROM pro_payment_orders WHERE order_id = ?", (order_id,)).fetchone()
            if row is None:
                raise InvalidPaymentTransition("unknown order")
            existing = self.connection.execute("SELECT 1 FROM pro_payment_events WHERE event_key = ?", (event_key,)).fetchone()
            if existing is not None:
                return False
            if row["status"] == "REFUNDED":
                return False
            if row["status"] != "PAID":
                raise InvalidPaymentTransition("only a PAID order may be refunded")
            self.connection.execute(
                "INSERT INTO pro_payment_events(event_key, order_id, event_kind, payload_sha256, created_at_epoch) VALUES (?, ?, 'REFUNDED', ?, ?)",
                (event_key, order_id, payload_sha256, now),
            )
            self.connection.execute(
                "UPDATE pro_payment_orders SET status = 'REFUNDED', receipt_status = 'REFUNDED', updated_at_epoch = ? WHERE order_id = ?",
                (now, order_id),
            )
            self.connection.execute(
                "UPDATE pro_entitlements SET state = 'REVOKED', revoked_at_epoch = ?, revoke_reason = 'PAYMENT_REFUNDED' WHERE order_id = ? AND state = 'ACTIVE'",
                (now, order_id),
            )
        return True

    def entitlement_for_order(self, order_id: str) -> Mapping[str, Any] | None:
        return self.connection.execute("SELECT * FROM pro_entitlements WHERE order_id = ?", (order_id,)).fetchone()


class RobokassaTestAdapter:
    """Build and verify Robokassa test-mode messages without network execution."""

    ACTION_URL = "https://auth.robokassa.ru/Merchant/Payment/Index"
    ALLOWED_METHODS = {"BankCard", "SBP"}

    def __init__(
        self,
        *,
        merchant_login: str,
        test_password1: str,
        test_password2: str,
        is_test: bool,
        hash_name: str = "md5",
    ) -> None:
        if is_test is not True:
            raise UnsafePaymentMode("Robokassa non-production adapter requires explicit IsTest=1")
        if not merchant_login or not test_password1 or not test_password2:
            raise ValueError("test merchant login and separate test Password #1/#2 are required")
        if test_password1 == test_password2:
            raise ValueError("Password #1 and Password #2 must be separate credentials")
        if hash_name.lower() not in hashlib.algorithms_available:
            raise ValueError("unsupported signature hash")
        self.merchant_login = merchant_login
        self._password1 = test_password1
        self._password2 = test_password2
        self.is_test = True
        self.hash_name = hash_name.lower()

    def _digest(self, value: str) -> str:
        return hashlib.new(self.hash_name, value.encode("utf-8")).hexdigest()

    @staticmethod
    def _amount_text(amount_kopecks: int) -> str:
        return f"{Decimal(amount_kopecks) / Decimal(100):.2f}"

    def build_receipt(self, *, offer: Offer, fiscal_policy: FiscalItemPolicy) -> str:
        receipt = {
            "items": [
                {
                    "name": offer.title_ru,
                    "quantity": 1,
                    "sum": float(Decimal(offer.amount_kopecks) / Decimal(100)),
                    "tax": fiscal_policy.tax,
                    "payment_method": fiscal_policy.payment_method,
                    "payment_object": fiscal_policy.payment_object,
                }
            ]
        }
        raw = json.dumps(receipt, ensure_ascii=False, separators=(",", ":"))
        return quote(raw, safe="")

    def build_test_initiation(
        self,
        *,
        inv_id: int,
        offer: Offer,
        payment_method: str,
        fiscal_policy: FiscalItemPolicy,
    ) -> Mapping[str, str]:
        if self.is_test is not True:
            raise UnsafePaymentMode("test flag was not explicitly enabled")
        if payment_method not in self.ALLOWED_METHODS:
            raise InvalidPaymentMethod("only BankCard and SBP are allowed at launch")
        out_sum = self._amount_text(offer.amount_kopecks)
        receipt = self.build_receipt(offer=offer, fiscal_policy=fiscal_policy)
        signature_base = f"{self.merchant_login}:{out_sum}:{inv_id}:{receipt}:{self._password1}"
        signature = self._digest(signature_base)
        fields = {
            "MerchantLogin": self.merchant_login,
            "OutSum": out_sum,
            "InvId": str(inv_id),
            "Description": offer.title_ru,
            "Receipt": receipt,
            "SignatureValue": signature,
            "IsTest": "1",
            "IncCurrLabel": payment_method,
            "PaymentMethods": payment_method,
            "Culture": "ru",
        }
        forbidden = {"Token", "Recurring", "StepByStep"}
        if forbidden & set(fields):
            raise UnsafePaymentMode("saved-card/recurring/hold parameters are forbidden")
        return fields

    def verify_result_url(self, payload: Mapping[str, Any], *, expected_inv_id: int, expected_amount_kopecks: int) -> tuple[str, str]:
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

    def sign_test_result(self, *, out_sum_text: str, inv_id: int) -> str:
        """Test helper: emulate ResultURL signature with test Password #2."""
        return self._digest(f"{out_sum_text}:{inv_id}:{self._password2}")


class ProPaymentService:
    """Server-side orchestration from order to entitlement."""

    CREATE_ALLOWED_FIELDS = {"offer_code", "payment_method"}

    def __init__(
        self,
        *,
        store: PaymentStore,
        catalog: OfferCatalog,
        provider: RobokassaTestAdapter,
        fiscal_policy: FiscalItemPolicy,
        now_provider: Callable[[], int] | None = None,
        order_id_factory: Callable[[], str] | None = None,
        inv_id_factory: Callable[[], int] | None = None,
    ) -> None:
        self.store = store
        self.catalog = catalog
        self.provider = provider
        self.fiscal_policy = fiscal_policy
        self.now_provider = now_provider or (lambda: int(time.time()))
        self.order_id_factory = order_id_factory or (lambda: "ord:" + secrets.token_urlsafe(18))
        self.inv_id_factory = inv_id_factory or (lambda: secrets.randbelow(2_000_000_000) + 1)

    @staticmethod
    def _validate_server_identity(user_identity_ref: str, learner_profile_id: str) -> None:
        if not isinstance(user_identity_ref, str) or not user_identity_ref.startswith("user:"):
            raise InvalidPaymentRequest("verified server-owned user identity is required")
        if not isinstance(learner_profile_id, str) or not learner_profile_id.startswith("learner:"):
            raise InvalidPaymentRequest("server-owned learner profile is required")

    def create_order(
        self,
        payload: Mapping[str, Any],
        *,
        user_identity_ref: str,
        learner_profile_id: str,
    ) -> PaymentInitiation:
        if not isinstance(payload, Mapping) or set(payload) != self.CREATE_ALLOWED_FIELDS:
            raise InvalidPaymentRequest("browser may supply only offer_code and payment_method")
        self._validate_server_identity(user_identity_ref, learner_profile_id)
        offer_code = payload.get("offer_code")
        payment_method = payload.get("payment_method")
        if not isinstance(offer_code, str) or not isinstance(payment_method, str):
            raise InvalidPaymentRequest("offer_code/payment_method must be strings")
        offer = self.catalog.get(offer_code)
        if payment_method not in self.provider.ALLOWED_METHODS:
            raise InvalidPaymentMethod("unsupported payment method")
        now = int(self.now_provider())
        order_id = self.order_id_factory()
        inv_id = int(self.inv_id_factory())
        self.store.create_order(
            order_id=order_id,
            inv_id=inv_id,
            user_identity_ref=user_identity_ref,
            learner_profile_id=learner_profile_id,
            offer=offer,
            payment_method=payment_method,
            now=now,
        )
        fields = self.provider.build_test_initiation(
            inv_id=inv_id,
            offer=offer,
            payment_method=payment_method,
            fiscal_policy=self.fiscal_policy,
        )
        self.store.mark_initiated(order_id, now=now)
        return PaymentInitiation(
            order_id=order_id,
            inv_id=inv_id,
            offer_code=offer.code,
            payment_method=payment_method,
            amount_kopecks=offer.amount_kopecks,
            provider="ROBOKASSA",
            test_mode=True,
            action_url=self.provider.ACTION_URL,
            form_fields=fields,
        )

    def retry(self, order_id: str) -> PaymentInitiation:
        row = self.store.order(order_id=order_id)
        if row is None:
            raise InvalidPaymentTransition("unknown order")
        if row["status"] != "FAILED":
            raise InvalidPaymentTransition("only FAILED orders may be retried")
        offer = self.catalog.get(str(row["offer_code"]))
        fields = self.provider.build_test_initiation(
            inv_id=int(row["inv_id"]),
            offer=offer,
            payment_method=str(row["payment_method"]),
            fiscal_policy=self.fiscal_policy,
        )
        now = int(self.now_provider())
        self.store.mark_initiated(order_id, now=now)
        return PaymentInitiation(
            order_id=order_id,
            inv_id=int(row["inv_id"]),
            offer_code=offer.code,
            payment_method=str(row["payment_method"]),
            amount_kopecks=offer.amount_kopecks,
            provider="ROBOKASSA",
            test_mode=True,
            action_url=self.provider.ACTION_URL,
            form_fields=fields,
        )

    def result_url(self, payload: Mapping[str, Any]) -> PaymentResult:
        if not isinstance(payload, Mapping) or "InvId" not in payload:
            raise InvalidProviderNotification("ResultURL is missing InvId")
        try:
            inv_id = int(str(payload["InvId"]))
        except ValueError as exc:
            raise InvalidProviderNotification("InvId must be numeric") from exc
        row = self.store.order(inv_id=inv_id)
        if row is None:
            raise InvalidProviderNotification("unknown InvId")
        _, provider_ref = self.provider.verify_result_url(
            payload,
            expected_inv_id=inv_id,
            expected_amount_kopecks=int(row["amount_kopecks"]),
        )
        payload_hash = hashlib.sha256(
            json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        entitlement = self.store.grant_paid_exactly_once(
            inv_id=inv_id,
            provider_payment_ref=provider_ref,
            payload_sha256=payload_hash,
            now=int(self.now_provider()),
        )
        updated = self.store.order(inv_id=inv_id)
        assert updated is not None
        return PaymentResult(
            acknowledgement=f"OK{inv_id}",
            order_id=str(updated["order_id"]),
            status=str(updated["status"]),
            receipt_status=str(updated["receipt_status"]),
            entitlement=entitlement,
        )

    def mark_failure(self, order_id: str, *, provider_reason_code: str) -> bool:
        if not isinstance(provider_reason_code, str) or not provider_reason_code:
            raise InvalidPaymentRequest("provider reason code is required")
        digest = hashlib.sha256(provider_reason_code.encode("utf-8")).hexdigest()
        return self.store.mark_failed(order_id, payload_sha256=digest, now=int(self.now_provider()))

    def record_receipt(self, order_id: str, *, status: str, provider_receipt_ref: str | None = None) -> None:
        self.store.update_receipt_status(
            order_id,
            status=status,
            provider_receipt_ref=provider_receipt_ref,
            now=int(self.now_provider()),
        )

    def refund_confirmed(self, order_id: str, *, provider_ref: str) -> bool:
        if not provider_ref:
            raise InvalidPaymentRequest("provider refund reference is required")
        digest = hashlib.sha256(provider_ref.encode("utf-8")).hexdigest()
        return self.store.refund_confirmed(
            order_id,
            provider_ref=provider_ref,
            payload_sha256=digest,
            now=int(self.now_provider()),
        )
