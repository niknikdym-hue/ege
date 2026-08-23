# Eksamio AI Tutor — Continuity & Failover Architecture v1.0

**Status:** ACTIVE CENTRAL P0 RELIABILITY ARCHITECTURE  
**Date:** 2026-08-23  
**Parent:** `AI-TUTOR-LAUNCH-PLAN-2026-08-23.md`  
**Owner decision:** `OWNER-DECISION-AI-TUTOR-GLOBAL-CONTINUITY-2026-08-23.md`

## 1. Reliability objective

The paid Tutor must behave as one Eksamio service even when external providers fail.

The learner must not experience provider names, API keys, provider billing state or provider-specific session mechanics.

Target shape:

`Learner browser -> Eksamio edge -> Tutor Orchestrator -> Reliability Gateway -> admitted provider pool`

Canonical session and educational state remain Eksamio-owned.

## 2. Failure domains to remove

The system must not have an unmitigated single point of failure in:

1. conversational model provider;
2. provider model/version;
3. provider API credential/account;
4. provider billing balance / quota bucket;
5. speech/realtime path;
6. provider-specific conversation state;
7. Tutor turn accounting;
8. canonical EvidenceEvent writes;
9. Eksamio deployment/runtime where reasonable for the launch stage.

Provider redundancy is necessary but is not by itself sufficient.

## 3. Provider registry

Every provider/model path is registered server-side with normalized metadata:

- `provider_id`;
- `adapter_version`;
- `capabilities[]` (text, streaming text, tools, realtime voice, STT, TTS, multimodal);
- `admission_status`;
- `quality_profile_version`;
- `privacy_security_gate_version`;
- `legal_accessibility_gate_version`;
- `cost_profile_version`;
- `configured_capacity_class`;
- `health_state`;
- `health_updated_at`;
- `circuit_state`;
- `manual_enable/disable`;
- optional geography/contract restrictions known to Eksamio operations.

Only providers in `PRODUCTION_ADMITTED` state may serve paid production Tutor traffic.

## 4. Normalized provider health states

At minimum:

- `HEALTHY`;
- `DEGRADED`;
- `OPEN_CIRCUIT`;
- `DISABLED_MAINTENANCE`;
- `BLOCKED_FINOPS`;
- `BLOCKED_CREDENTIAL`;
- `BLOCKED_POLICY`.

Health is capability-specific. A provider can be healthy for text and unavailable for realtime voice.

Do not use one global boolean for all provider capabilities.

## 5. Normalized failure taxonomy

Adapters translate provider-specific HTTP/SDK errors into provider-neutral classes:

- `TIMEOUT`;
- `NETWORK_FAILURE`;
- `RATE_LIMIT`;
- `QUOTA_OR_BILLING_EXHAUSTED`;
- `CREDENTIAL_OR_ACCOUNT_FAILURE`;
- `MODEL_UNAVAILABLE`;
- `PROVIDER_5XX`;
- `CAPACITY_UNAVAILABLE`;
- `MALFORMED_PROVIDER_OUTPUT`;
- `TOOL_PROTOCOL_FAILURE`;
- `PROVIDER_SPECIFIC_REJECTION`;
- `PLATFORM_SAFETY_BLOCK`;
- `INVALID_PLATFORM_REQUEST`.

`PLATFORM_SAFETY_BLOCK` must never be bypassed by changing provider.

`INVALID_PLATFORM_REQUEST` must be fixed by Eksamio rather than retried across providers.

## 6. Retry vs failover policy

The gateway uses a bounded retry budget.

General rule:

- transient network/5xx/timeout: at most a small bounded same-provider retry if the current latency budget allows it, otherwise fail over;
- rate limit/capacity: honor a short provider retry signal only if it fits the Tutor latency budget, otherwise fail over immediately;
- quota/billing exhaustion: no blind retry; mark the path `BLOCKED_FINOPS` and fail over;
- credential/account failure: no blind retry; open circuit and fail over;
- model unavailable/retired: disable the model path and route to another admitted model/provider;
- malformed output: one bounded normalization/retry path may be attempted; repeated failure opens the circuit;
- platform safety block: no failover to bypass safety.

Exact timing thresholds are measured in the evaluation harness and staging; do not invent production latency constants before representative data exists.

## 7. Circuit breaker

Circuit breaker is maintained per provider capability/path.

States:

