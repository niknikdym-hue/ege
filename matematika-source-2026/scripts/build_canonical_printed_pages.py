#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "canonical-printed-pages"
EVIDENCE_ROOT = ROOT.parent / "ege-matematika-baza-demoversiya-2026" / "source-evidence" / "printed-pages"
COORD_ROOT = ROOT.parent / "ege-matematika-baza-demoversiya-2026" / "source-diagnostics" / "canonical-coordinates"

JOBS = [
    ("base-demo", ROOT / "original" / "МА-11 ЕГЭ 2026 ДЕМО_базовый.pdf", 29),
    ("base-spec", ROOT / "original" / "МА-11 ЕГЭ 2026 СПЕЦ_базовый.pdf", 12),
    ("profile-demo", ROOT / "original" / "МА-11 ЕГЭ 2026 ДЕМО_профильный.pdf", None),
    ("profile-spec", ROOT / "original" / "МА-11 ЕГЭ 2026 СПЕЦ_профильный.pdf", None),
    ("codifier", ROOT / "original" / "МА-11 ЕГЭ 2026_КОДИФ.pdf", 18),
]


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
    """Group transformed words into visual text lines without merging across page halves."""
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


def split_pdf(name, pdf_path, expected_pages):
    dest = OUT / name
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("page-*.txt"):
        old.unlink()

    doc = fitz.open(pdf_path)
    pages = []
    printed_no = 0
    base_demo_evidence = []

    for physical_index, page in enumerate(doc, start=1):
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

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        raster = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        raster_mid = raster.width // 2

        for half in ("left", "right"):
            printed_no += 1
            if expected_pages is not None and printed_no > expected_pages:
                break

            words = buckets[half]
            text = "\n".join(group_words(words)).strip() + "\n"
            text_path = dest / f"page-{printed_no:02d}.txt"
            text_path.write_text(text, encoding="utf-8")

            row = {
                "printed_page": printed_no,
                "physical_pdf_page": physical_index,
                "half": half,
                "visual_width_pt": round(visual.width / 2, 3),
                "visual_height_pt": round(visual.height, 3),
                "word_count": len(words),
                "text_file": str(text_path),
            }
            pages.append(row)

            if name == "base-demo":
                COORD_ROOT.mkdir(parents=True, exist_ok=True)
                coord_path = COORD_ROOT / f"page-{printed_no:02d}.json"
                coord_path.write_text(json.dumps({**row, "words": sorted(words, key=lambda x: (x["y0"], x["x0"]))}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

                EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
                crop = raster.crop((0, 0, raster_mid, raster.height) if half == "left" else (raster_mid, 0, raster.width, raster.height))
                image_path = EVIDENCE_ROOT / f"page-{printed_no:02d}.webp"
                crop.save(image_path, "WEBP", quality=94, method=6)
                blob = image_path.read_bytes()
                base_demo_evidence.append({
                    "printed_page": printed_no,
                    "physical_pdf_page": physical_index,
                    "half": half,
                    "width_px": crop.width,
                    "height_px": crop.height,
                    "bytes": len(blob),
                    "sha256": hashlib.sha256(blob).hexdigest(),
                    "file": str(image_path),
                })

        if expected_pages is not None and printed_no >= expected_pages:
            break

    (dest / "PAGE-MAP.json").write_text(json.dumps({
        "source_pdf": str(pdf_path),
        "physical_pdf_pages": len(doc),
        "expected_printed_pages": expected_pages,
        "generated_printed_pages": len(pages),
        "geometry_rule": "mediabox transformed exactly once by page.rotation_matrix; visual page split by transformed X midpoint",
        "pages": pages,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if name == "base-demo":
        (EVIDENCE_ROOT / "SOURCE-PAGE-EVIDENCE.json").write_text(json.dumps({
            "source_pdf": str(pdf_path),
            "render_scale": 2,
            "format": "webp",
            "quality": 94,
            "geometry_rule": "get_pixmap display orientation split into equal left/right printed pages",
            "pages": base_demo_evidence,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


for job in JOBS:
    split_pdf(*job)

print("Canonical mathematics 2026 printed-page preprocessing complete")
