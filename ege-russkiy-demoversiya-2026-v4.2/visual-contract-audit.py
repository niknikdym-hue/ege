import json,re
from pathlib import Path
base=Path(__file__).resolve().parent
objs=[]
for n in [2,3,4]:
    txt=(base/f'ege-russkiy-demoversiya-T123-0{n}.txt').read_text('utf-8')
    for m in re.finditer(r'<script type="application/json" id="[^"]+">(.*?)</script>',txt,re.S):
        objs.append(json.loads(m.group(1).replace('<\\/','</')))
sources={}; tasks=[]
for o in objs: sources.update(o.get('sources',{})); tasks.extend(o.get('tasks',[]))
assert len(tasks)==27
fails=[]; checks=0
def ck(c,m):
    global checks
    checks+=1
    if not c:fails.append(m)
# Specific source contracts
s13=sources['text-1-3']['html']
ck(s13.count('<strong>')==5,'text-1-3 must contain exactly 5 explicit highlighted words')
for w in ['пришёл','духовной','характер','прозрение','кровь']:
    ck(f'<strong>{w}</strong>' in s13,f'missing highlighted source word {w}')
paras=re.findall(r'<p(?:\s[^>]*)?>(.*?)</p>',s13,re.S)
ck(len(paras)>=3,'text-1-3 must have >=3 paragraphs')
ck('&lt;…&gt;' in paras[2],'task1 placeholder must be in paragraph 3')
s2327=sources['text-23-27']['html']
nums=[int(x) for x in re.findall(r'\((\d+)\)',s2327)]
ck(nums==list(range(1,48)),f'text-23-27 numbering must be 1..47, got {nums[:5]}..{nums[-5:]} len={len(nums)}')
# Every instruction that explicitly says highlighted must expose explicit visual emphasis in the relevant rendered material.
for t in tasks:
    prompt=t.get('promptHtml','')
    if re.search(r'выделен',prompt,re.I):
        sid=t.get('sourceId')
        material=(sources.get(sid,{}).get('html','') if sid else '') + prompt
        strong_count=material.count('<strong>')+material.count('<em>')+material.count('<u>')
        ck(strong_count>0,f'task {t["number"]}: instruction references highlighting but no explicit emphasis markup')
    # referenced source must exist
    if t.get('sourceId'): ck(t['sourceId'] in sources,f'task {t["number"]}: missing source {t["sourceId"]}')
# Task 13/14 explicitly mark target tokens, not only instruction words
for num,min_targets in [(13,7),(14,11)]:
    t=next(x for x in tasks if x['number']==num)
    ck(t['promptHtml'].count('<strong>')>=min_targets,f'task {num}: target forms lack explicit emphasis')
# source ranges used by tasks 25/26 exist
ck(all(f'({i})' in s2327 for i in range(10,17)),'task25 range 10-16 absent')
ck(all(f'({i})' in s2327 for i in range(17,26)),'task26 range 17-25 absent')
if fails:
    print('\n'.join(fails)); print(f'FAIL visual contract {len(fails)}/{checks}'); raise SystemExit(1)
print(f'PASS visual contract: {checks} checks')
