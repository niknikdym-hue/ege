# Eksamio — Current Project Priorities

**Status:** CURRENT PRODUCT / DELIVERY SNAPSHOT  
**Updated:** 2026-08-22

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

Current owner-decision authority: `OWNER-DECISIONS-2026-08-22.md`.

## 3. First Pro launch gate — P0 capability, not first dependency

The shared PEIS closed loop, verified knowledge, deployment/security and production Tutor foundations remain prerequisite work. Voice P0 does not authorize a voice-first bypass of that dependency graph.

The first paid Pro launch is nevertheless forbidden until one Tutor is production-ready in both text and realtime voice, with `voice -> text -> voice` continuity in the same learning episode. Text-only and voice-only Pro launches are forbidden.

The production contour must also preserve:

- separate web application for Pro; Tilda remains public/free-demo only;
- Russia/no-VPN access with no direct learner-browser dependency on a foreign AI service;
- primary Yandex Cloud Russia deployment with portable/provider-neutral canonical state and business logic;
- passwordless verified e-mail/phone identity and safe anonymous-to-account progress linking;
- absolute non-storage of learner audio;
- replaceable provider/payment layers and their separate legal/security/quality/API gates.

No cloud, provider, auth or payment runtime is declared implemented or production-approved by this priority update.

## 4. Russian — active P0 lane

Continue the current Russian subject-program / semantic / PEIS-integration work from actual `main` and current PR state.

Important current drafts include PR #72, PR #57 and PR #23. Drafts are not main authority.

Do not restart broad 185×174 coverage auditing from zero. Resolve the concrete current semantic/content/integration gates and move forward.

## 5. Mathematics — P0 system subject; broad historical PROFILE build lane closed

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

## 6. Physics — P1 subject; 2025/2026 demo acceptance closed

Physics 2026 is the accepted technical reference (merged PR #49).

Physics 2025 was source/subject accepted and merged through PR #48. Do not reopen the completed bounded demo audit without a new concrete finding.

Further Physics work requires a real source/identity/PEIS dependency and must not create subject-specific PEIS engines or slow critical P0/platform work.

## 7. Parallel execution

Recommended active chats/lanes:

- Eksamio Brain — architecture, shared PEIS, priorities, cross-lane review and acceptance decisions.
- Russian — Russian-only execution lane.
- Physics — only when a concrete Physics source/identity/PEIS dependency is active.

No permanent Mathematics historical-demo chat is needed. The known PROFILE 2024 UI defect may be handled by one short-lived bounded task/worker and then closed.

Parallel lanes communicate through GitHub branches/PRs/results, not by copying chat histories.

## 8. Brain review cadence

Review deltas, not the entire project repeatedly.

Brain cross-lane review is warranted after:

- significant merges;
- material PR updates affecting acceptance;
- blocker/milestone changes;
- shared PEIS/production changes;
- cross-subject conflicts;
- unsupported claims of completion.

If nothing material changed, do not create another checkpoint or repeat an audit.

## 9. Delivery rule

Choose the next work by bottleneck and dependency, not by the number of open files or how easy a task is.

Prefer:

`current authority -> narrow task -> evidence -> accept/reject -> next dependency`

over
`re-audit -> meta-report -> re-audit the report`.

The project should become easier to reason about as it grows.
