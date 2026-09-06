#!/usr/bin/env python3
from __future__ import annotations

import base64
from typing import Any, Mapping, Sequence

from yandex_lera_finalists_ui import App, FINALISTS, MAX_CHUNK_CHARS, TEXT


class FakeCredential:
    def authorization_header(self) -> str:
        return "Api-Key fixture"


class CaptureTransport:
    def __init__(self) -> None:
        self.bodies: list[Mapping[str, object]] = []

    def post_json_stream(self, **kwargs: Any) -> Sequence[Mapping[str, object]]:
        body = dict(kwargs["body"])
        self.bodies.append(body)
        encoded = base64.b64encode(b"ID3-finalist-chunk").decode("ascii")
        return ({"audioChunk": {"data": encoded}},)


def main() -> int:
    assert set(FINALISTS) == {"A", "D"}
    assert len(TEXT) > MAX_CHUNK_CHARS

    for finalist in ("A", "D"):
        app = App()
        capture = CaptureTransport()
        app.transport = capture
        app.credential = FakeCredential()  # type: ignore[assignment]
        result = app.synthesize(finalist)
        assert result["audio_b64"]
        assert int(result["chunks"]) >= 2
        assert result["brain_calls"] == 0
        assert result["persistent_audio_bytes"] == 0
        assert len(capture.bodies) == int(result["chunks"])
        assert all(len(str(body["text"])) <= MAX_CHUNK_CHARS for body in capture.bodies)
        hints = capture.bodies[0]["hints"]
        if finalist == "A":
            assert {"role": "neutral"} in hints
            assert {"speed": "1.04"} in hints
            assert {"pitchShift": "0.0"} in hints
        else:
            assert {"role": "friendly"} in hints
            assert {"speed": "0.97"} in hints
            assert {"pitchShift": "-35.0"} in hints

    print("YANDEX_LERA_FINALISTS=PASS")
    print("FINALISTS=A,D")
    print("LONG_TEXT_CHUNKING=PASS")
    print(f"MAX_CHUNK_CHARS={MAX_CHUNK_CHARS}")
    print("BRAIN_CALLS=0")
    print("PERSISTENT_AUDIO_BYTES=0")
    print("LIVE_PROVIDER_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
