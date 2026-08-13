from playwright.sync_api import sync_playwright
import pathlib, json, sys
base=pathlib.Path(__file__).parent
patch=(base/'ege-russkiy-demoversiya-T123-06.txt').read_text(encoding='utf-8')
html='''<!doctype html><html><head><meta charset="utf-8"></head><body>
<div id="ege-demo-2026" data-state="running">
 <div id="edemo-task-stage"><div class="edemo-task-number">Задание 27 из 27</div><div class="edemo-answer"><label>Текст</label><textarea id="edemo-answer-input"></textarea><span id="edemo-live-word-count"></span></div></div>
 <section id="edemo-result" class="edemo-result">
  <div class="edemo-score-card"><div><span id="edemo-essay-score">—</span>/22</div><p id="edemo-essay-status"></p></div>
  <div class="edemo-score-card"><span id="edemo-total-score">—</span><p id="edemo-total-status"></p></div>
  <section><p><span id="edemo-result-word-count">0</span></p><div id="edemo-criteria"></div></section>
 </section>
</div>
<script>
window.__edemoRussian2026v41={technicalWordCount:function(v){var m=String(v||'').match(/[А-ЯЁа-яёA-Za-z]+(?:-[А-ЯЁа-яёA-Za-z]+)*/g);return m?m.length:0;}};
(function(){var i=document.getElementById('edemo-answer-input');i.addEventListener('input',function(){var k='eksamio_ege_russian_demo_2026_v4_1',s=JSON.parse(localStorage.getItem(k)||'{"answers":{}}');s.answers=s.answers||{};s.answers[27]=i.value;localStorage.setItem(k,JSON.stringify(s));});})();
</script>
'''+patch+'''</body></html>'''
fails=[]
def check(c,m):
    if not c:fails.append(m)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1000,'height':900})
    page.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return Object.prototype.hasOwnProperty.call(this._d,k)?this._d[k]:null},setItem(k,v){this._d[k]=String(v)},removeItem(k){delete this._d[k]}}})")
    page.set_content(html,wait_until='domcontentloaded')
    check(page.locator('.edemo-essay-mode').count()==1,'mode selector mounted')
    check(not page.locator('.edemo-answer').is_visible(),'paper mode hides demo textarea')
    page.check('#edemo-paper-complete')
    core=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_1'))")
    check(core['answers']['27']=='—','paper marker stored through core input event')
    page.check('input[name="edemo-writing-mode"][value="demo"]')
    check(page.locator('.edemo-answer').is_visible(),'demo mode shows textarea')
    page.fill('#edemo-answer-input','Демо текст сочинения')
    page.evaluate("document.getElementById('ege-demo-2026').setAttribute('data-state','finished')")
    page.wait_for_timeout(100)
    check(page.locator('#edemo-task27-transfer').count()==1,'post-exam transfer mounted')
    check(page.locator('#edemo-criteria[data-task27-hotfix="true"]').count()==1,'review replaces old criteria')
    words149=' '.join(['слово']*149)
    page.fill('#edemo-transferred-essay',words149)
    check(page.locator('#edemo-threshold-box').get_attribute('data-state')=='danger','149 words triggers danger guidance')
    words150=' '.join(['слово']*150)
    page.fill('#edemo-transferred-essay',words150)
    check(page.locator('#edemo-threshold-box').get_attribute('data-state')=='ok','150 words reaches threshold')
    page.check('#edemo-review-eligibility')
    for k,v in [('K1','1'),('K2','3'),('K3','2'),('K4','1'),('K5','2'),('K6','1')]:
        page.select_option(f'[data-review-score="{k}"]',v)
    for k in ['K7','K8','K9','K10']:
        page.select_option(f'[data-confirmed-errors="{k}"]','0')
    check(page.locator('#edemo-essay-score').inner_text()=='22','official score max 22')
    check('24/24' in page.locator('#edemo-diagnostic24').inner_text(),'normalized diagnostic max 24')
    # possible errors must not reduce score
    page.select_option('[data-possible-errors="K7"]','5')
    check(page.locator('#edemo-essay-score').inner_text()=='22','possible errors do not reduce score in UI')
    saved=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))")
    check(saved['transferredText']==words150,'transferred text persisted')
    check(saved['confirmedErrors']['K7']==0 and saved['possibleErrors']['K7']==5,'error states persisted separately')
    browser.close()
if fails:
    print('FAIL browser task27:',len(fails));print('\n'.join(fails));sys.exit(1)
print('PASS browser task27: modes, transfer, 149/150 threshold, scoring, possible-vs-confirmed persistence')
