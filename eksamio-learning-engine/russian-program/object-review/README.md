# Russian object-level subject review queue

This lane turns the 1400 deterministic official Russian requirement rows from `source-knowledge/` into two deliberately different structures without weakening source truth.

## Review batches — work organization only

There are **354 review batches**. They combine requirements when these broad review dimensions are identical:
- normalized meaning;
- requirement class;
- exact `RU-PROG` module set;
- exact route scope.

A review batch is only a convenient way to inspect similar requirements together. It is explicitly **not** a semantic/content admission decision and may contain multiple different official source codes.

## Admission units — decision granularity

There are **1325 strict admission units** covering all **1400/1400 requirements**. An admission unit additionally fixes:
- exact source ID;
- exact source document;
- exact source section;
- exact official code.

Every page/grade/source fingerprint remains attached as member evidence. Only this stricter unit is eligible for a later object-level subject admission decision.

## Auto-resolution boundary

Automatic canonical resolution is allowed only when existing reviewed repository authority directly names the same `RSK-*` requirement ID and maps it to one canonical `school-*` identity. Topic/module/keyword/fuzzy similarity is never enough.

Current result: **0 automatic canonical units / 0 requirements**. No semantic decision is fabricated from module overlap.

PR #139 at `f16884ec4f8992ee9ad01c2930c42349f579bc70` is context-only. Its `ru-*` identities remain proposed and cannot be auto-admitted. Current context coverage is 288 work batches / 874 admission units / 920 requirements, but every one remains subject-review-required until explicit object-level admission.

Launch-first queue order is EGE → OGE → school; that changes review efficiency only, never truth. `russian_content` remains `BLOCKED_SUBJECT`. This lane generates no learner prose, changes no mastery/state, and activates no production capability.
