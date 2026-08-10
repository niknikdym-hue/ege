#!/usr/bin/env python3
import hashlib
import json
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "source-evidence" / "printed-pages"
COORD = ROOT / "source-diagnostics" / "canonical-coordinates"
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

# Full official-example regions. A figure can continue below the printed Ответ:
# line when the answer line is on the left and the figure is on the right, so the
# correct lower boundary is the next ИЛИ / next task marker, not Ответ:.
SPECS = [
    ("base-03-v1-temperature-chart", 10, 59, 292, 1),
    ("base-03-v3-nickel-chart", 11, 56, 353, 1),
    ("base-07-v1-derivative-graph", 14, 262, 540, 1),
    ("base-07-v2-torque-chart", 15, 57, 540, 1),
    ("base-07-v3-function-graphs", 16, 56, 540, 8),
    ("base-09-v1-lake-plan", 18, 63, 323, 1),
    ("base-09-v2-grid-plan", 18, 322, 540, 1),
    ("base-10-v1-dacha-plan", 19, 59, 171, 1),
    ("base-10-v2-wheel", 19, 170, 272, 1),
    ("base-10-v3-fence-plan", 19, 271, 540, 2),
    ("base-11-v1-tank", 20, 59, 158, 1),
    ("base-11-v2-cut-prism", 20, 157, 254, 1),
    ("base-11-v3-polyhedron", 20, 253, 417, 1),
    ("base-11-v4-boxes", 20, 416, 540, 1),
    ("base-12-v1-triangle-median", 21, 59, 145, 1),
    ("base-12-v2-circle-chord", 21, 144, 233, 1),
    ("base-12-v3-right-triangle", 21, 232, 313, 1),
    ("base-12-v4-midline", 21, 312, 540, 1),
    ("base-13-v1-cone", 22, 62, 146, 1),
    ("base-13-v2-pyramid", 22, 145, 237, 1),
    ("base-13-v3-cylinders", 22, 236, 339, 2),
    ("base-13-v4-spheres", 22, 338, 540, 2),
    ("base-18-v1-number-line", 25, 59, 278, 1),
    ("base-18-v3-number-line", 26, 56, 340, 1),
    ("base-21-v2-rectangle-partition", 28, 148, 253, 1),
]

MONTHS = {"янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"}
LABELS = MONTHS | {"x", "y", "A", "B", "C", "D", "А", "Б", "В", "Г", "M", "N", "K", "м", "км", "см", "м²", "м³", "°"}


def mask_text(rgb, words, sx, sy):
    out = rgb.copy()
    for w in words:
        x0 = max(0, int(w["x0"] * sx) - 4)
        x1 = min(out.shape[1], int(w["x1"] * sx) + 5)
        y0 = max(0, int(w["y0"] * sy) - 4)
        y1 = min(out.shape[0], int(w["y1"] * sy) + 5)
        if x1 > x0 and y1 > y0:
            out[y0:y1, x0:x1] = 255
    return out


def detect_components(img, words, sx, sy, y0_pt, y1_pt):
    masked = mask_text(np.array(img), words, sx, sy)
    gray = cv2.cvtColor(masked, cv2.COLOR_RGB2GRAY)
    raw = np.zeros_like(gray, dtype=np.uint8)
    top = int(y0_pt * sy)
    bottom = int(y1_pt * sy)
    left = int(18 * sx)
    right = int((img.width / sx - 18) * sx)
    raw[top:bottom, :] = (gray[top:bottom, :] < 225).astype(np.uint8) * 255
    raw[:, :left] = 0
    raw[:, right:] = 0

    # Morphology is used ONLY to group strokes into the same diagram.
    grouped = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)
    grouped = cv2.dilate(grouped, cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5)), iterations=1)
    n, _, stats, _ = cv2.connectedComponentsWithStats(grouped, 8)
    components = []
    for i in range(1, n):
        x, y, w, h, area = [int(v) for v in stats[i]]
        if area < 45 or (w < 8 and h < 8):
            continue
        if h <= 7 and w >= 100:
            continue
        if w <= 7 and h >= 100:
            continue
        components.append({"x": x, "y": y, "w": w, "h": h, "area": area, "bbox_area": w * h})
    components.sort(key=lambda c: (c["area"], c["bbox_area"]), reverse=True)
    return components, raw, (top, bottom, left, right)


