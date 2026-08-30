#!/usr/bin/env python3
"""Validate and store non-secret Tutor provider configuration."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from private_provider_config import load_private_provider_config, write_private_provider_config  # noqa: E402
from qwen_live_adapter import resolve_qwen_chat_endpoint  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qwen-base-url", default=None)
    parser.add_argument("--yandex-folder-id", default=None)
    parser.add_argument("--show", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = load_private_provider_config()
    if args.show:
        print(f"QWEN_BASE_URL_CONFIGURED={int(bool(current.qwen_base_url))}")
        print(f"YANDEX_FOLDER_ID_CONFIGURED={int(bool(current.yandex_folder_id))}")
        return 0

    qwen = args.qwen_base_url.strip() if isinstance(args.qwen_base_url, str) and args.qwen_base_url.strip() else current.qwen_base_url
    yandex = args.yandex_folder_id.strip() if isinstance(args.yandex_folder_id, str) and args.yandex_folder_id.strip() else current.yandex_folder_id
    if qwen:
        resolve_qwen_chat_endpoint(qwen, execution_enabled=True)
    if yandex and (len(yandex) < 8 or any(ch.isspace() for ch in yandex)):
        raise ValueError("Yandex folder id has an invalid shape")
    path = write_private_provider_config(qwen_base_url=qwen, yandex_folder_id=yandex)
    print(f"PRIVATE_PROVIDER_CONFIG_SAVED={path}")
    print("SECRET_VALUES_STORED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
