#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
CANON = ROOT / "canonical-printed-pages"
EVIDENCE = REPO / "ege-matematika-baza-demoversiya-2024" / "source-evidence" / "printed-pages"
COORD = REPO / "ege-matematika-baza-demoversiya-2024" / "source-diagnostics" / "canonical-coordinates"

JOBS = [
    ("base-demo", ROOT / "ege-2024-matematika-baza-demoversiya.pdf", True),
    ("base-spec", ROOT / "ege-2024-matematika-baza-specifikatsiya.pdf", False),
    ("codifier", ROOT / "ege-2024-matematika-kodifikator.pdf", False),
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


def split_pdf(name, pdf_path, make_evidence):
    dest = CANON / name
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("page-*.*"):
        old.unlink()

    doc = fitz.open(pdf_path)
    rows = []
    evidence_rows = []
    printed_no = 0

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
            words = buckets[half]
            # Skip truly blank imposed halves.
            if not words:
                continue
            printed_no += 1
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
                "text_file": str(text_path.relative_to(REPO)),
            }
            rows.append(row)

            if make_evidence:
                COORD.mkdir(parents=True, exist_ok=True)
                coord_path = COORD / f"page-{printed_no:02d}.json"
                coord_path.write_text(json.dumps({**row, "words": sorted(words, key=lambda x: (x["y0"], x["x0"]))}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

                EVIDENCE.mkdir(parents=True, exist_ok=True)
                crop = raster.crop((0, 0, raster_mid, raster.height) if half == "left" else (raster_mid, 0, raster.width, raster.height))
                img_path = EVIDENCE / f"page-{printed_no:02d}.webp"
                crop.save(img_path, "WEBP", lossless=True, method=6)
                blob = img_path.read_bytes()
                evidence_rows.append({
                    "printed_page": printed_no,
                    "physical_pdf_page": physical_index,
                    "half": half,
                    "width_px": crop.width,
                    "height_px": crop.height,
                    "bytes": len(blob),
                    "sha256": hashlib.sha256(blob).hexdigest(),
                    "file": str(img_path.relative_to(REPO)),
                })

    (dest / "PAGE-MAP.json").write_text(json.dumps({
        "source_pdf": str(pdf_path.relative_to(REPO)),
        "physical_pdf_pages": len(doc),
        "generated_printed_pages": len(rows),
        "geometry_rule": "mediabox transformed once by page.rotation_matrix; visual spread split by transformed X midpoint; blank halves skipped",
        "pages": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if make_evidence:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        (EVIDENCE / "SOURCE-PAGE-EVIDENCE.json").write_text(json.dumps({
            "source_pdf": str(pdf_path.relative_to(REPO)),
            "render_scale": 2,
            "format": "lossless webp",
            "pages": evidence_rows,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"job": name, "physical_pages": len(doc), "printed_pages": len(rows)}, ensure_ascii=False))


for job in JOBS:
    split_pdf(*job)
