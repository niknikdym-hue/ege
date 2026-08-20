# Eksamio Brain Checkpoint 09 — PEIS Browser Hook

Date: 2026-08-20
Status: DURABLE PROJECT CHECKPOINT
Main at checkpoint start: `cc989ad5f94ff3cdaedf1f79e6e3a23e5a2a475f`

## 1. Central milestone reached

`PEIS-BROWSER-HOOK-001` is merged.

The project now has a validated fail-open browser integration pattern between the actual current Russian trainer boundary and the previously merged PEIS service bridge.

The current production trainer runtime itself was NOT modified.

Validated browser-side pattern:

`current card/session facts`
→ `disabled-by-default browser hook`
→ `host-injected transport`
→ `PEIS service boundary`
→ `read-only shared-PEIS directive`

## 2. Current trainer safety is preserved

The integration map is pinned to the current Russian trainer runtime blob:

`97143363a5adfaef5609bc28fe823c31a2c1fc4d`

The reference projection inserts observation only after the existing:

`session.checked -> recordCard -> saveSession`

path.

Therefore the intended product order is:

1. current answer checking;
2. current local progress recording;
3. current session save;
4. non-blocking PEIS observation.

PEIS is not allowed to become a prerequisite for the trainer's existing core behavior.

## 3. Browser trust boundary is explicit

The browser may send only product facts:
- card_id;
- session_started_at_ms;
- session_mode;
- answer;
- occurred_at_client;
- stable client_request_id.

The browser does NOT send:
- score/correctness;
- semantic truth;
- evaluator trust;
- mastery/readiness/retention/NBA;
- learner_profile_id;
- anonymous/user identity refs;
- server sequence/watermark.

Canonical educational truth and canonical learner state remain server/shared-PEIS concerns.

## 4. Browser hook behavior validated

The generic hook is:
- disabled by default;
- transport-injected;
- endpoint-agnostic;
- authentication-agnostic;
- subject-neutral;
- non-persistent for canonical PEIS state;
- fail-open on transport error;
- fail-open on timeout;
- fail-open on directive callback failure;
- fail-open on invalid/non-shared directive.

Only an allowlisted read-only directive is exposed to the browser product layer.

Extra mastery/state/evidence fields from a server response are ignored by the hook.

## 5. Important non-claims

This checkpoint does NOT mean:
- PEIS is deployed publicly;
- Tilda is wired to PEIS;
- production authentication exists;
- browser JavaScript owns learner identity;
- production persistence infrastructure has been selected;
- real learners are already generating PEIS evidence.

The merged hook is a validated integration boundary, not a production rollout.

## 6. Next central bottleneck

Next gate:

`PEIS-TRUSTED-HOST-001`

The next problem is identity/authentication and trusted host context.

The browser hook intentionally sends no learner identity. Therefore a trusted server-side host boundary must resolve:

`request/session/cookie/account context`
→ `learner_profile_id + stable identity_refs`

before calling the PEIS service bridge.

## 7. Reuse-first rule for PEIS-TRUSTED-HOST-001

Before implementing any identity mechanism, audit current `main` for existing:
- authentication;
- login/account system;
- server-side session handling;
- opaque anonymous-user identifiers;
- signed cookies/tokens;
- API gateway/backend routes.

If a suitable trusted host already exists, reuse it.

Do NOT create a parallel account/auth system merely for PEIS.

If none exists, the gate may build a reference trusted-host boundary, but it must remain explicitly non-production until deployment/security decisions are admitted.

## 8. Identity invariants

Forbidden:
- email as academic-history primary key;
- learner_profile_id chosen by browser JS;
- browser-readable secret used as trust proof;
- unsigned identity cookie treated as trusted;
- subject-specific learner identities;
- separate Russian learner profile.

Required direction:
- one cross-subject learner_profile_id;
- opaque stable identity reference;
- server-side resolution;
- explicit anonymous→account linking path;
- no loss of historical EvidenceEvent records when identity is linked.

## 9. Candidate architecture only if no existing host auth exists

A reasonable reference candidate is:
- server-issued opaque anonymous identity;
- integrity-protected/signed host token or HttpOnly cookie;
- browser hook cannot read or modify canonical learner identity;
- trusted host resolves the token to learner_profile_id;
- later account login may link a user identity ref to the same learner_profile_id through shared persistence identity linking.

This is a candidate for validation, not automatic production authorization.

## 10. Current architectural sequence

Merged and validated:

`verified subject truth`
→ `semantic identity`
→ `EvidenceEvent`
→ `shared persistence`
→ `shared PEIS inference`
→ `NBA`
→ `current-product-shaped sensor integration`
→ `subject-neutral service boundary`
→ `fail-open browser hook`

Next:

`trusted host identity boundary`
→ later `deployment/security gate`
→ later `controlled production rollout`
→ real learner telemetry/outcome measurement.
