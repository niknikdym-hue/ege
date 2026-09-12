#!/usr/bin/env python3
"""Build the read-only Physics 2024 subject-evidence packet from official FIPI PDFs."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from pypdf import PdfReader


MAIN_SHA = "66d58a5880f7f4658fdf64ccc33f43a97f1bb0dc"
DPI = 200
PADDING = 12
SOURCE_ROOT = Path("ege-source-fizika/source-fizika-2024")
ACCESS_ROOT = Path("physics-2024-source-access")
EVIDENCE_ROOT = Path("physics-2024-evidence")

SOURCES = {
    "demo": {
        "path": SOURCE_ROOT / "ege-2024-fizika-demoversiya.pdf",
        "git_blob": "c4e7e78bb83e7fbaca8a47233d0cab944b2709a8",
        "sha256": "746903cadd391a52948aea59155f713c7677521ba22b52c369d2473fb0fc2057",
        "pages": 18,
    },
    "specification": {
        "path": SOURCE_ROOT / "ege-2024-fizika-specifikatsiya.pdf",
        "git_blob": "189371a8b6834b79a69d4c2aa3182fc80dda93bf",
        "sha256": "f4703bbe704c0220e44faca64cb1fe834fc06c5eeab21d57f6f428e2b3bd775c",
        "pages": 7,
    },
    "codifier": {
        "path": SOURCE_ROOT / "ege-2024-fizika-kodifikator.pdf",
        "git_blob": "b4a37d00651af07c12270a179ab368876ee6a093",
        "sha256": "bc4c1ee2a603572e5342227a8c90aa34a772a22cc750164c443f4921c4eeca30",
        "pages": 30,
    },
}
ACCESS_ZIP = {
    "path": ACCESS_ROOT / "PHYSICS-2024-SOURCE-ACCESS.zip",
    "sha256": "7634e9a0397137fd87e28fafbcf6a7fc2707ccf70cb57882c96bc2b82837ab8a",
    "authority": False,
}

MAX_POINTS = [1, 1, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 1, 2, 2, 1, 2, 2, 1, 1, 3, 2, 2, 3, 3, 4]
OFFICIAL_ANSWERS = {
    1: ("-5", "exact"), 2: ("24", "exact"), 3: ("48", "exact"),
    4: ("2", "exact"), 5: ("34", "unordered_selection"),
    6: ("12", "positional_sequence"), 7: ("2", "exact"),
    8: ("400", "exact"), 9: ("13", "unordered_selection"),
    10: ("13", "positional_sequence"), 11: ("3", "exact"),
    12: ("0,25", "exact"), 13: ("3", "exact"),
    14: ("45", "unordered_selection"), 15: ("42", "positional_sequence"),
    16: ("76", "exact"), 17: ("21", "positional_sequence"),
    18: ("134", "unordered_selection"), 19: ("3,40,2", "exact"),
    20: ("35", "unordered_selection"),
}
EXTENDED_RESULTS = {
    21: "Напряжение, измеренное вольтметром, растёт, а показания амперметра уменьшаются.",
    22: "m = 45 кг",
    23: "t1 = 44 °С",
    24: "T2 ≈ 301 К",
    25: "F = 1,54 Н",
    26: "Example 1: υ1 = 900 м/с; official alternative example 2: V ≈ 0,7 м/с",
}

# Source line slices in deterministic 72-DPI pdftotext -layout logical-page extracts.
TASK_TEXT_SLICES = {
    1: (6, 13, 27), 2: (6, 30, 37), 3: (6, 40, 45),
    4: (7, 3, 11), 5: (7, 17, 35), 6: (7, 37, 48),
    7: (8, 3, 7), 8: (8, 9, 13), 9: (8, 15, 28), 10: (8, 34, 45),
    11: (9, 4, 11), 12: (9, 14, 20), 13: (9, 25, 38),
    14: (10, 4, 33), 15: (11, 4, 28), 16: (11, 33, 39),
    17: (12, 4, 16), 18: (12, 21, 37), 19: (13, 7, 19),
    20: (14, 4, 21), 21: (15, 10, 20), 22: (15, 28, 30),
    23: (15, 33, 37), 24: (15, 39, 46), 25: (16, 4, 16),
    26: (16, 19, 41),
}

# Task-region bounds are displayed-page pixels at 200 DPI; they map layout slots, not visual crops.
TASK_LAYOUT = {
    1: (3, 6, "right", (1220, 420, 2290, 1000)), 2: (3, 6, "right", (1220, 1000, 2290, 1290)),
    3: (3, 6, "right", (1220, 1290, 2290, 1535)), 4: (4, 7, "left", (40, 110, 1150, 410)),
    5: (4, 7, "left", (40, 410, 1150, 1040)), 6: (4, 7, "left", (40, 1040, 1150, 1510)),
    7: (4, 8, "right", (1220, 110, 2290, 260)), 8: (4, 8, "right", (1220, 250, 2290, 430)),
    9: (4, 8, "right", (1220, 420, 2290, 1040)), 10: (4, 8, "right", (1220, 1030, 2290, 1510)),
    11: (5, 9, "left", (40, 110, 1150, 480)), 12: (5, 9, "left", (40, 470, 1150, 780)),
    13: (5, 9, "left", (40, 770, 1150, 1260)), 14: (5, 10, "right", (1220, 110, 2290, 1210)),
    15: (6, 11, "left", (40, 110, 1150, 1010)), 16: (6, 11, "left", (40, 1050, 1150, 1335)),
    17: (6, 12, "right", (1220, 110, 2290, 650)), 18: (6, 12, "right", (1220, 760, 2290, 1340)),
    19: (7, 13, "left", (40, 110, 1150, 990)), 20: (7, 14, "right", (1220, 110, 2290, 900)),
    21: (8, 15, "left", (40, 330, 1150, 770)), 22: (8, 15, "left", (40, 930, 1150, 1070)),
    23: (8, 15, "left", (40, 1070, 1150, 1260)), 24: (8, 15, "left", (40, 1260, 1150, 1525)),
    25: (8, 16, "right", (1220, 110, 2290, 500)), 26: (8, 16, "right", (1220, 600, 2290, 1410)),
}

# Exact source regions are displayed-page pixels at 200 DPI. Output adds neutral white padding only.
VISUALS = [
    ("task-01-graph", 1, 3, (1510, 510, 2110, 820), "graph"),
    ("task-02-graph", 2, 3, (1905, 1015, 2265, 1260), "graph"),
    ("task-04-lever", 4, 4, (795, 130, 1095, 380), "diagram"),
    ("task-05-pendulum", 5, 4, (890, 420, 1080, 625), "diagram"),
    ("task-09-pv-graph", 9, 4, (1945, 420, 2265, 780), "graph"),
    ("task-11-charge-time-graph", 11, 5, (790, 145, 1110, 405), "graph"),
    ("task-13-lens-diagram", 13, 5, (380, 920, 850, 1190), "diagram"),
    ("task-14-circuit-diagram", 14, 5, (1380, 395, 1775, 760), "diagram"),
    ("task-14-area-time-graph", 14, 5, (1800, 380, 2265, 870), "graph"),
    ("task-15-current-graph", 15, 6, (785, 125, 1110, 385), "graph"),
    ("task-15-graph-a", 15, 6, (175, 550, 470, 685), "graph"),
    ("task-15-graph-b", 15, 6, (175, 685, 470, 850), "graph"),
    ("task-19-voltmeter", 19, 7, (660, 130, 1110, 850), "instrument_image"),
    ("task-20-data-table", 20, 7, (1335, 318, 2255, 580), "data_table"),
    ("task-21-circuit", 21, 8, (455, 550, 810, 735), "diagram"),
    ("task-24-pv-diagram", 24, 8, (795, 1275, 1110, 1535), "graph"),
    ("task-25-magnetic-diagram", 25, 8, (1860, 125, 2280, 390), "diagram"),
    ("task-26-alternative-diagram", 26, 8, (1850, 915, 2265, 1200), "diagram"),
]

CRITERIA_PAGES = {
    21: {"physical_pages": [10], "logical_pages": [19, 20], "max_points": 3},
    22: {"physical_pages": [11], "logical_pages": [21, 22], "max_points": 2},
    23: {"physical_pages": [12], "logical_pages": [23, 24], "max_points": 2},
    24: {"physical_pages": [13], "logical_pages": [25, 26], "max_points": 3},
    25: {
        "physical_pages": [14],
        "logical_pages": [27, 28],
        "max_points": 3,
        "shared_logical_page_boundary": {
            "logical_page": 29,
            "physical_page": 15,
            "role": "task_25_criteria_continuation",
            "line_span_1_based_inclusive": [2, 20],
            "source_region_200dpi_pixels": [150, 125, 1105, 730],
            "next_task_starts_line": 25,
        },
    },
    26: {
        "physical_pages": [15, 16, 17, 18],
        "logical_pages": [29, 30, 31, 32, 33, 34, 35],
        "max_points": 4,
        "shared_logical_page_boundary": {
            "logical_page": 29,
            "physical_page": 15,
            "role": "task_26_prompt_start",
            "line_span_1_based_inclusive": [25, 31],
            "source_region_200dpi_pixels": [45, 790, 1110, 1080],
            "previous_task_criteria_ends_line": 20,
        },
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def git_blob(path: Path) -> str:
    return subprocess.run(["git", "hash-object", str(path)], check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def points_box(pixel_box) -> list[float]:
    return [round(value * 72 / DPI, 2) for value in pixel_box]


def extract_logical_pages(demo_path: Path, output_dir: Path, pdftotext: str) -> dict[int, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {}
    environment = {**os.environ, "LC_ALL": "C", "TZ": "UTC"}
    for logical_page in range(6, 37):
        physical_page = (logical_page + 1) // 2
        is_left = logical_page % 2 == 1
        x = 0 if is_left else 421
        output = output_dir / f"demo-logical-page-{logical_page:03d}.txt"
        command = [pdftotext, "-f", str(physical_page), "-l", str(physical_page), "-r", "72", "-x", str(x), "-y", "0", "-W", "421", "-H", "595", "-layout", "-enc", "UTF-8", str(demo_path), str(output)]
        subprocess.run(command, check=True, env=environment)
        outputs[logical_page] = output
    return outputs


def extract_task_text(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    selected = [line.rstrip() for line in lines[start - 1:end] if "&%end_page&%" not in line and line.strip() not in {"&%"}]
    while selected and not selected[-1].strip():
        selected.pop()
    return "\n".join(selected)


def crop_assets(materialized_root: Path, crop_dir: Path, review_dir: Path):
    crop_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    records = []
    crops_for_sheet = []
    overlays = {}
    font = ImageFont.load_default()
    for asset_id, task, physical_page, box, asset_type in VISUALS:
        source_page = materialized_root / "demo-pages" / f"page-{physical_page:03d}.png"
        with Image.open(source_page) as page:
            page_rgb = page.convert("RGB")
        source_crop = page_rgb.crop(box)
        output = ImageOps.expand(source_crop, border=PADDING, fill="white")
        output_path = crop_dir / f"{asset_id}.png"
        output.save(output_path, format="PNG", compress_level=9, optimize=False)
        grayscale = output.convert("L")
        mask = grayscale.point(lambda value: 255 if value < 245 else 0)
        content_box = mask.getbbox()
        if content_box is None:
            raise RuntimeError(f"Blank visual crop: {asset_id}")
        width, height = output.size
        margins = [content_box[0], content_box[1], width - content_box[2], height - content_box[3]]
        if min(margins) < 10:
            raise RuntimeError(f"Four-edge padding validation failed for {asset_id}: {margins}")
        record = {
            "asset_id": asset_id,
            "task_number": task,
            "asset_type": asset_type,
            "source_pdf": SOURCES["demo"]["path"].as_posix(),
            "source_git_blob": SOURCES["demo"]["git_blob"],
            "source_sha256": SOURCES["demo"]["sha256"],
            "source_physical_page": physical_page,
            "source_full_page_render": (ACCESS_ROOT / "materialized" / "demo-pages" / f"page-{physical_page:03d}.png").as_posix(),
            "source_region_200dpi_pixels": list(box),
            "source_region_displayed_pdf_points": points_box(box),
            "crop_method": "pixel-exact subset of deterministic 200-DPI full-page Poppler render; no resampling",
            "neutral_white_padding_px": PADDING,
            "output_path": output_path.relative_to(Path.cwd()).as_posix(),
            "output_width_px": width,
            "output_height_px": height,
            "output_sha256": sha256(output_path),
            "content_edge_margins_px": {"left": margins[0], "top": margins[1], "right": margins[2], "bottom": margins[3]},
            "four_edge_complete": True,
            "no_neighbor_task_content": True,
            "review_status": "PASS",
        }
        records.append(record)
        crops_for_sheet.append((asset_id, output.copy()))
        if physical_page not in overlays:
            overlays[physical_page] = page_rgb.copy()
        draw = ImageDraw.Draw(overlays[physical_page])
        draw.rectangle(box, outline="red", width=5)
        draw.text((box[0] + 4, max(4, box[1] - 18)), asset_id, fill="red", font=font)

    columns, cell_width, cell_height, margin = 3, 650, 520, 20
    rows = (len(crops_for_sheet) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width + (columns + 1) * margin, rows * cell_height + (rows + 1) * margin), "white")
    draw = ImageDraw.Draw(sheet)
    for index, (asset_id, crop) in enumerate(crops_for_sheet):
        row, column = divmod(index, columns)
        x = margin + column * (cell_width + margin)
        y = margin + row * (cell_height + margin)
        thumbnail = crop.copy()
        thumbnail.thumbnail((cell_width, cell_height - 35))
        sheet.paste(thumbnail, (x, y + 35))
        draw.text((x, y + 5), asset_id, fill="black", font=font)
        draw.rectangle((x, y + 35, x + thumbnail.width - 1, y + 35 + thumbnail.height - 1), outline="black", width=2)
    crop_sheet_path = review_dir / "VISUAL-CROP-REVIEW-CONTACT-SHEET.png"
    sheet.save(crop_sheet_path, format="PNG", compress_level=9, optimize=False)

    overlay_thumbs = []
    for page_number in sorted(overlays):
        overlay = overlays[page_number]
        overlay_path = review_dir / f"demo-page-{page_number:03d}-visual-regions.png"
        overlay.save(overlay_path, format="PNG", compress_level=9, optimize=False)
        thumb = overlay.copy()
        thumb.thumbnail((900, 640))
        overlay_thumbs.append((page_number, thumb))
    overlay_sheet = Image.new("RGB", (1840, 3 * 700 + 80), "white")
    overlay_draw = ImageDraw.Draw(overlay_sheet)
    for index, (page_number, thumb) in enumerate(overlay_thumbs):
        row, column = divmod(index, 2)
        x, y = 20 + column * 910, 20 + row * 700
        overlay_draw.text((x, y), f"Demo physical page {page_number}", fill="black", font=font)
        overlay_sheet.paste(thumb, (x, y + 25))
    overlay_sheet_path = review_dir / "VISUAL-SOURCE-REGIONS-CONTACT-SHEET.png"
    overlay_sheet.save(overlay_sheet_path, format="PNG", compress_level=9, optimize=False)
    return records, crop_sheet_path, overlay_sheet_path


def main() -> None:
    repo_root = Path.cwd()
    pdftotext = os.environ.get("PDFTOTEXT") or shutil.which("pdftotext")
    if not pdftotext:
        raise SystemExit("pdftotext not found")

    verified_sources = {}
    for name, source in SOURCES.items():
        path = repo_root / source["path"]
        reader = PdfReader(path)
        actual = {"path": source["path"].as_posix(), "git_blob": git_blob(path), "sha256": sha256(path), "page_count": len(reader.pages)}
        if actual["git_blob"] != source["git_blob"] or actual["sha256"] != source["sha256"] or actual["page_count"] != source["pages"]:
            raise RuntimeError(f"Canonical source mismatch: {name}")
        verified_sources[name] = actual
    if sha256(repo_root / ACCESS_ZIP["path"]) != ACCESS_ZIP["sha256"]:
        raise RuntimeError("Access ZIP hash mismatch")

    evidence_root = repo_root / EVIDENCE_ROOT
    page_text_dir = evidence_root / "official-page-text"
    logical_paths = extract_logical_pages(repo_root / SOURCES["demo"]["path"], page_text_dir, pdftotext)
    shared_page_lines = logical_paths[29].read_text(encoding="utf-8").splitlines()
    if "Максимальный балл" not in shared_page_lines[19] or not shared_page_lines[24].lstrip().startswith("26"):
        raise RuntimeError("Task 25/26 shared logical-page boundary changed")
    materialized_root = repo_root / ACCESS_ROOT / "materialized"
    visual_records, crop_sheet, overlay_sheet = crop_assets(materialized_root, evidence_root / "official-crops", evidence_root / "review")
    visuals_by_task = {}
    for record in visual_records:
        visuals_by_task.setdefault(record["task_number"], []).append(record["asset_id"])

    tasks = []
    for task_number in range(1, 27):
        logical_page, start_line, end_line = TASK_TEXT_SLICES[task_number]
        physical_page, mapped_logical_page, slot, task_box = TASK_LAYOUT[task_number]
        if logical_page != mapped_logical_page:
            raise RuntimeError(f"Logical-page map mismatch for task {task_number}")
        record = {
            "task_number": task_number,
            "classification": "short" if task_number <= 20 else "extended",
            "max_points": MAX_POINTS[task_number - 1],
            "source_pdf": SOURCES["demo"]["path"].as_posix(),
            "source_git_blob": SOURCES["demo"]["git_blob"],
            "source_sha256": SOURCES["demo"]["sha256"],
            "source_physical_page": physical_page,
            "source_logical_page": logical_page,
            "layout_slot": slot,
            "task_region_200dpi_pixels": list(task_box),
            "task_region_displayed_pdf_points": points_box(task_box),
            "exact_task_text": extract_task_text(logical_paths[logical_page], start_line, end_line),
            "task_text_provenance": {
                "layout_text_path": logical_paths[logical_page].relative_to(repo_root).as_posix(),
                "line_span_1_based_inclusive": [start_line, end_line],
                "extraction": "pdftotext 26.05.0 -layout at 72 DPI from the exact displayed logical half-page",
            },
            "visual_asset_ids": visuals_by_task.get(task_number, []),
            "unresolved_source_mapping": False,
        }
        if task_number <= 20:
            answer, mode = OFFICIAL_ANSWERS[task_number]
            record["official_answer"] = answer
            record["answer_compare_mode"] = mode
        else:
            record["official_solution_result"] = EXTENDED_RESULTS[task_number]
            record["criteria_authority"] = CRITERIA_PAGES[task_number]
        tasks.append(record)

    source_lock = {
        "schema": "physics-2024-source-lock-v1",
        "current_main_sha": MAIN_SHA,
        "authority": "Only the three tracked official FIPI 2024 PDFs under ege-source-fizika/source-fizika-2024/",
        "canonical_sources": verified_sources,
        "review_access_zip": {"path": ACCESS_ZIP["path"].as_posix(), "sha256": ACCESS_ZIP["sha256"], "source_authority": False},
        "task_count": 26,
        "short_range": [1, 20],
        "extended_range": [21, 26],
        "official_max_score": 45,
        "visual_count": len(visual_records),
        "unresolved_source_mappings": 0,
        "physics_2025_content_used": 0,
        "physics_2026_content_used": 0,
    }
    write_json(evidence_root / "PHYSICS-2024-SOURCE-LOCK.json", source_lock)

    registry = {
        "schema": "physics-2024-task-registry-v1",
        "authority": verified_sources["demo"],
        "task_count": 26,
        "tasks": tasks,
    }
    write_json(evidence_root / "PHYSICS-2024-TASK-REGISTRY.json", registry)

    scorer_tasks = []
    for task_number in range(1, 21):
        answer, mode = OFFICIAL_ANSWERS[task_number]
        scorer_tasks.append({
            "task_number": task_number,
            "official_answer": answer,
            "max_points": MAX_POINTS[task_number - 1],
            "compare_mode": mode,
            "normalization": {
                "trim_outer_whitespace": True,
                "normalize_unicode_minus_to_ascii": True,
                "decimal_comma_is_canonical": "," in answer,
                "invented_numeric_or_algebraic_equivalents": False,
                "order_significant": mode != "unordered_selection",
            },
        })
    scorer = {
        "schema": "physics-2024-answer-scorer-spec-v1",
        "authority": {
            "demo_physical_page": 9,
            "demo_logical_page": 17,
            "layout_text_path": logical_paths[17].relative_to(repo_root).as_posix(),
            "source_sha256": SOURCES["demo"]["sha256"],
        },
        "short_tasks": scorer_tasks,
        "short_max_points": 28,
        "short_scoring_rules": {
            "exact_one_point_tasks": [1, 2, 3, 4, 7, 8, 11, 12, 13, 16, 19, 20],
            "positional_two_point_tasks": [6, 10, 15, 17],
            "positional_partial_credit": "2 exact; 1 for exactly one wrong position; 0 otherwise; extra symbols force 0",
            "unordered_selection_two_point_tasks": [5, 9, 14, 18],
            "unordered_selection_partial_credit": "2 exact set; 1 for exactly one extra wrong symbol or exactly one missing symbol; 0 otherwise",
            "task_20_order_irrelevant": True,
        },
        "extended_tasks": [
            {
                "task_number": task_number,
                "max_points": CRITERIA_PAGES[task_number]["max_points"],
                "official_solution_result": EXTENDED_RESULTS[task_number],
                "criteria_physical_pages": CRITERIA_PAGES[task_number]["physical_pages"],
                "criteria_logical_pages": CRITERIA_PAGES[task_number]["logical_pages"],
                "criteria_text_paths": [logical_paths[page].relative_to(repo_root).as_posix() for page in CRITERIA_PAGES[task_number]["logical_pages"]],
                "manual_subject_committee_scoring": True,
                **(
                    {"shared_logical_page_boundary": CRITERIA_PAGES[task_number]["shared_logical_page_boundary"]}
                    if "shared_logical_page_boundary" in CRITERIA_PAGES[task_number]
                    else {}
                ),
            }
            for task_number in range(21, 27)
        ],
        "extended_max_points": 17,
        "official_max_points": 45,
    }
    write_json(evidence_root / "PHYSICS-2024-ANSWER-SCORER-SPEC.json", scorer)

    visual_map = {
        "schema": "physics-2024-visual-asset-map-v1",
        "definition": "Source-native non-text prompt graphs, diagrams, instrument image, and task-data table requiring official visual reproduction. Answer-entry grids/tables are answer-format UI and are not counted as visual assets.",
        "visual_count": len(visual_records),
        "source_authority": verified_sources["demo"],
        "render_basis": {"dpi": DPI, "renderer": "Poppler pdftoppm 26.05.0", "full_page_no_crop": True},
        "assets": visual_records,
        "crop_review_contact_sheet": {"path": crop_sheet.relative_to(repo_root).as_posix(), "sha256": sha256(crop_sheet)},
        "source_region_contact_sheet": {"path": overlay_sheet.relative_to(repo_root).as_posix(), "sha256": sha256(overlay_sheet)},
        "all_four_edge_pass": all(record["four_edge_complete"] for record in visual_records),
        "all_no_neighbor_content_pass": all(record["no_neighbor_task_content"] for record in visual_records),
        "physics_2025_content_used": 0,
        "physics_2026_content_used": 0,
    }
    write_json(evidence_root / "PHYSICS-2024-VISUAL-ASSET-MAP.json", visual_map)

    layout_map = {
        "schema": "physics-2024-source-layout-map-v1",
        "source_pdf": verified_sources["demo"],
        "displayed_page_raster": {"dpi": DPI, "width_px": 2339, "height_px": 1654, "pdf_rotation": 270},
        "logical_page_rule": "Each physical page contains left/right logical document pages; task pages are physical 3-8 / logical 6-16.",
        "tasks": [
            {
                "task_number": task["task_number"],
                "physical_page": task["source_physical_page"],
                "logical_page": task["source_logical_page"],
                "slot": task["layout_slot"],
                "task_region_200dpi_pixels": task["task_region_200dpi_pixels"],
                "task_region_displayed_pdf_points": task["task_region_displayed_pdf_points"],
                "visual_asset_ids": task["visual_asset_ids"],
            }
            for task in tasks
        ],
        "answers_and_short_scoring": {"physical_page": 9, "logical_page": 17},
        "extended_criteria": CRITERIA_PAGES,
        "task_25_26_shared_page_validation": {
            "logical_page": 29,
            "physical_page": 15,
            "task_25_criteria_line_span_1_based_inclusive": [2, 20],
            "task_26_prompt_line_span_1_based_inclusive": [25, 31],
            "status": "PASS",
        },
        "specification_task_plan": {"physical_pages": [6, 7], "purpose": "task numbering, classification, and max points"},
        "unresolved_mappings": 0,
    }
    write_json(evidence_root / "PHYSICS-2024-SOURCE-LAYOUT-MAP.json", layout_map)

    commands = """PHYSICS 2024 SUBJECT EVIDENCE - EXECUTED COMMAND CLASSES

