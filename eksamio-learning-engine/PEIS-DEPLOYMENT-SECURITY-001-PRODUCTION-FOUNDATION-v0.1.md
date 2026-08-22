# PEIS-DEPLOYMENT-SECURITY-001 — Production Foundation v0.1

**Status:** CENTRAL BRAIN IMPLEMENTATION-READY PLAN  
**Date:** 2026-08-23  
**Baseline:** `99cf2dbfb7600af3976914a04334722efb82e8bb`  
**Gate:** `PEIS-DEPLOYMENT-SECURITY-001`  
**Production target:** Russia / Yandex Cloud, portable architecture.

## 1. WHY_NOW

The validated PEIS chain already reaches a trusted-host identity boundary. Public browser -> PEIS traffic remains prohibited until the production deployment/security envelope is chosen, implemented, and validated.

This is the highest-value central dependency because auth, real learner telemetry, AI Tutor, payments, and paid Pro all depend on a production-safe service/persistence boundary.

## 2. EXPECTED_UNLOCK

A PASS of this foundation does **not** launch Pro and does not connect public traffic automatically. It unlocks a controlled staging/production-candidate PEIS service that can safely support the next gates:

1. passwordless account/auth integration;
2. anonymous -> account continuity against production persistence;
3. controlled real learner evidence telemetry;
4. Tutor/provider integration behind Eksamio infrastructure;
5. later payment/entitlement integration.

## 3. Minimal production architecture

Use the smallest mature Yandex Cloud contour that preserves portability and avoids managing VMs:

`browser/app`
-> `api.eksamio.ru` (production candidate FQDN)
-> `Yandex API Gateway`
-> `private Yandex Serverless Container`
-> `existing subject-neutral PEIS service/application layer`
-> `Managed PostgreSQL`

Supporting services:

- Yandex Lockbox for runtime secrets;
- Certificate Manager + API Gateway custom domain for TLS;
- Yandex Monitoring for metrics/alerts;
- Audit Trails for cloud-resource audit events;
- existing GitHub source of truth and reproducible deployment configuration.

The application remains a normal containerized service with standard PostgreSQL semantics. No canonical learner/PEIS state may depend on a Yandex-proprietary database representation or proprietary provider conversation state.

## 4. Why these components

### API Gateway

Use as the only public API edge for the first production contour.

Responsibilities:

- HTTPS/custom domain;
- explicit CORS policy;
- request/response validation where useful;
- coarse API rate limiting;
- integration with private Serverless Container;
- controlled canary/rollback-capable gateway revisions/spec updates.

Do not expose the container publicly.

### Private Serverless Container

Run the existing subject-neutral PEIS service as a portable Docker image.

Requirements:

- private invocation only;
- API Gateway service account has container-invoker permission;
- no hard-coded secrets;
- stateless application process apart from external persistence;
- health endpoint with no learner/private data;
- bounded request timeout/body handling;
- deterministic image/version identifier in deployment evidence.

### Managed PostgreSQL

Production persistence replaces reference SQLite while preserving existing persistence/service contracts.

Requirements:

- TLS connection;
- least-privilege DB user;
- schema migrations tracked in GitHub;
- automatic backups/PITR enabled;
- restore test required before production admission;
- no subject-specific duplicate learner database.

SQLite remains reference/local-test infrastructure only.

### Lockbox

Store all production secrets outside Git:

- DB credentials;
- host/session signing secrets or successor auth secrets;
- provider API keys when later admitted;
- webhook/payment secrets when later admitted.

Secret rotation must use versioned secrets and must not require code changes.

## 5. Gate mapping — 18 required deployment/security decisions

1. **Production runtime/hosting** — Serverless Containers.
2. **API hostname/origin strategy** — planned `api.eksamio.ru`; staging may use provider hostname until DNS/certificate is validated. Public production requires project-controlled custom domain.
3. **TLS termination** — API Gateway/custom domain + Certificate Manager; no plaintext public endpoint.
4. **Secret management/rotation** — Lockbox, service-account least privilege, version rotation.
5. **Production persistence** — Managed PostgreSQL.
6. **SQLite migration path** — explicit schema compatibility/migration layer and production migration test; no direct file-copy migration assumption.
7. **CORS/credentials** — exact allowlist only; no `*` with credentials. Allow only approved Eksamio web origins. Preflight tested.
8. **CSRF/replay** — state-changing authenticated requests require server-side origin/CSRF protection appropriate to the final passwordless session mechanism; trusted-host tokens remain short-lived/validated; idempotency/replay protection where writes can be retried.
9. **Request/body limits** — API/gateway validation plus application hard limits; reject oversized/malformed payloads before PEIS writes.
10. **Rate limiting/abuse** — API Gateway rate limit for initial rollout; add Smart Web Security/advanced protection only if the threat/load model requires it rather than by default.
11. **Server-side identity issuance/verification** — only trusted server contour may resolve canonical learner identity. Browser never supplies authoritative learner_profile_id/mastery.
12. **Logs/metrics/alerts** — structured application logs with no secrets/audio; service/error/latency/write-failure metrics; Monitoring alarms for availability/error-rate/DB failures.
13. **Backup/recovery** — PostgreSQL automated backups/PITR plus a documented restore drill before PASS.
14. **Deploy/rollback** — immutable container revisions/images; deploy new revision; smoke test; rollback to previous known-good revision/spec without DB destructive rollback.
15. **Environment separation** — separate staging and production resource/config/secrets; no production secret in staging; distinct DBs.
16. **Retention/deletion/privacy** — learner data retention/deletion is explicit and separate from logs; logs must minimize identifiers; learner audio persistence remains absolutely forbidden.
17. **Feature flag/kill switch** — public PEIS write path remains OFF by default until gate PASS; runtime kill switch disables PEIS network integration while current demo/trainer remains usable.
18. **Failure mode** — browser integration fails open to the existing deterministic demo/trainer experience; network/PEIS failure must not corrupt or block current trainer functionality.

