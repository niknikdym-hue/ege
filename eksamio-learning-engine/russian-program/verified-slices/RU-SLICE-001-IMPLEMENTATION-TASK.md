# RU-SLICE-001 — Implementation Task

**Status:** READY FOR IMPLEMENTATION  
**Date:** 2026-08-19  
**Scope:** Russian subject slice only + shared-contract fixtures; no production integration

## Goal

Materialize the smallest source-complete Russian content/fixture package that can feed the first shared PEIS executable closed-loop test.

The slice is fixed by `RU-SLICE-001-TASK12-CONJUGATION-PARTICIPLE-SOURCE-GATE-v0.1.json`:

- prerequisite/direct target: `school-verb-personal-ending-conjugation-base`;
- primary target: `school-participle-vowel-suffix-conjugation-base`;
- conditional REQUIRED prerequisite: conjugation -> present-tense participle suffix selection.

Do not expand this task into a general Russian course build.

## Authority

Must reuse, not replace:

- `../../277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json`;
- `../../278-EKSAMIO-LEARNER-STATE-MATERIALIZED-VIEW-SCHEMA-v0.1.json`;
- `../../282-EKSAMIO-MASTERY-INFERENCE-CONTRACT-v0.1.json`;
- `../../283-EKSAMIO-PREREQUISITE-READINESS-CONTRACT-v0.1.json`;
- `../../284-EKSAMIO-RETENTION-SCHEDULE-STATE-CONTRACT-v0.1.json`;
- `../../285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json`;
- the Russian source gate in this directory;
- canonical/source/explanation artifacts cited by that source gate.

## Required outputs

Create only subject-slice data, deterministic checking helpers/fixtures and validation artifacts needed by the future shared PEIS reference kernel.

### 1. Exact-target item bank

Create a small original Eksamio item bank containing at minimum:

- 4 isolated conjugation/personal-ending diagnostic items;
- 4 isolated present-tense participle suffix items;
- 4 fresh independent verification items.

Requirements:

- every item has exactly one declared canonical semantic target;
- wording must be original Eksamio content, not copied from FIPI/demo/trainer cards;
- all answers are deterministic;
- every item carries provenance to the verified rule/source used to construct it;
- include ordinary cases plus only source-reviewed exception boundaries;
- present-tense participle items must stay separate from past-passive participle suffix branches;
- explanation/worked examples must not be reused verbatim as independent verification items.

### 2. Composite-entry fixture

Create a fixture representing the current card `ege-ru-12-2026-12-01` as a composite evidence source.

Its EvidenceEvent mapping must contain both semantic IDs with `mapping_resolution = COMPOSITE`.

A wrong answer must NOT be represented as an exact failure of either semantic identity.

### 3. Exact diagnostic EvidenceEvent fixtures

Create schema-valid EvidenceEvent fixtures for:

- prerequisite diagnostic success;
- prerequisite diagnostic failure;
- target diagnostic success/failure;
- assisted learning event where applicable;
- independent verification success;
- independent verification failure.

Use the shared Event schema exactly. Do not add Russian-only mastery fields.

### 4. Prerequisite edge materialization fixture

Materialize the source-gated edge using the edge schema from contract 283:

- source: `school-verb-personal-ending-conjugation-base`;
- target: `school-participle-vowel-suffix-conjugation-base`;
- relation: `REQUIRED`;
- conditional scope: present-tense participle suffix selection only;
- provenance exactly source-backed;
- review status at least `SOURCE_VERIFIED`;
- do not edit the immutable v0.1 contract file merely to inject data.

This output is data for shared graph materialization/reference-runtime tests, not a Russian readiness engine.

### 5. Golden scenario

Create a deterministic scenario describing/fixture-testing this sequence:

`composite EGE-12 error -> uncertainty over two semantic targets -> isolated prerequisite diagnostic -> readiness decision -> remediation if needed -> prerequisite re-verification -> exact target practice -> independent target verification -> second evidence -> recomputation`

The scenario must explicitly test both branches:

- prerequisite gap confirmed;
- prerequisite already met.

## Required validation

Validation must fail if any of the following occurs:

- a composite task failure is converted into exact semantic failure without exact evidence;
- an item has multiple supposed primary semantic targets;
- a verification item was already exposed as a worked example;
- an answer requires AI judgment;
- the prerequisite edge is applied outside present-tense participle suffix selection;
- a subject-specific learner-state/mastery/readiness/NBA schema is introduced;
- existing trainer/T123/scoring/localStorage/runtime is modified;
- production/Tilda is modified.

## Deliverable boundary

This task closes **Russian slice content/fixture readiness**, not the shared PEIS runtime itself.

The next shared task consumes these fixtures to implement/reference-test:

`EvidenceEvent -> state materialization -> mastery -> readiness -> retention -> NBA`.

## Acceptance

PASS only when:

1. all item/evidence/edge fixtures validate;
2. source provenance is intact;
3. current mixed EGE-12 card is correctly treated as composite evidence;
4. independent verification is genuinely independent;
5. no parallel Russian learner engine exists;
6. a shared-runtime executor can consume the package without needing to reinterpret Russian linguistic truth.
