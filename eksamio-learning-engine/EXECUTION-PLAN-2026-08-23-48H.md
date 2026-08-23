# Eksamio — 36–48h execution plan

**Status:** ACTIVE EXECUTION PLAN  
**Window start:** 2026-08-23  
**Baseline main:** `ad08f4102cc609338b825932cfa9940a785c2922`  
**Owner:** Central Brain  
**Primary engineering executor:** Codex

This is a short-horizon execution plan, not a new product strategy. It exists to convert already accepted subject assets and merged PEIS foundations into concrete implementation progress.

## Non-negotiable boundaries

- Russian demos 2022–2026 are manually accepted and closed.
- Mathematics BASE + PROFILE demos 2022–2026 are manually accepted and closed.
- Physics 2025 is manually accepted and closed.
- Physics 2024 is in manual acceptance; no new code changes until a concrete manual finding returns.
- Do not spend this window rebuilding or re-auditing accepted demos.
- One shared PEIS only. No subject-specific learner engine.
- Central Brain owns dependency order, acceptance, merge decisions and the next task.
- Codex owns engineering-heavy implementation/testing through bounded PRs.

# Outcome target for this window

By the end of the 36–48h window, maximize the probability of achieving all three:

1. `PEIS_PRODUCTION_SUBSTRATE_READY_FOR_YANDEX_STAGING` or one exact proven blocker;
2. Russian RU-1 reconciliation converted into durable canonical mapping/decision state, with the path from `0 live-connected` to first real shared-PEIS integration explicitly executable;
3. Mathematics moved from one admitted semantic identity to a source-backed full-subject candidate inventory and first coherent admission wave ready for/through subject acceptance.

No task is admitted only because it is easy. Every task must close a blocker or unlock the next dependency.

# Lane A — CENTRAL P0 / PEIS production substrate

## A1 — Execute `PEIS-PRODUCTION-SUBSTRATE-001`

**Executor:** Codex  
**Task authority:** `tasks/PEIS-PRODUCTION-SUBSTRATE-001.md`

Required result:

`PEIS_PRODUCTION_SUBSTRATE_READY_FOR_YANDEX_STAGING`

or one exact blocker allowed by that task.

Acceptance focus:

- reuse existing service bridge / persistence / trusted-host / browser-hook contracts;
- PostgreSQL-compatible persistence with migrations and transaction/idempotency equivalence;
- container build and runtime smoke;
- separate `/healthz` and `/readyz`;
- config/secrets boundary;
- network-write kill switch;
- old PEIS regression validators remain green;
- PostgreSQL integration tests prove restart, append-only semantics, identity continuity and snapshots;
- `PUBLIC_TRAFFIC_CONNECTED=false`;
- no Tilda/subject/demo changes.

## A2 — Brain review immediately after Codex PR

Central Brain must inspect:

- changed paths;
- actual implementation vs existing PEIS contracts;
- all required tests;
- hidden parallel-backend risk;
- secret/privacy leakage;
- kill-switch/fail-open semantics;
- migration/rollback safety.

Outcome:

- approve/merge if all gates PASS;
- otherwise return one bounded correction to the same PR;
- no adjacent architecture work.

## A3 — Only after A1 PASS: create/execute `PEIS-YANDEX-STAGING-001`

The next cloud slice must focus only on the staging envelope:

`API Gateway -> private Serverless Container -> Managed PostgreSQL -> Lockbox -> Monitoring/Audit`

Do not combine auth, payments, Tutor or public rollout into this slice.

If cloud authentication/2FA is the only missing dependency, surface that exact auth step to the owner and continue the same flow after authentication; do not redesign deployment around it.

# Lane B — RUSSIAN P0 / convert mature content into usable PEIS

## B1 — Close RU-1 decision/reconciliation by delta

**Subject authority:** EKSAMIO — РУССКИЙ  
**Central Brain role:** task framing + acceptance + landing decision  
**Engineering executor after subject decisions:** Codex

Use current PR #72 as the main decision ledger and reconcile against PR #57 proposals and PR #23 reviewed 121-card content checkpoint.

Do not repeat the broad 185×174 audit.

Required decision outcome for all 25 currently BLOCKED exception cards:

- `REUSE_EXISTING_CANONICAL_ID`;
- `ADMIT_NEW_IDENTITY` only when source-backed and genuinely needed;
- or `REMAIN_BLOCKED` with exact reason.

Hard invariants:

- preserve all 185 canonical school identities;
- do not auto-admit proposed `ru-*` identities;
- broad/composite errors never become guessed exact weakness;
- historical PRs are not merged wholesale merely to land accepted decisions.

