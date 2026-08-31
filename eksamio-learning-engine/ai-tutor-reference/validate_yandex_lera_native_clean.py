#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Sequence

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from private_openai_yandex_121_tutor import FastTutorConfig  # noqa: E402
from yandex_lera_native_clean import (  # noqa: E402
    PROFILE,
    YandexNativePitchTransport,
    prepare_yandex_lera_native_speech,
)
from yandex_speechkit_v3_tts import normalize_tutor_text_for_speech  # noqa: E402


ALICE_RUN_ON = (
    "Обычно перед «а» пишется «и» но в словах «сочетать», «сочетание» сохраняется «е»."
)


class CaptureTransport:
    def __init__(self) -> None:
        self.bodies: list[Mapping[str, object]] = []

    def post_json_stream(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object],
        timeout_seconds: float,
    ) -> Sequence[Mapping[str, object]]:
        self.bodies.append(dict(body))
        return ({"audioChunk": {"data": "SQ=="}},)


def main() -> int:
    shared = normalize_tutor_text_for_speech(ALICE_RUN_ON)
    native = prepare_yandex_lera_native_speech(ALICE_RUN_ON)

    # The shared/OpenAI reference path does not silently acquire Alice-specific
    # punctuation repair. The native Yandex profile does, and the selected
    # `marked` profile upgrades contextual small pauses to medium pauses.
    assert "перед а пишется и, <[small]> но" not in shared
    assert "перед а пишется и, <[medium]> но" in native
    assert "сочетать, сочетание <[medium]> сохраняется е" in native

    assert PROFILE.name == "YANDEX_LERA_NATIVE_CLEAN_V3_A"
    assert PROFILE.voice == "lera"
    assert PROFILE.role == "neutral"
    assert PROFILE.speed == 1.04
    assert PROFILE.pitch_shift_hz == 0.0
    assert PROFILE.pause_profile == "marked"

    capture = CaptureTransport()
    wrapped = YandexNativePitchTransport(capture)
    wrapped.post_json_stream(
        url="https://tts.api.cloud.yandex.net/tts/v3/utteranceSynthesis",
        headers={"Authorization": "Api-Key fixture"},
        body={
            "text": native,
            "hints": [
                {"voice": "lera"},
                {"role": "friendly"},
                {"speed": "0.97"},
                {"pitchShift": "-35.0"},
            ],
        },
        timeout_seconds=1.0,
    )
    hints = capture.bodies[0]["hints"]
    assert isinstance(hints, list)
    assert {"voice": "lera"} in hints
    assert {"role": "neutral"} in hints
    assert {"speed": "1.04"} in hints
    assert {"pitchShift": "0.0"} in hints
    assert {"role": "friendly"} not in hints
    assert {"speed": "0.97"} not in hints
    assert {"pitchShift": "-35.0"} not in hints

    openai_cfg = FastTutorConfig(brain_mode="openai")
    yandex_cfg = FastTutorConfig(brain_mode="yandex")
    assert openai_cfg.lera_reading_profile == "OPENAI_LERA_REFERENCE_CLEAN_V1"
    assert yandex_cfg.lera_reading_profile == "YANDEX_LERA_NATIVE_CLEAN_V3_A"
    assert openai_cfg.lera_reading_profile != yandex_cfg.lera_reading_profile

    print("YANDEX_LERA_NATIVE_PROFILE_A=PASS")
    print("YANDEX_LERA_ROLE=neutral")
    print("YANDEX_LERA_SPEED=1.04")
    print("YANDEX_LERA_PITCH_HZ=0")
    print("YANDEX_LERA_PAUSES=marked")
    print("YANDEX_ALICE_RUN_ON_REPAIR=PASS")
    print("OPENAI_YANDEX_READING_PROFILES_SEPARATE=PASS")
    print("LIVE_PROVIDER_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
