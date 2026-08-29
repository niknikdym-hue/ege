#!/usr/bin/env python3
"""Shared server-owned prompt projection for interchangeable Tutor LLM providers."""
from __future__ import annotations

from typing import Any, Sequence

from tutor_boundary import ProviderRequest


def history_messages(history: Sequence[Any]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for entry in history:
        role = "user" if entry.role == "learner" else "assistant"
        messages.append({"role": role, "content": entry.text})
    return messages


def grounded_system_text(request: ProviderRequest) -> str:
    if not request.verified_source_refs or len(request.verified_source_refs) != len(request.verified_excerpts):
        raise ValueError("grounded Tutor requires paired verified source refs/excerpts")
    if not all(ref.startswith("source:") for ref in request.verified_source_refs):
        raise ValueError("Tutor providers accept server-verified source refs only")

    verified = "\n\n".join(
        f"[{ref}]\n{excerpt}"
        for ref, excerpt in zip(request.verified_source_refs, request.verified_excerpts)
    )
    return (
        f"{request.policy_instruction}\n"
        "Ты образовательный Tutor Eksamio. Используй только проверенный контекст ниже как предметную истину. "
        "Не выдумывай правило, ответ, источник или состояние ученика. Не утверждай mastery по самому диалогу. "
        "После существенной помощи напомни, что навык подтверждается отдельной самостоятельной проверкой.\n\n"
        f"Цель обучения: {request.learning_goal}\n"
        f"PEIS summary: {request.peis_learning_summary}\n"
        f"Проверенный контекст:\n{verified}"
    )


def chat_messages(request: ProviderRequest) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": grounded_system_text(request)}]
    messages.extend(history_messages(request.history))
    messages.append({"role": "user", "content": request.learner_text})
    return messages
