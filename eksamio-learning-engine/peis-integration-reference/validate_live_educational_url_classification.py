#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str) -> dict:
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main() -> None:
    classified = load("LIVE-EDUCATIONAL-URL-CLASSIFICATION-v0.1.json")
    registry = load("LIVE-EDUCATIONAL-ASSET-RECONCILIATION-v0.1.json")
    assert classified["issue"] == registry["issue"] == 185
    assert classified["status"] == "BOUNDED_OWNER_PRIORITY_LIVE_EDUCATIONAL_URLS_CLASSIFIED"
    expected_vocab = {"VITRINE_ONLY", "INTERACTIVE_LEARNING", "REFERENCE_KNOWLEDGE", "LEGACY_ROUTE"}
    assert set(classified["classification_vocabulary"]) == expected_vocab
    assert set(classified["classifications"]) == expected_vocab

    buckets = classified["classifications"]
    for key, urls in buckets.items():
        assert len(urls) == classified["counts"][key]
        assert len(urls) == len(set(urls)), f"duplicate URL in {key}"
        assert all(url.startswith("https://eksamio.ru/") for url in urls)
    all_urls = [url for urls in buckets.values() for url in urls]
    assert len(all_urls) == len(set(all_urls)), "one live URL cannot have two classifications"
    assert classified["counts"] == {
        "VITRINE_ONLY": 5,
        "INTERACTIVE_LEARNING": 29,
        "REFERENCE_KNOWLEDGE": 0,
        "LEGACY_ROUTE": 0,
    }

    assets = {asset["asset_id"]: asset for asset in registry["assets"]}
    trainer_ids = [
        "live-russian-ege-full-trainer",
        "live-russian-orthoepy-trainer",
        "live-russian-dictionary-words-trainer",
        "live-russian-paronyms-trainer",
        "live-russian-phraseology-trainer",
    ]
    expected_learning = {assets[asset_id]["live_url"] for asset_id in trainer_ids}
    demo = assets["live-ege-demo-catalog"]
    expected_learning.update(route["url"] for route in demo["verified_demo_routes"])
    assert len(expected_learning) == 29
    assert set(buckets["INTERACTIVE_LEARNING"]) == expected_learning, "classification must cover exactly all reconciled learning routes"

    expected_vitrine = {
        "https://eksamio.ru/",
        "https://eksamio.ru/ege/",
        "https://eksamio.ru/ege/demoversii/",
        "https://eksamio.ru/trenazhery/",
        "https://eksamio.ru/ege/russkiy/",
    }
    assert set(buckets["VITRINE_ONLY"]) == expected_vitrine
    embedded = classified["embedded_reference_knowledge"]
    assert embedded["status"] == "PRESENT_INSIDE_INTERACTIVE_DEMO_ROUTES_NOT_STANDALONE_URL_ASSET"
    assert embedded["reading_or_opening_creates_mastery"] is False
    assert embedded["tutor_admission_requires_source_provenance"] is True
    boundary = classified["learner_state_boundary"]
    assert boundary["browser_local_state_is_future_canonical"] is False
    assert boundary["future_canonical_learning_event_requires_registered_user_identity_ref"] is True
    assert boundary["url_classification_alone_can_emit_mastery"] is False
    assert classified["false_exact_mastery"] == 0

    print("LIVE_EDUCATIONAL_URL_CLASSIFICATION=PASS")
    print("vitrine_only=5 interactive_learning=29 reference_standalone=0 legacy_observed=0")
    print("embedded_reference_reading_mastery=0")
    print("false_exact_mastery=0")


if __name__ == "__main__":
    main()
