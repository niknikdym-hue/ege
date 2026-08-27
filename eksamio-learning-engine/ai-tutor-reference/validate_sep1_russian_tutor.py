#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(ENGINE / "peis-production-substrate"),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
]

from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_service_bridge import AdapterRegistry, HostIdentity, PeisServiceBridge  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from reliability_gateway import (  # noqa: E402
    DelayedProviderSuccess,
    FailureClass,
    GatewayConfig,
    ProviderAttempt,
    ProviderOutcome,
    ProviderPath,
    ReliabilityGateway,
)
from russian_exceptions_practice_adapter import (  # noqa: E402
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)
from sep1_russian_tutor import (  # noqa: E402
    GroundedTextProvider,
    MockSpeechProvider,
    RussianTutorVerticalSlice,
    VoiceGateway,
)
from tutor_boundary import ProviderRequest, ProviderResponse  # noqa: E402


class DelayedOnceProvider:
    provider_id = "late-primary"

    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        self.calls += 1
        response = ProviderResponse(
            text="late grounded fixture",
            source_refs=request.verified_source_refs,
        )
        if self.calls == 1:
            return DelayedProviderSuccess(response)
        return response


def make_text_gateway() -> ReliabilityGateway:
    primary = GroundedTextProvider(
        "text-primary-mock",
        fail_once=FailureClass.CREDENTIAL_OR_ACCOUNT_FAILURE,
    )
    reserve = GroundedTextProvider("text-reserve-mock")
    registry = {
        ("text-primary-mock", "text"): ProviderPath(
            "text-primary-mock", "text", "fixture-v1", "PRODUCTION_ADMITTED", 1
        ),
        ("text-reserve-mock", "text"): ProviderPath(
            "text-reserve-mock", "text", "fixture-v1", "PRODUCTION_ADMITTED", 2
        ),
    }
    return ReliabilityGateway(registry, {primary.provider_id: primary, reserve.provider_id: reserve})


def validate_late_response_discard(turn_service: RussianTutorVerticalSlice, session_ref: str) -> None:
    grounding = turn_service.sessions[session_ref].grounding
    delayed = DelayedOnceProvider()
    reserve = GroundedTextProvider("late-reserve")
    registry = {
        ("late-primary", "text"): ProviderPath("late-primary", "text", "fixture-v1", "PRODUCTION_ADMITTED", 1),
        ("late-reserve", "text"): ProviderPath("late-reserve", "text", "fixture-v1", "PRODUCTION_ADMITTED", 2),
    }
    gateway = ReliabilityGateway(
        registry,
        {"late-primary": delayed, "late-reserve": reserve},
        GatewayConfig(max_same_path_retries=0),
    )
    # Reuse the service constructor purely to build a new server-owned logical session.
    voice = turn_service.voice_gateway
    test_service = RussianTutorVerticalSlice(
        engine_root=ENGINE,
        text_gateway=gateway,
        voice_gateway=voice,
        session_ref_factory=lambda: "tutor:late-response-audit",
    )
    state = test_service.open_session(
        learner_profile_id="learner:tutor-late-audit",
        card_id=grounding.card_id,
    )
    interaction = test_service.text_turn(state.session_ref, "Объясни правило по проверенному материалу")
    assert interaction.reliable_result.status == "TUTOR_ADVISORY"
    delayed_ids = list(gateway.delayed)
    assert len(delayed_ids) == 1
    assert gateway.deliver_late_success(delayed_ids[0], interaction_to_episode(test_service, state.session_ref, interaction.turn_id)) is False
    assert any(event.event_type == "late_response_discarded" for event in gateway.events)


def interaction_to_episode(service: RussianTutorVerticalSlice, session_ref: str, turn_id: str):
    # The delayed-delivery API needs only episode/turn IDs for audit event projection.
    from reliability_gateway import EpisodeProjection

    state = service.sessions[session_ref]
    grounding = state.grounding
    return EpisodeProjection(
        episode_id=session_ref,
        turn_id=turn_id,
        learning_goal=f"understand:{grounding.semantic_id}",
        semantic_targets=(grounding.semantic_id,),
        verified_context_refs=(grounding.source_ref,),
        peis_projection_version="sep1-russian-tutor-v1",
        peis_projection_ref=f"server-projection:{state.learner_profile_id}:{grounding.semantic_id}",
        help_state="GUIDED_HELP",
        verification_required=True,
        structured_history_summary=(),
        continuation_marker=session_ref,
    )


