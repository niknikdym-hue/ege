# Physics 2025 v1.4 — Tilda staging selector gate

Date: 2026-08-22  
Requested baseline main SHA: `e9dfffae7275be9de829d1c5a5668e7715d8261f`

## Result

`FINAL_STATUS=BLOCKED_TILDA_COMPATIBILITY`

No private/staging deployment, runtime test, or production publication was performed.

## Verified accepted source

- accepted source directory: `ege-fizika-demoversiya-2025-v1.4-TILDA-HQ-SOURCE`
- baseline tree object: `8dab3ab2820d8d64c879af852c131e7ed0ea0b9f`
- build hash: `2780a729967e70355a8ae52e726c67abe8597dff3ce2d5b0c55da635791f2e13`
- ZIP hash: `21a6fdeffa1696b5f134ce50eab10dd5b279c82764bfe5165ae3c50ab330c80d`

The external handoff copy was byte-identical to the accepted source:

```text
source:  e60eba903b8dbf378817d2c07cf05a046231350e795d27ee55fb4e70ce2a9eb6
staging: e60eba903b8dbf378817d2c07cf05a046231350e795d27ee55fb4e70ce2a9eb6
diff -qr: IDENTICAL
```

Exact external copy path:

`/Users/elenadymova/Documents/New project/exam-platform-tilda/tilda-ready/pages/ege-fizika-demoversiya-2025-v1.4`

## Selector proof failure

The required chain cannot be proven from the available control plane:

`accepted main build -> external tilda-ready copy -> [missing selector/deployment flow] -> [unknown private/staging target]`

- Baseline main contains **0** paths under `tilda-ready/pages/ege-fizika-demoversiya-2025-v1.4/`; the `tilda-ready` copy is outside the repository.
- Baseline `.github/workflows/**` contains **0** references to `ege-fizika-demoversiya-2025-v1.4`.
- Searched deployment/config/script candidates in the repository workflows and the external Tilda workspace contain **0** references to `ege-fizika-demoversiya-2025-v1.4`.
- The only v1.4 installation instruction is `tilda-ready/pages/ege-fizika-demoversiya-2025-v1.4/00-README-TILDA.txt`: manually paste `ege-fizika-demoversiya-2025-HEAD.txt`, then create and paste 48 ordered T123 blocks. It contains no private/staging target identifier, selector, run/workflow ID, or `production_publish=false` control.

Therefore a real staging upload could not be attributed unambiguously to v1.4 or shown to avoid v1.3, Physics 2026/v3/v3-1-fixed, or any other directory. Performing manual UI actions would require inventing a deployment flow/target and violates the requested gate.

## Safety outcome

- `production_publish=false` (no publication action invoked)
- accepted Physics 2025 content unchanged
- no Tilda/global code changed
- no staging URL, target identifier, deployment command, or deployment run exists

## Required unblocking input

Provide an existing deployment selector/config/script (or a verified private Tilda target plus its accepted non-production deployment procedure) that binds this exact external directory to a staging-only page. Re-run Phase A before any deployment.
