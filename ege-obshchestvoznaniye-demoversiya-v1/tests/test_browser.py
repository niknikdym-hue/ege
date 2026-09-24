from pathlib import Path
import json,os,shutil
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
preview=(root/'ege-obshchestvoznaniye-demoversiya-PREVIEW.html').read_text('utf-8')
key='eksamio_ege_soc_demo_v3'

def document(saved=None):
    initial=json.dumps(saved,ensure_ascii=False)
    poly=f"""<script>(function(){{const d={{}};Object.defineProperty(window,'localStorage',{{value:{{getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>d[k]=String(v),removeItem:k=>delete d[k],clear:()=>{{for(const k of Object.keys(d))delete d[k]}},key:i=>Object.keys(d)[i]||null,get length(){{return Object.keys(d).length}}}}}});const saved={initial};if(saved!==null)localStorage.setItem('{key}',saved);}})();</script>"""
    return preview.replace('<head>','<head>'+poly,1)

errors=[]
evidence=Path(os.environ['EVIDENCE_DIR']) if os.environ.get('EVIDENCE_DIR') else None
if evidence:evidence.mkdir(parents=True,exist_ok=True)
with sync_playwright() as pw:
    exe=os.environ.get('CHROME_PATH') or shutil.which('chromium') or shutil.which('google-chrome') or shutil.which('google-chrome-stable');assert exe,'Chrome/Chromium not found';browser=pw.chromium.launch(headless=True,executable_path=exe,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    page.on('dialog',lambda d:d.accept())
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.set_content(document(),wait_until='load')
    page.get_by_role('button',name='Начать экзамен').click()

    matching={3:'32132',6:'24431',13:'21312',15:'21212'}
    answers={1:'46',2:'13',3:'32132',4:'146',5:'15',6:'24431',7:'2356',8:'125',9:'145',10:'234',11:'245',12:'123',13:'21312',14:'123',15:'21212',16:'125'}

    for n in range(1,17):
        page.get_by_role('button',name=f'Задание {n}',exact=True).click()
        assert page.locator('#soc-short').count()==0
        if n in matching:
            sels=page.locator('.soc-match-select')
            assert sels.count()==5
            code=matching[n]
            if n==3:
                sels.nth(0).select_option(code[0])
                assert 'is-filled' not in (page.get_by_role('button',name='Задание 3',exact=True).get_attribute('class') or '')
                saved=page.evaluate(f"localStorage.getItem('{key}')")
                page.set_content(document(saved),wait_until='load')
                page.get_by_role('button',name='Задание 3',exact=True).click()
                sels=page.locator('.soc-match-select')
                assert sels.nth(0).input_value()==code[0]
            for i,ch in enumerate(code):
                sels.nth(i).select_option(ch)
            assert code in page.locator('#soc-code').inner_text()
        else:
            for ch in answers[n]:
                page.get_by_role('checkbox',name=f'Вариант {ch}').check()
            assert answers[n] in page.locator('#soc-code').inner_text()

    page.get_by_role('button',name='Задание 1',exact=True).click()
    assert page.get_by_role('checkbox',name='Вариант 1').is_disabled()
    assert page.evaluate('window.EKSAMIO_SOC_TEST.shortTotal()')==28

    page.get_by_role('button',name='Задание 2',exact=True).click()
    page.get_by_role('button',name='☆ Вернуться позже').click()
    saved=page.evaluate(f"localStorage.getItem('{key}')")
    page.set_content(document(saved),wait_until='load')
    assert 'is-marked' in (page.get_by_role('button',name='Задание 2',exact=True).get_attribute('class') or '')
    assert page.evaluate('window.EKSAMIO_SOC_TEST.shortTotal()')==28

    for n in range(17,26):
        page.get_by_role('button',name=f'Задание {n}',exact=True).click()
        tas=page.locator('textarea')
        for i in range(tas.count()):
            tas.nth(i).fill('Развёрнутый учебный ответ для проверки механики.')

    page.locator('#soc-finish').click()
    page.wait_for_timeout(200)
    assert page.locator('#soc-part1-score').inner_text()=='28/28'
    if evidence:page.screenshot(path=evidence/'results-1440.png',full_page=True)
    assert page.locator('#soc-total-score').inner_text()=='—/58'

    for n in range(17,26):
        page.get_by_text(f'Задание {n}',exact=True).last.click()
    selects=page.locator('.soc-rubric select')
    for i in range(selects.count()):
        s=selects.nth(i)
        if s.is_disabled():
            continue
        vals=s.locator('option').evaluate_all('(o)=>o.map(x=>x.value).filter(Boolean).map(Number)')
        s.select_option(str(max(vals)))

    s241=page.locator('select[data-task="24"][data-rubric="24.1"]')
    s242=page.locator('select[data-task="24"][data-rubric="24.2"]')
    s241.select_option('2')
    assert s242.is_disabled() and s242.input_value()=='0'
    s241.select_option('3')
    assert not s242.is_disabled()
    s242.select_option('1')
    assert page.locator('#soc-part2-score').inner_text()=='30/30'
    assert page.locator('#soc-total-score').inner_text()=='58/58'

    for field in ['q1','q2','q3']:
        page.evaluate(f"window.EKSAMIO_SOC_TEST.setLong(17,'{field}','')")
    page.evaluate('window.EKSAMIO_SOC_TEST.showResults()')
    page.get_by_text('Задание 17',exact=True).last.click()
    assert page.locator('select[data-task="17"]').is_disabled()
    assert page.locator('#soc-part2-score').inner_text()=='—/30'
    assert page.locator('#soc-total-score').inner_text()=='—/58'

    for width in [768,390,360,320]:
        page.set_viewport_size({'width':width,'height':900})
        page.get_by_role('button',name='Пройти заново').click()
        page.get_by_role('button',name='Начать экзамен').click()
        for n in range(1,26):
            page.get_by_role('button',name=f'Задание {n}',exact=True).click()
            overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            assert overflow<=0,(width,n,overflow)
            if evidence and width==320 and n in (2,3):page.screenshot(path=evidence/f'task-{n:02d}-320.png',full_page=True)
        page.evaluate('window.EKSAMIO_SOC_TEST.finish()')
        if evidence and width==320:page.screenshot(path=evidence/'results-320.png',full_page=True)

    assert not errors,errors
    if evidence:(evidence/'browser-evidence.json').write_text(json.dumps({'status':'PASS','part1':'28/28','part2_self_assessment':'30/30','orientational_total_after_full_self_assessment':'58/58','widths':[1440,768,390,360,320],'typed_part1_tasks':16,'javascript_errors':len(errors)},ensure_ascii=False,indent=2)+'\n','utf-8')
    browser.close()
print('BROWSER PASS')
