from pathlib import Path
import json, os, sys, time
from playwright.sync_api import sync_playwright

URL=sys.argv[1]
MODE=sys.argv[2] if len(sys.argv)>2 else 'full'
OUT=Path(os.environ.get('EVIDENCE_DIR','/tmp/physics-final-evidence')); OUT.mkdir(parents=True,exist_ok=True)
KEY='eksamio_ege_physics_demo_2026_v2'
errors=[]
visual_tasks={1:1,2:1,6:2,7:1,8:1,10:1,19:1,21:1,22:1,23:1,25:1}
widths=[1280,768,390,360,320]

def state_set(page, **updates):
    page.evaluate("""([key,updates])=>{let s=JSON.parse(localStorage.getItem(key)||'{}'); Object.assign(s,updates); localStorage.setItem(key,JSON.stringify(s));}""",[KEY,updates])

def assert_visual(page,n,expected):
    page.locator('#ephys-nav button').nth(n-1).click()
    page.wait_for_timeout(80)
    if page.locator('#ephys-task-stage svg').count()!=0:
        raise AssertionError(f'task {n}: SVG remains visible')
    imgs=page.locator('#ephys-task-stage img.ephys-source-crop')
    if imgs.count()!=expected:
        raise AssertionError(f'task {n}: expected {expected} source crops, got {imgs.count()}')
    for i in range(imgs.count()):
        d=imgs.nth(i).evaluate("""el=>({w:el.getBoundingClientRect().width,h:el.getBoundingClientRect().height,max:Number(el.dataset.maxWidth),nw:el.naturalWidth,nh:el.naturalHeight,vw:innerWidth})""")
        if d['nw']<=0 or d['nh']<=0 or d['w']<=0 or d['h']<=0:
            raise AssertionError(f'task {n}: unloaded/zero crop {d}')
        if d['w']>d['max']+1.5 or d['w']>d['vw']+1:
            raise AssertionError(f'task {n}: oversized crop {d}')

