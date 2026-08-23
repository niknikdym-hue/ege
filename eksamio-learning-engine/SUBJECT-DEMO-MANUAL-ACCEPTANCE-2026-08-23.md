# Eksamio — Subject Demo Manual Acceptance Authority

**Status:** CURRENT MANUAL ACCEPTANCE AUTHORITY  
**Date:** 2026-08-23  
**Scope:** subject demo release status only

This file records owner-confirmed manual acceptance facts for demo releases. It is intentionally narrow: it does not replace official source authority, PEIS/full-subject readiness, production-security gates, or the Product Masterplan.

Where an older operational handoff, backlog item, automated finding, or historical PR text conflicts with the manual acceptance status below, this file supersedes that **operational demo-status claim**. Historical evidence remains historical evidence and must not be silently deleted.

## Mathematics demos — CLOSED / MANUALLY ACCEPTED

The owner confirms that **all Mathematics demos for 2022, 2023, 2024, 2025 and 2026, both BASE and PROFILE routes, passed full manual acceptance**.

Operational consequences:

- `BASE Mathematics 2022–2026 = FULL_MANUAL_ACCEPTANCE_PASS / CLOSED`;
- `PROFILE Mathematics 2022–2026 = FULL_MANUAL_ACCEPTANCE_PASS / CLOSED`;
- do not create routine re-audit, parity-fix, rebuild or re-acceptance tasks for these demos;
- reopen a specific accepted demo only for a new concrete defect/evidence explicitly admitted by Central Brain;
- historical demo findings remain provenance only unless explicitly reopened.

This closes the previously listed PROFILE-2024 UI-parity item as an active execution dependency. It is retained only as historical evidence and must not generate work by itself.

Mathematics work now belongs to real product dependencies such as full-subject identity/PEIS integration, base-route product integration, telemetry, learning content, or another explicitly approved product milestone — not historical demo preparation.

## Russian demos — CLOSED / MANUALLY ACCEPTED

The owner confirms that **all Russian demos for 2022, 2023, 2024, 2025 and 2026 passed full manual acceptance**.

Operational consequences:

- `Russian demos 2022–2026 = FULL_MANUAL_ACCEPTANCE_PASS / CLOSED`;
- do not restart demo source/content/browser acceptance work merely because Russian full-subject work remains open;
- PR #72 / #57 / #23 and Russian PEIS/semantic/course work concern the **full-subject learning system**, not demo acceptance;
- reopen a specific accepted Russian demo only for a new concrete defect/evidence explicitly admitted by Central Brain.

Russian may therefore be **demo-ready while full-subject/PEIS launch readiness remains incomplete**. These are separate gates.

## Physics demos

The owner confirms:

- `Physics 2025 demo = FULL_MANUAL_ACCEPTANCE_PASS / CLOSED`.

Current separate state:

- `Physics 2024 demo = MANUAL_ACCEPTANCE_IN_PROGRESS` — no further automated/code changes until manual review returns a concrete finding;
- Physics 2026 remains the repository's frozen technical/runtime/layout reference; this file does not add a new owner-confirmed manual-acceptance claim for 2026 beyond existing repository authority.

Do not reopen Physics 2025 without a new concrete finding.

## Important distinction: demo acceptance != full-subject launch readiness

Manual acceptance of a demo proves the demo release is accepted. It does **not** by itself prove that the entire subject is launch-ready inside Eksamio Pro/shared PEIS.

Full-subject launch readiness additionally depends on the applicable subject identity/content/semantic integration plus the shared production platform gates (PEIS production substrate, deployment/security, identity/auth, telemetry, Tutor/Pro gates where applicable).

Therefore Central Brain must report these separately:

1. `DEMO_RELEASE_STATUS`;
2. `FULL_SUBJECT_PEIS_STATUS`;
3. `PRODUCTION/PRO_LAUNCH_STATUS`.

Never downgrade an accepted demo merely because full-subject PEIS integration is incomplete, and never call a full subject launch-ready merely because its demos passed manual acceptance.