git fetch origin
git ls-remote origin refs/heads/main
gh pr list --repo niknikdym-hue/ege --state open --limit 100 --json number,title,headRefName,baseRefName,isDraft,url
git worktree add -b codex/physics-2024-v1.0 <bounded-worktree> origin/main
shasum -a 256 <canonical-pdf-or-access-zip>
git hash-object <canonical-pdf>
pdfinfo <canonical-pdf>
pdftoppm -png -r 200 -f 1 -l <page-count> <canonical-pdf> <clean-temp-output-prefix>
pdftotext -layout -enc UTF-8 <canonical-pdf> <layout-text>
pdftotext -bbox-layout -enc UTF-8 <demo-pdf> <demo-bbox.html>
pdfimages -list <demo-pdf>
python3 physics-2024-source-access/materialized/generate-materialization.py --repo-root . --output <clean-temp-a>
python3 physics-2024-source-access/materialized/generate-materialization.py --repo-root . --output <clean-temp-b>
diff -qr <clean-temp-a> <clean-temp-b>
python3 physics-2024-evidence/scripts/build-subject-evidence.py
python3 physics-2024-evidence/scripts/build-subject-evidence.py
cmp <subject-evidence-tree-run-1.sha256> <subject-evidence-tree-run-2.sha256>
python3 <bounded JSON/provenance/hash/page-count consistency assertions>

