# PEIS-INTEGRATION-001 — Russian EGE trainer sensor to shared PEIS

Date: 2026-08-20
Status: IMPLEMENTATION
Baseline: `main@80b361f6071fb6fd9671b8409fb0ccd2c2aa7071`

## Milestone

Move the first real current-product-shaped learner attempt through the already merged shared PEIS stack:

`current Russian trainer checked card -> canonical EvidenceEvent 277 -> shared persistence -> deterministic shared PEIS recompute -> shared NBA -> exact diagnostic/remediation/verification -> measured learner-state delta`.

This task is the first integration gate after PEIS-PERSISTENCE-001. It is not a new learner engine and it is not a Tilda deployment task.

## Real product surface

Current Russian EGE trainer runtime:

- `russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-10.txt`
- `PROGRESS_KEY=eksamio:ege-russian-trainer:progress:v1`
- `SESSION_KEY=eksamio:ege-russian-trainer:session:v1`
- `checkCurrent(card)` creates `{score,max,answer}` and writes `session.checked[card.id]`;
- `recordCard(card,checked)` writes only legacy product progress;
- session identity is currently represented by `session.startedAt` plus the selected card IDs.

Current Task 12 source card:

- bank chunk: `ege-russkiy-trenazher-T123-06.txt`
- card: `ege-ru-12-2026-12-01`
- task: 12
- response kind: `unordered_digits`
- deterministic whole-card scoring: max 1.

## Precision boundary

The current Task 12 trainer card mixes multiple semantic causes inside one whole-card answer. A whole-card failure therefore MUST NOT become an exact semantic failure.

For `ege-ru-12-2026-12-01`, the product sensor emits source-verified `COMPOSITE` mappings to:

- `school-verb-personal-ending-conjugation-base`
- `school-participle-vowel-suffix-conjugation-base`

An incorrect whole-card result produces `UNKNOWN_OR_INSUFFICIENT_PRECISION`, not `EXACT_RULE_ERROR`.

Expected PEIS response after only this real trainer event:

- prerequisite evidence remains unknown;
- target readiness = `INSUFFICIENT_EVIDENCE`;
- NBA = `DIAGNOSE_TARGET` for the prerequisite semantic identity.

This is a required guardrail, not a limitation to work around by guessing.

## Reuse requirements

Must reuse without mutation:

- EvidenceEvent contract 277;
- materialized learner state contract 278;
- mastery/readiness/retention/NBA contracts 282–285;
- legacy adapter policy 279;
- shared `peis-reference-kernel` inference;
- shared `peis-persistence-reference` append/replay/recompute boundary;
- RU-SLICE-001 verified semantic mappings, item fixtures and canonical prerequisite edge.

## Implementation scope

Create an additive reference integration package that:

1. parses the actual current trainer bank/runtime artifacts during validation;
2. converts the actual `card + session + checked` product shape into a canonical EvidenceEvent;
3. derives stable event/idempotency identity from the existing session/card identity without changing the current trainer runtime;
4. requires learner identity from the shared host boundary; it does not invent authentication;
5. persists the event through `PeisPersistenceStore`;
6. recomputes the target state/NBA through the shared kernel;
7. exposes a read-side product directive containing NBA/state routing data only;
8. continues the closed loop through already verified RU-SLICE-001 exact diagnostic, repair and independent verification events;
9. records recommendation outcomes so the final independent success is linked to the recommendation that requested it.

## Identity boundary

This task does not implement login/authentication.

`learner_profile_id` and an anonymous or user identity ref are required inputs from the shared host boundary. Email is forbidden as the academic-history key.

The current Russian trainer localStorage is not promoted into canonical learner identity or canonical learner state.

## Production safety

Forbidden in PEIS-INTEGRATION-001:

- editing Tilda/live page code;
- changing current trainer scoring;
- changing `PROGRESS_KEY` / `SESSION_KEY` semantics;
- replacing or deleting current localStorage progress;
- writing PEIS mastery/readiness/retention into legacy product progress;
- changing shared PEIS contracts;
- creating Russian-specific persistence/mastery/NBA engines;
- AI Tutor or voice work.

The reference package may read real trainer artifacts and reproduce their event shape in CI. Live runtime wiring requires a subsequent explicit integration gate after this task passes.

## Required validation

PASS requires all of the following:

1. the actual current Task 12 card is loaded from `T123-06`, not duplicated as invented fixture content;
2. the actual runtime contains the expected `checkCurrent` / `recordCard` product surfaces;
3. current trainer-shaped wrong answer validates against EvidenceEvent 277;
4. semantic mapping is COMPOSITE and exact error inference is absent;
5. duplicate product sensor delivery is idempotent;
6. first shared recompute returns `INSUFFICIENT_EVIDENCE -> DIAGNOSE_TARGET`;
7. exact prerequisite diagnostic failure changes readiness to `BLOCKED_BY_REQUIRED_PREREQUISITE -> LEARN_PREREQUISITE`;
8. independent prerequisite re-verification changes readiness to `READY_TO_LEARN_OR_PRACTICE`;
9. assisted target success requires `INDEPENDENT_PRACTICE`;
10. fresh independent target verification produces mastery `DEVELOPING` and NBA `RETENTION_REVIEW`;
11. recommendation outcome log links final independent success to the prior NBA;
12. source trainer artifacts remain byte-identical after the validation run;
13. no subject-specific learner engine is created.

## Completion boundary

Passing this task proves the first real current-product-shaped PEIS closed loop in repository/CI reference integration.

It does NOT yet claim that the live Tilda trainer is connected to a production PEIS service. The next gate after merge is a minimal live-safe transport/read-side bridge behind an explicit integration boundary, preserving current scoring/localStorage behavior as fallback.
