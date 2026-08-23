# AI-TUTOR-RELIABILITY-GATEWAY-001

**Status:** IMPLEMENTATION TASK / AI TUTOR P0 RELIABILITY  
**Date:** 2026-08-23  
**Parent architecture:** `AI-TUTOR-CONTINUITY-FAILOVER-ARCHITECTURE-v1.0.md`  
**Executor:** Codex

## WHY_NOW

The provider-neutral Tutor boundary prevents semantic/provider lock-in, but paid service continuity additionally requires automatic provider failover, circuit breaking, session portability and exactly-once learner/accounting semantics.

The learner must not lose a paid Tutor episode because one provider times out, exhausts quota/balance or becomes unreachable.

## ACTIVE_BLOCKER_OR_MILESTONE

Build and prove the provider-neutral reliability layer using deterministic fake providers and injected failures.

This task does NOT connect a live external provider.

## BASELINE_MAIN_SHA

Refresh actual `origin/main` before execution.

## DEPENDENCY_IN

Required before implementation:

- `AI-TUTOR-PROVIDER-NEUTRAL-BOUNDARY-001` must be merged/PASS;
- `OWNER-DECISION-AI-TUTOR-GLOBAL-CONTINUITY-2026-08-23.md`;
- `AI-TUTOR-CONTINUITY-FAILOVER-ARCHITECTURE-v1.0.md`;
- current AI Tutor core contract and PEIS authority.

If the provider-neutral boundary is not yet PASS, STOP with:

`BLOCKED_AI_TUTOR_RELIABILITY_PROVIDER_BOUNDARY_NOT_READY`

## EXPECTED_UNLOCK

PASS enables two real providers to be plugged into the same reliability gateway in a later sandbox/staging task without changing Tutor/PEIS semantics.

Success status:

`AI_TUTOR_RELIABILITY_GATEWAY_READY_FOR_MULTI_PROVIDER_SANDBOX`

## MINIMAL_DELTA

Extend the existing `ai-tutor-reference` boundary rather than creating a second Tutor core.

Implement at minimum:

1. provider registry/routing config;
2. normalized provider health and failure classes;
3. circuit breaker per provider capability;
4. bounded retry/failover orchestrator;
5. logical `episode_id` / `turn_id` / `provider_attempt_id` / `accepted_attempt_id` semantics;
6. exactly-once turn acceptance;
7. learner quota debit idempotency boundary;
8. late response discard;
9. deterministic fake-provider fault injection;
10. metrics/event hooks for routing/failure without learner secrets;
11. validator/test evidence.

Use Python standard library / existing project patterns where practical.

## REQUIRED FAILURE NORMALIZATION

At minimum support normalized categories:

- TIMEOUT
- NETWORK_FAILURE
- RATE_LIMIT
- QUOTA_OR_BILLING_EXHAUSTED
- CREDENTIAL_OR_ACCOUNT_FAILURE
- MODEL_UNAVAILABLE
- PROVIDER_5XX
- CAPACITY_UNAVAILABLE
- MALFORMED_PROVIDER_OUTPUT
- TOOL_PROTOCOL_FAILURE
- PROVIDER_SPECIFIC_REJECTION
- PLATFORM_SAFETY_BLOCK
- INVALID_PLATFORM_REQUEST

Provider-specific error strings/codes must be isolated inside adapters/test fixtures, not spread through Tutor Core.

## REQUIRED ROUTING RULES

- Only registered/admitted fake provider paths are routable.
- Provider order/weight is server-owned.
- Learner cannot select provider.
- QUOTA_OR_BILLING_EXHAUSTED opens/blocks that provider path and fails over without blind retry.
- CREDENTIAL_OR_ACCOUNT_FAILURE opens/blocks the path and fails over.
- TIMEOUT/NETWORK/5xx may receive only bounded retries before fallback.
- PLATFORM_SAFETY_BLOCK must never cause fallback intended to bypass safety.
- INVALID_PLATFORM_REQUEST must not be sprayed across providers.
- Returning to a recovered provider must go through half-open probe/controlled recovery semantics.

Exact wall-clock thresholds may remain config values in this reference task; do not invent production SLA numbers.

## REQUIRED SESSION CONTINUITY

Provider failover must preserve a provider-neutral episode projection containing at minimum:

- current goal;
- semantic targets;
- verified context refs;
- bounded PEIS context projection ref/version;
- help/escalation state;
- verification-required flag;
- allowed structured history/summary.

Provider-specific session IDs may exist only as ephemeral adapter fields.

A fallback fake provider must be able to complete the turn without the primary provider's session ID.

## EXACTLY-ONCE RULES

For one logical turn:

- multiple provider attempts are allowed;
- only one attempt may become accepted;
- late completions after acceptance are discarded;
- provider attempts cannot write PEIS directly;
- provider retry/failover cannot create multiple EvidenceEvents;
- learner quota/entitlement charge can be committed at most once;
- if all providers fail before a valid response, learner AI quota is not consumed.

