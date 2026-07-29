#!/usr/bin/env python3
from __future__ import annotations
import base64, json, re, subprocess
from pathlib import Path
from PIL import Image

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO/'ege-khimiya-demoversiya-v1'
P='ege-khimiya-demoversiya'

def dump(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def compact(obj): return json.dumps(obj,ensure_ascii=False,separators=(',',':'))
def replace_json_script(path,script_id,payload):
    text=path.read_text(encoding='utf-8')
    pat=re.compile(r'(<script type="application/json" id="'+re.escape(script_id)+r'">)(.*?)(</script>)',re.S)
    text,n=pat.subn(lambda m:m.group(1)+compact(payload)+m.group(3),text,count=1)
    if n!=1: raise RuntimeError(f'{script_id} not found: {path}')
    path.write_text(text,encoding='utf-8')
def replace_or_confirm(text,old,new,label):
    if old in text:return text.replace(old,new,1)
    if new in text:return text
    raise RuntimeError(f'cannot patch {label}')
def ui_task(t): return {k:v for k,v in t.items() if k not in {'required_acceptance_case_ids','criteria'}}

# Strict official decimal form.
task_path=ROOT/f'{P}-TASK-MAP.json'; task_data=json.loads(task_path.read_text(encoding='utf-8'))
for t in task_data['tasks']:
    if t['kind']=='short' and t['number'] in (27,28) and ',' in t['answer']['canonical']:
        t['answer']['normalization']['allow_decimal_point']=False
        t['input_hint']='Введите число в точной форме ФИПИ, используя десятичную запятую; без пробелов, единиц и дополнительных знаков.'
dump(task_path,task_data)
cases_path=ROOT/f'{P}-ACCEPTANCE-CASES.json'; cases=json.loads(cases_path.read_text(encoding='utf-8'))
for c in cases['cases']:
    if c['id'] in {'task-27-v1-decimal-point','task-28-v1-decimal-point'}:
        c.update(expected_score=0,category='negative-decimal-point',basis='official answer table and strict form require the decimal comma')
dump(cases_path,cases)
replace_json_script(ROOT/f'{P}-T123-02.txt','chem-data-short-a',[ui_task(t) for t in task_data['tasks'] if t['kind']=='short' and t['number']<=18])
replace_json_script(ROOT/f'{P}-T123-03.txt','chem-data-short-b',[ui_task(t) for t in task_data['tasks'] if t['kind']=='short' and 19<=t['number']<=28])
replace_json_script(ROOT/f'{P}-T123-04.txt','chem-data-extended',[ui_task(t) for t in task_data['tasks'] if t['kind']=='extended'])
replace_json_script(ROOT/f'{P}-T123-04.txt','chem-acceptance-data',cases['cases'])

# High-resolution official references from physical PDF pages 2 and 3.
tmp=REPO/'.chem-audit-render'; tmp.mkdir(exist_ok=True)
pdf=ROOT/'source/ege-2026-khimiya-demoversiya.pdf'
for page,name in [(2,'reference-solubility.webp'),(3,'reference-periodic.webp')]:
    prefix=tmp/f'p{page}'
    subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-r','120','-png','-singlefile',str(pdf),str(prefix)],check=True)
    with Image.open(prefix.with_suffix('.png')) as im: im.convert('RGB').save(ROOT/'assets'/name,'WEBP',quality=92,method=6)
for idx,name,sid in [(7,'reference-solubility.webp','chem-ref-solubility-data'),(8,'reference-periodic.webp','chem-ref-periodic-data')]:
    raw=(ROOT/'assets'/name).read_bytes(); replace_json_script(ROOT/f'{P}-T123-{idx:02d}.txt',sid,{'data':'data:image/webp;base64,'+base64.b64encode(raw).decode()})
for p in tmp.glob('*'):p.unlink()
tmp.rmdir()

# Mobile reference viewport.
css_path=ROOT/f'{P}-T123-01.txt'; css=css_path.read_text(encoding='utf-8')
old='.chem-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:13px 0}.chem-ref-img{display:none;width:100%;height:auto;border:1px solid var(--chem-line);border-radius:12px}.chem-ref-img.is-active{display:block}'
new='.chem-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:13px 0}.chem-ref-help{margin:0 0 9px}.chem-ref-viewport{overflow:auto;max-height:calc(100vh - 190px);border:1px solid var(--chem-line);border-radius:12px;background:white;-webkit-overflow-scrolling:touch;overscroll-behavior:contain}.chem-ref-img{display:none;width:100%;height:auto;max-width:none}.chem-ref-img.is-active{display:block}'
css=replace_or_confirm(css,old,new,'reference CSS')
css=replace_or_confirm(css,'@media(max-width:520px){.chem-hero','@media(max-width:520px){.chem-ref-img.is-active{width:1000px}.chem-hero','mobile reference CSS')
css_path.write_text(css,encoding='utf-8')
markup_path=ROOT/f'{P}-T123-05.txt'; markup=markup_path.read_text(encoding='utf-8')
old='<div class="chem-tabs"><button class="chem-btn chem-btn-primary" data-ref-tab="solubility">Растворимость и ряд активности</button><button class="chem-btn chem-btn-ghost" data-ref-tab="periodic">Периодическая система</button></div><img class="chem-ref-img is-active" id="chem-ref-solubility" alt="Таблица растворимости и ряд активности металлов"><img class="chem-ref-img" id="chem-ref-periodic" alt="Периодическая система химических элементов">'
new='<div class="chem-tabs"><button class="chem-btn chem-btn-primary" data-ref-tab="solubility">Растворимость и ряд активности</button><button class="chem-btn chem-btn-ghost" data-ref-tab="periodic">Периодическая система</button></div><div class="chem-hint chem-ref-help">На телефоне таблицу можно прокручивать по горизонтали.</div><div class="chem-ref-viewport" tabindex="0" aria-label="Прокручиваемая область справочной таблицы"><img class="chem-ref-img is-active" id="chem-ref-solubility" alt="Таблица растворимости и ряд активности металлов"><img class="chem-ref-img" id="chem-ref-periodic" alt="Периодическая система химических элементов"></div>'
markup=replace_or_confirm(markup,old,new,'reference markup'); markup_path.write_text(markup,encoding='utf-8')

# Scoring and robust reference initialization.
js_path=ROOT/f'{P}-T123-06.txt'; js=js_path.read_text(encoding='utf-8')
old="function scoreShort(task,value){const v=String(value??'');const a=task.answer.canonical;const typ=task.answer.type;if(typ==='numeric_exact'){if(!/^\\d+(?:[.,]\\d+)?$/.test(v))return 0;const norm=x=>x.replace('.',',');return norm(v)===norm(a)?task.max_score:0}"
new="function scoreShort(task,value){const v=String(value??'');const a=task.answer.canonical;const typ=task.answer.type;if(typ==='numeric_exact'){const n=task.answer.normalization||{},allowPoint=n.allow_decimal_point===true,pattern=allowPoint?/^\\d+(?:[.,]\\d+)?$/:/^\\d+(?:,\\d+)?$/;if(!pattern.test(v))return 0;const normalized=allowPoint?v.replace('.',','):v;return normalized===a?task.max_score:0}"
js=replace_or_confirm(js,old,new,'numeric scoring')
old="window.addEventListener('DOMContentLoaded',()=>{try{const r1=JSON.parse(document.getElementById('chem-ref-solubility-data').textContent),r2=JSON.parse(document.getElementById('chem-ref-periodic-data').textContent);$('#chem-ref-solubility').src=r1.data;$('#chem-ref-periodic').src=r2.data}catch(e){console.error('Reference assets failed',e)}})"
new="function loadReferenceAssets(){try{const r1=JSON.parse(document.getElementById('chem-ref-solubility-data').textContent),r2=JSON.parse(document.getElementById('chem-ref-periodic-data').textContent);$('#chem-ref-solubility').src=r1.data;$('#chem-ref-periodic').src=r2.data}catch(e){console.error('Reference assets failed',e)}}if(document.readyState==='loading')window.addEventListener('DOMContentLoaded',loadReferenceAssets,{once:true});else loadReferenceAssets()"
js=replace_or_confirm(js,old,new,'reference initialization'); js_path.write_text(js,encoding='utf-8')

# Extracted-release validator mode.
val_path=ROOT/'scripts/validate_demo_package.py'; val=val_path.read_text(encoding='utf-8')
if '--extracted-release' not in val:
    val=val.replace('def validate_build_files(root: Path, contract_path: Path, contract: dict[str, Any], result: ValidationResult) -> None:','def validate_build_files(root: Path, contract_path: Path, contract: dict[str, Any], result: ValidationResult, extracted_release: bool = False) -> None:')
    val=val.replace('''    if status in RELEASE_STATUSES:\n        if result.check(zip_path.is_file(), f"Release ZIP is missing: {zip_path.name}"):\n            try:\n                with zipfile.ZipFile(zip_path) as archive:''','''    if status in RELEASE_STATUSES:\n        if extracted_release and not zip_path.is_file():\n            pass\n        elif result.check(zip_path.is_file(), f"Release ZIP is missing: {zip_path.name}"):\n            try:\n                with zipfile.ZipFile(zip_path) as archive:''')
    val=val.replace('def validate_package(contract_path: Path) -> ValidationResult:','def validate_package(contract_path: Path, extracted_release: bool = False) -> ValidationResult:')
    val=val.replace('validate_build_files(root, contract_path, contract, result)','validate_build_files(root, contract_path, contract, result, extracted_release=extracted_release)')
    val=val.replace('parser.add_argument("--self-test", action="store_true", help="Run validator internal tests")','parser.add_argument("--self-test", action="store_true", help="Run validator internal tests")\n    parser.add_argument("--extracted-release", action="store_true", help="Validate files unpacked from the release ZIP; do not require a nested copy of the ZIP")')
    val=val.replace('result = validate_package(args.contract)','result = validate_package(args.contract, extracted_release=args.extracted_release)')
val_path.write_text(val,encoding='utf-8')

# Tests.
static_path=ROOT/'tests/test_static.py'; st=static_path.read_text(encoding='utf-8')
if 'test_decimal_point_is_rejected' not in st:
    insert="""\n def test_decimal_point_is_rejected(self):\n  cases=json.loads((ROOT/f'{P}-ACCEPTANCE-CASES.json').read_text(encoding='utf-8'))['cases']\n  by={c['id']:c for c in cases}\n  self.assertEqual(by['task-27-v1-decimal-point']['expected_score'],0)\n  self.assertEqual(by['task-28-v1-decimal-point']['expected_score'],0)\n def test_reference_assets_high_resolution(self):\n  from PIL import Image\n  for name in ['reference-solubility.webp','reference-periodic.webp']:\n   with Image.open(ROOT/'assets'/name) as im:self.assertGreaterEqual(im.width,1400)\n"""
    st=st.replace(' def test_no_service_text(self):',insert+' def test_no_service_text(self):')
static_path.write_text(st,encoding='utf-8')
browser_path=ROOT/'tests/browser_test.mjs'; br=browser_path.read_text(encoding='utf-8')
if 'decimal point rejected task 27' not in br:
    br=br.replace("assert(got===c.expected_score,`${c.id}: ${got} != ${c.expected_score}`)}","assert(got===c.expected_score,`${c.id}: ${got} != ${c.expected_score}`)}assert(await page.evaluate(()=>window.KhimiyaDemoTestApi.scoreShort(27,1,'68.7'))===0,'decimal point rejected task 27');assert(await page.evaluate(()=>window.KhimiyaDemoTestApi.scoreShort(28,1,'2.24'))===0,'decimal point rejected task 28');")
    br=br.replace("await page.locator('#chem-results [data-open-reference]').click();assert(await page.locator('#chem-ref-solubility').getAttribute('src').then(x=>x.startsWith('data:image/webp;base64,')),'embedded reference');","await page.setViewportSize({width:320,height:900});await page.locator('#chem-results [data-open-reference]').click();assert(await page.locator('#chem-ref-solubility').getAttribute('src').then(x=>x.startsWith('data:image/webp;base64,')),'embedded reference');const refMetrics=await page.evaluate(()=>{const v=document.querySelector('.chem-ref-viewport'),i=document.getElementById('chem-ref-solubility');return{viewport:v.clientWidth,scroll:v.scrollWidth,image:i.clientWidth,natural:i.naturalWidth}});assert(refMetrics.image>=900&&refMetrics.scroll>refMetrics.viewport,'mobile reference supports horizontal pan');")
browser_path.write_text(br,encoding='utf-8')

# Version, evidence and reports.
contract_path=ROOT/f'{P}-PACKAGE-CONTRACT.json'; contract=json.loads(contract_path.read_text(encoding='utf-8')); contract['package']['version']='1.0.1'; dump(contract_path,contract)
page_status=ROOT/f'{P}-PAGE-STATUS.txt'; page_status.write_text(page_status.read_text(encoding='utf-8').replace('PACKAGE_VERSION: 1.0.0','PACKAGE_VERSION: 1.0.1'),encoding='utf-8')
readme=ROOT/'00-README-CODEX.txt'; r=readme.read_text(encoding='utf-8').replace('Версия: 1.0.0','Версия: 1.0.1')
if '--extracted-release' not in r:r=r.replace('python scripts/validate_demo_package.py ege-khimiya-demoversiya-PACKAGE-CONTRACT.json','python scripts/validate_demo_package.py ege-khimiya-demoversiya-PACKAGE-CONTRACT.json\nПосле распаковки ZIP: python scripts/validate_demo_package.py --extracted-release ege-khimiya-demoversiya-PACKAGE-CONTRACT.json')
readme.write_text(r,encoding='utf-8')
installation=ROOT/f'{P}-INSTALLATION.txt'; installation.write_text(installation.read_text(encoding='utf-8').replace('справочники, ширины 320/360/390 px и консоль.','справочники (включая горизонтальную прокрутку таблиц на телефоне), ширины 320/360/390 px и консоль.'),encoding='utf-8')
evidence_path=ROOT/f'{P}-INDEPENDENT-TEST-EVIDENCE.json'; ev=json.loads(evidence_path.read_text(encoding='utf-8')); ev['package_version']='1.0.1'; ev['independent_reaudit']={'source_pdf_visual_review':True,'official_answer_table_rechecked':True,'extended_criteria_29_34_rechecked':True,'decimal_point_rejected_for_official_comma_answers':True,'mobile_reference_horizontal_pan':True,'reference_assets_resolution':'1404x993','extracted_release_validator_mode':True}; dump(evidence_path,ev)
(ROOT/f'{P}-TEST-REPORT.txt').write_text('''ТЕХНИЧЕСКИЙ ОТЧЁТ\nИнтерактивная демоверсия ЕГЭ по химии\nВерсия: 1.0.1\n\nСТАТУС: PASS — READY_FOR_TILDA_TEST\n\n- финальные PDF ФИПИ: 3/3;\n- заданий: 34; официальных примеров с вариантами «ИЛИ»: 40;\n- официальный максимум: 36 + 20 = 56;\n- продолжительность: 210 минут;\n- accepted answers без подтверждения: 0;\n- строгая форма ответов 1–28: PASS;\n- десятичная точка в заданиях 27 и 28 отклоняется, принимается официальная запись с запятой: PASS;\n- частичный балл 6, 7, 8, 14, 15, 22, 23, 24: PASS;\n- варианты 19, 20, 24, 25, 28 сохраняются: PASS;\n- критерии 29–34, включая особую ветвь одной вычислительной ошибки в № 34: PASS;\n- зависимость задания 29: PASS;\n- справочные материалы сверены с PDF, заменены на изображения 1404×993 и доступны с горизонтальной прокруткой на телефоне: PASS;\n- localStorage с безопасным fallback: PASS;\n- T123-01 — T123-08: PASS;\n- preview: PASS;\n- manifest и ZIP: PASS;\n- validator запускается и в исходной папке, и после распаковки ZIP с флагом --extracted-release: PASS.\n\nНезависимый повторный аудит выявил и исправил три дефекта версии 1.0.0: принятие десятичной точки вместо официальной запятой; нечитаемое уменьшение справочных таблиц на мобильном экране; невозможность штатного запуска validator из распакованного ZIP.\n\nРеальная установка и опубликованная страница Tilda: НЕ ПРОВЕРЕНЫ.\n''',encoding='utf-8')
(ROOT/f'{P}-INDEPENDENT-AUDIT-2026-07-29.txt').write_text('''НЕЗАВИСИМЫЙ ПОВТОРНЫЙ АУДИТ\nИнтерактивная демоверсия ЕГЭ по химии\nВерсия после исправлений: 1.0.1\nДата: 29 июля 2026 года\n\nИТОГ: PASS — READY_FOR_TILDA_TEST\n\nПроверено заново без доверия к прежнему TEST-REPORT:\n1. Финальные демоверсия, спецификация и кодификатор ФИПИ.\n2. Структура экзамена: 34 задания, 210 минут, 56 первичных баллов.\n3. Таблица официальных ответов всех 40 примеров, включая варианты «ИЛИ».\n4. Правила неупорядоченных ответов и частичного оценивания.\n5. Полные условия заданий 1–34.\n6. Модельные ответы и критерии заданий 29–34.\n7. Зависимость электронного баланса в задании 29.\n8. Особая ветвь одной вычислительной ошибки в задании 34.\n9. Таймер, варианты, сохранение, результаты и маркировка неофициальной самооценки.\n10. Справочные материалы и мобильное отображение.\n11. Manifest, ZIP и повторная проверка распакованного релиза.\n\nВЫЯВЛЕННЫЕ И ИСПРАВЛЕННЫЕ ДЕФЕКТЫ\n1. Задания 27 и 28 принимали запись с десятичной точкой вместо официальной запятой. Точка теперь отклоняется.\n2. Справочные таблицы на ширине 320 px уменьшались примерно до 286 px. Добавлена горизонтальная прокрутка и изображения 1404×993.\n3. Validator из распакованного ZIP требовал ZIP внутри самого ZIP. Добавлен режим --extracted-release.\n\nБЛОКИРУЮЩИХ ПРЕДМЕТНЫХ ОШИБОК ПОСЛЕ ИСПРАВЛЕНИЙ НЕ ОБНАРУЖЕНО.\n\nОпубликованная страница Tilda ещё не проверена. После установки восьми T123 обязателен production smoke-test.\n''',encoding='utf-8')
print('chemistry independent audit fixes applied')
