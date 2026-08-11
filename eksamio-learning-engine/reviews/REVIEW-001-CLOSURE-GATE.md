# REVIEW-001 closure gate — Russian Skill Graph

TASK_ID: TASK-001  
RELATED_REVIEW: `reviews/REVIEW-001-russian-skill-graph.md`  
STATUS: HOLD  
MODE: INDEPENDENT LOCAL VALIDATION / NO CODEX REQUIRED

## Why this closure file exists

The original independent review was `CHANGES_REQUIRED` mainly because the current 174-card trainer used as the highest-priority factual product source was local-only at graph creation time and was not independently repository-visible.

The user later uploaded the trainer snapshot into:

`eksamio-learning-engine/russkiy-knigi/ege-russkiy-trenazher/`

That removes the original source-visibility blocker for an independent check, but approval must still be based on an actual cross-validation run rather than on Codex's prior PASS statements.

## Independent validator

Run locally from `eksamio-learning-engine/`:

`python3 build/validate_russian_skill_graph_against_trainer.py`

Or run the full current checkpoint gate:

`python3 build/run_russian_learning_engine_validation_current_v3.py`

Expected dedicated report:

`audits/RUSSIAN-SKILL-GRAPH-INDEPENDENT-VALIDATION.txt`

## Approval criteria

TASK-001 may move to `APPROVED` when the independent validator returns PASS and the report confirms, at minimum:

1. repository-visible trainer PREVIEW parses successfully;
2. trainer card total matches current BANK-MANIFEST;
3. per-task counts match BANK-MANIFEST;
4. every current trainer card ID is represented in the Skill Graph source mapping/reference set;
5. no duplicate Skill Graph skill IDs;
6. all difficulty values remain null unless a later measured-data task explicitly changes this policy;
7. prerequisites remain empty in this initial graph unless a later evidence-based task explicitly adds them;
8. the known historical task-25 contextual-synonym anomaly remains visible as review/legacy risk rather than silently treated as current phraseology;
9. no production trainer file is modified by the validation.

## Warnings that do not automatically block approval

The validator may emit review warnings rather than FAIL for:

- graph-like item IDs that are historical/provenance references not present in the current snapshot, if they are explained and do not create orphan current items;
- the known source anomaly where historical task-25 contextual synonym data has imperfect `legacyFormat` metadata in the trainer source;
- top-level/child counts changing only after an explicitly reviewed graph-extension task.

Warnings must still be read before approval.

## Original metadata follow-ups

These are documentation quality issues but are not, by themselves, reasons to reject an independently validated graph:

- `RESULT-001-russian-skill-graph.md` recorded an artifact commit that preceded the RESULT file's own commit;
- historical provenance wording reflected the graph-creation moment when the top-priority trainer source was local-only;
- uploaded repository snapshot path differs from the original local `tilda-ready/pages/...` source path.

After independent PASS, update/append provenance notes so the current repository-visible snapshot relationship is explicit. Do not rewrite historical facts to pretend the source was repository-visible earlier than it was.

## Runtime boundary

`APPROVED` for TASK-001 means:

- graph is accepted as the durable data/content foundation;
- data-contract/routing/content work may rely on it.

It does NOT independently authorize:

- modifying the current EGE trainer;
- Tilda integration;
- AI layer;
- guessed prerequisites/difficulty;
- automatic exact learner diagnosis where item result precision is insufficient.

Those remain controlled by their separate gates.

## Current decision

TASK-001: HOLD PENDING LOCAL INDEPENDENT PASS  
CODEX: NOT REQUIRED  
CURRENT TRAINER: UNCHANGED
