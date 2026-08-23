# AI-TUTOR-PROVIDER-NEUTRAL-BOUNDARY-001

**Status:** IMPLEMENTATION TASK / AI TUTOR P0 PREPARATION  
**Date:** 2026-08-23  
**Baseline at task creation:** `f7107e1eacce9ac21ce92fcf2778bcaeb649d069`  
**Parent plan:** `AI-TUTOR-LAUNCH-PLAN-2026-08-23.md`  
**Executor:** Codex

## WHY_NOW

The production PEIS/Yandex staging dependencies are still being completed, but provider-neutral Tutor boundaries can be implemented and tested now without any live AI provider, cloud secret or public traffic.

Doing this first prevents provider lock-in and proves that a future LLM remains an advisory conversational component rather than becoming the owner of verified subject truth, learner identity, correctness, mastery, readiness, retention or NBA.

## ACTIVE_BLOCKER_OR_MILESTONE

Prepare the reusable server-side AI Tutor boundary required before `AI-TUTOR-GROUNDED-TEXT-001` can safely connect a real model to real PEIS context.

## BASELINE_MAIN_SHA

Refresh actual `origin/main` before work. Do not assume the creation baseline is still current.

## DEPENDENCY_IN

Read current applicable authority first:

- `AGENTS.md`
- `00-PRODUCT-MASTERPLAN.md`
- `00E-CURRENT-BRAIN-HANDOFF.md`
- `OWNER-DECISIONS-2026-08-22.md`
- `AI-TUTOR-LAUNCH-PLAN-2026-08-23.md`
- current Evidence/Mastery/Readiness/Retention/NBA contracts;
- current PEIS service bridge and trusted-host reference boundaries;
- `PRODUCT-BENCHMARK-2026.md` and any current Tutor benchmark authority if present.

Reuse existing PEIS types/contracts where they already express the needed meaning. Do not duplicate learner-state semantics inside Tutor code.

## EXPECTED_UNLOCK

PASS must make the next AI Tutor task able to plug a real text provider into a stable server boundary without changing PEIS semantics.

Next task after PASS and infrastructure dependencies:

`AI-TUTOR-GROUNDED-TEXT-001`

Success status:

`AI_TUTOR_PROVIDER_NEUTRAL_BOUNDARY_READY_FOR_GROUNDED_TEXT_SLICE`

## MINIMAL_DELTA

Create a small executable/reference Tutor boundary, preferably under:

`eksamio-learning-engine/ai-tutor-reference/`

The implementation must use deterministic fake provider adapters only. No external AI network/API calls in this task.

Minimum useful components:

1. normalized provider-neutral request/response/event contract;
2. server-side Tutor orchestrator boundary;
3. deterministic fake provider adapter(s);
4. strict tool-intent allowlist/mediation boundary;
5. verified-subject-context and PEIS-context projection validation;
6. deterministic tests/validator;
7. durable contract/result evidence.

Avoid a framework. Prefer Python standard library / existing project patterns unless a concrete existing dependency is clearly better.

## REQUIRED ARCHITECTURAL BOUNDARY

### A. Server-owned Tutor request

The full internal Tutor turn may contain only what the server has legitimately resolved for the active episode, for example:

- opaque Tutor session ref;
- subject id;
- current learning goal/semantic target refs;
- bounded read-only PEIS context projection;
- verified subject context/source refs;
- relevant text/structured Tutor history;
- learner message;
- allowed tool descriptors;
- deterministic policy flags supplied by the server.

Do not make browser-provided canonical `learner_profile_id`, mastery/readiness/retention/NBA or correctness authoritative.

### B. Provider request minimization

The provider adapter must receive a minimized payload, not the full internal learner object.

Default rules:

- no e-mail;
- no phone;
- no payment/payer data;
- no production auth token/session secret;
- no raw database row;
- no browser-authoritative learner state;
- no need for a stable personally identifying learner id;
- only the bounded educational context needed for the turn.

If an opaque correlation/session value is required by the fake contract, it must not be a canonical learner identifier and must be replaceable.

### C. Trusted context classes

The contract must distinguish at minimum:

1. server/system policy authority;
2. verified subject context/source refs;
3. read-only PEIS context projection;
4. prior Tutor text history;
5. current learner/untrusted text.

Learner text or retrieved free-form text cannot silently promote itself into verified subject authority.

### D. Provider output is advisory

Provider response MAY contain normalized conversational output and bounded tool intents.

Provider response MUST NOT be accepted as authoritative values for:

- correctness;
- mastery;
- readiness;
- retention state;
- Next Best Action;
- semantic identity admission;
- source truth;
- learner identity linking;
- payment/entitlement.

If a malicious/fake provider returns fields attempting these mutations, the orchestrator must reject or ignore them deterministically and tests must prove it.

### E. Independent verification policy cannot be disabled by provider

The orchestrator/server policy owns whether the current interaction requires subsequent independent verification.

Provider output cannot downgrade/clear an already-required verification flag.

This task does not need to invent the final pedagogical help classifier; it only must prove that the provider cannot override the server-owned requirement.

### F. Tools are server-mediated

Provider may emit a `tool_intent`/function-call-like normalized request only for tools in the server-provided allowlist.

Provider does NOT:

- run arbitrary shell/code;
- query DB directly;
- write PEIS directly;
- mint semantic ids;
- submit EvidenceEvents directly;
- mutate learner identity.