Use explicit idempotency/commit semantics; do not rely on timing coincidence.

## FAKE PROVIDER MATRIX

Implement deterministic behaviors sufficient to simulate:

- healthy primary;
- healthy secondary;
- timeout;
- network failure;
- 429/rate limit;
- quota/billing exhaustion;
- credential failure;
- model unavailable;
- 5xx;
- malformed response;
- delayed success arriving after fallback success;
- platform safety block;
- recovery after an open circuit.

No external AI calls.

## REQUIRED TESTS

At minimum prove:

1. primary success uses primary only;
2. primary timeout -> secondary success;
3. primary network failure -> secondary success;
4. primary 5xx -> secondary success;
5. primary rate limit -> secondary success according to bounded policy;
6. primary quota/billing exhaustion -> circuit blocked/open -> secondary success;
7. primary credential failure -> circuit blocked/open -> secondary success;
8. primary malformed output -> bounded policy -> fallback success;
9. late primary success after secondary acceptance is discarded;
10. both providers fail -> stable Tutor-unavailable result;
11. both providers fail -> learner quota debit count = 0;
12. successful fallback -> learner quota debit count = 1;
13. successful primary -> learner quota debit count = 1;
14. retries/fallback never produce learner quota debit count > 1;
15. no provider attempt emits direct PEIS canonical writes;
16. mocked verification/evidence commit remains max one under retry race;
17. safety block is not bypassed by provider hopping;
18. invalid platform request is not retried across providers;
19. failover preserves current learning goal;
20. failover preserves semantic targets;
21. failover preserves `verification_required`;
22. fallback does not require primary provider session id;
23. provider recovers through half-open/controlled path without rapid flapping;
24. normalized metrics/events contain no provider secret/contact/payment/learner audio data;
25. all existing AI Tutor boundary tests remain green;
26. directly affected PEIS validators remain green.

Repeat deterministic validator twice if it materializes result artifacts; hashes/results must match.

## STREAMING / VOICE BOUNDARY

This task need not implement real streaming or voice runtime.

It must, however, expose enough neutral state to support later:

- interrupted streaming segment marker;
- abandoned attempt;
- continuation attempt;
- voice->text continuity using the same `episode_id`.

Do not store learner audio.

## OBSERVABILITY CONTRACT

Emit normalized test/reference events for at least:

- provider attempt started/completed/failed;
- normalized failure class;
- fallback activated/succeeded/failed;
- circuit state change;
- late response discarded;
- logical turn accepted;
- learner quota debit committed/skipped;
- Tutor unavailable.

Do not log secrets, contact data, raw payment data or learner audio.

## ALLOWED_PATHS

Prefer only:

- `eksamio-learning-engine/ai-tutor-reference/**`

Add a result/contract file in that subtree if useful.

## FORBIDDEN

Do not:

- call OpenAI/Google/Yandex or any external model;
- add real API keys/secrets;
- implement cloud resources;
- change PEIS canonical semantics;
- change subject truth;
- change demos/Tilda;
- implement payment processing;
- implement actual entitlement commerce;
- persist learner audio;
- choose a production provider;
- build a new Tutor core beside the existing one.

## ACCEPTANCE_EVIDENCE

Return:

- actual main baseline SHA;
- branch/commit/PR;
- files changed;
- reliability contract/version;
- exact test commands/results;
- failure matrix results;
- circuit breaker results;
- session portability result;
- late response discard result;
- learner quota idempotency result;
- direct canonical write count;
- existing AI Tutor/PEIS regression results;
- deterministic hashes if applicable;
- `EXTERNAL_AI_CALLS=0`;
- `PROVIDER_SECRETS_ADDED=0`;
- `LEARNER_AUDIO_PERSISTED=false`;
- `PUBLIC_TRAFFIC_CONNECTED=false`;
- blockers.

## STOP_CONDITIONS

STOP if:

- provider-neutral boundary is not PASS/merged;
- exactly-once semantics require provider direct writes;
- session continuity requires provider-specific canonical state;
- retry/failover would require bypassing safety or PEIS contracts;
- learner quota semantics cannot be separated from provider attempt count;
- scope expands to real provider/cloud/payment/voice integration.

## FINAL_STATUS

Success only:

`AI_TUTOR_RELIABILITY_GATEWAY_READY_FOR_MULTI_PROVIDER_SANDBOX`

Otherwise one exact blocker, for example:

- `BLOCKED_AI_TUTOR_RELIABILITY_PROVIDER_BOUNDARY_NOT_READY`
- `BLOCKED_AI_TUTOR_RELIABILITY_SESSION_PORTABILITY`
- `BLOCKED_AI_TUTOR_RELIABILITY_IDEMPOTENCY`
- `BLOCKED_AI_TUTOR_RELIABILITY_SAFETY_ROUTING`
- `BLOCKED_AI_TUTOR_RELIABILITY_UNEXPECTED_SCOPE`
