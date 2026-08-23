# AI-TUTOR-OPENAI-SANDBOX-001

**Status:** IMPLEMENTATION TASK / AI TUTOR P0 REAL-PROVIDER SANDBOX  
**Date:** 2026-08-23  
**Executor:** Codex  
**Dependency:** `AI_TUTOR_RELIABILITY_GATEWAY_READY_FOR_MULTI_PROVIDER_SANDBOX`

## WHY_NOW

The provider-neutral Tutor boundary and deterministic reliability/failover gateway are now implemented and accepted. The next smallest useful step is to prove that a real OpenAI Responses API adapter can operate through those Eksamio-owned boundaries without acquiring authority over subject truth, learner state, identity, entitlement, verification policy, or session continuity.

This task is a **controlled real-provider sandbox**, not production admission and not public rollout.

## ACTIVE_BLOCKER_OR_MILESTONE

Prove a real OpenAI text provider path end-to-end in a bounded sandbox and produce model-quality/cost/latency evidence for Central Brain review.

## BASELINE_MAIN_SHA

Refresh actual `origin/main` before work. Do not assume the task-creation baseline remains current.

## DEPENDENCY_IN

Read and reuse:

- `AGENTS.md`;
- `00-PRODUCT-MASTERPLAN.md`;
- `OWNER-DECISIONS-2026-08-22.md`;
- `AI-TUTOR-LAUNCH-PLAN-2026-08-23.md`;
- `OWNER-DECISION-AI-TUTOR-GLOBAL-CONTINUITY-2026-08-23.md`;
- `AI-TUTOR-CONTINUITY-FAILOVER-ARCHITECTURE-v1.0.md`;
- merged `ai-tutor-reference/tutor_boundary.py`;
- merged `ai-tutor-reference/reliability_gateway.py`;
- current T0/T1 validators and result evidence;
- current accepted Russian semantic/source authority needed only for bounded test fixtures.

Do not create a second Tutor core or a provider-specific learner model.

## CURRENT OPENAI TECHNICAL AUTHORITY

At task issue time, current official OpenAI documentation establishes:

- use the Responses API for direct model requests;
- API authentication through `OPENAI_API_KEY` from the environment/secret store;
- `store=false` is supported for stateless Responses API use;
- GPT-5.6 Sol (`gpt-5.6-sol`) is the quality-ceiling/frontier model;
- GPT-5.6 Terra (`gpt-5.6-terra`) is positioned as the intelligence/cost balance;
- both support Responses API, text input/output, multilingual use, streaming, function calling and structured outputs.

Before implementation, re-check current official OpenAI docs if exact SDK syntax has changed. Do not rely on old examples or unofficial wrappers.

## EXPECTED_UNLOCK

PASS produces:

1. a real OpenAI adapter behind the already-merged provider-neutral boundary;
2. real sandbox evidence for Sol and Terra on the same grounded Russian Tutor cases;
3. real usage/latency/cost evidence;
4. normalized error mapping into the merged reliability taxonomy;
5. a clean path to the next task: add a second **real independent provider** and prove real cross-provider failover.

Success status:

`AI_TUTOR_OPENAI_SANDBOX_READY_FOR_QUALITY_REVIEW`

This status does **not** mean OpenAI is production-admitted or that Pro Tutor is launch-ready.

## EXECUTION MODE

This task performs real outbound OpenAI API calls.

Use only a secret already configured in the execution environment:

`OPENAI_API_KEY`

Never print, echo, serialize, commit, attach, or include any part of the key in logs, fixtures, PR text, test artifacts, exception text, screenshots, or result files.

If `OPENAI_API_KEY` is absent, stop with:

`BLOCKED_AI_TUTOR_OPENAI_API_KEY_NOT_CONFIGURED`

Do not ask for the secret value in chat and do not create a committed `.env` containing it.

## OPENAI ADAPTER

Extend the existing `eksamio-learning-engine/ai-tutor-reference/` implementation.

Create one bounded OpenAI sandbox adapter that:

