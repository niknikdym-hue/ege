#!/usr/bin/env python3
"""Real PostgreSQL contract suite; PEIS_TEST_POSTGRES_DSN is mandatory."""
from __future__ import annotations
import copy, json, os, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ENGINE=HERE.parent
sys.path[:0]=[str(HERE),str(ENGINE/"peis-persistence-reference"),str(ENGINE/"peis-reference-kernel")]
from peis_postgres import PostgresPeisPersistenceStore
from peis_persistence import IntegrityConflict
from peis_reference_kernel import snapshot
def load(p): return json.loads(p.read_text())
def ok(x,msg):
    if not x: raise AssertionError(msg)
    print("PASS",msg)
def conflicts(fn,msg):
    try: fn()
    except IntegrityConflict: print("PASS",msg); return
    raise AssertionError(msg)
def make(dsn): return PostgresPeisPersistenceStore(dsn,evidence_schema=load(ENGINE/"277-EKSAMIO-LEARNER-EVIDENCE-EVENT-SCHEMA-v0.1.json"),nba_schema=load(ENGINE/"285-EKSAMIO-NEXT-BEST-ACTION-CONTRACT-v0.1.json"))
def main():
    dsn=os.environ["PEIS_TEST_POSTGRES_DSN"]
    fixture=copy.deepcopy(load(ENGINE/"mathematics-identity/verified-slices/MATH-SLICE-001-EVIDENCE-FIXTURES-v0.1.json")["events"][0])
    fixture.update(event_id="pgsubstrate.event.001",learner_profile_id="learner-pgsubstrate",identity_refs={"anonymous_identity_ref":"anon:pgsubstrate"})
    with make(dsn) as s:
        ok(s.readiness(),"empty DB migration is applied and ready")
        ok(s.append_event(fixture)["status"]=="ACCEPTED","event and semantic target append")
        ok(s.append_event(fixture)["status"]=="ALREADY_APPLIED","exact replay idempotency")
        idem=copy.deepcopy(fixture); idem.update(event_id="pgsubstrate.event.idem",idempotency_key="pgsubstrate-idem"); idem["timestamps"]["server_sequence"]=2
        ok(s.append_event(idem)["status"]=="ACCEPTED","idempotency seed append")
        retry=copy.deepcopy(idem); retry["event_id"]="pgsubstrate.event.retry"; retry["timestamps"]["server_sequence"]=3
        ok(s.append_event(retry)["status"]=="ALREADY_APPLIED","idempotency-key replay")
        changed=copy.deepcopy(fixture); changed["result"]["response_value"]="conflict"; conflicts(lambda:s.append_event(changed),"conflicting replay rejected")
        ok([e["event_id"] for e in s.list_events("learner-pgsubstrate","mathematics",effective=False)][:2]==[fixture["event_id"],idem["event_id"]],"server sequence ordering preserved")
        ok(s.resolve_identity("anon:pgsubstrate")=="learner-pgsubstrate","anonymous evidence identity resolves")
        ok(s.link_identity("user:pgsubstrate","learner-pgsubstrate")["status"]=="LINKED","anonymous account continuity links without migration")
        conflicts(lambda:s.link_identity("user:pgsubstrate","other-learner"),"identity cannot be reassigned")
        state=s.recompute_snapshot(learner_profile_id="learner-pgsubstrate",subject_id="mathematics",semantic_id="math-probability-classical-equally-likely",admitted_edges=[],goal_context="pgsubstrate",kernel_snapshot=snapshot,recommendation_id="nba.pgsubstrate.001")
        ok(s.append_recommendation(state["nba"])["status"]=="ACCEPTED","recommendation append")
        outcome={"outcome_event_id":"pgsubstrate.outcome.001","recommendation_id":"nba.pgsubstrate.001","event_type":"SUBSEQUENT_INDEPENDENT_SUCCESS","occurred_at":"2026-08-23T00:00:00+00:00","outcome_log_policy_version":"nba-outcome-log-v0.1","evidence_event_refs":[fixture["event_id"]]}
        ok(s.append_recommendation_outcome(outcome)["status"]=="ACCEPTED","recommendation outcome append")
        ok(s.load_materialized_snapshot("learner-pgsubstrate","mathematics","math-probability-classical-equally-likely",goal_context="pgsubstrate")==state,"materialized snapshot round trip")
        broken=copy.deepcopy(fixture); broken["event_id"]="pgsubstrate.event.rollback"; broken["semantic_targets"]*=2
        try: s.append_event(broken)
        except Exception: pass
        else: raise AssertionError("duplicate target must fail")
        ok(s.raw_event("pgsubstrate.event.rollback") is None,"failed append rolls back canonical event")
        try:
            with s.connection: s.connection.execute("UPDATE evidence_events SET subject_id = %s WHERE event_id = %s",("tampered",fixture["event_id"]))
        except Exception: print("PASS append-only trigger")
        else: raise AssertionError("append-only trigger")
    with make(dsn) as restarted: ok(restarted.raw_event(fixture["event_id"])==fixture,"restart preserves canonical history")
if __name__=="__main__": main()
