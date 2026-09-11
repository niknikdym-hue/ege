#!/usr/bin/env python3
"""Current Russian launch progress after exact OGE COD p.21 4.1.6 RU02 acceptance."""
from __future__ import annotations
import argparse, hashlib, json, runpy
from copy import deepcopy
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
BASE = HERE / "build_russian_semantic_acceptance_progress_launch_current_v28.py"
REVIEW = HERE / "build_ru02_orthoepy_oge_p021_4_1_6_exact_object_binding_review.py"
AUTHORITY = HERE / "RU02-OGE-P021-4-1-6-EXACT-CANONICAL-COMPONENT-ACCEPTANCE-v0.1.json"
BASE_SHA = "be4b747386c4dadd52b152b65fed60a9a76e585c6501a6080fd214025748eb8a"
REVIEW_SHA = "4d7a08bd13b44fd4b342470173d6880a69df7a15d0a4baaded6aae0966b0e0c4"
AUTHORITY_SHA = "2d0c9c2affecfac4845c9bdaa801dbd4e85e31f4029e710b78033774545b7737"
GROUP = "RUS-SEM-REVIEW-047"
UNIT = "RAU-475d1c2a36040b45e190"
REQ = "RSK-OGE_COD-4-1-6-P021"
COMPONENTS = ["ru-orthoepy-normative-pronunciation-selection", "ru-orthoepy-normative-stress-selection"]
EVIDENCE = {COMPONENTS[0]: [f"p02-u4-v{i}" for i in range(1,6)], COMPONENTS[1]: [f"p02-u3-v{i}" for i in range(1,5)]}
BASE_SUMMARY = {
 "semantic_units_with_accepted_component_sets":44,"semantic_requirements_with_accepted_component_sets":44,
 "semantic_units_remaining_without_accepted_component_set":1272,"semantic_requirements_remaining_without_accepted_component_set":1347,
 "subject_disposed_units_total":45,"subject_disposed_requirements_total":45,"subject_review_units_remaining":1271,
 "subject_review_requirements_remaining":1346,"canonical_component_refs_reused_unique":125,
 "review_groups_with_accepted_component_sets":14,"fully_accepted_semantic_groups":0,
 "accepted_bounded_ru_route_semantics":9,"accepted_bounded_ru_subject_semantics":75,"accepted_bounded_ru_semantics_total":84,
 "false_exact_mastery_admissions":0}
AFTER = dict(BASE_SUMMARY)
AFTER.update({"semantic_units_with_accepted_component_sets":45,"semantic_requirements_with_accepted_component_sets":45,
 "semantic_units_remaining_without_accepted_component_set":1271,"semantic_requirements_remaining_without_accepted_component_set":1346,
 "subject_disposed_units_total":46,"subject_disposed_requirements_total":46,"subject_review_units_remaining":1270,
 "subject_review_requirements_remaining":1345,"fully_accepted_semantic_groups":1})

def cbytes(v: Any) -> bytes:
 return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()

