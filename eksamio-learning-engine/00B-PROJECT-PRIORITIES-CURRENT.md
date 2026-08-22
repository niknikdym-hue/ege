# Eksamio — Current Project Priorities

**Status:** CURRENT PRODUCT / DELIVERY SNAPSHOT  
**Updated:** 2026-08-23  
**Baseline at update:** `85b1f4316cf33dc6ab0eebce2e9281b6432e4bbb`

This file does not replace `00-PRODUCT-MASTERPLAN.md`. For the shortest current operating state, read `00E-CURRENT-BRAIN-HANDOFF.md` and the newest relevant worklog checkpoint.

## 1. Product priority

Eksamio remains one **Personal Exam Intelligence System (PEIS)**.

Subject order:

1. Russian — subject #1, P0.
2. Mathematics — subject #2, P0 system subject.
3. Physics — subject #3, P1.

P0/P1 describes product/architecture importance, not a requirement to keep obsolete workstreams alive.

## 2. Current shared-system bottleneck

The validated reference chain has reached trusted-host identity. The next central production gate is:

`PEIS-DEPLOYMENT-SECURITY-001`

No public PEIS browser traffic should be enabled before this gate explicitly passes.

The production design must preserve the free deterministic/base learning loop and must not depend on ChatGPT Plus/Pro, Codex credits, an OpenAI end-user account or one fixed AI provider.

Current owner-decision authority: `OWNER-DECISIONS-2026-08-22.md`.

This gate is now constrained by approved owner decisions:

- first Pro client is a separate Eksamio web app; Tilda remains public/free-demo;
- Russia/no-VPN operation is mandatory, including AI Tutor;
- primary production cloud is Yandex Cloud Russia, while canonical state/core logic remain portable;
- passwordless verified e-mail/phone identity;
- replaceable payment/provider layers;
- learner audio is never stored in any persistent form;
- first paid Pro requires one Tutor production-ready in both text and realtime voice.

## 3. Execution order — what should move now

### CENTRAL P0 — immediate bottleneck

Close `PEIS-DEPLOYMENT-SECURITY-001` as the main platform dependency.

Every central task must reduce one concrete part of this gate or directly unlock the next production dependency. Do not start unrelated infrastructure, provider experiments or UI work because they are convenient.

### RUSSIAN P0 — parallel subject lane

PR #72 remains the active Russian decision lane. Continue by delta, not by repeating the broad 185×174 audit.

Current accepted working invariants remain:

- 121 active cards;
- 88 exception IDs;
- 91 EXACT;
- 5 PARTIAL_COMPOSITE;
- 25 BLOCKED;
- 96 integration-ready;
- 0 live-connected;
- 35 existing canonical school identities;
- 0 new `ru-*` IDs admitted.

PR #57 remains HOLD: proposed identities are not canonical authority.

PR #23 remains a valuable reviewed 121-card content checkpoint, but the whole historical branch is not automatically mergeable authority.

The next Russian result should be a bounded decision/reconciliation packet that tells Central Brain exactly what can be admitted/landed and what remains blocked; any required write/rebase/validator implementation goes to Codex.

### PHYSICS P1 — bounded parallel lane only

Physics 2026 remains the frozen technical/runtime/layout reference.

Physics 2025 v1.5 was subject-accepted and merged through PR #96. Its bounded result-page order fix is closed; do not reopen 2025 without a new concrete finding.

Physics 2024 is an active bounded source/demo lane because a real official-source dependency exists. The official FIPI 2024 source contour is `ege-source-fizika/source-fizika-2024/`; the derived source-access pack landed through PR #97 outside the authority folder. Continue:

`source lock -> source/layout/visual registry -> Physics subject build packet -> deterministic Codex build -> bounded subject acceptance -> Tilda delivery`

Physics 2024 must not slow the central P0 blocker or import content from 2025/2026.

### MATHEMATICS P0 — no broad historical lane

The broad PROFILE Mathematics historical preparation cycle for 2022–2026 is closed for normal work.

One known narrow exception remains: `matematika-source-2024/PROFILE-2024-UI-PARITY-FINDING.txt`. Handle only as a surgical repair when scheduled:

`targeted fix -> exact regression/browser verification -> durable acceptance/freeze -> close`

After that, Mathematics work returns only to a real shared-PEIS/identity/base-route/telemetry dependency.

## 4. First Pro launch gate — P0 capability, not first dependency

The shared PEIS closed loop, verified knowledge, deployment/security and production Tutor foundations remain prerequisite work. Voice P0 does not authorize a voice-first bypass of that dependency graph.

The first paid Pro launch is forbidden until one Tutor is production-ready in both text and realtime voice, with `voice -> text -> voice` continuity in the same learning episode. Text-only and voice-only Pro launches are forbidden.

No cloud, provider, auth or payment runtime is declared implemented or production-approved merely because its architecture/candidate is documented.

## 5. Mandatory task admission test

Before Central Brain issues any new implementation/audit task, it must be able to state all of the following in one short contract:

- `WHY_NOW` — why this task is the best next use of effort now;
- `ACTIVE_BLOCKER_OR_MILESTONE` — exact blocker/milestone it serves;
- `BASELINE_MAIN_SHA` — current durable baseline;
- `DEPENDENCY_IN` — what must already be true before execution;
- `MINIMAL_DELTA` — smallest change/evidence needed;
- `EXPECTED_UNLOCK` — what becomes possible if PASS;
- `EXECUTOR` — Brain / Codex / Spark / deterministic tool and why that is the cheapest sufficient choice;
- `ALLOWED_PATHS` and `FORBIDDEN_PATHS` where repo changes are possible;
- `ACCEPTANCE_EVIDENCE` — measurable proof of success;
- `STOP_CONDITIONS` — when to stop rather than improvise;
- `FINAL_STATUS` — bounded allowed outcomes.

If `EXPECTED_UNLOCK` is unclear, the task is not admitted.

If an existing working process already solves the problem, reuse it. Do not invent a new CI, staging layer, framework or architecture unless the existing path is proven insufficient for a real requirement.

If execution unexpectedly expands materially beyond the contract, STOP and return the new blocker to Central Brain. Do not turn a small delivery task into an architecture project.

## 6. Parallel execution

Parallel lanes are useful only when they do not compete for the same blocker-critical resource and have a concrete accepted endpoint.

- Eksamio Brain — architecture, shared PEIS, priorities, cross-lane review and acceptance decisions.
- Russian — Russian-only subject/semantic lane.
- Physics — current bounded 2024 source/demo lane only.
- Mathematics — no persistent historical-demo lane.

Parallel lanes communicate through GitHub branches/PRs/results, not by copying chat histories.

## 7. Brain review cadence

Review deltas, not the entire project repeatedly.

Brain cross-lane review is warranted after significant merges, blocker changes, production/shared-PEIS changes, cross-subject conflicts or unsupported DONE claims.

If nothing material changed, do not create another checkpoint or repeat an audit.

## 8. Delivery rule

Choose the next work by **bottleneck + dependency + expected unlock**, not by the number of open files, ease of implementation or visual appeal.

Prefer:

`current authority -> justified narrow task -> evidence -> accept/reject -> next dependency`

over
`re-audit -> meta-report -> new process -> re-audit the process`.

A task is efficient only if it reduces uncertainty, closes a real gap, unlocks the next dependency or produces a measurable learning/production capability with the lightest safe method.
