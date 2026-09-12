# EKSAMIO — New Chat Handoff — 2026-09-07

Status: DURABLE CONTINUATION CHECKPOINT
Repository: `niknikdym-hue/ege`

This file exists because chat history is not a source of truth. A new Central Brain session must start by re-reading GitHub and must treat the SHAs below as a frozen checkpoint, not as permission to skip a fresh remote-state read.

## 1. Owner decision added on 2026-09-07

Eksamio development-agent architecture is now:

- **Astra = Senior Brain / Architect / Reviewer**;
- **Codex = bounded Execution Engineer**;
- **GitHub = durable source of truth**;
- **GitHub Actions / deterministic tests = objective implementation evidence**;
- **Owner = final authority for merge/deploy/live-provider/payment/production-sensitive actions**.

Canonical authority file:
`docs/agent-orchestration/EKSAMIO-AGENT-ORCHESTRATION-AUTHORITY-v0.1.md`

Agent-orchestration work is isolated on branch:
`brain/agent-orchestration-v0-1-20260907`

First authority commit on that branch:
`eb8fa933cd73d4b0b300bd5c036d02736f486d5b`

Do not mix this branch into Admissions Gate #189 or Russian subject closure #164.

## 2. Exact repository checkpoint read on 2026-09-07

### main

Actual `main` HEAD at checkpoint:
`85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb`

No merge was performed while creating this handoff.

### PR #186 — authenticated registration/runtime

State: OPEN / DRAFT / unmerged
Actual HEAD:
`ae169c82a6f6e515e95293625e31e342b447f867`

Central Brain state in GitHub: CODE/CI PASS for authenticated registration + one shared PostgreSQL learner identity/state + private Yandex-ready runtime.

Important invariant already implemented there: ambiguous delivery outcome is fail-closed; exact retry cannot resend unless explicit `NOT_SENT` permits the same challenge/code retry.

No Yandex apply/deploy, real email/SMS, production learner write, payment/provider/OpenAI call or merge is implied.

### PR #187 — live educational asset reconciliation / issue #185

State: OPEN / DRAFT / unmerged
Actual HEAD:
`c5592c212557b91578ed48e1bf778e30dd489dc7`

Central Brain state in GitHub: CODE/CI PASS.

Durable accepted reconciliation includes:
- Russian trainer denominator: 174 cards / 9 source texts;
- orthoepy: 291 exact live IDs;
- dictionary words: 308 exact live IDs;
- paronyms: 144 groups / 334 entries;
- phraseology: 285 exact live IDs;
- bounded action-scoped semantic bindings only;
- production event/mastery admission remained closed in #187 itself.

### Issue #188 / PR #189 — registered exact-event Admissions Gate

Issue #188 state: OPEN, implementation CODE/CI PASS pending owner-controlled integration.
PR #189 state: OPEN / DRAFT / unmerged.
Actual PR #189 HEAD at checkpoint:
`05e54aa4d43abd813f306f46345f1d913f8611a2`

IMPORTANT: this is ahead of the prior chat checkpoint. Paronyms are already closed; do not repeat the old paronym probe task.

All four action-scoped semantic components accepted in #187 are now admitted through the registered exact-event server-owned gate:

1. Orthoepy stress
   - `w001..w291`
   - `normative_stress_selection`
   - semantic owner `ru-orthoepy-normative-stress-selection`

2. Dictionary words missing-root-vowel insertion
   - exact 308 live IDs
   - `missing_root_vowel_insertion`
   - semantic owner `school-root-vowel-dictionary-unverifiable`

3. Phraseology fragment identification
   - exactly 199 production-safe IDs from the 285-row live denominator
   - requires both `examEligible=true` and `exactInExample=true`
   - primary `expression` is the server-owned correct answer under bounded case/whitespace normalization
   - variants and remaining 86 rows remain unadmitted

4. Paronym context/collocation choice
   - exact denominator 144 groups / 334 entries
   - `context_collocation_choice`
   - semantic owner `ru-lexis-paronym-collocation-choice`
   - canonical response mode is `SELECTED_OPTION`
   - prior invalid `SINGLE_SELECT` implementation was caught by exact-head CI and fixed

Exact-head Admissions Gate run recorded in GitHub:
`34139892968` = SUCCESS on PostgreSQL 16.
Companion authenticated-runtime / registration / Yandex staging / authority-capture workflows on the same head are also recorded SUCCESS in PR #189 / issue #188.

Hard boundary still holds:
`false_exact_mastery = 0`.

Do not merge #189 or deploy/apply anything without owner authority.

### PR #164 — Russian full-subject closure

State: OPEN / DRAFT / unmerged.
Actual metadata HEAD at checkpoint:
`e35c7d1ef49194c7fe59ec1e3bff8164ff36ac08`

The PR body contains an older narrative checkpoint and must not be treated as exact current HEAD authority. Re-read exact remote diff/CI before any new Russian subject work.

The durable subject rule remains: no fuzzy/module-only semantic admission, no invented school identity, and no false exact mastery. Russian subject closure remains a separate mandatory launch gate from runtime Admissions Gate.

## 3. Current launch interpretation

At this checkpoint:

- registration/authenticated learner substrate: CODE/CI PASS in #186, unmerged;
- live educational asset identity/provenance reconciliation: CODE/CI PASS in #187, unmerged;
- four current action-scoped registered exact-event admissions: CODE/CI PASS in #189, unmerged;
- Russian full-subject closure: still separate draft work in #164;
- `main` has not been advanced by any of these draft stacks.

Therefore a new chat MUST NOT repeat phraseology or paronym admission work merely because an older chat ended there.

Before selecting a new launch-critical code task, re-read current `main`, #164, #186, #187, #189 and issue #188, then choose the first genuinely unresolved blocker from current GitHub truth.

## 4. Agent-runner continuation point

Separate from launch feature branches, continue implementation on:
`brain/agent-orchestration-v0-1-20260907`

The architecture decision is already persisted. Next bounded implementation slice:

1. add versioned JSON schemas for Astra task-plan and Astra review decision;
2. add a minimal Astra Responses API adapter using configurable `OPENAI_ASTRA_MODEL` with default `gpt-6-astra`;
3. add a Codex executor adapter boundary (SDK-first, `codex exec` shell fallback if needed);
4. add `dry-run` mode that performs no repo/cloud/live mutations;
5. add permission-gate tests proving merge/deploy/live-provider/payment/production-write actions are rejected without explicit owner authorization;
6. persist per-run exact Git SHA, model identity, decision and usage/cost metadata when available;
7. open/update a DRAFT PR only after deterministic tests are green.

Do not create a broad autonomous-agent platform. Build the smallest useful `Astra -> Codex -> CI -> Astra review` loop.

## 5. Development vs Tutor provider

Astra being Senior Brain for software development does NOT select Astra as the learner-facing Tutor brain.

Tutor AI-brain selection remains provider-neutral and must be decided by Eksamio's own comparative pedagogical test across the approved candidate set (OpenAI, Qwen, DeepSeek, Yandex). Voice remains a separate provider-neutral STT/TTS layer.

## 6. Forbidden assumptions in a new chat

Do not assume:
- a stored SHA is still current without re-reading GitHub;
- a Codex narrative proves a pushed commit;
- green local tests prove exact-head GitHub CI;
- live trainer/page names grant semantic authority;
- client/browser correctness claims can create mastery;
- `main` contains draft PR work;
- an agent may merge/deploy/pay/send/live-call merely because implementation is green.

## 7. First instruction for a new Central Brain session

Read this file, then immediately verify current GitHub `main` and live PR/issue heads. Continue from repository truth without restoring implementation state from chat memory.
