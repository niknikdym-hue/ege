# EKSAMIO Agent Orchestration Status v0.1

Status: LIVE INTEGRATION PROVEN / DRAFT PR #190 / NO MERGE / NO DEPLOY
Date: 2026-09-10
Branch: `brain/agent-orchestration-v0-1-20260907`

## Durable checkpoint

Owner-approved architecture is implemented as:
- Astra = Senior Brain / architect / reviewer;
- Codex = bounded execution engineer;
- GitHub = source of truth;
- CI = deterministic evidence;
- owner gates remain mandatory for dangerous actions.

Canonical authority:
`docs/agent-orchestration/EKSAMIO-AGENT-ORCHESTRATION-AUTHORITY-v0.1.md`

New-chat handoff:
`docs/handoffs/EKSAMIO-NEW-CHAT-HANDOFF-2026-09-07.md`

## Code/CI state

### Slice A — Astra contracts + fail-closed orchestration core

Exact code HEAD:
`a16b4e2d87935857bff896fd1f2b93e400e4b247`

Implemented:
- versioned strict Astra task-plan JSON schema;
- versioned strict Astra review-decision JSON schema;
- Responses API adapter defaulting to `gpt-6-astra` and Structured Outputs;
- plan/review post-validation, including hard refusal of `PASS` when any hard invariant is false;
- fail-closed dangerous-action permission gate;
- original trusted-command Codex boundary retained only as a simple fallback/test seam;
- safe dry-run;
- immutable-style run record binding input SHA-256 to exact Git SHA;
- network-free unit suite;
- dedicated GitHub Actions gate with read-only contents permission, no OpenAI/Codex secrets and no live calls.

Exact-head GitHub Actions evidence:
- workflow: `Agent orchestration v0.1`;
- run: `34154896134`;
- head SHA: `a16b4e2d87935857bff896fd1f2b93e400e4b247`;
- result: SUCCESS;
- compile: SUCCESS;
- 16 network-free unit tests: SUCCESS;
- safe dry-run: SUCCESS.

### Slice B — official Python Codex SDK executor

Exact code HEAD:
`36585224c8026f78216f19328833bfd5ad7192e8`

Implemented:
- official stable Python SDK boundary for package `openai-codex`;
- delayed SDK import so normal PR CI remains network-free and credential-free;
- exact repository-root verification before execution;
- exact checkout `HEAD == task.base_sha` verification;
- exact current branch `== target_branch` verification;
- owner permission gate runs before provider execution;
- API-key authentication is required before a live Codex SDK turn;
- Codex thread uses exact `cwd` and `Sandbox.workspace_write`;
- execution prompt repeats the bounded scope and dangerous-action prohibitions;
- returned Codex turn id/status/final response/duration/usage are converted to JSON-safe evidence;
- six additional SDK-boundary tests cover exact checkout, branch movement, wrong branch, missing key, dangerous-action rejection and action-specific owner grants.

Exact-head GitHub Actions evidence:
- workflow: `Agent orchestration v0.1`;
- run: `34155323488`;
- head SHA: `36585224c8026f78216f19328833bfd5ad7192e8`;
- PR merge-test checkout SHA used by GitHub Actions: `3815cc0500b7caa36b25edd2ff2fddce17cb319f`;
- result: SUCCESS;
- compile: SUCCESS;
- 22 total network-free unit tests: SUCCESS;
- safe dry-run: SUCCESS;
- no OpenAI/Astra/Codex live API call occurred;
- no secret was supplied to CI.

Codex SDK boundary documentation:
`agent-orchestration/CODEX-SDK.md`

### Slice C — owner-gated live-smoke controller

Exact code HEAD:
`c67a9b07eb3f6cf594d34e57800f68773f4fba15`

