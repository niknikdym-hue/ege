# Eksamio — Current Brain Handoff

**Status:** CURRENT OPERATING HANDOFF  
**Date:** 2026-08-23  
**Repository:** `niknikdym-hue/ege`  
**Baseline when refreshed:** `85b1f4316cf33dc6ab0eebce2e9281b6432e4bbb`

> This file is the shortest current entry point for a new ChatGPT/Brain/Codex session. It does not replace the Product Masterplan or subject/source authorities. Always refresh `main` before acting. Where older documents contain stale operational start/read-order instructions, this current handoff plus current `AGENTS.md` supersede those pointers; their substantive architecture/content remains valid unless separately superseded.

Current approved owner-decision addendum: `OWNER-DECISIONS-2026-08-22.md`. Read it for any work involving Pro launch, Tutor channels, product client, Russia accessibility, cloud, providers, audio privacy, identity/auth or payments.

Latest execution checkpoint at this refresh: `worklog/2026-08-23-EKSAMIO-BRAIN-CHECKPOINT-11-EXECUTION-RESET.md`.

## 1. Product identity

Eksamio is a **Personal Exam Intelligence System (PEIS)**, not a collection of unrelated demos and trainers.

Core free learning loop:

`diagnose -> model -> prioritize -> practice/help -> verify -> retain -> reassess -> replan`

The system optimizes for demonstrated change in learner knowledge state, not chat length, clicks or time on site.

## 2. Product bar: world-leading, measurable, economical

Eksamio is designed to reach the **leading edge of current educational technology**, not merely reproduce the world baseline.

The operating benchmark is `PRODUCT-BENCHMARK-2026.md` plus `270-EKSAMIO-AI-TUTOR-WORLD-BENCHMARK-2026-v1.0.txt`.

The standard is not a marketing claim such as “best in the world” without evidence. Internally, every major product decision should be judged against measurable world-level outcomes, including:

- exam/source fidelity;
- next-item correctness;
- transfer;
- retention;
- repeat-error reduction;
- mastery gain / score gain per study minute;
- calibrated forecast quality;
- cost per successful learning intervention;
- AI factual/source-grounding error rate;
- measurable exam/control improvement.

A feature that only reproduces generic chatbot, adaptive-plan, voice or dashboard behavior is not sufficient differentiation.

At the same time, **advanced must not mean expensive**.

Architecture should minimize recurring cost and moving parts:

- deterministic tools before model calls where possible;
- small/cheap models for simple grounded tasks and stronger models only when justified;
- compact context, targeted retrieval and caching where useful;
- no expensive frontier model for every event;
- no always-on paid infrastructure without measured need;
- provider adapters, fallback and kill switch;
- reuse existing verified infrastructure instead of duplicating services;
- optimize `cost per successful learning outcome`, not token usage or technical grandeur.

If a proposed architecture is more expensive or complex without a measurable learning/product gain, reject or simplify it.

## 3. One shared PEIS

All subjects reuse one shared platform layer for:

- learner evidence;
- learner semantic state;
- mastery inference;
- prerequisite/readiness;
- retention;
- Next Best Action / recommendation;
- learner identity and persistence boundaries.

A subject may own verified source truth, semantic identities, prerequisite relations, exam-route mappings and teaching/practice content. A subject must not create a parallel Student Model or PEIS engine.

## 4. Subscription/provider independence

Eksamio production architecture must work **without any ChatGPT/OpenAI subscription**.

This means:

- ChatGPT Plus/Pro and Codex are development/execution tools, never runtime dependencies of the product;
- the base Eksamio learning loop must remain usable if the project owner has no OpenAI subscription at all;
- learner identity, evidence, state, mastery, readiness, retention, NBA, official scoring, source truth and deterministic tools must not depend on an OpenAI account or subscription;
- premium AI features may call paid model APIs, but only through replaceable provider adapters and explicit Eksamio-side entitlement/cost policy;
- no learner should need their own ChatGPT/OpenAI subscription to use Eksamio;
- loss of one AI provider must degrade only the provider-dependent enhancement, not corrupt learner state or disable the base learning system;
- AI-provider absence must have a defined fallback: deterministic/base experience continues, while unavailable AI-only actions are disabled or routed to another approved provider when configured;
- no provider-specific model ID, auth model, billing plan or proprietary conversation state may become canonical PEIS state.

