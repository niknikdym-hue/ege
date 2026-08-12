#!/usr/bin/env python3
"""Build a local standalone Tilda preview/package for the Russian Exceptions Trainer.

Consumes only reviewed standalone source modules plus generated validated runtime chunks.
Writes reproducible T123 text files and a local preview under build/. Does not publish
or modify any existing Tilda/current-trainer source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

MAX_BLOCK_BYTES = 35_000
PREFIX = "trenazhery-russkiy-isklyucheniya"


class PackageError(RuntimeError):
    pass


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise PackageError(f"Missing source: {path}") from exc


def script_wrap(text: str) -> str:
    return "<script>\n" + text.rstrip() + "\n</script>\n"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=root / "build" / "standalone-exceptions-tilda")
    args = parser.parse_args()
    try:
        runtime_manifest = json.loads(read(root / "build" / "RUSSIAN-EXCEPTIONS-T123-CHUNKS-MANIFEST.json"))
        source = root / "standalone-exceptions-trainer"
        shell = read(source / "ui" / "rex-shell.html").rstrip()
        css = read(source / "ui" / "rex.css").rstrip()
        runtime_loader = read(source / "core" / "rex-runtime-loader.js")
        evaluators = read(source / "core" / "rex-evaluators.js")
        state = read(source / "core" / "rex-state.js")
        selector = read(source / "core" / "rex-selector.js")
        app = read(source / "ui" / "rex-app.js")
        seo = read(source / "page" / f"{PREFIX}-SEO.txt")
        head = read(source / "page" / f"{PREFIX}-HEAD.txt")

        blocks: list[tuple[str, str, str]] = []
        blocks.append((f"{PREFIX}-T123-01.txt", "shell_css", shell + "\n<style>\n" + css + "\n</style>\n"))
        blocks.append((f"{PREFIX}-T123-02.txt", "runtime_loader", script_wrap(runtime_loader)))
        blocks.append((f"{PREFIX}-T123-03.txt", "evaluators_state", script_wrap(evaluators + "\n\n" + state)))
        blocks.append((f"{PREFIX}-T123-04.txt", "selector", script_wrap(selector)))

        data_rows = runtime_manifest.get("chunks")
        if not isinstance(data_rows, list) or not data_rows:
            raise PackageError("Runtime T123 manifest has no chunks[]")
        for offset, row in enumerate(data_rows, start=5):
            rel = row.get("path")
            if not isinstance(rel, str):
                raise PackageError("Runtime chunk path missing")
            text = read(root / rel)
            blocks.append((f"{PREFIX}-T123-{offset:02d}.txt", f"runtime_data_{offset-4:02d}", text))
        app_index = len(blocks) + 1
        blocks.append((f"{PREFIX}-T123-{app_index:02d}.txt", "app_init", script_wrap(app)))

        out = args.output_dir
        if out.exists(): shutil.rmtree(out)
        out.mkdir(parents=True, exist_ok=True)
        manifest_rows = []
        for index, (name, role, text) in enumerate(blocks, start=1):
            raw = text.encode("utf-8")
            if len(raw) > MAX_BLOCK_BYTES:
                raise PackageError(f"{name} exceeds {MAX_BLOCK_BYTES} bytes: {len(raw)}")
            (out / name).write_bytes(raw)
            manifest_rows.append({"order":index,"file":name,"role":role,"bytes":len(raw),"sha256":sha(raw)})

        preview_parts = [
            "<!doctype html><html lang=\"ru\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Тренажёр исключений — локальный preview</title></head><body style=\"margin:0\">"
        ]
        preview_parts += [text for _,_,text in blocks]
        preview_parts.append("</body></html>\n")
        preview = "\n".join(preview_parts)
        (out / f"{PREFIX}-PREVIEW.html").write_text(preview, encoding="utf-8")
        (out / f"{PREFIX}-SEO.txt").write_text(seo.rstrip() + "\n", encoding="utf-8")
        (out / f"{PREFIX}-HEAD.txt").write_text(head.rstrip() + "\n", encoding="utf-8")

        installation_lines = [
            "EKSAMIO / TILDA INSTALLATION",
            "PAGE: /trenazhery/russkiy/isklyucheniya/",
            "STATUS: PREVIEW PACKAGE / PUBLICATION HOLD",
            "",
            "HEADER / FOOTER",
            "- use the existing Eksamio header and footer separately; they are NOT included in these T123 files.",
            "",
            "SEO",
            f"- enter Title / Description / Keywords from {PREFIX}-SEO.txt",
            f"- add HEAD code from {PREFIX}-HEAD.txt",
            "- canonical must remain https://eksamio.ru/trenazhery/russkiy/isklyucheniya/",
            "- do not add a year to the persistent slug/canonical/SEO title solely because current source data is 2026-derived.",
            "",
            "T123 ORDER — STRICT",
        ]
        for row in manifest_rows:
            installation_lines.append(f"{row['order']:02d}. {row['file']} — {row['role']} — {row['bytes']} bytes")
        installation_lines += [
            "",
            "IMPORTANT",
            "- add every T123 block exactly once and in the listed order;",
            "- do not edit generated runtime-data blocks by hand;",
            "- all runtime-data blocks must have the same content_version;",
            "- missing/duplicate/mixed-version runtime blocks make the trainer fail closed;",
            "- do not add the /trenazhery/ catalog card in the same change; that is a separate rollout step;",
            "- do not modify /ege/russkiy/trenazher/ for this standalone preview;",
            "- publication is NOT authorized by this package. First use Tilda preview/hidden test and run the release smoke checklist.",
            "",
            "LOCAL PREVIEW",
            f"- {PREFIX}-PREVIEW.html",
            "",
        ]
        (out / f"{PREFIX}-INSTALLATION.txt").write_text("\n".join(installation_lines), encoding="utf-8")

        manifest = {
            "schema_version":"1.0.0",
            "product_id":"russian_exceptions",
            "content_version":runtime_manifest.get("content_version"),
            "t123_blocks":len(blocks),
            "runtime_data_blocks":len(data_rows),
            "max_block_bytes":MAX_BLOCK_BYTES,
            "largest_block_bytes":max(x["bytes"] for x in manifest_rows),
            "files":manifest_rows,
            "preview_file":f"{PREFIX}-PREVIEW.html",
            "seo_file":f"{PREFIX}-SEO.txt",
            "head_file":f"{PREFIX}-HEAD.txt",
            "installation_file":f"{PREFIX}-INSTALLATION.txt",
            "publication":"HOLD",
        }
        (out / f"{PREFIX}-PACKAGE-MANIFEST.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(f"PASS: T123 blocks={len(blocks)}, data={len(data_rows)}, max_bytes={manifest['largest_block_bytes']}, version={manifest['content_version']}")
        print(f"Output: {out}")
        return 0
    except (PackageError, json.JSONDecodeError) as exc:
        print(f"PACKAGE ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
