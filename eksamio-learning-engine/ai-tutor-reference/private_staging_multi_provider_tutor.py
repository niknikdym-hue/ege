#!/usr/bin/env python3
"""Private-staging Eksamio Tutor with three interchangeable text brains.

Text priority in AUTO mode is OpenAI -> Qwen -> Yandex Alice AI. Forced modes
exist only for controlled human comparison. Russian speech remains Yandex
SpeechKit only. Provider execution is disabled by default and requires explicit
owner authorization.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from openai_live_adapter import OpenAICredential, OpenAITextConfig, OpenAITextProvider
from openai_secret_provider import OpenAISecretProvider
from qwen_live_adapter import QwenTextProvider, QwenTutorConfig
from reliability_gateway import ProviderPath, ReliabilityGateway
from resilient_voice_tutor import ResilientAcceptedSemanticTutor
from sep1_russian_tutor import VoiceGateway
from stdlib_json_transport import UrllibJsonTransport
from stdlib_speechkit_transport import UrllibBinaryTransport, UrllibFormBytesTransport
from yandex_alice_live_adapter import YandexAliceTextProvider, YandexAliceTutorConfig
from yandex_live_adapters import (
    BinaryTransport,
    CredentialKind,
    YandexCredential,
    YandexSpeechConfig,
    YandexSpeechKitProvider,
)
from yandex_speech_secret_provider import YandexSpeechSecretProvider
from yandex_speechkit_v3_tts import (
    StreamingJsonTransport,
    UrllibStreamingJsonTransport,
    YandexHybridSpeechProvider,
    YandexSpeechKitV3TTS,
    YandexSpeechKitV3TTSConfig,
)


TextProviderMode = Literal["auto", "openai", "qwen", "yandex"]


class PrivateMultiProviderConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class PrivateMultiProviderTutorConfig:
    yandex_voice: str = "lera"
    yandex_voice_role: str = "neutral"
    yandex_voice_speed: float = 1.04
    text_provider_mode: TextProviderMode = "auto"
    openai_model: str = "gpt-5.6-terra"
    qwen_model: str = "qwen3.8-max"
    qwen_base_url: str | None = None
    yandex_folder_id: str | None = None
    yandex_model_id: str = "aliceai-llm"
    speech_stt_audio_format: str = "lpcm"
    speech_stt_sample_rate_hertz: int = 16_000
    private_staging: bool = True
    public_traffic_enabled: bool = False
    owner_live_authorized: bool = False
    text_execution_enabled: bool = False
    speech_execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.text_provider_mode not in {"auto", "openai", "qwen", "yandex"}:
            raise PrivateMultiProviderConfigurationError("unknown Tutor text provider mode")
        if not self.private_staging:
            raise PrivateMultiProviderConfigurationError("this assembly is private-staging only")
        if self.public_traffic_enabled:
            raise PrivateMultiProviderConfigurationError("Tutor private staging cannot enable public traffic")
        if (self.text_execution_enabled or self.speech_execution_enabled) and not self.owner_live_authorized:
            raise PrivateMultiProviderConfigurationError("live provider execution requires explicit owner authorization")
        if self.yandex_voice != "lera" or self.yandex_voice_role != "neutral" or abs(self.yandex_voice_speed - 1.04) > 0.0001:
            raise PrivateMultiProviderConfigurationError("Tutor Yandex voice profile is locked to Lera / neutral / 1.04")
        if self.speech_stt_audio_format != "lpcm" or self.speech_stt_sample_rate_hertz != 16_000:
            raise PrivateMultiProviderConfigurationError(
                "private browser voice test is locked to mono LPCM 16 kHz input"
            )

    @property
    def resolved_yandex_folder_id(self) -> str | None:
        return self.yandex_folder_id or os.environ.get("YANDEX_FOLDER_ID") or None


@dataclass(frozen=True)
class PrivateMultiProviderTutorAssembly:
    tutor: ResilientAcceptedSemanticTutor
    text_providers: tuple[object, ...]
    speech_provider: YandexHybridSpeechProvider
    config: PrivateMultiProviderTutorConfig

    def safety_snapshot(self) -> dict[str, object]:
        registry = self.tutor.text_gateway.registry
        ordered = sorted(
            (path for path in registry.values() if path.capability == "text"),
            key=lambda path: path.priority,
        )
        return {
            "private_staging": self.config.private_staging,
            "public_traffic_enabled": self.config.public_traffic_enabled,
            "owner_live_authorized": self.config.owner_live_authorized,
            "text_execution_enabled": self.config.text_execution_enabled,
            "speech_execution_enabled": self.config.speech_execution_enabled,
            "text_provider_mode": self.config.text_provider_mode,
            "text_provider_order": [path.provider_id for path in ordered],
            "stt_provider": self.speech_provider.provider_id,
            "tts_provider": self.speech_provider.provider_id,
            "stt_format": self.speech_provider.stt_provider.config.resolved_stt_format,
            "stt_sample_rate_hertz": self.speech_provider.stt_provider.config.stt_sample_rate_hertz,
            "tts_api": "v3-rest",
            "tts_voice": self.speech_provider.tts_provider.config.voice,
            "tts_role": self.speech_provider.tts_provider.config.role,
            "tts_speed": self.speech_provider.tts_provider.config.speed,
            "tts_container": self.speech_provider.tts_provider.config.container_audio_type,
            "voice_text_fallback_enabled": True,
            "accepted_semantic_count": len(self.tutor.accepted_semantics.semantic_ids),
            "learner_audio_persisted_bytes": 0,
        }


def assemble_private_multi_provider_tutor(
    *,
    engine_root: str | Path,
    config: PrivateMultiProviderTutorConfig,
    openai_transport=None,
    qwen_transport=None,
    yandex_text_transport=None,
    stt_transport: BinaryTransport | None = None,
    tts_v3_transport: StreamingJsonTransport | None = None,
    session_ref_factory=None,
) -> PrivateMultiProviderTutorAssembly:
    def text_enabled(name: str) -> bool:
        return config.text_execution_enabled and config.text_provider_mode in {"auto", name}

    openai_provider = OpenAITextProvider(
        config=OpenAITextConfig(
            credential=OpenAICredential(OpenAISecretProvider()),
            model=config.openai_model,
            execution_enabled=text_enabled("openai"),
        ),
        transport=openai_transport or UrllibJsonTransport(),
    )
    qwen_provider = QwenTextProvider(
        config=QwenTutorConfig(
            model=config.qwen_model,
            base_url=config.qwen_base_url,
            execution_enabled=text_enabled("qwen"),
        ),
        transport=qwen_transport or UrllibJsonTransport(),
    )
    yandex_provider = YandexAliceTextProvider(
        config=YandexAliceTutorConfig(
            folder_id=config.resolved_yandex_folder_id,
            model_id=config.yandex_model_id,
            execution_enabled=text_enabled("yandex"),
        ),
        transport=yandex_text_transport or UrllibJsonTransport(),
    )

    by_name = {
        "openai": openai_provider,
        "qwen": qwen_provider,
        "yandex": yandex_provider,
    }
    selected_names = ("openai", "qwen", "yandex") if config.text_provider_mode == "auto" else (config.text_provider_mode,)

    registry: dict[tuple[str, str], ProviderPath] = {}
    providers: dict[str, object] = {}
    for priority, name in enumerate(selected_names, start=1):
        provider = by_name[name]
        provider_id = provider.provider_id
        registry[(provider_id, "text")] = ProviderPath(
            provider_id,
            "text",
            f"{name}-tutor-private-staging-v1",
            "PRODUCTION_ADMITTED",
            priority,
        )
        providers[provider_id] = provider
    text_gateway = ReliabilityGateway(registry, providers)  # type: ignore[arg-type]

    speech_credential = YandexCredential(CredentialKind.API_KEY, YandexSpeechSecretProvider())
    stt_provider = YandexSpeechKitProvider(
        config=YandexSpeechConfig(
            credential=speech_credential,
            voice="lera",
            folder_id=config.resolved_yandex_folder_id,
            stt_audio_format=config.speech_stt_audio_format,
            tts_audio_format="oggopus",
            stt_sample_rate_hertz=config.speech_stt_sample_rate_hertz,
            execution_enabled=config.speech_execution_enabled,
        ),
        stt_transport=stt_transport or UrllibBinaryTransport(),
        # v1 synthesis is deliberately not used; this satisfies the retained adapter contract only.
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

    tutor = ResilientAcceptedSemanticTutor(
        engine_root=engine_root,
        text_gateway=text_gateway,
        voice_gateway=voice_gateway,
        session_ref_factory=session_ref_factory,
    )
    return PrivateMultiProviderTutorAssembly(
        tutor=tutor,
        text_providers=tuple(by_name[name] for name in selected_names),
        speech_provider=speech_provider,
        config=config,
    )
