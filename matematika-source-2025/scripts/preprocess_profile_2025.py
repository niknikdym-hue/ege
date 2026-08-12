#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path

import pymupdf as fitz
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "matematika-source-2025"
PROJECT = REPO / "ege-matematika-profil-demoversiya-2025"
OUT = SRC / "canonical-profile-printed-pages"
EVIDENCE = PROJECT / "source-evidence" / "printed-pages"
COORDS = PROJECT / "source-diagnostics" / "canonical-coordinates"
ASSETS = PROJECT / "assets"

JOBS = [
    ("profile-demo", SRC / "ege-2025-matematika-profil-demoversiya.pdf"),
    ("profile-spec", SRC / "ege-2025-matematika-profil-specifikatsiya.pdf"),
    ("codifier", SRC / "ege-2025-matematika-kodifikator.pdf"),
]

# Printed-page crop coordinates in PDF points. The generated asset is a direct
# crop of the official PDF raster; no formula/text reconstruction is used.
# For alternative official examples, y0 starts below the red structural label
# "ИЛИ": the learner receives one already-assigned official condition, not a
# visible choice between variants.
CONDITION_CROPS = {
    "1-1": (4, 155, 272), "1-2": (4, 295, 393), "1-3": (4, 415, 492), "1-4": (5, 75, 155),
    "2-1": (5, 165, 337), "2-2": (5, 363, 415),
    "3-1": (5, 420, 520), "3-2": (6, 75, 180), "3-3": (6, 207, 340),
    "4-1": (6, 360, 420), "4-2": (6, 446, 515),
    "5-1": (7, 52, 125), "5-2": (7, 150, 215),
    "6-1": (7, 235, 290), "6-2": (7, 316, 370), "6-3": (7, 395, 440), "6-4": (7, 465, 515),
    "7-1": (8, 52, 95), "7-2": (8, 130, 190), "7-3": (8, 225, 275),
    "8-1": (8, 290, 465), "8-2": (9, 75, 315),
    "9-1": (9, 330, 485),
    "10-1": (10, 52, 125), "10-2": (10, 150, 225), "10-3": (10, 250, 315),
    "11-1": (10, 330, 545),
    "12-1": (11, 52, 125), "12-2": (11, 170, 225), "12-3": (11, 270, 325),
    "13-1": (12, 125, 205), "14-1": (12, 200, 300), "15-1": (12, 295, 350), "16-1": (12, 345, 590),
    "17-1": (13, 55, 145), "18-1": (13, 140, 240), "19-1": (13, 240, 390),
}