`CLOSED -> OPEN -> HALF_OPEN -> CLOSED`

Opening inputs include:

- consecutive normalized failures;
- failure ratio over a rolling window;
- explicit billing/quota failure;
- credential failure;
- external operational disable;
- provider/model deprecation.

Half-open probes use synthetic, non-learner payloads wherever possible.

Anti-flapping/hysteresis is required so that traffic does not bounce rapidly between unstable providers.

## 8. Proactive provider health

Runtime failures are the final defense, not the only defense.

Production operations should combine:

- passive real-request success/error/latency metrics;
- synthetic non-learner canary requests;
- provider status/health signals when available;
- quota/rate-limit telemetry when available;
- billing/balance/budget signals when available;
- model deprecation/configuration checks.

Provider-native financial controls are defense in depth:

- OpenAI supports prepaid credits and auto-recharge thresholds/limits;
- Google Gemini exposes usage tiers/rate limits and billing spend controls;
- Yandex Cloud supports balance/cost budgets, notifications and budget-trigger automation.

These facilities reduce risk but never replace Eksamio runtime failover.

## 9. Eksamio-owned Tutor session

Canonical episode state is provider-neutral.

Minimum continuity identity:

- `episode_id`;
- `turn_id`;
- `provider_attempt_id` per external attempt;
- `accepted_attempt_id` when one result is committed;
- current learning goal;
- semantic target refs;
- verified subject context refs/version;
- bounded PEIS context projection/version;
- help/escalation state;
- `verification_required`;
- structured Tutor history/summary allowed by privacy policy;
- pending tool intents/results;
- entitlement/quota accounting ref.

Provider conversation/session IDs are adapter-local ephemeral values only.

A new provider must be able to reconstruct the next request from the Eksamio session projection without access to the previous provider's private session state.

## 10. Exactly-once learner-visible and educational side effects

A provider generation attempt is not an educational write.

Rules:

- provider adapters cannot write PEIS directly;
- canonical EvidenceEvents are emitted only through the normal evidence service after deterministic verification;
- every canonical write uses an Eksamio idempotency key;
- late responses from abandoned provider attempts are ignored;
- only one provider attempt may be accepted for the same logical turn commit;
- provider failover never creates a second verification result or duplicate mastery update.

This is required to make retries/failover safe.

## 11. Tutor quota and accounting semantics

Keep two separate ledgers:

A. learner entitlement/quota consumption;
B. internal provider cost/attempt accounting.

Multiple provider attempts may increase Eksamio's internal infrastructure cost, but they do not create multiple learner charges.

For a logical Tutor unit:

- failover success -> learner quota consumed once;
- all providers fail before a valid learner-facing result -> learner AI quota not consumed;
- late/duplicate provider completion -> no additional learner quota;
- voice fails and the same episode continues in text -> no duplicate Tutor-unit charge merely because of the channel switch.

## 12. Streaming text failure

Streaming creates a harder continuity case because the learner may already have seen partial output.

Required semantics:

- before the first committed learner-visible segment, failover may be transparent;
- after partial output is visible, mark the failed generation segment as interrupted;
- preserve the visible partial text in the Eksamio episode history;
- the fallback provider receives a bounded continuation context and must continue rather than blindly repeat the whole answer;
- abandoned attempts cannot execute canonical writes;
- UX may show a neutral continuity message, never a provider-specific error.

The first implementation may use bounded buffering if needed to reduce visibly interrupted turns, but must not hide long latency indefinitely.

## 13. Voice/realtime failure

Voice is the same Tutor episode, not a separate state machine.

Failure levels:

- STT/realtime input failure -> offer typed input while keeping episode state;
- TTS/output failure -> render text immediately;
- conversational provider failure -> change conversational provider and preserve the episode projection;
- mid-utterance interruption -> cancel the abandoned voice segment, preserve text/structured state, continue from the last committed semantic turn;
- speech provider outage -> route to an independently admitted speech/realtime path where available;
- if no voice path is healthy -> text remains available and voice quota is not consumed for the failed segment.

No learner audio persistence is introduced by retry/failover.

## 14. Learner-country independence

The browser calls Eksamio only.

External provider access occurs from Eksamio server infrastructure. Therefore a learner in Russia, the United States or another supported country does not need direct reachability to the chosen model provider.

Provider/legal restrictions are an internal admission/routing concern.

