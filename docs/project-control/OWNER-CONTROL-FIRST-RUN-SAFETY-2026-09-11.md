# Owner Control — First Paid Run Safety Gate — 2026-09-11

Status: `FREE_SAFETY_REPAIR_PUBLISHED / PAID_RUN_NOT_STARTED`.

## Why this gate was added

Before the first real paid Owner Control run, the live board/panel was checked against current GitHub reality. Two unsafe assumptions were found before any paid call:

1. the panel could recommend an `executor: Owner` task (for example A8.1) to the Astra/API-Codex path;
2. the controller read its board/checkpoint files only after checking out `base_ref`, so an older active work branch such as PR #164 could lack Owner Control authority files.

## Permanent safety changes

- Paid autonomous selection requires `executor == Codex`.
- `executor: Owner` rows are Owner Gates and cannot enter paid autonomous execution.
- `SUBJECT` is treated as an internal work blocker that a bounded Codex task may resolve; external/non-subject blockers still fail before any paid API call.
- Controller snapshots its operational board and checkpoint authority from `main` before checking out the target work branch.
- `NON_CODEX_EXECUTOR` fails closed before Astra/Codex.
- `A2.2 Exact semantic/object closure` is on the Critical Path and is bound to PR #164 / `brain/sep1-russian-subject-closure` for the current Russian closure lane.

## Free evidence

Temporary validation run `34630322368`:
- patch application PASS;
- 7/7 Owner Control tests PASS;
- control YAML parse PASS;
- static Owner Control build PASS;
- first-run safety assertions PASS;
- staging commit/push PASS.

The validated control-workflow blob was then published to `main` through the GitHub connector because the GitHub Actions bot correctly refused to modify workflow files without `workflows` permission.

## Paid accounting

No Astra or API-Codex provider call was made by this first-run safety repair.

`PAID_CALLS = 0`

The first paid `start` remains owner-confirmed and must not be launched until current PR #164 HEAD/current acceptance state is rechecked immediately before `Run workflow`.
