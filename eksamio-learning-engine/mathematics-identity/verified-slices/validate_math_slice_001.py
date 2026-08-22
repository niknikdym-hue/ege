#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
KERNEL_DIR = ENGINE / "peis-reference-kernel"
sys.path.insert(0, str(KERNEL_DIR))

from peis_reference_kernel import snapshot  # noqa: E402

TARGET = "math-probability-classical-equally-likely"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(schema: dict, instance: dict, label: str) -> None:
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)
    print(f"PASS schema: {label}")


def sub_schema(contract: dict, def_name: str) -> dict:
    return {
        "$schema": contract.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$defs": contract["$defs"],
        "$ref": f"#/$defs/{def_name}",
    }


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def main() -> int:
    evidence_doc = load(HERE / "MATH-SLICE-001-EVIDENCE-FIXTURES-v0.1.json")
    golden = load(HERE / "MATH-SLICE-001-GOLDEN-SCENARIOS-v0.1.json")
    prereq_doc = load(HERE / "MATH-SLICE-001-PREREQUISITE-FIXTURE-v0.1.json")
    registry = load(HERE.parent / "MATHEMATICS-SEMANTIC-REGISTRY-v0.1.json")
    source_gate = load(HERE / "MATH-SLICE-001-SOURCE-GATE-v0.1.json")

    evidence_schema = load(ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json")
    state_schema = load(ENGINE / "278-EKSAMIO-LEARNER-STATE-MATERIALIZED-VIEW-SCHEMA-v0.1.json")
    mastery_schema = load(ENGINE / "282-EKSAMIO-MASTERY-INFERENCE-CONTRACT-v0.1.json")
    readiness_contract = load(ENGINE / "283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json")
    retention_contract = load(ENGINE / "284-EKSAMIO-RETENTION-SCHEDULE-STATE-CONTRACT-v0.1.json")
    nba_schema = load(ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json")

    require(registry["canonical_semantic_identity_count"] == 1, "registry contains exactly one canonical identity at slice v0.1")
    require(registry["canonical_semantic_identities"][0]["semantic_id"] == TARGET, "registry identity equals slice target")
    require(source_gate["admitted_semantic_identity"]["semantic_id"] == TARGET, "source gate admits the registry target")
    require(source_gate["prerequisite_admission"]["canonical_prerequisite_edge_created"] is False, "slice creates no canonical prerequisite edge")

    kernel_text = (KERNEL_DIR / "peis_reference_kernel.py").read_text(encoding="utf-8")
    require(TARGET not in kernel_text, "shared PEIS kernel contains no Mathematics target identity")

    events = evidence_doc["events"]
    require(len(events) == 3, "fixture contains exactly three learner evidence events")
    for index, event in enumerate(events, start=1):
        validate(evidence_schema, event, f"EvidenceEvent #{index}")
        require(event["subject_id"] == "mathematics", f"event #{index} subject is mathematics")
        require(event["semantic_targets"] == [{
            "semantic_id": TARGET,
            "target_role": "PRIMARY",
            "mapping_resolution": "EXACT",
            "mapping_confidence": 1.0,
            "mapping_review_status": "source_verified",
        }], f"event #{index} has one exact source-verified semantic target")

    validate(sub_schema(readiness_contract, "edge"), prereq_doc["edge"], "TEST_FIXTURE_ONLY prerequisite edge shape")
    require(prereq_doc["edge"]["admission_scope"] == "TEST_FIXTURE_ONLY", "prerequisite fixture is explicitly non-canonical")
    admitted_edges = [prereq_doc]

    snapshots = []
    for row in golden["scenarios"]:
        count = row["event_count"]
        snap = snapshot(
            events[:count],
            TARGET,
            admitted_edges,
            goal_context="math-slice-001",
            recommendation_id=f"nba.math001.{count:04d}",
        )
        snapshots.append(snap)

        validate(mastery_schema, snap["mastery"], f"Mastery scenario {count}")
        validate(sub_schema(readiness_contract, "readiness_state"), snap["readiness"], f"Readiness scenario {count}")
        validate(sub_schema(retention_contract, "state"), snap["retention"], f"Retention scenario {count}")
        validate(state_schema, snap["state"], f"Materialized state scenario {count}")
        validate(nba_schema, snap["nba"], f"NBA scenario {count}")

        require(snap["mastery"]["mastery"]["band"] == row["expected_mastery_band"], f"scenario {count} mastery band = {row['expected_mastery_band']}")
        require(snap["mastery"]["system_inference"]["confidence_band"] == row["expected_confidence_band"], f"scenario {count} confidence band = {row['expected_confidence_band']}")
        require(snap["readiness"]["status"] == row["expected_readiness_status"], f"scenario {count} readiness = {row['expected_readiness_status']}")
        require(snap["retention"]["current_state"] == row["expected_retention_state"], f"scenario {count} retention = {row['expected_retention_state']}")
        require(snap["nba"]["action_type"] == row["expected_nba_action"], f"scenario {count} NBA = {row['expected_nba_action']}")
        require(set(row["expected_nba_reasons"]).issubset(set(snap["nba"]["reason_codes"])), f"scenario {count} expected NBA reasons are present")
        require(snap["readiness"]["required_prerequisite_assessments"] == [], f"scenario {count} TEST_FIXTURE_ONLY edge does not enter canonical readiness")

    first, second, final = snapshots
    require(first["mastery"]["mastery"]["band"] == "EMERGING", "diagnostic failure establishes EMERGING state")
    require(second["mastery"]["mastery"]["band"] == "EMERGING", "assisted success alone does not promote mastery")
    require(second["nba"]["action_type"] == "INDEPENDENT_PRACTICE", "meaningful assistance requires independent verification")
    require(final["mastery"]["mastery"]["band"] == "DEVELOPING", "fresh independent verification yields EMERGING -> DEVELOPING delta")
    require(final["mastery"]["mastery"]["estimate"] is None, "reference kernel does not invent numeric mastery coefficient")
    require(final["state"]["mastery"]["estimate"] is None, "materialized state preserves null numeric mastery estimate")
    require(final["state"]["retention_due_at"] is None, "materialized state does not invent retention due time")
    require(final["retention"]["next_due_calculation"]["scheduled_at"] is None, "retention policy does not invent scheduled_at")
    require(final["retention"]["next_due_calculation"]["due_window_start"] is None, "retention policy does not invent due-window start")
    require(final["retention"]["next_due_calculation"]["due_window_end"] is None, "retention policy does not invent due-window end")
    require(final["retention"]["last_delayed_check"] is None, "same-session verification is not delayed retention")
    require(final["nba"]["action_type"] == "RETENTION_REVIEW", "verified target advances to retention review")

    output = {
        "slice_id": "MATH-SLICE-001",
        "result": "PASS",
        "target_semantic_id": TARGET,
        "mastery_bands": [snap["mastery"]["mastery"]["band"] for snap in snapshots],
        "confidence_bands": [snap["mastery"]["system_inference"]["confidence_band"] for snap in snapshots],
        "readiness_statuses": [snap["readiness"]["status"] for snap in snapshots],
        "retention_states": [snap["retention"]["current_state"] for snap in snapshots],
        "nba_actions": [snap["nba"]["action_type"] for snap in snapshots],
        "final_mastery_estimate": final["mastery"]["mastery"]["estimate"],
        "final_retention_due_at": final["state"]["retention_due_at"],
        "test_fixture_edge_assessments": final["readiness"]["required_prerequisite_assessments"],
    }
    out_path = HERE / "MATH-SLICE-001-RUN-OUTPUT.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print("MATH-SLICE-001 VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
