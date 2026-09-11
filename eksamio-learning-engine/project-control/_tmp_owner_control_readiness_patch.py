#!/usr/bin/env python3
from pathlib import Path

PANEL = Path('eksamio-learning-engine/project-control/owner-control.html')
TESTS = Path('eksamio-learning-engine/tests/test_owner_agent_console.py')


def replace_exact(text: str, old: str, new: str, count: int = 1) -> str:
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f'expected {count} occurrences, found {actual}: {old[:120]!r}')
    return text.replace(old, new, count)


html = PANEL.read_text()
html = replace_exact(
    html,
    ".selected{margin-top:12px;padding:10px;border-radius:10px;background:var(--chip);font-size:13px}",
    ".selected{margin-top:12px;padding:10px;border-radius:10px;background:var(--chip);font-size:13px}.launch-readiness{margin-top:10px;padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--panel);font-size:13px}.launch-readiness .truth{font-size:18px}.launch-readiness small{display:block;margin-top:5px;color:var(--muted);line-height:1.4}.controls button:disabled{opacity:.45;cursor:not-allowed}",
)
html = replace_exact(
    html,
    "      <div class=\"selected\"><b>Bounded-задача перед платным запуском:</b> <span id=\"selectedTask\">не выбрана</span><br><span id=\"selectedTaskDetail\">Выберите допустимую задачу в списке. Заблокированные и owner-gated задачи не запускаются.</span></div>\n      <div class=\"controls\" aria-label=\"Owner controls\">\n        <button class=\"primary\" data-command=\"start\">Запустить следующую задачу</button>",
    "      <div class=\"selected\"><b>Bounded-задача перед платным запуском:</b> <span id=\"selectedTask\">не выбрана</span><br><span id=\"selectedTaskDetail\">Выберите допустимую задачу в списке. Заблокированные и owner-gated задачи не запускаются.</span></div>\n      <div id=\"launchReadiness\" class=\"launch-readiness\"><b>Готовность к платному запуску:</b> <span id=\"launchDecision\" class=\"truth warn\">ПРОВЕРЯЕТСЯ</span><small id=\"launchReason\">Проверяю актуальный GitHub, выбранную задачу и выполняющиеся workflow.</small></div>\n      <div class=\"controls\" aria-label=\"Owner controls\">\n        <button id=\"startButton\" class=\"primary\" data-command=\"start\" disabled>Запустить следующую задачу</button>",
)
html = replace_exact(
    html,
    "const state={board:null,tasks:[],view:'Critical Path',selectedTaskId:null,boardSource:'NONE',mainSha:null,prHead:null,checks:'unavailable'};",
    "const state={board:null,tasks:[],view:'Critical Path',selectedTaskId:null,boardSource:'NONE',mainSha:null,prHead:null,checks:'unavailable',launchReady:false,launchReason:'Проверяется',selectedBaseRef:'main',selectedLiveSha:null};",
)
html = replace_exact(
    html,
    "function setTruth(text,kind){const e=$('truth');e.textContent=text;e.className='truth '+kind}\nfunction stageCounts(tasks,s){return tasks.filter(t=>t.stage===s)}",
    "function setTruth(text,kind){const e=$('truth');e.textContent=text;e.className='truth '+kind}\nfunction setLaunchReadiness(ready,label,reason){state.launchReady=Boolean(ready);state.launchReason=reason||'';const d=$('launchDecision'),r=$('launchReason'),b=$('startButton');if(d){d.textContent=label;d.className='truth '+(ready?'ok':label==='ПРОВЕРЯЕТСЯ'?'warn':'bad')}if(r)r.textContent=reason||'';if(b)b.disabled=!ready}\nfunction taskBaseRef(t){return t&&t.branch?t.branch:'main'}\nasync function evaluateLaunchReadiness(){setLaunchReadiness(false,'ПРОВЕРЯЕТСЯ','Проверяю актуальный GitHub и отсутствие параллельной работы…');const task=state.tasks.find(t=>t.task_id===state.selectedTaskId);if(!task){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ','Нет выбранной bounded-задачи.');return}if(state.boardSource!=='LIVE_BRANCH'){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ','Operational board не подтверждён live-источником.');return}if(task.owner_gate_required||(task.blocker_type&&task.blocker_type!=='SUBJECT')||task.executor!=='Codex'){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ','Эта задача не допускает автономный платный Codex-маршрут.');return}try{const main=await fetchJson(`${API}/branches/main`);state.mainSha=main.commit.sha;$('mainSha').textContent=state.mainSha;if(typeof DEPLOYED_MAIN!=='undefined'&&state.mainSha!==DEPLOYED_MAIN){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ','Панель ещё не обновилась до текущего main. Обновите страницу после Pages deploy.');return}state.selectedBaseRef=taskBaseRef(task);state.selectedLiveSha=state.mainSha;if(task.pr){const pr=await fetchJson(`${API}/pulls/${task.pr}`);if(pr.state!=='open'){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ',`PR #${task.pr} не открыт.`);return}if(task.branch&&pr.head.ref!==task.branch){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ',`PR #${task.pr} указывает на другую ветку: ${pr.head.ref}.`);return}state.selectedBaseRef=pr.head.ref;state.selectedLiveSha=pr.head.sha;const rr=await fetchJson(`${API}/actions/runs?branch=${encodeURIComponent(pr.head.ref)}&per_page=100`);const active=(rr.workflow_runs||[]).filter(x=>x.status!=='completed');if(active.length){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ',`На ${pr.head.ref} ещё выполняется/ожидает ${active.length} GitHub workflow. Дождитесь завершения; панель перепроверит автоматически.`);return}}const owner=await fetchJson(`${API}/actions/workflows/owner-agent-console-control.yml/runs?per_page=20`);const paidActive=(owner.workflow_runs||[]).filter(x=>x.status!=='completed');if(paidActive.length){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ',`Уже активен Owner Control run: ${paidActive[0].id}. Параллельный платный запуск запрещён.`);return}setLaunchReadiness(true,'МОЖНО ЗАПУСКАТЬ',`GitHub свободен. task_id=${task.task_id}; base_ref=${state.selectedBaseRef}; live SHA=${state.selectedLiveSha}. Завершённые failures не блокируют bounded-ремонт; активных workflow нет.`)}catch(err){setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ',`Не удалось подтвердить GitHub readiness: ${err.message}`)}}\nfunction stageCounts(tasks,s){return tasks.filter(t=>t.stage===s)}",
)
html = replace_exact(
    html,
    "function selectTask(t){if(!t||t.owner_gate_required||(t.blocker_type&&t.blocker_type!=='SUBJECT')||t.executor!=='Codex'){return}state.selectedTaskId=t.task_id;$('selectedTask').textContent=`${t.task_id} — ${t.title}`;$('selectedTaskDetail').textContent=`Статус: ${t.status}. Следующее действие: ${safe(t.next_action)}. Перед Run workflow укажите task_id=${t.task_id}; платный executor выбирается Astra по правилу Luna → Terra → Sol.`;renderTasks()}",
    "function selectTask(t){if(!t||t.owner_gate_required||(t.blocker_type&&t.blocker_type!=='SUBJECT')||t.executor!=='Codex'){return}state.selectedTaskId=t.task_id;state.selectedBaseRef=taskBaseRef(t);$('selectedTask').textContent=`${t.task_id} — ${t.title}`;$('selectedTaskDetail').textContent=`Статус: ${t.status}. Следующее действие: ${safe(t.next_action)}. Для Start: task_id=${t.task_id}; base_ref=${state.selectedBaseRef}; resume_run_id пусто.`;renderTasks();evaluateLaunchReadiness().catch(err=>setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ',err.message))}",
)
html = replace_exact(
    html,
    "function commandConfirm(command){const labels={start:'Запустить следующую задачу',pause:'Пауза после текущего шага',resume:'Продолжить',stop:'Остановить',refresh:'Обновить статус'};const paid=command==='start'||command==='resume';if(paid&&!state.selectedTaskId){alert('Сначала выберите конкретную незаблокированную задачу.');return}",
    "function commandConfirm(command){const labels={start:'Запустить следующую задачу',pause:'Пауза после текущего шага',resume:'Продолжить',stop:'Остановить',refresh:'Обновить статус'};const paid=command==='start'||command==='resume';if(command==='start'&&!state.launchReady){alert('Платный запуск заблокирован: '+state.launchReason);return}if(paid&&!state.selectedTaskId){alert('Сначала выберите конкретную незаблокированную задачу.');return}",
)
html = replace_exact(
    html,
    "async function boot(){try{$('repoLink').href=`https://github.com/${REPO}`;await loadBoard();fillFilters();renderStageRail();updateHeader();renderTasks();recomputeTruth();loadGithubFacts()}catch(err){showError(`Панель fail-closed: ${err.message}`);setTruth('SOURCE OF TRUTH ERROR','bad')}}",
    "async function boot(){try{$('repoLink').href=`https://github.com/${REPO}`;await loadBoard();fillFilters();renderStageRail();updateHeader();renderTasks();recomputeTruth();await loadGithubFacts();await evaluateLaunchReadiness()}catch(err){showError(`Панель fail-closed: ${err.message}`);setTruth('SOURCE OF TRUTH ERROR','bad');setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ',err.message)}}",
)
html = replace_exact(
    html,
    "boot();\n</script>",
    "boot();\nsetInterval(()=>{if(state.selectedTaskId)evaluateLaunchReadiness().catch(err=>setLaunchReadiness(false,'НЕ ЗАПУСКАТЬ',err.message))},300000);\n</script>",
)
PANEL.write_text(html)

tests = TESTS.read_text()
tests = replace_exact(
    tests,
    "        self.assertIn(\"t.executor==='Codex'\",html)\n        self.assertIn(\"'/__pycache__/' not in x[3:]\",yml)",
    "        self.assertIn(\"t.executor==='Codex'\",html)\n        for token in ['Готовность к платному запуску','МОЖНО ЗАПУСКАТЬ','НЕ ЗАПУСКАТЬ','launchReady','startButton','evaluateLaunchReadiness','actions/runs?branch=','selectedBaseRef']:\n            self.assertIn(token,html)\n        self.assertIn('data-command=\"start\" disabled',html)\n        self.assertIn(\"'/__pycache__/' not in x[3:]\",yml)",
)
TESTS.write_text(tests)
print('OWNER_CONTROL_READINESS_PATCH=APPLIED')
