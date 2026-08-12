#!/usr/bin/env python3
"""Chromium smoke for generated standalone Russian Exceptions Trainer preview.

Uses page.set_content because some controlled environments block file:// and localhost
navigation. It still executes the exact generated inline package in real Chromium.
No production/network mutation.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path


def find_chromium() -> str | None:
    explicit = os.environ.get("CHROMIUM_PATH")
    if explicit and Path(explicit).is_file():
        return explicit
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        value = shutil.which(name)
        if value:
            return value
    for value in ("/usr/bin/chromium", "/usr/bin/google-chrome"):
        if Path(value).is_file():
            return value
    return None


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        print(f"PREVIEW TEST ERROR: Playwright is required: {exc}", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[2]
    out = root / "build" / "standalone-exceptions-tilda"
    prefix = "trenazhery-russkiy-isklyucheniya"
    preview = out / f"{prefix}-PREVIEW.html"
    runtime_path = root / "build" / "RUSSIAN-EXCEPTIONS-RUNTIME.json"
    manifest_path = out / f"{prefix}-PACKAGE-MANIFEST.json"
    for path in (preview, runtime_path, manifest_path):
        if not path.is_file():
            print(f"PREVIEW TEST ERROR: missing generated file {path}", file=sys.stderr)
            return 2

    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    html = preview.read_text(encoding="utf-8")

    # Static package safety before browser execution.
    if manifest.get("t123_blocks") != 9 or manifest.get("runtime_data_blocks") != 4:
        raise AssertionError(f"unexpected package shape: {manifest.get('t123_blocks')} / {manifest.get('runtime_data_blocks')}")
    if int(manifest.get("largest_block_bytes", 999999)) > int(manifest.get("max_block_bytes", 0)):
        raise AssertionError("package contains oversized T123 block")
    package_text = "\n".join((out / row["file"]).read_text(encoding="utf-8") for row in manifest["files"])
    forbidden = (
        "eksamio:ege-russian-trainer:progress:v1",
        "eksamio:ege-russian-trainer:session:v1",
        "__erTrainerTest",
        "id=\"er-trainer\"",
        "#er-trainer",
    )
    for needle in forbidden:
        if needle in package_text:
            raise AssertionError(f"standalone package leaks current-trainer namespace: {needle}")
    if package_text.count("EksamioRussianExceptions") < 4:
        raise AssertionError("standalone namespace not consistently present")

    chromium = find_chromium()
    if not chromium:
        print("PREVIEW TEST ERROR: Chromium executable not found.", file=sys.stderr)
        return 2

    storage_js = """Object.defineProperty(window,'localStorage',{configurable:true,value:(()=>{const m=new Map();return{getItem:k=>m.has(k)?m.get(k):null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k),clear:()=>m.clear()}})()});"""

    def answer(page, correct: bool = True) -> str:
        pid = page.locator('.rex-card').get_attribute('data-practice-id')
        item = runtime['practice_items'][pid]
        if item['response_kind'] in ('single_choice', 'classification'):
            idx = int(item['answer']['option_index'])
            options = item['prompt']['options']
            if not correct:
                idx = (idx + 1) % len(options)
            page.locator(f'.rex-option[data-option="{idx}"]').click()
        else:
            text = item['answer']['text'] if correct else item['answer']['text'] + 'x'
            page.locator('[data-rex-input]').fill(text)
        page.locator('[data-action="check"]').click()
        page.locator('.rex-feedback-title').wait_for()
        expected = 'Верно' if correct else 'Неверно'
        assert expected in page.locator('.rex-feedback-title').inner_text()
        return pid

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium, args=['--no-sandbox'])
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.evaluate(storage_js)
        page.set_content(html, wait_until='load')
        page.locator('[data-rex-ready="1"]').wait_for(timeout=5000)
        assert page.locator('h1').inner_text() == 'Тренажёр исключений'
        assert page.locator('[data-action="my"]').count() == 0

        # Full normal session, including rule drawer.
        page.locator('[data-action="start-all"]').click()
        for index in range(10):
            answer(page, True)
            if index == 0:
                page.locator('[data-action="rule"]').click()
                assert page.locator('[data-rex-dialog-body]').inner_text().strip()
                page.locator('[data-rex-dialog] .rex-button-secondary').click()
            page.locator('[data-action="next"]').click()
        page.get_by_text('Что получилось').wait_for()
        assert page.locator('[data-action="my"]').count() == 0, 'all-correct new material must not create My Exceptions'

        # One genuine error -> My Exceptions + repeat errors.
        page.locator('[data-action="start-all"]').click()
        answer(page, False)
        page.locator('[data-action="finish"]').click()
        assert page.locator('[data-action="repeat-errors"]').count() == 1
        raw = page.evaluate("localStorage.getItem('eksamio:russian:exceptions')")
        state = json.loads(raw)
        assert any(row.get('wrong_count', 0) > 0 for row in state['exceptions'].values())
        page.locator('[data-action="my"]').click()
        assert 'В работе' in page.locator('.rex-panel').inner_text()
        assert page.locator('[data-action="practice-one"]').count() >= 1

        # Mobile layout: no horizontal overflow and quiet session finish action.
        page.set_viewport_size({"width": 375, "height": 812})
        page.locator('[data-action="home"]').click()
        dims = page.evaluate("({sw:document.documentElement.scrollWidth,cw:document.documentElement.clientWidth})")
        assert dims['sw'] <= dims['cw'] + 1, dims
        page.locator('[data-action="start-all"]').click()
        finish_width = page.locator('[data-action="finish"]').bounding_box()['width']
        viewport_width = page.viewport_size['width']
        assert finish_width < viewport_width * 0.7, 'Finish should be a quiet secondary action on mobile'

        # Corrupt state must remain untouched; anonymous training remains available.
        page.evaluate("localStorage.setItem('eksamio:russian:exceptions','{broken')")
        page.set_content(html, wait_until='load')
        page.locator('[data-rex-ready="1"]').wait_for()
        assert 'сохранённые данные' in page.locator('.rex-notice').inner_text()
        assert page.evaluate("localStorage.getItem('eksamio:russian:exceptions')") == '{broken'
        page.locator('[data-action="start-all"]').click()
        page.locator('.rex-card').wait_for()

        # Remove one runtime chunk: UI must fail closed, not invent questions.
        scripts = list(re.finditer(r'<script type="application/json" class="rex-runtime-chunk"[\s\S]*?</script>\s*', html))
        assert len(scripts) == 4
        match = scripts[-1]
        broken_html = html[:match.start()] + html[match.end():]
        page2 = browser.new_page(viewport={"width": 900, "height": 700})
        page2.evaluate(storage_js)
        page2.set_content(broken_html, wait_until='load')
        page2.get_by_text('Тренажёр не загрузился').wait_for(timeout=5000)
        assert page2.locator('.rex-card').count() == 0
        browser.close()

    print(
        "PASS: standalone preview Chromium flow / 10-card session / rule drawer / personal error / "
        "mobile / corrupt-state / fail-closed runtime"
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
