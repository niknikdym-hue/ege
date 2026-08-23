#!/usr/bin/env python3
"""Bounded regression for repeated transient-failure circuit semantics."""

from __future__ import annotations

from reliability_fake_providers import ScriptedFakeProvider, healthy
from reliability_gateway import (
    CircuitState,
    EpisodeProjection,
    FailureClass,
    GatewayConfig,
    HealthState,
    ProviderFault,
    ProviderPath,
    ReliabilityGateway,
)
from tutor_boundary import (
    PeisContextProjection,
    ProviderResponse,
    ServerTutorTurn,
    SystemPolicy,
    TutorHistoryEntry,
    VerifiedSubjectContext,
)


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def turn() -> ServerTutorTurn:
    return ServerTutorTurn(
        tutor_session_ref="tutor:circuit-repair-test",
        subject_id="russian",
        learning_goal="Explain one verified rule without claiming mastery.",
        policy=SystemPolicy(verification_required=True, allowed_tool_names=()),
        verified_subject=VerifiedSubjectContext(
            source_refs=("source:ru-circuit-repair-test",),
            excerpts=("Verified bounded educational context.",),
        ),
        peis_projection=PeisContextProjection(
            projection_version="peis-projection.v1",
            learning_summary="Synthetic bounded learner projection.",
            target_refs=("school-ru-circuit-repair-test",),
            projection_ref="peis:circuit-repair-test",
        ),
        history=(TutorHistoryEntry("learner", "Почему это правило работает?"),),
        learner_text="Объясни кратко и оставь проверку обязательной.",
        help_state="GUIDED_HELP",
        continuation_marker="continue:circuit-repair-test",
    )


def episode(turn_id: str) -> EpisodeProjection:
    sample = turn()
    return EpisodeProjection(
        episode_id="episode:circuit-repair-test",
        turn_id=turn_id,
        learning_goal=sample.learning_goal,
        semantic_targets=sample.peis_projection.target_refs,
        verified_context_refs=sample.verified_subject.source_refs,
        peis_projection_version=sample.peis_projection.projection_version,
        peis_projection_ref=sample.peis_projection.projection_ref,
        help_state=sample.help_state,
        verification_required=sample.policy.verification_required,
        structured_history_summary=tuple(
            f"{entry.role}:{entry.text}" for entry in sample.history
        ),
        continuation_marker=sample.continuation_marker,
    )


def failed(kind: FailureClass) -> ProviderFault:
    return ProviderFault(kind, "fixture-only")


def gateway(primary_outcomes, secondary_outcomes):
    primary = ScriptedFakeProvider("fake-primary", list(primary_outcomes))
    secondary = ScriptedFakeProvider("fake-secondary", list(secondary_outcomes))
    registry = {
        ("fake-primary", "text"): ProviderPath(
            "fake-primary", "text", "fake.v1", "PRODUCTION_ADMITTED", 1
        ),
        ("fake-secondary", "text"): ProviderPath(
            "fake-secondary", "text", "fake.v1", "PRODUCTION_ADMITTED", 2
        ),
    }
    runner = ReliabilityGateway(
        registry,
        {primary.provider_id: primary, secondary.provider_id: secondary},
    )
    return runner, primary, secondary


def main() -> int:
    try:
        ReliabilityGateway(
            {},
            {},
            GatewayConfig(transient_failures_before_open=0),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid transient circuit threshold was accepted")

    runner, primary, secondary = gateway(
        [failed(FailureClass.TIMEOUT), healthy()],
        [healthy()],
    )
    result = runner.handle_turn(episode("recover-on-retry"), turn())
    circuit = runner.circuits[("fake-primary", "text")]
    require(
        result.status == "TUTOR_ADVISORY"
        and len(primary.attempts) == 2
        and len(secondary.attempts) == 0,
        "single transient failure may recover on bounded same-path retry",
    )
    require(
        circuit.state is CircuitState.CLOSED
        and circuit.health is HealthState.HEALTHY
        and circuit.consecutive_failures == 0,
        "successful retry resets transient failure state",
    )

    runner, primary, secondary = gateway(
        [failed(FailureClass.TIMEOUT), failed(FailureClass.TIMEOUT)],
        [healthy()],
    )
    result = runner.handle_turn(episode("repeat-timeout"), turn())
    circuit = runner.circuits[("fake-primary", "text")]
    require(
        result.status == "TUTOR_ADVISORY"
        and circuit.state is CircuitState.OPEN
        and circuit.health is HealthState.OPEN_CIRCUIT
        and circuit.consecutive_failures == 2
        and len(secondary.attempts) == 1,
        "repeated timeout opens primary circuit and fallback succeeds",
    )

    malformed = ProviderResponse(text="placeholder")
    object.__setattr__(malformed, "text", 17)
    runner, primary, secondary = gateway([malformed, malformed], [healthy()])
    result = runner.handle_turn(episode("repeat-malformed"), turn())
    circuit = runner.circuits[("fake-primary", "text")]
    require(
        circuit.state is CircuitState.OPEN
        and result.accepted_attempt_id == secondary.attempts[0].provider_attempt_id,
        "repeated malformed ProviderResponse opens circuit and cannot be accepted",
    )
    require(
        result.learner_quota_debit_count == 1
        and result.evidence_verification_commit_count == 1
        and result.direct_canonical_peis_writes == 0,
        "fallback still preserves exactly-once quota/evidence and zero direct PEIS writes",
    )

    runner, primary, secondary = gateway(
        [
            failed(FailureClass.TIMEOUT),
            failed(FailureClass.TIMEOUT),
            failed(FailureClass.TIMEOUT),
            healthy(),
        ],
        [healthy(), healthy()],
    )
    runner.handle_turn(episode("open"), turn())
    require(
        runner.circuits[("fake-primary", "text")].state is CircuitState.OPEN,
        "transient threshold opens circuit before recovery",
    )
    runner.tick += 2
    runner.handle_turn(episode("half-open-fail"), turn())
    require(
        runner.circuits[("fake-primary", "text")].state is CircuitState.OPEN,
        "failed half-open probe immediately reopens circuit",
    )
    runner.tick += 2
    runner.handle_turn(episode("half-open-success"), turn())
    circuit = runner.circuits[("fake-primary", "text")]
    require(
        circuit.state is CircuitState.CLOSED
        and circuit.health is HealthState.HEALTHY
        and circuit.consecutive_failures == 0,
        "successful half-open probe closes circuit and resets failure state",
    )

    print("AI_TUTOR_RELIABILITY_CIRCUIT_REPAIR_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
