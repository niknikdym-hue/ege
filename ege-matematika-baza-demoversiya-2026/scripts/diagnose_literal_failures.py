#!/usr/bin/env python3
import difflib
import html
import json
import re
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'matematika-source-2026'/'canonical-printed-pages'/'base-demo'
EVIDENCE=ROOT/'ege-matematika-baza-demoversiya-2026-LITERAL-AUDIT-EVIDENCE.json'
TAG=re.compile(r'<[^>]+>')
SPACE=re.compile(r'\s+')

def norm(s):
    s=html.unescape(TAG.sub(' ',s or ''))
    s=unicodedata.normalize('NFC',s).replace('\u00a0',' ')
    return SPACE.sub(' ',s).strip()

def best_window(target, source):
    tw=target.split(); sw=source.split()
    if not tw or not sw: return 0.0,''
    n=len(tw)
    best=(0.0,0,0)
    for size in range(max(3,n-5), min(len(sw),n+7)+1):
        step=1
        for i in range(0,len(sw)-size+1,step):
            cand=sw[i:i+size]
            ratio=difflib.SequenceMatcher(None,tw,cand,autojunk=False).ratio()
            if ratio>best[0]: best=(ratio,i,i+size)
    return best[0],' '.join(sw[best[1]:best[2]])

data=json.loads(EVIDENCE.read_text(encoding='utf-8'))
rows=[]
for f in data['failures']:
    target=norm(f['text'])
    source=norm((SOURCE/f"page-{f['page']:02d}.txt").read_text(encoding='utf-8'))
    ratio,candidate=best_window(target,source)
    diff=list(difflib.ndiff(target.split(),candidate.split()))
    rows.append({**f,'similarity':round(ratio,4),'nearest_source':candidate,'word_diff':diff})

out={'failure_count':len(rows),'records':rows}
(ROOT/'source-diagnostics'/'LITERAL-FAILURE-DIFF.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[]
for r in rows:
    lines += [f"===== {r['example']} {r['field']} page={r['page']} similarity={r['similarity']} =====",
              'NEW: '+r['text'],'SRC: '+r['nearest_source'],'DIFF: '+' '.join(r['word_diff']),'']
(ROOT/'source-diagnostics'/'LITERAL-FAILURE-DIFF.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Literal failure diagnostics:',len(rows))
