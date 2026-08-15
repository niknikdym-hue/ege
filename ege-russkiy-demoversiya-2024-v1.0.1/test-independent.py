from pathlib import Path
import json,re,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent);bad=[];checks=0
def ck(c,m):
 global checks;checks+=1
 if not c:bad.append(m)
# Official FIPI 2024 key, including official OR branches captured in the demo.
expected={1:'все',2:'34',3:'1234',4:'24',5:'праздничный',6:['очень','одержать'],7:'полутораста',8:'43827',9:'124',10:'134',11:'15',12:'235',13:['124','35'],14:['14','135','24'],15:['125','34'],16:'125',17:'34',18:'124567',19:'34',20:'23',21:['13','235','24'],22:['235','14'],23:['35','124'],24:['нет дела','дела нет','нет никакого дела','никакого дела нет'],25:'21',26:'5149'}
tasks=[]
for i in (2,3,4):
 s=(root/f'ege-russkiy-demoversiya-T123-0{i}.txt').read_text(encoding='utf-8');m=re.search(r'<script type="application/json"[^>]*>(.*?)</script>',s,re.S);tasks+=json.loads(m.group(1))['tasks']
by={t['number']:t for t in tasks};ck(len(by)==27,'27 tasks')
for n,w in expected.items():
 t=by[n]
 if isinstance(w,list):
  if n==24: got=[t['answer'],*t.get('altAnswers',[])]
  else: got=[v['answer'] for v in t.get('variants',[])]
  for x in w: ck(x in got,f'task {n}: missing official key {x}')
 else: ck(t['answer']==w,f'task {n}: {t["answer"]}!={w}')
ck(sum(by[n]['maxScore'] for n in range(1,27))==29,'part1 max 29')
ck(by[27]['maxScore']==21,'essay max 21');ck(29+21==50,'total max 50')
ck(by[8]['maxScore']==2 and by[26]['maxScore']==3,'partial tasks max 2/3')
contract=json.loads((root/'ege-russkiy-demoversiya-INTERACTION-CONTRACT.json').read_text(encoding='utf-8'))
ctrl={x['number']:x['control'] for x in contract['tasks']}
ck(ctrl[8]=='position_selects','task8 position selects');ck(ctrl[26]=='position_selects','task26 position selects');ck(ctrl[27]=='textarea','essay textarea')
essay_contract=next(x for x in contract['tasks'] if x['number']==27);ck(not essay_contract['automatic_scoring'],'essay expert only')
passport=json.loads((root/'YEAR-PASSPORT-2024.json').read_text(encoding='utf-8'))
ck(passport['source_year']==2024,'source year');ck(passport['public_url']=='/ege/russkiy/demoversiya/2024/','archive URL')
# 2024 essay bands: <=69 zero; 70-149 reduced K7-K12; 150+ normal.
blob=json.dumps(passport,ensure_ascii=False).lower();ck('69' in blob,'<=69 essay rule');ck('70' in blob and '149' in blob,'70-149 essay rule');ck('150' in blob,'150+ essay rule')
# no stale year IDs in publishable runtime
for f in root.glob('ege-russkiy-demoversiya-*'):
 if f.suffix in {'.txt','.html','.json'}:
  s=f.read_text(errors='ignore')
  ck('eksamio_ege_russian_demo_2025' not in s,f'stale 2025 storage in {f.name}')
  ck('eksamio_ege_russian_demo_2026' not in s,f'stale 2026 storage in {f.name}')
for i in range(1,6):ck((root/f'ege-russkiy-demoversiya-T123-0{i}.txt').stat().st_size<55000,f'T123-{i} <55KB')
seo=(root/'ege-russkiy-demoversiya-SEO.txt').read_text();head=(root/'ege-russkiy-demoversiya-HEAD.txt').read_text();ck('/2024/' in seo and '/2024/' in head,'2024 canonical/SEO')
if bad:
 print('NO-GO independent',len(bad),'/',checks);print('\n'.join(bad));sys.exit(1)
print(f'PASS independent: {checks} checks; official keys/variants, controls, 2024 scoring model, release hygiene')
