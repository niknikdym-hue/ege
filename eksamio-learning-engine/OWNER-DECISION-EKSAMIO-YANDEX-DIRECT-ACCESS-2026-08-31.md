# Owner Decision — Eksamio Yandex Direct access

**Status:** APPROVED OWNER DECISION  
**Date:** 2026-08-31

## Exact account binding

For Eksamio advertising in Yandex Direct:

- technical API/operator account: `reklamadymova`;
- advertiser / managed target account where Eksamio campaigns must live: `dymova`;
- the existing approved Direct API/OAuth contour of `reklamadymova` is reused; Eksamio must not create a second independent OAuth identity unless the existing binding stops satisfying provider/security requirements;
- Direct requests for the advertiser must target the exact managed login `dymova` (`Client-Login: dymova` where required by the Direct API role model);
- the technical account and advertiser account must never be aliased or silently substituted for each other.

## Secret boundary

OAuth tokens, passwords and other provider credentials are not stored in GitHub, chat, issues or learner-facing configuration. Existing secrets remain in their protected local/provider secret storage. Repository artifacts may contain only non-secret account-role identifiers and deterministic configuration contracts.

## Eksamio campaign scope

Advertising may begin for learner-facing Eksamio surfaces that are already `LIVE` under the Progressive Public Release invariant. Advertising must not claim unfinished Pro/payment/identity/Tutor capabilities as available.

Campaign creation, mutation and spend must be attributable to `site_id=eksamio` / `eksamio.ru` and must not mix Eksamio campaign state, analytics, conversion goals or economic decisions with Dilivox, even when the same technical Direct operator is reused.

## Spend authority

No campaign may begin spending without an explicit Eksamio advertising budget/limit. Until such a limit is fixed, acquisition work may prepare targeting, creatives, UTM/measurement contracts and a paused campaign candidate, but may not start paid delivery.
