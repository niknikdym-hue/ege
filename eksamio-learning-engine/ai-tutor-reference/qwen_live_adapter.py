#!/usr/bin/env python3
"""Qwen Model Studio text provider for the Eksamio Tutor boundary."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from openai_compatible_chat_adapter import (
    CompatibleChatConfig,
    CompatibleCredential,
    OpenAICompatibleChatProvider,
)
from qwen_secret_provider import QwenSecretProvider
from tutor_boundary import ProviderRequest
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
    timeout_seconds: float = 45.0
    max_completion_tokens: int = 4_096
    temperature: float = 0.2
    thinking_enabled: bool = True
    preserve_thinking: bool = False
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.model.startswith("qwen"):
            raise QwenConfigurationError("Qwen Tutor model must be an explicit qwen* model id")
        if not 64 <= self.max_completion_tokens <= 16_384:
            raise QwenConfigurationError("Qwen completion-token bound is invalid")
        if self.preserve_thinking and not self.thinking_enabled:
            raise QwenConfigurationError("Qwen cannot preserve thinking when thinking is disabled")


class QwenTextProvider(OpenAICompatibleChatProvider):
    provider_id = "qwen-model-studio"

    def __init__(self, *, config: QwenTutorConfig, transport: JsonTransport) -> None:
        self.qwen_config = config
        endpoint = resolve_qwen_chat_endpoint(config.base_url, execution_enabled=config.execution_enabled)
        super().__init__(
            config=CompatibleChatConfig(
                provider_id=self.provider_id,
                credential=CompatibleCredential(QwenSecretProvider(), "Bearer"),
                model=config.model,
                endpoint=endpoint,
                timeout_seconds=config.timeout_seconds,
                max_output_tokens=min(config.max_completion_tokens, 4_096),
                temperature=config.temperature,
                execution_enabled=config.execution_enabled,
            ),
            transport=transport,
        )

    def _request_body(self, request: ProviderRequest) -> Mapping[str, Any]:
        body = dict(super()._request_body(request))
        # qwen3.8-max defaults to thinking+preserve_thinking. Eksamio makes both
        # choices explicit so a model-side default change cannot alter the test.
        body.pop("max_tokens", None)
        body["max_completion_tokens"] = self.qwen_config.max_completion_tokens
        body["enable_thinking"] = self.qwen_config.thinking_enabled
        body["preserve_thinking"] = self.qwen_config.preserve_thinking
        return body
