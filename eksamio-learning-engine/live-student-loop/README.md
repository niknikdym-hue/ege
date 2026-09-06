# Eksamio live student loop — registered owner-test staging

This directory composes the repository's accepted registration/identity, EvidenceEvent,
PEIS persistence/kernel/service bridge, Russian adapters, NBA and Tutor contracts into
one executable **loopback-only STAGING** vertical slice.

This is not a public production deployment. The current admitted owner-test entry is
`gated_runtime.py`.

## Registered-only invariant

The staging learning surface is login-first:

- an unauthenticated request to `/trainer/` receives only the registered-entry gate;
- the actual trainer blocks and PEIS browser hook are not delivered before a server session exists;
- PEIS writes, progress/history/plan reads, practice writes and Tutor calls require the server session;
- owner-test login creates the synthetic `.invalid` account with `anonymous_host_token=None`;
- repeated sessions for that registered identity resolve to the same server-owned `learner_profile_id`;
- no anonymous learner profile or anonymous-to-account continuity is part of the admitted staging path.

`registered_runtime.py` reuses the accepted PEIS/NBA/Tutor engine while removing the
legacy anonymous HTTP admission. `gated_runtime.py` adds the page-level login gate and
is the runtime launched by the macOS owner panel.

The synthetic owner-test login is **not** a legal/production registration simulation.
Production passwordless registration and consent are owned by the stacked registration
boundary (`registration_http.py`, PR #186): required separate PD consent, optional
unchecked marketing consent, and server-owned HttpOnly session cookie.

## Run the owner test

From the repository root:

```bash
export EKSAMIO_STAGING_HMAC_KEY="$(openssl rand -hex 32)"
export EKSAMIO_STAGING_DB="/tmp/eksamio-owner-test.sqlite"
python3 eksamio-learning-engine/live-student-loop/gated_runtime.py
```

Open `http://127.0.0.1:8782/trainer/`. Before login this URL shows only the entry gate.
The disposable HMAC value is generated locally and must not be committed or pasted into
Tilda. Remove the temporary SQLite file after review if persistence is no longer needed.

## State and Tutor boundaries

- Canonical learner evidence/mastery is server-owned SQLite reference state in this staging slice.
- Browser requests do not supply semantic truth, mastery, readiness or NBA state; the server recomputes them.
- Tutor is deterministic/source-grounded staging and makes no paid AI/provider call.
- Tutor help itself does not raise mastery; a subsequent independent attempt is required.
- Any browser observation outbox in legacy T123-11 is transport retry only, never canonical learner state,
  and the gated staging runtime does not deliver that block before authentication.
- “Today” is calculated from `received_at_server` in `Europe/Moscow`.

## Tilda boundary

`ege-russkiy-trenazher-T123-11.txt` remains a **staging candidate only**. Do not publish
or republish it on the public Tilda page in this repository task. Public admission still
requires the real HTTPS backend/runtime, exact CORS/cookie policy, production passwordless
delivery, managed persistence/secrets and the registered learner integration to be verified.

The current public site is not changed by this owner-test branch.

## macOS owner panel

On macOS run `macos/install-desktop-app.sh` to replace the local
`~/Desktop/Eksamio — Ученик STAGING.app`. The installer uses an isolated Python runtime
when supplied by CI, launches `gated_runtime.py`, binds only to loopback, keeps the bounded
staging key in Keychain, and stores staging SQLite state in Application Support.
