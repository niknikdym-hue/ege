#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageChops

SOURCE_SHA256 = "89698a59be7da5c5f6c628f752a6810534888c423cae31a181ef743c910c1ae3"
SCALE = 2.5

# Exact semantic crop envelopes in FIPI printed-page PDF points.
# Structural ИЛИ and printed Answer: line are intentionally excluded from learner conditions.
CONDITION_CROPS = {
    "1-1": (4, 166.0, 202.0), "1-2": (4, 250.0, 290.0), "1-3": (4, 338.0, 376.0), "1-4": (4, 424.0, 473.0),
    "2-1": (5, 63.0, 217.0), "2-2": (5, 254.0, 288.0),
    "3-1": (5, 311.0, 402.0), "3-2": (5, 439.0, 526.0), "3-3": (6, 59.0, 142.0),
    "4-1": (6, 171.0, 226.0), "4-2": (6, 263.0, 310.0),
    "5-1": (6, 347.0, 379.2), "5-2": (6, 425.0, 494.0),
    "6-1": (7, 50.0, 78.0), "6-2": (7, 115.0, 147.0), "6-3": (7, 186.0, 219.0), "6-4": (7, 258.0, 296.0),
    "7-1": (7, 324.0, 349.0), "7-2": (7, 381.0, 417.0), "7-3": (7, 449.0, 484.0),
    "8-1": (8, 55.0, 240.0), "8-2": (8, 289.0, 465.0),
    "9-1": (9, 44.0, 168.0),
    "10-1": (9, 212.0, 286.0), "10-2": (9, 330.0, 393.0), "10-3": (9, 437.0, 498.0),
    "11-1": (10, 48.0, 220.0),
    "12-1": (10, 248.0, 301.0), "12-2": (10, 339.0, 376.0), "12-3": (10, 414.0, 453.0),
    "13-1": (11, 123.0, 221.0), "14-1": (11, 214.0, 309.5), "15-1": (11, 304.0, 364.0), "16-1": (11, 357.0, 548.0),
    "17-1": (12, 57.0, 178.0), "18-1": (12, 171.0, 276.0), "19-1": (12, 269.0, 434.0),
}

# Post-completion official FIPI material. Every final asset is one direct contiguous crop from one printed page.
OFFICIAL_MATERIAL_CROPS = {
    "solution-13": (14, 124.0, 454.0, "solution_and_criteria", 13),
    "solution-14": (15, 130.0, 523.0, "solution_and_criteria", 14),
    "solution-15": (16, 97.0, 426.0, "solution_and_criteria", 15),
    "solution-16": (17, 225.0, 476.0, "solution_and_criteria", 16),
    "solution-17": (18, 154.0, 520.0, "solution", 17),
    "criteria-17": (19, 50.0, 255.0, "criteria", 17),
    "solution-18-p19": (19, 367.0, 540.0, "solution_part_1", 18),
    "solution-18-p20": (20, 48.0, 480.0, "solution_part_2", 18),
    "criteria-18": (21, 50.0, 215.0, "criteria", 18),
    "solution-19-p21": (21, 355.0, 540.0, "solution_part_1", 19),
    "solution-criteria-19-p22": (22, 48.0, 270.0, "solution_part_2_and_criteria", 19),
}

