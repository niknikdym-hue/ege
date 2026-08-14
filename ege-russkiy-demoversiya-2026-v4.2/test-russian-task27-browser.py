from playwright.sync_api import sync_playwright
import pathlib, json, os, sys

base=pathlib.Path(__file__).resolve().parent
preview=(base/'ege-russkiy-demoversiya-PREVIEW.html').read_text(encoding='utf-8')
for n in range(1,6):
    block=(base/f'ege-russkiy-demoversiya-T123-{n:02d}.txt').read_text(encoding='utf-8')
    if block not in preview:
        raise SystemExit(f'FAIL real preview does not contain exact T123-{n:02d}')
hotfix=(base/'ege-russkiy-demoversiya-T123-06.txt').read_text(encoding='utf-8')
addon=(base/'ege-russkiy-demoversiya-T123-07.txt').read_text(encoding='utf-8')
html=preview.replace('</body>',hotfix+addon+'</body>')

browser_candidates=[
    os.environ.get('BROWSER_EXECUTABLE'),
    '/usr/bin/chromium',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
]
browser_executable=next((p for p in browser_candidates if p and pathlib.Path(p).exists()),None)
if not browser_executable:
    raise SystemExit('FAIL no Chromium-compatible browser executable')

fails=[]
def check(cond,msg):
    if not cond:fails.append(msg)
def reset_storage(page):
    page.evaluate("localStorage.removeItem('eksamio_ege_russian_demo_2026_v4_1');localStorage.removeItem('eksamio_ege_russian_demo_2026_v4_2_task27_review')")
def load_real(page):
    page.set_content(html,wait_until='domcontentloaded',timeout=15000)
def go_task27(page):
    page.click('#edemo-start')
    page.locator('#edemo-nav .edemo-nav-btn').nth(26).click()
def finish(page):
    page.once('dialog',lambda d:d.accept())
    page.click('#edemo-finish-top')
