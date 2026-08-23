# RUSSIAN-RU1-121-MAPPING-LANDING-001

**Status:** IMPLEMENTATION TASK / RUSSIAN P0  
**Date:** 2026-08-23  
**Baseline main:** `5a6ae0b5cf20545b532ecb260577061ed4198265`

## WHY_NOW

Russian demos 2022–2026 are manually accepted and closed. The Russian subject lane has completed RU-1 reconciliation of the 121-card Exceptions bank and Central Brain has admitted exactly the 12 semantic identities required to resolve its 25 previously blocked rows.

The highest-value next Russian delta is therefore to land that accepted semantic decision as a deterministic, versioned current-main registry slice + 121-card mapping. Do not reopen demos, re-audit the 121 cards, or import whole historical branches.

## ACTIVE_BLOCKER_OR_MILESTONE

`RU-1 / RUSSIAN FULL-SUBJECT SEMANTIC INTEGRATION`

Current pre-landing ledger remains:

- active = 121;
- EXACT = 91;
- PARTIAL_COMPOSITE = 5;
- BLOCKED = 25;
- integration-ready = 96;
- live-connected = 0.

Target after this task:

- active = 121;
- EXACT = 116;
- PARTIAL_COMPOSITE = 5;
- BLOCKED = 0;
- integration-ready = 121;
- live-connected = 0.

## DEPENDENCY_IN

Read and obey:

- `eksamio-learning-engine/AGENTS.md`;
- `eksamio-learning-engine/00-PRODUCT-MASTERPLAN.md`;
- `eksamio-learning-engine/SUBJECT-DEMO-MANUAL-ACCEPTANCE-2026-08-23.md`;
- `eksamio-learning-engine/SUBJECT-FULL-PROGRAM-COMPLETION-PLAN-2026-08-23.md`;
- `eksamio-learning-engine/russian-program/semantic-registry/RUSSIAN-RU1-121-CARD-ADMISSION-DECISION-v1.0.json`.

Evidence inputs only, not blanket merge authority:

- PR #72 head `6211b3f80f75d8c26c25ca8578f883d861ac254d` — 121-row integration ledger;
- PR #57 head `572a3764ff9d5b99b8d1d61aec64d89eb079e013` — candidate proposal evidence only;
- PR #23 head `2215e47b5c211cbff7e12d5b823a0a835adb7480` — reviewed learner content/source refs only.

## CENTRAL BRAIN ADMISSION BOUNDARY

Exactly these 12 `ru-*` identities are admitted for RU-1 materialization:

1. `ru-lexis-paronym-context-choice`
2. `ru-morphology-noun-nominative-plural-lexical-norms`
3. `ru-orthoepy-verbs`
4. `ru-orthoepy-nouns`
5. `ru-syntax-indirect-speech-construction`
6. `ru-syntax-uncoordinated-apposition-construction`
7. `ru-punctuation-false-introductory-comparison-particles`
8. `ru-punctuation-false-introductory-logical-adverbials`
9. `ru-punctuation-konechno-function-context`
10. `ru-punctuation-pravda-function-context`
11. `ru-punctuation-v-kontse-kontsov-function-context`
12. `ru-orthography-plyvuny-exception`

Do not admit any other PR #57 proposal.

Explicit guards:

- preserve all 185 canonical `school-*` identities unchanged;
- broad `candidate-025 -> ru-morphology-noun-form-norms` is NOT admitted by RU-1;
- `candidate-018 -> ru-orthoepy-normative-stress-selection` is COMPOSITE and is NOT an exact target for the current rows;
- candidate-015 and candidate-053 remain unresolved outside RU-1;
- `candidate-*` refs are never canonical mastery keys.

## MINIMAL_DELTA

Create a small canonical RU-1 registry/mapping layer on current main. Prefer these add-only durable artifacts:

1. `eksamio-learning-engine/russian-program/semantic-registry/RUSSIAN-SEMANTIC-REGISTRY-RU1-v1.0.json`
   - exactly the 12 admitted identities;
   - canonical definitions/scopes copied from the admission decision;
   - exact verified source/provenance refs materialized from PR #57/PR #23 where required;
   - no prerequisite edges invented.

2. `eksamio-learning-engine/russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json`
   - all 121 active cards exactly once;
   - 116 `EXACT` rows;
   - 5 `PARTIAL_COMPOSITE` rows;
   - 0 `BLOCKED` rows;
   - existing exact `school-*` mappings from PR #72 preserved;
   - the 25 resolved rows mapped exactly as specified by the admission decision;
   - the five existing partial/composite target sets preserved exactly and not upgraded to exact.

3. `eksamio-learning-engine/russian-program/validate_russian_exceptions_121_semantic_mapping_v1.py`
   - deterministic validator for the new registry + mapping.

4. Durable validation/result text or JSON under the same Russian-program area if needed.

Do not modify PR #23/#57/#72 branches. Do not wholesale copy their architecture.

## EXPECTED_UNLOCK

PASS produces a current-main, canonical, versioned 121-card Russian mapping with no semantic blocks. This makes the full accepted Exceptions corpus ready for the next bounded shared-PEIS service-adapter connection once the central PEIS production substrate permits it.