Existing Tutor Core provider-neutral routing, fallback and kill-switch rules remain authority for AI integrations. The stronger product invariant here is that **OpenAI itself is optional to Eksamio runtime**.

## 5. Owner decisions now in force

- First paid Pro launch requires both text and realtime voice interfaces of one Tutor; text-only and voice-only launch are forbidden.
- Voice is a P0 launch capability, not a separate Tutor and not permission to bypass the shared PEIS closed loop or production foundations.
- First Pro client is a separate desktop/mobile-browser web application; Tilda remains public/free-demo and does not own accounts, PEIS, Tutor, payments or canonical learner state.
- Russia/no-VPN operation is a hard invariant, including realtime voice; the learner browser does not call a foreign AI service directly.
- Primary production cloud is Yandex Cloud Russia, while canonical state and core logic remain portable/provider-neutral.
- OpenAI/Google conversational AI and Yandex SpeechKit are candidates, not production-approved providers. Admission and fallback are gate-controlled.
- Learner audio is never stored in any form; only transient realtime processing is allowed. Text/structured Tutor history may exist under privacy/retention controls.
- Pro auth is passwordless by verified e-mail or phone; anonymous same-device progress must link safely to a later account without making the browser identity authority.
- Robokassa + Robocheki SMZ is the first replaceable NPD payment candidate and still requires separate legal/API/webhook/receipt/SBP-card/refund/failure gates.
- Routine/reversible evidence-backed implementation and pedagogical decisions should be resolved by Central Brain without owner-question spam; owner questions are reserved for genuinely material decisions.

Full authority and learning-policy details: `OWNER-DECISIONS-2026-08-22.md`.

## 6. Current platform state

Merged/validated reference sequence already reaches:

`verified subject truth`
→ `semantic identity`
→ `EvidenceEvent`
→ `shared persistence`
→ `shared PEIS inference`
→ `NBA`
→ `current-product-shaped sensor`
→ `subject-neutral service boundary`
→ `fail-open browser hook`
→ `trusted host identity boundary`

The latest central durable Brain checkpoint is:

`worklog/2026-08-23-EKSAMIO-BRAIN-CHECKPOINT-11-EXECUTION-RESET.md`

The current central blocker is:

`PEIS-DEPLOYMENT-SECURITY-001`

Before any public PEIS browser traffic, the production deployment/security envelope must be explicitly chosen, implemented and validated. Do not treat reference HTTP, SQLite or reference HMAC identity as production infrastructure.

Central work now starts from concrete sub-gaps of this blocker; do not create adjacent infrastructure unless it has an explicit `EXPECTED_UNLOCK`.

## 7. Current subject lanes

### Russian — P0 / active

Russian remains the first subject and the main active subject-program / semantic integration lane.

Current important open work:

- PR #72 — active draft/read-only integration ledger lane. Working invariants: `121 active / 88 exception IDs / 91 EXACT / 5 PARTIAL_COMPOSITE / 25 BLOCKED / 96 integration-ready / 0 live-connected / 35 existing canonical school identities / 0 new ru-* admitted`.
- PR #57 — HOLD; draft semantic canonicalization proposal only. Proposed `ru-*` identities are not canonical authority.
- PR #23 — valuable reviewed 121-card Exceptions content checkpoint, still draft and not blanket merge authority.

Do not restart the broad 185×174 audit as a new project. Continue by delta. The next Russian output should be a bounded decision/reconciliation packet; any required write/rebase/validator implementation goes through an explicit Codex task.

### Mathematics — P0 system subject; broad PROFILE build lane closed

Mathematics remains the second P0 subject of the shared PEIS architecture.

The broad historical **PROFILE Mathematics EGE preparation cycle for 2022–2026 is closed for normal work**. Do not keep a permanent chat working on those historical demo packages merely because the old conversation exists.

Current accepted/finalized state includes:

- PROFILE 2026 — accepted technical reference;
- PROFILE 2025 — accepted technical reference;
- PROFILE 2023 — accepted/frozen, with its regression lessons carried forward;
- PROFILE 2022 — `READY_FOR_TILDA / FROZEN`, 18 tasks, 35/35 official FIPI examples accepted.

