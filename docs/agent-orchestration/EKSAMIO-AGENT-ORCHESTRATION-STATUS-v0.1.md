# EKSAMIO Agent Orchestration Status v0.1

Status: ACTIVE IMPLEMENTATION / DRAFT PR #190 / NO MERGE / NO DEPLOY
Date: 2026-09-07
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
- 22 total network-free unit tests: SUCCESS (`Ran 22 tests ... OK`);
- safe dry-run: SUCCESS;
- no OpenAI/Astra/Codex live API call occurred;
- no secret was supplied to CI.

Codex SDK boundary documentation:
`agent-orchestration/CODEX-SDK.md`

## Current limitation / next bounded slice

The development loop is now implemented and CI-proven through the **offline boundary**, including the real official Codex SDK adapter, but no paid/live Astra or Codex development-agent turn has been executed yet.

Next bounded implementation slice is a **live-smoke harness**, not an unbounded autonomous system. It must:
- require an explicit owner/live-provider authorization flag in addition to credentials;
- bind the run to an exact Git repository, base SHA and dedicated target branch/worktree;
- run `Astra plan -> Codex SDK execution -> deterministic checks -> Astra review`;
- persist a machine-readable run artifact with exact Git SHA, input hashes, requested/returned model identity and usage metadata;
- remain fail-closed for merge/deploy/publication/payment/production learner writes/email/SMS/secret actions;
- have mocked/network-free tests proving that a live provider cannot be reached without the explicit authorization gate;
- keep ordinary PR CI free of paid/live provider calls.

A real paid live smoke must be separately owner-bounded before execution. This status file does not authorize spend by itself.

## Hard boundaries still in force

No merge, deploy, Tilda publication, public traffic change, payment/refund, production learner mutation/migration, email/SMS delivery, secret creation/rotation/exposure, or other dangerous operation is authorized merely because this PR is green.

Development-agent Astra does not become the learner-facing Tutor provider by implication. Tutor brain selection remains provider-neutral and must be decided by Eksamio comparative pedagogical testing.
