#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUSSIAN_PROGRAM = HERE.parent
ENGINE = RUSSIAN_PROGRAM.parent
REPO = ENGINE.parent

CANDIDATES = [
("001","Подбор средства связи по смыслу и грамматической форме","cohesion_gap_grammatical_fit","text_cohesion","PROCEDURAL_SKILL"),
("002","Определительное местоимение как средство связи","cohesion_determinative_pronoun","text_cohesion","RECOGNITION_SKILL"),
("003","Указательное местоимение как средство связи","cohesion_demonstrative_pronoun","text_cohesion","RECOGNITION_SKILL"),
("004","Притяжательное местоимение как средство связи","cohesion_possessive_pronoun","text_cohesion","RECOGNITION_SKILL"),
("005","Союз как средство межфразовой связи","cohesion_conjunction","text_cohesion","RECOGNITION_SKILL"),
("006","Формы одного слова как средство межфразовой связи","cohesion_word_forms","text_cohesion","RECOGNITION_SKILL"),
("007","Однокоренные слова как средство межфразовой связи","cohesion_cognate_words","text_cohesion","RECOGNITION_SKILL"),
("008","Определение значения слова в данном контексте","lexical_meaning_in_context","lexis","PROCEDURAL_SKILL"),
("009","Выбор значения многозначного слова по словарной статье","dictionary_sense_selection","lexis","PROCEDURAL_SKILL"),
("010","Сопоставление словарного толкования с употреблением слова в тексте","definition_context_matching","lexis","PROCEDURAL_SKILL"),
("011","Выбор паронима по значению и лексической сочетаемости","paronym_context_choice","lexis","DISCRIMINATION_SKILL"),
("012","Обнаружение и устранение плеоназма или лишнего слова","lexical_redundancy","lexis","PROCEDURAL_SKILL"),
("013","Замена слова, нарушающего лексическую сочетаемость","lexical_collocation_correction","lexis","PROCEDURAL_SKILL"),
("014","Поиск фразеологизма в заданном фрагменте текста","phraseologism_identification","lexis","RECOGNITION_SKILL"),
("015","Подбор контекстного синонима к слову исходного текста","contextual_synonym_selection","lexis","PROCEDURAL_SKILL"),
("016","Определение функционального стиля текста","functional_style_identification","stylistics","RECOGNITION_SKILL"),
("017","Определение жанра, адресата и коммуникативной цели текста","genre_and_communicative_purpose","stylistics","COMPOSITE_COMPETENCY"),
("018","Определение нормативной позиции ударения","normative_stress_selection","orthoepy","COMPOSITE_COMPETENCY"),
("019","Ударение в существительных и их формах","stress_nouns","orthoepy","PROCEDURAL_SKILL"),
("020","Ударение в прилагательных, кратких формах и степенях сравнения","stress_adjectival_forms","orthoepy","PROCEDURAL_SKILL"),
("021","Ударение в глаголах и личных/родовых формах","stress_verbs","orthoepy","PROCEDURAL_SKILL"),
("022","Ударение в причастиях и кратких причастиях","stress_participles","orthoepy","PROCEDURAL_SKILL"),
("023","Ударение в деепричастиях","stress_gerunds","orthoepy","PROCEDURAL_SKILL"),
("024","Ударение в наречиях","stress_adverbs","orthoepy","PROCEDURAL_SKILL"),
("025","Нормативные формы рода, числа и падежа существительных","noun_form_norms","morphological_norms","PROCEDURAL_SKILL"),
("026","Нормативное образование и склонение числительных","numeral_form_norms","morphological_norms","PROCEDURAL_SKILL"),
("027","Нормативные формы глагола, включая инфинитив и повелительное наклонение","verb_form_norms","morphological_norms","PROCEDURAL_SKILL"),
("028","Нормативная предложно-падежная форма управляемого слова","government_case_norm","syntactic_norms","PROCEDURAL_SKILL"),
("029","Нормативное построение предложения с косвенной речью","indirect_speech_construction","syntactic_norms","PROCEDURAL_SKILL"),
("030","Нормативное употребление несогласованного приложения","uncoordinated_apposition_construction","syntactic_norms","PROCEDURAL_SKILL"),
("031","Соотнесение деепричастного оборота с производителем действия","gerundial_construction_norm","syntactic_norms","PROCEDURAL_SKILL"),
("032","Нормативное построение конструкции с однородными членами","homogeneous_members_construction","syntactic_norms","PROCEDURAL_SKILL"),
("033","Распознавание ассонанса","device_assonance","expressive_means","RECOGNITION_SKILL"),
("034","Распознавание гиперболы","device_hyperbole","expressive_means","RECOGNITION_SKILL"),
("035","Распознавание метонимии","device_metonymy","expressive_means","RECOGNITION_SKILL"),
("036","Распознавание анафоры","device_anaphora","expressive_means","RECOGNITION_SKILL"),
("037","Распознавание парцелляции","device_parcellation","expressive_means","RECOGNITION_SKILL"),
("038","Распознавание ряда однородных членов как средства выразительности","device_homogeneous_rows","expressive_means","RECOGNITION_SKILL"),
("039","Распознавание обращения как синтаксического средства выразительности","device_address","expressive_means","RECOGNITION_SKILL"),
("040","Распознавание эпитета","device_epithet","expressive_means","RECOGNITION_SKILL"),
("041","Распознавание метафоры","device_metaphor","expressive_means","RECOGNITION_SKILL"),
("042","Распознавание сравнения","device_comparison","expressive_means","RECOGNITION_SKILL"),
("043","Проверка утверждения по фактам и смыслам исходного текста","content_statement_verification","text_analysis","PROCEDURAL_SKILL"),
("044","Распознавание повествования","narration_identification","text_analysis","RECOGNITION_SKILL"),
("045","Распознавание описания","description_identification","text_analysis","RECOGNITION_SKILL"),
("046","Распознавание рассуждения","reasoning_identification","text_analysis","RECOGNITION_SKILL"),
("047","Определение причинных, следственных, пояснительных и противительных отношений между предложениями","semantic_relation_between_sentences","text_analysis","RECOGNITION_SKILL"),
("048","Формулирование позиции автора по проблеме исходного текста","author_position_formulation","essay","PRODUCTION_SKILL"),
("049","Выбор и пояснение двух примеров-иллюстраций из исходного текста","textual_comment_examples","essay","PRODUCTION_SKILL"),
("050","Определение и пояснение смысловой связи между примерами","example_relation_explanation","essay","PRODUCTION_SKILL"),
("051","Формулирование и обоснование собственного отношения к позиции автора","own_position_argumentation","essay","PRODUCTION_SKILL"),
("052","Логичная композиция, связность и последовательность сочинения","essay_composition_coherence","essay","PRODUCTION_SKILL"),
("053","Нормативные формы степеней сравнения прилагательных и наречий","comparison_degree_forms","morphological_norms","PROCEDURAL_SKILL"),
("054","Фактическая точность письменного рассуждения","essay_factual_accuracy","essay","PRODUCTION_SKILL"),
("055","Этическая нормативность письменного ответа","essay_ethical_compliance","essay","PRODUCTION_SKILL"),
]

