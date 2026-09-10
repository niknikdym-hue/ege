# OWNER-AGENT-CONSOLE-REMOTE-SLICE-1 — SPARSE RETRY

You are API-Codex, the bounded implementation executor for `niknikdym-hue/ege`.

The checkout is intentionally sparse to protect the hosted runner. Do not scan the repository: no broad `find`, `rg`, `git ls-files`, builds, dependency installs, browser tests, or unrelated test suites.

Read only these tracked inputs:
- `eksamio-learning-engine/AGENTS.md` and only the instruction files it explicitly requires for this exact path;
- `docs/project-control/EKSAMIO-OWNER-CONSOLE-REQUIREMENTS-v0.1.md`;
- `eksamio-learning-engine/00B-PROJECT-PRIORITIES-CURRENT.md`;
- this task.

Implement a deterministic GitHub-Issue Owner Control page. It is a project-management surface only and must remain independent of learner production.

Allowed output paths only:
- `eksamio-learning-engine/project-control/**`
- `eksamio-learning-engine/tests/test_owner_agent_console.py`
- `eksamio-learning-engine/results/RESULT-OWNER-AGENT-CONSOLE-REMOTE-SLICE-1.md`
- `.github/workflows/owner-agent-console-sync.yml`

Required implementation:
1. `operational-board-v1.json`: a versioned machine-readable projection containing every Stage A-E task row from `00B-PROJECT-PRIORITIES-CURRENT.md` exactly once. Preserve task IDs and factual statuses; never invent percentages.
2. `owner_agent_console.py`: dependency-free Python CLI with stable commands:
   - `render --board ... --github-fixture ... --output ...`
   - `sync --board ... --repository niknikdym-hue/ege --issue-title 'Eksamio — Owner Control'`
   Offline render uses the tracked fixture. Live sync may use only `gh` and `GH_TOKEN`, updating exactly one issue of that title. Never read/render secrets or learner data.
3. Render these sections: header truth, stage rail A-E, Whole Project, Critical Path, Russian Product (A+B), Visible Product, Owner Gates, Blockers, History, Astra/API-Codex activity. Show `CODE_READY != VISIBLE_TO_LEARNER` and visible `STALE/CONFLICT` on contradictory facts.
4. Explain that `CORRECTION:` comments are durable but `NOT_DISPATCHED`; do not auto-execute them or create fake controls.
5. `.github/workflows/owner-agent-console-sync.yml`: manual, daily and relevant control-plan path triggers; `contents: read`, `issues: write`; no provider/API key.
6. Deterministic unittest covering A-E, unique task IDs, A+B visibility, code-only not learner-visible, owner-gate filtering, conflict rendering, secret/unknown-field exclusion, correction NOT_DISPATCHED and all required sections.
7. Result report listing exact files/checks and the remaining audited pause/correct/resume/rework adapter slice.

Forbidden: learner/runtime/demo/trainer/payment/Tutor edits; Yandex operations; OpenAI calls in the resulting console; secrets; deployment; merge; public hosting; invented progress; edits to PR #190/#191; git commit/push from this step.

Implement, run only the targeted unittest and CLI render smoke, then stop. The trusted workflow validates, commits and syncs Issue #194.
