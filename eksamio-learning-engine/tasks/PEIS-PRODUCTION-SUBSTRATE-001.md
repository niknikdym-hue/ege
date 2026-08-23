# PEIS-PRODUCTION-SUBSTRATE-001

**Status:** IMPLEMENTATION TASK / CENTRAL P0  
**Date:** 2026-08-23  
**Baseline:** `f51e4fa7d6d3e45136df73cc053f91d14840b220`  
**Parent gate:** `PEIS-DEPLOYMENT-SECURITY-001`

## WHY_NOW

The current shared PEIS chain already has executable reference components for persistence, the subject-neutral service bridge, the fail-open browser hook, and the trusted-host identity boundary. Public browser -> PEIS traffic remains prohibited because these components are still reference/local infrastructure.

The smallest useful production step is therefore **not** a new backend and not a full Yandex Cloud deployment. It is to make the existing PEIS application layer portable and production-shaped locally, with PostgreSQL compatibility and container/integration evidence. This separates application hardening from cloud provisioning and prevents one oversized infrastructure PR.

## ACTIVE_BLOCKER_OR_MILESTONE

`PEIS-DEPLOYMENT-SECURITY-001`

This task closes the application/runtime/persistence substrate sub-gap only.

It does NOT close the whole deployment-security gate and does NOT authorize public traffic.

## DEPENDENCY_IN

Already merged and must be reused rather than replaced:

- `peis-persistence-reference/peis_persistence.py` — `PeisPersistenceStore`, append-only evidence, idempotency, identity links, recommendations/outcomes, materialized snapshots; SQLite is explicitly local/CI reference only;
- `peis-service-bridge-reference/peis_service_bridge.py` — `PeisServiceBridge`, `HostIdentity`, registered server adapters, `/healthz`, bounded checked-card request transport;
- `peis-browser-hook-reference/peis_browser_hook.js` — fail-open browser integration contract;
- `peis-trusted-host-reference/peis_trusted_host.py` — reference trusted-host identity verification/linking;
- shared Evidence/Mastery/Readiness/Retention/NBA contracts and current kernel;
- `PEIS-DEPLOYMENT-SECURITY-001-PRODUCTION-FOUNDATION-v0.1.md`.

Do not create parallel learner state, parallel identity, or a second service bridge.

## MINIMAL_DELTA

Create a portable production-substrate layer around the existing PEIS contracts that proves all of the following locally/CI:

1. the service can run as a containerized application without changing subject semantics;
2. the persistence contract works against PostgreSQL, not only SQLite;
3. schema/migrations are tracked and deterministic;
4. runtime configuration comes from environment/secret references, never hard-coded secrets;
5. health and readiness are distinct: health = process alive; readiness = required persistence/dependencies usable;
6. a server-side PEIS kill switch can disable network writes without breaking the deterministic/base product;
7. all existing reference behavior/regression tests remain green;
8. PostgreSQL integration tests prove append/idempotency/identity/snapshot behavior and anonymous -> account continuity;
9. no public Tilda/demo traffic is connected.

## EXPECTED_UNLOCK

PASS makes the existing PEIS application deployable as a portable Docker image onto the already chosen Yandex staging contour.

The immediate next gate becomes:

`PEIS-YANDEX-STAGING-001`

which can then focus only on cloud resources and real staging evidence:

`API Gateway -> private Serverless Container -> Managed PostgreSQL -> Lockbox -> Monitoring/Audit`

without simultaneously redesigning application persistence/runtime.

PASS also provides the production-shaped persistence boundary required before passwordless auth and real learner telemetry can be connected.

## EXECUTOR

**Codex**.

Reason: this task requires multi-file engineering, a local PostgreSQL runtime/container, migrations, regression tests, integration tests, container build/smoke, and iterative debugging. Central Brain owns scope/acceptance; Codex owns execution.

## ALLOWED PATHS

Prefer add-only production-substrate code under a new explicit path such as:

- `eksamio-learning-engine/peis-production-substrate/`

Existing reference modules may be changed only when a small compatibility abstraction is genuinely necessary and all existing reference validators remain green:

- `eksamio-learning-engine/peis-persistence-reference/`
- `eksamio-learning-engine/peis-service-bridge-reference/`
- `eksamio-learning-engine/peis-trusted-host-reference/`

This task contract may be updated with exact result pointers if useful.

## FORBIDDEN PATHS / SCOPE

Do not modify:

- published/frozen demos or trainers;
- Tilda blocks/pages;
- Physics/Russian/Mathematics source authority;
- canonical subject answers/scoring;
- shared PEIS semantic/mastery/readiness/retention/NBA contracts unless a concrete incompatibility is proven and returned as a blocker;
- payment code;
- AI Tutor/provider code;
- voice/audio storage of any kind;
- Yandex production resources or live DNS;
- public browser -> PEIS wiring.

Do not build passwordless auth in this task.

Do not replace the current trusted-host reference with a new account system.

## REQUIRED DESIGN

### Persistence interface

Preserve the behavior currently consumed by `PeisServiceBridge`, including at minimum:

