#!/usr/bin/env python3
"""Fail-closed OpenAI-compatible Chat Completions adapter for Tutor backends."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from reliability_gateway import FailureClass, ProviderAttempt, ProviderFault, ProviderOutcome
from tutor_boundary import ProviderRequest, ProviderResponse
from tutor_provider_prompt import chat_messages
from yandex_live_adapters import JsonTransport


@dataclass(frozen=True)
class CompatibleCredential:
    secret_provider: Callable[[], str] = field(repr=False, compare=False)
    authorization_scheme: str = "Bearer"

    def __post_init__(self) -> None:
        if self.authorization_scheme not in {"Bearer", "Api-Key"}:
            raise ValueError("unsupported provider authorization scheme")

    def authorization_header(self) -> str:
        try:
            secret = self.secret_provider()
        except Exception as exc:
            raise PermissionError("provider credential unavailable") from exc
        if not isinstance(secret, str) or not secret.strip():
            raise PermissionError("provider credential unavailable")
        return f"{self.authorization_scheme} {secret.strip()}"


@dataclass(frozen=True)
class CompatibleChatConfig:
    provider_id: str
    credential: CompatibleCredential = field(repr=False)
    model: str
    endpoint: str
    timeout_seconds: float = 30.0
    max_request_chars: int = 60_000
    max_response_chars: int = 12_000
    max_output_tokens: int = 900
    temperature: float = 0.2
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.provider_id or not self.model:
            raise ValueError("provider_id and model are required")
        if not self.endpoint.startswith("https://") or not self.endpoint.endswith("/chat/completions"):
            raise ValueError("compatible Tutor endpoint must be HTTPS chat/completions")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("provider timeout must be in (0, 60]")
        if not 64 <= self.max_output_tokens <= 4096:
            raise ValueError("provider output-token bound is invalid")
        if not 0 <= self.temperature <= 1:
            raise ValueError("Tutor temperature must be in [0, 1]")


class OpenAICompatibleChatProvider:
    def __init__(self, *, config: CompatibleChatConfig, transport: JsonTransport) -> None:
        self.config = config
        self.transport = transport
        self.provider_id = config.provider_id

    def __repr__(self) -> str:
        return (
            f"OpenAICompatibleChatProvider(provider_id={self.provider_id!r}, model={self.config.model!r}, "
            f"endpoint={self.config.endpoint!r}, execution_enabled={self.config.execution_enabled!r}, "
            "credential='<redacted>')"
        )

    def _request_body(self, request: ProviderRequest) -> Mapping[str, Any]:
        body: Mapping[str, Any] = {
            "model": self.config.model,
            "messages": chat_messages(request),
            "max_tokens": self.config.max_output_tokens,
            "temperature": self.config.temperature,
            "stream": False,
        }
        if len(repr(body)) > self.config.max_request_chars:
            raise ValueError("compatible Tutor request exceeds configured bound")
        return body

    @staticmethod
    def _extract_text(response: Mapping[str, Any]) -> str | None:
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first = choices[0]
        if not isinstance(first, Mapping):
            return None
        message = first.get("message")
        if not isinstance(message, Mapping):
            return None
        content = message.get("content")
        return content.strip() if isinstance(content, str) and content.strip() else None

    @staticmethod
    def _runtime_failure(exc: RuntimeError) -> FailureClass:
        text = str(exc)
        if "429" in text:
            return FailureClass.RATE_LIMIT
        if any(f" {code}" in text for code in range(500, 600)):
            return FailureClass.PROVIDER_5XX
        return FailureClass.NETWORK_FAILURE

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        if not self.config.execution_enabled:
            return ProviderFault(FailureClass.PROVIDER_SPECIFIC_REJECTION, f"{self.provider_id} execution disabled")
        try:
            response = self.transport.post_json(
                url=self.config.endpoint,
                headers={
                    "Authorization": self.config.credential.authorization_header(),
                    "Content-Type": "application/json",
                },
                body=self._request_body(request),
                timeout_seconds=self.config.timeout_seconds,
            )
        except TimeoutError:
            return ProviderFault(FailureClass.TIMEOUT, f"{self.provider_id} timeout")
        except PermissionError:
            return ProviderFault(FailureClass.CREDENTIAL_OR_ACCOUNT_FAILURE, f"{self.provider_id} credential rejected")
        except ValueError:
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, f"invalid grounded {self.provider_id} request")
        except RuntimeError as exc:
            return ProviderFault(self._runtime_failure(exc), f"{self.provider_id} HTTP failure")
        except Exception:
            return ProviderFault(FailureClass.NETWORK_FAILURE, f"{self.provider_id} transport failure")

        content = self._extract_text(response)
        if not isinstance(content, str) or not content.strip() or len(content) > self.config.max_response_chars:
            return ProviderFault(FailureClass.MALFORMED_PROVIDER_OUTPUT, f"{self.provider_id} response text invalid")
        return ProviderResponse(text=content.strip(), source_refs=request.verified_source_refs)
