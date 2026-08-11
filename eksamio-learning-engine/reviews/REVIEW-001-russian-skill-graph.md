# REVIEW-001 — Russian Skill Graph

TASK_ID: TASK-001
STATUS: CHANGES_REQUIRED
REVIEW_DATE: 2026-08-11
SCOPE: independent repository review of Skill Graph artifacts

## What passed

- Required artifacts exist: `03-RUSSIAN-SKILL-GRAPH.json`, provenance, validation, RESULT-001.
- Graph contract is structurally coherent: 12 top-level skills, 89 child subskills, 101 total nodes.
- Current task coverage is reported as 27/27; trainer coverage 174/174.
- `difficulty` remains null for all trainer items.
- No prerequisite edges were invented.
- 12 conflicts/gaps are explicitly recorded rather than silently repaired.
- No runtime handoff/mastery/recommendation/AI implementation was started.
- ADD-ONLY discipline is reported and production/source scope hash is unchanged.

## Blocking review issue before approval

### 1. Current trainer source is not present in GitHub

The provenance explicitly states that the current trainer and builder used as Priority-1 evidence were read from the local `exam-platform-tilda` workspace and are not present in the audited GitHub commit.

This prevents independent repository-side verification of the 174 trainer-item mappings, which conflicts with the project communication rule that GitHub is the durable shared source of truth between ChatGPT and Codex.

Do NOT modify or relocate the production trainer.

Create an ADD-ONLY, read-only audit snapshot under:

`eksamio-learning-engine/sources/russian-current-trainer-snapshot/`

The snapshot must contain the exact source artifacts actually used for TASK-001, or a lossless copy sufficient to independently reproduce/verify all 174 trainer links. At minimum include:

- `BANK-MANIFEST.json`
- `ege-russkiy-trenazher-SOURCE-AUDIT.txt`
- `OFFICIAL-CORRECTIONS.json`
- `SOURCE-CORRECTIONS.json`
- `ORTHOEPIC-TRAINER-BANK.json`
- the exact builder script used
- the T123/data artifacts that contain the 174 trainer items and their stable `trainer_item_id`, prompts/content metadata and task associations

Add `SNAPSHOT-MANIFEST.json` with:

- original local relative path
- snapshot relative path
- SHA-256
- byte size
- purpose
- source status

Do not include secrets, tokens or machine-specific absolute paths.

After snapshot creation, rerun the graph validation against the repository snapshot and record that 174/174 trainer links can be verified from repository-visible sources.

### 2. `source_status` wording is inaccurate

`03-RUSSIAN-SKILL-GRAPH.json` currently says:

`"source_status": "repository-audited"`

but the highest-priority trainer source was local-only during construction.

Until repository snapshot verification is complete, change this value to an accurate state such as:

`"repository-and-local-audited"`

After successful repository snapshot revalidation it may become `repository-audited` if that is factually true.

### 3. Result commit metadata is inaccurate

`RESULT-001-russian-skill-graph.md` names commit `42926f...`, but the RESULT-001 file itself was committed later (`58ef84a...`). Record artifact commits accurately, or use an explicit `ARTIFACT_COMMITS` list/range rather than one misleading commit field.

This is bookkeeping, not a content defect.

## Non-blocking observations

- Task 25 remains a mixed historical/current pool. Keeping it `exact` is acceptable only with the explicit phraseologism-subpool guard already documented; implementation must not route into the historical synonym item.
- Tasks 8 and 22 may be `exact` only after future position-level Attempt identifiers exist, as already stated.
- Task 27 correctly remains unavailable for automatic handoff until a separately reviewed criterion-level diagnosis exists.
- The 12 `needs_review` items should not be fixed as part of this review unless a later explicit task authorizes them.

## Allowed corrections

ADD-ONLY source snapshot plus minimal metadata corrections to Learning Engine artifacts only.

DO NOT modify production demo/trainer/source files.
DO NOT start handoff, mastery, storage, recommendation, UX or AI implementation.

## Approval condition

TASK-001 becomes eligible for APPROVED when:

1. repository-visible trainer snapshot exists;
2. snapshot hashes are recorded;
3. 174/174 mappings are revalidated against that snapshot;
4. `source_status` accurately reflects source visibility;
5. RESULT commit metadata is corrected.
