#!/usr/bin/env python3
"""Fast private acceptance assembly for OpenAI vs Yandex Tutor brains.

This lane intentionally avoids the branch-authored ru-* acceptance overlay.  It
uses the already merged reviewed 121-card Russian grounding path and one exact
production-shaped card for the imminent human provider comparison.

Fast voice acceptance uses the existing bounded SpeechKit v1 REST STT with the
same SpeechKit v3 Lera TTS for both brains.  Production realtime STT remains the
separate SpeechKit v3 gRPC-streaming target; this benchmark must never be
represented as production streaming acceptance.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from openai_live_adapter import OpenAICredential, OpenAITextConfig, OpenAITextProvider
from openai_secret_provider import OpenAISecretProvider
from reliability_gateway import ProviderPath, ReliabilityGateway
from sep1_russian_tutor import (
    RussianTutorVerticalSlice,
    TutorInteraction,
    TutorSliceError,
    VoiceGateway,
    VoiceProviderFailure,
)
from stdlib_json_transport import UrllibJsonTransport
from stdlib_speechkit_transport import UrllibBinaryTransport, UrllibFormBytesTransport
from yandex_alice_live_adapter import YandexAliceTextProvider, YandexAliceTutorConfig
from yandex_live_adapters import CredentialKind, YandexCredential, YandexSpeechConfig, YandexSpeechKitProvider
from yandex_speech_secret_provider import YandexSpeechSecretProvider
from yandex_speechkit_v3_tts import (
    UrllibStreamingJsonTransport,
    YandexHybridSpeechProvider,
    YandexSpeechKitV3TTS,
    YandexSpeechKitV3TTSConfig,
)

BrainMode = Literal["openai", "yandex"]
BENCHMARK_CARD_ID = "ex-practice-alt-sochetat-001"
BENCHMARK_SEMANTIC_ID = "school-i-e-alternating-verb-roots-stressed-a"
OPENAI_BENCHMARK_MODEL = "gpt-5.6-sol"
YANDEX_BENCHMARK_MODEL_ID = "aliceai-llm"


class FastTutorConfigurationError(ValueError):
    pass


class ResilientRussian121Tutor(RussianTutorVerticalSlice):
    """Keep one accepted text turn even when TTS fails; STT failure makes no LLM turn."""

    def voice_turn(self, session_ref: str, audio: bytes) -> TutorInteraction:
        state = self._state(session_ref)
        if not isinstance(audio, bytes) or not audio:
            raise TutorSliceError("non-empty transient learner audio is required")
        try:
            asr = self.voice_gateway.transcribe(audio, session_ref=session_ref)
        except VoiceProviderFailure as exc:
            raise TutorSliceError("voice input unavailable; retry speech or use text") from exc
        transcript = str(asr.value).strip()
        if not transcript:
            raise TutorSliceError("voice input returned an empty transcript")

        state.raw_audio_inputs_seen += 1
        state.asr_provider_log.append(asr.provider_id)
        interaction = self._text_turn(state, transcript, modality="voice")

        try:
            tts = self.voice_gateway.synthesize(interaction.tutor_text, session_ref=session_ref)
        except VoiceProviderFailure:
            return TutorInteraction(
                session_ref=interaction.session_ref,
                turn_id=interaction.turn_id,
                modality="voice-text-fallback",
                transcript=interaction.transcript,
                tutor_text=interaction.tutor_text,
                reliable_result=interaction.reliable_result,
                asr_provider_id=asr.provider_id,
                tts_provider_id=None,
                audio=None,
            )

        if not isinstance(tts.value, bytes) or not tts.value:
            return TutorInteraction(
                session_ref=interaction.session_ref,
                turn_id=interaction.turn_id,
                modality="voice-text-fallback",
                transcript=interaction.transcript,
                tutor_text=interaction.tutor_text,
                reliable_result=interaction.reliable_result,
                asr_provider_id=asr.provider_id,
                tts_provider_id=None,
                audio=None,
            )

        state.tts_provider_log.append(tts.provider_id)
        state.synthesized_audio_outputs_seen += 1
        return TutorInteraction(
            session_ref=interaction.session_ref,
            turn_id=interaction.turn_id,
            modality="voice",
            transcript=interaction.transcript,
            tutor_text=interaction.tutor_text,
            reliable_result=interaction.reliable_result,
            asr_provider_id=asr.provider_id,
            tts_provider_id=tts.provider_id,
            audio=tts.value,
        )


@dataclass(frozen=True)
class FastTutorConfig:
    brain_mode: BrainMode
    yandex_folder_id: str | None = None
    openai_model: str = OPENAI_BENCHMARK_MODEL
    yandex_model_id: str = YANDEX_BENCHMARK_MODEL_ID
    yandex_voice: str = "lera"
    yandex_voice_role: str = "neutral"
    yandex_voice_speed: float = 1.04
    owner_live_authorized: bool = False
    text_execution_enabled: bool = False
    speech_execution_enabled: bool = False
    public_traffic_enabled: bool = False

    def __post_init__(self) -> None:
        if self.brain_mode not in {"openai", "yandex"}:
            raise FastTutorConfigurationError("fast acceptance allows only openai or yandex")
        if self.openai_model != OPENAI_BENCHMARK_MODEL:
            raise FastTutorConfigurationError("human benchmark OpenAI model is locked to gpt-5.6-sol")
        if self.yandex_model_id != YANDEX_BENCHMARK_MODEL_ID:
            raise FastTutorConfigurationError("human benchmark Yandex brain is locked to full-size Alice AI LLM")
        if self.public_traffic_enabled:
            raise FastTutorConfigurationError("fast acceptance is localhost/private only")
        if (self.text_execution_enabled or self.speech_execution_enabled) and not self.owner_live_authorized:
            raise FastTutorConfigurationError("live provider execution requires explicit owner authorization")
        if self.yandex_voice != "lera" or self.yandex_voice_role != "neutral" or abs(self.yandex_voice_speed - 1.04) > 0.0001:
            raise FastTutorConfigurationError("voice benchmark is locked to Lera / neutral / 1.04")
        if self.speech_execution_enabled and not self.resolved_yandex_folder_id:
            raise FastTutorConfigurationError("voice benchmark requires YANDEX_FOLDER_ID")
        if self.brain_mode == "yandex" and self.text_execution_enabled and not self.resolved_yandex_folder_id:
            raise FastTutorConfigurationError("Alice AI live execution requires YANDEX_FOLDER_ID")

    @property
    def resolved_yandex_folder_id(self) -> str | None:
        return self.yandex_folder_id or os.environ.get("YANDEX_FOLDER_ID") or None


@dataclass(frozen=True)
class FastTutorAssembly:
    tutor: ResilientRussian121Tutor
    brain_provider: object
    speech_provider: YandexHybridSpeechProvider
    config: FastTutorConfig

    @property
    def exact_brain_model(self) -> str:
        if self.config.brain_mode == "openai":
            return self.config.openai_model
        folder = self.config.resolved_yandex_folder_id or "unresolved-folder"
        return f"gpt://{folder}/{self.config.yandex_model_id}/latest"

    def safety_snapshot(self) -> dict[str, object]:
        return {
            "brain_mode": self.config.brain_mode,
            "brain_provider_id": getattr(self.brain_provider, "provider_id", "unknown"),
            "exact_brain_model": self.exact_brain_model,
            "benchmark_card_id": BENCHMARK_CARD_ID,
            "benchmark_semantic_id": BENCHMARK_SEMANTIC_ID,
            "public_traffic_enabled": False,
            "production_peis_writes_enabled": False,
            "learner_audio_persisted_bytes": 0,
            "benchmark_stt_contract": "speechkit-v1-bounded-rest",
            "production_stt_target": "speechkit-v3-grpc-streaming",
            "tts_contract": "speechkit-v3-rest",
            "tts_voice": "lera",
            "tts_role": "neutral",
            "tts_speed": 1.04,
        }


def assemble_fast_tutor(
    *,
    engine_root: str | Path,
    config: FastTutorConfig,
    openai_transport=None,
    yandex_text_transport=None,
    stt_transport=None,
    tts_v3_transport=None,
    session_ref_factory=None,
) -> FastTutorAssembly:
    json_transport = UrllibJsonTransport
    if config.brain_mode == "openai":
        provider = OpenAITextProvider(
            config=OpenAITextConfig(
                credential=OpenAICredential(OpenAISecretProvider()),
                model=config.openai_model,
                execution_enabled=config.text_execution_enabled,
            ),
            transport=openai_transport or json_transport(),
        )
    else:
        provider = YandexAliceTextProvider(
            config=YandexAliceTutorConfig(
                folder_id=config.resolved_yandex_folder_id,
                model_id=config.yandex_model_id,
                execution_enabled=config.text_execution_enabled,
            ),
            transport=yandex_text_transport or json_transport(),
        )

    provider_id = getattr(provider, "provider_id")
    registry = {
        (provider_id, "text"): ProviderPath(
            provider_id,
            "text",
            f"{config.brain_mode}-fast-human-acceptance-v1",
            "PRODUCTION_ADMITTED",
            1,
        )
    }
    text_gateway = ReliabilityGateway(registry, {provider_id: provider})  # type: ignore[arg-type]

    speech_credential = YandexCredential(CredentialKind.API_KEY, YandexSpeechSecretProvider())
    stt_provider = YandexSpeechKitProvider(
        config=YandexSpeechConfig(
            credential=speech_credential,
            voice="lera",
            folder_id=config.resolved_yandex_folder_id,
            stt_audio_format="lpcm",
            tts_audio_format="oggopus",
            stt_sample_rate_hertz=16_000,
            execution_enabled=config.speech_execution_enabled,
        ),
        stt_transport=stt_transport or UrllibBinaryTransport(),
        tts_transport=UrllibFormBytesTransport(),
    )
    tts_provider = YandexSpeechKitV3TTS(
        config=YandexSpeechKitV3TTSConfig(
            credential=speech_credential,
            voice=config.yandex_voice,
            role=config.yandex_voice_role,
            speed=config.yandex_voice_speed,
            execution_enabled=config.speech_execution_enabled,
        ),
        transport=tts_v3_transport or UrllibStreamingJsonTransport(),
    )
    speech_provider = YandexHybridSpeechProvider(stt_provider=stt_provider, tts_provider=tts_provider)
    voice_gateway = VoiceGateway([speech_provider])  # type: ignore[list-item]

    tutor = ResilientRussian121Tutor(
        engine_root=engine_root,
        text_gateway=text_gateway,
        voice_gateway=voice_gateway,
        session_ref_factory=session_ref_factory,
    )
    return FastTutorAssembly(tutor=tutor, brain_provider=provider, speech_provider=speech_provider, config=config)


def open_benchmark_session(assembly: FastTutorAssembly, learner_profile_id: str):
    state = assembly.tutor.open_session(learner_profile_id=learner_profile_id, card_id=BENCHMARK_CARD_ID)
    if state.grounding.semantic_id != BENCHMARK_SEMANTIC_ID:
        raise FastTutorConfigurationError("merged 121-card benchmark semantic drift")
    if state.grounding.mapping_resolution != "EXACT":
        raise FastTutorConfigurationError("benchmark card is no longer EXACT")
    return state
