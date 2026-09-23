# Owner Control API-Codex smoke contract v2 — 2026-09-23

Status: FREE SAFETY REWORK / SECOND PAID SMOKE NOT YET AUTHORIZED

## Evidence that changed the contract

The first live Owner Control smoke reached one `codex exec` process with:

- model: `gpt-5.6-luna`;
- Astra plan: OFF;
- Astra acceptance: OFF;
- `request_max_retries=0`;
- `stream_max_retries=0`;
- hard aggregate OpenAI cap: `$0.10`;
- one signed command, one permanent claim and one bound batch;
- six Responses API provider requests inside the single Codex agent/tool loop;
- proxy reservation: `$0.079242`;
- remaining hard budget: `$0.020758`;
- one candidate path only:
  `docs/project-control/OWNER-CONTROL-API-CODEX-SMOKE-TARGET-2026-09-22.md`;
- exact candidate effect:
  append `API_CODEX_SMOKE_2026_09_22=PASS_CANDIDATE`;
- `git diff --check`: PASS.

The run was intentionally rejected before validation because the previous smoke contract incorrectly required exactly one provider request.

## Astra review

Astra run: `35816167207`

Decision: `REWORK`.

Astra determined that Codex agent/tool turns are distinct from automatic retries. The accepted upper bound to implement is the smallest observed working bound: **6 provider requests per authorized Codex execution**.

## Hard execution contract

For every API-Codex task:

1. exactly one `codex exec` process;
2. `request_max_retries=0`;
3. `stream_max_retries=0`;
4. maximum provider requests: **6**;
5. request slot must be claimed in the budget proxy before upstream forwarding;
6. request 7 must be rejected locally and must never reach OpenAI;
7. failed/cancelled/streamed upstream attempts consume their request slot and it is never refunded;
8. provider-request state is held by the root-owned budget proxy for the execution; Codex cannot restart it or obtain the raw OpenAI key;
9. if proxy/counter state is unavailable or ambiguous, execution fails closed;
10. aggregate OpenAI budget remains independently enforced;
11. model allowlist remains independently enforced;
12. no automatic rerun at workflow or model layer.

Astra plan/acceptance phases, when explicitly required by task authority, remain limited to one direct provider request each and are budgeted separately.

## Second smoke contract

A second smoke, if separately authorized, must keep:

- task: `A1.4`;
- model: `gpt-5.6-luna`;
- hard aggregate OpenAI cap: `$0.10`;
- maximum provider requests: `6`;
- one `codex exec`;
- retries: `0/0`;
- Astra plan: OFF;
- Astra acceptance: OFF;
- allowed path only:
  `docs/project-control/OWNER-CONTROL-API-CODEX-SMOKE-TARGET-2026-09-22.md`;
- expected exact effect:
  append `API_CODEX_SMOKE_2026_09_22=PASS_CANDIDATE`;
- no merge;
- no deploy;
- no Ready transition;
- no production/learner/payment/Tilda mutation;
- no automatic next task.

Acceptance requires trusted validation to run and pass after Codex completes. Candidate work alone is not acceptance.

## Authorization state

This document and the free tests do **not** authorize another paid run. A second paid smoke must be explicitly authorized after all free six-turn enforcement gates pass.
