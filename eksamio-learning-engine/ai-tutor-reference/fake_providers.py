"""Deterministic fake adapters used exclusively by the T0 boundary validator."""

from __future__ import annotations

from tutor_boundary import ProviderFailure, ProviderRequest, ProviderResponse, ToolIntent


class GroundedFakeProvider:
    provider_id = "fake-grounded-a"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            text="Разберём правило по переданному проверенному фрагменту.",
            source_refs=(request.verified_source_refs[0],),
            tool_intents=(ToolIntent("open_verified_explanation", {"target": request.target_refs[0]}),),
        )


class EquivalentGroundedFakeProvider:
    provider_id = "fake-grounded-b"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(text="Сначала применим проверенный источник к этому шагу.")


class HostileFakeProvider:
    provider_id = "fake-hostile"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            text="Неподтверждённый совет.",
            source_refs=("source:invented",),
            tool_intents=(ToolIntent("run_shell", {"command": "bad"}),),
            attempted_mutations={
                "correctness": True,
                "mastery": "STRONG",
                "readiness": "READY",
                "retention": "DURABLE",
                "nba": "STOP_SESSION_COMPLETE",
                "semantic_id": "made-up",
                "identity_link": "other",
                "payment_entitlement": "paid",
            },
            attempted_verification_required=False,
        )


class UnavailableFakeProvider:
    provider_id = "fake-unavailable"

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        raise ProviderFailure("deterministic fake outage")


class MalformedFakeProvider:
    provider_id = "fake-malformed"

    def generate(self, request: ProviderRequest) -> ProviderResponse:  # type: ignore[override]
        return "not-a-provider-response"  # type: ignore[return-value]
