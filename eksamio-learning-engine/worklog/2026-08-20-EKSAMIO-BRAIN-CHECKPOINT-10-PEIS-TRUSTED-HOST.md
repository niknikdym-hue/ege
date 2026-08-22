# Eksamio Brain Checkpoint 10 — PEIS Trusted Host Identity

Date: 2026-08-20
Status: DURABLE PROJECT CHECKPOINT
Main at checkpoint start: `968945db6cf641c98ee5ae989272e0536856c02c`

## 1. Central milestone reached

`PEIS-TRUSTED-HOST-001` is merged.

The project now has a validated reference trusted-host identity boundary that fills the missing server-side identity handoff between the fail-open browser hook and the subject-neutral PEIS service bridge.

Validated chain:

`browser sends no trusted identity`
→ `trusted host verifies signed opaque token`
→ `shared persistence resolves identity_ref`
→ `HostIdentity`
→ `PEIS service bridge`
→ `EvidenceEvent / shared PEIS`

## 2. Reuse-first audit result

A fresh-main reuse audit was completed before implementation.

No existing repository-defined production auth/account/backend host was found.

No project application backend/package/serverless account system was available to reuse.

The following existing PEIS capabilities WERE reused:
- `PeisPersistenceStore.link_identity`;
- `PeisPersistenceStore.resolve_identity`;
- `HostIdentity` validation in the PEIS service bridge.

Therefore the new code is a reference trusted-host identity boundary, not a parallel account system.

## 3. Identity invariants proven

The browser does NOT own:
- learner_profile_id;
- anonymous_identity_ref;
- user_identity_ref;
- email identity;
- canonical academic history.

The browser-facing host token contains only:
- version;
- key id;
- opaque anonymous identity_ref;
- issued_at;
- expires_at.

It does NOT contain learner_profile_id, email, subject, mastery, semantics or EvidenceEvent data.

## 4. Integrity/security mechanics validated

Reference token:
- HMAC-SHA256;
- runtime-injected secret only;
- key-id/version aware;
- expiry checked;
- future issue-time skew checked;
- tamper detection checked;
- wrong key/wrong secret rejected.

Reference cookie projection:
- HttpOnly;
- Secure;
- SameSite=Lax;
- Path=/;
- bounded Max-Age.

No production secret is committed.

## 5. Anonymous → account continuity proven

A current-product-shaped Russian EvidenceEvent was persisted before account linking.

Then a trusted user identity ref was linked to the same learner through shared persistence.

Validated result:
- same learner_profile_id;
- same anonymous identity ref;
- new user identity ref points to same learner;
- existing EvidenceEvent unchanged;
- no evidence migration;
- no evidence duplication;
- identity reassignment to another learner rejected.

The learner profile is cross-subject; the same profile can be used by Russian and Mathematics.

## 6. Important non-claims

This checkpoint does NOT mean:
- production authentication exists;
- an account/login product exists;
- a backend is publicly deployed;
- production database/storage is selected;
- Tilda is wired to PEIS;
- real browser traffic is authorized;
- HMAC reference token is automatically the final production auth mechanism.

## 7. Next central bottleneck

Next gate:

`PEIS-DEPLOYMENT-SECURITY-001`

Before any public traffic is allowed, the project must explicitly choose and validate the production security/deployment envelope.

Required decisions include:
1. production runtime/hosting;
2. API hostname/origin strategy;
3. TLS termination;
4. production secret management and rotation;
5. production persistence/storage;
6. migration path from reference SQLite contract;
7. CORS and credential policy;
8. CSRF/replay considerations;
9. request/body limits;
10. rate limiting/abuse protection;
11. server-side identity issuance/verification;
12. structured logs/metrics/alerts;
13. data backup/recovery;
14. deploy/rollback strategy;
15. environment separation;
16. retention/deletion/privacy controls;
17. rollout feature flag/kill switch;
18. failure mode that preserves current trainer usability.

## 8. Production rollout prohibition

Do not wire the current public trainer to any endpoint until `PEIS-DEPLOYMENT-SECURITY-001` has an explicit PASS/ADMIT decision.

A reference HTTP service or reference cookie is not equivalent to a production security boundary.

## 9. Deployment gate principle

Production architecture should minimize new moving parts and reuse infrastructure already legitimately available to the project where that does not compromise correctness/security.

Provider selection must be based on current verified capabilities rather than remembered product names or stale assumptions.

If the production hosting choice introduces subject-specific learner state, browser-owned identity, hidden local mastery or uncontrolled public endpoints, reject it.

## 10. Current architecture sequence

Merged and validated:

`verified subject truth`
→ `semantic identity`
→ `EvidenceEvent`
→ `shared persistence`
→ `shared PEIS inference`
→ `NBA`
→ `current-product-shaped sensor`
→ `subject-neutral service boundary`
→ `fail-open browser hook`
→ `trusted host identity boundary`

Next:

`production deployment/security envelope`
→ `controlled production rollout gate`
→ `real learner evidence telemetry`
→ `measured intervention outcomes`
→ iterative PEIS expansion.
