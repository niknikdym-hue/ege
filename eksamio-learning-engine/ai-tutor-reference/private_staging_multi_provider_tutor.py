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
from typing import Any, Literal

from accepted_russian_semantic_tutor import AcceptedSemanticRussianTutorVerticalSlice
from openai_live_adapter import OpenAICredential, OpenAITextConfig, OpenAITextProvider
from openai_secret_provider import OpenAISecretProvider
from qwen_live_adapter import QwenTextProvider, QwenTutorConfig
from reliability_gateway import ProviderPath, ReliabilityGateway
from sep1_russian_tutor import VoiceGateway
from stdlib_json_transport import UrllibJsonTransport
from yandex_alice_live_adapter import YandexAliceTextProvider, YandexAliceTutorConfig
from yandex_live_adapters import (
    BinaryTransport,
    CredentialKind,
    FormBytesTransport,
    YandexCredential,
    YandexSpeechConfig,
    YandexSpeechKitProvider,
)
from yandex_speech_secret_provider import YandexSpeechSecretProvider


TextProviderMode = Literal["auto", "openai", "qwen", "yandex"]


class PrivateMultiProviderConfigurationError(ValueError):
    pass


class _DisabledBinaryTransport:
    def post_binary(self, **kwargs: Any):
        raise AssertionError("SpeechKit STT transport is not configured")


class _DisabledFormTransport:
    def post_form_bytes(self, **kwargs: Any):
        raise AssertionError("SpeechKit TTS transport is not configured")


@dataclass(frozen=True)
class PrivateMultiProviderTutorConfig:
    yandex_voice: str
    text_provider_mode: TextProviderMode = "auto"
    openai_model: str = "gpt-5.6-terra"
    qwen_model: str = "qwen3.8-max"
    qwen_base_url: str | None = None
    yandex_folder_id: str | None = None
    yandex_model_id: str = "aliceai-llm"
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
        if not self.yandex_voice:
            raise PrivateMultiProviderConfigurationError("Yandex Tutor voice must be configured")

    @property
    def resolved_yandex_folder_id(self) -> str | None:
        return self.yandex_folder_id or os.environ.get("YANDEX_FOLDER_ID") or None


@dataclass(frozen=True)
class PrivateMultiProviderTutorAssembly:
    tutor: AcceptedSemanticRussianTutorVerticalSlice
    text_providers: tuple[object, ...]
    speech_provider: YandexSpeechKitProvider
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
            "tts_provider": self.speech_provider.provider_id,
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
    tts_transport: FormBytesTransport | None = None,
    session_ref_factory=None,
) -> PrivateMultiProviderTutorAssembly:
    if config.speech_execution_enabled and (stt_transport is None or tts_transport is None):
        raise PrivateMultiProviderConfigurationError(
            "live SpeechKit execution requires explicit transient STT/TTS transports"
        )

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
    if config.text_provider_mode == "auto":
        selected_names = ("openai", "qwen", "yandex")
    else:
        selected_names = (config.text_provider_mode,)

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

    speech_provider = YandexSpeechKitProvider(
        config=YandexSpeechConfig(
            credential=YandexCredential(CredentialKind.API_KEY, YandexSpeechSecretProvider()),
            voice=config.yandex_voice,
            folder_id=config.resolved_yandex_folder_id,
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
    return PrivateMultiProviderTutorAssembly(
        tutor=tutor,
        text_providers=tuple(by_name[name] for name in selected_names),
        speech_provider=speech_provider,
        config=config,
    )
