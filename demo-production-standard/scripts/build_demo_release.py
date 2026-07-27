#!/usr/bin/env python3
"""Deterministic release builder for Eksamio interactive EGE demos.

The builder reads PACKAGE-CONTRACT.json and creates, in this exact order:
1. PREVIEW from HEAD and ordered T123 blocks;
2. MANIFEST with SHA-256 for a release whitelist;
3. release ZIP containing the whitelisted files and manifest.

Generated files must not be edited manually.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read contract {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("Contract root must be an object")
    return data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def safe_file(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return path.is_file() and not path.is_symlink()


def build_preview(root: Path, contract: dict[str, Any]) -> Path:
    build = contract.get("build") or {}
    head_path = root / str(build.get("head", ""))
    preview_path = root / str(build.get("preview", ""))
    t123_paths = [root / str(value) for value in build.get("t123_order") or []]

    if not head_path.is_file():
        raise SystemExit(f"Missing HEAD: {head_path}")
    if not t123_paths or any(not path.is_file() for path in t123_paths):
        missing = [str(path) for path in t123_paths if not path.is_file()]
        raise SystemExit(f"Missing ordered T123 files: {missing}")

    head = head_path.read_text(encoding="utf-8").strip()
    blocks = "\n".join(path.read_text(encoding="utf-8").rstrip() for path in t123_paths)
    title = str((contract.get("page") or {}).get("preview_title") or "Интерактивная демоверсия ЕГЭ")
    preview = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title}</title>\n{head}</head>"
        f'<body style="margin:0">{blocks}\n</body></html>\n'
    )
    preview_path.write_text(preview, encoding="utf-8", newline="\n")
    return preview_path


def expand_release_whitelist(root: Path, contract: dict[str, Any]) -> list[Path]:
    build = contract.get("build") or {}
    patterns = build.get("release_include")
    if not isinstance(patterns, list) or not patterns:
        raise SystemExit("build.release_include must be a non-empty whitelist of relative glob patterns")

    manifest_name = str(build.get("manifest", ""))
    zip_name = str((contract.get("package") or {}).get("release_zip", ""))
    excluded = {manifest_name, zip_name}
    files: dict[str, Path] = {}

    for raw_pattern in patterns:
        if not isinstance(raw_pattern, str) or not raw_pattern:
            raise SystemExit(f"Invalid release whitelist pattern: {raw_pattern!r}")
        if os.path.isabs(raw_pattern) or ".." in Path(raw_pattern).parts:
            raise SystemExit(f"Unsafe release whitelist pattern: {raw_pattern}")
        for value in glob.glob(str(root / raw_pattern), recursive=True):
            path = Path(value)
            if not safe_file(root, path):
                continue
            name = relative(root, path)
            if name in excluded:
                continue
            files[name] = path

    required = {
        str((contract.get("maps") or {}).get(key, ""))
        for key in ("exam", "tasks", "assets", "acceptance_cases")
    }
    required.update(str(value) for value in (build.get("t123_order") or []))
    required.update(
        {
            str(build.get("head", "")),
            str(build.get("preview", "")),
            str(build.get("evidence", "")),
            str(build.get("test_report", "")),
        }
    )
    required.update(
        str(item.get("path"))
        for item in (contract.get("sources") or [])
        if isinstance(item, dict)
    )
    required = {name for name in required if name}

    missing = sorted(required - set(files))
    if missing:
        raise SystemExit(f"Release whitelist does not include required files: {missing}")

    forbidden_parts = {"__pycache__", "node_modules", ".git"}
    forbidden_suffixes = {".log", ".tmp", ".pyc"}
    forbidden_name_re = re.compile(r"(?:project|proekt|draft|проект)", re.I)
    for name in files:
        path = Path(name)
        if forbidden_parts.intersection(path.parts):
            raise SystemExit(f"Forbidden directory in release whitelist: {name}")
        if path.suffix.lower() in forbidden_suffixes:
            raise SystemExit(f"Forbidden temporary file in release whitelist: {name}")
        if forbidden_name_re.search(name):
            raise SystemExit(f"Project/draft file in release whitelist: {name}")

    return [files[name] for name in sorted(files)]


def build_manifest(root: Path, contract: dict[str, Any], release_files: list[Path]) -> Path:
    manifest_path = root / str((contract.get("build") or {}).get("manifest", ""))
    if not manifest_path.name:
        raise SystemExit("build.manifest is required")
    lines = [f"{sha256(path)}  {relative(root, path)}" for path in release_files]
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return manifest_path


def build_zip(root: Path, contract: dict[str, Any], release_files: list[Path], manifest_path: Path) -> Path:
    zip_path = root / str((contract.get("package") or {}).get("release_zip", ""))
    if not zip_path.name:
        raise SystemExit("package.release_zip is required")
    zip_path.unlink(missing_ok=True)
    timestamp = (2026, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(release_files + [manifest_path], key=lambda item: relative(root, item)):
            name = relative(root, path)
            info = zipfile.ZipInfo(name, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    with zipfile.ZipFile(zip_path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise SystemExit(f"Corrupt ZIP member: {bad_member}")
    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", type=Path, help="Path to PACKAGE-CONTRACT.json")
    args = parser.parse_args()

    contract_path = args.contract.resolve()
    root = contract_path.parent
    contract = read_json(contract_path)

    preview_path = build_preview(root, contract)
    release_files = expand_release_whitelist(root, contract)
    manifest_path = build_manifest(root, contract, release_files)
    zip_path = build_zip(root, contract, release_files, manifest_path)

    print(f"PREVIEW: {relative(root, preview_path)}")
    print(f"MANIFEST: {relative(root, manifest_path)}")
    print(f"ZIP: {relative(root, zip_path)}")
    print(f"ZIP SHA-256: {sha256(zip_path)}")
    print("STATUS: BUILD PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