def max_k1_k6(page):
    for k,v in [('K1','1'),('K2','3'),('K3','2'),('K4','1'),('K5','2'),('K6','1')]:
        page.select_option(f'[data-review-score="{k}"]',v)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=browser_executable,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1280,'height':900})
    errors=[]
    page.on('console',lambda m:errors.append(f'console {m.type}: {m.text}') if m.type=='error' else None)
    page.on('pageerror',lambda e:errors.append(f'pageerror: {e}'))
    from urllib.parse import urlparse,parse_qs
    def speller_route(route):
        q=parse_qs(urlparse(route.request.url).query);cb=q.get('callback',[''])[0]
        body=f'{cb}([{json.dumps({"code":1,"pos":0,"row":0,"col":0,"len":6,"word":"карова","s":["корова"]},ensure_ascii=False)}]);'
        route.fulfill(status=200,content_type='application/javascript; charset=utf-8',body=body)
    page.route('https://speller.yandex.net/**',speller_route)
    page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return Object.prototype.hasOwnProperty.call(this._d,k)?this._d[k]:null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}}})")

    # Demo mode on the real PREVIEW composed from exact T123-01...T123-05 plus T123-06.
    load_real(page);go_task27(page)
    page.check('input[name="edemo-writing-mode"][value="demo"]')
    essay=page.locator('#edemo-answer-input')
    for attr,want in [('spellcheck','false'),('autocomplete','off'),('autocorrect','off'),('autocapitalize','off'),('data-gramm','false'),('data-enable-grammarly','false'),('writingSuggestions','false')]:
        check(essay.get_attribute(attr)==want,f'demo textarea {attr}={want}')
    original='Карова. Это это исходное сочинение без точки'
    essay.fill(original)
    finish(page)
    check(page.locator('h3',has_text='Ваше сочинение').count()==1,'demo result has Ваше сочинение')
    check(page.locator('#edemo-frozen-essay').inner_text()==original,'demo essay frozen verbatim')
    check(page.locator('#edemo-transferred-essay').count()==0,'demo result has no editable transferred text')
    check(page.locator('#edemo-diagnostic24').count()==0,'0-24 diagnostic removed')
    saved=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))")
    check(saved['analysisStatus']=='complete','preliminary analysis runs after finish')
    check(len(saved['confirmedFindings']['K10'])==0,'adjacent duplicate is not confirmed K10')
    check(len(saved['possibleFindings']['K10'])==1,'adjacent duplicate is possible K10')
    check(len(saved['possibleFindings']['K8'])==1,'system creates possible finding')
    check('K10' not in saved['essayScores'],'absence of confirmed score does not auto-award 3')
    check(page.locator('[data-confirmed-errors]').count()==0,'no manual confirmed-error counters')
    page.check('#edemo-review-eligibility');max_k1_k6(page)
    check(page.get_by_text('Проверка ошибок',exact=False).count()>=1,'student-friendly analysis label shown')
    check(page.locator('details.edemo-criterion-help').count()==10,'all K1-K10 have optional scoring help')
    check(page.get_by_text('может заметить не все ошибки',exact=False).count()>=1,'automatic-check limitation shown')
    check(page.locator('#edemo-run-text-check').count()==1,'explicit text-check button shown')
    page.click('#edemo-run-text-check')
    page.wait_for_function("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_spelling_check')||'{}').status==='complete'")
    check(page.get_by_text('Проверка завершена',exact=False).count()>=1,'spelling-check completion is visible')
    checked=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))")
    check(any('карова' in x['message'].lower() for x in checked['possibleFindings']['K7']),'external spelling candidate merged into K7')
    check(page.locator('.edemo-error-row').nth(0).locator('.edemo-finding-box--check-active').count()==1,'K7 Стоит проверить block highlighted when finding exists')
    for k in ['K7','K8','K9','K10']:page.select_option(f'[data-review-score="{k}"]','3')
    check(page.locator('#edemo-essay-score').inner_text()=='22','possible K10 does not create hard cap')
    check(page.locator('#edemo-total-score').inner_text()=='22','whole demo result includes essay self-assessment')
    check('Задания 1–26: 0 + сочинение: 22' in page.locator('#edemo-total-status').inner_text(),'whole-result breakdown is clear')
    # A separately validated confirmed finding applies the official hard cap.
    page.evaluate("window.__edemoRussian2026Task27Review.submitAnalysis({version:'browser-validated-test',confirmed:{K10:[{id:'validated-k10',message:'Подтверждённая речевая ошибка'}]},possible:{}})")
    page.wait_for_timeout(50)
    check(page.locator('.edemo-error-row').nth(3).locator('.edemo-finding-box--error-active').count()==1,'K10 Найдены ошибки block highlighted when confirmed finding exists')
    page.select_option('[data-review-score="K10"]','2')
    check(page.locator('#edemo-essay-score').inner_text()=='21','confirmed K10 hard cap limits max to 21')
    page.eval_on_selector('[data-review-score="K10"]',"el=>{el.value='3';el.dispatchEvent(new Event('change',{bubbles:true}))}")
    check(page.locator('[data-review-score="K10"]').input_value()=='2','programmatic score above cap rejected in UI')
    # Core answer changes after finish must not mutate the frozen essay.
    page.evaluate("let s=JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_1'));s.answers[27]='ИЗМЕНЕНО ПОСЛЕ ФИНИША';localStorage.setItem('eksamio_ege_russian_demo_2026_v4_1',JSON.stringify(s))")
    load_real(page)
    check(page.locator('#edemo-frozen-essay').inner_text()==original,'frozen demo essay survives reload and core mutation')

    # Paper mode alone gets editable transferred text; analysis updates automatically.
    reset_storage(page);load_real(page);go_task27(page)
    page.check('#edemo-paper-complete');finish(page)
    check(page.locator('#edemo-frozen-essay').count()==0,'paper result has no frozen demo block')
    check(page.locator('#edemo-transferred-essay').count()==1,'paper result has editable transferred text')
    scan_svg=b'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="1200"><rect width="800" height="1200" fill="white"/><path d="M80 140h640M80 220h640M80 300h640" stroke="black" stroke-width="8"/></svg>'
    check(page.locator('#edemo-essay-scan').get_attribute('multiple') is not None,'scan input supports multiple files')
    check(page.locator('.edemo-file-pick').is_visible(),'highlighted add-files button visible')
    page.set_input_files('#edemo-essay-scan',files=[{'name':'essay-page-1.svg','mimeType':'image/svg+xml','buffer':scan_svg},{'name':'essay-page-2.svg','mimeType':'image/svg+xml','buffer':scan_svg}])
    page.wait_for_function("document.querySelectorAll('.edemo-scan-open').length===2")
    check(page.locator('.edemo-scan-open').count()==2,'two essay pages previewed')
    page.click('.edemo-scan-open')
    check(page.locator('#edemo-scan-lightbox').count()==1,'scan lightbox opens')
    page.click('[data-scan-zoom="in"]')
    check(page.locator('#edemo-scan-lightbox').get_attribute('data-zoom')=='1.25','scan zoom in works')
    page.keyboard.press('Escape')
    check(page.locator('#edemo-scan-lightbox').count()==0,'scan lightbox closes with Escape')
    page.fill('#edemo-transferred-essay','Это пример , текста.')
    paper_saved=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))")
    check(paper_saved['analysisStatus']=='complete','paper transfer triggers preliminary analysis')
    check(len(paper_saved['confirmedFindings']['K8'])==0,'space before punctuation is not confirmed K8')
    check(len(paper_saved['possibleFindings']['K8'])==0,'space before punctuation is not possible K8')
    check(len(paper_saved['technicalFindings'])==1,'space before punctuation is technical note only')
    page.check('#edemo-review-eligibility');max_k1_k6(page)
    check(page.locator('#edemo-technical-findings').count()==1,'technical note shown separately')
    check(page.get_by_text('не влияют на балл',exact=False).count()>=1,'technical note has no scoring effect')
    for k in ['K7','K8','K9','K10']:page.select_option(f'[data-review-score="{k}"]','3')
    check(page.locator('#edemo-essay-score').inner_text()=='22','technical findings do not change 22-point maximum')
    check(page.locator('#edemo-diagnostic24').count()==0,'no 0-24 scale in paper mode')
    check(not errors,'; '.join(errors))
    browser.close()

if fails:
    print('FAIL real-preview task27 browser regression:',len(fails));print('\n'.join(fails));sys.exit(1)
print('PASS real-preview task27 browser: T123-01...07, language aids off, frozen demo essay, preliminary findings, technical notes, verified hard caps')
