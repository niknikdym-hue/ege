#!/usr/bin/env python3
"""Lazy Yandex SpeechKit credential discovery for Eksamio private staging."""
from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass


class YandexSpeechSecretUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class YandexSpeechSecretProvider:
    env_name: str = "YANDEX_SPEECHKIT_API_KEY"
    keychain_service: str = "AudiobookStudio-YandexSpeechKit"
    keychain_account: str = "elenadymova"

    def __repr__(self) -> str:
        return (
            f"YandexSpeechSecretProvider(env_name={self.env_name!r}, "
            f"keychain_service={self.keychain_service!r}, keychain_account={self.keychain_account!r}, "
            "secret='<redacted>')"
        )

    def __call__(self) -> str:
        env_value = os.environ.get(self.env_name, "").strip()
        if env_value:
            return env_value
        if platform.system() != "Darwin":
            raise YandexSpeechSecretUnavailable(
                f"Yandex SpeechKit credential unavailable: set {self.env_name} on this server"
            )
        try:
            completed = subprocess.run(
                [
                    "/usr/bin/security",
                    "find-generic-password",
                    "-s",
                    self.keychain_service,
                    "-a",
                    self.keychain_account,
                    "-w",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.SubprocessError) as exc:
            raise YandexSpeechSecretUnavailable(
                f"Yandex SpeechKit credential unavailable in macOS Keychain service {self.keychain_service}"
            ) from exc
        value = completed.stdout.strip()
        if not value:
            raise YandexSpeechSecretUnavailable(
                f"Yandex SpeechKit credential unavailable in macOS Keychain service {self.keychain_service}"
            )
        return value
