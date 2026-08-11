#!/usr/bin/env python3
"""Measure built Russian Learning Engine runtime payload sizes before Tilda chunking decisions."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FILES = [
    "build/RUSSIAN-EXPLANATION-RUNTIME.json",
    "build/RUSSIAN-EXCEPTIONS-RUNTIME.json",
]


class AuditError(RuntimeError):
    pass


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=root)
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "audits" / "RUSSIAN-RUNTIME-SIZE-AUDIT.txt",
    )
    parser.add_argument("--file", action="append", default=[])
    args = parser.parse_args()

    root = args.root.resolve()
    rels = args.file or DEFAULT_FILES
    rows = []
    try:
        for rel in rels:
            path = root / rel
            if not path.is_file():
                raise AuditError(f"Missing runtime file: {rel}")
            raw = path.read_bytes()
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except Exception as exc:
                raise AuditError(f"Runtime is not valid UTF-8 JSON: {rel}: {exc}") from exc
            compact = json.dumps(parsed, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            pretty = json.dumps(parsed, ensure_ascii=False, indent=2).encode("utf-8")
            gz = gzip.compress(compact, compresslevel=9)
            rows.append(
                {
                    "path":rel,
                    "pretty_bytes":len(pretty),
                    "compact_bytes":len(compact),
                    "gzip_bytes":len(gz),
                    "compact_kib":round(len(compact)/1024,2),
                    "gzip_kib":round(len(gz)/1024,2),
                }
            )
    except AuditError as exc:
        print(f"AUDIT ERROR: {exc}", file=sys.stderr)
        return 2

    lines = [
        "EKSAMIO LEARNING ENGINE",
        "RUSSIAN RUNTIME PAYLOAD SIZE AUDIT",
        "",
        f"GENERATED_AT_UTC: {datetime.now(timezone.utc).isoformat()}",
        "",
        "FILES",
    ]
    for row in rows:
        lines.extend(
            [
                f"- {row['path']}",
                f"  PRETTY_BYTES: {row['pretty_bytes']}",
                f"  COMPACT_BYTES: {row['compact_bytes']}",
                f"  COMPACT_KIB: {row['compact_kib']}",
                f"  GZIP_BYTES: {row['gzip_bytes']}",
                f"  GZIP_KIB: {row['gzip_kib']}",
            ]
        )
    lines.extend(
        [
            "",
            "INTERPRETATION",
            "- This audit measures data only; it does not choose T123 chunking automatically.",
            "- Decide hosted JSON vs T123 chunks only after seeing actual validated sizes.",
            "- If T123 is used, include script/HTML wrapper overhead and keep safety margin below the project's accepted block-size limit.",
            "- Gzip size is useful for hosted static asset/network estimates but does not reduce raw T123 editor text size.",
            "",
            "SAFETY",
            "- No source/runtime file is modified.",
            "",
        ]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"PASS: measured {len(rows)} runtime payload(s)")
    print(f"Report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
