#!/usr/bin/env python3
"""Subject-neutral executable reference service boundary for Eksamio PEIS.

The service accepts constrained product-observation payloads through registered
server-side adapters. It does not accept canonical educational truth from the
browser. Adapters construct EvidenceEvent records, the shared persistence store
owns append/replay, and the shared PEIS kernel owns inference.

The bundled HTTP handler is loopback/reference transport only. It is not an
authentication system and is not a claim of a deployed production service.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from typing import Any, Callable, Mapping, Protocol

from peis_persistence import IntegrityConflict, PeisPersistenceStore


class ServiceRequestError(ValueError):
    """Rejected browser/product request."""


class MissingHostIdentity(ServiceRequestError):
    """No trusted host identity context was supplied."""


class UnknownAdapter(ServiceRequestError):
    """Requested server adapter is not registered."""


@dataclass(frozen=True)
class HostIdentity:
    learner_profile_id: str
    identity_refs: dict[str, str]

    def validate(self) -> None:
        if not isinstance(self.learner_profile_id, str) or len(self.learner_profile_id) < 3:
            raise MissingHostIdentity("learner_profile_id is required from the trusted host boundary")
        allowed = {"anonymous_identity_ref", "user_identity_ref"}
        if not self.identity_refs or not set(self.identity_refs).issubset(allowed):
            raise MissingHostIdentity("identity_refs must contain only anonymous_identity_ref/user_identity_ref")
        if not any(isinstance(value, str) and len(value) >= 3 for value in self.identity_refs.values()):
            raise MissingHostIdentity("at least one stable host identity ref is required")
        for key, value in self.identity_refs.items():
            if not isinstance(value, str) or len(value) < 3:
                raise MissingHostIdentity(f"invalid identity ref for {key}")
            if "@" in value:
                raise MissingHostIdentity("email is forbidden as the academic-history identity key")


@dataclass(frozen=True)
class ServerEventPosition:
    received_at_server: str
    server_sequence: int
    server_watermark: str


@dataclass(frozen=True)
class AdaptedObservation:
    event: dict[str, Any]
    target_semantic_id: str
    goal_context: str | None
    admitted_edges: list[dict[str, Any]]


class CheckedCardAdapter(Protocol):
    adapter_id: str
    subject_id: str

    def stable_event_id(self, payload: Mapping[str, Any]) -> str:
        ...

    def build_observation(
        self,
        payload: Mapping[str, Any],
        *,
        host_identity: HostIdentity,
        server_position: ServerEventPosition,
    ) -> AdaptedObservation:
        ...


class AdapterRegistry:
    """Server-side registry. Adapter IDs, not subjects, choose educational truth."""

    def __init__(self) -> None:
        self._adapters: dict[str, CheckedCardAdapter] = {}

    def register(self, adapter: CheckedCardAdapter) -> None:
        adapter_id = getattr(adapter, "adapter_id", None)
        if not isinstance(adapter_id, str) or not adapter_id:
            raise ValueError("adapter_id is required")
        if adapter_id in self._adapters:
            raise ValueError(f"adapter already registered: {adapter_id}")
        self._adapters[adapter_id] = adapter

    def get(self, adapter_id: str) -> CheckedCardAdapter:
        try:
            return self._adapters[adapter_id]
        except KeyError as exc:
            raise UnknownAdapter(f"unknown adapter_id: {adapter_id}") from exc

    def adapter_ids(self) -> list[str]:
        return sorted(self._adapters)


def _digest(value: str, length: int = 24) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _product_directive(snapshot: dict[str, Any]) -> dict[str, Any]:
    nba = snapshot["nba"]
    return {
        "recommendation_id": nba["recommendation_id"],
        "action_type": nba["action_type"],
        "semantic_targets": list(nba["semantic_targets"]),
        "prerequisite_targets": list(nba.get("prerequisite_targets", [])),
        "reason_codes": list(nba["reason_codes"]),
        "verification_required": bool(nba["verification_required"]),
        "learner_state_watermark": nba["learner_state_watermark"],
        "route": dict(nba["route"]),
        "canonical_state_owner": "shared_peis",
    }


class PeisServiceBridge:
    """Generic service orchestrator around server adapters + shared PEIS."""

    def __init__(
        self,
        *,
        store: PeisPersistenceStore,
        registry: AdapterRegistry,
        kernel_snapshot: Callable[..., dict[str, Any]],
        now_provider: Callable[[], str] = _utc_now,
    ) -> None:
        self.store = store
        self.registry = registry
        self.kernel_snapshot = kernel_snapshot
        self.now_provider = now_provider
        self._append_lock = threading.RLock()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "peis-service-bridge-reference",
            "mode": "REFERENCE_NOT_PUBLIC_PRODUCTION",
            "registered_adapter_ids": self.registry.adapter_ids(),
        }

    def _position_for_new_event(
        self,
        *,
        learner_profile_id: str,
        subject_id: str,
        event_id: str,
    ) -> ServerEventPosition:
        events = self.store.list_events(
            learner_profile_id,
            subject_id,
            effective=False,
        )
        sequences = [
            event.get("timestamps", {}).get("server_sequence")
            for event in events
            if isinstance(event.get("timestamps", {}).get("server_sequence"), int)
        ]
        sequence = (max(sequences) if sequences else 0) + 1
        received = self.now_provider()
        watermark = f"svcwm.{_digest(f'{learner_profile_id}|{subject_id}|{sequence}|{event_id}')}"
        return ServerEventPosition(
            received_at_server=received,
            server_sequence=sequence,
            server_watermark=watermark,
        )

    @staticmethod
    def _existing_position(event: dict[str, Any]) -> ServerEventPosition:
        timestamps = event["timestamps"]
        sequence = timestamps.get("server_sequence")
        watermark = timestamps.get("server_watermark")
        if not isinstance(sequence, int) or not isinstance(watermark, str) or not watermark:
            raise IntegrityConflict("existing canonical event lacks a reusable server position")
        return ServerEventPosition(
            received_at_server=timestamps["received_at_server"],
            server_sequence=sequence,
            server_watermark=watermark,
        )

    def _recommendation_id(
        self,
        *,
        learner_profile_id: str,
        subject_id: str,
        target_semantic_id: str,
    ) -> str:
        effective = self.store.list_events(learner_profile_id, subject_id, effective=True)
        basis = "|".join(event["event_id"] for event in effective)
        return f"nba.svc.{_digest(f'{learner_profile_id}|{subject_id}|{target_semantic_id}|{basis}')}"

    def submit_checked_card(
        self,
        *,
        adapter_id: str,
        payload: Mapping[str, Any],
        host_identity: HostIdentity,
    ) -> dict[str, Any]:
        host_identity.validate()
        if not isinstance(adapter_id, str) or not adapter_id:
            raise ServiceRequestError("adapter_id is required")
        if not isinstance(payload, Mapping):
            raise ServiceRequestError("payload must be a JSON object")
        adapter = self.registry.get(adapter_id)
        stable_event_id = adapter.stable_event_id(payload)

        with self._append_lock:
            existing = self.store.raw_event(stable_event_id)
            if existing is not None:
                if existing.get("learner_profile_id") != host_identity.learner_profile_id:
                    raise IntegrityConflict("stable product event is already linked to another learner")
                if existing.get("subject_id") != adapter.subject_id:
                    raise IntegrityConflict("stable product event subject disagrees with registered adapter")
                position = self._existing_position(existing)
            else:
                position = self._position_for_new_event(
                    learner_profile_id=host_identity.learner_profile_id,
                    subject_id=adapter.subject_id,
                    event_id=stable_event_id,
                )

            adapted = adapter.build_observation(
                payload,
                host_identity=host_identity,
                server_position=position,
            )
            if adapted.event["event_id"] != stable_event_id:
                raise IntegrityConflict("adapter stable_event_id differs from canonical event_id")
            if adapted.event["subject_id"] != adapter.subject_id:
                raise IntegrityConflict("adapter emitted an event for a different subject")

            append_result = self.store.append_event(adapted.event)
            canonical_event = self.store.raw_event(append_result["event_id"])
            if canonical_event is None:
                raise RuntimeError("accepted event cannot be reloaded from shared persistence")

            recommendation_id = self._recommendation_id(
                learner_profile_id=host_identity.learner_profile_id,
                subject_id=adapter.subject_id,
                target_semantic_id=adapted.target_semantic_id,
            )
            snapshot = self.store.recompute_snapshot(
                learner_profile_id=host_identity.learner_profile_id,
                subject_id=adapter.subject_id,
                semantic_id=adapted.target_semantic_id,
                admitted_edges=adapted.admitted_edges,
                goal_context=adapted.goal_context,
                kernel_snapshot=self.kernel_snapshot,
                recommendation_id=recommendation_id,
            )
            recommendation_result = self.store.append_recommendation(snapshot["nba"])

        timestamps = canonical_event["timestamps"]
        return {
            "status": append_result["status"],
            "event_receipt": {
                "event_id": canonical_event["event_id"],
                "subject_id": canonical_event["subject_id"],
                "server_sequence": timestamps.get("server_sequence"),
                "server_watermark": timestamps.get("server_watermark"),
                "received_at_server": timestamps.get("received_at_server"),
            },
            "recommendation_persistence_status": recommendation_result["status"],
            "directive": _product_directive(snapshot),
            "service_mode": "REFERENCE_NOT_PUBLIC_PRODUCTION",
        }


class ReferenceHeaderIdentityResolver:
    """CI/loopback transport adapter, explicitly not production authentication."""

    def resolve(self, headers: Mapping[str, str]) -> HostIdentity:
        if headers.get("X-Eksamio-Email"):
            raise MissingHostIdentity("email header is forbidden as academic identity")
        learner_profile_id = headers.get("X-Eksamio-Learner-Profile", "")
        refs: dict[str, str] = {}
        anonymous = headers.get("X-Eksamio-Anonymous-Identity")
        user = headers.get("X-Eksamio-User-Identity")
        if anonymous:
            refs["anonymous_identity_ref"] = anonymous
        if user:
            refs["user_identity_ref"] = user
        identity = HostIdentity(learner_profile_id=learner_profile_id, identity_refs=refs)
        identity.validate()
        return identity


def make_reference_http_handler(
    bridge: PeisServiceBridge,
    *,
    identity_resolver: ReferenceHeaderIdentityResolver | None = None,
) -> type[BaseHTTPRequestHandler]:
    """Create a loopback/reference HTTP handler bound to one service bridge."""

    resolver = identity_resolver or ReferenceHeaderIdentityResolver()

    class Handler(BaseHTTPRequestHandler):
        server_version = "EksamioPEISReference/0.1"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/healthz":
                self._json(404, {"error": "NOT_FOUND"})
                return
            self._json(200, bridge.health())

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/v0/checked-card":
                self._json(404, {"error": "NOT_FOUND"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 262144:
                    raise ServiceRequestError("invalid request body length")
                raw = self.rfile.read(length)
                request = json.loads(raw.decode("utf-8"))
                if not isinstance(request, dict):
                    raise ServiceRequestError("request body must be a JSON object")
                allowed = {"adapter_id", "payload"}
                extras = set(request) - allowed
                if extras:
                    raise ServiceRequestError(f"unexpected top-level fields: {sorted(extras)}")
                identity = resolver.resolve(self.headers)
                result = bridge.submit_checked_card(
                    adapter_id=request.get("adapter_id", ""),
                    payload=request.get("payload", {}),
                    host_identity=identity,
                )
                self._json(200, result)
            except MissingHostIdentity as exc:
                self._json(401, {"error": "HOST_IDENTITY_REQUIRED", "message": str(exc)})
            except UnknownAdapter as exc:
                self._json(404, {"error": "UNKNOWN_ADAPTER", "message": str(exc)})
            except IntegrityConflict as exc:
                self._json(409, {"error": "INTEGRITY_CONFLICT", "message": str(exc)})
            except (ServiceRequestError, json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                self._json(400, {"error": "INVALID_REQUEST", "message": str(exc)})
            except Exception:
                self._json(500, {"error": "REFERENCE_SERVICE_ERROR"})

    return Handler
