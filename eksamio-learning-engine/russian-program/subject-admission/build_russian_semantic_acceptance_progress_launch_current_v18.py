#!/usr/bin/env python3
"""Current Russian launch progress after exact OGE 2.1 RU01 composite sound-composition acceptance."""
from __future__ import annotations
import argparse, hashlib, json, runpy
from copy import deepcopy
from pathlib import Path

H=Path(__file__).resolve().parent
P=H.parent
BASE=H/"build_russian_semantic_acceptance_progress_launch_current_v17.py"
AUTH=H/"RU01-OGE-2-1-SOUND-COMPOSITION-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
BINDING_REVIEW=H/"build_ru01_phonetics_exact_object_binding_review.py"
PHONETICS_CONTENT=P/"production-learning-content"/"RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"
SOUND_CONTENT=P/"production-learning-content"/"RU-PROG-01-SOUND-COMPOSITION-WAVE-004-v0.1.json"
BASE_HEAD="49725a2d39adc846dffd84871cd8ae22868b8194"; BASE_BLOB="a7163078092de8435b809837d0bb767ad5fc8397"; BASE_SHA="c09969aa4740adb262e6a61fa1645a9497dd2fcc27cf6e8566d1e31dcbd007d5"
PHON_SEM_SHA="47c1ebe7ddb98c043b76367d19b700b5e9ff559d27c251487ab8bddd0b19bf29"; SOUND_SEM_SHA="45b4f5d0e1a7ea0247912ab4cce4c7c6e146b41966a61c18a3ed4c76835ea6ac"; OWNER_RESOLUTION_SHA="c3c01a40b7877ba400bebe2e0de6a2ea503bca4b00eae38b96a02432d4d6bac9"; OBJ_SHA="7fd5397ce39cccd33f25bebb2c00dc673a45b0fa349b6633993d41ea14f85377"
AID="RU01_OGE_2_1_SOUND_COMPOSITION_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
PHON_AID="RU01_PHONETICS_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
SOUND_AID="RU01_SOUND_COMPOSITION_DETERMINATION_BOUNDED_SUBJECT_SEMANTIC_ACCEPTANCE_v0.1"
FEATURE="ru-phonetics-vowel-consonant-features"; COMPOSITION="ru-phonetics-sound-composition-determination"
UNIT="RAU-b6f5dff93864358672bc"; REQ="RSK-OGE_COD-2-1-P010"; GROUP="RUS-SEM-REVIEW-001"; SRC="FIPI-OGE-RU-2026-FINAL"; DOC="OGE_COD"
DOC_SHA="2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a"; LOC="FIPI-OGE-RU-2026-FINAL/OGE_COD p.10 2.1"
FEATURE_EVID=['p01-u2-v1', 'p01-u2-v2']; COMPOSITION_EVID=['p01-u6-v1', 'p01-u6-v2', 'p01-u6-v3', 'p01-u6-v4', 'p01-u6-v5', 'p01-u6-v6']
BASE_SUM={"semantic_units_with_accepted_component_sets":40,"semantic_requirements_with_accepted_component_sets":40,"semantic_units_remaining_without_accepted_component_set":1276,"semantic_requirements_remaining_without_accepted_component_set":1351,"subject_disposed_units_total":41,"subject_disposed_requirements_total":41,"subject_review_units_remaining":1275,"subject_review_requirements_remaining":1350,"canonical_component_refs_reused_unique":120,"review_groups_with_accepted_component_sets":14,"accepted_bounded_ru_route_semantics":9,"accepted_bounded_ru_subject_semantics":69,"accepted_bounded_ru_semantics_total":78,"false_exact_mastery_admissions":0}
AFTER=dict(BASE_SUM); AFTER.update({"semantic_units_with_accepted_component_sets":41,"semantic_requirements_with_accepted_component_sets":41,"semantic_units_remaining_without_accepted_component_set":1275,"semantic_requirements_remaining_without_accepted_component_set":1350,"subject_disposed_units_total":42,"subject_disposed_requirements_total":42,"subject_review_units_remaining":1274,"subject_review_requirements_remaining":1349,"canonical_component_refs_reused_unique":121})

