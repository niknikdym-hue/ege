# Eksamio — Full Subject Source & Textbook Ingestion Policy v0.1

**Status:** CURRENT FULL-SUBJECT SOURCE AUTHORITY  
**Date:** 2026-08-23  
**Scope:** all Eksamio full-subject programs  
**Owner:** Central Brain under owner-approved product direction

## 1. Purpose

This document defines where a **Full Subject Scope** comes from and how textbooks and other verified subject materials are used to build Eksamio's canonical subject model.

A full subject is **not** derived from EGE/OGE task numbers, one textbook, one publisher line, or AI-generated ontology.

The target chain is:

`official subject scope -> canonical semantic capabilities -> prerequisite graph -> exam/diagnostic overlays -> original Eksamio teach/practice/verify/retain content -> shared PEIS`

## 2. Source hierarchy

### Tier 1 — normative subject-scope authority

For the Russia launch, the declared school-subject scope is grounded first in the applicable current official Russian educational requirements and federal program/curriculum documents (for example FSES/Federal Educational Program/Federal Working Program documents where applicable to the subject and grade range).

Tier 1 answers:

- what domains/topics/capabilities belong to the school subject;
- which grade bands they belong to;
- which required learning outcomes must be represented.

Tier 1 defines the **scope skeleton**. It does not by itself define the best Eksamio learning granularity or pedagogy.

### Tier 2 — official assessment and exam overlays

Use official FIPI and other applicable official assessment authority for exam/diagnostic truth, including where applicable:

- EGE codifiers, specifications and demos;
- OGE codifiers, specifications and demos;
- VPR/other official diagnostic materials when admitted under the applicable rights/source policy.

Tier 2 answers:

- what is assessed on a route;
- current official numbering/scoring/criteria;
- route-specific combinations of capabilities;
- exact exam evidence mappings.

Exam task numbers are **route metadata**, not semantic identities.

Tier 2 does not define the whole school subject.

### Tier 3 — verified textbooks and pedagogical subject sources

User-provided or otherwise lawfully available textbooks, manuals and strong subject references may be ingested as **knowledge and pedagogy evidence**.

They are used to recover and compare:

- chapter/topic structure;
- definitions and conceptual boundaries;
- methods and algorithms;
- worked-example patterns;
- typical misconceptions and contrasts;
- progression/order of introduction;
- task families and practice depth;
- prerequisite signals;
- alternative pedagogical explanations.

A textbook does **not** automatically become canonical scope authority, and no textbook can override current official FIPI exam facts.

Prefer more than one independent strong source/line where practical for important domains so Eksamio does not inherit one author's arbitrary decomposition.

### Tier 4 — verified Eksamio repository corpus

Use already verified Eksamio source matrices, accepted demos, trainers, diagnostics and reviewed subject evidence as provenance and mapping evidence.

Accepted demo/task material can prove that a capability is exercised on a route/year. It must not silently redefine the full subject ontology.

### Tier 5 — international curricula and world benchmarks

International curricula/taxonomies may be used as a **coverage and granularity check**:

- detect omitted domains;
- compare decomposition quality;
- compare prerequisite structure;
- benchmark pedagogical completeness.

They do not override the Russia-launch normative scope authority.

## 3. Canonical Full Subject Scope construction

For every subject, build a versioned `scope coverage ledger` from the hierarchy above.

Every normative scope item must end in exactly one explicit disposition:

- mapped to an existing canonical semantic identity;
- mapped to a reviewed candidate awaiting admission;
- explicitly outside the declared product/grade scope;
- blocked/needs-source-review with a recorded reason.

No item may disappear merely because it does not occur in current EGE/OGE demos.

Canonical semantic identities are capability-based and route-independent. They must have:

- stable capability definition;
- clear `includes` / `excludes` boundary;
- grade/scope applicability;
- source provenance;
- duplicate/granularity review;
- route mappings as overlays, not identity definitions.

AI may propose candidates and mappings but may not self-admit canonical identities.

## 4. Textbook ingestion pipeline

Textbook ingestion is a controlled evidence pipeline, not a copy/import-to-product pipeline.

### 4.1 Register source

For each uploaded/ingested source, preserve at minimum when available:

- source ID;
- title;
- authors;
- publisher;
- edition/year;
- grade/subject;
- file hash/version;
- acquisition/provenance note;
- rights/publication-use status if known.

Unknown rights status stays `needs_review`; do not infer publication rights from file possession.

### 4.2 Structural extraction

Extract or reconstruct a reviewable source map:

- table of contents;
- chapters/sections;
- topic labels;
- page/section locators.

The extracted map must preserve source provenance.

### 4.3 Knowledge/pedagogy extraction

Materialize **candidate evidence**, not canonical truth, for:

- concepts;
- skills/capabilities;
- rules/theorems/methods;
- worked-example patterns;
- prerequisite clues;
- misconceptions/errors;
- practice/task families.

