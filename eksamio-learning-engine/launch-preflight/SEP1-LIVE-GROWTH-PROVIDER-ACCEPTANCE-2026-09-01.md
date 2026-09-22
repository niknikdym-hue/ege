# Eksamio SEP-1 live growth provider acceptance

**Status:** `BLOCKED_EXTERNAL`

**Executed:** `2026-09-01T12:39:33Z`

**Source commit:** `b075d71d8e2d2eddc74726bc50612a020c1ba3d8`

## Result

Provider acceptance is not complete. The Owner has now explicitly authorized creation of the 19 canonical Metrika goals and deployment/installation of browser-eligible `eks_*` events. Direct activation, budget mutation and spend remain forbidden.

### Metrika

- counter `110348386` and domain `eksamio.ru` were verified by live GET;
- provider inventory contains 31 existing goals;
- canonical matches remain `0/19` (`0/8` learning, `0/6` commercial, `0/5` referral);
- duplicate canonical event IDs: none;
- all 19 canonical goals remain missing;
- Owner authorization for `--apply` is complete;
- live `--apply` plus required read-back has not yet run because it requires execution in the Owner Mac context where Keychain service/account `ProfitEngine-YandexOAuth-Read` / `profit-engine` is available;
- token value was not printed or persisted.

### Browser events

Read-only inspection covered the public home page, Physics demo, and trainer catalog. The live HEAD initializes counter `110348386`, but `tilda-ready/eksamio-metrika-events-v0.1.js` is still not verified as loaded on the public site. Live instrumentation remains on the older `ep_*` family. Deployment is authorized, but repository presence is not live Tilda deployment evidence. Publishing still requires an authenticated Tilda operator/session. No server-only event was emitted or simulated.

### Direct

The deterministic dry run passed with the canonical inert contract: 4 groups, 22 keywords, 4 responsive ads, and intended Search/Network state `SERVING_OFF`. A separate GET-only provider inventory failed on `campaigns.get` with Direct authorization error code `53`. Consequently campaign ID, provider object totals, actual serving state, actual budget state and provider-account spend remain `NOT_PROVIDER_VERIFIED`.

No Direct object was created or changed. **Spend created by this acceptance run is exactly ₽0; total/provider-account spend is not verified and must not be represented as zero.**

## Exact external blockers

1. Run the already-authorized Metrika `--apply` and post-apply read-back in the Owner Mac context with the protected Keychain credential; PASS requires all 19 canonical goals exactly once.
2. Publish the authorized canonical `eks_*` bridge through an authenticated Tilda operator/session and verify the actual public runtime/events.
3. Repair/reauthorize the protected OAuth credential for Yandex Direct API v501 in the `reklamadymova` operator / `dymova` client context, then perform GET-only provider read-back. The secret must not be pasted into chat or GitHub.

Owner Console remains correctly classified as not live-connected. After provider acceptance, the next executable delta is a read-only aggregate collector joining admitted Metrika and Direct data with server payment/refund/entitlement truth, referral truth, and SEO aggregates.

Machine-readable evidence: `SEP1-LIVE-GROWTH-PROVIDER-ACCEPTANCE-2026-09-01.json`.
