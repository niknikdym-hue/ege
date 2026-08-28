# EGE 2026 exact route bridge — current launch state

This lane connects the merged Russian official requirement/admission-unit layer to the already reviewed EGE-2026 task authority **only through the explicit FIPI 2026 task-to-code relation**. It remains fail-closed: a bridge candidate is not semantic admission.

## Current exact result

The final FIPI 2026 specification table (`Обобщённый план варианта КИМ ЕГЭ 2026 года по РУССКОМУ ЯЗЫКУ`, printed pages 18–20) is now materialized as authority:

`task 1–27 -> exact content-element code expression(s) + checked-requirement code expression(s)`.

Source: `FIPI-EGE-RU-2026-FINAL / EGE_SPEC`, SHA-256 `3b71ec81f954bc32b574a0b3b997ee37bb3bc19ae8825f11217fd7149198b476`.

Bridge result against the 259 EGE admission units / 275 official requirement members:
- task-proven units: **63**;
- task-proven requirement members: **64**;
- task-unproven units: **196**;
- task-unproven requirement members: **211**;
- semantic admissions: **0**.

Candidate classes:
- `EXACT_MULTI_TASK_CANONICAL_CANDIDATE_SET`: 10;
- `EXACT_MULTI_TASK_ROUTE_WITHOUT_CANONICAL_TARGET`: 10;
- `EXACT_SINGLE_TASK_COMPOSITE_CANONICAL_SET`: 16;
- `EXACT_SINGLE_TASK_ROUTE_WITHOUT_CANONICAL_TARGET`: 27;
- `TASK_ID_NOT_PROVEN`: 196.

## Authority boundary

A dotted FIPI codifier code is **not** itself a task number. Task identity may be inferred only from the explicit final FIPI task-code table and only when both canonical codifier section and exact code match. Module, meaning, keyword or fuzzy inference is forbidden. Many-to-many task relations are preserved.

Every output remains `SUBJECT_REVIEW_REQUIRED`. The bridge may surface reviewed `school-*` candidates, but it cannot admit them and cannot create/admit any `ru-*` identity.

## Pinned state

- current authority: `RUSSIAN-EGE-ROUTE-BRIDGE-STATE-v2.0.json`;
- historical `RUSSIAN-EGE-ROUTE-BRIDGE-STATE-v1.0.json` is explicitly `SUPERSEDED` and must not be read as current launch truth;
- `validate_ege_route_bridge_state.py` validates the v2 state and the v1 supersession marker.

Current bridge normalized SHA-256: `310bda33ea30ce10227b1cdf4303152d2496e957811f2dfa09db65e13444eaa5`.
Deterministic emitted JSON SHA-256: `aaf52939fdb873e75c8ac12a1675c79027eca1e2ba582bb10e627cd2e17cf27b`.

## Launch truth

`russian_source_knowledge = READY`, but `russian_content = BLOCKED_SUBJECT`. This lane does not mutate PR #139, does not write learner state/mastery, and does not enable public traffic, production charges, PEIS network writes or Yandex gateway apply.

The next launch-critical step is **Russian subject admission/content closure**, not another source-research loop.
