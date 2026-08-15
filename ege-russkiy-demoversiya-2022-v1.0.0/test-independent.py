#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent)
checks=0
def ck(x,msg):
 global checks
 checks+=1
 if not x: raise AssertionError(msg)
parts=[]; sources={}
for n in (2,3,4):
 txt=(root/f'ege-russkiy-demoversiya-T123-0{n}.txt').read_text(encoding='utf-8')
 obj=json.loads(re.search(r'>(\{.*\})</script>',txt,re.S).group(1)); parts+=obj['tasks']; sources.update(obj['sources'])
ck(len(parts)==27,'27 tasks'); by={t['number']:t for t in parts}; ck(set(by)==set(range(1,28)),'numbers 1-27')
keys={1:'1234',2:'все',3:'2',4:'гражданство',5:'памятные',6:'очень',7:'полутораста',8:'43827',9:'34',10:'134',11:'15',12:'235',13:'неподвижные',14:'навстречувдали',15:'124',16:'125',17:'34',18:'124567',19:'34',20:'23',21:'13',22:'135',23:'145',24:'внезапно',25:'12',26:'2519'}
for n,a in keys.items(): ck(by[n]['answer']==a,f'key {n}')
ck(sum(by[n]['maxScore'] for n in range(1,27))==33,'part1 max33')
ck(by[8]['maxScore']==5,'task8 max5'); ck(by[26]['maxScore']==4,'task26 max4'); ck(by[27]['maxScore']==25,'essay max25')
ck('<strong>основа</strong>' in sources['text-1-3']['html'].lower(),'source highlight task3')
ck('(45)' in sources['text-22-27']['html'],'source has sentence45')
passport=json.loads((root/'YEAR-PASSPORT-2022.json').read_text(encoding='utf-8'))
ck(passport['part1MaxScore']==33 and passport['essayMaxScore']==25 and passport['totalMaxScore']==58,'passport scores')
ck(passport['year']==2022 and passport['url'].endswith('/2022/'),'passport year/url')
contract=json.loads((root/'ege-russkiy-demoversiya-INTERACTION-CONTRACT.json').read_text(encoding='utf-8'))
ck(len(contract['tasks'])==27,'contract27')
for t in contract['tasks']:
 ck(t['maxScore']==by[t['number']]['maxScore'],f'contract score {t["number"]}')
html=(root/'ege-russkiy-demoversiya-PREVIEW.html').read_text(encoding='utf-8')
for bad in ['2023','/54','/30','/24']: ck(bad not in html,f'no stale {bad}')
ck('/58' in html and '/33' in html and '/25' in html,'display scores')
ck('max:6' in (root/'ege-russkiy-demoversiya-T123-05.txt').read_text(encoding='utf-8'),'K2 max6 runtime')
print(f'PASS independent: {checks} checks; 2022 keys, scoring, sources, release hygiene')