PREFIX = {"text_cohesion":"text-cohesion","lexis":"lexis","stylistics":"stylistics","orthoepy":"orthoepy","morphological_norms":"morphology","syntactic_norms":"syntax","expressive_means":"expressive","text_analysis":"text-analysis","essay":"essay"}
BLOCKED = {"015":"BLOCKED_SOURCE_REVIEW","053":"BLOCKED_GRANULARITY_REVIEW"}
SPECIAL = {"017":"READY_FOR_HUMAN_ADMISSION_AS_COMPOSITE","018":"READY_FOR_HUMAN_ADMISSION_AS_COMPOSITE","049":"READY_FOR_HUMAN_ADMISSION_WITH_ROUTE_NORMALIZATION"}

def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def semantic_id(domain: str, legacy: str) -> str:
    slug = legacy
    for prefix in ("cohesion_", "stress_", "device_", "essay_"):
        if slug.startswith(prefix):
            slug = slug[len(prefix):]
    return f"ru-{PREFIX[domain]}-{slug.replace('_','-')}"

def source_refs(num: str, legacy: str):
    if num == "053":
        return ["eksamio-learning-engine/03-RUSSIAN-SKILL-GRAPH.json#skills[morphological_norms]","eksamio-learning-engine/87A-RUSSIAN-MORPHOLOGY-GRAPH-GAP-CANDIDATES.txt"]
    if num == "054":
        return ["eksamio-learning-engine/53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[K4]","eksamio-learning-engine/55-RUSSIAN-ESSAY-27-EXPLANATION-COMPONENTS-v0.1.json#essay_fact_logic_review"]
    if num == "055":
        return ["eksamio-learning-engine/53-RUSSIAN-ESSAY-27-CRITERIA-MAP-2026.json#criteria[K6]","eksamio-learning-engine/55-RUSSIAN-ESSAY-27-EXPLANATION-COMPONENTS-v0.1.json#essay_ethics_review"]
    return [f"eksamio-learning-engine/03-RUSSIAN-SKILL-GRAPH.json#skills[{legacy}]"]

