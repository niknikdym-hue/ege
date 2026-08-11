# TASK-002 — Local project workspace for Eksamio Learning Engine

STATUS: OPEN
MODE: ADD-ONLY / NO DESTRUCTIVE CHANGES
REPOSITORY: niknikdym-hue/ege
REMOTE DIRECTION: eksamio-learning-engine/
LOCAL PROJECT ROOT: exam-platform-tilda
LOCAL WORKSPACE: exam-platform-tilda/eksamio-learning-engine/

## Goal

Create a persistent local file-based workspace for the Eksamio Learning Engine inside the user's existing local project `exam-platform-tilda`, so project context, specifications, tasks, results, reviews, build inputs and future implementation files live as normal files rather than being scattered across chat messages.

The local workspace must mirror the working direction in GitHub closely enough that ChatGPT and Codex can use the repository as the synchronization channel while Codex works with the user's local files.

## Important context

The Learning Engine pilot is EGE Russian language.

The current Russian trainer was previously assembled by Codex as the result of work across all Russian EGE demo materials. Therefore local Russian demo/trainer/source files already present on the computer are important working inputs and must not be destroyed, moved, renamed or silently replaced.

## Safety mode

This task is ADD-ONLY.

Do NOT:
- delete any existing file;
- rename or move existing demo/trainer/source files;
- modify current production/demo/trainer HTML, CSS, JS, T123, answers, criteria, URLs or localStorage keys;
- overwrite unrelated local files;
- refactor existing Russian demo/trainer code;
- merge duplicate-looking files without an explicit later task;
- remove old materials because they look obsolete;
- make implementation changes to the published Learning Engine.

If the target directory already exists, inspect it first and merge only by adding missing files/directories. Do not overwrite non-identical files silently.

## Step 1 — Locate the local project

Find the existing local project directory named:

`exam-platform-tilda`

Do not create a second copy of `exam-platform-tilda` elsewhere if it already exists.

Record the absolute resolved path in:

`exam-platform-tilda/eksamio-learning-engine/LOCAL-WORKSPACE-STATUS.txt`

Do not expose machine-specific credentials, tokens or secrets in GitHub.

## Step 2 — Create the local workspace

Inside the existing project create:

`exam-platform-tilda/eksamio-learning-engine/`

Create this structure if missing:

```text
exam-platform-tilda/
└── eksamio-learning-engine/
    ├── 00-WORK-STATUS.txt
    ├── 01-RUSSIAN-PILOT-CONCEPT.txt
    ├── 02-CODEX-BUILD-INDEX.txt
    ├── 02A-CODEX-RUSSIAN-SKILL-GRAPH-TASK.txt
    ├── AGENTS.md
    ├── COMMUNICATION-PROTOCOL.md
    ├── LOCAL-WORKSPACE-STATUS.txt
    ├── tasks/
    ├── results/
    ├── reviews/
    ├── specs/
    ├── audits/
    ├── build/
    └── sources/
```

The folders `specs/`, `audits/`, `build/`, and `sources/` are local organizational directories for future work. Do not move existing source material into them during this task unless explicitly copying references is necessary and safe.

## Step 3 — Synchronize current project-control files from GitHub

Use the current GitHub repository versions as source of truth for the following control files:

- `eksamio-learning-engine/00-WORK-STATUS.txt`
- `eksamio-learning-engine/01-RUSSIAN-PILOT-CONCEPT.txt`
- `eksamio-learning-engine/02-CODEX-BUILD-INDEX.txt`
- `eksamio-learning-engine/02A-CODEX-RUSSIAN-SKILL-GRAPH-TASK.txt`
- `eksamio-learning-engine/AGENTS.md`
- `eksamio-learning-engine/COMMUNICATION-PROTOCOL.md`
- `eksamio-learning-engine/tasks/TASK-001-russian-skill-graph.md`
- `eksamio-learning-engine/tasks/TASK-002-local-project-workspace.md`

