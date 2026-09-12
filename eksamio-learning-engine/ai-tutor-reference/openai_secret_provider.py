#!/usr/bin/env python3
"""Lazy OpenAI credential discovery for Eksamio private staging.

Resolution order:
1. ``OPENAI_API_KEY`` server environment variable.
2. Existing macOS Keychain Generic Password service ``AudiobookStudio-OpenAI``.

The secret is never read during import or assembly construction; the resolver is
called only by a live-enabled provider request. No secret value is logged or
stored in repository state.
"""
from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass


class OpenAISecretUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenAISecretProvider:
    env_name: str = "OPENAI_API_KEY"
    keychain_service: str = "AudiobookStudio-OpenAI"

    def __repr__(self) -> str:
        return (
            f"OpenAISecretProvider(env_name={self.env_name!r}, "
            f"keychain_service={self.keychain_service!r}, secret='<redacted>')"
        )

    def __call__(self) -> str:
        env_value = os.environ.get(self.env_name, "").strip()
        if env_value:
            return env_value

        if platform.system() != "Darwin":
            raise OpenAISecretUnavailable(
                f"OpenAI credential unavailable: set {self.env_name} on this server"
            )

        try:
            completed = subprocess.run(
                [
                    "/usr/bin/security",
                    "find-generic-password",
                    "-s",
                    self.keychain_service,
                    "-w",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            raise OpenAISecretUnavailable(
                f"OpenAI credential unavailable in macOS Keychain service {self.keychain_service}"
            ) from exc

        value = completed.stdout.strip()
        if not value:
            raise OpenAISecretUnavailable(
                f"OpenAI credential unavailable in macOS Keychain service {self.keychain_service}"
            )
        return value