Long copyrighted passages or wholesale exercise banks are not Eksamio product content.

### 4.4 Map against the canonical model

Each extracted candidate is classified as one of:

- `EXACT_EXISTING_IDENTITY`;
- `PARTIAL_EXISTING_IDENTITY`;
- `POSSIBLE_DUPLICATE`;
- `NEW_CANDIDATE_NEEDS_REVIEW`;
- `PEDAGOGY_ONLY_NO_NEW_IDENTITY`;
- `OUT_OF_DECLARED_SCOPE`;
- `SOURCE_CONFLICT_NEEDS_REVIEW`.

No automatic canonical admission from textbook extraction.

### 4.5 Cross-source reconciliation

Where multiple textbooks/sources are available, compare:

- common stable concepts;
- alternative decompositions;
- grade/order differences;
- granularity differences;
- conflicting definitions/methods;
- practice coverage depth.

A disagreement must remain explicit until subject review resolves it.

### 4.6 Subject acceptance

Only reviewed source-backed candidates can be admitted as canonical semantic identities or prerequisite relations.

Admission must preserve versioning and provenance.

## 5. Copyright / originality boundary

Eksamio's commercial learner-facing content must be original unless there is explicit authority/right to reproduce a source item.

Default rule for textbooks and non-public-domain references:

- use them to learn scope, concepts, methods, pedagogy, misconceptions and task families;
- paraphrase/synthesize where appropriate;
- create original Eksamio explanations, examples and practice;
- do not copy long passages, illustrations, or substantial exercise banks into the product merely because the source file is available.

Possession/upload of a textbook does not by itself prove redistribution rights.

Official exam material follows its separate source/rights/provenance policy.

## 6. Required content after identity admission

Textbook ingestion alone does not make a subject complete.

For every launch-relevant canonical identity, Eksamio must materialize the complete content bundle required by the Full Subject Completion Plan:

- canonical explanation/rule/method;
- provenance;
- worked examples;
- common errors/misconceptions and contrasts;
- guided practice;
- independent practice;
- mixed/transfer practice;
- retention items;
- fresh independent verification.

These are Eksamio learning artifacts, not copied textbook chapters.

## 7. Completion gate for Full Subject Scope

`FULL_SUBJECT_SCOPE_SOURCE_COMPLETE` may be claimed only when:

1. the declared normative grade/program scope has a complete coverage ledger;
2. every required normative item is mapped, explicitly excluded, or explicitly blocked;
3. no semantic identity exists without provenance;
4. exam/diagnostic route overlays are separate from the route-independent identity model;
5. textbook/source conflicts and granularity disputes are resolved or explicitly blocked;
6. known uncovered domains are recorded rather than silently omitted;
7. subject/human acceptance has occurred for canonical admissions.

This gate proves **scope/source completeness only**. It does not by itself prove full teaching-content completeness, PEIS connection, or production launch readiness.

## 8. Subject-specific application

### Russian

Use official school-program scope + current FIPI route truth + verified `russkiy-knigi/` and other admitted subject sources. Books support rule/method/pedagogy evidence; FIPI remains exam authority.

### Mathematics

The full 1–11 Mathematics program must not be reduced to BASE/PROFILE EGE coverage. Federal school scope supplies the full skeleton; FIPI BASE/PROFILE are overlays; textbooks deepen capability decomposition and pedagogy. The result is one route-independent Mathematics identity model with route overlays.

### Physics

When Physics moves from accepted demos to full-subject construction, apply the same hierarchy: official school-program scope first, FIPI routes as overlays, then verified textbooks/pedagogical sources for decomposition and content evidence. Do not infer the full Physics program from demo years alone.

## 9. Operational rules for Codex / subject agents

For any task claiming to build, extend or audit a full subject:

- read this policy first;
- identify which source tier supports each claimed capability;
- do not call FIPI-only coverage a full school-subject scope;
- do not turn textbook chapter headings directly into canonical identities without granularity review;
- do not auto-admit AI-generated identities;
- preserve source locators/provenance;
- keep unresolved coverage explicit;
- do not create learner-facing copied textbook content without reproduction authority.

If the normative scope source for a required grade/domain is absent or unverified, use a blocker rather than inventing completeness:

`BLOCKED_FULL_SUBJECT_NORMATIVE_SCOPE_SOURCE_MISSING`

## 10. Relationship to existing authority

This policy clarifies and governs the source-construction part of `SUBJECT-FULL-PROGRAM-COMPLETION-PLAN-2026-08-23.md`.

The Full Subject Completion Plan still governs the later sequence:

`scope/identities -> prerequisites -> complete content bundles -> mappings -> shared PEIS connection -> end-to-end subject acceptance`.

Accepted demo status remains separate and is governed by `SUBJECT-DEMO-MANUAL-ACCEPTANCE-2026-08-23.md`.