def build_progress() -> dict[str, Any]:
 data = runpy.run_path(str(BASE))["build_progress"]()
 assert data["schema_version"] == "0.30.0" and data["normalized_sha256"] == BASE_SHA
 s = data["progress_summary"]
 for k,v in BASE_SUMMARY.items(): assert s[k] == v, (k,s[k],v)
 assert len(data["accepted_authorities"]) == 74
 review = runpy.run_path(str(REVIEW))["build_review"]()
 assert review["normalized_sha256"] == REVIEW_SHA
 assert review["status"] == "CENTRAL_BRAIN_RU02_OGE_P021_4_1_6_EXACT_OBJECT_BINDING_REVIEW_READY_FOR_SEPARATE_ACCEPTANCE_NOT_ACCEPTED"
 assert review["current_v28_exact_head_gate"] == {"workflow":"Russian RU02 EDSOO59 p190 5.1 current exact acceptance","run_id":34600017223,"head_sha":"f050dfa7ecf69e371839c6693f68b18928a2fef2","conclusion":"SUCCESS","normalized_sha256":BASE_SHA}
 sel=review["selected_object"]
 assert (sel["admission_unit_id"],sel["requirement_id"],sel["source_id"],sel["document_id"],sel["page"],sel["code"]) == (UNIT,REQ,"FIPI-OGE-RU-2026-FINAL","OGE_COD",21,"4.1.6")
 reuse=review["reuse_first_owner_resolution"]
 assert reuse["canonical_component_refs"] == COMPONENTS and reuse["independent_evidence_items"] == 9
 assert reuse["missing_source_components"] == [] and reuse["overlapping_component_boundaries"] == []
 ready=review["acceptance_readiness"]
 for k in ("exact_source_identity_verified","target_is_sole_remaining_object_in_current_v28_group","exact_current_component_owners_verified","all_components_have_component_specific_independent_evidence","source_backed_two_component_decomposition_verified","separate_object_acceptance_required"): assert ready[k] is True
 assert ready["object_accepted_by_this_review"] is False and review["summary"]["false_exact_mastery_admissions"] == 0
 authority=json.loads(AUTHORITY.read_text(encoding="utf-8")); body=deepcopy(authority); body.pop("normalized_sha256",None)
 assert authority["normalized_sha256"] == AUTHORITY_SHA == hashlib.sha256(cbytes(body)).hexdigest()
 assert authority["status"] == "CENTRAL_BRAIN_ACCEPTED_EXACT_RU02_OGE_P021_4_1_6_CANONICAL_COMPONENT_SET"
 assert authority["exact_object_binding_review_exact_head_gate"] == {"workflow":"Russian RU02 OGE p21 4.1.6 exact object binding review","run_id":34615104326,"head_sha":"cdbb01dfe223e090bbddf1872bb9afd6253d85af","conclusion":"SUCCESS","normalized_sha256":REVIEW_SHA}
 d=authority["decision"]
 assert (d["admission_unit_id"],d["requirement_id"],d["source_id"],d["document_id"],d["page"],d["content_code"],d["route"]) == (UNIT,REQ,"FIPI-OGE-RU-2026-FINAL","OGE_COD",21,"4.1.6","oge")
 assert d["canonical_component_refs"] == COMPONENTS and d["component_specific_independent_evidence"] == EVIDENCE and d["independent_evidence_items"] == 9
 m=d["mastery_boundary"]
 for k in ("registered_user_identity_required_for_future_canonical_learner_evidence","exact_versioned_item_and_action_required_for_future_canonical_learner_evidence","server_owned_received_at_required_for_future_canonical_learner_evidence","durable_evidence_event_required_for_future_canonical_learner_evidence","component_specific_independent_evidence_required"): assert m[k] is True
 for k in ("anonymous_or_device_only_canonical_progress_allowed","generic_orthoepy_attempt_can_emit_exact_component_mastery","object_acceptance_itself_emits_mastery","shared_sibling_object_acceptance_can_close_target"): assert m[k] is False
 groups=[g for g in data["semantic_review_groups"] if g.get("group_id") == GROUP]; assert len(groups)==1; g=groups[0]
 assert g["admission_unit_count"] == 4 and g["requirement_count"] == 4 and g["accepted_component_set_count"] == 3
 assert not any(r.get("admission_unit_id")==UNIT or r.get("requirement_id")==REQ for r in g["accepted_component_sets"])
 g["accepted_component_sets"].append({"accepted_authority_id":"RU02_OGE_P021_4_1_6_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1","admission_unit_id":UNIT,"requirement_id":REQ,"packet_group":GROUP,"source_id":"FIPI-OGE-RU-2026-FINAL","document_id":"OGE_COD","content_code":"4.1.6","source_locator":"FIPI-OGE-RU-2026-FINAL/OGE_COD p.21 4.1.6","modules":["RU-PROG-02"],"canonical_component_refs":COMPONENTS,"component_count":2,"authority":{"base_current_v28_head_sha":"f050dfa7ecf69e371839c6693f68b18928a2fef2","base_current_v28_normalized_sha256":BASE_SHA,"exact_object_binding_review_head_sha":"cdbb01dfe223e090bbddf1872bb9afd6253d85af","exact_object_binding_review_run_id":34615104326,"exact_object_binding_review_normalized_sha256":REVIEW_SHA,"accepted_authority_normalized_sha256":AUTHORITY_SHA,"component_specific_independent_evidence_items":9},"mastery_boundary":deepcopy(m),"subject_semantic_status":"CENTRAL_BRAIN_ACCEPTED_CANONICAL_COMPONENT_SET"})
 g["accepted_component_set_count"]=4; g["status"]="SUBJECT_ACCEPTED_COMPONENT_SET_COMPLETE"; g["remaining_group_action"]="NONE; ALL EXACT SOURCE OBJECTS IN GROUP HAVE ACCEPTED CANONICAL COMPONENT SETS"
 data["accepted_authorities"].append({"id":"RU02_OGE_P021_4_1_6_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1","authority_kind":"OBJECT_BOUND_EXACT_CANONICAL_COMPONENT_SET","sha256":AUTHORITY_SHA,"status":authority["status"],"accepted_admission_units":1,"accepted_requirements":1,"canonical_component_refs":2,"accepted_route_semantics":0,"accepted_subject_semantics":0,"semantic_identity_admissions":0})
 for k,delta in (("semantic_units_with_accepted_component_sets",1),("semantic_requirements_with_accepted_component_sets",1),("semantic_units_remaining_without_accepted_component_set",-1),("semantic_requirements_remaining_without_accepted_component_set",-1),("subject_disposed_units_total",1),("subject_disposed_requirements_total",1),("subject_review_units_remaining",-1),("subject_review_requirements_remaining",-1),("fully_accepted_semantic_groups",1)): s[k]+=delta
 for k,v in AFTER.items(): assert s[k] == v, (k,s[k],v)
 assert len(data["accepted_authorities"]) == 75 and s["false_exact_mastery_admissions"] == 0
 data["schema_version"]="0.31.0"; data["base_current_launch_progress_v28_head_sha"]="f050dfa7ecf69e371839c6693f68b18928a2fef2"; data["base_current_launch_progress_v28_normalized_sha256"]=BASE_SHA
 data["newly_accepted_exact_object"]={"accepted_authority_id":"RU02_OGE_P021_4_1_6_EXACT_CANONICAL_COMPONENT_ACCEPTANCE_v0.1","admission_unit_id":UNIT,"requirement_id":REQ,"accepted_component_refs":COMPONENTS,"component_specific_independent_evidence":EVIDENCE,"independent_evidence_items":9,"sibling_source_objects_accepted":0,"semantic_identity_admissions":0,"exact_mastery_admissions":0,"completed_review_group":GROUP}
 data.setdefault("policy",{})["shared_ru02_sibling_acceptance_can_auto_close_target"]=False; data["policy"]["anonymous_or_device_only_progress_can_be_canonical_for_oge_p021_4_1_6"]=False
 data.pop("normalized_sha256",None); data["normalized_sha256"]=hashlib.sha256(cbytes(data)).hexdigest(); return data

def main() -> int:
 p=argparse.ArgumentParser(); p.add_argument("--output"); p.add_argument("--emit",action="store_true"); a=p.parse_args(); d=build_progress()
 if a.output: Path(a.output).write_text(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n",encoding="utf-8")
 if a.emit: print(json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":")))
 else:
  s=d["progress_summary"]; print("RUSSIAN_RU02_OGE_P021_4_1_6_EXACT_OBJECT_ACCEPTANCE=PASS"); print("ACCEPTED_UNIT="+UNIT); print("ACCEPTED_REQUIREMENT="+REQ); print("ACCEPTED_AUTHORITIES="+str(len(d["accepted_authorities"]))); print("SUBJECT_REVIEW_UNITS_REMAINING="+str(s["subject_review_units_remaining"])); print("SUBJECT_REVIEW_REQUIREMENTS_REMAINING="+str(s["subject_review_requirements_remaining"])); print("FULLY_ACCEPTED_SEMANTIC_GROUPS="+str(s["fully_accepted_semantic_groups"])); print("FALSE_EXACT_MASTERY="+str(s["false_exact_mastery_admissions"])); print("NORMALIZED_SHA256="+d["normalized_sha256"])
 return 0
if __name__ == "__main__": raise SystemExit(main())
