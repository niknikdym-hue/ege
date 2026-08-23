# Eksamio — Russian + Mathematics Full-Program Completion Plan

**Status:** CURRENT EXECUTION PLAN  
**Date:** 2026-08-23  
**Scope:** complete subject-program readiness; demo release acceptance is separate

This plan starts from the owner-confirmed fact that accepted demos must not be reopened as routine subject work. Russian demos 2022–2026 and Mathematics BASE+PROFILE demos 2022–2026 have passed full manual acceptance. Subject completion work therefore targets the knowledge/content/PEIS layers, not historical demo rebuilds.

## Launch-blocking source/textbook gate

`FULL-SUBJECT-SOURCE-AND-TEXTBOOK-INGESTION-POLICY-v0.1.md` and `FULL-SUBJECT-TEXTBOOK-INGESTION-PRIORITY-2026-08-23.md` are mandatory authority for this plan.

No subject may reach `FULL_SUBJECT_PROGRAM_READY` unless its declared launch scope has first reached:

`FULL_SUBJECT_SCOPE_SOURCE_COMPLETE`

That source gate requires a complete normative scope coverage ledger, reviewed source-backed semantic coverage, selected/ingested textbook and pedagogical evidence where required by the source policy, explicit handling of uncovered/conflicting items, and subject/human acceptance of scope/source completeness.

Accepted demos, FIPI coverage, an existing identity registry, or an AI-generated candidate inventory do not satisfy this gate by themselves.

For staged paid launch, the rule is applied to the subjects actually included in the offer. Therefore Russian source completeness is launch-blocking for the first Russian paid subject; Mathematics becomes launch-blocking before Mathematics is sold as a complete subject; Physics becomes launch-blocking before Physics is sold as a complete subject.

The textbook/source-ingestion lane is strictly sequential:

`Russian -> Mathematics -> Physics`

Central PEIS, infrastructure, Tutor and other non-conflicting platform work may continue in parallel, but do not run the subject textbook/source acquisition waves in parallel.

## Shared definition of FULL_SUBJECT_PROGRAM_READY

A subject is fully program-ready only when all of the following are true:

1. `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE=PASS` for the declared launch scope and the resulting route-independent semantic/identity model covers that accepted scope;
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

These existing assets are valuable but do not by themselves prove `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE`. The current Russian source/textbook wave must reconcile the existing 16-module/185-identity architecture against the official school-program coverage ledger and selected verified textbook/pedagogical lines.

## Required completion sequence

### RU-0 — Close Full Subject source/textbook scope

This is the current active source gate.

Required outcome:
- lock the applicable official Russian school-program scope and grade coverage;
- build and approve the Russian textbook-line selection matrix before downloads;
- acquire only approved `TAKE_*` sources into approved external storage, not owner-local folders by default;
- catalog provenance, edition/authors, source/storage identifiers and SHA-256;
- ingest structural/knowledge/pedagogy evidence without auto-admitting canonical truth;
- reconcile textbook evidence against the existing 16-module / 185-identity architecture;
- build the normative scope coverage ledger;
- resolve or explicitly block source conflicts, omissions and granularity disputes;
- obtain subject/human acceptance of `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE`.

Until RU-0 passes, Russian may continue using already verified assets for bounded work, but it must not be declared a source-complete full school subject.

### RU-1 — Close current semantic decision/reconciliation

Use PR #72 as the current decision ledger; reconcile it with PR #57 proposals and PR #23 reviewed content without merging historical branches wholesale.

Required outcome:
- decide every one of the 25 blocked Exceptions cards by reuse/admission/block;
- admit no unnecessary new ru-* identity;
- preserve 185 school identities unless RU-0 source reconciliation provides reviewed authority for a versioned change;
- land a canonical versioned mapping for the accepted 121-card corpus;
- close/supersede stale draft proposal state when the decisions are durable.

### RU-2 — Complete semantic coverage of all 16 program modules

Use the accepted RU-0 coverage ledger as scope authority. Source-close domains explicitly marked as expansion-required, especially phonetics/graphics, morphemics, word formation, morphology and OGE written-response competencies, plus any remaining draft-candidate modules.

For every genuinely missing capability:
- verified source provenance;
- duplicate/granularity review;
- stable semantic identity admission;
- grade/route scope;
- exam-route mapping where applicable.

### RU-3 — Build/admit the prerequisite graph needed for adaptive learning

Do not fabricate a dense graph. Admit source-backed blocking relations sufficient for real diagnosis/prerequisite repair across the subject, expanding from the already proven verified slice and RU-0 textbook/pedagogical evidence where accepted.

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

Learner-facing Eksamio content must respect the textbook-ingestion copyright/originality boundary and must not become copied textbook chapters/exercise banks merely because the source was ingested.

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

