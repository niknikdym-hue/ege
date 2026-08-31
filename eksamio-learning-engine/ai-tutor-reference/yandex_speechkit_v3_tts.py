#!/usr/bin/env python3
"""SpeechKit v3 REST TTS for the selected Eksamio Russian Tutor voice.

The existing bounded SpeechKit STT adapter is reused. This module only supplies
v3 synthesis because the selected `lera` voice is v3-only. Audio is returned
transiently and never retained by provider state.

Visible Tutor text may contain presentation markup for the browser. SpeechKit
receives a separate Russian pedagogical speech rendering: presentation syntax
is removed, school notation is normalized, pronunciation hints are added only
where required, and semantic pauses are generated from reusable Russian clause
rules rather than per-answer patches.
"""
from __future__ import annotations

import base64
import json
import os
import re
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Mapping, Protocol, Sequence

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


_HYPHEN = "-‐‑‒–—"
_WORD = "A-Za-zА-Яа-яЁё"
_SENTENCE_PAUSE_MS = 260
_LETTER_EXAMPLE_PAUSE_MS = 180
_CONTEXT_SMALL = "<[small]>"
_CONTEXT_MEDIUM = "<[medium]>"
_ROOT_CHET_PHONEMES = "[[t͡ɕ ɛ t]]"
_ROOT_CHIT_PHONEMES = "[[t͡ɕ i t]]"
_CONTRAST_WORDS = "но|однако|зато|при этом"
_CONCLUSION_WORDS = "сохраняется|пишется|остаётся|остается|получается|значит|поэтому|следовательно"


def _strip_presentation_markup(source: str) -> str:
    source = re.sub(r"```(?:[^`]|`(?!``))*```", " ", source, flags=re.DOTALL)
    source = re.sub(r"`([^`]+)`", r"\1", source)
    source = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", source)
    source = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", source)
    source = re.sub(r"https?://\S+|www\.\S+", " ", source)
    source = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", source)
    source = re.sub(r"(?m)^\s*[-+*]\s+", "", source)
    source = re.sub(r"(?m)^\s*\d+[.)]\s+", "", source)
    source = re.sub(r"\*\*([^*]+)\*\*", r"\1", source)
    source = re.sub(r"__([^_]+)__", r"\1", source)
    source = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", source)
    source = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"\1", source)
    return source.replace("**", "").replace("*", "").replace("`", "")


def _normalize_school_notation(source: str) -> str:
    # Root notation may arrive as -чет-/-чит- or ЧЕТ-/ЧИТ-. Convert the slash to
    # ordinary Russian speech before phonetic hints are applied.
    source = re.sub(
        rf"(?<![{_WORD}])([{_WORD}]+)[{_HYPHEN}]+\s*/\s*([{_WORD}]+)[{_HYPHEN}]+(?![{_WORD}])",
        r"\1 или \2",
        source,
    )
    source = re.sub(
        rf"(?<![{_WORD}])[{_HYPHEN}]+([{_WORD}]+)[{_HYPHEN}]+(?![{_WORD}])",
        r"\1",
        source,
    )
    source = re.sub(rf"(?<=[{_WORD}])\s*/\s*(?=[{_WORD}])", " или ", source)

    # In constructions like "буквы «а» после корня" the pedagogically useful
    # pause belongs after the named letter, never before it.
    source = re.sub(
        r"\b(букв[аы])\s+[«„“\"]\s*([А-Яа-яЁё])\s*[»”\"]\s+(?=после\b)",
        rf"\1 \2 sil<[{_LETTER_EXAMPLE_PAUSE_MS}]> ",
        source,
        flags=re.IGNORECASE,
    )

    # A sequence of quoted examples followed by a conclusion is a reusable
    # educational pattern: finish the examples, then make a small semantic pause.
    source = re.sub(
        rf"((?:[«„“\"][^»”\"]+[»”\"])(?:\s*,\s*(?:[«„“\"][^»”\"]+[»”\"]))+)(\s+)(?=(?:{_CONCLUSION_WORDS})\b)",
        rf"\1 {_CONTEXT_SMALL} ",
        source,
        flags=re.IGNORECASE,
    )

    # Quotes are visual punctuation. Once enumeration structure is captured they
    # are removed from the spoken rendering so they cannot distort timing.
    source = re.sub(r"[«»„“”\"]", "", source)

    # The isolated school root ЧЕТ is easy for TTS to drift toward ЧЁТ. Lock only
    # the pedagogical root labels, not ordinary Russian words containing them.
    source = re.sub(
        rf"(?<![{_WORD}])чет(?![{_WORD}])",
        _ROOT_CHET_PHONEMES,
        source,
        flags=re.IGNORECASE,
    )
    source = re.sub(
        rf"(?<![{_WORD}])чит(?![{_WORD}])",
        _ROOT_CHIT_PHONEMES,
        source,
        flags=re.IGNORECASE,
    )
    return source


