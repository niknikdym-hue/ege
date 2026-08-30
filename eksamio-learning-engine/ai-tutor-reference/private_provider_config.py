#!/usr/bin/env python3
"""Non-secret local configuration for private Tutor provider tests."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = "eksamio.tutor.private-provider-config.v1"
ALLOWED_KEYS = {"schema_version", "qwen_base_url", "yandex_folder_id"}


def default_path() -> Path:
    override = os.environ.get("EKSAMIO_TUTOR_PROVIDER_CONFIG", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / "Library" / "Application Support" / "Eksamio" / "Tutor" / "provider-config.json"


@dataclass(frozen=True)
class PrivateProviderConfig:
    qwen_base_url: str | None = None
    yandex_folder_id: str | None = None


def load_private_provider_config(path: Path | None = None) -> PrivateProviderConfig:
    target = path or default_path()
    if not target.exists():
        return PrivateProviderConfig(
            qwen_base_url=os.environ.get("QWEN_BASE_URL") or os.environ.get("DASHSCOPE_BASE_URL") or None,
            yandex_folder_id=os.environ.get("YANDEX_FOLDER_ID") or None,
        )
    raw = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) - ALLOWED_KEYS:
        raise ValueError("private provider config contains unsupported fields")
    if raw.get("schema_version") != SCHEMA:
        raise ValueError("private provider config schema mismatch")
    qwen = os.environ.get("QWEN_BASE_URL") or os.environ.get("DASHSCOPE_BASE_URL") or raw.get("qwen_base_url")
    yandex = os.environ.get("YANDEX_FOLDER_ID") or raw.get("yandex_folder_id")
    return PrivateProviderConfig(
        qwen_base_url=qwen.strip() if isinstance(qwen, str) and qwen.strip() else None,
        yandex_folder_id=yandex.strip() if isinstance(yandex, str) and yandex.strip() else None,
    )


def write_private_provider_config(*, qwen_base_url: str | None, yandex_folder_id: str | None, path: Path | None = None) -> Path:
    target = path or default_path()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(target.parent, 0o700)
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "qwen_base_url": qwen_base_url.strip() if isinstance(qwen_base_url, str) and qwen_base_url.strip() else None,
        "yandex_folder_id": yandex_folder_id.strip() if isinstance(yandex_folder_id, str) and yandex_folder_id.strip() else None,
    }
    tmp = target.with_suffix(".tmp")
    descriptor = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
        os.chmod(target, 0o600)
    finally:
        tmp.unlink(missing_ok=True)
    return target
