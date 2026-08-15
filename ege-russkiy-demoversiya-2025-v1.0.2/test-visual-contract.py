#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
all_tasks=[]; sources={}
for f in sorted(root.glob('ege-russkiy-demoversiya-T123-*.txt')):
    s=f.read_text(encoding='utf-8')
    for m in re.finditer(r'<script type="application/json" id="edemo-data-[^"]+">(.*?)</script>',s,re.S):
        data=json.loads(m.group(1)); sources.update(data.get('sources',{})); all_tasks.extend(data.get('tasks',[]))
assert len(all_tasks)==27, f'expected 27 tasks, got {len(all_tasks)}'
by={t['number']:t for t in all_tasks}
src=sources['text-1-3']['html']
for token in ['ансамбли','простая','числа','вкус','доставляет']:
    assert re.search(r'<strong[^>]*>\s*'+re.escape(token)+r'\s*</strong>',src,re.I), f'task2 target not explicitly highlighted: {token}'
assert len(re.findall(r'<strong[^>]*>',src)) >= 5, 'task2 source must contain at least five explicit highlights'
assert '<…>' in src or '&lt;…&gt;' in src, 'task1 source gap missing'
for n in [4,5,7,13,14]:
    prompt=by[n]['promptHtml']
    visible=('<strong>' in prompt or bool(re.search(r'[А-ЯЁ]{2,}',prompt)) or bool(re.search(r'[а-яё][А-ЯЁ][а-яё]',prompt)))
    assert visible, f'task {n}: no visible target marker'
# sentence-numbered source for 23-27
src2=' '.join(v.get('html','') for k,v in sources.items() if k!='text-1-3')
for n in [23,24,25,26,27]:
    assert n in by, f'task {n} missing'
print('PASS visual-contract: 27 tasks; task2 source highlights; target markers')
