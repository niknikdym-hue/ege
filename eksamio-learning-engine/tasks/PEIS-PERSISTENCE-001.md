# PEIS-PERSISTENCE-001 — Shared Evidence Persistence / Deterministic Replay Boundary

**Date:** 2026-08-20  
**Status:** IMPLEMENTATION TASK  
**Baseline:** `main@534ff07242e2304b75bf64e6bbac1fcadda22bc2`

## Milestone

Move Eksamio from a validated in-memory/reference PEIS loop to a subject-neutral persistence/replay boundary without creating a second learner engine.

Required closed path:

`append EvidenceEvent -> durable append-only store -> idempotent replay -> effective event history -> shared PEIS kernel recompute -> materialized snapshot cache -> recommendation/outcome telemetry`

## Reuse audit

Before implementation, actual `main` was searched and the repository tree inspected for shared persistence/event-store/state-service implementations.

Findings:

- no approved `peis-persistence`, shared event-store, SQLite learner-state service or equivalent shared persistence implementation exists;
- `peis-reference-kernel/` is explicitly in-memory/reference and remains the inference owner;
- Russian `standalone-exceptions-trainer/core/rex-state.js` is legacy subject-local compatibility state and is forbidden as the shared base;
- adapter 279 already defines idempotency/import invariants that the shared persistence layer must preserve.

Decision: create one new **subject-neutral reference persistence boundary** that calls the existing PEIS kernel rather than reimplementing mastery/readiness/retention/NBA.

## Scope

Implement a local/CI reference boundary using Python stdlib SQLite plus the already-used JSON Schema validator dependency.

Required capabilities:

1. append valid EvidenceEvent 277 records without in-place mutation;
2. stable `event_id` idempotency;
3. optional `idempotency_key` replay suppression with conflict detection;
4. atomic event + semantic index + identity-link acceptance;
5. deterministic replay ordering independent of insertion order;
6. CORRECTION/RETRACTION reference integrity and effective-history filtering;
7. query by learner / subject / semantic identity;
8. recompute learner semantic snapshot through existing `peis-reference-kernel.snapshot`;
9. persist materialized snapshot only as a rebuildable cache/view, never source of truth;
10. persist NBA proposals and 285 outcome events append-only;
11. expose raw telemetry summaries for assistance / transfer / retention / verification provenance;
12. attach later user identity to an existing learner profile without rewriting historical evidence.

## Validation

Must exercise both already-verified P0 subject slices:

- RU-SLICE-001;
- MATH-SLICE-001.

Mandatory tests:

- math events appended out of order replay to the validated final DEVELOPING / RETENTION_REVIEW state;
- exact duplicate append is `ALREADY_APPLIED` and creates no extra event/state delta;
- same event_id with different payload is rejected as integrity conflict;
- replay order is deterministic;
- Russian golden-B event subset reproduces a ready target and successful independent-verification outcome through the shared kernel;
- canonical Russian prerequisite edge is honored;
- recommendation proposal + outcome event logging validates against 285;
- duplicate outcome event is idempotent;
- anonymous identity can be linked to later user identity without raw event rewrite;
- telemetry preserves assistance / verification / transfer / retention provenance;
- no subject-specific learner tables/engines exist.

## Safety boundary

This task does **not**:

- deploy a production database/service;
- alter Tilda, production demos, scoring or localStorage;
- change shared PEIS contracts;
- introduce final mastery coefficients or forgetting curves;
- migrate legacy Russian production state;
- implement authentication;
- implement AI Tutor or voice.

The SQLite implementation is a deterministic reference/service boundary for architecture and CI validation, not live production infrastructure.
