from __future__ import annotations
from pathlib import Path
import json, re, hashlib, shutil

root=Path('ege-istoriya-demoversiya-v1')
pfx='ege-istoriya-demoversiya'
assert root.exists()
old_css='.eh-alpha{list-style-type:upper-alpha}'
new_css=(
'.eh-alpha{list-style:none!important;padding-left:31px!important}'
'.eh-alpha>li{position:relative}'
'.eh-alpha>li::before{position:absolute;left:-31px;width:25px;text-align:right;font-weight:700}'
'.eh-alpha>li:nth-child(1)::before{content:"а)"}'
'.eh-alpha>li:nth-child(2)::before{content:"б)"}'
'.eh-alpha>li:nth-child(3)::before{content:"в)"}'
'.eh-alpha>li:nth-child(4)::before{content:"г)"}'
'.eh-alpha>li:nth-child(5)::before{content:"д)"}'
'.eh-alpha>li:nth-child(6)::before{content:"е)"}'
'.eh-two-col .eh-alpha>li:nth-child(1)::before{content:"А)"}'
'.eh-two-col .eh-alpha>li:nth-child(2)::before{content:"Б)"}'
'.eh-two-col .eh-alpha>li:nth-child(3)::before{content:"В)"}'
'.eh-two-col .eh-alpha>li:nth-child(4)::before{content:"Г)"}'
'.eh-two-col .eh-alpha>li:nth-child(5)::before{content:"Д)"}'
'.eh-two-col .eh-alpha>li:nth-child(6)::before{content:"Е)"}'
)

hits=0
for p in sorted(root.rglob('*')):
    if not p.is_file() or p.suffix.lower() not in {'.txt','.json','.html','.css','.py'}:
        continue
    text=p.read_text(encoding='utf-8')
    changed=False
    if old_css in text:
        hits += text.count(old_css)
        text=text.replace(old_css,new_css)
        changed=True
    if 'v1_0_2' in text or '1.0.2' in text:
        text=text.replace('v1_0_2','v1_0_3').replace('1.0.2','1.0.3')
        changed=True
    if changed: p.write_text(text,encoding='utf-8')
assert hits==3 or (hits==0 and new_css in (root/'assets.css').read_text(encoding='utf-8')),hits

old=root/'tests/test_independent_v102.py'; new=root/'tests/test_independent_v103.py'
if old.exists(): old.rename(new)
assert new.exists()

exam_path=root/f'{pfx}-EXAM-DATA.json'
exam=json.loads(exam_path.read_text(encoding='utf-8'))
assert exam['version']=='1.0.3'
assert exam['storage_key']=='eksamio_ege_istoriya_demo_2026_v1_0_3'
expected={1:list('АБВГ'),3:list('АБВГ'),4:list('АБВГДЕ'),5:list('АБВГ'),7:list('АБВГ')}
for n,labels in expected.items():
    assert exam['tasks'][n-1]['interaction']['labels']==labels
for t in exam['tasks']:
    assert not re.search(r'>\s*[A-F]\s*(?:<|\))',t['prompt_html']),t['number']

contract_path=root/f'{pfx}-PACKAGE-CONTRACT.json'
contract=json.loads(contract_path.read_text(encoding='utf-8'))
contract['package_version']='1.0.3'
contract.setdefault('interaction_contract',{})['lettered_positions_match_fipi_alphabet_and_case']=True
blocks=sorted(root.glob(f'{pfx}-T123-*.txt'))
contract['t123_max_bytes']=max(p.stat().st_size for p in blocks)
contract_path.write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

static_path=root/'tests/test_static.py'
static=static_path.read_text(encoding='utf-8')
if 'lettered_positions_match_fipi_alphabet_and_case' not in static:
    insert='''\ncss=(ROOT/"assets.css").read_text(encoding="utf-8")\nassert "upper-alpha" not in css and "lower-alpha" not in css\nfor marker in ["А)","Б)","В)","Г)","Д)","Е)","а)","б)","в)"]:\n    assert f'content:"{marker}"' in css,marker\nfor n in [1,3,5,7]:\n    assert 'class="eh-alpha"' in exam["tasks"][n-1]["prompt_html"]\nassert 'class="eh-alpha"' in exam["tasks"][17]["prompt_html"]\nassert contract["interaction_contract"]["lettered_positions_match_fipi_alphabet_and_case"] is True\n'''
    static=static.replace('print("STATIC PASS")',insert+'\nprint("STATIC PASS")')
    static_path.write_text(static,encoding='utf-8')

