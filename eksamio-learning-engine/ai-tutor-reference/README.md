# AI Tutor provider-neutral boundary reference

`eksamio.tutor.provider-request.v1` is an executable, server-owned text-turn
boundary for the T0 slice. It uses only deterministic local fake providers.

The internal `ServerTutorTurn` holds five explicitly separate context classes:

1. `SystemPolicy` — server policy authority;
2. `VerifiedSubjectContext` — server-supplied verified source refs/excerpts;
3. `PeisContextProjection` — bounded read-only PEIS projection;
4. `TutorHistoryEntry` — prior structured Tutor text;
5. `learner_text` — current untrusted learner text.

`TutorOrchestrator` derives the minimized `ProviderRequest`; providers receive
no canonical learner identifier, contact information, payment data, auth token,
secret, raw database row, or browser-authoritative state. Provider output is
advisory. The orchestrator retains the server verification policy, filters
source refs and tool intents against server allowlists, and never writes PEIS.

The reference neither executes tools nor persists data. A valid tool intent is
only returned for a later server mediation layer. Failure or malformed output
returns the stable `TUTOR_UNAVAILABLE` result. This is not a provider SDK,
production endpoint, or reliability/failover gateway.

Run:

```sh
python3 eksamio-learning-engine/ai-tutor-reference/validate_ai_tutor_provider_neutral_boundary_001.py
python3 -m py_compile eksamio-learning-engine/ai-tutor-reference/*.py
```
