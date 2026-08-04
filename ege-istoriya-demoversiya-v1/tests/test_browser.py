from __future__ import annotations
import json,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'ege-istoriya-demoversiya-PREVIEW.html').read_text(encoding='utf-8')
assert 'eksamio_ege_istoriya_demo_2026_v1_0_2' in HTML
assert 'eksamio_ege_istoriya_demo_2026_v1_0_1' not in HTML
EVIDENCE=ROOT/'tests'/'evidence'
EVIDENCE.mkdir(parents=True,exist_ok=True)
WIDTHS=[1440,768,390,360,320]
POLYFILL="window.__EH_STORAGE=window.__EH_STORAGE||(()=>{const m={};return {getItem:k=>Object.prototype.hasOwnProperty.call(m,k)?m[k]:null,setItem:(k,v)=>m[k]=String(v),removeItem:k=>delete m[k],clear:()=>Object.keys(m).forEach(k=>delete m[k]),_dump:()=>JSON.stringify(m)}})();"
report={'widths':{},'task_render_count':0,'image_checks':0,'scoring_cases':0,'matching_tasks_checked':[],'matching_persistence':False,'persistence':False,'errors':[]}

def choose_matching(page,values):
    selects=page.locator('.eh-match-select')
    assert selects.count()==len(values)
    for i,value in enumerate(values): selects.nth(i).select_option(str(value))

