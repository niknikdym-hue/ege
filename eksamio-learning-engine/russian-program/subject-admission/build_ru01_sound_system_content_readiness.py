#!/usr/bin/env python3
"""Fail-closed readiness validator for the bounded RU01 whole sound-system candidate.

This gate does not admit a semantic, close an object, or emit mastery.  It only
checks that the exact source-bound integrated learner-content candidate is ready
for a separate content-adequacy review.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
CANDIDATE = (
    HERE.parent
    / "production-learning-content"
    / "RU-PROG-01-SOUND-SYSTEM-INTEGRATION-WAVE-010-v0.1.json"
)
EXPECTED_GIT_BLOB = "aeba08fe00dbe5626748427e2792e196976b8256"
EXPECTED_SOURCE_CLAUSE = "EDSOO59-P181-4.1-C"
EXPECTED_SEMANTIC = "ru-phonetics-sound-system"
EXPECTED_EVIDENCE_IDS = [f"p01-u12-v{i}" for i in range(1, 6)]
FORBIDDEN_PARENT_EVIDENCE_PREFIXES = ("p01-u9-v", "p01-u10-v")
PREREQUISITE = {
    "workflow": "Russian RU01 sound system exact component-set review",
    "run_id": 34510774242,
    "head_sha": "03397a71a723bed3df27aa27a9e60b2b386e120a",
    "conclusion": "SUCCESS",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def git_blob_sha(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def first_dict_with_key(value: Any, key: str) -> dict[str, Any] | None:
    for node in walk(value):
        if key in node:
            return node
    return None


def all_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from all_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_strings(child)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def main() -> None:
    raw = CANDIDATE.read_bytes()
    actual_blob = git_blob_sha(raw)
    require(actual_blob == EXPECTED_GIT_BLOB, f"candidate blob drift: {actual_blob}")

    data = json.loads(raw.decode("utf-8"))
    require(data.get("status") == "CONTENT_AND_EVIDENCE_READY_SEMANTIC_ACCEPTANCE_REQUIRED", "unexpected candidate status")
    require(data.get("subject") == "russian", "subject drift")
    require(data.get("module_id") == "RU-PROG-01", "module drift")

    provenance = data.get("source_provenance")
    require(isinstance(provenance, list), "source_provenance missing")
    provenance_text = json.dumps(provenance, ensure_ascii=False, sort_keys=True)
    require(EXPECTED_SOURCE_CLAUSE in provenance_text, "exact source clause missing")
    require(EXPECTED_SEMANTIC in provenance_text, "proposed whole-system semantic missing from provenance")
    for key, expected in PREREQUISITE.items():
        require(str(expected) in provenance_text, f"prerequisite pin missing: {key}")

    identity = data.get("identity_boundary")
    require(isinstance(identity, dict), "identity_boundary missing")
    require(identity.get("proposed_semantic_id") == EXPECTED_SEMANTIC, "semantic identity drift")
    require(identity.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "candidate became canonical before acceptance")
    require(identity.get("proposed_item_identity_prefix") == "p01-u12", "item lineage drift")
    require(identity.get("vowel_system_semantic_may_substitute_parent") is False, "vowel system may not substitute parent")
    require(identity.get("consonant_system_semantic_may_substitute_parent") is False, "consonant system may not substitute parent")
    require(identity.get("sound_characterization_semantic_may_substitute_parent") is False, "sound characterization may not substitute parent")
    require(identity.get("sound_letter_relation_semantic_may_substitute_parent") is False, "sound-letter relation may not substitute parent")
    require(identity.get("normative_pronunciation_semantic_may_substitute_parent") is False, "pronunciation may not substitute parent")
    require(identity.get("normative_stress_semantic_may_substitute_parent") is False, "stress may not substitute parent")
    require(identity.get("existing_p01_u9_or_u10_evidence_may_be_reused_as_parent_evidence") is False, "component evidence reuse must stay forbidden")
    require(identity.get("generic_ru01_result_can_emit_exact_sound_system_mastery") is False, "generic RU01 exact mastery must stay forbidden")

    units = data.get("units")
    require(isinstance(units, list) and len(units) == 1, "expected one bounded sound-system unit")
    unit = units[0]
    require(unit.get("proposed_semantic_id") == EXPECTED_SEMANTIC, "unit semantic drift")

    verification = unit.get("independent_verification")
    require(isinstance(verification, list) and len(verification) == 5, "expected exactly five independent verification items")
    ids = [item.get("id") for item in verification if isinstance(item, dict)]
    require(ids == EXPECTED_EVIDENCE_IDS, f"verification lineage mismatch: {ids}")
    require(len(set(ids)) == 5, "verification identities must be distinct")
    for item in verification:
        require(item.get("exact_item_identity_required") is True, f"exact item identity missing for {item.get('id')}")
        require(item.get("registered_user_identity_ref_required") is True, f"registered identity missing for {item.get('id')}")
        require(item.get("received_at_server_required") is True, f"server timestamp missing for {item.get('id')}")

    # The candidate must actually integrate both subsystems while preserving the
    # spelling/sound and orthoepy boundaries.  The exact blob pin above prevents
    # later wording drift from silently satisfying these coarse semantic guards.
    text = "\n".join(all_strings(data)).lower()
    for token in ("гласн", "согласн", "букв", "произнош", "ударен"):
        require(token in text, f"integrated boundary token missing: {token}")

    peis_holder = first_dict_with_key(data, "peis_evidence")
    require(peis_holder is not None, "peis_evidence missing")
    peis = peis_holder["peis_evidence"]
    require(isinstance(peis, dict), "peis_evidence malformed")
    require(peis.get("semantic_ref") == EXPECTED_SEMANTIC, "PEIS semantic drift")
    require(peis.get("semantic_ref_status") == "PROPOSED_NOT_CANONICAL", "PEIS semantic became canonical before acceptance")
    require(peis.get("independent_verification_required") is True, "independent verification must be required")
    require(peis.get("assistance_must_be_recorded") is True, "assistance recording must be required")
    require(peis.get("user_identity_ref") == "REGISTERED_USER_REQUIRED", "registered learner boundary missing")
    require(peis.get("item_identity") == "EXACT_VERSIONED_ITEM_REQUIRED", "versioned item boundary missing")
    require(peis.get("received_at") == "SERVER_OWNED_TIMESTAMP_REQUIRED", "server-owned received_at boundary missing")
    require(peis.get("today_timezone") == "Europe/Moscow", "Today timezone drift")
    require(peis.get("durable_evidence_event_required") is True, "durable EvidenceEvent must be required")
    require(peis.get("durable_outbox_required") is True, "durable outbox must be required")
    require(peis.get("mastery_before_separate_semantic_acceptance") is False, "mastery before acceptance must be forbidden")
    require(peis.get("generic_ru01_attempt_can_emit_exact_mastery") is False, "generic exact mastery must be forbidden")
    require(peis.get("anonymous_progress_allowed") is False, "anonymous progress must be forbidden")
    require(peis.get("device_only_canonical_state_allowed") is False, "device-only canonical state must be forbidden")

    boundary = data.get("admission_boundary")
    require(isinstance(boundary, dict), "admission_boundary missing")
    expected_zero = {
        "semantic_admissions": 0,
        "object_level_closures": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }
    for key, expected in expected_zero.items():
        require(boundary.get(key) == expected, f"{key} must remain zero")

    # Old vowel/consonant evidence can be mentioned only as explicitly non-reusable
    # component evidence.  New whole-system proof is exclusively p01-u12-v1..v5.
    require(identity.get("existing_p01_u9_or_u10_evidence_may_be_reused_as_parent_evidence") is False, "old component evidence reuse boundary missing")
    provenance_refs = set()
    for node in walk(provenance):
        refs = node.get("existing_component_evidence_refs")
        if isinstance(refs, list):
            provenance_refs.update(str(ref) for ref in refs)
    require(any(ref.startswith(FORBIDDEN_PARENT_EVIDENCE_PREFIXES[0]) for ref in provenance_refs), "p01-u9 component evidence inventory missing")
    require(any(ref.startswith(FORBIDDEN_PARENT_EVIDENCE_PREFIXES[1]) for ref in provenance_refs), "p01-u10 component evidence inventory missing")

    result = {
        "status": "READY_FOR_CONTENT_ADEQUACY_REVIEW",
        "subject": "russian",
        "module_id": "RU-PROG-01",
        "candidate": str(CANDIDATE.relative_to(HERE.parent.parent)),
        "candidate_git_blob_sha": actual_blob,
        "source_clause_id": EXPECTED_SOURCE_CLAUSE,
        "proposed_semantic_id": EXPECTED_SEMANTIC,
        "independent_evidence_refs": EXPECTED_EVIDENCE_IDS,
        "independent_evidence_count": 5,
        "prerequisite": PREREQUISITE,
        "semantic_admissions": 0,
        "object_level_closures": 0,
        "exact_mastery_admissions": 0,
        "false_exact_mastery_admissions": 0,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
