#!/usr/bin/env python3
"""Validate the first reviewed Russian Exceptions -> shared PEIS PostgreSQL slice."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path[:0] = [
    str(HERE),
    str(ENGINE / "peis-persistence-reference"),
    str(ENGINE / "peis-service-bridge-reference"),
    str(ENGINE / "peis-reference-kernel"),
]

from peis_persistence import IntegrityConflict  # noqa: E402
from peis_reference_kernel import snapshot as kernel_snapshot  # noqa: E402
from peis_service_bridge import AdapterRegistry, HostIdentity, PeisServiceBridge  # noqa: E402
from peis_postgres import PostgresPeisPersistenceStore  # noqa: E402
from russian_exceptions_practice_adapter import (  # noqa: E402
    FIRST_SLICE_CARD_ID,
    RussianExceptionsPracticeAdapter,
)


def _recommendation_count(store: PostgresPeisPersistenceStore, learner_profile_id: str) -> int:
    row = store.connection.execute(
        "SELECT COUNT(*) AS count FROM recommendations WHERE learner_profile_id = %s",
        (learner_profile_id,),
    ).fetchone()
    return int(row["count"] if isinstance(row, dict) else row[0])


def main() -> int:
    dsn = os.environ["PEIS_DATABASE_DSN"]
    evidence_schema = json.loads(
        (ENGINE / "277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json").read_text(encoding="utf-8")
    )
    nba_schema = json.loads(
        (ENGINE / "285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json").read_text(encoding="utf-8")
    )
    store = PostgresPeisPersistenceStore(dsn, evidence_schema=evidence_schema, nba_schema=nba_schema)
    if not store.readiness():
        raise AssertionError("PostgreSQL PEIS store is not ready")

    adapter = RussianExceptionsPracticeAdapter(ENGINE)
    registry = AdapterRegistry()
    registry.register(adapter)
    bridge = PeisServiceBridge(
        store=store,
        registry=registry,
        kernel_snapshot=kernel_snapshot,
        now_provider=lambda: "2026-08-26T18:30:00+00:00",
    )
    identity = HostIdentity(
        learner_profile_id="learner-sep1-russian-001",
        identity_refs={"anonymous_identity_ref": "anon-sep1-russian-001"},
    )
    payload = {
        "card_id": FIRST_SLICE_CARD_ID,
        "session_started_at_ms": 1787769000000,
        "session_mode": "practice",
        "answer": "сочитание",
        "occurred_at_client": "2026-08-26T18:29:59+00:00",
        "client_request_id": "req-sep1-russian-001",
    }

    first = bridge.submit_checked_card(
        adapter_id=adapter.adapter_id,
        payload=payload,
        host_identity=identity,
    )
    if first["status"] != "ACCEPTED":
        raise AssertionError(f"first mapped attempt not accepted: {first['status']}")
    if first["directive"].get("canonical_state_owner") != "shared_peis":
        raise AssertionError("NBA directive is not owned by shared PEIS")
    if not first["directive"].get("action_type"):
        raise AssertionError("shared PEIS did not produce a next-best action")
    if first.get("recommendation_persistence_status") not in {"ACCEPTED", "ALREADY_APPLIED"}:
        raise AssertionError("shared PEIS recommendation was not persisted")

    events = store.list_events(identity.learner_profile_id, adapter.subject_id, effective=False)
    if len(events) != 1:
        raise AssertionError(f"expected exactly one canonical event after first attempt, got {len(events)}")
    event = events[0]
    if event["source"]["object_id"] != FIRST_SLICE_CARD_ID:
        raise AssertionError("persisted event does not reference the real reviewed practice card")
    if event["result"]["correctness"] is not False or event["result"]["score"] != 0:
        raise AssertionError("server-side deterministic evaluator did not reject the intentionally wrong answer")
    if event["semantic_targets"][0]["semantic_id"] != "school-i-e-alternating-verb-roots-stressed-a":
        raise AssertionError("server-owned semantic mapping is not the merged RU-1 mapping")
    if event["semantic_targets"][0]["mapping_resolution"] != "EXACT":
        raise AssertionError("first-slice mapping resolution drifted")
    if not event["error_observations"] or event["error_observations"][0]["precision"] != "EXACT":
        raise AssertionError("exact mapped failure did not produce exact server-side evidence")

    replay = bridge.submit_checked_card(
        adapter_id=adapter.adapter_id,
        payload=dict(payload),
        host_identity=identity,
    )
    if replay["status"] != "ALREADY_APPLIED":
        raise AssertionError(f"identical replay is not idempotent: {replay['status']}")
    if replay["event_receipt"] != first["event_receipt"]:
        raise AssertionError("identical replay changed the canonical server position")
    if len(store.list_events(identity.learner_profile_id, adapter.subject_id, effective=False)) != 1:
        raise AssertionError("identical replay duplicated canonical evidence")
    if _recommendation_count(store, identity.learner_profile_id) != 1:
        raise AssertionError("identical replay duplicated the persisted NBA")

    changed = dict(payload)
    changed["answer"] = "сочетание"
    try:
        bridge.submit_checked_card(
            adapter_id=adapter.adapter_id,
            payload=changed,
            host_identity=identity,
        )
    except IntegrityConflict:
        pass
    else:
        raise AssertionError("changed educational payload under stable event identity was not rejected")
    if len(store.list_events(identity.learner_profile_id, adapter.subject_id, effective=False)) != 1:
        raise AssertionError("integrity-conflict retry changed canonical evidence count")

    counts = adapter.mapping["counts"]
    expected_counts = {
        "active_cards": 121,
        "integration_ready": 121,
        "blocked": 0,
        "exact": 116,
        "partial_composite": 5,
        "represented_exception_ids": 88,
    }
    if {key: counts.get(key) for key in expected_counts} != expected_counts:
        raise AssertionError("merged 121 mapping counts drifted during service connection")

    result = {
        "task": "SEP1-RU-PEIS-001",
        "result": "PASS",
        "baseline_main": "1ca4e771fc712ed68aca9c0ba2928d631e080cdf",
        "adapter_id": adapter.adapter_id,
        "practice_item_id": FIRST_SLICE_CARD_ID,
        "mapping_counts": expected_counts,
        "postgres_persistence": True,
        "server_owned_score": True,
        "server_owned_semantic_mapping": True,
        "first_attempt": first["status"],
        "replay": replay["status"],
        "canonical_event_count_for_fixture_learner": len(
            store.list_events(identity.learner_profile_id, adapter.subject_id, effective=False)
        ),
        "recommendation_count_for_fixture_learner": _recommendation_count(store, identity.learner_profile_id),
        "nba_action": first["directive"]["action_type"],
        "canonical_state_owner": first["directive"]["canonical_state_owner"],
        "integrity_conflict_rejected": True,
        "public_traffic_connected": False,
        "learner_pii_in_fixture": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