## 6. Security invariants

- learner audio is never persisted;
- no browser-owned canonical identity;
- no secrets in repository, browser bundle, logs, or error responses;
- no direct browser -> PostgreSQL/container/provider path;
- provider-neutral PEIS state;
- official/subject truth is not stored as AI-generated canonical data;
- production service account permissions are least privilege;
- staging cannot write production DB;
- public rollout remains disabled until explicit PASS.

## 7. Portability requirements

Yandex Cloud is the primary production host, not the canonical architecture.

The following must remain portable:

- application container;
- HTTP API contract;
- PostgreSQL schema/migrations;
- PEIS learner/evidence/state contracts;
- identity abstraction;
- AI/speech provider adapters;
- payment adapter.

Provider-specific infrastructure belongs only to deployment/IaC/config layers.

## 8. Minimal implementation delta for Codex

Codex should **not** build the full Pro app, auth, AI Tutor, or payment system in this task.

First implementation slice should add only what is needed to prove the production foundation:

1. deployment/IaC/config for staging contour;
2. containerization of the existing PEIS service boundary if not already containerized;
3. PostgreSQL persistence adapter/migrations preserving current contracts;
4. Lockbox secret wiring;
5. API Gateway spec with exact CORS/rate/request constraints;
6. health/readiness endpoints;
7. environment separation and feature flag/kill switch;
8. deployment/rollback scripts or reproducible commands;
9. automated integration/security tests;
10. durable result artifact with real staging evidence.

Do not connect public Tilda/demo traffic in this slice.

## 9. Acceptance evidence

A PASS requires evidence for all of the following:

### Build/reproducibility

- clean build from current GitHub branch;
- container image version/digest recorded;
- migration files deterministic/tracked;
- no untracked production-critical config.

### Network boundary

- only API Gateway public;
- container direct unauthenticated invocation denied;
- TLS endpoint works;
- disallowed CORS origin rejected;
- approved staging origin accepted;
- rate limit/oversize/malformed request behavior tested.

### Secrets

- repository secret scan PASS;
- runtime uses Lockbox/service-account access;
- secret version rotation test does not require source change.

### Persistence

- PostgreSQL adapter passes existing persistence contract tests;
- anonymous EvidenceEvent survives restart;
- anonymous -> account identity link preserves same learner/evidence semantics;
- migration test from a representative reference state passes without duplication;
- backup restore drill passes.

### Failure/fail-open

- API unavailable -> client hook does not break deterministic trainer/demo;
- DB unavailable -> no false success/partial canonical write;
- kill switch disables PEIS integration without breaking existing trainer;
- rollback to previous known-good service revision demonstrated.

### Observability/privacy

- errors/latency/write failures observable;
- alert path tested;
- logs contain no secrets;
- logs contain no learner audio;
- no audio storage resource/path is introduced.

## 10. STOP CONDITIONS

Stop and return to Central Brain if implementation requires any of the following:

- changing shared PEIS semantics/contracts merely to fit Yandex services;
- introducing subject-specific learner persistence;
- making Serverless Container public to simplify integration;
- storing learner audio;
- putting secrets in Git/environment files committed to repo;
- connecting live Tilda/public traffic before gate PASS;
- adding a new infrastructure framework/CI system when existing repo workflow can deploy/test the bounded contour;
- fundamental auth/product redesign not required by this foundation.

## 11. Allowed final statuses

- `PEIS_DEPLOYMENT_SECURITY_FOUNDATION_PASS`
- `PEIS_DEPLOYMENT_SECURITY_FOUNDATION_PARTIAL`
- `PEIS_DEPLOYMENT_SECURITY_FOUNDATION_BLOCKED_<CONCRETE_REASON>`

Only PASS unlocks controlled production-rollout admission work.

## 12. Current official Yandex Cloud capability references verified 2026-08-23

- Serverless Containers: https://yandex.cloud/en/docs/serverless-containers/
- API Gateway: https://yandex.cloud/en/docs/api-gateway/
- API Gateway -> Serverless Containers integration: https://yandex.cloud/en/docs/api-gateway/concepts/extensions/containers
- API Gateway CORS: https://yandex.cloud/en/docs/api-gateway/concepts/extensions/cors
- API Gateway custom domains: https://yandex.cloud/en/docs/api-gateway/operations/api-gw-domains
- Managed PostgreSQL: https://yandex.cloud/en/docs/managed-postgresql/
- PostgreSQL backups: https://yandex.cloud/en/docs/managed-postgresql/concepts/backup
- Lockbox: https://yandex.cloud/en/docs/lockbox/
- Monitoring alerts: https://yandex.cloud/en/docs/monitoring/concepts/alerting/alert
- Audit Trails: https://yandex.cloud/en/docs/audit-trails/

This file chooses a reversible technical production contour under already approved owner decisions. It does not claim any resource has been deployed yet and does not constitute a production PASS by itself.