## B2 — Codex lands the accepted RU-1 delta

After the subject decision packet is accepted by Central Brain, Codex receives one bounded implementation task to:

- materialize the canonical versioned 121-card semantic mapping;
- add/update deterministic validator evidence;
- close/supersede stale proposal state where appropriate;
- leave accepted demos untouched;
- leave shared PEIS contracts untouched.

Expected unlock:

A stable Russian mapping that can be connected to the existing shared service adapter path without semantic ambiguity.

## B3 — First Russian live-connection slice after A1 PASS

Do not wait for every future Russian module before proving integration.

Connect a small but representative subset of the already integration-ready Russian cards through the production-shaped shared PEIS boundary, proving:

`product observation -> server mapping -> EvidenceEvent -> persistence -> shared PEIS -> directive -> independent verify`

with fail-open behavior and no client-owned semantic truth.

This is the shortest path from `0 live-connected` to a real production-shaped Russian loop.

# Lane C — MATHEMATICS P0 / build the actual subject model, not demos

## C1 — Full source-backed candidate inventory

**Executor:** Codex for deterministic extraction/materialization; Central Brain for scope/architecture review; subject acceptance required before canonical admission.

Create a route-independent candidate inventory spanning BASE + PROFILE subject scope using verified current sources.

Required domains include, as applicable:

- arithmetic and numerical reasoning;
- algebraic expressions;
- equations and inequalities;
- functions and graphs;
- geometry;
- probability and statistics;
- applied/modeling tasks;
- profile-only advanced domains required by source scope (including calculus/parameters/high-complexity reasoning where actually supported).

Rules:

- exam task number is metadata, never the semantic identity;
- BASE and PROFILE remain route overlays of one Mathematics Identity Model;
- exact source provenance and includes/excludes boundaries are required;
- candidate inventory is not automatically canonical admission.

Expected result:

`MATHEMATICS_FULL_SUBJECT_CANDIDATE_INVENTORY_READY`

## C2 — First coherent admission wave

Select the first source-complete coherent wave from C1, favoring capabilities that unlock broad routing/prerequisite value rather than arbitrary task-number order.

For every admitted identity require:

- stable semantic ID;
- label/capability;
- includes/excludes;
- source provenance;
- BASE/PROFILE applicability;
- exact route/year mappings where relevant;
- human/subject acceptance;
- no invented prerequisite edges.

## C3 — Prepare content/prerequisite work from admitted wave

Only after C2 admission, prepare the next bounded packages:

- source-backed prerequisite relations where genuinely blocking;
- worked examples;
- guided/independent/transfer/retention/verification items;
- shared EvidenceEvent mappings.

Reuse the already proven MATH-SLICE-001 PEIS path; do not invent a mathematics-specific learner engine.

# Central Brain operating loop for the window

For every executor result:

1. refresh `main`;
2. compare only relevant delta;
3. verify task acceptance evidence;
4. reject scope expansion;
5. merge when PASS;
6. update blocker status only if materially changed;
7. immediately issue the next dependency from this plan.

Do not wait for the owner to ask what is next.

# Parallelism rules

Run concurrently when dependencies permit:

- Codex A1 can run while Russian subject decision B1 is being completed;
- C1 can run in parallel because it is source/inventory work and does not depend on A1;
- B2 waits for B1 acceptance;
- B3 waits for both B2 mapping readiness and A1 production-substrate PASS;
- A3 waits for A1 PASS;
- C2 waits for C1 and subject/Brain review.

Physics 2024 manual acceptance consumes no engineering lane unless a concrete finding returns.

# 36–48h stop conditions

Do not expand into:

- accepted demo rework;
- new global framework/CI unless proven necessary;
- payment implementation;
- AI Tutor implementation;
- voice implementation;
- public production traffic;
- subject-specific learner state engines;
- broad re-audits already closed by current authority.

If a task discovers a real architecture/privacy/source conflict, return one exact blocker and replan from that evidence.

# Window success statuses

Best-case end state:

- `PEIS_PRODUCTION_SUBSTRATE_READY_FOR_YANDEX_STAGING`;
- `RUSSIAN_RU1_CANONICAL_MAPPING_READY` and first live-connection task admitted/started if A1 also passed;
- `MATHEMATICS_FULL_SUBJECT_CANDIDATE_INVENTORY_READY` plus first coherent admission wave accepted or under bounded review.

A partial window is acceptable only when the remaining blocker is concrete, evidenced and narrower than at window start.
