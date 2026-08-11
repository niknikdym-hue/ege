#!/usr/bin/env python3
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parent
pages = root.parent
packages = {
    2022: pages / "ege-russkiy-demoversiya-2022-v1.0.0",
    2023: pages / "ege-russkiy-demoversiya-2023-v1.0.0",
    2024: pages / "ege-russkiy-demoversiya-2024-v1.0.1",
    2025: pages / "ege-russkiy-demoversiya-2025-v1.0.2",
    2026: pages / "ege-russkiy-demoversiya-2026-v4.2",
}
corrections = {
    tuple(map(int, key.split("-"))): value
    for key, value in json.loads(
        (root / "OFFICIAL-CORRECTIONS.json").read_text(encoding="utf-8")
    ).items()
}
source_corrections = json.loads(
    (root / "SOURCE-CORRECTIONS.json").read_text(encoding="utf-8")
)


def block(path):
    text = path.read_text("utf-8")
    match = re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', text, re.S)
    assert match, f"JSON block missing: {path}"
    return json.loads(match.group(1))


cards = []
rendered_sources = {}
for path in sorted(root.glob("ege-russkiy-trenazher-T123-0[2-9].txt")):
    data = block(path)
    cards.extend(data.get("cards", []))
    rendered_sources.update(data.get("sources", {}))

raw = {}
for year, folder in packages.items():
    tasks = []
    sources = {}
    for part in (2, 3, 4):
        data = block(folder / f"ege-russkiy-demoversiya-T123-0{part}.txt")
        tasks.extend(data["tasks"])
        sources.update(data.get("sources", {}))
    raw[year] = ({int(task["number"]): task for task in tasks}, sources)

failures = []
checks = 0


def check(condition, message):
    global checks
    checks += 1
    if not condition:
        failures.append(message)


def marker_count(value):
    return len(re.findall(r"<(?:strong|em|u)\b", value or "", re.I))


def has_visible_marker(value):
    return bool(
        marker_count(value)
        or re.search(r"[А-ЯЁ]{2,}", re.sub(r"<[^>]+>", " ", value or ""))
        or re.search(r"[а-яё][А-ЯЁ][а-яё]", re.sub(r"<[^>]+>", " ", value or ""))
    )


for card in cards:
    match = re.fullmatch(r"ege-ru-(\d+)-(\d{4})-(\d+)-(\d+)", card["id"])
    check(bool(match), f"bad provenance id {card['id']}")
    if not match:
        continue
    _, year, original, variant = map(int, match.groups())
    if card.get("bankSource") == "orthoepic-list-2026":
        check(card["task"] == 4, f"{card['id']}: supplemental visual card must be task 4")
        check(card["promptHtml"].count("<li>") == 5, f"{card['id']}: five orthoepic words required")
        check(
            len(re.findall(r"<strong>[А-ЯЁ]</strong>", card["promptHtml"])) == 5,
            f"{card['id']}: every supplemental stress letter must be explicit",
        )
        check(
            "Запишите номера ответов." in card["promptHtml"],
            f"{card['id']}: full supplemental instruction missing",
        )
        continue
    base, source_map = raw[year][0][original], raw[year][1]
    variants = base.get("variants") or [base]
    expected = dict(base)
    expected.pop("variants", None)
    expected.update(variants[variant - 1])
    correction = corrections.get((year, original, variant), {})
    expected_prompt = str(
        correction.get("promptHtml", expected.get("promptHtml", ""))
    ).strip()
    for old, new in correction.get("promptReplacements", []):
        expected_prompt = expected_prompt.replace(old, new)
    check(card["promptHtml"] == expected_prompt, f"{card['id']}: prompt markup changed")
    check(
        marker_count(card["promptHtml"]) == marker_count(expected_prompt),
        f"{card['id']}: prompt emphasis count changed",
    )
    source_id = expected.get("sourceId", base.get("sourceId"))
    if source_id:
        source = source_map[source_id]
        expected_source = source.get("html", "") if isinstance(source, dict) else str(source)
        for old, new in source_corrections.get(f"{year}:{source_id}", {}).get("replacements", []):
            expected_source = expected_source.replace(old, new)
        actual_source = rendered_sources.get(card.get("sourceKey"), "")
        check(actual_source == expected_source, f"{card['id']}: source HTML changed")
        check(
            marker_count(actual_source) == marker_count(expected_source),
            f"{card['id']}: source emphasis count changed",
        )
    material = card["promptHtml"] + rendered_sources.get(card.get("sourceKey"), "")
    if re.search(r"выделен", card["promptHtml"], re.I):
        check(has_visible_marker(material), f"{card['id']}: highlighting referenced but invisible")

task2_2026 = next(card for card in cards if card["id"].startswith("ege-ru-02-2026"))
task2_source = rendered_sources[task2_2026["sourceKey"]]
check(task2_source.count("<strong>") == 5, "2026 task 2 must keep five highlighted source words")
for token in ("пришёл", "духовной", "характер", "прозрение", "кровь"):
    check(f"<strong>{token}</strong>" in task2_source, f"2026 task 2 missing highlight: {token}")
for card in (card for card in cards if card["task"] == 4):
    check(
        len(re.findall(r"<strong>[А-ЯЁ]</strong>", card["promptHtml"])) == 5,
        f"{card['id']}: every stress letter must be explicitly highlighted",
    )
    if card["sourceYear"] >= 2024:
        check(
            "Запишите номера ответов." in card["promptHtml"],
            f"{card['id']}: full answer instruction missing",
        )
for task, minimum in ((13, 7), (14, 11)):
    current = next(card for card in cards if card["task"] == task and card["sourceYear"] == 2026)
    check(current["promptHtml"].count("<strong>") >= minimum, f"2026 task {task}: target markup missing")

task22_2026 = next(card for card in cards if card["id"] == "ege-ru-22-2026-22-01")
check(task22_2026["promptHtml"].count("<strong>") >= 11, "2026 task 22: letter/word emphasis missing")
check("<em>Фарфор</em>" in task22_2026["promptHtml"], "2026 task 22: italic word Фарфор missing")
check("<em>бронза</em>" in task22_2026["promptHtml"], "2026 task 22: italic word бронза missing")

for card_id in (
    "ege-ru-23-2026-23-02",
    "ege-ru-23-2025-23-02",
    "ege-ru-23-2024-22-02",
    "ege-ru-24-2026-24-02",
    "ege-ru-24-2025-24-02",
    "ege-ru-24-2024-23-02",
):
    card = next(card for card in cards if card["id"] == card_id)
    check("<strong>" in card["promptHtml"], f"{card_id}: significant negation/error emphasis missing")

if failures:
    print("\n".join(failures))
    print(f"FAIL visual contract: {len(failures)} failures / {checks} checks")
    raise SystemExit(1)
print(f"PASS visual contract: {len(cards)} cards, {checks} markup/source checks")
