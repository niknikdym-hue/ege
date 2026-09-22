# Owner Control v2 — Astra REWORK free-closure evidence
Date: 2026-09-22
Status: FREE FIXES IMPLEMENTED / PAID SMOKE NOT YET AUTHORIZED BY GATE

## Astra audit
- Brain audit run: 35689818626
- Decision: REWORK
- One Astra call only; Codex calls: 0
- Estimated actual Astra cost: $0.111018
- Automatic retries: disabled

## Frozen starting authority
- EGE main at audit: 7f090536cd7debc11d6304a7c58adb748c0653f3
- Brain main at audit: 96e452c6659ca32e6ec1658324c3800281800932

## Exact prior green evidence requested by Astra
- Brain CI run 34706765662: repository niknikdym-hue/eksamio-brain; workflow .github/workflows/ci.yml; branch main; head 96e452c6659ca32e6ec1658324c3800281800932; conclusion SUCCESS.
- Brain deploy run 34706765661: repository niknikdym-hue/eksamio-brain; workflow .github/workflows/yandex-brain-deploy.yml; branch main; head 96e452c6659ca32e6ec1658324c3800281800932; conclusion SUCCESS.
- One-click Owner Control deploy run 34635032213: repository niknikdym-hue/eksamio-brain; workflow .github/workflows/yandex-brain-deploy.yml; branch main; head e57e018eea67561caf15798ae976d9a3ff9dc6cf; conclusion SUCCESS.
- Historical API-Codex run 34704716581: repository niknikdym-hue/ege; workflow .github/workflows/owner-agent-task-v2.yml; branch main; head 40bebe89e223d074483457189f9b4934854cbf8b; conclusion FAILURE after provider high-demand reconnects. It is credential/execution-entry evidence only, not current readiness evidence.

## Free fixes after Astra REWORK
1. Provider API key isolation
   - Real OPENAI_API_KEY is consumed only by the authenticated budget proxy.
   - Codex receives only a random loopback client token.
   - Budget proxy rejects missing/wrong client authorization before upstream forwarding.
2. Hard budget enforcement
   - Budget exhaustion returns 402 before upstream forwarding.
   - Loopback upstream override exists only in explicit test mode.
3. No internal Codex retries
   - Codex CLI pinned to 0.154.0.
   - Custom provider has request_max_retries=0 and stream_max_retries=0.
   - Free failing-provider mock proves exactly one provider request and zero real OpenAI calls.
4. Privilege boundary
   - Codex runs after sudo removal under setpriv with no_new_privs, cleared supplementary groups and empty capability sets.
   - Workspace-write sandbox remains explicit.
5. Prompt safety
   - Full generated prompt is passed through stdin with codex exec -, not interpolated into a shell command.
6. Parallel/duplicate dispatch
   - Brain tests explicitly reject duplicate task IDs and already-active Owner Control work before dispatch.
7. Source-of-truth corrections
   - A1.2 is CODE_READY, not DONE.
   - A1.3 and A1.4 are INTEGRATION_PENDING, not DONE.
   - Existing locked UI is unchanged.

## Exact free acceptance runs
- EGE Owner Control v2 free safety proof run 35691044228: SUCCESS on d3870c021117ec0c86da879ff7314b6cd4101195.
- EGE budget proxy auth/exhaustion proof run 35690989938: SUCCESS on e5568da8b5878b1f45ce87aab8ed64a1f0a35ce6.
- EGE retry-zero proof run 35690791151: SUCCESS on d801eabe0a98d54406613b46faec615643472f7f; FREE_CODEX_PROVIDER_REQUESTS=1, REQUEST_MAX_RETRIES=0, STREAM_MAX_RETRIES=0, REAL_OPENAI_CALLS=0.
- EGE Owner Control board/sync run 35690633167: SUCCESS on d563c86125aa48feff087717dc50eda881891fb3.
- Brain PR #47 CI run 35690807672: SUCCESS on 7ab5e7df3a08282aced7d4c8c0499cd413858428.

## Remaining sequence
1. Merge free-only EGE and Brain safety changes after final exact-head checks.
2. Create a GitHub-backed immutable smoke manifest from the resulting EGE main SHA.
3. Run exactly one docs-only API-Codex smoke with Luna, one provider request maximum, no Astra phase, no retry/rerun, no merge/deploy/production mutation.
4. Only after smoke PASS may normal Eksamio development be routed through Owner Control.
