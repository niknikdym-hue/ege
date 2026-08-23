"""Scripted deterministic providers for reliability-gateway fault injection only."""

from __future__ import annotations

from collections import deque

from reliability_gateway import DelayedProviderSuccess, ProviderAttempt, ProviderFault, ProviderOutcome
from tutor_boundary import ProviderRequest, ProviderResponse


class ScriptedFakeProvider:
    def __init__(self, provider_id: str, outcomes: list[ProviderOutcome]) -> None:
        self.provider_id = provider_id
        self.outcomes: deque[ProviderOutcome] = deque(outcomes)
        self.requests: list[ProviderRequest] = []
        self.attempts: list[ProviderAttempt] = []

    def generate(self, request: ProviderRequest, attempt: ProviderAttempt) -> ProviderOutcome:
        self.requests.append(request)
        self.attempts.append(attempt)
        if not self.outcomes:
            raise AssertionError(f"fixture {self.provider_id} exhausted")
        return self.outcomes.popleft()


def healthy(text: str = "Нормализованный ответ.") -> ProviderResponse:
    return ProviderResponse(text=text)


def delayed(text: str = "Поздний ответ.") -> DelayedProviderSuccess:
    return DelayedProviderSuccess(healthy(text))
