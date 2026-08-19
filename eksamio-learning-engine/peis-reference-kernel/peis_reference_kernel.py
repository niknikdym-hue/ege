#!/usr/bin/env python3
"""Subject-neutral, deterministic reference implementation of the Eksamio PEIS core.

This module intentionally implements transparent ordinal guardrails rather than
final statistical coefficients. Raw learner EvidenceEvent objects remain the
canonical history. Every state/mastery/readiness/retention/NBA result is
recomputable from accepted evidence plus an explicit source-reviewed graph.

It is a reference kernel for validation and product-slice integration. It is
not a production service, database, authentication layer, or subject ruleset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

INFERENCE_VERSION = "peis-reference-kernel-v0.1-ordinal-no-coefficients"
READINESS_POLICY_VERSION = "readiness-v0.1-source-gated"
RETENTION_POLICY_VERSION = "retention-schedule-v0.1-conservative-no-curve"
NBA_POLICY_VERSION = "nba-v0.1-transparent-guardrails"

UNASSISTED = "UNASSISTED"
DELAYED_RETENTION = "DELAYED_RETENTION"
SAME_SESSION_VERIFICATION = "SAME_SESSION_VERIFICATION"


@dataclass(frozen=True)
class EventView:
    event: dict[str, Any]
    target: dict[str, Any]

    @property
    def event_id(self) -> str:
        return self.event["event_id"]

    @property
    def sequence(self) -> int:
        value = self.event.get("timestamps", {}).get("server_sequence")
        return int(value) if isinstance(value, int) else 0

    @property
    def observed_at(self) -> str:
        return self.event.get("timestamps", {}).get("received_at_server") or self.event["created_at"]

    @property
    def exact(self) -> bool:
        return self.target.get("mapping_resolution") == "EXACT"

    @property
    def composite(self) -> bool:
        return self.target.get("mapping_resolution") == "COMPOSITE"

    @property
    def unassisted(self) -> bool:
        return self.event.get("assistance", {}).get("level") == UNASSISTED

    @property
    def correct(self) -> bool:
        return self.event.get("result", {}).get("correctness") is True

    @property
    def incorrect(self) -> bool:
        return self.event.get("result", {}).get("correctness") is False

    @property
    def assisted(self) -> bool:
        return not self.unassisted

    @property
    def transfer_kind(self) -> str:
        return self.event.get("transfer_context", {}).get("kind", "NOT_APPLICABLE")

    @property
    def retention_kind(self) -> str:
        return self.event.get("retention_context", {}).get("kind", "NONE")


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _sort(views: Iterable[EventView]) -> list[EventView]:
    return sorted(views, key=lambda view: (view.sequence, view.observed_at, view.event_id))


def mapped_views(events: Iterable[dict[str, Any]], semantic_id: str) -> list[EventView]:
    views: list[EventView] = []
    for event in events:
        for target in event.get("semantic_targets", []):
            if target.get("semantic_id") == semantic_id:
                views.append(EventView(event=event, target=target))
    return _sort(views)


def exact_views(events: Iterable[dict[str, Any]], semantic_id: str) -> list[EventView]:
    return [view for view in mapped_views(events, semantic_id) if view.exact]


def independent_exact_views(events: Iterable[dict[str, Any]], semantic_id: str) -> list[EventView]:
    return [view for view in exact_views(events, semantic_id) if view.unassisted]


def assisted_exact_views(events: Iterable[dict[str, Any]], semantic_id: str) -> list[EventView]:
    return [view for view in exact_views(events, semantic_id) if view.assisted]


def _semantic_registry_version(views: list[EventView]) -> str:
    if not views:
        return "unknown-semantic-registry"
    return views[-1].event["semantic_context"]["semantic_registry_version"]


def _mapping_versions(views: list[EventView]) -> list[str]:
    versions = [view.event["semantic_context"]["semantic_mapping_version"] for view in views]
    return _unique(versions) or ["unknown-mapping-version"]


def _watermark(views: list[EventView]) -> str:
    for view in reversed(views):
        watermark = view.event.get("timestamps", {}).get("server_watermark")
        if watermark:
            return watermark
    return views[-1].event_id if views else "reference-no-evidence"


def _position(views: list[EventView]) -> dict[str, Any]:
    if not views:
        return {
            "included_event_refs": ["reference-no-evidence"],
            "semantic_mapping_versions": ["unknown-mapping-version"],
        }
    return {
        "server_watermark": _watermark(views),
        "max_server_sequence": max(view.sequence for view in views),
        "included_event_refs": [view.event_id for view in views],
        "semantic_mapping_versions": _mapping_versions(views),
    }


def _computed_at(views: list[EventView]) -> str:
    return views[-1].observed_at if views else "2026-08-20T00:00:00+03:00"


def _summary(views: list[EventView]) -> dict[str, Any]:
    return {
        "accepted_event_count": len(views),
        "correct_count": sum(1 for view in views if view.correct),
        "incorrect_count": sum(1 for view in views if view.incorrect),
        "event_refs": [view.event_id for view in views],
        "last_observed_at": views[-1].observed_at if views else None,
    }


def _resolved_contradiction(independent: list[EventView]) -> bool:
    if not independent:
        return False
    latest = independent[-1]
    return latest.correct and (
        latest.transfer_kind == SAME_SESSION_VERIFICATION
        or latest.retention_kind == DELAYED_RETENTION
    )


def infer_mastery(events: Iterable[dict[str, Any]], semantic_id: str) -> dict[str, Any]:
    mapped = mapped_views(events, semantic_id)
    exact = [view for view in mapped if view.exact]
    independent = [view for view in exact if view.unassisted]
    assisted = [view for view in exact if view.assisted]
    composite = [view for view in mapped if view.composite]
    transfer = [view for view in independent if view.transfer_kind in {"SAME_PATTERN", "NEAR_TRANSFER", "BROAD_TRANSFER"}]
    retention = [view for view in independent if view.retention_kind == DELAYED_RETENTION]

    has_independent_correct = any(view.correct for view in independent)
    has_independent_incorrect = any(view.incorrect for view in independent)
    contradiction = has_independent_correct and has_independent_incorrect and not _resolved_contradiction(independent)

    latest_independent = independent[-1] if independent else None
    latest_assisted = assisted[-1] if assisted else None
    assisted_pending = bool(
        latest_assisted
        and (latest_independent is None or latest_assisted.sequence > latest_independent.sequence)
    )

    reason_codes: list[str] = []
    if independent:
        reason_codes.append("INDEPENDENT_EVIDENCE_PRESENT")
    elif assisted:
        reason_codes.append("ASSISTED_EVIDENCE_ONLY")
    if transfer:
        reason_codes.append("TRANSFER_EVIDENCE_PRESENT")
    if retention:
        reason_codes.append("DELAYED_RETENTION_PRESENT")
    if composite:
        reason_codes.append("MAPPING_PARTIAL")
    if contradiction:
        reason_codes.append("CONTRADICTORY_EVIDENCE")
    if assisted_pending:
        reason_codes.append("INDEPENDENT_VERIFICATION_REQUIRED")
    if not reason_codes:
        reason_codes.append("INDEPENDENT_VERIFICATION_REQUIRED")

    if retention and retention[-1].correct:
        band = "STRONG"
        status = "INFERRED"
        confidence_band = "HIGH"
    elif contradiction:
        band = "DEVELOPING"
        status = "INFERRED"
        confidence_band = "LOW"
    elif latest_independent is not None and latest_independent.incorrect:
        band = "EMERGING"
        status = "INFERRED"
        confidence_band = "HIGH"
    elif latest_independent is not None and latest_independent.correct:
        independent_correct_count = sum(1 for view in independent if view.correct)
        band = "ESTABLISHED" if independent_correct_count >= 2 else "DEVELOPING"
        status = "INFERRED"
        confidence_band = "HIGH" if independent_correct_count >= 2 else "MODERATE"
    elif assisted:
        band = "EMERGING"
        status = "INFERRED"
        confidence_band = "LOW"
    else:
        band = "NOT_ESTABLISHED"
        status = "INSUFFICIENT_EVIDENCE"
        confidence_band = "INSUFFICIENT"

    contradictory_refs = [view.event_id for view in independent] if contradiction else []
    contradiction_resolution = "INDEPENDENT_VERIFICATION_REQUIRED" if contradiction else "NONE_NEEDED"
    contradiction_status = "PRESENT_VERIFICATION_RECOMMENDED" if contradiction else "NONE_OBSERVED"

    learner_profile_id = mapped[-1].event["learner_profile_id"] if mapped else "learner-reference-none"
    subject_id = mapped[-1].event["subject_id"] if mapped else "unknown"

    return {
        "schema_version": "0.1.0",
        "learner_profile_id": learner_profile_id,
        "subject_id": subject_id,
        "semantic_id": semantic_id,
        "semantic_registry_version": _semantic_registry_version(mapped),
        "mastery": {"estimate": None, "band": band, "status": status},
        "system_inference": {
            "confidence": None,
            "uncertainty": None,
            "confidence_band": confidence_band,
            "reason_codes": _unique(reason_codes),
            "contradiction_status": contradiction_status,
        },
        "evidence_summaries": {
            "independent": _summary(independent),
            "assisted": _summary(assisted),
            "transfer": _summary(transfer),
            "retention": _summary(retention),
            "contradictory": {
                "observed": contradiction,
                "event_refs": contradictory_refs,
                "resolution": contradiction_resolution,
            },
        },
        "inference_version": INFERENCE_VERSION,
        "evidence_position": _position(mapped),
        "computed_at": _computed_at(mapped),
    }


def _evidence_summary_for_state(views: list[EventView]) -> dict[str, Any]:
    return {
        "accepted_event_count": len(views),
        "correct_count": sum(1 for view in views if view.correct),
        "incorrect_count": sum(1 for view in views if view.incorrect),
        "partial_count": sum(1 for view in views if view.event.get("result", {}).get("outcome") == "PARTIAL"),
        "first_event_at": views[0].observed_at if views else None,
        "last_event_at": views[-1].observed_at if views else None,
        "event_refs": [view.event_id for view in views],
    }


def infer_retention(events: Iterable[dict[str, Any]], semantic_id: str) -> dict[str, Any]:
    mapped = mapped_views(events, semantic_id)
    independent = independent_exact_views(events, semantic_id)
    delayed = [view for view in independent if view.retention_kind == DELAYED_RETENTION]
    latest_delayed = delayed[-1] if delayed else None
    latest_independent_success = next((view for view in reversed(independent) if view.correct), None)

    if latest_delayed is not None and latest_delayed.incorrect:
        current_state = "RETENTION_FAILURE_RESTABILIZATION_NEEDED"
        reason = "RETENTION_FAILURE_RESTABILIZE"
    elif latest_delayed is not None and latest_delayed.correct:
        current_state = "RETAINED_AFTER_DELAYED_CHECK"
        reason = "RETAINED_AND_RESCHEDULED"
    elif latest_independent_success is not None:
        current_state = "SCHEDULED"
        reason = "SCHEDULED_AFTER_INDEPENDENT_VERIFICATION"
    else:
        current_state = "NOT_ELIGIBLE_INSUFFICIENT_EVIDENCE"
        reason = "AWAITING_FIRST_DELAYED_CHECK"

    last_delayed_check = None
    if latest_delayed is not None:
        origin_refs = latest_delayed.event.get("transfer_context", {}).get("origin_event_refs", [])
        qualifying_ref = origin_refs[0] if origin_refs else latest_delayed.event_id
        qualifying_event = next((view.event for view in mapped if view.event_id == qualifying_ref), None)
        delay_seconds = latest_delayed.event.get("retention_context", {}).get("delay_seconds") or 1
        last_delayed_check = {
            "event_ref": latest_delayed.event_id,
            "checked_at": latest_delayed.observed_at,
            "outcome": latest_delayed.event["result"]["outcome"],
            "delay_seconds": int(delay_seconds),
            "qualifying_event_ref": qualifying_ref,
            "qualifying_session_id": qualifying_event["session_id"] if qualifying_event else "unknown-session",
            "check_session_id": latest_delayed.event["session_id"],
        }

    source_refs = [view.event_id for view in mapped] or ["reference-no-evidence"]
    learner_profile_id = mapped[-1].event["learner_profile_id"] if mapped else "learner-reference-none"
    subject_id = mapped[-1].event["subject_id"] if mapped else "unknown"

    return {
        "learner_profile_id": learner_profile_id,
        "subject_id": subject_id,
        "semantic_id": semantic_id,
        "current_state": current_state,
        "last_delayed_check": last_delayed_check,
        "history": {
            "previous_retention_successes": sum(1 for view in delayed if view.correct),
            "previous_retention_failures": sum(1 for view in delayed if view.incorrect),
            "event_refs": [view.event_id for view in delayed],
        },
        "schedule_policy_version": RETENTION_POLICY_VERSION,
        "source_evidence_refs": source_refs,
        "next_due_calculation": {
            "scheduled_at": None,
            "due_window_start": None,
            "due_window_end": None,
            "input_refs": [latest_independent_success.event_id] if latest_independent_success else source_refs,
            "reason_codes": [reason],
        },
        "computed_at": _computed_at(mapped),
    }


def _edge_applies(edge_doc: dict[str, Any], *, subject_id: str, target_semantic_id: str, goal_context: str | None) -> bool:
    edge = edge_doc.get("edge", edge_doc)
    if edge.get("target_semantic_id") != target_semantic_id:
        return False
    if edge.get("relation_type") != "REQUIRED":
        return False
    if edge.get("review_status") not in {"SOURCE_VERIFIED", "ACCEPTED"}:
        return False
    if edge.get("admission_scope") != "CANONICAL_GRAPH":
        return False
    scope = edge.get("conditional_scope") or {}
    if scope.get("subject_id") and scope["subject_id"] != subject_id:
        return False
    if scope.get("goal_context") and scope["goal_context"] != goal_context:
        return False
    return True


def _prerequisite_assessment(events: list[dict[str, Any]], edge_doc: dict[str, Any]) -> dict[str, Any]:
    edge = edge_doc.get("edge", edge_doc)
    edge_ref = edge_doc.get("edge_id", f"edge:{edge['source_semantic_id']}->{edge['target_semantic_id']}")
    semantic_id = edge["source_semantic_id"]
    mastery = infer_mastery(events, semantic_id)
    independent = independent_exact_views(events, semantic_id)
    basis = [view.event_id for view in independent]

    if mastery["evidence_summaries"]["contradictory"]["observed"]:
        state = "STALE_OR_CONTRADICTORY"
        confidence_band = "MODERATE"
    elif not independent:
        state = "UNKNOWN"
        confidence_band = "INSUFFICIENT"
    elif independent[-1].incorrect:
        state = "GAP_CONFIRMED"
        confidence_band = "HIGH"
    else:
        state = "MET"
        confidence_band = mastery["system_inference"]["confidence_band"]
        if confidence_band not in {"LOW", "MODERATE", "HIGH"}:
            confidence_band = "MODERATE"

    return {
        "edge_ref": edge_ref,
        "relation_type": edge["relation_type"],
        "state": state,
        "confidence_band": confidence_band,
        "basis_evidence_refs": basis,
    }


def assess_readiness(
    events: Iterable[dict[str, Any]],
    target_semantic_id: str,
    admitted_edges: Iterable[dict[str, Any]],
    *,
    goal_context: str | None,
    content_available: bool = True,
) -> dict[str, Any]:
    event_list = list(events)
    mapped_target = mapped_views(event_list, target_semantic_id)
    if mapped_target:
        subject_id = mapped_target[-1].event["subject_id"]
        learner_profile_id = mapped_target[-1].event["learner_profile_id"]
        semantic_registry_version = _semantic_registry_version(mapped_target)
    else:
        all_events = list(event_list)
        if not all_events:
            raise ValueError("readiness requires at least one evidence event in reference mode")
        subject_id = all_events[-1]["subject_id"]
        learner_profile_id = all_events[-1]["learner_profile_id"]
        semantic_registry_version = all_events[-1]["semantic_context"]["semantic_registry_version"]

    applicable = [
        edge_doc for edge_doc in admitted_edges
        if _edge_applies(edge_doc, subject_id=subject_id, target_semantic_id=target_semantic_id, goal_context=goal_context)
    ]
    assessments = [_prerequisite_assessment(event_list, edge_doc) for edge_doc in applicable]

    if not content_available:
        status = "CONTENT_UNAVAILABLE"
    elif any(row["state"] == "GAP_CONFIRMED" for row in assessments):
        status = "BLOCKED_BY_REQUIRED_PREREQUISITE"
    elif any(row["state"] == "STALE_OR_CONTRADICTORY" for row in assessments):
        status = "NEEDS_VERIFICATION"
    elif any(row["state"] == "UNKNOWN" for row in assessments):
        status = "INSUFFICIENT_EVIDENCE"
    else:
        target_mastery = infer_mastery(event_list, target_semantic_id)
        target_retention = infer_retention(event_list, target_semantic_id)
        if target_mastery["mastery"]["band"] == "STRONG" and target_retention["current_state"] == "RETAINED_AFTER_DELAYED_CHECK":
            status = "ALREADY_STRONG_NOT_CURRENT_PRIORITY"
        elif target_mastery["evidence_summaries"]["contradictory"]["observed"]:
            status = "NEEDS_VERIFICATION"
        else:
            status = "READY_TO_LEARN_OR_PRACTICE"

    edge_versions = [edge_doc.get("edge", edge_doc).get("graph_version") for edge_doc in applicable]
    evidence_refs = _unique(
        [ref for row in assessments for ref in row["basis_evidence_refs"]]
        + [view.event_id for view in mapped_target]
    )
    all_mapped = mapped_target[:]
    for edge_doc in applicable:
        all_mapped.extend(mapped_views(event_list, edge_doc.get("edge", edge_doc)["source_semantic_id"]))
    all_mapped = _sort(all_mapped)

    return {
        "learner_profile_id": learner_profile_id,
        "subject_id": subject_id,
        "target_semantic_id": target_semantic_id,
        "semantic_registry_version": semantic_registry_version,
        "prerequisite_graph_version": _unique([v for v in edge_versions if v])[0] if edge_versions else "reference-graph-no-required-edge-v0.1",
        "readiness_policy_version": READINESS_POLICY_VERSION,
        "status": status,
        "required_prerequisite_assessments": assessments,
        "evidence_refs": evidence_refs,
        "computed_at": _computed_at(all_mapped),
        "evidence_watermark": _watermark(all_mapped),
        "original_goal_ref": goal_context,
    }


def materialize_state(
    events: Iterable[dict[str, Any]],
    semantic_id: str,
    *,
    readiness_state: dict[str, Any] | None = None,
    retention_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event_list = list(events)
    mapped = mapped_views(event_list, semantic_id)
    exact = [view for view in mapped if view.exact]
    independent = [view for view in exact if view.unassisted]
    assisted = [view for view in exact if view.assisted]
    mastery = infer_mastery(event_list, semantic_id)
    retention_state = retention_state or infer_retention(event_list, semantic_id)

    transfer = [view for view in independent if view.transfer_kind in {"SAME_PATTERN", "NEAR_TRANSFER", "BROAD_TRANSFER"}]
    delayed = [view for view in independent if view.retention_kind == DELAYED_RETENTION]
    recent = mapped

    assistance_levels = _unique([view.event["assistance"]["level"] for view in assisted])
    error_items: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[tuple[EventView, dict[str, Any]]]] = {}
    for view in exact:
        for observation in view.event.get("error_observations", []):
            if observation.get("semantic_id") not in {None, semantic_id}:
                continue
            if observation.get("precision") != "EXACT":
                continue
            key = (observation.get("observation_type", "UNKNOWN"), observation.get("precision", "UNKNOWN"))
            grouped.setdefault(key, []).append((view, observation))
    for (observation_type, precision), rows in grouped.items():
        error_items.append({
            "fingerprint_id": f"fp:{semantic_id}:{observation_type}",
            "observation_type": observation_type,
            "confidence": rows[-1][1].get("confidence"),
            "precision": precision,
            "event_refs": [row[0].event_id for row in rows],
            "last_observed_at": rows[-1][0].observed_at,
        })

    mastery_state = {
        "estimate": mastery["mastery"]["estimate"],
        "band": mastery["mastery"]["band"],
        "status": mastery["mastery"]["status"],
        "system_confidence": mastery["system_inference"]["confidence"],
        "uncertainty": mastery["system_inference"]["uncertainty"],
    }

    last_independent_verification = next(
        (view.observed_at for view in reversed(independent) if view.transfer_kind == SAME_SESSION_VERIFICATION or view.retention_kind == DELAYED_RETENTION),
        None,
    )

    return {
        "schema_version": "0.1.0",
        "learner_profile_id": mastery["learner_profile_id"],
        "subject_id": mastery["subject_id"],
        "semantic_id": semantic_id,
        "semantic_registry_version": mastery["semantic_registry_version"],
        "mastery": mastery_state,
        "independent_evidence_summary": _evidence_summary_for_state(independent),
        "assisted_evidence_summary": {
            **_evidence_summary_for_state(assisted),
            "assistance_levels_observed": assistance_levels,
        },
        "recent_evidence_summary": {
            "window_definition": "all mapped reference-fixture evidence; production recency window not frozen",
            "event_count": len(recent),
            "independent_count": len(independent),
            "assisted_count": len(assisted),
            "event_refs": [view.event_id for view in recent],
        },
        "last_independent_verification_at": last_independent_verification,
        "last_assisted_attempt_at": assisted[-1].observed_at if assisted else None,
        "transfer_evidence_summary": {
            "same_pattern_count": sum(1 for view in transfer if view.transfer_kind == "SAME_PATTERN"),
            "near_transfer_count": sum(1 for view in transfer if view.transfer_kind == "NEAR_TRANSFER"),
            "broad_transfer_count": sum(1 for view in transfer if view.transfer_kind == "BROAD_TRANSFER"),
            "last_transfer_at": transfer[-1].observed_at if transfer else None,
            "event_refs": [view.event_id for view in transfer],
        },
        "retention_evidence_summary": {
            "delayed_check_count": len(delayed),
            "delayed_correct_count": sum(1 for view in delayed if view.correct),
            "delayed_incorrect_count": sum(1 for view in delayed if view.incorrect),
            "last_delay_seconds": delayed[-1].event.get("retention_context", {}).get("delay_seconds") if delayed else None,
            "event_refs": [view.event_id for view in delayed],
        },
        "last_retention_check_at": delayed[-1].observed_at if delayed else None,
        "retention_due_at": None,
        "prerequisite_readiness_hooks": {
            "prerequisite_graph_version": readiness_state.get("prerequisite_graph_version") if readiness_state else None,
            "prerequisite_state_refs": [row["edge_ref"] for row in readiness_state.get("required_prerequisite_assessments", [])] if readiness_state else [],
            "readiness_policy_version": readiness_state.get("readiness_policy_version") if readiness_state else None,
            "readiness_status": readiness_state.get("status") if readiness_state else None,
        },
        "error_fingerprint": error_items,
        "goal_exam_overlay_refs": [],
        "inference_version": INFERENCE_VERSION,
        "computed_at": _computed_at(mapped),
        "evidence_position": _position(mapped),
        "state_revision": len(mapped),
        "recompute_metadata": {
            "reason": "INITIAL" if len(mapped) <= 1 else "NEW_EVIDENCE",
            "previous_inference_version": None,
            "backfill_id": None,
        },
    }


def _latest_exact(events: list[dict[str, Any]], semantic_id: str, *, assisted: bool | None = None) -> EventView | None:
    views = exact_views(events, semantic_id)
    if assisted is True:
        views = [view for view in views if view.assisted]
    elif assisted is False:
        views = [view for view in views if view.unassisted]
    return views[-1] if views else None


def _repaired_required_prerequisite(events: list[dict[str, Any]], readiness_state: dict[str, Any], admitted_edges: list[dict[str, Any]]) -> bool:
    if readiness_state["status"] != "READY_TO_LEARN_OR_PRACTICE":
        return False
    edge_ids = {row["edge_ref"] for row in readiness_state["required_prerequisite_assessments"] if row["state"] == "MET"}
    for edge_doc in admitted_edges:
        edge = edge_doc.get("edge", edge_doc)
        edge_ref = edge_doc.get("edge_id", f"edge:{edge['source_semantic_id']}->{edge['target_semantic_id']}")
        if edge_ref not in edge_ids:
            continue
        independent = independent_exact_views(events, edge["source_semantic_id"])
        if any(view.incorrect for view in independent) and independent and independent[-1].correct and _resolved_contradiction(independent):
            return True
    return False


def _recommendation(
    *,
    recommendation_id: str,
    learner_profile_id: str,
    subject_id: str,
    action_type: str,
    semantic_targets: list[str],
    prerequisite_targets: list[str],
    reason_codes: list[str],
    policy_inputs: list[str],
    verification_required: bool,
    watermark: str,
    goal_context: str | None,
    content_refs: list[str],
    computed_at: str,
) -> dict[str, Any]:
    return {
        "recommendation_id": recommendation_id,
        "learner_profile_id": learner_profile_id,
        "subject_id": subject_id,
        "action_type": action_type,
        "semantic_targets": semantic_targets,
        "prerequisite_targets": prerequisite_targets,
        "reason_codes": _unique(reason_codes),
        "priority": {"band": "NORMAL", "policy_inputs_used": _unique(policy_inputs)},
        "estimated_minutes": None,
        "route": {"product_or_mode": "reference_fixture", "content_refs": content_refs},
        "verification_required": verification_required,
        "created_at": computed_at,
        "expires_at": None,
        "nba_policy_version": NBA_POLICY_VERSION,
        "learner_state_watermark": watermark,
        "source_goal_context_refs": [goal_context] if goal_context else [],
    }


def select_nba(
    events: Iterable[dict[str, Any]],
    target_semantic_id: str,
    admitted_edges: Iterable[dict[str, Any]],
    *,
    goal_context: str | None,
    meaningful_help_delivered_for: Iterable[str] = (),
    recommendation_id: str = "nba.reference.0001",
    content_available: bool = True,
) -> dict[str, Any]:
    event_list = list(events)
    edge_list = list(admitted_edges)
    mastery = infer_mastery(event_list, target_semantic_id)
    retention = infer_retention(event_list, target_semantic_id)
    readiness = assess_readiness(
        event_list,
        target_semantic_id,
        edge_list,
        goal_context=goal_context,
        content_available=content_available,
    )
    learner_profile_id = mastery["learner_profile_id"]
    subject_id = mastery["subject_id"]
    computed_at = mastery["computed_at"]
    watermark = readiness["evidence_watermark"]
    helped = set(meaningful_help_delivered_for)

    def make(action: str, targets: list[str], reasons: list[str], inputs: list[str], *, prereqs: list[str] | None = None, verify: bool = True) -> dict[str, Any]:
        refs = [f"{action.lower()}:{semantic_id}" for semantic_id in (prereqs or targets)]
        return _recommendation(
            recommendation_id=recommendation_id,
            learner_profile_id=learner_profile_id,
            subject_id=subject_id,
            action_type=action,
            semantic_targets=targets,
            prerequisite_targets=prereqs or [],
            reason_codes=reasons,
            policy_inputs=inputs,
            verification_required=verify,
            watermark=watermark,
            goal_context=goal_context,
            content_refs=refs,
            computed_at=computed_at,
        )

    if retention["current_state"] == "RETENTION_FAILURE_RESTABILIZATION_NEEDED":
        return make("GUIDED_PRACTICE", [target_semantic_id], ["RETENTION_FAILURE_RESTABILIZE"], ["RETENTION_STATE", "RECENT_ERRORS", "READINESS"])

    if readiness["status"] == "BLOCKED_BY_REQUIRED_PREREQUISITE":
        prereqs = []
        for row in readiness["required_prerequisite_assessments"]:
            if row["state"] != "GAP_CONFIRMED":
                continue
            for edge_doc in edge_list:
                edge = edge_doc.get("edge", edge_doc)
                edge_ref = edge_doc.get("edge_id", f"edge:{edge['source_semantic_id']}->{edge['target_semantic_id']}")
                if edge_ref == row["edge_ref"]:
                    prereqs.append(edge["source_semantic_id"])
        return make(
            "LEARN_PREREQUISITE", [target_semantic_id],
            ["PREREQUISITE_BLOCKS_TARGET", "PREREQUISITE_REPAIR_FOR_ORIGINAL_GOAL"],
            ["LEARNER_GOAL", "READINESS", "CONTENT_AVAILABILITY"], prereqs=_unique(prereqs),
        )

    if readiness["status"] == "NEEDS_VERIFICATION":
        return make("VERIFY_UNCERTAIN_STATE", [target_semantic_id], ["CONTRADICTORY_EVIDENCE_NEEDS_VERIFICATION"], ["SYSTEM_CONFIDENCE", "READINESS", "RECENT_ERRORS"])

    if readiness["status"] == "INSUFFICIENT_EVIDENCE":
        unknown_prereqs: list[str] = []
        for row in readiness["required_prerequisite_assessments"]:
            if row["state"] != "UNKNOWN":
                continue
            for edge_doc in edge_list:
                edge = edge_doc.get("edge", edge_doc)
                edge_ref = edge_doc.get("edge_id", f"edge:{edge['source_semantic_id']}->{edge['target_semantic_id']}")
                if edge_ref == row["edge_ref"]:
                    unknown_prereqs.append(edge["source_semantic_id"])
        targets = _unique(unknown_prereqs) or [target_semantic_id]
        return make("DIAGNOSE_TARGET", targets, ["STATE_UNCERTAIN_NEEDS_DIAGNOSTIC"], ["LEARNER_GOAL", "SYSTEM_CONFIDENCE", "READINESS"])

    if target_semantic_id in helped:
        return make("INDEPENDENT_PRACTICE", [target_semantic_id], ["INDEPENDENT_VERIFICATION_REQUIRED_AFTER_HELP"], ["ASSISTANCE_DEPENDENCE", "READINESS", "CONTENT_AVAILABILITY"])

    latest_assisted = _latest_exact(event_list, target_semantic_id, assisted=True)
    latest_independent = _latest_exact(event_list, target_semantic_id, assisted=False)
    if latest_assisted is not None and (latest_independent is None or latest_assisted.sequence > latest_independent.sequence):
        return make("INDEPENDENT_PRACTICE", [target_semantic_id], ["INDEPENDENT_VERIFICATION_REQUIRED_AFTER_HELP"], ["ASSISTANCE_DEPENDENCE", "READINESS"])

    if mastery["evidence_summaries"]["contradictory"]["observed"]:
        return make("VERIFY_UNCERTAIN_STATE", [target_semantic_id], ["CONTRADICTORY_EVIDENCE_NEEDS_VERIFICATION"], ["SYSTEM_CONFIDENCE", "RECENT_ERRORS", "READINESS"])

    if mastery["mastery"]["status"] == "INSUFFICIENT_EVIDENCE":
        if _repaired_required_prerequisite(event_list, readiness, edge_list):
            return make("GUIDED_PRACTICE", [target_semantic_id], ["TARGET_READY_TO_LEARN"], ["LEARNER_GOAL", "READINESS", "CONTENT_AVAILABILITY"])
        return make("DIAGNOSE_TARGET", [target_semantic_id], ["STATE_UNCERTAIN_NEEDS_DIAGNOSTIC"], ["LEARNER_GOAL", "SYSTEM_CONFIDENCE", "READINESS"])

    if latest_independent is not None and latest_independent.incorrect:
        return make("GUIDED_PRACTICE", [target_semantic_id], ["LOW_MASTERY_HIGH_CONFIDENCE", "TARGET_READY_TO_LEARN"], ["SYSTEM_CONFIDENCE", "READINESS", "RECENT_ERRORS"])

    if retention["current_state"] in {"SCHEDULED", "DUE", "OVERDUE"} and latest_independent is not None and latest_independent.correct:
        reasons = ["RETENTION_OVERDUE"] if retention["current_state"] == "OVERDUE" else ["RETENTION_DUE"]
        return make("RETENTION_REVIEW", [target_semantic_id], reasons, ["RETENTION_STATE", "LEARNER_GOAL"], verify=True)

    if readiness["status"] == "ALREADY_STRONG_NOT_CURRENT_PRIORITY" or retention["current_state"] == "RETAINED_AFTER_DELAYED_CHECK":
        return make("MOVE_TO_NEXT_TARGET", [target_semantic_id], ["ALREADY_STRONG_RETAINED"], ["READINESS", "RETENTION_STATE"], verify=False)

    return make("GUIDED_PRACTICE", [target_semantic_id], ["TARGET_READY_TO_LEARN"], ["READINESS", "CONTENT_AVAILABILITY"])


def snapshot(
    events: Iterable[dict[str, Any]],
    target_semantic_id: str,
    admitted_edges: Iterable[dict[str, Any]],
    *,
    goal_context: str | None,
    meaningful_help_delivered_for: Iterable[str] = (),
    recommendation_id: str = "nba.reference.0001",
) -> dict[str, Any]:
    event_list = list(events)
    edge_list = list(admitted_edges)
    mastery = infer_mastery(event_list, target_semantic_id)
    retention = infer_retention(event_list, target_semantic_id)
    readiness = assess_readiness(event_list, target_semantic_id, edge_list, goal_context=goal_context)
    state = materialize_state(event_list, target_semantic_id, readiness_state=readiness, retention_state=retention)
    nba = select_nba(
        event_list,
        target_semantic_id,
        edge_list,
        goal_context=goal_context,
        meaningful_help_delivered_for=meaningful_help_delivered_for,
        recommendation_id=recommendation_id,
    )
    return {"mastery": mastery, "readiness": readiness, "retention": retention, "state": state, "nba": nba}
