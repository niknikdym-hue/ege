# Eksamio Brain Checkpoint 05 — Mathematics Semantic Slice 001 / Two-Subject PEIS Proof

**Date:** 2026-08-20  
**Status:** DURABLE BRAIN CHECKPOINT  
**Repository:** `niknikdym-hue/ege`

## MAIN BASELINE

Actual `main` at checkpoint creation:

- `29cb2b50e51b91c3be9714f305ffbb4d26de7e6f`
- merge: PR #60 — `MATH-SLICE-001: first source-backed Mathematics PEIS slice`.

This SHA is a continuation anchor, not a substitute for re-fetching current `main` in future work.

## MILESTONE CLOSED

The shared PEIS reference architecture is now demonstrated with real source-backed subject semantics in two materially different P0 subjects:

1. Russian — RU-SLICE-001;
2. Mathematics — MATH-SLICE-001.

The common loop has now been exercised without a subject-specific learner engine:

`source-backed semantic identity -> EvidenceEvent -> shared mastery/readiness/retention/state -> NBA -> targeted practice/help -> fresh independent verification -> measured state delta`

This closes the architecture-proof question: a single PEIS can consume different subject layers.

It does **not** mean production persistence, live learner accounts, telemetry, calibrated forecasting or production recommendation delivery are implemented.

## MATH-SLICE-001 — CANONICAL SUBJECT RESULT

First admitted Mathematics semantic identity:

`math-probability-classical-equally-likely`

Meaning is intentionally narrow:

- finite simple equally-likely outcome model;
- probability as favorable outcomes / total outcomes;
- simple complement count may be used to obtain favorable outcomes first.

Explicitly excluded from this identity:

- probability addition/subtraction as a distinct operation;
- conditional probability;
- multiplication of probabilities;
- Bernoulli formula;
- combinatorial probability that needs a separate counting model;
- continuous probability distributions.

This prevents exam task number or generic answer type `probability` from becoming a false semantic identity.

## SOURCE AUTHORITY USED

Official FIPI 2024 Mathematics codifier supplies the subject-level requirement to compute probabilities in simple cases.

Exact item mappings admitted for the first slice:

### Base route

- 2024 example 5.1 — 7 favorable outcomes among 35 equally selectable divers -> 0.2;
- 2024 example 5.2 — 97 good outcomes among 100 bulbs -> 0.97.

### Profile route

- 2024 task 4, official variant 1 — 2 favorable tickets among 25 equally selectable tickets -> 0.08.

Explicit non-mappings:

- profile task 4 variant 2 — difference of nested event probabilities;
- profile task 5 variants — conditional-probability reasoning.

No canonical prerequisite edge was admitted.

## EXECUTABLE VALIDATION

GitHub Actions validation:

- workflow: `Mathematics Semantic Slice 001 Validation`;
- run: `32375529794`;
- job: `96445885969`;
- validated head: `18b56fc423afe43d24e885f08673df306891c0e4`;
- result: **PASS**.

Validated against shared contracts:

- 277 EvidenceEvent;
- 278 materialized learner state;
- 282 mastery;
- 283 readiness/prerequisite;
- 284 retention;
- 285 NBA.

Temporary validation workflow was removed before merge.

## GOLDEN LEARNER SEQUENCE

### 1. Exact unassisted diagnostic failure

- mastery: `EMERGING`;
- confidence: `HIGH`;
- readiness: `READY_TO_LEARN_OR_PRACTICE`;
- retention: `NOT_ELIGIBLE_INSUFFICIENT_EVIDENCE`;
- NBA: `GUIDED_PRACTICE`.

### 2. Correct answer after guided hint

- mastery remains `EMERGING`;
- confidence remains `HIGH`;
- readiness remains ready;
- retention remains not eligible;
- NBA becomes `INDEPENDENT_PRACTICE`.

The assisted result does not promote mastery by itself.

### 3. Fresh independent same-session verification

- mastery: `DEVELOPING`;
- confidence: `MODERATE`;
- readiness: `READY_TO_LEARN_OR_PRACTICE`;
- retention: `SCHEDULED`;
- NBA: `RETENTION_REVIEW`.

Measured state delta:

`EMERGING -> DEVELOPING`

No numeric mastery coefficient is invented.
No retention due timestamp/window is invented.
Same-session verification is not misrepresented as delayed retention.

## PREREQUISITE SAFETY PROOF

A synthetic REQUIRED-shaped edge was supplied only as `TEST_FIXTURE_ONLY`.

Result:

- it produced zero canonical prerequisite assessments;
- it did not block readiness;
- it was not promoted into Mathematics subject truth.