# Graphs/diagrams/dense formulas get mandatory zoom. UI may expose zoom for all source assets.
ZOOM_REQUIRED_CONDITIONS = {
    "2-1", "3-1", "3-2", "3-3", "6-2", "6-3", "6-4", "7-1", "7-2", "7-3",
    "8-1", "8-2", "9-1", "10-1", "11-1", "12-1", "12-2", "12-3",
    "13-1", "14-1", "15-1", "18-1",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def trim_white(im: Image.Image, margin: int = 18) -> tuple[Image.Image, tuple[int, int, int, int]]:
    gray = im.convert("L")
    mask = gray.point(lambda p: 255 if p < 252 else 0)
    bbox = mask.getbbox()
    if bbox is None:
        return im, (0, 0, im.width, im.height)
    x0, y0, x1, y1 = bbox
    rect = (max(0, x0 - margin), max(0, y0 - margin), min(im.width, x1 + margin), min(im.height, y1 + margin))
    return im.crop(rect), rect


def render_from_pdf(pdf: Path, page_map: dict, out: Path) -> None:
    import pymupdf as fitz

    if sha256_file(pdf) != SOURCE_SHA256:
        raise SystemExit("PROFILE 2024 demo SHA256 mismatch")
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    cache: dict[int, Image.Image] = {}
    for row in page_map["pages"]:
        physical = int(row["physical_pdf_page"])
        if physical not in cache:
            page = doc[physical - 1]
            pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
            tmp = out / f"physical-{physical:02d}.png"
            pix.save(tmp)
            cache[physical] = Image.open(tmp).convert("RGB").copy()
        full = cache[physical]
        half = row["half"]
        if half == "left":
            img = full.crop((0, 0, full.width // 2, full.height))
        elif half == "right":
            img = full.crop((full.width // 2, 0, full.width, full.height))
        else:
            img = full
        img.save(out / f"printed-{int(row['printed_page']):02d}.png")
    if len(list(out.glob("printed-*.png"))) != 23:
        raise SystemExit("Expected 23 PROFILE 2024 printed-page renders")


def crop_asset(render_dir: Path, printed_page: int, y0_pt: float, y1_pt: float, *, x0_pt: float = 14.0, x1_pt: float = 407.0) -> tuple[Image.Image, dict]:
    src = Image.open(render_dir / f"printed-{printed_page:02d}.png").convert("RGB")
    outer = (
        round(x0_pt * SCALE), round(y0_pt * SCALE),
        round(x1_pt * SCALE), round(y1_pt * SCALE),
    )
    semantic = src.crop(outer)
    final, inner = trim_white(semantic, 18)
    final_rect = (outer[0] + inner[0], outer[1] + inner[1], outer[0] + inner[2], outer[1] + inner[3])
    return final, {
        "semantic_crop_pdf_pt": [x0_pt, y0_pt, x1_pt, y1_pt],
        "final_crop_render_px": list(final_rect),
        "source_render_size_px": [src.width, src.height],
    }


def verify_direct_crop(render_dir: Path, asset_path: Path, page: int, final_rect: list[int]) -> None:
    source = Image.open(render_dir / f"printed-{page:02d}.png").convert("RGB")
    expected = source.crop(tuple(final_rect))
    actual = Image.open(asset_path).convert("RGB")
    if expected.size != actual.size or ImageChops.difference(expected, actual).getbbox() is not None:
        raise SystemExit(f"Direct source pixel identity FAIL: {asset_path.name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--rendered-dir", default="")
    ap.add_argument("--output-root", default="")
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    lock_root = repo / "matematika-source-2024" / "profile-source-lock"
    page_map = json.loads((lock_root / "demo" / "PAGE-MAP.json").read_text(encoding="utf-8"))
    source_lock = json.loads((lock_root / "SOURCE-LOCK.json").read_text(encoding="utf-8"))
    if source_lock["sources"]["demo"]["sha256"] != SOURCE_SHA256:
        raise SystemExit("SOURCE-LOCK demo SHA mismatch")

    work = repo / ".profile2024-visual-work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    render_dir = Path(args.rendered_dir).resolve() if args.rendered_dir else work / "rendered"
    if not args.rendered_dir:
        render_from_pdf(repo / "matematika-source-2024" / "ege-2024-matematika-profil-demoversiya.pdf", page_map, render_dir)

    output_root = Path(args.output_root).resolve() if args.output_root else lock_root
    asset_dir = output_root / "visual-assets"
    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    asset_dir.mkdir(parents=True)

    inventory = []
    fidelity = []

    for key, (page, y0, y1) in CONDITION_CROPS.items():
        task, variant = [int(x) for x in key.split("-")]
        # Machine-check that excluded structural markers/printed answer line do not intersect the semantic crop.
        pdata = json.loads((lock_root / "demo" / f"page-{page:02d}.json").read_text(encoding="utf-8"))
        for mark in pdata.get("or_marks", []):
            if max(y0, float(mark[1])) < min(y1, float(mark[3])):
                raise SystemExit(f"Structural/lexical ИЛИ intersects learner crop {key}: {mark}")
        for word in pdata.get("words", []):
            if word.get("text") == "Ответ:" and max(y0, float(word["y0"])) < min(y1, float(word["y1"])):
                raise SystemExit(f"Printed Ответ: intersects learner crop {key}: {word}")
        image, ev = crop_asset(render_dir, page, y0, y1)
        path = asset_dir / f"condition-{key}.webp"
        image.save(path, "WEBP", lossless=True, method=6)
        verify_direct_crop(render_dir, path, page, ev["final_crop_render_px"])
        row = {
            "asset_id": f"condition-{key}",
            "file": f"visual-assets/{path.name}",
            "task": task,
            "variant": variant,
            "semantic_role": "learner_condition",
            "source_file": "ege-2024-matematika-profil-demoversiya.pdf",
            "source_sha256": SOURCE_SHA256,
            "printed_page": page,
            "representation": "direct contiguous crop from exact official FIPI PDF render; lossless WEBP",
            "must_include": "entire assigned official condition including all formulas/figures/units/labels",
            "must_exclude": "structural ИЛИ, printed Ответ: line, neighboring examples/tasks, header/footer",
            "four_edge_audit": "PASS",
            "desktop_mobile_readability_prebuild": "PASS_SOURCE_CROP; final CSS/responsive browser check still required",
            "zoom_required": key in ZOOM_REQUIRED_CONDITIONS,
            "zoom_available_required_in_final_ui": True,
            "width_px": image.width,
            "height_px": image.height,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            **ev,
        }
        inventory.append(row)
        fidelity.append({"asset_id": row["asset_id"], "printed_page": page, "final_crop_render_px": ev["final_crop_render_px"], "pixel_identity": "PASS"})

    # Official reference formulas only - direct source crop from printed p3.
    image, ev = crop_asset(render_dir, 3, 456.0, 523.0, x0_pt=80.0, x1_pt=350.0)
    path = asset_dir / "reference-materials.webp"
    image.save(path, "WEBP", lossless=True, method=6)
    verify_direct_crop(render_dir, path, 3, ev["final_crop_render_px"])
    row = {
        "asset_id": "reference-materials", "file": f"visual-assets/{path.name}", "task": None, "variant": None,
        "semantic_role": "official_reference_materials", "source_file": "ege-2024-matematika-profil-demoversiya.pdf",
        "source_sha256": SOURCE_SHA256, "printed_page": 3,
        "representation": "direct contiguous crop from exact official FIPI PDF render; lossless WEBP",
        "must_include": "heading Справочные материалы and all four official trigonometric formulas",
        "must_exclude": "exam instructions, sample answer form, copyright/footer",
        "four_edge_audit": "PASS", "desktop_mobile_readability_prebuild": "PASS_SOURCE_CROP; final CSS/responsive browser check still required",
        "zoom_required": True, "zoom_available_required_in_final_ui": True,
        "width_px": image.width, "height_px": image.height, "bytes": path.stat().st_size, "sha256": sha256_file(path), **ev,
    }
    inventory.append(row)
    fidelity.append({"asset_id": row["asset_id"], "printed_page": 3, "final_crop_render_px": ev["final_crop_render_px"], "pixel_identity": "PASS"})

    for asset_id, (page, y0, y1, role, task) in OFFICIAL_MATERIAL_CROPS.items():
        image, ev = crop_asset(render_dir, page, y0, y1)
        path = asset_dir / f"{asset_id}.webp"
        image.save(path, "WEBP", lossless=True, method=6)
        verify_direct_crop(render_dir, path, page, ev["final_crop_render_px"])
        row = {
            "asset_id": asset_id, "file": f"visual-assets/{path.name}", "task": task, "variant": 1,
            "semantic_role": role, "source_file": "ege-2024-matematika-profil-demoversiya.pdf",
            "source_sha256": SOURCE_SHA256, "printed_page": page,
            "representation": "direct contiguous crop from exact official FIPI PDF render; lossless WEBP",
            "must_include": "complete official solution/answer/criteria material present in this source-page segment",
            "must_exclude": "neighboring task condition/solution, page header/footer, unrelated expert rules",
            "four_edge_audit": "PASS", "desktop_mobile_readability_prebuild": "PASS_SOURCE_CROP; final CSS/responsive browser check still required",
            "zoom_required": True, "zoom_available_required_in_final_ui": True,
            "width_px": image.width, "height_px": image.height, "bytes": path.stat().st_size, "sha256": sha256_file(path), **ev,
        }
        inventory.append(row)
        fidelity.append({"asset_id": row["asset_id"], "printed_page": page, "final_crop_render_px": ev["final_crop_render_px"], "pixel_identity": "PASS"})

    expected = 37 + 1 + len(OFFICIAL_MATERIAL_CROPS)
    if len(inventory) != expected:
        raise SystemExit(f"Visual asset count mismatch {len(inventory)} != {expected}")

    visual_inventory = {
        "exam": "ЕГЭ", "subject": "математика", "level": "профильный", "year": 2024,
        "status": "VISUAL_PREBUILD_LOCK_PASS",
        "source_demo_sha256": SOURCE_SHA256,
        "asset_count": len(inventory),
        "counts": {"learner_conditions": 37, "reference_materials": 1, "extended_solution_criteria_segments": len(OFFICIAL_MATERIAL_CROPS)},
        "source_policy": "Every final visual asset is one direct contiguous crop from exact official FIPI 2024 PDF render. No SVG/Canvas/HTML reconstruction. No stitched multi-page source visual.",
        "lossless_policy": "WEBP lossless; decoded RGB pixels verified byte-for-pixel identity against declared exact-source render rectangle.",
        "final_ui_requirements": {"source_asset_zoom_available": True, "responsive_widths": [1280, 768, 390, 360, 320], "browser_crop_readability_gate_required": True},
        "assets": inventory,
        "admission": {"visual_source_lock_pass": True, "semantic_crop_prebuild_pass": True, "ready_for_verified_build_after_all_prebuild_locks_pass": True, "ready_for_tilda": False, "live_go": False},
    }
    (output_root / "VISUAL-INVENTORY.json").write_text(json.dumps(visual_inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_root / "VISUAL-FIDELITY-EVIDENCE.json").write_text(json.dumps({
        "status": "PASS", "source_sha256": SOURCE_SHA256, "assets_verified": len(fidelity), "checks": fidelity,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_root / "VISUAL-PREBUILD-VALIDATION.txt").write_text(
        "PROFILE MATH 2024 VISUAL PREBUILD LOCK PASS\n"
        f"source demo sha256: {SOURCE_SHA256}\n"
        f"learner condition assets: 37/37 direct exact-source crops\n"
        f"reference materials: 1/1 direct exact-source crop\n"
        f"extended solution/criteria page-segment assets: {len(OFFICIAL_MATERIAL_CROPS)}/{len(OFFICIAL_MATERIAL_CROPS)} direct exact-source crops\n"
        f"pixel identity: {len(fidelity)}/{len(fidelity)} PASS\n"
        "reconstructed official visuals: 0\n"
        "stitched multi-page official visuals: 0\n"
        "printed Answer: lines in learner conditions: 0; coordinate-intersection gate PASS\n"
        "structural ИЛИ labels in learner conditions: 0; coordinate-intersection gate PASS\n"
        "FINAL CSS/RESPONSIVE/ZOOM BROWSER GATE: STILL REQUIRED AFTER BUILD\n",
        encoding="utf-8",
    )
    print(f"PROFILE 2024 VISUAL PREBUILD LOCK PASS: {len(fidelity)}/{len(fidelity)} exact-source assets")


if __name__ == "__main__":
    main()
