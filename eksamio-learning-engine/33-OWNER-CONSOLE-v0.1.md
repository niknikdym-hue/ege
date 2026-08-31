# Eksamio Owner Console v0.1

**Status:** APPROVED PRODUCT / OWNER OPERATIONS SPEC  
**Date:** 2026-08-31  
**Target:** local macOS owner application / panel

## 1. Purpose

Eksamio Owner Console is a small owner-facing dashboard on the Owner's Mac. It is not a BI warehouse and not an admin screen full of operational detail.

It answers only the questions required to run the business:

1. Are qualified people coming to Eksamio?
2. Are they progressing toward Pro?
3. Are they buying?
4. What does a real paid customer cost?
5. Is acquisition economically healthy or wasting money?

The first release is **read-only**. It must not mutate Direct, budgets, payments, learner records or production state.

## 2. First-screen information budget

The default screen contains exactly six headline KPIs for the selected period (`today / 7d / 30d`):

1. **Visitors** — unique/qualified visits to live learner surfaces.
2. **Meaningful learners** — users who reached `eks_demo_complete` or `eks_trainer_meaningful`.
3. **Checkout starts** — `eks_checkout_start`.
4. **Paid Pro customers** — server-confirmed `eks_purchase` only.
5. **Pro revenue** — verified gross/refund-adjusted revenue shown clearly.
6. **Paid CAC** — attributable paid acquisition spend / server-confirmed new paid customers.

No CTR, impressions or raw click count belongs in the six headline cards.

## 3. One compact funnel

One funnel only:

`visit -> meaningful learning -> Pro intent -> checkout -> verified purchase`

Each step shows:

- count;
- step conversion rate;
- largest current drop-off highlighted.

No duplicate funnels by subject on the home screen.

## 4. One channel table

Maximum four default rows:

- Organic SEO;
- Yandex Direct Search;
- Referral;
- Other/direct.

Columns:

- qualified visitors;
- verified purchases;
- purchase CVR;
- acquisition cost where applicable;
- CAC where applicable;
- refund-adjusted revenue.

Network/retargeting appears as a separate row only after it is actually live.

## 5. One trend chart

One chart for the last 30 days:

- paid customers trend;
- paid CAC trend.

If there are not enough paid conversions yet, show meaningful learners and Pro intent instead, clearly labelled as leading indicators rather than revenue truth.

## 6. Maximum three alerts

The home screen shows at most three prioritized alerts. Examples:

- spend occurred with no qualified progression/purchase beyond an admitted threshold;
- CAC materially exceeded the Owner-approved target/cap;
- checkout-to-purchase conversion dropped sharply;
- payment/refund anomaly;
- Metrika/Direct attribution stopped matching;
- a major live landing is receiving traffic but its canonical measurement is broken.

Alerts are actionable sentences, not a log stream.

## 7. Data sources

The console reads from the same commercial truth system as the acquisition controller:

- Yandex Metrika counter `110348386`;
- Yandex Direct advertiser `dymova` through technical API operator `reklamadymova`;
- server-owned Eksamio payment/order/entitlement/refund truth;
- referral ledger;
- canonical live landing/SEO registry.

GitHub is not a runtime data source for business analytics.

## 8. Local security/runtime

Target shape:

- native/local macOS application (`Eksamio Owner Console.app`) or equivalent local-first packaged UI;
- aggregate analytics only by default;
- credentials read from protected local Keychain/secret storage;
- no OAuth token rendered in UI/logs;
- no learner answer text, raw Tutor conversations or payment secrets;
- no dependency on a ChatGPT conversation;
- no dependency on GitHub availability for normal operation.

## 9. Read-only first release

Version 0.1 is deliberately read-only.

Allowed:

- refresh analytics;
- switch period;
- inspect channel/funnel breakdown;
- view top alert details;
- view current Direct spend/cap state.

Not allowed in v0.1:

- start/stop campaigns;
- edit budget;
- edit bids;
- refund payments;
- change entitlements;
- change referral rewards.

Future bounded control actions may be added only after separate Owner authority and audit-safe write gates exist. A global Direct kill switch is the first likely write control, not arbitrary campaign editing.

## 10. Minimal drill-down

From the home screen, only three drill-downs are required initially:

1. **Acquisition** — Search queries / SEO landings / referral by verified paid outcome.
2. **Funnel** — where users leave between learning, Pro intent, checkout and purchase.
3. **Economics** — spend, paid customers, CAC, revenue, refunds by channel.

Do not build a general-purpose analytics explorer in the first release.

## 11. Owner north star

The panel should make one business truth impossible to miss:

**How many real paid Pro customers did Eksamio acquire, from where, and at what verified cost?**

Everything else is supporting evidence.