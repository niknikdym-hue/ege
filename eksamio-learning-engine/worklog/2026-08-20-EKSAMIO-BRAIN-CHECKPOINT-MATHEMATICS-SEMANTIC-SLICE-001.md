# Eksamio Brain Checkpoint — Mathematics Semantic Slice 001

Date: 2026-08-20  
Status: PR #56 VALIDATED / PROPOSED CANONICAL PENDING HUMAN ACCEPTANCE

## Current deliverable

`MATHEMATICS-SEMANTIC-SLICE-001` is materialized under:

`eksamio-learning-engine/mathematics-identity/semantic-slices/`

Proposed route-independent identity:

`math-probability-equiprobable-elementary-outcomes`

Meaning: compute probability of an event in a model with equiprobable elementary outcomes by identifying favorable and total outcomes.

## Source authority

The semantic meaning is independently evidenced by:

- official 2022 Mathematics codifier 6.3.1;
- official 2023 Mathematics codifier 6.3.1;
- current 2026 probability requirement/content scope;
- exact reviewed BASE-2026 task-5 variants;
- exact reviewed PROFILE-2026 task-4 variants.

PROFILE task 4 is mixed. The passenger-count 15–19 variant is explicitly excluded from this identity because it requires a nested-event difference. This is a deliberate proof that task number is route metadata, not semantic truth.

## BASE-2025 erratum

PR #54/#55 incorrectly classified BASE-2025 as a source gap. Direct verification at the original baseline SHA proves `matematika-source-2025/` and all three official BASE source PDFs were already present.

Correct state:

- explicit known source gaps in the 10-cell base/profile × 2022–2026 matrix: 0;
- BASE-2025: exact official source present; route-build package absent;
- PROFILE-2022: source/prelock present; route-build package absent/unconfirmed.

The validator now checks the actual BASE-2025 files, preventing recurrence of this large-tree listing bug.

## Slice content

- 12 original deterministic items;
- 4 diagnostic;
- 4 targeted practice;
- 4 fresh independent verification;
- 5 shared EvidenceEvent fixtures;
- no AI evaluation;
- no copied FIPI wording;
- no multiple-target item.

## PEIS execution

GitHub Actions run `32332130299`, job `96314663842`: SUCCESS.

The unchanged shared `peis-reference-kernel/` executed two Mathematics golden scenarios.

Main scenario:

`real exact BASE-2026 error -> GUIDED_PRACTICE -> assisted success -> INDEPENDENT_PRACTICE -> fresh independent verification -> RETENTION_REVIEW -> delayed retention success -> MOVE_TO_NEXT_TARGET`

Measured qualitative mastery-state delta:

`EMERGING -> DEVELOPING -> STRONG`

Readiness uses **zero** fabricated Mathematics prerequisite edges. This is intentional: contract 283 forbids inventing a dependency merely to exercise the readiness engine.

## Shared-platform proof

This is the first real Mathematics semantic fixture executed through the same subject-neutral PEIS kernel already used by Russian.

No Mathematics-specific copy was created of:

- learner evidence;
- learner state;
- mastery;
- readiness;
- retention;
- NBA.

No Mathematics branch or semantic ID was hard-coded into the shared kernel.

## Admission boundary

The identity remains:

`SOURCE_VERIFIED / PROPOSED_CANONICAL_PENDING_HUMAN_PR_ACCEPTANCE`

PR #56 merge is the human project-admission gate. Until merge, do not claim that the canonical Mathematics semantic registry in `main` contains this ID.

## Production boundary

Not changed:

- existing math source/demo content;
- scoring;
- T123;
- localStorage;
- Tilda/production;
- shared PEIS contracts.

## Next gate after human acceptance

1. Treat the admitted seed as the first canonical Mathematics semantic identity.
2. Expand the registry only through the same source-backed dedupe/granularity gate; do not mass-generate IDs from task numbers.
3. Select the next identity where either a genuinely source-backed prerequisite can be admitted or another cross-route mapping materially expands PEIS evidence quality.
4. Keep PROFILE-2022 and BASE-2025 route-build gaps separate from semantic/source truth.
