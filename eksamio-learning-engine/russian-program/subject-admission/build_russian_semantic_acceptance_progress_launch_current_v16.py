#!/usr/bin/env python3
"""Current Russian launch progress after exact OGE P021 RU01 sound-changes object acceptance."""
from __future__ import annotations
import argparse, hashlib, json, runpy
from copy import deepcopy
from pathlib import Path

H=Path(__file__).resolve().parent
BASE=H/"build_russian_semantic_acceptance_progress_launch_current_v15.py"
AUTH=H/"RU01-SOUND-CHANGES-OGE-P021-4-1-3-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
BASE_HEAD="90b373cb5c268eaf9d17982d2f656625fb9f8c0a"; BASE_BLOB="d2fc2495d67e6f08fe32b076fcc8c785efb3f519"; BASE_SHA="7786e2ddf2d622d39be0eb087cdb9eb4c817386a2a437b61eb98005df477445d"
SEM_SHA="f2583aea8da9b3b79e68ba30a9a68559b9cbe1b6fb6e0aeafc4bf3c0d653c63d"; REF_SHA="992c07da724f734a28cdbd4bf058c1240826b5a3c94ee1eef55b2c8791d43de7"; OBJ_SHA="abda0a950ac17d8fa8809309834a4724f751a6b5d51a21b859e5c31f093e1b3a"
AID="RU01_SOUND_CHANGES_OGE_P021_4_1_3_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
REF_AID="RU01_SOUND_CHANGES_P187_4_1_3_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
SEM="ru-phonetics-sound-changes-in-speech-flow"
UNIT="RAU-f709f1855bb0b8d104bc"; REQ="RSK-OGE_COD-4-1-3-P021"
REF_UNIT="RAU-b1ba48cb81e96255122a"; REF_REQ="RSK-EDSOO59-4-1-3-P187"
GROUP="RUS-SEM-REVIEW-001"; SRC="FIPI-OGE-RU-2026-FINAL"; DOC="OGE_COD"
DOC_SHA="2d83e987ddad08d405827f98dfa490721f2d67b787b2803d8c499eea7b84858a"
LOC="FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.3"; EVID=[f"p01-u5-v{i}" for i in range(1,7)]
BASE_SUM={"semantic_units_with_accepted_component_sets":39,"semantic_requirements_with_accepted_component_sets":39,"semantic_units_remaining_without_accepted_component_set":1277,"semantic_requirements_remaining_without_accepted_component_set":1352,"subject_disposed_units_total":40,"subject_disposed_requirements_total":40,"subject_review_units_remaining":1276,"subject_review_requirements_remaining":1351,"canonical_component_refs_reused_unique":120,"review_groups_with_accepted_component_sets":14,"accepted_bounded_ru_route_semantics":9,"accepted_bounded_ru_subject_semantics":68,"accepted_bounded_ru_semantics_total":77,"false_exact_mastery_admissions":0}
AFTER=dict(BASE_SUM); AFTER.update({"semantic_units_with_accepted_component_sets":40,"semantic_requirements_with_accepted_component_sets":40,"semantic_units_remaining_without_accepted_component_set":1276,"semantic_requirements_remaining_without_accepted_component_set":1351,"subject_disposed_units_total":41,"subject_disposed_requirements_total":41,"subject_review_units_remaining":1275,"subject_review_requirements_remaining":1350})

