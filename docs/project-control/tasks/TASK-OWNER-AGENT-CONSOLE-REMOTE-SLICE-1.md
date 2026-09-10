# OWNER-AGENT-CONSOLE-REMOTE-SLICE-1

You are API-Codex, the bounded implementation executor for niknikdym-hue/ege.

Base is exact PR #191 head `f84a74c55362de4e830e8a98a3a08d7bb1002403`. Read completely: `eksamio-learning-engine/AGENTS.md`, the mandatory files it names, `docs/project-control/EKSAMIO-OWNER-CONSOLE-REQUIREMENTS-v0.1.md`, `eksamio-learning-engine/00-PRODUCT-MASTERPLAN.md`, and `eksamio-learning-engine/00B-PROJECT-PRIORITIES-CURRENT.md`.

Implement a first real remote Owner Control page as one durable GitHub Issue maintained by deterministic repository code. This is the safe bootstrap UI because the Owner's Mac must do no checkout, server, build, or background work.

Allowed paths only:
- `eksamio-learning-engine/project-control/**`
- `eksamio-learning-engine/tests/test_owner_agent_console.py`
- `eksamio-learning-engine/results/RESULT-OWNER-AGENT-CONSOLE-REMOTE-SLICE-1.md`
- `.github/workflows/owner-agent-console-sync.yml`

Required:
1. A versioned machine-readable JSON operational board containing every Stage A-E task from the current operational board exactly once, with honest statuses and no invented percentages.
2. A dependency-free Python renderer/synchronizer. Offline render uses a tracked GitHub fixture. Live sync uses only `gh` read/write issue metadata through `GH_TOKEN`; it may read main/PR/head/Draft/check facts and create/update exactly one issue titled `Eksamio — Owner Control`. Never read or render secrets or learner data.
3. The issue page must show Header truth, stage rail A-E, Whole Project, Critical Path, Russian Product, Visible Product, Owner Gates, Blockers, History, and a separate Astra/API-Codex activity section. It must distinguish CODE_READY from VISIBLE_TO_LEARNER and show STALE/CONFLICT.
4. Owner correction: explain that an Owner comment beginning `CORRECTION:` is a durable instruction but is `NOT_DISPATCHED` until the audited command adapter slice. Do not create fake action buttons and do not auto-execute comments.
5. A workflow with `contents: read` and `issues: write` that runs manually, daily, and when control-plan documents change; it renders and syncs the one issue. No provider key is used by this resulting sync workflow.
6. Deterministic tests: A-E present; all board task IDs unique; A+B visible together; code-only never becomes learner-visible; owner gates exclude routine tasks; stale/conflict visible; no secret/unknown fields in output; correction is NOT_DISPATCHED; renderer makes all required sections.
7. Durable result report with exact files/checks and explicit remaining slice for real pause/correct/resume/request-rework dispatch.

Required stable CLI:
`python3 eksamio-learning-engine/project-control/owner_agent_console.py render --board eksamio-learning-engine/project-control/operational-board-v1.json --github-fixture eksamio-learning-engine/project-control/github-fixture-v1.json --output /tmp/owner-console.md`

`python3 eksamio-learning-engine/project-control/owner_agent_console.py sync --board eksamio-learning-engine/project-control/operational-board-v1.json --repository niknikdym-hue/ege --issue-title 'Eksamio — Owner Control'`

Forbidden: learner/runtime/demo/trainer/payment/Tutor changes; Yandex; OpenAI calls in resulting console; secrets; deploy; merge; public site; invented progress; editing PR #190/#191; git commit/push from your step.

Implement, run the exact relevant tests, and stop. Return a concise result; the trusted workflow will validate, commit and publish the issue page.