def main() -> int:
    text_gateway = make_text_gateway()
    yandex = MockSpeechProvider(
        "yandex-speechkit-mock",
        transcript="Почему в слове сочетание пишется е?",
        fail_asr_once=True,
    )
    openai = MockSpeechProvider(
        "openai-voice-reserve-mock",
        transcript="Почему в слове сочетание пишется е?",
    )
    voice_gateway = VoiceGateway([yandex, openai])
    service = RussianTutorVerticalSlice(
        engine_root=ENGINE,
        text_gateway=text_gateway,
        voice_gateway=voice_gateway,
        session_ref_factory=lambda: "tutor:sep1-russian-001",
    )
    state = service.open_session(
        learner_profile_id="learner:tutor-sep1-001",
        card_id=FIRST_SLICE_CARD_ID,
    )

    # Grounding must be the accepted mapping already present in current main.
    assert state.grounding.card_id == FIRST_SLICE_CARD_ID
    assert state.grounding.semantic_id == "school-i-e-alternating-verb-roots-stressed-a"
    assert state.grounding.mapping_resolution == "EXACT"
    assert state.grounding.source_ref.startswith("source:russian-reviewed-card:")

    # Text path: primary fixture is blocked once, existing reliability gateway falls back.
    text = service.text_turn(state.session_ref, "Объясни, почему пишется «сочетание»")
    assert text.session_ref == state.session_ref
    assert text.reliable_result.status == "TUTOR_ADVISORY"
    assert text.reliable_result.learner_quota_debit_count == 1
    assert text.reliable_result.evidence_verification_commit_count == 1
    assert text.reliable_result.accepted_attempt_id is not None
    assert "text-reserve-mock" in text.reliable_result.accepted_attempt_id
    assert text.reliable_result.tutor_result is not None
    assert text.reliable_result.tutor_result.accepted_source_refs == (state.grounding.source_ref,)
    assert state.grounding.explanation in text.tutor_text

    # Same logical session: transient learner audio -> ASR -> grounded text -> TTS.
    learner_audio = b"TRANSIENT_LEARNER_AUDIO_FIXTURE_DO_NOT_PERSIST"
    voice = service.voice_turn(state.session_ref, learner_audio)
    assert voice.session_ref == text.session_ref
    assert voice.modality == "voice"
    assert voice.transcript == "Почему в слове сочетание пишется е?"
    # Yandex is preferred but intentionally fails ASR once; reserve handles this turn.
    assert voice.asr_provider_id == "openai-voice-reserve-mock"
    # Yandex TTS remains healthy and is selected first.
    assert voice.tts_provider_id == "yandex-speechkit-mock"
    assert isinstance(voice.audio, bytes) and voice.audio
    assert state.modality_log == ["text", "voice"]
    assert len(state.history) == 4
    assert state.raw_audio_inputs_seen == 1
    assert state.raw_audio_persistence_count() == 0
    assert learner_audio not in repr(vars(state)).encode("utf-8")

    # Provider kill switch preserves the same voice contract through reserve.
    voice_gateway.set_disabled("yandex-speechkit-mock", True)
    killed = voice_gateway.synthesize("Проверка резервного TTS", session_ref=state.session_ref)
    assert killed.provider_id == "openai-voice-reserve-mock"
    assert killed.fallback_used is False  # disabled provider is not attempted
    voice_gateway.set_disabled("yandex-speechkit-mock", False)

    validate_late_response_discard(service, state.session_ref)

    # Independent verification after Tutor help goes through the already merged
    # Russian reviewed-card adapter -> shared PEIS PostgreSQL path exactly once.
    dsn = os.environ["PEIS_DATABASE_DSN"]
    evidence_schema = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8")
    )
    nba_schema = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(encoding="utf-8")
    )
    peis_store = PostgresPeisPersistenceStore(dsn, evidence_schema=evidence_schema, nba_schema=nba_schema)
    assert peis_store.readiness()
    adapter = RussianExceptionsPracticeAdapter(ENGINE)
    registry = AdapterRegistry()
    registry.register(adapter)
    bridge = PeisServiceBridge(
        store=peis_store,
        registry=registry,
        kernel_snapshot=kernel_snapshot,
        now_provider=lambda: "2026-08-27T03:50:00+00:00",
    )
    identity = HostIdentity(
        learner_profile_id=state.learner_profile_id,
        identity_refs={"anonymous_identity_ref": "anon:tutor-sep1-001"},
    )
    verification_payload = {
        "card_id": FIRST_SLICE_CARD_ID,
        "session_started_at_ms": 1800000000000,
        "session_mode": "practice",
        "answer": state.grounding.correct_answer,
        "occurred_at_client": "2026-08-27T03:49:59+00:00",
        "client_request_id": "req:tutor-independent-verification-001",
    }
    first = bridge.submit_checked_card(
        adapter_id=adapter.adapter_id,
        payload=verification_payload,
        host_identity=identity,
    )
    assert first["status"] == "ACCEPTED"
    replay = bridge.submit_checked_card(
        adapter_id=adapter.adapter_id,
        payload=dict(verification_payload),
        host_identity=identity,
    )
    assert replay["status"] == "ALREADY_APPLIED"
    events = peis_store.list_events(state.learner_profile_id, "russian", effective=False)
    assert len(events) == 1
    event = events[0]
    assert event["source"]["object_id"] == FIRST_SLICE_CARD_ID
    assert event["semantic_targets"][0]["semantic_id"] == state.grounding.semantic_id
    assert event["result"]["correctness"] is True
    assert event["result"]["score"] == event["result"]["max_score"]
    serialized_event = json.dumps(event, ensure_ascii=False, sort_keys=True)
    assert "TRANSIENT_LEARNER_AUDIO_FIXTURE_DO_NOT_PERSIST" not in serialized_event
    assert "MOCK_AUDIO|" not in serialized_event

    print("SEP1_RUSSIAN_TUTOR_VERTICAL_SLICE=PASS")
    print(f"session_ref={state.session_ref}")
    print(f"grounding_card={state.grounding.card_id}")
    print(f"grounding_semantic={state.grounding.semantic_id}")
    print("text_grounded=PASS")
    print("same_session_voice_text_voice=PASS")
    print("yandex_preferred_voice=PASS")
    print("voice_fallback_and_kill_switch=PASS")
    print("late_response_discard=PASS")
    print("raw_learner_audio_persisted=0")
    print("peis_independent_verification_events=1")
    print("peis_replay=ALREADY_APPLIED")
    print("external_provider_calls=0")
    print("production_billing=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
