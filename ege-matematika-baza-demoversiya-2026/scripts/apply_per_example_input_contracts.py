#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREFIX='ege-matematika-baza-demoversiya-2026'

runtime_path=ROOT/'templates'/'runtime.js'
runtime=runtime_path.read_text(encoding='utf-8')
runtime=runtime.replace("const NUMERIC_FORMATS={1:'integer'};", "const INPUT_CONTRACTS=__INPUT_CONTRACTS__;" )

new_numeric=r'''function inputContract(v){const key=String(state.current)+'-'+String(v.variant);const c=INPUT_CONTRACTS[key];if(!c)throw new Error('Missing input contract '+key);return c}
function numericError(c,reason){
if(reason==='space')return 'Пробелы в поле ответа не используются. Введите значение без пробелов.';
if(reason==='plus')return 'Знак «+» в поле ответа не нужен. Введите значение без него.';
if(reason==='percent')return c.percent_error||'Знак «%» в поле ответа не нужен. Введите только числовое значение.';
if(reason==='unit')return c.unit_error||'Буквы и единицы измерения в поле ответа не вводятся. Введите только числовое значение.';
if(reason==='fraction')return 'Обыкновенную дробь через «/» вводить нельзя. Запишите ответ целым числом или конечной десятичной дробью.';
if(reason==='integer')return 'Для этого примера нужно ввести целое число. Запятая, точка и дробная часть не используются.';
if(reason==='digit_count')return `Для этого примера нужно ввести число из ${c.exact_digits} цифр.`;
if(reason==='sign')return 'Знак «−» здесь не используется. Введите неотрицательное значение.';
if(reason==='incomplete_decimal')return 'После десятичного разделителя укажите цифры.';
if(reason==='separator')return 'В числе может быть только один десятичный разделитель.';
return c.mode==='digits'?'Введите только требуемое количество цифр без дополнительных символов.':'Введите только числовое значение без дополнительных символов.'
}
function numericPanel(v){const c=inputContract(v),a=answerObj(state.current)||{value:'',valid:false},value=String(a.value||''),chk=validateNumeric(v,value),invalid=!chk.empty&&!chk.valid,inputMode=c.mode==='number'?'decimal':'numeric';return `<div class="mb-answerbox"><label class="mb-answer-title" for="mb-short">Ответ</label><div class="mb-answer-hint">${esc(c.hint)}</div><input class="mb-input ${invalid?'is-invalid':''}" id="mb-short" inputmode="${inputMode}" autocomplete="off" value="${esc(value)}" aria-describedby="mb-input-error"><div class="mb-error" id="mb-input-error" aria-live="polite">${invalid?esc(numericError(c,chk.reason)):''}</div></div>`}
'''
runtime,n=re.subn(r"function numericError\([^\n]*\nfunction numericPanel\([^\n]*\n",lambda m:new_numeric,runtime,count=1)
if n!=1: raise SystemExit('numericError/numericPanel patch failed')

new_validate=r'''function validateNumeric(v,value){
const c=inputContract(v),raw=String(value==null?'':value);
if(raw==='')return {empty:true,valid:false,reason:null,normalized:''};
if(/\s/.test(raw))return {empty:false,valid:false,reason:'space',normalized:raw};
if(raw.includes('+'))return {empty:false,valid:false,reason:'plus',normalized:raw};
if(raw.includes('%'))return {empty:false,valid:false,reason:'percent',normalized:raw};
if(/[A-Za-zА-Яа-яЁё°²³]/.test(raw))return {empty:false,valid:false,reason:'unit',normalized:raw};
if(raw.includes('/'))return {empty:false,valid:false,reason:'fraction',normalized:raw};
if(c.mode==='integer'||c.mode==='digits'){
if(/[.,]/.test(raw))return {empty:false,valid:false,reason:'integer',normalized:raw};
if(raw.startsWith('-')&&!c.allow_negative)return {empty:false,valid:false,reason:'sign',normalized:raw};
if(!/^-?\d+$/.test(raw))return {empty:false,valid:false,reason:'format',normalized:raw};
if(c.mode==='digits'&&c.exact_digits&&raw.replace(/^-/,'').length!==Number(c.exact_digits))return {empty:false,valid:false,reason:'digit_count',normalized:raw};
return {empty:false,valid:true,reason:null,normalized:raw};
}
if(c.mode==='number'){
let normalized=raw.replace('−','-');
if(normalized.startsWith('-')&&!c.allow_negative)return {empty:false,valid:false,reason:'sign',normalized:raw};
const seps=(normalized.match(/[.,]/g)||[]).length;
if(seps>1)return {empty:false,valid:false,reason:'separator',normalized:raw};
if(/[.,]$/.test(normalized))return {empty:false,valid:false,reason:'incomplete_decimal',normalized:normalized.replace('.',',')};
if(!/^-?\d+(?:[.,]\d+)?$/.test(normalized))return {empty:false,valid:false,reason:'format',normalized:raw};
normalized=normalized.replace('.',',');
return {empty:false,valid:true,reason:null,normalized};
}
return {empty:false,valid:false,reason:'format',normalized:raw};
}
'''
runtime,n=re.subn(r"function validateNumeric\(v,value\)\{.*?\}\nfunction updateCode",lambda m:new_validate+'function updateCode',runtime,count=1,flags=re.S)
if n!=1: raise SystemExit('validateNumeric patch failed')

