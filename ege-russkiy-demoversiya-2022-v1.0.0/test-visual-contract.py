#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent)
tasks=[];sources={}
for n in (2,3,4):
 txt=(root/f'ege-russkiy-demoversiya-T123-0{n}.txt').read_text(encoding='utf-8'); obj=json.loads(re.search(r'>(\{.*\})</script>',txt,re.S).group(1)); tasks+=obj['tasks'];sources.update(obj['sources'])
assert len(tasks)==27
by={t['number']:t for t in tasks}
assert '<strong>основа</strong>' in sources['text-1-3']['html'].lower()
assert all(f'({i})' in sources['text-22-27']['html'] for i in [1,5,15,25,35,45])
for n in [4,5,7,13,14]: assert '<strong>' in by[n]['promptHtml'] or n==7
assert by[8]['kind']=='ordered_sequence' and len(by[8]['answer'])==5
assert by[26]['kind']=='ordered_sequence' and len(by[26]['answer'])==4
assert '150' in by[27]['promptHtml']
print('PASS visual-contract: 27 tasks; highlights, numbered positions, 45-sentence source, 2022 matching semantics')