- implements the existing provider interface rather than changing Tutor semantics;
- uses the official OpenAI Python SDK;
- uses the Responses API;
- uses `store=False` / current exact SDK equivalent;
- does not use OpenAI conversation state as canonical Tutor state;
- does not use `previous_response_id` as canonical session continuity;
- sends only the minimized `ProviderRequest` fields already authorized by T0;
- sends no canonical learner id, email, phone, payment data, auth token, raw DB row, or provider-independent secret;
- uses no built-in web search/file search/computer/code tools in this sandbox;
- performs no PEIS write;
- returns a normalized `ProviderResponse` only after validating the OpenAI response shape;
- isolates all OpenAI-specific fields/errors inside the adapter.

If structured output is used, use the current official structured-output mechanism and a bounded schema matching the normalized advisory response. Do not let schema/tool fields acquire PEIS authority.

## SANDBOX ADMISSION MODE

Do **not** label OpenAI `PRODUCTION_ADMITTED` merely to make the existing gateway route it.

If the reliability gateway needs a small change to support real sandbox routing, add an explicit server-owned sandbox mode/status such as `SANDBOX_ADMITTED` while preserving the current production default.

Mandatory proof:

- production/default routing cannot route a sandbox-only provider path;
- sandbox routing can route a sandbox-admitted provider path;
- learner input cannot select or promote a provider path;
- no change silently promotes OpenAI to production admission.

## MODELS UNDER TEST

Use exact model IDs for reproducibility:

- `gpt-5.6-sol`
- `gpt-5.6-terra`

Do not use the unsuffixed alias for the comparison.

Use the same input fixtures, same output-token ceiling, same system/policy instructions, and same provider request shape for both models unless the API requires a documented model-specific difference. Record any difference.

Do not production-select a winner in this task. Produce evidence for Central Brain review.

## LIVE CALL BUDGET

Hard cap:

`MAX_LIVE_RESPONSES=12`

Target exactly six bounded Tutor cases × two models = 12 responses, including all successful benchmark calls. Any auth/probe call counts toward this cap if it creates a model response.

Per live response:

- bounded educational input only;
- target input below 4,000 tokens;
- `max_output_tokens` / current equivalent <= 500;
- no paid built-in tools;
- no background mode;
- no batch mode.

Hard projected sandbox spend ceiling:

`MAX_PROJECTED_OPENAI_COST_USD=1.00`

Before executing the benchmark, calculate a conservative worst-case projection using current official OpenAI token prices and stop if the planned run could exceed $1.00.

Do not automatically broaden the sample or rerun failed quality cases repeatedly. API/network retry must remain bounded by reliability policy.

## TEST FIXTURE REQUIREMENTS

Use six bounded Russian-language Tutor cases.

Preferred fixture source:

- already-canonical, already-source-backed Russian `school-*` semantic identities and their existing verified source/provenance in the repository.

Rules:

- do not admit or invent new semantic identities;
- do not reopen Russian subject reconciliation;
- do not copy 2025/2026 demo text as authority for another context unless it is already the exact accepted source basis;
- preserve exact source refs used in the fixture;
- fixture learner text must be synthetic/test-only and contain no real learner PII;
- include a mix of explanation, misconception correction, guided hint, and “do not give away mastery” situations;
- every case must require `verification_required=true` after Tutor help.

If exact verified excerpt material cannot be safely recovered from already accepted repository authority without new subject judgment, STOP with:

`BLOCKED_AI_TUTOR_OPENAI_VERIFIED_CONTEXT_FIXTURE`

Do not invent source truth to keep the API test moving.

## PROVIDER RESPONSE CONTRACT

For every real response, prove:

- response is normalized before acceptance;
- text is a real string and within configured limits;
- any returned source ref outside the server-supplied allowlist is rejected/flagged;
- unknown tool intent is rejected/not executed;
- provider cannot mutate correctness/mastery/readiness/retention/NBA/semantic identity/learner identity/entitlement;
- provider cannot clear `verification_required`;
- canonical PEIS writes remain zero at provider boundary;
- a malformed/invalid response cannot debit learner quota or become accepted.