Copy/sync them into the corresponding local workspace paths.

If a local copy already exists and differs from GitHub:
1. do not overwrite it silently;
2. create a comparison note in `audits/LOCAL-SYNC-CONFLICTS.txt`;
3. preserve both versions until explicitly reviewed.

## Step 4 — Make local files the working project notebook

From now on, for this Learning Engine direction:

- tasks are files, not chat-only instructions;
- Codex results are written to `results/`;
- ChatGPT review instructions are read from/written to `reviews/` in GitHub and synchronized locally;
- technical specifications belong in `specs/` or the numbered top-level spec files;
- audit findings belong in `audits/`;
- build-ready artifacts belong in `build/`;
- local source references or manifests belong in `sources/`.

Chat messages may trigger work, but the durable state of the project must live in files.

## Step 5 — Local source inventory, without moving anything

Create:

`exam-platform-tilda/eksamio-learning-engine/sources/RUSSIAN-LOCAL-SOURCE-INVENTORY.txt`

Inventory the existing local materials relevant to Russian EGE:

- current Russian trainer;
- all Russian demo packages/versions available locally;
- source-gate files;
- task maps;
- answer maps;
- criteria;
- implementation notes;
- T123/HTML/JS/CSS files;
- other Russian files previously used to assemble the trainer.

For every item record:

- absolute or project-relative path;
- filename/folder;
- apparent role;
- whether it is currently tracked in GitHub;
- whether it appears current, archival, unknown or duplicate-candidate;
- DO NOT delete or consolidate anything.

If status cannot be established, use `UNKNOWN / NEEDS_REVIEW`.

## Step 6 — Create local workspace status

Create:

`exam-platform-tilda/eksamio-learning-engine/LOCAL-WORKSPACE-STATUS.txt`

Include:

- resolved local project root;
- resolved Learning Engine workspace path;
- creation date/time;
- synchronization status of each control file;
- source inventory path;
- active task: TASK-001 Russian Skill Graph;
- safety mode: ADD-ONLY;
- statement that production/demo/trainer files were not modified.

## Step 7 — GitHub result file

After local workspace setup, create/update the repository result file:

`eksamio-learning-engine/results/RESULT-002-local-project-workspace.md`

It must contain only portable information, not private machine secrets.

Report:

- workspace created/found;
- control files synchronized;
- local source inventory created;
- any sync conflicts;
- any unresolved local path ambiguity;
- confirmation of NO DESTRUCTIVE CHANGES;
- confirmation that existing Russian demo/trainer files were not modified.

Do not commit machine-specific absolute paths to GitHub if they reveal private user directory names. Use a redacted form if necessary.

## Communication protocol from now on

The repository is the synchronization channel between ChatGPT and Codex.

Workflow:

1. ChatGPT/user creates or approves a task file in `eksamio-learning-engine/tasks/`.
2. Codex reads `AGENTS.md`, `COMMUNICATION-PROTOCOL.md`, then the active TASK file.
3. Codex performs local work using files under `exam-platform-tilda`.
4. Codex writes durable outputs into the local `eksamio-learning-engine/` workspace.
5. Codex writes a portable RESULT file into the GitHub repository.
6. User tells ChatGPT only that the task is finished.
7. ChatGPT reads the repository result/artifacts and writes a REVIEW file if needed.
8. Codex reads the REVIEW file and makes only requested corrections.

Do not rely on chat history as the only source of project state.

## Stop condition

For TASK-002, stop after:

- local `exam-platform-tilda/eksamio-learning-engine/` workspace exists;
- current control/task files are synchronized safely;
- local Russian source inventory is created;
- `LOCAL-WORKSPACE-STATUS.txt` exists;
- `results/RESULT-002-local-project-workspace.md` is written to GitHub.

Do NOT start Learning Engine implementation as part of TASK-002.
Do NOT modify existing demo/trainer production files.

After TASK-002, continue TASK-001 only under its own ADD-ONLY rules.