def selected_raw_geometry(raw, chosen):
    """Return undilated source pixels located inside selected component boxes."""
    selected = np.zeros_like(raw, dtype=np.uint8)
    for c in chosen:
        x0, y0 = c["x"], c["y"]
        x1, y1 = x0 + c["w"], y0 + c["h"]
        selected[y0:y1, x0:x1] = np.maximum(selected[y0:y1, x0:x1], raw[y0:y1, x0:x1])
    ys, xs = np.where(selected > 0)
    if not len(xs):
        raise RuntimeError("selected component contains no undilated source ink")
    return selected, (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)


def near(word, bbox_pt, pad=16):
    x0, y0, x1, y1 = bbox_pt
    return not (
        word["x1"] < x0 - pad or word["x0"] > x1 + pad or
        word["y1"] < y0 - pad or word["y0"] > y1 + pad
    )


def is_diagram_label(text):
    token = text.strip().strip(".,:;()")
    if not token:
        return False
    if token in LABELS:
        return True
    if re.fullmatch(r"[−–-]?\d+(?:[,.]\d+)?", token):
        return True
    if re.fullmatch(r"[A-Za-zА-ЯЁ]", token):
        return True
    return False


def ascii_preview(crop, columns=56):
    rows = max(6, int(crop.height / max(1, crop.width) * columns * 0.45))
    small = np.array(crop.convert("L").resize((columns, rows), Image.Resampling.LANCZOS))
    return "\n".join(
        "".join("█" if v < 130 else ("▓" if v < 190 else ("·" if v < 235 else " ")) for v in row)
        for row in small
    )


records = []
previews = []
errors = []

