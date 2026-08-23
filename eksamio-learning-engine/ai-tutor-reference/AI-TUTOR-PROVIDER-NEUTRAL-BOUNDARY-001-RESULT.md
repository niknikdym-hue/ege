# AI-TUTOR-PROVIDER-NEUTRAL-BOUNDARY-001 — result

**Status:** `AI_TUTOR_PROVIDER_NEUTRAL_BOUNDARY_READY_FOR_GROUNDED_TEXT_SLICE`

**Baseline/current main:** `1262da5ebe77cae51b34add385e1f7dc93b39064`
**Boundary contract:** `eksamio.tutor.provider-request.v1`

## Delivered

- Server-owned `ServerTutorTurn` and minimized provider-neutral request.
- Deterministic fake adapters: two normal swappable providers, hostile,
  unavailable, and malformed-output fixtures.
- Advisory-only orchestration with verified-source and tool-intent allowlists.
- Stable `TUTOR_UNAVAILABLE` result for local fake provider failure/malformed
  output, with zero canonical PEIS writes.
- Deterministic validator and reference documentation.

## Acceptance checks

Passed on this branch:

```sh
python3 eksamio-learning-engine/ai-tutor-reference/validate_ai_tutor_provider_neutral_boundary_001.py
python3 -m py_compile eksamio-learning-engine/ai-tutor-reference/*.py
python3 eksamio-learning-engine/peis-service-bridge-reference/validate_peis_service_bridge_001.py
env EKSAMIO_PEIS_TRUSTED_HOST_TEST_SECRET=<ephemeral-test-value> python3 eksamio-learning-engine/peis-trusted-host-reference/validate_peis_trusted_host_001.py
python3 eksamio-learning-engine/peis-reference-kernel/run_reference_kernel_validation.py
```

The Tutor validator was run twice. Both runs passed with canonical result hash:

`e41a45312760a7f95d555e5eff5b4d3c22d191a55aa9bfa488b7099f07e4efd5`

It proves fake-provider swapping, minimized data, separated context classes,
rejection of correctness/mastery/readiness/retention/NBA/semantic/identity/
entitlement mutation attempts, verification-policy retention, tool/source
allowlist enforcement, stable failures, no PEIS writes, and no audio-persistence
field/path in the reference contract.

## Scope attestations

- `EXTERNAL_AI_CALLS=0`
- `PROVIDER_SECRETS_ADDED=0`
- `PUBLIC_TRAFFIC_CONNECTED=false`
- `PEIS_CANONICAL_CONTRACTS_CHANGED=false`
- `SUBJECT_SOURCE_CHANGED=false`
- `TILDA_CHANGED=false`
- `LEARNER_AUDIO_PERSISTED=false`

## Blockers

None. Reliability gateway, retry/failover, quota, and session-portability work
remain explicitly out of scope for the next task.
