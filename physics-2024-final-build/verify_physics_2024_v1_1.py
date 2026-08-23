#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

BUILD = Path(__file__).resolve().parent
OUT = BUILD / "out" / "ege-fizika-demoversiya-2024-v1.1-TILDA-HQ-SOURCE"
DIST = BUILD / "dist"
PREFIX = "ege-fizika-demoversiya-2024"
PREVIEW = OUT / f"{PREFIX}-PREVIEW.html"
ARCHIVE = DIST / "ege-fizika-demoversiya-2024-v1.1-TILDA-HQ-SOURCE.zip"
PORT = 8765
VIEWPORTS = (1280, 768, 390, 360, 320)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_true(value, label: str) -> None:
    if not value:
        raise AssertionError(label)


def browser_gate() -> dict:
    from playwright.sync_api import sync_playwright

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--directory", str(OUT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(1)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            context = browser.new_context(viewport={"width": 1280, "height": 900})
            page = context.new_page()
            page_errors: list[str] = []
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            url = f"http://127.0.0.1:{PORT}/{PREVIEW.name}"
            page.goto(url, wait_until="networkidle")

            assert_true(page.locator("#ep24").get_attribute("data-state") == "idle", "initial idle state")
            assert_true(page.locator("#ep24-calculator").count() == 1, "calculator control")
            assert_true(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), "desktop overflow")
            page.locator("#ep24-start").click()
            assert_true(page.locator(".ep24-nav-btn").count() == 26, "26 navigation buttons")

            task_images = 0
            for number in range(1, 27):
                page.get_by_role("button", name=str(number), exact=True).click()
                image = page.locator(".ep24-source")
                assert_true(image.count() == 1, f"task {number} source image")
                assert_true(image.evaluate("e => e.complete && e.naturalWidth > 0"), f"task {number} image decode")
                assert_true(f"Задание {number} из 26" in page.locator(".ep24-task-number").inner_text(), f"task {number} identity")
                task_images += 1

            scorer_checks = {
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
            assert_true(scorer_checks == expected, f"scorer regression {scorer_checks}")

            page.get_by_role("button", name="1", exact=True).click()
            page.locator("#ep24-answer").fill("-5")
            page.reload(wait_until="networkidle")
            assert_true(page.locator("#ep24").get_attribute("data-state") == "running", "running restore")
            assert_true(page.locator("#ep24-answer").input_value() == "-5", "answer restore")

            page.locator("#ep24-calculator").click()
            page.locator("#ep24-calc-input").fill("sqrt(9)+2^3")
            page.locator('[data-action="equals"]').click()
            assert_true(page.locator("#ep24-calc-result").inner_text().strip() == "11", "calculator result")
            page.keyboard.press("Escape")
            assert_true(page.locator("#ep24-modal").get_attribute("data-open") == "false", "calculator closes")
            assert_true(page.evaluate("document.activeElement && document.activeElement.id === 'ep24-calculator'"), "modal focus return")

            page.get_by_role("button", name="21", exact=True).click()
            page.locator('.ep24-symbol[data-symbol="μ"]').first.click()
            assert_true("μ" in page.locator("#ep24-answer").input_value(), "symbol insertion")

            official = {
                1: "-5", 2: "24", 3: "48", 4: "2", 5: "34", 6: "12", 7: "2", 8: "400", 9: "13", 10: "13",
                11: "3", 12: "0,25", 13: "3", 14: "45", 15: "42", 16: "76", 17: "21", 18: "134", 19: "3,40,2", 20: "35",
            }
            for number, answer in official.items():
                page.get_by_role("button", name=str(number), exact=True).click()
                page.locator("#ep24-answer").fill(answer)
            for number in range(21, 27):
                page.get_by_role("button", name=str(number), exact=True).click()
                page.locator("#ep24-answer").fill(f"Контрольное решение {number}")

            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("#ep24-finish").click()
            page.locator('#ep24[data-state="finished"]').wait_for()
            assert_true(page.locator(".ep24-review").count() == 20, "20 short review cards")
            assert_true(page.locator(".ep24-self").count() == 6, "6 self-assessment cards")
            assert_true(page.locator(".ep24-review").evaluate_all("els => els.map(e => Number(e.dataset.task)).join(',')") == ",".join(map(str, range(1, 21))), "short review order")
            assert_true(page.locator(".ep24-self").evaluate_all("els => els.map(e => Number(e.dataset.task)).join(',')") == ",".join(map(str, range(21, 27))), "extended review order")
            sections = page.eval_on_selector_all("[data-section]", "els => els.map(e => e.dataset.section)")
            assert_true(sections == ["result", "short-review", "self-assessment", "sources"], f"result order {sections}")
            assert_true(page.get_by_role("heading", name="Проверка заданий", exact=True).count() == 1, "single review heading")
            assert_true(page.get_by_role("heading", name="Самооценка заданий 21–26", exact=True).count() == 1, "single self heading")

            max_points = {21: 3, 22: 2, 23: 2, 24: 3, 25: 3, 26: 4}
            for number, points in max_points.items():
                page.locator(f'.ep24-self[data-task="{number}"] select').select_option(str(points))
            assert_true(page.locator("#ep24-total-score").inner_text().strip() == "45", "45/45 total")

            page.locator(".ep24-criteria").evaluate_all("els => els.forEach(e => e.open = true)")
            criteria = page.locator(".ep24-criteria img")
            assert_true(criteria.count() == 18, "18 bounded criteria assets")
            criteria.evaluate_all("els => els.forEach(e => e.loading = 'eager')")
            page.wait_for_function("() => [...document.querySelectorAll('.ep24-criteria img')].every(e => e.complete && e.naturalWidth > 0)")

            sentinels = ["ep24-sentinel-2025", "ep24-sentinel-2026"]
            page.evaluate("([a,b]) => { localStorage.setItem('eksamio_ege_physics_demo_2025_v1', a); localStorage.setItem('eksamio_ege_physics_demo_2026_v2', b); }", sentinels)
            page.reload(wait_until="networkidle")
            assert_true(page.locator("#ep24").get_attribute("data-state") == "finished", "finished restore")
            assert_true(page.locator("#ep24-total-score").inner_text().strip() == "45", "score restore")
            stored = page.evaluate("() => [localStorage.getItem('eksamio_ege_physics_demo_2025_v1'), localStorage.getItem('eksamio_ege_physics_demo_2026_v2')]")
            assert_true(stored == sentinels, "storage isolation")

            responsive: dict[str, bool] = {}
            for width in VIEWPORTS:
                page.set_viewport_size({"width": width, "height": 900})
                page.reload(wait_until="networkidle")
                ok = page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
                responsive[str(width)] = bool(ok)
                assert_true(ok, f"responsive {width} overflow")

            page.set_viewport_size({"width": 1280, "height": 900})
            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("#ep24-reset-result").click()
            page.locator("#ep24-start").click()
            page.locator("#ep24-answer").fill("wrong")
            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("#ep24-finish").click()
            assert_true(page.locator(".ep24-review").count() == 20, "partial finish review")
            assert_true(page.locator("#ep24-short-score").inner_text().strip() == "0", "partial finish score")

            assert_true(not page_errors, f"browser errors: {page_errors}")
            context.close()
            browser.close()
            return {
                "status": "PASS", "task_images_checked": task_images, "short_review": 20, "extended_review": 6,
                "criteria_assets": 18, "scorer": scorer_checks, "responsive": responsive, "full_score": "45/45",
                "full_finish": "PASS", "partial_finish": "PASS", "state_restore": "PASS", "calculator": "PASS",
                "symbol_keyboard": "PASS", "focus": "PASS", "storage_isolation": "PASS",
                "result_order": sections, "browser_errors": 0,
            }
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def package_gate() -> dict:
    acceptance = json.loads((OUT / f"{PREFIX}-ACCEPTANCE.json").read_text(encoding="utf-8"))
    manifest = json.loads((OUT / f"{PREFIX}-ASSET-MANIFEST.json").read_text(encoding="utf-8"))
    assert_true(acceptance["unresolved_text_fidelity"] == 0, "text fidelity")
    assert_true(acceptance["physics_2025_content_used"] == 0 and acceptance["physics_2026_content_used"] == 0, "cross-year")
    assert_true(acceptance["criteria_source_logical_pages"] == 18, "criteria region count")
    task_regions = [item for item in manifest if item["kind"] == "task_source_region"]
    assert_true(len(task_regions) == 26, "task source count")
    assert_true([item["task"] for item in task_regions] == list(range(1, 27)), "task source order")
    bounded = [item for item in manifest if item["kind"] == "official_solution_criteria_bounded_region"]
    assert_true(len(bounded) == 2, "shared-page bounded regions")
    assert_true(all(item["four_edge_complete"] and item["no_neighbor_task_content"] for item in bounded), "shared-page edge gate")
    t123 = sorted(OUT.glob(f"{PREFIX}-T123-*.txt"))
    assert_true(len(t123) == acceptance["t123_count"], "T123 manifest")
    assert_true(len(t123) == 48, "T123 reference practical count")
    assert_true(max(path.stat().st_size for path in t123) < 42500, "T123 size")
    assert_true(
        all(path.read_text(encoding="utf-8").count("<script") == path.read_text(encoding="utf-8").count("</script>") for path in t123),
        "T123 script tags independently closed",
    )
    head = (OUT / f"{PREFIX}-HEAD.txt").read_text(encoding="utf-8")
    assert_true("<body" not in head.lower() and "<script" not in head.lower(), "deployable HEAD markup")
    assert_true("2025" not in head and "2026" not in head, "HEAD cross-year gate")
    assert_true(ARCHIVE.exists() and ARCHIVE.stat().st_size > 0, "archive exists")
    recorded = (DIST / "SHA256.txt").read_text(encoding="utf-8").split()[0]
    assert_true(recorded == sha256(ARCHIVE), "archive sha256")
    with tempfile.TemporaryDirectory(prefix="physics-2024-clean-") as tmp:
        with zipfile.ZipFile(ARCHIVE) as archive:
            assert_true(archive.testzip() is None, "zip integrity")
            archive.extractall(tmp)
        extracted = Path(tmp) / OUT.name
        assert_true((extracted / PREVIEW.name).exists(), "clean preview")
        assert_true(len(list(extracted.glob(f"{PREFIX}-T123-*.txt"))) == len(t123), "clean T123 count")
    return {
        "status": "PASS", "archive": ARCHIVE.name, "archive_sha256": recorded, "archive_bytes": ARCHIVE.stat().st_size,
        "output_build_sha256": sha256(OUT / "SHA256SUMS.txt"), "t123_count": len(t123),
        "max_t123_bytes": max(path.stat().st_size for path in t123), "clean_package": "PASS",
    }


def main() -> None:
    report = {"status": "PASS", "package": package_gate(), "browser": browser_gate()}
    (DIST / "VERIFICATION.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
