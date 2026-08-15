#!/usr/bin/env python3
from pathlib import Path
import sys,subprocess,time,urllib.request,os
root=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent)
port=8765
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1'],cwd=root,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
 for _ in range(30):
  try: urllib.request.urlopen(f'http://127.0.0.1:{port}/ege-russkiy-demoversiya-PREVIEW.html',timeout=.3);break
  except: time.sleep(.1)
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox']); page=b.new_page(viewport={'width':1440,'height':1000}); html=(root/'ege-russkiy-demoversiya-PREVIEW.html').read_text(encoding='utf-8'); page.set_content(html, wait_until='load');
  assert page.locator('#edemo-start').is_visible(); page.click('#edemo-start');
  assert page.evaluate("window.__edemoRussian2022v100.scoreTask({number:8,kind:'ordered_sequence',answer:'43827',maxScore:5,altAnswers:[]},['4','3','8','2','7'])")==5
  assert page.evaluate("window.__edemoRussian2022v100.scoreTask({number:8,kind:'ordered_sequence',answer:'43827',maxScore:5,altAnswers:[]},['4','3','8','2','6'])")==4
  assert page.evaluate("window.__edemoRussian2022v100.scoreTask({number:26,kind:'ordered_sequence',answer:'2519',maxScore:4,altAnswers:[]},['2','5','1','8'])")==3
  assert 'ЗАДАНИЕ 1 ИЗ 27' in page.locator('#edemo-task-stage').inner_text().upper();
  # task 8 positional controls
  page.click('#edemo-reset-start') if page.locator('#edemo-reset-start').is_visible() else None
  page.set_content(html, wait_until='load'); page.click('#edemo-start');
  page.locator('.edemo-nav-btn').nth(7).click(); assert page.locator('[data-match-index]').count()==5
  # task26 positional controls
  page.locator('.edemo-nav-btn').nth(25).click(); assert page.locator('[data-match-index]').count()==4
  # essay textarea and mobile overflow
  page.locator('.edemo-nav-btn').nth(26).click(); assert page.locator('#edemo-answer-input').evaluate('(e)=>e.tagName')=='TEXTAREA'
  m=b.new_page(viewport={'width':390,'height':844});m.set_content(html, wait_until='load');assert m.evaluate('document.documentElement.scrollWidth<=document.documentElement.clientWidth+2')
  b.close()
 print('PASS browser: start, task8/26 controls, essay, mobile overflow')
finally:
 srv.terminate(); srv.wait(timeout=3)
