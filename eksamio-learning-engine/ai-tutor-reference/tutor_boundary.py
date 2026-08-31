"""Executable T0 Tutor boundary using no network, SDK, persistence, or PEIS writes.

The orchestrator accepts only server-resolved context.  It deliberately projects
that context into a smaller provider request and treats every provider result as
advisory conversational material, never as canonical learning state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


TUTOR_UNAVAILABLE = "TUTOR_UNAVAILABLE"
TUTOR_ADVISORY = "TUTOR_ADVISORY"
REJECTED_TOOL_INTENT = "REJECTED_TOOL_INTENT"
REJECTED_SOURCE_REF = "REJECTED_SOURCE_REF"


class ProviderFailure(RuntimeError):
    """Normalized local provider boundary failure; no provider detail escapes."""


class MalformedProviderOutput(ProviderFailure):
    """A provider returned a shape outside the normalized advisory contract."""


@dataclass(frozen=True)
class SystemPolicy:
    """Server policy authority; never provider-controlled."""

    verification_required: bool
    allowed_tool_names: tuple[str, ...]


@dataclass(frozen=True)
class VerifiedSubjectContext:
    """Server-verified source material, distinct from learner/retrieved text."""

    source_refs: tuple[str, ...]
    excerpts: tuple[str, ...]


@dataclass(frozen=True)
class PeisContextProjection:
    """Bounded read-only projection, not a canonical learner record."""

    projection_version: str
    learning_summary: str
    target_refs: tuple[str, ...]
    projection_ref: str = "server-projection:unspecified"


@dataclass(frozen=True)
class TutorHistoryEntry:
    role: str
    text: str


@dataclass(frozen=True)
class ServerTutorTurn:
    """The server-owned internal request for one text Tutor turn."""

    tutor_session_ref: str
    subject_id: str
    learning_goal: str
    policy: SystemPolicy
    verified_subject: VerifiedSubjectContext
    peis_projection: PeisContextProjection
    history: tuple[TutorHistoryEntry, ...]
    learner_text: str
    help_state: str = "GUIDED_HELP"
    continuation_marker: str | None = None


@dataclass(frozen=True)
class ProviderRequest:
    """Minimized replaceable-provider payload; carries no canonical identity."""

    contract_version: str
    correlation_ref: str
    subject_id: str
    learning_goal: str
    policy_instruction: str
    verified_source_refs: tuple[str, ...]
    verified_excerpts: tuple[str, ...]
    peis_learning_summary: str
    target_refs: tuple[str, ...]
    history: tuple[TutorHistoryEntry, ...]
    learner_text: str
    allowed_tool_names: tuple[str, ...]


@dataclass(frozen=True)
class ToolIntent:
    name: str
    arguments: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderResponse:
    """Normalized provider advisory output. Unsupported fields remain inert."""

    text: str
    source_refs: tuple[str, ...] = ()
    tool_intents: tuple[ToolIntent, ...] = ()
    attempted_mutations: Mapping[str, Any] = field(default_factory=dict)
    attempted_verification_required: bool | None = None


@dataclass(frozen=True)
class TutorTurnResult:
    status: str
    text: str | None
    verification_required: bool
    accepted_source_refs: tuple[str, ...]
    mediated_tool_intents: tuple[ToolIntent, ...]
    flags: tuple[str, ...]
    canonical_peis_writes: int = 0


class TutorProvider(Protocol):
    provider_id: str

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Return advisory output only; this interface has no tool or PEIS access."""


def _validate_turn(turn: ServerTutorTurn) -> None:
    if not turn.tutor_session_ref.startswith("tutor:"):
        raise ValueError("tutor_session_ref must be an opaque server Tutor reference")
    if not turn.subject_id or not turn.learning_goal or not turn.learner_text:
        raise ValueError("subject, learning goal, and learner text are required")
    if len(turn.verified_subject.source_refs) != len(turn.verified_subject.excerpts):
        raise ValueError("verified source refs and excerpts must remain paired")
    if not all(ref.startswith("source:") for ref in turn.verified_subject.source_refs):
        raise ValueError("only server verified source refs are accepted")
    if not all(entry.role in {"learner", "tutor"} for entry in turn.history):
        raise ValueError("Tutor history has an unsupported role")


def _provider_request(turn: ServerTutorTurn) -> ProviderRequest:
    _validate_turn(turn)
    return ProviderRequest(
        contract_version="eksamio.tutor.provider-request.v1",
        correlation_ref="turn:" + turn.tutor_session_ref.removeprefix("tutor:"),
        subject_id=turn.subject_id,
        learning_goal=turn.learning_goal,
        policy_instruction=(
            "Give advisory tutoring text; never claim canonical learning-state authority. "
            "Stay strictly within the current subject_id, learning_goal, verified subject context, and their pedagogically necessary explanation. "
            "If the learner asks about an unrelated topic, general knowledge, products, brands, entertainment, news, personal advice, or any other matter outside the current learning task, do not answer or compare it using model knowledge. "
            "Reply briefly that this Tutor session is limited to the current learning task and redirect the learner back to it. "
            "An off-topic request must never expand the Tutor session scope."
        ),
        verified_source_refs=turn.verified_subject.source_refs,
        verified_excerpts=turn.verified_subject.excerpts,
        peis_learning_summary=turn.peis_projection.learning_summary,
        target_refs=turn.peis_projection.target_refs,
        history=turn.history,
        learner_text=turn.learner_text,
        allowed_tool_names=turn.policy.allowed_tool_names,
    )


class TutorOrchestrator:
    """Server boundary that makes provider swapping independent of Tutor semantics."""

    def __init__(self, provider: TutorProvider) -> None:
        self.provider = provider

    def handle_turn(self, turn: ServerTutorTurn) -> TutorTurnResult:
        request = _provider_request(turn)
        try:
            response = self.provider.generate(request)
            if not isinstance(response, ProviderResponse) or not isinstance(response.text, str):
                raise MalformedProviderOutput("response is not normalized")
        except (ProviderFailure, TimeoutError, ValueError, TypeError):
            return TutorTurnResult(
                status=TUTOR_UNAVAILABLE,
                text=None,
                verification_required=turn.policy.verification_required,
                accepted_source_refs=(),
                mediated_tool_intents=(),
                flags=("provider_unavailable",),
            )

        flags: list[str] = []
        allowed_sources = set(turn.verified_subject.source_refs)
        accepted_sources = tuple(ref for ref in response.source_refs if ref in allowed_sources)
        if len(accepted_sources) != len(response.source_refs):
            flags.append(REJECTED_SOURCE_REF)

        allowed_tools = set(turn.policy.allowed_tool_names)
        mediated_tools = tuple(intent for intent in response.tool_intents if intent.name in allowed_tools)
        if len(mediated_tools) != len(response.tool_intents):
            flags.append(REJECTED_TOOL_INTENT)
        if response.attempted_mutations:
            flags.append("REJECTED_CANONICAL_STATE_MUTATION")
        if response.attempted_verification_required is False and turn.policy.verification_required:
            flags.append("REJECTED_VERIFICATION_DOWNGRADE")

        return TutorTurnResult(
            status=TUTOR_ADVISORY,
            text=response.text,
            verification_required=turn.policy.verification_required,
            accepted_source_refs=accepted_sources,
            mediated_tool_intents=mediated_tools,
            flags=tuple(flags),
        )