with sync_playwright() as p:
    launch={'headless':True};exe=shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
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
        assert not page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth')
        image_checks=0
        for n in range(1,22):
            page.click(f'.eh-nav-btn:nth-child({n})')
            assert f'Задание {n}' in page.locator('#eh-question').inner_text()
            for img in page.locator('#eh-question img').all():
                assert img.evaluate('e=>e.complete && e.naturalWidth>0');image_checks+=1
        report['task_render_count']=21;report['image_checks']=max(report['image_checks'],image_checks)
        # Human matching UI for every correspondence task.
        expectations={1:(4,6,[6,2,3,5],'6235'),3:(4,6,[3,1,2,6],'3126'),4:(6,9,[9,4,3,5,1,7],'943517'),5:(4,6,[4,6,2,5],'4625'),7:(4,6,[6,5,2,4],'6524')}
        for n,(positions,option_count,values,code) in expectations.items():
            page.click(f'.eh-nav-btn:nth-child({n})')
            selects=page.locator('.eh-match-select')
            assert selects.count()==positions
            assert selects.first.locator('option').count()==option_count+1
            choose_matching(page,values)
            assert page.locator('#eh-match-output').inner_text()==code
            assert code in page.evaluate('window.__EH_STORAGE._dump()')
            assert 'is-answered' in (page.locator('.eh-nav-btn').nth(n-1).get_attribute('class') or '')
            report['matching_tasks_checked'].append(n)
        # Incomplete selection remains incomplete and survives navigation.
        page.click('.eh-nav-btn:nth-child(5)');page.click('#eh-clear')
        page.locator('.eh-match-select').nth(0).select_option('4')
        assert page.locator('#eh-match-output').inner_text()=='4———'
        assert 'is-answered' not in (page.locator('.eh-nav-btn').nth(4).get_attribute('class') or '')
        page.click('.eh-nav-btn:nth-child(6)');page.click('.eh-nav-btn:nth-child(5)')
        assert page.locator('.eh-match-select').nth(0).input_value()=='4'
        assert page.locator('.eh-match-select').nth(1).input_value()==''
        # Complete task 5 again and verify exact scoring later.
        choose_matching(page,[4,6,2,5])
        report['matching_persistence']=True
        # Other answer types and persistence.
        page.click('.eh-nav-btn:nth-child(6)');page.fill('#eh-answer','2457')
        page.click('.eh-nav-btn:nth-child(9)');page.fill('#eh-answer','Алексей Романов')
        page.click('.eh-nav-btn:nth-child(13)');page.fill('#eh-answer','1964; Хрущёв; А.Н. Косыгин')
        stored=page.evaluate('window.__EH_STORAGE._dump()')
        assert '4625' in stored and '1964' in stored
        page.evaluate("delete window.EKSAMIO_HISTORY_TASKS;delete window.EKSAMIO_HISTORY_EXAM;delete window.EKSAMIO_HISTORY_EXAM_META;delete window.EKSAMIO_HISTORY_ASSET_CHUNKS;delete window.EKSAMIO_HISTORY_TEST")
        page.set_content(HTML,wait_until='load');page.click('#eh-resume-btn')
        assert page.locator('#eh-answer').input_value().startswith('1964')
        page.click('.eh-nav-btn:nth-child(7)')
        assert [page.locator('.eh-match-select').nth(i).input_value() for i in range(4)]==['6','5','2','4']
        report['persistence']=True
        cases=[
          (1,'6235',2),(2,'132',1),(3,'3126',2),(4,'943517',3),(5,'4625',2),(6,'2456',2),
          (7,'6524',2),(8,'сорок пятом',1),(9,'Алексей Михайлович',1),(10,'Симбирск',1),(11,'Астрахань',1),(12,'56',2),
          (1,'6234',1),(1,'62345',0),(4,'943516',2),(4,'943126',1),(4,'9435171',0),
          (5,'4624',1),(5,'462-',0),(7,'6523',1),(7,'65--',0),
          (6,'6542',2),(6,'2457',1),(6,'245',1),(6,'24561',1),(6,'24566',0),
          (8,'Сорок пятом.',1),(9,'Алексей Романов',1),(12,'65',2),(12,'5',1),(12,'57',1)
        ]
        for n,value,expected in cases:
            got=page.evaluate("([n,v])=>{const t=window.EKSAMIO_HISTORY_TEST.exam.tasks.find(x=>x.number===n);return window.EKSAMIO_HISTORY_TEST.scoreShort(t,v)}",[n,value])
            assert got==expected,(n,value,got,expected)
        report['scoring_cases']=len(cases)
        page.click('#eh-finish-side');page.click('#eh-modal-confirm');page.wait_for_selector('#eh-results:not(.eh-hidden)')
        txt=page.locator('#eh-results').inner_text()
        assert '13 / 20' in txt and '— / 42' in txt and 'не является официальным результатом' in txt
        assert page.locator('.eh-result-task').count()==21
        checks=[(12,'отсутствия неверных позиций'),(13,'переписанный целиком объёмный отрывок'),(18,'содержится в определении'),(19,'оцениваются только первый тезис'),(20,'указанный первым')]
        for idx,snippet in checks:
            item=page.locator('.eh-result-task').nth(idx);item.locator('summary').click();assert snippet.lower() in item.inner_text().lower(),(idx,snippet)
        details=page.locator('.eh-result-task').nth(12);details.locator('input[value="2"]').check();assert '2 / 22' in page.locator('#eh-self-total').inner_text()
        d14=page.locator('.eh-result-task').nth(13);assert 'is-disabled' in d14.locator('.eh-rubric').get_attribute('class')
        assert not js_errors,js_errors;assert not failed,failed
        page.screenshot(path=str(EVIDENCE/f'results-{w}.png'),full_page=True)
        report['widths'][str(w)]={'horizontal_overflow':False,'javascript_errors':0,'failed_requests':0}
        page.close()
    page=browser.new_page(viewport={'width':320,'height':900});page.evaluate(POLYFILL);page.set_content(HTML);page.click('#eh-start-btn');page.click('.eh-nav-btn:nth-child(7)');page.screenshot(path=str(EVIDENCE/'question-matching-320.png'),full_page=True);page.close()
    browser.close()
report['matching_tasks_checked']=sorted(set(report['matching_tasks_checked']))
(ROOT/'ege-istoriya-demoversiya-BROWSER-TEST-EVIDENCE.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('BROWSER PASS')
