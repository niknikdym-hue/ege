from pathlib import Path
import json,re,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else '.'); bad=[]; checks=0
def ck(c,m):
 global checks; checks+=1
 if not c: bad.append(m)
# exact expected official answer map 2025
expected={1:['эти','такие'],2:'345',3:'245',4:'145',5:'праздничный',6:['очень','одержать'],7:'повидлом',8:'43827',9:'25',10:'134',11:'123',12:'245',13:['134','35'],14:['14','135','35'],15:['14','34'],16:'125',17:'134',18:'1245',19:'23',20:'1345',21:['13','235','259'],22:'75924',23:['15','234'],24:['134','25'],25:['в конце концов','может быть','оставили в покое'],26:'35'}
tasks=[]
for i in (2,3,4):
 s=(root/f'ege-russkiy-demoversiya-T123-0{i}.txt').read_text(); j=json.loads(re.search(r'>(\{.*\})</script>',s,re.S).group(1));tasks+=j['tasks']
by={t['number']:t for t in tasks}
ck(len(by)==27,'27 tasks')
for n,w in expected.items():
 t=by[n]
 if isinstance(w,list):
  if n==1: got=[t['answer'],*t.get('altAnswers',[])]
  elif n==25: got=[t['answer'],*t.get('altAnswers',[])]; got=[x for x in got if ' ' in x]
  else: got=[v['answer'] for v in t.get('variants',[])]
  for x in w: ck(x in got,f'task {n}: missing {x}')
 else: ck(t['answer']==w,f'task {n}: {t["answer"]}!={w}')
ck(by[8]['maxScore']==2 and by[22]['maxScore']==2,'partial tasks max 2')
contract=json.loads((root/'ege-russkiy-demoversiya-INTERACTION-CONTRACT.json').read_text())
ctrl={x['number']:x['control'] for x in contract['tasks']}; ck(ctrl[8]=='position_selects' and ctrl[22]=='position_selects','matching controls'); ck(ctrl[26]=='sentence_number_checkboxes','task26 sentence controls'); ck(ctrl[27]=='textarea' and not next(x for x in contract['tasks'] if x['number']==27)['automatic_scoring'],'essay expert only')
passport=json.loads((root/'YEAR-PASSPORT-2025.json').read_text()); ck(passport['source_year']==2025,'source year');ck(passport['public_url']=='/ege/russkiy/demoversiya/2025/','archive URL');ck(passport['essay_word_rules']['99_or_less']=='0/22','<=99 rule');ck('100_149' in passport['essay_word_rules'],'100-149 rule')
# no stale 2026/runtime identifiers in publishable files
for f in root.glob('ege-russkiy-demoversiya-*'):
 if f.suffix in {'.txt','.html','.json'}:
  s=f.read_text(errors='ignore')
  ck('ege-demo-2026' not in s,f'stale root in {f.name}')
  ck('eksamio_ege_russian_demo_2026' not in s,f'stale storage in {f.name}')
# T123 safe sizes
for i in range(1,6): ck((root/f'ege-russkiy-demoversiya-T123-0{i}.txt').stat().st_size<55000,f'T123-{i} <55KB')
# canonical/year
seo=(root/'ege-russkiy-demoversiya-SEO.txt').read_text();head=(root/'ege-russkiy-demoversiya-HEAD.txt').read_text(); ck('/2025/' in seo and '/2025/' in head,'2025 canonical/SEO')
if bad:
 print('NO-GO independent',len(bad),'/',checks);print('\n'.join(bad));sys.exit(1)
print(f'PASS independent: {checks} checks; official answer map, controls, year rules, release hygiene')
