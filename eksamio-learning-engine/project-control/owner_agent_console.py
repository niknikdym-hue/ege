#!/usr/bin/env python3
"""Bounded, deterministic Owner Console projection; never a learner runtime."""
import argparse, json, subprocess, sys
from pathlib import Path
STATUSES={'NOT_STARTED','DESIGNED','CODE_READY','INTEGRATION_PENDING','BLOCKED_SUBJECT','BLOCKED_EXTERNAL','PRIVATE_PRODUCTION_PASS','VISIBLE_TO_LEARNER','PUBLIC_LAUNCH_PASS','DONE'}
ROOT=Path(__file__).resolve().parents[1]; BOARD=ROOT/'project-control/operational-board-v1.json'
ALLOWED={'repository','main_sha','sync_time','owner_actions','autonomous_work','corrections','facts','activity'}
def rows(board=BOARD):
 d=json.loads(Path(board).read_text()); r=d['tasks']
 if len(r)!=115 or len({x['task_id'] for x in r})!=115: raise ValueError('board must contain 115 unique tasks')
 return r
def load_fixture(path=None):
 if not path:return {}
 d=json.loads(Path(path).read_text()); return {k:v for k,v in d.items() if k in ALLOWED}
def gh_facts(repo):
 def call(a): return json.loads(subprocess.run(['gh',*a],check=True,capture_output=True,text=True).stdout)
 main=call(['api',f'repos/{repo}/commits/main']); prs=call(['pr','list','--repo',repo,'--state','open','--limit','100','--json','number,title,headRefName,headRefOid,isDraft,statusCheckRollup,url'])
 return {'repository':repo,'main_sha':main.get('sha'),'sync_time':'live','facts':{'main':main.get('sha'),'prs':prs,'conflict':False}}
def render(board,fixture):
 data=json.loads(Path(board).read_text()); rs=rows(board); f=fixture or {}; facts=f.get('facts',{}); conflict=bool(facts.get('conflict')) or bool(facts.get('main') and facts.get('main') != data['baseline_main']); state='STALE/CONFLICT' if conflict else 'SOURCE OF TRUTH OK'
 lines=['# Eksamio — Owner Control','',f"Repository: {f.get('repository','niknikdym-hue/ege')}",f"Main SHA: {f.get('main_sha',data['baseline_main'])}",f"Milestone: {data['active_milestone']}",f'Truth: {state}',f"Owner actions: {f.get('owner_actions',0)} | Autonomous work: {f.get('autonomous_work',0)}",'', 'CODE_READY != VISIBLE_TO_LEARNER','']
 names={'A':'Russian Public Paid Launch','B':'Russian Full Product','C':'Mathematics','D':'Physics','E':'Next Subjects / Platform Scale'}
 lines+=['## Stage rail A–E','']
 for s,n in names.items():
  q=[r for r in rs if r['stage']==s]; lines.append(f"- {s} — {n}: {len(q)} tasks; statuses: "+', '.join(f"{x}:{sum(r['status']==x for r in q)}" for x in sorted(STATUSES) if any(r['status']==x for r in q))+f"; visible learner result: {'YES' if any(r['visible_to_learner'] for r in q) else 'NO'}")
 def cards(q): return [f"- {r['task_id']} — {r['title']} | {r['status']} | action: {r['current_action']}" for r in q]
 lines+=['','## Whole Project',*cards(rs),'','## Critical Path']
 for i,tid in enumerate(data['critical_path'],1): lines.append(f"- {i}. "+next(r['task_id']+' — '+r['title']+' | '+r['status'] for r in rs if r['task_id']==tid))
 lines+=['','## Russian Product (A+B)',*cards([r for r in rs if r['stage'] in 'AB']),'','## Visible Product']
 lines += [f"- {r['task_id']} — {r['title']} | {r['status']} | visible_to_learner={str(r['visible_to_learner']).lower()} | production={r['production_state']}" for r in rs if r['stage']=='A' and (r['visible_to_learner'] or 'site' in r['workstream'].lower())]
 lines+=['','## Owner Gates',*cards([r for r in rs if r['owner_gate_required']]),'','## Blockers']
 for typ in sorted({r['blocker_type'] for r in rs if r['blocker_type']}): lines += [f'### {typ}',*cards([r for r in rs if r['blocker_type']==typ])]
 lines+=['','## History','- Accepted source baseline: 85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb','','## GitHub facts',f"- Open PRs/checks: {facts.get('prs',[])}",'', '## Astra/API-Codex activity',f"- {f.get('activity',{})}",'','CORRECTION: comments are durable but NOT_DISPATCHED; they are not auto-executed.']
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
