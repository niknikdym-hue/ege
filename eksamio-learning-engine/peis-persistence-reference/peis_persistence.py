#!/usr/bin/env python3
"""Subject-neutral reference persistence boundary for Eksamio PEIS.

This module persists canonical EvidenceEvent records and rebuildable PEIS
snapshots. It deliberately does not own mastery/readiness/retention/NBA logic;
those remain in ``peis-reference-kernel``.

SQLite here is a local/CI reference implementation, not live production
infrastructure.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


class IntegrityConflict(RuntimeError):
    """Raised when a stable identity is replayed with incompatible content."""


class MissingReference(RuntimeError):
    """Raised when an append-only control/outcome record references nothing."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload_hash(value: Any) -> str:
    return _sha256_text(_canonical_json(value))


def _replay_projection(event: dict[str, Any]) -> dict[str, Any]:
    """Remove transport-assigned identity/receive fields for idempotency replay.

    ``idempotency_key`` identifies the logical append operation. A client retry
    may be assigned a fresh event_id or server receive position, but the
    observed educational payload must remain identical.
    """

    projected = copy.deepcopy(event)
    projected.pop("event_id", None)
    projected.pop("created_at", None)
    timestamps = projected.get("timestamps")
    if isinstance(timestamps, dict):
        timestamps.pop("received_at_server", None)
        timestamps.pop("server_sequence", None)
        timestamps.pop("server_watermark", None)
    return projected


def _event_order_key(event: dict[str, Any]) -> tuple[Any, ...]:
    timestamps = event.get("timestamps") or {}
    sequence = timestamps.get("server_sequence")
    has_sequence = isinstance(sequence, int)
    return (
        0 if has_sequence else 1,
        sequence if has_sequence else 0,
        timestamps.get("received_at_server") or event.get("created_at") or "",
        event.get("event_id") or "",
    )


def _history_fingerprint(events: Iterable[dict[str, Any]]) -> str:
    material = [
        {
            "event_id": event["event_id"],
            "payload_hash": _payload_hash(event),
        }
        for event in events
    ]
    return _payload_hash(material)


