# Owner Decision — Referral reward only after verified paid purchase

**Status:** APPROVED OWNER DECISION  
**Date:** 2026-08-31

## 1. Referral product intent

Eksamio must include a referral growth mechanism of the form:

`invite -> qualified learner journey -> Pro purchase -> verified payment/entitlement -> referral reward`

The referral mechanism is part of the same commercial growth system as SEO, Yandex Direct, Metrika, checkout and retention. It is not a detached promotion and it must be measurable end to end.

## 2. Hard reward gate

A referral reward is created **only after a real paid purchase by the invited user has been verified server-side**.

The following are explicitly insufficient and must never grant a reward:

- referral link click;
- visit/session;
- registration;
- demo start or completion;
- trainer activity;
- Pro offer view;
- checkout start;
- order creation;
- payment-page redirect;
- frontend success screen;
- unverified provider callback.

Canonical qualifying event:

`verified payment -> exactly-once paid entitlement grant -> referral qualification`

The referral engine must consume server-owned payment/entitlement truth, not browser-reported purchase state.

## 3. Refund / revoke integrity

Referral economics must not remain falsely positive after a reversed commercial transaction.

If the qualifying purchase is refunded, charged back, revoked or otherwise invalidated under the canonical payment lifecycle, the referral system must support deterministic reversal/cancellation of any reward that has not become irrevocably vested under the final product policy.

No referral reward may survive a transaction that the canonical commercial ledger no longer treats as a valid paid acquisition unless an explicit later policy says otherwise.

## 4. Anti-abuse invariants

The implementation must be fail-closed against at least:

- self-referral;
- repeated reward for the same first qualifying purchase;
- duplicate identities/accounts used to recycle rewards;
- replayed payment/provider events;
- referral reassignment after a qualifying purchase;
- reward multiplication through refund/rebuy loops;
- manually supplied referral attribution that conflicts with server-owned evidence.

Referral qualification and reward grant must be idempotent and auditable.

## 5. Attribution and measurement

Referral attribution is kept as a distinct acquisition channel and must remain separable from:

- Yandex Direct Search;
- Yandex Network/retargeting;
- organic SEO;
- direct/other traffic.

Canonical referral funnel signals may include:

- `eks_referral_visit`;
- `eks_referral_qualified`;
- `eks_referral_purchase_verified`;
- `eks_referral_reward_granted`;
- `eks_referral_reward_reversed`.

Only bounded non-sensitive identifiers/aggregates may be sent to Metrika. E-mail, phone, learner answers, payment secrets and other PII must not be sent in advertising/analytics parameters.

The commercial KPI for referral is not raw invites; it is economics of verified incremental paid Pro customers, including reward cost and refund/revoke effects.

## 6. Reward form/value is intentionally not fixed yet

This owner decision fixes **when** a reward may be earned, not its exact amount or form.

The actual launch incentive must be explicit server-owned product configuration and may later be selected from approved product-safe forms such as:

- extra Pro access time;
- bounded AI/Tutor credits;
- discount/credit toward a future Pro purchase;
- another explicitly approved non-cash product benefit.

Do not hard-code a reward amount/value before the Owner approves the economics.

## 7. Commercial rule

The referral mechanism must support Eksamio's main growth objective:

`minimize profitable paid customer acquisition cost while preserving learner value and truthful product behavior`

A referral is successful only when it produces a real qualifying paid customer. Vanity metrics such as link shares, registrations or free-demo usage are supporting funnel signals, not referral success.