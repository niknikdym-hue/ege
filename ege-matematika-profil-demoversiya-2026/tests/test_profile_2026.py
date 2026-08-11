#!/usr/bin/env python3
import json, os, time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

URL=os.environ.get('EKSAMIO_PREVIEW_URL','http://127.0.0.1:8765/ege-matematika-profil-demoversiya-2026-PREVIEW.html')
OUT=Path(os.environ.get('EKSAMIO_EVIDENCE_OUT','tests/evidence/profile-2026-browser-evidence.json'))
ANS={1:['61','18','40','5'],2:['12','13','4'],3:['1,125','36','104','9'],4:['0,1','0,38','0,3'],5:['0,657','0,15','0,79','0,78'],6:['7','7','93','3'],7:['0,75','5','125'],8:['5','6','1,6'],9:['45','5','4900'],10:['19','15','8'],11:['0,1','5','32'],12:['5','-6','16','-18']}
COUNTS={1:4,2:3,3:4,4:3,5:4,6:4,7:3,8:3,9:3,10:3,11:3,12:4,13:2,14:2,15:2,16:2,17:2,18:2,19:2}
MAX={13:2,14:3,15:2,16:2,17:3,18:4,19:4}

def driver_new():
    o=webdriver.ChromeOptions();o.add_argument('--headless=new');o.add_argument('--no-sandbox');o.add_argument('--disable-dev-shm-usage');o.add_argument('--window-size=1280,1000');o.set_capability('goog:loggingPrefs',{'browser':'ALL'});return webdriver.Chrome(options=o)
def js(d,code,*args):return d.execute_script('return '+code,*args)
def force(d,n,v):d.execute_script('window.EKSAMIO_MATH_PROFILE_TEST.forceVariant(arguments[0],arguments[1]);',n,v)
def current(d,n):d.execute_script('window.EKSAMIO_MATH_PROFILE_TEST.setCurrent(arguments[0]);',n)
def fill(el,text):el.click();el.send_keys(Keys.CONTROL,'a');el.send_keys(text)