def cj(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def blob(p):
    b=p.read_bytes(); return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def embedded(a):
    if a.get("normalized_sha256")!=OBJ_SHA: raise ValueError("object authority normalized SHA drift")
    x=deepcopy(a); x.pop("normalized_sha256",None)
    if hashlib.sha256(cj(x)).hexdigest()!=OBJ_SHA: raise ValueError("object authority embedded SHA mismatch")
def evidence_ids(path, semantic):
    d=json.loads(path.read_text(encoding="utf-8")); rows=[u for u in d.get("units") or [] if u.get("proposed_semantic_id")==semantic]
    if len(rows)!=1: raise ValueError(f"learner-content semantic missing or duplicated: {semantic}")
    return [x.get("id") for x in rows[0].get("independent_verification") or []]

def build_progress():
    if blob(BASE)!=BASE_BLOB: raise ValueError("current-v17 builder blob drift")
    d=runpy.run_path(str(BASE))["build_progress"]()
    if d.get("schema_version")!="0.20.0" or d.get("normalized_sha256")!=BASE_SHA: raise ValueError("current-v17 authority drift")
    s=d["progress_summary"]
    for k,v in BASE_SUM.items():
        if s.get(k)!=v: raise ValueError(f"current-v17 aggregate drift: {k}")
    if len(d.get("accepted_authorities") or [])!=64: raise ValueError("current-v17 authority count drift")
    prev=d.get("newly_accepted_bounded_subject_semantic") or {}
    if prev.get("semantic_id")!=COMPOSITION or prev.get("target")!={"admission_unit_id":UNIT,"requirement_id":REQ,"source_locator":LOC}: raise ValueError("current-v17 semantic predecessor drift")
    if prev.get("required_component_refs_for_future_exact_object_acceptance")!=[FEATURE,COMPOSITION]: raise ValueError("required component-set predecessor drift")
    if prev.get("independent_verification_item_ids")!=COMPOSITION_EVID: raise ValueError("sound-composition accepted evidence predecessor drift")

    auths={a.get("id"):a for a in d.get("accepted_authorities") or [] if isinstance(a,dict)}
    if (auths.get(PHON_AID) or {}).get("sha256")!=PHON_SEM_SHA: raise ValueError("existing phonetics semantic authority drift")
    if (auths.get(SOUND_AID) or {}).get("sha256")!=SOUND_SEM_SHA: raise ValueError("sound-composition semantic authority drift")
    if evidence_ids(PHONETICS_CONTENT,FEATURE)!=FEATURE_EVID: raise ValueError("vowel/consonant feature independent evidence drift")
    if evidence_ids(SOUND_CONTENT,COMPOSITION)!=COMPOSITION_EVID: raise ValueError("sound-composition independent evidence drift")
    if set(FEATURE_EVID)&set(COMPOSITION_EVID): raise ValueError("component evidence overlap opened")

    review=runpy.run_path(str(BINDING_REVIEW))["build_review"]()
    rows=[r for r in review.get("records") or [] if r.get("admission_unit_id")==UNIT and r.get("requirement_id")==REQ]
    if len(rows)!=1: raise ValueError("target binding review record missing or duplicated")
    rr=rows[0]
    exact={"source_id":SRC,"document_id":DOC,"page":10,"code":"2.1","source_locator":LOC,"normalized_source_signature":"SOUND_IDENTIFICATION_FEATURES_COMPOSITION","review_classification":"COMPOSITE","accepted_semantic_refs":[FEATURE],"blocker_or_reroute":"SOUND_COMPOSITION_FACET_UNBOUND"}
    for k,v in exact.items():
        if rr.get(k)!=v: raise ValueError(f"target binding review drift: {k}")

    a=json.loads(AUTH.read_text(encoding="utf-8")); embedded(a)
    if a.get("status")!="CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_OGE_2_1_SOUND_COMPOSITION_CANONICAL_COMPONENT_SET": raise ValueError("object authority status drift")
    if a.get("current_launch_progress_v17_base_head_sha")!=BASE_HEAD or a.get("current_launch_progress_v17_normalized_sha256")!=BASE_SHA: raise ValueError("object authority base drift")
    if a.get("exact_owner_resolution_normalized_sha256")!=OWNER_RESOLUTION_SHA or a.get("existing_phonetics_semantic_acceptance_authority_sha256")!=PHON_SEM_SHA or a.get("sound_composition_semantic_acceptance_authority_sha256")!=SOUND_SEM_SHA: raise ValueError("object authority provenance drift")
    q=a.get("decision") or {}
    exact_dec={"admission_unit_id":UNIT,"requirement_id":REQ,"packet_group":GROUP,"source_id":SRC,"document_id":DOC,"document_sha256":DOC_SHA,"page":10,"content_code":"2.1","source_locator":LOC,"normalized_source_signature":"SOUND_IDENTIFICATION_FEATURES_COMPOSITION","module_id":"RU-PROG-01","source_review_classification":"COMPOSITE","canonical_component_refs":[FEATURE,COMPOSITION],"component_count":2,"component_specific_independent_evidence":{FEATURE:FEATURE_EVID,COMPOSITION:COMPOSITION_EVID},"independent_evidence_items":8,"subject_semantic_status":"CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"}
    for k,v in exact_dec.items():
        if q.get(k)!=v: raise ValueError(f"object identity drift: {k}")
    m=q.get("mastery_boundary") or {}
    for k in ("accepted_bounded_subject_semantics_required_for_both_components","component_specific_independent_evidence_required","validated_exact_component_item_may_support_only_its_single_canonical_ref","sound_composition_mastery_requires_established_spoken_realization"):
        if m.get(k) is not True: raise ValueError(f"mastery boundary weakened: {k}")
    for k in ("generic_ru01_attempt_can_emit_exact_component_mastery","vowel_consonant_features_evidence_can_substitute_for_sound_composition","sound_composition_evidence_can_substitute_for_vowel_consonant_features","sound_letter_relation_evidence_can_substitute_for_either_component","word_analysis_evidence_can_substitute_for_either_component","phonetic_transcription_evidence_can_substitute_for_either_component","sound_changes_evidence_can_substitute_for_either_component","normative_pronunciation_or_stress_evidence_can_substitute_for_either_component","unknown_normative_pronunciation_can_be_inferred_from_spelling","single_component_success_can_close_composite_source_object"):
        if m.get(k) is not False: raise ValueError(f"mastery boundary weakened: {k}")
    pol=a.get("policy") or {}
    if pol.get("whole_group_acceptance_allowed") is not False or pol.get("task_module_route_title_keyword_fuzzy_or_embedding_inference_allowed") is not False or pol.get("single_component_object_closure_allowed") is not False or pol.get("false_exact_mastery_admissions")!=0: raise ValueError("object policy boundary drift")
    if (a.get("summary") or {}).get("false_exact_mastery_admissions")!=0 or (a.get("summary") or {}).get("sibling_ru01_source_objects_accepted")!=0: raise ValueError("false mastery or sibling leakage")

    gs=[g for g in d["semantic_review_groups"] if g.get("group_id")==GROUP]
    if len(gs)!=1: raise ValueError("RU01 group not unique")
    g=gs[0]
    if g.get("accepted_component_set_count")!=11 or UNIT not in set(map(str,g.get("admission_unit_ids") or [])): raise ValueError("RU01 group drift")
    reqs=[r for r in g.get("requirements") or [] if r.get("requirement_id")==REQ]
    if len(reqs)!=1: raise ValueError("target requirement not unique")
    r=reqs[0]
    for k,v in (("source_id",SRC),("document_id",DOC),("page",10),("code","2.1"),("source_locator",LOC)):
        if r.get(k)!=v: raise ValueError(f"target source identity drift: {k}")
    sets=[i for gg in d["semantic_review_groups"] for i in gg.get("accepted_component_sets") or [] if isinstance(i,dict)]
    if any(i.get("admission_unit_id")==UNIT or i.get("requirement_id")==REQ for i in sets): raise ValueError("target already accepted")

    g["accepted_component_sets"].append({"accepted_authority_id":AID,"admission_unit_id":UNIT,"requirement_id":REQ,"packet_group":GROUP,"source_id":SRC,"document_id":DOC,"content_code":"2.1","source_locator":LOC,"modules":["RU-PROG-01"],"canonical_component_refs":[FEATURE,COMPOSITION],"component_count":2,"authority":{"base_current_v17_normalized_sha256":BASE_SHA,"existing_phonetics_semantic_acceptance_authority_sha256":PHON_SEM_SHA,"sound_composition_semantic_acceptance_authority_sha256":SOUND_SEM_SHA,"exact_owner_resolution_normalized_sha256":OWNER_RESOLUTION_SHA,"accepted_authority_normalized_sha256":OBJ_SHA,"component_specific_independent_evidence_items":8},"mastery_boundary":deepcopy(m),"subject_semantic_status":"CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"})
    g["accepted_component_set_count"]=len(g["accepted_component_sets"])
    if g["accepted_component_set_count"]!=12: raise ValueError("accepted-set count drift")
    g["status"]="SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
    g["remaining_group_action"]="CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"
    d["accepted_authorities"].append({"id":AID,"authority_kind":"OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET","sha256":OBJ_SHA,"status":a["status"],"accepted_admission_units":1,"accepted_requirements":1,"canonical_component_refs":2,"accepted_route_semantics":0,"accepted_subject_semantics":0,"semantic_identity_admissions":0})
    for k,x in (("semantic_units_with_accepted_component_sets",1),("semantic_requirements_with_accepted_component_sets",1),("semantic_units_remaining_without_accepted_component_set",-1),("semantic_requirements_remaining_without_accepted_component_set",-1),("subject_disposed_units_total",1),("subject_disposed_requirements_total",1),("subject_review_units_remaining",-1),("subject_review_requirements_remaining",-1)): s[k]+=x
    s["canonical_component_refs_reused_unique"]=len({z for gg in d["semantic_review_groups"] for i in gg.get("accepted_component_sets") or [] for z in i.get("canonical_component_refs") or []})
    for k,v in AFTER.items():
        if s.get(k)!=v: raise ValueError(f"post-OGE-2.1 aggregate drift: {k}")
    if len(d["accepted_authorities"])!=65 or s["false_exact_mastery_admissions"]!=0: raise ValueError("final authority/mastery drift")

    d["schema_version"]="0.21.0"
    d["base_current_launch_progress_v17_head_sha"]=BASE_HEAD
    d["base_current_launch_progress_v17_builder_git_blob_sha1"]=BASE_BLOB
    d["base_current_launch_progress_v17_normalized_sha256"]=BASE_SHA
    d["newly_accepted_exact_object"]={"accepted_authority_id":AID,"admission_unit_id":UNIT,"requirement_id":REQ,"accepted_component_refs":[FEATURE,COMPOSITION],"component_specific_independent_evidence":{FEATURE:FEATURE_EVID,COMPOSITION:COMPOSITION_EVID},"independent_evidence_items":8,"source_review_classification":"COMPOSITE","sibling_source_objects_accepted":0}
    d.setdefault("policy",{})["ru01_oge_2_1_exact_object_requires_both_bounded_subject_semantics"]=True
    d["policy"]["ru01_oge_2_1_exact_object_requires_component_specific_independent_evidence_for_each_component"]=True
    d["policy"]["ru01_oge_2_1_single_component_success_can_close_composite_object"]=False
    d["policy"]["generic_ru01_attempt_can_emit_exact_oge_2_1_mastery"]=False
    d["policy"]["unknown_normative_pronunciation_can_be_inferred_from_spelling_for_sound_composition"]=False
    d.pop("normalized_sha256",None); d["normalized_sha256"]=hashlib.sha256(cj(d)).hexdigest(); return d

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output"); p.add_argument("--emit",action="store_true"); a=p.parse_args(); d=build_progress()
    if a.output: Path(a.output).write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    if a.emit: print(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":")))
    else:
        s=d["progress_summary"]; print("RUSSIAN_RU01_OGE_2_1_SOUND_COMPOSITION_EXACT_OBJECT_ACCEPTANCE=PASS"); print("ACCEPTED_UNIT="+UNIT); print("ACCEPTED_REQUIREMENT="+REQ); print("EXACT_COMPONENT_REFS=2"); print("INDEPENDENT_EVIDENCE_ITEMS=8"); print("ADDITIONAL_SIBLING_RU01_OBJECTS_ACCEPTED=0"); print(f"ACCEPTED_AUTHORITIES={len(d['accepted_authorities'])}"); print(f"SUBJECT_REVIEW_UNITS_REMAINING={s['subject_review_units_remaining']}"); print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={s['subject_review_requirements_remaining']}"); print(f"FALSE_EXACT_MASTERY={s['false_exact_mastery_admissions']}"); print("NORMALIZED_SHA256="+d["normalized_sha256"])
    return 0
if __name__=="__main__": raise SystemExit(main())