Unknown/unapproved tool intent must be rejected safely.

### G. Source grounding boundary

The provider response may refer only to verified source refs supplied for the turn when it claims grounding/source provenance.

A provider-emitted source ref outside the allowed set must be rejected/flagged, never silently accepted as verified truth.

This task need not solve full RAG/retrieval. It proves the contract around already-supplied verified context.

### H. Provider failure / fail-open product

Provider timeout/error/malformed output must produce a stable Tutor-unavailable result without corrupting PEIS state.

The base deterministic product/PEIS loop must remain logically usable.

No browser/product wiring is required in this task.

### I. Audio exclusion

This task is text-boundary only.

Do not add learner audio bytes/files/blobs/paths/embeddings/voiceprints/acoustic features to any persisted/request contract.

If a future voice extension point is named, it must be explicitly transient and outside persisted Tutor state.

## FAKE PROVIDER REQUIREMENT

Implement at least two deterministic fake provider configurations/adapters sufficient to prove the orchestrator is provider-neutral.

Example behaviors to test:

- normal grounded answer;
- provider unavailable/error;
- unknown tool intent;
- invented source ref;
- attempted mastery/correctness/NBA mutation;
- attempt to clear `verification_required`.

Do not emulate a full LLM. The fakes exist to prove boundaries.

## REQUIRED TESTS

At minimum prove deterministically:

1. provider adapter can be swapped without changing the orchestrator public contract;
2. minimized provider payload excludes direct canonical learner identity and secret/contact data;
3. verified source refs and learner text remain separate context classes;
4. provider cannot alter correctness;
5. provider cannot alter mastery;
6. provider cannot alter readiness;
7. provider cannot alter retention;
8. provider cannot alter NBA;
9. provider cannot mint/admit semantic ids;
10. provider cannot clear an existing independent-verification requirement;
11. allowed tool intent is normalized but not directly executed by provider;
12. unknown tool intent is rejected;
13. source ref outside supplied verified allowlist is rejected/flagged;
14. malformed/provider error returns stable Tutor-unavailable result;
15. no canonical PEIS write occurs in the provider boundary;
16. no audio persistence field/path exists in the reference contract;
17. existing directly affected PEIS validators remain green;
18. deterministic validator/run repeated twice yields identical canonical result artifacts/hashes if materialization is used.

Also run Python compilation / repository-equivalent static checks for changed code.

## ALLOWED_PATHS

Prefer add-only:

- `eksamio-learning-engine/ai-tutor-reference/**`

The task file may be updated with exact result pointers if useful.

Existing shared/reference PEIS modules may be changed only if a tiny compatibility import is genuinely necessary and all existing contracts/tests remain unchanged semantically. Prefer not to change them.

## FORBIDDEN_PATHS / SCOPE

Do not modify:

- accepted demos/trainers;
- Tilda;
- Russian/Mathematics/Physics source truth;
- subject answers/scoring;
- canonical semantic identities;
- Evidence/Mastery/Readiness/Retention/NBA contract semantics;
- PEIS production substrate implementation except read/import reuse;
- auth implementation;
- payment/entitlement;
- Yandex cloud resources;
- public API/DNS;
- provider secrets;
- production provider SDK/config;
- voice/STT/TTS runtime;
- learner audio storage of any kind.

Do not call OpenAI, Google, YandexGPT or any other external model in this task.

## ACCEPTANCE_EVIDENCE

Return:

- actual baseline/current main SHA;
- branch;
- commit SHA;
- PR number/URL;
- files changed;
- normalized contract/version;
- exact test commands/results;
- fake provider swap result;
- forbidden canonical-state mutation tests;
- tool allowlist tests;
- source allowlist tests;
- provider failure result;
- existing PEIS regression results;
- deterministic artifact hashes if applicable;
- `EXTERNAL_AI_CALLS=0`;
- `PROVIDER_SECRETS_ADDED=0`;
- `PUBLIC_TRAFFIC_CONNECTED=false`;
- `PEIS_CANONICAL_CONTRACTS_CHANGED=false`;
- `SUBJECT_SOURCE_CHANGED=false`;
- `TILDA_CHANGED=false`;
- `LEARNER_AUDIO_PERSISTED=false`;
- blockers.

## STOP_CONDITIONS

STOP and return an exact blocker rather than broadening if:

- the boundary requires changing canonical PEIS semantics;
- a provider-specific SDK/contract appears necessary before a generic boundary can be defined;
- authoritative learner identity must be sent to provider for a reason not already approved;
- the implementation requires production auth/cloud/provider credentials;
- a tool path would let the provider write learner state directly;
- learner audio persistence becomes necessary;
- a subject-specific AI/learner engine is required.

## FINAL_STATUS

Success only:

`AI_TUTOR_PROVIDER_NEUTRAL_BOUNDARY_READY_FOR_GROUNDED_TEXT_SLICE`

Otherwise return one exact blocker, for example:

- `BLOCKED_AI_TUTOR_PEIS_BOUNDARY_CONFLICT`
- `BLOCKED_AI_TUTOR_PROVIDER_ABSTRACTION`
- `BLOCKED_AI_TUTOR_TOOL_SECURITY_BOUNDARY`
- `BLOCKED_AI_TUTOR_CONTEXT_PRIVACY_BOUNDARY`
