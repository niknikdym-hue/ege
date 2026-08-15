#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
tasks=[];sources={}
for f in sorted(root.glob('ege-russkiy-demoversiya-T123-*.txt')):
 s=f.read_text(encoding='utf-8')
 for m in re.finditer(r'<script type="application/json" id="edemo-data-[^"]+">(.*?)</script>',s,re.S):
  d=json.loads(m.group(1));sources.update(d.get('sources',{}));tasks.extend(d.get('tasks',[]))
assert len(tasks)==27
by={t['number']:t for t in tasks};assert sorted(by)==list(range(1,28))
src=sources['text-1-3']['html']
for token in ['живых','средой','мириться','основа','ключ']:
 assert re.search(r'<strong[^>]*>\s*'+re.escape(token)+r'\s*</strong>',src,re.I),token
assert '&lt;…&gt;' in src or '<…>' in src
# Visual targets: task4 uses a single uppercase stress letter; tasks 5,13,14 use explicit markup.
assert re.search(r'[а-яё][А-ЯЁ][а-яё]|^[А-ЯЁ][а-яё]', re.sub(r'<[^>]+>','',by[4]['promptHtml']), re.M), 'task4 stress marker'
for n in [5,13,14]:
 assert '<strong' in by[n]['promptHtml'],f'task{n} explicit marker'
assert by[13]['kind']=='word' and '<strong' in by[13]['promptHtml']
assert by[14]['kind']=='word_compact' and len(re.findall(r'<strong',by[14]['promptHtml']))>=2
src2=sources['text-22-27']['html']
for n in range(1,32): assert f'({n})' in src2,f'missing ({n})'
assert 'повествование с элементами описания' in by[23]['promptHtml'].lower()
assert by[23]['answer']=='345'
assert by[26]['answer']=='5149'
assert not any(t.get('variants') for t in tasks)
print('PASS visual-contract: 27 tasks; explicit highlights; 31-sentence source; 2023 task13/14/23/26 semantics')
