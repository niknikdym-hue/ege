# MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-001

**Status:** IMPLEMENTATION / EVIDENCE TASK  
**Date:** 2026-08-23  
**Baseline:** `ad08f4102cc609338b825932cfa9940a785c2922`  
**Parent plan:** `EXECUTION-PLAN-2026-08-23-48H.md`

## WHY_NOW

Mathematics BASE + PROFILE demos 2022–2026 have passed full manual acceptance and are closed. Rebuilding historical demos would not advance the product.

The Mathematics Identity Model foundation exists and the shared PEIS path has been proven with one admitted semantic identity (`math-probability-classical-equally-likely`), but one identity is not a full subject model.

The next useful Mathematics dependency is therefore a source-backed, route-independent full-subject candidate inventory that can be reviewed/admitted in bounded waves.

## ACTIVE_BLOCKER_OR_MILESTONE

`MATHEMATICS_FULL_SUBJECT_MODEL_INCOMPLETE`

## DEPENDENCY_IN

Use current main and reuse:

- `eksamio-learning-engine/mathematics-identity/MATHEMATICS-IDENTITY-MODEL-FOUNDATION-v0.1.json`;
- `eksamio-learning-engine/mathematics-identity/MATHEMATICS-SEMANTIC-REGISTRY-v0.1.json`;
- `eksamio-learning-engine/mathematics-identity/MATHEMATICS-SOURCE-MATRIX-2022-2026-v0.2.json`;
- `eksamio-learning-engine/mathematics-identity/verified-slices/`;
- accepted Mathematics BASE + PROFILE source/build contours already present in current main;
- official FIPI/codifier/specification source evidence in repository;
- shared PEIS contracts only as architectural constraints, not as Mathematics truth.

Manual acceptance authority:

`eksamio-learning-engine/SUBJECT-DEMO-MANUAL-ACCEPTANCE-2026-08-23.md`

Do not reopen accepted demo releases.

## MINIMAL_DELTA

Create a deterministic, source-provenanced **candidate semantic inventory** for the declared Mathematics BASE + PROFILE scope.

This task does NOT canonically admit new semantic identities.

It prepares the evidence required for bounded subject/Brain admission waves.

## EXPECTED_UNLOCK

Success status:

`MATHEMATICS_FULL_SUBJECT_CANDIDATE_INVENTORY_READY`

This unlocks the first coherent canonical admission wave without another broad source audit or historical demo rebuild.

## EXECUTOR

Codex.

Reason: repository-wide source inventory, deterministic extraction/materialization, cross-year/route mapping, validation and large structured artifacts are engineering-heavy. Semantic admission remains subject/Brain authority.

## ALLOWED PATHS

Prefer add-only artifacts under:

- `eksamio-learning-engine/mathematics-identity/full-subject-inventory/`

May add/update this task result pointers only if useful.

Read-only source access is allowed across existing Mathematics source/build contours and relevant authority files.

## FORBIDDEN PATHS / SCOPE

Do not modify:

- any manually accepted BASE/PROFILE demo runtime/build/package;
- official source PDFs;
- answers, scoring, criteria or task order;
- existing canonical Mathematics semantic registry except to read it;
- shared PEIS contracts/kernel;
- Russian/Physics paths;
- Tilda/live production;
- learner state/mastery/readiness/retention/NBA logic.

Do not create a Mathematics-specific learner engine.

Do not auto-admit candidate identities.

## INVENTORY MODEL

Create route-independent candidate capabilities, not task-number labels.

Each candidate must include at minimum:

- `candidate_id`;
- `label_ru`;
- `capability`;
- `domain`;
- `subdomain` where useful;
- `scope_includes`;
- `scope_excludes`;
- `source_refs` with exact repository source provenance;
- `route_applicability`: BASE / PROFILE / BOTH;
- `year_task_mappings` as route metadata only;
- `overlap_with_existing_canonical_ids`;
- `possible_duplicate_candidate_ids`;
- `granularity_status`: `CLEAR | NEEDS_SUBJECT_REVIEW`;
- `source_status`: `SOURCE_BACKED | NEEDS_SOURCE_REVIEW`;
- `admission_status`: always `CANDIDATE_NOT_CANONICAL` in this task.

## REQUIRED SUBJECT COVERAGE

Inventory the full Mathematics subject scope supported by verified repository sources, including where applicable:

1. arithmetic / numbers / percentages / proportions / numerical reasoning;
2. algebraic expressions and transformations;
3. equations and systems;
4. inequalities and systems;
5. functions and graphs;
6. sequences where supported;
7. applied/modeling/word problems;
8. probability and statistics;
9. plane geometry;
10. solid geometry;
11. coordinate/vector/trigonometric capabilities where supported;
12. calculus/derivative/extrema capabilities for PROFILE where supported;
13. parameter problems and high-complexity algebraic reasoning where supported;
14. high-complexity geometry/proof capabilities where supported;
15. any additional verified official capability domain required to avoid false completeness.

