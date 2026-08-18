# TASK-003 — Russian Semantic Identity Inventory + Crosswalk

TASK_ID: TASK-003
STATUS: READY
MODE: ADD_ONLY / AUDIT_ONLY / NO_PRODUCTION_INTEGRATION
SCOPE: Build the first machine-readable inventory and crosswalk required for the Russian Unified Semantic Identity Registry without creating guessed canonical identities and without changing existing products.

## Read first

1. `../AGENTS.md`
2. `../00-WORK-STATUS.txt`
3. `../00A-WORK-STATUS-CURRENT-ADDENDUM.txt`
4. `../COMMUNICATION-PROTOCOL.md`
5. `../02-CODEX-BUILD-INDEX.txt`
6. `../272-RUSSIAN-UNIFIED-SEMANTIC-IDENTITY-REGISTRY-CONTRACT-v1.0.txt`
7. `../266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json`
8. `../03-RUSSIAN-SKILL-GRAPH.json`

Then inspect the current semantic-reference layers required below.

## Current semantic authorities

- Current school semantic denominator authority = 185 active `school-*` identities under the 266 authority chain.
- `03-RUSSIAN-SKILL-GRAPH.json` remains the EGE-oriented exam taxonomy and must not be rewritten into the universal registry.
- Existing product/content IDs remain stable source IDs.

## Required source/reference inventory

Audit current semantic references in at least:

- school denominator/current canonical school identity artifacts under the 259-266 authority chain;
- `03-RUSSIAN-SKILL-GRAPH.json`;
- current explanation schemas/maps/routing/tag indexes;
- current exceptions manifest (`118-RUSSIAN-EXCEPTIONS-CURRENT-MANIFEST.json`) and registered exception banks;
- current practice manifest (`119-RUSSIAN-EXCEPTIONS-PRACTICE-CURRENT-CORRECTED-MANIFEST.json`) and practice schema;
- learner-state schema/addendum (`102...`, `120...`);
- error-to-exception handoff spec/map (`113...`, `114...`);
- essay semantic/criteria components where semantic linkage exists (`52-55`, `57`, `79`);
- current Russian trainer semantic/evidence refs;
- EGE/OGE 2026 overlays (`264...`, `265...`).

If a referenced file has been superseded, use the current authority and record the supersession rather than silently treating the old file as current.

## Goal

Produce a factual crosswalk of existing semantic/taxonomy/product identities before admitting any new subject-level canonical identities.

For each inventoried object classify its relationship to canonical semantic meaning as one of:

- CANONICAL_SCHOOL_IDENTITY
- EGE_TAXONOMY_NODE
- SAME_MEANING_AS_EXISTING
- PARENT_OF
- CHILD_OF
- PARTIAL_OVERLAP
- COMPOSITE_OF
- PRODUCT_OBJECT_ONLY
- EXPLANATION_OBJECT_ONLY
- EXCEPTION_OBJECT_ONLY
- PRACTICE_OBJECT_ONLY
- EXAM_ROUTE_ONLY
- LEARNER_STATE_LEGACY_REF
- MISSING_SUBJECT_SEMANTIC_CANDIDATE
- NEEDS_REVIEW

Do not use these labels to invent semantic truth. They are audit classifications.

## Critical duplicate-prevention rule

Before marking anything `MISSING_SUBJECT_SEMANTIC_CANDIDATE`, verify it is not already owned by:

1. an active `school-*` identity;
2. an absorbed/alias school identity;
3. an existing Skill Graph node/subskill with same meaning;
4. another current semantic reference in explanation/exception/practice layers.

Different wording, different exam task, different example or different product does NOT prove a new identity.

## Allowed outputs

Create only ADD-ONLY artifacts:

- `../273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json`
- `../274-RUSSIAN-SEMANTIC-CROSSWALK-DRAFT-v0.1.json`
- `../275-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-VALIDATION.txt`
- `../results/RESULT-003-russian-semantic-identity-inventory-crosswalk.md`

If code is needed solely to validate these ADD-ONLY artifacts, add a narrow validator under `../build/` only if necessary and list it in the result. Do not alter existing builders unless explicitly required and justified.

## Inventory output requirements

`273...` must include at minimum:

- schema/version/date/status;
- authorities used;
- active school identity count observed;
- Skill Graph skill/subskill counts observed;
- semantic-reference source systems inventoried;
- per-object stable source ID;
- source system/object type;
- current/superseded status;
- observed label/meaning;
- current semantic refs;
- audit classification;
- candidate canonical owner when known;
- evidence/provenance refs;
- needs_review reason where applicable.

Do NOT force every object to one canonical owner if evidence is partial.

## Crosswalk output requirements

`274...` is a DRAFT crosswalk, not the final canonical registry.

Each mapping must contain at minimum:

- mapping_id;
- source_system;
- source_object_type;
- source_id;
- target_semantic_id when already canonically known;
- target_candidate_ref when no canonical ID is yet admitted;
- relation;
- evidence_level;
- provenance refs;
- review_status;
- notes for partial/composite mappings.

For `MISSING_SUBJECT_SEMANTIC_CANDIDATE`, do NOT generate the final new semantic_id in this task. Use a stable candidate reference such as `candidate-###` and preserve the source-backed description.

## Validation requirements

Validate and report:

- JSON parse;
- unique inventory object keys;
- unique mapping IDs;
- every `target_semantic_id` resolves to an existing canonical identity when claimed;
- active school identity count matches current authority;
- no existing `school-*` ID is renamed or duplicated;
- all superseded manifests/files are marked as such when encountered;
- all current manifest references point to current authority where detectable;
- count of exact/same-meaning mappings;
- count of parent/child/partial/composite mappings;
- count of product-only objects;
- count of missing-subject-semantic candidates;
- count of needs_review;
- no production files changed.

## Important expected finding

The 185 school denominator is intentionally narrower than the full Russian-language subject. Therefore some source-backed `MISSING_SUBJECT_SEMANTIC_CANDIDATE` records are expected in domains such as orthoepy, lexical/paronym/phraseology, text/style, expressive means, essay and possibly morphology/syntax.

Do not assume candidate counts in advance.

## Forbidden

Do NOT:

- change `03-RUSSIAN-SKILL-GRAPH.json`;
- change any of the 185 canonical `school-*` IDs;
- create final new semantic IDs;
- alter demos/trainers/T123/HTML/CSS/JS/scoring/localStorage;
- migrate learner state;
- integrate Tutor Core;
- integrate Homework;
- modify Tilda;
- invent prerequisites;
- treat exam route/task numbers as canonical knowledge identities;
- resolve source conflicts by guess.

## Required result file

Create `../results/RESULT-003-russian-semantic-identity-inventory-crosswalk.md` containing at least:

- `TASK_ID: TASK-003`
- `STATUS: DONE|PARTIAL|BLOCKED`
- `CREATED_FILES`
- `MODIFIED_FILES`
- `DELETED_FILES`
- `CHECKS_RUN`
- active school identity count
- Skill Graph skill/subskill counts
- inventoried object count by source system
- mapping counts by relation/classification
- `MISSING_SUBJECT_SEMANTIC_CANDIDATE_COUNT`
- `NEEDS_REVIEW_COUNT`
- supersession inconsistencies found
- contradictions found
- `PRODUCTION_FILES_CHANGED: YES|NO`
- branch/commit/PR

## Stop condition

STOP after inventory, draft crosswalk, validation and result are complete.

Do NOT create the final Unified Semantic Identity Registry in this task.
Do NOT begin learner-state migration or Tutor integration.
