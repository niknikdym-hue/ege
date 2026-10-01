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
OUT = BUILD / "out" / "ege-fizika-demoversiya-2022-v1.0-TILDA-HQ-SOURCE"
DIST = BUILD / "dist"
PREFIX = "ege-fizika-demoversiya-2022"
PREVIEW = OUT / f"{PREFIX}-PREVIEW.html"
ARCHIVE = DIST / "ege-fizika-demoversiya-2022-v1.0-TILDA-HQ-SOURCE.zip"
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

            assert_true(page.locator("#ep22").get_attribute("data-state") == "idle", "initial idle state")
            assert_true(page.locator("#ep22-calculator").count() == 1, "calculator control")
            assert_true(page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth"), "desktop overflow")
            page.locator("#ep22-start").click()
            assert_true(page.locator(".ep22-nav-btn").count() == 30, "30 navigation buttons")

            task_images = 0
            for number in range(1, 31):
                page.get_by_role("button", name=str(number), exact=True).click()
                image = page.locator(".ep22-source")
                assert_true(image.count() == 1, f"task {number} source image")
                assert_true(image.evaluate("e => e.complete && e.naturalWidth > 0"), f"task {number} image decode")
                assert_true(f"задание {number} из 30" in page.locator(".ep22-task-number").inner_text().lower(), f"task {number} identity")
                assert_true(page.locator("#ep22-task-stage .ep22-mini").first.inner_text().strip() == f"ФИПИ 2022 · официальный пример {number}", f"task {number} official example label")
                task_images += 1

            scorer_checks = {
                "task1_exact": page.evaluate("EP22_TEST_SCORE(1,'35')"),
                "task1_reverse": page.evaluate("EP22_TEST_SCORE(1,'53')"),
                "task1_missing": page.evaluate("EP22_TEST_SCORE(1,'3')"),
                "task1_extra": page.evaluate("EP22_TEST_SCORE(1,'135')"),
                "task1_wrong": page.evaluate("EP22_TEST_SCORE(1,'14')"),
                "task2_exact": page.evaluate("EP22_TEST_SCORE(2,'325')"),
                "task2_one_wrong": page.evaluate("EP22_TEST_SCORE(2,'324')"),
                "task2_extra": page.evaluate("EP22_TEST_SCORE(2,'3251')"),
                "task14_comma": page.evaluate("EP22_TEST_SCORE(14,'0,4')"),
                "task14_dot": page.evaluate("EP22_TEST_SCORE(14,'0.4')"),
                "task22_exact": page.evaluate("EP22_TEST_SCORE(22,'0,60,1')"),
                "task23_reverse": page.evaluate("EP22_TEST_SCORE(23,'21')"),
            }
            expected = {
                "task1_exact": 2, "task1_reverse": 2, "task1_missing": 1, "task1_extra": 1, "task1_wrong": 0,
                "task2_exact": 2, "task2_one_wrong": 1, "task2_extra": 0,
                "task14_comma": 1, "task14_dot": 1, "task22_exact": 1, "task23_reverse": 1,
            }
            assert_true(scorer_checks == expected, f"scorer regression {scorer_checks}")

            page.get_by_role("button", name="1", exact=True).click()
            page.locator("#ep22-answer").fill("35")
            page.reload(wait_until="networkidle")
            assert_true(page.locator("#ep22").get_attribute("data-state") == "running", "running restore")
            assert_true(page.locator("#ep22-answer").input_value() == "35", "answer restore")

            page.locator("#ep22-calculator").click()
            page.locator("#ep22-calc-input").fill("sqrt(9)+2^3")
            page.locator('[data-action="equals"]').click()
            assert_true(page.locator("#ep22-calc-result").inner_text().strip() == "11", "calculator result")
            page.keyboard.press("Escape")
            assert_true(page.locator("#ep22-modal").get_attribute("data-open") == "false", "calculator closes")
            assert_true(page.evaluate("document.activeElement && document.activeElement.id === 'ep22-calculator'"), "modal focus return")

            page.get_by_role("button", name="24", exact=True).click()
            page.locator('.ep22-symbol[data-symbol="μ"]').first.click()
            assert_true("μ" in page.locator("#ep22-answer").input_value(), "symbol insertion")

            official = {
                1: "35", 2: "325", 3: "3", 4: "2", 5: "100", 6: "134", 7: "33", 8: "23", 9: "200", 10: "2",
                11: "600", 12: "12", 13: "22", 14: "0,4", 15: "8", 16: "40", 17: "124", 18: "23", 19: "41", 20: "0,025",
                21: "23", 22: "0,60,1", 23: "12",
            }
            for number, answer in official.items():
                page.get_by_role("button", name=str(number), exact=True).click()
                page.locator("#ep22-answer").fill(answer)
            for number in range(24, 31):
                page.get_by_role("button", name=str(number), exact=True).click()
                page.locator("#ep22-answer").fill(f"Контрольное решение {number}")

            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("#ep22-finish").click()
            page.locator('#ep22[data-state="finished"]').wait_for()
            assert_true(page.locator(".ep22-review").count() == 23, "23 short review cards")
            assert_true(page.locator(".ep22-self").count() == 7, "7 self-assessment cards")
            assert_true(page.locator(".ep22-review").evaluate_all("els => els.map(e => Number(e.dataset.task)).join(',')") == ",".join(map(str, range(1, 24))), "short review order")
            assert_true(page.locator(".ep22-self").evaluate_all("els => els.map(e => Number(e.dataset.task)).join(',')") == ",".join(map(str, range(24, 31))), "extended review order")
            sections = page.eval_on_selector_all("[data-section]", "els => els.map(e => e.dataset.section)")
            assert_true(sections == ["result", "short-review", "self-assessment", "sources"], f"result order {sections}")
            assert_true(page.get_by_role("heading", name="Проверка заданий", exact=True).count() == 1, "single review heading")
            assert_true(page.get_by_role("heading", name="Самооценка заданий 24–30", exact=True).count() == 1, "single self heading")

            max_points = {24: 3, 25: 2, 26: 2, 27: 3, 28: 3, 29: 3, 30: 4}
            for number, points in max_points.items():
                page.locator(f'.ep22-self[data-task="{number}"] select').select_option(str(points))
            assert_true(page.locator("#ep22-total-score").inner_text().strip() == "54", "54/54 total")

            page.locator(".ep22-criteria").evaluate_all("els => els.forEach(e => e.open = true)")
            criteria = page.locator(".ep22-criteria img")
            assert_true(criteria.count() == 17, "17 bounded criteria assets")
            criteria.evaluate_all("els => els.forEach(e => e.loading = 'eager')")
            page.wait_for_function("() => [...document.querySelectorAll('.ep22-criteria img')].every(e => e.complete && e.naturalWidth > 0)")

            sentinels = ["ep22-sentinel-2023", "ep22-sentinel-2024", "ep22-sentinel-2025", "ep22-sentinel-2026"]
            page.evaluate("([a,b,c,d]) => { localStorage.setItem('eksamio_ege_physics_demo_2023_v1', a); localStorage.setItem('eksamio_ege_physics_demo_2024_v1', b); localStorage.setItem('eksamio_ege_physics_demo_2025_v1', c); localStorage.setItem('eksamio_ege_physics_demo_2026_v2', d); }", sentinels)
            page.reload(wait_until="networkidle")
            assert_true(page.locator("#ep22").get_attribute("data-state") == "finished", "finished restore")
            assert_true(page.locator("#ep22-total-score").inner_text().strip() == "54", "score restore")
            stored = page.evaluate("() => [localStorage.getItem('eksamio_ege_physics_demo_2023_v1'), localStorage.getItem('eksamio_ege_physics_demo_2024_v1'), localStorage.getItem('eksamio_ege_physics_demo_2025_v1'), localStorage.getItem('eksamio_ege_physics_demo_2026_v2')]")
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
            page.locator("#ep22-reset-result").click()
            page.locator("#ep22-start").click()
            page.locator("#ep22-answer").fill("wrong")
            page.once("dialog", lambda dialog: dialog.accept())
            page.locator("#ep22-finish").click()
            assert_true(page.locator(".ep22-review").count() == 23, "partial finish review")
            assert_true(page.locator("#ep22-short-score").inner_text().strip() == "0", "partial finish score")

            assert_true(not page_errors, f"browser errors: {page_errors}")
            context.close()
            browser.close()
            return {
                "status": "PASS", "task_images_checked": task_images, "short_review": 23, "extended_review": 7,
                "criteria_assets": 17, "scorer": scorer_checks, "responsive": responsive, "full_score": "54/54",
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
    assert_true(all(acceptance[f"physics_{year}_content_used"] == 0 for year in (2023, 2024, 2025, 2026)), "cross-year")
    assert_true(acceptance["criteria_source_logical_pages"] == 17, "criteria region count")
    task_regions = [item for item in manifest if item["kind"] == "task_source_region"]
    assert_true(len(task_regions) == 30, "task source count")
    assert_true([item["task"] for item in task_regions] == list(range(1, 31)), "task source order")
    bounded = [item for item in manifest if item["kind"] == "official_solution_criteria_bounded_region"]
    assert_true(len(bounded) == 17, "bounded criteria regions")
    assert_true(all(item["four_edge_complete"] and item["no_neighbor_task_content"] for item in bounded), "shared-page edge gate")
    t123 = sorted(OUT.glob(f"{PREFIX}-T123-*.txt"))
    assert_true(len(t123) == acceptance["t123_count"], "T123 manifest")
    assert_true(len(t123) <= 48, "T123 practical count")
    assert_true(max(path.stat().st_size for path in t123) < 42500, "T123 size")
    assert_true(
        all(path.read_text(encoding="utf-8").count("<script") == path.read_text(encoding="utf-8").count("</script>") for path in t123),
        "T123 script tags independently closed",
    )
    head = (OUT / f"{PREFIX}-HEAD.txt").read_text(encoding="utf-8")
    assert_true("<body" not in head.lower() and "<script" not in head.lower(), "deployable HEAD markup")
    assert_true(all(year not in head for year in ("2023", "2024", "2025", "2026")), "HEAD cross-year gate")
    seo_path = OUT / f"{PREFIX}-SEO.txt"
    assert_true(seo_path.exists(), "SEO file exists")
    seo = seo_path.read_text(encoding="utf-8")
    assert_true("/ege/fizika/demoversiya/2022/" in seo, "SEO canonical year")
    assert_true("30 заданий" in seo and "235 минут" in seo, "SEO content facts")
    assert_true(all(year not in seo for year in ("2023", "2024", "2025", "2026")), "SEO cross-year gate")
    assert_true(ARCHIVE.exists() and ARCHIVE.stat().st_size > 0, "archive exists")
    recorded = (DIST / "SHA256.txt").read_text(encoding="utf-8").split()[0]
    assert_true(recorded == sha256(ARCHIVE), "archive sha256")
    with tempfile.TemporaryDirectory(prefix="physics-2022-clean-") as tmp:
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
