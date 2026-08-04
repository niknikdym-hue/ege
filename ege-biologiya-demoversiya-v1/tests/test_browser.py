from __future__ import annotations
import json,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];P='ege-biologiya-demoversiya'
CHROME=next((x for x in ['/usr/bin/chromium','/usr/bin/google-chrome','/usr/bin/google-chrome-stable'] if Path(x).exists()),None)
assert CHROME,'Chrome/Chromium executable not found'
HTML=(ROOT/f'{P}-PREVIEW.html').read_text(encoding='utf-8')
KEY='eksamio_ege_biologiya_demo_2026_v1_0_2'
errors=[]

def mock_script(seed=None):
    seed=json.dumps(seed or {},ensure_ascii=False)
    return f"""(() => {{ const d={seed}; Object.defineProperty(window,'localStorage',{{configurable:true,value:{{getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>{{d[k]=String(v)}},removeItem:k=>{{delete d[k]}},clear:()=>{{for(const k in d)delete d[k]}},key:i=>Object.keys(d)[i]||null,get length(){{return Object.keys(d).length}}}}}}); window.__store=d; }})();"""

def page_new(browser,width=1440,store=None):
    page=browser.new_page(viewport={'width':width,'height':1000})
    page.evaluate(mock_script(store))
    page.on('console',lambda m: errors.append(f'console {m.type}: {m.text}') if m.type=='error' else None)
    page.on('pageerror',lambda e: errors.append(f'pageerror: {e}'))
    page.set_content(HTML,wait_until='load')
    assert page.evaluate('!!window.BiologyDemoTestApi')
    return page

def start(page,variants=None):
    page.evaluate('(v)=>window.BiologyDemoTestApi.startWithVariants(v)',variants or {'4':1,'56':1,'24':1,'27':1})
    page.wait_for_selector('#bio-app.is-active')

def go(page,n):
    page.evaluate('(n)=>window.BiologyDemoTestApi.goTo(n)',n)
    page.wait_for_function('(n)=>document.querySelector(".bio-question-number")?.textContent.trim()===`Задание ${n}`',arg=n)

def answer(page): return page.evaluate('window.BiologyDemoTestApi.getState().answers')
def cls(page,n,c): return page.locator('#bio-nav .bio-nav-btn').filter(has_text=re.compile(rf'^{n}$')).evaluate('(e,c)=>e.classList.contains(c)',c)

def select_code(page,code):
    sels=page.locator('[data-structured-select]')
    assert sels.count()==len(code)
    for i,ch in enumerate(code): sels.nth(i).select_option(ch)

def click_multi(page,code):
    for ch in code: page.locator(f'[data-multi-value="{ch}"]').check()

