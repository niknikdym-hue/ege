#!/usr/bin/env python3
"""Generate deterministic Physics 2024 PDF review materialization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


DPI = 200
SOURCE_SPECS = {
    "demo": {
        "path": "ege-source-fizika/source-fizika-2024/ege-2024-fizika-demoversiya.pdf",
        "git_blob": "c4e7e78bb83e7fbaca8a47233d0cab944b2709a8",
        "sha256": "746903cadd391a52948aea59155f713c7677521ba22b52c369d2473fb0fc2057",
        "page_count": 18,
        "render_directory": "demo-pages",
    },
    "specification": {
        "path": "ege-source-fizika/source-fizika-2024/ege-2024-fizika-specifikatsiya.pdf",
        "git_blob": "189371a8b6834b79a69d4c2aa3182fc80dda93bf",
        "sha256": "f4703bbe704c0220e44faca64cb1fe834fc06c5eeab21d57f6f428e2b3bd775c",
        "page_count": 7,
        "render_directory": "specification-pages",
    },
    "codifier": {
        "path": "ege-source-fizika/source-fizika-2024/ege-2024-fizika-kodifikator.pdf",
        "git_blob": "b4a37d00651af07c12270a179ab368876ee6a093",
        "sha256": "bc4c1ee2a603572e5342227a8c90aa34a772a22cc750164c443f4921c4eeca30",
        "page_count": 30,
        "render_directory": None,
    },
}


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tool_version(executable: str) -> str:
    result = subprocess.run(
        [executable, "-v"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={**os.environ, "LC_ALL": "C", "TZ": "UTC"},
    )
    return result.stdout.splitlines()[0].strip()


def run(command: list[str], *, stdout_path: Path | None = None) -> None:
    environment = {**os.environ, "LC_ALL": "C", "TZ": "UTC"}
    if stdout_path is None:
        subprocess.run(command, check=True, env=environment)
        return
    with stdout_path.open("wb") as output:
        subprocess.run(command, check=True, stdout=output, stderr=subprocess.PIPE, env=environment)


def normalize_render_names(directory: Path, expected_count: int) -> list[Path]:
    candidates = sorted(directory.glob("render-*.png"))
    if len(candidates) != expected_count:
        raise RuntimeError(f"Expected {expected_count} rendered pages in {directory}, got {len(candidates)}")
    normalized: list[Path] = []
    for physical_page, source in enumerate(candidates, start=1):
        target = directory / f"page-{physical_page:03d}.png"
        source.rename(target)
        normalized.append(target)
    return normalized


def page_geometry(page) -> tuple[float, float, int]:
    width = round(float(page.mediabox.width), 4)
    height = round(float(page.mediabox.height), 4)
    rotation = int(page.get("/Rotate", 0) or 0) % 360
    return width, height, rotation


def render_pdf(
    *,
    source_path: Path,
    relative_source_path: str,
    source_spec: dict,
    output_directory: Path,
    pdftoppm: str,
) -> list[dict]:
    output_directory.mkdir(parents=True)
    command = [
        pdftoppm,
        "-png",
        "-r",
        str(DPI),
        "-f",
        "1",
        "-l",
        str(source_spec["page_count"]),
        str(source_path),
        str(output_directory / "render"),
    ]
    forbidden_crop_flags = {"-x", "-y", "-W", "-H", "-sz", "-cropbox"}
    if forbidden_crop_flags.intersection(command):
        raise RuntimeError("Crop option unexpectedly present in render command")
    run(command)
    rendered = normalize_render_names(output_directory, source_spec["page_count"])
    reader = PdfReader(source_path)
    records: list[dict] = []
    for physical_page, (png_path, pdf_page) in enumerate(zip(rendered, reader.pages), start=1):
        width_points, height_points, rotation = page_geometry(pdf_page)
        with Image.open(png_path) as image:
            width_px, height_px = image.size
            extrema = image.convert("L").getextrema()
        display_width_points = height_points if rotation in {90, 270} else width_points
        display_height_points = width_points if rotation in {90, 270} else height_points
        expected_width_px = round(display_width_points * DPI / 72)
        expected_height_px = round(display_height_points * DPI / 72)
        full_canvas = (
            abs(width_px - expected_width_px) <= 1
            and abs(height_px - expected_height_px) <= 1
        )
        nonblank = extrema is not None and extrema[0] < 250
        if not full_canvas or not nonblank or width_px <= 0 or height_px <= 0:
            raise RuntimeError(f"Page completeness validation failed: {png_path}")
        records.append(
            {
                "physical_page": physical_page,
                "filename": png_path.relative_to(output_directory.parent).as_posix(),
                "source_path": relative_source_path,
                "source_git_blob": source_spec["git_blob"],
                "source_sha256": source_spec["sha256"],
                "width_px": width_px,
                "height_px": height_px,
                "pdf_media_width_points": width_points,
                "pdf_media_height_points": height_points,
                "pdf_rotation": rotation,
                "nonblank": nonblank,
                "full_page_canvas": full_canvas,
                "sha256": file_sha256(png_path),
            }
        )
    return records


def make_contact_sheet(page_paths: list[Path], output_path: Path) -> None:
    columns = 3
    rows = (len(page_paths) + columns - 1) // columns
    margin = 24
    thumb_width = 600
    label_height = 36
    with Image.open(page_paths[0]) as first:
        thumb_height = round(first.height * thumb_width / first.width)
    sheet_width = columns * thumb_width + (columns + 1) * margin
    sheet_height = rows * (thumb_height + label_height) + (rows + 1) * margin
    sheet = Image.new("RGB", (sheet_width, sheet_height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, path in enumerate(page_paths):
        row, column = divmod(index, columns)
        x = margin + column * (thumb_width + margin)
        y = margin + row * (thumb_height + label_height + margin)
        with Image.open(path) as page:
            thumbnail = page.convert("RGB").resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        sheet.paste(thumbnail, (x, y + label_height))
        draw.text((x, y + 8), f"Physical page {index + 1:03d}", fill="black", font=font)
        draw.rectangle(
            (x, y + label_height, x + thumb_width - 1, y + label_height + thumb_height - 1),
            outline="black",
            width=1,
        )
    sheet.save(output_path, format="PNG", compress_level=9, optimize=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    repo_root = arguments.repo_root.resolve()
    output = arguments.output.resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"Output directory must be clean: {output}")
    output.mkdir(parents=True, exist_ok=True)

    pdftoppm = os.environ.get("PDFTOPPM") or shutil.which("pdftoppm")
    pdftotext = os.environ.get("PDFTOTEXT") or shutil.which("pdftotext")
    pdfimages = os.environ.get("PDFIMAGES") or shutil.which("pdfimages")
    git = os.environ.get("GIT") or shutil.which("git")
    if not all((pdftoppm, pdftotext, pdfimages, git)):
        raise SystemExit("Required Poppler/git executable not found")

    tool_versions = {
        "pdftoppm": tool_version(pdftoppm),
        "pdftotext": tool_version(pdftotext),
        "pdfimages": tool_version(pdfimages),
    }

    text_directory = output / "text"
    layout_directory = output / "layout"
    inspection_directory = output / "inspection"
    text_directory.mkdir()
    layout_directory.mkdir()
    inspection_directory.mkdir()

    manifest_sources = []
    validation_lines = [
        "PHYSICS 2024 VISUAL MATERIALIZATION VALIDATION",
        "DERIVED REVIEW EVIDENCE ONLY - NOT SOURCE AUTHORITY",
        "",
    ]
    rendered_records: dict[str, list[dict]] = {}

    for source_name, source_spec in SOURCE_SPECS.items():
        relative_path = source_spec["path"]
        source_path = repo_root / relative_path
        actual_sha256 = file_sha256(source_path)
        actual_blob = subprocess.run(
            [git, "hash-object", str(source_path)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            env={**os.environ, "LC_ALL": "C", "TZ": "UTC"},
        ).stdout.strip()
        reader = PdfReader(source_path)
        if actual_sha256 != source_spec["sha256"]:
            raise RuntimeError(f"Canonical SHA256 mismatch: {relative_path}")
        if actual_blob != source_spec["git_blob"]:
            raise RuntimeError(f"Canonical git blob mismatch: {relative_path}")
        if len(reader.pages) != source_spec["page_count"]:
            raise RuntimeError(f"Canonical page count mismatch: {relative_path}")

        layout_output = text_directory / f"{source_name}-layout.txt"
        run(
            [pdftotext, "-layout", "-enc", "UTF-8", str(source_path), str(layout_output)]
        )
        form_feed_pages = layout_output.read_bytes().count(b"\x0c")
        if form_feed_pages != source_spec["page_count"]:
            raise RuntimeError(
                f"Layout extraction page markers mismatch for {relative_path}: {form_feed_pages}"
            )

        page_records: list[dict] = []
        render_directory = source_spec["render_directory"]
        if render_directory:
            page_records = render_pdf(
                source_path=source_path,
                relative_source_path=relative_path,
                source_spec=source_spec,
                output_directory=output / render_directory,
                pdftoppm=pdftoppm,
            )
        rendered_records[source_name] = page_records

        manifest_sources.append(
            {
                "name": source_name,
                "source_path": relative_path,
                "source_git_blob": source_spec["git_blob"],
                "source_sha256": source_spec["sha256"],
                "page_count": source_spec["page_count"],
                "renderer": tool_versions["pdftoppm"] if render_directory else None,
                "dpi": DPI if render_directory else None,
                "generation_command": (
                    f"pdftoppm -png -r {DPI} -f 1 -l {source_spec['page_count']} "
                    f"{relative_path} {render_directory}/render"
                    if render_directory
                    else "No raster render required; pdftotext -layout extraction only"
                ),
                "layout_extractor": tool_versions["pdftotext"],
                "layout_generation_command": (
                    f"pdftotext -layout -enc UTF-8 {relative_path} text/{source_name}-layout.txt"
                ),
                "rendered_pages": page_records,
            }
        )
        validation_lines.extend(
            [
                f"{source_name.upper()}_SHA256=PASS",
                f"{source_name.upper()}_GIT_BLOB=PASS",
                f"{source_name.upper()}_PAGE_COUNT={len(reader.pages)}",
                f"{source_name.upper()}_LAYOUT_TEXT_PAGE_MARKERS={form_feed_pages}",
                f"{source_name.upper()}_RENDERED_PAGES={len(page_records)}",
                "",
            ]
        )

    demo_path = repo_root / SOURCE_SPECS["demo"]["path"]
    bbox_path = layout_directory / "demo-bbox.html"
    run(
        [
            pdftotext,
            "-bbox-layout",
            "-enc",
            "UTF-8",
            str(demo_path),
            str(bbox_path),
        ]
    )
    bbox_page_count = len(re.findall(rb"<page\b", bbox_path.read_bytes()))
    if bbox_page_count != SOURCE_SPECS["demo"]["page_count"]:
        raise RuntimeError(f"Bbox page count mismatch: {bbox_page_count}")

    pdfimages_output = inspection_directory / "demo-pdfimages-list.txt"
    run([pdfimages, "-list", str(demo_path)], stdout_path=pdfimages_output)

    demo_page_paths = [output / record["filename"] for record in rendered_records["demo"]]
    contact_sheet = output / "demo-contact-sheet.png"
    make_contact_sheet(demo_page_paths, contact_sheet)

    manifest = {
        "schema": "physics-2024-page-manifest-v1",
        "authority_statement": (
            "Derived review evidence only. Canonical source authority remains the tracked FIPI PDFs."
        ),
        "determinism": {
            "timestamp_included": False,
            "locale": "C",
            "timezone": "UTC",
            "full_page_render_no_crop": True,
            "post_render_resampling_of_full_pages": False,
        },
        "tools": tool_versions,
        "sources": manifest_sources,
        "demo_bbox": {
            "filename": "layout/demo-bbox.html",
            "page_count": bbox_page_count,
            "sha256": file_sha256(bbox_path),
            "generation_command": (
                "pdftotext -bbox-layout -enc UTF-8 "
                f"{SOURCE_SPECS['demo']['path']} layout/demo-bbox.html"
            ),
        },
        "demo_pdfimages_list": {
            "filename": "inspection/demo-pdfimages-list.txt",
            "sha256": file_sha256(pdfimages_output),
            "generation_command": (
                f"pdfimages -list {SOURCE_SPECS['demo']['path']}"
            ),
            "note": "PDF image object count is not an official visual count.",
        },
        "demo_contact_sheet": {
            "filename": "demo-contact-sheet.png",
            "source_page_count": len(demo_page_paths),
            "sha256": file_sha256(contact_sheet),
            "note": "Navigation evidence only; full-page PNG files remain the review artifacts.",
        },
    }
    manifest_path = output / "PAGE-MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    validation_lines.extend(
        [
            f"DEMO_BBOX_PAGES={bbox_page_count}",
            "FULL_PAGE_RENDER_NO_CROP=PASS",
            "FULL_PAGE_CANVAS_VALIDATION=PASS",
            "FULL_PAGE_NONBLANK_VALIDATION=PASS",
            "CONTACT_SHEET=PASS",
            "PAGE_MANIFEST=PASS",
        ]
    )
    (output / "VALIDATION.txt").write_text(
        "\n".join(validation_lines) + "\n", encoding="utf-8", newline="\n"
    )

    checksum_path = output / "OUTPUT-SHA256SUMS.txt"
    checksum_lines = []
    for path in sorted(candidate for candidate in output.rglob("*") if candidate.is_file()):
        if path == checksum_path:
            continue
        checksum_lines.append(f"{file_sha256(path)}  {path.relative_to(output).as_posix()}")
    checksum_path.write_text(
        "\n".join(checksum_lines) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