EXPECTED_VARIANT_COUNTS = {
    1: 4, 2: 2, 3: 3, 4: 2, 5: 2, 6: 4, 7: 3, 8: 2, 9: 1,
    10: 3, 11: 1, 12: 3, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1, 19: 1,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def split_pdf(name: str, pdf_path: Path):
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    dest = OUT / name
    img_dest = EVIDENCE / name
    coord_dest = COORDS / name
    for folder in (dest, img_dest, coord_dest):
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("page-*"):
            old.unlink()

    doc = fitz.open(pdf_path)
    printed_no = 0
    rows = []
    source_text_parts = []

    for physical_index, page in enumerate(doc, start=1):
        matrix = page.rotation_matrix
        visual = transformed_bounds(page.mediabox, matrix)
        visual_mid = (visual.x0 + visual.x1) / 2
        buckets = {"left": [], "right": []}

        for w in page.get_text("words", sort=False):
            vr = fitz.Rect(w[0], w[1], w[2], w[3]) * matrix
            cx = (vr.x0 + vr.x1) / 2
            half = "left" if cx < visual_mid else "right"
            origin_x = visual.x0 if half == "left" else visual_mid
            buckets[half].append({
                "text": w[4], "x0": round(vr.x0 - origin_x, 3), "y0": round(vr.y0 - visual.y0, 3),
                "x1": round(vr.x1 - origin_x, 3), "y1": round(vr.y1 - visual.y0, 3),
                "block": w[5], "line": w[6], "word": w[7],
            })

        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        raster = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        raster_mid = raster.width // 2

        for half in ("left", "right"):
            crop = raster.crop((0, 0, raster_mid, raster.height) if half == "left" else (raster_mid, 0, raster.width, raster.height))
            words = buckets[half]
            text = "\n".join(group_words(words)).strip()
            if not text and physical_index == len(doc) and half == "right":
                continue

            printed_no += 1
            text += "\n"
            source_text_parts.append(text)
            ordered_words = sorted(words, key=lambda x: (x["y0"], x["x0"]))

            text_path = dest / f"page-{printed_no:02d}.txt"
            text_path.write_text(text, encoding="utf-8")
            image_path = img_dest / f"page-{printed_no:02d}.webp"
            crop.save(image_path, "WEBP", quality=96, method=6)
            image_blob = image_path.read_bytes()
            coord_path = coord_dest / f"page-{printed_no:02d}.json"
            coord_path.write_text(json.dumps({
                "printed_page": printed_no, "physical_pdf_page": physical_index, "half": half,
                "visual_width_pt": round(visual.width / 2, 3), "visual_height_pt": round(visual.height, 3),
                "words": ordered_words,
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            rows.append({
                "printed_page": printed_no, "physical_pdf_page": physical_index, "half": half,
                "visual_width_pt": round(visual.width / 2, 3), "visual_height_pt": round(visual.height, 3),
                "word_count": len(words), "text_file": str(text_path.relative_to(REPO)),
                "image_file": str(image_path.relative_to(REPO)), "image_bytes": len(image_blob),
                "image_sha256": hashlib.sha256(image_blob).hexdigest(),
                "coordinates_file": str(coord_path.relative_to(REPO)),
            })

    joined_text = "\n".join(source_text_parts)
    standalone_project_marker = bool(re.search(r"(?mi)^\s*ПРОЕКТ\s*$", joined_text))
    checks = {
        "contains_2025": "2025" in joined_text,
        "contains_profile_marker": ("Профильный" in joined_text) if name != "codifier" else True,
        "standalone_project_marker": standalone_project_marker,
    }
    page_map = {
        "source_pdf": str(pdf_path.relative_to(REPO)), "source_bytes": pdf_path.stat().st_size,
        "source_sha256": sha256_file(pdf_path), "physical_pdf_pages": len(doc),
        "generated_printed_pages": len(rows),
        "geometry_rule": "mediabox transformed once by page.rotation_matrix; displayed two-up page split at visual X midpoint",
        "checks": checks, "pages": rows,
    }
    (dest / "PAGE-MAP.json").write_text(json.dumps(page_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if standalone_project_marker:
        raise RuntimeError(f"{pdf_path.name}: standalone ПРОЕКТ marker found")
    if not checks["contains_2025"]:
        raise RuntimeError(f"{pdf_path.name}: 2025 marker not found")
    if not checks["contains_profile_marker"]:
        raise RuntimeError(f"{pdf_path.name}: profile marker not found")
    return page_map


def build_condition_assets():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for old in ASSETS.glob("condition-*.webp"):
        old.unlink()
    manifest = []
    demo_pages = EVIDENCE / "profile-demo"
    for key, (page_no, y0_pt, y1_pt) in CONDITION_CROPS.items():
        source_image = demo_pages / f"page-{page_no:02d}.webp"
        if not source_image.exists():
            raise FileNotFoundError(source_image)
        im = Image.open(source_image).convert("RGB")
        y0 = max(0, round(y0_pt * 2))
        y1 = min(im.height, round(y1_pt * 2))
        crop = im.crop((0, y0, im.width, y1))
        asset_path = ASSETS / f"condition-{key}.webp"
        crop.save(asset_path, "WEBP", quality=96, method=6)
        blob = asset_path.read_bytes()
        manifest.append({
            "example": key, "source_printed_page": page_no, "crop_y_pt": [y0_pt, y1_pt],
            "file": str(asset_path.relative_to(REPO)), "width_px": crop.width, "height_px": crop.height,
            "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
            "source_mode": "direct official PDF raster crop; alternate structural OR label omitted from learner crop",
        })

    expected_total = sum(EXPECTED_VARIANT_COUNTS.values())
    if len(manifest) != expected_total:
        raise RuntimeError(f"expected {expected_total} condition assets, got {len(manifest)}")
    (PROJECT / "ege-matematika-profil-demoversiya-2025-ASSET-MAP.generated.json").write_text(
        json.dumps({
            "status": "SOURCE_ASSETS_BUILT", "official_examples_total": expected_total,
            "variant_counts": {str(k): v for k, v in EXPECTED_VARIANT_COUNTS.items()}, "assets": manifest,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


for folder in (PROJECT, OUT, EVIDENCE, COORDS, ASSETS):
    folder.mkdir(parents=True, exist_ok=True)

inventory = {"status": "SOURCE_PREPROCESSING_ONLY", "exam": "ЕГЭ", "subject": "математика", "level": "профильный", "source_year": 2025, "sources": {}}
for job_name, job_path in JOBS:
    inventory["sources"][job_name] = split_pdf(job_name, job_path)
assets = build_condition_assets()
inventory["official_condition_assets"] = len(assets)

inventory_path = PROJECT / "ege-matematika-profil-demoversiya-2025-SOURCE-INVENTORY.generated.json"
inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps({
    "status": "PASS", "inventory": str(inventory_path.relative_to(REPO)), "condition_assets": len(assets),
    "sources": {k: {"sha256": v["source_sha256"], "bytes": v["source_bytes"], "physical_pdf_pages": v["physical_pdf_pages"], "printed_pages": v["generated_printed_pages"], "checks": v["checks"]} for k, v in inventory["sources"].items()},
}, ensure_ascii=False, indent=2))
