# Eksamio Tutor — four-brain TEXT benchmark v1

This is the canonical private human benchmark for brain selection. It has exactly
four forced text providers: OpenAI, Qwen, DeepSeek and Yandex. Their order is not
a quality ranking. The human-facing surface shows only Tutor A/B/C/D; provider
mapping is revealed only after all four runs are scored. `AUTO` and provider
fallback are forbidden while scoring.

## Current model/API contract — rechecked 2026-09-06

- OpenAI: `gpt-6-astra`, OpenAI Responses API `/v1/responses`. If the owner
  account has not received Astra API access yet, preflight/live execution must
  fail honestly; no silent fallback to GPT-5.6 Sol.
- Qwen: `qwen3.8-max`, Alibaba Model Studio OpenAI-compatible Responses API.
  Live execution requires the owner workspace-specific `aliyuncs.com` base URL;
  no guessed WorkspaceId is committed.
- DeepSeek: `deepseek-v4-pro` (current V4-Pro-0813), Responses API at the current
  DeepSeek API base.
- Yandex: full-size Alice AI LLM, never Flash. The exact model ID/URI is resolved
  from the owner account before live execution and independently confirmed as
  full-size. Offline `aliceai-llm` is only a deterministic fixture.

All four receive the same server-owned grounding, same provider-neutral prompt
and history projection, same ten scripted learner turns, same 900-token output
cap, and no custom temperature. The grounding path is the already reviewed
121-card exact mapping:

`ex-practice-alt-sochetat-001` -> EXACT
`school-i-e-alternating-verb-roots-stressed-a`

The tester cannot edit the ten learner turns during the canonical run.

## Human scorecard

After each ten-turn run, score every dimension 0–5:

1. subject correctness / adherence to Eksamio source truth;
2. diagnostic precision;
3. sequencing;
4. quality of hints / scaffolding;
5. does not reveal the final answer prematurely;
6. correction clarity;
7. transfer to a new example;
8. natural Russian / age-appropriate tone;
9. multi-turn context consistency;
10. overall Tutor usefulness.

Scores stay in process memory until the local benchmark exits. Provider mapping
and totals are revealed only after all four labels have been scored.

## Hard boundaries

The benchmark is localhost-only and owner-authorized. Credentials stay
server-side. CI contains no provider secrets and makes zero live/paid calls.
Production PEIS writes remain off. Dialogue evidence is not written to disk.
Voice is a separate integration gate and cannot change the text ranking. Raw
learner audio persisted bytes remain zero.
