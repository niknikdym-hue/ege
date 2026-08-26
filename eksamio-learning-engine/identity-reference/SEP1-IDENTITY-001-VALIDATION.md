# SEP1-IDENTITY-001 — Acceptance Evidence

Status: `IDENTITY_VERTICAL_SLICE_READY_FOR_PROVIDER_ACCEPTANCE`

Baseline main: `9e4354af83347a0952483976cfebdabd74cae0e3`

Implementation branch: `brain/sep1-identity-passwordless`

Dedicated GitHub Actions gate: run `32999604829` — `SEP1 Passwordless identity` — **PASS** on HEAD `fbe4c0f11e422638aabf306a32b2a5052a22847f`.

Validated in PostgreSQL-backed CI:

- bounded identity implementation compiles;
- existing trusted-host boundary passes;
- existing PostgreSQL PEIS substrate passes;
- merged Russian PEIS vertical slice remains green;
- passwordless challenge happy path passes;
- wrong, expired and replayed challenges are rejected;
- raw verified e-mail/phone is not persisted;
- raw session token is not persisted;
- anonymous Russian PEIS evidence is retained and linked exactly once to the verified opaque user identity;
- the same verified contact resolves the same learner profile across browsers;
- browser/localStorage identity assertion cannot replace canonical server identity;
- session rotation and logout/revocation pass;
- unsafe merge of a returning account with distinct anonymous evidence is rejected;
- non-production delivery adapter refuses real destinations;
- no production e-mail/SMS was sent;
- no payment, Tutor, Tilda, Mathematics, Physics or subject-content change is part of this slice.

The temporary acceptance workflow was removed after the successful gate. Production e-mail/SMS provider admission and credentials remain a later boundary; this slice does not claim production provider readiness.
