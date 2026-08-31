# Eksamio — Current Project Priorities

**Status:** CURRENT PRODUCT / DELIVERY AUTHORITY  
**Updated:** 2026-08-31  
**Baseline main at update:** `0e7cb3cd05cd999ea97606d65cf5aef5625fcb3f`  
**Primary deadline:** paid `Eksamio Pro — Russian` production launch by **2026-09-01**

This file is the current executable critical path. It supplements, but does not replace, `00-PRODUCT-MASTERPLAN.md` and approved owner decisions. When an older priority statement conflicts with this file, the newer explicitly approved owner/product decision wins.

## 1. One launch goal

Until the Russian paid launch is real, the project has one dominant delivery objective:

`FULL_RUSSIAN_TRUTH -> WORKING_RUSSIAN_PRODUCT -> YANDEX_PRODUCTION -> REAL_IDENTITY -> REAL_PAYMENT -> REAL_TUTOR -> END_TO_END_ACCEPTANCE -> PUBLIC_GO_LIVE`

Work that does not materially reduce one of these launch blockers is deferred.

Mathematics, Physics, historical polish, speculative platform work and nonessential UI expansion must not steal capacity from Russian launch closure.

## 2. Product architecture fixed on 2026-08-31

Eksamio remains one Personal Exam Intelligence System (PEIS), not a collection of unrelated demo/trainer/course pages.

For the Russian learner experience:

- `eksamio.ru` / Tilda remains the public marketing + free-demo layer;
- the protected learning area is one Eksamio web application from the learner's point of view;
- accounts, canonical learner state, PEIS, Tutor, entitlements and paid learning state live server-side, not in Tilda;
- primary production runtime is **Yandex Cloud Russia**;
- GitHub is a current development/version-control tool, **not a runtime dependency**;
- a GitHub outage must not break an already deployed Eksamio;
- production code/artifacts/configuration/data required for normal learner operation must be available from the production contour without fetching GitHub;
- repository hosting must remain replaceable without redesigning PEIS, subject truth or the learner product.

Google Drive may remain a bounded Source Archive for raw source materials, but is never on the normal learner runtime path after ingestion.

## 3. Russian full program is one source for many learner products

The full Russian program is not one linear course. It is the shared verified knowledge/content layer from which Eksamio can expose multiple learner surfaces without creating parallel subject ontologies.

Student-facing Russian product family:

1. **Free official demos and diagnostics** — EGE/OGE/school diagnostic entry points where admitted.
2. **Work on mistakes** — direct handoff from a failed item to the exact semantic skill and prerequisite chain.
3. **Thematic trainer** — practice by topic/skill, using the same canonical identities.
4. **Exam-task trainer** — EGE and OGE routes mapped to official task/code structures.
5. **Trainer constructor** — learner chooses admitted topics/task families/amount/difficulty or a system-generated mix; it reuses the same item/semantic pool rather than creating a separate knowledge model.
6. **Personal training / “Training for today”** — PEIS selects the next best work from errors, readiness, retention risk and exam value.
7. **Russian course / guided route** — structured learning path through the complete program with prerequisites, teaching, practice, verification and return-to-gap logic.
8. **School Russian 5–11** — grade/program views over the same full-subject knowledge layer.
9. **OGE Russian preparation** — exam route plus prerequisite repair into the school program.
10. **EGE Russian preparation** — exam route plus prerequisite repair into the school program.
11. **AI Tutor** — text + realtime voice over verified Russian knowledge and current learner state; not a general chat.
12. **Independent verification and retention** — mastery cannot be awarded merely because Tutor helped or the learner said “I understand”.
13. **Progress / readiness / weak-points map** — server-owned learner state with explainable next action.
14. **Extended-answer / essay learning support** — only where the rubric/source/evaluation gates are admitted; richer functionality may roll out after the core launch.
15. **Personalized course and exam plan** — deadline-aware sequence recomputed from evidence rather than a static checklist.

These are product surfaces over one Russian truth layer. No course, trainer, constructor, OGE route or EGE route may create a second semantic truth or separate mastery database.

## 4. Progressive rollout rule

Full-subject truth and product-surface rollout are separate gates.

A section may be opened to learners only when all dependencies for that section are admitted. Eksamio may progressively open sections, but must never claim a section or “full Russian” capability that is not actually backed by accepted content and runtime evidence.

### Stage R0 — private production assembly

Purpose: make the system real before public traffic.

Required:

- accepted Russian subject/content slice sufficient for the exposed learner surface;
- Yandex production-shaped backend and persistence;
- server-owned identity/session;
- product client connected to real backend;
- payment/entitlement contour connected in bounded production acceptance;
- Tutor connected behind server-side provider gateway;
- public traffic OFF until final gate.

