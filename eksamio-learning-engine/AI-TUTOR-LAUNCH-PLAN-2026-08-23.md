# Eksamio AI Tutor — launch execution plan

**Status:** ACTIVE CENTRAL P0 DIRECTION / PRE-PRODUCTION EXECUTION  
**Date:** 2026-08-23  
**Baseline main at plan creation:** `f7107e1eacce9ac21ce92fcf2778bcaeb649d069`  
**Owner:** Central Brain  
**Primary engineering executor:** Codex  
**Launch target:** first paid Eksamio Pro, Russian web product, text + realtime voice as one Tutor

This plan is an execution authority for the AI Tutor direction. It does not authorize public AI traffic, a specific production model/provider, or paid launch by itself.

## 1. Product outcome

Eksamio AI Tutor is not a generic chatbot. It is the conversational help layer of one shared PEIS learning loop:

`diagnose -> learner state -> next learning goal -> practice/help -> independent verify -> retain -> reassess -> replan`.

The Tutor must improve measurable learning outcomes by using verified subject truth and bounded PEIS context while never becoming the owner of canonical identity, correctness, mastery, readiness, retention, source truth or Next Best Action.

First paid Pro launch requires BOTH:

1. production-ready text Tutor;
2. production-ready realtime voice Tutor;

with seamless `voice -> text -> voice` continuity inside one Tutor session/learning episode.

## 2. Hard invariants

These are launch-blocking, not preferences.

- one shared PEIS only;
- verified subject/source truth remains outside provider-generated content;
- browser never supplies authoritative learner identity/mastery;
- model/provider output never writes canonical mastery/readiness/retention/NBA directly;
- deterministic/server evaluator owns correctness acceptance;
- substantial Tutor help requires independent verification before mastery advancement;
- a learner saying “I understand” is not mastery evidence;
- provider-neutral architecture; no end-user OpenAI/Google/Yandex account dependency;
- automatic fallback only among explicitly production-admitted providers;
- learner does not choose provider;
- product must work for learners in Russia without VPN;
- learner browser must not require direct access to a foreign AI provider;
- no learner audio persistence of any kind, including recordings, fragments, voiceprints, embeddings or acoustic vectors;
- text/structured Tutor history may be persisted only under explicit privacy/retention controls;
- deterministic/base product must survive Tutor/provider outage;
- Tilda remains public/free-demo layer; Pro Tutor lives in the separate Eksamio web application/service contour.

## 3. Current dependency state

AI Tutor production connection is intentionally downstream of the production PEIS boundary.

Current upstream work:

- `PEIS-PRODUCTION-SUBSTRATE-001` — active Codex implementation;
- `PEIS-YANDEX-STAGING-001` — next central cloud slice after substrate PASS;
- Russian RU-1 canonical mapping — active landing; this provides the preferred first subject slice;
- first Russian production-shaped PEIS live-connection slice — starts after mapping + PEIS substrate/staging readiness.

The Tutor direction can nevertheless begin NOW on provider-neutral boundaries, evaluation, policy contracts and deterministic harnesses because those do not require a live provider or public PEIS traffic.

## 4. Target architecture

Production shape:

`Eksamio web app`
-> `Eksamio authenticated/trusted server edge`
-> `Tutor Orchestrator`
-> bounded read-only `PEIS Context Projection`
-> bounded `Verified Subject Context`
-> `AI Provider Gateway`
-> approved conversational provider

The provider may request server tools through a strict allowlist. It does not execute privileged actions directly.

Tutor result returns through the orchestrator, which enforces policy, records structured Tutor interaction metadata where allowed, and routes any later assessment to the normal deterministic/shared PEIS path.

Voice adds replaceable speech adapters around the SAME Tutor session:

`browser microphone (transient)`
-> realtime speech transport/STT
-> Tutor Orchestrator / AI Provider Gateway
-> TTS
-> browser playback

Audio is transient pipeline data only. No Eksamio persistence path may accept learner audio.

