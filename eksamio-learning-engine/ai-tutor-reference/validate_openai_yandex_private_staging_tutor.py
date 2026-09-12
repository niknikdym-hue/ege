#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from openai_live_adapter import OpenAICredential, OpenAITextConfig, OpenAITextProvider  # noqa: E402
from private_staging_openai_yandex_tutor import (  # noqa: E402
    PrivateOpenAIYandexConfigurationError,
    PrivateOpenAIYandexTutorConfig,
    assemble_private_openai_yandex_tutor,
)
from reliability_gateway import ProviderAttempt, ProviderFault  # noqa: E402
from tutor_boundary import ProviderRequest, ProviderResponse, TutorHistoryEntry  # noqa: E402


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
        raise AssertionError("OFF private staging must not call OpenAI transport")


class FixtureJsonTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.last: dict[str, Any] | None = None

    def post_json(self, **kwargs: Any):
        self.calls += 1
        self.last = kwargs
        return {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Проверенное объяснение по принятой теме.",
                        }
                    ],
                }
            ]
        }


def provider_request() -> ProviderRequest:
    return ProviderRequest(
        contract_version="eksamio.tutor.provider-request.v1",
        correlation_ref="turn:fixture",
        subject_id="russian",
        learning_goal="Различать эпитет и обычное определение",
        policy_instruction="Advisory only; no canonical learning-state authority.",
        verified_source_refs=("source:russian-accepted-semantic:ru-expressive-epithet",),
        verified_excerpts=("Проверенное объяснение: эпитет — образное определение.\nГраницы: не каждое определение эпитет.\nАлгоритм: проверь образность.",),
        peis_learning_summary="bounded private-staging projection",
        target_refs=("ru-expressive-epithet",),
        history=(TutorHistoryEntry("learner", "Что такое эпитет?"),),
        learner_text="Дай короткий пример.",
        allowed_tool_names=(),
    )


def main() -> int:
    transport = NoCallJsonTransport()
    config = PrivateOpenAIYandexTutorConfig(
        yandex_voice="jane",
        owner_live_authorized=False,
        text_execution_enabled=False,
        speech_execution_enabled=False,
    )

    previous = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with patch("openai_secret_provider.subprocess.run") as keychain_run:
            assembly = assemble_private_openai_yandex_tutor(
                engine_root=ENGINE,
                config=config,
                text_transport=transport,
                session_ref_factory=lambda: "tutor:openai-yandex-off-fixture",
            )
            snapshot = assembly.safety_snapshot()
            assert snapshot == {
                "private_staging": True,
                "public_traffic_enabled": False,
                "owner_live_authorized": False,
                "openai_text_execution_enabled": False,
                "yandex_speech_execution_enabled": False,
                "accepted_semantic_count": 19,
                "learner_audio_persisted_bytes": 0,
            }
            state = assembly.tutor.open_semantic_session(
                learner_profile_id="learner:openai-yandex-off-fixture",
                semantic_id="ru-ege-essay-author-position",
            )
            assert state.grounding.semantic_id == "ru-ege-essay-author-position"
            assert keychain_run.call_count == 0
            assert transport.calls == 0
    finally:
        if previous is not None:
            os.environ["OPENAI_API_KEY"] = previous

    try:
        PrivateOpenAIYandexTutorConfig(
            yandex_voice="jane",
            owner_live_authorized=False,
            text_execution_enabled=True,
        )
    except PrivateOpenAIYandexConfigurationError:
        pass
    else:
        raise AssertionError("OpenAI live execution was allowed without owner authorization")

    secret = SecretProbe("OPENAI_FIXTURE_SECRET")
    live_transport = FixtureJsonTransport()
    provider = OpenAITextProvider(
        config=OpenAITextConfig(
            credential=OpenAICredential(secret),
            model="gpt-5.6-terra",
            execution_enabled=True,
        ),
        transport=live_transport,
    )
    outcome = provider.generate(
        provider_request(),
        ProviderAttempt("attempt:1", "episode:1", "turn:1", provider.provider_id, "text", 0),
    )
    assert isinstance(outcome, ProviderResponse), outcome
    assert not isinstance(outcome, ProviderFault)
    assert outcome.text == "Проверенное объяснение по принятой теме."
    assert secret.calls == 1
    assert live_transport.calls == 1
    assert live_transport.last is not None
    assert live_transport.last["url"] == "https://api.openai.com/v1/responses"
    assert live_transport.last["headers"]["Authorization"] == "Bearer OPENAI_FIXTURE_SECRET"
    assert live_transport.last["body"]["model"] == "gpt-5.6-terra"
    assert live_transport.last["body"]["input"][-1] == {"role": "user", "content": "Дай короткий пример."}
    assert "OPENAI_FIXTURE_SECRET" not in repr(provider)

    print("OPENAI_YANDEX_PRIVATE_STAGING=PASS")
    print("OPENAI_TEXT_PROVIDER=READY_OFF_BY_DEFAULT")
    print("OPENAI_SECRET_RESOLUTION=ENV_THEN_EXISTING_MACOS_KEYCHAIN")
    print("OPENAI_KEYCHAIN_SERVICE=AudiobookStudio-OpenAI")
    print("OWNER_LIVE_AUTHORIZATION_REQUIRED=PASS")
    print("SECRET_READS_WHILE_OFF=0")
    print("PUBLIC_TRAFFIC=OFF")
    print("LEARNER_AUDIO_PERSISTED_BYTES=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
