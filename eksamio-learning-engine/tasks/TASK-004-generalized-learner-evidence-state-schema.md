# TASK-004 — Generalized Learner Evidence + Learner State Schema

TASK_ID: TASK-004
STATUS: READY
MODE: ADD_ONLY / ARCHITECTURE_MATERIALIZATION / NO_PRODUCTION_INTEGRATION
SCOPE: Materialize the first machine-readable subject-agnostic learner evidence/event and learner-state contracts plus explicit legacy adapters, without changing current products or implementing the final mastery algorithm.

## Read first

1. `../AGENTS.md`
2. `../00-WORK-STATUS.txt`
3. `../00A-WORK-STATUS-CURRENT-ADDENDUM.txt`
4. `../COMMUNICATION-PROTOCOL.md`
5. `../02-CODEX-BUILD-INDEX.txt`
6. `../267-EKSAMIO-PEIS-PRODUCT-ARCHITECTURE-DECISIONS-v0.1.txt`
7. `../271-EKSAMIO-AI-TUTOR-CORE-CONTRACT-v1.0.txt`
8. `../272-RUSSIAN-UNIFIED-SEMANTIC-IDENTITY-REGISTRY-CONTRACT-v1.0.txt`
9. `../276-EKSAMIO-LEARNER-EVIDENCE-STATE-CONTRACT-v1.0.txt`
10. `../273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json`
11. `../274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json`
12. `../275-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-VALIDATION.txt`
13. `../results/RESULT-003-russian-semantic-identity-inventory-crosswalk.md`
14. `../102-RUSSIAN-EXCEPTIONS-LEARNER-STATE-SCHEMA.json`
15. `../120-RUSSIAN-EXCEPTIONS-LEARNER-STATE-v1.1-ADDENDUM.json`
16. `../114-RUSSIAN-ERROR-EXCEPTION-HANDOFF-MAP-v0.1.json`

Then inspect any current `103...`, `104...`, `113...` learner-state/handoff validation artifacts that exist and are still applicable, and inspect current Russian course/thematic-trainer/localStorage progress contracts where repository-visible.

If a referenced file is superseded, use the current authority and record the supersession instead of silently treating the old file as current.

## Goal

Create a subject-agnostic machine-readable contract for:

1. append-only learner evidence events;
2. recomputable learner semantic state/materialized view;
3. backward-compatible adapters from current Russian product-local learner state;
4. validator coverage proving the schemas obey `276`.

The result must work for Russian first and be reusable by Mathematics, Physics and future subjects without changing the core shape.

## Core invariants

- Evidence is observed; mastery is inferred.
- Accepted raw evidence is immutable.
- Corrections/retractions are new linked events, never in-place edits.
- Product/UI state is not canonical mastery.
- Tutor-assisted success is not independent mastery evidence.
- Historical demo year/task route is metadata, not semantic identity.
- Every canonical semantic-state record declares inference version and evidence watermark/reference.
- Clients do not author final `effective_weight` / mastery coefficients.
- AI may contribute lower-trust interpreted evidence but may not directly write canonical mastery.
- Existing Russian state/history must be adaptable without double import or destructive migration.

## Allowed outputs

Create only ADD-ONLY artifacts:

- `../277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json`
- `../278-EKSAMIO-LEARNER-STATE-MATERIALIZED-VIEW-SCHEMA-v0.1.json`
- `../279-EKSAMIO-LEGACY-LEARNER-STATE-ADAPTER-MAP-v0.1.json`
- `../280-EKSAMIO-LEARNER-EVIDENCE-STATE-VALIDATION.txt`
- `../results/RESULT-004-generalized-learner-evidence-state-schema.md`

If code is needed solely for validation, add one narrow validator under `../build/` and corresponding tests only if useful. Do not modify existing production builders or product runtime.

## 277 — Evidence event schema requirements

Use a real machine-readable JSON Schema or an equally strict machine-validatable JSON contract.

The event model must support at minimum:

