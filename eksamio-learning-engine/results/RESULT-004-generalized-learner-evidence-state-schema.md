# RESULT-004 — Generalized Learner Evidence + Learner State Schema

TASK_ID: TASK-004

STATUS: DONE

MODE: ADD_ONLY / ARCHITECTURE_MATERIALIZATION / NO_PRODUCTION_INTEGRATION

BRANCH: `codex/task-004-generalized-learner-evidence-state-schema`

COMMIT: `9acf1d98281c09416f1a2b1d7dd3c670b65713c5` (published review-fix validated artifact set)

PR: [#33](https://github.com/niknikdym-hue/ege/pull/33)

## CREATED_FILES

- `277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json`
- `278-EKSAMIO-LEARNER-STATE-MATERIALIZED-VIEW-SCHEMA-v0.1.json`
- `279-EKSAMIO-LEGACY-LEARNER-STATE-ADAPTER-MAP-v0.1.json`
- `280-EKSAMIO-LEARNER-EVIDENCE-STATE-VALIDATION.txt`
- `build/validate_generalized_learner_evidence_state.py`
- `results/RESULT-004-generalized-learner-evidence-state-schema.md`

## MODIFIED_FILES

- None.

## DELETED_FILES

- None.

## SCHEMA_VERSIONS

- Event schema: JSON Schema Draft 2020-12, `0.1.0`.
- Materialized learner-state schema: JSON Schema Draft 2020-12, `0.1.0`.
- Legacy adapter map: `0.1.0`.

## EVENT CONTRACT MATERIALIZED

- Append-only immutable evidence with linked `CORRECTION` / `RETRACTION` events.
- Required stable `event_id`; optional purpose-distinct `idempotency_key`, required for legacy imports.
- Stable `learner_profile_id` plus separate anonymous/user identity refs; email is not a learner ID field.
- Subject-agnostic semantic targets with `PRIMARY`, `SECONDARY`, and `PREREQUISITE_OBSERVED` roles.
- Semantic registry/mapping version and source object/content/item version traceability.
- Required product/source type, session, client/server timestamps, result, response mode, assistance, evaluator/trust, provenance, transfer and retention context.
- Full required assistance and evaluator enums from TASK-004.
- AI evaluator is restricted to `AI_INTERPRETED_LOW`, uncertainty/review metadata and educational/non-official truth; independently validated AI output uses `HYBRID_VALIDATED`.
- Open-response rubric evidence and per-dimension evidence refs, including an authorized non-AI reviewed/official path.
- Structured error observations with exact/partial/broad/unknown precision.
- Learner self-confidence as a separate optional raw signal.
- Versioned `subject_extension` envelope for Russian/Mathematics/Physics-specific payloads.
- Recursive ingestion invariant forbidding client-authored final `effective_weight`, `mastery_weight`, contribution percentages or canonical mastery estimates.

## MATERIALIZED STATE CONTRACT

- Keyed by `learner_profile_id x semantic_id` with subject and semantic registry version.
- Inference-output mastery estimate/band/status without freezing a universal taxonomy or coefficient.
- System confidence/uncertainty remains distinct from learner self-confidence.
- Independent, assisted, recent, transfer and retention evidence summaries remain separate.
- Last independent verification, last assisted attempt, last retention check and optional retention due hooks.
- Prerequisite/readiness hooks without inventing edges or an algorithm.
- Structured error fingerprint and goal/exam/course overlay refs.
- Mandatory `inference_version`, `computed_at`, evidence watermark/reference and `state_revision`.
- Explicit recompute/backfill metadata for inference/mapping version changes and corrections/retractions.

## ADAPTER_SOURCES_INVENTORIED

1. `102-RUSSIAN-EXCEPTIONS-LEARNER-STATE-SCHEMA.json` — exact attempt events plus conservative aggregate fallback.
2. `120-RUSSIAN-EXCEPTIONS-LEARNER-STATE-v1.1-ADDENDUM.json` — `processed_event_ids` and `state_revision` preservation.
3. `113-RUSSIAN-ERROR-TO-EXCEPTION-HANDOFF-SPEC.txt` / `114-RUSSIAN-ERROR-EXCEPTION-HANDOFF-MAP-v0.1.json` — exact-vs-broad error boundary.
4. Current EGE Russian trainer progress namespace `eksamio:ege-russian-trainer:progress:v1`.
5. Current EGE Russian trainer session namespace `eksamio:ege-russian-trainer:session:v1`.
6. Course/thematic product-state contract for `new | learning | review | mastered` labels, design-only until a concrete repository-visible namespace/schema is declared.

ADAPTER_COUNT: 6

## FIXTURES / EXAMPLES

EVENT_FIXTURE_COUNT: 13

- historical Russian demo with exam year/route metadata;
- full subject-trainer unassisted attempt;
- thematic-trainer attempt;
- Tutor-assisted attempt;
- separate unassisted verification after Tutor help;
- Homework event;
- essay/open-response rubric event with AI trust/uncertainty/non-official boundary;
- authorized human-reviewed open-response event with reviewed/official truth status;
- legacy Exceptions exact-state import;
- course/local product-state aggregate import with `mastered` kept product-local;
- delayed retention event;
- append-only correction/retraction event;
- Mathematics structural placeholder using production-valid unresolved mapping (`PARTIAL` + `needs_review`), with fixture-only provenance in `subject_extension` and no invented subject truth or new core fields.

STATE_FIXTURE_COUNT: 2

- Russian empty/recomputable semantic state;
- Mathematics structural placeholder state.

NEGATIVE_FIXTURE_COUNT: 12

- invalid semantic role;
- test-only `PLACEHOLDER_FIXTURE` mapping resolution;
- test-only `fixture_only` mapping review status;
- client-authored `effective_weight`;
- missing source content version;
- correction without supersession link;
- AI evaluation without uncertainty;
- AI evaluator with non-AI/high trust class;
- AI open response claiming official truth;
- legacy import without idempotency key;
- state without `inference_version`;
- state without evidence watermark/reference.

## CHECKS_RUN

- `python3 build/validate_generalized_learner_evidence_state.py` — PASS: schemas `0.1.0`; 13 event fixtures; 2 state fixtures; 12 negative fixtures rejected; 6 adapters; 0 production changes.
- `python3 -m py_compile build/validate_generalized_learner_evidence_state.py` — PASS.
- `jq empty 277...json 278...json 279...json` — PASS.
- `python3 -m unittest discover -s build/tests -v` — PASS: 29/29 tests.
- Isolated `/tmp` current Exceptions builds — PASS: 127 exceptions, 80 practice cards, 127 launch-priority rows, 73 runtime exceptions, 80 runtime practice items, 3 runtime chunks.
- Isolated `/tmp` `standalone-exceptions-trainer/tests/test-core.js` — PASS: runtime/evaluator/state/selector/browser-core and storage-namespace isolation tests.
- Direct `rex-state.js` compatibility smoke — PASS: replay idempotency, no false stabilized/mastery state, corrupt source state preserved.
- `git diff --check` — PASS.
- Forbidden-path diff guard in TASK-004 validator — PASS.

VALIDATOR_RESULT: PASS

CROSS_SUBJECT_STRUCTURAL_VALIDATION: PASS

No Russian-specific field such as `exception_id` is required by the universal event or state core. The Russian legacy fixture preserves it only inside the versioned `subject_extension.subject_payload` envelope. The Mathematics fixture is structural, uses the production-valid unresolved mapping `PARTIAL` + `needs_review`, and carries fixture-only marking only in provenance / `subject_extension`; no Mathematics subject truth was invented.

## PR_33_REVIEW_REMEDIATION

- Removed `PLACEHOLDER_FIXTURE` and `fixture_only` from canonical semantic mapping enums.
- Enforced `AI_EVALUATOR` → `AI_INTERPRETED_LOW` + uncertainty/review metadata + `EDUCATIONAL_NON_OFFICIAL` in both evaluator and open-response truth fields.
- Generalized nested open-response truth status for authorized deterministic/human reviewed paths.
- Added positive human-reviewed open-response coverage and four new negative boundary fixtures.
- Rebased the PR branch onto current `main` at `36298dfc7df0c4194b500fd82c4078c1e2ee26d4` before the review-fix validation run.

## LEGACY_COMPATIBILITY_FINDINGS

- Exact 102 attempt history can become exact generalized evidence; aggregate counters/statuses cannot be expanded into fabricated historical attempts.
- 120 replay suppression survives through a durable import ledger keyed by namespace, schema version, record identity/revision and source event ID where present.
- 114 may emit exact structured errors only when exact word/position/option evidence and an enabled current target exist.
- Whole-task failure, task number, generic wrong status or total score does not become an exact exception error.
- Current trainer progress is aggregate product state. Its UI-computed `mastered` counter is never mapped to canonical mastery.
- Current product/localStorage state continues unchanged; TASK-004 defines future read-only adaptation only.

## UNRESOLVED / NEEDS_REVIEW

NEEDS_REVIEW_COUNT: 2

1. `114` still declares superseded Exceptions manifest `83`; current authority is `118`. The adapter preserves both provenance refs and resolves enabled targets against `118`, without rewriting `114`.
2. No concrete course/thematic runtime namespace or state schema is repository-visible at TASK-004 time. Its adapter therefore remains design-only until the product owner declares a stable namespace, schema version and record revision identity.

The 55 TASK-003 semantic candidates remain draft candidate refs. TASK-004 does not canonicalize them or create final `ru-*` IDs.

## CONTRADICTIONS_FOUND

- No new contradiction beyond the known `114` manifest supersession inconsistency.
- The current trainer's learner-facing `mastered` counter is a local UI aggregate and is intentionally not treated as canonical mastery, consistent with contract 276.

PRODUCTION_FILES_CHANGED: NO

DEMOS_CHANGED: NO

CURRENT_TRAINERS_CHANGED: NO

TILDA_CHANGED: NO

SCORING_CHANGED: NO

LOCALSTORAGE_CHANGED: NO

TUTOR_OR_HOMEWORK_PRODUCTION_INTEGRATION_STARTED: NO

FINAL_MASTERY_COEFFICIENTS_DEFINED: NO

UNIVERSAL_FORGETTING_CURVE_DEFINED: NO

PREREQUISITE_EDGES_CREATED: NO

FINAL_NEW_RUSSIAN_SEMANTIC_IDS_CREATED: NO

STOP: Evidence schema, materialized-state schema, legacy adapter map, validation and RESULT-004 only. Final mastery/readiness/retention/NBA algorithm and all production integration remain out of scope.
