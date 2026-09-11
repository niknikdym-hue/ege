# RUSSIAN-CRITICAL-PATH-FINGERPRINT-DRIFT

You are API-Codex executing one bounded repair on existing Draft PR #164.

WHY_NOW: the current exact OGE 6.14 gate is blocked by `ValueError: 6.2 reuse-exhaustion fingerprint drift` after later, unrelated accepted production-learning evidence files were added.

BASELINE_MAIN_SHA: `85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb`
BASELINE_SUBJECT_HEAD: `feb0b6ce6febcc33f766dc800bc010e778f80304`
EXPECTED_UNLOCK: restore the already accepted historical OGE 6.2 reuse-exhaustion fingerprint so the existing OGE 6.14 acceptance chain can regenerate unchanged.

Read the mandatory `eksamio-learning-engine/AGENTS.md` startup files and only the directly relevant OGE 6.14/6.2 builders, validators, accepted artifacts, and production-learning filenames needed to prove the drift.

Allowed output path — exactly one file:
`eksamio-learning-engine/russian-program/subject-admission/build_oge_6_14_remaining_6_2_reuse_exhaustion.py`

Required implementation:
- Identify later production-learning JSON files that are unrelated to the historical OGE 6.14 reuse proof and change only its count denominator.
- Extend the existing explicit `POST_PROOF_NON_6_14_CONTENT_NOT_COUNTED_IN_HISTORICAL_DENOMINATOR` mechanism for exactly those files.
- Preserve the safety behavior: every excluded count-only file must still be loaded and scanned for reusable exact OGE 6.2 evidence.
- Do not weaken any assertion or skip any file scan.
- Do not update accepted expected hashes merely to follow drift. The result must restore historical `normalized_sha256=9aae09034623cdd73c043bd5c515b9a8271e422d6cac70205300daceaa5a6773`.

Forbidden:
- Any production-learning JSON edit.
- Any semantic identity, canonical authority, task, answer, scorer, runtime, demo, Tilda, learner state, UI, payment, provider, Yandex, deployment, or public-traffic change.
- Any merge or new PR.
- Broad refactoring or broad audit.
- Editing any path other than the one allowed file.

Run the exact bounded checks requested by the trusted workflow. Report the root cause, exact filename additions to the count-only exclusion set, changed path, and tests. Do not commit or push; the trusted workflow owns validation, Astra review, commit, and push.
