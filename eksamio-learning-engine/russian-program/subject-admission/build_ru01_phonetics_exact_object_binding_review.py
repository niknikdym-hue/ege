#!/usr/bin/env python3
"""Fail-closed exact binding review for residual RU01 phonetics objects."""
from __future__ import annotations
import argparse, hashlib, json, runpy
from pathlib import Path

H=Path(__file__).resolve().parent
CUR=H/'build_russian_semantic_acceptance_progress_launch_current_v2.py'
ACC=H/'RU01-PHONETICS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json'
IDX=H.parent/'source-knowledge'/'RUSSIAN-OFFICIAL-REQUIREMENTS-INDEX-v1.0.json'
ACCT=H/'build_russian_subject_accounting_complete.py'
CUR_SHA='f25202c09baf0452fce2392726ddb02ce8a17dd111851f25f58e5334e873a4c7'
BR_SHA='ea5d4ac01fcb8a51847a8a278746dccb6ac455e8720c795c839fdefe0a8e8f3f'
GID='RUS-SEM-REVIEW-001'; DU='RAU-532ee826fbf30b195484'; DR='RSK-OGE_COD-6-1-P024'
WORD='ru-phonetics-word-analysis-sequence'
SEM={'ru-phonetics-sound-letter-relation','ru-phonetics-vowel-consonant-features',WORD}
DOC={
'EDSOO59':('EDSOO-RU-5-9-2025','1d2f68b5e77e7b67fccd52ce0fed36d84141dc719e50db7b225f40b1313eeb0d'),
'EDSOO1011':('EDSOO-RU-10-11-BASIC-2025','6be6b29f4512627c5a9510a0fb6ff6e6e5b7d81718564f19e361eaab4ef00bd6'),
'OGE_COD':('FIPI-OGE-RU-2026-FINAL','2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a'),
'EGE_COD':('FIPI-EGE-RU-2026-FINAL','c5a886b39b659df827f8766b71a99cb1c04140c4a506ccd32d952a021efc046f')}
# unit|requirement|document|page|code|short source signature|class|accepted refs comma-separated|blocker/reroute
DATA='''
RAU-043ae3d307ad5fd95639|RSK-EDSOO59-4-2-P181|EDSOO59|181|4.2|PHONETIC_WORD_ANALYSIS|READY|ru-phonetics-word-analysis-sequence|
RAU-0985ee43535361c09cd9|RSK-EDSOO59-4-1-7-P187|EDSOO59|187|4.1.7|PHONETIC_WORD_ANALYSIS|READY|ru-phonetics-word-analysis-sequence|
RAU-3e5308ed79e62fc16e94|RSK-EDSOO59-4-24-P196|EDSOO59|196|4.24|PHONETIC_WORD_ANALYSIS|READY|ru-phonetics-word-analysis-sequence|
RAU-8e357e9bbe18a741725c|RSK-EDSOO1011-2-2-1-P074|EDSOO1011|74|2.2.1|PHONETIC_WORD_ANALYSIS|READY|ru-phonetics-word-analysis-sequence|
RAU-cb307f6635d27f73fa88|RSK-EDSOO1011-2-2-2-P078|EDSOO1011|78|2.2.2|PHONETIC_WORD_ANALYSIS|READY|ru-phonetics-word-analysis-sequence|
RAU-df45aa3b99e1baefca01|RSK-OGE_COD-3-1-P014|OGE_COD|14|3.1|PHONETIC_WORD_ANALYSIS|READY|ru-phonetics-word-analysis-sequence|
RAU-f3896151ffac143c05da|RSK-OGE_COD-4-1-7-P021|OGE_COD|21|4.1.7|PHONETIC_WORD_ANALYSIS|READY|ru-phonetics-word-analysis-sequence|
RAU-5a6511267f156745f93c|RSK-EDSOO59-4-1-P181|EDSOO59|181|4.1|SOUND_LETTER_AND_SOUND_SYSTEM|PARTIAL|ru-phonetics-sound-letter-relation,ru-phonetics-vowel-consonant-features|SIBLING_BROAD_HEADER
RAU-5a6511267f156745f93c|RSK-EDSOO59-4-1-P187|EDSOO59|187|4.1|PHONETICS_GRAPHICS_HEADER|PENDING||BROAD_HEADER_INCOMPLETE
RAU-b6f5dff93864358672bc|RSK-OGE_COD-2-1-P010|OGE_COD|10|2.1|SOUND_IDENTIFICATION_FEATURES_COMPOSITION|COMPOSITE|ru-phonetics-vowel-consonant-features|SOUND_COMPOSITION_FACET_UNBOUND
RAU-2725ee5b709b70502748|RSK-EDSOO59-4-1-4-P187|EDSOO59|187|4.1.4|PHONETIC_TRANSCRIPTION|PENDING||TRANSCRIPTION_SEMANTIC_REQUIRED
RAU-b1ba48cb81e96255122a|RSK-EDSOO59-4-1-3-P187|EDSOO59|187|4.1.3|SOUND_CHANGES_IN_SPEECH_FLOW|PENDING||SOUND_CHANGES_SEMANTIC_REQUIRED
RAU-3916b5e3da77ed038830|RSK-OGE_COD-4-1-P020|OGE_COD|20|4.1|PHONETICS_GRAPHICS_HEADER|PENDING||BROAD_HEADER_INCOMPLETE
RAU-f12c55d19d60877d22ef|RSK-OGE_COD-4-1-4-P021|OGE_COD|21|4.1.4|PHONETIC_TRANSCRIPTION|PENDING||TRANSCRIPTION_SEMANTIC_REQUIRED
RAU-f709f1855bb0b8d104bc|RSK-OGE_COD-4-1-3-P021|OGE_COD|21|4.1.3|SOUND_CHANGES_IN_SPEECH_FLOW|PENDING||SOUND_CHANGES_SEMANTIC_REQUIRED
RAU-0a6c57b411726cc7cf0c|RSK-EDSOO1011-2-6-6-P079|EDSOO1011|79|2.6.6|ORTHOGRAPHY_I_Y_AFTER_PREFIXES|REROUTE||ORTHOGRAPHY
RAU-23a73ecd845411739f6d|RSK-EGE_COD-3-7-1-P007|EGE_COD|7|3.7.1|ORTHOGRAPHY_UPPERCASE_LOWERCASE|REROUTE||ORTHOGRAPHY
RAU-5dec2ed9657f263f91ff|RSK-EDSOO59-6-1-P191|EDSOO59|191|6.1|ORTHOGRAM_CONCEPT|REROUTE||ORTHOGRAPHY
RAU-6c959b5c82028e50dd34|RSK-OGE_COD-4-18-4-P022|OGE_COD|22|4.18.4|ONOMATOPOEIC_WORDS|REROUTE||MORPHOLOGY_ONOMATOPOEIA
RAU-ee34e4676a578b003696|RSK-EDSOO59-4-9-4-P210|EDSOO59|210|4.9.4|ONOMATOPOEIC_WORDS|REROUTE||MORPHOLOGY_ONOMATOPOEIA
RAU-f2beb8071d88472ac727|RSK-EDSOO59-4-29-P205|EDSOO59|205|4.29|ONOMATOPOEIC_WORDS|REROUTE||MORPHOLOGY_ONOMATOPOEIA
'''.strip()

