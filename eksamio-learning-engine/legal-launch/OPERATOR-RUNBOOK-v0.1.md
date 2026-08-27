# Eksamio Pro — Русский: launch operator runbook v0.1

**STATUS: CODE/PROCESS CANDIDATE — EXTERNAL INPUTS REQUIRED BEFORE GO-LIVE**

## 1. Launch-day support

Required public support channel: **[SUPPORT_CONTACT]**.
Required privacy/data-subject channel: **[PRIVACY_CONTACT]**.

Until these values are accepted and published, public paid traffic must remain OFF.

Operational target for the first paid cohort:
- acknowledge payment/access blockers during the operating day as soon as practicable;
- prioritize `payment captured but entitlement absent`, `receipt missing`, `account access failure`, privacy/security incident and paid Tutor failure above non-blocking product feedback;
- every paid-support case gets an order/user-safe identifier and disposition; never paste credentials or full payment-card data into support records.

## 2. Payment / entitlement incident

1. Freeze repeated charge attempts for the affected order.
2. Read provider payment state using server-side authority only.
3. Compare provider event identity with Eksamio order/payment event ledger.
4. If payment is not conclusively successful, do not grant paid entitlement manually without an auditable owner/operator decision.
5. If payment is successful but entitlement is missing, restore entitlement through the admitted server-side repair path and record evidence.
6. Verify receipt/fiscal state separately; entitlement success must not hide a missing receipt.

## 3. Refund / revoke

1. Resolve exact order, payer contact and current entitlement.
2. Record refund reason and operator decision.
3. Execute the admitted provider refund/correction flow only after production credentials and merchant acceptance are enabled.
4. Revoke or recompute entitlement atomically with the accepted refund outcome.
5. Verify fiscal correction/receipt status where applicable.
6. Record final state without storing card details.

## 4. Personal-data request

1. Receive requests only through the accepted published channel.
2. Verify requester identity proportionately before disclosing or changing personal data.
3. Classify request: access / correction / cessation / deletion / consent withdrawal / other.
4. Route to the applicable retention/legal rule; do not promise deletion where another lawful retention duty still applies.
5. Record request, decision, execution evidence and completion date.

## 5. Privacy/security incident

1. Stop the affected write/provider path using the narrowest available kill switch.
2. Preserve minimal forensic evidence without expanding personal-data exposure.
3. Determine affected data, subjects, systems, time window and processors.
4. Escalate immediately to **[PRIVACY_INCIDENT_CONTACT]** and legal/operator review.
5. Apply the legally accepted notification timetable for a qualifying incident; repository drafts must not be treated as legal advice.
6. Restore service only after root cause is bounded and the relevant gate is re-accepted.

## 6. Learner audio incident

Any persisted learner audio, audio fragment, voiceprint or persistent acoustic embedding is launch-critical failure.

Required action:
1. disable voice execution path;
2. identify where persistence occurred;
3. stop further writes and remove data only under the accepted incident/deletion procedure;
4. re-run persistence-zero acceptance before re-enabling voice.

## 7. Kill switches

The following remain OFF until explicit final go-live decision:
- `PUBLIC_TRAFFIC_ENABLED=false`;
- `PRODUCTION_CHARGES_ENABLED=false`;
- `PEIS_NETWORK_WRITES_ENABLED=false` until its own production admission;
- provider-specific apply/execute switches not separately accepted.

A support/operator action must never bypass a kill switch by editing client state.

## 8. Escalation contract

`P0`: captured payment without service, duplicate/unsafe charge, personal-data/security incident, learner-audio persistence, widespread login failure, entitlement corruption.

`P1`: receipt delivery failure with otherwise correct service, material Tutor/provider outage, localized paid-flow failure.

`P2`: non-blocking UI/content/support issues that do not jeopardize money, access, rights or safety.

Final named contacts, service hours and external escalation destinations remain **BLOCKED_EXTERNAL** until owner/operator acceptance.