#### Known narrow exception: PROFILE 2024 UI parity

`main` still contains `matematika-source-2024/PROFILE-2024-UI-PARITY-FINDING.txt` with a confirmed defect: source labels and extended-result headings omit the assigned official example number.

This is not permission to reopen Mathematics broadly. Handle it as one bounded repair:

`targeted UI fix -> exact regression/browser verification -> durable acceptance/freeze -> close`

Do not change 2024 source truth, answers, scoring, criteria, task order or semantic state as part of that repair.

After the narrow 2024 repair, Mathematics work should resume only for a real next dependency: Mathematics Identity Model / PEIS integration / base route / telemetry / new explicitly approved product work.

### Physics — P1 / bounded 2024 lane active

Physics is the third subject and may proceed in parallel without slowing P0/central blocker work.

Current facts:

- Physics 2026 remains the frozen technical/runtime/layout reference (merged PR #49); it is not source authority for other years.
- Physics 2025 v1.5 result-order fix was subject-accepted and merged through PR #96. 2025 is frozen/closed again unless a new concrete finding appears.
- Physics 2024 official FIPI source contour exists under `ege-source-fizika/source-fizika-2024/`; derived source-access evidence landed through PR #97 outside the authority folder.
- Active 2024 flow is bounded: `source lock -> source/layout/visual registry -> Physics subject build packet -> deterministic Codex build -> bounded subject acceptance -> Tilda delivery`.

Physics 2024 must preserve `2025_CONTENT_USED=0` and `2026_CONTENT_USED=0`; 2026 may be used only as technical/runtime/layout reference.

## 8. Parallel-chat operating model

Parallel chats are allowed and useful, but they are execution lanes, not independent project brains.

Recommended active set:

1. **Eksamio Brain** — architecture, priorities, central blocker, cross-lane review, shared PEIS, merge decisions.
2. **Russian** — Russian subject program/content/semantic lane only.
3. **Physics** — current bounded 2024 source/demo lane only.

Do **not** keep a permanent Mathematics historical-demo chat active. The known PROFILE 2024 UI defect should be handled by one short-lived bounded task/worker, then that lane closes again.

A subject chat must not independently redesign shared PEIS contracts, learner identity, mastery, readiness, retention, NBA or cross-subject architecture.

## 9. Brain / Codex / Spark execution routing

Use the strongest reasoning only where it changes decisions or quality. Do not spend expensive reasoning on mechanical work.

### Mandatory task admission

Before issuing a significant task, Central Brain must be able to state:

`WHY_NOW -> ACTIVE_BLOCKER_OR_MILESTONE -> DEPENDENCY_IN -> MINIMAL_DELTA -> EXPECTED_UNLOCK -> cheapest sufficient EXECUTOR -> ACCEPTANCE_EVIDENCE -> STOP_CONDITIONS`.

If `EXPECTED_UNLOCK` is unclear, do not issue the task.

If an existing working process already solves the problem, reuse it. Do not invent a new CI, selector, staging layer, service or framework without a proven requirement. If a bounded task materially expands, stop and return the new blocker to Brain instead of turning it into an architecture project.

### Brain

Brain owns:

- product and architecture decisions;
- dependency order and bottleneck selection;
- cross-subject/shared-PEIS decisions;
- source/identity admission boundaries;
- production/security gates;
- review of risky or ambiguous PRs;
- deciding when a result is actually accepted.

Brain may directly perform small safe GitHub governance/evidence updates when write access exists; it should still use Codex for engineering-heavy implementation/testing rather than becoming a bulk code editor.

### Codex

Use Codex for engineering-heavy work that benefits from repository execution:

- multi-file implementation;
- builders/materializers/migrations;
- test suites and browser checks;
- CI/debugging;
- large deterministic transforms;
- source/package assembly with explicit gates;
- fixes that require running and iterating on code.

Codex must follow current `AGENTS.md`, branch/PR discipline and source/production boundaries.

### Spark

When available, Spark is an optional fast executor for **small, sharply bounded tasks** where the desired change is already known.

Do not use Spark to decide architecture, infer missing official source truth, approve semantic identities, or resolve ambiguous cross-system design.

For Spark tasks, required tests/checks must be stated explicitly; never assume they will be run automatically. Spark availability/limits are an execution convenience only. Any Spark task must remain executable by normal Codex or another approved environment if Spark is unavailable.

### Routing rule

Choose by **risk + ambiguity + execution weight**, not by prestige of the model:

- high ambiguity / architecture / irreversible decision -> Brain;
- substantial implementation / testing / repo iteration -> Codex;
- known answer + tiny bounded change -> Spark when available;
- deterministic local check with no AI need -> ordinary script/tool first.

The routing itself must reduce cost/time without lowering acceptance quality.

## 10. Durable communication with minimal bureaucracy

GitHub is the shared bus. Existing mechanisms are sufficient:

- task contract when a bounded task genuinely needs one;
- implementation branch/PR;
- validation/test evidence;
- `results/` artifact for completed implementation work when useful;
- review/status only when a real acceptance decision is needed.

Do not create duplicate reports just to report that another report exists.

A PR + its durable result/validation is normally enough evidence for a subject lane. A separate Brain checkpoint is needed only when project state meaningfully changes: major merge, blocker change, priority change, architecture decision, production gate change, or cross-lane conflict.

## 11. Brain cross-lane review rule

The Brain periodically checks parallel work, but **not by rerunning broad audits from zero**.

Cross-lane review inspects deltas since the last accepted state:

- new commits to `main` that affect Eksamio;
- opened/updated/merged subject PRs;
- changed blockers or acceptance status;
- changes touching shared PEIS contracts or cross-subject boundaries;
- contradictions between subject work and current authority;
- claims of DONE that lack durable evidence.

Review cadence:

- after a significant subject merge;
- before accepting a subject PR that can affect shared architecture or production;
- after a material architecture/product decision;
- once per working day only if meaningful parallel activity occurred.

If nothing material changed, do not manufacture a checkpoint or repeat an audit.

## 12. New-session continuity

A new Brain session should:

1. refresh current `main` HEAD;
2. read `00-PRODUCT-MASTERPLAN.md`;
3. read this file `00E-CURRENT-BRAIN-HANDOFF.md`;
4. read the current approved owner-decision artifact named above;
5. inspect current open PRs and the newest relevant worklog/result artifact;
6. read deeper governance/contracts only when the current task actually needs them;
7. continue only from verified repository state.

Subject chats should receive only their subject scope plus a pointer to this handoff and the relevant subject authority. They do not need old conversation transcripts.

## 13. Current next gates

### Central platform

`PEIS-DEPLOYMENT-SECURITY-001` is the immediate central bottleneck, constrained by Russia/no-VPN, portable Yandex Cloud, provider-admission, passwordless identity/payment contours and learner-audio non-storage.

The next central task must close a concrete sub-gap of this blocker and name its `EXPECTED_UNLOCK`.

### First paid Pro launch

Requires shared PEIS + production foundations + passwordless identity/payment gates + one continuous Tutor with both text and realtime voice production-ready. Do not launch a single-channel Pro.

### Russian

Continue PR #72 decision/reconciliation by delta; PR #57 remains HOLD; PR #23 is a content checkpoint, not automatic authority.

### Physics

Continue the bounded Physics 2024 official-source lane through source lock and subject build packet. Physics 2025/2026 remain frozen references as described above.

### Mathematics

Close the one known PROFILE 2024 UI-parity defect only as a bounded repair when scheduled; do not reopen the broad 2022–2026 lane. After that, resume Mathematics only for a real PEIS/base/product dependency.

## 14. Anti-chaos / efficiency rule

The project should become easier to reason about as it grows.

Prefer:

`current authority -> justified narrow task -> evidence -> merge/reject -> next dependency`

over
`new audit -> new meta-document -> new process -> audit of the process`.

If a proposed task/process does not reduce uncertainty, close a real gap, unlock the next dependency, prevent a demonstrated class of mistakes or improve measurable learning/production outcome, do not add it.

A tooling/cache/authentication limitation is not automatically a new product/source blocker. First use the shortest existing way to obtain the same authority or resume the existing authenticated flow.