Implemented:
- `agent-orchestration/live_smoke.py` controller for `Astra plan -> Codex SDK -> deterministic checks -> Astra review`;
- explicit owner live-provider authorization gate is checked **before** the first call to Astra;
- a live-provider grant does not grant deploy/merge/payment/production/publication or other dangerous product actions;
- live smoke requires a clean exact Git checkout, exact `base_sha` and exact target branch;
- Astra cannot change owner-controlled repository/base SHA/target branch;
- task acceptance commands must be exact members of an owner-provided allowlist and are executed without `shell=True`;
- changed paths must fit both Astra task scope and owner maximum scope;
- first live smoke forbids Codex commit/push by requiring Git HEAD to remain equal to the pinned base SHA;
- review receives the actual bounded diff, changed paths, deterministic acceptance results and a SHA-256 of the diff;
- oversized review diffs fail closed rather than being partially reviewed;
- run artifact contains exact base SHA, context/task/diff hashes, provider usage metadata and Astra decision;
- artifact output is forced outside the mutable checkout so the controller cannot silently contaminate the reviewed diff;
- ordinary CI still performs no paid/live provider calls.

Exact-head GitHub Actions evidence:
- workflow: `Agent orchestration v0.1`;
- run: `34155825825`;
- head SHA: `c67a9b07eb3f6cf594d34e57800f68773f4fba15`;
- PR merge-test checkout SHA used by GitHub Actions: `d45c3788f641797e9fdd1a3deec2174b588ff2f0`;
- result: SUCCESS;
- all three orchestration modules compile: SUCCESS;
- 30 total network-free unit tests: SUCCESS (`Ran 30 tests ... OK`);
- safe dry-run: SUCCESS;
- owner-flag-before-Astra, exact-SHA, dirty-workspace, out-of-scope-change, arbitrary-command and dangerous-action rejection are explicitly covered;
- no OpenAI/Astra/Codex live API call occurred;
- no secret was supplied to CI.

## Slice D — first live Astra -> Codex -> Astra proof

Successful execution HEAD:
`06f10c212c5ae7bf1c6e83e42f877a18a1d20854`

GitHub Actions evidence:
- workflow run: `34503423279`;
- result: SUCCESS;
- Astra Brain produced the bounded read-only task with `gpt-6-astra`;
- Codex executed it with `gpt-5.6-terra` through `openai/codex-action@v1` in `read-only` sandbox;
- Codex inspected only `agent-orchestration/README.md` and reported no changed files;
- deterministic checkout-clean assertion: `true`;
- Astra reviewed the Codex evidence with `gpt-6-astra` and returned `PASS`;
- Astra plan usage: 334 input + 233 output = 567 tokens;
- Astra review usage: 495 input + 81 output = 576 tokens;
- provider storage was disabled for both Astra calls (`store: false`);
- sanitized durable evidence: `agent-orchestration/evidence/astra-codex-joint-run-34503423279.json`.

The preceding one-model Astra connectivity smoke also passed in workflow run `34502398594` at HEAD `30974f6ee0abee2b721362577e4a5e2c750753c8`; its sanitized durable evidence is `agent-orchestration/evidence/astra-paid-smoke-run-34502398594.json`. The first joint attempt, run `34503072353`, stopped before the Codex provider call because of an incompatible action flag; its successful Astra plan was reused for the corrected joint run.

The one-shot triggers have been removed. A future paid/live task still requires a new explicit owner authorization and a new SHA-bound trigger. This status file does **not** authorize further spend by itself.

This development-agent path is `GitHub Actions -> OpenAI`; it does not use Yandex as an intermediary or execution host.

## Hard boundaries still in force

No merge, deploy, Tilda publication, public traffic change, payment/refund, production learner mutation/migration, email/SMS delivery, secret creation/rotation/exposure, or other dangerous operation is authorized merely because this PR is green.

Development-agent Astra does not become the learner-facing Tutor provider by implication. Tutor brain selection remains provider-neutral and must be decided by Eksamio comparative pedagogical testing.
