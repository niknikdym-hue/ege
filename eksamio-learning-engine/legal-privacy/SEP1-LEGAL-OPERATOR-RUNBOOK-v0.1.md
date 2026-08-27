# SEP1 Legal / Privacy / Operator Runbook v0.1

Status: `CODE_READY_EXTERNAL_INPUTS_REQUIRED`

This runbook is operational scaffolding, not legal advice and not evidence of external legal acceptance.

## Launch owner/operator fields that must be resolved
- `LEGAL_OPERATOR_FULL_NAME`
- `LEGAL_OPERATOR_INN`
- `LEGAL_SUPPORT_CONTACT`
- final legal review/acceptance of privacy, personal-data, offer, audio non-storage, and NPD/receipt artifacts

No operator address, contact, age rule, guarantee, legal basis, retention period, or provider acceptance may be invented from absence of authority.

## Launch-day support
Public traffic must remain OFF until a real support contact and a launch-day response/escalation target are explicitly approved. The final SLA is `[[UNRESOLVED:LEGAL_SUPPORT_SLA]]`.

## Payment/refund/revoke path
1. Identify the server-owned order and provider confirmation.
2. Confirm entitlement state from the server, never from browser state.
3. For an approved refund, execute provider refund under the admitted payment contour.
4. Record provider-confirmed refund exactly once.
5. Revoke the corresponding entitlement exactly once.
6. Preserve audit identifiers without card data or provider secrets.
7. Escalate any refund/receipt mismatch and keep production charges disabled if reconciliation is uncertain.

## Privacy/audio incident path
1. Stop the affected feature or provider route.
2. Preserve non-audio audit metadata needed to diagnose the event.
3. Do not persist learner audio while investigating.
4. If any learner-audio persistence is detected, treat the zero-persistence invariant as failed and keep voice disabled.
5. Escalate to the approved operator/legal contact before restoring live voice.

## Kill switches
The production preflight must fail if any of these are enabled before final go-live:
- `PUBLIC_TRAFFIC_ENABLED`
- `PRODUCTION_CHARGES_ENABLED`
- `PEIS_NETWORK_WRITES_ENABLED`
- `YC_GATEWAY_APPLY`

Tutor/provider-specific kill switches remain owned by their existing runtime contracts.

## Go-live rule
Code readiness is not legal acceptance. Exact accepted artifact version + SHA-256, resolved operator fields, external legal/fiscal/provider acceptance, upstream subject/source gates, and final production-candidate E2E are all required before owner go-live.
