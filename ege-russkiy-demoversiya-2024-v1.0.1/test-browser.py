from playwright.sync_api import sync_playwright
from pathlib import Path
import sys,json,re
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent); HTML=ROOT/'ege-russkiy-demoversiya-PREVIEW.html'; fail=[]
def ck(c,m):
    if not c: fail.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--allow-file-access-from-files'])
    page=b.new_page(viewport={'width':1280,'height':900});page.set_default_timeout(5000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return Object.prototype.hasOwnProperty.call(this._d,k)?this._d[k]:null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}}})")
    page.set_content(HTML.read_text(encoding='utf-8'),wait_until='domcontentloaded')
    ck(page.locator('#edemo-start').is_visible(),'start visible');page.click('#edemo-start');ck(page.locator('#edemo-nav .edemo-nav-btn').count()==27,'27 nav')
    # task2: five source highlights must be visible, and task options are checkboxes
    page.locator('#edemo-nav .edemo-nav-btn').nth(1).click();ck(page.locator('.edemo-source strong').count()>=5,'task2 source has 5 visible highlights');ck(page.locator('[data-choice]').count()==5,'task2 5 choices')
    for v in ['3','4']: page.locator(f'[data-choice="{v}"]').check(force=True)
    # task8 matching controls
    page.locator('#edemo-nav .edemo-nav-btn').nth(7).click();ck(page.locator('[data-match-index]').count()==5,'task8 5 selects')
    for i,v in enumerate(['4','3','8','2','7']):page.locator(f'[data-match-index="{i}"]').select_option(v,force=True)
    # task23 corrected semantic/key visible
    page.locator('#edemo-nav .edemo-nav-btn').nth(22).click();p23=page.locator('.edemo-task-prompt').inner_text().lower();ck(('верными' in p23) or ('ошибочными' in p23),'task23 semantic variant visible')
    # task25 uses sentence-number checkbox tokens 15-22, not digit chars
    page.locator('#edemo-nav .edemo-nav-btn').nth(24).click();vals=page.locator('[data-choice]').evaluate_all("e=>e.map(x=>x.getAttribute('data-choice'))");ck(vals==[str(x) for x in range(15,23)],f'task25 sentence options {vals}');page.locator('[data-choice="21"]').check(force=True)
    # task26 ordered A-D selects
    page.locator('#edemo-nav .edemo-nav-btn').nth(25).click();ck(page.locator('[data-match-index]').count()==4,'task26 four selects')
    for i,v in enumerate(['5','1','4','9']):page.locator(f'[data-match-index="{i}"]').select_option(v,force=True)
    # variant choice persistence: task6
    page.locator('#edemo-nav .edemo-nav-btn').nth(5).click();badge=page.locator('.edemo-variant-badge').inner_text();prompt=page.locator('.edemo-task-prompt').inner_text();state=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2024_v1_0_1'))")
    ck(state and '6' in {str(k):v for k,v in state.get('variantChoices',{}).items()},'task6 variant persisted')
    page.set_content(HTML.read_text(encoding='utf-8'),wait_until='domcontentloaded');
    if page.locator('#edemo-resume').is_visible():page.click('#edemo-resume')
    ck(page.locator('.edemo-variant-badge').inner_text()==badge,'OR badge persists');ck(page.locator('.edemo-task-prompt').inner_text()==prompt,'OR prompt persists')
    page.once('dialog',lambda d:d.accept());page.click('#edemo-finish-top');ck(page.locator('#edemo-total-score').inner_text()=='—','official total separated')
    # 2024 essay gates: 70-149 reduced; <=69 zero
    page.check('#edemo-eligibility-confirm');page.check('#edemo-short-band')
    caps={'K7':2,'K8':2,'K9':1,'K10':1,'K11':0,'K12':0}
    for k,cap in caps.items():
        vals=[x for x in page.locator(f'#edemo-{k} option').evaluate_all("e=>e.map(x=>x.value)") if x!=''];ck(max(map(int,vals))==cap if vals else cap==0,f'{k} short cap {cap}')
    page.check('[data-zero-reason="under70"]');ck(page.locator('#edemo-K1').is_disabled(),'under70 blocks criteria');ck(page.locator('#edemo-essay-score').inner_text()=='0','under70 score 0')
    for w,h in [(320,700),(360,800),(390,844),(768,1024),(1280,900)]:
        page.set_viewport_size({'width':w,'height':h});overflow=page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1');ck(not overflow,f'overflow {w}')
    ck(not errors,'browser errors: '+','.join(errors));b.close()
if fail:
    print('FAIL browser',len(fail));print('\n'.join(fail));sys.exit(1)
print('PASS browser: 27 nav, visual highlights, typed controls, task23 fix, OR persistence, 2024 essay bands, responsive')