def canonical_text(num: str, label: str):
    if num == "017":
        return label, "Определять жанр текста, предполагаемого адресата и коммуникативную цель как составные параметры речевой ситуации."
    if num == "018":
        return label, "Определять нормативную позицию словесного ударения; используется как составная орфоэпическая компетенция над более узкими частеречными ветвями."
    if num == "049":
        return "Выбор и пояснение примеров-иллюстраций из исходного текста", "Выбирать релевантные примеры-иллюстрации из исходного текста и пояснять их связь с анализируемой авторской позицией; требуемое количество примеров задаётся экзаменационным маршрутом, а не semantic identity."
    return label, label.rstrip(".") + "."

def build_rows():
    rows = []
    for num, label, legacy, domain, entity_type in CANDIDATES:
        candidate_ref = f"candidate-{num}"
        decision = BLOCKED.get(num, SPECIAL.get(num, "READY_FOR_HUMAN_ADMISSION"))
        canon_label, canon_def = canonical_text(num, label)
        blocked_reason = None
        if num == "015": blocked_reason = "Skill Graph source node is explicitly marked needs_review; source-review flag must be cleared before canonical admission."
        elif num == "053": blocked_reason = "Source-backed graph gap explicitly leaves final granularity open: one identity or narrower comparison-degree branches."
        rows.append({"candidate_ref":candidate_ref,"legacy_semantic_ref":legacy,"observed_label_ru":label,"proposed_semantic_id":None if num in BLOCKED else semantic_id(domain, legacy),"proposed_entity_type":entity_type,"domain":domain,"canonical_label_ru_proposal":canon_label,"canonical_definition_ru_proposal":canon_def,"admission_decision":decision,"source_authority_refs":source_refs(num, legacy),"duplicate_gate_basis":["eksamio-learning-engine/273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json","eksamio-learning-engine/266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json"],"prerequisite_ids_proposed":[],"blocked_reason":blocked_reason,"human_admission_required":True})
    return rows

