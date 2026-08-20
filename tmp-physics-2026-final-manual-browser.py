from pathlib import Path
import json, os, sys, time
from playwright.sync_api import sync_playwright

URL=sys.argv[1]
MODE=sys.argv[2] if len(sys.argv)>2 else 'full'
OUT=Path(os.environ.get('EVIDENCE_DIR','/tmp/physics-final-manual-evidence')); OUT.mkdir(parents=True,exist_ok=True)
KEY='eksamio_ege_physics_demo_2026_v2'
CORRECTED={'t02','t06a','t21s','t22s','t24sb','t25p','t25s','t26v2p','t26v2s'}
PROMPT_VISUALS={1:['t01'],2:['t02'],6:['t06a','t06b'],7:['t07'],8:['t08'],10:['t10'],19:['t19'],21:['t21p'],22:['t22p'],23:['t23p'],25:['t25p']}
WIDTHS=[1280,768,390,360,320]
errors=[]

def set_state(page,**u):
 page.evaluate("""([k,u])=>{let s=JSON.parse(localStorage.getItem(k)||'{}'); Object.assign(s,u); localStorage.setItem(k,JSON.stringify(s));}""",[KEY,u])

def open_task(page,n):
 page.locator('#ephys-nav button').nth(n-1).click(); page.wait_for_timeout(60)

def assert_crop(el,cid):
 d=el.evaluate("""e=>({id:e.dataset.sourceCrop,w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height,max:Number(e.dataset.maxWidth),nw:e.naturalWidth,nh:e.naturalHeight,vw:innerWidth})""")
 if d['id']!=cid or d['nw']<=0 or d['nh']<=0 or d['w']<=0 or d['h']<=0: raise AssertionError(f'bad crop {cid}: {d}')
 if d['w']>d['max']+1.5 or d['w']>d['vw']+1: raise AssertionError(f'oversized crop {cid}: {d}')

def set_variant(page,v,status='running'):
 now=int(time.time()*1000); set_state(page,variant26=v,current=26,status=status,startedAt=now-1000,endsAt=now+3600000); page.reload(wait_until='networkidle'); page.wait_for_timeout(80)

