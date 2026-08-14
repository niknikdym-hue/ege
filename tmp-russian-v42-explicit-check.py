from pathlib import Path
import hashlib,re
base=Path('ege-russkiy-demoversiya-2026-v4.2')

# T123-06: typing/saving must not run analysis. Analysis starts only from explicit button in T123-07.
p6=base/'ege-russkiy-demoversiya-T123-06.txt'
s=p6.read_text(encoding='utf-8')
old='''  function runSystemAnalysis(){reviewState=applyAnalysisResult(reviewState,analyzeEssayText(essayForReview()));saveReviewState();}\n  function freezeDemoEssay(){if(reviewState.writingMode!=="demo")return;if(!reviewState.demoEssayFrozen){var value=currentCoreEssay();reviewState.frozenEssay=value===PAPER_MARKER?"":value;reviewState.demoEssayFrozen=true;}if(reviewState.analysisStatus!=="complete")runSystemAnalysis();else saveReviewState();}\n'''
new='''  function runSystemAnalysis(){reviewState=applyAnalysisResult(reviewState,analyzeEssayText(essayForReview()));saveReviewState();}\n  function markAnalysisPending(){reviewState.analysisStatus="pending";reviewState.analysisVersion="";reviewState.confirmedFindings=emptyFindingMap();reviewState.possibleFindings=emptyFindingMap();reviewState.technicalFindings=[];ERROR_CRITERIA.forEach(function(k){delete reviewState.essayScores[k];});}\n  function freezeDemoEssay(){if(reviewState.writingMode!=="demo")return;if(!reviewState.demoEssayFrozen){var value=currentCoreEssay();reviewState.frozenEssay=value===PAPER_MARKER?"":value;reviewState.demoEssayFrozen=true;markAnalysisPending();}saveReviewState();}\n'''
if old not in s: raise SystemExit('freeze anchor missing')
s=s.replace(old,new,1)
old2='''    var transferred=byId("edemo-transferred-essay");if(transferred){if(reviewState.analysisStatus!=="complete")runSystemAnalysis();transferred.addEventListener("input",function(e){reviewState.transferredText=e.target.value;runSystemAnalysis();byId("edemo-transfer-save").textContent="✓ Текст сохранён. Проверка обновлена.";updateWordStatus();renderCriteria();});}\n'''
new2='''    var transferred=byId("edemo-transferred-essay");if(transferred){transferred.addEventListener("input",function(e){reviewState.transferredText=e.target.value;markAnalysisPending();saveReviewState();byId("edemo-transfer-save").textContent="✓ Текст сохранён. Нажмите «Проверить текст», когда закончите.";updateWordStatus();renderCriteria();updateResultScores();});}\n'''
if old2 not in s: raise SystemExit('transfer input anchor missing')
s=s.replace(old2,new2,1)
p6.write_text(s,encoding='utf-8')

# T123-07: make explicit-check UX unambiguous.
p7=base/'ege-russkiy-demoversiya-T123-07.txt'
s=p7.read_text(encoding='utf-8')
old_phrase='После завершения быстрая проверка уже выполнена. Кнопка выше дополнительно проверяет орфографию. Пунктуацию, грамматику и речь проверяйте также по подсказкам К8–К10.'
new_phrase='Проверка запускается только по этой кнопке. Пока вы печатаете или исправляете текст, он только сохраняется. После нажатия система проверит орфографию и отметит некоторые места, которые стоит проверить по К8–К10.'
if old_phrase not in s: raise SystemExit('check intro anchor missing')
s=s.replace(old_phrase,new_phrase,1)
old_status='api&&essayText().trim()?"Быстрая проверка выполнена. Дополнительная проверка орфографии ещё не запускалась.":"Сначала введите текст сочинения."'
new_status='api&&essayText().trim()?"Нажмите «Проверить текст», чтобы запустить проверку.":"Сначала введите текст сочинения."'
if old_status not in s: raise SystemExit('status anchor missing')
s=s.replace(old_status,new_status,1)
p7.write_text(s,encoding='utf-8')

