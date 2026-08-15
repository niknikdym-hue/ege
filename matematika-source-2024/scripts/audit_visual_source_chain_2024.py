#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import collections
import hashlib
import json
import re
from pathlib import Path

import fitz
from PIL import Image, ImageChops

EXPECTED_SOURCE_SHA256 = "7e7111654239dbf17c73786bccc9109f2f0f05d80039cfdeca114e83f67f5546"
EXPECTED_ASSETS_BY_PAGE = {
    9: ["base-02-v1-table", "base-02-v2-table"],
    10: ["base-03-v1-rivers-chart", "base-03-v2-smartphone-table"],
    11: ["base-03-v3-temperature-chart", "base-04-v1-formula", "base-04-v2-formula"],
    12: ["base-06-v1-translators-table"],
    13: ["base-06-v2-suitcases-table", "base-06-v3-suppliers-table"],
    14: ["base-07-v1-derivative-graph", "base-07-v1-values-table"],
    15: ["base-07-v2-engine-chart", "base-07-v2-match-table"],
    16: ["base-07-v3-function-graphs", "base-07-v3-characteristics"],
    18: ["base-09-v1-lake-plan", "base-09-v2-grid-plan"],
    19: ["base-10-v1-dacha-plan", "base-10-v2-clock", "base-11-v1-cylinder", "base-11-v2-cut-cube"],
    20: ["base-12-v1-triangle-median", "base-13-v1-cylinder-section", "base-13-v2-condition", "base-13-v2-pyramid", "base-13-v3-spheres"],
    21: ["base-14-v1-formula", "base-14-v2-formula"],
    22: ["base-16-v1-formula", "base-16-v2-formula", "base-16-v3-formula", "base-16-v4-formula", "base-17-v1-formula", "base-17-v2-formula", "base-17-v3-formula"],
    23: ["base-18-v1-number-line", "base-18-v1-numbers-table", "base-18-v2-inequalities-table"],
    24: ["base-19-v2-expression"],
    25: ["base-21-v2-rectangle-partition"],
}
EXPECTED_REFERENCE_PAGES = (4, 5, 6, 7)
FORBIDDEN_RECONSTRUCTION_MARKERS = (
    "<svg",
    "<canvas",
    "canvas.getcontext",
    "getcontext('2d",
    'getcontext("2d',
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise AssertionError(message)


def render_printed_pages(pdf_path: Path) -> dict[int, Image.Image]:
    doc = fitz.open(pdf_path)
    if len(doc) != 13:
        fail(f"official demo physical page count changed: {len(doc)} != 13")

    printed: dict[int, Image.Image] = {}
    for physical_index, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        if image.width % 2:
            fail(f"physical page {physical_index} has odd rendered width {image.width}")
        midpoint = image.width // 2
        left = image.crop((0, 0, midpoint, image.height))
        right = image.crop((midpoint, 0, image.width, image.height))
        printed[physical_index * 2 - 1] = left
        printed[physical_index * 2] = right
    return printed


def parse_chunked_base64(t123_files: list[Path], bucket: str) -> dict[str, list[str]]:
    parts: dict[str, list[str]] = collections.defaultdict(list)
    pattern = re.compile(rf'{re.escape(bucket)}\["([^"]+)"\].*?\.push\("([A-Za-z0-9+/=]+)"\)')
    for file in t123_files:
        for line in file.read_text(encoding="utf-8").splitlines():
            match = pattern.search(line)
            if match:
                parts[match.group(1)].append(match.group(2))
    return dict(parts)


def same_pixels(a: Image.Image, b: Image.Image) -> bool:
    if a.size != b.size:
        return False
    return ImageChops.difference(a.convert("RGB"), b.convert("RGB")).getbbox() is None


def audit(package_root: Path, repo_source_pdf: Path) -> None:
    package_root = package_root.resolve()
    repo_source_pdf = repo_source_pdf.resolve()

    if not package_root.is_dir():
        fail(f"package root not found: {package_root}")
    if not repo_source_pdf.is_file():
        fail(f"repo source PDF not found: {repo_source_pdf}")

    source_sha = sha256(repo_source_pdf)
    if source_sha != EXPECTED_SOURCE_SHA256:
        fail(f"repo source PDF SHA mismatch: {source_sha}")

    packaged_pdf = package_root / "source-evidence/official-pdf/ege-2024-matematika-baza-demoversiya.pdf"
    if sha256(packaged_pdf) != EXPECTED_SOURCE_SHA256:
        fail("packaged official PDF is not byte-identical to the locked repository source")

    printed = render_printed_pages(repo_source_pdf)

    # The package source-evidence pages must themselves be exact fresh renders
    # from the locked repository PDF, not copied from an earlier package.
    for printed_page in range(4, 27):
        evidence_path = package_root / f"source-evidence/printed-pages/page-{printed_page:02d}.webp"
        evidence = Image.open(evidence_path)
        if not same_pixels(printed[printed_page], evidence):
            fail(f"source-evidence page {printed_page} is not an exact fresh render of repository PDF")

    asset_map_path = package_root / "ege-matematika-baza-demoversiya-2024-ASSET-MAP.json"
    asset_map = json.loads(asset_map_path.read_text(encoding="utf-8"))
    assets = asset_map.get("assets", [])
    if len(assets) != 41:
        fail(f"asset count changed: {len(assets)} != 41")

    expected_ids = [asset_id for page in sorted(EXPECTED_ASSETS_BY_PAGE) for asset_id in EXPECTED_ASSETS_BY_PAGE[page]]
    actual_ids = [asset["id"] for asset in assets]
    if set(actual_ids) != set(expected_ids) or len(actual_ids) != len(set(actual_ids)):
        fail("asset ID set differs from independently locked 41-source-visual inventory")

    actual_by_page: dict[int, list[str]] = collections.defaultdict(list)
    for asset in assets:
        asset_id = asset["id"]
        printed_page = int(asset["printed_page"])
        actual_by_page[printed_page].append(asset_id)

        if asset.get("source_pdf") != "ege-2024-matematika-baza-demoversiya.pdf":
            fail(f"{asset_id}: wrong source filename")
        if asset.get("source_pdf_sha256") != EXPECTED_SOURCE_SHA256:
            fail(f"{asset_id}: wrong source SHA")
        if asset.get("source_transform") != "direct contiguous crop + lossless encoding only":
            fail(f"{asset_id}: source transform is not direct crop + lossless encoding")
        if asset.get("encoding") != "lossless webp":
            fail(f"{asset_id}: encoding is not locked lossless webp")

        crop_box = tuple(int(v) for v in asset["crop_px"])
        direct_crop = printed[printed_page].crop(crop_box)
        asset_path = package_root / asset["file"]
        asset_image = Image.open(asset_path)

        if direct_crop.size != (int(asset["width_px"]), int(asset["height_px"])):
            fail(f"{asset_id}: crop dimensions differ from manifest")
        if not same_pixels(direct_crop, asset_image):
            fail(f"{asset_id}: asset pixels are not an exact direct crop of repository PDF")
        if sha256(asset_path) != asset["sha256"]:
            fail(f"{asset_id}: asset SHA mismatch")

    normalized_actual_by_page = {page: ids for page, ids in sorted(actual_by_page.items())}
    if normalized_actual_by_page != EXPECTED_ASSETS_BY_PAGE:
        fail("visual inventory by source page differs from locked independent audit map")

    t123_files = sorted(package_root.glob("ege-matematika-baza-demoversiya-2024-T123-*.txt"))
    if len(t123_files) != 18:
        fail(f"T123 block count changed: {len(t123_files)} != 18")

    asset_parts = parse_chunked_base64(t123_files, "assetParts")
    if set(asset_parts) != set(expected_ids):
        fail("T123 embedded asset ID set differs from source visual inventory")

    asset_by_id = {asset["id"]: asset for asset in assets}
    for asset_id in expected_ids:
        embedded = base64.b64decode("".join(asset_parts[asset_id]), validate=True)
        source_asset_bytes = (package_root / asset_by_id[asset_id]["file"]).read_bytes()
        if embedded != source_asset_bytes:
            fail(f"{asset_id}: T123 embedded bytes differ from verified source-crop asset")

    ref_parts = parse_chunked_base64(t123_files, "refParts")
    if set(ref_parts) != {str(page) for page in EXPECTED_REFERENCE_PAGES}:
        fail("T123 reference-page set differs from official pages 4-7")
    for page in EXPECTED_REFERENCE_PAGES:
        ref_file = package_root / f"reference-pages/ref-{page:02d}.webp"
        ref_image = Image.open(ref_file)
        if not same_pixels(printed[page], ref_image):
            fail(f"reference page {page}: not an exact direct render of repository PDF")
        embedded = base64.b64decode("".join(ref_parts[str(page)]), validate=True)
        if embedded != ref_file.read_bytes():
            fail(f"reference page {page}: T123 embedded bytes differ from source render")

    tasks = json.loads((package_root / "content/tasks.json").read_text(encoding="utf-8"))["tasks"]
    task_asset_refs: list[str] = []
    for task in tasks:
        for variant in task["variants"]:
            task_asset_refs.extend(variant.get("asset_ids", []))
    counts = collections.Counter(task_asset_refs)
    if set(counts) != set(expected_ids) or any(count != 1 for count in counts.values()):
        fail("task variants do not reference every verified source visual exactly once")

    # Reject drawing/reconstruction technology in the delivered demo. The only
    # images allowed for source content are the verified source-crop assets and
    # four verified reference-page renders above.
    scan_files = t123_files + [package_root / "index.html", package_root / "script.js", package_root / "content/tasks.json"]
    for file in scan_files:
        text = file.read_text(encoding="utf-8", errors="ignore").lower()
        for marker in FORBIDDEN_RECONSTRUCTION_MARKERS:
            if marker in text:
                fail(f"forbidden source-visual reconstruction marker {marker!r} found in {file.name}")

    print("VISUAL SOURCE CHAIN PASS")
    print(f"  repository source PDF SHA: {EXPECTED_SOURCE_SHA256}")
    print("  fresh source-evidence pages: 23/23 exact")
    print("  official task visuals: 41/41 exact direct crops")
    print("  T123 embedded task visuals: 41/41 byte-identical")
    print("  reference pages: 4/4 exact direct renders and byte-identical in T123")
    print("  reconstructed SVG/Canvas source visuals: 0")


def main() -> None:
    parser = argparse.ArgumentParser(description="Strict source-origin audit for Eksamio BASE mathematics 2024 visuals")
    parser.add_argument("package_root", type=Path)
    parser.add_argument("repo_source_pdf", type=Path)
    args = parser.parse_args()
    audit(args.package_root, args.repo_source_pdf)


if __name__ == "__main__":
    main()
