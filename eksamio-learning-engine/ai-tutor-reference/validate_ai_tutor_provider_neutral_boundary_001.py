#!/usr/bin/env python3
"""Deterministically validate the T0 provider-neutral AI Tutor boundary."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from fake_providers import (  # noqa: E402
    EquivalentGroundedFakeProvider,
    GroundedFakeProvider,
    HostileFakeProvider,
    MalformedFakeProvider,
    UnavailableFakeProvider,
)
from tutor_boundary import (  # noqa: E402
    REJECTED_SOURCE_REF,
    REJECTED_TOOL_INTENT,
    TUTOR_ADVISORY,
    TUTOR_UNAVAILABLE,
    PeisContextProjection,
    ServerTutorTurn,
    SystemPolicy,
    TutorHistoryEntry,
    TutorOrchestrator,
    VerifiedSubjectContext,
    _provider_request,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS assertion: {message}")


def turn() -> ServerTutorTurn:
    return ServerTutorTurn(
        tutor_session_ref="tutor:opaque-episode-001",
        subject_id="russian",
        learning_goal="resolve spelling uncertainty",
        policy=SystemPolicy(True, ("open_verified_explanation",)),
        verified_subject=VerifiedSubjectContext(
            ("source:ru-rule-001",), ("Verified source excerpt.",)
        ),
        peis_projection=PeisContextProjection(
            "peis-context-projection.v1", "Needs an independent check after help.", ("school:rule-001",)
        ),
        history=(TutorHistoryEntry("tutor", "Предыдущий проверенный шаг."),),
        learner_text="Почему здесь такое написание?",
    )


def canonical_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(asdict(value), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def main() -> int:
    sample = turn()
    minimized = _provider_request(sample)
    request_json = json.dumps(asdict(minimized), ensure_ascii=False, sort_keys=True)
    forbidden_identity_and_secret_terms = (
        "learner_profile_id", "email", "phone", "payment", "auth_token", "session_secret", "database_row"
    )
    require(all(term not in request_json for term in forbidden_identity_and_secret_terms), "minimized provider request excludes identity, contact, secret, payment, and raw-row data")
    require(minimized.verified_source_refs == ("source:ru-rule-001",) and minimized.learner_text == sample.learner_text, "verified source and untrusted learner text remain separate contract fields")

    first = TutorOrchestrator(GroundedFakeProvider()).handle_turn(sample)
    swapped = TutorOrchestrator(EquivalentGroundedFakeProvider()).handle_turn(sample)
    require(first.status == swapped.status == TUTOR_ADVISORY, "two fake providers swap under unchanged orchestrator public contract")
    require(first.accepted_source_refs == ("source:ru-rule-001",), "allowed verified source reference is retained")
    require(tuple(intent.name for intent in first.mediated_tool_intents) == ("open_verified_explanation",), "allowed tool intent is normalized and only server-mediated")

    hostile = TutorOrchestrator(HostileFakeProvider()).handle_turn(sample)
    require(hostile.canonical_peis_writes == 0, "provider boundary performs no canonical PEIS write")
    require("REJECTED_CANONICAL_STATE_MUTATION" in hostile.flags, "correctness/mastery/readiness/retention/NBA/identity/entitlement mutation attempts are rejected")
    require(hostile.verification_required is True and "REJECTED_VERIFICATION_DOWNGRADE" in hostile.flags, "provider cannot clear server-required independent verification")
    require(hostile.mediated_tool_intents == () and REJECTED_TOOL_INTENT in hostile.flags, "unknown tool intent is rejected without execution")
    require(hostile.accepted_source_refs == () and REJECTED_SOURCE_REF in hostile.flags, "invented provider source reference is rejected")

    for provider in (UnavailableFakeProvider(), MalformedFakeProvider()):
        result = TutorOrchestrator(provider).handle_turn(sample)
        require(result.status == TUTOR_UNAVAILABLE and result.canonical_peis_writes == 0, f"{provider.provider_id} returns stable Tutor-unavailable without PEIS corruption")

    contract_source = (HERE / "tutor_boundary.py").read_text(encoding="utf-8")
    require(all(term not in contract_source for term in ("voiceprint", "acoustic", "recording", "blob", "embedding")), "reference contract has no learner audio persistence field or path")
    digest_one = canonical_digest(first)
    digest_two = canonical_digest(TutorOrchestrator(GroundedFakeProvider()).handle_turn(sample))
    require(digest_one == digest_two, f"repeated deterministic run has identical canonical result hash {digest_one}")
    print("AI_TUTOR_PROVIDER_NEUTRAL_BOUNDARY_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
