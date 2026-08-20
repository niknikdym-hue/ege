#!/usr/bin/env python3
"""Validate and execute MATHEMATICS-SEMANTIC-SLICE-001 through shared PEIS."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
KERNEL_DIR = ENGINE / "peis-reference-kernel"
sys.path.insert(0, str(KERNEL_DIR))

from peis_reference_kernel import infer_mastery, snapshot  # noqa: E402

SEMANTIC_ID = "math-probability-equiprobable-elementary-outcomes"
SOURCE_GATE = HERE / "MATHEMATICS-SEMANTIC-SLICE-001-SOURCE-GATE-v0.1.json"
REGISTRY = HERE / "MATHEMATICS-SEMANTIC-SLICE-001-REGISTRY-SEED-v0.1.json"
CROSSWALK = HERE / "MATHEMATICS-SEMANTIC-SLICE-001-CROSSWALK-v0.1.json"
ITEM_BANK = HERE / "MATHEMATICS-SEMANTIC-SLICE-001-ITEM-BANK-v0.1.json"
EVIDENCE = HERE / "MATHEMATICS-SEMANTIC-SLICE-001-EVIDENCE-FIXTURES-v0.1.json"
GOLDEN = HERE / "MATHEMATICS-SEMANTIC-SLICE-001-GOLDEN-SCENARIOS-v0.1.json"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), path
    return value


def validator(schema: dict[str, Any]) -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())


def nested_schema(contract: dict[str, Any], def_name: str) -> dict[str, Any]:
    value = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$defs": contract["$defs"]}
    value.update(contract["$defs"][def_name])
    return value


def validate_snapshot(value: dict[str, Any], validators: dict[str, jsonschema.Draft202012Validator]) -> None:
    validators["mastery"].validate(value["mastery"])
    validators["readiness"].validate(value["readiness"])
    validators["retention"].validate(value["retention"])
    validators["state"].validate(value["state"])
    validators["nba"].validate(value["nba"])
    assert value["mastery"]["mastery"]["estimate"] is None
    assert value["state"]["mastery"]["estimate"] is None
    calc = value["retention"]["next_due_calculation"]
    assert calc["due_window_start"] is None and calc["due_window_end"] is None


def main() -> None:
    source_gate = load(SOURCE_GATE)
    registry = load(REGISTRY)
    crosswalk = load(CROSSWALK)
    item_bank = load(ITEM_BANK)
    evidence = load(EVIDENCE)
    golden = load(GOLDEN)

    assert source_gate["semantic_candidate"]["semantic_id"] == SEMANTIC_ID
    assert source_gate["semantic_candidate"]["admission_status"] == "PROPOSED_CANONICAL"
    assert source_gate["prerequisite_gate"]["canonical_edges_proposed"] == 0
    assert source_gate["prerequisite_gate"]["decision"] == "NO_EDGE_ADMITTED"
    assert registry["identity_count"] == 1
    assert registry["identities"][0]["semantic_id"] == SEMANTIC_ID
    assert registry["identities"][0]["prerequisite_ids"] == []
    assert registry["status"] == "PROPOSED_CANONICAL_PENDING_HUMAN_PR_ACCEPTANCE"

    exact_product_maps = [row for row in crosswalk["mappings"] if row["relation"] == "ASSESSES" and row["mapping_resolution"] == "EXACT"]
    assert len(exact_product_maps) == 5
    assert len(crosswalk["explicit_non_mappings"]) == 1
    assert crosswalk["explicit_non_mappings"][0]["source_id"] == "2026:task4:passenger-count-15-19"

    items = item_bank["items"]
    assert len(items) == 12
    assert len({item["item_id"] for item in items}) == 12
    for item in items:
        assert item["semantic_targets"] == [SEMANTIC_ID]
        assert item["answer"]["type"] == "number"
        assert item["model"]["equiprobable_outcomes"] > 0
        assert 0 <= item["model"]["favorable_outcomes"] <= item["model"]["equiprobable_outcomes"]
    practice_prompts = {item["prompt_ru"] for item in items if item["phase"] == "TARGETED_PRACTICE"}
    verify_prompts = {item["prompt_ru"] for item in items if item["phase"] == "INDEPENDENT_VERIFICATION"}
    assert practice_prompts.isdisjoint(verify_prompts)
    assert item_bank["content_policy"]["official_fipi_wording_copied"] is False
    assert item_bank["counts"] == {"total": 12, "diagnostic": 4, "targeted_practice": 4, "independent_verification": 4}

    event_schema = load(ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json")
    state_schema = load(ENGINE / "278-EKSAMIO-LEARNER-STATE-MATERIALIZED-VIEW-SCHEMA-v0.1.json")
    mastery_schema = load(ENGINE / "282-EKSAMIO-MASTERY-INFERENCE-CONTRACT-v0.1.json")
    readiness_contract = load(ENGINE / "283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json")
    retention_contract = load(ENGINE / "284-EKSAMIO-RETENTION-SCHEDULE-STATE-CONTRACT-v0.1.json")
    nba_schema = load(ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json")

    event_validator = validator(event_schema)
    validators = {
        "state": validator(state_schema),
        "mastery": validator(mastery_schema),
        "readiness": validator(nested_schema(readiness_contract, "readiness_state")),
        "retention": validator(nested_schema(retention_contract, "state")),
        "nba": validator(nba_schema),
    }

    events_by_id = {event["event_id"]: event for event in evidence["events"]}
    assert len(events_by_id) == 5
    for event in events_by_id.values():
        event_validator.validate(event)
        assert event["subject_id"] == "mathematics"
        assert event["semantic_targets"] == [{
            "semantic_id": SEMANTIC_ID,
            "target_role": "PRIMARY",
            "mapping_resolution": "EXACT",
            "mapping_confidence": 1.0,
            "mapping_review_status": "source_verified",
        }]

    kernel_source = (KERNEL_DIR / "peis_reference_kernel.py").read_text(encoding="utf-8")
    assert SEMANTIC_ID not in kernel_source

    traces: list[dict[str, Any]] = []
    for scenario in golden["scenarios"]:
        selected: list[dict[str, Any]] = []
        trace: list[dict[str, Any]] = []
        for index, step in enumerate(scenario["steps"], start=1):
            before_band = infer_mastery(selected, SEMANTIC_ID)["mastery"]["band"]
            selected.append(events_by_id[step["consume_event"]])
            value = snapshot(
                selected,
                SEMANTIC_ID,
                [],
                goal_context=golden["goal_context"],
                recommendation_id=f"nba.math001.{scenario['scenario_id'].lower()}.{index:02d}",
            )
            validate_snapshot(value, validators)
            band = value["mastery"]["mastery"]["band"]
            assert band == step["expected_mastery_band"], (scenario["scenario_id"], index, band)
            assert value["readiness"]["status"] == step["expected_readiness"]
            if "expected_retention_state" in step:
                assert value["retention"]["current_state"] == step["expected_retention_state"]
            expected_nba = step["expected_nba"]
            assert value["nba"]["action_type"] == expected_nba["action_type"]
            assert set(value["nba"]["reason_codes"]) == set(expected_nba["reason_codes"])
            if "measured_state_delta" in step:
                expected_delta = step["measured_state_delta"]
                assert before_band == expected_delta["before_band"]
                assert band == expected_delta["after_band"]
                assert step["consume_event"] == expected_delta["evidence_event_ref"]
            trace.append({
                "step": index,
                "event": step["consume_event"],
                "mastery_band": band,
                "readiness": value["readiness"]["status"],
                "retention": value["retention"]["current_state"],
                "nba": value["nba"]["action_type"],
            })
        traces.append({"scenario_id": scenario["scenario_id"], "status": "PASS", "trace": trace})

    print("EKSAMIO MATHEMATICS SEMANTIC SLICE 001 VALIDATION")
    print("STATUS: PASS")
    print("SEMANTIC_ID:", SEMANTIC_ID)
    print("ADMISSION_STATUS: PROPOSED_CANONICAL_PENDING_HUMAN_PR_ACCEPTANCE")
    print("PREREQUISITE_EDGES: 0")
    print("ITEMS: 12 (4 diagnostic / 4 practice / 4 verification)")
    print("EVIDENCE_EVENTS: 5 / SHARED_SCHEMA_277_PASS")
    print("EXACT_PRODUCT_MAPPINGS: 5")
    print("PROFILE_TASK4_NON_MAPPING_GUARD: PASS")
    for row in traces:
        print(f"{row['scenario_id']}: PASS / steps={len(row['trace'])}")
    print("MEASURED_DELTA_A: EMERGING -> DEVELOPING -> STRONG")
    print("SHARED_KERNEL_SUBJECT_BRANCH_ADDED: false")
    print("PRODUCTION_INTEGRATION: false")


if __name__ == "__main__":
    main()
