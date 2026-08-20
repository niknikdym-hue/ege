# Eksamio Brain Checkpoint 08 — PEIS Service Bridge

Date: 2026-08-20
Status: DURABLE PROJECT CHECKPOINT
Main at checkpoint start: `4ac61b82971383638651278d90153c1b1403cd2d`

## 1. Central milestone reached

`PEIS-SERVICE-BRIDGE-001` is merged.

The project now has an executable subject-neutral service/transport boundary on top of the already merged shared PEIS persistence + reference kernel.

Validated chain:

`browser-safe checked-card facts`
→ `registered server-side subject adapter`
→ `server-owned scoring / semantic mapping / evaluator trust`
→ `EvidenceEvent 277`
→ `shared persistence`
→ `shared PEIS recompute`
→ `shared NBA persistence`
→ `read-only product directive`

This is no longer only an in-process integration fixture. A real loopback JSON/HTTP transport was validated.

## 2. Trust boundary is now explicit and executable

The client/browser is not allowed to assert canonical educational truth.

Rejected client-owned fields include:
- score / correctness;
- semantic_targets / semantic mapping;
- evaluator trust;
- mastery;
- NBA;
- server_sequence;
- server_watermark.

The server owns:
- canonical evaluator/scoring path for the admitted adapter;
- semantic mapping supplied by verified subject artifacts;
- evaluator trust class;
- receive timestamp;
- server sequence / watermark;
- persistence append/replay;
- PEIS recomputation;
- canonical NBA proposal.

Email is explicitly forbidden as the academic-history identity key in the reference boundary.

## 3. Russian current-product proof remains the admitted first route

The first registered adapter is:

`russian-ege-trainer-task12-v0.1`

It uses the actual current Russian EGE trainer Task 12 card bank and server-recomputes the whole-card result from the pinned answer key.

A broad Task 12 failure remains `COMPOSITE` and does not become an invented exact semantic error.

The resulting PEIS response remains:

`DIAGNOSE_TARGET`

until exact evidence is obtained.

## 4. Important implementation distinction

The merged service bridge is still a REFERENCE SERVICE BOUNDARY.

It is NOT yet:
- public production deployment;
- production authentication/authorization;
- deployed durable multi-user infrastructure;
- live Tilda wiring;
- a replacement for the current trainer runtime;
- permission to move canonical learner state into JavaScript/localStorage.

The loopback HTTP fixture intentionally preserves Python sqlite3 thread-affinity safety. It does not weaken the shared persistence contract merely to satisfy a threaded test harness.

## 5. Shared PEIS invariants remain intact

There is still exactly one shared:
- EvidenceEvent contract;
- learner history / persistence boundary;
- mastery inference path;
- readiness path;
- retention path;
- NBA path.

No Russian Student Model or Russian learner engine was created.

Subject adapters may own verified subject truth and deterministic subject evaluation, but never canonical learner state.

## 6. Live product safety rule

The next integration step must be fail-open from the learner-facing product perspective.

A PEIS transport failure must NOT:
- break answer checking;
- block navigation;
- corrupt or replace existing local progress;
- change scoring;
- make the trainer unusable;
- fabricate mastery from local product state.

The current trainer must continue functioning if PEIS is unavailable.

Therefore the first browser hook must be optional / feature-gated and additive.

## 7. Next central bottleneck

Next gate:

`PEIS-BROWSER-HOOK-001`

Goal:
prove that the actual current Russian trainer's checked-card boundary can produce the minimal browser-safe service request and consume only a read-only PEIS directive without changing current scoring/progress behavior.

The gate should validate:
1. payload is built only from facts already known by current trainer runtime;
2. client does not send score/correctness/semantic truth/mastery/NBA;
3. transport can be disabled by configuration;
4. transport timeout/failure is non-blocking and fail-open;
5. duplicate submission has stable request/event identity;
6. existing `recordCard`, scoring, session completion and localStorage continue unchanged;
7. returned directive is advisory/read-only and cannot overwrite canonical state locally;
8. no live endpoint/deployment claim is made until deployment/auth decisions are separately admitted.

## 8. Scope rule for PEIS-BROWSER-HOOK-001

Do NOT modify production/Tilda directly in the first gate.

Preferred implementation:
- a browser-hook module/reference patch or installable snippet;
- a controlled current-runtime integration fixture;
- deterministic validator proving byte-preservation or narrowly authorized additive diff;
- no publication to Tilda;
- no backend deployment.

Only after this gate passes should a separate production rollout gate decide whether and how to wire the hook into the published trainer.

## 9. Other subject lanes

Russian and Mathematics remain P0 subject tracks.
Physics remains P1 and may progress in parallel only without slowing shared PEIS or P0 work.

Do not modify their parallel source/demo paths from the browser-hook task unless required by a separately admitted dependency.

## 10. Current architectural sequence

Merged foundation now supports:

`verified subject truth`
→ `semantic identity`
→ `EvidenceEvent`
→ `shared persistence`
→ `shared PEIS inference`
→ `NBA`
→ `current-product-shaped integration`
→ `subject-neutral service boundary`

Next:

`fail-open browser hook`
→ later `deployment/auth gate`
→ later `controlled production rollout`
→ measurable real learner outcomes.

The project must not skip directly from reference HTTP to uncontrolled production wiring.
