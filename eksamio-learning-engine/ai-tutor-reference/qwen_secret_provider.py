#!/usr/bin/env python3
"""Lazy Alibaba Model Studio/Qwen credential discovery for Eksamio Tutor.

Resolution order:
1. ``QWEN_API_KEY`` server environment variable.
2. ``DASHSCOPE_API_KEY`` server environment variable (Alibaba's documented name).
3. macOS Keychain Generic Password service ``Eksamio-Qwen``.

No credential is read during import or assembly. Secret values are never logged or
stored in repository state.
"""
from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass


class QwenSecretUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class QwenSecretProvider:
    env_names: tuple[str, ...] = ("QWEN_API_KEY", "DASHSCOPE_API_KEY")
    keychain_service: str = "Eksamio-Qwen"

    def __repr__(self) -> str:
        return (
            f"QwenSecretProvider(env_names={self.env_names!r}, "
            f"keychain_service={self.keychain_service!r}, secret='<redacted>')"
        )

    def __call__(self) -> str:
        for env_name in self.env_names:
            env_value = os.environ.get(env_name, "").strip()
            if env_value:
                return env_value

        if platform.system() != "Darwin":
            names = " or ".join(self.env_names)
            raise QwenSecretUnavailable(f"Qwen credential unavailable: set {names} on this server")

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
            raise QwenSecretUnavailable(
                f"Qwen credential unavailable in macOS Keychain service {self.keychain_service}"
            ) from exc

        value = completed.stdout.strip()
        if not value:
            raise QwenSecretUnavailable(
                f"Qwen credential unavailable in macOS Keychain service {self.keychain_service}"
            )
        return value