def rows():
    out=[]
    for line in DATA.splitlines():
        u,r,d,p,c,s,k,refs,b=line.split('|'); src,sha=DOC[d]
        out.append({'admission_unit_id':u,'requirement_id':r,'source_id':src,'document_id':d,'document_sha256':sha,'page':int(p),'code':c,'source_locator':f'{src}/{d} p.{p} {c}','normalized_source_signature':s,'review_classification':k,'accepted_semantic_refs':refs.split(',') if refs else [],'blocker_or_reroute':b or None})
    return out

def cj(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def input_sha(): return hashlib.sha256(cj({'documents':DOC,'data':DATA,'source_prose_committed':False,'fuzzy':False})).hexdigest()
def find_docs(v):
    if isinstance(v,dict):
        x=v.get('documents')
        if isinstance(x,list) and any(isinstance(r,dict) and 'document_id' in r and 'sha256' in r for r in x): return x
        for z in v.values():
            q=find_docs(z)
            if q:return q
    elif isinstance(v,list):
        for z in v:
            q=find_docs(z)
            if q:return q
    return []

def build_review():
    cur=runpy.run_path(str(CUR))['build_progress'](); s=cur['progress_summary']
    assert cur['normalized_sha256']==CUR_SHA and len(cur['accepted_authorities'])==49
    assert (s['subject_disposed_units_total'],s['subject_disposed_requirements_total'],s['subject_review_units_remaining'],s['subject_review_requirements_remaining'],s['false_exact_mastery_admissions'])==(29,29,1287,1362,0)
    g=[x for x in cur['semantic_review_groups'] if x['group_id']==GID]; assert len(g)==1; g=g[0]
    assert (g['admission_unit_count'],g['requirement_count'],g['accepted_component_set_count'],g['accepted_nonsemantic_object_disposition_count'])==(21,22,0,1)
    disp=g['accepted_nonsemantic_object_dispositions']; assert len(disp)==1 and disp[0]['admission_unit_id']==DU and disp[0]['requirement_id']==DR and disp[0]['disposition']=='ROUTE_OR_FORMAT_ONLY' and disp[0]['canonical_component_refs']==[] and disp[0]['bounded_ru_semantic_refs']==[]

    acc=json.loads(ACC.read_text()); assert acc['status']=='CENTRAL_BRAIN_ACCEPTED_RU01_PHONETICS_BOUNDED_SUBJECT_SEMANTICS' and acc['authority']['boundary_review_normalized_sha256']==BR_SHA
    assert {x['accepted_semantic_id'] for x in acc['decisions']}==SEM and acc['summary']['object_level_admission_units_closed']==0 and acc['summary']['false_exact_mastery_admissions']==0
    indexed={x['document_id']:x for x in find_docs(json.loads(IDX.read_text()))}
    for d,(src,sha) in DOC.items(): assert indexed[d]['source_id']==src and indexed[d]['sha256']==sha

    rr=rows(); gr={x['requirement_id']:x for x in g['requirements']}; units=set(g['admission_unit_ids'])-{DU}; reqs=set(gr)-{DR}
    assert len(rr)==21 and {x['admission_unit_id'] for x in rr}==units and {x['requirement_id'] for x in rr}==reqs and len(units)==20 and len(reqs)==21
    acct=runpy.run_path(str(ACCT))['build_accounting'](); assert acct['summary']['accepted_classification_units']==1325 and acct['summary']['accepted_classification_requirements']==1400
    ar={x['admission_unit_id']:x for x in acct['dispositions']}
    for x in rr:
        q=gr[x['requirement_id']]
        for k in ('source_id','document_id','page','code','source_locator'): assert q[k]==x[k]
        assert set(x['accepted_semantic_refs'])<=SEM
        assert ar[x['admission_unit_id']]['disposition']=='PARTIAL_OR_COMPOSITE'
        assert x['requirement_id'] in {m['requirement_id'] for m in ar[x['admission_unit_id']]['members']}

    by={}
    for x in rr: by.setdefault(x['admission_unit_id'],[]).append(x)
    outcomes=[]
    for u,xs in sorted(by.items()):
        ks={x['review_classification'] for x in xs}
        o='EXACT_REUSE_READY' if ks=={'READY'} else 'REROUTE_OUT_OF_RU01' if ks=={'REROUTE'} else 'PENDING_EXACT_DECOMPOSITION'
        outcomes.append({'admission_unit_id':u,'requirement_ids':sorted(x['requirement_id'] for x in xs),'unit_review_outcome':o})
    oc={k:sum(x['unit_review_outcome']==k for x in outcomes) for k in ('EXACT_REUSE_READY','REROUTE_OUT_OF_RU01','PENDING_EXACT_DECOMPOSITION')}; assert oc=={'EXACT_REUSE_READY':7,'REROUTE_OUT_OF_RU01':6,'PENDING_EXACT_DECOMPOSITION':7}
    ready=[x for x in rr if x['review_classification']=='READY']; rer=[x for x in rr if x['review_classification']=='REROUTE']; assert len(ready)==7 and all(x['accepted_semantic_refs']==[WORD] for x in ready) and len(rer)==6
    out={'schema_version':'0.1.0','status':'CENTRAL_BRAIN_RU01_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED','current_launch_progress_sha256':CUR_SHA,'source_review_input_sha256':input_sha(),'accepted_semantic_ids':sorted(SEM),'source_documents':[{'document_id':d,'source_id':v[0],'sha256':v[1]} for d,v in sorted(DOC.items())],'records':rr,'unit_outcomes':outcomes,'exact_reuse_ready':{'semantic_id':WORD,'admission_unit_ids':sorted(x['admission_unit_id'] for x in ready),'requirement_ids':sorted(x['requirement_id'] for x in ready),'units':7,'requirements':7,'separate_object_acceptance_required':True,'object_closures_by_this_review':0},'reroute_out_of_ru01':{'units':6,'requirements':6,'records':[{'admission_unit_id':x['admission_unit_id'],'requirement_id':x['requirement_id'],'target_domain':x['blocker_or_reroute']} for x in rer]},'pending_exact_decomposition':{'units':7,'requirements':8},'policy':{'review_is_acceptance':False,'review_can_reduce_object_counts':False,'review_can_create_school_identity':False,'review_can_create_ru_semantic_identity':False,'whole_group_acceptance_allowed':False,'source_prose_committed':False,'keyword_or_fuzzy_inference_allowed':False,'generic_group_attempt_can_emit_exact_component_mastery':False},'summary':{'reviewed_residual_units':20,'reviewed_residual_requirements':21,'exact_reuse_ready_units':7,'exact_reuse_ready_requirements':7,'reroute_out_of_ru01_units':6,'reroute_out_of_ru01_requirements':6,'pending_exact_decomposition_units':7,'pending_exact_decomposition_requirements':8,'object_level_admission_units_closed':0,'object_level_requirements_closed':0,'new_school_canonical_identities':0,'new_ru_semantic_identities':0,'false_exact_mastery_admissions':0,'current_subject_review_units_remaining':1287,'current_subject_review_requirements_remaining':1362}}
    out['normalized_sha256']=hashlib.sha256(cj(out)).hexdigest(); return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--output');p.add_argument('--emit',action='store_true');a=p.parse_args();r=build_review()
    if a.output:Path(a.output).write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
    if a.emit:print(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    else:
        s=r['summary'];print('RU01_PHONETICS_EXACT_OBJECT_BINDING_REVIEW=PASS')
        for k in ('reviewed_residual_units','reviewed_residual_requirements','exact_reuse_ready_units','exact_reuse_ready_requirements','reroute_out_of_ru01_units','reroute_out_of_ru01_requirements','pending_exact_decomposition_units','pending_exact_decomposition_requirements','object_level_admission_units_closed','false_exact_mastery_admissions','current_subject_review_units_remaining','current_subject_review_requirements_remaining'):print(f'{k.upper()}={s[k]}')
        print('SOURCE_REVIEW_INPUT_SHA256='+r['source_review_input_sha256']);print('normalized_sha256='+r['normalized_sha256'])
    return 0
if __name__=='__main__':raise SystemExit(main())
