# OWNER-AGENT-CONSOLE-REMOTE-SLICE-3 — SEMANTIC ACCEPTANCE REPAIR

You are API-Codex repairing the bounded Owner Console implementation already present on the current branch. Do not scan the repository or touch unrelated files.

Read only:
- `eksamio-learning-engine/AGENTS.md` and mandatory exact-path instructions;
- `docs/project-control/EKSAMIO-OWNER-CONSOLE-REQUIREMENTS-v0.1.md`;
- `eksamio-learning-engine/00B-PROJECT-PRIORITIES-CURRENT.md`;
- the existing files under `eksamio-learning-engine/project-control/`;
- the existing targeted test and result file;
- this task.

The first implementation passed its targeted test and synchronized Issue #194, but independent review found substantive contract gaps. Fix these gaps; do not merely weaken tests.

Allowed output paths only:
- `eksamio-learning-engine/project-control/**`
- `eksamio-learning-engine/tests/test_owner_agent_console.py`
- `eksamio-learning-engine/results/RESULT-OWNER-AGENT-CONSOLE-REMOTE-SLICE-1.md`
- `.github/workflows/owner-agent-console-sync.yml`

Required repairs:
1. `operational-board-v1.json` must itself contain a `tasks` array with every official operational-board row exactly once: total 115; stage counts A=74, B=15, C=11, D=8, E=7. Each task carries the full task-card contract from the requirements, including the exact raw/source status as `source_status`. Runtime rendering must consume this JSON, not reparse Markdown as its task database.
2. Preserve truthful semantics. Exact required normalized examples: A2.1 must not be `NOT_STARTED`; A6.1 (`VISIBLE BASE EXISTS`) must be `VISIBLE_TO_LEARNER` with `visible_to_learner=true`. Do not label all future D/E work `DESIGNED`, and never make `CODE_READY` learner-visible. Preserve uncertain/compound source states verbatim in `source_status` and map conservatively to the shared vocabulary.
3. Owner Gates must contain only genuine owner actions. In particular A12.4 post-launch smoke and A12.5 monitoring are not owner gates. Do not mark all A/B tasks as Astra work.
4. Critical Path must be the ordered 12-step critical path from section 10 of the operational board, not every Stage A row.
5. Implement live GitHub fact ingestion for sync: refresh current main SHA plus relevant open PR/head/Draft/check facts using read-only `gh` calls before rendering. The offline fixture must cover the same adapter shape. Conflicts between board facts and GitHub facts render `STALE/CONFLICT`. Do not infer learner visibility from CI.
6. Render all required views with useful task title/status/current action, not only IDs. Keep all stages A-E, A+B together, Visible Product truth, real Owner Gates, grouped blockers, history, Astra/API-Codex activity, and `CORRECTION: ... NOT_DISPATCHED`.
7. Expand deterministic tests to enforce exact task count/stage counts/unique IDs/required fields, known semantic examples, owner-gate exclusions, ordered critical path, offline GitHub PR/check rendering, conflict behavior, no secret/unknown fields, and all required sections.
8. Update the durable result with exact checks and remaining audited command-adapter work.
9. Produce `.github/workflows/owner-agent-console-sync.yml` with manual/daily/control-plan triggers, `contents: read`, `issues: write`, no provider key and no learner/runtime dependency.

Forbidden: learner/runtime/demo/trainer/payment/Tutor changes; Yandex operations; OpenAI calls in the resulting console; secrets; deployment; merge; public hosting; invented progress; edits to PR #190/#191; broad test suites; git commit/push from your step.

Run only the targeted unittest and offline render smoke. Stop after the repaired bounded implementation; the trusted workflow validates, commits and synchronizes Issue #194.
