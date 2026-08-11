# Eksamio Learning Engine — repository communication protocol

## Goal

Use the GitHub repository as the shared communication layer between ChatGPT review/planning work and Codex implementation work. Durable decisions, tasks, results and reviews belong in the repository, not only in chat.

## Roles

### Planner / reviewer

Creates or updates:

- architecture/status files;
- `tasks/TASK-*.md` task files;
- `reviews/REVIEW-*.md` review files.

Reads:

- Codex result files;
- PR diffs;
- validation/test reports;
- source/provenance artifacts.

### Codex

Reads:

- `AGENTS.md`;
- current status/index;
- the exact task file supplied for the run;
- relevant project/source files.

Creates:

- requested artifacts/code;
- `results/RESULT-*.md` for every task;
- PR for implementation changes that can affect existing behavior.

Codex must not use the chat response as the only durable record.

## Directory contract

`tasks/`
: one task = one file. Contains scope, allowed paths, forbidden changes, required outputs, validation and stop condition.

`results/`
: Codex completion record for the matching task.

`reviews/`
: independent review of the result. Contains `APPROVED`, `CHANGES_REQUIRED`, or `HOLD`.

Architecture/source files may stay at the root of `eksamio-learning-engine/` when they are part of the long-lived specification.

## Naming

Task:
`tasks/TASK-001-russian-skill-graph.md`

Result:
`results/RESULT-001-russian-skill-graph.md`

Review:
`reviews/REVIEW-001-russian-skill-graph.md`

Use the same numeric ID across the three files.

## Task lifecycle

1. Planner creates `TASK-NNN-...md` with `STATUS: READY`.
2. User tells Codex only: `Read eksamio-learning-engine/AGENTS.md and execute TASK-NNN-...md exactly.`
3. Codex performs the task.
4. Codex creates `RESULT-NNN-...md` and, for implementation changes, a PR.
5. User tells ChatGPT: `Codex finished TASK-NNN; review repository result/PR.`
6. Reviewer writes `REVIEW-NNN-...md`.
7. If `APPROVED`, next task may begin.
8. If `CHANGES_REQUIRED`, Codex receives only the review file and corrects the current task; do not start a new dependent task.

## Minimal task header

Every task should include:

- `TASK_ID`
- `STATUS`
- `MODE` (`ADD_ONLY`, `AUDIT_ONLY`, `IMPLEMENTATION`, `MIGRATION`, etc.)
- `SCOPE`
- `ALLOWED_PATHS`
- `FORBIDDEN_CHANGES`
- `INPUTS`
- `REQUIRED_OUTPUTS`
- `VALIDATION`
- `STOP_CONDITION`

## Minimal result header

Every Codex result should include:

- `TASK_ID`
- `STATUS: DONE|PARTIAL|BLOCKED`
- `BRANCH`
- `COMMIT`
- `PR`
- `CREATED_FILES`
- `MODIFIED_FILES`
- `DELETED_FILES`
- `CHECKS_RUN`
- `NEEDS_REVIEW_COUNT`
- `PRODUCTION_FILES_CHANGED: YES|NO`

## Safe implementation rule

For work that can change a published demo, trainer or shared runtime:

- do not work directly on `main`;
- use a dedicated branch/worktree;
- open a PR;
- do not merge until review status is `APPROVED`;
- keep rollback possible;
- unrelated fixes belong in separate tasks.

## Concurrency rule

Do not let ChatGPT/Codex independently edit the same task/result/review file at the same time.

Ownership:

- `TASK-*` — planner/reviewer owns;
- `RESULT-*` — Codex owns;
- `REVIEW-*` — planner/reviewer owns.

This avoids overwrites and ambiguous state.

## Chat becomes a pointer, not the payload

Normal message to Codex should be short:

`Read eksamio-learning-engine/AGENTS.md and execute tasks/TASK-001-russian-skill-graph.md. Do not go beyond the stop condition.`

Normal message to ChatGPT after completion:

`Codex finished TASK-001. Review the repository result and PR.`

All substantial requirements and findings remain in GitHub.