def click_sequence(page,code):
    for ch in code: page.locator(f'[data-sequence-value="{ch}"]').click()

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=CHROME)
    page=page_new(browser);start(page)
    assert page.locator('#bio-nav .bio-nav-btn').count()==28
    before=page.locator('#bio-timer').inner_text();page.wait_for_timeout(1100);after=page.locator('#bio-timer').inner_text();assert before!=after

    # Table: incomplete state must not be treated or scored as complete.
    go(page,2);assert page.locator('[data-structured-select]').count()==2
    page.locator('[data-structured-select]').nth(0).select_option('3')
    assert answer(page)['2']=='3_';assert not page.evaluate('window.BiologyDemoTestApi.isAnswered(2)');assert page.evaluate('window.BiologyDemoTestApi.scoreState(2,"3_")')==0;assert not cls(page,2,'is-answered')
    page.locator('[data-structured-select]').nth(1).select_option('1')
    assert answer(page)['2']=='31';assert page.evaluate('window.BiologyDemoTestApi.isAnswered(2)');assert page.evaluate('window.BiologyDemoTestApi.scoreState(2,"31")')==2
    page.locator('[data-structured-select]').nth(0).select_option('2');assert page.evaluate('window.BiologyDemoTestApi.scoreState(2,"21")')==1
    page.click('#bio-clear');assert '2' not in answer(page)

    # Matching every affected task, including linked variant 6.
    for n in [6,10,14,19]:
        go(page,n);t=page.evaluate('(n)=>window.BiologyDemoTestApi.getSelectedTask(n)',n);code=t['answer']['canonical'];assert page.locator('[data-structured-select]').count()==len(code);select_code(page,code);assert answer(page)[str(n)]==code;assert page.evaluate('(n)=>window.BiologyDemoTestApi.scoreState(n,window.BiologyDemoTestApi.getState().answers[n])',n)==2
    page.close()
    page=page_new(browser);start(page,{'4':2,'56':2,'24':2,'27':4});go(page,6);t=page.evaluate('window.BiologyDemoTestApi.getSelectedTask(6)');assert t['variant_id']=='2';select_code(page,t['answer']['canonical']);assert page.evaluate('window.BiologyDemoTestApi.scoreState(6,window.BiologyDemoTestApi.getState().answers[6])')==2

    # Table 20 does not permit reusing one list element.
    go(page,20);assert page.locator('[data-structured-select]').count()==3
    page.locator('[data-structured-select]').nth(0).select_option('7')
    assert page.locator('[data-structured-select]').nth(1).locator('option[value="7"]').is_disabled()
    page.click('#bio-clear')

    # Sequence builder: incomplete sequence is preserved but not scored as ready.
    for n in [8,12,16]:
        go(page,n);t=page.evaluate('(n)=>window.BiologyDemoTestApi.getSelectedTask(n)',n);code=t['answer']['canonical'];assert page.locator('[data-sequence-value]').count()==len(code);click_sequence(page,code[:2]);assert not page.evaluate('(n)=>window.BiologyDemoTestApi.isAnswered(n)',n);assert page.evaluate('(n)=>window.BiologyDemoTestApi.scoreState(n,window.BiologyDemoTestApi.getState().answers[n])',n)==0;click_sequence(page,code[2:]);assert answer(page)[str(n)]==code;assert page.evaluate('(n)=>window.BiologyDemoTestApi.scoreState(n,window.BiologyDemoTestApi.getState().answers[n])',n)==2;page.click('#bio-sequence-undo');assert not page.evaluate('(n)=>window.BiologyDemoTestApi.isAnswered(n)',n);page.click('#bio-sequence-reset')

    # Multiple choice; only prompts that explicitly say three reveal/enforce three.
    for n in [7,11,15,17,18]:
        go(page,n);t=page.evaluate('(n)=>window.BiologyDemoTestApi.getSelectedTask(n)',n);code=t['answer']['canonical'];click_multi(page,code);assert answer(page)[str(n)]==''.join(sorted(code));assert page.evaluate('(n)=>window.BiologyDemoTestApi.scoreState(n,window.BiologyDemoTestApi.getState().answers[n])',n)==2;unchecked=page.locator('[data-multi-value]:not(:checked)');assert unchecked.count()>0 and unchecked.first.is_disabled();page.locator(f'[data-multi-value="{code[-1]}"]').uncheck();assert page.evaluate('(n)=>window.BiologyDemoTestApi.scoreState(n,window.BiologyDemoTestApi.getState().answers[n])',n)==1;assert page.evaluate('(n)=>window.BiologyDemoTestApi.isAnswered(n)',n);page.click('#bio-clear')
    go(page,21);text=page.locator('.bio-structured-answer').inner_text();assert 'из 2' not in text and 'выберите 2' not in text.lower();assert page.locator('[data-multi-value]').count()==5
    for ch in '1245': page.locator(f'[data-multi-value="{ch}"]').check()
    assert page.locator('[data-multi-value="3"]').is_enabled();page.click('#bio-clear');click_multi(page,'13');assert page.evaluate('window.BiologyDemoTestApi.scoreState(21,"13")')==2

    # Simple tasks retain a strict single input.
    for n in [1,3,4,5,9,13]: go(page,n);assert page.locator('#bio-answer').count()==1;assert page.locator('[data-structured-select],[data-sequence-value],[data-multi-value]').count()==0

    # Persistence of both complete and incomplete structured states.
    go(page,2);page.locator('[data-structured-select]').nth(0).select_option('3')
    go(page,8);click_sequence(page,'54')
    go(page,21);click_multi(page,'13');page.click('#bio-flag')
    go(page,22);page.fill('#bio-ext','Проверочный развёрнутый ответ.')
    stored=page.evaluate('window.__store');page.close()
    page=page_new(browser,store=stored);assert page.locator('#bio-continue-btn').is_visible();page.click('#bio-continue-btn');assert page.evaluate('window.BiologyDemoTestApi.getState().current')==22
    assert page.evaluate('window.BiologyDemoTestApi.getState().answers[2]')=='3_';assert not page.evaluate('window.BiologyDemoTestApi.isAnswered(2)');assert page.evaluate('window.BiologyDemoTestApi.getState().answers[8]')=='54';assert not page.evaluate('window.BiologyDemoTestApi.isAnswered(8)');assert page.evaluate('window.BiologyDemoTestApi.getState().answers[21]')=='13';assert page.evaluate('window.BiologyDemoTestApi.isAnswered(21)');assert 21 in page.evaluate('window.BiologyDemoTestApi.getState().flags');assert page.evaluate('window.BiologyDemoTestApi.getState().extendedText[22]')=='Проверочный развёрнутый ответ.'

    # Full official short pass and result contract.
    for n in range(1,22):
        t=page.evaluate('(n)=>window.BiologyDemoTestApi.getSelectedTask(n)',n);page.evaluate('(x)=>window.BiologyDemoTestApi.setAnswer(x.n,x.v)',{'n':n,'v':t['answer']['canonical']})
    assert page.evaluate('window.BiologyDemoTestApi.shortTotal()')==36
    page.evaluate('window.BiologyDemoTestApi.finishNow()');page.wait_for_selector('#bio-results.is-active')
    result=page.locator('#bio-results').inner_text();assert re.search(r'36\s*/\s*36',result);assert re.search(r'—\s*/\s*57',result);assert 'не прибавляется к результату первой части' in result;assert page.locator('.bio-review-card').count()==28
    assert page.locator('[data-self-task="23"]').first.is_disabled();assert page.locator('[data-self-task="22"]').first.is_enabled()
    page.close()

    # Every task and every official variant render at five widths without overflow or broken images.
    for width in [1440,768,390,360,320]:
        page=page_new(browser,width);start(page,{'4':1,'56':1,'24':1,'27':1})
        for n in range(1,29):
            go(page,n)
            assert page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')<=3,(width,n)
            for i in range(page.locator('#bio-question img').count()):
                assert page.locator('#bio-question img').nth(i).evaluate('img=>img.complete&&img.naturalWidth>20&&img.naturalHeight>20'),(width,n,i)
        page.close()
    for forced in [{'4':2,'56':2,'24':2,'27':2},{'4':1,'56':1,'24':1,'27':3},{'4':1,'56':1,'24':1,'27':4}]:
        page=page_new(browser,1280);start(page,forced)
        for n in [4,5,6,24,27]: go(page,n);assert page.locator('.bio-question-number').inner_text()==f'Задание {n}'
        page.close()
    browser.close()
assert not errors,errors
print('BROWSER PASS')
