#!/usr/bin/env python3
from __future__ import annotations

import base64
from typing import Any, Mapping, Sequence

from yandex_lera_casting_ui import CASTING_TEXT, MAX_SYNTHESIS_CALLS, PAGE, PRESETS, CastingApp, prepare_casting_speech


class FakeCredential:
    def authorization_header(self) -> str:
        return "Api-Key fixture"


class CaptureTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.bodies: list[Mapping[str, object]] = []

    def post_json_stream(self, **kwargs: Any) -> Sequence[Mapping[str, object]]:
        self.calls += 1
        self.bodies.append(dict(kwargs["body"]))
        return ({"audioChunk": {"data": base64.b64encode(b"ID3-casting").decode("ascii")}},)


def main() -> int:
    assert len(PRESETS) == 6
    assert MAX_SYNTHESIS_CALLS == 120
    for preset in PRESETS.values():
        assert preset["role"] in {"neutral", "friendly"}
        assert 0.90 <= float(preset["speed"]) <= 1.12
        assert -100 <= float(preset["pitch"]) <= 100
        assert preset["pauses"] in {"light", "balanced", "marked"}

    for pauses in ("light", "balanced", "marked"):
        spoken = prepare_casting_speech(CASTING_TEXT, pauses)
        assert "*" not in spoken and "/" not in spoken
        assert "[[t͡ɕ ɛ t]]" in spoken and "[[t͡ɕ i t]]" in spoken

    app = CastingApp()
    transport = CaptureTransport()
    app.transport = transport
    app.credential = FakeCredential()  # type: ignore[assignment]
    status = app.status()
    assert status["remaining_calls"] == 120
    result = app.synthesize("friendly", 1.00, -20.0, "light")
    assert result["audio_b64"]
    assert result["brain_calls"] == 0
    assert result["persistent_audio_bytes"] == 0
    assert result["remaining_calls"] == 119
    body = transport.bodies[0]
    hints = body["hints"]
    assert {"voice": "lera"} in hints
    assert {"role": "friendly"} in hints
    assert {"speed": "1.00"} in hints
    assert {"pitchShift": "-20.0"} in hints

    assert 'id="speed"' in PAGE and 'id="pitch"' in PAGE and 'id="role"' in PAGE and 'id="pauses"' in PAGE
    assert "OpenAI и Tutor-мозг не вызываются" in PAGE
    assert "осталось" in PAGE
    print("YANDEX_LERA_CASTING_UI=PASS")
    print("YANDEX_NATIVE_CONTROLS=role,speed,pitchShift,pauses")
    print("PRESET_COUNT=6")
    print("MAX_SYNTHESIS_CALLS=120")
    print("BRAIN_CALLS=0")
    print("PERSISTENT_AUDIO_BYTES=0")
    print("LIVE_PROVIDER_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
