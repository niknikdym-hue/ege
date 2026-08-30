#!/usr/bin/env python3
"""Qwen Model Studio text provider for the Eksamio Tutor boundary."""
from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from openai_compatible_chat_adapter import (
    CompatibleChatConfig,
    CompatibleCredential,
    OpenAICompatibleChatProvider,
)
from qwen_secret_provider import QwenSecretProvider
from yandex_live_adapters import JsonTransport


class QwenConfigurationError(ValueError):
    pass


def resolve_qwen_chat_endpoint(explicit_base_url: str | None = None, *, execution_enabled: bool) -> str:
    raw = (
        explicit_base_url
        or os.environ.get("QWEN_BASE_URL")
        or os.environ.get("DASHSCOPE_BASE_URL")
        or ""
    ).strip().rstrip("/")
    if not raw:
        if execution_enabled:
            raise QwenConfigurationError(
                "Qwen live execution requires QWEN_BASE_URL/DASHSCOPE_BASE_URL from Model Studio workspace"
            )
        return "https://disabled.invalid/compatible-mode/v1/chat/completions"

    if raw.endswith("/chat/completions"):
        endpoint = raw
    elif raw.endswith("/compatible-mode/v1"):
        endpoint = raw + "/chat/completions"
    else:
        raise QwenConfigurationError(
            "Qwen base URL must end with /compatible-mode/v1 or /chat/completions"
        )

    parsed = urlparse(endpoint)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host.endswith("aliyuncs.com"):
        raise QwenConfigurationError("Qwen Model Studio endpoint must be an HTTPS aliyuncs.com endpoint")
    return endpoint


@dataclass(frozen=True)
class QwenTutorConfig:
    model: str = "qwen3.8-max"
    base_url: str | None = None
    timeout_seconds: float = 30.0
    max_output_tokens: int = 900
    temperature: float = 0.2
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.model.startswith("qwen"):
            raise QwenConfigurationError("Qwen Tutor model must be an explicit qwen* model id")


class QwenTextProvider(OpenAICompatibleChatProvider):
    provider_id = "qwen-model-studio"

    def __init__(self, *, config: QwenTutorConfig, transport: JsonTransport) -> None:
        endpoint = resolve_qwen_chat_endpoint(config.base_url, execution_enabled=config.execution_enabled)
        super().__init__(
            config=CompatibleChatConfig(
                provider_id=self.provider_id,
                credential=CompatibleCredential(QwenSecretProvider(), "Bearer"),
                model=config.model,
                endpoint=endpoint,
                timeout_seconds=config.timeout_seconds,
                max_output_tokens=config.max_output_tokens,
                temperature=config.temperature,
                execution_enabled=config.execution_enabled,
            ),
            transport=transport,
        )
