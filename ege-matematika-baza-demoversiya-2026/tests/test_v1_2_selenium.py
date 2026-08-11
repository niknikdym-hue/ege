#!/usr/bin/env python3
import json
import os
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

URL=os.environ.get('EKSAMIO_PREVIEW_URL','http://127.0.0.1:8765/ege-matematika-baza-demoversiya-2026-PREVIEW.html')
OUT=Path(os.environ.get('EKSAMIO_EVIDENCE_OUT','tests/evidence/v1.2-selenium-regression-evidence.json'))


def make_driver():
    options=webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,900')
    options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
    return webdriver.Chrome(options=options)


def js(driver,expr,*args):
    return driver.execute_script('return ('+expr+');',*args)


def set_variant(driver,n,k):
    driver.execute_script('window.EKSAMIO_MATH_BASE_TEST.setVariant(arguments[0],arguments[1]);',n,k)


def set_current(driver,n):
    driver.execute_script('window.EKSAMIO_MATH_BASE_TEST.setCurrent(arguments[0]);',n)


def meta(driver,n):
    return driver.execute_script('const v=window.EKSAMIO_MATH_BASE_TEST.variantFor(arguments[0]); return {variant:v.variant,control:v.control,forms:v.canonical_forms,order_ignored:!!v.order_ignored};',n)


def fill_input(el,value):
    el.clear()
    el.send_keys(value)


def fill_current_correct(driver,n):
    m=meta(driver,n)
    code=str(m['forms'][0])
    ctl=m['control']
    if ctl=='numeric_input':
        fill_input(driver.find_element(By.ID,'mb-short'),code)
    elif ctl=='matching_selects_4':
        assert len(code)==4,(n,m,code)
        for i,ch in enumerate(code):
            Select(driver.find_element(By.CSS_SELECTOR,f'.mb-select[data-pos="{i}"]')).select_by_value(ch)
    elif ctl=='checkboxes':
        for ch in code:
            driver.find_element(By.CSS_SELECTOR,f'input[data-choice="{ch}"]').click()
    elif ctl=='row_checkboxes':
        for ch in code:
            driver.find_element(By.CSS_SELECTOR,f'input[data-row="{ch}"]').click()
    else:
        raise AssertionError(f'Unknown control {ctl}')
    assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.isAnswered(arguments[0])',n),(n,m,code)
    assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.score(arguments[0])',n)==1,(n,m,code)
    return m


def main():
    ev={'status':'PASS','package_version':'1.2','checks':{},'details':{}}
    driver=make_driver()
    try:
        driver.get(URL)
        driver.execute_script('localStorage.clear();')
        driver.refresh()
        driver.find_element(By.ID,'mb-start').click()

        variants=driver.execute_script('return window.EKSAMIO_MATH_BASE_TEST.tasks.map(t=>({n:t.number,variants:t.variants.map(v=>v.variant)}));')
        passed=0
        for item in variants:
            for k in item['variants']:
                set_variant(driver,item['n'],k)
                fill_current_correct(driver,item['n'])
                passed+=1
        assert passed==70
        ev['checks']['official_examples_real_controls']='70/70'

        set_variant(driver,1,3)
        inp=driver.find_element(By.ID,'mb-short')
        fill_input(inp,'11.2')
        assert inp.get_attribute('value')=='11,2',inp.get_attribute('value')
        st=js(driver,'window.EKSAMIO_MATH_BASE_TEST.state().answers[1]')
        assert st=={'value':'11,2','valid':False},st
        assert not js(driver,'window.EKSAMIO_MATH_BASE_TEST.isAnswered(1)')
        assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.score(1)')==0
        assert 'целый ответ' in driver.find_element(By.ID,'mb-input-error').text
        assert 'Введите целое число.' in driver.find_element(By.CSS_SELECTOR,'.mb-answerbox .mb-answer-hint').text
        set_current(driver,2);set_current(driver,1)
        assert driver.find_element(By.ID,'mb-short').get_attribute('value')=='11,2'
        driver.refresh()
        assert driver.find_element(By.ID,'mb-short').get_attribute('value')=='11,2'
        assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.state().answers[1].value')=='11,2'
        ev['checks']['task1_decimal_wrong_persists']='PASS: 11.2 → 11,2; explicit integer-format error; navigation/reload preserves raw value; scorer 0/1'

        inp=driver.find_element(By.ID,'mb-short')
        fill_input(inp,'12')
        assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.score(1)')==1
        ev['checks']['task1_correct_integer']='PASS: 12 scores 1/1'

        set_variant(driver,5,1)
        inp=driver.find_element(By.ID,'mb-short')
        fill_input(inp,'0.25')
        assert inp.get_attribute('value')=='0,25'
        assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.score(5)')==1
        driver.refresh()
        assert driver.find_element(By.ID,'mb-short').get_attribute('value')=='0,25'
        ev['checks']['decimal_dot_normalization']='PASS: 0.25 → 0,25 → reload 0,25'

        set_variant(driver,3,3)
        inp=driver.find_element(By.ID,'mb-short')
        fill_input(inp,'12 200')
        st=js(driver,'window.EKSAMIO_MATH_BASE_TEST.state().answers[3]')
        assert st=={'value':'12 200','valid':False},st
        assert inp.get_attribute('value')=='12 200'
        assert 'is-invalid' in inp.get_attribute('class').split()
        assert not js(driver,'window.EKSAMIO_MATH_BASE_TEST.isAnswered(3)')
        driver.refresh()
        inp=driver.find_element(By.ID,'mb-short')
        assert inp.get_attribute('value')=='12 200'
        assert 'is-invalid' in inp.get_attribute('class').split()
        ev['checks']['invalid_space_preserved']='PASS: 12 200 remains raw invalid input and never becomes 12200'

        set_variant(driver,7,2)
        text=driver.find_element(By.ID,'mb-task').text
        assert 'Н·м' in text and 'Нꞏм' not in text,text
        ev['checks']['task7_unit_typography']='PASS: Н·м'

        overflow={}
        for w in [1280,768,390,360,320]:
            driver.set_window_size(w,900)
            time.sleep(.05)
            delta=driver.execute_script('return document.documentElement.scrollWidth-window.innerWidth;')
            overflow[str(w)]=delta
            assert delta<=1,(w,delta)
        ev['checks']['widths']='PASS: 1280, 768, 390, 360, 320'
        ev['details']['overflow_delta_px']=overflow

        driver.set_window_size(1280,900)
        driver.execute_script('localStorage.clear();')
        driver.refresh()
        driver.find_element(By.ID,'mb-start').click()
        for n in range(1,22):
            set_current(driver,n)
            fill_current_correct(driver,n)
        assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.total()')==21
        assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.answeredCount()')==21
        driver.execute_script('window.EKSAMIO_MATH_BASE_TEST.finish();')
        assert driver.find_element(By.ID,'mb-score').text.strip()=='21/21'
        assert driver.find_element(By.ID,'mb-answered').text.strip()=='21/21'
        ev['checks']['full_correct_attempt']='21/21'
        ev['checks']['state_restore']='PASS'

        raw_severe=[x for x in driver.get_log('browser') if x.get('level')=='SEVERE']
        ignored=[x for x in raw_severe if '/favicon.ico' in x.get('message','') and '404' in x.get('message','')]
        severe=[x for x in raw_severe if x not in ignored]
        ev['checks']['javascript_errors']=len(severe)
        ev['details']['browser_severe_logs']=severe
        ev['details']['ignored_favicon_404']=len(ignored)
        assert not severe,severe
    finally:
        driver.quit()

    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(ev,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(ev,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
