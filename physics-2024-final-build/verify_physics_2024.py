#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BUILD = Path(__file__).resolve().parent
OUT = BUILD / "out" / "ege-fizika-demoversiya-2024-v1.0-TILDA-HQ-SOURCE"
DIST = BUILD / "dist"
PREFIX = "ege-fizika-demoversiya-2024"
PREVIEW = OUT / f"{PREFIX}-PREVIEW.html"
PORT = 8765


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_true(value, label: str):
    if not value:
        raise AssertionError(label)


def browser_gate() -> dict:
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--directory", str(OUT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page_errors: list[str] = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            url = f"http://127.0.0.1:{PORT}/{PREVIEW.name}"
            page.goto(url, wait_until="networkidle")
            card_count = page.locator(".ep24-card").count()
            if card_count != 26:
                raise AssertionError(f"26 task cards: got {card_count}; ep24={page.locator('#ep24').count()}; runtime={page.evaluate('typeof window.EP24_TEST_SCORE')}; errors={page_errors[:10]}")
            assert_true(page.locator(".ep24-source").count() == 26, "26 official source task images")
            assert_true(page.locator(".ep24-source").evaluate_all("els => els.every(e => e.complete && e.naturalWidth > 0)"), "all task images decode")
            assert_true(page.locator("#ep24-total").count() == 1, "result score node")
            assert_true(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), "desktop no horizontal overflow")

            checks = {
                "task5_exact": page.evaluate("EP24_TEST_SCORE(5,'34')"),
                "task5_reverse": page.evaluate("EP24_TEST_SCORE(5,'43')"),
                "task5_missing": page.evaluate("EP24_TEST_SCORE(5,'3')"),
                "task5_extra": page.evaluate("EP24_TEST_SCORE(5,'134')"),
                "task5_wrong": page.evaluate("EP24_TEST_SCORE(5,'12')"),
                "task6_exact": page.evaluate("EP24_TEST_SCORE(6,'12')"),
                "task6_one_wrong": page.evaluate("EP24_TEST_SCORE(6,'11')"),
                "task6_extra": page.evaluate("EP24_TEST_SCORE(6,'123')"),
                "task12_comma": page.evaluate("EP24_TEST_SCORE(12,'0,25')"),
                "task12_dot": page.evaluate("EP24_TEST_SCORE(12,'0.25')"),
                "task20_reverse": page.evaluate("EP24_TEST_SCORE(20,'53')"),
            }
            expected = {
                "task5_exact": 2, "task5_reverse": 2, "task5_missing": 1, "task5_extra": 1, "task5_wrong": 0,
                "task6_exact": 2, "task6_one_wrong": 1, "task6_extra": 0,
                "task12_comma": 1, "task12_dot": 1, "task20_reverse": 1,
            }
            assert_true(checks == expected, f"scorer regression {checks}")

            page.locator("#ep24-a-1").fill("-5")
            page.reload(wait_until="networkidle")
            assert_true(page.locator("#ep24-a-1").input_value() == "-5", "answer persistence")

            official = {
                1:"-5",2:"24",3:"48",4:"2",5:"34",6:"12",7:"2",8:"400",9:"13",10:"13",
                11:"3",12:"0,25",13:"3",14:"45",15:"42",16:"76",17:"21",18:"134",19:"3,40,2",20:"35"
            }
            for n, answer in official.items():
                page.locator(f"#ep24-a-{n}").fill(answer)
            for n in range(21,27):
                page.locator(f"#ep24-a-{n}").fill(f"Контрольное решение {n}")
            page.locator("#ep24-finish").click()
            page.locator("#ep24-results.is-open").wait_for()
            assert_true(page.locator(".ep24-review").count() == 20, "20 short review cards")
            assert_true(page.locator(".ep24-self").count() == 6, "6 extended self-assessment cards")
            order = page.eval_on_selector_all("[data-section]", "els => els.map(e => e.dataset.section)")
            assert_true(order == ["short-review", "self-assessment"], f"result order {order}")
            max_points = {21:3,22:2,23:2,24:3,25:3,26:4}
            for n, pts in max_points.items():
                page.locator(f'.ep24-score-btn[data-n="{n}"][data-p="{pts}"]').click()
            assert_true(page.locator("#ep24-total").inner_text().strip() == "45 / 45", "45/45 total")

            criteria = page.locator(".ep24-criteria img")
            assert_true(criteria.count() == 17, "17 official solution/criteria logical pages")
            page.locator(".ep24-criteria details").evaluate_all("els => els.forEach(e => e.open = true)")
            criteria.evaluate_all("els => els.forEach(e => e.loading = 'eager')")
            page.wait_for_function("() => [...document.querySelectorAll('.ep24-criteria img')].every(e => e.complete && e.naturalWidth > 0)")
            assert_true(criteria.evaluate_all("els => els.every(e => e.complete && e.naturalWidth > 0)"), "all criteria images decode")

            responsive = {}
            for width in (390, 320):
                page.set_viewport_size({"width": width, "height": 820})
                page.goto(url, wait_until="networkidle")
                ok = page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
                responsive[str(width)] = bool(ok)
                assert_true(ok, f"responsive {width} no horizontal overflow")

            assert_true(not page_errors, f"browser page errors: {page_errors}")
            browser.close()
            return {"status":"PASS","task_cards":26,"short_review":20,"extended_review":6,"criteria_pages":17,"scorer":checks,"responsive":responsive,"full_score":"45 / 45","browser_errors":0}
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def package_gate() -> dict:
    acceptance = json.loads((OUT / f"{PREFIX}-ACCEPTANCE.json").read_text(encoding="utf-8"))
    assert_true(acceptance["unresolved_text_fidelity"] == 0, "text fidelity gate")
    assert_true(acceptance["physics_2025_content_used"] == 0 and acceptance["physics_2026_content_used"] == 0, "cross-year gate")
    assert_true(acceptance["criteria_source_logical_pages"] == 17, "criteria source count")
    t123 = sorted(OUT.glob(f"{PREFIX}-T123-*.txt"))
    assert_true(len(t123) == acceptance["t123_count"], "T123 manifest count")
    assert_true(len(t123) <= 80, "T123 practicality limit")
    assert_true(max(p.stat().st_size for p in t123) < 42500, "T123 size limit")
    archive = DIST / "ege-fizika-demoversiya-2024-v1.0-TILDA-HQ-SOURCE.zip"
    assert_true(archive.exists() and archive.stat().st_size > 0, "archive exists")
    recorded = (DIST / "SHA256.txt").read_text(encoding="utf-8").split()[0]
    assert_true(recorded == sha256(archive), "archive sha256")
    return {"status":"PASS","archive":archive.name,"archive_sha256":recorded,"archive_bytes":archive.stat().st_size,"t123_count":len(t123),"max_t123_bytes":max(p.stat().st_size for p in t123)}


def main():
    pkg = package_gate()
    browser = browser_gate()
    report = {"status":"PASS","package":pkg,"browser":browser}
    (DIST / "VERIFICATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