- `append_event`;
- `raw_event`;
- `list_events`;
- `link_identity`;
- `resolve_identity`;
- `append_recommendation`;
- recommendation outcomes;
- `recompute_snapshot` / snapshot loading;
- current integrity/idempotency semantics.

A clean persistence abstraction may be introduced if necessary, but existing callers should not become PostgreSQL-specific.

### PostgreSQL

Use standard PostgreSQL semantics and a maintained Python driver.

Requirements:

- TLS-capable DSN/config shape;
- least-privilege-compatible application user model;
- explicit tracked migrations/schema;
- unique constraints preserving event/idempotency semantics;
- transactions preserving append + semantic targets + identity-link atomicity;
- append-only protection for canonical evidence/recommendation history;
- deterministic ordering semantics equivalent to the reference behavior;
- no SQLite file-copy migration assumption.

### Runtime/container

Provide a minimal container entry point for the existing subject-neutral PEIS service.

Do not introduce a heavy web framework unless the existing standard-library handler is demonstrably insufficient for the required production-shaped health/readiness/config behavior. Prefer minimal dependencies.

Required endpoints/behavior:

- `/healthz` — process health, no learner data;
- `/readyz` — verifies required persistence connectivity/migration state without leaking secrets;
- checked-card service boundary remains server-owned and bounded;
- generic 5xx responses must not leak secrets/private learner data.

### Configuration / secrets

All environment-specific values are runtime configuration:

- database DSN/host/database/user secret reference;
- environment name;
- PEIS network-write enable/kill switch;
- trusted-host signing secret or later secret reference where relevant.

No real secret may be committed.

Provide `.env.example` or equivalent only with obviously non-secret placeholders.

### Kill switch / fail-open

The server must expose a configuration-controlled mode where PEIS checked-card writes are disabled safely.

When disabled:

- health may remain healthy;
- readiness semantics must be explicit;
- mutation endpoint must return a stable non-success status/code that the existing fail-open browser contract can treat as PEIS unavailable;
- no partial learner write occurs.

Do not modify the public product to call this service yet.

## REQUIRED TESTS

### Existing regressions

Run all directly affected existing validators, including at minimum:

- persistence reference validator;
- service bridge validator;
- trusted-host validator;
- browser-hook validator;
- any closed-loop/current-product sensor regression required by imports/contracts.

### PostgreSQL integration

Use an ephemeral/local PostgreSQL container or equivalent CI service.

Prove at minimum:

1. schema migration from empty DB;
2. event append;
3. exact replay -> already applied;
4. idempotency-key replay -> already applied;
5. conflicting replay rejected;
6. semantic target persistence;
7. event ordering/server sequence behavior preserved;
8. identity link + resolve;
9. one identity cannot be reassigned to another learner;
10. anonymous evidence exists before account link;
11. later user identity links to the same learner with no evidence migration/duplication;
12. recommendation + outcome persistence;
13. materialized snapshot write/read;
14. transaction rollback leaves no partial canonical write;
15. append-only protections hold;
16. process restart preserves data.

### Container/runtime

Prove:

- clean container build;
- container starts with test config;
- `/healthz` PASS;
- `/readyz` PASS with PostgreSQL available;
- `/readyz` FAIL/non-ready when required DB unavailable;
- body/request limits preserved;
- no secret values in response/log fixtures;
- kill switch prevents writes;
- after kill switch/offline failure the browser-hook regression still proves fail-open behavior.

## ACCEPTANCE_EVIDENCE

Required durable result must state:

- baseline/main used;
- branch + commit + PR;
- files changed;
- container image/build identifier or deterministic local image digest where available;
- migration list/version;
- PostgreSQL driver/dependency choice;
- exact tests/commands and outcomes;
- existing reference regression results;
- PostgreSQL integration test results;
- health/readiness/kill-switch smoke results;
- `PUBLIC_TRAFFIC_CONNECTED=false`;
- `TILDA_CHANGED=false`;
- `PRODUCTION_CLOUD_RESOURCES_CREATED=false`;
- `LEARNER_AUDIO_PERSISTED=false`;
- unresolved blockers.

## STOP_CONDITIONS

STOP and return to Central Brain instead of broadening scope if:

- preserving current persistence semantics requires changing canonical Evidence/Mastery/Readiness/Retention/NBA contracts;
- a PostgreSQL adapter exposes a hidden subject-specific learner model;
- the existing service boundary cannot be containerized without a major framework rewrite;
- cloud credentials/resources become necessary to prove this local substrate;
- a task requires production auth/payment/AI-provider implementation;
- a real ambiguity affects privacy/security or canonical learner identity.

## FINAL_STATUS

Success only:

`PEIS_PRODUCTION_SUBSTRATE_READY_FOR_YANDEX_STAGING`

Otherwise one exact blocker, for example:

- `BLOCKED_PEIS_POSTGRES_CONTRACT_INCOMPATIBILITY`
- `BLOCKED_PEIS_RUNTIME_BOUNDARY`
- `BLOCKED_PEIS_IDENTITY_SECURITY`
- `BLOCKED_PEIS_TEST_ENVIRONMENT`

No public rollout and no claim that `PEIS-DEPLOYMENT-SECURITY-001` is fully PASS after this task alone.
