# Eksamio Referral Growth System v0.1

**Status:** ACTIVE PRODUCT / COMMERCIAL ARCHITECTURE  
**Date:** 2026-08-31

Authority: `OWNER-DECISION-REFERRAL-AFTER-PAID-PURCHASE-2026-08-31.md`.

## 1. Purpose

Referral is a first-class acquisition channel inside the same Eksamio growth system as SEO, Direct, Metrika, checkout, purchase attribution and retention.

Canonical path:

`referral share -> attributed visit -> useful learner journey -> Pro checkout -> verified paid purchase -> exactly-once entitlement -> anti-abuse checks -> referral reward`

The success metric is verified incremental paid Pro acquisition, not shares, clicks, registrations or free-demo activity.

## 2. Server-owned referral identities

The backend must own immutable identities for:

- `referral_code` / referral link identity;
- referrer account;
- invited account / guest-to-account continuity;
- first qualifying order;
- payment transaction;
- granted entitlement;
- referral qualification;
- reward grant/reversal ledger entry.

Browser state may carry referral attribution into a guest session, but it may never authoritatively decide qualification or reward.

## 3. Reward state machine

Allowed lifecycle:

`ATTRIBUTED -> QUALIFYING_ORDER_CREATED -> PAYMENT_VERIFIED -> ENTITLEMENT_GRANTED -> PENDING_REWARD -> GRANTED`

Negative/reversal paths:

`ATTRIBUTED -> EXPIRED/INVALID`

`PENDING_REWARD -> REJECTED_ABUSE`

`GRANTED/PENDING_REWARD -> REVERSED` when the qualifying commercial transaction is refunded/revoked/charged back according to final commercial policy.

No state may skip directly from visit/registration/checkout to `GRANTED`.

## 4. Exact qualification gate

A referral can qualify only if all conditions are true:

1. invited customer attribution is valid under the current referral attribution policy;
2. referrer and invited customer are not the same canonical identity;
3. the purchase is a qualifying Pro SKU under server-owned configuration;
4. payment is verified by the canonical payment backend;
5. exactly-once entitlement grant succeeds;
6. the order/payment has not already qualified another referral reward;
7. anti-abuse rules pass;
8. no refund/revoke invalidation is currently recorded.

Qualification must be idempotent under provider webhook retries.

## 5. Anti-abuse minimum

Fail closed on at least:

- self-referral;
- same canonical account on both sides;
- repeated accounts created to cycle rewards;
- duplicate qualification from the same order/payment;
- webhook replay;
- referral-code switching after qualifying checkout/purchase;
- refund/rebuy reward cycling;
- referral chains designed only to manufacture benefits without incremental paid customers;
- inconsistent or manually forged client-side referral state.

Anti-abuse may use server-owned account/payment/order evidence. Do not export PII to Metrika or Direct for fraud control.

## 6. Refund / revoke handling

Referral economics are calculated on refund-adjusted purchases.

A qualifying purchase that is later invalidated must create a deterministic reversal record. The reward ledger must never simply delete history; it records why the reward was reversed.

If a reward has already been partly consumed, final product policy must define the non-destructive recovery rule before launch. Do not invent negative balances or debt collection behavior in implementation code.

## 7. Reward configuration

Reward form and amount are deliberately configuration, not hard-coded business logic.

Potential reward types may include only Owner-approved product-safe benefits, for example:

- bounded extra Pro time;
- bounded Tutor/AI credits;
- bounded credit/discount against a future Eksamio purchase.

Required configuration fields should support:

- `reward_type`;
- `reward_value`;
- qualifying SKU set;
- optional qualification/vesting delay;
- expiration policy;
- maximum rewards per referrer/time window;
- refund/reversal policy version.

No cash payout mechanism is implied by this architecture.

## 8. Attribution policy

Referral remains a separate acquisition channel from:

- organic SEO;
- Yandex Direct Search;
- Network/retargeting;
- direct/other traffic.

The system must preserve the referral source even while retaining ordinary UTM/yclid acquisition evidence for channel analysis. Attribution priority and overwrite windows must be explicitly versioned before production launch; the client must not silently choose whichever source is most favorable.

## 9. Metrika / growth events

Useful aggregate events:

- `eks_referral_visit`;
- `eks_referral_qualified`;
- `eks_referral_purchase_verified`;
- `eks_referral_reward_granted`;
- `eks_referral_reward_reversed`.

These are analytics signals only. Server ledger state is authority.

Never send to analytics:

- e-mail;
- phone;
- payment tokens/secrets;
- learner answer text;
- raw internal fraud evidence;
- direct personal identifiers.

## 10. Economics

Controller reporting must compare referral against paid/organic channels using:

`referral_CAC = reward economic cost + incremental operational cost / verified new paid referred customers`

Also track:

- referral visit -> paid purchase conversion;
- purchase value;
- reward cost;
- refund/revoke rate;
- repeat purchase / retention;
- net contribution after reward cost.

The referral program should be expanded only when verified incremental customer economics are healthy; invitation volume alone is not a success criterion.

## 11. Integration with Eksamio Acquisition Controller

`31-ACQUISITION-CONTROLLER-SEO-v0.1.md` remains the cross-channel growth architecture. Referral adds another measurable channel into that same commercial truth system.

The acquisition controller may compare SEO, Direct Search, retargeting and referral economics, but it must never merge their attribution records or hide channel-specific CAC.

## 12. Launch gate

Referral UI may be developed earlier, but production reward granting stays disabled until all of these are admitted:

- production identity continuity;
- verified payment lifecycle;
- exactly-once entitlement;
- refund/revoke lifecycle;
- referral ledger/state machine;
- anti-abuse checks;
- explicit Owner-approved reward type/value/economics;
- Metrika measurement without PII leakage.

Hard invariant:

**No verified paid purchase = no referral reward.**
