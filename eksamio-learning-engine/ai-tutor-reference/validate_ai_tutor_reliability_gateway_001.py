#!/usr/bin/env python3
"""Deterministic acceptance validator for AI-TUTOR-RELIABILITY-GATEWAY-001."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict, replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from reliability_fake_providers import ScriptedFakeProvider, delayed, healthy  # noqa: E402
from reliability_gateway import (  # noqa: E402
    CircuitState, EpisodeProjection, FailureClass, GatewayConfig, HealthState, ProviderFault,
    ProviderPath, ReliabilityGateway,
)
from validate_ai_tutor_provider_neutral_boundary_001 import turn  # noqa: E402


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def episode(turn_id: str = "turn-001") -> EpisodeProjection:
    sample = turn()
    return EpisodeProjection("episode-001", turn_id, sample.learning_goal, sample.peis_projection.target_refs, sample.verified_subject.source_refs, sample.peis_projection.projection_version, sample.peis_projection.projection_ref, sample.help_state, sample.policy.verification_required, tuple(f"{entry.role}:{entry.text}" for entry in sample.history), sample.continuation_marker)


def gateway(primary_outcomes, secondary_outcomes, config: GatewayConfig = GatewayConfig()):
    primary, secondary = ScriptedFakeProvider("fake-primary", list(primary_outcomes)), ScriptedFakeProvider("fake-secondary", list(secondary_outcomes))
    registry = {
        ("fake-primary", "text"): ProviderPath("fake-primary", "text", "fake.v1", "PRODUCTION_ADMITTED", 1),
        ("fake-secondary", "text"): ProviderPath("fake-secondary", "text", "fake.v1", "PRODUCTION_ADMITTED", 2),
    }
    return ReliabilityGateway(registry, {primary.provider_id: primary, secondary.provider_id: secondary}, config), primary, secondary


def failed(kind: FailureClass) -> ProviderFault:
    return ProviderFault(kind, "provider-native-fixture-detail")


def scenario(name: str, primary_outcomes, secondary_outcomes, expected: str = "TUTOR_ADVISORY"):
    runner, primary, secondary = gateway(primary_outcomes, secondary_outcomes)
    result = runner.handle_turn(episode(name), turn())
    require(result.status == expected, f"{name}: expected normalized result {expected}")
    return runner, primary, secondary, result


def digest() -> str:
    runner, _, _, result = scenario("digest", [healthy()], [healthy()])
    return hashlib.sha256(json.dumps(asdict(result), sort_keys=True).encode()).hexdigest()


def main() -> int:
    runner, primary, secondary, result = scenario("healthy-primary", [healthy()], [healthy()])
    require(len(primary.attempts) == 1 and len(secondary.attempts) == 0 and result.accepted_attempt_id is not None, "healthy primary is accepted without fallback")
    require(result.learner_quota_debit_count == 1 and result.evidence_verification_commit_count == 1, "primary success commits quota and mock verification once")

    failure_cases = [
        ("timeout", FailureClass.TIMEOUT), ("network", FailureClass.NETWORK_FAILURE), ("provider-5xx", FailureClass.PROVIDER_5XX),
    ]
    for name, failure in failure_cases:
        runner, primary, secondary, result = scenario(name, [failed(failure), failed(failure)], [healthy()])
        require(len(primary.attempts) == 2 and len(secondary.attempts) == 1, f"{name}: bounded retry then secondary fallback")
        require(result.learner_quota_debit_count == 1 and result.direct_canonical_peis_writes == 0, f"{name}: one quota debit and no direct PEIS write")

    malformed_response = healthy()
    object.__setattr__(malformed_response, "text", 17)
    runner, primary, secondary, result = scenario("malformed", [malformed_response, malformed_response], [healthy()])
    require(len(primary.attempts) == 2 and len(secondary.attempts) == 1 and result.status == "TUTOR_ADVISORY", "malformed adapter output is normalized, bounded, then falls back")
    require(result.accepted_attempt_id == secondary.attempts[0].provider_attempt_id and sum(event.event_type == "logical_turn_accepted" and event.provider_id == "fake-primary" for event in runner.events) == 0, "malformed ProviderResponse never becomes an accepted primary attempt")
    require(sum(event.event_type == "learner_quota_debit_committed" and event.provider_id == "fake-primary" for event in runner.events) == 0 and result.learner_quota_debit_count == result.evidence_verification_commit_count == 1, "malformed primary creates zero quota/evidence commits before secondary success")

    for name, failure, health in [
        ("rate-limit", FailureClass.RATE_LIMIT, HealthState.OPEN_CIRCUIT),
        ("billing", FailureClass.QUOTA_OR_BILLING_EXHAUSTED, HealthState.BLOCKED_FINOPS),
        ("credential", FailureClass.CREDENTIAL_OR_ACCOUNT_FAILURE, HealthState.BLOCKED_CREDENTIAL),
        ("model", FailureClass.MODEL_UNAVAILABLE, HealthState.OPEN_CIRCUIT),
    ]:
        runner, primary, secondary, result = scenario(name, [failed(failure)], [healthy()])
        require(len(primary.attempts) == 1 and len(secondary.attempts) == 1, f"{name}: no blind retry and secondary fallback")
        require(runner.circuits[("fake-primary", "text")].health is health and runner.circuits[("fake-primary", "text")].state is CircuitState.OPEN, f"{name}: primary path is opened/blocked")

    runner, primary, secondary, result = scenario("late", [delayed()], [healthy()])
    late_id = primary.attempts[0].provider_attempt_id
    require(result.accepted_attempt_id == secondary.attempts[0].provider_attempt_id, "secondary accepts logical turn after delayed primary")
    require(runner.deliver_late_success(late_id, episode("late")) is False and any(event.event_type == "late_response_discarded" for event in runner.events), "late primary completion is explicitly discarded")
    require(result.learner_quota_debit_count == result.evidence_verification_commit_count == 1, "late response cannot duplicate quota or evidence commit")

    runner, _, _, result = scenario("both-fail", [failed(FailureClass.NETWORK_FAILURE), failed(FailureClass.NETWORK_FAILURE)], [failed(FailureClass.PROVIDER_5XX), failed(FailureClass.PROVIDER_5XX)], "TUTOR_UNAVAILABLE")
    require(result.learner_quota_debit_count == result.evidence_verification_commit_count == 0, "all-provider failure skips learner quota and evidence commit")

    runner, primary, secondary, result = scenario("safety", [failed(FailureClass.PLATFORM_SAFETY_BLOCK)], [healthy()], "TUTOR_UNAVAILABLE")
    require(len(primary.attempts) == 1 and len(secondary.attempts) == 0, "platform safety block is not bypassed by provider hopping")
    runner, primary, secondary, result = scenario("invalid", [failed(FailureClass.INVALID_PLATFORM_REQUEST)], [healthy()], "TUTOR_UNAVAILABLE")
    require(len(primary.attempts) == 1 and len(secondary.attempts) == 0, "invalid platform request is not retried across providers")

    runner, primary, secondary = gateway([failed(FailureClass.QUOTA_OR_BILLING_EXHAUSTED), healthy()], [healthy(), healthy()])
    first = runner.handle_turn(episode("billing-block-1"), turn())
    require(first.status == "TUTOR_ADVISORY" and runner.circuits[("fake-primary", "text")].state is CircuitState.OPEN, "billing opens primary circuit while fallback succeeds")
    runner.tick += 20
    second = runner.handle_turn(episode("billing-block-2"), turn())
    require(second.accepted_attempt_id is not None and second.accepted_attempt_id.split(":")[3] == "fake-secondary", "billing-blocked provider is not auto-probed on later learner turns")
    require(runner.circuits[("fake-primary", "text")].state is CircuitState.OPEN and runner.circuits[("fake-primary", "text")].health is HealthState.BLOCKED_FINOPS, "billing block remains fail-closed until explicit recovery/reassembly")

    runner, primary, secondary, result = scenario("portability", [failed(FailureClass.NETWORK_FAILURE), failed(FailureClass.NETWORK_FAILURE)], [healthy("secondary continuity")])
    secondary_request = secondary.requests[0]
    sample = turn()
    require(secondary_request.learning_goal == sample.learning_goal and secondary_request.target_refs == sample.peis_projection.target_refs and result.tutor_result.verification_required is True, "learning goal, semantic targets, and verification requirement survive failover")
    require("fake-primary" not in json.dumps(asdict(secondary_request), sort_keys=True), "secondary completes without primary provider session identifier")

    binding_runner, binding_primary, binding_secondary = gateway([healthy()], [healthy()])
    base_episode = episode("binding")
    for field, invalid in {
        "learning_goal": "other-goal", "semantic_targets": ("other-target",), "verified_context_refs": ("source:other",),
        "peis_projection_version": "other-version", "peis_projection_ref": "peis:other", "help_state": "OTHER_HELP",
        "verification_required": False, "structured_history_summary": ("tutor:other",), "continuation_marker": "other-marker",
    }.items():
        try:
            binding_runner.handle_turn(replace(base_episode, **{field: invalid}), turn())
        except ValueError as error:
            require(field in str(error), f"mismatched {field} is rejected before provider routing")
        else:
            raise AssertionError(f"mismatched {field} routed a provider")
    require(not binding_primary.attempts and not binding_secondary.attempts, "all mismatched episode projections are rejected before provider routing")

    event_json = json.dumps([asdict(event) for event in result.events], sort_keys=True)
    forbidden = ("secret", "email", "phone", "payment", "audio", "token")
    require(all(term not in event_json.lower() for term in forbidden), "normalized observability events contain no secret/contact/payment/audio data")
    require(digest() == digest(), "repeated deterministic gateway result has identical canonical hash " + digest())
    print("AI_TUTOR_RELIABILITY_GATEWAY_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
