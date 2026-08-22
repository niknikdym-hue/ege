# Eksamio — Owner Decisions 2026-08-22

**Status:** APPROVED OWNER / PRODUCT / ARCHITECTURE AUTHORITY
**Date:** 2026-08-22
**Baseline:** `e9dfffae7275be9de829d1c5a5668e7715d8261f`
**Scope:** governance and authority only; this document does not claim runtime or production implementation.

This addendum records decisions made by the owner and Central Brain on 2026-08-22. It supplements `00-PRODUCT-MASTERPLAN.md` and explicitly supersedes older statements that classify realtime voice as an optional late/P3 capability or place it after the first paid Pro launch.

The dependency meaning remains unchanged: the shared PEIS closed loop, verified source truth, independent verification, deployment/security and production Tutor foundations must be built correctly. This decision does not authorize a voice-first architecture that bypasses PEIS.

## 1. First Eksamio Pro launch gate

The first paid Eksamio Pro launch is forbidden until both interfaces of one Tutor are production-ready:

1. text AI Tutor;
2. realtime voice AI Tutor.

Text-only Pro and voice-only Pro launches are both forbidden. Voice is a P0 launch capability and a principal product differentiator, not a later optional/P3 feature.

Text and voice are two interfaces of one Tutor and one learning episode. A learner must be able to switch `voice -> text -> voice` inside the same session without losing learning goal, verified context, help history or PEIS learning context.

The earlier rule “do not start with a generic or voice-first AI product” remains valid as an implementation/dependency rule: the first bounded AI slice may prove grounded help and independent verification before the complete Pro launch contour exists. It does not permit a paid text-only Pro launch.

## 2. Product client and Tilda boundary

The first Eksamio Pro client is a separate Eksamio web application with excellent desktop and mobile-browser experience. Native iPhone and Android applications are not required for the first launch.

Tilda remains the public site and free-demo layer. Accounts, canonical learner identity/state, PEIS, AI Tutor and payments must not be implemented inside Tilda.

## 3. Russia accessibility and production cloud

For a learner in Russia, Eksamio — including text AI Tutor and realtime voice Tutor — must work without VPN. The learner browser must not depend on direct access to a foreign AI service.

The primary production cloud is Yandex Cloud Russia. The architecture must remain portable and provider-neutral. Canonical PEIS state, learner state, subject truth and core business logic must not use a proprietary Yandex-only representation that prevents reasonable migration to another provider.

## 4. AI and speech provider architecture

AI remains provider-neutral. OpenAI and Google are principal candidates for the conversational brain needed for highly natural realtime dialogue. This candidate status is not production admission.

Production admission of any AI/speech provider requires applicable:

- Russia/accessibility gate;
- legal gate;
- quality gate;
- security gate.

Yandex SpeechKit is the priority candidate for Russian STT/TTS. No specific LLM, model or speech provider is declared production-approved by this decision.

Automatic AI Gateway fallback is allowed only between pre-approved production providers that passed the required gates. Provider switching is backend/internal; the learner does not select providers.

## 5. Learner audio privacy — hard invariant

**Eksamio does not store learner audio at all, in any form.**

No persistent Eksamio state may contain or retain:

- original recordings, audio files or fragments;
- copies, archives, datasets or backups of learner audio;
- voice samples or voiceprints;
- any persistent speaker/voice embedding, biometric feature, acoustic feature vector or other representation derived from learner audio, regardless of whether its intended purpose is identity, personalization, analytics, model improvement or another product function;
- any other persisted representation that preserves, fingerprints, reconstructs or enables later reuse of the learner's voice/audio.

Audio may exist only transiently as required by the current realtime processing pipeline. It must not become persistent Eksamio state. The architecture should intentionally avoid learner-audio persistence rather than treat it as an optional future feature.

The applicable launch/legal/privacy documentation must state explicitly and unambiguously that Eksamio does not store learner audio. The exact legal document for that statement remains subject to later legal/privacy review. No special UI banner/flag is required by this product decision; the legal/privacy placement and wording are determined in the later legal review.

Stored text or structured learning history is not learner audio and is governed separately by privacy and retention controls.

## 6. Identity and anonymous-to-account continuity

Eksamio Pro authentication is passwordless. The supported verified login identifiers are:

- e-mail;
- phone.

The user chooses either identifier; no classic password is required.

