# SEP1-RU-PEIS-001 — Validation Record

Status: `RUSSIAN_PEIS_VERTICAL_SLICE_READY_FOR_BRAIN_ACCEPTANCE`

Baseline main: `1ca4e771fc712ed68aca9c0ba2928d631e080cdf`
Accepted implementation head for the executable gate: `f957612f1b05a8d6812a3c328c078ad0e4d9e6e9`
GitHub Actions run: `32998706934`
Job: `postgres-vertical-slice`
Result: `PASS`

## What is proven

- The current Russian Exceptions manifest is the reviewed 121-card checkpoint.
- The merged mapping remains exactly 121 integration-ready rows: 116 `EXACT`, 5 `PARTIAL_COMPOSITE`, 0 blocked, 88 represented exception IDs.
- A real reviewed practice item (`ex-practice-alt-sochetat-001`) is admitted through a server-side Russian adapter into the existing subject-neutral `PeisServiceBridge`.
- Browser/product input cannot assert canonical score, correctness, semantic mapping, learner identity, mastery/readiness or next-best-action truth.
- The deterministic answer is evaluated server-side.
- The resulting EvidenceEvent uses the existing schema and the already merged semantic mapping.
- The event persists through the existing PostgreSQL production substrate.
- Shared PEIS recomputation runs and produces a persisted next-best action.
- Identical replay is `ALREADY_APPLIED` with one canonical event and one persisted recommendation for the fixture learner.
- Changed educational payload under the same stable event identity is rejected as an integrity conflict.
- Existing trusted-host identity boundary passes.
- Existing fail-open browser-hook validation passes, preserving current learner usability when PEIS is unavailable.
- The production-substrate Docker image builds with the bounded admitted Russian adapter/source inputs.
- Scope guard passes: no Tilda/frozen Russian demo/scorer, Mathematics, Physics or new semantic-ID admission changes.
- Public traffic remains OFF and network writes remain disabled by default.
- No real learner PII or production secret is present in test fixtures.

## Exact gate results

Run `32998706934`, head `f957612f1b05a8d6812a3c328c078ad0e4d9e6e9`:

1. Compile bounded implementation — PASS
2. Existing shared service bridge — PASS
3. Existing trusted-host boundary — PASS
4. Existing fail-open browser hook — PASS
5. Existing PostgreSQL production substrate — PASS
6. Russian Exceptions mapped attempt -> evidence -> persistence -> recompute -> NBA — PASS
7. Production-substrate Docker build — PASS
8. Scope guard / `git diff --check` — PASS

Two earlier red runs were gate-fixture wiring defects, not accepted product failures: the first omitted the existing trusted-host validator's synthetic test secret; the second omitted the existing PostgreSQL validator's legacy `PEIS_TEST_POSTGRES_DSN` environment name. Both were repaired without weakening any product/security invariant before the accepted run above.

## Boundary

This proves the first production-shaped Russian shared-PEIS vertical slice. It does not claim public production traffic, all 121 cards routed through a deployed edge, identity-provider completion, payments, Tutor readiness or Yandex production admission. Those remain separate September 1 gates.
