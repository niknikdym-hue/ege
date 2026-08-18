# TASK-003 — Eksamio product realignment

**Date:** 2026-08-18  
**Type:** documentation / product architecture  
**System root:** `eksamio-learning-engine/`  
**Production code:** MUST NOT CHANGE

## Goal

Reconcile the current Eksamio repository with the new product direction. The shared `ege` repository remains the container for demos, trainers, sources and subject packages; `eksamio-learning-engine/` remains the root of the new intelligent learning system.

Eksamio must evolve from separate demos/trainers/content into one measurable personalized learning system, with Russian as the first implementation domain and with future reusable Living Core boundaries.

## Required outputs

1. Create the product/architecture authority **inside `eksamio-learning-engine/`**.
2. Define the relationship between demos, EGE trainer, standalone trainers, the full Russian program, Learning Engine and AI.
3. Record implementation priorities, including what must happen before realtime voice.
4. Preserve all current exam/source fidelity and production safety rules.
5. Update repository entry points/instructions so Codex reads the new authority before implementation work.
6. Produce a durable result artifact.

## Mandatory current Russian facts

- Current subject authority is the latest explicitly frozen current/final file, not an older checkpoint.
- As of this task, `266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json` establishes 185 active semantic school identities and closes the FIPI 2026 EGE/OGE overlay for the audited scope.
- The next active Russian content step remains trainer coverage audit against the 185 identities and exam-route overlays.
- Do not treat the current trainer snapshot count as proof of full coverage.

## Architecture decisions to record

- `eksamio-learning-engine/` is the root of the new system;
- one semantic/skill identity space;
- one Student Model/evidence model;
- demos remain exam-faithful and non-adaptive inside exam mode;
- personalization happens around/after evidence collection;
- deterministic official truth is separate from AI inference;
- free base learning loop remains useful and complete;
- paid layer sells deep personalized computation, not artificial removal of base value;
- Eksamio is first product, while reusable provider/identity/usage interfaces remain Living-Core-aware;
- do not build a generic cross-project platform before proving the Eksamio closed loop;
- text/structured AI Review precedes realtime voice.

## Safety

- documentation only;
- no T123/JS/CSS/HTML/runtime/scoring/localStorage changes;
- no source bank or canonical count changes;
- no demo content changes;
- no production deployment.
