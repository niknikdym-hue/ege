from playwright.sync_api import sync_playwright
from pathlib import Path
import sys
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent); HTML=ROOT/'ege-russkiy-demoversiya-PREVIEW.html'; fail=[]
def ck(c,m):
 if not c: fail.append(m)
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--allow-file-access-from-files'])
 page=b.new_page(viewport={'width':1280,'height':900});page.set_default_timeout(5000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return Object.prototype.hasOwnProperty.call(this._d,k)?this._d[k]:null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}}})")
 page.set_content(HTML.read_text(encoding='utf-8'),wait_until='domcontentloaded')
 ck(page.locator('#edemo-start').is_visible(),'start visible');page.click('#edemo-start');ck(page.locator('#edemo-nav .edemo-nav-btn').count()==27,'27 nav')
 page.locator('#edemo-nav .edemo-nav-btn').nth(1).click();ck(page.locator('.edemo-source strong').count()>=5,'task2 5 source highlights');ck(page.locator('[data-choice]').count()==5,'task2 choices')
 page.locator('#edemo-nav .edemo-nav-btn').nth(7).click();ck(page.locator('[data-match-index]').count()==5,'task8 five selects')
 for i,v in enumerate(['4','3','8','2','7']): page.locator(f'[data-match-index="{i}"]').select_option(v,force=True)
 page.locator('#edemo-nav .edemo-nav-btn').nth(12).click();ck(page.locator('#edemo-answer-input').count()==1,'task13 input');ck(page.locator('.edemo-task-prompt strong').count()>=5,'task13 highlighted targets')
 page.locator('#edemo-answer-input').fill('неподвижные')
 page.locator('#edemo-nav .edemo-nav-btn').nth(13).click();ck(page.locator('#edemo-answer-input').count()==1,'task14 input');ck(page.locator('.edemo-task-prompt strong').count()>=2,'task14 highlighted targets');page.locator('#edemo-answer-input').fill('навстречу вдали')
 page.locator('#edemo-nav .edemo-nav-btn').nth(22).click();txt=page.locator('.edemo-task-prompt').inner_text().lower();ck('повествование с элементами описания' in txt,'task23 exact item4')
 page.locator('#edemo-nav .edemo-nav-btn').nth(24).click();vals=page.locator('[data-choice]').evaluate_all("e=>e.map(x=>x.getAttribute('data-choice'))");ck(vals==[str(x) for x in range(15,23)],f'task25 options {vals}')
 page.locator('#edemo-nav .edemo-nav-btn').nth(25).click();ck(page.locator('[data-match-index]').count()==4,'task26 4 selects')
 for i,v in enumerate(['5','1','4','9']):page.locator(f'[data-match-index="{i}"]').select_option(v,force=True)
 page.locator('#edemo-nav .edemo-nav-btn').nth(26).click();ck(page.locator('textarea#edemo-answer-input').count()==1,'task27 textarea')
 # Finish without needing complete answers; then test essay gates
 page.once('dialog',lambda d:d.accept());page.click('#edemo-finish-top');ck(page.locator('#edemo-total-score').inner_text()=='—','official total separated')
 page.check('#edemo-eligibility-confirm');page.check('#edemo-short-band')
 caps={'K7':2,'K8':2,'K9':1,'K10':1,'K11':0,'K12':0}
 for k,cap in caps.items():
  vals=[x for x in page.locator(f'#edemo-{k} option').evaluate_all("e=>e.map(x=>x.value)") if x!=''];ck(max(map(int,vals))==cap if vals else cap==0,f'{k} short cap')
 # K6 max 1 until K10=2 (and short band caps K10 to1)
 vals=[x for x in page.locator('#edemo-K6 option').evaluate_all("e=>e.map(x=>x.value)") if x!=''];ck(max(map(int,vals))==1,'K6 cap when K10 not max')
 page.check('[data-zero-reason="under70"]');ck(page.locator('#edemo-K1').is_disabled(),'under70 blocks');ck(page.locator('#edemo-essay-score').inner_text()=='0','under70 zero')
 for w,h in [(320,700),(360,800),(390,844),(768,1024),(1280,900)]:
  page.set_viewport_size({'width':w,'height':h});overflow=page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth + 1');ck(not overflow,f'overflow {w}')
 ck(not errors,'browser errors: '+','.join(errors));b.close()
if fail:
 print('FAIL browser',len(fail));print('\n'.join(fail));sys.exit(1)
print('PASS browser: 27 nav, visual highlights, task8/task26 selects, task13/14 inputs, essay gates, responsive')