def set_variant(page,v,status='running'):
    state_set(page,variant26=v,current=26,status=status,endsAt=int(time.time()*1000)+3600000,startedAt=int(time.time()*1000)-1000)
    page.reload(wait_until='networkidle')

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

    # State persistence gate.
    page.locator('#ephys-answer-input').fill('-1')
    page.reload(wait_until='networkidle')
    if page.locator('#ephys-answer-input').input_value()!='-1': raise AssertionError('state restore failed')

    # Calculator gate.
    page.locator('#ephys-calculator').click(); page.locator('#ephys-calc-expression').fill('sqrt(16)+sin(30)'); page.locator('#ephys-calc-expression').press('Enter')
    if page.locator('#ephys-calc-result').inner_text().strip()!='4.5': raise AssertionError('calculator regression')
    if MODE=='full': page.screenshot(path=str(OUT/'calculator-1280.png'),full_page=False)
    page.locator('#ephys-modal-close').click()

    # Physics keyboard gate on extended answer and draft.
    page.locator('#ephys-nav button').nth(20).click(); page.wait_for_timeout(100)
    if page.locator('.ephys-symbol-keyboard').count()<2: raise AssertionError('symbol keyboards missing for answer/draft')
    answer=page.locator('#ephys-answer-input'); answer.fill('v');
    page.locator('.ephys-symbol-keyboard').first.locator('button[data-symbol="²"]').click()
    if answer.input_value()!='v²': raise AssertionError('symbol keyboard insertion failed')

    if MODE=='full':
        # All official prompt visuals at all acceptance widths.
        for w in widths:
            page.set_viewport_size({'width':w,'height':900 if w>=768 else 760})
            state_set(page,status='running',current=1,endsAt=int(time.time()*1000)+3600000)
            page.reload(wait_until='networkidle')
            for n,count in visual_tasks.items(): assert_visual(page,n,count)
            # Task 26 alternatives: v1 has no prompt image, v2/v3 one exact official crop.
            for v,count in [(1,0),(2,1),(3,1)]:
                set_variant(page,v)
                if page.locator('#ephys-task-stage svg').count()!=0: raise AssertionError(f'task26 v{v}: SVG visible')
                imgs=page.locator('#ephys-task-stage img.ephys-source-crop')
                if imgs.count()!=count: raise AssertionError(f'task26 v{v}: prompt crop count {imgs.count()} != {count}')
                for i in range(imgs.count()):
                    d=imgs.nth(i).evaluate("el=>({w:el.getBoundingClientRect().width,max:Number(el.dataset.maxWidth),nw:el.naturalWidth,vw:innerWidth})")
                    if d['nw']<=0 or d['w']>d['max']+1.5 or d['w']>d['vw']+1: raise AssertionError(f'task26 v{v}: size {d}')
            overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            if overflow>2: raise AssertionError(f'horizontal overflow at {w}: {overflow}')

        # Representative screenshots for visual review.
        page.set_viewport_size({'width':1280,'height':900}); state_set(page,status='running',current=1,variant26=1,endsAt=int(time.time()*1000)+3600000); page.reload(wait_until='networkidle'); page.screenshot(path=str(OUT/'task-01-1280.png'),full_page=False)
        page.set_viewport_size({'width':390,'height':844}); page.locator('#ephys-nav button').nth(21).click(); page.screenshot(path=str(OUT/'task-22-390.png'),full_page=False)
        page.locator('#ephys-nav button').nth(24).click(); page.screenshot(path=str(OUT/'task-25-390.png'),full_page=False)

        # Scorer regression: official short-answer key must produce 28/28.
        correct={
          '1':'-1','2':'16','3':'10','4':'2.25','5':['3','5'],'6':['4','3'],'7':'4','8':'0.75','9':['3','5'],'10':['3','3'],
          '11':'100','12':'2','13':'4','14':['1','3'],'15':['1','2'],'16':'4','17':['1','2'],'18':['2','3','4'],'19':{'value':'136','error':'3'},'20':['2','5']}
        page.set_viewport_size({'width':1280,'height':900})
        st={'version':2,'status':'running','current':1,'answers':correct,'drafts':{},'flagged':{},'startedAt':int(time.time()*1000)-1000,'endsAt':int(time.time()*1000)+3600000,'completedAt':None,'variant26':1,'selfScores':{},'shortScore':0}
        page.evaluate('([k,s])=>localStorage.setItem(k,JSON.stringify(s))',[KEY,st]); page.reload(wait_until='networkidle'); page.locator('#ephys-finish-top').click(); page.wait_for_timeout(150)
        saved=page.evaluate('k=>JSON.parse(localStorage.getItem(k))',KEY)
        if saved.get('status')!='finished' or saved.get('shortScore')!=28: raise AssertionError(f'scorer failed: {saved.get("shortScore")}')

        # Review-side official figures for each task26 alternative; v1 must contain no invented solution figure.
        for v,expected in [(1,0),(2,1),(3,1)]:
            state_set(page,status='finished',variant26=v,current=26); page.reload(wait_until='networkidle'); page.wait_for_timeout(120)
            last=page.locator('#ephys-review .ephys-review-item').last
            c=last.locator('details .ephys-solution img.ephys-source-crop').count()
            s=last.locator('details .ephys-solution svg').count()
            if c!=expected or s!=0: raise AssertionError(f'task26 v{v} review source visual mismatch crops={c} svg={s}')

    if errors: raise AssertionError('browser errors: '+' | '.join(errors[:10]))
    result={'result':'PASS','mode':MODE,'severe_js_errors':0,'state_restore':'PASS','calculator':'PASS','symbol_keyboard':'PASS'}
    if MODE=='full': result.update({'visual_tasks_checked':sorted(visual_tasks),'responsive_widths':widths,'task26_variants':[1,2,3],'scorer':'PASS_28_OF_28','visual_source':'PASS_EXACT_PDF_CROPS','visual_size':'PASS_PER_ASSET_LIMITS'})
    (OUT/('browser-result.json' if MODE=='full' else 'clean-unpack-browser-result.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    browser.close()
print('BROWSER_GATE_PASS',MODE)
