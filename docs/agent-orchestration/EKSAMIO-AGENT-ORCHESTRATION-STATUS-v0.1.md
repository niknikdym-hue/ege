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

## First code slice

Exact code HEAD before this status commit:
`a16b4e2d87935857bff896fd1f2b93e400e4b247`

Implemented:
- versioned strict Astra task-plan JSON schema;
- versioned strict Astra review-decision JSON schema;
- Responses API adapter defaulting to `gpt-6-astra` and Structured Outputs;
- plan/review post-validation, including hard refusal of PASS when an invariant is false;
- fail-closed dangerous-action permission gate;
- Codex executor boundary with safe dry-run;
- immutable-style run record binding input SHA-256 to exact Git SHA;
- network-free unit suite;
- dedicated GitHub Actions gate with no OpenAI/Codex secrets and no live calls.

Exact-head GitHub Actions evidence:
- workflow: `Agent orchestration v0.1`;
- run: `34154896134`;
- exact SHA: `a16b4e2d87935857bff896fd1f2b93e400e4b247`;
- result: SUCCESS;
- compile: SUCCESS;
- 16 network-free unit tests: SUCCESS;
- safe dry-run: SUCCESS.

## Important current limitation

The first code slice intentionally stops before a live agent execution. The Codex boundary is currently a trusted command adapter so CI can prove permissions without installing/authenticating Codex.

Official OpenAI documentation checked on 2026-09-07 confirms the stable Python Codex SDK package is `openai-codex`; it can start a local Codex thread programmatically and supports `Sandbox.workspace_write`, exact `cwd`, model selection, usage reporting, and API-key or existing Codex authentication.

## Next bounded slice

Replace/augment the trusted-command Codex boundary with the official Python `openai-codex` SDK behind the same task contract and owner permission gate. Keep SDK import/auth optional so ordinary PR CI remains network-free. Add mocked SDK tests before any bounded live smoke.

After that, add a single owner-controlled live smoke path for:
`Astra plan -> bounded Codex SDK execution in a dedicated branch/worktree -> deterministic tests -> Astra review`.

No merge/deploy/payment/publication/production learner writes or unbounded provider calls are authorized by this status file.
