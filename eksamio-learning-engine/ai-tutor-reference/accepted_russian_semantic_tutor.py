#!/usr/bin/env python3
"""Fail-closed Tutor grounding for explicitly accepted Russian semantics.

This private-staging boundary is additive: the existing reviewed 121-card Tutor
path remains unchanged. A semantic session can open only when a Central-Brain
acceptance authority exists and an original Eksamio learner-content unit with
independent verification is present. The accepted denominator is derived from
the canonical Russian semantic-progress builder rather than duplicated here.
No network/provider execution occurs in this module.
"""
from __future__ import annotations

import json
import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reliability_gateway import FailureClass, ProviderAttempt, ProviderFault, ProviderOutcome
from sep1_russian_tutor import RussianTutorVerticalSlice, TutorSessionState, TutorSliceError
from tutor_boundary import ProviderRequest, ProviderResponse


class TutorSemanticNotAccepted(TutorSliceError):
    pass


@dataclass(frozen=True)
class AcceptedSemanticGrounding:
    semantic_id: str
    title: str
    explanation: str
    boundaries: tuple[str, ...]
    algorithm: tuple[str, ...]
    source_ref: str
    authority_ref: str
    content_ref: str

    @property
    def verified_excerpt(self) -> str:
        boundary_text = "\n".join(f"- {item}" for item in self.boundaries)
        algorithm_text = "\n".join(f"{index}. {item}" for index, item in enumerate(self.algorithm, start=1))
        return (
            f"Принятая тема: {self.title}\n"
            f"Проверенное объяснение: {self.explanation}\n"
            f"Границы:\n{boundary_text}\n"
            f"Алгоритм:\n{algorithm_text}"
        )