def build_documents():
    rows = build_rows(); ready = [row for row in rows if row["proposed_semantic_id"]]
    ledger = {"schema_version":"0.1.0","date":"2026-08-20","status":"PHASE_2_ADMISSION_REVIEW_COMPLETE_PROPOSAL_NOT_CANONICAL","subject_id":"russian","registry_contract_ref":"eksamio-learning-engine/272-RUSSIAN-UNIFIED-SEMANTIC-IDENTITY-REGISTRY-CONTRACT-v1.0.txt","inventory_ref":"eksamio-learning-engine/273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json","school_denominator_ref":"eksamio-learning-engine/266-RUSSIAN-SCHOOL-FINAL-REFREEZE-AND-FIPI-2026-OVERLAY-CLOSURE-v1.0.json","scope":{"candidate_count":55,"ready_for_human_admission":53,"blocked":2,"blocked_candidate_refs":["candidate-015","candidate-053"],"canonical_school_ids_preserved":185},"rules":["candidate-* refs remain legacy/audit refs and are never canonical semantic IDs.","No proposed ru-* identity is canonical until the human admission gate is completed.","No proposed ru-* identity duplicates an existing school-* identity according to the Phase-1 inventory classification.","Exam task numbers and product IDs are mappings/evidence sources, not identity owners.","No prerequisite edge is proposed in this admission pass.","Blocked candidates remain unresolved rather than being force-fit into the registry."],"entries":rows}
    identities = []
    for row in ready:
        identities.append({"semantic_id":row["proposed_semantic_id"],"subject_id":"russian","entity_type":row["proposed_entity_type"],"canonical_label_ru":row["canonical_label_ru_proposal"],"canonical_definition_ru":row["canonical_definition_ru_proposal"],"domain":row["domain"],"subdomain":None,"parent_ids":[],"prerequisite_ids":[],"aliases":[],"status":"PROPOSED_CANONICAL_PENDING_HUMAN_ADMISSION","source_authority_refs":row["source_authority_refs"],"source_provenance_refs":[f"eksamio-learning-engine/273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json#semantic_candidate::{row['candidate_ref']}"],"school_grade_scope":[],"exam_relevance_flags":["ege"],"legacy_refs":[row["candidate_ref"],row["legacy_semantic_ref"]],"supersedes":[],"superseded_by":[],"notes":"Phase-2 proposal. Human admission is required by registry contract; no prerequisite truth is asserted.","review_status":"SOURCE_REVIEWED_PROPOSAL_PENDING_HUMAN_ADMISSION"})
    registry = {"schema_version":"0.1.0","registry_version":"russian-semantic-registry-proposal-v0.1","date":"2026-08-20","status":"PROPOSAL_NOT_CANONICAL","subject_id":"russian","contract_ref":"eksamio-learning-engine/272-RUSSIAN-UNIFIED-SEMANTIC-IDENTITY-REGISTRY-CONTRACT-v1.0.txt","preserved_school_identity_count":185,"proposed_new_identity_count":53,"blocked_candidate_count":2,"blocked_candidate_refs":["candidate-015","candidate-053"],"admission_gate":"Human project acceptance of a future canonical materialization; this proposal does not self-admit identities.","identities":identities}
    mappings=[]
    for idx,row in enumerate(ready,1):
        mappings.append({"mapping_id":f"ru-phase2-candidate-map-{idx:03d}","source_system":"semantic_candidate","source_object_type":"draft_subject_semantic_candidate","source_id":row["candidate_ref"],"semantic_id":row["proposed_semantic_id"],"relation":"ROUTES_TO","evidence_level":"repository_audited_source_review","mapping_version":"russian-semantic-candidate-crosswalk-proposal-v0.1","valid_from":None,"valid_to":None,"review_status":"PROPOSED_PENDING_HUMAN_ADMISSION","provenance":row["source_authority_refs"]+[f"eksamio-learning-engine/273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json#semantic_candidate::{row['candidate_ref']}"]})
    crosswalk={"schema_version":"0.1.0","date":"2026-08-20","status":"PROPOSAL_NOT_CANONICAL","subject_id":"russian","mapping_version":"russian-semantic-candidate-crosswalk-proposal-v0.1","source_inventory_ref":"eksamio-learning-engine/273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json","registry_proposal_ref":"RUSSIAN-SEMANTIC-REGISTRY-PROPOSAL-v0.1.json","mapping_count":53,"blocked_candidate_refs":["candidate-015","candidate-053"],"rules":["Mappings cover only candidates ready for human admission.","Blocked candidate refs remain unresolved and must not be silently routed.","This Phase-3 proposal does not mutate product objects or draft crosswalk 274."],"mappings":mappings}
    gaps=[
      {"gap_id":"RU-GAP-001","kind":"SEMANTIC_ADMISSION","priority":"P0_RUSSIAN_CURRENT","status":"IN_PROGRESS_PHASE2_PROPOSAL_READY","problem":"55 missing-subject semantic candidates were inventoried in Phase 1 but were not yet admitted into the unified Russian registry.","current_result":{"candidate_count":55,"ready_for_human_admission":53,"blocked":2,"blocked_candidate_refs":["candidate-015","candidate-053"]},"result_refs":["semantic-registry/RUSSIAN-SEMANTIC-CANDIDATE-ADMISSION-LEDGER-v0.1.json","semantic-registry/RUSSIAN-SEMANTIC-REGISTRY-PROPOSAL-v0.1.json","semantic-registry/RUSSIAN-SEMANTIC-CANDIDATE-CROSSWALK-PROPOSAL-v0.1.json"],"closure_gate":["human admission of 53 source-reviewed proposals","resolve candidate-015 source review","resolve candidate-053 granularity","canonical crosswalk materialization after admission"]},
      {"gap_id":"RU-GAP-002","kind":"FOUNDATIONAL_SUBJECT_SCOPE","priority":"NEXT_AFTER_RU_GAP_001","status":"OPEN","modules":["RU-PROG-01","RU-PROG-04","RU-PROG-05","RU-PROG-06"],"problem":"Current inventory does not yet prove complete grades-5-11 canonical coverage for phonetics/graphics, morphemics, word formation and full morphology.","closure_gate":["source-library coverage pass per domain","reuse existing school-/ru-* identity where meaning exists","admit only genuinely missing identities","record provenance and grade scope"]},
      {"gap_id":"RU-GAP-003","kind":"OGE_WRITTEN_RESPONSE_SCOPE","priority":"NEXT_AFTER_FOUNDATIONAL_SCOPE","status":"OPEN","modules":["RU-PROG-15"],"problem":"OGE exposition/compression/written-response competencies are not yet fully canonicalized into route-independent semantic identities.","closure_gate":["official OGE authority decomposition","source-backed semantic admission","route mapping","evidence semantics without inventing official scoring"]},
      {"gap_id":"RU-GAP-004","kind":"CURRENT_EGE_TRAINER_IDENTITY_COVERAGE","priority":"CLOSED","status":"CLOSED_CURRENT_MAIN_AUTHORITY","result_summary":{"COVERED":0,"PARTIALLY_COVERED":144,"NOT_COVERED":41},"result_refs":["RUSSIAN-SCHOOL-TRAINER-COVERAGE-AUDIT-VALIDATION.txt"],"note":"Preserves current-main merged authority; unmerged second-pass proposals are not canonical state."},
      {"gap_id":"RU-GAP-005","kind":"PROGRAM_CONTENT_MATERIALIZATION","priority":"AFTER_REGISTRY_SCOPE","status":"OPEN","modules":"RU-PROG-01..RU-PROG-16","problem":"Not every stable semantic identity has a complete source-backed teach/practice/check bundle.","required_bundle":["canonical explanation","source provenance","worked examples","misconceptions/errors","guided practice","independent practice","mixed/transfer practice","retention items","independent verification items"]},
      {"gap_id":"RU-GAP-006","kind":"PRODUCT_ADAPTER_COMPLETION","priority":"AFTER_CANONICAL_REGISTRY_AND_CONTENT","status":"OPEN","problem":"Generalized semantic evidence adapters are not production-integrated.","closure_gate":["canonical registry slice available","versioned crosswalk available","shared learner evidence/state schemas used","legacy state adapter validated","regression tests pass","production integration separately approved"]},
      {"gap_id":"RU-GAP-007","kind":"SOURCE_BACKED_PREREQUISITE_RELATIONS","priority":"CLOSED_FIRST_VERIFIED_SLICE","status":"CLOSED_AT_VERIFIED_SLICE_LEVEL","result_refs":["verified-slices/RU-SLICE-001-TASK12-CONJUGATION-PARTICIPLE-SOURCE-GATE-v0.1.json","verified-slices/RU-SLICE-001-PREREQUISITE-EDGE-v0.1.json"],"result":"First source-verified conditional REQUIRED edge is materialized for present-tense participle suffix selection; no claim of a complete Russian prerequisite graph."},
      {"gap_id":"RU-GAP-008","kind":"FIRST_VERIFIED_PEIS_SLICE","priority":"CLOSED_REFERENCE_IMPLEMENTATION","status":"CLOSED_AT_REFERENCE_IMPLEMENTATION_LEVEL","result_refs":["verified-slices/RU-SLICE-001-GOLDEN-SCENARIOS-v0.1.json","../peis-reference-kernel/PEIS-REFERENCE-KERNEL-RU-SLICE-001-RUN-v0.1.json","../peis-reference-kernel/PEIS-REFERENCE-KERNEL-VALIDATION.txt"],"result":"RU-SLICE-001 executes source -> identity -> prerequisite -> evidence -> shared PEIS -> NBA -> independent verification with measured ordinal learner-state delta. Production persistence/API remains outside this closure."}
    ]
    gap={"schema_version":"1.2.0","date":"2026-08-20","status":"ACTIVE_GAP_REGISTER_PHASE2_CANONICALIZATION","subject":"russian","program_ref":"RUSSIAN-FULL-SUBJECT-PROGRAM-v1.1.json","supersedes":"RUSSIAN-FULL-SUBJECT-GAP-REGISTER-v1.1.json","baseline_main_sha":"0d5fff2cf25b6a93d60cbd7eac8b61546e29d793","observed_baseline":{"canonical_school_identities":185,"draft_missing_subject_semantic_candidates":55,"phase2_ready_for_human_admission":53,"phase2_blocked_candidates":2,"current_ege_trainer_items":174,"canonical_prerequisite_edge_count_at_first_verified_slice":1,"first_verified_peis_slice":"RU-SLICE-001","shared_reference_kernel":"implemented"},"principles":["Preserve all 185 school-* identities unchanged.","New ru-* identities require source review and human admission; AI does not self-approve canonical truth.","Exam/product/task IDs are routes/evidence sources, not semantic identity owners.","No Russian-specific learner/mastery/readiness/retention/NBA engine.","No production mutation during registry/content materialization."],"phase_status":{"PHASE_1_INVENTORY_CROSSWALK":"COMPLETE","FIRST_VERIFIED_VERTICAL_SLICE":"COMPLETE_REFERENCE_LEVEL","PHASE_2_GAP_CANONICALIZATION":"IN_PROGRESS_PROPOSAL_READY","PHASE_3_VERSIONED_CROSSWALKS":"STARTED_FOR_53_PROPOSALS","PHASE_4_BUILDER_VALIDATION":"STARTED_DETERMINISTIC_MATERIALIZER","PHASE_5_LEARNER_EVIDENCE_ADAPTER":"NOT_STARTED_PRODUCTION","PHASE_6_TUTOR_HOMEWORK_CONSUMPTION":"NOT_STARTED"},"gaps":gaps,"current_next_gate":"RU-GAP-001: human admission of 53 source-reviewed ru-* proposals plus resolution of candidate-015 and candidate-053; then RU-GAP-002 foundational school-domain completion, RU-GAP-003 OGE written-response semantics, and RU-GAP-005 complete content bundles."}
    return ledger,registry,crosswalk,gap

