#!/usr/bin/env python3
"""Bounded, deterministic Owner Console projection; never a learner runtime."""
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
STATUSES={'NOT_STARTED','DESIGNED','CODE_READY','INTEGRATION_PENDING','BLOCKED_SUBJECT','BLOCKED_EXTERNAL','PRIVATE_PRODUCTION_PASS','VISIBLE_TO_LEARNER','PUBLIC_LAUNCH_PASS','DONE'}
ROOT=Path(__file__).resolve().parents[1]; BOARD=ROOT/'project-control/operational-board-v1.json'
ALLOWED={'repository','main_sha','sync_time','owner_actions','autonomous_work','corrections','facts','activity'}
def normalize_status(source_status):
 """Conservative vocabulary mapping; accepts only the verbatim board state."""
 s=source_status.upper()
 if 'VISIBLE BASE EXISTS' in s: return 'VISIBLE_TO_LEARNER'
 if 'BLOCKED_SUBJECT' in s or 'SUBJECT GATE' in s or 'CONTENT ADMISSION REQUIRED' in s: return 'BLOCKED_SUBJECT'
 if 'BLOCKED_EXTERNAL' in s: return 'BLOCKED_EXTERNAL'
 if 'BLOCKED_DEPENDENCIES' in s: return 'INTEGRATION_PENDING'
 if 'CODE_READY' in s or 'CODE/CONTENT AUTHORITY EXISTS' in s: return 'CODE_READY'
 if 'INTEGRATION_PENDING' in s: return 'INTEGRATION_PENDING'
 if 'PRIVATE_PRODUCTION_PASS' in s: return 'PRIVATE_PRODUCTION_PASS'
 if 'PUBLIC_LAUNCH_PASS' in s: return 'PUBLIC_LAUNCH_PASS'
 if s.strip()=='DONE': return 'DONE'
 if any(x in s for x in ('NOT ', 'NEEDS ', 'NOT_FINAL', 'NOT READY', 'FUTURE', 'REQUIRED', 'LATER ')): return 'NOT_STARTED'
 return 'DESIGNED'
def rows(board=BOARD):
 d=json.loads(Path(board).read_text()); r=d['tasks']
 counts={s:sum(x['stage']==s for x in r) for s in 'ABCDE'}
 required={'task_id','title','user_visible_outcome','stage','workstream','priority','status','source_status','target_state','dependencies','blocker_type','blocker_detail','branch','pr','head_sha','ci_evidence','visible_to_learner','production_state','executor','owner_gate_required','current_action','next_action','last_evidence_timestamp','evidence'}
 if len(r)!=115 or len({x['task_id'] for x in r})!=115 or counts != {'A':74,'B':15,'C':11,'D':8,'E':7} or any(required-x.keys() for x in r) or any(x['status'] != normalize_status(x['source_status']) for x in r): raise ValueError('invalid operational board inventory')
 return r
def load_fixture(path=None):
 if not path:return {}
 d=json.loads(Path(path).read_text()); return {k:v for k,v in d.items() if k in ALLOWED}
def gh_facts(repo):
 def call(a): return json.loads(subprocess.run(['gh',*a],check=True,capture_output=True,text=True).stdout)
 main=call(['api',f'repos/{repo}/commits/main']); prs=call(['pr','list','--repo',repo,'--state','open','--limit','100','--json','number,title,headRefName,headRefOid,isDraft,statusCheckRollup,url'])
 compact=[]
 for pr in prs:
  checks=pr.get('statusCheckRollup') or []
  completed=[x for x in checks if x.get('status')=='COMPLETED']
  failed=sum(x.get('conclusion') not in {'SUCCESS','NEUTRAL','SKIPPED'} for x in completed)
  summary='no checks reported' if not checks else ('checks failing' if failed else f"checks {len(completed)}/{len(checks)} complete")
  compact.append({'number':pr.get('number'),'title':pr.get('title'),'head':pr.get('headRefName'),'head_sha':pr.get('headRefOid'),'draft':bool(pr.get('isDraft')),'checks':summary,'url':pr.get('url')})
 return {'repository':repo,'main_sha':main.get('sha'),'sync_time':datetime.now(timezone.utc).replace(microsecond=0).isoformat(),'facts':{'main':main.get('sha'),'prs':compact,'conflict':False}}
def pr_summary(pr):
 return f"#{pr.get('number')} — {pr.get('title','untitled')} | head {pr.get('head',pr.get('headRefName','unknown'))}@{pr.get('head_sha',pr.get('headRefOid','unknown'))} | {'draft' if pr.get('draft',pr.get('isDraft',False)) else 'ready'} | {pr.get('checks','checks unavailable')}"
