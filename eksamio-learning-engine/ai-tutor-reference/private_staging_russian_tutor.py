#!/usr/bin/env python3
"""Private-staging assembly for accepted-semantic Russian Tutor + Yandex adapters.

The assembly is OFF by default. Live execution can be constructed only when an
explicit owner authorization flag is supplied together with private-staging
scope and public traffic remains disabled. Credential providers are lazy: the
assembly and semantic-session opening never read a secret.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from accepted_russian_semantic_tutor import AcceptedSemanticRussianTutorVerticalSlice
from reliability_gateway import ProviderPath, ReliabilityGateway
from sep1_russian_tutor import VoiceGateway
from yandex_live_adapters import (
    BinaryTransport,
    CredentialKind,
    FormBytesTransport,
    JsonTransport,
    YandexCredential,
    YandexSpeechConfig,
    YandexSpeechKitProvider,
    YandexTextConfig,
    YandexTextProvider,
)


class PrivateStagingConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class PrivateStagingTutorConfig:
    yandex_model_uri: str
    yandex_voice: str
    yandex_folder_id: str | None = None
    text_credential_kind: CredentialKind = CredentialKind.API_KEY
    speech_credential_kind: CredentialKind = CredentialKind.API_KEY
    private_staging: bool = True
    public_traffic_enabled: bool = False
    owner_live_authorized: bool = False
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.public_traffic_enabled:
            raise PrivateStagingConfigurationError("Tutor private staging cannot enable public traffic")
        if not self.private_staging:
            raise PrivateStagingConfigurationError("this assembly is private-staging only")
        if self.execution_enabled and not self.owner_live_authorized:
            raise PrivateStagingConfigurationError(
                "live provider execution requires explicit owner authorization"
            )


@dataclass(frozen=True)
class PrivateStagingTutorAssembly:
    tutor: AcceptedSemanticRussianTutorVerticalSlice
    text_provider: YandexTextProvider
    speech_provider: YandexSpeechKitProvider
    config: PrivateStagingTutorConfig

    def safety_snapshot(self) -> dict[str, object]:
        return {
            "private_staging": self.config.private_staging,
            "public_traffic_enabled": self.config.public_traffic_enabled,
            "owner_live_authorized": self.config.owner_live_authorized,
            "provider_execution_enabled": self.config.execution_enabled,
            "accepted_semantic_count": len(self.tutor.accepted_semantics.semantic_ids),
            "learner_audio_persisted_bytes": 0,
        }


def assemble_private_staging_tutor(
    *,
    engine_root: str | Path,
    config: PrivateStagingTutorConfig,
    text_secret_provider: Callable[[], str],
    speech_secret_provider: Callable[[], str],
    text_transport: JsonTransport,
    stt_transport: BinaryTransport,
    tts_transport: FormBytesTransport,
    session_ref_factory: Callable[[], str] | None = None,
) -> PrivateStagingTutorAssembly:
    text_credential = YandexCredential(config.text_credential_kind, text_secret_provider)
    speech_credential = YandexCredential(config.speech_credential_kind, speech_secret_provider)

    text_provider = YandexTextProvider(
        config=YandexTextConfig(
            credential=text_credential,
            model_uri=config.yandex_model_uri,
            execution_enabled=config.execution_enabled,
        ),
        transport=text_transport,
    )
    text_gateway = ReliabilityGateway(
        {
            (text_provider.provider_id, "text"): ProviderPath(
                text_provider.provider_id,
                "text",
                "yandex-ai-studio-private-staging-v1",
                "PRODUCTION_ADMITTED",
                1,
            )
        },
        {text_provider.provider_id: text_provider},
    )

    speech_provider = YandexSpeechKitProvider(
        config=YandexSpeechConfig(
            credential=speech_credential,
            voice=config.yandex_voice,
            folder_id=config.yandex_folder_id,
            execution_enabled=config.execution_enabled,
        ),
        stt_transport=stt_transport,
        tts_transport=tts_transport,
    )
    voice_gateway = VoiceGateway([speech_provider])

    tutor = AcceptedSemanticRussianTutorVerticalSlice(
        engine_root=engine_root,
        text_gateway=text_gateway,
        voice_gateway=voice_gateway,
        session_ref_factory=session_ref_factory,
    )
    return PrivateStagingTutorAssembly(tutor, text_provider, speech_provider, config)
