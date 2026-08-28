# Russian object-level subject review queue

This lane reduces the 1400 deterministic official Russian requirement rows from `source-knowledge/` into stable review groups without weakening source truth.

A review group may combine requirements only when these admission dimensions are identical:
- normalized meaning;
- requirement class;
- exact `RU-PROG` module set;
- exact route scope.

Every source/grade/page/code/section locator remains attached to the group as evidence.

## Auto-resolution boundary

Automatic canonical resolution is allowed only when existing reviewed repository authority directly names the same `RSK-*` requirement ID and maps it to one canonical `school-*` identity. Topic/module/keyword/fuzzy similarity is never enough.

PR #139 at `f16884ec4f8992ee9ad01c2930c42349f579bc70` is context-only. Its `ru-*` identities remain proposed and cannot be auto-admitted.

The queue is an efficiency tool for subject review. It does not change `russian_content=BLOCKED_SUBJECT`, does not generate learner content, and does not write learner mastery/state.
