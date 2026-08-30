#!/usr/bin/env python3
"""Safe live diagnostic for Yandex SpeechKit STT access.

Reads the existing SpeechKit API key lazily through the project secret resolver,
never prints the key or response body, and sends one second of 16 kHz mono LPCM
silence to the official synchronous STT endpoint. The request is intentionally
minimal and is only for owner-authorized private diagnosis.
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request

from yandex_speech_secret_provider import YandexSpeechSecretProvider

ENDPOINT = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
PARAMS = {
    "lang": "ru-RU",
    "format": "lpcm",
    "sampleRateHertz": "16000",
}
SILENCE_PCM_1S = b"\x00\x00" * 16000


def main() -> int:
    try:
        key = YandexSpeechSecretProvider()()
    except Exception:
        print("SPEECHKIT_KEY=BLOCKED")
        return 2

    if not key.strip():
        print("SPEECHKIT_KEY=BLOCKED")
        return 2

    url = ENDPOINT + "?" + urllib.parse.urlencode(PARAMS)
    request = urllib.request.Request(
        url=url,
        data=SILENCE_PCM_1S,
        headers={
            "Authorization": f"Api-Key {key.strip()}",
            "Content-Type": "application/octet-stream",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            status = int(response.status)
            payload = response.read()
    except urllib.error.HTTPError as exc:
        code = int(exc.code)
        if code == 401:
            print("SPEECHKIT_STT_ACCESS=BLOCKED_AUTH_401")
        elif code == 403:
            print("SPEECHKIT_STT_ACCESS=BLOCKED_PERMISSION_403")
            print("LIKELY_REQUIRED_ROLE=ai.speechkit-stt.user")
        elif code == 429:
            print("SPEECHKIT_STT_ACCESS=BLOCKED_RATE_LIMIT_429")
        elif 500 <= code <= 599:
            print(f"SPEECHKIT_STT_ACCESS=BLOCKED_PROVIDER_{code}")
        else:
            print(f"SPEECHKIT_STT_ACCESS=BLOCKED_HTTP_{code}")
        return 3
    except (urllib.error.URLError, socket.timeout, TimeoutError):
        print("SPEECHKIT_STT_ACCESS=BLOCKED_NETWORK")
        return 4

    if status != 200:
        print(f"SPEECHKIT_STT_ACCESS=BLOCKED_HTTP_{status}")
        return 3

    try:
        decoded = json.loads(payload.decode("utf-8"))
    except Exception:
        print("SPEECHKIT_STT_ACCESS=BLOCKED_INVALID_RESPONSE")
        return 5

    if not isinstance(decoded, dict) or "result" not in decoded:
        print("SPEECHKIT_STT_ACCESS=BLOCKED_UNEXPECTED_RESPONSE")
        return 5

    print("SPEECHKIT_KEY=READY")
    print("SPEECHKIT_STT_ACCESS=PASS")
    print("YANDEX_FOLDER_ID_REQUIRED_FOR_THIS_API_KEY_REQUEST=0")
    print("SECRET_VALUES_PRINTED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