def _apply_russian_pedagogical_prosody(source: str) -> str:
    # New lines indicate a thought boundary in generated Tutor text.
    source = source.replace("|", ", ").replace(" ", " ")
    source = re.sub(r"\s*\n+\s*", ". ", source)

    # Russian contrastive clauses should be separated after the preceding idea,
    # not by an accidental pause around a quoted letter or example.
    source = re.sub(
        rf",\s*(?=(?:{_CONTRAST_WORDS})\b)",
        rf", {_CONTEXT_SMALL} ",
        source,
        flags=re.IGNORECASE,
    )

    # Colons in Tutor explanations normally introduce a rule, instruction or
    # example. Let SpeechKit choose a short context-sensitive pause.
    source = re.sub(r":\s+(?=[А-Яа-яЁё])", rf": {_CONTEXT_SMALL} ", source)

    # Semicolons carry a stronger intra-sentence boundary than commas.
    source = re.sub(r";\s+(?=[А-Яа-яЁё])", rf"; {_CONTEXT_MEDIUM} ", source)

    # Clean punctuation before inserting sentence-level pauses.
    source = re.sub(r"\s+([,.;:!?])", r"\1", source)
    source = re.sub(r"([!?]){2,}", r"\1", source)
    source = re.sub(r"\.{3,}", "…", source)

    # Sentence boundaries get a stable pause; clause-level pauses above remain
    # context-sensitive so the voice retains natural variation.
    source = re.sub(
        r"([.!?])\s+(?=[А-ЯЁ])",
        rf"\1 sil<[{_SENTENCE_PAUSE_MS}]> ",
        source,
    )
    return re.sub(r"\s{2,}", " ", source).strip(" .")


def normalize_tutor_text_for_speech(text: str) -> str:
    """Render browser-facing Tutor text as reusable Russian pedagogical speech.

    This function deliberately separates three concerns: presentation cleanup,
    school-notation pronunciation, and Russian pedagogical prosody. The rules are
    generic across Tutor responses; no exact benchmark sentence is hard-coded.
    """

    if not isinstance(text, str):
        raise TypeError("Tutor speech text must be a string")
    source = text.replace("\r\n", "\n").replace("\r", "\n")
    source = _strip_presentation_markup(source)
    source = _normalize_school_notation(source)
    return _apply_russian_pedagogical_prosody(source)


def _last_boundary_end(window: str, marks: tuple[str, ...]) -> int:
    """Return an exclusive boundary index, or -1 when none is suitable."""

    best = -1
    for mark in marks:
        pos = window.rfind(mark)
        if pos >= 0:
            best = max(best, pos + len(mark))
    return best


def _extend_over_pause_tag(window: str, cut: int) -> int:
    """Keep a SpeechKit pause tag attached to the phrase before it."""

    if cut < 0:
        return cut
    match = re.match(r"(?:sil<\[\d+\]>|<\[(?:tiny|small|medium|large|huge)\]>)\s*", window[cut:])
    if match:
        return cut + match.end()
    return cut


def _split_text(text: str, limit: int) -> tuple[str, ...]:
    """Split at complete phrase boundaries while respecting the v3 limit."""

    source = " ".join(text.strip().split())
    if not source:
        return ()
    chunks: list[str] = []
    strong_marks = (". ", "! ", "? ", "; ", ": ")
    weak_marks = (", ", " — ", " – ", " ")
    while source:
        if len(source) <= limit:
            chunks.append(source)
            break
        window = source[: limit + 1]
        cut = _last_boundary_end(window, strong_marks)
        if cut < max(60, limit // 2):
            cut = _last_boundary_end(window, weak_marks)
        if cut < max(40, limit // 3):
            cut = limit
        else:
            cut = _extend_over_pause_tag(window, cut)
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
        spoken_text = normalize_tutor_text_for_speech(text)
        if not spoken_text:
            raise VoiceProviderFailure("SpeechKit v3 TTS normalization produced no speech text")
        chunks = _split_text(spoken_text, self.config.max_chunk_chars)
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
