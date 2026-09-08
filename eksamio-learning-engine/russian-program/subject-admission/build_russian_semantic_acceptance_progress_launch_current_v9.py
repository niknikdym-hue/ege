#!/usr/bin/env python3
"""Current Sep-1 Russian launch progress with sixth exact RU01 phonetics object acceptance."""
from __future__ import annotations
import argparse, hashlib, json, runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

H=Path(__file__).resolve().parent
BASE=H/"build_russian_semantic_acceptance_progress_launch_current_v8.py"
BINDING=H/"build_ru01_phonetics_exact_object_binding_review.py"
BOUNDED=H/"RU01-PHONETICS-BOUNDED-SUBJECT-SEMANTIC-ACCEPTANCE-v0.1.json"
AUTH=H/"RU01-PHONETICS-OGE-P014-3-1-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
CONTENT=H.parent/"production-learning-content"/"RU-PROG-01-PHONETICS-GRAPHICS-WAVE-001-v0.1.json"
BASE_HEAD="9e4beb4b7bb13bf1bd7459eae44d100f0a483d4d"
BASE_BLOB="526359b6ff0a53110f102df3b54588c5a45a9de9"
BASE_SHA="78bf63f9c4a94e820b18e6e4b56e2754c2ff2c01a0e94acd2c6fbc7ae44c96be"
BINDING_SHA="9e903409896463f350eb06e7bf5874eaaf9f1e21037c76f7c9c4b9e53831613e"
BINDING_INPUT_SHA="39f8c5974c3b2fff4e397595655146e78a52ce9119a939cf86bf925f618a51b2"
AUTH_SHA="1494ceac53a9af748525f40a25bfd6a826b5fe265b42857af0231bb4b91406ef"
AUTH_ID="RU01_PHONETICS_OGE_P014_3_1_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1"
UNIT="RAU-df45aa3b99e1baefca01"
REQ="RSK-OGE_COD-3-1-P014"
GROUP="RUS-SEM-REVIEW-001"
SOURCE="FIPI-OGE-RU-2026-FINAL"
DOC="OGE_COD"
PAGE=14
CODE="3.1"
LOCATOR="FIPI-OGE-RU-2026-FINAL/OGE_COD p.14 3.1"
SIGNATURE="PHONETIC_WORD_ANALYSIS"
COMP="ru-phonetics-word-analysis-sequence"
EVID=["p01-u3-v1","p01-u3-v2"]
PRIOR={
"RU01_PHONETICS_P181_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1":("RAU-043ae3d307ad5fd95639","RSK-EDSOO59-4-2-P181"),
"RU01_PHONETICS_P187_4_1_7_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1":("RAU-0985ee43535361c09cd9","RSK-EDSOO59-4-1-7-P187"),
"RU01_PHONETICS_P196_4_24_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1":("RAU-3e5308ed79e62fc16e94","RSK-EDSOO59-4-24-P196"),
"RU01_PHONETICS_P074_2_2_1_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1":("RAU-8e357e9bbe18a741725c","RSK-EDSOO1011-2-2-1-P074"),
"RU01_PHONETICS_P078_2_2_2_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1":("RAU-cb307f6635d27f73fa88","RSK-EDSOO1011-2-2-2-P078")
}
EXPECTED_BASE={
"semantic_units_with_accepted_component_sets":34,
"semantic_requirements_with_accepted_component_sets":34,
"semantic_units_remaining_without_accepted_component_set":1282,
"semantic_requirements_remaining_without_accepted_component_set":1357,
"subject_disposed_units_total":35,
"subject_disposed_requirements_total":35,
"subject_review_units_remaining":1281,
"subject_review_requirements_remaining":1356,
"canonical_component_refs_reused_unique":118,
"review_groups_with_accepted_component_sets":14,
"accepted_bounded_ru_route_semantics":9,
"accepted_bounded_ru_subject_semantics":66,
"accepted_bounded_ru_semantics_total":75,
"false_exact_mastery_admissions":0}
EXPECTED_AFTER={
"semantic_units_with_accepted_component_sets":35,
"semantic_requirements_with_accepted_component_sets":35,
"semantic_units_remaining_without_accepted_component_set":1281,
"semantic_requirements_remaining_without_accepted_component_set":1356,
"subject_disposed_units_total":36,
"subject_disposed_requirements_total":36,
"subject_review_units_remaining":1280,
"subject_review_requirements_remaining":1355,
"canonical_component_refs_reused_unique":118,
"review_groups_with_accepted_component_sets":14,
"accepted_bounded_ru_route_semantics":9,
"accepted_bounded_ru_subject_semantics":66,
"accepted_bounded_ru_semantics_total":75,
"false_exact_mastery_admissions":0}

