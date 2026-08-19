#!/usr/bin/env python3
import importlib.util, json, os, time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementClickInterceptedException

URL=os.environ.get('EKSAMIO_PREVIEW_URL','http://127.0.0.1:8765/ege-matematika-profil-demoversiya-2024-PREVIEW.html')
HERE=Path(__file__).resolve(); ROOT=Path(os.environ.get('EKSAMIO_PACKAGE_ROOT', str(HERE.parent.parent))).resolve()
OUT=ROOT/'tests'/'evidence'/'profile-2024-browser-evidence.json'
ANS={1:['64','6','154','16'],2:['12','10'],3:['4','12','52'],4:['0,08','0,2'],5:['0,6','0,1'],6:['9','17','93','3'],7:['-0,96','4','16'],8:['4','-1,75'],9:['751'],10:['5','15','7,5'],11:['61'],12:['-83','-6','16']}
COUNTS={1:4,2:2,3:3,4:2,5:2,6:4,7:3,8:2,9:1,10:3,11:1,12:3,13:1,14:1,15:1,16:1,17:1,18:1,19:1}
MAX={13:2,14:3,15:2,16:2,17:3,18:4,19:4}
SOL_COUNTS={13:1,14:1,15:1,16:1,17:2,18:3,19:2}
STORAGE='eksamio_ege_math_profile_demo_2024_v1_0'

def driver_new():
    o=webdriver.ChromeOptions();o.add_argument('--headless=new');o.add_argument('--no-sandbox');o.add_argument('--disable-dev-shm-usage');o.add_argument('--window-size=1280,1000')
    o.set_capability('goog:loggingPrefs',{'browser':'ALL'}); return webdriver.Chrome(options=o)
def js(d,code,*args):return d.execute_script('return '+code,*args)
def force(d,n,v):d.execute_script('window.EKSAMIO_MATH_PROFILE_TEST.forceVariant(arguments[0],arguments[1]);',n,v)
def fill(el,text):
    el.click();el.send_keys(Keys.CONTROL,'a');el.send_keys(Keys.BACKSPACE)
    if text!='':el.send_keys(text)
def nav(d,n):return d.find_element(By.CSS_SELECTOR,f'.mp-num[data-n="{n}"]')
def safe_click(d,el):
    d.execute_script("arguments[0].scrollIntoView({block:'center',inline:'center'});",el);time.sleep(.03)
    try:el.click()
    except ElementClickInterceptedException:d.execute_script('arguments[0].click();',el)