class PeisPersistenceStore:
    """Append-only evidence + rebuildable materialized-view reference store."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        evidence_schema: dict[str, Any],
        nba_schema: dict[str, Any],
    ) -> None:
        self.database_path = str(database_path)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.evidence_validator = Draft202012Validator(
            evidence_schema,
            format_checker=FormatChecker(),
        )
        self.nba_validator = Draft202012Validator(
            nba_schema,
            format_checker=FormatChecker(),
        )
        outcome_schema = {
            "$schema": nba_schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
            "$defs": nba_schema["$defs"],
            "$ref": "#/$defs/outcome_event",
        }
        self.outcome_validator = Draft202012Validator(
            outcome_schema,
            format_checker=FormatChecker(),
        )
        self._create_schema()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "PeisPersistenceStore":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS evidence_events (
                ingest_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                idempotency_key TEXT UNIQUE,
                full_hash TEXT NOT NULL,
                replay_hash TEXT NOT NULL,
                learner_profile_id TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                event_kind TEXT NOT NULL,
                server_sequence INTEGER,
                received_at_server TEXT NOT NULL,
                created_at TEXT NOT NULL,
                event_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_evidence_learner_subject
                ON evidence_events(learner_profile_id, subject_id);
            CREATE INDEX IF NOT EXISTS idx_evidence_server_sequence
                ON evidence_events(learner_profile_id, subject_id, server_sequence);

            CREATE TABLE IF NOT EXISTS event_semantic_targets (
                event_id TEXT NOT NULL,
                semantic_id TEXT NOT NULL,
                target_role TEXT NOT NULL,
                mapping_resolution TEXT NOT NULL,
                PRIMARY KEY(event_id, semantic_id, target_role),
                FOREIGN KEY(event_id) REFERENCES evidence_events(event_id)
            );

            CREATE INDEX IF NOT EXISTS idx_semantic_target_query
                ON event_semantic_targets(semantic_id, event_id);

            CREATE TABLE IF NOT EXISTS identity_links (
                identity_ref TEXT PRIMARY KEY,
                identity_kind TEXT NOT NULL,
                learner_profile_id TEXT NOT NULL,
                linked_at TEXT NOT NULL,
                source_event_id TEXT,
                FOREIGN KEY(source_event_id) REFERENCES evidence_events(event_id)
            );

            CREATE INDEX IF NOT EXISTS idx_identity_learner
                ON identity_links(learner_profile_id);

            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id TEXT PRIMARY KEY,
                payload_hash TEXT NOT NULL,
                learner_profile_id TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                recommendation_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recommendation_outcomes (
                outcome_event_id TEXT PRIMARY KEY,
                recommendation_id TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                outcome_json TEXT NOT NULL,
                FOREIGN KEY(recommendation_id) REFERENCES recommendations(recommendation_id)
            );

            CREATE INDEX IF NOT EXISTS idx_outcome_recommendation
                ON recommendation_outcomes(recommendation_id, occurred_at);

            CREATE TABLE IF NOT EXISTS materialized_snapshots (
                learner_profile_id TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                semantic_id TEXT NOT NULL,
                goal_context_key TEXT NOT NULL,
                evidence_fingerprint TEXT NOT NULL,
                effective_event_count INTEGER NOT NULL,
                snapshot_json TEXT NOT NULL,
                computed_at TEXT NOT NULL,
                PRIMARY KEY(learner_profile_id, subject_id, semantic_id, goal_context_key)
            );

            CREATE TRIGGER IF NOT EXISTS no_update_evidence_events
            BEFORE UPDATE ON evidence_events
            BEGIN SELECT RAISE(ABORT, 'evidence_events are append-only'); END;

            CREATE TRIGGER IF NOT EXISTS no_delete_evidence_events
            BEFORE DELETE ON evidence_events
            BEGIN SELECT RAISE(ABORT, 'evidence_events are append-only'); END;

            CREATE TRIGGER IF NOT EXISTS no_update_event_semantic_targets
            BEFORE UPDATE ON event_semantic_targets
            BEGIN SELECT RAISE(ABORT, 'event_semantic_targets are append-only'); END;

            CREATE TRIGGER IF NOT EXISTS no_delete_event_semantic_targets
            BEFORE DELETE ON event_semantic_targets
            BEGIN SELECT RAISE(ABORT, 'event_semantic_targets are append-only'); END;

            CREATE TRIGGER IF NOT EXISTS no_update_recommendations
            BEFORE UPDATE ON recommendations
            BEGIN SELECT RAISE(ABORT, 'recommendations are append-only proposals'); END;

            CREATE TRIGGER IF NOT EXISTS no_delete_recommendations
            BEFORE DELETE ON recommendations
            BEGIN SELECT RAISE(ABORT, 'recommendations are append-only proposals'); END;

            CREATE TRIGGER IF NOT EXISTS no_update_recommendation_outcomes
            BEFORE UPDATE ON recommendation_outcomes
            BEGIN SELECT RAISE(ABORT, 'recommendation_outcomes are append-only'); END;

            CREATE TRIGGER IF NOT EXISTS no_delete_recommendation_outcomes
            BEFORE DELETE ON recommendation_outcomes
            BEGIN SELECT RAISE(ABORT, 'recommendation_outcomes are append-only'); END;
            """
        )
        self.connection.commit()

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        self.evidence_validator.validate(event)
        event_json = _canonical_json(event)
        full_hash = _sha256_text(event_json)
        replay_hash = _payload_hash(_replay_projection(event))
        event_id = event["event_id"]
        idempotency_key = event.get("idempotency_key")

        existing = self.connection.execute(
            "SELECT event_id, full_hash FROM evidence_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if existing is not None:
            if existing["full_hash"] == full_hash:
                return {"status": "ALREADY_APPLIED", "event_id": existing["event_id"], "reason": "EVENT_ID_REPLAY"}
            raise IntegrityConflict(f"event_id {event_id} already exists with different payload")

        if idempotency_key:
            prior = self.connection.execute(
                "SELECT event_id, replay_hash FROM evidence_events WHERE idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if prior is not None:
                if prior["replay_hash"] == replay_hash:
                    return {"status": "ALREADY_APPLIED", "event_id": prior["event_id"], "reason": "IDEMPOTENCY_KEY_REPLAY"}
                raise IntegrityConflict(f"idempotency_key {idempotency_key} already exists with different logical payload")

        referenced_event_id = self._control_reference(event)
        if referenced_event_id is not None:
            referenced = self.connection.execute(
                "SELECT learner_profile_id, subject_id FROM evidence_events WHERE event_id = ?",
                (referenced_event_id,),
            ).fetchone()
            if referenced is None:
                raise MissingReference(f"control event {event_id} references unknown event {referenced_event_id}")
            if referenced["learner_profile_id"] != event["learner_profile_id"] or referenced["subject_id"] != event["subject_id"]:
                raise IntegrityConflict("correction/retraction must remain within learner_profile_id and subject_id")

        timestamps = event["timestamps"]
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO evidence_events(
                    event_id, idempotency_key, full_hash, replay_hash,
                    learner_profile_id, subject_id, event_kind, server_sequence,
                    received_at_server, created_at, event_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    idempotency_key,
                    full_hash,
                    replay_hash,
                    event["learner_profile_id"],
                    event["subject_id"],
                    event["event_kind"],
                    timestamps.get("server_sequence"),
                    timestamps["received_at_server"],
                    event["created_at"],
                    event_json,
                ),
            )
            for target in event["semantic_targets"]:
                self.connection.execute(
                    """
                    INSERT INTO event_semantic_targets(event_id, semantic_id, target_role, mapping_resolution)
                    VALUES (?, ?, ?, ?)
                    """,
                    (event_id, target["semantic_id"], target["target_role"], target["mapping_resolution"]),
                )
            for key, identity_ref in event["identity_refs"].items():
                kind = "ANONYMOUS" if key == "anonymous_identity_ref" else "USER"
                self._link_identity_in_transaction(
                    identity_ref=identity_ref,
                    identity_kind=kind,
                    learner_profile_id=event["learner_profile_id"],
                    linked_at=event["created_at"],
                    source_event_id=event_id,
                )

        return {"status": "ACCEPTED", "event_id": event_id, "reason": "NEW_APPEND"}

    @staticmethod
    def _control_reference(event: dict[str, Any]) -> str | None:
        correction = event.get("correction") or {}
        if event.get("event_kind") == "CORRECTION":
            return correction.get("supersedes_event_id")
        if event.get("event_kind") == "RETRACTION":
            return correction.get("retracts_event_id")
        return None

    def _link_identity_in_transaction(
        self,
        *,
        identity_ref: str,
        identity_kind: str,
        learner_profile_id: str,
        linked_at: str,
        source_event_id: str | None,
    ) -> str:
        existing = self.connection.execute(
            "SELECT learner_profile_id, identity_kind FROM identity_links WHERE identity_ref = ?",
            (identity_ref,),
        ).fetchone()
        if existing is not None:
            if existing["learner_profile_id"] != learner_profile_id:
                raise IntegrityConflict(f"identity_ref {identity_ref} is already linked to another learner")
            return "ALREADY_LINKED"
        self.connection.execute(
            """
            INSERT INTO identity_links(identity_ref, identity_kind, learner_profile_id, linked_at, source_event_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (identity_ref, identity_kind, learner_profile_id, linked_at, source_event_id),
        )
        return "LINKED"

    def link_identity(
        self,
        identity_ref: str,
        learner_profile_id: str,
        *,
        identity_kind: str = "USER",
        linked_at: str | None = None,
    ) -> dict[str, Any]:
        if identity_kind not in {"ANONYMOUS", "USER"}:
            raise ValueError("identity_kind must be ANONYMOUS or USER")
        linked_at = linked_at or datetime.now(timezone.utc).isoformat()
        with self.connection:
            status = self._link_identity_in_transaction(
                identity_ref=identity_ref,
                identity_kind=identity_kind,
                learner_profile_id=learner_profile_id,
                linked_at=linked_at,
                source_event_id=None,
            )
        return {"status": status, "identity_ref": identity_ref, "learner_profile_id": learner_profile_id}

    def resolve_identity(self, identity_ref: str) -> str | None:
        row = self.connection.execute(
            "SELECT learner_profile_id FROM identity_links WHERE identity_ref = ?",
            (identity_ref,),
        ).fetchone()
        return row["learner_profile_id"] if row is not None else None

    def raw_event(self, event_id: str) -> dict[str, Any] | None:
        row = self.connection.execute(
            "SELECT event_json FROM evidence_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return json.loads(row["event_json"]) if row is not None else None

    def event_count(self, *, learner_profile_id: str | None = None, subject_id: str | None = None) -> int:
        where: list[str] = []
        params: list[Any] = []
        if learner_profile_id is not None:
            where.append("learner_profile_id = ?")
            params.append(learner_profile_id)
        if subject_id is not None:
            where.append("subject_id = ?")
            params.append(subject_id)
        sql = "SELECT COUNT(*) AS n FROM evidence_events"
        if where:
            sql += " WHERE " + " AND ".join(where)
        return int(self.connection.execute(sql, params).fetchone()["n"])

    def list_events(
        self,
        learner_profile_id: str,
        subject_id: str,
        *,
        semantic_id: str | None = None,
        effective: bool = True,
    ) -> list[dict[str, Any]]:
        if semantic_id is None:
            rows = self.connection.execute(
                """
                SELECT event_json FROM evidence_events
                WHERE learner_profile_id = ? AND subject_id = ?
                """,
                (learner_profile_id, subject_id),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT DISTINCT e.event_json
                FROM evidence_events AS e
                JOIN event_semantic_targets AS s ON s.event_id = e.event_id
                WHERE e.learner_profile_id = ? AND e.subject_id = ? AND s.semantic_id = ?
                """,
                (learner_profile_id, subject_id, semantic_id),
            ).fetchall()
        events = sorted((json.loads(row["event_json"]) for row in rows), key=_event_order_key)
        return self._effective_events(events) if effective else events

    @staticmethod
    def _effective_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        suppressed: set[str] = set()
        evidence_candidates: list[dict[str, Any]] = []
        for event in events:
            kind = event.get("event_kind")
            correction = event.get("correction") or {}
            if kind == "RETRACTION":
                target = correction.get("retracts_event_id")
                if target:
                    suppressed.add(target)
                continue
            if kind == "CORRECTION":
                target = correction.get("supersedes_event_id")
                if target:
                    suppressed.add(target)
                evidence_candidates.append(event)
                continue
            evidence_candidates.append(event)
        return [event for event in evidence_candidates if event["event_id"] not in suppressed]

    def append_recommendation(self, recommendation: dict[str, Any]) -> dict[str, Any]:
        self.nba_validator.validate(recommendation)
        payload_hash = _payload_hash(recommendation)
        recommendation_id = recommendation["recommendation_id"]
        existing = self.connection.execute(
            "SELECT payload_hash FROM recommendations WHERE recommendation_id = ?",
            (recommendation_id,),
        ).fetchone()
        if existing is not None:
            if existing["payload_hash"] == payload_hash:
                return {"status": "ALREADY_APPLIED", "recommendation_id": recommendation_id}
            raise IntegrityConflict(f"recommendation_id {recommendation_id} already exists with different payload")
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO recommendations(
                    recommendation_id, payload_hash, learner_profile_id, subject_id, created_at, recommendation_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    recommendation_id,
                    payload_hash,
                    recommendation["learner_profile_id"],
                    recommendation["subject_id"],
                    recommendation["created_at"],
                    _canonical_json(recommendation),
                ),
            )
        return {"status": "ACCEPTED", "recommendation_id": recommendation_id}

    def append_recommendation_outcome(self, outcome: dict[str, Any]) -> dict[str, Any]:
        self.outcome_validator.validate(outcome)
        outcome_id = outcome["outcome_event_id"]
        payload_hash = _payload_hash(outcome)
        existing = self.connection.execute(
            "SELECT payload_hash FROM recommendation_outcomes WHERE outcome_event_id = ?",
            (outcome_id,),
        ).fetchone()
        if existing is not None:
            if existing["payload_hash"] == payload_hash:
                return {"status": "ALREADY_APPLIED", "outcome_event_id": outcome_id}
            raise IntegrityConflict(f"outcome_event_id {outcome_id} already exists with different payload")
        recommendation = self.connection.execute(
            "SELECT recommendation_id FROM recommendations WHERE recommendation_id = ?",
            (outcome["recommendation_id"],),
        ).fetchone()
        if recommendation is None:
            raise MissingReference(f"outcome {outcome_id} references unknown recommendation")
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO recommendation_outcomes(
                    outcome_event_id, recommendation_id, payload_hash, event_type, occurred_at, outcome_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    outcome_id,
                    outcome["recommendation_id"],
                    payload_hash,
                    outcome["event_type"],
                    outcome["occurred_at"],
                    _canonical_json(outcome),
                ),
            )
        return {"status": "ACCEPTED", "outcome_event_id": outcome_id}

    def recommendation_outcomes(self, recommendation_id: str) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT outcome_json FROM recommendation_outcomes
            WHERE recommendation_id = ? ORDER BY occurred_at, outcome_event_id
            """,
            (recommendation_id,),
        ).fetchall()
        return [json.loads(row["outcome_json"]) for row in rows]

    def recompute_snapshot(
        self,
        *,
        learner_profile_id: str,
        subject_id: str,
        semantic_id: str,
        admitted_edges: Iterable[dict[str, Any]],
        goal_context: str | None,
        kernel_snapshot: Any,
        meaningful_help_delivered_for: Iterable[str] = (),
        recommendation_id: str,
    ) -> dict[str, Any]:
        events = self.list_events(learner_profile_id, subject_id, effective=True)
        if not events:
            raise MissingReference("cannot recompute a learner state without accepted evidence")
        result = kernel_snapshot(
            events,
            semantic_id,
            list(admitted_edges),
            goal_context=goal_context,
            meaningful_help_delivered_for=list(meaningful_help_delivered_for),
            recommendation_id=recommendation_id,
        )
        goal_key = goal_context or "__NONE__"
        fingerprint = _history_fingerprint(events)
        computed_at = result["state"]["computed_at"]
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO materialized_snapshots(
                    learner_profile_id, subject_id, semantic_id, goal_context_key,
                    evidence_fingerprint, effective_event_count, snapshot_json, computed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_profile_id, subject_id, semantic_id, goal_context_key)
                DO UPDATE SET
                    evidence_fingerprint = excluded.evidence_fingerprint,
                    effective_event_count = excluded.effective_event_count,
                    snapshot_json = excluded.snapshot_json,
                    computed_at = excluded.computed_at
                """,
                (
                    learner_profile_id,
                    subject_id,
                    semantic_id,
                    goal_key,
                    fingerprint,
                    len(events),
                    _canonical_json(result),
                    computed_at,
                ),
            )
        return result

    def load_materialized_snapshot(
        self,
        learner_profile_id: str,
        subject_id: str,
        semantic_id: str,
        *,
        goal_context: str | None,
    ) -> dict[str, Any] | None:
        row = self.connection.execute(
            """
            SELECT snapshot_json FROM materialized_snapshots
            WHERE learner_profile_id = ? AND subject_id = ? AND semantic_id = ? AND goal_context_key = ?
            """,
            (learner_profile_id, subject_id, semantic_id, goal_context or "__NONE__"),
        ).fetchone()
        return json.loads(row["snapshot_json"]) if row is not None else None

    def telemetry_summary(
        self,
        learner_profile_id: str,
        subject_id: str,
        semantic_id: str,
    ) -> dict[str, Any]:
        events = self.list_events(
            learner_profile_id,
            subject_id,
            semantic_id=semantic_id,
            effective=True,
        )
        assistance = Counter()
        transfer = Counter()
        retention = Counter()
        source_types = Counter()
        evaluator_trust = Counter()
        provenance: list[str] = []
        error_refs: list[str] = []
        independent_refs: list[str] = []
        assisted_refs: list[str] = []
        verification_refs: list[str] = []
        for event in events:
            level = event.get("assistance", {}).get("level", "UNKNOWN")
            assistance[level] += 1
            if level == "UNASSISTED":
                independent_refs.append(event["event_id"])
            else:
                assisted_refs.append(event["event_id"])
            transfer_kind = event.get("transfer_context", {}).get("kind", "NOT_APPLICABLE")
            transfer[transfer_kind] += 1
            if transfer_kind == "SAME_SESSION_VERIFICATION":
                verification_refs.append(event["event_id"])
            retention[event.get("retention_context", {}).get("kind", "NONE")] += 1
            source_types[event.get("product", {}).get("source_type", "unknown")] += 1
            evaluator_trust[event.get("evaluator", {}).get("trust_class", "unknown")] += 1
            for ref in event.get("provenance_refs", []):
                if ref not in provenance:
                    provenance.append(ref)
            if any(obs.get("precision") == "EXACT" for obs in event.get("error_observations", [])):
                error_refs.append(event["event_id"])
        return {
            "learner_profile_id": learner_profile_id,
            "subject_id": subject_id,
            "semantic_id": semantic_id,
            "effective_event_count": len(events),
            "event_refs": [event["event_id"] for event in events],
            "independent_event_refs": independent_refs,
            "assisted_event_refs": assisted_refs,
            "same_session_verification_refs": verification_refs,
            "exact_error_event_refs": error_refs,
            "assistance_levels": dict(sorted(assistance.items())),
            "transfer_kinds": dict(sorted(transfer.items())),
            "retention_kinds": dict(sorted(retention.items())),
            "product_source_types": dict(sorted(source_types.items())),
            "evaluator_trust_classes": dict(sorted(evaluator_trust.items())),
            "provenance_refs": provenance,
        }
