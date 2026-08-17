#!/usr/bin/env python3
"""Validate Eksamio Tilda T123 package atomicity.

Usage:
  python validate_t123_atomicity.py /path/to/package [--max-bytes 42500] [--manifest FILE]

Every T123 is validated as a standalone fragment:
- sequence must be 01..N without gaps;
- every file must be below max bytes;
- <script> and <style> tags must be balanced inside the same file;
- no T123 may start/end as a continuation of another T123's script/base64 string;
- inline script bodies are checked with `node --check` when Node is available;
- concatenated 01..N stream is checked again;
- optional manifest records filename, bytes, and SHA-256 for minimal safe re-upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

SCRIPT_OPEN = re.compile(r"<script(?:\s[^>]*)?>", re.I)
SCRIPT_CLOSE = re.compile(r"</script\s*>", re.I)
STYLE_OPEN = re.compile(r"<style(?:\s[^>]*)?>", re.I)
STYLE_CLOSE = re.compile(r"</style\s*>", re.I)
T123_NUM = re.compile(r"T123-(\d{2,3})\.txt$", re.I)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def script_bodies(text: str) -> list[str]:
    return re.findall(r"<script(?:\s[^>]*)?>(.*?)</script\s*>", text, flags=re.I | re.S)


def count_tags(text: str, opener: re.Pattern[str], closer: re.Pattern[str]) -> tuple[int, int]:
    return len(opener.findall(text)), len(closer.findall(text))


def suspicious_boundary(text: str) -> list[str]:
    issues: list[str] = []
    stripped = text.strip()
    if not stripped:
        issues.append("empty T123")
        return issues
    if stripped.startswith(('"', "'", '`', '+', ');', ']);', '},')):
        issues.append("starts like a continuation of a previous JS/string chunk")
    if stripped.endswith(('\\', '+', '${')):
        issues.append("ends like an unfinished JS/string continuation")
    return issues


def node_check(js: str, label: str) -> str | None:
    node = shutil.which("node")
    if not node or not js.strip():
        return None
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".js", delete=False) as fh:
        fh.write(js)
        path = Path(fh.name)
    try:
        proc = subprocess.run([node, "--check", str(path)], capture_output=True, text=True)
        if proc.returncode:
            msg = (proc.stderr or proc.stdout).strip().replace("\n", " | ")
            return f"{label}: node --check failed: {msg}"
    finally:
        path.unlink(missing_ok=True)
    return None


def validate_fragment(path: Path, max_bytes: int) -> tuple[list[str], dict[str, object]]:
    data = path.read_bytes()
    text = data.decode("utf-8")
    issues: list[str] = []
    if len(data) >= max_bytes:
        issues.append(f"size {len(data)} >= limit {max_bytes}")

    so, sc = count_tags(text, SCRIPT_OPEN, SCRIPT_CLOSE)
    st_o, st_c = count_tags(text, STYLE_OPEN, STYLE_CLOSE)
    if so != sc:
        issues.append(f"unbalanced <script>: open={so}, close={sc}")
    if st_o != st_c:
        issues.append(f"unbalanced <style>: open={st_o}, close={st_c}")

    issues.extend(suspicious_boundary(text))

    if so == sc:
        for idx, body in enumerate(script_bodies(text), 1):
            err = node_check(body, f"script#{idx}")
            if err:
                issues.append(err)

    record = {
        "file": path.name,
        "bytes": len(data),
        "sha256": sha256_bytes(data),
        "script_blocks": so,
        "style_blocks": st_o,
        "status": "PASS" if not issues else "FAIL",
    }
    return issues, record


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("package_dir", type=Path)
    ap.add_argument("--max-bytes", type=int, default=42500)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args()

    files = []
    for p in args.package_dir.glob("*T123-*.txt"):
        m = T123_NUM.search(p.name)
        if m:
            files.append((int(m.group(1)), p))
    files.sort()
    if not files:
        print("T123 ATOMIC FAIL: no T123 files found")
        return 2

    numbers = [n for n, _ in files]
    expected = list(range(1, len(files) + 1))
    failures: list[str] = []
    if numbers != expected:
        failures.append(f"sequence mismatch: got {numbers}, expected {expected}")

    records = []
    combined = ""
    for _n, path in files:
        issues, rec = validate_fragment(path, args.max_bytes)
        records.append(rec)
        combined += path.read_text(encoding="utf-8") + "\n"
        for issue in issues:
            failures.append(f"{path.name}: {issue}")

    so, sc = count_tags(combined, SCRIPT_OPEN, SCRIPT_CLOSE)
    st_o, st_c = count_tags(combined, STYLE_OPEN, STYLE_CLOSE)
    if so != sc:
        failures.append(f"combined stream unbalanced <script>: open={so}, close={sc}")
    if st_o != st_c:
        failures.append(f"combined stream unbalanced <style>: open={st_o}, close={st_c}")
    if so == sc:
        for idx, body in enumerate(script_bodies(combined), 1):
            err = node_check(body, f"combined script#{idx}")
            if err:
                failures.append(err)

    manifest = {
        "gate": "TILDA_T123_ATOMIC_GATE",
        "max_bytes_exclusive": args.max_bytes,
        "t123_count": len(files),
        "sequence": numbers,
        "files": records,
        "status": "FAIL" if failures else "PASS",
    }
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if failures:
        print("T123 ATOMIC FAIL")
        for item in failures:
            print(" -", item)
        return 1

    print(f"T123 ATOMIC PASS: {len(files)} standalone blocks; max={max(r['bytes'] for r in records)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
