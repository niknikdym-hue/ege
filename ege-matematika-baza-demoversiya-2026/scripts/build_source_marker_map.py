#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COORD=ROOT/'source-diagnostics'/'canonical-coordinates'
PAGES=[10,11,14,15,16,18,19,20,21,22,25,26,28]
TASK_NUMBERS={3,4,6,7,9,10,11,12,13,18,19,21}
result={}
for page in PAGES:
    data=json.loads((COORD/f'page-{page:02d}.json').read_text(encoding='utf-8'))
    markers=[]
    for w in data['words']:
        text=w['text'].strip()
        kind=None
        if text=='ИЛИ': kind='OR'
        elif text=='Ответ:': kind='ANSWER'
        elif text.isdigit() and int(text) in TASK_NUMBERS and w['x0']<45: kind='TASK_NUMBER'
        if kind:
            markers.append({'kind':kind,'text':text,'x0':w['x0'],'y0':w['y0'],'x1':w['x1'],'y1':w['y1']})
    markers.sort(key=lambda x:(x['y0'],x['x0']))
    result[str(page)]={'page':page,'markers':markers}
(ROOT/'source-diagnostics'/'CANONICAL-SOURCE-MARKERS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=[]
for page,row in result.items():
    lines.append(f'===== PAGE {page} =====')
    for m in row['markers']:
        lines.append(f"{m['kind']:11s} y={m['y0']:.3f}..{m['y1']:.3f} x={m['x0']:.3f} {m['text']}")
    lines.append('')
(ROOT/'source-diagnostics'/'CANONICAL-SOURCE-MARKERS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Canonical source marker map built')
