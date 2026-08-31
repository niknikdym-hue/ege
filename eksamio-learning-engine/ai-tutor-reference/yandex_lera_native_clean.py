#!/usr/bin/env python3
"""Native Yandex Alice -> Lera reading profile for Eksamio Tutor.

This profile is deliberately Yandex-owned. It does not copy provider prompts or
runtime settings from OpenAI. Alice text is repaired only for spoken rendering,
then the existing SpeechKit v3 Russian pedagogical normalizer is applied. The
visible Tutor answer is unchanged.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Sequence

from yandex_speechkit_v3_tts import StreamingJsonTransport, YandexSpeechKitV3TTS, normalize_tutor_text_for_speech


@dataclass(frozen=True)
class YandexLeraNativeCleanProfile:
    name: str = "YANDEX_LERA_NATIVE_CLEAN_V1"
    voice: str = "lera"
    role: str = "neutral"
    speed: float = 1.04
    pitch_shift_hz: float = 0.0


PROFILE = YandexLeraNativeCleanProfile()
_CONTRAST = "но|однако|зато|при этом"
_CONCLUSION = "поэтому|следовательно|значит|итак"


def _repair_alice_spoken_punctuation(text: str) -> str:
    """Repair punctuation that is semantically clear but awkward when read aloud."""

    source = text.replace("\r\n", "\n").replace("\r", "\n")

    # Alice can occasionally produce a grammatically understandable run-on such
    # as "пишется и но ...". Russian speech needs the contrast boundary before
    # the conjunction, so restore the missing comma in the spoken copy only.
    source = re.sub(
        rf"(?<=[А-Яа-яЁё0-9»\)])\s+(?=(?:{_CONTRAST})\b)",
        ", ",
        source,
        flags=re.IGNORECASE,
    )

    # Conclusions benefit from a semantic boundary when Alice omitted one.
    source = re.sub(
        rf"(?<=[А-Яа-яЁё0-9»\)])\s+(?=(?:{_CONCLUSION})\b)",
        ", ",
        source,
        flags=re.IGNORECASE,
    )

    return re.sub(r"\s{2,}", " ", source).strip()


def prepare_yandex_lera_native_speech(text: str) -> str:
    """Return a SpeechKit-ready spoken rendering for Alice answers."""

    repaired = _repair_alice_spoken_punctuation(text)
    rendered = normalize_tutor_text_for_speech(repaired)

    # The shared normalizer already treats contrastive clauses. Add a native
    # Yandex context pause before explicit conclusions when one is present.
    rendered = re.sub(
        rf",\s+(?!<\[)(?=(?:{_CONCLUSION})\b)",
        ", <[small]> ",
        rendered,
        flags=re.IGNORECASE,
    )
    return rendered


class YandexNativePitchTransport:
    """Inject the native SpeechKit v3 pitchShift hint for the Yandex profile."""

    def __init__(self, inner: StreamingJsonTransport, *, profile: YandexLeraNativeCleanProfile = PROFILE) -> None:
        self.inner = inner
        self.profile = profile

    def post_json_stream(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object],
        timeout_seconds: float,
    ) -> Sequence[Mapping[str, object]]:
        payload = dict(body)
        raw_hints = payload.get("hints")
        hints = list(raw_hints) if isinstance(raw_hints, list) else []
        if not any(isinstance(item, Mapping) and "pitchShift" in item for item in hints):
            hints.append({"pitchShift": str(self.profile.pitch_shift_hz)})
        payload["hints"] = hints
        return self.inner.post_json_stream(
            url=url,
            headers=headers,
            body=payload,
            timeout_seconds=timeout_seconds,
        )


class YandexNativeCleanTTSAdapter:
    """Apply Yandex-native reading direction before the ordinary SpeechKit TTS."""

    provider_id = "yandex-speechkit-v3-tts"

    def __init__(self, inner: YandexSpeechKitV3TTS) -> None:
        self.inner = inner
        self.config = inner.config
        self.transport = inner.transport

    def synthesize(self, text: str, *, session_ref: str) -> bytes:
        return self.inner.synthesize(prepare_yandex_lera_native_speech(text), session_ref=session_ref)

    def raw_audio_persistence_count(self) -> int:
        return self.inner.raw_audio_persistence_count()
