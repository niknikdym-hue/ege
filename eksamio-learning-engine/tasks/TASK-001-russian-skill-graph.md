# TASK-001 — Russian Skill Graph

TASK_ID: TASK-001
STATUS: READY
MODE: ADD_ONLY / AUDIT_ONLY
SCOPE: Build the factual Russian EGE Skill Graph from the existing trainer and all Russian demo/source materials without changing existing products.

## Read first

1. `../AGENTS.md`
2. `../00-WORK-STATUS.txt`
3. `../COMMUNICATION-PROTOCOL.md`
4. `../02-CODEX-BUILD-INDEX.txt`
5. `../02A-CODEX-RUSSIAN-SKILL-GRAPH-TASK.txt`

The detailed technical specification is `../02A-CODEX-RUSSIAN-SKILL-GRAPH-TASK.txt` and is authoritative for this task.

## Important context

The current Russian trainer was previously built by Codex as a synthesis/result of work over all Russian EGE demos. Therefore do not derive the Skill Graph from one current demo only. Audit the actual trainer plus all relevant local/repository Russian demo/source materials.

## Allowed repository outputs

Create only:

- `../03-RUSSIAN-SKILL-GRAPH.json`
- `../03A-RUSSIAN-SKILL-GRAPH-PROVENANCE.txt`
- `../03B-RUSSIAN-SKILL-GRAPH-VALIDATION.txt`
- `../results/RESULT-001-russian-skill-graph.md`

If an audit note is required by the detailed spec, include it in provenance/validation/result rather than modifying the affected existing file.

## Forbidden

Do not modify/delete/rename/move any existing demo, trainer, answer, criteria, HTML, CSS, JS, T123, URL, localStorage or other production/source file.

Do not implement demo->trainer handoff, mastery, recommendation, spaced repetition, server sync or AI.

Do not fix unrelated defects.

Do not invent unverified data. Use `needs_review` / `null` as specified.

## Required result file

Create `../results/RESULT-001-russian-skill-graph.md` containing at least:

- `TASK_ID: TASK-001`
- `STATUS: DONE|PARTIAL|BLOCKED`
- `CREATED_FILES`
- `MODIFIED_FILES`
- `DELETED_FILES`
- `CHECKS_RUN`
- count of skills/subskills
- demo/task coverage
- trainer coverage
- `NEEDS_REVIEW_COUNT`
- contradictions found
- `PRODUCTION_FILES_CHANGED: YES|NO`
- branch/commit/PR if applicable

## Stop condition

STOP after producing and validating the three Skill Graph artifacts and the RESULT file.

Do not begin TASK-002 or any implementation work.
