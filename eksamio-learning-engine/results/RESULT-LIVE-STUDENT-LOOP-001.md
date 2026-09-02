# RESULT — LIVE STUDENT LOOP 001

Date: 2026-09-02

Baseline `origin/main`: `85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb`

Branch: `codex/live-student-loop-staging`

Result: `STAGING_OWNER_TEST_PASS / PUBLIC_PRODUCTION_NOT_CONNECTED`

## Executable chain

| Boundary | Status | Evidence |
|---|---|---|
| Trainer | STAGING | Existing 174-card trainer, unchanged card corpus/UX; bounded T123-11 host integration. |
| Identity | STAGING | Existing passwordless identity + trusted-host continuity, synthetic `.invalid` owner-test account, non-production delivery. |
| Evidence | STAGING | Existing browser-hook request contract and subject adapters; server recomputes score/semantic truth. |
| PEIS | STAGING | Existing deterministic kernel/service bridge with server-side SQLite reference persistence. |
| Progress | STAGING | Learner-facing Today, skills, latest changes and server-restored history. |
| NBA / plan | STAGING | Recomputed from persisted PEIS snapshot after each accepted event. |
| Tutor context | STAGING | Card, answer, exact accepted semantic target and error are resolved server-side. |
| Tutor provider | MOCK | Deterministic reviewed-source response; no paid or non-admitted AI provider call. |
| Independent verify | STAGING | New event is marked `SAME_SESSION_VERIFICATION`; identical retry is `ALREADY_APPLIED`. |
| Public `eksamio.ru` path | NOT CONNECTED | No admitted HTTPS backend, production Postbox delivery, managed Postgres, TLS/CORS/cookie deployment. |

## Owner scenario executed in the browser

1. Opened the existing trainer and selected Task 12 only.
2. Submitted the accepted Task 12 card. Browser-safe observation reached the
   server; owner diagnostics displayed a server event ID, watermark and NBA.
3. Opened `Мой Eksamio`, used the server-owned owner-test login and confirmed
   anonymous-to-account continuity: the prior attempt appeared in Today/history.
4. Submitted the exact reviewed practice item incorrectly as `сочитание`.
5. Opened Tutor. The client sent only `card_id` and the learner message; the
   server supplied the incorrect answer, error event, exact semantic target and
   reviewed source grounding without asking the learner to repeat context.
6. Confirmed Tutor help generated assistance-aware evidence and changed NBA to
   independent verification without changing mastery.
7. Submitted a new answer `сочетание`; server marked the event as independent
   verification, changed NBA to retention, and diagnostics showed all seven
   causal steps PASS.
8. Replayed identical requests in automated tests: no duplicate event was made.
9. Logged out, logged in again and reloaded: the same server-owned history and
   profile were restored. A second anonymous context resolving the same test
   identity also reached the same learner profile in automated coverage.
10. Ran a separate stopped-backend browser test: local trainer feedback remained
    available and the integration displayed `Прогресс временно не синхронизирован`;
    it did not display server acceptance.

Owner diagnostic after verification:

- Attempt captured: PASS
- EvidenceEvent sent: PASS
- Server accepted: PASS
- PEIS updated: PASS
- Next action recalculated: PASS
- Tutor context available: PASS
- Independent verification completed: PASS

## Safety invariants

- Browser request contains only `card_id`, `session_started_at_ms`,
  `session_mode`, `answer`, `occurred_at_client`, `client_request_id`.
- Learner identity, correctness, score, evaluator trust, semantic mapping,
  mastery, readiness, retention and NBA remain server-owned.
- The accepted trainer card is COMPOSITE evidence and therefore creates no
  exact skill mastery. The reviewed practice item has the existing EXACT mapping.
- Tutor help is a separate `RULE_EXPLANATION` event with no score/correctness;
  only the subsequent independent attempt changes mastery.
- SQLite duplicate/idempotency and changed-payload integrity gates pass.
- Canonical authenticated state is not persisted to browser localStorage.
- Owner diagnostics contain opaque IDs/revisions/timestamps only; no contact,
  access token, verification code, provider credential or answer text.
- The owner runtime binds only to loopback and cannot be exposed publicly.

## Validation

- `test_live_student_loop.py`: 2/2 PASS, including full loop, continuity,
  idempotency, integrity conflict, Tutor/mastery separation and cross-browser identity.
- `validate_pro_client.py`: PASS.
- `validate_peis_browser_hook_001.mjs`: PASS.
- `validate_peis_service_bridge_001.py`: PASS, including real loopback HTTP.
- `validate_peis_persistence_001.py`: PASS.
- `validate_peis_trusted_host_001.py`: PASS with disposable runtime-only test secret.
- `test-trainer-data.js`: 1652 checks PASS; 174 cards; 9 source texts.
- Browser: full owner path PASS; reload/logout/login PASS; console errors/warnings 0.
- Responsive trainer and Pro: desktop 1280, mobile 390, 375 and 320 PASS;
  no horizontal overflow.
- Failure browser: visible unsynchronised state PASS; local attempt preserved.
- Production identity validator requiring `PEIS_DATABASE_DSN`: not run because
  no managed production database is provisioned; this is the explicit external blocker.

## Tilda handoff

Local owner folder contains `ege-russkiy-trenazher-T123-11.txt` as a staging
candidate. It must be placed after T123-10 only when a production host config is
admitted. It is inert when config is absent.

Current public action: **do not upload or republish T123-11**. HEAD, SEO/settings
and T123-02…08 are unchanged. T123-01/T123-10 in this branch materialise the
previously prepared semantic-state boundary; T123-11 is the only new live-loop
Tilda block. A real public handoff cannot be exact until the production HTTPS
base URL and cookie/CORS policy exist.

## External production blocker

Code cannot complete the public LIVE claim without provisioned and admitted
external resources: HTTPS gateway/domain route, secure cross-origin cookie/CORS
policy, production passwordless delivery, managed Postgres/Lockbox secrets and
an admitted Tutor provider path. The slice therefore stops at a production-shaped,
fully executable loopback STAGING implementation and does not mislabel it LIVE.