def cb(v:Any)->bytes:
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()

def blob(path:Path)->str:
    b=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def verify_sha(d:dict[str,Any],sha:str)->None:
    if d.get("normalized_sha256")!=sha:
        raise ValueError("authority normalized SHA drift")
    q=deepcopy(d)
    q.pop("normalized_sha256",None)
    if hashlib.sha256(cb(q)).hexdigest()!=sha:
        raise ValueError("authority embedded SHA mismatch")

def build_progress()->dict[str,Any]:
    if blob(BASE)!=BASE_BLOB:
        raise ValueError("current-v8 builder blob drift")
    d=runpy.run_path(str(BASE))["build_progress"]()
    if d.get("schema_version")!="0.11.0" or d.get("normalized_sha256")!=BASE_SHA:
        raise ValueError("current-v8 authority drift")
    s=d["progress_summary"]
    for k,v in EXPECTED_BASE.items():
        if s.get(k)!=v:
            raise ValueError(f"current-v8 aggregate drift: {k}")
    if len(d.get("accepted_authorities",[]))!=55:
        raise ValueError("current-v8 authority count drift")

    b=runpy.run_path(str(BINDING))["build_review"]()
    if b.get("normalized_sha256")!=BINDING_SHA or b.get("source_review_input_sha256")!=BINDING_INPUT_SHA:
        raise ValueError("RU01 binding review drift")
    if (b.get("summary") or {}).get("false_exact_mastery_admissions")!=0:
        raise ValueError("binding false mastery drift")
    ready=b.get("exact_reuse_ready") or {}
    if ready.get("semantic_id")!=COMP or ready.get("separate_object_acceptance_required") is not True:
        raise ValueError("RU01 reuse boundary drift")
    if UNIT not in ready.get("admission_unit_ids",[]) or REQ not in ready.get("requirement_ids",[]):
        raise ValueError("OGE P014 3.1 no longer exact-reuse-ready")
    rec=[x for x in b.get("records",[]) if x.get("admission_unit_id")==UNIT and x.get("requirement_id")==REQ]
    if len(rec)!=1:
        raise ValueError("OGE P014 3.1 binding not unique")
    r=rec[0]
    for k,v in {"source_id":SOURCE,"document_id":DOC,"page":PAGE,"code":CODE,"source_locator":LOCATOR,
                "normalized_source_signature":SIGNATURE,"review_classification":"READY","accepted_semantic_refs":[COMP],"blocker_or_reroute":None}.items():
        if r.get(k)!=v:
            raise ValueError(f"OGE P014 3.1 binding identity drift: {k}")

    bounded=json.loads(BOUNDED.read_text(encoding="utf-8"))
    owners=[x for x in bounded.get("decisions",[]) if x.get("accepted_semantic_id")==COMP]
    if bounded.get("status")!="CENTRAL_BRAIN_ACCEPTED_RU01_PHONETICS_BOUNDED_SUBJECT_SEMANTICS" or len(owners)!=1:
        raise ValueError("RU01 owner drift")
    if (bounded.get("policy") or {}).get("component_specific_independent_evidence_required") is not True:
        raise ValueError("evidence guard drift")
    if (bounded.get("policy") or {}).get("broad_domain_attempt_can_emit_exact_component_mastery") is not False:
        raise ValueError("generic mastery guard drift")

    content=json.loads(CONTENT.read_text(encoding="utf-8"))
    units=[x for x in content.get("units",[]) if x.get("proposed_semantic_id")==COMP]
    if len(units)!=1:
        raise ValueError("word-analysis learner unit drift")
    if [x.get("id") for x in units[0].get("independent_verification",[]) if isinstance(x,dict)]!=EVID:
        raise ValueError("word-analysis evidence identity drift")
    peis=units[0].get("peis_evidence") or {}
    if peis.get("independent_verification_required") is not True or peis.get("assistance_must_be_recorded") is not True:
        raise ValueError("PEIS evidence guard drift")

    a=json.loads(AUTH.read_text(encoding="utf-8"))
    verify_sha(a,AUTH_SHA)
    if a.get("status")!="CENTRAL_BRAIN_ACCEPTED_EXACT_RU01_PHONETICS_WORD_ANALYSIS_CANONICAL_COMPONENT_SET":
        raise ValueError("OGE P014 3.1 authority status drift")
    if (a.get("current_launch_progress_v8_base_head_sha"),a.get("current_launch_progress_v8_builder_git_blob_sha1"),a.get("current_launch_progress_v8_normalized_sha256"))!=(BASE_HEAD,BASE_BLOB,BASE_SHA):
        raise ValueError("OGE P014 3.1 base binding drift")
    if (a.get("exact_object_binding_review_sha256"),a.get("exact_source_review_input_sha256"))!=(BINDING_SHA,BINDING_INPUT_SHA):
        raise ValueError("OGE P014 3.1 source binding drift")
    dec=a.get("decision") or {}
    exact={"admission_unit_id":UNIT,"requirement_id":REQ,"packet_group":GROUP,"source_id":SOURCE,"document_id":DOC,"page":PAGE,
           "content_code":CODE,"source_locator":LOCATOR,"normalized_source_signature":SIGNATURE,"module_id":"RU-PROG-01",
           "disposition":"PARTIAL_OR_COMPOSITE","canonical_component_refs":[COMP],"component_count":1,
           "component_specific_independent_evidence":{COMP:EVID},"independent_evidence_items":2,
           "subject_semantic_status":"CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"}
    for k,v in exact.items():
        if dec.get(k)!=v:
            raise ValueError(f"OGE P014 3.1 authority identity drift: {k}")
    m=dec.get("mastery_boundary") or {}
    if m.get("component_specific_independent_evidence_required") is not True or m.get("validated_word_analysis_item_may_support_only_its_single_canonical_ref") is not True:
        raise ValueError("OGE P014 3.1 evidence boundary weakened")
    for k in ("generic_ru01_attempt_can_emit_exact_component_mastery","spelling_or_morphemic_evidence_can_substitute_for_word_analysis","shared_evidence_can_close_sibling_source_objects_without_separate_acceptance"):
        if m.get(k) is not False:
            raise ValueError(f"OGE P014 3.1 mastery boundary weakened: {k}")
    if (a.get("policy") or {}).get("separate_object_acceptance_required") is not True or (a.get("policy") or {}).get("whole_group_acceptance_allowed") is not False:
        raise ValueError("OGE P014 3.1 object-isolation guard weakened")
    if (a.get("summary") or {}).get("false_exact_mastery_admissions")!=0 or (a.get("summary") or {}).get("sibling_ru01_source_objects_accepted")!=0:
        raise ValueError("OGE P014 3.1 authority boundary weakened")

    groups=[g for g in d.get("semantic_review_groups",[]) if g.get("group_id")==GROUP]
    if len(groups)!=1:
        raise ValueError("RU01 group not unique")
    g=groups[0]
    if g.get("accepted_component_set_count")!=5:
        raise ValueError("current-v8 RU01 accepted-set count drift")
    sets=g.get("accepted_component_sets",[])
    for aid,(u,q) in PRIOR.items():
        hit=[x for x in sets if x.get("accepted_authority_id")==aid and x.get("admission_unit_id")==u and x.get("requirement_id")==q]
        if len(hit)!=1:
            raise ValueError(f"prior acceptance missing: {aid}")
    if UNIT not in set(map(str,g.get("admission_unit_ids",[]))):
        raise ValueError("OGE P014 3.1 unit missing from group")
    rows=[x for x in g.get("requirements",[]) if x.get("requirement_id")==REQ]
    if len(rows)!=1:
        raise ValueError("OGE P014 3.1 requirement not unique")
    for k,v in (("source_id",SOURCE),("document_id",DOC),("page",PAGE),("code",CODE),("source_locator",LOCATOR)):
        if rows[0].get(k)!=v:
            raise ValueError(f"OGE P014 3.1 source identity drift: {k}")
    accepted=[x for gg in d.get("semantic_review_groups",[]) for x in gg.get("accepted_component_sets",[])]
    if any(x.get("admission_unit_id")==UNIT or x.get("requirement_id")==REQ for x in accepted):
        raise ValueError("OGE P014 3.1 already accepted")
    if any(x.get("id")==AUTH_ID for x in d.get("accepted_authorities",[])):
        raise ValueError("OGE P014 3.1 authority already integrated")
    if COMP not in {r for x in accepted for r in x.get("canonical_component_refs",[])}:
        raise ValueError("word-analysis component is not prior accepted reuse")

    projection={"accepted_authority_id":AUTH_ID,"admission_unit_id":UNIT,"requirement_id":REQ,"packet_group":GROUP,
                "source_id":SOURCE,"document_id":DOC,"content_code":CODE,"source_locator":LOCATOR,"modules":["RU-PROG-01"],
                "canonical_component_refs":[COMP],"component_count":1,
                "authority":{"exact_object_binding_review_normalized_sha256":BINDING_SHA,"accepted_authority_normalized_sha256":AUTH_SHA,"component_specific_independent_evidence_items":2},
                "mastery_boundary":deepcopy(m),"subject_semantic_status":"CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"}
    g.setdefault("accepted_component_sets",[]).append(projection)
    g["accepted_component_set_count"]=len(g["accepted_component_sets"])
    if g["accepted_component_set_count"]!=6:
        raise ValueError("OGE P014 3.1 accepted-set count drift")
    g["status"]="SUBJECT_ACCEPTANCE_REQUIRED_WITH_ACCEPTED_COMPONENT_SET"
    g["remaining_group_action"]="CONTINUE_EXACT_COMPONENT_REVIEW; DO NOT TREAT PARTIAL GROUP PROGRESS AS WHOLE-GROUP ACCEPTANCE"
    d["accepted_authorities"].append({"id":AUTH_ID,"authority_kind":"OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET","sha256":AUTH_SHA,
        "status":a["status"],"accepted_admission_units":1,"accepted_requirements":1,"canonical_component_refs":1,
        "accepted_route_semantics":0,"accepted_subject_semantics":0,"semantic_identity_admissions":0})

    for k,delta in (("semantic_units_with_accepted_component_sets",1),("semantic_requirements_with_accepted_component_sets",1),
                    ("semantic_units_remaining_without_accepted_component_set",-1),("semantic_requirements_remaining_without_accepted_component_set",-1),
                    ("subject_disposed_units_total",1),("subject_disposed_requirements_total",1),
                    ("subject_review_units_remaining",-1),("subject_review_requirements_remaining",-1)):
        s[k]+=delta
    for k,v in EXPECTED_AFTER.items():
        if s.get(k)!=v:
            raise ValueError(f"OGE P014 3.1 post-acceptance aggregate drift: {k}")
    if len(d["accepted_authorities"])!=56:
        raise ValueError("OGE P014 3.1 post-acceptance authority count drift")

    siblings=set(ready.get("admission_unit_ids",[]))-{UNIT}-{u for u,_ in PRIOR.values()}
    if siblings!={"RAU-f3896151ffac143c05da"}:
        raise ValueError("unexpected remaining READY sibling set")
    new=[x for x in g["accepted_component_sets"] if x.get("accepted_authority_id")==AUTH_ID]
    if len(new)!=1 or new[0].get("admission_unit_id")!=UNIT or new[0].get("admission_unit_id") in siblings:
        raise ValueError("OGE P014 3.1 sibling leak")
    if s.get("false_exact_mastery_admissions")!=0:
        raise ValueError("false exact mastery must remain zero")

    d["schema_version"]="0.12.0"
    d["base_current_launch_progress_v8_head_sha"]=BASE_HEAD
    d["base_current_launch_progress_v8_builder_git_blob_sha1"]=BASE_BLOB
    d["base_current_launch_progress_v8_normalized_sha256"]=BASE_SHA
    d["policy"]["exact_ru01_phonetics_reuse_requires_separate_object_acceptance_per_source_object"]=True
    d["policy"]["ru01_shared_evidence_can_close_sibling_source_objects_without_separate_acceptance"]=False
    d["policy"]["generic_ru01_attempt_can_emit_exact_component_mastery"]=False
    d.pop("normalized_sha256",None)
    d["normalized_sha256"]=hashlib.sha256(cb(d)).hexdigest()
    return d

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("--output")
    p.add_argument("--emit",action="store_true")
    a=p.parse_args()
    d=build_progress()
    if a.output:
        Path(a.output).write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
    if a.emit:
        print(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":")))
    else:
        s=d["progress_summary"]
        print("RUSSIAN_RU01_OGE_P014_3_1_EXACT_OBJECT_ACCEPTANCE=PASS")
        print("ACCEPTED_UNIT="+UNIT)
        print("ACCEPTED_REQUIREMENT="+REQ)
        print("EXACT_COMPONENT_REFS=1")
        print("INDEPENDENT_EVIDENCE_ITEMS=2")
        print("ADDITIONAL_SIBLING_RU01_OBJECTS_ACCEPTED=0")
        print(f"ACCEPTED_AUTHORITIES={len(d['accepted_authorities'])}")
        print(f"SUBJECT_REVIEW_UNITS_REMAINING={s['subject_review_units_remaining']}")
        print(f"SUBJECT_REVIEW_REQUIREMENTS_REMAINING={s['subject_review_requirements_remaining']}")
        print(f"FALSE_EXACT_MASTERY={s['false_exact_mastery_admissions']}")
        print("NORMALIZED_SHA256="+d["normalized_sha256"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