Do not force these headings if official evidence supports a better decomposition. They are coverage prompts, not canonical taxonomy.

## ROUTE RULES

- BASE and PROFILE are route overlays of one Mathematics Identity Model.
- The same mathematical capability should be one semantic candidate when meaning is the same across routes.
- Route/year/task number stays mapping metadata.
- A task may map to several capabilities.
- Several tasks may map to one capability.
- Difficulty or exam position alone must not split identities.
- Profile-only advanced capabilities may legitimately be PROFILE-only candidates.

## SOURCE RULES

Use verified repository source evidence.

Prefer official FIPI demo/specification/codifier evidence for exam-route truth and verified curriculum/source material already admitted in repo for broader mathematical capability meaning.

Do not use AI intuition as source truth.

If source evidence is insufficient for a proposed capability boundary, mark `NEEDS_SOURCE_REVIEW` rather than inventing certainty.

## DEDUPLICATION / GRANULARITY

Before output:

- compare candidates against the existing canonical identity `math-probability-classical-equally-likely`;
- detect duplicates/near-duplicates among new candidates;
- distinguish concept identity from operation/subskill only when source and adaptive-learning utility justify it;
- do not create hundreds of identities merely mirroring individual FIPI items;
- do not collapse materially different capabilities into one vague identity merely to minimize count.

Create an explicit `NEEDS_SUBJECT_REVIEW` queue for ambiguous granularity rather than silently deciding.

## REQUIRED ARTIFACTS

Under the new inventory path produce at minimum:

1. `MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-v0.1.json`;
2. `MATHEMATICS-FULL-SUBJECT-SOURCE-COVERAGE-v0.1.json`;
3. `MATHEMATICS-FULL-SUBJECT-DUPLICATE-GRANULARITY-REVIEW-v0.1.json`;
4. `MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-VALIDATION.txt`;
5. deterministic materializer/validator scripts necessary to reproduce the artifacts;
6. concise result artifact stating counts, unresolved items and recommended first coherent admission wave.

## VALIDATION

Prove:

- all candidates have source refs;
- all candidates are `CANDIDATE_NOT_CANONICAL`;
- zero accepted demo files changed;
- zero source PDFs changed;
- zero shared PEIS contracts changed;
- existing canonical math identity preserved exactly;
- task number is never used as semantic ID;
- BASE/PROFILE route overlay rule preserved;
- duplicate/ambiguous candidates are surfaced explicitly;
- major subject domains supported by source are represented or explicitly marked as uncovered/needs review;
- deterministic regeneration produces identical structured outputs, excluding explicitly non-deterministic metadata if any.

## RECOMMENDED FIRST ADMISSION WAVE

The result must recommend one bounded coherent first wave based on:

- strong source completeness;
- high prerequisite/routing leverage;
- broad applicability across BASE/PROFILE where useful;
- ability to create independent verification items;
- minimal semantic ambiguity.

Do not canonically admit that wave in this task.

## ACCEPTANCE_EVIDENCE

Return:

- `CURRENT_MAIN_SHA`;
- branch/commit/PR;
- candidate count;
- source-backed count;
- needs-source-review count;
- needs-granularity-review count;
- domain coverage summary;
- duplicate/overlap summary;
- recommended first admission wave with candidate IDs and rationale;
- exact validation commands/results;
- `ACCEPTED_DEMO_FILES_CHANGED=0`;
- `SOURCE_AUTHORITY_FILES_CHANGED=0`;
- `SHARED_PEIS_CONTRACTS_CHANGED=0`;
- `CANONICAL_IDS_AUTO_ADMITTED=0`.

## STOP_CONDITIONS

Stop rather than broaden scope if:

- required official source is genuinely absent/corrupt;
- source conflicts prevent a capability boundary;
- completing inventory requires changing accepted demos;
- a new cross-subject/shared-PEIS architecture decision becomes necessary;
- semantic admission would require human/subject authority.

## FINAL_STATUS

Success only:

`MATHEMATICS_FULL_SUBJECT_CANDIDATE_INVENTORY_READY`

Otherwise one exact blocker:

- `BLOCKED_MATHEMATICS_SOURCE_AUTHORITY`
- `BLOCKED_MATHEMATICS_SCOPE_CONFLICT`
- `BLOCKED_MATHEMATICS_INVENTORY_DETERMINISM`

No canonical admission and no production integration claim in this task.
