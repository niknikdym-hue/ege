#!/usr/bin/env python3
"""DeepSeek V4 text provider for the Eksamio Tutor boundary."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from deepseek_secret_provider import DeepSeekSecretProvider
from openai_compatible_chat_adapter import (
    CompatibleChatConfig,
    CompatibleCredential,
    OpenAICompatibleChatProvider,
)
from tutor_boundary import ProviderRequest
from yandex_live_adapters import JsonTransport


class DeepSeekConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class DeepSeekTutorConfig:
    model: str = "deepseek-v4-pro"
    endpoint: str = "https://api.deepseek.com/chat/completions"
    timeout_seconds: float = 45.0
    max_output_tokens: int = 4_096
    temperature: float = 0.2
    thinking_enabled: bool = True
    reasoning_effort: str = "high"
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.model not in {"deepseek-v4-pro", "deepseek-v4-flash"}:
            raise DeepSeekConfigurationError("DeepSeek Tutor model must be deepseek-v4-pro or deepseek-v4-flash")
        if self.endpoint != "https://api.deepseek.com/chat/completions":
            raise DeepSeekConfigurationError("DeepSeek Tutor must use the approved official chat endpoint")
        if self.reasoning_effort not in {"low", "high", "max"}:
            raise DeepSeekConfigurationError("DeepSeek reasoning_effort must be low/high/max")
        if not 64 <= self.max_output_tokens <= 4_096:
            raise DeepSeekConfigurationError("DeepSeek output-token bound is invalid")


class DeepSeekTextProvider(OpenAICompatibleChatProvider):
    provider_id = "deepseek-api"

    def __init__(self, *, config: DeepSeekTutorConfig, transport: JsonTransport) -> None:
        self.deepseek_config = config
        super().__init__(
            config=CompatibleChatConfig(
                provider_id=self.provider_id,
                credential=CompatibleCredential(DeepSeekSecretProvider(), "Bearer"),
                model=config.model,
                endpoint=config.endpoint,
                timeout_seconds=config.timeout_seconds,
                max_output_tokens=config.max_output_tokens,
                temperature=config.temperature,
                execution_enabled=config.execution_enabled,
            ),
            transport=transport,
        )

    def _request_body(self, request: ProviderRequest) -> Mapping[str, Any]:
        body = dict(super()._request_body(request))
        body["thinking"] = {
            "type": "enabled" if self.deepseek_config.thinking_enabled else "disabled",
        }
        if self.deepseek_config.thinking_enabled:
            # DeepSeek documents temperature/top_p/presence/frequency penalties as
            # unsupported (ignored) in thinking mode. Omit temperature entirely so
            # the live-test contract matches the provider rather than relying on an
            # ignored compatibility field.
            body.pop("temperature", None)
            body["reasoning_effort"] = self.deepseek_config.reasoning_effort
        return body
