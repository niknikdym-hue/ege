#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from accepted_russian_semantic_tutor import (  # noqa: E402
    AcceptedRussianSemanticAllowlist,
    AcceptedSemanticGroundedTextProvider,
    AcceptedSemanticRussianTutorVerticalSlice,
    TutorSemanticNotAccepted,
)
from reliability_gateway import ProviderPath, ReliabilityGateway  # noqa: E402
from sep1_russian_tutor import MockSpeechProvider, VoiceGateway  # noqa: E402

# These 19 semantics were the first accepted private-staging slice. They must
# remain available, but they are no longer treated as the complete denominator.
MUST_RETAIN = {
    "ru-ege-essay-author-position",
    "ru-ege-essay-source-examples-explanation",
    "ru-ege-essay-example-semantic-relation",
    "ru-ege-essay-own-relation-justification",
    "ru-ege-essay-logical-composition-cohesion",
    "ru-expressive-alliteration",
    "ru-expressive-personification",
    "ru-expressive-syntactic-parallelism",
    "ru-expressive-question-answer-form",
    "ru-expressive-gradation",
    "ru-expressive-inversion",
    "ru-expressive-lexical-repetition",
    "ru-expressive-epiphora",
    "ru-expressive-antithesis",
    "ru-expressive-rhetorical-question",
    "ru-expressive-rhetorical-exclamation",
    "ru-expressive-polysyndeton",
    "ru-expressive-asyndeton",
    "ru-expressive-litotes",
}
REJECTED = {
    "candidate-039",
    "school-ne-verb-gerund-spelling-base",
    "ru-not-accepted-fixture",
}


def build_text_gateway() -> tuple[ReliabilityGateway, AcceptedSemanticGroundedTextProvider]:
    provider = AcceptedSemanticGroundedTextProvider("accepted-semantic-text-fixture")
    registry = {
        (provider.provider_id, "text"): ProviderPath(
            provider.provider_id,
            "text",
            "fixture-v1",
            "PRODUCTION_ADMITTED",
            1,
        )
    }
    return ReliabilityGateway(registry, {provider.provider_id: provider}), provider


def main() -> int:
    allowlist = AcceptedRussianSemanticAllowlist(ENGINE)
    actual = set(allowlist.semantic_ids)
    if len(actual) != allowlist.expected_semantic_count:
        raise AssertionError(
            f"Tutor accepted-semantic denominator drift: {len(actual)} != {allowlist.expected_semantic_count}"
        )
    if not MUST_RETAIN.issubset(actual):
        raise AssertionError(f"Tutor lost previously accepted semantics: {sorted(MUST_RETAIN - actual)}")

    for semantic_id in sorted(actual):
        grounding = allowlist.require(semantic_id)
        if grounding.semantic_id != semantic_id:
            raise AssertionError(f"Tutor allowlist semantic mismatch: {semantic_id}")
        if not grounding.source_ref.startswith("source:russian-accepted-semantic:"):
            raise AssertionError(f"Tutor allowlist source ref drift: {semantic_id}")
        if "Проверенное объяснение:" not in grounding.verified_excerpt:
            raise AssertionError(f"Tutor verified excerpt missing explanation: {semantic_id}")
        if "Границы:" not in grounding.verified_excerpt or "Алгоритм:" not in grounding.verified_excerpt:
            raise AssertionError(f"Tutor verified excerpt missing boundary/algorithm: {semantic_id}")

    for semantic_id in REJECTED:
        try:
            allowlist.require(semantic_id)
        except TutorSemanticNotAccepted:
            pass
        else:
            raise AssertionError(f"Tutor fail-closed allowlist accepted forbidden semantic: {semantic_id}")

    text_gateway, text_provider = build_text_gateway()
    speech = MockSpeechProvider(
        "accepted-semantic-voice-fixture",
        transcript="Объясни, как отличить градацию от обычного перечисления.",
    )
    tutor = AcceptedSemanticRussianTutorVerticalSlice(
        engine_root=ENGINE,
        text_gateway=text_gateway,
        voice_gateway=VoiceGateway([speech]),
        session_ref_factory=lambda: "tutor:accepted-semantic-private-staging-fixture",
    )
    state = tutor.open_semantic_session(
        learner_profile_id="learner:private-staging-fixture",
        semantic_id="ru-expressive-gradation",
    )
    if state.grounding.semantic_id != "ru-expressive-gradation":
        raise AssertionError("Tutor semantic session grounded in wrong target")

    text_turn = tutor.text_turn(state.session_ref, "Объясни правило и его границу.")
    if text_turn.reliable_result.status != "TUTOR_ADVISORY":
        raise AssertionError("accepted-semantic Tutor text turn is not advisory")
    if "принятую предметную семантику Eksamio" not in text_turn.tutor_text:
        raise AssertionError("Tutor text did not use accepted-semantic deterministic grounding")

    transient_audio = b"TRANSIENT_LEARNER_AUDIO_PRIVATE_STAGING_FIXTURE"
    voice_turn = tutor.voice_turn(state.session_ref, transient_audio)
    if voice_turn.session_ref != state.session_ref or voice_turn.modality != "voice":
        raise AssertionError("Tutor text/voice continuity failed")
    if not isinstance(voice_turn.audio, bytes) or not voice_turn.audio:
        raise AssertionError("Tutor voice fixture did not return transient audio")
    if state.raw_audio_persistence_count() != 0:
        raise AssertionError("Tutor state persisted raw/generated audio bytes")
    if state.raw_audio_inputs_seen != 1 or state.synthesized_audio_outputs_seen != 1:
        raise AssertionError("Tutor voice counters drift")
    if text_provider.calls != 2:
        raise AssertionError("Tutor text provider call count drift")

    try:
        tutor.open_semantic_session(
            learner_profile_id="learner:private-staging-rejected",
            semantic_id="ru-not-accepted-fixture",
        )
    except TutorSemanticNotAccepted:
        pass
    else:
        raise AssertionError("Tutor opened a session on an unaccepted semantic")

    evidence = {
        "accepted_semantics": sorted(actual),
        "accepted_count": len(actual),
        "canonical_authority_count": len(allowlist.authority_specs),
        "canonical_expected_semantic_count": allowlist.expected_semantic_count,
        "retained_original_slice": len(MUST_RETAIN),
        "rejected_fixture_count": len(REJECTED),
        "text_voice_same_session": True,
        "raw_audio_persisted_bytes": 0,
        "provider_network_requests": 0,
        "paid_provider_requests": 0,
        "public_traffic": False,
    }
    digest = hashlib.sha256(
        json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    print("ACCEPTED_RUSSIAN_SEMANTIC_TUTOR=PASS")
    print(f"ACCEPTED_SEMANTICS={len(actual)}")
    print(f"CANONICAL_AUTHORITY_FILES={len(allowlist.authority_specs)}")
    print(f"CANONICAL_EXPECTED_SEMANTICS={allowlist.expected_semantic_count}")
    print("ORIGINAL_19_SEMANTICS_RETAINED=PASS")
    print("UNACCEPTED_SEMANTIC_SESSION=DENIED")
    print("TEXT_VOICE_SAME_SESSION=PASS")
    print("RAW_AUDIO_PERSISTED_BYTES=0")
    print("PROVIDER_NETWORK_REQUESTS=0")
    print("PAID_PROVIDER_REQUESTS=0")
    print(f"EVIDENCE_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
