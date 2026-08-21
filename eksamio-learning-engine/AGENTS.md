# Eksamio Learning Engine — Codex instructions

These instructions apply to the entire `eksamio-learning-engine/` tree.

## Source of truth

GitHub is the durable source of truth. Chat history is navigation, not project authority.

`eksamio-learning-engine/` is the Eksamio Personal Exam Intelligence System (PEIS) root inside `niknikdym-hue/ege`.

### Minimal required start for every task

1. Refresh/check current `main`.
2. Read `00-PRODUCT-MASTERPLAN.md`.
3. Read `00E-CURRENT-BRAIN-HANDOFF.md`.
4. Read the exact task/scope supplied for this run.
5. Read only the subject/source/contracts directly relevant to that task.

For cross-subject architecture, PEIS, production, deployment/security, identity/auth, commerce or governance work, also read the relevant current authority named by `00E`, including `00B-PROJECT-PRIORITIES-CURRENT.md`, `00C-IMPLEMENTATION-GOVERNANCE-GUIDE.md` and `00D-BRAIN-CONTINUITY-PROTOCOL.md` when needed.

`00-WORK-STATUS.txt` and `00A-WORK-STATUS-CURRENT-ADDENDUM.txt` are historical checkpoints, not current operating state. Older files may contain valid substantive architecture but stale start/read-order instructions; current `00E` + this file supersede those operational pointers.

Do not perform broad repository audits from zero when the task can be resolved by checking the delta from current accepted state.

## Fixed system rules

- Eksamio is one PEIS, not separate learner engines per subject.
- Russian is subject #1, Mathematics #2, Physics #3.
- Russian and Mathematics are P0 system subjects; Physics is P1 and may proceed in parallel without slowing P0 work.
- Subject source target is 2022–2026 where applicable.
- A subject may own verified source, semantic identities, prerequisites, exam routes and content, but not a separate Student Model / Evidence / Mastery / Readiness / Retention / NBA engine.
- The base loop remains free: `diagnose -> model -> prioritize -> practice/help -> verify -> retain -> reassess -> replan`.
- Eksamio runtime must not depend on a ChatGPT/OpenAI subscription. OpenAI/Codex may be development tools or replaceable AI providers, never canonical product infrastructure.

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

1. dedicated branch/worktree;
2. narrow scope;
3. required tests/validation;
4. durable result/validation evidence;
5. PR;
6. review before merge where acceptance matters.

For small add-only governance/documentation work, do not manufacture extra task/result/review files when the commit/PR itself is sufficient evidence.

## Result contract

Every completed implementation/audit task must leave durable evidence in GitHub. A chat response alone is insufficient.

Minimum useful result data:

- status `DONE|PARTIAL|BLOCKED`;
- files changed;
- checks/tests and outcomes;
- unresolved items/contradictions;
- branch/commit/PR when applicable;
- whether production files changed.

Do not duplicate the same information across multiple documents without a real need.

## Parallel work

Parallel subject chats/agents may work on separate branches and subject scopes. They are execution lanes, not independent project brains.

The Brain reviews meaningful deltas across lanes: significant merges, changed blockers, cross-subject/shared-core changes, production-impacting PRs and unsupported DONE claims. If nothing material changed, do not create another checkpoint or repeat an audit.

## Subscription/provider independence

No Eksamio product state or base learning function may require:

- ChatGPT Plus/Pro;
- Codex subscription/credits;
- an OpenAI end-user account;
- one fixed AI provider/model.

Provider-dependent premium AI may fail over, be disabled, or use another approved adapter while deterministic/base PEIS continues to work.