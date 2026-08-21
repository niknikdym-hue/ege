# Eksamio — Current Project Priorities

**Status:** CURRENT PRODUCT / DELIVERY SNAPSHOT  
**Updated:** 2026-08-21

This file does not replace `00-PRODUCT-MASTERPLAN.md`. For the shortest current operating state, read `00E-CURRENT-BRAIN-HANDOFF.md`.

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

Eksamio should operate at the leading edge of current educational technology while remaining economical: world-level educational outcomes are the benchmark; complexity and recurring cost without measurable gain are rejected.

## 3. Russian — active P0 lane

Continue the current Russian subject-program / semantic / PEIS-integration work from actual `main` and current PR state.

Important current drafts include PR #72, PR #57 and PR #23. Drafts are not main authority.

Do not restart broad 185×174 coverage auditing from zero. Resolve the concrete current semantic/content/integration gates and move forward.

## 4. Mathematics — P0 system subject; broad historical PROFILE build lane closed

The broad PROFILE Mathematics EGE historical preparation cycle for 2022–2026 is closed for normal work. Do not keep a permanent historical-demo chat alive merely because the old conversation exists.

Current accepted/finalized state includes:

- PROFILE 2026 — accepted technical reference;
- PROFILE 2025 — accepted technical reference;
- PROFILE 2023 — accepted/frozen, with regression lessons carried forward;
- PROFILE 2022 — `READY_FOR_TILDA / FROZEN`, 18 tasks, 35/35 official FIPI examples accepted.

### One known narrow exception — PROFILE 2024

`main` still contains `matematika-source-2024/PROFILE-2024-UI-PARITY-FINDING.txt` with `STATUS: DEFECT CONFIRMED`.

The defect is narrowly defined: learner-facing source labels and extended-result headings lost the required official example number. This is a UI parity issue, not a source/content/scoring/criteria issue.

Treat it as one surgical repair gate:

`targeted fix -> exact regression/browser verification -> durable acceptance/freeze -> close`

Do **not** reopen a broad 2022–2026 audit, rebuild other years, or restore a permanent Mathematics historical-demo lane because of this defect.

After this repair, Mathematics work should resume only for a real current dependency: shared Mathematics Identity Model/PEIS integration, base-route work, telemetry or another explicitly approved product need.

## 5. Physics — active P1 lane with quality gate

Physics 2026 is the accepted technical reference (merged PR #49).

Physics 2025 remains active in draft PR #48 and requires concrete quality revalidation before acceptance. Check actual source truth, year isolation, completeness, browser behavior and legitimate regressions; fix defects in the active lane rather than launching another general audit cycle.

Physics may proceed in parallel but must not create subject-specific PEIS engines or slow critical P0/platform work.

## 6. Parallel execution

Recommended active chats/lanes:

- Eksamio Brain — architecture, shared PEIS, priorities, cross-lane review and acceptance decisions.
- Russian — Russian-only execution lane.
- Physics — Physics-only execution lane.

No permanent Mathematics historical-demo chat is needed. The known PROFILE 2024 UI defect may be handled by one short-lived bounded task/worker and then closed.

Parallel lanes communicate through GitHub branches/PRs/results, not by copying chat histories.

## 7. Brain review cadence

Review deltas, not the entire project repeatedly.

Brain cross-lane review is warranted after:

- significant merges;
- material PR updates affecting acceptance;
- blocker/milestone changes;
- shared PEIS/production changes;
- cross-subject conflicts;
- unsupported claims of completion.

If nothing material changed, do not create another checkpoint or repeat an audit.

## 8. Delivery rule

Choose the next work by bottleneck and dependency, not by the number of open files or how easy a task is.

Prefer:

`current authority -> narrow task -> evidence -> accept/reject -> next dependency`

over
`re-audit -> meta-report -> re-audit the report`.

The project should become easier to reason about as it grows.