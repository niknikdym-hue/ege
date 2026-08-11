# Eksamio Learning Engine — Codex instructions

These instructions apply to the entire `eksamio-learning-engine/` directory tree.

## Source of truth

The GitHub repository is the durable source of truth for this direction. Do not rely on memory from prior chats when repository files provide current instructions.

Before every task in this direction, read in this order:

1. `00-WORK-STATUS.txt`
2. `COMMUNICATION-PROTOCOL.md`
3. `02-CODEX-BUILD-INDEX.txt`
4. the exact task file named by the user in `tasks/` or another explicitly named task file in this directory
5. any source/provenance files referenced by that task

If instructions conflict, the more specific current task wins, but safety constraints and explicit NO-DESTRUCTIVE/ADD-ONLY rules must never be relaxed implicitly.

## Safety

- Never modify existing Eksamio demo/trainer production files unless the current task explicitly authorizes exact paths.
- Never delete, rename, move, or refactor existing files as a side effect.
- Never silently fix unrelated problems discovered during an audit.
- Record discovered conflicts/problems in the task result or validation report.
- Unknown or unverified facts must be represented as `null`, `needs_review`, `NOT_CONFIRMED`, or another schema value explicitly allowed by the task. Do not guess.
- Official exam facts, answers, criteria, task numbering and scoring are source-of-truth data and must not be synthesized by AI.
- Difficulty must remain `null` unless supported by validated data or explicitly defined by a reviewed algorithm.
- Preserve backward compatibility unless the task explicitly describes and tests a migration.

## Change workflow

For implementation work that can affect existing behavior:

1. Work on a dedicated branch/worktree.
2. Keep the change limited to the current task.
3. Run the checks required by the task and applicable project tests.
4. Produce a result report in `results/`.
5. Open a PR rather than merging directly to `main`.
6. Wait for review before further implementation that depends on the change.

For documentation-only ADD-ONLY tasks, direct creation of new files is allowed if the task explicitly permits it.

## Result contract

Every completed task must produce a durable result artifact in the repository. Do not make the chat response the only record of work.

The result must contain at least:

- task ID;
- status: `DONE`, `PARTIAL`, or `BLOCKED`;
- files created;
- files modified;
- files deleted;
- tests/checks run and outcomes;
- unresolved `needs_review` items;
- contradictions found;
- exact branch/commit/PR when applicable;
- explicit confirmation whether existing production files were changed.

## Review contract

If a review file exists for the task in `reviews/`, read it before continuing.

Statuses:

- `APPROVED` — task may be treated as accepted.
- `CHANGES_REQUIRED` — make only the requested corrections, preferably in the same task branch/PR.
- `HOLD` — do not continue dependent implementation.

Do not infer approval from silence.

## Product rule

The base Eksamio learning loop remains free:

`diagnose -> find weakness -> practice -> verify -> retain -> reassess`

Premium features may add deep personalized computation/AI but must not be implemented by degrading or paywalling the base loop unless a future explicit product decision changes this rule.
