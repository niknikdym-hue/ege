# PEIS-PRODUCTION-SUBSTRATE-001 validation

Status: PASS for the application/persistence substrate only. This does not pass or deploy the wider `PEIS-DEPLOYMENT-SECURITY-001` gate.

- Baseline/current main: `5a6ae0b5cf20545b532ecb260577061ed4198265`.
- Branch: `codex/peis-production-substrate-001`.
- PR: #111.
- Real temporary GitHub Actions evidence: run `32638355809`, job `97191395375`, Linux GitHub-hosted runner, conclusion `success`.
- The temporary workflow was removed from the final PR diff after that successful historical run, as required by `PEIS-PRODUCTION-SUBSTRATE-001-TEST-ENV-RECOVERY`.

Implementation files are `peis_postgres.py`, `migrations/0001_peis_postgres.sql`, `runtime.py`, `Dockerfile`, `.env.example`, `requirements.txt`, and `validate_postgres_integration.py` in this directory. The driver is `psycopg[binary]` 3.x. Migration `0001_peis_postgres` is tracked, idempotent, and includes PostgreSQL append-only triggers.

The successful job ran:

1. reference persistence, service-bridge, trusted-host and browser-hook validators;
2. `validate_postgres_integration.py` against an empty PostgreSQL 16 service, covering append, exact/idempotency replay, conflict, semantic target/order, identity continuity/reassignment rejection, recommendation/outcome, snapshot, transaction rollback, append-only trigger and restart;
3. `docker build -f eksamio-learning-engine/peis-production-substrate/Dockerfile -t peis-substrate:ci eksamio-learning-engine`;
4. container `/healthz` 200, `/readyz` 200 with PostgreSQL, disabled writes 503 `PEIS_WRITES_DISABLED`, oversized request 413, and non-ready/unavailable DB behavior.

No secrets are committed: test values are CI-only placeholders and normal runtime configuration is environment supplied. The runtime emits generic error codes only. The image was ephemeral GitHub-hosted runner image tag `peis-substrate:ci`; no registry image was published.

`PUBLIC_TRAFFIC_CONNECTED=false`  
`TILDA_CHANGED=false`  
`PRODUCTION_CLOUD_RESOURCES_CREATED=false`  
`LEARNER_AUDIO_PERSISTED=false`

Unresolved substrate blockers: none.
