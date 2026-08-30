#!/usr/bin/env python3
"""Reveal a completed private Tutor blind-test provider mapping locally."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path.home() / "Library" / "Application Support" / "Eksamio" / "TutorBlindTests"
DISPLAY = {
    "openai": "OpenAI",
    "qwen": "Qwen",
    "deepseek": "DeepSeek",
    "yandex": "Яндекс / Alice AI",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-id", default=None)
    parser.add_argument("--latest", action="store_true")
    return parser.parse_args()


def resolve_file(test_id: str | None, latest: bool) -> Path:
    if test_id:
        path = ROOT / f"{test_id}.json"
        if not path.exists():
            raise FileNotFoundError("blind test id not found")
        return path
    if not latest:
        raise ValueError("pass --test-id or --latest")
    files = sorted(ROOT.glob("blind-*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not files:
        raise FileNotFoundError("no local blind Tutor mapping found")
    return files[0]


def main() -> int:
    args = parse_args()
    path = resolve_file(args.test_id, args.latest)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "eksamio.tutor.blind-provider-map.v1":
        raise ValueError("blind mapping schema mismatch")
    mapping = payload.get("mapping")
    if not isinstance(mapping, dict) or set(mapping) != {"A", "B", "C", "D"}:
        raise ValueError("blind mapping is malformed")
    candidate_sha = payload.get("candidate_sha")
    if not isinstance(candidate_sha, str) or len(candidate_sha) != 40 or any(ch not in "0123456789abcdef" for ch in candidate_sha):
        raise ValueError("blind mapping is not bound to a valid exact candidate SHA")
    print(f"BLIND_TEST_ID={payload.get('test_id')}")
    print(f"CANDIDATE_SHA={candidate_sha}")
    for alias in ("A", "B", "C", "D"):
        provider = mapping[alias]
        if provider not in DISPLAY:
            raise ValueError("unknown provider in blind mapping")
        print(f"{alias} = {DISPLAY[provider]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