for asset_id, page_no, y0_pt, y1_pt, expected_count in SPECS:
    img = Image.open(PAGES / f"page-{page_no:02d}.webp").convert("RGB")
    coord = json.loads((COORD / f"page-{page_no:02d}.json").read_text(encoding="utf-8"))
    sx = img.width / coord["visual_width_pt"]
    sy = img.height / coord["visual_height_pt"]

    components, raw, band = detect_components(img, coord["words"], sx, sy, y0_pt, y1_pt)
    if len(components) < expected_count:
        raise RuntimeError(f"{asset_id}: need {expected_count} components, found {len(components)}")
    chosen = components[:expected_count]
    selected_raw, raw_bbox = selected_raw_geometry(raw, chosen)
    rx0, ry0, rx1, ry1 = raw_bbox
    band_top, band_bottom, band_left, band_right = band

    source_gaps = {
        "top": ry0 - band_top,
        "bottom": band_bottom - ry1,
        "left": rx0 - band_left,
        "right": band_right - rx1,
    }
    geometry_clipped = any(v <= 0 for v in source_gaps.values())
    source_boundary_ink_px = int(
        selected_raw[band_top:band_top + 1, band_left:band_right].sum() / 255 +
        selected_raw[max(band_top, band_bottom - 1):band_bottom, band_left:band_right].sum() / 255 +
        selected_raw[band_top:band_bottom, band_left:band_left + 1].sum() / 255 +
        selected_raw[band_top:band_bottom, max(band_left, band_right - 1):band_right].sum() / 255
    )
    if geometry_clipped or source_boundary_ink_px:
        errors.append(
            f"{asset_id}: selected real source geometry reaches official variant boundary "
            f"gaps={source_gaps}, boundaryInk={source_boundary_ink_px}"
        )

    bbox_pt = [rx0 / sx, ry0 / sy, rx1 / sx, ry1 / sy]
    labels = [
        w for w in coord["words"]
        if y0_pt <= (w["y0"] + w["y1"]) / 2 <= y1_pt
        and is_diagram_label(w["text"])
        and near(w, bbox_pt)
    ]
    if labels:
        bbox_pt = [
            min(bbox_pt[0], min(w["x0"] for w in labels)),
            min(bbox_pt[1], min(w["y0"] for w in labels)),
            max(bbox_pt[2], max(w["x1"] for w in labels)),
            max(bbox_pt[3], max(w["y1"] for w in labels)),
        ]

    pad = 12
    bbox_pt = [
        max(18, bbox_pt[0] - pad),
        max(y0_pt, bbox_pt[1] - pad),
        min(coord["visual_width_pt"] - 18, bbox_pt[2] + pad),
        min(y1_pt, bbox_pt[3] + pad),
    ]
    crop_px = [
        int(bbox_pt[0] * sx), int(bbox_pt[1] * sy),
        int(np.ceil(bbox_pt[2] * sx)), int(np.ceil(bbox_pt[3] * sy)),
    ]
    crop = img.crop(tuple(crop_px))

    local = selected_raw[crop_px[1]:crop_px[3], crop_px[0]:crop_px[2]] > 0
    edge = min(5, max(1, min(local.shape) // 4))
    crop_edge_diagnostic = int(
        local[:edge, :].sum() + local[-edge:, :].sum() +
        local[:, :edge].sum() + local[:, -edge:].sum()
    ) if local.size else 999999

    included_words = [
        w["text"] for w in coord["words"]
        if not (
            w["x1"] < bbox_pt[0] or w["x0"] > bbox_pt[2] or
            w["y1"] < bbox_pt[1] or w["y0"] > bbox_pt[3]
        )
    ]
    prose = [x for x in included_words if len(x.strip(".,:;()")) > 14]
    if prose:
        errors.append(f"{asset_id}: likely prose in crop {prose[:5]}")

    path = ASSETS / f"{asset_id}.webp"
    crop.save(path, "WEBP", lossless=True, method=6)
    blob = path.read_bytes()
    status = "PASS" if not geometry_clipped and source_boundary_ink_px == 0 and not prose else "FAIL"
    rec = {
        "id": asset_id,
        "source_page": page_no,
        "official_variant_region_pt": [y0_pt, y1_pt],
        "expected_components": expected_count,
        "selected_components": chosen,
        "selected_source_bbox_px": [rx0, ry0, rx1, ry1],
        "source_boundary_gap_px": source_gaps,
        "source_boundary_ink_px": source_boundary_ink_px,
        "geometry_clipped": geometry_clipped,
        "crop_pt": [round(v, 2) for v in bbox_pt],
        "crop_px": crop_px,
        "width_px": crop.width,
        "height_px": crop.height,
        "bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "lossless_webp": True,
        "crop_edge_source_ink_px_diagnostic_only": crop_edge_diagnostic,
        "included_source_words": included_words,
        "status": status,
    }
    records.append(rec)
    previews += [
        f"===== {asset_id} page={page_no} sourceGaps={source_gaps} "
        f"boundaryInk={source_boundary_ink_px} cropEdgeDiagnostic={crop_edge_diagnostic} {status} =====",
        "WORDS: " + " ".join(included_words),
        ascii_preview(crop),
        "",
    ]

status = "PASS" if not errors and len(records) == 25 else "FAIL"
evidence = {
    "status": status,
    "source": "official FIPI 2026 base mathematics PDF via canonical printed-page render",
    "method": "full official variant region between variant markers; morphology locates diagram components; final clipping proof uses only undilated source pixels inside selected component boxes",
    "asset_count": len(records),
    "errors": errors,
    "records": records,
}
(ROOT / "source-evidence" / "ASSET-CROP-EVIDENCE.json").write_text(
    json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
(ROOT / "source-diagnostics" / "ASSET-CROP-PREVIEWS.txt").write_text(
    "\n".join(previews) + "\n", encoding="utf-8"
)
print(json.dumps({"status": status, "assets": len(records), "errors": errors}, ensure_ascii=False, indent=2))
raise SystemExit(0 if status == "PASS" else 1)
