#!/usr/bin/env python3
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

URL=os.environ.get('EKSAMIO_PREVIEW_URL','http://127.0.0.1:8765/ege-matematika-baza-demoversiya-2026-PREVIEW.html')
OUT=Path(os.environ.get('EKSAMIO_EVIDENCE_OUT','tests/evidence/v1.1-browser-regression-evidence.json'))


def task_meta(page,n):
    return page.evaluate("""n=>{const v=window.EKSAMIO_MATH_BASE_TEST.variantFor(n);return {variant:v.variant,control:v.control,forms:v.canonical_forms,order_ignored:!!v.order_ignored}}""",n)

def fill_current_correct(page,n):
    meta=task_meta(page,n)
    code=str(meta['forms'][0])
    ctl=meta['control']
    if ctl=='numeric_input':
        page.locator('#mb-short').fill(code)
    elif ctl=='matching_selects_4':
        assert len(code)==4
        for i,ch in enumerate(code):
            page.locator(f'.mb-select[data-pos="{i}"]').select_option(ch)
    elif ctl=='checkboxes':
        for ch in code:
            page.locator(f'input[data-choice="{ch}"]').check()
    elif ctl=='row_checkboxes':
        for ch in code:
            page.locator(f'input[data-row="{ch}"]').check()
    else:
        raise AssertionError(f'Unknown control {ctl}')
    assert page.evaluate('n=>window.EKSAMIO_MATH_BASE_TEST.isAnswered(n)',n), (n,meta)
    assert page.evaluate('n=>window.EKSAMIO_MATH_BASE_TEST.score(n)',n)==1, (n,meta,code)
    return meta


def main():
    evidence={'status':'PASS','package_version':'1.1','checks':{},'details':{}}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[]
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.goto(URL,wait_until='load')
        page.evaluate('localStorage.clear()')
        page.reload(wait_until='load')
        page.locator('#mb-start').click()

        variants=page.evaluate("""()=>window.EKSAMIO_MATH_BASE_TEST.tasks.map(t=>({n:t.number,variants:t.variants.map(v=>v.variant)}))""")
        passed=0
        for item in variants:
            n=item['n']
            for k in item['variants']:
                page.evaluate('([n,k])=>window.EKSAMIO_MATH_BASE_TEST.setVariant(n,k)',[n,k])
                fill_current_correct(page,n)
                passed+=1
        assert passed==70
        evidence['checks']['official_examples_real_controls']='70/70'

        page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.setVariant(1,3)')
        page.locator('#mb-short').fill('11.2')
        assert page.locator('#mb-short').input_value()=='11,2'
        st=page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.state().answers[1]')
        assert st=={'value':'11,2','valid':True}, st
        assert page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.score(1)')==0
        assert 'Введите целое число.' in page.locator('.mb-answerbox .mb-answer-hint').inner_text()
        page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.setCurrent(2)')
        page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.setCurrent(1)')
        assert page.locator('#mb-short').input_value()=='11,2'
        page.reload(wait_until='load')
        assert page.locator('#mb-short').input_value()=='11,2'
        assert page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.state().answers[1].value')=='11,2'
        evidence['checks']['task1_decimal_wrong_persists']='PASS: 11.2 → 11,2 → reload 11,2; scorer 0/1'

        page.locator('#mb-short').fill('12')
        assert page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.score(1)')==1
        evidence['checks']['task1_correct_integer']='PASS: 12 scores 1/1'

        page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.setVariant(5,1)')
        page.locator('#mb-short').fill('0.25')
        assert page.locator('#mb-short').input_value()=='0,25'
        assert page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.score(5)')==1
        page.reload(wait_until='load')
        assert page.locator('#mb-short').input_value()=='0,25'
        evidence['checks']['decimal_dot_normalization']='PASS: 0.25 → 0,25 → reload 0,25'

        page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.setVariant(3,3)')
        page.locator('#mb-short').fill('12 200')
        st=page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.state().answers[3]')
        assert st=={'value':'12 200','valid':False}, st
        assert page.locator('#mb-short').input_value()=='12 200'
        assert page.locator('#mb-short').evaluate('(e)=>e.classList.contains("is-invalid")')
        assert not page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.isAnswered(3)')
        page.reload(wait_until='load')
        assert page.locator('#mb-short').input_value()=='12 200'
        assert page.locator('#mb-short').evaluate('(e)=>e.classList.contains("is-invalid")')
        evidence['checks']['invalid_space_preserved']='PASS: 12 200 remains invalid and is not normalized to 12200'

        page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.setVariant(7,2)')
        txt=page.locator('#mb-task').inner_text()
        assert 'Н·м' in txt
        assert 'Нꞏм' not in txt
        evidence['checks']['task7_unit_typography']='PASS: Н·м'

        widths=[1280,768,390,360,320]
        overflow={}
        for w in widths:
            page.set_viewport_size({'width':w,'height':900})
            page.wait_for_timeout(50)
            delta=page.evaluate('()=>document.documentElement.scrollWidth-window.innerWidth')
            overflow[str(w)]=delta
            assert delta<=1,(w,delta)
        evidence['checks']['widths']='PASS: '+', '.join(map(str,widths))
        evidence['details']['overflow_delta_px']=overflow

        page.set_viewport_size({'width':1280,'height':900})
        page.evaluate('localStorage.clear()')
        page.reload(wait_until='load')
        page.locator('#mb-start').click()
        for n in range(1,22):
            page.evaluate('n=>window.EKSAMIO_MATH_BASE_TEST.setCurrent(n)',n)
            fill_current_correct(page,n)
        assert page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.total()')==21
        assert page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.answeredCount()')==21
        page.evaluate('()=>window.EKSAMIO_MATH_BASE_TEST.finish()')
        assert page.locator('#mb-score').inner_text().strip()=='21/21'
        assert page.locator('#mb-answered').inner_text().strip()=='21/21'
        evidence['checks']['full_correct_attempt']='21/21'
        evidence['checks']['state_restore']='PASS'
        evidence['checks']['javascript_errors']=len(errors)
        assert not errors,errors
        browser.close()

    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
