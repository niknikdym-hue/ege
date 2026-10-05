# Fresh evidence after retained success: F3

Status: offline implementation and validation complete; production acceptance is not claimed.

- Audit: [issue #210](https://github.com/niknikdym-hue/ege/issues/210), finding F3.
- Exact baseline: `77cdb7ca071320dc6de90272ded7d43a0b07ea6c` (`main`, checked 2026-10-04).
- Authority: shared contracts 281 §§7, 11–13 and 284; no new engine, enums, thresholds or coefficients.

## Bounded correction

An exact independent error after a successful delayed check now produces `DEVELOPING` mastery with `LOW` confidence, `NEEDS_VERIFICATION` readiness and `SCHEDULED` retention. The old delayed check/history remain intact; an ordinary error does not become a recorded failed delayed check.

A fresh successful independent verification resolves the contradiction using the existing mastery evidence-count rule. Retention stays scheduled until a new qualifying delayed success. Further ordinary successes preserve that resolution, and a newer independent failure reopens the contradiction. An actual failed delayed check still requires restabilization. Assisted answers cannot resolve an independent contradiction or renew retention.

Due windows remain `null`: this correction does not implement or claim a production scheduler. Canonical subject/source facts and existing mapping, content and prerequisite guards remain unchanged.

## Reproducible validation

Run from the repository root with Python 3.12 and the existing dependency range `jsonschema>=4.23,<5`:

```sh
python -m unittest discover -s eksamio-learning-engine/peis-reference-kernel -p 'test_fresh_evidence.py' -v
python eksamio-learning-engine/peis-reference-kernel/run_reference_kernel_validation.py
```

- 22 schema-valid structural regressions: PASS; original baseline kernel fails 13 of these checks.
- Existing reference-kernel golden scenarios and cross-subject smoke: PASS.
- Existing persistence, integration, service-bridge and trusted-host validators: PASS locally. Trusted-host testing used only an ephemeral synthetic test secret.
- Input permutations, server ordering, exact-skill isolation, assisted answers, history preservation, same-session recovery, newer delayed failure and resolved-error neighbor sequences are covered.
- `.github/workflows/peis-fresh-evidence.yml` runs the two commands above on relevant pull requests and main pushes, with read-only repository permissions and no provider calls or secrets.

Validation used Python 3.12 and jsonschema 4.26.0. The GitHub-hosted workflow has not run at artifact preparation time. No PostgreSQL/live E2E, real student data, paid model call, deployment or public launch acceptance is claimed.
