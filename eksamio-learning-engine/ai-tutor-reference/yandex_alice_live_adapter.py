#!/usr/bin/env python3
"""Current Yandex AI Studio Alice AI LLM provider for Eksamio Tutor."""
from __future__ import annotations

from dataclasses import dataclass

from openai_compatible_chat_adapter import (
    CompatibleChatConfig,
    CompatibleCredential,
    OpenAICompatibleChatProvider,
)
from yandex_ai_secret_provider import YandexAISecretProvider
from yandex_live_adapters import JsonTransport


class YandexAliceConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class YandexAliceTutorConfig:
    folder_id: str | None = None
    model_id: str = "aliceai-llm"
    endpoint: str = "https://ai.api.cloud.yandex.net/v1/chat/completions"
    timeout_seconds: float = 30.0
    max_output_tokens: int = 900
    temperature: float = 0.2
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.execution_enabled and not (isinstance(self.folder_id, str) and self.folder_id.strip()):
            raise YandexAliceConfigurationError("Yandex Alice live execution requires YANDEX_FOLDER_ID/config folder_id")
        if self.endpoint != "https://ai.api.cloud.yandex.net/v1/chat/completions":
            raise YandexAliceConfigurationError("Yandex Alice Tutor must use the approved AI Studio chat endpoint")
        if not self.model_id.startswith("aliceai-llm"):
            raise YandexAliceConfigurationError("Yandex Tutor model must be an Alice AI LLM model id")

    @property
    def model_uri(self) -> str:
        folder = (self.folder_id or "disabled-folder").strip()
        return f"gpt://{folder}/{self.model_id}"


class YandexAliceTextProvider(OpenAICompatibleChatProvider):
    provider_id = "yandex-alice-ai"

    def __init__(self, *, config: YandexAliceTutorConfig, transport: JsonTransport) -> None:
        super().__init__(
            config=CompatibleChatConfig(
                provider_id=self.provider_id,
                credential=CompatibleCredential(YandexAISecretProvider(), "Api-Key"),
                model=config.model_uri,
                endpoint=config.endpoint,
                timeout_seconds=config.timeout_seconds,
                max_output_tokens=config.max_output_tokens,
                temperature=config.temperature,
                execution_enabled=config.execution_enabled,
            ),
            transport=transport,
        )
