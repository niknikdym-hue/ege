#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "matematika-source-2025"
PROJECT = REPO / "ege-matematika-profil-demoversiya-2025"
OUT = SRC / "canonical-profile-printed-pages"
EVIDENCE = PROJECT / "source-evidence" / "printed-pages"
COORDS = PROJECT / "source-diagnostics" / "canonical-coordinates"

JOBS = [
    ("profile-demo", SRC / "ege-2025-matematika-profil-demoversiya.pdf"),
    ("profile-spec", SRC / "ege-2025-matematika-profil-specifikatsiya.pdf"),
    ("codifier", SRC / "ege-2025-matematika-kodifikator.pdf"),
]


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
    return [
        " ".join(w["text"] for w in sorted(line["items"], key=lambda x: x["x0"]))
        for line in lines
    ]


def is_blank_half(words, crop: Image.Image) -> bool:
    if words:
        return False
    extrema = crop.convert("L").getextrema()
    return extrema is not None and extrema[0] >= 250


def split_pdf(name: str, pdf_path: Path):
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    dest = OUT / name
    img_dest = EVIDENCE / name
    coord_dest = COORDS / name
    for folder in (dest, img_dest, coord_dest):
        folder.mkdir(parents=True, exist_ok=True)
        for pattern in ("page-*.txt", "page-*.webp", "page-*.json", "PAGE-MAP.json"):
            for old in folder.glob(pattern):
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
            crop = raster.crop(
                (0, 0, raster_mid, raster.height)
                if half == "left"
                else (raster_mid, 0, raster.width, raster.height)
            )
            words = buckets[half]
            if is_blank_half(words, crop):
                continue

            printed_no += 1
            ordered_words = sorted(words, key=lambda x: (x["y0"], x["x0"]))
            text = "\n".join(group_words(words)).strip() + "\n"
            source_text_parts.append(text)

            text_path = dest / f"page-{printed_no:02d}.txt"
            text_path.write_text(text, encoding="utf-8")

            image_path = img_dest / f"page-{printed_no:02d}.webp"
            crop.save(image_path, "WEBP", quality=96, method=6)
            image_blob = image_path.read_bytes()

            coord_path = coord_dest / f"page-{printed_no:02d}.json"
            coord_payload = {
                "printed_page": printed_no,
                "physical_pdf_page": physical_index,
                "half": half,
                "visual_width_pt": round(visual.width / 2, 3),
                "visual_height_pt": round(visual.height, 3),
                "words": ordered_words,
            }
            coord_path.write_text(
                json.dumps(coord_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            rows.append({
                "printed_page": printed_no,
                "physical_pdf_page": physical_index,
                "half": half,
                "visual_width_pt": round(visual.width / 2, 3),
                "visual_height_pt": round(visual.height, 3),
                "word_count": len(words),
                "text_file": str(text_path.relative_to(REPO)),
                "image_file": str(image_path.relative_to(REPO)),
                "image_bytes": len(image_blob),
                "image_sha256": hashlib.sha256(image_blob).hexdigest(),
                "coordinates_file": str(coord_path.relative_to(REPO)),
            })

    joined_text = "\n".join(source_text_parts)
    checks = {
        "contains_2025": "2025" in joined_text,
        "contains_profile_marker": ("Профильный" in joined_text) if name != "codifier" else True,
        "contains_project_marker": "ПРОЕКТ" in joined_text.upper(),
    }

    page_map = {
        "source_pdf": str(pdf_path.relative_to(REPO)),
        "source_bytes": pdf_path.stat().st_size,
        "source_sha256": sha256_file(pdf_path),
        "physical_pdf_pages": len(doc),
        "generated_printed_pages": len(rows),
        "geometry_rule": "mediabox transformed exactly once by page.rotation_matrix; displayed page split by transformed X midpoint; only a fully blank trailing half is omitted",
        "checks": checks,
        "pages": rows,
    }
    (dest / "PAGE-MAP.json").write_text(
        json.dumps(page_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if checks["contains_project_marker"]:
        raise RuntimeError(f"{pdf_path.name}: source contains prohibited ПРОЕКТ marker")
    if not checks["contains_2025"]:
        raise RuntimeError(f"{pdf_path.name}: 2025 marker not found")
    if not checks["contains_profile_marker"]:
        raise RuntimeError(f"{pdf_path.name}: profile marker not found")

    return page_map


PROJECT.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
COORDS.mkdir(parents=True, exist_ok=True)

inventory = {
    "status": "SOURCE_PREPROCESSING_ONLY",
    "exam": "ЕГЭ",
    "subject": "математика",
    "level": "профильный",
    "source_year": 2025,
    "sources": {},
}
for job_name, job_path in JOBS:
    inventory["sources"][job_name] = split_pdf(job_name, job_path)

inventory_path = PROJECT / "ege-matematika-profil-demoversiya-2025-SOURCE-INVENTORY.generated.json"
inventory_path.write_text(
    json.dumps(inventory, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(json.dumps({
    "status": "PASS",
    "inventory": str(inventory_path.relative_to(REPO)),
    "sources": {
        k: {
            "sha256": v["source_sha256"],
            "bytes": v["source_bytes"],
            "physical_pdf_pages": v["physical_pdf_pages"],
            "printed_pages": v["generated_printed_pages"],
            "checks": v["checks"],
        }
        for k, v in inventory["sources"].items()
    },
}, ensure_ascii=False, indent=2))
