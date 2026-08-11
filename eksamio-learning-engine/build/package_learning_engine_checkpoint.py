#!/usr/bin/env python3
"""Create a reproducible-ish ZIP checkpoint of the local eksamio-learning-engine folder.

The packager is read-only with respect to source files. It writes only under
build/checkpoints/ and never runs Git/Tilda operations.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

EXCLUDED_DIR_NAMES = {".git", "__pycache__", ".idea", ".vscode"}
EXCLUDED_FILE_NAMES = {".DS_Store", "Thumbs.db"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".swp", ".swo", ".tmp"}
SUMMARY_REL = Path("audits/RUSSIAN-LEARNING-ENGINE-VALIDATION-SUMMARY.txt")
CHECKPOINT_DIR_REL = Path("build/checkpoints")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_validation_status(root: Path) -> str:
    summary = root / SUMMARY_REL
    if not summary.is_file():
        return "NOT_CONFIRMED"
    for line in summary.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("OVERALL_STATUS:"):
            value = line.split(":", 1)[1].strip().upper()
            return value or "NOT_CONFIRMED"
    return "NOT_CONFIRMED"


def is_excluded(root: Path, path: Path, output_dir: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True

    if any(part in EXCLUDED_DIR_NAMES for part in rel.parts[:-1]):
        return True
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    if path.is_relative_to(output_dir):
        return True
    return False


def collect_files(root: Path, output_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if is_excluded(root, path, output_dir):
            continue
        files.append(path)
    files.sort(key=lambda p: p.relative_to(root).as_posix())
    return files


def zipinfo_for(arcname: str) -> zipfile.ZipInfo:
    # Stable timestamp avoids checksum churn from local mtimes.
    info = zipfile.ZipInfo(arcname, date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def build_archive(root: Path, output_dir: Path, require_pass: bool) -> tuple[Path, Path]:
    status = read_validation_status(root)
    if require_pass and status != "PASS":
        raise RuntimeError(
            f"Validated checkpoint refused: aggregate validation status is {status!r}, not PASS"
        )

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d-%H%M%S")
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"eksamio-learning-engine-checkpoint-{stamp}.zip"
    inventory_path = output_dir / f"eksamio-learning-engine-checkpoint-{stamp}.sha256.txt"

    files = collect_files(root, output_dir)
    if not files:
        raise RuntimeError("No files selected for checkpoint archive")

    inventory_rows: list[tuple[str, str]] = []
    root_name = "eksamio-learning-engine"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in files:
            rel = path.relative_to(root).as_posix()
            arcname = f"{root_name}/{rel}"
            data = path.read_bytes()
            zf.writestr(zipinfo_for(arcname), data)
            inventory_rows.append((hashlib.sha256(data).hexdigest(), rel))

        metadata = (
            "EKSAMIO LEARNING ENGINE CHECKPOINT\n"
            f"GENERATED_AT_UTC: {now.isoformat()}\n"
            f"VALIDATION_STATUS: {status}\n"
            f"FILES_INCLUDED: {len(files)}\n"
            "SOURCE_FOLDER: eksamio-learning-engine/\n"
            "PRODUCTION_MUTATION: NONE BY PACKAGER\n"
        ).encode("utf-8")
        zf.writestr(zipinfo_for(f"{root_name}/CHECKPOINT-METADATA.txt"), metadata)

    archive_sha = sha256_file(zip_path)
    lines = [
        "EKSAMIO LEARNING ENGINE CHECKPOINT SHA-256 INVENTORY",
        f"GENERATED_AT_UTC: {now.isoformat()}",
        f"VALIDATION_STATUS: {status}",
        f"FILES_INCLUDED: {len(files)}",
        f"ARCHIVE: {zip_path.name}",
        f"ARCHIVE_SHA256: {archive_sha}",
        "",
        "FILES",
    ]
    lines.extend(f"{digest}  {rel}" for digest, rel in inventory_rows)
    lines.append("")
    inventory_path.write_text("\n".join(lines), encoding="utf-8")
    return zip_path, inventory_path


def main() -> int:
    parser = argparse.ArgumentParser()
    root_default = Path(__file__).resolve().parents[1]
    parser.add_argument("--root", type=Path, default=root_default)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    output_dir = (args.output_dir or root / CHECKPOINT_DIR_REL).resolve()

    try:
        zip_path, inventory_path = build_archive(root, output_dir, args.require_pass)
    except Exception as exc:
        print(f"PACKAGE ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"ZIP: {zip_path}")
    print(f"SHA256 INVENTORY: {inventory_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
