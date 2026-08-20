# Eksamio Brain Checkpoint 06 — PEIS Persistence

Date: 2026-08-20
Authority status: durable project checkpoint after merge of PEIS-PERSISTENCE-001.

## Current main baseline

PEIS-PERSISTENCE-001 merged through PR #62.
Merge commit: `b036bd085606eaa2f05d8cb3849712ea87a4dd94`.

The project has now proven one shared PEIS across Russian and Mathematics at two levels:

1. deterministic subject-neutral inference through the shared reference kernel;
2. deterministic subject-neutral append/replay persistence through the shared persistence boundary.

## What is now established

The shared persistence boundary under `eksamio-learning-engine/peis-persistence-reference/` provides the current reference implementation for:

- append-only storage of canonical EvidenceEvent 277 payloads;
- idempotent event replay by `event_id` and `idempotency_key`;
- rejection of conflicting retries;
- learner / subject / semantic evidence queries;
- deterministic effective replay independent of insertion order;
- append-only correction/retraction history without raw evidence mutation;
- rebuildable materialized state cache computed by the existing shared PEIS kernel;
- anonymous-to-authenticated identity continuity without rewriting historical evidence;
- append-only NBA proposal and NBA outcome logging against contract 285;
- raw telemetry for assistance, verification, transfer, retention, evaluator trust and provenance.

The persistence layer does NOT own mastery/readiness/retention/NBA inference. The existing shared PEIS kernel remains the inference owner.

## Validation result

GitHub Actions run `32376949923`, job `96450555184`: PASS.

Validated outcomes include:

- Mathematics persisted replay -> mastery `DEVELOPING` -> NBA `RETENTION_REVIEW`;
- Russian persisted replay -> prerequisite `MET` -> readiness `READY_TO_LEARN_OR_PRACTICE` -> mastery `DEVELOPING` -> NBA `RETENTION_REVIEW`;
- Russian forward and reverse insertion -> identical snapshot;
- duplicate application suppression -> PASS;
- identity continuity -> PASS;
- immutable raw evidence -> PASS;
- append-only correction boundary -> PASS;
- NBA outcome logging -> PASS;
- no numeric mastery coefficient invented;
- no retention due time invented;
- no subject-specific learner engine created.

Durable validation artifacts:

- `peis-persistence-reference/PEIS-PERSISTENCE-REFERENCE-BOUNDARY-v0.1.json`
- `peis-persistence-reference/PEIS-PERSISTENCE-001-RUN-OUTPUT.json`
- `peis-persistence-reference/PEIS-PERSISTENCE-001-VALIDATION.txt`

## Architectural invariant after this checkpoint

There is still exactly one PEIS.

Subjects may provide verified knowledge, semantic identities, item mappings, subject-specific evaluators/tools and source-backed prerequisite relations.

Subjects must not create their own canonical learner state, mastery, readiness, retention, recommendation/NBA or universal evidence contracts.

Legacy product state remains compatibility input only and must enter PEIS through explicit adapters such as contract 279.

## Central bottleneck now

The reference architecture is no longer the primary bottleneck.

The next central gate is **PEIS-INTEGRATION-001**: connect one real product sensor to the shared EvidenceEvent -> shared persistence -> deterministic recompute -> shared state/NBA loop without embedding another learner engine in the product.

The first integration surface is Russian because RU-SLICE-001 already has:

- exact semantic mappings;
- a source-verified canonical prerequisite edge;
- deterministic item/evaluator fixtures;
- real current Russian trainer/source context;
- adapter 279 coverage for current Russian product state.

The integration must proceed by lowest-risk stages:

1. audit the real current Russian trainer event/progress/session surfaces;
2. define an additive product-sensor adapter that emits canonical EvidenceEvent without changing current product scoring truth;
3. validate against real trainer-shaped events and RU-SLICE-001 semantic mappings;
4. send accepted events into the shared persistence boundary;
5. recompute shared PEIS state/NBA;
6. expose a read-side integration contract back to the product;
7. only after deterministic validation, consider live runtime wiring behind an explicit integration gate.

## Explicitly not next

Do not make AI Tutor, voice, engagement UI, new subject-specific learner state, or broad production redesign the central line before PEIS-INTEGRATION-001 is closed.

Do not rewrite Tilda, current EGE scoring, current trainer localStorage or legacy Russian runtime merely to make integration convenient.

## Parallel lanes remain isolated

- Russian subject lane: 121-card PEIS integration ledger and semantic mapping salvage; no autonomous learner engine.
- Mathematics demo/source lane: continues independently.
- Physics source/demo lane: continues independently as P1 and must not slow the P0 PEIS integration path.

## Leadership decision

The project now moves from architecture proof to real product integration.

Success for the next milestone is not another schema or fixture. It is a reproducible real-product-shaped closed loop:

`product attempt -> canonical EvidenceEvent -> append-only shared persistence -> deterministic PEIS recompute -> shared NBA -> independent verification -> second EvidenceEvent -> measured learner-state delta`.