## 5. Workstream T0 — provider-neutral Tutor boundary (START NOW)

**Executor:** Codex  
**Task:** `tasks/AI-TUTOR-PROVIDER-NEUTRAL-BOUNDARY-001.md`

Purpose: prove the product/provider boundary before any real provider SDK or cloud secret is introduced.

Required proof:

- normalized provider-neutral request/response contract;
- provider sees only a bounded PEIS context projection, not canonical identity machinery;
- verified source context is explicitly separated from learner/untrusted text;
- provider cannot write/override correctness, mastery, readiness, retention or NBA;
- provider tool intents are mediated by server allowlist;
- provider failure degrades Tutor availability without breaking base PEIS/product;
- deterministic fake provider(s) prove provider replacement;
- no audio fields/storage path in the text boundary;
- existing PEIS contracts remain unchanged.

Expected status:

`AI_TUTOR_PROVIDER_NEUTRAL_BOUNDARY_READY_FOR_GROUNDED_TEXT_SLICE`

## 6. Workstream T1 — Tutor evaluation harness (after T0)

Create a deterministic provider-independent evaluation corpus/harness before selecting a production model.

It must test at minimum:

### Grounding / truth

- no contradiction of supplied verified source truth;
- no invention of official answer/scoring/criterion facts;
- no source ref outside the server-provided allowlist;
- uncertainty is surfaced rather than fabricated;
- prompt injection inside learner text or retrieved content cannot redefine canonical authority.

### Pedagogy

- hints/guided help do not masquerade as mastery;
- substantial help triggers independent-verification requirement;
- repeated failure changes explanation/diagnosis rather than auto-advancing;
- prerequisite repair can be suggested through normal PEIS/NBA boundaries;
- full worked solution may be shown only as help, never mastery evidence;
- off-topic conversation is bounded and returns to the learning objective.

### Security / privacy

- no secret leakage;
- no authoritative learner identifier leakage to provider unless a future gate explicitly proves need (default: do not send it);
- no provider-originated canonical state mutation;
- no audio persistence;
- safe failure on malformed/tool-injection outputs.

### Reliability / economics

- provider timeout/error handling;
- retry/idempotency behavior where applicable;
- token/context budgets measured;
- cost per representative learning episode measured before commercial quotas are chosen.

Do not choose a production provider solely on synthetic benchmark score; include real Russian tutoring dialogue and subject-expert review.

## 7. Workstream T2 — first grounded TEXT Tutor vertical slice

**Dependency gate:**

- provider-neutral boundary PASS;
- PEIS production substrate PASS;
- Yandex staging contour available;
- one production-shaped Russian PEIS mapping/live slice available;
- trusted server identity path available for staging (full commercial auth may follow before external pilot).

First slice should be deliberately narrow and real, preferably one Russian capability cluster from the accepted 121-card mapping.

Required flow:

`learner turn`
-> server-owned learner/session resolution
-> PEIS selects/exports bounded current learning context
-> server fetches verified subject context
-> Tutor produces grounded help
-> help metadata is recorded without claiming mastery
-> learner gets a NEW independent verification item
-> deterministic evaluator scores it
-> EvidenceEvent enters PEIS
-> state/NBA update comes from shared PEIS, not the model.

No public rollout in this slice.

Success status:

`AI_TUTOR_GROUNDED_TEXT_VERTICAL_SLICE_PASS`

## 8. Workstream T3 — conversational provider admission

Production provider choice is a gate, not an early lock-in.

Every candidate must pass the same provider-neutral evaluation harness plus:

- Russia accessibility/operability;
- legal/contractual availability for the production contour;
- security/data-handling review;
- Russian-language pedagogical quality;
- tool/function reliability;
- latency and streaming behavior;
- cost/quotas;
- failure/fallback behavior.

### Current candidate state (verified 2026-08-23)

**Yandex AI Studio / YandexGPT family**