Immediate success status:

`RUSSIAN_RU1_121_MAPPING_READY_FOR_SERVICE_CONNECTION`

This task itself must keep `LIVE_CONNECTED=0`.

## EXECUTOR

**Codex** — multi-file deterministic materialization + validation is engineering work. Subject decisions are already fixed; Codex must not reopen them.

## ALLOWED_PATHS

Only:

- `eksamio-learning-engine/russian-program/semantic-registry/**`
- `eksamio-learning-engine/russian-program/RUSSIAN-EXCEPTIONS-121-SEMANTIC-MAPPING-v1.0.json`
- `eksamio-learning-engine/russian-program/validate_russian_exceptions_121_semantic_mapping_v1.py`
- one bounded validation/result artifact under `eksamio-learning-engine/russian-program/`

A temporary GitHub Actions workflow is allowed only if genuinely required to execute deterministic validation and must be removed before final PR acceptance.

## FORBIDDEN

Do not modify:

- Russian demos 2022–2026;
- Tilda/demo runtime;
- current EGE trainer scoring/localStorage/UI;
- PR #23 source/content branch wholesale;
- 185 canonical `school-*` identities;
- shared PEIS schemas/contracts/kernel;
- PEIS production substrate;
- Mathematics/Physics;
- auth/payment/Tutor/provider code.

Do not connect live browser/product traffic in this task.

## REQUIRED MAPPING DELTA

The 25 rows listed in `RUSSIAN-RU1-121-CARD-ADMISSION-DECISION-v1.0.json` must become `EXACT` and point only to the admitted target identity listed there.

The five `PARTIAL_COMPOSITE` rows must remain exactly:

- `ex-practice-and-compound-001` -> `school-ssp-comma-base` + `school-homogeneous-single-conjunction-punctuation-base`;
- `ex-practice-colon-rule-001` -> `school-colon-bsp-vs-generalizing-word` + `school-direct-speech-adjacent-author-words-system`;
- `ex-practice-comma-multi-rule-001` -> `school-spp-main-subordinate-comma-base` + `school-homogeneous-no-conjunction-punctuation-base`;
- `ex-practice-dash-rules-001` -> `school-dash-subject-predicate-basic-placement` + `school-generalizing-word-basic-colon-dash-position`;
- `ex-practice-junction-001` -> `school-spp-multiple-subordinate-punctuation` + `school-spp-complex-subordinator-comma-boundary`.

Exact weakness attribution remains forbidden for those five.

## VALIDATION / ACCEPTANCE_EVIDENCE

Validator must prove at minimum:

- active rows = 121;
- unique `practice_item_id` = 121;
- represented exception IDs = 88;
- EXACT = 116;
- PARTIAL_COMPOSITE = 5;
- BLOCKED = 0;
- integration-ready = 121;
- live-connected = 0;
- admitted new RU IDs = exactly 12 and exactly the Central Brain list;
- every referenced `ru-*` target exists in the RU-1 canonical registry slice;
- no candidate ref is used as a semantic/mastery target;
- all legacy PR #72 exact `school-*` mappings remain unchanged unless one of the 25 explicit RU-1 resolved rows replaces a blocked row;
- five partial/composite semantic target sets are byte-for-byte/equivalent-set unchanged;
- `school-*` canonical denominator remains 185 / no school identity mutation;
- candidate-015, candidate-053, broad candidate-025 and composite candidate-018 are not silently admitted as RU-1 exact targets;
- no demo/runtime/Tilda/scoring/localStorage files changed;
- deterministic generation/validation passes twice with identical generated hashes if generation is used.

Also run any existing directly relevant Russian semantic/integration validators that can be run without modifying historical branches.

Return:

- baseline main SHA;
- branch;
- commit SHA;
- PR number/URL;
- files changed;
- exact validation commands/results;
- registry SHA256;
- mapping SHA256;
- counts above;
- `RUSSIAN_DEMOS_CHANGED=0`;
- `TILDA_CHANGED=0`;
- `SHARED_PEIS_CONTRACTS_CHANGED=0`;
- `LIVE_CONNECTED=0`.

## STOP_CONDITIONS

STOP and return a concrete blocker instead of improvising if:

- any of the 25 RU-1 row mappings conflicts with the admission decision;
- a 13th new identity appears necessary;
- a new exact mapping requires mutating an existing `school-*` identity;
- source refs needed for one of the 12 admitted identities cannot be recovered from the cited reviewed evidence;
- a partial/composite row would need exact attribution;
- completing the task requires changing shared PEIS architecture or demo/runtime/scoring.

Do not reopen subject semantics. Return the exact conflict to Central Brain.

## FINAL_STATUS

Success only:

`RUSSIAN_RU1_121_MAPPING_READY_FOR_SERVICE_CONNECTION`

Otherwise one exact blocker, for example:

- `BLOCKED_RUSSIAN_RU1_SOURCE_PROVENANCE`
- `BLOCKED_RUSSIAN_RU1_MAPPING_CONFLICT`
- `BLOCKED_RUSSIAN_RU1_REGISTRY_CONTRACT`
- `BLOCKED_RUSSIAN_RU1_UNEXPECTED_SCOPE_EXPANSION`
