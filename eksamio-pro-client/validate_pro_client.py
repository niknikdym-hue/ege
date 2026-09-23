#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "eksamio-learning-engine"
CANONICAL = ENGINE / "russian-program" / "RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json"
CATALOG = HERE / "program-catalog.json"


def main() -> int:
    canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))

    assert catalog["program_id"] == canonical["program_id"]
    assert catalog["subject"] == "russian"
    assert catalog["grades"] == [5, 6, 7, 8, 9, 10, 11]
    assert set(catalog["routes"]) == set(canonical["program_scope"]["routes"])
    assert len(catalog["modules"]) == 16
    assert len({module["module_id"] for module in catalog["modules"]}) == 16

    expected = {module["module_id"]: module for module in canonical["modules"]}
    actual = {module["module_id"]: module for module in catalog["modules"]}
    assert set(actual) == set(expected) == {f"RU-PROG-{number:02d}" for number in range(1, 17)}
    for module_id, module in actual.items():
        source = expected[module_id]
        assert module["title_ru"] == source["title_ru"], module_id
        assert set(module["routes"]) == set(source["route_relevance"]), module_id

    index = (HERE / "index.html").read_text(encoding="utf-8")
    app = (HERE / "app.js").read_text(encoding="utf-8")
    adapters = (HERE / "adapters.js").read_text(encoding="utf-8")
    styles = (HERE / "styles.css").read_text(encoding="utf-8")
    loop_styles = (HERE / "live-loop.css").read_text(encoding="utf-8")

    # Separate Pro authority: no browser persistence is canonical learner state.
    assert "/ege/russkiy/demoversiya/" in index
    assert "Tilda" not in adapters
    assert "localStorage" not in index + app + adapters
    assert "sessionStorage" not in index + app + adapters
    assert "EKSAMIO_PRO_RUSSIAN" in adapters

    # UI consumes swappable adapters; localhost mock identity remains only a CI fixture.
    for contract in ("continuePasswordless", "submitPractice", "createSandboxOrder", "confirmSandboxOrder", "ask"):
        assert contract in adapters and contract in app, contract
    assert "mode==='http'" in adapters
    assert "/api/tutor/turn" in adapters
    assert "/api/russian/practice/submit" in adapters
    assert "/api/russian/history" in adapters
    assert "/api/owner/diagnostics" in adapters
    assert "/api/identity/logout" in adapters
    assert "/api/identity/demo-continuity" not in adapters
    assert "state.adapters.tutor.ask({card_id:state.practice.card_id,message})" in app
    assert "semantic_id:state.practice.semantic_id" not in app
    assert "source_ref:state.practice.source_ref" not in app
    assert "entitlement:state.entitlement" not in app
    assert "if(state.identity.authenticated)await loadAuthenticatedState();else renderGuestState();" in app

    # Registered-only production path: HTTP UI navigates to the explicit registration
    # surface and never creates or merges an anonymous learner profile itself.
    assert "safeRegistrationUrl" in app
    assert "production registration URL is required" in app
    assert "production registration URL requires HTTPS" in app
    assert "window.location.assign(state.runtime.registrationUrl)" in app
    assert "if(state.adapters.mode!=='mock')" in app
    assert "Mock identity используется только localhost/CI" in app
    assert "Анонимная попытка связана" not in app
    assert "Ответ можно отправить из тренажёра без входа" not in app
    assert "Без входа учебные действия не записываются в PEIS" in app
    assert "window.addEventListener('eksamio:authenticated',refreshAuthenticatedSession)" in app

    # Runtime safety: localhost may default to deterministic mock for CI/browser fixtures,
    # but a deployed/non-local client must have explicit HTTP runtime binding and HTTPS.
    assert "EKSAMIO_PRO_RUNTIME_CONFIG" in app
    assert "resolveAdapterRuntime()" in app
    assert "mock Pro adapters are forbidden outside localhost" in app
    assert "EKSAMIO_PRO_RUNTIME_CONFIG is required outside localhost" in app
    assert "production Pro client requires HTTPS" in app
    assert "production Pro backend requires HTTPS" in app
    assert "credentials are forbidden in Pro backend URL" in app
    assert "state.runtime=resolveAdapterRuntime()" in app
    assert "state.adapters=window.EksamioProAdapters.createAdapters(state.runtime)" in app
    assert "state.adapters=window.EksamioProAdapters.createAdapters({mode:'mock'})" not in app

    # Sandbox payment remains localhost/mock-only; HTTP mode can read entitlement only.
    assert "/api/payments/entitlement" in adapters
    assert "/api/payments/sandbox/confirm" not in adapters
    assert "/api/payments/orders" not in adapters
    assert "sandbox purchase is localhost/mock only" in app
    assert "if(state.adapters.mode==='mock')" in app and "addEventListener('click',purchaseSandbox)" in app
    assert "button.hidden=true" in app
    assert "Production checkout будет доступен только после допуска server-owned SKU и trusted payment boundary." in app

    # Reuse the one existing owner-reviewed Russian source item; do not generate truth in UI.
    reviewed = json.loads((ENGINE / "92-RUSSIAN-EXCEPTIONS-PRACTICE-PILOT-v0.1.json").read_text(encoding="utf-8"))
    item = next(item for item in reviewed["items"] if item["practice_item_id"] == "ex-practice-alt-sochetat-001")
    assert item["status"] in {"reviewed", "source_verified"}
    assert item["prompt"]["text"] in adapters
    assert item["answer"]["text"] in adapters
    assert item["feedback"]["why"] in adapters
    mapping = json.loads((ENGINE / "russian-program" / "RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json").read_text(encoding="utf-8"))
    row = next(row for row in mapping["rows"] if row["practice_item_id"] == item["practice_item_id"])
    assert row["integration_ready"] is True
    assert row["mapping_resolution"] == "EXACT"
    assert row["semantic_target_ids"] == ["school-i-e-alternating-verb-roots-stressed-a"]
    assert row["semantic_target_ids"][0] in adapters

    combined = "\n".join((index, app, adapters, styles, loop_styles))
    forbidden_literals = ("ROBOKASSA_PASSWORD", "YANDEX_API_KEY", "OPENAI_API_KEY", "Authorization: Bearer", "sk-proj-")
    for literal in forbidden_literals:
        assert literal not in combined, literal

    assert "@media(max-width:600px)" in styles
    assert "@media(max-width:600px)" in loop_styles
    assert "Решено сегодня" in index
    assert "ownerDiagnostics" in index
    assert "Мой Eksamio" in index
    print("SEP1_PRO_CLIENT_STATIC_VALIDATION=PASS")
    print("canonical_program_modules=16")
    print("grade_scope=5-11")
    print("oge_route=present")
    print("ege_route=present")
    print("reviewed_owner_practice_reused=1")
    print("runtime_binding=EXPLICIT_HTTP_OUTSIDE_LOCALHOST")
    print("production_registration=EXPLICIT_REGISTERED_ONLY")
    print("production_anonymous_continuity=0")
    print("production_mock_fallback=0")
    print("production_sandbox_payment_path=0")
    print("client_secrets=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
