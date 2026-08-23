# Eksamio — AI Tutor Global Continuity Owner Decision

**Status:** APPROVED OWNER / PRODUCT / RELIABILITY AUTHORITY  
**Date:** 2026-08-23  
**Scope:** AI Tutor service continuity, provider resilience and learner-country independence  
**Supersedes:** any weaker interpretation that a single AI provider, provider account, provider balance or provider geography may be a production dependency for paid Tutor service.

## Decision

Russia remains the first commercial/legal launch market, but that does **not** mean the learning service is technically Russia-only.

A learner studying Russian through Eksamio should receive the same paid learning service regardless of whether the learner is physically in Russia, the United States or another supported country, subject only to applicable law and the ordinary availability of the public Internet/Eksamio service.

The learner browser must connect to Eksamio, not directly to an external AI provider. The learner must not need a VPN, an OpenAI/Google/Yandex account, a provider API key, or knowledge of which provider is currently serving the Tutor turn.

## Paid Tutor continuity invariant

A paid Tutor service must not depend on one external AI provider, one model, one API key, one provider billing balance, one quota bucket or one provider-specific session representation.

Before broad paid Tutor launch, Eksamio must have at least two independently production-admitted conversational provider paths capable of serving the required text Tutor contract. Provider admission remains subject to quality, legal, security, privacy and accessibility gates.

Provider switching is automatic and server-side. The learner does not choose a provider.

Examples of incidents that must be handled automatically when a suitable admitted fallback exists:

- provider outage;
- timeout/network failure;
- model outage or retirement;
- rate-limit or capacity exhaustion;
- provider billing/quota exhaustion;
- API credential/account failure;
- malformed provider response;
- provider-specific regional reachability failure.

A provider failure must not corrupt PEIS state, duplicate learning evidence, duplicate entitlement consumption or force the learner to restart the learning episode.

## Session ownership

The canonical Tutor episode/session state belongs to Eksamio.

Provider-specific conversation/session IDs may be used only as transient adapter details. They must never be the only representation of:

- current learning goal;
- current semantic targets;
- verified subject context;
- help history;
- verification-required state;
- learner-facing Tutor history required for continuity;
- PEIS context required to continue the episode.

When a provider fails, another admitted provider must be able to resume from an Eksamio-owned bounded session projection.

## Entitlement and paid-user protection

Provider retry/failover attempts are infrastructure details, not additional learner purchases.

A single learner Tutor turn/session unit must not be charged twice because Eksamio retried or changed provider.

If no admitted provider can return a valid Tutor result, the failed infrastructure attempt must not consume the corresponding AI interaction/session quota. The base deterministic learning product must remain available where technically possible.

Any broader commercial compensation for a prolonged outage is a separate commercial/legal decision and is not created by this technical authority.

## Voice continuity

Voice and text remain interfaces of the same Tutor episode.

Speech/realtime failure must not destroy the episode. At minimum the session must be able to continue in text while retaining the same learning goal and structured Tutor/PEIS context.

Before broad paid launch, the voice contour must have a tested independent fallback path: either a second admitted speech/realtime provider path or another approved voice architecture that does not share the same single point of failure as the primary path.

Learner audio remains transient and is never persisted by Eksamio.

## Financial continuity / provider account health

Provider billing and quota health are operational production signals.

Where a provider exposes balance, quota, budget or usage signals, Eksamio operations should monitor them and warn/route away before exhaustion where practical. Provider-native auto-recharge/budget-alert facilities may be used as an additional defense, but they do not replace runtime failover.

A provider billing/quota error at request time must normalize into the same provider-health/routing layer and must not be surfaced to the learner as a provider-specific failure.

## Learner-country independence

`learner_country` is not a product-level AI provider selector exposed to the learner and must not be used as a reason to require a different Eksamio product flow merely because the learner is studying from another country.

Provider/legal routing constraints, if any, are resolved inside the Eksamio backend/provider admission layer.

The architecture must support synthetic availability checks from multiple geographies before broad paid launch so that Eksamio can detect a service path that works from one geography but fails from another.

## Non-negotiable consistency rules

Automatic failover must never:

- bypass Eksamio safety policy;
- bypass verified subject grounding;
- bypass independent verification;
- allow a provider to mutate canonical mastery/readiness/retention/NBA;
- duplicate canonical EvidenceEvents;
- double-consume learner AI quota;
- persist learner audio;
- expose provider secrets to the client;
- silently accept a lower-quality provider that has not passed production admission.

## Consequence

The AI Tutor launch plan must include a dedicated continuity/failover gateway, deterministic chaos/failure tests, multi-provider sandbox proof, billing/quota failure simulation, session-resume proof, voice-to-text degradation proof and multi-geography availability checks.

This decision strengthens the existing provider-neutral and Russia-no-VPN architecture; it does not replace it.