# Browser regression: explicit check only.
t=base/'test-russian-task27-browser.py'
q=t.read_text(encoding='utf-8')
old_block='''    check(saved['analysisStatus']=='complete','preliminary analysis runs after finish')\n    check(len(saved['confirmedFindings']['K10'])==0,'adjacent duplicate is not confirmed K10')\n    check(len(saved['possibleFindings']['K10'])==1,'adjacent duplicate is possible K10')\n    check(len(saved['possibleFindings']['K8'])==1,'system creates possible finding')\n'''
new_block='''    check(saved['analysisStatus']=='pending','analysis stays pending after finish until explicit check')\n    check(sum(len(saved['confirmedFindings'][k])+len(saved['possibleFindings'][k]) for k in ['K7','K8','K9','K10'])==0,'no findings are produced before explicit check')\n'''
if old_block not in q: raise SystemExit('demo precheck assertions anchor missing')
q=q.replace(old_block,new_block,1)
old_help="    check(page.locator('details.edemo-criterion-help').count()==10,'all K1-K10 have optional scoring help')\n"
new_help="    check(page.locator('details.edemo-criterion-help').count()==6,'K1-K6 help is available before explicit text check')\n"
if old_help not in q: raise SystemExit('help assertion anchor missing')
q=q.replace(old_help,new_help,1)
anchor="    checked=page.evaluate(\"JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))\")\n"
insert=anchor+"    check(checked['analysisStatus']=='complete','explicit button completes analysis')\n    check(page.locator('details.edemo-criterion-help').count()==10,'K1-K10 help is available after explicit text check')\n    check(len(checked['confirmedFindings']['K10'])==0,'adjacent duplicate is not confirmed K10')\n    check(len(checked['possibleFindings']['K10'])==1,'adjacent duplicate is possible K10 after explicit check')\n    check(len(checked['possibleFindings']['K8'])==1,'K8 possible finding appears only after explicit check')\n"
if anchor not in q: raise SystemExit('checked anchor missing')
q=q.replace(anchor,insert,1)
old_paper='''    paper_saved=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))")\n    check(paper_saved['analysisStatus']=='complete','paper transfer triggers preliminary analysis')\n    check(len(paper_saved['confirmedFindings']['K8'])==0,'space before punctuation is not confirmed K8')\n    check(len(paper_saved['possibleFindings']['K8'])==0,'space before punctuation is not possible K8')\n    check(len(paper_saved['technicalFindings'])==1,'space before punctuation is technical note only')\n'''
new_paper='''    paper_saved=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))")\n    check(paper_saved['analysisStatus']=='pending','typing paper transfer does not trigger analysis')\n    check(len(paper_saved['technicalFindings'])==0,'typing produces no findings before explicit check')\n    check('Нажмите «Проверить текст»' in page.locator('#edemo-check-status').inner_text(),'explicit-check prompt shown while typing')\n    page.click('#edemo-run-text-check')\n    page.wait_for_function("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_spelling_check')||'{}').status==='complete'")\n    paper_saved=page.evaluate("JSON.parse(localStorage.getItem('eksamio_ege_russian_demo_2026_v4_2_task27_review'))")\n    check(paper_saved['analysisStatus']=='complete','paper analysis starts from explicit button')\n    check(len(paper_saved['confirmedFindings']['K8'])==0,'space before punctuation is not confirmed K8')\n    check(len(paper_saved['possibleFindings']['K8'])==0,'space before punctuation is not possible K8')\n    check(len(paper_saved['technicalFindings'])==1,'space before punctuation is technical note only after explicit check')\n'''
if old_paper not in q: raise SystemExit('paper precheck assertions anchor missing')
q=q.replace(old_paper,new_paper,1)
t.write_text(q,encoding='utf-8')

# Manifest hashes for runtime files changed.
m=base/'MANIFEST-SHA256.txt'; ms=m.read_text(encoding='utf-8')
for p in (p6,p7):
    h=hashlib.sha256(p.read_bytes()).hexdigest(); fn=p.name
    ms=re.sub(r'^[0-9a-f]{64}  '+re.escape(fn)+r'$',h+'  '+fn,ms,flags=re.M)
m.write_text(ms,encoding='utf-8')
print('PATCH READY explicit-check-only')
