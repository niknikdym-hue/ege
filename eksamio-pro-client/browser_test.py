#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
VIEWPORTS = [
    ("desktop", 1280, 900),
    ("mobile-390", 390, 844),
    ("mobile-375", 375, 812),
    ("mobile-320", 320, 720),
]


def wait_for_server() -> None:
    deadline = time.time() + 10
    while time.time() < deadline:
        with contextlib.suppress(OSError):
            with socket.create_connection(("127.0.0.1", PORT), timeout=0.2):
                return
        time.sleep(0.1)
    raise RuntimeError("Pro client HTTP server did not start")


def wait_for_app_ready(page, console_errors: list[str], label: str) -> None:
    try:
        page.wait_for_function("document.documentElement.dataset.appReady === 'true'", timeout=5000)
    except PlaywrightTimeoutError as exc:
        state = page.evaluate("document.documentElement.dataset.appReady || 'unset'")
        alert = page.locator("[role='alert']").all_inner_texts()
        raise AssertionError(
            f"app initialization failed at {label}: appReady={state}; alerts={alert}; console={console_errors}"
        ) from exc


def assert_no_overflow(page, label: str) -> None:
    values = page.evaluate(
        """() => ({
          docScroll: document.documentElement.scrollWidth,
          docClient: document.documentElement.clientWidth,
          bodyScroll: document.body.scrollWidth,
          bodyClient: document.body.clientWidth
        })"""
    )
    if values["docScroll"] > values["docClient"] + 1 or values["bodyScroll"] > values["bodyClient"] + 1:
        raise AssertionError(f"horizontal overflow at {label}: {values}")


def run_viewport(browser, label: str, width: int, height: int) -> None:
    page = browser.new_page(viewport={"width": width, "height": height})
    console_errors: list[str] = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda error: console_errors.append(str(error)))
    page.goto(BASE, wait_until="networkidle")
    wait_for_app_ready(page, console_errors, label)

    # Product scope must be visible and complete before authentication.
    assert page.locator("body").get_attribute("data-auth") == "anonymous"
    page.locator("button[data-view='program']").click()
    assert page.locator("[data-module-id]").count() == 16
    assert page.locator("[data-module-id='RU-PROG-15']").count() == 1
    assert page.locator("[data-module-id='RU-PROG-16']").count() == 1
    for route in ("school", "oge", "ege", "diagnostic", "thematic_trainer", "homework", "tutor"):
        assert page.locator(f"[data-route-chip='{route}']").count() == 1
    assert_no_overflow(page, f"{label}:program")

    # Anonymous free-demo entry continues into a server-owned Pro identity boundary.
    page.locator("button[data-view='plan']").click()
    page.locator("#entryContinue").click()
    page.wait_for_function("document.body.dataset.auth === 'authenticated'")
    assert page.locator("#identityStatus").inner_text() == "Ученик Pro"

    # One actual owner-reviewed Russian learning action -> evidence-shaped progress/NBA.
    page.locator("button[data-view='practice']").click()
    assert "соч..тание" in page.locator("#practicePrompt").inner_text()
    assert page.locator("#practiceSemantic").inner_text() == "Проверенный навык"
    page.locator("#practiceAnswer").fill("сочетание")
    page.locator("#checkAnswer").click()
    page.wait_for_selector("#practiceFeedback.is-correct")
    assert "независим" in page.locator("#practiceFeedback").inner_text().lower()
    assert page.locator("#todayCorrect").inner_text() == "1"

    # Tutor is visible but locked until payment/entitlement; sandbox grant unlocks without UI rewrite.
    page.locator("button[data-view='tutor']").click()
    assert page.locator("#tutorLocked").is_visible()
    assert page.locator("#tutorAvailable").is_hidden()
    page.locator("#purchaseButton").click()
    page.wait_for_function("document.body.dataset.entitlement === 'active'")
    assert page.locator("#tutorLocked").is_hidden()
    assert page.locator("#tutorAvailable").is_visible()
    assert "sandbox" in page.locator("#paymentStatus").inner_text().lower()

    # Grounded Tutor response retains same session and advertises independent verification.
    page.locator("#tutorInput").fill("Почему здесь пишется Е?")
    page.locator("#tutorForm button[type='submit']").click()
    page.wait_for_function("document.querySelectorAll('#tutorThread .message').length >= 3")
    page.wait_for_function("document.querySelector('#progressEvents').textContent.toLowerCase().includes('tutor')")
    tutor_texts = page.locator("#tutorThread .message.tutor").all_inner_texts()
    assert any("проверенному материалу" in text.lower() for text in tutor_texts)
    assert any("сочет" in text.lower() for text in tutor_texts)

    page.locator("button[data-view='progress']").click()
    assert page.locator("#progressPercent").inner_text() == "48%"
    events_text = page.locator("#progressEvents").inner_text().lower()
    assert "evidence" in events_text
    assert "tutor" in events_text
    assert_no_overflow(page, f"{label}:completed-flow")

    # Core accessibility / safety checks.
    assert page.locator("h1:visible").count() == 1
    assert page.locator("a[href='#']").count() == 0
    for selector in ("#practiceAnswer", "#tutorInput"):
        assert page.locator(selector).count() == 1
    if console_errors:
        raise AssertionError(f"browser console errors at {label}: {console_errors}")
    page.close()


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "--directory", str(ROOT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_server()
        chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium")
        if not chrome:
            raise RuntimeError("Chrome/Chromium not available on browser-test runner")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=chrome, headless=True)
            try:
                for label, width, height in VIEWPORTS:
                    run_viewport(browser, label, width, height)
            finally:
                browser.close()
    finally:
        server.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            server.wait(timeout=3)
        if server.poll() is None:
            server.kill()
    print("SEP1_PRO_CLIENT_BROWSER_E2E=PASS")
    print("viewports=1280,390,375,320")
    print("modules=16")
    print("routes=school,oge,ege,diagnostic,thematic_trainer,homework,tutor")
    print("identity_continuity=PASS")
    print("reviewed_practice_to_progress_nba=PASS")
    print("payment_entitlement_adapter=PASS")
    print("grounded_tutor_adapter=PASS")
    print("horizontal_overflow=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
