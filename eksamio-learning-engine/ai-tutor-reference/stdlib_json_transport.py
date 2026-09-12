#!/usr/bin/env python3
"""Small HTTPS JSON transport for explicit private-staging provider execution."""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Mapping


class UrllibJsonTransport:
    """POST JSON over HTTPS without retaining request/response bodies."""

    def __init__(self) -> None:
        self.calls = 0

    def post_json(
        self,
        *,
        url: str,
        headers: Mapping[str, str],
        body: Mapping[str, Any],
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        if not url.startswith("https://"):
            raise ValueError("provider transport requires HTTPS")
        self.calls += 1
        request = urllib.request.Request(
            url=url,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=dict(headers),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403}:
                raise PermissionError("provider credential/account rejected") from exc
            raise RuntimeError(f"provider HTTP error {exc.code}") from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            raise TimeoutError("provider transport timeout/network failure") from exc
        try:
            decoded = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("provider returned invalid JSON") from exc
        if not isinstance(decoded, Mapping):
            raise ValueError("provider returned non-object JSON")
        return decoded
