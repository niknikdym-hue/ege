# AI-TUTOR-RELIABILITY-CIRCUIT-REPAIR-001 — result

**Status:** `AI_TUTOR_RELIABILITY_CIRCUIT_REPAIR_READY_FOR_REVIEW`

**Baseline main:** `b571518a3e63eec526dcfd5f4503d5e0b600edb5`

## Repair

The T1 reliability gateway now maintains deterministic consecutive transient-failure state per provider/capability circuit.

- First retryable transient failure leaves the circuit closed but marks health `DEGRADED`.
- Repeated `TIMEOUT`, `NETWORK_FAILURE`, `PROVIDER_5XX`, `MALFORMED_PROVIDER_OUTPUT`, or `TOOL_PROTOCOL_FAILURE` opens the circuit at a server-owned configurable threshold (default 2).
- A successful same-path retry resets the transient failure counter and health.
- A failed half-open transient probe immediately reopens the circuit.
- A successful half-open probe closes the circuit and resets failure state.
- Existing immediate-open policy for billing/quota, credentials, model/capacity remains intact.
- Safety and invalid-platform-request terminal behavior is unchanged.
- Provider attempts still perform zero direct canonical PEIS writes and exactly-once acceptance/quota/evidence boundaries remain unchanged.

## Validation

A bounded local functional harness against the repaired gateway and the current T0 boundary semantics passed:

`AI_TUTOR_RELIABILITY_CIRCUIT_REPAIR_VALIDATION=PASS`

The repository now includes `validate_ai_tutor_reliability_circuit_repair_001.py` to prove:

1. invalid threshold rejection;
2. one transient failure followed by successful retry resets state;
3. repeated timeout opens the circuit and falls back;
4. repeated malformed provider output opens the circuit and cannot be accepted;
5. fallback preserves exactly-once quota/evidence and zero direct PEIS writes;
6. failed half-open probe reopens immediately;
7. successful half-open probe closes and resets state.

## Scope

- `EXTERNAL_AI_CALLS=0`
- `PROVIDER_SECRETS_ADDED=0`
- `PUBLIC_TRAFFIC_CONNECTED=false`
- `PEIS_CANONICAL_CONTRACTS_CHANGED=false`
- `SUBJECT_SOURCE_CHANGED=false`
- `TILDA_CHANGED=false`

## Next gate

After repository/PR checks, this repair clears the identified T1 circuit-breaker gap before `AI-TUTOR-OPENAI-SANDBOX-001` live-provider execution.
