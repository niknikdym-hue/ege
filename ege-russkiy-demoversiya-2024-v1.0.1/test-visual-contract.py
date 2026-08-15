#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
all_tasks=[];sources={}
for f in sorted(root.glob('ege-russkiy-demoversiya-T123-*.txt')):
    s=f.read_text(encoding='utf-8')
    for m in re.finditer(r'<script type="application/json" id="edemo-data-[^"]+">(.*?)</script>',s,re.S):
        data=json.loads(m.group(1)); sources.update(data.get('sources',{})); all_tasks.extend(data.get('tasks',[]))
assert len(all_tasks)==27, f'expected 27 tasks, got {len(all_tasks)}'
by={t['number']:t for t in all_tasks}
assert sorted(by)==list(range(1,28)), 'task numbering must be 1..27'
# Task 2 says five words in source are highlighted: require explicit HTML markup, not typography-by-accident.
src=sources['text-1-3']['html']
for token in ['живых','средой','мириться','основа','ключ']:
    assert re.search(r'<strong[^>]*>\s*'+re.escape(token)+r'\s*</strong>',src,re.I), f'task2 target not explicitly highlighted: {token}'
assert len(re.findall(r'<strong[^>]*>',src)) >= 5, 'task2 source must contain >=5 explicit highlights'
assert '&lt;…&gt;' in src or '<…>' in src, 'task1 source gap missing'
# Any task explicitly referring to highlighted text must visibly mark targets in its own prompt/source.
for n in [4,5,13,14]:
    prompt=by[n]['promptHtml']
    visible=('<strong' in prompt or bool(re.search(r'[А-Яа-яЁё][А-ЯЁ][А-Яа-яЁё]',prompt)) or bool(re.search(r'[А-ЯЁ]{2,}',prompt)))
    assert visible, f'task {n}: no visible target marker'
# Long source must have all 31 numbered sentences because tasks 22-27 reference ranges through 31.
src2=sources['text-22-27']['html']
for n in range(1,32):
    assert f'({n})' in src2, f'long source missing sentence ({n})'
# Official OR branches represented in demo package.
expected_variant_counts={6:2,13:2,14:3,15:2,21:3,22:2,23:2}
for n,c in expected_variant_counts.items():
    assert len(by[n].get('variants',[]))==c, f'task {n}: expected {c} variants, got {len(by[n].get("variants",[]))}'
# The corrected task 23 must be semantically aligned with its key.
assert 'верными' in by[23]['promptHtml'].lower() and by[23]['answer']=='35', 'task23 base prompt/key mismatch'
assert by[23]['variants'][1]['answer']=='124' and 'ошибоч' in by[23]['variants'][1]['promptHtml'].lower(), 'task23 alternate mismatch'
print('PASS visual-contract: 27 tasks; explicit task2 highlights; sentence numbering; OR variants; task23 semantic key')