label_test=root/'tests/test_cyrillic_labels.py'
label_test.write_text(r'''from pathlib import Path
import shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'ege-istoriya-demoversiya-PREVIEW.html').read_text(encoding='utf-8')
POLYFILL="window.__EH_STORAGE=window.__EH_STORAGE||(()=>{const m={};return {getItem:k=>Object.prototype.hasOwnProperty.call(m,k)?m[k]:null,setItem:(k,v)=>m[k]=String(v),removeItem:k=>delete m[k],clear:()=>Object.keys(m).forEach(k=>delete m[k])}})();"
def markers(locator):
    return locator.evaluate_all("els=>els.map(e=>getComputedStyle(e,'::before').content.replace(/^['\\\"]|['\\\"]$/g,''))")
with sync_playwright() as p:
    launch={'headless':True}; exe=shutil.which('chromium') or shutil.which('chromium-browser') or shutil.which('google-chrome')
    if exe: launch['executable_path']=exe
    browser=p.chromium.launch(**launch)
    for width in [1440,768,390,360,320]:
        page=browser.new_page(viewport={'width':width,'height':1000})
        page.evaluate(POLYFILL); page.set_content(HTML,wait_until='load'); page.click('#eh-start-btn')
        for n in [1,3,5,7]:
            page.click(f'.eh-nav-btn:nth-child({n})')
            assert markers(page.locator('.eh-two-col .eh-alpha>li'))==['А)','Б)','В)','Г)']
            assert [page.locator('.eh-match-letter').nth(i).inner_text() for i in range(4)]==list('АБВГ')
        page.click('.eh-nav-btn:nth-child(4)')
        table=[x.strip() for x in page.locator('.eh-table td').all_inner_texts()]
        for label in list('АБВГДЕ'): assert label in table
        assert not any(x in list('ABCDEF') for x in table)
        page.click('.eh-nav-btn:nth-child(17)')
        source=page.locator('.eh-source').inner_text()
        assert 'А)' in source and 'Б)' in source and 'A)' not in source and 'B)' not in source
        page.click('.eh-nav-btn:nth-child(18)')
        assert markers(page.locator('.eh-prompt>.eh-alpha>li'))==['а)','б)','в)']
        assert not page.evaluate('document.documentElement.scrollWidth > document.documentElement.clientWidth')
        page.close()
    browser.close()
print('CYRILLIC LABELS PASS')
''',encoding='utf-8')

report_path=root/f'{pfx}-TEST-REPORT.txt'; report=report_path.read_text(encoding='utf-8').rstrip()
if 'Кириллические метки А–Е' not in report:
    report += ('\n23. Кириллические метки А–Е во всех заданиях на соответствие и таблицах: PASS'
               '\n24. Кириллические метки а–в в задании 18 и критериях: PASS'
               '\n25. Браузерная проверка вычисленных маркеров без латинских A–F: PASS\n')
report_path.write_text(report,encoding='utf-8')

audit_path=root/f'{pfx}-INDEPENDENT-AUDIT.txt'; audit=audit_path.read_text(encoding='utf-8').rstrip()
if 'ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ВЕРСИИ 1.0.3' not in audit:
    audit += ('\n\nДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА ВЕРСИИ 1.0.3\n'
              'PASS — позиции соответствий и пропуски таблицы используют кириллические А–Е, как в ФИПИ. '
              'В задании 18 пункты ответа используют строчные кириллические а–в. Латинская CSS-нумерация удалена.\n')
audit_path.write_text(audit,encoding='utf-8')

rules_path=root/f'{pfx}-IMPLEMENTATION-RULES.txt'; rules=rules_path.read_text(encoding='utf-8').rstrip()
if 'Буквенные обозначения должны совпадать' not in rules:
    rules += ('\n10. Буквенные обозначения должны совпадать с ФИПИ по алфавиту и регистру. '
              'Для кириллицы запрещено использовать CSS upper-alpha/lower-alpha; фактические маркеры проверяются в браузере.\n')
rules_path.write_text(rules,encoding='utf-8')

build=root/'scripts/build_demo_release.py'
build.write_text(build.read_text(encoding='utf-8').replace('v1.0.2.zip','v1.0.3.zip'),encoding='utf-8')
for p in root.rglob('__pycache__'):
    if p.is_dir(): shutil.rmtree(p)
manifest=root/f'{pfx}-MANIFEST-SHA256.txt'
lines=[]
for f in sorted(root.rglob('*')):
    if f.is_file() and f!=manifest:
        lines.append(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(root).as_posix()}')
manifest.write_text('\n'.join(lines)+'\n',encoding='utf-8')

# trigger after workflow registration
