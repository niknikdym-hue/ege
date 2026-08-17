#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/tmp/base2023-source-analysis")
OUT.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "demo": ROOT / "ege-2023-matematika-baza-demoversiya.pdf",
    "spec": ROOT / "ege-2023-matematika-baza-specifikatsiya.pdf",
    "cod": ROOT / "ege-2023-matematika-kodifikator.pdf",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        rect = page.rect
        words_raw = page.get_text("words", sort=False)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False) if render else None
        raster = Image.frombytes("RGB", [pix.width, pix.height], pix.samples) if pix else None

        is_spread = rect.width > rect.height * 1.15
        halves = ["full"] if not is_spread else ["left", "right"]
        for half in halves:
            if half == "full":
                x0, x1 = 0.0, rect.width
                rx0 = 0
                rx1 = raster.width if raster else None
            elif half == "left":
                x0, x1 = 0.0, rect.width / 2
                rx0 = 0
                rx1 = raster.width // 2 if raster else None
            else:
                x0, x1 = rect.width / 2, rect.width
                rx0 = raster.width // 2 if raster else None
                rx1 = raster.width if raster else None

            selected = []
            for w in words_raw:
                wr = fitz.Rect(w[0], w[1], w[2], w[3])
                cx = (wr.x0 + wr.x1) / 2
                if not (x0 <= cx < x1):
                    continue
                selected.append({
                    "text": w[4],
                    "x0": round(wr.x0 - x0, 3),
                    "y0": round(wr.y0, 3),
                    "x1": round(wr.x1 - x0, 3),
                    "y1": round(wr.y1, 3),
                    "block": w[5],
                    "line": w[6],
                    "word": w[7],
                })

            if is_spread and not selected:
                continue
            printed_counter += 1
            text = "\n".join(group_words(selected)).strip() + "\n"
            (dest / f"page-{printed_counter:02d}.txt").write_text(text, encoding="utf-8")
            record = {
                "printed_page": printed_counter,
                "physical_pdf_page": physical_index,
                "half": half,
                "physical_width_pt": round(rect.width, 3),
                "physical_height_pt": round(rect.height, 3),
                "word_count": len(selected),
                "words": selected,
            }
            (dest / f"page-{printed_counter:02d}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if raster:
                crop = raster if half == "full" else raster.crop((rx0, 0, rx1, raster.height))
                crop.save(dest / f"page-{printed_counter:02d}.webp", "WEBP", lossless=True, method=6)
            pages.append({k: v for k, v in record.items() if k != "words"})

    meta = {
        "label": label,
        "source_file": pdf_path.name,
        "sha256": sha256(pdf_path),
        "bytes": pdf_path.stat().st_size,
        "physical_pdf_pages": len(doc),
        "generated_printed_pages": printed_counter,
        "pages": pages,
    }
    (dest / "PAGE-MAP.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta


summary = {}
for label, path in SOURCES.items():
    summary[label] = extract_pdf(label, path, render=(label == "demo"))

(OUT / "SOURCE-LOCK.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report = ["BASE 2023 SOURCE ANALYSIS", ""]
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
