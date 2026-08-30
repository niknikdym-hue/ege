#!/usr/bin/env python3
"""Bounded transient retry wrappers for the private SpeechKit human benchmark.

Retries are deliberately below the Tutor/LLM layer:
- STT retry happens before any LLM turn;
- TTS retry happens after the already accepted LLM turn;
- no retry can create a second LLM request or a second Tutor quota debit.

Authentication/authorization and ordinary 4xx rejections fail closed without retry.
"""
from __future__ import annotations

import time
from typing import Any, Mapping, Sequence


RETRY_DELAYS_SECONDS = (0.35, 0.9)


def _retryable(exc: Exception) -> bool:
    if isinstance(exc, (PermissionError, ValueError)):
        return False
    if isinstance(exc, TimeoutError):
        return True
    text = str(exc).lower()
    if "http error 429" in text:
        return True
    for code in range(500, 600):
        if f"http error {code}" in text:
            return True
    if "network failure" in text or "timeout" in text:
        return True
    return False


class RetryingBinaryTransport:
    """Retry transient bounded STT transport failures at most twice."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.calls = 0
        self.retries = 0

    def post_binary(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        params: Mapping[str, str],
        body: bytes,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        for attempt in range(len(RETRY_DELAYS_SECONDS) + 1):
            self.calls += 1
            try:
                return self.inner.post_binary(
                    url=url,
                    headers=headers,
                    params=params,
                    body=body,
                    timeout_seconds=timeout_seconds,
                )
            except Exception as exc:
                if attempt >= len(RETRY_DELAYS_SECONDS) or not _retryable(exc):
                    raise
                self.retries += 1
                time.sleep(RETRY_DELAYS_SECONDS[attempt])
        raise AssertionError("unreachable")


class RetryingStreamingJsonTransport:
    """Retry transient SpeechKit v3 TTS transport failures at most twice."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.calls = 0
        self.retries = 0

    def post_json_stream(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, object],
        timeout_seconds: float,
    ) -> Sequence[Mapping[str, object]]:
        for attempt in range(len(RETRY_DELAYS_SECONDS) + 1):
            self.calls += 1
            try:
                return self.inner.post_json_stream(
                    url=url,
                    headers=headers,
                    body=body,
                    timeout_seconds=timeout_seconds,
                )
            except Exception as exc:
                if attempt >= len(RETRY_DELAYS_SECONDS) or not _retryable(exc):
                    raise
                self.retries += 1
                time.sleep(RETRY_DELAYS_SECONDS[attempt])
        raise AssertionError("unreachable")