Therefore shared readiness correctly enforces the canonical admission boundary rather than merely trusting relation shape/review labels.

## PROJECT ARCHITECTURE RESULT

We have now proven the reusable shared kernel on:

- language/grammar semantics;
- mathematical probability semantics.

This is sufficient to stop spending the central P0 lane on additional reference-kernel demonstrations as the primary bottleneck.

Additional subject slices remain useful only when they prove a new system property or are required for subject integration.

## NEXT CENTRAL BOTTLENECK

The project now moves from **reference proof** to **production-grade shared learning-state plumbing**.

Next shared-platform gate:

`PEIS-PERSISTENCE-001`

Required outcome:

`append EvidenceEvent -> durable/idempotent event store boundary -> deterministic materialized-state recompute -> learner semantic snapshot -> recommendation outcome/verification telemetry`

The implementation must remain subject-neutral.

It must support Russian and Mathematics fixtures without creating new subject learner engines.

### Required first capabilities

1. append-only EvidenceEvent persistence boundary;
2. event idempotency / duplicate rejection by stable event identity;
3. deterministic replay/recompute of learner semantic state from accepted events;
4. stable learner/subject/semantic query boundary;
5. recommendation outcome logging boundary;
6. verification / assistance / retention / transfer / recurrence telemetry carried without destroying provenance;
7. anonymous learner continuity boundary designed so later authentication can attach identity without rewriting historical evidence.

## IMPLEMENTATION BOUNDARY FOR PEIS-PERSISTENCE-001

Before writing new runtime, audit current repository for any existing persistence/storage/event-log implementation that can be reused.

Do not create a parallel store if an approved shared implementation already exists.

The first implementation may be a deterministic reference/service boundary suitable for local/CI validation, but must distinguish clearly:

- durable contract;
- reference implementation;
- production deployment.

Do not falsely label an in-repo SQLite/file fixture as live production infrastructure.

## PARALLEL LANES

### Russian P0

Continue `RUSSIAN-121-CARD-PEIS-INTEGRATION-LEDGER`:

`practice_item -> exception_id -> canonical semantic mapping -> evidence precision -> EvidenceEvent 277 -> adapter 279 -> shared PEIS -> independent verification`.

PR #23 remains salvage/content source, not merge-as-is architecture.
PR #57 remains HOLD until the ledger demonstrates actual need for new `ru-*` admissions.

### Mathematics demo/source P0

Profile Mathematics demo/source work continues independently.
Do not let task numbers become semantic identities.
Do not make PEIS work rewrite mature demo/source packages unnecessarily.

### Physics P1

Physics exact-source/demo work continues in its isolated subject contour.
No Physics learner engine.
Any diverged PR must revalidate against current main before merge.

## DO NOT DO NEXT

- do not start AI Tutor as the central lane yet;
- do not start voice/realtime;
- do not introduce final mastery coefficients/forgetting curves without calibration evidence;
- do not build subject-specific persistence/state engines;
- do not couple persistence implementation to a single Russian or Mathematics product UI;
- do not treat reference fixtures as production telemetry;
- do not modify Tilda/production demo/scoring/localStorage inside the shared persistence task without a separate integration gate.

## NEXT EXECUTION ORDER

1. Audit actual current `main` for reusable evidence persistence/event-log/state-recompute code.
2. Define the smallest `PEIS-PERSISTENCE-001` implementation task against contracts 277/278/282/283/284/285 and existing kernel.
3. Build one shared append/replay/recompute path.
4. Validate it with both RU-SLICE-001 and MATH-SLICE-001 fixtures.
5. Add idempotency/replay-order tests and recommendation/verification telemetry checks.
6. Record durable validation and merge only after scope/path review.
7. Then choose the next production integration gate from measured bottlenecks.

## AUTHORITY FOR NEXT CONTINUATION

Read in order:

1. `eksamio-learning-engine/00-PRODUCT-MASTERPLAN.md`
2. `eksamio-learning-engine/00B-PROJECT-PRIORITIES-CURRENT.md`
3. `eksamio-learning-engine/00C-IMPLEMENTATION-GOVERNANCE-GUIDE.md`
4. `eksamio-learning-engine/00D-BRAIN-CONTINUITY-PROTOCOL.md`
5. this checkpoint
6. shared contracts 277/278/279/282/283/284/285
7. `eksamio-learning-engine/peis-reference-kernel/`
8. RU-SLICE-001 verified fixtures/results
9. MATH-SLICE-001 verified fixtures/results
10. actual current branch/PR being reviewed.
