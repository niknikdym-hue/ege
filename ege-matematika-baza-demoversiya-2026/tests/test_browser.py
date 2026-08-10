#!/usr/bin/env python3
import json
import os
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(os.environ.get('DEMO_ROOT') or Path(__file__).resolve().parents[1])
PREFIX='ege-matematika-baza-demoversiya-2026'
PREVIEW=(ROOT/f'{PREFIX}-PREVIEW.html').read_text(encoding='utf-8')
KEY='eksamio_ege_math_base_demo_2026_v1_0'
EVIDENCE=Path(os.environ['EVIDENCE_DIR']) if os.environ.get('EVIDENCE_DIR') else None
if EVIDENCE:EVIDENCE.mkdir(parents=True,exist_ok=True)

def document(saved=None):
    initial=json.dumps(saved,ensure_ascii=False)
    poly=f"""<script>(function(){{const d={{}};Object.defineProperty(window,'localStorage',{{value:{{getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>d[k]=String(v),removeItem:k=>delete d[k],clear:()=>{{for(const k of Object.keys(d))delete d[k]}},key:i=>Object.keys(d)[i]||null,get length(){{return Object.keys(d).length}}}}}});const saved={initial};if(saved!==null)localStorage.setItem('{KEY}',saved);}})();</script>"""
    return PREVIEW.replace('<head>','<head>'+poly,1)

def js_variant(page,n):
    return page.evaluate(f'window.EKSAMIO_MATH_BASE_TEST.variantFor({n})')

def fill_correct(page,n):
    v=js_variant(page,n);code=str(v['canonical_forms'][0]);control=v['control']
    if control=='numeric_input':
        page.locator('#mb-short').fill(code)
    elif control=='matching_selects_4':
        sels=page.locator('.mb-select[data-pos]');assert sels.count()==4,(n,v['variant'])
        assert len(code)==4,(n,v['variant'],code)
        for i,ch in enumerate(code):sels.nth(i).select_option(ch)
    elif control=='checkboxes':
        for ch in code:page.locator(f'input[data-choice="{ch}"]').check()
    elif control=='row_checkboxes':
        for ch in code:page.locator(f'input[data-row="{ch}"]').check()
    else:raise AssertionError((n,v['variant'],control))
    assert page.evaluate(f'window.EKSAMIO_MATH_BASE_TEST.isAnswered({n})'),(n,v['variant'],'not answered')
    assert page.evaluate(f'window.EKSAMIO_MATH_BASE_TEST.score({n})')==1,(n,v['variant'],code)
    return v

def set_variant(page,n,k):
    page.evaluate(f'window.EKSAMIO_MATH_BASE_TEST.setVariant({n},{k})')
    assert page.locator('#mb-task').is_visible()