Any existing FIPI-heavy Mathematics candidate inventory remains useful candidate evidence only. It must not be treated as the full 1–11 school scope until the Mathematics source/textbook wave opens after Russian RU-0 and reconciles the inventory against the official school program plus selected textbook/pedagogical evidence.

## Required completion sequence

### MATH-0 — Close Full Subject source/textbook scope

Do not begin this textbook/source acquisition wave until Russian RU-0 reaches `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE`.

Required outcome:
- lock the official Mathematics 1–11 school-program scope;
- build and approve the Mathematics textbook-line selection matrix;
- acquire only approved sources into external storage;
- ingest and reconcile selected textbook/pedagogical evidence;
- reconcile existing FIPI candidate inventory against school-program scope rather than treating exam coverage as the whole subject;
- complete the normative scope coverage ledger;
- obtain subject/human acceptance of `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE`.

### MATH-1 — Define and source-lock the full Mathematics semantic inventory

Build the route-independent Mathematics Identity Model across the accepted MATH-0 scope using verified school-program, textbook/pedagogical and FIPI/source evidence.

Do not use exam task numbers as semantic identities.

The inventory must cover the mathematical capability domains required by the accepted school scope, including applicable arithmetic, algebra, equations/inequalities, functions/graphs, geometry, probability/statistics, applied modeling and advanced domains where the school scope requires them. BASE/PROFILE/OGE/EGE/VPR are overlays on this model, not the definition of the full school subject.

### MATH-2 — Admit canonical semantic identities in bounded source-backed waves

For each identity:
- stable capability definition;
- includes/excludes boundary;
- source provenance;
- grade applicability;
- BASE/PROFILE and other route applicability;
- exact year/task mappings as overlays where applicable;
- human/subject acceptance.

Use bounded coherent waves rather than one huge ontology-generation task.

### MATH-3 — Build/admit source-backed prerequisite relations

Create the mathematical dependency graph needed for adaptive routing and prerequisite repair. Course order, task number and AI intuition are not sufficient authority. Use accepted MATH-0 pedagogical/source evidence where it supports prerequisite relations.

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

Content must cover shared school mathematics and route-specific overlays without creating separate learner engines. Learner-facing Eksamio content must remain original unless explicit reproduction authority exists.

### MATH-5 — Map all accepted demo/task evidence and trainers to identities

All manually accepted BASE + PROFILE demos 2022–2026 remain closed releases. Use them as diagnostic evidence sources by adding versioned mappings outside the frozen demo truth. Add/complete thematic/adaptive trainer coverage where the program lacks practice depth.

### MATH-6 — Connect Mathematics to the shared PEIS service path

Generalize from the already proven first semantic slice to production-shaped adapters and learner evidence across the launch-relevant registry. Reuse the same shared persistence/mastery/readiness/retention/NBA system as Russian.

### MATH-7 — End-to-end Mathematics subject acceptance

Prove representative learner journeys and route overlays:
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

# Physics source-order dependency

Physics is third in the textbook/source-ingestion sequence.

Do not start the Physics textbook/source acquisition wave until Mathematics MATH-0 reaches `FULL_SUBJECT_SCOPE_SOURCE_COMPLETE`.

Physics full-subject construction must use the same source hierarchy: official school-program scope first, FIPI routes as overlays, then selected verified textbook/pedagogical evidence. Accepted Physics demos do not establish the full school-subject scope.

A dedicated Physics full-subject completion sequence should be materialized when the Mathematics source gate has passed and the Physics wave becomes active.

# Efficient execution order

The current execution order is:

1. **Russian source/textbook lane:** RU-0 first, beginning with the Russian textbook selection matrix; do not batch-download before matrix approval.
2. **Russian full-subject lane:** continue bounded semantic/content work where current verified authority is sufficient, but final source-complete claims depend on RU-0.
3. **Mathematics source/textbook lane:** remains queued until RU-0 PASS; existing candidate inventory stays candidate evidence, not full-school completeness.
4. **Physics source/textbook lane:** remains queued until MATH-0 PASS.
5. **Central platform:** PEIS production substrate -> Yandex staging -> production identity/telemetry may continue in parallel because it does not require parallel textbook acquisition.
6. **Tutor/platform work:** may continue in parallel where it does not fabricate missing subject truth or bypass subject-source gates.
7. As soon as the production PEIS boundary and the relevant subject program are ready, connect Russian first, then later Mathematics using the same adapter/persistence pattern.

Do not block useful platform engineering on unrelated historical/demo re-audits. Conversely, do not use platform readiness as a reason to falsely call a subject complete before its source/textbook gate passes.
