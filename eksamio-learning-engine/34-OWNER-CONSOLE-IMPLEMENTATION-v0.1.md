# Eksamio Owner Console — Implementation v0.1

**Status:** EXECUTABLE READ-ONLY CORE / LIVE AGGREGATE COLLECTOR PENDING  
**Date:** 2026-09-01  
**Product authority:** `33-OWNER-CONSOLE-v0.1.md`  
**Commercial measurement authority:** `30-METRIKA-GROWTH-MEASUREMENT-v0.2.md`

## 1. What is implemented

`tools/eksamio_owner_console.py` is a dependency-free local renderer for the first Owner Console.

It accepts one aggregate commercial snapshot, validates it fail-closed, derives verified economics, and produces one self-contained local HTML dashboard.

The first screen implements the approved information budget:

- exactly six KPI cards: Visitors, Meaningful learners, Checkout starts, Paid Pro customers, refund-adjusted Pro revenue, Paid CAC;
- one five-step funnel: visit -> meaningful learning -> Pro intent -> checkout -> verified purchase;
- one four-row channel table: Organic SEO / Yandex Direct Search / Referral / Other-direct;
- one 30-day trend panel;
- at most three prioritized alerts.

The dashboard supports `today / 7d / 30d` without rebuilding the page.

## 2. Hard read-only boundary

This v0.1 renderer has **no provider mutation path**.

It does not:

- call or modify Yandex Direct;
- call or modify Yandex Metrika;
- create/refund a payment;
- grant/revoke entitlement;
- grant/reverse a referral reward;
- write production PEIS state;
- accept a browser POST endpoint;
- depend on ChatGPT or GitHub at runtime.

Its only write is the local HTML output file explicitly supplied by the Owner/operator.

Provider/API collection is intentionally a separate upstream layer. That layer may read protected credentials from local secret storage, but the rendered snapshot must contain aggregate business truth only.

## 3. Snapshot schema

Schema identity: `owner-console-v0.1`.

Required periods:

- `today`;
- `7d`;
- `30d`.

Required aggregate fields per period:

- `qualified_visitors`;
- `meaningful_learners`;
- `pro_intent`;
- `checkout_starts`;
- `verified_paid_pro_customers`;
- `gross_pro_revenue_rub`;
- `refunds_rub`;
- `attributable_paid_spend_rub`;
- the four canonical channel rows.

Derived truth:

`refund_adjusted_pro_revenue_rub = gross_pro_revenue_rub - refunds_rub`

`paid_cac_rub = attributable_paid_spend_rub / verified_paid_pro_customers`

When there is no verified paid customer, CAC is undefined (`—`), never fabricated as zero.

The renderer rejects:

- negative or non-finite numbers;
- refunds greater than gross revenue;
- a later funnel stage greater than the preceding stage;
- unsupported/missing channel rows;
- invalid timestamps;
- invalid guardrail rates.

Unknown source fields are discarded during normalization and are never copied blindly into the HTML. This is a second privacy boundary against accidental PII leakage.

## 4. Alerts use Owner guardrails, not invented business targets

Supported guardrails:

- `stale_after_minutes`;
- `max_paid_cac_rub`;
- `min_checkout_sample`;
- `min_checkout_purchase_cvr`;
- `max_refund_rate`.

Economic thresholds are not hard-coded. If the Owner has not approved a threshold, keep it `null` and no target-based alert is emitted.

Independent of numeric targets, the console can signal:

- non-OK measurement status;
- stale snapshot when a freshness guardrail is configured;
- paid spend with zero server-confirmed purchases.

Only the three highest-priority signals are shown.

## 5. Canonical local command

From repository root:

```bash
python3 eksamio-learning-engine/tools/eksamio_owner_console.py \
  --input eksamio-learning-engine/owner-console/sample-snapshot.json \
  --output /tmp/eksamio-owner-console.html \
  --period 7d
```

The checked-in sample is deliberately marked `SAMPLE_NOT_LIVE` and contains zero commercial data. It must never be represented as live Eksamio analytics.

## 6. Tests

```bash
python3 -m unittest discover \
  -s eksamio-learning-engine/tests \
  -p 'test_eksamio_owner_console.py' \
  -v

python3 -m py_compile \
  eksamio-learning-engine/tools/eksamio_owner_console.py
```

Acceptance coverage includes:

- refund-adjusted revenue and paid CAC calculation;
- channel CAC calculation;
- Owner-guardrail alert behavior;
- maximum three alerts;
- six approved headline KPIs;
- four canonical channel rows;
- unknown-field/PII non-propagation;
- impossible funnel rejection;
- refund > gross rejection.

## 7. What remains before live Owner Console

The UI/core is implemented, but **live source collection is not yet admitted**.

Remaining sequence:

1. execute and read back live Metrika goal inventory/apply using protected local OAuth;
2. verify browser-eligible live events on accepted public surfaces;
3. complete/read back the inert Direct Search campaign state;
4. admit the production payment/order/entitlement/refund aggregate truth path;
5. admit referral ledger aggregate truth when referral runtime is live;
6. build the local collector that produces this exact aggregate schema from those sources;
7. set explicit Owner guardrails where desired;
8. render/open the dashboard from the fresh aggregate snapshot.

Until steps 1-6 are proven, the correct status is **Owner Console executable core ready, live dashboard data pending**.

## 8. Security invariant

**The Owner Console may display commercial truth; it may not mint commercial truth.**

Verified purchase, entitlement, refund and referral reward remain server-owned exactly as defined by the payment/referral authorities and the Metrika measurement contract.