Before broad paid launch, monitor the public Eksamio service from multiple geographic probes, including at minimum Russia and a non-Russia geography, to detect ingress/DNS/CDN/API paths that are accidentally country-specific.

Do not infer that provider redundancy alone proves global Eksamio reachability.

## 15. Platform/cloud continuity

Provider failover protects the AI dependency but not the Eksamio platform itself.

Launch hardening should separately prove:

- stateless/restartable Tutor Orchestrator instances;
- immutable/reproducible deployment;
- database HA/backup/restore appropriate to the production persistence layer;
- secrets not tied to one runtime instance;
- health/readiness/kill-switch behavior;
- an explicit disaster-recovery path for the Eksamio application.

Yandex Cloud remains the primary launch cloud. The application and persistence contracts must remain portable so a future warm-standby/secondary-cloud deployment does not require redesigning Tutor or PEIS semantics.

A second paid cloud deployment is a later infrastructure/cost decision; portability and DR design are required now.

## 16. Graceful degradation ladder

The user-facing product should degrade in this order rather than fail catastrophically:

1. preferred admitted conversational provider;
2. secondary admitted conversational provider;
3. additional admitted provider/model path if configured;
4. voice -> text continuity if speech/realtime is unhealthy;
5. bounded deterministic/existing educational functionality while Tutor is temporarily unavailable.

Never degrade to an unapproved model that has not passed quality/safety/privacy/grounding gates.

## 17. Observability

Metrics must include at least:

- requests/turns by normalized capability;
- provider attempts per logical turn;
- primary success rate;
- fallback activation rate;
- fallback success rate;
- failure class counts;
- circuit state transitions;
- p50/p95/p99 latency per provider/capability;
- learner-visible Tutor-unavailable rate;
- streaming interruptions;
- voice->text degradation events;
- quota/billing block events;
- duplicate/late provider responses discarded;
- entitlement double-charge prevention count;
- canonical write duplication count (target 0);
- cost per successful Tutor episode and extra cost due to failover.

No secrets, learner audio, raw payment data or unnecessary learner identifiers in metrics/logs.

## 18. Chaos/failure acceptance matrix

Deterministically test at least:

1. primary timeout -> secondary succeeds;
2. primary 5xx -> secondary succeeds;
3. primary 429/capacity -> secondary succeeds;
4. primary billing/quota exhausted -> primary circuit opens, secondary succeeds;
5. primary credential invalid -> primary circuit opens, secondary succeeds;
6. primary malformed output -> fallback succeeds;
7. late primary response after secondary acceptance -> discarded;
8. both providers unavailable -> stable Tutor-unavailable result, no learner quota consumed;
9. safety block -> no provider hopping to bypass it;
10. same logical turn under retries -> one learner quota debit maximum;
11. same verification under retries -> one EvidenceEvent maximum;
12. provider swap preserves learning goal/semantic targets/help state/verification requirement;
13. voice provider failure -> text continues same episode;
14. primary recovers -> half-open probe -> controlled return without flapping;
15. restart of Tutor service -> session can resume from Eksamio-owned state;
16. synthetic geo checks show public Eksamio path from Russia and at least one non-Russia region.

## 19. Paid launch reliability gate

Before broad paid Tutor launch:

- at least two independently production-admitted conversational provider paths;
- automated failover proven with real sandbox/staging providers;
- provider billing/quota failure simulation proven;
- session continuity across provider switch proven;
- no double learner quota/evidence writes;
- voice failure has an independent approved fallback path and text continuity;
- monitoring/circuit breaker/kill switch operational;
- multi-geography Eksamio ingress checks operational;
- provider and platform incidents have an operator runbook;
- representative soak/chaos tests completed.

Functional correctness gates are mandatory. Numeric latency/SLO thresholds are versioned only after representative staging measurements.

## 20. Work sequence

R0. Provider-neutral Tutor boundary.  
R1. Reliability Gateway with deterministic fake providers and fault injection.  
R2. Evaluation harness and normalized quality contract.  
R3. Two real conversational providers in sandbox/staging.  
R4. Grounded Russian text vertical slice with injected provider failure.  
R5. Speech/realtime primary + independent fallback and voice->text continuity.  
R6. FinOps monitors/budget alerts/capacity alarms.  
R7. Multi-geography availability monitoring.  
R8. Chaos/soak + operator runbook.  
R9. Paid launch reliability admission.

No public AI traffic is authorized by this document alone.