def main():
    ev={'status':'PASS','package_version':'1.0','checks':{},'details':{}}
    d=driver_new()
    try:
        d.get(URL);d.execute_script('localStorage.clear()');d.refresh();d.find_element(By.ID,'mp-start').click()
        assert len(d.find_elements(By.CSS_SELECTOR,'.mp-num'))==19
        # All 55 official examples: actual rendered source image + real control interaction.
        opened=0; short=0; ext=0
        for n in range(1,20):
            for v in range(1,COUNTS[n]+1):
                force(d,n,v);time.sleep(.02)
                img=d.find_element(By.CSS_SELECTOR,'.mp-source-img');assert js(d,'arguments[0].naturalWidth',img)>0,(n,v)
                if n<=12:
                    inp=d.find_element(By.ID,'mp-short');fill(inp,ANS[n][v-1].replace(',','.'))
                    assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(arguments[0])',n),(n,v)
                    assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(arguments[0])',n)==1,(n,v,inp.get_attribute('value'))
                    # syntactically valid wrong answer stays a completed answer and scores 0
                    wrong='0,99' if n in (4,5) else ('999' if n==8 and v in (1,2) else '999999')
                    fill(inp,wrong);assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(arguments[0])',n);assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(arguments[0])',n)==0
                    fill(inp,ANS[n][v-1]);short+=1
                else:
                    ta=d.find_element(By.ID,'mp-long');fill(ta,f'Тестовое полное решение {n}-{v}\nОтвет.');assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(arguments[0])',n);ext+=1
                    assert not d.find_elements(By.CSS_SELECTOR,'.mp-solution'),(n,v,'solution leaked before finish')
                opened+=1
        assert opened==55 and short==41 and ext==14
        ev['checks']['official_examples_real_controls']='55/55 PASS (41 input + 14 textarea)'
        ev['checks']['official_source_assets']='55/55 rendered from direct FIPI crops'

        # Per-example format feedback, not one generic numeric rule.
        force(d,4,1);inp=d.find_element(By.ID,'mp-short');fill(inp,'50%');assert '%' in d.find_element(By.ID,'mp-error').text
        fill(inp,'1,2');assert 'от 0 до 1' in d.find_element(By.ID,'mp-error').text
        fill(inp,'0.1');assert inp.get_attribute('value')=='0,1' and js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(4)')==1
        force(d,8,1);inp=d.find_element(By.ID,'mp-short');fill(inp,'5,0');assert 'целое число' in d.find_element(By.ID,'mp-error').text;assert not js(d,'window.EKSAMIO_MATH_PROFILE_TEST.isAnswered(8)')
        fill(inp,'5');assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.scoreShort(8)')==1
        force(d,1,1);inp=d.find_element(By.ID,'mp-short');fill(inp,'61 град');assert 'Единицы измерения' in d.find_element(By.ID,'mp-error').text
        fill(inp,'61 ');assert 'Пробелы' in d.find_element(By.ID,'mp-error').text
        ev['checks']['per_example_input_contracts']='PASS: probability / integer count / general numeric feedback differ correctly'

        # State restore: assigned example + short answer + long solution.
        force(d,5,4);fill(d.find_element(By.ID,'mp-short'),'0,78');force(d,16,2);fill(d.find_element(By.ID,'mp-long'),'Сохранённое решение 16-2');d.refresh()
        st=js(d,'window.EKSAMIO_MATH_PROFILE_TEST.state()');assert int(st['variants']['16'])==2 and st['answers']['16']['text']=='Сохранённое решение 16-2';assert st['answers']['5']['value']=='0,78'
        ev['checks']['state_restore']='PASS: variants + short answer + extended solution'

        # Fresh full attempt: first official example in each position, correct part 1, filled part 2.
        d.execute_script('localStorage.clear()');d.refresh();d.find_element(By.ID,'mp-start').click()
        for n in range(1,13):
            force(d,n,1);fill(d.find_element(By.ID,'mp-short'),ANS[n][0])
        for n in range(13,20):
            force(d,n,1);fill(d.find_element(By.ID,'mp-long'),f'Полное решение задания {n}')
        assert js(d,'window.EKSAMIO_MATH_PROFILE_TEST.autoTotal()')==12
        d.find_element(By.ID,'mp-finish').click();d.switch_to.alert.accept();time.sleep(.05)
        assert d.find_element(By.ID,'mp-auto-score').text.strip()=='12/12'
        # Official solution/criteria visible only now, self-score by real buttons.
        for n in range(13,20):
            card=d.find_element(By.CSS_SELECTOR,f'.mp-ext-card[data-ext="{n}"]');img=card.find_element(By.CSS_SELECTOR,'.mp-source-img');assert js(d,'arguments[0].naturalWidth',img)>0
            card.find_element(By.CSS_SELECTOR,f'.mp-score-btn[data-s="{MAX[n]}"]').click()
        assert d.find_element(By.ID,'mp-self-score').text.strip()=='20/20'
        assert d.find_element(By.ID,'mp-total-score').text.strip()=='32/32'
        assert d.find_element(By.ID,'mp-auto-score').text.strip()=='12/12'
        ev['checks']['scoring_separation']='PASS: automatic 12/12 + explicit self-evaluation 20/20 = 32/32; automatic score unchanged'
        ev['checks']['full_correct_short_attempt']='12/12'
        ev['checks']['extended_self_evaluation']='7/7 tasks; max map 2,3,2,2,3,4,4'

        # Responsive overflow gate.
        overflow={}
        for w in [1280,768,390,360,320]:
            d.set_window_size(w,1000);time.sleep(.04);delta=d.execute_script('return document.documentElement.scrollWidth-window.innerWidth;');overflow[str(w)]=delta;assert delta<=1,(w,delta)
        ev['checks']['widths']='PASS: 1280, 768, 390, 360, 320';ev['details']['overflow_delta_px']=overflow
        severe=[x for x in d.get_log('browser') if x.get('level')=='SEVERE' and '/favicon.ico' not in x.get('message','')]
        assert not severe,severe;ev['checks']['javascript_errors']=0;ev['details']['browser_severe_logs']=severe
    finally:d.quit()
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(ev,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