def cj(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
def blob(p):
    b=p.read_bytes(); return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def embedded(a):
    if a.get("normalized_sha256")!=OBJ_SHA: raise ValueError("object authority normalized SHA drift")
    x=deepcopy(a); x.pop("normalized_sha256",None)
    if hashlib.sha256(cj(x)).hexdigest()!=OBJ_SHA: raise ValueError("object authority embedded SHA mismatch")

def build_progress():
    if blob(BASE)!=BASE_BLOB: raise ValueError("current-v15 builder blob drift")
    d=runpy.run_path(str(BASE))["build_progress"]()
    if d.get("schema_version")!="0.18.0" or d.get("normalized_sha256")!=BASE_SHA: raise ValueError("current-v15 authority drift")
    s=d["progress_summary"]
    for k,v in BASE_SUM.items():
        if s.get(k)!=v: raise ValueError(f"current-v15 aggregate drift: {k}")
    if len(d.get("accepted_authorities") or [])!=62: raise ValueError("current-v15 authority count drift")
    p=d.get("newly_accepted_exact_object") or {}
    if (p.get("accepted_authority_id"),p.get("admission_unit_id"),p.get("requirement_id"),p.get("accepted_semantic_ref"),p.get("component_specific_independent_evidence_ids"))!=(REF_AID,REF_UNIT,REF_REQ,SEM,EVID): raise ValueError("current-v15 predecessor drift")
    if p.get("remaining_same_signature_target")!={"admission_unit_id":UNIT,"requirement_id":REQ,"status":"PENDING_SEPARATE_EXACT_OBJECT_ACCEPTANCE"}: raise ValueError("current-v15 remaining target drift")
    refs=[a for a in d["accepted_authorities"] if a.get("id")==REF_AID]
    if len(refs)!=1 or refs[0].get("sha256")!=REF_SHA: raise ValueError("accepted reference authority drift")

    a=json.loads(AUTH.read_text(encoding="utf-8")); embedded(a)
    if a.get("status")!="CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_SOUND_CHANGES_CANONICAL_COMPONENT_SET" or a.get("current_launch_progress_v15_base_head_sha")!=BASE_HEAD or a.get("current_launch_progress_v15_normalized_sha256")!=BASE_SHA or a.get("semantic_acceptance_authority_sha256")!=SEM_SHA or a.get("accepted_reference_object_authority_sha256")!=REF_SHA: raise ValueError("object authority binding drift")
    q=a.get("decision") or {}
    exact={"admission_unit_id":UNIT,"requirement_id":REQ,"packet_group":GROUP,"source_id":SRC,"document_id":DOC,"document_sha256":DOC_SHA,"page":21,"content_code":"4.1.3","source_locator":LOC,"normalized_source_signature":"SOUND_CHANGES_IN_SPEECH_FLOW","module_id":"RU-PROG-01","canonical_component_refs":[SEM],"component_count":1,"component_specific_independent_evidence":{SEM:EVID},"independent_evidence_items":6,"subject_semantic_status":"CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"}
    for k,v in exact.items():
        if q.get(k)!=v: raise ValueError(f"object identity drift: {k}")
    m=q.get("mastery_boundary") or {}
    for k in ("accepted_bounded_subject_semantic_required","component_specific_independent_evidence_required","prior_same_signature_object_acceptance_required","validated_sound_changes_item_may_support_only_its_single_canonical_ref"):
        if m.get(k) is not True: raise ValueError(f"mastery boundary weakened: {k}")
    for k in ("generic_ru01_attempt_can_emit_exact_component_mastery","sound_letter_relation_evidence_can_substitute_for_sound_changes","vowel_consonant_features_evidence_can_substitute_for_sound_changes","word_analysis_evidence_can_substitute_for_sound_changes","phonetic_transcription_evidence_can_substitute_for_sound_changes","normative_pronunciation_or_stress_evidence_can_substitute_for_sound_changes","shared_evidence_can_close_sibling_source_objects_without_separate_acceptance"):
        if m.get(k) is not False: raise ValueError(f"mastery boundary weakened: {k}")
    pol=a.get("policy") or {}
    if pol.get("whole_group_acceptance_allowed") is not False or pol.get("task_module_route_title_keyword_fuzzy_or_embedding_inference_allowed") is not False or pol.get("false_exact_mastery_admissions")!=0: raise ValueError("object policy boundary drift")
    if (a.get("summary") or {}).get("sibling_ru01_source_objects_accepted")!=0 or (a.get("summary") or {}).get("false_exact_mastery_admissions")!=0: raise ValueError("false mastery or sibling leakage")

    gs=[g for g in d["semantic_review_groups"] if g.get("group_id")==GROUP]
    if len(gs)!=1: raise ValueError("RU01 group not unique")
    g=gs[0]
    if g.get("accepted_component_set_count")!=10 or UNIT not in set(map(str,g.get("admission_unit_ids") or [])): raise ValueError("RU01 group drift")
    rows=[r for r in g.get("requirements") or [] if r.get("requirement_id")==REQ]
    if len(rows)!=1: raise ValueError("target requirement not unique")
    r=rows[0]
    for k,v in (("source_id",SRC),("document_id",DOC),("page",21),("code","4.1.3"),("source_locator",LOC)):
        if r.get(k)!=v: raise ValueError(f"target source identity drift: {k}")
    sets=[i for gg in d["semantic_review_groups"] for i in gg.get("accepted_component_sets") or [] if isinstance(i,dict)]
    if any(i.get("admission_unit_id")==UNIT or i.get("requirement_id")==REQ for i in sets): raise ValueError("target already accepted")
    prior=[i for i in sets if i.get("admission_unit_id")==REF_UNIT and i.get("requirement_id")==REF_REQ]
    if len(prior)!=1 or prior[0].get("accepted_authority_id")!=REF_AID or prior[0].get("canonical_component_refs")!=[SEM]: raise ValueError("accepted same-signature reference object absent")

    g["accepted_component_sets"].append({"accepted_authority_id":AID,"admission_unit_id":UNIT,"requirement_id":REQ,"packet_group":GROUP,"source_id":SRC,"document_id":DOC,"content_code":"4.1.3","source_locator":LOC,"modules":["RU-PROG-01"],"canonical_component_refs":[SEM],"component_count":1,"authority":{"base_current_v15_normalized_sha256":BASE_SHA,"accepted_subject_semantic_authority_sha256":SEM_SHA,"accepted_reference_object_authority_sha256":REF_SHA,"accepted_authority_normalized_sha256":OBJ_SHA,"component_specific_independent_evidence_items":6},"mastery_boundary":deepcopy(m),"subject_semantic_status":"CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"})
    g["accepted_component_set_count"]=len(g["accepted_component_sets"])
    if g["accepted_component_set_count"]!=11: raise ValueError("accepted-set count drift")
    g["status"]="SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
    g["remaining_group_action"]="CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"
    d["accepted_authorities"].append({"id":AID,"authority_kind":"OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET","sha256":OBJ_SHA,"status":a["status"],"accepted_admission_units":1,"accepted_requirements":1,"canonical_component_refs":1,"accepted_route_semantics":0,"accepted_subject_semantics":0,"semantic_identity_admissions":0})
    for k,x in (("semantic_units_with_accepted_component_sets",1),("semantic_requirements_with_accepted_component_sets",1),("semantic_units_remaining_without_accepted_component_set",-1),("semantic_requirements_remaining_without_accepted_component_set",-1),("subject_disposed_units_total",1),("subject_disposed_requirements_total",1),("subject_review_units_remaining",-1),("subject_review_requirements_remaining",-1)): s[k]+=x
    s["canonical_component_refs_reused_unique"]=len({z for gg in d["semantic_review_groups"] for i in gg.get("accepted_component_sets") or [] for z in i.get("canonical_component_refs") or []})
    for k,v in AFTER.items():
        if s.get(k)!=v: raise ValueError(f"post-OGE aggregate drift: {k}")
    if len(d["accepted_authorities"])!=63 or s["false_exact_mastery_admissions"]!=0: raise ValueError("final authority/mastery drift")
    d["schema_version"]="0.19.0"; d["base_current_launch_progress_v15_head_sha"]=BASE_HEAD; d["base_current_launch_progress_v15_builder_git_blob_sha1"]=BASE_BLOB; d["base_current_launch_progress_v15_normalized_sha256"]=BASE_SHA
    d["newly_accepted_exact_object"]={"accepted_authority_id":AID,"admission_unit_id":UNIT,"requirement_id":REQ,"accepted_semantic_ref":SEM,"component_specific_independent_evidence_ids":EVID,"sibling_source_objects_accepted":0,"accepted_same_signature_reference_object":{"accepted_authority_id":REF_AID,"admission_unit_id":REF_UNIT,"requirement_id":REF_REQ},"remaining_same_signature_targets":[]}
    d.setdefault("policy",{})["ru01_sound_changes_object_requires_prior_bounded_subject_semantic_acceptance"]=True
    d["policy"]["ru01_sound_changes_object_requires_component_specific_independent_evidence"]=True
    d["policy"]["ru01_sound_changes_second_object_requires_prior_separate_same_signature_object_acceptance"]=True
    d["policy"]["generic_ru01_attempt_can_emit_exact_sound_changes_mastery"]=False
    d["policy"]["ru01_shared_sound_changes_evidence_can_close_sibling_source_objects_without_separate_acceptance"]=False
    d.pop("normalized_sha256",None); d["normalized_sha256"]=hashlib.sha256(cj(d)).hexdigest(); return d

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output"); p.add_argument("--emit",action="store_true"); a=p.parse_args(); d=build_progress()
    if a.output: Path(a.output).write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    if a.emit: print(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":")))
    else:
        s=d["progress_summary"]; print("RUSSIAN_RU01_SOUND_CHANGES_OGE_P021_4_1_3_EXACT_OBJECT_ACCEPTANCE=PASS"); print("ACCEPTED_UNIT="+UNIT); print("ACCEPTED_REQUIREMENT="+REQ); print("EXACT_COMPONENT_REFS=1"); print("INDEPENDENT_EVIDENCE_ITEMS=6"); print("ADDITIONAL_SIBLING_RU01_OBJECTS_ACCEPTED=0"); print(f"ACCEPTED_AUTHORITIES={len(d['accepted_authorities'])}"); print(f"SUBJECT_REVIEW_UNITS_REMAINING={s['subject_review_units_remaining']}"); print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={s['subject_review_requirements_remaining']}"); print(f"FALSE_EXACT_MASTERY={s['false_exact_mastery_admissions']}"); print("NORMALIZED_SHA256="+d["normalized_sha256"])
    return 0
if __name__=="__main__": raise SystemExit(main())