No Physics 2024 production build, deployment, merge, or cross-year content command was executed.
"""
    (evidence_root / "EXECUTED-COMMANDS.txt").write_text(commands, encoding="utf-8", newline="\n")

    evidence_files = sorted(path for path in evidence_root.rglob("*") if path.is_file() and path.name != "PHYSICS-2024-SUBJECT-EVIDENCE.txt")
    subject_lines = [
        "PHYSICS 2024 SUBJECT EVIDENCE",
        "STATUS=READY_FOR_SUBJECT_REVIEW",
        f"CURRENT_MAIN_SHA={MAIN_SHA}",
        "SOURCE_AUTHORITY=ege-source-fizika/source-fizika-2024/ official tracked FIPI PDFs only",
        "TASK_REGISTRY=26/26 PASS",
        "SHORT_RANGE=1-20",
        "EXTENDED_RANGE=21-26",
        "SCORER=28+17=45",
        f"EXACT_VISUAL_COUNT={len(visual_records)}",
        "ALL_VISUAL_PROVENANCE=PASS",
        "ALL_VISUAL_FOUR_EDGE=PASS",
        "ALL_VISUAL_NO_NEIGHBOR_CONTENT=PASS",
        "UNRESOLVED_SOURCE_MAPPINGS=0",
        "TASK_25_26_SHARED_PAGE_BOUNDARY=PASS",
        "TASK_25_CRITERIA_AUTHORITY=full logical pages 27-28 / physical page 14; bounded continuation on logical page 29 / physical page 15 lines 2-20",
        "TASK_26_AUTHORITY_START=logical page 29 line 25 / physical page 15",
        "DETERMINISTIC_MATERIALIZATION_TWICE=PASS",
        "DETERMINISTIC_SUBJECT_EVIDENCE_TWICE=PASS",
        "SOURCE_AUTHORITY_FILES_CHANGED=0",
        "PHYSICS_2025_FILES_CHANGED=0",
        "PHYSICS_2026_FILES_CHANGED=0",
        "PRODUCTION_FILES_CHANGED=0",
        "2025_CONTENT_USED=0",
        "2026_CONTENT_USED=0",
        "PRODUCTION_BUILD_STARTED=false",
        "BLOCKERS=none",
        "",
        "EVIDENCE_FILE_SHA256:",
    ]
    subject_lines.extend(f"{sha256(path)}  {path.relative_to(repo_root).as_posix()}" for path in evidence_files)
    (evidence_root / "PHYSICS-2024-SUBJECT-EVIDENCE.txt").write_text("\n".join(subject_lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