### Stage R1 — first paid Russian closed loop

Minimum learner loop:

`diagnosis/attempt -> error evidence -> weak skill -> explanation/practice -> independent verify -> learner state -> next action`

Must include:

- account/login;
- paid entitlement;
- Russian learning content;
- trainer/practice;
- work on mistakes;
- personal next action;
- text + realtime voice Tutor as two interfaces of one Tutor;
- persistence across sessions;
- operational refund/revoke path;
- desktop + mobile-browser acceptance.

### Stage R2 — EGE Russian full learner surface

Open the complete admitted EGE route, exam-task training, thematic training, trainer constructor, course route, personalized practice, retention and Tutor over the complete accepted EGE-relevant Russian program.

### Stage R3 — OGE Russian full learner surface

Open the admitted OGE route using the same school/full-subject identities and PEIS state. OGE must not become a parallel subject database.

### Stage R4 — school Russian 5–11 surfaces

Expose grade/program navigation, topic study, thematic training and prerequisite repair across the accepted full school program.

### Stage R5 — advanced learner services

Add/expand essay and extended-answer evaluation, richer score forecast, deeper longitudinal analytics, parent/reporting surfaces and later multimodal tools only after their own gates pass.

Stages are rollout surfaces, not permission to weaken subject truth. If a feature is not open, the site must describe only what is actually available.

## 5. Russian content lane — highest P0 and acceleration rule

PR #164 is the current subject-closure authority branch and remains draft/NO-GO while Russian content is blocked.

Current exact truth from that PR:

- `1325 / 1325` admission units accounted exactly once;
- `1400 / 1400` official requirements accounted exactly once;
- exact object-bound accepted component sets: `21 units / 21 requirements`;
- remaining without accepted component set: `1295 units / 1370 requirements`;
- accepted bounded `ru-*` semantics: `75` total;
- false exact-mastery admissions: `0`.

This proves the denominator is known. The bottleneck is now acceptance throughput, not scope discovery.

### Mandatory acceleration change

Do **not** continue closing the Russian program as a long sequence of single-object micro-audits when a deterministic family/module batch can be reviewed safely.

Use:

`official family/module -> exact canonical owners -> bounded source packet -> deterministic object binding -> batch subject acceptance -> regression gate`

Batch by coherent canonical families and program modules where the same source authority and semantic boundary apply. Reuse existing canonical `school-*` owners first. Create new identities only for real source-backed gaps. Historical evidence is not silently rewritten.

Every batch must remain fail-closed:

- no broad family evidence may emit exact component mastery;
- no unresolved owner may be marked accepted;
- no rights-blocked textbook prose enters learner-facing content;
- exact object/requirement coverage counters must reconcile after each batch.

The goal is to move hundreds of compatible objects through reviewed mappings per wave where possible, not to lower semantic precision.

## 6. Tutor lane — casting closed, integration remains

The voice casting exercise is **closed**. Do not spend launch-critical time on further Lera casting unless a new production defect appears.

Accepted Russian speech policy:

- Yandex SpeechKit voice: **Lera**;
- accepted reading profile: `neutral / speed 1.04 / pitch 0 Hz / marked pauses`;
- learner audio persistence: `0`.

Brain routing owner decision for Russian launch:

- **Yandex brain is the default conversational brain for learners in Russia**;
- OpenAI is fallback/escalation only after applicable production admission;
- provider selection is backend/internal; the learner does not select “Yandex/OpenAI”;
- one learner-facing identity remains “Tutor Eksamio”.

PR #172 contains the current OpenAI/Yandex fast text/voice acceptance work. Its human benchmark/casting evidence must be incorporated into the production Tutor integration without reopening subjective voice casting.

Remaining Tutor work is production integration, latency/reliability, same-session continuity and PEIS evidence correctness — not voice selection.

## 7. Identity/session lane

Passwordless identity architecture is already implemented; PR #148 (`Yandex Postbox + SMS.RU production delivery`) is merged.

Remaining launch work:

- real verified Postbox sender/domain and IAM/service-account path;
- real SMS.RU credential/sender acceptance if phone login is enabled at launch;
- bounded real delivery smoke;
- anonymous -> permanent account continuity;
- server-owned canonical identity/session;
- privacy/retention and failure behavior.

No secrets, verification codes or raw contact data may be committed to Git or exposed to browser logs.

## 8. Payments / entitlement lane

Robokassa + Robocheki SMZ remains the first Russian self-employed/NPD payment candidate. Production-candidate code is merged; real provider acceptance remains a launch gate.

Required before paid public traffic:

- actual merchant settings/credentials outside Git;
- SBP and bank-card path;
- NPD/receipt acceptance;
- Password #1 / Password #2 boundaries;
- server-owned amount/order/InvId verification;
- webhook replay/idempotency;
- exactly-once entitlement grant;
- refund -> revoke;
- failure/retry behavior;
- no saved-card/autorenew requirement.

Payment success is not a browser flag; entitlement authority is server-side.

## 9. Yandex Cloud / server lane

Primary production cloud for Russian launch is **Yandex Cloud Russia**.

Normal learner operation must not depend on:

- GitHub availability;
- Google Drive availability;
- an owner laptop/local workspace;
- direct learner-browser access to a foreign AI provider.

Production contour must own or have admitted equivalents for:

- application runtime;
- database/persistence;
- production release artifacts/images;
- secrets/credentials outside repository and client;
- logs/monitoring with secret redaction;
- backup/restore and rollback;
- provider gateway and kill switches;
- server-owned PEIS/learner state.

GitHub may remain source/version-control and CI during development, but **GitHub outage != Eksamio outage**. Repository hosting must be replaceable later without changing product data models or business logic.

## 10. Product client / site assembly lane

The learner sees one Eksamio, even though public and protected technical layers differ.

Public layer:

- `eksamio.ru` / Tilda;
- product explanation;
- free demos and anonymous entry where applicable;
- sign-in / purchase entry points.

Protected learning layer:

- account;
- Russian program/course surfaces;
- trainers and trainer constructor;
- personal route / “training for today”;
- work on mistakes;
- Tutor;
- progress/readiness;
- entitlement-aware access.

The protected application should share brand/navigation continuity with the public site so the learner does not experience it as a different product.

## 11. Critical execution order from 2026-08-31

Run independent lanes in parallel, but resolve blockers in this order of business impact:

### P0-A — Russian subject closure

1. Stop micro-audit throughput where safe batch acceptance is possible.
2. Close canonical owner families/modules in bounded waves.
3. Reconcile every wave against the exact 1325/1400 denominator.
4. Reach `russian_content = PASS` without false exact mastery.

### P0-B — production Russian assembly

In parallel with subject closure:

1. assemble the protected Russian client against the production-shaped backend;
2. connect accepted Russian content to PEIS live flow;
3. wire account/session continuity;
4. wire trainer/work-on-errors/personal-route surfaces;
5. integrate the accepted Tutor policy into the same learner state.

### P0-C — external production gates

1. Yandex production deployment/persistence/security;
2. passwordless real delivery smoke;
3. Robokassa/Robocheki bounded real payment + receipt acceptance;
4. payment -> entitlement -> receipt -> refund/revoke E2E;
5. monitoring/rollback/kill switches.

### P0-D — final production E2E

Prove on one exact release identity:

`public entry -> account -> purchase -> entitlement -> Russian learning -> PEIS write/read -> trainer -> Tutor text/voice -> independent verify -> persisted progress -> logout/login continuity -> refund/revoke`

Then and only then enable owner-approved public paid traffic.

## 12. Go-live gates

Public paid Russian launch is `GO` only when all mandatory classes are true:

- `RUSSIAN_SUBJECT_CONTENT = PASS` for the marketed scope;
- `RUSSIAN_PEIS_LIVE = PASS`;
- `YANDEX_PRODUCTION = PASS`;
- `IDENTITY_DELIVERY = PASS`;
- `PAYMENT_RECEIPT_ENTITLEMENT = PASS`;
- `PRODUCT_CLIENT = PASS`;
- `TUTOR_TEXT_AND_VOICE = PASS`;
- `AUDIO_PERSISTENCE = 0`;
- `LEGAL_PRIVACY_OPERATIONS = PASS`;
- `FINAL_PRODUCTION_E2E = PASS`;
- explicit owner go-live approval is recorded.

No deadline may silently convert a failed mandatory gate into PASS.

## 13. Deferred until after launch

Unless directly required to clear a gate above, defer:

- more Lera casting;
- new Tutor provider experiments;
- Mathematics/Physics full-subject work;
- SourceCraft/GitHub migration;
- broad UI polish;
- native mobile apps;
- speculative infrastructure refactors;
- vision/photo/richer multimodal work;
- nonessential reports/dashboards;
- historical cleanup that does not affect launch truth.

## 14. Execution rule

Every task until go-live must answer:

`Which exact launch blocker does this remove?`

Preferred loop:

`blocker -> smallest production-shaped delta -> tests/evidence -> accept or repair -> immediately attack next blocker`

Not acceptable:

`new document -> another audit -> another document` without executable effect.

Authority documents are updated only when a material product/architecture/owner decision changed, as happened on 2026-08-31.