new_bind=r'''function bindNumeric(v){const c=inputContract(v),inp=$('#mb-short'),err=$('#mb-input-error');inp.oninput=()=>{let raw=inp.value;const chk=validateNumeric(v,raw);let stored=raw;if(c.mode==='number'&&chk.normalized!==raw&&(chk.valid||chk.reason==='incomplete_decimal')){stored=chk.normalized;inp.value=stored}const finalChk=validateNumeric(v,stored);inp.classList.toggle('is-invalid',!finalChk.empty&&!finalChk.valid);err.textContent=finalChk.empty||finalChk.valid?'':numericError(c,finalChk.reason);state.answers[state.current]={value:stored,valid:finalChk.valid};save();renderGrid()}}
'''
runtime,n=re.subn(r"function bindNumeric\(v\)\{.*?\}\nfunction disableMatchingDuplicates",lambda m:new_bind+'function disableMatchingDuplicates',runtime,count=1,flags=re.S)
if n!=1: raise SystemExit('bindNumeric patch failed')
runtime=runtime.replace('validateNumeric,fixTypography,startNew', 'validateNumeric,inputContract,fixTypography,startNew')
runtime_path.write_text(runtime,encoding='utf-8')

build_path=ROOT/'scripts'/'build_demo_release.py'
build=build_path.read_text(encoding='utf-8')
build=build.replace("CONTENT_VERSION='2026.3'","CONTENT_VERSION='2026.4'")
build=build.replace("runtime=(ROOT/'templates'/'runtime.js').read_text(encoding='utf-8')\n    blocks=[shell]", "runtime=(ROOT/'templates'/'runtime.js').read_text(encoding='utf-8')\n    input_contracts=load_json(f'{PREFIX}-INPUT-CONTRACT.json')['contracts']\n    runtime=runtime.replace('__INPUT_CONTRACTS__',json.dumps(input_contracts,ensure_ascii=False,separators=(',',':')))\n    if '__INPUT_CONTRACTS__' in runtime:raise RuntimeError('Input-contract injection failed')\n    blocks=[shell]")
build=build.replace("'numeric_input':'numeric syntax is validated independently from answer correctness; dot normalizes to comma; raw invalid input is preserved'", "'numeric_input':'each free-input official example has an explicit input contract; format validation never infers correctness from canonical answers; decimal-dot normalization is used only where decimal input is permitted; raw invalid input is preserved'")
build=build.replace("'task 1 integer-answer hint','task 1 rejects non-integer numeric format with explicit student feedback'", "'58 per-example free-input contracts','format-specific student feedback without answer-correctness inference'")
build_path.write_text(build,encoding='utf-8')

old_test=ROOT/'tests'/'test_v1_2_selenium.py'
t=old_test.read_text(encoding='utf-8')
t=t.replace("assert inp.get_attribute('value')=='11,2',inp.get_attribute('value')", "assert inp.get_attribute('value')=='11.2',inp.get_attribute('value')")
t=t.replace("assert st=={'value':'11,2','valid':False},st", "assert st=={'value':'11.2','valid':False},st")
t=t.replace("assert 'целый ответ' in driver.find_element(By.ID,'mb-input-error').text", "assert 'целое число' in driver.find_element(By.ID,'mb-input-error').text")
t=t.replace("assert 'Введите целое число.' in driver.find_element(By.CSS_SELECTOR,'.mb-answerbox .mb-answer-hint').text", "assert 'количество пачек целым числом' in driver.find_element(By.CSS_SELECTOR,'.mb-answerbox .mb-answer-hint').text")
t=t.replace("assert driver.find_element(By.ID,'mb-short').get_attribute('value')=='11,2'", "assert driver.find_element(By.ID,'mb-short').get_attribute('value')=='11.2'")
t=t.replace("assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.state().answers[1].value')=='11,2'", "assert js(driver,'window.EKSAMIO_MATH_BASE_TEST.state().answers[1].value')=='11.2'")
t=t.replace("'PASS: 11.2 → 11,2; explicit integer-format error; navigation/reload preserves raw value; scorer 0/1'", "'PASS: integer-only example preserves 11.2 as raw invalid input; explicit whole-number feedback; navigation/reload preserves raw value; scorer 0/1'")
old_test.write_text(t,encoding='utf-8')

print('patched runtime, build and legacy regression test')