def render(board,fixture):
 data=json.loads(Path(board).read_text()); rs=rows(board); f=fixture or {}; facts=f.get('facts',{}); conflict=bool(facts.get('conflict')) or bool(facts.get('main') and facts.get('main') != data['baseline_main']); state='STALE/CONFLICT' if conflict else 'SOURCE OF TRUTH OK'
 critical={r['task_id'] for r in rs if r['task_id'] in data['critical_path']}
 owner_actions=sum(r['owner_gate_required'] for r in rs)
 critical_blockers=sum(bool(r['blocker_type']) for r in rs if r['task_id'] in critical)
 lines=['# Eksamio — Owner Control','',f"Repository: {f.get('repository','niknikdym-hue/ege')}",f"Main SHA: {f.get('main_sha',data['baseline_main'])}",f"Milestone: {data['active_milestone']}",f"Last synchronization: {f.get('sync_time','not recorded')}",f'Truth: {state}',f"Owner actions: {owner_actions} | Autonomous work: {f.get('autonomous_work',0)} | Critical blockers: {critical_blockers}",'', 'CODE_READY != VISIBLE_TO_LEARNER','']
 names={'A':'Russian Public Paid Launch','B':'Russian Full Product','C':'Mathematics','D':'Physics','E':'Next Subjects / Platform Scale'}
 stage_state={'A':'IN PROGRESS / NO-GO','B':'PLANNED + PARTIAL CODE/CONTENT','C':'DEFERRED / EXISTING ASSETS PRESERVED','D':'DEFERRED / EXISTING ASSETS PRESERVED','E':'FUTURE'}
 next_milestone={'A':'Russian public paid launch pass','B':'Russian full product pass','C':'Russian full product pass first','D':'Mathematics after Russian full product','E':'product-market proof first'}
 lines+=['## Stage rail A–E','']
 for s,n in names.items():
  q=[r for r in rs if r['stage']==s]; accepted=sum(r['status']==r['target_state'] for r in q); blockers=sum(bool(r['blocker_type']) for r in q)
  lines.append(f"- {s} — {n}: {stage_state[s]}; {accepted}/{len(q)} rows at target state; blockers: {blockers}; statuses: "+', '.join(f"{x}:{sum(r['status']==x for r in q)}" for x in sorted(STATUSES) if any(r['status']==x for r in q))+f"; visible learner result: {'YES' if any(r['visible_to_learner'] for r in q) else 'NO'}; next: {next_milestone[s]}")
 def cards(q): return [f"- {r['task_id']} — {r['title']} | {r['status']} | action: {r['current_action']}" for r in q]
 lines+=['','## Whole Project',*cards(rs),'','## Critical Path']
 for i,tid in enumerate(data['critical_path'],1):
  r=next(r for r in rs if r['task_id']==tid); lines.append(f"- {i}. {r['task_id']} — {r['title']} | {r['status']} | action: {r['current_action']}")
 lines+=['','## Russian Product (A+B)',*cards([r for r in rs if r['stage'] in 'AB']),'','## Visible Product']
 visible_map=[('public site','A6.1'),('registration/login','A6.2'),('Pro purchase','A8.3'),('entitlement','A8.6'),('Russian navigation','A6.4'),('diagnostics','A7.1'),('work on mistakes','A7.3'),('next action','A7.4'),('Tutor text','A9.1'),('Tutor voice','A9.4'),('progress','A6.6'),('return login','A3.5'),('support/refund','A8.7')]
 by_id={r['task_id']:r for r in rs}
 lines += [f"- {label}: {by_id[tid]['task_id']} — {by_id[tid]['title']} | {by_id[tid]['status']} | visible_to_learner={str(by_id[tid]['visible_to_learner']).lower()} | production={by_id[tid]['production_state']}" for label,tid in visible_map]
 lines+=['','## Owner Gates',*cards([r for r in rs if r['owner_gate_required']]),'','## Blockers']
 for typ in sorted({r['blocker_type'] for r in rs if r['blocker_type']}): lines += [f'### {typ}',*cards([r for r in rs if r['blocker_type']==typ])]
 lines+=['','## History','- Accepted source baseline: 85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb','','## GitHub facts']
 lines += ['- '+pr_summary(pr) for pr in facts.get('prs',[])] or ['- No relevant open PR facts reported.']
 activity=f.get('activity',{})
 lines+=['','## Astra/API-Codex activity',f"- executor: {activity.get('executor','unknown')} | state: {activity.get('state','unknown')}",'','CORRECTION: comments are durable but NOT_DISPATCHED; they are not auto-executed.']
 return '\n'.join(lines)+'\n'
def main():
 p=argparse.ArgumentParser(); sp=p.add_subparsers(dest='cmd',required=True)
 for cmd in ('render','sync'):
  x=sp.add_parser(cmd); x.add_argument('--board',required=True); x.add_argument('--github-fixture'); x.add_argument('--output'); x.add_argument('--repository'); x.add_argument('--issue-title')
 a=p.parse_args(); f=load_fixture(a.github_fixture)
 if a.cmd=='sync': f.update(gh_facts(a.repository))
 result=render(a.board,f)
 if a.cmd=='render':
  if a.output: Path(a.output).write_text(result); return
  sys.stdout.write(result); return
 if not a.repository or not a.issue_title: p.error('sync requires --repository and --issue-title')
 q=subprocess.run(['gh','issue','list','--repo',a.repository,'--search',a.issue_title+' in:title','--limit','20','--json','number,title'],check=True,capture_output=True,text=True); issues=[x for x in json.loads(q.stdout) if x.get('title')==a.issue_title]
 if len(issues)!=1: raise SystemExit('expected exactly one Owner Control issue')
 subprocess.run(['gh','issue','edit',str(issues[0]['number']),'--repo',a.repository,'--body',result],check=True)
if __name__=='__main__': main()
