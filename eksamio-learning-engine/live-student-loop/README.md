# Eksamio live student loop — owner-test staging

This directory composes the repository's accepted identity, trusted-host,
EvidenceEvent, PEIS persistence/kernel/service bridge, Russian adapters and NBA
contracts into one executable loopback-only vertical slice.

It is **STAGING**, not a public production deployment. It deliberately:

- binds only to `127.0.0.1`;
- uses the non-production passwordless delivery provider and one synthetic
  `.invalid` test identity;
- stores canonical learner evidence in a server-side SQLite reference store;
- uses deterministic, source-grounded Tutor copy without calling an AI provider;
- cannot enable public payments or commercial entitlement.

## Run the owner test

From the repository root:

```bash
export EKSAMIO_STAGING_HMAC_KEY="$(openssl rand -hex 32)"
export EKSAMIO_STAGING_DB="/tmp/eksamio-owner-test.sqlite"
python3 eksamio-learning-engine/live-student-loop/runtime.py
```

Open `http://127.0.0.1:8782/trainer/`. The disposable HMAC value is generated
locally and must not be committed or pasted into Tilda. Remove the temporary
SQLite file after the review if persistence is no longer needed.

## Tilda boundary

`ege-russkiy-trenazher-T123-11.txt` is the bounded browser integration block.
It is inert unless `window.EKSAMIO_LEARNER_LOOP_CONFIG.enabled === true` is set
by an admitted host. Do not publish this block to the public Tilda page until a
real HTTPS backend URL, CORS policy, cookie policy and production identity/
Postgres resources have passed deployment admission.

The learner browser sends only accepted observation fields. It does not send
identity, score, semantic truth, mastery, readiness or NBA state. A failed
backend call is shown as unsynchronised and never as accepted.
# Owner staging durability

Failed checked-card deliveries use a bounded, non-canonical browser outbox; the
server remains the sole owner of evidence and mastery. “Today” is calculated
from `received_at_server` in `Europe/Moscow`. Tutor help after verification
opens a fresh independent-verification lineage.

On macOS run `macos/install-desktop-app.sh` to replace the local
`~/Desktop/Eksamio — Ученик STAGING.app`. The panel is loopback-only, keeps its
stable staging key in Keychain, and stores bounded SQLite state in Application
Support. This remains STAGING; T123-11 is not published.