- Russia-native cloud candidate;
- supports synchronous/streaming dialog and OpenAI-compatible APIs;
- strong candidate for the first Russia-safe conversational baseline;
- must still pass Eksamio pedagogical quality/tooling benchmark; no automatic admission.

Official references:
- https://yandex.cloud/en/docs/ai-studio/
- https://yandex.cloud/en/docs/overview/api
- https://yandex.cloud/en/docs/foundation-models/concepts/yandexart/

**OpenAI Realtime / Responses**

- technically strong candidate for natural realtime dialogue, WebRTC and tool/function calling;
- Russia is not currently listed in OpenAI API supported countries/territories;
- therefore OpenAI may NOT be the sole production dependency and is not production-admitted by this plan.

Official references:
- https://platform.openai.com/docs/guides/realtime
- https://platform.openai.com/docs/guides/realtime-conversations
- https://developers.openai.com/api/docs/supported-countries

**Google Gemini Live**

- technically strong realtime candidate with Live API, WebSockets and ephemeral client tokens;
- Russia is not currently listed in Gemini API / Google AI Studio available regions;
- direct client-to-Gemini is also contrary to the current Eksamio “browser does not depend on foreign provider” launch boundary;
- therefore no production admission without a separate legal/accessibility architecture gate.

Official references:
- https://ai.google.dev/gemini-api/docs/live-api
- https://ai.google.dev/gemini-api/docs/live-api/ephemeral-tokens
- https://ai.google.dev/gemini-api/docs/available-regions

Provider admission result must explicitly name at least one primary and, before broad paid launch where practical, one approved fallback or an acceptable Tutor-unavailable fail-open mode.

## 9. Workstream T4 — realtime speech layer

**Priority speech candidate:** Yandex SpeechKit.

Current verified capabilities include bidirectional/streaming STT and streaming TTS suitable for low-latency voice interfaces.

Official references:
- https://yandex.cloud/ru/docs/speechkit/stt-v3/api-ref/grpc/Recognizer/recognizeStreaming
- https://yandex.cloud/en/docs/speechkit/tts-v3/api-ref/grpc/Synthesizer/streamSynthesis

Required design:

- learner audio exists only transiently in the active realtime pipeline;
- no object storage, DB, logs, analytics payloads, backups, vector store or model-training dataset may receive learner audio;
- no voiceprint/speaker embedding persistence;
- STT transcript may enter the text Tutor session only under the same text/history privacy policy;
- Tutor text response and voice response are two renderings/interfaces of the same session state;
- interruption/barge-in and turn cancellation must not duplicate PEIS writes or verification events;
- network/speech failure falls back to text without losing the learning episode.

Success status:

`AI_TUTOR_REALTIME_VOICE_SLICE_PASS`

## 10. Workstream T5 — unified text/voice session continuity

Prove all of these in one staging episode:

1. begin in voice;
2. switch to text;
3. continue the same learning goal/context/history;
4. switch back to voice;
5. complete independent verification;
6. PEIS receives exactly one valid verification evidence chain;
7. no learner audio is persisted;
8. provider/speech failure can fall back without state corruption.

Success status:

`AI_TUTOR_TEXT_VOICE_CONTINUITY_PASS`

## 11. Workstream T6 — identity, history, privacy and minor-safe product gate

Before external learner pilot:

- passwordless/trusted learner identity must resolve server-side;
- anonymous -> account continuity must preserve the same learner evidence semantics;
- Tutor text/structured history schema and retention/deletion rules must be explicit;
- logs minimize learner identifiers and contain no secrets/audio;
- age-appropriate educational/safety behavior for grade 10–11 users must be reviewed;
- parent visibility must follow the established privacy boundary rather than exposing private Tutor conversation by default;
- legal/privacy copy must explicitly state that learner audio is not stored.

A material legal/privacy question that cannot be inferred is escalated to owner at this gate, not earlier.

## 12. Workstream T7 — production hardening

Before paid launch:

- provider secrets in Lockbox/approved secret manager;
- rate limits and abuse controls;
- per-session/token/cost limits;
- provider circuit breaker;
- approved-provider fallback policy;
- kill switch that disables Tutor while deterministic/base learning remains usable;
- monitoring for latency/error/tool failures;
- no prompts/context/secrets leaked in error responses;
- deployment rollback;
- staging/prod separation;
- load/soak testing for representative text + voice concurrency.

Commercial quota/cost numbers should be chosen only after real usage/cost measurements. If the resulting cost envelope materially changes Pro pricing/quota, Central Brain must bring that concrete decision to the owner.

## 13. Acceptance scorecard

Launch-blocking invariants:

- canonical source contradiction in accepted critical test set: `0`;
- unauthorized canonical state/mastery/correctness writes: `0`;
- substantial-help cases bypassing required independent verification: `0`;
- learner audio persisted: `0`;
- browser authoritative identity/mastery input accepted: `0`;
- accepted provider secrets exposed to client/logs/repo: `0`;
- voice/text session corruption in continuity acceptance set: `0`;
- base deterministic product unavailable solely because Tutor/provider is down: `0`.

Quality budgets (latency, tutoring-quality score, cost/session) are measured and versioned during T1–T4. Do not invent a launch threshold before representative measurements exist; once measured, Central Brain sets the smallest defensible threshold and records it before production admission.

## 14. Rollout sequence

### Stage A — reference/internal

Fake provider + deterministic harness only.

### Stage B — provider sandbox

Real provider(s), synthetic/staging learner context, no public learner traffic.

### Stage C — internal grounded Russian vertical slice

Real staging PEIS + verified Russian content + independent verification.

### Stage D — closed learner pilot

Authenticated limited cohort, Tutor kill switch, strict quotas/monitoring, text first plus voice when T4/T5 gates are ready.

### Stage E — paid trial readiness

One discounted paid full-cycle AI trial session only after legal/payment/entitlement and BOTH text+voice Tutor launch gates pass.

### Stage F — first paid Pro

Allowed only when text Tutor + realtime voice + continuity + PEIS/auth/security/privacy/provider admission + mobile web launch gates pass.

## 15. Immediate execution queue

1. **NOW** — `AI-TUTOR-PROVIDER-NEUTRAL-BOUNDARY-001` via Codex.
2. Brain reviews/merges only if boundary invariants and regressions PASS.
3. `AI-TUTOR-EVAL-HARNESS-001` — build deterministic grounding/pedagogy/security corpus.
4. In parallel, finish current PEIS substrate and Yandex staging prerequisites.
5. Finish Russian RU-1 mapping and first production-shaped live PEIS slice.
6. `AI-TUTOR-GROUNDED-TEXT-001` — first real Russian Tutor loop.
7. Run Yandex/OpenAI/Google/other eligible provider candidates through one harness; only legally/accessibly deployable candidates can become production-approved.
8. `AI-TUTOR-SPEECHKIT-REALTIME-001` — transient STT/TTS layer.
9. `AI-TUTOR-TEXT-VOICE-CONTINUITY-001`.
10. privacy/minor-safe/retention gate.
11. production hardening, cost/quota, pilot.
12. paid launch admission.

## 16. STOP conditions

Stop the affected slice and return to Central Brain if it requires:

- provider-specific changes to canonical PEIS contracts;
- browser-owned learner identity/mastery;
- storing learner audio;
- AI-generated official subject truth;
- bypassing independent verification to improve UX metrics;
- a foreign provider as the only path for a Russia no-VPN launch;
- putting provider secrets in client/Git;
- a second subject-specific learner engine;
- public AI traffic before production PEIS/security/auth gates;
- materially new commercial/legal/privacy commitments without owner decision.

## 17. Direction status

At plan creation:

`AI_TUTOR_DIRECTION_ACTIVE_PREPRODUCTION`

First executable unlock sought now:

`AI_TUTOR_PROVIDER_NEUTRAL_BOUNDARY_READY_FOR_GROUNDED_TEXT_SLICE`
