#!/usr/bin/env python3
"""SpeechKit v3 REST TTS for the selected Eksamio Russian Tutor voice.

The existing bounded SpeechKit STT adapter is reused. This module only supplies
v3 synthesis because the selected `lera` voice is v3-only. Audio is returned
transiently and never retained by provider state.
"""
from __future__ import annotations

import base64
import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Mapping, Protocol, Sequence

from sep1_russian_tutor import VoiceProviderFailure
from yandex_live_adapters import YandexCredential, YandexSpeechKitProvider


class StreamingJsonTransport(Protocol):
    def post_json_stream(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object],
        timeout_seconds: float,
    ) -> Sequence[Mapping[str, object]]: ...


class UrllibStreamingJsonTransport:
    """Read a small REST streaming response without persisting provider payloads."""

    def __init__(self) -> None:
        self.calls = 0

    def post_json_stream(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object],
        timeout_seconds: float,
    ) -> Sequence[Mapping[str, object]]:
        if not url.startswith("https://"):
            raise ValueError("SpeechKit v3 TTS endpoint must use HTTPS")
        self.calls += 1
        request = urllib.request.Request(
            url=url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={**dict(headers), "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise PermissionError("SpeechKit v3 credential/account rejected") from exc
            raise RuntimeError(f"SpeechKit v3 HTTP error {exc.code}") from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise TimeoutError("SpeechKit v3 TTS timeout/network failure") from exc

        text = raw.decode("utf-8").strip()
        if not text:
            raise ValueError("SpeechKit v3 returned an empty response")
        objects: list[Mapping[str, object]] = []
        # REST streaming may return sequential JSON objects. Also accept a single
        # ordinary JSON object to remain robust across gateway implementations.
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, Mapping):
            objects.append(parsed)
        else:
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError("SpeechKit v3 returned malformed streaming JSON") from exc
                if not isinstance(item, Mapping):
                    raise ValueError("SpeechKit v3 streaming item must be an object")
                objects.append(item)
        if not objects:
            raise ValueError("SpeechKit v3 returned no streaming objects")
        return tuple(objects)


@dataclass(frozen=True)
class YandexSpeechKitV3TTSConfig:
    credential: YandexCredential = field(repr=False)
    voice: str = "lera"
    role: str = "neutral"
    speed: float = 1.04
    endpoint: str = field(
        default_factory=lambda: os.environ.get(
            "YANDEX_SPEECHKIT_V3_TTS_ENDPOINT",
            "https://tts.api.cloud.yandex.net/tts/v3/utteranceSynthesis",
        )
    )
    container_audio_type: str = "MP3"
    timeout_seconds: float = 30.0
    max_chunk_chars: int = 240
    max_total_text_chars: int = 4_000
    max_output_audio_bytes: int = 8_000_000
    execution_enabled: bool = False

    def __post_init__(self) -> None:
        if self.voice != "lera":
            raise ValueError("Eksamio Tutor v3 TTS is locked to the accepted Lera voice for this test")
        if self.role != "neutral":
            raise ValueError("Eksamio Tutor Lera role is locked to neutral")
        if abs(self.speed - 1.04) > 0.0001:
            raise ValueError("Eksamio Tutor Lera speed is locked to 1.04")
        if not self.endpoint.startswith("https://") or "/tts/v3/utteranceSynthesis" not in self.endpoint:
            raise ValueError("invalid SpeechKit v3 TTS endpoint")
        if self.container_audio_type != "MP3":
            raise ValueError("private Tutor v3 output is locked to MP3 for browser-safe chunk concatenation")
        if not 1 <= self.max_chunk_chars <= 250:
            raise ValueError("SpeechKit v3 synthesis chunk must remain <= 250 characters")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("SpeechKit v3 timeout must be in (0, 60]")


def _split_text(text: str, limit: int) -> tuple[str, ...]:
    """Split on natural boundaries while respecting the v3 utterance limit."""
    source = " ".join(text.strip().split())
    if not source:
        return ()
    chunks: list[str] = []
    while source:
        if len(source) <= limit:
            chunks.append(source)
            break
        window = source[: limit + 1]
        cut = max(window.rfind(mark) for mark in (". ", "! ", "? ", "; ", ": ", ", ", " "))
        if cut < max(40, limit // 3):
            cut = limit
        else:
            cut += 1
        chunk = source[:cut].strip()
        if chunk:
            chunks.append(chunk)
        source = source[cut:].strip()
    return tuple(chunks)


class YandexSpeechKitV3TTS:
    provider_id = "yandex-speechkit-v3-tts"

    def __init__(self, *, config: YandexSpeechKitV3TTSConfig, transport: StreamingJsonTransport) -> None:
        self.config = config
        self.transport = transport

    def __repr__(self) -> str:
        return (
            f"YandexSpeechKitV3TTS(voice={self.config.voice!r}, role={self.config.role!r}, "
            f"speed={self.config.speed!r}, execution_enabled={self.config.execution_enabled!r}, "
            "credential='<redacted>')"
        )

    def _headers(self) -> Mapping[str, str]:
        return {"Authorization": self.config.credential.authorization_header()}

    @staticmethod
    def _audio_data(item: Mapping[str, object]) -> str | None:
        candidate: object = item
        result = item.get("result")
        if isinstance(result, Mapping):
            candidate = result
        if not isinstance(candidate, Mapping):
            return None
        audio_chunk = candidate.get("audioChunk")
        if not isinstance(audio_chunk, Mapping):
            return None
        data = audio_chunk.get("data")
        return data if isinstance(data, str) and data else None

    def synthesize(self, text: str, *, session_ref: str) -> bytes:
        if not self.config.execution_enabled:
            raise VoiceProviderFailure("SpeechKit v3 TTS execution disabled")
        if not session_ref.startswith("tutor:") or not isinstance(text, str) or not text.strip():
            raise VoiceProviderFailure("invalid SpeechKit v3 TTS input")
        if len(text) > self.config.max_total_text_chars:
            raise VoiceProviderFailure("SpeechKit v3 TTS text exceeds configured bound")
        chunks = _split_text(text, self.config.max_chunk_chars)
        if not chunks:
            raise VoiceProviderFailure("SpeechKit v3 TTS text produced no utterances")

        output = bytearray()
        try:
            headers = self._headers()
            for chunk in chunks:
                body: Mapping[str, object] = {
                    "text": chunk,
                    "hints": [
                        {"voice": self.config.voice},
                        {"role": self.config.role},
                        {"speed": str(self.config.speed)},
                    ],
                    "outputAudioSpec": {
                        "containerAudio": {"containerAudioType": self.config.container_audio_type}
                    },
                    "loudnessNormalizationType": "LUFS",
                }
                responses = self.transport.post_json_stream(
                    url=self.config.endpoint,
                    headers=headers,
                    body=body,
                    timeout_seconds=self.config.timeout_seconds,
                )
                found = False
                for item in responses:
                    encoded = self._audio_data(item)
                    if not encoded:
                        continue
                    found = True
                    try:
                        output.extend(base64.b64decode(encoded, validate=True))
                    except (ValueError, TypeError) as exc:
                        raise VoiceProviderFailure("SpeechKit v3 returned malformed audio base64") from exc
                    if len(output) > self.config.max_output_audio_bytes:
                        raise VoiceProviderFailure("SpeechKit v3 audio exceeds configured bound")
                if not found:
                    raise VoiceProviderFailure("SpeechKit v3 returned no audio chunk")
        except VoiceProviderFailure:
            raise
        except Exception as exc:
            raise VoiceProviderFailure("SpeechKit v3 TTS failed") from exc
        if not output:
            raise VoiceProviderFailure("SpeechKit v3 returned empty audio")
        return bytes(output)

    def raw_audio_persistence_count(self) -> int:
        return int(any(isinstance(value, bytes) for value in vars(self).values()))


class YandexHybridSpeechProvider:
    """One Tutor speech provider: existing bounded STT + v3 Lera TTS."""

    provider_id = "yandex-speechkit"

    def __init__(self, *, stt_provider: YandexSpeechKitProvider, tts_provider: YandexSpeechKitV3TTS) -> None:
        self.stt_provider = stt_provider
        self.tts_provider = tts_provider

    def transcribe(self, audio: bytes, *, session_ref: str) -> str:
        return self.stt_provider.transcribe(audio, session_ref=session_ref)

    def synthesize(self, text: str, *, session_ref: str) -> bytes:
        return self.tts_provider.synthesize(text, session_ref=session_ref)

    def raw_audio_persistence_count(self) -> int:
        return self.stt_provider.raw_audio_persistence_count() + self.tts_provider.raw_audio_persistence_count()