## OPENAI ERROR NORMALIZATION

Map OpenAI/SDK/API failures into the existing reliability taxonomy without leaking provider-native secret-bearing details.

Cover with deterministic adapter tests at minimum:

- timeout -> `TIMEOUT`;
- connection/network error -> `NETWORK_FAILURE`;
- rate limit / 429 -> `RATE_LIMIT` or `QUOTA_OR_BILLING_EXHAUSTED` when the provider error clearly indicates billing/quota exhaustion;
- authentication/account failure -> `CREDENTIAL_OR_ACCOUNT_FAILURE`;
- unavailable/invalid model path where appropriate -> `MODEL_UNAVAILABLE`;
- server 5xx -> `PROVIDER_5XX`;
- malformed successful HTTP response/output -> `MALFORMED_PROVIDER_OUTPUT`;
- invalid request generated by Eksamio -> `INVALID_PLATFORM_REQUEST`;
- safety refusal/block must not be transformed into provider hopping that bypasses policy.

Do not intentionally exhaust the real account balance, revoke the real key, or create harmful traffic merely to produce live failures. Use deterministic injected/mocked SDK error fixtures for destructive failure classes.

## REAL OPENAI + RELIABILITY GATEWAY

Prove at least one successful real OpenAI response can traverse:

`ServerTutorTurn -> ProviderRequest -> OpenAI adapter -> normalized ProviderResponse -> T0 policy boundary -> T1 sandbox reliability gateway -> accepted advisory result`

with:

- `ACCEPTED_ATTEMPT_COUNT=1`;
- `LEARNER_QUOTA_DEBIT_COUNT=1` in the sandbox accounting fixture;
- `DIRECT_CANONICAL_PEIS_WRITES=0`;
- `verification_required=true` preserved.

For real OpenAI failure/fallback behavior in this task, use OpenAI adapter error injection plus the existing deterministic fake secondary. Do not require a second paid external provider yet.

The next task will replace that fake secondary with a real independent provider.

## QUALITY / PEDAGOGY EVIDENCE

For each of six cases and each model record a bounded review object containing:

- case id;
- semantic/source refs only, no real learner identity;
- model id;
- response status;
- answer text or a sanitized pointer/artifact;
- accepted source refs;
- boundary flags;
- `verification_required`;
- input tokens;
- cached input tokens if reported;
- output/reasoning token usage as reported by current API;
- latency milliseconds;
- estimated USD cost from current official pricing;
- request id if the SDK exposes one safely;
- no API key/secret.

Prepare a Central Brain / subject-review comparison packet for qualitative review across:

- source grounding / factual consistency;
- pedagogical clarity;
- usefulness of explanation/hint;
- avoidance of unsupported claims;
- avoidance of giving “mastery” authority to the model;
- preservation of independent-verification framing;
- verbosity/latency;
- cost.

Codex may compute mechanical metrics but must **not** declare a model production-admitted or declare subject correctness solely by self-rating.

## PRIVACY / DATA MINIMIZATION

The live sandbox must use only synthetic learner messages and bounded verified educational context.

No real learner:

- name;
- email;
- phone;
- account id;
- payer/payment data;
- private conversation history;
- audio;
- voiceprint/acoustic feature;
- browser auth token.

`store=false` is mandatory for this sandbox unless current API behavior makes that impossible, in which case STOP and return a privacy blocker rather than silently storing responses.

Do not persist learner audio. This task is text-only.

## REQUIRED TESTS

Before live calls:

1. T0 validator PASS;
2. T1 validator PASS;
3. Python compilation/static checks PASS;
4. OpenAI adapter unit tests PASS using fake/injected SDK responses/errors;
5. sandbox admission isolation PASS;
6. secret-redaction test PASS;
7. request-minimization test PASS;
8. malformed-response-before-commit regression PASS.

Live sandbox:

