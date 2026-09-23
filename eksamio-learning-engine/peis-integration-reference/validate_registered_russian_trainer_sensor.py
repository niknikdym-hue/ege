#!/usr/bin/env python3
"""Registered-only acceptance for the actual Russian trainer -> PEIS sensor boundary."""
from __future__ import annotations

import json
from pathlib import Path

from russian_trainer_sensor import (
    RussianTrainerSensorAdapter,
    SensorMappingError,
    find_card,
    load_trainer_bank_chunk,
)

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
MAPPING = HERE / "RUSSIAN-EGE-TRAINER-SENSOR-MAP-v0.1.json"
BANK = ENGINE / "russkiy-knigi" / "ege-russkiy-trenazher" / "ege-russkiy-trenazher-T123-06.txt"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
    bank = load_trainer_bank_chunk(BANK)
    card = find_card(bank, "ege-ru-12-2026-12-01")
    require(card["task"] == 12, "acceptance card is the real Task 12 bank object")

    adapter = RussianTrainerSensorAdapter(mapping)
    session = {
        "version": 1,
        "status": "running",
        "mode": "practice",
        "ids": [card["id"]],
        "current": 0,
        "answers": {card["id"]: ["2", "5"]},
        "checked": {},
        "recorded": {},
        "startedAt": 1787238000000,
        "endsAt": None,
        "completedAt": None,
        "config": {"mode": "practice", "tasks": [12]},
    }
    checked = {"score": 0, "max": 1, "answer": ["2", "5"]}

    def build(identity_refs: dict[str, str]) -> dict:
        return adapter.build_checked_event(
            card=card,
            session=session,
            checked=checked,
            learner_profile_id="learner-registered-sensor-ci",
            identity_refs=identity_refs,
            occurred_at_client="2026-09-06T17:00:00+03:00",
            received_at_server="2026-09-06T17:00:01+03:00",
            server_sequence=1,
            server_watermark="wm-registered-sensor-ci",
        )

    valid_identity = {"user_identity_ref": "user:sensor-ci"}
    event = build(valid_identity)
    require(event["identity_refs"] == valid_identity, "valid server-owned user identity is preserved exactly")
    require(all(target["mapping_resolution"] == "COMPOSITE" for target in event["semantic_targets"]), "Task 12 remains COMPOSITE")
    require(event["error_observations"], "wrong whole-card result remains observable")
    require(all(obs["precision"] != "EXACT" for obs in event["error_observations"]), "whole-card Task 12 failure creates no exact semantic error")

    rejected = [
        ({}, "missing identity"),
        ({"anonymous_identity_ref": "anon:sensor-ci"}, "anonymous identity"),
        ({"user_identity_ref": "user:sensor-ci", "anonymous_identity_ref": "anon:sensor-ci"}, "mixed identity"),
        ({"user_identity_ref": "device:sensor-ci"}, "device namespace"),
        ({"user_identity_ref": "user:"}, "empty user namespace payload"),
    ]
    for identity_refs, label in rejected:
        try:
            build(identity_refs)
        except SensorMappingError:
            pass
        else:
            raise AssertionError(f"{label} must fail closed")

    print("REGISTERED_RUSSIAN_TRAINER_SENSOR=PASS")
    print("valid_user_identity_ref=PASS")
    print("anonymous_missing_mixed_device_identity=REJECTED")
    print("task12_mapping=COMPOSITE")
    print("false_exact_mastery=0")


if __name__ == "__main__":
    main()
