#!/usr/bin/env python3
"""Private-staging Russian Tutor with OpenAI text + Yandex SpeechKit voice.

This is an additive assembly. It reuses the existing accepted-semantic Tutor,
ReliabilityGateway and SpeechKit adapter. Provider execution is OFF by default.
Credentials are lazy and auto-resolve from server environment or the owner's
existing macOS Keychain entries; callers never pass secret values.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from accepted_russian_semantic_tutor import AcceptedSemanticRussianTutorVerticalSlice
from openai_live_adapter import OpenAICredential, OpenAITextConfig, OpenAITextProvider
from openai_secret_provider import OpenAISecretProvider
from reliability_gateway import ProviderPath, ReliabilityGateway
from sep1_russian_tutor import VoiceGateway
from stdlib_json_transport import UrllibJsonTransport
from yandex_live_adapters import (
    BinaryTransport,
    CredentialKind,
    FormBytesTransport,
    YandexCredential,
    YandexSpeechConfig,
    YandexSpeechKitProvider,
)
from yandex_speech_secret_provider import YandexSpeechSecretProvider


class PrivateOpenAIYandexConfigurationError(ValueError):
    pass


class _DisabledBinaryTransport:
    def post_binary(self, **kwargs: Any):
        raise AssertionError("SpeechKit STT transport is not configured")


class _DisabledFormTransport:
    def post_form_bytes(self, **kwargs: Any):
        raise AssertionError("SpeechKit TTS transport is not configured")


@dataclass(frozen=True)
class PrivateOpenAIYandexTutorConfig:
    yandex_voice: str
    openai_model: str = "gpt-5.6-terra"
    yandex_folder_id: str | None = None
    private_staging: bool = True
    public_traffic_enabled: bool = False
    owner_live_authorized: bool = False
    text_execution_enabled: bool = False
    speech_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.private_staging:
            raise PrivateOpenAIYandexConfigurationError("this assembly is private-staging only")
        if self.public_traffic_enabled:
            raise PrivateOpenAIYandexConfigurationError("Tutor private staging cannot enable public traffic")
        if (self.text_execution_enabled or self.speech_execution_enabled) and not self.owner_live_authorized:
            raise PrivateOpenAIYandexConfigurationError(
                "live provider execution requires explicit owner authorization"
            )
        if not self.yandex_voice:
            raise PrivateOpenAIYandexConfigurationError("Yandex Tutor voice must be configured")


@dataclass(frozen=True)
class PrivateOpenAIYandexTutorAssembly:
    tutor: AcceptedSemanticRussianTutorVerticalSlice
    text_provider: OpenAITextProvider
    speech_provider: YandexSpeechKitProvider
    config: PrivateOpenAIYandexTutorConfig

    def safety_snapshot(self) -> dict[str, object]:
        return {
            "private_staging": self.config.private_staging,
            "public_traffic_enabled": self.config.public_traffic_enabled,
            "owner_live_authorized": self.config.owner_live_authorized,
            "openai_text_execution_enabled": self.config.text_execution_enabled,
            "yandex_speech_execution_enabled": self.config.speech_execution_enabled,
            "accepted_semantic_count": len(self.tutor.accepted_semantics.semantic_ids),
            "learner_audio_persisted_bytes": 0,
        }


def assemble_private_openai_yandex_tutor(
    *,
    engine_root: str | Path,
    config: PrivateOpenAIYandexTutorConfig,
    text_transport: UrllibJsonTransport | None = None,
    stt_transport: BinaryTransport | None = None,
    tts_transport: FormBytesTransport | None = None,
    session_ref_factory=None,
) -> PrivateOpenAIYandexTutorAssembly:
    if config.speech_execution_enabled and (stt_transport is None or tts_transport is None):
        raise PrivateOpenAIYandexConfigurationError(
            "live SpeechKit execution requires explicit transient STT/TTS transports"
        )

    openai_credential = OpenAICredential(OpenAISecretProvider())
    openai_provider = OpenAITextProvider(
        config=OpenAITextConfig(
            credential=openai_credential,
            model=config.openai_model,
            execution_enabled=config.text_execution_enabled,
        ),
        transport=text_transport or UrllibJsonTransport(),
    )
    text_gateway = ReliabilityGateway(
        {
            (openai_provider.provider_id, "text"): ProviderPath(
                openai_provider.provider_id,
                "text",
                "openai-responses-private-staging-v1",
                "PRODUCTION_ADMITTED",
                1,
            )
        },
        {openai_provider.provider_id: openai_provider},
    )

    speech_provider = YandexSpeechKitProvider(
        config=YandexSpeechConfig(
            credential=YandexCredential(CredentialKind.API_KEY, YandexSpeechSecretProvider()),
            voice=config.yandex_voice,
            folder_id=config.yandex_folder_id,
            execution_enabled=config.speech_execution_enabled,
        ),
        stt_transport=stt_transport or _DisabledBinaryTransport(),
        tts_transport=tts_transport or _DisabledFormTransport(),
    )
    voice_gateway = VoiceGateway([speech_provider])

    tutor = AcceptedSemanticRussianTutorVerticalSlice(
        engine_root=engine_root,
        text_gateway=text_gateway,
        voice_gateway=voice_gateway,
        session_ref_factory=session_ref_factory,
    )
    return PrivateOpenAIYandexTutorAssembly(tutor, openai_provider, speech_provider, config)
