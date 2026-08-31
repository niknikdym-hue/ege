# Eksamio Metrika Growth Measurement v0.2

**Status:** ACTIVE MEASUREMENT / COMMERCIAL ANALYTICS AUTHORITY  
**Date:** 2026-08-31  
**Counter:** `110348386`  
**Site:** `eksamio.ru`

## 1. Purpose

Metrika is the measurement spine that connects the live learner product, SEO, Yandex Direct, Pro checkout, verified purchase truth and referral growth.

Canonical chain:

`SEO / Direct / referral -> Eksamio -> Metrika learning intent -> server-owned checkout/payment -> verified commercial conversion -> acquisition controller`

The system must be able to answer:

1. who arrived and from which channel;
2. whether the visitor performed a useful learner action;
3. whether that visitor progressed toward Pro;
4. whether a real server-confirmed paid purchase occurred;
5. how much the acquired paid customer cost and what value they produced.

## 2. Existing goals are preserved

The current counter may already contain manually created Eksamio goals.

Rules:

- inventory the existing goal list before mutation;
- never delete an existing goal as part of canonical setup;
- never rename or overwrite a user-created goal automatically;
- recognize existing canonical JavaScript-event IDs and reuse them;
- create only missing canonical goals;
- fail closed on duplicate canonical event IDs.

Tool:

`eksamio-learning-engine/tools/eksamio_metrika_goals_setup.py`

## 3. Canonical goal set

### Learning layer

- `eks_demo_open`
- `eks_demo_start`
- `eks_demo_complete`
- `eks_result_to_practice`
- `eks_trainer_open`
- `eks_trainer_start`
- `eks_trainer_meaningful`
- `eks_return_learning`

These are learning-quality and pre-Pro funnel signals. They are not final revenue conversions.

### Commercial layer

- `eks_pro_offer_view`
- `eks_pro_intent`
- `eks_checkout_start`
- `eks_purchase`
- `eks_entitlement_active`
- `eks_refund`

`eks_purchase` means only a real server-confirmed paid purchase followed by successful exactly-once entitlement grant. A click on Buy, checkout page visit, provider redirect or client-side success message is not purchase truth.

### Referral layer

- `eks_referral_visit`
- `eks_referral_qualified`
- `eks_referral_purchase_verified`
- `eks_referral_reward_granted`
- `eks_referral_reward_reversed`

Referral qualification/reward truth is server-owned and follows `32-REFERRAL-GROWTH-SYSTEM-v0.1.md`.

## 4. Browser-eligible vs server-only

Browser event bridge:

`tilda-ready/eksamio-metrika-events-v0.1.js`

Browser-eligible signals are limited to non-authoritative learning/intent events:

- learning events;
- `eks_pro_offer_view`;
- `eks_pro_intent`;
- `eks_checkout_start` only as a leading funnel signal;
- `eks_referral_visit`.

Server-only goals:

- `eks_purchase`;
- `eks_entitlement_active`;
- `eks_refund`;
- `eks_referral_qualified`;
- `eks_referral_purchase_verified`;
- `eks_referral_reward_granted`;
- `eks_referral_reward_reversed`.

The browser bridge must not expose these authoritative events.

## 5. Offline/server conversion attribution

For server-confirmed commercial events, retain at least one Metrika attribution identifier where available:

- `ClientID` preferred for general session matching;
- `yclid` for Direct click attribution;
- `PurchaseId` for exact server-owned purchase linkage;
- `UserID` only under the approved identity/privacy contract.

The order/session layer must preserve attribution without exposing PII.

For verified purchases, the offline conversion payload should include server-owned conversion time and, where applicable, exact value in RUB.

Only conversions successfully matched by Metrika may be treated as Direct optimization evidence.

## 6. Privacy boundary

Never send in Metrika goals/parameters:

- e-mail;
- phone;
- payment credentials/tokens;
- raw learner answers;
- free-form Tutor text;
- raw fraud evidence;
- direct personal identifiers not explicitly admitted by privacy policy.

Allowed parameters are bounded non-sensitive product dimensions such as:

- subject;
- year;
- route;
- task family;
- landing identity;
- release identity;
- SKU code;
- acquisition channel.

## 7. Direct integration

Every Eksamio Direct campaign uses counter `110348386`.

Requirements:

- preserve `yclid`;
- preserve canonical UTM attribution;
- Search and Network remain separable channels;
- free-learning goals are leading signals only;
- after enough paid evidence, `eks_purchase` / verified purchase value becomes the primary Direct optimization truth;
- poor paid CAC cannot be hidden behind high free-demo conversion.

## 8. Reporting hierarchy

Owner-facing reporting should prioritize, in order:

1. verified paid customers;
2. paid CAC;
3. Pro revenue / refund-adjusted revenue;
4. checkout -> purchase conversion;
5. meaningful learner progression;
6. source/channel quality.

CTR, impressions and raw pageviews are diagnostic only and must not dominate owner reporting.

## 9. Current implementation state

As of this authority version:

- counter identity `110348386`: confirmed on live site;
- canonical goal registry: implemented in repo;
- existing-goal inventory + create-only-missing behavior: implemented;
- browser bridge excludes server-only goals: implemented;
- actual live provider goal inventory/apply: requires execution with the existing protected local OAuth token and read-back evidence;
- server-side offline purchase/refund/referral upload path: architecture fixed, production implementation follows payment/referral runtime admission.

## 10. Hard rule

**Metrika measures the funnel; the backend owns commercial truth.**

No client-side event can mint a paid customer, entitlement, refund or referral reward.