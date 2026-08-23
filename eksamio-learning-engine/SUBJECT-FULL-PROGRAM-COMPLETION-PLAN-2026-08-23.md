# Eksamio — Russian + Mathematics Full-Program Completion Plan

**Status:** CURRENT EXECUTION PLAN  
**Date:** 2026-08-23  
**Scope:** complete subject-program readiness; demo release acceptance is separate

This plan starts from the owner-confirmed fact that accepted demos must not be reopened as routine subject work. Russian demos 2022–2026 and Mathematics BASE+PROFILE demos 2022–2026 have passed full manual acceptance. Subject completion work therefore targets the knowledge/content/PEIS layers, not historical demo rebuilds.

## Shared definition of FULL_SUBJECT_PROGRAM_READY

A subject is fully program-ready only when all of the following are true:

1. source-backed route-independent semantic/identity model covers the declared subject scope;
2. required prerequisite relations are source-backed and admitted;
3. every launch-relevant semantic identity has a complete teach/practice/verify/retain content bundle;
4. accepted demos/trainers/diagnostics/homework/Tutor interactions map to versioned semantic identities without making client runtime the authority;
5. product observations can emit safe shared EvidenceEvents through the shared PEIS service boundary;
6. shared PEIS can execute diagnose -> model -> prioritize -> teach/practice -> independent verify -> retain -> reassess -> replan for the subject;
7. browser/product regression and subject acceptance prove no scoring/source/runtime regression;
8. unresolved items are explicitly outside the launch scope or remain blocked with no false completeness claim.

Production/public Pro launch additionally requires the central production/security/auth/Tutor/payment gates. Subject-program readiness does not bypass them.

# Russian

## Current state

Russian already has a 16-module full-subject architecture for grades 5–11, OGE/EGE, thematic trainers, Homework and Tutor. The existing school semantic layer preserves 185 canonical identities. The 121-card Exceptions checkpoint has a current integration audit showing 91 EXACT + 5 PARTIAL_COMPOSITE = 96 integration-ready cards, 25 blocked, and 0 live-connected.

## Required completion sequence

### RU-1 — Close current semantic decision/reconciliation

Use PR #72 as the current decision ledger; reconcile it with PR #57 proposals and PR #23 reviewed content without merging historical branches wholesale.

Required outcome:
- decide every one of the 25 blocked Exceptions cards by reuse/admission/block;
- admit no unnecessary new ru-* identity;
- preserve 185 school identities;
- land a canonical versioned mapping for the accepted 121-card corpus;
- close/supersede stale draft proposal state when the decisions are durable.

### RU-2 — Complete semantic coverage of all 16 program modules

Source-close domains explicitly marked as expansion-required, especially phonetics/graphics, morphemics, word formation, morphology and OGE written-response competencies, plus any remaining draft-candidate modules.

For every genuinely missing capability:
- verified source provenance;
- duplicate/granularity review;
- stable semantic identity admission;
- grade/route scope;
- exam-route mapping where applicable.

### RU-3 — Build/admit the prerequisite graph needed for adaptive learning

Do not fabricate a dense graph. Admit source-backed blocking relations sufficient for real diagnosis/prerequisite repair across the subject, expanding from the already proven verified slice.

### RU-4 — Materialize complete content bundles

For every launch-relevant identity provide:
- canonical explanation/rule/method;
- provenance;
- worked examples;
- common errors/misconceptions and contrasts;
- guided practice;
- independent practice;
- mixed/transfer practice;
- retention items;
- fresh independent verification.

### RU-5 — Connect existing Russian products to shared PEIS

Turn the versioned mappings into production-shaped server adapters so accepted demo/trainer/diagnostic actions emit shared EvidenceEvents. Preserve server-owned semantic truth, scoring and identity. Move from 0 live-connected toward complete launch-relevant coverage.

### RU-6 — Written response / essay learning layer

Source-close EGE/OGE written-response competencies and rubric mappings required by the selected product scope. AI feedback may be educational, but must not be called human checking. Human essay-checking is not required for the initial product contour unless separately approved.