with sync_playwright() as p:
 browser=p.chromium.launch()
 context=browser.new_context(viewport={'width':1280,'height':900})
 page=context.new_page()
 page.on('console',lambda m: errors.append(f'console:{m.type}:{m.text}') if m.type=='error' else None)
 page.on('pageerror',lambda e: errors.append('pageerror:'+str(e)))
 page.on('dialog',lambda d:d.accept())
 page.goto(URL,wait_until='networkidle')
 if page.locator('#ege-physics-demo-2026').count()!=1: raise AssertionError('root missing')
 page.locator('#ephys-start').click(); page.wait_for_timeout(100)
 # state restore
 page.locator('#ephys-answer-input').fill('-1'); page.reload(wait_until='networkidle')
 if page.locator('#ephys-answer-input').input_value()!='-1': raise AssertionError('state restore failed')
 # calculator
 page.locator('#ephys-calculator').click(); page.locator('#ephys-calc-expression').fill('sqrt(16)+sin(30)'); page.locator('#ephys-calc-expression').press('Enter')
 if page.locator('#ephys-calc-result').inner_text().strip()!='4.5': raise AssertionError('calculator failed')
 page.locator('#ephys-modal-close').click()
 # keyboard
 open_task(page,21)
 if page.locator('.ephys-symbol-keyboard').count()<2: raise AssertionError('symbol keyboards missing')
 a=page.locator('#ephys-answer-input'); a.fill('v'); k=page.locator('.ephys-symbol-keyboard').first.locator('button.ephys-symbol-key').first
 if k.get_attribute('data-symbol')!='²': raise AssertionError('UTF-8 physics keyboard contract broken')
 k.click()
 if a.input_value()!='v²': raise AssertionError('symbol insertion failed')

 if MODE=='full':
  for w in WIDTHS:
   page.set_viewport_size({'width':w,'height':900 if w>=768 else 780})
   now=int(time.time()*1000); set_state(page,status='running',current=1,variant26=1,startedAt=now-1000,endsAt=now+3600000); page.reload(wait_until='networkidle')
   for n,ids in PROMPT_VISUALS.items():
    open_task(page,n)
    if page.locator('#ephys-task-stage svg').count(): raise AssertionError(f'task {n}: reconstructed svg visible')
    els=page.locator('#ephys-task-stage img.ephys-source-crop')
    got=[els.nth(i).get_attribute('data-source-crop') for i in range(els.count())]
    if got!=ids: raise AssertionError(f'task {n}: crop ids {got} != {ids}')
    for i,cid in enumerate(ids): assert_crop(els.nth(i),cid)
   for v,ids in [(1,[]),(2,['t26v2p']),(3,['t26v3p'])]:
    set_variant(page,v)
    els=page.locator('#ephys-task-stage img.ephys-source-crop'); got=[els.nth(i).get_attribute('data-source-crop') for i in range(els.count())]
    if got!=ids or page.locator('#ephys-task-stage svg').count(): raise AssertionError(f'task26 v{v} prompt visual mismatch {got}')
    for i,cid in enumerate(ids): assert_crop(els.nth(i),cid)
   overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
   if overflow>2: raise AssertionError(f'horizontal overflow at {w}: {overflow}')

  # scorer official short-answer key => 28/28
  correct={'1':'-1','2':'16','3':'10','4':'2.25','5':['3','5'],'6':['4','3'],'7':'4','8':'0.75','9':['3','5'],'10':['3','3'],'11':'100','12':'2','13':'4','14':['1','3'],'15':['1','2'],'16':'4','17':['1','2'],'18':['2','3','4'],'19':{'value':'136','error':'3'},'20':['2','5']}
  now=int(time.time()*1000); st={'version':2,'status':'running','current':1,'answers':correct,'drafts':{},'flagged':{},'startedAt':now-1000,'endsAt':now+3600000,'completedAt':None,'variant26':1,'selfScores':{},'shortScore':0}
  page.set_viewport_size({'width':1280,'height':900}); page.evaluate('([k,s])=>localStorage.setItem(k,JSON.stringify(s))',[KEY,st]); page.reload(wait_until='networkidle'); page.locator('#ephys-finish-top').click(); page.wait_for_timeout(150)
  saved=page.evaluate('k=>JSON.parse(localStorage.getItem(k))',KEY)
  if saved.get('shortScore')!=28 or saved.get('status')!='finished': raise AssertionError(f'scorer failed {saved.get("shortScore")}')
  # review solution visuals and no invented SVGs; expected exact source ids
  expected={21:['t21s'],22:['t22s'],23:[],24:['t24sa','t24sb'],25:['t25s']}
  for n,ids in expected.items():
   item=page.locator('#ephys-review .ephys-review-item').nth(n-1)
   imgs=item.locator('img.ephys-source-crop'); got=[imgs.nth(i).get_attribute('data-source-crop') for i in range(imgs.count())]
   if got!=ids or item.locator('svg').count(): raise AssertionError(f'review task {n}: visuals {got} != {ids}')
   for i,cid in enumerate(ids): assert_crop(imgs.nth(i),cid)
  for v,ids in [(1,[]),(2,['t26v2s']),(3,['t26v3s'])]:
   set_variant(page,v,status='finished')
   item=page.locator('#ephys-review .ephys-review-item').last; imgs=item.locator('img.ephys-source-crop'); got=[imgs.nth(i).get_attribute('data-source-crop') for i in range(imgs.count())]
   if got!=ids or item.locator('svg').count(): raise AssertionError(f'review task26 v{v}: {got} != {ids}')
   for i,cid in enumerate(ids): assert_crop(imgs.nth(i),cid)

 if errors: raise AssertionError('browser errors: '+' | '.join(errors[:8]))
 result={'result':'PASS','mode':MODE,'state_restore':'PASS','calculator':'PASS','symbol_keyboard':'PASS','severe_js_errors':0}
 if MODE=='full': result.update({'responsive_widths':WIDTHS,'scorer':'PASS_28_OF_28','all_prompt_visuals':'PASS','extended_solution_visuals':'PASS','manual_corrected_crop_ids':sorted(CORRECTED),'visual_size_gate':'PASS'})
 (OUT/('browser-result.json' if MODE=='full' else 'clean-unpack-browser-result.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 browser.close()
print('FINAL_MANUAL_BROWSER_PASS',MODE)
