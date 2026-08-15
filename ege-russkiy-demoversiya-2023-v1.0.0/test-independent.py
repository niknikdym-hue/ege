#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
bad=[];checks=0
def ck(c,m):
 global checks;checks+=1
 if not c:bad.append(m)
expected={1:'все',2:'34',3:'1234',4:'24',5:'праздничный',6:'очень',7:'полутораста',8:'43827',9:'124',10:'134',11:'15',12:'235',13:'неподвижные',14:'навстречу вдали',15:'124',16:'125',17:'34',18:'124567',19:'34',20:'23',21:'13',22:'235',23:'345',24:'нет дела',25:'21',26:'5149'}
tasks=[];sources={}
for i in (2,3,4):
 s=(root/f'ege-russkiy-demoversiya-T123-0{i}.txt').read_text(encoding='utf-8');m=re.search(r'<script type="application/json"[^>]*>(.*?)</script>',s,re.S);d=json.loads(m.group(1));tasks+=d['tasks'];sources.update(d.get('sources',{}))
by={t['number']:t for t in tasks};ck(len(by)==27,'27 tasks')
for n,w in expected.items(): ck(by[n]['answer']==w,f'task {n}: {by[n]["answer"]}!={w}')
ck(not any(t.get('variants') for t in tasks),'2023 exact demo has no synthetic OR variants')
ck(sum(by[n]['maxScore'] for n in range(1,27))==30,'part1 max 30')
ck(by[8]['maxScore']==3 and by[26]['maxScore']==3,'task8/task26 max 3/3')
ck(by[27]['maxScore']==24,'essay max24');ck(30+24==54,'total max54')
ck(by[13]['kind']=='word','task13 word input');ck(by[14]['kind']=='word_compact','task14 two-word input')
ck('повествование с элементами описания' in by[23]['promptHtml'].lower() and by[23]['answer']=='345','task23 wording/key')
ck(set([by[24]['answer'],*by[24].get('altAnswers',[])])=={'нет дела','дела нет','нет никакого дела','никакого дела нет'},'task24 accepted forms')
contract=json.loads((root/'ege-russkiy-demoversiya-INTERACTION-CONTRACT.json').read_text(encoding='utf-8'));ctrl={x['number']:x['control'] for x in contract['tasks']}
ck(ctrl[8]=='position_selects' and ctrl[26]=='position_selects','position selects');ck(ctrl[13]=='text_input' and ctrl[14]=='text_input','task13/14 inputs');ck(ctrl[25]=='sentence_number_checkboxes','task25 numbers')
passport=json.loads((root/'YEAR-PASSPORT-2023.json').read_text(encoding='utf-8'))
ck(passport['part1MaxScore']==30 and passport['essayMaxScore']==24 and passport['totalMaxScore']==54,'passport scores')
ck(passport['source_year']==2023 and passport['public_url']=='/ege/russkiy/demoversiya/2023/','passport year/url')
blob=json.dumps(passport,ensure_ascii=False);ck('69' in blob and '70-149' in blob and '150' in blob,'essay word bands')
for i in range(1,6):ck((root/f'ege-russkiy-demoversiya-T123-0{i}.txt').stat().st_size<55000,f'T123-{i}<55KB')
for f in root.glob('ege-russkiy-demoversiya-*'):
 if f.suffix in {'.txt','.html','.json'}:
  s=f.read_text(errors='ignore');ck('2024' not in s,f'stale 2024 in {f.name}');ck('2025' not in s,f'stale 2025 in {f.name}');ck('2026' not in s,f'stale 2026 in {f.name}')
if bad:
 print('NO-GO independent',len(bad),'/',checks);print('\n'.join(bad));sys.exit(1)
print(f'PASS independent: {checks} checks; official 2023 keys, controls, scoring, essay model, release hygiene')
