from __future__ import annotations
import json,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'ege-istoriya-demoversiya-PREVIEW.html').read_text(encoding='utf-8')
EVIDENCE=ROOT/'tests'/'evidence'
EVIDENCE.mkdir(parents=True,exist_ok=True)
WIDTHS=[1440,768,390,360,320]
POLYFILL="window.__EH_STORAGE=window.__EH_STORAGE||(()=>{const m={};return {getItem:k=>Object.prototype.hasOwnProperty.call(m,k)?m[k]:null,setItem:(k,v)=>m[k]=String(v),removeItem:k=>delete m[k],clear:()=>Object.keys(m).forEach(k=>delete m[k]),_dump:()=>JSON.stringify(m)}})();"
report={'widths':{},'task_render_count':0,'image_checks':0,'scoring_cases':0,'persistence':False,'errors':[]}

with sync_playwright() as p:
    launch={'headless':True};exe=shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome');
    if exe: launch['executable_path']=exe
    browser=p.chromium.launch(**launch)
    for w in WIDTHS:
        page=browser.new_page(viewport={'width':w,'height':1000})
        js_errors=[];failed=[]
        page.on('pageerror',lambda e,bag=js_errors:bag.append(str(e)))
        page.on('requestfailed',lambda r,bag=failed:bag.append(r.url))
        page.evaluate(POLYFILL)
        page.set_content(HTML,wait_until='load')
        assert page.locator('#eh-start-btn').is_visible()
        page.click('#eh-start-btn')
        assert page.locator('.eh-nav-btn').count()==21
        overflow=page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth')
        assert not overflow
        # Render all tasks and verify every embedded image.
        image_checks=0
        for n in range(1,22):
            page.click(f'.eh-nav-btn:nth-child({n})')
            assert f'Задание {n}' in page.locator('#eh-question').inner_text()
            for img in page.locator('#eh-question img').all():
                assert img.evaluate('e=>e.complete && e.naturalWidth>0')
                image_checks+=1
        report['task_render_count']=21
        report['image_checks']=max(report['image_checks'],image_checks)
        # Functional and official scoring cases.
        page.click('.eh-nav-btn:nth-child(1)');page.fill('#eh-answer','6235')
        page.click('.eh-nav-btn:nth-child(6)');page.fill('#eh-answer','2457')
        page.click('.eh-nav-btn:nth-child(9)');page.fill('#eh-answer','Алексей Романов')
        page.click('.eh-nav-btn:nth-child(13)');page.fill('#eh-answer','1964; Хрущёв; А.Н. Косыгин')
        stored=page.evaluate('window.__EH_STORAGE._dump()')
        assert '6235' in stored and '1964' in stored
        # Simulated clean reload of T123 content while preserving browser storage.
        page.evaluate("delete window.EKSAMIO_HISTORY_TASKS;delete window.EKSAMIO_HISTORY_EXAM;delete window.EKSAMIO_HISTORY_EXAM_META;delete window.EKSAMIO_HISTORY_ASSET_CHUNKS;delete window.EKSAMIO_HISTORY_TEST")
        page.set_content(HTML,wait_until='load')
        page.click('#eh-resume-btn')
        assert page.locator('#eh-answer').input_value().startswith('1964')
        report['persistence']=True
        # Direct scorer acceptance cases.
        cases=[
          (1,'6235',2),(2,'132',1),(3,'3126',2),(4,'943517',3),(5,'4625',2),(6,'2456',2),
          (7,'6524',2),(8,'сорок пятом',1),(9,'Алексей Михайлович',1),(10,'Симбирск',1),(11,'Астрахань',1),(12,'56',2),
          (1,'6234',1),(1,'62345',0),(4,'943516',2),(4,'943126',1),(4,'9435171',0),
          (6,'6542',2),(6,'2457',1),(6,'245',1),(6,'24561',1),(6,'24566',0),
          (8,'Сорок пятом.',1),(9,'Алексей Романов',1),(12,'65',2),(12,'5',1),(12,'57',1)
        ]
        for n,value,expected in cases:
            got=page.evaluate("([n,v])=>{const t=window.EKSAMIO_HISTORY_TEST.exam.tasks.find(x=>x.number===n);return window.EKSAMIO_HISTORY_TEST.scoreShort(t,v)}",[n,value])
            assert got==expected,(n,value,got,expected)
        report['scoring_cases']=len(cases)
        # Finish and verify result contract.
        page.click('#eh-finish-side');page.click('#eh-modal-confirm')
        page.wait_for_selector('#eh-results:not(.eh-hidden)')
        txt=page.locator('#eh-results').inner_text()
        assert '4 / 20' in txt
        assert '— / 42' in txt
        assert 'не является официальным результатом' in txt
        details=page.locator('.eh-result-task').nth(12);details.locator('summary').click();details.locator('input[value="2"]').check()
        assert '2 / 22' in page.locator('#eh-self-total').inner_text()
        # Empty task 14 cannot receive a score.
        d14=page.locator('.eh-result-task').nth(13);d14.locator('summary').click();assert 'is-disabled' in d14.locator('.eh-rubric').get_attribute('class')
        assert not js_errors,js_errors
        assert not failed,failed
        page.screenshot(path=str(EVIDENCE/f'results-{w}.png'),full_page=True)
        report['widths'][str(w)]={'horizontal_overflow':False,'javascript_errors':0,'failed_requests':0}
        page.close()
    # Separate mobile question evidence.
    page=browser.new_page(viewport={'width':320,'height':900});page.evaluate(POLYFILL);page.set_content(HTML);page.click('#eh-start-btn');page.click('.eh-nav-btn:nth-child(9)');page.screenshot(path=str(EVIDENCE/'question-map-320.png'),full_page=True);page.close()
    browser.close()

(ROOT/'ege-istoriya-demoversiya-BROWSER-TEST-EVIDENCE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('BROWSER PASS')
