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

    assert PROFILE.name == "YANDEX_LERA_NATIVE_CLEAN_V2_D"
    assert PROFILE.voice == "lera"
    assert PROFILE.role == "friendly"
    assert PROFILE.speed == 0.97
    assert PROFILE.pitch_shift_hz == -35.0
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
                {"role": "neutral"},
                {"speed": "1.04"},
            ],
        },
        timeout_seconds=1.0,
    )
    hints = capture.bodies[0]["hints"]
    assert isinstance(hints, list)
    assert {"voice": "lera"} in hints
    assert {"role": "friendly"} in hints
    assert {"speed": "0.97"} in hints
    assert {"pitchShift": "-35.0"} in hints
    assert {"role": "neutral"} not in hints
    assert {"speed": "1.04"} not in hints

    openai_cfg = FastTutorConfig(brain_mode="openai")
    yandex_cfg = FastTutorConfig(brain_mode="yandex")
    assert openai_cfg.lera_reading_profile == "OPENAI_LERA_REFERENCE_CLEAN_V1"
    assert yandex_cfg.lera_reading_profile == "YANDEX_LERA_NATIVE_CLEAN_V2_D"
    assert openai_cfg.lera_reading_profile != yandex_cfg.lera_reading_profile

    print("YANDEX_LERA_NATIVE_PROFILE_D=PASS")
    print("YANDEX_LERA_ROLE=friendly")
    print("YANDEX_LERA_SPEED=0.97")
    print("YANDEX_LERA_PITCH_HZ=-35")
    print("YANDEX_LERA_PAUSES=marked")
    print("YANDEX_ALICE_RUN_ON_REPAIR=PASS")
    print("OPENAI_YANDEX_READING_PROFILES_SEPARATE=PASS")
    print("LIVE_PROVIDER_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
