#!/usr/bin/env python3
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "matematika-source-2026"
BASE = SRC / "canonical-printed-pages" / "base-demo"
SPEC = SRC / "canonical-printed-pages" / "base-spec"
COORD = REPO / "ege-matematika-baza-demoversiya-2026" / "source-diagnostics" / "canonical-coordinates"
EVIDENCE = REPO / "ege-matematika-baza-demoversiya-2026" / "source-evidence" / "printed-pages"

errors = []
notes = []

def require(condition, message):
    if not condition:
        errors.append(message)

base_pages = sorted(BASE.glob("page-*.txt"))
spec_pages = sorted(SPEC.glob("page-*.txt"))
images = sorted(EVIDENCE.glob("page-*.webp"))
notes.append(f"base text pages={len(base_pages)}")
notes.append(f"base spec pages={len(spec_pages)}")
notes.append(f"base evidence images={len(images)}")
require(len(base_pages) == 29, f"expected 29 base text pages, got {len(base_pages)}")
require(len(spec_pages) == 12, f"expected 12 base spec pages, got {len(spec_pages)}")
require(len(images) == 29, f"expected 29 base source images, got {len(images)}")

checks = {
    8: "Шоколадка стоит 25 рублей",
    9: "365 суток",
    20: "В бак, имеющий форму",
    28: "Список заданий викторины",
    29: "Система оценивания экзаменационной работы по математике",
}
for page, phrase in checks.items():
    p = BASE / f"page-{page:02d}.txt"
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    require(phrase in text, f"page {page}: missing phrase {phrase!r}")

if (BASE / "page-09.txt").exists():
    p9 = (BASE / "page-09.txt").read_text(encoding="utf-8")
    require("15,8 секунды" in p9, "page 9: missing '15,8 секунды'")
if (BASE / "page-10.txt").exists():
    p10 = (BASE / "page-10.txt").read_text(encoding="utf-8")
    require("365 суток" not in p10, "page 10 incorrectly contains table cell '365 суток' from page 9")
    require("15,8 секунды" not in p10, "page 10 incorrectly contains table cell '15,8 секунды' from page 9")

map_path = BASE / "PAGE-MAP.json"
if map_path.exists():
    page_map = json.loads(map_path.read_text(encoding="utf-8"))
    require(page_map.get("generated_printed_pages") == 29, "PAGE-MAP generated_printed_pages != 29")
    widths = sorted({round(p["visual_width_pt"], 3) for p in page_map["pages"]})
    heights = sorted({round(p["visual_height_pt"], 3) for p in page_map["pages"]})
    notes.append(f"visual widths={widths}")
    notes.append(f"visual heights={heights}")
    require(all(419 <= w <= 423 for w in widths), f"unexpected printed-page widths: {widths}")
    require(all(593 <= h <= 597 for h in heights), f"unexpected printed-page heights: {heights}")
else:
    errors.append("base PAGE-MAP.json missing")

coord20 = COORD / "page-20.json"
if coord20.exists():
    data = json.loads(coord20.read_text(encoding="utf-8"))
    xs0 = [w["x0"] for w in data["words"]]
    xs1 = [w["x1"] for w in data["words"]]
    notes.append(f"page20 x-range={min(xs0):.3f}..{max(xs1):.3f}")
    require(min(xs0) >= -3, f"page20 x0 too negative: {min(xs0)}")
    require(max(xs1) <= 424, f"page20 x1 outside printed page: {max(xs1)}")
else:
    errors.append("canonical coordinate page-20.json missing")

result = {
    "status": "PASS" if not errors else "FAIL",
    "notes": notes,
    "errors": errors,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