errors=[]
with sync_playwright() as pw:
    exe=os.environ.get('CHROME_PATH') or shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome') or shutil.which('google-chrome-stable')
    browser=pw.chromium.launch(headless=True,executable_path=exe if exe else None,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1280,'height':950})
    page.on('dialog',lambda d:d.accept())
    page.on('pageerror',lambda e:errors.append('pageerror: '+str(e)))
    page.on('console',lambda m:errors.append('console: '+m.text) if m.type=='error' else None)
    page.set_content(document(),wait_until='load')
    page.get_by_role('button',name='Начать экзамен').click()
    assert page.locator('#mb-timer').inner_text().startswith('02:59') or page.locator('#mb-timer').inner_text()=='03:00:00'
    assert page.locator('.mb-num').count()==21
    assert 'Официально принимаемый ответ' not in page.locator('body').inner_text()

    # Numeric hygiene: invalid content must neither turn green nor score.
    set_variant(page,1,1)
    inp=page.locator('#mb-short')
    for bad in ['abc','1 2','+6','6 руб']:
        inp.fill(bad)
        assert not page.evaluate('window.EKSAMIO_MATH_BASE_TEST.isAnswered(1)')
        assert page.evaluate('window.EKSAMIO_MATH_BASE_TEST.score(1)')==0
        assert 'is-invalid' in (inp.get_attribute('class') or '')
    inp.fill('6')
    assert page.evaluate('window.EKSAMIO_MATH_BASE_TEST.score(1)')==1

    # Decimal point is UX-canonicalized to comma before storage/scoring.
    decimal=None
    for n in range(1,22):
        t=page.evaluate(f'window.EKSAMIO_MATH_BASE_TEST.tasks.find(x=>x.number==={n})')
        for v in t['variants']:
            if v['control']=='numeric_input' and any(',' in str(x) for x in v['canonical_forms']):
                decimal=(n,v['variant'],str(v['canonical_forms'][0]));break
        if decimal:break
    assert decimal,'no decimal answer found'
    n,k,code=decimal;set_variant(page,n,k);page.locator('#mb-short').fill(code.replace(',','.'))
    assert page.locator('#mb-short').input_value()==code
    assert page.evaluate(f'window.EKSAMIO_MATH_BASE_TEST.score({n})')==1

    # Matching uses four real controls, partial state is persisted but not completed.
    set_variant(page,2,1);v=js_variant(page,2);code=str(v['canonical_forms'][0]);sels=page.locator('.mb-select[data-pos]')
    sels.nth(0).select_option(code[0])
    assert not page.evaluate('window.EKSAMIO_MATH_BASE_TEST.isAnswered(2)')
    assert sels.nth(1).locator(f'option[value="{code[0]}"]').is_disabled()
    saved=page.evaluate(f"localStorage.getItem('{KEY}')")
    page.set_content(document(saved),wait_until='load')
    assert page.locator('.mb-select[data-pos]').nth(0).input_value()==code[0]
    assert page.evaluate('window.EKSAMIO_MATH_BASE_TEST.variantFor(2).variant')==1
    for i,ch in enumerate(code[1:],start=1):page.locator('.mb-select[data-pos]').nth(i).select_option(ch)
    assert page.evaluate('window.EKSAMIO_MATH_BASE_TEST.score(2)')==1

    # Return marker survives reload independently of answer state.
    page.locator('#mb-mark').click();assert 'is-marked' in (page.get_by_role('button',name='Задание 2',exact=True).get_attribute('class') or '')
    saved=page.evaluate(f"localStorage.getItem('{KEY}')");page.set_content(document(saved),wait_until='load')
    assert 'is-marked' in (page.get_by_role('button',name='Задание 2',exact=True).get_attribute('class') or '')

    # Every one of the 70 official examples is completed through its real UI control.
    audited=[]
    for n in range(1,22):
        count=page.evaluate(f'window.EKSAMIO_MATH_BASE_TEST.tasks.find(x=>x.number==={n}).variants.length')
        for k in range(1,count+1):
            set_variant(page,n,k);v=fill_correct(page,n);audited.append(f'{n}.{k}')
            if v.get('asset_id'):
                img=page.locator('#mb-task .mb-figure img');assert img.count()==1
                assert img.evaluate('x=>x.complete&&x.naturalWidth>0'),(n,k,'image')
            if v.get('formula_mathml') or v.get('left_html') or v.get('right_html'):
                assert page.locator('#mb-task math').count()>0,(n,k,'mathml')
    assert len(audited)==70

    # Full first-variant attempt: 21/21 by real controls, answer reveal only after finish.
    page.set_content(document(),wait_until='load');page.get_by_role('button',name='Начать экзамен').click()
    for n in range(1,22):
        set_variant(page,n,1);fill_correct(page,n)
    assert page.evaluate('window.EKSAMIO_MATH_BASE_TEST.total()')==21
    assert page.evaluate('window.EKSAMIO_MATH_BASE_TEST.answeredCount()')==21
    assert 'Официально принимаемый ответ' not in page.locator('body').inner_text()
    page.locator('#mb-finish').click();page.wait_for_timeout(150)
    assert page.locator('#mb-score').inner_text()=='21/21'
    assert page.locator('#mb-answered').inner_text()=='21/21'
    assert page.locator('.mb-review-item').count()==21
    # Details are intentionally collapsed; text_content() verifies the answer disclosure exists in the DOM after finish.
    assert 'Официально принимаемый ответ' in (page.locator('#mb-review').text_content() or '')
    if EVIDENCE:page.screenshot(path=EVIDENCE/'results-1280.png',full_page=True)

    # Official reference material is actually available as four rendered FIPI pages.
    page.locator('#mb-ref-results').click();refs=page.locator('#mb-ref-pages img');assert refs.count()==4
    for i in range(4):assert refs.nth(i).evaluate('x=>x.complete&&x.naturalWidth>0')
    page.locator('#mb-ref-close').click()

    # Responsive regression: no page horizontal scroll; controls/images remain usable.
    responsive={}
    for width in [768,390,360,320]:
        page.set_viewport_size({'width':width,'height':900})
        page.set_content(document(),wait_until='load');page.get_by_role('button',name='Начать экзамен').click()
        max_over=0
        for n in range(1,22):
            page.get_by_role('button',name=f'Задание {n}',exact=True).click()
            overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            max_over=max(max_over,overflow);assert overflow<=0,(width,n,overflow)
            if page.locator('#mb-task .mb-figure img').count():assert page.locator('#mb-task .mb-figure img').evaluate('x=>x.complete&&x.naturalWidth>0')
        responsive[str(width)]={'max_overflow_px':max_over}
        if EVIDENCE and width==320:page.screenshot(path=EVIDENCE/'exam-320.png',full_page=True)

    assert not errors,errors
    if EVIDENCE:
        (EVIDENCE/'browser-evidence.json').write_text(json.dumps({'status':'PASS','official_examples_real_control_audited':len(audited),'examples':audited,'full_attempt':'21/21','widths':[1280,768,390,360,320],'responsive':responsive,'reference_pages':4,'javascript_errors':len(errors)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    browser.close()
print('BROWSER PASS: 70/70 real-control examples; full attempt 21/21')
