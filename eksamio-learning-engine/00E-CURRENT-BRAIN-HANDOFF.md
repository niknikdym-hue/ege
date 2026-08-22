# Eksamio — Current Brain Handoff

**Status:** CURRENT OPERATING HANDOFF  
**Date:** 2026-08-21  
**Repository:** `niknikdym-hue/ege`  
**Baseline when written:** `e25259f3789ab0c813d5816910803f8b2e4042dc`

> This file is the shortest current entry point for a new ChatGPT/Brain/Codex session. It does not replace the Product Masterplan or subject/source authorities. Always refresh `main` before acting. Where older documents contain stale operational start/read-order instructions, this current handoff plus current `AGENTS.md` supersede those pointers; their substantive architecture/content remains valid unless separately superseded.

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

## 5. Current platform state

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

`worklog/2026-08-20-EKSAMIO-BRAIN-CHECKPOINT-10-PEIS-TRUSTED-HOST.md`

The current central blocker is:

`PEIS-DEPLOYMENT-SECURITY-001`

Before any public PEIS browser traffic, the production deployment/security envelope must be explicitly chosen and validated. Do not treat reference HTTP, SQLite or reference HMAC identity as production infrastructure.

## 6. Current subject lanes

### Russian — P0 / active

Russian remains the first subject and the main active subject-program / semantic integration lane.

Current important open work:

- PR #72 — draft audit of the 121-card Exceptions bank for shared PEIS integration; read-only/product-safe scope; not yet main authority.
- PR #57 — draft semantic Phase 2 canonicalization proposal; proposal/HOLD boundary remains important; no automatic admission of proposed `ru-*` identities.
- PR #23 — valuable reviewed 121-card Exceptions bank, still draft and not production authority.

Do not restart the broad 185×174 audit as a new project. Continue from current Russian authorities and current PR state.

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

### Physics — P1 / active quality gate

Physics is the third subject and may proceed in parallel without slowing P0 work.

Current facts:

- merged PR #49 — Physics 2026 accepted technical reference with official-source visuals and exam tools;
- open draft PR #48 — Physics 2025 exact source and archive build;
- PR #48 must not be merged merely because it is mergeable.

The active 2025 Physics lane requires concrete quality revalidation before acceptance: verify source truth, year isolation, task/example completeness, browser behavior, regression against the accepted 2026 technical reference where legitimately applicable, and absence of silent reconstruction. Correct concrete defects in the active PR; do not create another broad audit program around it.

## 7. Parallel-chat operating model

Parallel chats are allowed and useful, but they are execution lanes, not independent project brains.

Recommended persistent active set on the Pro account:

1. **Eksamio Brain** — architecture, priorities, cross-lane review, shared PEIS, merge decisions.
2. **Russian** — Russian subject program/content/semantic lane only.
3. **Physics** — Physics source/demo/identity lane only, currently quality-gated.

Do **not** keep a permanent Mathematics historical-demo chat active. The known PROFILE 2024 UI defect should be handled by one short-lived bounded task/worker, then that lane closes again.

A subject chat must not independently redesign shared PEIS contracts, learner identity, mastery, readiness, retention, NBA or cross-subject architecture.

## 8. Brain / Codex / Spark execution routing

Use the strongest reasoning only where it changes decisions or quality. Do not spend expensive reasoning on mechanical work.

### Brain

Brain owns:

- product and architecture decisions;
- dependency order and bottleneck selection;
- cross-subject/shared-PEIS decisions;
- source/identity admission boundaries;
- production/security gates;
- review of risky or ambiguous PRs;
- deciding when a result is actually accepted.

Brain should not become a bulk file editor when a bounded executor can do the work safely.

### Codex

Use Codex for engineering-heavy work that benefits from repository execution:

- multi-file implementation;
- builders/materializers/migrations;
- test suites and browser checks;
- CI/debugging;
- large deterministic transforms;
- source/package assembly with explicit gates;
- fixes that require running and iterating on code.

Codex must still follow current `AGENTS.md`, branch/PR discipline and source/production boundaries. A strong model inside Codex is appropriate when the task is complex or architecture-sensitive.

