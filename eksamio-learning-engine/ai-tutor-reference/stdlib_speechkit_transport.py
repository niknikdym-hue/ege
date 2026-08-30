#!/usr/bin/env python3
"""Minimal transient HTTP transports for bounded SpeechKit v1 voice smoke.

These transports retain neither learner audio nor synthesized audio. They are a
short-utterance test path while SpeechKit v3 streaming is the production target.
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Mapping


class _HTTPMixin:
    @staticmethod
    def _raise_http(exc: urllib.error.HTTPError) -> None:
        if exc.code in {401, 403}:
            raise PermissionError("SpeechKit credential/account rejected") from exc
        raise RuntimeError(f"SpeechKit HTTP error {exc.code}") from exc


class UrllibBinaryTransport(_HTTPMixin):
    """POST transient binary audio and decode the small JSON STT response."""

    def __init__(self) -> None:
        self.calls = 0

    def post_binary(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        if not url.startswith("https://") or not isinstance(body, bytes) or not body:
            raise ValueError("SpeechKit binary transport requires HTTPS and non-empty bytes")
        self.calls += 1
        query = urllib.parse.urlencode(dict(params))
        request = urllib.request.Request(
            url=f"{url}?{query}" if query else url,
            data=body,
            headers={**dict(headers), "Content-Type": "application/octet-stream"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            self._raise_http(exc)
            raise AssertionError("unreachable")
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise TimeoutError("SpeechKit STT timeout/network failure") from exc
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("SpeechKit STT returned invalid JSON") from exc
        if not isinstance(decoded, Mapping):
            raise ValueError("SpeechKit STT returned non-object JSON")
        return decoded


class UrllibFormBytesTransport(_HTTPMixin):
    """POST TTS form fields and return synthesized bytes transiently."""

    def __init__(self) -> None:
        self.calls = 0

    def post_form_bytes(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        fields: Mapping[str, str],
        timeout_seconds: float,
    ) -> bytes:
        if not url.startswith("https://"):
            raise ValueError("SpeechKit form transport requires HTTPS")
        self.calls += 1
        request = urllib.request.Request(
            url=url,
            data=urllib.parse.urlencode(dict(fields)).encode("utf-8"),
            headers={**dict(headers), "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            self._raise_http(exc)
            raise AssertionError("unreachable")
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise TimeoutError("SpeechKit TTS timeout/network failure") from exc
