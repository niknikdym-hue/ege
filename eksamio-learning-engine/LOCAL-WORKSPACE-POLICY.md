# Eksamio — Local Workspace Policy

**Status:** OWNER-MANDATED / ACTIVE  
**Date:** 2026-08-23

## Owner rule

Codex and all project agents MUST NOT create new persistent local folders, Git clones, Git worktrees, task-specific repository copies, checkout directories, report folders, export folders, or other task-created workspace directories on the owner's computer unless the owner explicitly requests that local creation in the current task.

The default is **no new local folders**.

## Default execution

Use, in order of preference:

1. the already selected Codex cloud task environment;
2. the existing repository/workspace already opened for the task;
3. GitHub branches/PRs and repository artifacts without creating another owner-visible local directory.

A branch or PR may be created in GitHub without creating a new owner-visible folder on the Mac.

## Explicit owner permission required

Local creation is allowed only when the owner explicitly asks for it, for example:

- create/clone a local project folder;
- create a local Git worktree;
- download/export an artifact to a named local folder;
- materialize a staging/runtime folder on the Mac.

Permission is task-specific. A prior permission does not authorize future local folders.

## Forbidden by default

Without current explicit owner permission, do not run or cause operations whose purpose is to create additional persistent owner-visible workspace directories, including equivalents of:

- `git clone ... <new-folder>`;
- `git worktree add ...`;
- task-specific copies such as `ege-<task-name>`;
- duplicate repository folders for parallel agents;
- report/output folders outside the existing repository solely for task bookkeeping.

Do not solve parallelism by multiplying local repository copies. Use cloud isolation and GitHub branches/PRs instead.

## Temporary execution storage

Ephemeral container/sandbox directories that exist only inside the Codex cloud execution environment and are not materialized onto the owner's Mac are allowed. They must not be described as owner-local folders.

## Result evidence

Durable task evidence belongs in GitHub (commit/PR/tracked result artifact) unless the owner explicitly requests a local copy.

## Stop condition

If a task cannot continue without creating a new persistent folder on the owner's computer, STOP and return:

`BLOCKED_LOCAL_WORKSPACE_CREATION_REQUIRES_OWNER_PERMISSION`

Do not create the folder first and ask afterward.
