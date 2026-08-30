#!/usr/bin/env python3
"""Lazy DeepSeek credential discovery for Eksamio Tutor.

Resolution order:
1. ``DEEPSEEK_API_KEY`` server environment variable.
2. macOS Keychain Generic Password service ``Eksamio-DeepSeek``.

No secret is read during import/assembly. Secret values are never logged or
stored in repository state.
"""
from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass


class DeepSeekSecretUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class DeepSeekSecretProvider:
    env_name: str = "DEEPSEEK_API_KEY"
    keychain_service: str = "Eksamio-DeepSeek"

    def __repr__(self) -> str:
        return (
            f"DeepSeekSecretProvider(env_name={self.env_name!r}, "
            f"keychain_service={self.keychain_service!r}, secret='<redacted>')"
        )

    def __call__(self) -> str:
        env_value = os.environ.get(self.env_name, "").strip()
        if env_value:
            return env_value
        if platform.system() != "Darwin":
            raise DeepSeekSecretUnavailable(
                f"DeepSeek credential unavailable: set {self.env_name} on this server"
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
            raise DeepSeekSecretUnavailable(
                f"DeepSeek credential unavailable in macOS Keychain service {self.keychain_service}"
            ) from exc
        value = completed.stdout.strip()
        if not value:
            raise DeepSeekSecretUnavailable(
                f"DeepSeek credential unavailable in macOS Keychain service {self.keychain_service}"
            )
        return value
