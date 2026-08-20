# Eksamio Brain Checkpoint 07 — Current-product-shaped PEIS loop

Date: 2026-08-20
Authority status: durable project checkpoint after merge of PEIS-INTEGRATION-001.

## Current main baseline

PEIS-INTEGRATION-001 merged through PR #64.
Merge commit: `e96a3979cf363696a3395c4e566ffad791642a9a`.

The project has now crossed the boundary from isolated reference fixtures to a validated current-product-shaped PEIS integration.

## What was proven

The actual current Russian EGE trainer was audited without mutating it:

- runtime: `russkiy-knigi/ege-russkiy-trenazher/ege-russkiy-trenazher-T123-10.txt`;
- Task 12 bank: `ege-russkiy-trenazher-T123-06.txt`;
- current product surfaces `checkCurrent(card)`, `recordCard(card,checked)`, session `startedAt`, card ID, answer, score/max and mode were used as the sensor shape;
- actual card `ege-ru-12-2026-12-01` was loaded from the repository bank.

A wrong whole-card Task 12 answer was correctly treated as COMPOSITE evidence. The system did not invent an exact semantic error from a broad task failure.

Validated closed loop:

`current trainer whole-card failure`
-> `COMPOSITE EvidenceEvent 277`
-> `shared append-only persistence`
-> `INSUFFICIENT_EVIDENCE / DIAGNOSE_TARGET`
-> `exact prerequisite diagnostic failure`
-> `BLOCKED_BY_REQUIRED_PREREQUISITE / LEARN_PREREQUISITE`
-> `independent prerequisite re-verification`
-> `READY_TO_LEARN_OR_PRACTICE / GUIDED_PRACTICE`
-> `assisted target success`
-> `INDEPENDENT_PRACTICE`
-> `fresh independent target verification`
-> mastery `DEVELOPING`
-> `RETENTION_REVIEW`.

The independent success was also linked to the recommendation that requested independent verification through the shared NBA outcome log.

## Validation

GitHub Actions run `32383756827`, job `96473050656`: PASS.

Durable artifacts:

- `peis-integration-reference/RUSSIAN-EGE-TRAINER-SENSOR-MAP-v0.1.json`
- `peis-integration-reference/russian_trainer_sensor.py`
- `peis-integration-reference/validate_peis_integration_001.py`
- `peis-integration-reference/PEIS-INTEGRATION-001-RUN-OUTPUT.json`
- `peis-integration-reference/PEIS-INTEGRATION-001-VALIDATION.txt`
- `tasks/PEIS-INTEGRATION-001.md`

Safety results:

- current trainer runtime byte-identical after validation;
- current Task 12 bank byte-identical after validation;
- current scoring unchanged;
- current localStorage unchanged;
- no Russian-specific learner engine created;
- canonical learner state remains owned by shared PEIS;
- no live Tilda wiring is claimed yet.

## Architectural significance

The project now has four connected proof layers:

1. shared evidence/state/mastery/readiness/retention/NBA contracts;
2. shared deterministic PEIS kernel across Russian and Mathematics;
3. shared append-only persistence/replay/state boundary across Russian and Mathematics;
4. one current-product-shaped Russian sensor closed loop using the shared stack.

The next blocker is therefore no longer semantic proof or persistence proof.

## Central bottleneck now

The next central task is **PEIS-SERVICE-BRIDGE-001**: create the minimal subject-neutral executable service/transport boundary required for a browser product to submit a checked-card sensor payload and receive a shared PEIS read-side directive.

This task must precede live Tilda wiring because the browser must not embed Python/SQLite/mastery logic and the current reference persistence must not be mislabeled as deployed production infrastructure.

Required boundary:

`browser/product sensor payload`
-> `subject adapter registry`
-> `canonical EvidenceEvent validation`
-> `shared persistence append`
-> `shared PEIS recompute`
-> `NBA persistence/outcome capability`
-> `read-side directive response`.

The service boundary must be subject-neutral. Russian-specific mapping belongs in the Russian adapter, not in the service core.

## Required safety properties for PEIS-SERVICE-BRIDGE-001

- no authentication system is invented; host identity is supplied through an explicit identity boundary;
- email is not the academic-history key;
- no browser/localStorage field becomes canonical mastery;
- no subject-specific learner state is introduced;
- retries are idempotent;
- server sequence/watermark are server-owned rather than trusted from the browser;
- raw client payload cannot claim evaluator trust, semantic precision, mastery or NBA;
- adapter mapping version and source provenance are server-selected;
- response exposes shared state/NBA as read-only data;
- production secrets, deployment provider and public endpoint are not fabricated in repository code;
- no Tilda/live trainer mutation until this service boundary passes deterministic CI.

## What follows after the service bridge

If PEIS-SERVICE-BRIDGE-001 passes, the next gate is a minimal optional browser hook / feature-gated live bridge that preserves current scoring and localStorage as fallback.

After one live-safe Russian route is validated, the same service must be exercised by Mathematics before any claim of a production multi-subject PEIS.

AI Tutor and voice remain downstream. Their correct foundation is real structured evidence, shared learner state and independently measured outcomes, not chat interaction by itself.
