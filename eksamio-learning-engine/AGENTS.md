# Eksamio Learning Engine — Codex instructions

These instructions apply to the entire `eksamio-learning-engine/` directory tree.

## Source of truth

The GitHub repository is the durable source of truth for this direction. Do not rely on memory from prior chats when repository files provide current instructions.

`eksamio-learning-engine/` is the root of the Eksamio Personal Exam Intelligence System inside the shared `ege` repository.

Before every task in this direction, read in this order:

1. `00-PRODUCT-MASTERPLAN.md` — product target, architectural invariants and long-term implementation order;
2. `00B-PROJECT-PRIORITIES-CURRENT.md` — current subject/resource priorities and active delivery order;
3. `00-WORK-STATUS.txt` and `00A-WORK-STATUS-CURRENT-ADDENDUM.txt` — current checkpoints;
4. `COMMUNICATION-PROTOCOL.md`;
5. `02-CODEX-BUILD-INDEX.txt`;
6. the exact task file named by the user in `tasks/` or another explicitly named task file in this directory;
7. any source/provenance/current-authority files referenced by that task.

Product/architecture decisions from `00-PRODUCT-MASTERPLAN.md` and the current priority snapshot must not be silently overridden by an older historical checkpoint or a local subject task. Current explicit subject/source authority may supersede older subject counts or source checkpoints when it declares that supersession.

If instructions conflict materially, record the contradiction and stop the conflicting part instead of resolving it from memory. Safety constraints and explicit NO-DESTRUCTIVE/ADD-ONLY rules must never be relaxed implicitly.

## Fixed product priorities

Unless a newer explicit product decision changes them through the authority chain:

- Russian and mathematics are P0 and the two principal Eksamio subject directions;
- mathematics is the second subject of the system;
- physics is the third subject and may proceed in parallel only without slowing Russian or mathematics;
- the historical official source target for each subject is 2022–2026;
- all subjects reuse one PEIS architecture rather than creating subject-specific Student Model / evidence / mastery / readiness / retention / NBA engines.

## Safety

- Never modify existing Eksamio demo/trainer production files unless the current task explicitly authorizes exact paths.
- Never delete, rename, move, or refactor existing files as a side effect.
- Never silently fix unrelated problems discovered during an audit.
- Record discovered conflicts/problems in the task result or validation report.
- Unknown or unverified facts must be represented as `null`, `needs_review`, `NOT_CONFIRMED`, or another schema value explicitly allowed by the task. Do not guess.
- Official exam facts, answers, criteria, task numbering and scoring are source-of-truth data and must not be synthesized by AI.
- Difficulty must remain `null` unless supported by validated data or explicitly defined by a reviewed algorithm.
- Preserve backward compatibility unless the task explicitly describes and tests a migration.

## Unified learning-system rule

Demonstrations, exam trainers, standalone thematic trainers, full subject programs and AI are not separate competing learning systems.

They must converge on one stable semantic/skill identity principle and one Student Model. Do not introduce a second independent skill ontology, learner state, mastery model, readiness engine, retention engine or recommendation engine for a new course, subject, AI feature or trainer.

Each subject may and must have its own verified subject authority, semantic identities, prerequisite relationships, exam-route mappings and content layer.

AI must consume structured learner evidence and verified knowledge; AI must not become the owner of official scoring, exam facts or canonical skill identity.

## Russian explanations and rules — source policy

For Russian-language rules, explanations, algorithms, examples and error explanations, do not reinvent established subject matter and do not generate a new grammar methodology from scratch.

Primary working source directory:

`eksamio-learning-engine/russkiy-knigi/`

Use the books and reference materials in this directory as the priority subject-matter corpus for explanation content, together with official current FIPI materials where exam-specific facts or wording are required.

Rules:

- derive explanations from verified existing linguistic/teaching sources rather than inventing rules;
- preserve the meaning and correctness of the source rule while adapting presentation for a concise interactive trainer;
- do not copy long copyrighted passages verbatim; summarize, normalize and rewrite into original concise instructional wording;
- keep provenance for each explanation/rule block: source file, relevant section/topic, and any conflict between sources;
- if sources disagree materially, do not resolve by guess; mark `needs_review` and document the conflict;
- do not treat non-official books as source of truth for current EGE task numbering, scoring, criteria or official exam requirements; those must come from current verified FIPI sources;
- explanation UX may be new, but the underlying linguistic rule should come from established verified sources;
- whenever possible, separate `rule`, `short_rule`, `algorithm`, `examples`, `common_traps`, and `error_explanation`, so one verified rule can serve many trainer items without duplicating text.

The product principle is: do not invent the wheel; build a better learning interface around verified knowledge.

## Change workflow

For implementation work that can affect existing behavior:

1. Work on a dedicated branch/worktree.
2. Keep the change limited to the current task.
3. Run the checks required by the task and applicable project tests.
4. Produce a result report in `results/`.
5. Open a PR rather than merging directly to `main`.
6. Wait for review before further implementation that depends on the change.

For documentation-only ADD-ONLY tasks, direct creation of new files is allowed if the task explicitly permits it.

Direct commits to `main` that touch source authority, identity, PEIS, runtime or production must be treated as an audit trigger. Do not automatically revert them, but verify what changed, provenance/intent where applicable, and whether downstream branches must resync.

## Result contract

Every completed task must produce a durable result artifact in the repository. Do not make the chat response the only record of work.

The result must contain at least:

- task ID;
- status: `DONE`, `PARTIAL`, or `BLOCKED`;
- files created;
- files modified;
- files deleted;
- tests/checks run and outcomes;
- unresolved `needs_review` items;
- contradictions found;
- exact branch/commit/PR when applicable;
- explicit confirmation whether existing production files were changed.

## Review contract

If a review file exists for the task in `reviews/`, read it before continuing.

Statuses:

- `APPROVED` — task may be treated as accepted.
- `CHANGES_REQUIRED` — make only the requested corrections, preferably in the same task branch/PR.
- `HOLD` — do not continue dependent implementation.

Do not infer approval from silence.

## Product rule

The base Eksamio learning loop remains free:

`diagnose -> model -> prioritize -> practice/help -> verify -> retain -> reassess -> replan`

Premium features may add deep personalized computation/AI but must not be implemented by degrading or paywalling the base loop unless a future explicit product decision changes this rule through the product authority chain.
