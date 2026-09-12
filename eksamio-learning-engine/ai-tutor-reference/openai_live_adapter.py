#!/usr/bin/env python3
"""Fail-closed OpenAI Responses API adapter for the existing Tutor contracts.

Credentials and HTTP transport are injected. Live execution is disabled by
default. Provider output remains advisory and can never write PEIS or relax the
independent-verification boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

from reliability_gateway import FailureClass, ProviderAttempt, ProviderFault, ProviderOutcome
from tutor_boundary import ProviderRequest, ProviderResponse
from yandex_live_adapters import JsonTransport


@dataclass(frozen=True)
class OpenAICredential:
    secret_provider: Callable[[], str] = field(repr=False, compare=False)

    def authorization_header(self) -> str:
        secret = self.secret_provider()
        if not isinstance(secret, str) or not secret.strip():
            raise ValueError("OpenAI credential unavailable")
        return f"Bearer {secret.strip()}"


@dataclass(frozen=True)
class OpenAITextConfig:
    credential: OpenAICredential = field(repr=False)
    model: str = "gpt-5.6-terra"
    endpoint: str = "https://api.openai.com/v1/responses"
    timeout_seconds: float = 30.0
    max_request_chars: int = 40_000
    max_response_chars: int = 12_000
    max_output_tokens: int = 900
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.model or not self.model.startswith("gpt-"):
            raise ValueError("OpenAI Tutor model must be an explicit gpt-* model id")
        if self.endpoint != "https://api.openai.com/v1/responses":
            raise ValueError("OpenAI Tutor must use the approved Responses API endpoint")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("OpenAI text timeout must be in (0, 60]")
        if self.max_request_chars < 1_000 or self.max_response_chars < 256:
            raise ValueError("OpenAI text bounds are too small")
        if not 64 <= self.max_output_tokens <= 4_096:
            raise ValueError("OpenAI output-token bound is invalid")


class OpenAITextProvider:
    provider_id = "openai-responses"

    def __init__(self, *, config: OpenAITextConfig, transport: JsonTransport) -> None:
        self.config = config
        self.transport = transport

    def __repr__(self) -> str:
        return (
            f"OpenAITextProvider(model={self.config.model!r}, endpoint={self.config.endpoint!r}, "
            f"execution_enabled={self.config.execution_enabled!r}, credential='<redacted>')"
        )

    @staticmethod
    def _history_messages(history: Sequence[Any]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for entry in history:
            role = "user" if entry.role == "learner" else "assistant"
            messages.append({"role": role, "content": entry.text})
        return messages

    def _request_body(self, request: ProviderRequest) -> Mapping[str, Any]:
        if not request.verified_source_refs or len(request.verified_source_refs) != len(request.verified_excerpts):
            raise ValueError("grounded OpenAI Tutor requires paired verified source refs/excerpts")
        if not all(ref.startswith("source:") for ref in request.verified_source_refs):
            raise ValueError("OpenAI Tutor accepts server-verified source refs only")

        verified = "\n\n".join(
            f"[{ref}]\n{excerpt}" for ref, excerpt in zip(request.verified_source_refs, request.verified_excerpts)
        )
        system_text = (
            f"{request.policy_instruction}\n"
            "Ты образовательный Tutor Eksamio. Используй только проверенный контекст ниже как предметную истину. "
            "Не выдумывай правило, ответ, источник или состояние ученика. Не утверждай mastery по самому диалогу. "
            "После существенной помощи напомни, что навык подтверждается отдельной самостоятельной проверкой.\n\n"
            f"Цель обучения: {request.learning_goal}\n"
            f"PEIS summary: {request.peis_learning_summary}\n"
            f"Проверенный контекст:\n{verified}"
        )
        input_messages: list[dict[str, str]] = [{"role": "system", "content": system_text}]
        input_messages.extend(self._history_messages(request.history))
        input_messages.append({"role": "user", "content": request.learner_text})
        body: Mapping[str, Any] = {
            "model": self.config.model,
            "input": input_messages,
            "max_output_tokens": self.config.max_output_tokens,
        }
        if len(repr(body)) > self.config.max_request_chars:
            raise ValueError("OpenAI text provider request exceeds configured bound")
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
        if not self.config.execution_enabled:
            return ProviderFault(FailureClass.PROVIDER_SPECIFIC_REJECTION, "live OpenAI execution disabled")
        try:
            auth = self.config.credential.authorization_header()
            body = self._request_body(request)
            response = self.transport.post_json(
                url=self.config.endpoint,
                headers={"Authorization": auth, "Content-Type": "application/json"},
                body=body,
                timeout_seconds=self.config.timeout_seconds,
            )
        except TimeoutError:
            return ProviderFault(FailureClass.TIMEOUT, "OpenAI text timeout")
        except ValueError:
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, "invalid grounded OpenAI request")
        except PermissionError:
            return ProviderFault(FailureClass.CREDENTIAL_OR_ACCOUNT_FAILURE, "OpenAI credential rejected")
        except Exception:
            return ProviderFault(FailureClass.NETWORK_FAILURE, "OpenAI text transport failure")

        content = self._extract_text(response)
        if not isinstance(content, str) or not content.strip() or len(content) > self.config.max_response_chars:
            return ProviderFault(FailureClass.MALFORMED_PROVIDER_OUTPUT, "OpenAI response text invalid")
        return ProviderResponse(text=content.strip(), source_refs=request.verified_source_refs)