### Spark

When available, Spark is an optional fast executor for **small, sharply bounded tasks** where the desired change is already known, for example:

- one-file or very small localized fixes;
- straightforward test additions;
- mechanical refactors with exact boundaries;
- quick repository inspection/probes;
- narrow UI/label fixes such as the known PROFILE 2024 parity repair, if the task contract is exact.

Do not use Spark to decide architecture, infer missing official source truth, approve semantic identities, or resolve ambiguous cross-system design.

For Spark tasks, required tests/checks must be stated explicitly; never assume they will be run automatically. Spark availability/limits are an execution convenience only. Any Spark task must remain executable by normal Codex or another approved environment if Spark is unavailable.

### Routing rule

Choose by **risk + ambiguity + execution weight**, not by prestige of the model:

- high ambiguity / architecture / irreversible decision -> Brain;
- substantial implementation / testing / repo iteration -> Codex;
- known answer + tiny bounded change -> Spark when available;
- deterministic local check with no AI need -> ordinary script/tool first.

The routing itself must reduce cost/time without lowering acceptance quality.

## 9. Durable communication with minimal bureaucracy

GitHub is the shared bus. Existing mechanisms are sufficient:

- task contract when a bounded task genuinely needs one;
- implementation branch/PR;
- validation/test evidence;
- `results/` artifact for completed implementation work;
- review/status only when a real acceptance decision is needed.

Do not create duplicate reports just to report that another report exists.

A PR + its durable result/validation is normally enough evidence for a subject lane. A separate Brain checkpoint is needed only when project state meaningfully changes: major merge, blocker change, priority change, architecture decision, production gate change, or cross-lane conflict.

## 10. Brain cross-lane review rule

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

## 11. Migration to the Pro account

The Pro account should become the primary **development/Brain working account** for Eksamio because stronger reasoning is useful for the project. This does not create any product dependency on the Pro plan.

Do not attempt to recreate old chat history manually. The repository is the handoff.

A new Brain session on Pro should:

1. fetch current `main` HEAD;
2. read `00-PRODUCT-MASTERPLAN.md`;
3. read this file `00E-CURRENT-BRAIN-HANDOFF.md`;
4. inspect current open PRs and the latest relevant worklog/result artifacts;
5. read deeper governance/contracts only when the current task actually needs them;
6. continue only from verified repository state.

Subject chats on Pro should receive only their subject scope plus a pointer to this handoff and the relevant subject authority. They do not need the full old conversation transcript.

### User action at migration time

The user should not manually summarize the old project or copy long chat histories.

For the new Pro account the required user actions are intentionally small:

1. connect/authorize access to repository `niknikdym-hue/ege` if the new account does not already have it;
2. open the new **Eksamio Brain** chat and instruct it to restore state from current `main` using `00-PRODUCT-MASTERPLAN.md`, `00E-CURRENT-BRAIN-HANDOFF.md` and current open PRs;
3. open separate **Russian** and **Physics** chats only after Brain has restored and checked the current state;
4. give each subject chat only its bounded subject role; do not paste the old conversations;
5. keep the old account/chats only as historical reference until the new Brain confirms repository-based continuity.

Everything else should be recoverable from GitHub.

## 12. Current next gates

Central platform:

`PEIS-DEPLOYMENT-SECURITY-001`

Russian:

continue current semantic/program integration from actual current-main/open-PR state without repeating broad historical audits.

Physics:

quality-review and correct the active 2025 lane before merge; preserve accepted 2026 reference.

Mathematics:

close the one known PROFILE 2024 UI-parity defect with a bounded repair and regression/freeze; do not reopen the broad 2022–2026 lane. After that, resume Mathematics only for a real PEIS/base/product dependency.

## 13. Anti-chaos rule

The project should become easier to reason about as it grows.

Prefer:

`current authority -> narrow task -> evidence -> merge/reject -> next dependency`

over
`new audit -> new meta-document -> new audit of the audit -> repeated reconstruction`.

If a proposed process does not reduce uncertainty, prevent a real class of mistakes, improve measurable learning outcome, or unblock delivery, do not add it.