9. OpenAI auth/connectivity succeeds without revealing secret;
10. exact live response count <= 12;
11. six Sol cases attempted within cap;
12. six Terra cases attempted within cap;
13. at least one real accepted advisory result per model;
14. every accepted real result preserves `verification_required=true`;
15. real provider path performs zero direct canonical PEIS writes;
16. no unknown/unapproved tool is executed;
17. no unverified source ref is accepted;
18. usage and latency captured;
19. projected/actual estimated cost remains <= $1.00;
20. no secret appears in tracked diff/result artifact.

After live calls:

21. rerun T0/T1 regressions;
22. deterministic non-network adapter/error tests remain reproducible;
23. `git diff --check` or equivalent PASS.

## ALLOWED PATHS

Prefer only:

- `eksamio-learning-engine/ai-tutor-reference/**`;
- one bounded result/eval artifact in that subtree;
- this task file only if exact result pointers must be appended.

Do not change unrelated product areas.

## FORBIDDEN

Do not:

- expose or commit `OPENAI_API_KEY`;
- put real secrets into GitHub Actions logs/artifacts;
- create public Tutor/API traffic;
- connect Tilda/demo traffic;
- change canonical PEIS semantics;
- change subject truth or admit new semantic ids;
- implement payment processing;
- implement real learner entitlement commerce;
- use real learner data;
- persist learner audio;
- add voice/realtime in this task;
- add Google/Yandex/another real external provider in this task;
- mark OpenAI production-admitted;
- choose the production model/provider without Central Brain review;
- exceed 12 live Responses API calls;
- exceed the $1.00 projected sandbox budget.

## ACCEPTANCE_EVIDENCE

Return:

- actual baseline main SHA;
- branch/commit/PR;
- files changed;
- official OpenAI SDK version used;
- Responses API request configuration summary (`store=false`, tools disabled, output ceiling);
- secret-presence status only (`CONFIGURED=true/false`), never the value;
- model ids;
- exact live response count;
- benchmark case count;
- per-model accepted/failed counts;
- per-model token usage totals;
- per-model latency summary;
- per-model estimated cost;
- total estimated cost;
- sandbox admission isolation result;
- OpenAI error-normalization matrix;
- real OpenAI -> T0 -> T1 gateway result;
- source/tool/mutation/verification boundary results;
- T0/T1 regression results;
- `DIRECT_CANONICAL_PEIS_WRITES`;
- `PUBLIC_TRAFFIC_CONNECTED=false`;
- `REAL_LEARNER_DATA_USED=false`;
- `LEARNER_AUDIO_PERSISTED=false`;
- `OPENAI_RESPONSE_STORAGE_REQUESTED=false`;
- blockers;
- quality-review packet path.

## STOP_CONDITIONS

STOP rather than improvising if:

- `OPENAI_API_KEY` is unavailable;
- live OpenAI billing/account prevents bounded test calls;
- exact verified Russian fixture context cannot be recovered without new subject judgment;
- current OpenAI API does not permit the required stateless/privacy boundary;
- integrating the adapter requires canonical PEIS changes;
- model/provider output cannot be normalized before acceptance;
- cost projection could exceed $1.00;
- completing the task would require real learner data, public traffic, payment, voice, or a second real provider.

Exact blockers:

- `BLOCKED_AI_TUTOR_OPENAI_API_KEY_NOT_CONFIGURED`
- `BLOCKED_AI_TUTOR_OPENAI_ACCOUNT_OR_BILLING`
- `BLOCKED_AI_TUTOR_OPENAI_VERIFIED_CONTEXT_FIXTURE`
- `BLOCKED_AI_TUTOR_OPENAI_PRIVACY_BOUNDARY`
- `BLOCKED_AI_TUTOR_OPENAI_ADAPTER_CONTRACT`
- `BLOCKED_AI_TUTOR_OPENAI_COST_CAP`
- `BLOCKED_AI_TUTOR_OPENAI_UNEXPECTED_SCOPE`

## FINAL_STATUS

Success only:

`AI_TUTOR_OPENAI_SANDBOX_READY_FOR_QUALITY_REVIEW`

Do not merge the implementation PR. Central Brain reviews the real-provider evidence first.
