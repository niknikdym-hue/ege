# AI-TUTOR-RELIABILITY-CIRCUIT-REPAIR-001

**Status:** IMPLEMENTED BOUNDED REPAIR  
**Date:** 2026-08-23  
**Baseline:** `b571518a3e63eec526dcfd5f4503d5e0b600edb5`

## Defect

The merged T1 gateway had circuit states and immediate opening for billing/credential/model-capacity failures, but retryable transient failures did not accumulate consecutive-failure state. Repeated malformed output or repeated timeout/network/5xx could therefore fall back while leaving the failed path closed.

## Repair contract

- Track consecutive transient failures per provider/capability path.
- Default deterministic open threshold: 2.
- Covered transient classes: `TIMEOUT`, `NETWORK_FAILURE`, `PROVIDER_5XX`, `MALFORMED_PROVIDER_OUTPUT`, `TOOL_PROTOCOL_FAILURE`.
- First transient failure may remain within bounded retry policy and marks health degraded.
- Reaching threshold opens the circuit.
- Success resets transient failure state.
- Half-open transient failure reopens immediately.
- Half-open success closes and resets state.
- Do not change immediate-open billing/credential/model-capacity behavior.
- Do not change safety/invalid-request routing.
- Preserve exactly-once learner quota/evidence semantics and zero provider direct PEIS writes.

## Acceptance

`validate_ai_tutor_reliability_circuit_repair_001.py` must PASS before live-provider sandbox execution.

Success status:

`AI_TUTOR_RELIABILITY_CIRCUIT_REPAIR_READY_FOR_OPENAI_SANDBOX`
