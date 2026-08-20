# PEIS-SERVICE-BRIDGE-001 — subject-neutral executable transport boundary

Date: 2026-08-20
Status: IMPLEMENTATION
Baseline: `main@7c5822b971181efea0cfe045d9a25b5b8cf9fb8a`

## Milestone

Create the minimal executable JSON service boundary between a browser product sensor and the already validated shared PEIS stack.

Required flow:

`browser-safe checked-card payload`
-> `server-owned adapter registry`
-> `canonical EvidenceEvent 277`
-> `shared append-only persistence`
-> `shared deterministic PEIS recompute`
-> `persisted shared NBA`
-> `read-only product directive`.

This task does not deploy a public production endpoint and does not wire Tilda. It proves the executable service/transport contract that a later live-safe browser hook can call.

## Dependency/reuse rule

Must reuse:

- `peis-persistence-reference/PeisPersistenceStore`;
- `peis-reference-kernel`;
- EvidenceEvent 277 and NBA 285;
- `peis-integration-reference/RussianTrainerSensorAdapter`;
- `RUSSIAN-EGE-TRAINER-SENSOR-MAP-v0.1.json`;
- actual current Russian trainer bank/runtime artifacts;
- RU-SLICE-001 canonical prerequisite edge.

The service core must not contain Russian semantic IDs, Russian grammar rules, Task 12 scoring truth, or subject-specific learner state.

## Trust boundary

The raw browser payload is untrusted educational input.

The browser may supply only product-observation facts required by the registered adapter, such as:

- card ID;
- session source identity;
- response value;
- client occurrence time;
- product mode/request identity.

The browser MUST NOT be allowed to assert:

- semantic IDs or semantic mapping precision;
- evaluator type/trust class;
- correctness/score truth when the server adapter can deterministically recompute it;
- mastery/readiness/retention;
- NBA/reason codes;
- server sequence/watermark/receive time;
- subject ID independent of the registered adapter;
- prerequisite graph edges;
- canonical learner identity via email.

Those values are server/adapter/shared-PEIS owned.

## Identity boundary

Authentication is deliberately out of scope for this reference service.

The service receives a host-resolved identity context separately from the educational browser payload:

- `learner_profile_id`;
- exactly one or more allowed stable `identity_refs` (`anonymous_identity_ref` and/or `user_identity_ref`).

Email is forbidden as academic-history identity.

The reference loopback HTTP transport may use explicit `X-Eksamio-*` headers only to exercise transport mechanics in CI. Those headers are NOT a production authentication design and MUST be rejected for public deployment unless a trusted gateway resolves/signs them.

## Server-owned position

For new accepted events the service owns:

- `received_at_server`;
- `server_sequence`;
- `server_watermark`.

A retry of the same stable product observation must reuse the existing canonical event position and return idempotently. A changed educational payload under the same stable product identity must return an integrity conflict rather than rewrite history.

## Russian adapter used for first validation

Adapter ID:
`russian-ege-trainer-task12-v0.1`

The adapter:

- loads the actual current card by card ID from the pinned trainer bank;
- recomputes deterministic whole-card correctness on the server for the admitted `unordered_digits` route;
- ignores/rejects any client attempt to provide semantic/evaluator/mastery/NBA truth;
- delegates final canonical EvidenceEvent construction to the already validated Russian trainer sensor adapter;
- exposes target semantic/goal/prerequisite-edge metadata to the generic service only through the adapter interface.

The generic service core remains subject-neutral.

## Reference HTTP endpoints

Required reference endpoints:

- `GET /healthz`
- `POST /v0/checked-card`

Request body for `/v0/checked-card`:

```json
{
  "adapter_id": "russian-ege-trainer-task12-v0.1",
  "payload": {
    "card_id": "ege-ru-12-2026-12-01",
    "session_started_at_ms": 1787238000000,
    "session_mode": "practice",
    "answer": ["2", "5"],
    "occurred_at_client": "2026-08-20T17:00:00+03:00",
    "client_request_id": "browser-attempt-001"
  }
}
```

The response must contain only receipt/read-side data, including:

- accepted/idempotent status;
- canonical event ID;
- server sequence/watermark;
- subject ID;
- read-only shared PEIS directive;
- recommendation ID.

It must not expose a product-owned mastery write API.

## Validation requirements

PASS requires:

1. generic service module contains no Russian semantic IDs or Task 12 knowledge;
2. actual Russian adapter is registered separately;
3. actual current Task 12 card is loaded server-side;
4. client-supplied score/correctness/semantic/evaluator/mastery/NBA/server-position fields are rejected;
5. server recomputes the wrong whole-card response and emits COMPOSITE evidence;
6. server allocates sequence/watermark and ignores no client server-position because such fields are forbidden;
7. canonical event validates and persists through the shared store;
8. response after broad Task 12 failure is `DIAGNOSE_TARGET` for the prerequisite, not guessed mastery;
9. identical retry returns idempotently and preserves the original server position;
10. changed answer under the same stable session/card identity returns conflict and does not rewrite evidence;
11. recommendation proposal is persisted through shared NBA storage;
12. health endpoint works over real loopback HTTP;
13. checked-card endpoint works over real loopback HTTP;
14. missing host identity is rejected;
15. email identity is rejected;
16. original Russian trainer runtime/bank remain byte-identical;
17. no subject-specific learner engine is created;
18. service is explicitly marked reference/not publicly authenticated/not deployed production.

## Production safety

Forbidden in this task:

- editing current Tilda/trainer runtime;
- changing trainer scoring/localStorage;
- deploying credentials/secrets;
- inventing a hosting provider or public URL;
- implementing login/auth from scratch;
- accepting client-provided canonical semantic/evaluator/mastery/NBA truth;
- changing shared PEIS contracts;
- creating subject-owned persistence/mastery/NBA.

## Completion boundary

A PASS means the repository contains a deterministic executable service/transport boundary suitable for a subsequent live-safe browser bridge gate.

It does not mean the public Eksamio site is already connected to a production PEIS backend.
