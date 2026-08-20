# PEIS-TRUSTED-HOST-001

## Purpose

Validate a subject-neutral trusted-host identity boundary between the already merged browser hook/service bridge and the shared PEIS persistence identity links.

This task exists because the browser hook intentionally sends no trusted learner identity.

## Reuse decision

A fresh-main reuse audit was performed before implementation.

No reusable project auth/account/backend host was found in the repository tree:
- no package.json / application backend package;
- no requirements.txt / pyproject.toml backend package;
- no Vercel/Netlify/Cloudflare/serverless function tree;
- no OAuth/JWT/account/sign-in application layer;
- no existing trusted cookie/session resolver.

GitHub code search was additionally treated as non-authoritative because the index did not yet return some newly merged PEIS literals. The decision is therefore based on the actual recursive `main` tree, not search alone.

The shared `PeisPersistenceStore.link_identity/resolve_identity` functions ARE reusable and must remain the identity-link source of truth for this reference gate.

## Architectural position

Validated sequence before this task:

`browser product facts`
→ `fail-open browser hook`
→ `subject-neutral PEIS service bridge`
→ `HostIdentity required`

This task fills only:

`trusted host token/cookie`
→ `server-side identity verification`
→ `shared persistence identity resolution/linking`
→ `HostIdentity`

It must NOT become a new account system or learner-state engine.

## Scope

Add-only reference artifacts under:

`eksamio-learning-engine/peis-trusted-host-reference/`

plus this task contract.

Do not modify:
- current Russian trainer runtime/Tilda;
- current scoring/localStorage;
- browser hook contract;
- shared EvidenceEvent/mastery/readiness/retention/NBA contracts;
- mathematics or physics lanes.

## Identity model for the reference gate

### Anonymous host identity

The trusted host issues an opaque anonymous identity reference such as:

`anon:<random opaque id>`

and links it through shared persistence to one cross-subject `learner_profile_id`.

The browser must not choose either value.

### Signed host token

The reference host token is integrity protected with HMAC-SHA256 using a secret supplied only at runtime/test time.

The token may contain only the minimum host claims needed for verification, including:
- token version;
- key id;
- opaque identity_ref;
- issued_at;
- expires_at.

It must NOT contain:
- learner_profile_id;
- email;
- subject;
- mastery/readiness/retention/NBA;
- semantic identity;
- academic evidence.

After signature and expiry verification, the host resolves `identity_ref` through the shared persistence store to obtain `learner_profile_id`.

### Cookie projection

The reference cookie serializer must describe a cookie with:
- HttpOnly;
- Secure;
- SameSite=Lax;
- Path=/;
- Max-Age derived from host policy.

This is a reference security contract, not a production cookie/domain decision.

## Anonymous → account continuity

Later account identity linking must use shared persistence:

`store.link_identity(user_identity_ref, existing_learner_profile_id, identity_kind="USER")`

No evidence rewrite or learner-profile migration is allowed.

The same `learner_profile_id` must remain valid across subjects.

Email is never an academic-history identity ref.

## Required negative gates

The validator must reject:
- missing token;
- malformed token;
- tampered payload;
- tampered signature;
- expired token;
- token issued too far in the future;
- unknown key id;
- wrong signing secret;
- email-like identity ref;
- browser-supplied learner_profile_id;
- browser-supplied identity_refs;
- attempt to link one identity_ref to a different learner profile.

## Required positive gates

The validator must prove:
1. a new anonymous host identity is generated server-side;
2. it is linked through shared persistence;
3. a signed token resolves back to the same learner;
4. repeated resolution is stable;
5. cookie serialization does not expose learner_profile_id;
6. a user identity may be linked later to the same learner;
7. anonymous and user identity refs both resolve to the same learner;
8. existing evidence remains on the same learner profile after linking;
9. Russian and mathematics context can use the same cross-subject learner_profile_id;
10. resulting object is accepted by the existing `HostIdentity.validate()` contract;
11. no real secret is committed;
12. no production auth/deployment claim is made.

## Secret handling

No production secret or example that could be mistaken for one may be committed.

Validator secret must be injected through an in-memory test fixture or CI environment variable and must be clearly marked test-only.

## Completion evidence

Required durable files:
- `PEIS-TRUSTED-HOST-REUSE-AUDIT.txt`
- `PEIS-TRUSTED-HOST-CONTRACT-v0.1.json`
- `peis_trusted_host.py`
- `validate_peis_trusted_host_001.py`
- run output JSON;
- validation TXT.

Temporary GitHub Actions workflow is allowed for validation and must be removed before merge.

## Completion status

`REFERENCE_TRUSTED_HOST_IDENTITY_VALIDATED_NOT_PRODUCTION_AUTH`

Passing this gate does NOT authorize production login/account design, deployment, cookie domain configuration, or Tilda wiring.
