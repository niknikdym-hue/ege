# Russian Pro Astra remediation

Tracker: https://github.com/niknikdym-hue/ege/issues/210

Owner rule: persist decisions, tasks, evidence, blockers and restart context in this repository as they arise; chat is not the source of truth. Never include credentials or private learner records.

Base main: 77cdb7ca071320dc6de90272ded7d43a0b07ea6c. This is one draft integration branch, not a deployed release.

First reviewed changes: F3 fresh evidence fix and disabled DeepSeek adapter (#208). Independent reviews corrected the historical-contradiction resurrection, in-flight kill-switch race, and forged inline source checks before acceptance. Root reran the combined 22 F3 + 22 DeepSeek tests and the kernel/boundary/gateway/circuit/Yandex validators: PASS. GitHub CI must still be verified on the published SHA.

F1/F2/F4 remain offline and unaccepted: independent review found post-provider write-switch cancellation missing; correction pending. Real PostgreSQL migration/concurrency and browser E2E are not proven. F5 is being repaired separately; effective consent must follow contact verification and server-approved legal versions. F6-F9 remain open.

Next: finish independent reviews, integrate only required existing PR186/187/189/172 dependencies on this main baseline, run PostgreSQL/security/client/restart tests, then gated private tutor evaluation. No fake fresh item, no full Russian completion claim, no paid provider run or production merge/deploy by this checkpoint.
