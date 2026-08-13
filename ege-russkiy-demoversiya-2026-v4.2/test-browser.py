from playwright.sync_api import sync_playwright
import json, sys, os
HTML_PATH=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'ege-russkiy-demoversiya-PREVIEW.html')
fail=[]
def check(cond,msg):
    if not cond: fail.append(msg)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox','--allow-file-access-from-files'])
    context=browser.new_context(viewport={'width':1280,'height':900})
    page=context.new_page()
    page.set_default_timeout(3000)
    errors=[]
    page.on('console', lambda m: errors.append(f'console {m.type}: {m.text}') if m.type=='error' else None)
    page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
    html=open(HTML_PATH,encoding='utf-8').read()
    page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return Object.prototype.hasOwnProperty.call(this._d,k)?this._d[k]:null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}}})")
    page.set_content(html,wait_until='domcontentloaded',timeout=15000)
    print('loaded',flush=True)
    check(page.locator('#edemo-start').is_visible(),'start visible')
    page.click('#edemo-start')
    print('started',flush=True)
    check(page.locator('#edemo-nav .edemo-nav-btn').count()==27,'27 nav buttons')
    # Task 2 typed checkboxes and persistence
    page.locator('#edemo-nav .edemo-nav-btn').nth(1).click()
    check(page.locator('[data-choice]').count()==5,'task2 has 5 checkboxes')
    check(page.locator('.edemo-source p strong').count()==5,'task2 source has five explicit highlighted words')
    highlighted=[x.strip().lower() for x in page.locator('.edemo-source p strong').all_inner_texts()]
    check(highlighted==['пришёл','духовной','характер','прозрение','кровь'],f'task2 highlighted words {highlighted}')
    page.locator('[data-choice="4"]').check(force=True); page.locator('[data-choice="5"]').check(force=True)
    saved=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_1'))")
    variants_before=saved.get('variantChoices')
    check(saved['answers']['2']==['4','5'],'task2 stored as selected tokens')
    # Task 6 OR badge; reload persistence
    page.locator('#edemo-nav .edemo-nav-btn').nth(5).click()
    badge_before=page.locator('.edemo-variant-badge').inner_text()
    prompt_before=page.locator('.edemo-task-prompt').inner_text()
    page.set_content(html,wait_until='domcontentloaded',timeout=15000)
    check(page.locator('#edemo-resume').is_visible() or page.locator('#edemo-task-stage').is_visible(),'resume after reload')
    # Running state resumes automatically in current implementation
    if page.locator('#edemo-resume').is_visible(): page.click('#edemo-resume')
    check(page.locator('.edemo-variant-badge').inner_text()==badge_before,'OR badge persists')
    check(page.locator('.edemo-task-prompt').inner_text()==prompt_before,'OR prompt persists')
    variants_after=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_1')).variantChoices")
    check(variants_before==variants_after,'all OR choices persist')
    print('reloaded',flush=True)
    # Matching task
    print('go8',flush=True)
    page.locator('#edemo-nav .edemo-nav-btn').nth(7).click()
    print('at8',flush=True)
    check(page.locator('[data-match-index]').count()==5,'task8 has 5 per-position selects')
    for i,val in enumerate(['4','3','8','2','7']): page.locator(f'[data-match-index="{i}"]').select_option(val,force=True)
    print('match filled',flush=True)
    # punctuation positions task 18 should expose 7 positions
    page.locator('#edemo-nav .edemo-nav-btn').nth(17).click()
    check(page.locator('[data-choice]').count()==7,'task18 has position checkboxes 1-7')
    # sentence task 26 should expose sentence numbers 17-25, not digits 1-5
    page.locator('#edemo-nav .edemo-nav-btn').nth(25).click()
    labels=page.locator('[data-choice]').evaluate_all("els=>els.map(e=>e.getAttribute('data-choice'))")
    check(labels==[str(x) for x in range(17,26)],f'task26 options {labels}')
    page.locator('[data-choice="21"]').check(force=True)
    # Essay field
    page.locator('#edemo-nav .edemo-nav-btn').nth(26).click()
    check(page.locator('textarea#edemo-answer-input').count()==1,'essay textarea')
    page.fill('textarea#edemo-answer-input','Тестовый текст сочинения')
    print('inputs tested',flush=True)
    # finish and separated result
    page.once('dialog', lambda d:d.accept())
    page.click('#edemo-finish-top')
    # Above exact score can vary due task6 blank; expected 4. Correct below via direct condition.
    short=int(page.locator('#edemo-short-score').inner_text())
    check(short==4,f'short score expected 4 got {short}')
    check(page.locator('#edemo-total-score').inner_text()=='—','official total unavailable')
    check('не формирует официальный' in page.locator('#edemo-total-status').inner_text().lower(),'official total separation text')
    print('finished',flush=True)
    # essay gate and K1 dependency
    page.check('#edemo-eligibility-confirm')
    page.select_option('#edemo-K1','0')
    check(page.locator('#edemo-K2').is_disabled(),'K2 disabled when K1=0')
    check(page.locator('#edemo-K3').is_disabled(),'K3 disabled when K1=0')
    state=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_1'))")
    check(state['essayScores'].get('K2')==0 and state['essayScores'].get('K3')==0,'K1 dependency persisted in scorer state')
    print('criteria tested',flush=True)
    # Mobile / responsive widths
    for width,height in [(320,700),(360,800),(390,844),(768,1024),(1280,900)]:
        page.set_viewport_size({'width':width,'height':height})
        overflow=page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth + 1")
        check(not overflow,f'no horizontal overflow at {width}')
    check(not errors,'; '.join(errors))
    browser.close()
if fail:
    print('FAIL browser:',len(fail))
    print('\n'.join(fail))
    sys.exit(1)
print('PASS browser: typed fields, OR persistence, reload, result separation, essay dependency, responsive widths')