class AcceptedRussianSemanticAllowlist:
    """Load every bounded Russian semantic admitted by canonical progress authority."""

    PROGRESS_BUILDER_REF = "russian-program/subject-admission/build_russian_semantic_acceptance_progress.py"

    def __init__(self, engine_root: str | Path) -> None:
        self.engine_root = Path(engine_root).resolve()
        self.authority_specs = self._authority_specs()
        self.expected_semantic_count = sum(spec[3] for spec in self.authority_specs)
        self._entries = self._load()

    def _authority_specs(self) -> tuple[tuple[str, str, str, int], ...]:
        builder_path = self.engine_root / self.PROGRESS_BUILDER_REF
        try:
            namespace = runpy.run_path(str(builder_path))
        except (OSError, RuntimeError, ValueError) as exc:
            raise TutorSemanticNotAccepted("canonical Russian semantic-progress builder is unavailable") from exc

        # The versioned progress wrapper mutates the base builder namespace and
        # stores its effective authority tuples there. Read that effective
        # namespace rather than duplicating the authority list in Tutor code.
        effective = namespace.get("_namespace")
        if not isinstance(effective, dict):
            effective = namespace

        specs: list[tuple[str, str, str, int]] = []
        groups = (
            ("SUBJECT_SEMANTIC_AUTHORITIES", "CENTRAL_BRAIN_ACCEPTED_BOUNDED_SUBJECT_SEMANTIC"),
            ("ROUTE_SEMANTIC_AUTHORITIES", "CENTRAL_BRAIN_ACCEPTED_BOUNDED_ROUTE_SEMANTIC"),
        )
        for key, expected_semantic_status in groups:
            raw_specs = effective.get(key)
            if not isinstance(raw_specs, tuple) or not raw_specs:
                raise TutorSemanticNotAccepted(f"canonical progress builder has no {key}")
            for raw_spec in raw_specs:
                if not isinstance(raw_spec, tuple) or len(raw_spec) != 4:
                    raise TutorSemanticNotAccepted(f"invalid canonical authority spec in {key}")
                raw_path, expected_status, expected_count, _authority_id = raw_spec
                if not isinstance(raw_path, Path):
                    raise TutorSemanticNotAccepted(f"canonical authority path type drift in {key}")
                try:
                    relative = raw_path.resolve().relative_to(self.engine_root)
                except ValueError as exc:
                    raise TutorSemanticNotAccepted("canonical authority escaped the learning-engine root") from exc
                if not isinstance(expected_status, str) or not expected_status.startswith("CENTRAL_BRAIN_ACCEPTED_"):
                    raise TutorSemanticNotAccepted("canonical authority status is not accepted")
                if not isinstance(expected_count, int) or expected_count <= 0:
                    raise TutorSemanticNotAccepted("canonical authority count is invalid")
                specs.append((relative.as_posix(), expected_status, expected_semantic_status, expected_count))

        refs = [spec[0] for spec in specs]
        if len(refs) != len(set(refs)):
            raise TutorSemanticNotAccepted("canonical progress builder contains duplicate semantic authorities")
        return tuple(specs)

    @staticmethod
    def _rows(authority: dict[str, Any]) -> list[dict[str, Any]]:
        rows = authority.get("decisions")
        if rows is None and isinstance(authority.get("decision"), dict):
            rows = [authority["decision"]]
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise TutorSemanticNotAccepted("accepted semantic authority decisions are invalid")
        return rows

    def _content_unit(self, content_ref: str, semantic_id: str) -> dict[str, Any]:
        content_path_ref = content_ref.split("#", 1)[0]
        path = self.engine_root / content_path_ref
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise TutorSemanticNotAccepted(f"accepted semantic content is unavailable: {semantic_id}") from exc
        if payload.get("status") != "SUBJECT_ACCEPTANCE_REQUIRED":
            raise TutorSemanticNotAccepted("source learner bundle must remain fail-closed; acceptance belongs to overlay authority")
        copyright_guard = payload.get("copyright_guard")
        if not isinstance(copyright_guard, dict) or copyright_guard.get("source_passages_copied") != 0:
            raise TutorSemanticNotAccepted("Tutor semantic grounding violates source-passage guard")
        byte_guards = [
            value
            for key, value in copyright_guard.items()
            if isinstance(key, str) and key.endswith("_bytes_in_git")
        ]
        if not byte_guards or any(value != 0 for value in byte_guards):
            raise TutorSemanticNotAccepted("Tutor semantic grounding violates source-byte guard")
        units = [
            row for row in payload.get("units", [])
            if isinstance(row, dict) and row.get("proposed_semantic_id") == semantic_id
        ]
        if len(units) != 1:
            raise TutorSemanticNotAccepted(f"accepted semantic must map to exactly one learner unit: {semantic_id}")
        return units[0]

    def _load(self) -> dict[str, AcceptedSemanticGrounding]:
        entries: dict[str, AcceptedSemanticGrounding] = {}
        for authority_ref, expected_status, expected_semantic_status, expected_count in self.authority_specs:
            authority_path = self.engine_root / authority_ref
            try:
                authority = json.loads(authority_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise TutorSemanticNotAccepted(f"canonical semantic authority is unavailable: {authority_ref}") from exc
            if authority.get("status") != expected_status:
                raise TutorSemanticNotAccepted(f"semantic authority status drift: {authority_ref}")
            if authority.get("canonical_school_registry_mutated") is not False or authority.get("new_parallel_registry_created") is not False:
                raise TutorSemanticNotAccepted(f"semantic authority registry boundary drift: {authority_ref}")
            rows = self._rows(authority)
            if len(rows) != expected_count:
                raise TutorSemanticNotAccepted(f"semantic authority count drift: {authority_ref}")
            for row in rows:
                semantic_id = str(row.get("accepted_semantic_id", ""))
                if not semantic_id.startswith("ru-"):
                    raise TutorSemanticNotAccepted("Tutor semantic allowlist accepts only explicit ru-* overlay ids")
                if row.get("subject_semantic_status") != expected_semantic_status:
                    raise TutorSemanticNotAccepted(f"semantic not explicitly accepted: {semantic_id}")
                if semantic_id in entries:
                    raise TutorSemanticNotAccepted(f"duplicate accepted semantic authority: {semantic_id}")
                content_ref = str(row.get("content_ref", ""))
                if not content_ref.startswith("russian-program/production-learning-content/"):
                    raise TutorSemanticNotAccepted(f"semantic lacks production learner-content ref: {semantic_id}")
                unit = self._content_unit(content_ref, semantic_id)
                explanation = unit.get("canonical_explanation") or {}
                short = explanation.get("short")
                boundaries = explanation.get("boundaries")
                algorithm = unit.get("decision_algorithm")
                verification = unit.get("independent_verification")
                peis = unit.get("peis_evidence") or {}
                if not isinstance(short, str) or not short.strip():
                    raise TutorSemanticNotAccepted(f"semantic grounding explanation missing: {semantic_id}")
                if not isinstance(boundaries, list) or not boundaries or any(not isinstance(value, str) or not value.strip() for value in boundaries):
                    raise TutorSemanticNotAccepted(f"semantic grounding boundaries missing: {semantic_id}")
                if not isinstance(algorithm, list) or not algorithm or any(not isinstance(value, str) or not value.strip() for value in algorithm):
                    raise TutorSemanticNotAccepted(f"semantic grounding algorithm missing: {semantic_id}")
                if not isinstance(verification, list) or len(verification) < 2:
                    raise TutorSemanticNotAccepted(f"semantic independent verification missing: {semantic_id}")
                if peis.get("independent_verification_required") is not True:
                    raise TutorSemanticNotAccepted(f"semantic PEIS independent-verification guard missing: {semantic_id}")
                entries[semantic_id] = AcceptedSemanticGrounding(
                    semantic_id=semantic_id,
                    title=str(unit.get("title_ru", semantic_id)),
                    explanation=short.strip(),
                    boundaries=tuple(value.strip() for value in boundaries),
                    algorithm=tuple(value.strip() for value in algorithm),
                    source_ref=f"source:russian-accepted-semantic:{semantic_id}",
                    authority_ref=f"{authority_ref}#{semantic_id}",
                    content_ref=content_ref,
                )
        if len(entries) != self.expected_semantic_count:
            raise TutorSemanticNotAccepted(
                f"private-staging accepted semantic denominator drift: {len(entries)} != {self.expected_semantic_count}"
            )
        return entries

    @property
    def semantic_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))

    def require(self, semantic_id: str) -> AcceptedSemanticGrounding:
        try:
            return self._entries[semantic_id]
        except KeyError as exc:
            raise TutorSemanticNotAccepted(f"Russian Tutor semantic is not accepted for private staging: {semantic_id}") from exc


