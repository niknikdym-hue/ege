# Eksamio — Current Brain Handoff

**Status:** CURRENT OPERATING HANDOFF  
**Date:** 2026-08-21  
**Repository:** `niknikdym-hue/ege`  
**Baseline when written:** `e25259f3789ab0c813d5816910803f8b2e4042dc`

> This file is the shortest current entry point for a new ChatGPT/Brain/Codex session. It does not replace the Product Masterplan or subject/source authorities. Always refresh `main` before acting.

## 1. Product identity

Eksamio is a **Personal Exam Intelligence System (PEIS)**, not a collection of unrelated demos and trainers.

Core free learning loop:

`diagnose -> model -> prioritize -> practice/help -> verify -> retain -> reassess -> replan`

The system optimizes for demonstrated change in learner knowledge state, not chat length, clicks or time on site.

## 2. One shared PEIS

All subjects reuse one shared platform layer for:

- learner evidence;
- learner semantic state;
- mastery inference;
- prerequisite/readiness;
- retention;
- Next Best Action / recommendation;
- learner identity and persistence boundaries.

A subject may own verified source truth, semantic identities, prerequisite relations, exam-route mappings and teaching/practice content. A subject must not create a parallel Student Model or PEIS engine.

## 3. Current platform state

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

## 4. Current subject lanes

### Russian — P0 / active

Russian remains the first subject and the main active subject-program / semantic integration lane.

Current important open work:

- PR #72 — draft audit of the 121-card Exceptions bank for shared PEIS integration; read-only/product-safe scope; not yet main authority.
- PR #57 — draft semantic Phase 2 canonicalization proposal; proposal/HOLD boundary remains important; no automatic admission of proposed `ru-*` identities.
- PR #23 — valuable reviewed 121-card Exceptions bank, still draft and not production authority.

Do not restart the broad 185×174 audit as a new project. Continue from current Russian authorities and current PR state.

### Mathematics — P0 system subject; PROFILE demo 2022–2026 delivery lane closed

Mathematics remains the second P0 subject of the shared PEIS architecture.

The separate historical **PROFILE Mathematics EGE demo preparation lane for 2022–2026 is now treated as closed/accepted for normal work**. Do not keep a permanent chat working on those historical demo packages merely because the old conversation exists.

The latest explicit release freeze is PROFILE 2022:

- `results/PROFILE-MATH-2022-RELEASE-FREEZE-2026-08-21.md`
- status `READY_FOR_TILDA / FROZEN`;
- 18 tasks;
- 35/35 official FIPI examples;
- full acceptance and explicit reopen/version rule.

Earlier PROFILE years have their own accepted/finalized artifacts and commits in `main`; preserve their year-specific authority and regression gates.

Mathematics work should resume only for a real next dependency: Mathematics Identity Model / PEIS integration / base route / new explicitly approved product work. Do not reopen frozen historical demos without an explicit reopen reason and version.

### Physics — P1 / active but quality-gated

Physics is the third subject and may proceed in parallel without slowing P0 work.

Current facts:

- merged PR #49 — Physics 2026 accepted technical reference with official-source visuals and exam tools;
- open draft PR #48 — Physics 2025 exact source and archive build;
- PR #48 must not be merged merely because it is mergeable.

The user explicitly reported poor quality in the current Physics work on 2026-08-21. Therefore the active Physics lane is under a **quality review gate**: verify source truth, year isolation, task/example completeness, browser behavior, regression against accepted 2026 technical reference, and absence of silent reconstruction before acceptance/merge. Do not solve this by creating another broad audit program; inspect the actual PR/diff/results and correct concrete defects.

## 5. Parallel-chat operating model

Parallel chats are allowed and useful, but they are execution lanes, not independent project brains.

Recommended active set on the Pro account:

1. **Eksamio Brain** — architecture, priorities, cross-lane review, shared PEIS, merge decisions.
2. **Russian** — Russian subject program/content/semantic lane only.
3. **Physics** — Physics source/demo/identity lane only, currently quality-gated.

Do **not** keep a permanent Mathematics historical-demo chat active after the 2022–2026 PROFILE delivery lane has closed. Open a new Mathematics chat later only when a real new math dependency is selected.

A subject chat must not independently redesign shared PEIS contracts, learner identity, mastery, readiness, retention, NBA or cross-subject architecture.

## 6. Durable communication with minimal bureaucracy

GitHub is the shared bus. Existing mechanisms are sufficient:

- task contract when a bounded task genuinely needs one;
- implementation branch/PR;
- validation/test evidence;
- `results/` artifact for completed implementation work;
- review/status only when a real acceptance decision is needed.

Do not create duplicate reports just to report that another report exists.

A PR + its durable result/validation is normally enough evidence for a subject lane. A separate Brain checkpoint is needed only when project state meaningfully changes: major merge, blocker change, priority change, architecture decision, production gate change, or cross-lane conflict.

## 7. Brain cross-lane review rule

The Brain periodically checks parallel work, but **not by rerunning broad audits from zero**.

Cross-lane review should inspect deltas since the last accepted state:

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

## 8. Migration to the Pro account

The Pro account should become the primary working account for Eksamio.

Do not attempt to recreate old chat history manually. The repository is the handoff.

A new Brain session on Pro should:

1. fetch current `main` HEAD;
2. read `00-PRODUCT-MASTERPLAN.md`;
3. read this file `00E-CURRENT-BRAIN-HANDOFF.md`;
4. read `00B-PROJECT-PRIORITIES-CURRENT.md`, `00C-IMPLEMENTATION-GOVERNANCE-GUIDE.md`, `00D-BRAIN-CONTINUITY-PROTOCOL.md`;
5. inspect current open PRs and the latest relevant worklog/result artifacts;
6. continue only from verified repository state.

Subject chats on Pro should receive only their subject scope plus a pointer to this handoff and the relevant subject authority. They do not need the full old conversation transcript.

## 9. Current next gates

Central platform:

`PEIS-DEPLOYMENT-SECURITY-001`

Russian:

continue current semantic/program integration from actual current-main/open-PR state without repeating broad historical audits.

Physics:

quality-review and correct the active 2025 lane before merge; preserve accepted 2026 reference.

Mathematics:

historical PROFILE 2022–2026 demo delivery is closed for normal work; resume only when the next real Mathematics/PEIS/product dependency is explicitly selected.

## 10. Anti-chaos rule

The project should become easier to reason about as it grows.

Prefer:

`current authority -> narrow task -> evidence -> merge/reject -> next dependency`

over
`new audit -> new meta-document -> new audit of the audit -> repeated reconstruction`.

If a proposed process does not reduce uncertainty, prevent a real class of mistakes, or unblock delivery, do not add it.