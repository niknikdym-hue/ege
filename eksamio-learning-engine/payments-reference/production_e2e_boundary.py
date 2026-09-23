#!/usr/bin/env python3
"""Exact-candidate payment boundary for SEP-1 production E2E acceptance.

This module is deliberately framework-neutral.  It is the server-owned service
boundary that an HTTP route layer can mount for the Pro client contract.  It
reuses the existing PaymentStore and Robokassa production-candidate adapter,
adds provider-neutral receipt/refund event ingestion, and performs no network
or provider execution itself.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from payments import (
    InvalidPaymentMethod,
    InvalidPaymentRequest,
    InvalidPaymentTransition,
    InvalidProviderNotification,
    OfferCatalog,
    PaymentStore,
)
from robokassa_production import RobokassaAdapter, RobokassaMode


class ProviderEventConflict(InvalidProviderNotification):
    """A provider event id was replayed with different canonical content."""


@dataclass(frozen=True)
class ProviderReceiptEvent:
    event_id: str
    provider: str
    payment_provider: str
    order_id: str
    amount_kopecks: int
    provider_receipt_ref: str
    status: str


@dataclass(frozen=True)
class ProviderRefundEvent:
    event_id: str
    provider: str
    payment_provider: str
    order_id: str
    amount_kopecks: int
    provider_ref: str
    status: str = "CONFIRMED"


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _event_payload(event: ProviderReceiptEvent | ProviderRefundEvent) -> dict[str, Any]:
    return {name: getattr(event, name) for name in event.__dataclass_fields__}


class ProviderEventBoundary:
    """Apply provider receipt/refund confirmations exactly once and fail closed."""

    def __init__(self, store: PaymentStore) -> None:
        self.store = store

    @staticmethod
    def _validate_common(event: ProviderReceiptEvent | ProviderRefundEvent) -> None:
        if not event.event_id or not event.provider or not event.payment_provider or not event.order_id:
            raise InvalidProviderNotification("provider event identity is incomplete")
        if event.amount_kopecks <= 0:
            raise InvalidProviderNotification("provider event amount must be positive")

    def _order_for_event(self, event: ProviderReceiptEvent | ProviderRefundEvent) -> Mapping[str, Any]:
        self._validate_common(event)
        row = self.store.order(order_id=event.order_id)
        if row is None:
            raise InvalidProviderNotification("provider event references unknown order")
        if str(row["provider"]) != event.payment_provider:
            raise InvalidProviderNotification("provider event payment-provider mismatch")
        if int(row["amount_kopecks"]) != event.amount_kopecks:
            raise InvalidProviderNotification("provider event amount mismatch")
        return row

    def _existing_event(self, event_key: str) -> Mapping[str, Any] | None:
        return self.store.connection.execute(
            "SELECT * FROM pro_payment_events WHERE event_key = ?", (event_key,)
        ).fetchone()

    @staticmethod
    def _replay_or_conflict(existing: Mapping[str, Any], payload_sha256: str) -> bool:
        if str(existing["payload_sha256"]) != payload_sha256:
            raise ProviderEventConflict("provider event id replayed with different payload")
        return False

    def apply_receipt(self, event: ProviderReceiptEvent, *, now: int) -> bool:
        row = self._order_for_event(event)
        if event.status not in {"REGISTERED", "FAILED"}:
            raise InvalidProviderNotification("unsupported receipt provider status")
        if not event.provider_receipt_ref:
            raise InvalidProviderNotification("receipt provider reference is required")
        if str(row["status"]) != "PAID":
            raise InvalidPaymentTransition("receipt provider event requires a PAID order")

        payload_sha256 = _canonical_sha256(_event_payload(event))
        event_key = f"receipt-provider:{event.provider}:{event.event_id}"
        existing = self._existing_event(event_key)
        if existing is not None:
            return self._replay_or_conflict(existing, payload_sha256)

        with self.store.connection:
            self.store.connection.execute(
                """
                INSERT INTO pro_payment_events(event_key, order_id, event_kind, payload_sha256, created_at_epoch)
                VALUES (?, ?, 'PROVIDER_RECEIPT', ?, ?)
                """,
                (event_key, event.order_id, payload_sha256, now),
            )
            self.store.connection.execute(
                """
                UPDATE pro_payment_orders
                SET receipt_status = ?, provider_receipt_ref = ?, updated_at_epoch = ?
                WHERE order_id = ? AND status = 'PAID'
                """,
                (event.status, event.provider_receipt_ref, now, event.order_id),
            )
        return True

    def apply_refund(self, event: ProviderRefundEvent, *, now: int) -> bool:
        row = self._order_for_event(event)
        if event.status != "CONFIRMED":
            raise InvalidProviderNotification("only confirmed provider refunds may revoke access")
        if not event.provider_ref:
            raise InvalidProviderNotification("refund provider reference is required")

        payload_sha256 = _canonical_sha256(_event_payload(event))
        event_key = f"refund-provider:{event.provider}:{event.event_id}"
        existing = self._existing_event(event_key)
        if existing is not None:
            return self._replay_or_conflict(existing, payload_sha256)
        if str(row["status"]) != "PAID":
            raise InvalidPaymentTransition("refund provider event requires a PAID order")

        entitlement = self.store.entitlement_for_order(event.order_id)
        if entitlement is None or str(entitlement["state"]) != "ACTIVE":
            raise InvalidPaymentTransition("paid order is missing an active entitlement")

        with self.store.connection:
            self.store.connection.execute(
                """
                INSERT INTO pro_payment_events(event_key, order_id, event_kind, payload_sha256, created_at_epoch)
                VALUES (?, ?, 'PROVIDER_REFUND_CONFIRMED', ?, ?)
                """,
                (event_key, event.order_id, payload_sha256, now),
            )
            order_update = self.store.connection.execute(
                """
                UPDATE pro_payment_orders
                SET status = 'REFUNDED', receipt_status = 'REFUNDED', updated_at_epoch = ?
                WHERE order_id = ? AND status = 'PAID'
                """,
                (now, event.order_id),
            )
            entitlement_update = self.store.connection.execute(
                """
                UPDATE pro_entitlements
                SET state = 'REVOKED', revoked_at_epoch = ?, revoke_reason = 'PAYMENT_REFUNDED'
                WHERE order_id = ? AND state = 'ACTIVE'
                """,
                (now, event.order_id),
            )
            if order_update.rowcount != 1 or entitlement_update.rowcount != 1:
                raise InvalidPaymentTransition("refund transition lost its paid/active precondition")
        return True


class ProductionPaymentApiBoundary:
    """Server-owned payment methods corresponding to the Pro HTTP client contract.

    No HTTP framework is selected here.  A deployment adapter should map the
    existing client endpoints to these methods without moving payment authority
    into the browser.
    """

    CREATE_ALLOWED_FIELDS = {"offer_code", "payment_method"}
    CLIENT_ENDPOINTS = {
        "create_order": "/api/payments/orders",
        "entitlement": "/api/payments/entitlement",
        "result_url": "/api/payments/provider/result",
        "receipt_event": "/api/payments/provider/receipt",
        "refund_event": "/api/payments/provider/refund",
    }

    def __init__(
        self,
        *,
        store: PaymentStore,
        catalog: OfferCatalog,
        provider: RobokassaAdapter,
        now_provider: Callable[[], int] | None = None,
        order_id_factory: Callable[[], str] | None = None,
        inv_id_factory: Callable[[], int] | None = None,
    ) -> None:
        if provider.mode is not RobokassaMode.PRODUCTION_CANDIDATE:
            raise InvalidPaymentRequest("exact-candidate boundary requires PRODUCTION_CANDIDATE mode")
        self.store = store
        self.catalog = catalog
        self.provider = provider
        self.events = ProviderEventBoundary(store)
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
    ) -> dict[str, Any]:
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
        form_fields = self.provider.build_initiation(
            inv_id=inv_id, offer=offer, payment_method=payment_method
        )
        self.store.mark_initiated(order_id, now=now)
        return {
            "order_id": order_id,
            "inv_id": inv_id,
            "offer_code": offer.code,
            "payment_method": payment_method,
            "amount_kopecks": offer.amount_kopecks,
            "provider": "ROBOKASSA",
            "production_candidate": True,
            "test_mode": False,
            "action_url": self.provider.ACTION_URL,
            "form_fields": dict(form_fields),
        }

    def result_url(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        processed = self.provider.process_result_url(
            payload, store=self.store, now=int(self.now_provider())
        )
        return {
            "acknowledgement": processed.acknowledgement,
            "payment_method": processed.payment_method,
            "provider_ref": processed.provider_ref,
            "order_id": processed.entitlement.order_id,
            "entitlement_state": processed.entitlement.state,
            "replay": processed.entitlement.replay,
        }

    def entitlement(self, *, order_id: str, learner_profile_id: str) -> dict[str, Any]:
        order = self.store.order(order_id=order_id)
        entitlement = self.store.entitlement_for_order(order_id)
        if order is None or entitlement is None:
            return {"active": False, "state": "NONE"}
        if str(order["learner_profile_id"]) != learner_profile_id:
            raise InvalidPaymentRequest("entitlement does not belong to authenticated learner")
        active = (
            str(entitlement["state"]) == "ACTIVE"
            and int(entitlement["expires_at_epoch"]) > int(self.now_provider())
        )
        return {
            "active": active,
            "state": str(entitlement["state"]),
            "product_code": str(entitlement["product_code"]),
            "source_order_id": order_id,
        }

    def paid_access_allowed(self, *, order_id: str, learner_profile_id: str) -> bool:
        return bool(self.entitlement(order_id=order_id, learner_profile_id=learner_profile_id)["active"])

    def receipt_event(self, event: ProviderReceiptEvent) -> bool:
        return self.events.apply_receipt(event, now=int(self.now_provider()))

    def refund_event(self, event: ProviderRefundEvent) -> bool:
        return self.events.apply_refund(event, now=int(self.now_provider()))


@dataclass(frozen=True)
class CandidateIdentity:
    git_sha: str
    config_fingerprint: str
    preflight_fingerprint: str
    evidence_class: str = "CI_SIMULATED_CONTRACT_EVIDENCE"

    def __post_init__(self) -> None:
        if len(self.git_sha) != 40 or any(ch not in "0123456789abcdef" for ch in self.git_sha.lower()):
            raise ValueError("git_sha must be a full 40-character hexadecimal SHA")
        for value in (self.config_fingerprint, self.preflight_fingerprint):
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
                raise ValueError("candidate fingerprints must be SHA-256 hex strings")
        if self.evidence_class != "CI_SIMULATED_CONTRACT_EVIDENCE":
            raise ValueError("this CI boundary may emit simulated contract evidence only")

    def bind(self, results: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
        record = {
            "schema": "eksamio.sep1.production-e2e.payment.v1",
            "evidence_class": self.evidence_class,
            "candidate": {
                "git_sha": self.git_sha,
                "config_fingerprint": self.config_fingerprint,
                "preflight_fingerprint": self.preflight_fingerprint,
            },
            "results": dict(results),
        }
        return record, _canonical_sha256(record)

    def accepts(self, evidence: Mapping[str, Any]) -> bool:
        candidate = evidence.get("candidate") if isinstance(evidence, Mapping) else None
        return bool(
            isinstance(candidate, Mapping)
            and candidate.get("git_sha") == self.git_sha
            and candidate.get("config_fingerprint") == self.config_fingerprint
            and candidate.get("preflight_fingerprint") == self.preflight_fingerprint
            and evidence.get("evidence_class") == self.evidence_class
        )
