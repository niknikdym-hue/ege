#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/tmp/base2022-source-analysis")
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "demo": ROOT / "ege-2022-matematika-baza-demoversiya.pdf",
    "spec": ROOT / "ege-2022-matematika-baza-specifikatsiya.pdf",
    "cod": ROOT / "ege-2022-matematika-kodifikator.pdf",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transformed_bounds(rect: fitz.Rect, matrix: fitz.Matrix) -> fitz.Rect:
    pts = [
        fitz.Point(rect.x0, rect.y0) * matrix,
        fitz.Point(rect.x1, rect.y0) * matrix,
        fitz.Point(rect.x0, rect.y1) * matrix,
        fitz.Point(rect.x1, rect.y1) * matrix,
    ]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    return fitz.Rect(min(xs), min(ys), max(xs), max(ys))


def group_words(words):
    words = sorted(words, key=lambda w: (w["y0"], w["x0"]))
    lines = []
    for word in words:
        y = word["y0"]
        h = max(1.0, word["y1"] - word["y0"])
        tol = max(2.2, min(5.0, h * 0.45))
        if not lines or abs(y - lines[-1]["anchor"]) > tol:
            lines.append({"anchor": y, "items": [word]})
        else:
            lines[-1]["items"].append(word)
            lines[-1]["anchor"] = (lines[-1]["anchor"] * 3 + y) / 4
    return [" ".join(w["text"] for w in sorted(line["items"], key=lambda x: x["x0"])) for line in lines]


def extract_pdf(label: str, pdf_path: Path, render: bool) -> dict:
    doc = fitz.open(pdf_path)
    dest = OUT / label
    dest.mkdir(parents=True, exist_ok=True)
    pages = []
    printed_counter = 0

    for physical_index, page in enumerate(doc, 1):
        matrix = page.rotation_matrix
        visual = transformed_bounds(page.mediabox, matrix)
        visual_mid = (visual.x0 + visual.x1) / 2
        buckets = {"left": [], "right": []}

        for w in page.get_text("words", sort=False):
            raw_rect = fitz.Rect(w[0], w[1], w[2], w[3])
            vr = raw_rect * matrix
            cx = (vr.x0 + vr.x1) / 2
            half = "left" if cx < visual_mid else "right"
            origin_x = visual.x0 if half == "left" else visual_mid
            buckets[half].append({
                "text": w[4],
                "x0": round(vr.x0 - origin_x, 3),
                "y0": round(vr.y0 - visual.y0, 3),
                "x1": round(vr.x1 - origin_x, 3),
                "y1": round(vr.y1 - visual.y0, 3),
                "block": w[5],
                "line": w[6],
                "word": w[7],
            })

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False) if render else None
        raster = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) if pix else None
        raster_mid = raster.width // 2 if raster else None

        for half in ("left", "right"):
            words = buckets[half]
            if not words:
                continue
            printed_counter += 1
            text = "\n".join(group_words(words)).strip() + "\n"
            (dest / f"page-{printed_counter:02d}.txt").write_text(text, encoding="utf-8")
            record = {
                "printed_page": printed_counter,
                "physical_pdf_page": physical_index,
                "half": half,
                "visual_width_pt": round(visual.width / 2, 3),
                "visual_height_pt": round(visual.height, 3),
                "word_count": len(words),
                "words": sorted(words, key=lambda x: (x["y0"], x["x0"])),
            }
            (dest / f"page-{printed_counter:02d}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if raster:
                crop = raster.crop((0, 0, raster_mid, raster.height) if half == "left" else (raster_mid, 0, raster.width, raster.height))
                crop.save(dest / f"page-{printed_counter:02d}.webp", "WEBP", lossless=True, method=6)
            pages.append({k: v for k, v in record.items() if k != "words"})

    meta = {
        "label": label,
        "source_file": pdf_path.name,
        "sha256": sha256(pdf_path),
        "bytes": pdf_path.stat().st_size,
        "physical_pdf_pages": len(doc),
        "generated_printed_pages": printed_counter,
        "geometry_rule": "mediabox transformed once by page.rotation_matrix; visual spread split by transformed X midpoint; blank halves skipped",
        "pages": pages,
    }
    (dest / "PAGE-MAP.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta


summary = {label: extract_pdf(label, path, render=(label == "demo")) for label, path in SOURCES.items()}
(OUT / "SOURCE-LOCK.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report = ["BASE 2022 SOURCE ANALYSIS", ""]
for label in ("demo", "spec", "cod"):
    m = summary[label]
    report += [
        f"{label.upper()}",
        f"file={m['source_file']}",
        f"sha256={m['sha256']}",
        f"bytes={m['bytes']}",
        f"physical_pdf_pages={m['physical_pdf_pages']}",
        f"generated_printed_pages={m['generated_printed_pages']}",
        "",
    ]
(OUT / "SOURCE-LOCK.txt").write_text("\n".join(report), encoding="utf-8")
print((OUT / "SOURCE-LOCK.txt").read_text(encoding="utf-8"))
