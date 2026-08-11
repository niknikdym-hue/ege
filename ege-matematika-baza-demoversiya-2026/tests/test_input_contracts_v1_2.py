#!/usr/bin/env python3
import json, os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By

ROOT=Path(__file__).resolve().parents[1]
URL=os.environ.get('EKSAMIO_PREVIEW_URL','http://127.0.0.1:8765/ege-matematika-baza-demoversiya-2026-PREVIEW.html')
OUT=Path(os.environ.get('EKSAMIO_INPUT_EVIDENCE_OUT','tests/evidence/v1.2-input-contract-evidence.json'))
CONTRACTS=json.loads((ROOT/'ege-matematika-baza-demoversiya-2026-INPUT-CONTRACT.json').read_text(encoding='utf-8'))['contracts']

def driver():
    o=webdriver.ChromeOptions();o.add_argument('--headless=new');o.add_argument('--no-sandbox');o.add_argument('--disable-dev-shm-usage');o.add_argument('--window-size=1280,900')
    return webdriver.Chrome(options=o)

def fill(el,s): el.clear(); el.send_keys(s)

def main():
    d=driver(); evidence={'status':'PASS','contracts':len(CONTRACTS),'checked':0,'cases':{}}
    try:
        d.get(URL);d.execute_script('localStorage.clear()');d.refresh();d.find_element(By.ID,'mb-start').click()
        numeric=d.execute_script("return window.EKSAMIO_MATH_BASE_TEST.tasks.flatMap(t=>t.variants.filter(v=>v.control==='numeric_input').map(v=>String(t.number)+'-'+String(v.variant)));" )
        assert len(numeric)==58, len(numeric)
        assert set(numeric)==set(CONTRACTS), (set(numeric)-set(CONTRACTS),set(CONTRACTS)-set(numeric))
        for key in numeric:
            n,k=map(int,key.split('-')); c=CONTRACTS[key]
            d.execute_script('window.EKSAMIO_MATH_BASE_TEST.setVariant(arguments[0],arguments[1]);',n,k)
            hint=d.find_element(By.CSS_SELECTOR,'.mb-answerbox .mb-answer-hint').text.strip()
            assert hint==c['hint'].strip(),(key,hint,c['hint'])
            inp=d.find_element(By.ID,'mb-short'); err=d.find_element(By.ID,'mb-input-error')
            fill(inp,'12 3'); assert 'Пробелы' in err.text,(key,err.text)
            fill(inp,'+12'); assert '«+»' in err.text,(key,err.text)
            if c['mode']=='number':
                fill(inp,'11.2'); assert inp.get_attribute('value')=='11,2',(key,inp.get_attribute('value')); assert not err.text,(key,err.text)
                fill(inp,'11,'); assert 'После десятичного разделителя' in err.text,(key,err.text)
                fill(inp,'1/2'); assert 'Обыкновенную дробь' in err.text,(key,err.text)
            elif c['mode']=='integer':
                fill(inp,'11,2'); assert 'целое число' in err.text,(key,err.text); assert inp.get_attribute('value')=='11,2'
                fill(inp,'11.2'); assert 'целое число' in err.text,(key,err.text); assert inp.get_attribute('value')=='11.2'
                fill(inp,'11,'); assert 'целое число' in err.text,(key,err.text)
            elif c['mode']=='digits':
                wrong='1'*(int(c['exact_digits'])-1); fill(inp,wrong); assert 'цифр' in err.text,(key,err.text)
                good='1'*int(c['exact_digits']); fill(inp,good); assert not err.text,(key,err.text)
                fill(inp,'11,2'); assert 'целое число' in err.text,(key,err.text)
            else: raise AssertionError((key,c))
            if c.get('percent_error'):
                fill(inp,'30%'); assert err.text==c['percent_error'],(key,err.text,c['percent_error'])
            if c.get('unit_error'):
                fill(inp,'12км'); assert err.text==c['unit_error'],(key,err.text,c['unit_error'])
            evidence['checked']+=1
        # Explicit anti-inference regression inside one position: example 1-2 may accept a decimal-form wrong answer,
        # while example 1-3 rejects the same form because that example asks for a count.
        d.execute_script('window.EKSAMIO_MATH_BASE_TEST.setVariant(1,2)'); inp=d.find_element(By.ID,'mb-short'); fill(inp,'11.2')
        assert d.find_element(By.ID,'mb-input-error').text==''; assert d.execute_script('return window.EKSAMIO_MATH_BASE_TEST.isAnswered(1)') is True
        d.execute_script('window.EKSAMIO_MATH_BASE_TEST.setVariant(1,3)'); inp=d.find_element(By.ID,'mb-short'); fill(inp,'11.2')
        assert 'целое число' in d.find_element(By.ID,'mb-input-error').text; assert d.execute_script('return window.EKSAMIO_MATH_BASE_TEST.isAnswered(1)') is False
        evidence['cases']['task1_variant_specific']='PASS: 1-2 accepts decimal-form numeric input; 1-3 rejects decimal form as count'
    finally: d.quit()
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(evidence,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
