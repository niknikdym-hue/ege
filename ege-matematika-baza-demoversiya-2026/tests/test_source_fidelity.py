#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path
ROOT=Path(os.environ.get('DEMO_ROOT') or Path(__file__).resolve().parents[1]);PREFIX='ege-matematika-baza-demoversiya-2026'
def j(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
taskmap=j(f'{PREFIX}-TASK-MAP.json');data=j(f'{PREFIX}-EXAM-DATA.json');answers=j(f'{PREFIX}-OFFICIAL-ANSWERS.json');secondary=j(f'{PREFIX}-LITERAL-SECONDARY-EVIDENCE.json');formula=j(f'{PREFIX}-FORMULA-GATE-EVIDENCE.json');visual=j('source-evidence/ASSET-CROP-EVIDENCE.json')
assert len(taskmap['tasks'])==len(data['tasks'])==21 and sum(len(t['variants']) for t in taskmap['tasks'])==70
assert secondary['primary_failures']==29 and secondary['layout_subsequence_pass']==23 and secondary['formula_or_visual_review_required']==6
assert formula['status']=='PASS' and {r['example'] for r in formula['records']}=={'4.1','4.2','4.3','12.2','12.3','18.3'}
source={(t['number'],v['variant']):v for t in taskmap['tasks'] for v in t['variants']};generated={(t['number'],v['variant']):v for t in data['tasks'] for v in t['variants']};assert set(source)==set(generated)
for key,s in source.items():
 g=generated[key];assert g['source_page']==s['source_page'],key;assert g['control']==s['control'],key;assert g['canonical_forms']==s['canonical_forms'],key;assert g.get('prompt_html')==s.get('prompt_html'),key;assert g.get('continuation_html')==s.get('continuation_html'),key
 if s.get('formula_latex'):assert g.get('formula_latex')==s['formula_latex'] and '<math' in g.get('formula_mathml',''),key
 if s.get('left_latex'):assert len(g.get('left_html',[]))==4 and all('<math' in x for x in g['left_html']),key
 if s.get('right_latex'):assert len(g.get('right_html',[]))==4 and all('<math' in x for x in g['right_html']),key
answer_keys={(int(n),v['variant']) for n,rows in answers['tasks'].items() for v in rows};assert answer_keys==set(source)
assert visual['status']=='PASS' and len(visual['records'])==25
for r in visual['records']:
 p=ROOT/'assets'/f"{r['id']}.webp";assert p.exists(),r['id'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],r['id'];assert r['geometry_clipped'] is False,r['id'];assert r['source_boundary_ink_px']==0,r['id'];assert r['status']=='PASS',r['id']
for r in formula['records']:
 p=ROOT/r['source_page_file'];assert p.exists(),r['example'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['source_page_sha256'],r['example']
for n in range(4,8):
 p=ROOT/'source-evidence'/'printed-pages'/f'page-{n:02d}.webp';assert p.exists() and p.stat().st_size>10000
all_text='\n'.join(p.read_text(encoding='utf-8',errors='ignore') for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower() in {'.txt','.json','.py','.js','.html','.yml','.md'});assert 'v2.6-literal-audited' not in all_text
print('SOURCE FIDELITY PASS: 70 examples, 25 complete source visuals, 6 formula/glyph cases')
