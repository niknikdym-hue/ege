#!/usr/bin/env python3
"""Minimal no-temperature provider adapters for the four-brain Tutor benchmark.

The benchmark deliberately keeps provider payloads as small and comparable as
possible. OpenAI, Qwen and DeepSeek use Responses-compatible requests with the
same input projection and output cap. Yandex uses its OpenAI-compatible chat
endpoint with the same message projection and output cap. No adapter writes PEIS.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from reliability_gateway import FailureClass, ProviderAttempt, ProviderFault, ProviderOutcome
from tutor_boundary import ProviderRequest, ProviderResponse
from tutor_provider_prompt import chat_messages
from yandex_live_adapters import JsonTransport


@dataclass(frozen=True)
class BenchmarkCredential:
    secret_provider: Callable[[], str] = field(repr=False, compare=False)
    authorization_scheme: str = "Bearer"

    def __post_init__(self) -> None:
        if self.authorization_scheme not in {"Bearer", "Api-Key"}:
            raise ValueError("unsupported benchmark authorization scheme")

    def authorization_header(self) -> str:
        try:
            value = self.secret_provider()
        except Exception as exc:
            raise PermissionError("benchmark provider credential unavailable") from exc
        if not isinstance(value, str) or not value.strip():
            raise PermissionError("benchmark provider credential unavailable")
        return f"{self.authorization_scheme} {value.strip()}"


@dataclass(frozen=True)
class ResponsesBenchmarkConfig:
    provider_id: str
    credential: BenchmarkCredential = field(repr=False)
    model: str
    endpoint: str
    max_output_tokens: int = 900
    timeout_seconds: float = 30.0
    max_request_chars: int = 60_000
    max_response_chars: int = 12_000
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.provider_id not in {
            "openai-responses",
            "qwen-responses",
            "deepseek-responses",
        }:
            raise ValueError("provider is not admitted to Responses benchmark adapter")
        if not self.model:
            raise ValueError("benchmark model is required")
        if not self.endpoint.startswith("https://") or not self.endpoint.endswith("/responses"):
            raise ValueError("explicit HTTPS Responses endpoint is required")
        if not 64 <= self.max_output_tokens <= 4_096:
            raise ValueError("benchmark output-token bound is invalid")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("benchmark timeout must be in (0, 60]")


@dataclass(frozen=True)
class ChatBenchmarkConfig:
    provider_id: str
    credential: BenchmarkCredential = field(repr=False)
    model: str
    endpoint: str
    max_output_tokens: int = 900
    timeout_seconds: float = 30.0
    max_request_chars: int = 60_000
    max_response_chars: int = 12_000
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.provider_id != "yandex-alice-ai":
            raise ValueError("chat benchmark adapter is reserved for Yandex Alice AI")
        if not self.model.startswith("gpt://"):
            raise ValueError("Yandex benchmark requires an explicit model URI")
        if self.endpoint != "https://ai.api.cloud.yandex.net/v1/chat/completions":
            raise ValueError("Yandex benchmark endpoint drift")
        if not 64 <= self.max_output_tokens <= 4_096:
            raise ValueError("benchmark output-token bound is invalid")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("benchmark timeout must be in (0, 60]")


def _failure_class(exc: RuntimeError) -> FailureClass:
    text = str(exc)
    if "429" in text:
        return FailureClass.RATE_LIMIT
    if any(f" {code}" in text for code in range(500, 600)):
        return FailureClass.PROVIDER_5XX
    return FailureClass.NETWORK_FAILURE


class ResponsesBenchmarkProvider:
    def __init__(self, *, config: ResponsesBenchmarkConfig, transport: JsonTransport) -> None:
        self.config = config
        self.transport = transport
        self.provider_id = config.provider_id

    def __repr__(self) -> str:
        return (
            f"ResponsesBenchmarkProvider(provider_id={self.provider_id!r}, "
            f"model={self.config.model!r}, endpoint={self.config.endpoint!r}, "
            f"execution_enabled={self.config.execution_enabled!r}, credential='<redacted>')"
        )

    def _request_body(self, request: ProviderRequest) -> Mapping[str, Any]:
        body: Mapping[str, Any] = {
            "model": self.config.model,
            "input": chat_messages(request),
            "max_output_tokens": self.config.max_output_tokens,
        }
        if len(repr(body)) > self.config.max_request_chars:
            raise ValueError("Responses benchmark request exceeds configured bound")
        return body

    @staticmethod
    def _extract_text(response: Mapping[str, Any]) -> str | None:
        direct = response.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        output = response.get("output")
        if not isinstance(output, list):
            return None
        chunks: list[str] = []
        for item in output:
            if not isinstance(item, Mapping) or item.get("type") != "message":
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, Mapping):
                    continue
                if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    text = str(part["text"]).strip()
                    if text:
                        chunks.append(text)
        return "\n".join(chunks).strip() or None

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        del attempt
        if not self.config.execution_enabled:
            return ProviderFault(
                FailureClass.PROVIDER_SPECIFIC_REJECTION,
                f"{self.provider_id} execution disabled",
            )
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
            return ProviderFault(
                FailureClass.CREDENTIAL_OR_ACCOUNT_FAILURE,
                f"{self.provider_id} credential rejected",
            )
        except ValueError:
            return ProviderFault(
                FailureClass.INVALID_PLATFORM_REQUEST,
                f"invalid grounded {self.provider_id} request",
            )
        except RuntimeError as exc:
            return ProviderFault(_failure_class(exc), f"{self.provider_id} HTTP failure")
        except Exception:
            return ProviderFault(
                FailureClass.NETWORK_FAILURE,
                f"{self.provider_id} transport failure",
            )
        text = self._extract_text(response)
        if not isinstance(text, str) or not text.strip() or len(text) > self.config.max_response_chars:
            return ProviderFault(
                FailureClass.MALFORMED_PROVIDER_OUTPUT,
                f"{self.provider_id} response text invalid",
            )
        return ProviderResponse(text=text.strip(), source_refs=request.verified_source_refs)


class ChatBenchmarkProvider:
    def __init__(self, *, config: ChatBenchmarkConfig, transport: JsonTransport) -> None:
        self.config = config
        self.transport = transport
        self.provider_id = config.provider_id

    def __repr__(self) -> str:
        return (
            f"ChatBenchmarkProvider(provider_id={self.provider_id!r}, "
            f"model={self.config.model!r}, endpoint={self.config.endpoint!r}, "
            f"execution_enabled={self.config.execution_enabled!r}, credential='<redacted>')"
        )

    def _request_body(self, request: ProviderRequest) -> Mapping[str, Any]:
        body: Mapping[str, Any] = {
            "model": self.config.model,
            "messages": chat_messages(request),
            "max_tokens": self.config.max_output_tokens,
            "stream": False,
        }
        if len(repr(body)) > self.config.max_request_chars:
            raise ValueError("Yandex benchmark request exceeds configured bound")
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

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        del attempt
        if not self.config.execution_enabled:
            return ProviderFault(
                FailureClass.PROVIDER_SPECIFIC_REJECTION,
                "Yandex benchmark execution disabled",
            )
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
            return ProviderFault(FailureClass.TIMEOUT, "Yandex benchmark timeout")
        except PermissionError:
            return ProviderFault(
                FailureClass.CREDENTIAL_OR_ACCOUNT_FAILURE,
                "Yandex benchmark credential rejected",
            )
        except ValueError:
            return ProviderFault(
                FailureClass.INVALID_PLATFORM_REQUEST,
                "invalid grounded Yandex benchmark request",
            )
        except RuntimeError as exc:
            return ProviderFault(_failure_class(exc), "Yandex benchmark HTTP failure")
        except Exception:
            return ProviderFault(FailureClass.NETWORK_FAILURE, "Yandex benchmark transport failure")
        text = self._extract_text(response)
        if not isinstance(text, str) or not text.strip() or len(text) > self.config.max_response_chars:
            return ProviderFault(
                FailureClass.MALFORMED_PROVIDER_OUTPUT,
                "Yandex benchmark response text invalid",
            )
        return ProviderResponse(text=text.strip(), source_refs=request.verified_source_refs)