def validate(ledger,registry,crosswalk,gap):
    inventory=load(ENGINE/"273-RUSSIAN-SEMANTIC-IDENTITY-INVENTORY-v0.1.json")
    candidates={obj["source_id"]:obj for obj in inventory["objects"] if obj.get("source_system")=="semantic_candidate"}
    expected={f"candidate-{i:03d}" for i in range(1,56)}
    assert set(candidates)==expected
    assert inventory["active_school_identity_count_observed"]==185
    rows=ledger["entries"]; assert len(rows)==55 and {r["candidate_ref"] for r in rows}==expected
    ready=[r for r in rows if r["proposed_semantic_id"]]; blocked=[r for r in rows if not r["proposed_semantic_id"]]
    assert len(ready)==53 and {r["candidate_ref"] for r in blocked}=={"candidate-015","candidate-053"}
    for row in rows:
        inv=candidates[row["candidate_ref"]]
        assert inv["audit_classification"]=="MISSING_SUBJECT_SEMANTIC_CANDIDATE"
        assert row["legacy_semantic_ref"] in inv["current_semantic_refs"]
        for ref in row["source_authority_refs"]: assert (REPO/ref.split("#",1)[0]).exists(),(row["candidate_ref"],ref)
    assert candidates["candidate-015"]["review_status"]=="needs_review"
    assert candidates["candidate-053"]["review_status"]=="needs_review"
    ids=[i["semantic_id"] for i in registry["identities"]]
    assert len(ids)==len(set(ids))==53 and all(i.startswith("ru-") for i in ids) and not any(i.startswith("school-") for i in ids)
    assert not any(i["prerequisite_ids"] for i in registry["identities"])
    assert {m["source_id"] for m in crosswalk["mappings"]}==expected-{"candidate-015","candidate-053"}
    assert {m["semantic_id"] for m in crosswalk["mappings"]}==set(ids) and crosswalk["mapping_count"]==53
    by_gap={g["gap_id"]:g for g in gap["gaps"]}
    assert by_gap["RU-GAP-007"]["status"]=="CLOSED_AT_VERIFIED_SLICE_LEVEL"
    assert by_gap["RU-GAP-008"]["status"]=="CLOSED_AT_REFERENCE_IMPLEMENTATION_LEVEL"
    assert by_gap["RU-GAP-001"]["status"]=="IN_PROGRESS_PHASE2_PROPOSAL_READY"
    return Counter(r["admission_decision"] for r in rows)

