#!/usr/bin/env python3
"""Fail-closed Yandex AI Studio + SpeechKit adapters for the existing Tutor contracts.

No network stack is embedded here. All transports and credentials are injected,
and live execution is disabled by default. Provider output remains advisory;
verified source refs are server-owned and raw learner audio is never persisted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping, Protocol, Sequence

from reliability_gateway import FailureClass, ProviderAttempt, ProviderFault, ProviderOutcome
from sep1_russian_tutor import VoiceProviderFailure
from tutor_boundary import ProviderRequest, ProviderResponse


class CredentialKind(str, Enum):
    API_KEY = "API_KEY"
    IAM_TOKEN = "IAM_TOKEN"


@dataclass(frozen=True)
class YandexCredential:
    kind: CredentialKind
    secret_provider: Callable[[], str] = field(repr=False, compare=False)

    def authorization_header(self) -> str:
        secret = self.secret_provider()
        if not isinstance(secret, str) or not secret:
            raise ValueError("Yandex credential unavailable")
        prefix = "Api-Key" if self.kind is CredentialKind.API_KEY else "Bearer"
        return f"{prefix} {secret}"


class JsonTransport(Protocol):
    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
        timeout_seconds: float,
    ) -> Mapping[str, Any]: ...


class BinaryTransport(Protocol):
    def post_binary(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> Mapping[str, Any]: ...


class FormBytesTransport(Protocol):
    def post_form_bytes(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        fields: Mapping[str, str],
        timeout_seconds: float,
    ) -> bytes: ...


@dataclass(frozen=True)
class YandexTextConfig:
    credential: YandexCredential = field(repr=False)
    model_uri: str = ""
    endpoint: str = "https://ai.api.cloud.yandex.net/v1/chat/completions"
    timeout_seconds: float = 20.0
    max_request_chars: int = 40_000
    max_response_chars: int = 12_000
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.model_uri.startswith("gpt://"):
            raise ValueError("Yandex AI Studio model URI must start with gpt://")
        if not self.endpoint.startswith("https://"):
            raise ValueError("Yandex AI Studio endpoint must use HTTPS")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("text timeout must be in (0, 60]")
        if self.max_request_chars < 1_000 or self.max_response_chars < 256:
            raise ValueError("text bounds are too small")


@dataclass(frozen=True)
class YandexSpeechConfig:
    credential: YandexCredential = field(repr=False)
    voice: str = ""
    folder_id: str | None = None
    stt_endpoint: str = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    tts_endpoint: str = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    language: str = "ru-RU"
    audio_format: str = "oggopus"
    timeout_seconds: float = 20.0
    max_input_audio_bytes: int = 1_000_000
    max_output_audio_bytes: int = 8_000_000
    max_tts_text_chars: int = 4_000
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if not self.voice:
            raise ValueError("SpeechKit voice must be runtime-configured")
        if not self.stt_endpoint.startswith("https://") or not self.tts_endpoint.startswith("https://"):
            raise ValueError("SpeechKit endpoints must use HTTPS")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("speech timeout must be in (0, 60]")
        if self.max_input_audio_bytes > 1_000_000:
            raise ValueError("sync SpeechKit v1 STT input must remain <= 1 MB")


class YandexTextProvider:
    provider_id = "yandex-ai-studio"

    def __init__(self, *, config: YandexTextConfig, transport: JsonTransport) -> None:
        self.config = config
        self.transport = transport

    def __repr__(self) -> str:
        return (
            f"YandexTextProvider(model_uri={self.config.model_uri!r}, endpoint={self.config.endpoint!r}, "
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
            raise ValueError("grounded Yandex Tutor requires paired verified source refs/excerpts")
        if not all(ref.startswith("source:") for ref in request.verified_source_refs):
            raise ValueError("Yandex Tutor accepts server-verified source refs only")

        verified = "\n\n".join(
            f"[{ref}]\n{excerpt}" for ref, excerpt in zip(request.verified_source_refs, request.verified_excerpts)
        )
        system_text = (
            f"{request.policy_instruction}\n"
            "Ты образовательный Tutor Eksamio. Используй только проверенный контекст ниже как предметную истину. "
            "Не выдумывай правило, ответ, источник или состояние ученика. После существенной помощи напомни, "
            "что навык подтверждается отдельной самостоятельной проверкой.\n\n"
            f"Цель обучения: {request.learning_goal}\n"
            f"PEIS summary: {request.peis_learning_summary}\n"
            f"Проверенный контекст:\n{verified}"
        )
        messages = [{"role": "system", "content": system_text}]
        messages.extend(self._history_messages(request.history))
        messages.append({"role": "user", "content": request.learner_text})
        body: Mapping[str, Any] = {
            "model": self.config.model_uri,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 900,
            "stream": False,
        }
        if len(repr(body)) > self.config.max_request_chars:
            raise ValueError("Yandex text provider request exceeds configured bound")
        return body

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        if not self.config.execution_enabled:
            return ProviderFault(FailureClass.PROVIDER_SPECIFIC_REJECTION, "live Yandex execution disabled")
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
            return ProviderFault(FailureClass.TIMEOUT, "Yandex text timeout")
        except ValueError:
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, "invalid grounded Yandex request")
        except Exception:
            return ProviderFault(FailureClass.NETWORK_FAILURE, "Yandex text transport failure")

        try:
            choices = response["choices"]
            content = choices[0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return ProviderFault(FailureClass.MALFORMED_PROVIDER_OUTPUT, "Yandex response shape invalid")
        if not isinstance(content, str) or not content.strip() or len(content) > self.config.max_response_chars:
            return ProviderFault(FailureClass.MALFORMED_PROVIDER_OUTPUT, "Yandex response text invalid")
        return ProviderResponse(text=content.strip(), source_refs=request.verified_source_refs)


class YandexSpeechKitProvider:
    provider_id = "yandex-speechkit"

    def __init__(
        self,
        *,
        config: YandexSpeechConfig,
        stt_transport: BinaryTransport,
        tts_transport: FormBytesTransport,
    ) -> None:
        self.config = config
        self.stt_transport = stt_transport
        self.tts_transport = tts_transport

    def __repr__(self) -> str:
        return (
            f"YandexSpeechKitProvider(voice={self.config.voice!r}, language={self.config.language!r}, "
            f"execution_enabled={self.config.execution_enabled!r}, credential='<redacted>')"
        )

    def _headers(self) -> Mapping[str, str]:
        return {"Authorization": self.config.credential.authorization_header()}

    def transcribe(self, audio: bytes, *, session_ref: str) -> str:
        if not self.config.execution_enabled:
            raise VoiceProviderFailure("Yandex SpeechKit execution disabled")
        if not session_ref.startswith("tutor:") or not isinstance(audio, bytes) or not audio:
            raise VoiceProviderFailure("invalid transient STT input")
        if len(audio) > self.config.max_input_audio_bytes:
            raise VoiceProviderFailure("transient STT input exceeds configured bound")
        params = {"lang": self.config.language, "format": self.config.audio_format}
        if self.config.folder_id and self.config.credential.kind is CredentialKind.IAM_TOKEN:
            params["folderId"] = self.config.folder_id
        try:
            response = self.stt_transport.post_binary(
                url=self.config.stt_endpoint,
                headers=self._headers(),
                params=params,
                body=audio,
                timeout_seconds=self.config.timeout_seconds,
            )
        except Exception as exc:
            raise VoiceProviderFailure("Yandex SpeechKit STT failed") from exc
        result = response.get("result")
        if not isinstance(result, str) or not result.strip():
            raise VoiceProviderFailure("Yandex SpeechKit STT returned no transcript")
        return result.strip()

    def synthesize(self, text: str, *, session_ref: str) -> bytes:
        if not self.config.execution_enabled:
            raise VoiceProviderFailure("Yandex SpeechKit execution disabled")
        if not session_ref.startswith("tutor:") or not isinstance(text, str) or not text.strip():
            raise VoiceProviderFailure("invalid TTS input")
        if len(text) > self.config.max_tts_text_chars:
            raise VoiceProviderFailure("TTS text exceeds configured bound")
        fields = {
            "text": text,
            "lang": self.config.language,
            "voice": self.config.voice,
            "format": self.config.audio_format,
        }
        if self.config.folder_id and self.config.credential.kind is CredentialKind.IAM_TOKEN:
            fields["folderId"] = self.config.folder_id
        try:
            audio = self.tts_transport.post_form_bytes(
                url=self.config.tts_endpoint,
                headers=self._headers(),
                fields=fields,
                timeout_seconds=self.config.timeout_seconds,
            )
        except Exception as exc:
            raise VoiceProviderFailure("Yandex SpeechKit TTS failed") from exc
        if not isinstance(audio, bytes) or not audio or len(audio) > self.config.max_output_audio_bytes:
            raise VoiceProviderFailure("Yandex SpeechKit TTS returned invalid audio")
        return audio

    def raw_audio_persistence_count(self) -> int:
        """Hard audit: adapter state must never retain learner audio bytes."""
        for value in vars(self).values():
            if isinstance(value, bytes):
                return 1
            if isinstance(value, (list, tuple)) and any(isinstance(item, bytes) for item in value):
                return 1
        return 0
