# Independent DeepSeek adapter review

Verdict: PASS for the disabled, offline candidate scope only. No remaining blocking defect found in the reviewed final patch. No provider execution or GitHub mutation performed by this reviewer.

Reviewed frozen patch SHA-256: e4613c7cc5a07e87849a3d3983644ea6c0cc0f852070e56c53e1630b8eae90f4.
Patch: /workspace/shared/eksamio-deepseek-offline-20261004.patch.
Log: /workspace/shared/eksamio-deepseek-independent-review-20261004.log.
Audit authority: https://github.com/niknikdym-hue/ege/issues/210.

## Findings resolved before final review

1. The earlier adapter could accept an in-flight response after disabling and immediately re-enabling execution. Final code latches the old disable signal per request; re-enabling creates a different signal for future requests. The independent blocked-transport OFF→ON probe rejected all 50/50 old requests.
2. Earlier inline citation parsing missed Cyrillic/mixed-case source tokens and non-HTTP URLs. Final code rejects unknown URI-like tokens against exact server source IDs, including Unicode source:несуществующий, Source:forged and ftp:// links. Independent probes all reject; valid Unicode/ASCII IDs plus punctuation pass the supplied regressions. This is structural provenance validation, not proof that arbitrary generated prose is pedagogically true.

## Checks

- 22 DeepSeek offline tests: PASS.
- Existing provider-neutral boundary, reliability gateway, circuit repair and Yandex adapter validators: PASS.
- All Python files compile without changing source files: PASS.
- git diff --check: PASS.
- Actual git diff equals frozen patch hash before and after testing: PASS.
- Every baseline dependency file matches the recorded Git blob in the main 77cdb7ca source manifest: PASS.
- Exactly three additions: adapter, fake-transport validator, read-only offline workflow. No routing/provider admission, PEIS, canonical Russian source or production runtime edit.

## Bounds and compatibility

Execution defaults to false and requires an explicit boolean configuration. The server kill switch cannot override a disabled configuration. Request/response bounds default to 40,000/12,000 characters and are capped at 100,000; generated output is capped at 900 tokens. Default caller timeout is 20 seconds; accepted configured timeout is positive and at most 60 seconds. One daemon worker occupies the adapter slot until transport finishes; a timed-out hung call blocks further same-instance work and cannot later commit a result. The adapter does not claim to cancel remote inference/billing: production I/O transports still need their own deadline enforcement.

Official documentation supports the exact model URI, Chat Completions endpoint and JSON/store parameters, and logging opt-out:
- https://aistudio.yandex.ru/ru/docs/ai-studio/concepts/generation/models
- https://aistudio.yandex.ru/ru/docs/ai-studio/api/Chat-Completions/createChatCompletion
- https://aistudio.yandex.ru/ru/docs/ai-studio/operations/disable-logging

The API documentation warns that parameter support can vary by model. The exact model echo, actual model/parameter behavior, latency, quality, cost and provider-side privacy behavior remain unverified by live calls. The adapter fails closed on model mismatch; no alias/substitution is admitted. These limits do not block disabled offline-code review, and this review does not authorize live use or production admission.