def report(decisions):
    return "\n".join(["RUSSIAN SEMANTIC PHASE 2 VALIDATION v0.1","STATUS: PASS","SCHOOL_CANONICAL_IDS_PRESERVED: 185","CANDIDATES_REVIEWED: 55","READY_FOR_HUMAN_ADMISSION: 53","BLOCKED: 2 (candidate-015, candidate-053)","PROPOSED_RU_IDS: 53 / UNIQUE","PROPOSED_PREREQUISITE_EDGES: 0","CANDIDATE_TO_RU_CROSSWALK_ROWS: 53","RU_GAP_007_FIRST_VERIFIED_EDGE: CLOSED","RU_GAP_008_FIRST_VERIFIED_PEIS_SLICE: CLOSED_REFERENCE_LEVEL","PRODUCTION_INTEGRATION: false","DECISIONS: "+json.dumps(dict(decisions),ensure_ascii=False,sort_keys=True),""])

def main():
    p=argparse.ArgumentParser(); p.add_argument("--write",action="store_true"); args=p.parse_args()
    ledger,registry,crosswalk,gap=build_documents(); decisions=validate(ledger,registry,crosswalk,gap); text=report(decisions)
    if args.write:
        dump(HERE/"RUSSIAN-SEMANTIC-CANDIDATE-ADMISSION-LEDGER-v0.1.json",ledger)
        dump(HERE/"RUSSIAN-SEMANTIC-REGISTRY-PROPOSAL-v0.1.json",registry)
        dump(HERE/"RUSSIAN-SEMANTIC-CANDIDATE-CROSSWALK-PROPOSAL-v0.1.json",crosswalk)
        dump(RUSSIAN_PROGRAM/"RUSSIAN-FULL-SUBJECT-GAP-REGISTER-v1.2.json",gap)
        (HERE/"RUSSIAN-SEMANTIC-PHASE2-VALIDATION.txt").write_text(text,encoding="utf-8")
    print(text)

if __name__=="__main__": main()
