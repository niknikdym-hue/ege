# Eksamio SEP-1 live growth provider acceptance

**Status:** `BLOCKED_EXTERNAL`  
**Executed:** `2026-09-01T12:39:33Z`  
**Source commit:** `b075d71d8e2d2eddc74726bc50612a020c1ba3d8`

## Result

Provider acceptance is not complete. No provider write, campaign activation, budget mutation, payment/refund action, PEIS write, paid model call, or secret persistence occurred.

### Metrika

- counter `110348386` and domain `eksamio.ru` were verified by live GET;
- provider inventory contains 31 existing goals;
- canonical matches: `0/19` (`0/8` learning, `0/6` commercial, `0/5` referral);
- duplicate canonical event IDs: none;
- all 19 canonical goals remain missing;
- `--apply` was not executed because live goal creation requires explicit owner confirmation in a trusted user message;
- token source was Keychain service/account `ProfitEngine-YandexOAuth-Read` / `profit-engine`; token value was not printed.

### Browser events

Read-only inspection covered the public home page, Physics demo, and trainer catalog. The live HEAD initializes counter `110348386`, but the accepted `tilda-ready/eksamio-metrika-events-v0.1.js` bridge is not loaded. Live instrumentation remains on the older `ep_*` family. Canonical demo/trainer events are therefore `IMPLEMENTATION_GAP`; Pro/checkout/referral entry surfaces were not present in checked public navigation and are `SURFACE_NOT_CURRENTLY_AVAILABLE`. No server-only event was emitted or simulated.

### Direct

The deterministic dry run passed with the canonical inert contract: 4 groups, 22 keywords, 4 responsive ads, and both Search and Network `SERVING_OFF`. A separate GET-only provider inventory failed on `campaigns.get` with Direct authorization error code `53`. Consequently campaign ID, provider object totals, serving state, budget state, and spend state are not claimed. No Direct object was created or changed.

## Exact external blockers

1. Owner confirmation is required before creating the 19 missing live Metrika goals.
2. The canonical `eks_*` browser bridge must be deployed on the accepted public Tilda surfaces before live event acceptance can pass.
3. The protected Keychain OAuth credential must be authorized for Yandex Direct API v501 in the `reklamadymova` operator / `dymova` client context. The secret must not be pasted into chat or GitHub.

Owner Console remains correctly classified as not live-connected. After the blockers above are cleared, the next executable delta is a read-only aggregate collector joining admitted Metrika and Direct data with server payment/refund/entitlement truth, referral truth, and SEO aggregates.

Machine-readable evidence: `SEP1-LIVE-GROWTH-PROVIDER-ACCEPTANCE-2026-09-01.json`.
