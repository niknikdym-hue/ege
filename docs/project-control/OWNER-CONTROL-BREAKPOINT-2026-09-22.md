# EKSAMIO Owner Control — breakpoint before first paid API-Codex smoke

Date: 2026-09-22
Status: SAFE BREAKPOINT / NO PAID CODEX SMOKE YET

## Frozen authorities

- EGE main: `2e49dd86bb419ec6a1f1c3b76428c81faaf7a45d`
- Brain main: `b60fdac1bc33eefcbf84501ad330e086edefa60e`
- Brain Yandex deploy run: `35762063497` — SUCCESS
- Deployed bridge signing key id: `b112e9453bf55c94`
- Deployed bridge public key: `OMzLDqpkbW75xQIzUy_-7vVenvAIxs4l3F_knEkMpPg`

## Astra decisions

### Owner Control readiness audit
- Run: `35689818626`
- Decision: REWORK
- Astra calls: 1
- Codex calls: 0
- Estimated Astra cost: $0.111018
- Resulting free safety remediation is merged.

### Command bridge architecture review
- Run: `35758435849`
- Decision: REWORK
- Astra calls: 1
- Codex calls: 0
- Estimated Astra cost: $0.098370
- Astra accepted the dedicated signed command-branch/PR bridge direction subject to strict provenance, one-use claims, immutable verifier, exact SHA binding, hard budgets and no retries.

## Completed

1. Owner Control UI/backend exists and stays UI-locked.
2. Brain command bridge backend merged and deployed.
3. Brain signs commands with Ed25519 using server-only owner secret material.
4. EGE pins the deployed Brain public verification key.
5. EGE signed command bridge merged through PR #206.
6. EGE free safety gates on bridge HEAD passed:
   - Owner Control GitHub-first static safety — PASS
   - Owner Control v2 free safety proof — PASS
   - retry-zero mock — PASS
   - budget-proxy mock — PASS
7. Command transport channel:
   - persistent Draft PR #205
   - branch `owner-control/commands`
   - only allowed changed file: `ops/owner-control-command/command.json`
   - DO NOT MERGE PR #205.
8. Protected EGE PAT Contents-write capability proved:
   - HTTP 200 write
   - push triggered EGE workflow
   - zero paid calls.
9. Direct PAT Actions dispatch and issue-comment paths are known unusable:
   - workflow_dispatch -> HTTP 403
   - issue comment -> HTTP 403
   - these paths must not be retried.

## Current expected failure

Latest command bridge run:
- run `35777826374`
- trusted PR/base verification: PASS
- immutable command load: PASS
- signature/schema verification: FAIL because PR #205 currently contains the EMPTY transport baseline rather than a signed command envelope
- revalidation/claim/dispatch: SKIPPED
- paid calls: 0

This failure is fail-closed and expected before the panel is switched to the bridge.

## First action after resume

1. Update Brain Yandex deploy configuration to set:
   - `EKSAMIO_OWNER_CONTROL_COMMAND_BRIDGE_ENABLED=true`
   - `EKSAMIO_OWNER_CONTROL_COMMAND_BRANCH=owner-control/commands`
   - `EKSAMIO_OWNER_CONTROL_COMMAND_PATH=ops/owner-control-command/command.json`
   - retain short command TTL.
2. Deploy exact Brain main with those settings.
3. From the Owner Control panel, run exactly one A1.4 smoke:
   - model: `gpt-5.6-luna`
   - hard aggregate OpenAI cap: `$0.10`
   - Astra plan: OFF
   - Astra acceptance: OFF
   - automatic retries: 0
   - allowed path only:
     `docs/project-control/OWNER-CONTROL-API-CODEX-SMOKE-TARGET-2026-09-22.md`
   - no merge/deploy/Ready/production mutation.
4. Accept smoke only if there is exactly one command, one claim, one batch, one child/provider request, correct docs-only diff, and no automatic follow-up.
5. Only after smoke PASS route normal Eksamio development through Owner Control.

## Do not do on resume

- Do not create a new GitHub PAT.
- Do not retry direct workflow_dispatch with the protected EGE PAT.
- Do not use issue comments as the command transport.
- Do not merge PR #205.
- Do not redesign Owner Control UI.
- Do not launch Astra again unless new evidence requires an independent decision.
- Do not run more than the single bounded API-Codex smoke before accepting the bridge.
