"""Deterministic T1 reliability gateway around the existing Tutor boundary.

This module contains no provider SDK, I/O, persistence, or canonical PEIS write.
It reuses ``TutorOrchestrator`` for the advisory-response policy boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Mapping, Protocol

from tutor_boundary import ProviderRequest, ProviderResponse, ServerTutorTurn, TutorOrchestrator, TutorTurnResult, _provider_request


RELIABILITY_CONTRACT_VERSION = "eksamio.tutor.reliability-gateway.v1"


class FailureClass(str, Enum):
    TIMEOUT = "TIMEOUT"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    RATE_LIMIT = "RATE_LIMIT"
    QUOTA_OR_BILLING_EXHAUSTED = "QUOTA_OR_BILLING_EXHAUSTED"
    CREDENTIAL_OR_ACCOUNT_FAILURE = "CREDENTIAL_OR_ACCOUNT_FAILURE"
    MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
    PROVIDER_5XX = "PROVIDER_5XX"
    CAPACITY_UNAVAILABLE = "CAPACITY_UNAVAILABLE"
    MALFORMED_PROVIDER_OUTPUT = "MALFORMED_PROVIDER_OUTPUT"
    TOOL_PROTOCOL_FAILURE = "TOOL_PROTOCOL_FAILURE"
    PROVIDER_SPECIFIC_REJECTION = "PROVIDER_SPECIFIC_REJECTION"
    PLATFORM_SAFETY_BLOCK = "PLATFORM_SAFETY_BLOCK"
    INVALID_PLATFORM_REQUEST = "INVALID_PLATFORM_REQUEST"


class HealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    OPEN_CIRCUIT = "OPEN_CIRCUIT"
    DISABLED_MAINTENANCE = "DISABLED_MAINTENANCE"
    BLOCKED_FINOPS = "BLOCKED_FINOPS"
    BLOCKED_CREDENTIAL = "BLOCKED_CREDENTIAL"
    BLOCKED_POLICY = "BLOCKED_POLICY"


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass(frozen=True)
class ProviderPath:
    provider_id: str
    capability: str
    adapter_version: str
    admission_status: str
    priority: int
    configured_capacity_class: str = "REFERENCE"


@dataclass(frozen=True)
class EpisodeProjection:
    episode_id: str
    turn_id: str
    learning_goal: str
    semantic_targets: tuple[str, ...]
    verified_context_refs: tuple[str, ...]
    peis_projection_version: str
    peis_projection_ref: str
    help_state: str
    verification_required: bool
    structured_history_summary: tuple[str, ...]
    continuation_marker: str | None = None


@dataclass(frozen=True)
class ProviderAttempt:
    provider_attempt_id: str
    episode_id: str
    turn_id: str
    provider_id: str
    capability: str
    retry_index: int


@dataclass(frozen=True)
class ProviderFault:
    failure_class: FailureClass
    adapter_detail: str = "fixture-only"


@dataclass(frozen=True)
class DelayedProviderSuccess:
    response: ProviderResponse


ProviderOutcome = ProviderResponse | ProviderFault | DelayedProviderSuccess


class ReliableProvider(Protocol):
    provider_id: str

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        """Adapter-local execution; it has no PEIS, quota, or tool-write capability."""


@dataclass
class Circuit:
    state: CircuitState = CircuitState.CLOSED
    health: HealthState = HealthState.HEALTHY
    opened_at_tick: int | None = None


@dataclass(frozen=True)
class GatewayConfig:
    max_same_path_retries: int = 1
    half_open_after_ticks: int = 2


@dataclass(frozen=True)
class GatewayEvent:
    event_type: str
    episode_id: str
    turn_id: str
    provider_id: str | None = None
    failure_class: str | None = None
    circuit_state: str | None = None


@dataclass(frozen=True)
class ReliableTurnResult:
    status: str
    tutor_result: TutorTurnResult | None
    episode_id: str
    turn_id: str
    accepted_attempt_id: str | None
    learner_quota_debit_count: int
    evidence_verification_commit_count: int
    direct_canonical_peis_writes: int
    events: tuple[GatewayEvent, ...]


class _StaticResponseProvider:
    provider_id = "gateway-static-response"

    def __init__(self, response: ProviderResponse) -> None:
        self.response = response

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        return self.response


class ReliabilityGateway:
    """Server-owned routing/commit boundary; one instance represents an episode store."""

    def __init__(self, registry: Mapping[tuple[str, str], ProviderPath], providers: Mapping[str, ReliableProvider], config: GatewayConfig = GatewayConfig()) -> None:
        self.registry = dict(registry)
        self.providers = dict(providers)
        self.config = config
        self.circuits: dict[tuple[str, str], Circuit] = {key: Circuit() for key in registry}
        self.tick = 0
        self.accepted: dict[tuple[str, str], str] = {}
        self.quota_debits: set[tuple[str, str]] = set()
        self.evidence_commits: set[tuple[str, str]] = set()
        self.delayed: dict[str, DelayedProviderSuccess] = {}
        self.events: list[GatewayEvent] = []

    def _event(self, kind: str, episode: EpisodeProjection, provider_id: str | None = None, failure: FailureClass | None = None, circuit: CircuitState | None = None) -> None:
        self.events.append(GatewayEvent(kind, episode.episode_id, episode.turn_id, provider_id, failure.value if failure else None, circuit.value if circuit else None))

    def _eligible_paths(self, capability: str) -> list[ProviderPath]:
        paths = [path for path in self.registry.values() if path.capability == capability and path.admission_status == "PRODUCTION_ADMITTED"]
        return sorted(paths, key=lambda path: path.priority)

    def _allow_path(self, key: tuple[str, str], episode: EpisodeProjection) -> bool:
        circuit = self.circuits[key]
        if circuit.state is CircuitState.OPEN:
            if circuit.opened_at_tick is None or self.tick - circuit.opened_at_tick < self.config.half_open_after_ticks:
                return False
            circuit.state = CircuitState.HALF_OPEN
            self._event("circuit_state_changed", episode, key[0], circuit=circuit.state)
        return circuit.state in {CircuitState.CLOSED, CircuitState.HALF_OPEN}

    def _open(self, key: tuple[str, str], episode: EpisodeProjection, health: HealthState) -> None:
        circuit = self.circuits[key]
        circuit.state, circuit.health, circuit.opened_at_tick = CircuitState.OPEN, health, self.tick
        self._event("circuit_state_changed", episode, key[0], circuit=circuit.state)

    def _success(self, key: tuple[str, str], episode: EpisodeProjection) -> None:
        circuit = self.circuits[key]
        if circuit.state is CircuitState.HALF_OPEN:
            circuit.state, circuit.health, circuit.opened_at_tick = CircuitState.CLOSED, HealthState.HEALTHY, None
            self._event("circuit_state_changed", episode, key[0], circuit=circuit.state)
        elif circuit.state is CircuitState.CLOSED:
            circuit.health = HealthState.HEALTHY

    def _failure_policy(self, failure: FailureClass) -> tuple[bool, bool, HealthState | None]:
        """Return retryable, terminal-no-failover, and optional circuit health."""
        if failure is FailureClass.PLATFORM_SAFETY_BLOCK:
            return False, True, HealthState.BLOCKED_POLICY
        if failure is FailureClass.INVALID_PLATFORM_REQUEST:
            return False, True, None
        if failure is FailureClass.QUOTA_OR_BILLING_EXHAUSTED:
            return False, False, HealthState.BLOCKED_FINOPS
        if failure is FailureClass.CREDENTIAL_OR_ACCOUNT_FAILURE:
            return False, False, HealthState.BLOCKED_CREDENTIAL
        if failure in {FailureClass.MODEL_UNAVAILABLE, FailureClass.CAPACITY_UNAVAILABLE}:
            return False, False, HealthState.OPEN_CIRCUIT
        return failure in {FailureClass.TIMEOUT, FailureClass.NETWORK_FAILURE, FailureClass.PROVIDER_5XX, FailureClass.MALFORMED_PROVIDER_OUTPUT, FailureClass.TOOL_PROTOCOL_FAILURE}, False, None

    def _commit_success(self, logical_key: tuple[str, str], attempt: ProviderAttempt, episode: EpisodeProjection, response: ProviderResponse, turn: ServerTutorTurn) -> ReliableTurnResult:
        if logical_key in self.accepted:
            self._event("late_response_discarded", episode, attempt.provider_id)
            return self._result("TUTOR_UNAVAILABLE", None, episode)
        tutor_result = TutorOrchestrator(_StaticResponseProvider(response)).handle_turn(turn)
        self.accepted[logical_key] = attempt.provider_attempt_id
        self.quota_debits.add(logical_key)
        self.evidence_commits.add(logical_key)  # mock deterministic post-verification commit boundary
        self._event("logical_turn_accepted", episode, attempt.provider_id)
        self._event("learner_quota_debit_committed", episode, attempt.provider_id)
        return self._result(tutor_result.status, tutor_result, episode)

    def _result(self, status: str, tutor_result: TutorTurnResult | None, episode: EpisodeProjection) -> ReliableTurnResult:
        logical_key = (episode.episode_id, episode.turn_id)
        return ReliableTurnResult(status, tutor_result, episode.episode_id, episode.turn_id, self.accepted.get(logical_key), int(logical_key in self.quota_debits), int(logical_key in self.evidence_commits), 0, tuple(self.events))

    def handle_turn(self, episode: EpisodeProjection, turn: ServerTutorTurn, capability: str = "text") -> ReliableTurnResult:
        self.tick += 1
        if episode.learning_goal != turn.learning_goal or episode.semantic_targets != turn.peis_projection.target_refs or episode.verification_required != turn.policy.verification_required:
            raise ValueError("episode projection must match server-owned Tutor turn")
        logical_key = (episode.episode_id, episode.turn_id)
        if logical_key in self.accepted:
            return self._result("ALREADY_ACCEPTED", None, episode)
        request = _provider_request(turn)
        paths = self._eligible_paths(capability)
        for path_index, path in enumerate(paths):
            key = (path.provider_id, path.capability)
            if not self._allow_path(key, episode):
                continue
            provider = self.providers[path.provider_id]
            for retry_index in range(self.config.max_same_path_retries + 1):
                attempt = ProviderAttempt(f"attempt:{episode.episode_id}:{episode.turn_id}:{path.provider_id}:{retry_index}", episode.episode_id, episode.turn_id, path.provider_id, capability, retry_index)
                self._event("provider_attempt_started", episode, path.provider_id)
                outcome = provider.generate(request, attempt)
                if not isinstance(outcome, (ProviderResponse, ProviderFault, DelayedProviderSuccess)):
                    # Adapter-local malformed values are normalized here and never
                    # exposed beyond this gateway boundary.
                    outcome = ProviderFault(FailureClass.MALFORMED_PROVIDER_OUTPUT)
                if isinstance(outcome, ProviderResponse):
                    self._event("provider_attempt_completed", episode, path.provider_id)
                    result = self._commit_success(logical_key, attempt, episode, outcome, turn)
                    self._success(key, episode)
                    if path_index:
                        self._event("fallback_succeeded", episode, path.provider_id)
                    return self._result(result.status, result.tutor_result, episode)
                if isinstance(outcome, DelayedProviderSuccess):
                    self.delayed[attempt.provider_attempt_id] = outcome
                    self._event("provider_attempt_failed", episode, path.provider_id, FailureClass.TIMEOUT)
                    break
                failure = outcome.failure_class
                self._event("provider_attempt_failed", episode, path.provider_id, failure)
                retryable, terminal, health = self._failure_policy(failure)
                if health is not None:
                    self._open(key, episode, health)
                if terminal:
                    self._event("tutor_unavailable", episode, path.provider_id, failure)
                    self._event("learner_quota_debit_skipped", episode, path.provider_id)
                    return self._result("TUTOR_UNAVAILABLE", None, episode)
                if retryable and retry_index < self.config.max_same_path_retries and self.circuits[key].state is CircuitState.CLOSED:
                    continue
                break
            if path_index < len(paths) - 1:
                self._event("fallback_activated", episode, path.provider_id)
        self._event("fallback_failed", episode)
        self._event("tutor_unavailable", episode)
        self._event("learner_quota_debit_skipped", episode)
        return self._result("TUTOR_UNAVAILABLE", None, episode)

    def deliver_late_success(self, attempt_id: str, episode: EpisodeProjection) -> bool:
        delayed = self.delayed.pop(attempt_id, None)
        if delayed is None:
            return False
        self._event("late_response_discarded", episode)
        return False
