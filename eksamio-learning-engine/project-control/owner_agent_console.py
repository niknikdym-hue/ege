#!/usr/bin/env python3
"""Deterministic, dependency-free Owner Control projection (never learner runtime)."""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / '00B-PROJECT-PRIORITIES-CURRENT.md'
STATUSES = ('NOT_STARTED','DESIGNED','CODE_READY','INTEGRATION_PENDING','BLOCKED_SUBJECT','BLOCKED_EXTERNAL','PRIVATE_PRODUCTION_PASS','VISIBLE_TO_LEARNER','PUBLIC_LAUNCH_PASS','DONE')

def rows(source=SOURCE):
    text = Path(source).read_text(encoding='utf-8'); stage = None; out=[]
    for line in text.splitlines():
        m=re.match(r'##(?: \d+\.)? Stage ([A-E])(?:\s|—|$)', line)
        if m: stage=m.group(1); continue
        if not stage or not line.startswith('|') or '---' in line: continue
        c=[x.strip() for x in line.strip('|').split('|')]
        if len(c)<3: continue
        im=re.match(r'^([A-E]\d+(?:\.\d+)?)(?:\s+(.*))?$', c[0])
        if not im: continue
        tid, label=im.group(1), (im.group(2) or '').strip()
        if stage=='A': title, fact, nxt=tid+' '+label+' — '+c[1], c[1], c[-1]
        else: title, fact, nxt=c[0]+' — '+c[1], c[-1], c[-1]
        raw=re.sub(r'\*\*','',fact).upper()
        status=next((s for s in STATUSES if s in raw), 'DESIGNED' if stage in 'DE' else 'NOT_STARTED')
        if 'BLOCKED_SUBJECT' in raw: status='BLOCKED_SUBJECT'
        elif 'BLOCKED_EXTERNAL' in raw: status='BLOCKED_EXTERNAL'
        elif 'VISIBLE_TO_LEARNER' in raw: status='VISIBLE_TO_LEARNER'
        code_only=('CODE' in raw or 'SHELL' in raw or 'CONTRACT' in raw)
        out.append({'task_id':tid,'title':title,'user_visible_outcome':fact.replace('**',''),'stage':stage,
          'workstream':'project-control','priority':'P0' if stage in 'AB' else 'P1','status':status,
          'target_state':'DONE','dependencies':[],'blocker_type':('SUBJECT' if status=='BLOCKED_SUBJECT' else 'EXTERNAL' if status=='BLOCKED_EXTERNAL' else None),
          'blocker_detail':fact if status.startswith('BLOCKED') else None,'branch':None,'pr':None,'head_sha':None,'ci_evidence':None,
          'visible_to_learner':status in ('VISIBLE_TO_LEARNER','PUBLIC_LAUNCH_PASS'),'production_state':'CODE_ONLY' if code_only else 'NOT_PROVEN',
          'executor':'Astra' if stage in 'AB' else 'Owner','owner_gate_required':('OWNER' in raw or c[0].startswith('A12.')),
          'current_action':nxt.replace('**',''),'next_action':nxt.replace('**',''),'last_evidence_timestamp':'2026-09-09','evidence':[]})
    return out

def load_fixture(path):
    if not path: return {}
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    return {k:v for k,v in data.items() if k in ('repository','main_sha','sync_time','owner_actions','autonomous_work','corrections','facts','activity')}

def render(board, fixture):
    rs=rows(ROOT / board.get('source','00B-PROJECT-PRIORITIES-CURRENT.md'))
    f=fixture; conflict=bool(f.get('facts',{}).get('conflict'))
    state='STALE/CONFLICT' if conflict else 'SOURCE OF TRUTH OK'
    lines=['# Eksamio — Owner Control','',f"Repository: {f.get('repository','niknikdym-hue/ege')}",f"Main SHA: {f.get('main_sha',board.get('baseline_main'))}",f"Milestone: {board.get('active_milestone')}",f"Truth: {state}",f"Owner actions: {f.get('owner_actions',0)} | Autonomous work: {f.get('autonomous_work',0)}",'','CODE_READY != VISIBLE_TO_LEARNER','']
    lines += ['## Stage rail A–E','']
    for s,name in [('A','Russian Public Paid Launch'),('B','Russian Full Product'),('C','Mathematics'),('D','Physics'),('E','Next Subjects / Platform Scale')]:
        q=[r for r in rs if r['stage']==s]; lines.append(f"- {s} — {name}: {len(q)} tasks; visible learner result: {'YES' if any(r['visible_to_learner'] for r in q) else 'NO'}")
    lines += ['','## Whole Project',*['- '+r['task_id']+': '+r['status'] for r in rs], '', '## Critical Path',*['- '+r['task_id']+': '+r['next_action'] for r in rs if r['stage']=='A'], '', '## Russian Product (A+B)',*['- '+r['task_id']+': '+r['status'] for r in rs if r['stage'] in 'AB'], '', '## Visible Product', '- CODE_READY items remain code-only unless explicit accepted runtime evidence says VISIBLE_TO_LEARNER.', '', '## Owner Gates',*['- '+r['task_id']+': '+r['next_action'] for r in rs if r['owner_gate_required']], '', '## Blockers',*['- '+r['task_id']+': '+str(r['blocker_detail']) for r in rs if r['blocker_type']], '', '## History','- Accepted source baseline: 85d2f2b3dd0cf56c428f57c8a5c7d1b636ecebbb', '', '## Astra/API-Codex activity','- Activity is reported separately from product completion.', '', 'CORRECTION: comments are durable but NOT_DISPATCHED; they are not auto-executed.']
    return '\n'.join(lines)+'\n'

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True)
    for cmd in ('render','sync'):
        x=sub.add_parser(cmd); x.add_argument('--board',required=True); x.add_argument('--github-fixture'); x.add_argument('--output'); x.add_argument('--repository'); x.add_argument('--issue-title')
    a=p.parse_args(); board=json.loads(Path(a.board).read_text(encoding='utf-8')); fixture=load_fixture(a.github_fixture)
    if a.cmd=='render':
        result=render(board,fixture)
        if a.output: Path(a.output).write_text(result,encoding='utf-8')
        else: sys.stdout.write(result)
    else:
        if not a.repository or not a.issue_title: p.error('sync requires --repository and --issue-title')
        body=render(board,fixture)
        q=subprocess.run(['gh','issue','list','--repo',a.repository,'--search',a.issue_title+' in:title','--limit','20','--json','number,title'],check=True,capture_output=True,text=True)
        issues=[x for x in json.loads(q.stdout) if x.get('title')==a.issue_title]
        if len(issues)!=1: raise SystemExit('expected exactly one Owner Control issue')
        subprocess.run(['gh','issue','edit',str(issues[0]['number']),'--repo',a.repository,'--body',body],check=True)
if __name__=='__main__': main()
