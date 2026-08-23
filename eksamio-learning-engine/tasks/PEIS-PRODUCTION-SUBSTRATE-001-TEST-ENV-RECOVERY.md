# PEIS-PRODUCTION-SUBSTRATE-001 — TEST ENVIRONMENT RECOVERY

**Status:** CENTRAL BRAIN EXECUTION RECOVERY / BOUNDED AUTHORITY
**Date:** 2026-08-23
**Applies to:** `PEIS-PRODUCTION-SUBSTRATE-001`
**Trigger blocker:** `BLOCKED_PEIS_TEST_ENVIRONMENT`

## WHY

The Codex executor proved the existing reference regressions locally but its execution environment has no Docker/Podman/PostgreSQL binaries, so it cannot truthfully satisfy the required PostgreSQL migration/restart/transaction or container health/readiness/kill-switch evidence.

This is an execution-environment blocker only. It does not justify changing the PEIS architecture or reducing acceptance requirements.

## RECOVERY DECISION

Use the repository's existing GitHub Actions execution pattern as the temporary test environment.

For this task only, Codex is explicitly allowed to create and use:

- `.github/workflows/_tmp-peis-production-substrate-001.yml`

The workflow must run on a Linux GitHub-hosted runner and provide a real PostgreSQL service container plus Docker-based image/runtime checks.

No Yandex credentials or production cloud resources are permitted or required.

## REQUIRED CI EVIDENCE

The temporary workflow must prove the same gates already required by `PEIS-PRODUCTION-SUBSTRATE-001`, including:

1. existing persistence/service/trusted-host/browser-hook regressions;
2. empty-DB migration;
3. PostgreSQL append/replay/idempotency/conflict behavior;
4. identity link/resolve and anonymous-to-account continuity;
5. recommendation/outcome and materialized snapshot persistence;
6. transaction rollback with no partial canonical write;
7. append-only protections;
8. process/repository-backed restart persistence;
9. clean Docker image build;
10. container start against PostgreSQL;
11. `/healthz` and `/readyz` behavior with DB available;
12. non-ready behavior with DB unavailable;
13. request/body limits;
14. kill switch prevents writes with no partial write;
15. no secret values in committed fixtures or emitted test evidence;
16. browser-hook fail-open regression after service unavailability.

## WORKFLOW LIFECYCLE

The workflow is temporary validation infrastructure, not a new permanent CI framework.

Required sequence:

1. add workflow on the implementation branch;
2. run real CI and capture run/job IDs and results;
3. persist durable validation/result evidence under the task's allowed PEIS production-substrate area;
4. remove `_tmp-peis-production-substrate-001.yml` before the final implementation PR is accepted, unless Central Brain explicitly decides a permanent workflow is justified by new evidence.

The successful historical workflow run remains valid evidence even after the temporary workflow file is removed from the final diff.

## SCOPE

All original `PEIS-PRODUCTION-SUBSTRATE-001` architecture, security, allowed/forbidden product paths, stop conditions and final statuses remain in force.

This recovery adds only one temporary allowed workflow path and does not authorize:

- public traffic;
- Tilda changes;
- demo/source changes;
- Yandex resources;
- auth/payment/Tutor implementation;
- learner audio persistence;
- changes to canonical PEIS contracts.

## NEXT EXECUTION

Codex should resume the same task from fresh current `main`, reuse the existing branch name if safe, implement the production substrate, validate through the temporary GitHub Actions environment, open one bounded implementation PR, and do not merge.

Success remains exactly:

`PEIS_PRODUCTION_SUBSTRATE_READY_FOR_YANDEX_STAGING`

Return `BLOCKED_PEIS_TEST_ENVIRONMENT` again only if the GitHub Actions execution path itself cannot provide the required real PostgreSQL/container evidence, with the exact failed capability.