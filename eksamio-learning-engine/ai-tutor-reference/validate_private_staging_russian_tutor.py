#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from private_staging_russian_tutor import (  # noqa: E402
    PrivateStagingConfigurationError,
    PrivateStagingTutorConfig,
    assemble_private_staging_tutor,
)
from sep1_russian_tutor import TutorSliceError, VoiceProviderFailure  # noqa: E402
from yandex_live_adapters import CredentialKind  # noqa: E402


class SecretProbe:
    def __init__(self, value: str) -> None:
        self.value = value
        self.calls = 0

    def __call__(self) -> str:
        self.calls += 1
        return self.value


class NoCallJsonTransport:
    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, **kwargs: Any):
        self.calls += 1
        raise AssertionError("OFF private staging must not call text transport")


class NoCallBinaryTransport:
    def __init__(self) -> None:
        self.calls = 0

    def post_binary(self, **kwargs: Any):
        self.calls += 1
        raise AssertionError("OFF private staging must not call STT transport")


class NoCallFormTransport:
    def __init__(self) -> None:
        self.calls = 0

    def post_form_bytes(self, **kwargs: Any):
        self.calls += 1
        raise AssertionError("OFF private staging must not call TTS transport")


def main() -> int:
    text_secret = SecretProbe("TEXT_SECRET_FIXTURE_MUST_STAY_LAZY")
    speech_secret = SecretProbe("SPEECH_SECRET_FIXTURE_MUST_STAY_LAZY")
    text_transport = NoCallJsonTransport()
    stt_transport = NoCallBinaryTransport()
    tts_transport = NoCallFormTransport()

    config = PrivateStagingTutorConfig(
        yandex_model_uri="gpt://folder-private-staging/yandexgpt/latest",
        yandex_voice="jane",
        yandex_folder_id="folder-private-staging",
        text_credential_kind=CredentialKind.API_KEY,
        speech_credential_kind=CredentialKind.IAM_TOKEN,
        private_staging=True,
        public_traffic_enabled=False,
        owner_live_authorized=False,
        execution_enabled=False,
    )
    assembly = assemble_private_staging_tutor(
        engine_root=ENGINE,
        config=config,
        text_secret_provider=text_secret,
        speech_secret_provider=speech_secret,
        text_transport=text_transport,
        stt_transport=stt_transport,
        tts_transport=tts_transport,
        session_ref_factory=lambda: "tutor:private-staging-yandex-off-fixture",
    )
    snapshot = assembly.safety_snapshot()
    assert snapshot == {
        "private_staging": True,
        "public_traffic_enabled": False,
        "owner_live_authorized": False,
        "provider_execution_enabled": False,
        "accepted_semantic_count": 19,
        "learner_audio_persisted_bytes": 0,
    }
    assert text_secret.calls == 0 and speech_secret.calls == 0
    assert text_transport.calls == 0 and stt_transport.calls == 0 and tts_transport.calls == 0

    state = assembly.tutor.open_semantic_session(
        learner_profile_id="learner:private-staging-off-fixture",
        semantic_id="ru-ege-essay-author-position",
    )
    assert state.grounding.semantic_id == "ru-ege-essay-author-position"
    assert text_secret.calls == 0 and speech_secret.calls == 0

    try:
        assembly.tutor.text_turn(state.session_ref, "Объясни позицию автора.")
    except TutorSliceError:
        pass
    else:
        raise AssertionError("OFF private staging unexpectedly produced a provider-backed text turn")
    assert text_secret.calls == 0
    assert text_transport.calls == 0

    try:
        assembly.speech_provider.transcribe(b"TRANSIENT_AUDIO", session_ref=state.session_ref)
    except VoiceProviderFailure:
        pass
    else:
        raise AssertionError("OFF private staging unexpectedly executed SpeechKit STT")
    try:
        assembly.speech_provider.synthesize("Проверка", session_ref=state.session_ref)
    except VoiceProviderFailure:
        pass
    else:
        raise AssertionError("OFF private staging unexpectedly executed SpeechKit TTS")
    assert speech_secret.calls == 0
    assert stt_transport.calls == 0 and tts_transport.calls == 0
    assert assembly.speech_provider.raw_audio_persistence_count() == 0
    assert state.raw_audio_persistence_count() == 0

    try:
        PrivateStagingTutorConfig(
            yandex_model_uri="gpt://folder-private-staging/yandexgpt/latest",
            yandex_voice="jane",
            execution_enabled=True,
            owner_live_authorized=False,
        )
    except PrivateStagingConfigurationError:
        pass
    else:
        raise AssertionError("live execution was allowed without owner authorization")

    try:
        PrivateStagingTutorConfig(
            yandex_model_uri="gpt://folder-private-staging/yandexgpt/latest",
            yandex_voice="jane",
            public_traffic_enabled=True,
        )
    except PrivateStagingConfigurationError:
        pass
    else:
        raise AssertionError("private-staging assembly allowed public traffic")

    print("PRIVATE_STAGING_RUSSIAN_TUTOR_ASSEMBLY=PASS")
    print("ACCEPTED_SEMANTICS=19")
    print("PROVIDER_EXECUTION_DEFAULT=OFF")
    print("OWNER_LIVE_AUTHORIZATION_REQUIRED=PASS")
    print("PUBLIC_TRAFFIC=OFF")
    print("SECRET_READS_WHILE_OFF=0")
    print("TEXT_TRANSPORT_CALLS_WHILE_OFF=0")
    print("STT_TRANSPORT_CALLS_WHILE_OFF=0")
    print("TTS_TRANSPORT_CALLS_WHILE_OFF=0")
    print("LEARNER_AUDIO_PERSISTED_BYTES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
