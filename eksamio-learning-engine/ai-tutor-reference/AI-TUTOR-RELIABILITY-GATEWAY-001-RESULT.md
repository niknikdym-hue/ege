# AI-TUTOR-RELIABILITY-GATEWAY-001 — result

**Status:** `AI_TUTOR_RELIABILITY_GATEWAY_READY_FOR_MULTI_PROVIDER_SANDBOX`

**Baseline/current main:** `980ab97d12a2911383ca8f5f7b78ffbdebd21779`

**Reliability contract:** `eksamio.tutor.reliability-gateway.v1`

## Delivered

The merged provider-neutral `TutorOrchestrator` remains the sole advisory
response boundary. This T1 extension adds an in-memory deterministic reference
gateway around it: registered/admitted routing, normalized failure classes,
per-provider/capability circuit state, bounded retry/failover, half-open
recovery, provider-neutral episode projection, late-response discard,
exactly-once turn acceptance, separate learner-quota and mock-verification
commit ledgers, and normalized metadata-only observability events.

The provider fixtures are local, scripted, and deterministic. No provider can
write PEIS; `DIRECT_CANONICAL_PEIS_WRITES=0`.

## Deterministic acceptance evidence

`validate_ai_tutor_reliability_gateway_001.py` covers healthy primary,
timeout, network, provider 5xx, rate limit, billing/quota exhaustion,
credential failure, model unavailability, actual malformed adapter output,
late success, all-provider failure, safety block, invalid platform request,
half-open recovery, and portable fallback context.

- `ACCEPTED_ATTEMPT_MAX=1`
- `LEARNER_QUOTA_DEBIT_MAX=1`
- `EVIDENCE_VERIFICATION_COMMIT_MAX=1`
- `DIRECT_CANONICAL_PEIS_WRITES=0`
- repeated reliability result hash:
  `1ffdbfc1ac84b8ce8631aa3774abc9758b4989ed7069e989b03b2467c8ef006b`

Commands run successfully:

```sh
python3 eksamio-learning-engine/ai-tutor-reference/validate_ai_tutor_reliability_gateway_001.py
python3 eksamio-learning-engine/ai-tutor-reference/validate_ai_tutor_provider_neutral_boundary_001.py
python3 -m py_compile eksamio-learning-engine/ai-tutor-reference/*.py
python3 eksamio-learning-engine/peis-service-bridge-reference/validate_peis_service_bridge_001.py
env EKSAMIO_PEIS_TRUSTED_HOST_TEST_SECRET=<ephemeral-test-value> python3 eksamio-learning-engine/peis-trusted-host-reference/validate_peis_trusted_host_001.py
python3 eksamio-learning-engine/peis-reference-kernel/run_reference_kernel_validation.py
```

## Scope attestations

- `EXTERNAL_AI_CALLS=0`
- `PROVIDER_SECRETS_ADDED=0`
- `LEARNER_AUDIO_PERSISTED=false`
- `PUBLIC_TRAFFIC_CONNECTED=false`
- `PEIS_CANONICAL_CONTRACTS_CHANGED=false`
- `SUBJECT_SOURCE_CHANGED=false`
- `TILDA_CHANGED=false`

## Blockers

None. Real-provider sandbox/staging admission is the next separate task.