class AcceptedSemanticGroundedTextProvider:
    """Deterministic no-network fixture for the accepted-semantic Tutor path."""

    def __init__(self, provider_id: str) -> None:
        self.provider_id = provider_id
        self.calls = 0

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        self.calls += 1
        if len(request.verified_source_refs) != 1 or len(request.verified_excerpts) != 1:
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, "accepted semantic grounding must be singular")
        source_ref = request.verified_source_refs[0]
        excerpt = request.verified_excerpts[0]
        if not source_ref.startswith("source:russian-accepted-semantic:"):
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, "unaccepted Russian semantic source")
        if "Проверенное объяснение:" not in excerpt or "Границы:" not in excerpt or "Алгоритм:" not in excerpt:
            return ProviderFault(FailureClass.INVALID_PLATFORM_REQUEST, "accepted semantic excerpt is incomplete")
        explanation = excerpt.split("Проверенное объяснение:", 1)[1].split("\nГраницы:", 1)[0].strip()
        return ProviderResponse(
            text=(
                f"Опираемся только на принятую предметную семантику Eksamio: {explanation} "
                "Сначала примени правило сам, затем проверь решение по указанным границам и алгоритму."
            ),
            source_refs=(source_ref,),
        )


class AcceptedSemanticRussianTutorVerticalSlice(RussianTutorVerticalSlice):
    """Add a semantic-session entry point without changing the existing card path."""

    def __init__(self, *, engine_root: str | Path, **kwargs: Any) -> None:
        super().__init__(engine_root=engine_root, **kwargs)
        self.accepted_semantics = AcceptedRussianSemanticAllowlist(engine_root)

    def open_semantic_session(self, *, learner_profile_id: str, semantic_id: str) -> TutorSessionState:
        if not isinstance(learner_profile_id, str) or len(learner_profile_id) < 3:
            raise TutorSliceError("server-owned learner profile is required")
        grounding = self.accepted_semantics.require(semantic_id)
        session_ref = self.session_ref_factory()
        if not session_ref.startswith("tutor:") or session_ref in self.sessions:
            raise TutorSliceError("invalid/duplicate server Tutor session ref")
        state = TutorSessionState(session_ref, learner_profile_id, grounding)  # type: ignore[arg-type]
        self.sessions[session_ref] = state
        return state
