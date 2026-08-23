# Eksamio Learning Engine — Codex instructions

These instructions apply to the entire `eksamio-learning-engine/` tree.

## Source of truth

GitHub is the durable source of truth. Chat history is navigation, not project authority.

`eksamio-learning-engine/` is the Eksamio Personal Exam Intelligence System (PEIS) root inside `niknikdym-hue/ege`.

### Minimal required start for every task

1. Refresh/check current `main`.
2. Read `00-PRODUCT-MASTERPLAN.md`.
3. Read `00E-CURRENT-BRAIN-HANDOFF.md`.
4. Read `LOCAL-WORKSPACE-POLICY.md`.
5. Read the exact task/scope supplied for this run.
6. Read only the subject/source/contracts directly relevant to that task.

For cross-subject architecture, PEIS, production, deployment/security, identity/auth, commerce or governance work, also read the relevant current authority named by `00E`, including `OWNER-DECISIONS-2026-08-22.md`, `00B-PROJECT-PRIORITIES-CURRENT.md`, `00C-IMPLEMENTATION-GOVERNANCE-GUIDE.md` and `00D-BRAIN-CONTINUITY-PROTOCOL.md` when needed.

`00-WORK-STATUS.txt` and `00A-WORK-STATUS-CURRENT-ADDENDUM.txt` are historical checkpoints, not current operating state. Older files may contain valid substantive architecture but stale start/read-order instructions; current `00E` + this file supersede those operational pointers.

Do not perform broad repository audits from zero when the task can be resolved by checking the delta from current accepted state.

## Fixed system rules

- Eksamio is one PEIS, not separate learner engines per subject.
- Russian is subject #1, Mathematics #2, Physics #3.
- Russian and Mathematics are P0 system subjects; Physics is P1 and may proceed in parallel without slowing P0/central blocker work.
- Subject source target is 2022–2026 where applicable.
- A subject may own verified source, semantic identities, prerequisites, exam routes and content, but not a separate Student Model / Evidence / Mastery / Readiness / Retention / NBA engine.
- The base loop remains free: `diagnose -> model -> prioritize -> practice/help -> verify -> retain -> reassess -> replan`.
- Eksamio must aim beyond the current world baseline in measurable educational outcomes, not by adding fashionable features. Use `PRODUCT-BENCHMARK-2026.md` and the Tutor world benchmark when a task affects product differentiation or AI tutoring.
- Advanced architecture must remain economical: prefer deterministic tools, compact context, cheap model routing, reuse and on-demand infrastructure; reject complexity/cost without measurable learning or product gain.
- Eksamio runtime must not depend on a ChatGPT/OpenAI subscription. OpenAI/Codex may be development tools or replaceable AI providers, never canonical product infrastructure.

## Owner local-workspace boundary

`LOCAL-WORKSPACE-POLICY.md` is mandatory owner authority.

- Default: create no new persistent owner-local folders.
- Do not create new clones, Git worktrees, task-specific repository copies, checkout folders, report folders, export folders or other persistent workspace directories on the owner's computer unless the owner explicitly requests that local creation in the current task.
- Parallel work should use cloud isolation plus GitHub branches/PRs instead of multiplying local repository copies.
- Ephemeral directories inside a cloud/container sandbox are allowed when they are not materialized onto the owner's Mac.
- If a task genuinely cannot continue without a new owner-local folder, stop with `BLOCKED_LOCAL_WORKSPACE_CREATION_REQUIRES_OWNER_PERMISSION`; do not create first and ask later.

## Task admission and efficiency

A valid task contract should make the execution purpose obvious before code is touched.

For significant implementation/audit work, require or infer from the supplied contract:

