#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve()
spec=importlib.util.spec_from_file_location('profile2022_v11',HERE.with_name('final_v11.py'))
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
_orig=f.patch_sources

def patch_sources_v12():
    _orig()
    p=f.ROOT/'tests'/'test_profile_2022.py'
    s=p.read_text(encoding='utf-8')
    target="        force(d,4,2);fill(d.find_element(By.ID,'mp-short'),'4');force(d,15,1);fill(d.find_element(By.ID,'mp-long'),'Сохранённое решение 15');safe_click(d,d.find_element(By.ID,'mp-mark'));d.execute_script(\"window.dispatchEvent(new PageTransitionEvent('pagehide'));\");d.refresh();after=js(d,\"JSON.parse(localStorage.getItem(arguments[0]))\",STORAGE);assert after['answers']['15']['text']=='Сохранённое решение 15' and after['answers']['4']['value']=='4' and bool(after['marked']['15']);ev['checks']['state_restore']='PASS'"
    replacement="        # Establish a known unmarked baseline: the all-variant rerender gate intentionally toggles every task once.\n        force(d,15,1)\n        if bool(js(d,\"Boolean(window.EKSAMIO_MATH_PROFILE_TEST.state().marked['15'])\")):safe_click(d,d.find_element(By.ID,'mp-mark'))\n        force(d,4,2);fill(d.find_element(By.ID,'mp-short'),'4');force(d,15,1);fill(d.find_element(By.ID,'mp-long'),'Сохранённое решение 15');safe_click(d,d.find_element(By.ID,'mp-mark'));d.execute_script(\"window.dispatchEvent(new PageTransitionEvent('pagehide'));\");d.refresh();after=js(d,\"JSON.parse(localStorage.getItem(arguments[0]))\",STORAGE);assert after['answers']['15']['text']=='Сохранённое решение 15' and after['answers']['4']['value']=='4' and bool(after['marked']['15']),after;ev['checks']['state_restore']='PASS'"
    if target not in s:raise RuntimeError('state-restore test target missing')
    p.write_text(s.replace(target,replacement,1),encoding='utf-8')
    compile(p.read_text(encoding='utf-8'),str(p),'exec')
    print('STATE RESTORE TEST BASELINE FIX PASS')

f.patch_sources=patch_sources_v12
if __name__=='__main__':f.main()
