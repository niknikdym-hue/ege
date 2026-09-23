# EKSAMIO Agent Orchestration Authority v0.1

Status: OWNER-APPROVED / ACTIVE
Date: 2026-09-07
Repository: `niknikdym-hue/ege`

## 1. Source of truth

GitHub repository state is the only durable project source of truth for implementation status, architecture decisions, acceptance evidence and continuation points. Chat history is not authority.

Every agent run MUST re-read current GitHub state before acting. Do not reconstruct current branch/PR state from memory when GitHub can prove it.

## 2. Role architecture

### Astra = Senior Brain

OpenAI API model: `gpt-6-astra` through the Responses API.

Astra owns high-value reasoning, not mechanical implementation:
- determine the next launch-critical bounded step from current repository truth;
- produce explicit implementation scope and acceptance criteria;
- enforce cross-project architecture and launch invariants;
- review diffs and CI evidence;
- classify result as `PASS`, `REWORK` or `BLOCKED`;
- detect P0/P1 regressions, scope drift and unsupported semantic claims;
- design PEIS / Tutor / learner-state integration where cross-component reasoning is required;
- preserve durable handoff state after meaningful decisions.

Astra MUST NOT independently authorize dangerous external actions.

### Codex = Execution Engineer

Codex is the bounded implementation layer, callable programmatically through the Codex SDK / CLI adapter.

Codex may, inside an explicitly bounded task:
- inspect the repository and exact target branch;
- edit implementation and tests;
- run local deterministic checks;
- create commits and push to the assigned non-protected branch;
- open/update a draft PR when the task contract permits it;
- respond to Astra `REWORK` with another bounded implementation pass.

Codex does not own product truth, semantic authority, launch prioritization or final acceptance.

### CI = deterministic evidence

GitHub Actions and deterministic repository tests are evidence, not merely advisory output. Astra must review exact-head CI rather than infer success from a Codex narrative.

### Owner = final authority for dangerous actions

Explicit owner approval remains required for actions including, unless separately superseded by a later authority file:
- merge to `main`;
- production deploy/apply;
- public Tilda publication / public traffic change;
- real payment/refund;
- production learner-data mutation/migration;
- real email/SMS delivery;
- paid/live external AI, TTS or STT execution outside an already owner-approved bounded smoke;
- secret creation/rotation/exposure;
- destructive repository or cloud actions.

## 3. Mandatory Eksamio invariants

The agent system must preserve existing product/runtime constraints. In particular:
- `false_exact_mastery = 0`;
- semantic mastery/admission requires exact server-provable identity and server-owned evaluation;
- browser/client data cannot assert semantic correctness, score, mastery, evaluator identity or server timestamps;
- registered canonical learner state is server-owned; no anonymous/device-only canonical learner continuity;
- free vs paid is an entitlement distinction, not a separate learner identity;
- subject acceptance and production event admission are separate gates;
- working live UX is not silently invalidated by repository reconciliation;
- no agent may convert uncertain evidence into `PASS`.

## 4. Orchestration cycle

For each bounded implementation unit:

1. **READ** — read current `main`, target PR/issue, exact HEAD and relevant CI.
2. **PLAN** — Astra returns one bounded task with explicit non-goals and acceptance checks.
3. **EXECUTE** — Codex works only inside that task and target branch.
4. **PROVE** — run deterministic local/CI gates; record exact commit SHA.
5. **REVIEW** — Astra reviews diff + exact-head CI + hard invariants.
6. **DECIDE** — `PASS`, `REWORK`, or `BLOCKED` with factual reason.
7. **PERSIST** — meaningful decision and continuation point are written to GitHub.
8. **INTEGRATE** — owner-controlled action when integration/deploy authority is required.

No broad re-audit is allowed as a substitute for advancing the first real unresolved launch blocker.

## 5. Astra execution policy

Environment variable / configuration key: `OPENAI_ASTRA_MODEL`.
Default v0.1 alias: `gpt-6-astra`.

Recommended reasoning policy:
- `high` for ordinary Senior-Brain planning/review;
- `xhigh` or `max` only for genuinely hard architectural/security/semantic decisions;
- cheaper execution paths should handle deterministic/mechanical work.

Every run must persist at minimum:
- requested model ID;
- returned model identity when available;
- GitHub base/ref/HEAD read before the decision;
- bounded task or review input hash;
- decision (`PASS|REWORK|BLOCKED`);
- timestamp;
- cost/usage metadata when the API exposes it.

API keys must come from secret storage/environment and must never be committed to the repository, task prompt, CI artifact or log.

## 6. Codex execution policy

Preferred integration: Codex SDK (`@openai/codex-sdk`) behind an Eksamio-owned adapter; `codex exec` may be used for shell/CI environments.

Codex receives a machine-readable task contract produced/approved by Astra. At minimum it contains:
- repository;
- base SHA / target branch;
- exact allowed scope;
- acceptance commands/checks;
- forbidden actions;
- expected output contract.

The executor must fail closed if the branch moved incompatibly, required authority is missing, a secret is unavailable, or a forbidden live action would be required.

## 7. v0.1 implementation target

Build the smallest useful `Astra Senior Brain -> Codex executor -> CI -> Astra review` runner without creating a general autonomous-agent platform.

Initial deliverables:
- versioned task/review JSON schemas;
- Astra planner/reviewer adapter using Responses API;
- Codex execution adapter;
- immutable per-run result artifact suitable for GitHub attachment/commit;
- dry-run mode with no external mutations;
- deterministic tests for permission gates and schema validation;
- explicit owner-gate enforcement before merge/deploy/live-provider actions.

The runner must not be a hidden alternative source of truth: durable status returns to GitHub.

## 8. Provider separation

This authority concerns **Eksamio software development**, not automatic Tutor-provider selection.

`Astra = Senior Brain` for development does not imply `Astra = Tutor brain` for learners. Tutor provider selection remains provider-neutral and must be decided by Eksamio's comparative pedagogical testing across the approved candidate set.

## 9. Official API verification used for v0.1

Verified 2026-09-07 against official OpenAI documentation:
- GPT-6 Astra API model ID: `gpt-6-astra`; Responses API supported.
- Codex SDK is available for programmatic embedding; Codex CLI supports `codex exec` for shell workflows.

Any future implementation must re-check current OpenAI API/SDK documentation before depending on mutable capabilities or pricing.