- `WHY_NOW` — exact reason this is the next useful work;
- `ACTIVE_BLOCKER_OR_MILESTONE`;
- `BASELINE_MAIN_SHA`;
- `DEPENDENCY_IN`;
- `MINIMAL_DELTA`;
- `EXPECTED_UNLOCK`;
- `ALLOWED_PATHS` / `FORBIDDEN_PATHS` where applicable;
- `ACCEPTANCE_EVIDENCE`;
- `STOP_CONDITIONS`;
- allowed final status values.

If `EXPECTED_UNLOCK` is unclear, do not broaden the task to create work. Return the ambiguity/blocker.

Use the lightest existing path that can safely meet acceptance. Reuse a working build/deploy/review flow instead of inventing a new CI, selector, staging layer, service or framework unless the existing path is proven insufficient for a concrete requirement.

If a bounded task unexpectedly requires a materially wider architecture change, global configuration change, frozen-authority change or unrelated migration, STOP and report the exact new blocker. Do not expand the project on your own.

When an interactive task only needs owner authentication and Browser/Computer control is available, surface the real login/2FA/CAPTCHA step to the owner and continue the same task after authentication. Do not replace a simple authentication dependency with a new deployment mechanism.

## Safety

- Never modify published/frozen demo or trainer files unless the current task explicitly authorizes exact paths.
- Never silently delete, rename, move, refactor or fix unrelated files.
- Unknown/unverified facts must remain `null`, `needs_review`, `NOT_CONFIRMED` or another task-approved unresolved state.
- Official exam facts, answers, criteria, numbering and scoring must come from verified source authority, not AI reconstruction.
- Difficulty remains `null` unless validated data or an explicitly reviewed algorithm supports it.
- Preserve backward compatibility unless a migration is explicitly specified and tested.
- A mergeable PR is not automatically acceptable.

## Russian source policy

For Russian rules/explanations/algorithms/examples, prefer verified materials in `russkiy-knigi/` plus official FIPI for exam-specific truth.

- Do not invent grammar methodology when verified sources exist.
- Adapt and summarize; do not copy long copyrighted passages.
- Preserve provenance.
- Source conflicts remain `needs_review` until resolved.
- Non-official books never override current FIPI exam numbering/scoring/criteria.

## Change workflow

Use the lightest workflow that preserves correctness and recovery.

For behavior/source/identity/PEIS/production-affecting work:

1. dedicated Git branch; use a Git worktree only when the owner explicitly authorizes local worktree creation for the current task;
2. narrow scope;
3. required tests/validation;
4. durable result/validation evidence;
5. PR;
6. review before merge where acceptance matters.

For small add-only governance/documentation work, do not manufacture extra task/result/review files when the commit/PR itself is sufficient evidence.

## Result contract

Every completed implementation/audit task must leave durable evidence in GitHub. A chat response alone is insufficient.

Minimum useful result data:

- status `DONE|PARTIAL|BLOCKED` or task-specific bounded status;
- files changed;
- checks/tests and outcomes;
- unresolved items/contradictions;
- branch/commit/PR when applicable;
- whether production files changed;
- what dependency was actually unlocked.

Do not duplicate the same information across multiple documents without a real need.

## Parallel work

Parallel subject chats/agents may work on separate branches and subject scopes. They are execution lanes, not independent project brains.

The Brain reviews meaningful deltas across lanes: significant merges, changed blockers, cross-subject/shared-core changes, production-impacting PRs and unsupported DONE claims. If nothing material changed, do not create another checkpoint or repeat an audit.

Parallel work is only useful when each lane has a concrete bounded endpoint and does not steal resources from the active central blocker.

Parallelism must not create additional owner-local repository folders unless the owner explicitly requests them; prefer cloud task isolation and GitHub branches/PRs.

## Subscription/provider independence

No Eksamio product state or base learning function may require:

- ChatGPT Plus/Pro;
- Codex subscription/credits;
- an OpenAI end-user account;
- one fixed AI provider/model.

Provider-dependent premium AI may fail over, be disabled, or use another approved adapter while deterministic/base PEIS continues to work.