- `event_id`;
- optional distinct `idempotency_key`;
- schema version;
- `learner_profile_id`;
- anonymous/user identity references without using email as stable learner ID;
- `subject_id`;
- `semantic_targets[]`;
- source object type / ID / content version;
- product/source type;
- `session_id`;
- client occurrence timestamp;
- server receive timestamp;
- optional server sequence/watermark;
- attempt/result/correctness/score fields where applicable;
- response mode;
- assistance level;
- evaluator type/version/trust class;
- source/provenance refs;
- semantic registry / mapping version;
- transfer context;
- retention context;
- error/misconception observations;
- latency where valid;
- learner self-confidence as a separate optional signal, never system mastery confidence;
- versioned subject extension envelope.

### Semantic target roles

Support at least:
- `PRIMARY`;
- `SECONDARY`;
- `PREREQUISITE_OBSERVED`.

A multi-semantic item must not require arbitrary client-written mastery shares.

### Assistance enum

Support at least:
- `UNASSISTED`;
- `MICRO_HINT`;
- `GUIDED_HINT`;
- `SOCRATIC_GUIDANCE`;
- `RULE_EXPLANATION`;
- `PARTIAL_WORKED`;
- `WORKED_EXAMPLE`;
- `SOLUTION_EXPOSED`.

### Evaluator enum

Support at least:
- `DETERMINISTIC_VALIDATOR`;
- `OFFICIAL_KEY_OR_RULE`;
- `HUMAN_REVIEW`;
- `AI_EVALUATOR`;
- `HYBRID_VALIDATED`.

AI evaluation must expose uncertainty/review/trust metadata and must not imply official exam truth.

### Source/product types

Support at least:
- demo;
- subject trainer;
- thematic trainer;
- EGE/OGE trainer;
- Homework;
- Tutor;
- diagnostic;
- essay/open response;
- course module;
- retention review;
- imported legacy state.

### Append-only correction model

Represent correction/retraction through new events using fields equivalent to:
- `supersedes_event_id`;
- `retracts_event_id`;
- correction reason;
- correction actor/evaluator/version.

Do not define an API that mutates an accepted historical event.

### Explicitly forbidden event field semantics

The canonical client event must not contain a client-authored final mastery/evidence weight such as:
- `effective_weight`;
- `mastery_weight`;
- arbitrary final semantic contribution percentages.

Raw features are allowed; derived weight belongs to inference.

## Required event examples / fixtures

Schema validation must exercise representative examples for:

1. historical Russian demo event with exam year/route metadata and stable semantic target;
2. full subject-trainer unassisted attempt;
3. thematic-trainer attempt;
4. Tutor-assisted attempt;
5. separate unassisted verification after Tutor help;
6. Homework event;
7. essay/open-response rubric event with evaluator trust/uncertainty;
8. legacy Exceptions-state import/adaptation event;
9. course/local product-state adapter event;
10. delayed retention event;
11. correction/retraction event.

Fixtures may live inside the validator/tests or a clearly named ADD-ONLY fixture file only if necessary.

## 278 — Materialized learner-state schema requirements

Per `learner_profile_id x semantic_id`, support fields equivalent to:

- learner/profile identity;
- subject;
- semantic identity + registry version;
- mastery estimate/band/status as inference output;
- system confidence/uncertainty distinct from learner self-confidence;
- independent evidence summary;
- assisted evidence summary;
- recent evidence window/summary;
- last independent verification;
- last assisted attempt;
- transfer evidence summary;
- retention evidence summary;
- last retention check;
- retention due where scheduled;
- prerequisite/readiness hooks;
- structured error/misconception fingerprint;
- goal/exam overlay refs;
- `inference_version`;
- `computed_at`;
- evidence watermark/reference;
- state revision.

Do NOT freeze a universal mastery algorithm or final numeric coefficients in TASK-004.

The state schema must make recomputation/backfill possible when inference_version changes.

## 279 — Legacy adapter requirements

Inventory and define adapters for current Russian learner-state/product-state sources without rewriting them.

At minimum include:

### `102` Exceptions learner state
- preserve `exception_id` history and local statuses;
- map exact attempts/events to generalized evidence where data is sufficiently precise;
- map aggregate-only fields conservatively when exact event history does not exist;
- preserve import provenance/trust.