Anonymous free-demo learning progress from the same browser/device must be safely linkable to the later permanent learner account instead of being discarded. The browser must not become authority for canonical learner identity. Existing trusted-host, shared-PEIS and identity-boundary invariants remain in force.

## 7. Payments and payer rule

The first production payment candidate for the self-employed/NPD launch contour is `Robokassa + Robocheki SMZ`. It is a candidate, not irreversible provider lock-in; the payment layer must remain replaceable.

Before production admission, the contour requires separate:

- legal verification;
- API acceptance;
- webhook replay/idempotency validation;
- receipt validation;
- SBP/card validation;
- refund validation;
- failure/retry validation.

The payer is the person who actually makes the payment and is legally able to do so. Eksamio does not create a blanket product rule that only a parent may pay. Age/parental requirements apply only where law or the concrete contractual/payment contour requires them.

## 8. Tutor product boundary and history

AI Tutor is an educational Tutor, not a general-purpose companion or chatbot. Short natural human conversation is allowed in the learning context. Long off-topic conversation is not a product goal; Tutor should gently return the learner to the learning objective.

Tutor session history should be available for learner continuity and PEIS learning use, subject to privacy and retention controls. Text/structured history must not be confused with audio: the absolute audio non-storage invariant remains in force.

## 9. Learning and recommendation invariants

The deterministic-first, verified-source and independent-verification architecture remains unchanged. In addition:

- a learner saying “I understand” is not mastery evidence;
- substantial AI help requires independent verification;
- failed verification triggers a changed explanation and cause diagnosis rather than automatic advancement;
- if repeated explanations still fail, Tutor should test for an earlier prerequisite gap and may temporarily route to prerequisite repair, then return to the original learning goal after the prerequisite closes;
- a full worked solution may be shown after genuine attempts when pedagogically useful, but viewing it never counts as mastery;
- before giving an answer requested without an attempt, Tutor should first require or encourage an attempt or minimal guided step;
- PEIS must distinguish guessing/mechanical clicking from durable knowledge; a raw streak of correct answers alone is not sufficient mastery evidence when other evidence indicates guessing, instability or contradiction;
- immediate mastery and retained mastery are distinct;
- retention is re-tested later; failed retention lowers mastery confidence and returns the skill to review;
- retention intervals are individualized based on relevant learner evidence, including mastery stability, skill difficulty, error history and prior retention results;
- near a known exam/control deadline, the plan becomes deadline-aware and prioritizes high-risk/high-impact skills;
- exam value and cost of error may affect priority without bypassing critical prerequisites;
- score forecasts are probabilistic/range-based and never guarantees;
- the learner may leave the recommended route and study another topic; PEIS must account for that action and replan subsequent recommendations rather than forcing the learner back into a locked path;
- skipping a critical prerequisite may produce a clear warning but must not hard-lock the learner;
- Next Best Action must have a human-understandable explanation tied to relevant evidence such as errors, prerequisite dependency, retention risk, deadline or exam value.

## 10. Pedagogical development and owner-decision process

Eksamio should adapt strong evidence and world practice rather than invent educational methodology from scratch. Relevant approaches include mastery learning, retrieval practice, spaced/temporal practice, formative assessment, worked examples/scaffolding, deliberate practice, adaptive learning/knowledge tracing, independent verification and tutoring dialogue.

These approaches must be validated against measurable Eksamio learning outcomes.

Central Brain should independently resolve routine, reversible or evidence-backed decisions that already follow from current authority, architecture and established educational practice. The owner must not be asked to approve decisions merely because a choice exists.

Owner questions are reserved for genuinely material decisions that cannot be safely inferred from existing authority and that materially affect one or more of: money/commercial commitments, legal obligations, privacy/security, market/positioning, fundamental architecture, launch gates, or major user experience. Questions already answered must not be reopened without new evidence.

## 11. Preservation and non-implementation boundary

This decision does not weaken or replace:

- one shared PEIS;
- measurable learning outcome as the value unit;
- the free base learning loop;
- verified source truth and subject ownership boundaries;
- deterministic-first policies;
- independent verification;
- Student Learning Twin;
- provider-neutral architecture;
- frozen demo/source authority.

No cloud, auth, payment, AI, speech, Tilda or application runtime is implemented or production-approved by this authority-only decision.