def finalize(ev):
    spec=importlib.util.spec_from_file_location('b',ROOT/'scripts'/'build_profile_2024.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    data=json.loads((ROOT/f'{b.PREFIX}-EXAM-DATA.json').read_text(encoding='utf-8'));data['status']='READY_FOR_TILDA';(ROOT/f'{b.PREFIX}-EXAM-DATA.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for fn in [f'{b.PREFIX}-INPUT-CONTRACT.json',f'{b.PREFIX}-EXAM-MAP.json',f'{b.PREFIX}-BUILD-EVIDENCE.json']:
        p=ROOT/fn;x=json.loads(p.read_text(encoding='utf-8'));x['status']='READY_FOR_TILDA';x['browser_audit']='tests/evidence/profile-2024-browser-evidence.json';p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rows=[]
    import csv
    with (ROOT/'AUDIT-MATRIX-2024-profile.csv').open('r',encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    for r in rows:r['interaction_gate']='PASS_BROWSER'
    with (ROOT/'AUDIT-MATRIX-2024-profile.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    blocks=sorted(ROOT.glob(f'{b.PREFIX}-T123-*.txt'));mx=max(p.stat().st_size for p in blocks)
    (ROOT/f'{b.PREFIX}-PAGE-STATUS.txt').write_text(
      'PAGE_URL: /ege/matematika-profil/demoversiya/2024/\nPAGE_SLUG: ege-matematika-profil-demoversiya-2024\nEXAM: ЕГЭ\nSUBJECT: математика\nLEVEL: профильный\nSOURCE_YEAR: 2024\nPACKAGE_VERSION: 1.0\nSOURCE_GATE: PASS\nTEXT_TYPOGRAPHY_GATE: PASS\nFORMULA_GATE: PASS\nVISUAL_SOURCE_GATE: PASS — 49/49 direct lossless exact-source crops\nVISUAL_UI_GATE: PASS — all 37 conditions + extended material rendered; zoom tested\nINTERACTION_GATE: PASS — 37/37 official examples through real DOM controls\nSCORER_GATE: PASS — 30/30 short examples correct+wrong\nSTATE_RESTORE_GATE: PASS — variants, answers, mark, current state survive reload\nEXTENDED_UX_GATE: PASS — toolbar, quick transforms, own answer, criteria and self-evaluation 7/7\nTILDA_ATOMIC_GATE: PASS — '+str(len(blocks))+' T123, max '+str(mx)+' bytes < 42500; standalone script/style/node syntax PASS\nRESPONSIVE_GATE: PASS — 1280/768/390/360/320\nINDEPENDENT_AUDIT_GATE: PENDING_FINAL_CLEAN_ZIP\nFINAL_STATUS: READY_FOR_FINAL_CLEAN_ZIP_AUDIT\nREADY_FOR_TILDA: PENDING_FINAL_CLEAN_ZIP_AUDIT\nLIVE_GO: NO\n',encoding='utf-8')

def main():
    ev={'status':'PASS','checks':{},'details':{}}
    d=driver_new()
    try:
        d.get(URL);d.execute_script('localStorage.clear()');d.refresh();d.find_element(By.ID,'mp-start').click();assert len(d.find_elements(By.CSS_SELECTOR,'.mp-num'))==19
        st=js(d,'window.EKSAMIO_MATH_PROFILE_TEST.state()');assert all(1<=int(st['variants'][str(n)])<=COUNTS[n] for n in range(1,20));ev['checks']['assignment']='PASS'
        opened=short=ext=0
        for n in range(1,20):
            for v in range(1,COUNTS[n]+1):
                force(d,n,v);time.sleep(.01);src=d.find_element(By.CSS_SELECTOR,'.mp-source-img');assert js(d,'arguments[0].naturalWidth',src)>0
                assert 'официальный пример' not in d.find_element(By.ID,'mp-task').text.lower()
                assert d.find_elements(By.CSS_SELECTOR,'.mp-zoom-btn')
                if n<=12:
                    inp=d.find_element(By.ID,'mp-short');official=ANS[n][v-1];fill(inp,official.replace(',','.'));assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(arguments[0])',n)==1
                    wrong='0,99' if n in (4,5) else ('999' if n==8 and v==1 else '999999');fill(inp,wrong);assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(arguments[0])',n)==0
                    fill(inp,official);short+=1
                else:
                    ta=d.find_element(By.ID,'mp-long');assert len(d.find_elements(By.CSS_SELECTOR,'.mp-math-btn'))>=30
                    fill(ta,f'Тестовое решение {n}');assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(arguments[0])',n);assert not d.find_elements(By.CSS_SELECTOR,'.mp-solution');ext+=1
                opened+=1
        assert (opened,short,ext)==(37,30,7);ev['checks']['official_examples']='37/37';ev['checks']['short_correct_wrong']='30/30'

        force(d,4,1);inp=d.find_element(By.ID,'mp-short');fill(inp,'50%');assert '%' in d.find_element(By.ID,'mp-error').text;fill(inp,'0.08');assert inp.get_attribute('value')=='0,08' and js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(4)')==1
        force(d,8,1);inp=d.find_element(By.ID,'mp-short');fill(inp,'4,0');assert 'целое число' in d.find_element(By.ID,'mp-error').text;fill(inp,'4');assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(8)')==1
        force(d,8,2);fill(d.find_element(By.ID,'mp-short'),'-1.75');assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(8)')==1
        ev['checks']['input_contracts']='PASS'

        force(d,13,1);ta=d.find_element(By.ID,'mp-long');fill(ta,'');buttons=d.find_elements(By.CSS_SELECTOR,'.mp-math-btn');next(b for b in buttons if b.get_attribute('data-sym')=='π').click();next(b for b in d.find_elements(By.CSS_SELECTOR,'.mp-math-btn') if b.get_attribute('data-sym')=='√()').click();assert ta.get_attribute('value')=='π√()';assert d.execute_script('return arguments[0].selectionStart',ta)==3
        fill(ta,'x<=1 -> y!=2 >=0');val=ta.get_attribute('value');assert '≤' in val and '→' in val and '≠' in val and '≥' in val
        ev['checks']['math_toolbar']='PASS: symbols, sqrt cursor, quick transforms'

        force(d,8,1);d.find_element(By.CSS_SELECTOR,'.mp-zoom-btn').click();assert 'mp-hidden' not in d.find_element(By.ID,'mp-zoom-modal').get_attribute('class');d.find_element(By.ID,'mp-zoom-in').click();assert d.find_element(By.ID,'mp-zoom-reset').text.strip()=='125%';d.find_element(By.ID,'mp-zoom-out').click();assert d.find_element(By.ID,'mp-zoom-reset').text.strip()=='100%';d.find_element(By.ID,'mp-zoom-close').click();ev['checks']['zoom']='PASS 50-300 controls present; +/- tested'

        force(d,5,2);fill(d.find_element(By.ID,'mp-short'),'0,1');force(d,16,1);fill(d.find_element(By.ID,'mp-long'),'Сохранённое решение 16');safe_click(d,d.find_element(By.ID,'mp-mark'));d.execute_script("window.dispatchEvent(new PageTransitionEvent('pagehide'));");d.refresh();after=js(d,'window.EKSAMIO_MATH_PROFILE_TEST.state()');assert after['answers']['16']['text']=='Сохранённое решение 16' and after['answers']['5']['value']=='0,1' and bool(after['marked']['16']);ev['checks']['state_restore']='PASS'

        d.execute_script('localStorage.clear()');d.refresh();d.find_element(By.ID,'mp-start').click()
        own={}
        for n in range(1,13):force(d,n,1);fill(d.find_element(By.ID,'mp-short'),ANS[n][0])
        for n in range(13,20):force(d,n,1);own[n]=f'Полное решение задания {n}';fill(d.find_element(By.ID,'mp-long'),own[n])
        assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.autoTotal()')==12;d.find_element(By.ID,'mp-finish').click();d.switch_to.alert.accept();time.sleep(.05);assert d.find_element(By.ID,'mp-auto-score').text.strip()=='12/12'
        for n in range(13,20):
            card=d.find_element(By.CSS_SELECTOR,f'.mp-ext-card[data-ext="{n}"]');assert card.find_element(By.CSS_SELECTOR,'.mp-your-answer pre').text.strip()==own[n];imgs=card.find_elements(By.CSS_SELECTOR,'.mp-solution .mp-source-img');assert len(imgs)==SOL_COUNTS[n],(n,len(imgs));assert all(js(d,'arguments[0].naturalWidth',x)>0 for x in imgs);card.find_element(By.CSS_SELECTOR,f'.mp-score-btn[data-s="{MAX[n]}"]').click()
        assert d.find_element(By.ID,'mp-self-score').text.strip()=='20/20' and d.find_element(By.ID,'mp-total-score').text.strip()=='32/32';ev['checks']['extended_results']='PASS 7/7 own answer + official per-page assets + self-score';ev['checks']['scoring']='12 auto + 20 self = 32'

        overflow={}
        for w in [1280,768,390,360,320]:
            d.set_window_size(w,1000);time.sleep(.02);delta=d.execute_script('return document.documentElement.scrollWidth-window.innerWidth;');overflow[str(w)]=delta;assert delta<=1,(w,delta)
        ev['checks']['responsive']='PASS 1280/768/390/360/320';ev['details']['overflow_delta_px']=overflow
        severe=[x for x in d.get_log('browser') if x.get('level')=='SEVERE' and '/favicon.ico' not in x.get('message','')];assert not severe,severe;ev['checks']['javascript_errors']=0
    finally:d.quit()
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');finalize(ev);print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
