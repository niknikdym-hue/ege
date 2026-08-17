#!/usr/bin/env python3
from pathlib import Path
from playwright.sync_api import sync_playwright
import shutil
R=Path(__file__).resolve().parent
html=(R/'index.html').read_text(encoding='utf-8')
LS_SHIM="""(()=>{let d={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.prototype.hasOwnProperty.call(d,k)?d[k]:null,setItem:(k,v)=>d[k]=String(v),removeItem:k=>delete d[k],clear:()=>d={},key:i=>Object.keys(d)[i]||null,get length(){return Object.keys(d).length}}});})();"""
CHROME=shutil.which('chromium') or shutil.which('google-chrome') or shutil.which('chromium-browser') or shutil.which('google-chrome-stable')
assert CHROME
with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path=CHROME,args=['--no-sandbox'])
    page=b.new_page(viewport={'width':1280,'height':950})
    page.evaluate(LS_SHIM); page.set_content(html,wait_until='load'); page.evaluate('window.EKSAMIO_MATH_BASE_TEST.startNew()')
    tasks=page.evaluate('window.EKSAMIO_MATH_BASE_TEST.tasks')
    asset_total=0
    for t in tasks:
        for v in t['variants']:
            ids=v.get('asset_ids',[])
            if not ids: continue
            page.evaluate('(x)=>window.EKSAMIO_MATH_BASE_TEST.setVariant(x.n,x.k)',{'n':t['number'],'k':v['variant']})
            buttons=page.locator('.mb-zoom-btn')
            assert buttons.count()==len(ids),(t['number'],v['variant'],buttons.count(),len(ids))
            for i,aid in enumerate(ids):
                btn=buttons.nth(i); assert btn.get_attribute('data-asset-id')==aid
                btn.click(); assert page.locator('#mb-asset-modal').evaluate("e=>e.classList.contains('is-open')")
                src=page.locator('#mb-asset-img').get_attribute('src') or ''
                assert src.startswith('data:image/webp;base64,'),(t['number'],v['variant'],aid)
                assert page.locator('#mb-asset-scale').inner_text()=='100%'
                page.locator('#mb-asset-zoom-in').click(); assert page.locator('#mb-asset-scale').inner_text()=='125%'
                page.locator('#mb-asset-zoom-out').click(); assert page.locator('#mb-asset-scale').inner_text()=='100%'
                page.locator('#mb-asset-zoom-reset').click(); assert page.locator('#mb-asset-scale').inner_text()=='100%'
                page.locator('#mb-asset-close').click(); asset_total+=1
    assert asset_total==41,asset_total
    page.set_viewport_size({'width':390,'height':844})
    page.evaluate('(x)=>window.EKSAMIO_MATH_BASE_TEST.setVariant(x.n,x.k)',{'n':7,'k':1})
    page.locator('.mb-zoom-btn').first.click()
    assert page.locator('#mb-asset-modal').evaluate("e=>e.classList.contains('is-open')")
    page.locator('#mb-asset-zoom-in').click(); page.locator('#mb-asset-zoom-in').click()
    assert page.locator('#mb-asset-scale').inner_text()=='150%'
    (R/'source-diagnostics').mkdir(exist_ok=True)
    page.screenshot(path=str(R/'source-diagnostics/browser-mobile-zoom-task-07.png'),full_page=False)
    page.locator('#mb-asset-close').click()
    overflow=page.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth'); assert overflow<=2,overflow
    print('VISUAL UI ZOOM PASS: 41/41 source assets open; zoom in/out/reset; mobile zoom PASS')
    b.close()
