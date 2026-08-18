# RESULT-004 — Russian Exceptions P0 transfer closure

Date: 2026-08-12

## Decision

**PASS as the current non-production 93-card checkpoint.**

Tilda/publication remains **HOLD** until the user explicitly moves to the Tilda preview/publication step.

## Baseline

The original 80 active learner cards received a full linguistic/source audit:

- 80/80 reviewed;
- PASS: 48;
- FIX: 30;
- FAIL-REPLACE: 2;
- HOLD: 0.

Durable audit:
`130-RUSSIAN-EXCEPTIONS-80-CARD-DRABKINA-AUDIT-v0.1.txt`

The two unsafe active cases were replaced:

- universal non-introductory `в конце концов` -> context-dependent contrast;
- obsolete current answer `зоревать` -> `заревать`.

The 30 FIX items were upgraded through course-grade feedback/provenance handling, and 8 additional terse but correct learner explanations were polished after inspecting the generated payload.

## Wave 5

Goal: close remaining P0 practice/transfer gaps without adding random cards merely to increase count.

Reviewed Wave 5:
`140-RUSSIAN-EXCEPTIONS-PRACTICE-WAVE5-P0-TRANSFER-v1.0.json`

Manual review:
`138-RUSSIAN-EXCEPTIONS-WAVE5-MANUAL-CONTENT-REVIEW.txt`

Cards added: 13.

Coverage targets:

- `признательный / признанный` — both directions;
- `скачу` current full-rule transfer;
- `заревал` current-norm inflected transfer;
- `доктора`;
- `помидоров`;
- `ворот`;
- `жёванный` participial context;
- `стеклянный` vs `кожаный`;
- `оловянный` vs `серебряный`;
- `деревянный` vs `глиняный`;
- `вопреки совету`;
- `по окончании` after-event transfer.

Manual content review: **PASS 13/13**.

## Candidate gate before promotion

Wave 5 was first built and tested separately from current practice.

Isolated candidate result:

- 93-card candidate build: PASS;
- schema/content validation: PASS;
- coverage: PASS;
- P0/P1 uncovered: 0;
- learner-safe runtime: PASS;
- T123 chunks: PASS;
- standalone package: PASS;
- Chromium preview: PASS.

Only after this candidate PASS and 13/13 manual review was Wave 5 promoted into current manifest 119.

## Current manifest

`119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json`

Current counts:

- raw registered items: 95;
- disabled historical items: 2;
- active learner cards: **93**.

Current practice builder:
`build/build_russian_exceptions_practice_course_grade.py`

Current layers:

- `131-RUSSIAN-EXCEPTIONS-COURSE-GRADE-CORRECTIONS-v0.1.json`;
- `136-RUSSIAN-EXCEPTIONS-LEARNER-FEEDBACK-POLISH-v0.1.json`;
- `140-RUSSIAN-EXCEPTIONS-PRACTICE-WAVE5-P0-TRANSFER-v1.0.json`.

## Final current-93 gate

Successful GitHub Actions run:
`31625710299`

Successful gated head:
`202c1484258146c047077b4e38cc93824056950d`

All required steps PASS:

- canonical source: 127 exception/special-case items, 0 warnings;
- current course-grade practice: 93 cards, 0 warnings;
- launch priority build;
- coverage audit;
- explicit replacement and Wave 5 presence checks;
- P0/P1 uncovered = 0;
- runtime: 74 exceptions / 93 practice / 6 topics;
- forbidden learner-source leakage check;
- aggregate Learning Engine validation;
- browser core evaluator/state/selector tests;
- deterministic T123 chunking;
- standalone package build;
- Chromium preview smoke;
- runtime size audit.

Runtime content version:
`sha256-e2acf685bb659fd96971`

Package shape:

- 9 T123 blocks total;
- 4 runtime-data blocks;
- largest T123 block: 34,077 bytes.

## Generated artifact inspection

The successful CI artifact itself was opened after the gate.

Confirmed in final generated runtime:

- exactly 93 practice cards;
- all key Wave 5 cards are present;
- course-grade `кованый / кованный` explanation remains present;
- course-grade `жёваный / жёванный` explanation remains present;
- context-dependent `в конце концов` remains present;
- current `заревать / заревал` remains present;
- post-audit feedback polish remains present;
- user-approved human intro copy is in generated preview;
- internal Rosenthal/Gramota/Drabkina/source_refs/source_path/provenance/rule_ref data is absent from learner runtime.

Chromium preview validation explicitly passed the live package flow, 10-card session, rule drawer, personal-error flow, mobile, corrupt-state handling and fail-closed runtime behavior.

## Build-system defects caught and fixed during gate work

The process caught several real regressions instead of accepting a superficial PASS:

1. Aggregate validation was using an old practice builder and could overwrite reviewed feedback. It now uses the course-grade builder.
2. Candidate T123 custom paths exposed a relative/absolute path bug. The generic builder now normalizes project-relative paths safely and rejects output outside project root.
3. Browser core had a hard-coded `80` assertion. It now reads `expected_active_items` from current manifest and validates runtime consistency.
4. Coverage order was corrected so launch priority is built before coverage audit.

These are durable build-system improvements, not one-off test bypasses.

## Coverage after Wave 5

Canonical source exception/special-case items: 127.

Practice-covered exception IDs: 74.

Uncovered source IDs: 53.

P0/P1 uncovered: **0**.

The remaining 53 are lower-priority P2/P3 source-bank material. Future waves should be selected by pedagogical value and course architecture, not by raw count.

## Safety boundary

- Tilda unchanged.
- Current EGE Russian trainer unchanged.
- Existing EGE trainer answers/scoring/storage unchanged.
- Standalone storage namespace remains separate.
- PR remains draft.
- Public rollout remains HOLD.

## Next recommended work

1. Freeze the 93-card bank as the P0-complete reviewed checkpoint.
2. Select the next P2/P3 expansion wave from the remaining 53 source cases.
3. Reuse Drabkina/Subbotin tables/algorithms and Explanation Bank units so every new card also becomes reusable course material.
4. Require source review + manual item review + isolated machine/Chromium gate before each future wave is promoted.
5. Keep Tilda/publication as a separate explicit user-controlled step.