### `120` idempotency addendum
- preserve processed-event semantics;
- prevent duplicate import/application;
- preserve state revision semantics where useful.

### `114` exact error handoff
- exact word/position/option evidence may feed structured error/misconception evidence;
- whole-task failure must not become an exact exception error;
- record known stale manifest reference `83` vs current authority `118` without silently rewriting `114` inside this task.

### Current course/thematic product state
Where current repository-visible product state uses labels such as:
- `new`;
- `learning`;
- `review`;
- `mastered`;

map them as local/product state unless independent evidence proves more.

`mastered` MUST NOT be automatically converted to canonical mastery solely from the string value.

### localStorage/backward compatibility
- no production localStorage migration;
- define future import/adaptation policy only;
- preserve source namespace/schema version;
- prevent double import;
- allow current UI state to continue functioning during transition.

## Cross-subject requirement

The core event/state schemas must contain no required Russian-specific fields such as `exception_id`.

Russian-specific data belongs in an adapter or versioned `subject_payload` extension.

The validator must demonstrate that the core can represent at least one non-Russian placeholder example structurally without adding new core fields. Do not invent subject truth; a schema-level Mathematics/Physics structural fixture is enough.

## Validation requirements

Validate and report at minimum:

- JSON parse;
- JSON Schema validity or equivalent strict structural validation;
- event ID/idempotency requirements;
- semantic target role enum;
- assistance enum;
- evaluator/trust enum;
- product/source type enum;
- semantic registry/mapping version present where semantic targets exist;
- source object/content version traceability;
- no client-authored final effective/mastery weight;
- correction/retraction model is append-only;
- open-response/rubric evidence includes evaluator provenance/trust/uncertainty boundary;
- materialized state requires `inference_version`;
- materialized state requires evidence watermark/reference;
- system confidence remains distinct from learner self-confidence;
- legacy import prevents duplicate application;
- `mastered` product label is not mapped directly to canonical mastery;
- 102/120 compatibility is represented;
- 114 exact-vs-broad handoff boundary is represented;
- Russian-specific adapter data is not required by universal core;
- no production/demo/trainer/Tilda/runtime/scoring/localStorage files changed.

## Known current semantic input

TASK-003 is merged and provides:
- 185 active school semantic identities;
- 101 current EGE Skill Graph nodes;
- 983 inventoried semantic/product objects;
- 1429 draft mappings;
- 55 distinct missing-subject semantic candidates;
- no final new `ru-*` IDs.

TASK-004 must not canonicalize those 55 candidates. It may reference current semantic/candidate mapping versions only as architecture input.

## Forbidden

Do NOT:

- change demos or current trainers;
- change T123/HTML/CSS/JS/scoring/localStorage;
- migrate production learner data;
- implement Tutor or Homework production integration;
- choose final mastery coefficients;
- declare a universal forgetting curve;
- invent prerequisite edges;
- create final new Russian semantic IDs;
- use email as learner ID;
- let AI directly write canonical mastery;
- add vector DB / Kafka / Kubernetes or unrelated infrastructure;
- rewrite 102/120/114 in place;
- resolve source conflicts by guess.

## Required result file

Create `../results/RESULT-004-generalized-learner-evidence-state-schema.md` containing at least:

- `TASK_ID: TASK-004`;
- `STATUS: DONE|PARTIAL|BLOCKED`;
- `CREATED_FILES`;
- `MODIFIED_FILES`;
- `DELETED_FILES`;
- `CHECKS_RUN`;
- event schema/version;
- state schema/version;
- adapter sources inventoried;
- fixture/example count and categories;
- validator result;
- unresolved/needs-review findings;
- legacy compatibility findings;
- cross-subject structural validation result;
- `PRODUCTION_FILES_CHANGED: YES|NO`;
- branch/commit/PR.

## Stop condition

STOP after evidence schema, materialized-state schema, legacy adapter map, validation and RESULT-004 are complete.

Do NOT begin the final mastery/readiness/retention/NBA algorithm in TASK-004.
Do NOT integrate runtime storage, Tutor, Homework or production products.