### RU-7 — End-to-end Russian subject acceptance

Prove on fresh learner scenarios:
- diagnostic evidence;
- exact/partial evidence semantics;
- prerequisite repair;
- independent verification;
- retention scheduling/retest;
- explainable NBA;
- reassessment/score-risk update;
- no demo/scoring/source regressions.

Final subject status: `RUSSIAN_FULL_SUBJECT_PROGRAM_READY`.

# Mathematics

## Current state

Mathematics has one shared identity-model foundation for BASE + PROFILE route overlays, but the canonical semantic registry currently contains only one admitted semantic identity: classical probability with equally likely outcomes. A first Mathematics shared-PEIS slice has been proven, but this is not full-subject coverage.

## Required completion sequence

### MATH-1 — Define and source-lock the full Mathematics semantic inventory

Build the route-independent Mathematics Identity Model across the declared BASE + PROFILE subject scope using verified curriculum/FIPI/source evidence.

Do not use exam task numbers as semantic identities.

The inventory must cover the mathematical capability domains needed by both routes, including applicable arithmetic, algebra, equations/inequalities, functions/graphs, geometry, probability/statistics, applied modeling, and profile-only advanced domains such as calculus/parameter/high-complexity reasoning where source scope requires them.

### MATH-2 — Admit canonical semantic identities in bounded source-backed waves

For each identity:
- stable capability definition;
- includes/excludes boundary;
- source provenance;
- BASE/PROFILE route applicability;
- exact year/task mappings as overlays;
- human/subject acceptance.

Use bounded coherent waves rather than one huge ontology-generation task.

### MATH-3 — Build/admit source-backed prerequisite relations

Create the mathematical dependency graph needed for adaptive routing and prerequisite repair. Course order, task number and AI intuition are not sufficient authority.

### MATH-4 — Materialize full teaching/practice/verification content

For every launch-relevant identity provide:
- explanation/method;
- worked examples;
- misconception/error patterns;
- guided practice;
- independent practice;
- mixed/transfer tasks;
- retention tasks;
- fresh independent verification.

Content must cover both shared BASE/PROFILE skills and route-specific advanced profile skills without creating separate learner engines.

### MATH-5 — Map all accepted demo/task evidence and trainers to identities

All manually accepted BASE + PROFILE demos 2022–2026 remain closed releases. Use them as diagnostic evidence sources by adding versioned mappings outside the frozen demo truth. Add/complete thematic/adaptive trainer coverage where the program lacks practice depth.

### MATH-6 — Connect Mathematics to the shared PEIS service path

Generalize from the already proven first semantic slice to production-shaped adapters and learner evidence across the launch-relevant registry. Reuse the same shared persistence/mastery/readiness/retention/NBA system as Russian.

### MATH-7 — End-to-end Mathematics subject acceptance

Prove representative BASE and PROFILE learner journeys:
- diagnose;
- state update;
- prerequisite repair;
- targeted practice;
- independent verification;
- transfer;
- retention;
- reassessment;
- route-aware but identity-independent NBA;
- no source/scoring/demo regressions.

Final subject status: `MATHEMATICS_FULL_SUBJECT_PROGRAM_READY`.

# Efficient execution order

Run in parallel with the central PEIS production work:

1. Russian: close PR #72 reconciliation first because it converts existing mature content into usable semantic evidence fastest.
2. Mathematics: start full semantic inventory/admission waves; do not spend effort rebuilding accepted demos.
3. Central platform: continue PEIS production substrate -> Yandex staging -> production identity/telemetry.
4. As soon as the production PEIS boundary is ready, connect Russian first, then Mathematics using the same adapter/persistence pattern.

Do not block initial useful launch value on completing unrelated historical/demo re-audits. Full 5–11/OGE expansion may proceed in later bounded waves if the selected launch scope is narrower, but any omitted scope must be explicit rather than falsely marked complete.
