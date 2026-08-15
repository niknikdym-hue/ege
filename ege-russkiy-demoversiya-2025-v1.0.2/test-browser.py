from playwright.sync_api import sync_playwright
from pathlib import Path
import sys
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else '.'); HTML=ROOT/'ege-russkiy-demoversiya-PREVIEW.html'; fail=[]
def ck(c,m):
    if not c: fail.append(m)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--allow-file-access-from-files'])
    page=b.new_page(viewport={'width':1280,'height':900}); page.set_default_timeout(5000)
    errors=[]; page.on('pageerror',lambda e: errors.append(str(e)))
    page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return Object.prototype.hasOwnProperty.call(this._d,k)?this._d[k]:null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}}})")
    page.set_content(HTML.read_text(encoding='utf-8'),wait_until='domcontentloaded')
    ck(page.locator('#edemo-start').is_visible(),'start visible'); page.click('#edemo-start')
    ck(page.locator('#edemo-nav .edemo-nav-btn').count()==27,'27 nav')
    # task 2 checkboxes
    page.locator('#edemo-nav .edemo-nav-btn').nth(1).click(); ck(page.locator('[data-choice]').count()==5,'t2 checkboxes')
    for v in ['3','4','5']: page.locator(f'[data-choice="{v}"]').check(force=True)
    # task8 matching real selects
    page.locator('#edemo-nav .edemo-nav-btn').nth(7).click(); ck(page.locator('[data-match-index]').count()==5,'t8 5 selects')
    for i,v in enumerate(['4','3','8','2','7']): page.locator(f'[data-match-index="{i}"]').select_option(v,force=True)
    # task22 matching
    page.locator('#edemo-nav .edemo-nav-btn').nth(21).click(); ck(page.locator('[data-match-index]').count()==5,'t22 5 selects')
    for i,v in enumerate(['7','5','9','2','4']): page.locator(f'[data-match-index="{i}"]').select_option(v,force=True)
    # task26 sentence number controls
    page.locator('#edemo-nav .edemo-nav-btn').nth(25).click(); vals=page.locator('[data-choice]').evaluate_all("e=>e.map(x=>x.getAttribute('data-choice'))"); ck(vals==[str(x) for x in range(33,42)],f't26 options {vals}'); page.locator('[data-choice="35"]').check(force=True)
    # OR persistence task6
    page.locator('#edemo-nav .edemo-nav-btn').nth(5).click(); badge=page.locator('.edemo-variant-badge').inner_text(); prompt=page.locator('.edemo-task-prompt').inner_text()
    state=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2025_v1_0_0'))")
    page.set_content(HTML.read_text(encoding='utf-8'),wait_until='domcontentloaded')
    if page.locator('#edemo-resume').is_visible(): page.click('#edemo-resume')
    ck(page.locator('.edemo-variant-badge').inner_text()==badge,'OR badge persists'); ck(page.locator('.edemo-task-prompt').inner_text()==prompt,'OR prompt persists')
    # finish
    page.once('dialog',lambda d:d.accept()); page.click('#edemo-finish-top'); ck(page.locator('#edemo-total-score').inner_text()=='—','official total separated')
    # essay gates 100-149 band
    page.check('#edemo-eligibility-confirm'); page.check('#edemo-short-band')
    for k in ['K7','K8','K9','K10']:
        opts=page.locator(f'#edemo-{k} option').evaluate_all("e=>e.map(x=>x.value)"); ck('3' not in opts,f'{k} short band cap')
    # <=99 zero gate
    page.check('[data-zero-reason="under100"]'); ck(page.locator('#edemo-K1').is_disabled(),'under100 blocks criteria'); ck(page.locator('#edemo-essay-score').inner_text()=='0','under100 score 0')
    # responsive
    for w,h in [(320,700),(360,800),(390,844),(768,1024),(1280,900)]:
        page.set_viewport_size({'width':w,'height':h}); overflow=page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1'); ck(not overflow,f'overflow {w}')
    ck(not errors,'browser errors: '+','.join(errors)); b.close()
if fail:
    print('FAIL browser',len(fail)); print('\n'.join(fail)); sys.exit(1)
print('PASS browser: typed controls, matching, sentence numbers, OR persistence, essay bands, responsive')
