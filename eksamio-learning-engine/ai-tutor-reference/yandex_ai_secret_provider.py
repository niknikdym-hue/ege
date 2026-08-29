#!/usr/bin/env python3
"""Lazy Yandex AI Studio credential discovery for Eksamio Tutor.

AI Studio receives its own preferred env/keychain names, but can reuse the
existing SpeechKit API key when that key has the required AI Studio scope. This
fallback is deliberately lazy: whether the existing key is sufficiently scoped
is established only by the owner-authorized live smoke, never assumed by CI.
"""
from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass

from yandex_speech_secret_provider import YandexSpeechSecretProvider, YandexSpeechSecretUnavailable


class YandexAISecretUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class YandexAISecretProvider:
    env_name: str = "YANDEX_AI_STUDIO_API_KEY"
    keychain_service: str = "Eksamio-YandexAIStudio"
    keychain_account: str = "elenadymova"
    allow_speechkit_fallback: bool = True

    def __repr__(self) -> str:
        return (
            f"YandexAISecretProvider(env_name={self.env_name!r}, "
            f"keychain_service={self.keychain_service!r}, keychain_account={self.keychain_account!r}, "
            f"allow_speechkit_fallback={self.allow_speechkit_fallback!r}, secret='<redacted>')"
        )

    def __call__(self) -> str:
        env_value = os.environ.get(self.env_name, "").strip()
        if env_value:
            return env_value

        if platform.system() == "Darwin":
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
                value = completed.stdout.strip()
                if value:
                    return value
            except (FileNotFoundError, subprocess.SubprocessError):
                pass

        if self.allow_speechkit_fallback:
            try:
                return YandexSpeechSecretProvider()()
            except YandexSpeechSecretUnavailable as exc:
                raise YandexAISecretUnavailable(
                    "Yandex AI Studio credential unavailable; no dedicated credential or reusable SpeechKit key found"
                ) from exc

        raise YandexAISecretUnavailable(
            f"Yandex AI Studio credential unavailable: set {self.env_name} on this server"
        )
