# Eksamio Brain — PEIS Reference Kernel Checkpoint

**Date:** 2026-08-20  
**Status:** DURABLE POST-MERGE CHECKPOINT  
**Repository:** `niknikdym-hue/ege`

## MAIN BASELINE

At this checkpoint actual `main` is:

- `bd63e06706ccc349fdcbd458b745e62c1412d55e`
- merge: PR #52 — executable PEIS reference kernel v0.1.

A later Brain session must re-check actual `main`; this SHA is a historical continuation anchor.

## CENTRAL ARCHITECTURAL CHANGE

The previous central gap was:

> shared Evidence/State/Mastery/Readiness/Retention/NBA contracts exist, but no subject-neutral executable closed loop has been proven.

That gap is now **closed at the deterministic reference-implementation layer**.

It is **not** closed at the production-service layer.

Do not describe this checkpoint as a production Student Learning Twin, production Platform API, persistent Recommendation Service, or production learner database.

## MERGED FOUNDATION NOW AVAILABLE

### RU-SLICE-001

PR #51 merged the first source-backed subject fixture package:

- exact deterministic item bank;
- shared EvidenceEvent fixtures;
- source-verified conditional prerequisite edge fixture;
- golden closed-loop scenarios;
- schema validation.

### Shared PEIS reference kernel

PR #52 merged:

`eksamio-learning-engine/peis-reference-kernel/`

with:

- `peis_reference_kernel.py`;
- `run_reference_kernel_validation.py`;
- `PEIS-REFERENCE-KERNEL-RU-SLICE-001-RUN-v0.1.json`;
- `PEIS-REFERENCE-KERNEL-VALIDATION.txt`.

The kernel recomputes, from accepted EvidenceEvent history plus explicit graph data:

`EvidenceEvent -> learner semantic state -> mastery -> readiness -> retention -> NBA`

## WHAT IS ACTUALLY PROVEN

GitHub Actions run `32303566419` completed PASS.

Direct JSON Schema validation passed for:

- 277 EvidenceEvent;
- 278 learner semantic state;
- 282 mastery;
- 283 readiness;
- 284 retention;
- 285 NBA.

RU-SLICE-001 scenarios passed:

1. prerequisite gap branch — 6 steps;
2. prerequisite already met branch — 5 steps;
3. independent verification failure guardrail — 2 steps.

A structural-only Mathematics smoke passed through the same kernel with no Mathematics subject truth invented.

## FIRST EXECUTED PEIS BEHAVIOR

The prerequisite-gap path now executes as:

`composite EGE error`
→ `prerequisite UNKNOWN`
→ `exact prerequisite diagnostic failure`
→ `BLOCKED_BY_REQUIRED_PREREQUISITE`
→ `LEARN_PREREQUISITE`
→ `independent prerequisite re-verification`
→ `READY_TO_LEARN_OR_PRACTICE`
→ `target GUIDED_PRACTICE`
→ `assisted target success`
→ `INDEPENDENT_PRACTICE`
→ `independent target verification success`
→ `RETENTION_REVIEW`

The composite EGE task failure is not promoted to an exact semantic failure.

## FIRST MEASURED LEARNER-STATE DELTA

For the target semantic identity in the successful repair flow:

- before fresh independent target verification: `EMERGING`;
- after independent target verification: `DEVELOPING`;
- evidence event: `ru001.ev.target.verify.success`.

This is the first executable demonstration that an Eksamio intervention can be followed by independent verification and a recomputed learner-state change.

It is a qualitative/ordinal reference result, not a calibrated production mastery probability.

## POLICY BOUNDARIES PRESERVED

The reference kernel deliberately does NOT invent:

- universal mastery coefficients;
- numeric mastery probability where evidence does not justify calibration;
- universal forgetting curve;
- universal retention intervals;
- subject-specific learner engines;
- AI-owned canonical truth.

`mastery.estimate` remains `null` in the reference policy.

Same-session verification is not treated as delayed retention.

Raw EvidenceEvents remain canonical history; materialized state is recomputable inference.

## SUBJECT-NEUTRALITY STATUS

The kernel itself contains no Russian semantic ID, Russian grammar rule, EGE Russian task ID, or Russian-only branch.

A Mathematics structural-only smoke passes through the same code and produces `VERIFY_UNCERTAIN_STATE` for contradictory exact evidence.

This proves technical subject-neutrality of the reference kernel.

It does **not** yet prove a real Mathematics semantic/knowledge slice because the Mathematics Identity Model and source-backed subject fixtures are still pending.

## RUSSIAN STATUS AFTER THIS MILESTONE

Russian now provides the first verified subject slice and first real PEIS reference-loop proof.

Do not immediately expand all 185 identities or continue lower-priority Exceptions backlog as the main project line.

The next Russian work should be driven by:

- telemetry/learning-outcome needs exposed by the reference loop;
- additional verified slices only when needed to test a new system capability;
- later production adapter work after platform boundaries are ready.

## MATHEMATICS — NOW THE NEXT P0 SUBJECT GATE

The next subject-level priority is to replace the structural Mathematics smoke with real subject truth.

Required sequence:

1. non-destructive inventory of actual current-main Mathematics artifacts;
2. source matrix 2022–2026 for profile and base routes;
3. preserve accepted/verified profile/base demo work;
4. design one Mathematics Identity Model, not separate base/profile knowledge systems;
5. map school knowledge/skills -> semantic identities -> prerequisites -> profile/base routes -> demo/trainer/content objects;
6. select the first real source-backed Mathematics PEIS slice;
7. feed that slice into the already shared reference kernel.

Do not create a Mathematics-specific Evidence/State/Mastery/Readiness/Retention/NBA engine.

## PLATFORM WORK AFTER REFERENCE KERNEL

The production path is now clearer, but must remain dependency-gated.

Next shared platform capabilities after/alongside the real Mathematics slice:

- append-only Evidence store/service interface;
- deterministic state recompute service boundary;
- canonical prerequisite graph materialization boundary;
- recommendation outcome logging;
- telemetry for independent success, transfer, retention, recurrence, assistance and elapsed/cost data;
- learner_profile persistence/linkage;
- anonymous -> authenticated continuity;
- only later production Platform API/storage deployment.

Do not jump directly to AI Tutor or voice.

## METRICS GATE

The reference kernel now makes it possible to begin measuring the product rather than only describing it.

Near-term telemetry must support at least:

- independent verification outcome;
- intervention accepted/completed;
- subsequent independent success/failure;
- transfer result;
- delayed retention result;
- error recurrence;
- assistance intensity;
- elapsed time;
- eventual Score Gain per Minute;
- later cost per successful learning outcome.

No metric should optimize chat length, clicks, or voice minutes as the primary objective.

## DO NOT CLAIM YET

Still NOT proven production-ready:

- persistent Student Learning Twin;
- server-side append-only Evidence Service;
- production Mastery/Readiness/Retention/NBA services;
- account/auth synchronization;
- entitlement/payment integration;
- production Platform API;
- calibrated score forecast;
- intervention-effectiveness model across learners;
- AI Tutor production loop;
- multimodal/voice runtime.

## NEXT BRAIN ACTION

Immediate P0 subject action:

**Start Mathematics Identity Model current-main inventory and source matrix, preserving all verified profile/base work and treating profile/base as route overlays of one Mathematics subject model.**

Immediate shared-system action in parallel:

**Use the now-executable reference loop to define the minimum outcome/telemetry contract needed before production persistence.**

The next major product proof should be a **real Mathematics subject fixture through the same PEIS kernel**, not another structural-only smoke and not a separate learner engine.
