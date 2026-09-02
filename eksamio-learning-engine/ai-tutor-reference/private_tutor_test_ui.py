#!/usr/bin/env python3
"""Local-only user-test UI for the real OpenAI Russian Tutor.

The server binds only to 127.0.0.1, never accepts API keys from the browser,
and requires explicit owner authorization at process start. Public traffic,
production PEIS writes and SpeechKit execution remain OFF.
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from private_staging_openai_yandex_tutor import (  # noqa: E402
    PrivateOpenAIYandexTutorConfig,
    assemble_private_openai_yandex_tutor,
)

HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_MESSAGE_CHARS = 2_000
DEFAULT_MAX_TURNS = 20


PAGE = r'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eksamio — тестовый AI-Тьютор</title>
<style>
:root{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  color:#17202a;background:#f4f7fb;
  --ink:#17202a;--muted:#667085;--line:#e5eaf1;--soft:#f7f9fc;
  --brand:#4b5cf0;--brand2:#7656e8;--brand-soft:#eef0ff;
  --success:#137a42;--success-bg:#eaf8ef;--warn:#775d00;--warn-bg:#fff8da;
}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:
  radial-gradient(circle at 8% 0%,rgba(75,92,240,.12),transparent 31rem),
  radial-gradient(circle at 92% 8%,rgba(118,86,232,.10),transparent 28rem),#f4f7fb}
button,select,textarea{font:inherit}.page{max-width:980px;margin:0 auto;padding:34px 18px 48px}
.brandbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:18px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;letter-spacing:-.02em;font-size:20px;color:var(--ink)}
.logo{width:36px;height:36px;border-radius:12px;display:grid;place-items:center;color:white;font-weight:850;background:linear-gradient(135deg,var(--brand),var(--brand2));box-shadow:0 8px 20px rgba(75,92,240,.24)}
.mode{font-size:12px;font-weight:700;color:#475467;border:1px solid #dce2eb;background:rgba(255,255,255,.75);padding:6px 10px;border-radius:999px}
.shell{background:rgba(255,255,255,.96);border:1px solid rgba(220,226,235,.95);border-radius:24px;box-shadow:0 24px 65px rgba(34,44,73,.10);overflow:hidden}
.hero{padding:34px 34px 26px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#fff 0%,#fbfcff 100%)}
.kicker{display:inline-flex;align-items:center;gap:7px;color:var(--success);background:var(--success-bg);font-size:12px;font-weight:750;padding:6px 10px;border-radius:999px;margin-bottom:14px}.dot{width:7px;height:7px;border-radius:50%;background:#21a45b}
.hero h1{font-size:34px;line-height:1.08;letter-spacing:-.035em;margin:0 0 12px;max-width:680px}.hero p{margin:0;color:var(--muted);font-size:16px;line-height:1.55;max-width:720px}
.setup{padding:28px 34px 34px;display:grid;gap:20px}.section-label{font-size:13px;font-weight:750;color:#475467;text-transform:uppercase;letter-spacing:.055em}
.topic-card{border:1px solid var(--line);border-radius:18px;padding:18px;background:#fff;display:grid;gap:10px}.topic-card label{font-weight:750;font-size:17px}.topic-card select{width:100%;border:1px solid #cfd6e2;border-radius:12px;padding:12px 40px 12px 13px;background:white;color:var(--ink);outline:none}.topic-card select:focus,.composer textarea:focus{border-color:#8e99f7;box-shadow:0 0 0 4px rgba(75,92,240,.10)}
.topic-info{color:var(--muted);font-size:14px;line-height:1.5}.how{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.how-item{border:1px solid var(--line);background:var(--soft);border-radius:16px;padding:15px}.num{width:27px;height:27px;border-radius:9px;background:var(--brand-soft);color:var(--brand);font-weight:800;display:grid;place-items:center;margin-bottom:9px}.how-item b{display:block;font-size:14px;margin-bottom:4px}.how-item span{color:var(--muted);font-size:13px;line-height:1.4}
.limit{display:flex;align-items:flex-start;gap:11px;border-radius:15px;padding:14px 15px;background:#faf8ff;border:1px solid #ebe5ff;color:#51466c;font-size:14px;line-height:1.45}.limit strong{color:#342a52}
.start-row{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}.start-note{color:var(--muted);font-size:13px;line-height:1.45}.primary{border:0;border-radius:13px;padding:13px 19px;cursor:pointer;color:white;font-weight:750;background:linear-gradient(135deg,var(--brand),var(--brand2));box-shadow:0 9px 22px rgba(75,92,240,.24)}.primary:hover{filter:brightness(.98);transform:translateY(-1px)}button:disabled{opacity:.5;cursor:not-allowed;transform:none!important}
.tech{border-top:1px solid var(--line);padding-top:15px;color:#7a8391;font-size:12px}.tech summary{cursor:pointer;font-weight:650;color:#667085}.tech p{margin:8px 0 0;line-height:1.45}
.chat{display:none;min-height:670px;flex-direction:column}.chat-head{padding:17px 22px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;background:#fff}.tutor-id{display:flex;align-items:center;gap:11px}.avatar{width:42px;height:42px;border-radius:14px;display:grid;place-items:center;color:white;background:linear-gradient(135deg,var(--brand),var(--brand2));font-size:18px;font-weight:850}.tutor-name{font-weight:800;line-height:1.15}.topic-name{font-size:12px;color:var(--muted);margin-top:4px;max-width:560px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.progress-wrap{min-width:150px;text-align:right}.progress-label{font-size:12px;color:var(--muted);margin-bottom:6px}.progress{height:7px;border-radius:99px;background:#edf0f5;overflow:hidden}.progress>span{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--brand),var(--brand2));transition:width .25s ease}.turn-text{font-size:12px;color:#475467;margin-top:5px;font-weight:650}
.messages{padding:24px 22px;display:flex;flex-direction:column;gap:14px;flex:1;max-height:600px;overflow:auto;background:#fbfcfe}.line{display:flex;gap:9px;align-items:flex-end}.line.me-line{justify-content:flex-end}.mini-avatar{flex:0 0 30px;width:30px;height:30px;border-radius:10px;display:grid;place-items:center;font-size:12px;font-weight:800;background:var(--brand-soft);color:var(--brand)}.msg{max-width:76%;padding:12px 15px;border-radius:17px;white-space:pre-wrap;line-height:1.5;font-size:15px}.me{background:#283043;color:white;border-bottom-right-radius:5px}.tutor{background:white;border:1px solid var(--line);box-shadow:0 3px 9px rgba(21,32,43,.04);border-bottom-left-radius:5px}.system{align-self:center;background:var(--warn-bg);color:var(--warn);font-size:13px;max-width:94%;text-align:center;padding:10px 14px;border-radius:12px}
.composer{padding:15px 20px 18px;border-top:1px solid var(--line);display:grid;gap:10px;background:white}.composer textarea{width:100%;resize:vertical;min-height:82px;max-height:190px;border:1px solid #cfd6e2;border-radius:14px;padding:13px;outline:none;color:var(--ink);background:#fff}.composer-foot{display:flex;gap:10px;justify-content:space-between;align-items:center;flex-wrap:wrap}.hint{font-size:12px;color:#8a93a1}.actions{display:flex;gap:8px}.secondary{border:0;border-radius:12px;padding:11px 15px;cursor:pointer;background:#eef1f5;color:#303744;font-weight:700}.send{border:0;border-radius:12px;padding:11px 17px;cursor:pointer;background:linear-gradient(135deg,var(--brand),var(--brand2));color:white;font-weight:750}.busy{display:none;color:var(--muted);font-size:13px}
.done-card{display:none;margin:18px 22px 22px;border:1px solid #d9eadf;background:#f4fbf6;border-radius:16px;padding:18px;color:#28533a}.done-card b{display:block;margin-bottom:5px}.done-card span{font-size:13px;line-height:1.45;color:#4d6b59}
@media(max-width:700px){.page{padding:18px 10px 30px}.hero,.setup{padding-left:20px;padding-right:20px}.hero h1{font-size:29px}.how{grid-template-columns:1fr}.chat{min-height:640px}.msg{max-width:86%}.progress-wrap{min-width:120px}.topic-name{max-width:210px}}
</style>
</head>
<body><main class="page">
<div class="brandbar"><div class="brand"><div class="logo">E</div><span>Eksamio</span></div><span class="mode">Закрытый тест</span></div>
<section class="shell">
<div id="setupScreen">
  <div class="hero">
    <div class="kicker"><span class="dot"></span>Тестовый AI-Тьютор готов</div>
    <h1>Проверим, как Тьютор учит в настоящем диалоге</h1>
    <p>Выберите тему и общайтесь с ним как с обычным преподавателем: задавайте вопросы, ошибайтесь, спорьте и просите объяснить иначе.</p>
  </div>
  <div id="setup" class="setup">
    <div class="section-label">Старт тестового Тьютора</div>
    <div class="topic-card"><label for="topic">Тема разговора</label><select id="topic"></select><div id="topicInfo" class="topic-info"></div></div>
    <div class="how">
      <div class="how-item"><div class="num">1</div><b>Пишите естественно</b><span>Не нужно формулировать «правильные» вопросы. Ведите себя как реальный ученик.</span></div>
      <div class="how-item"><div class="num">2</div><b>Проверяйте объяснение</b><span>Можно не понимать, ошибаться, просить пример или более простое объяснение.</span></div>
      <div class="how-item"><div class="num">3</div><b>Не подыгрывайте</b><span>Наша задача — увидеть, действительно ли Тьютор умеет обучать, а не просто отвечать.</span></div>
    </div>
    <div class="limit"><div>●</div><div><strong>До <span id="limitText">20</span> сообщений ученика.</strong> Каждое отправленное сообщение вызывает один платный запрос к OpenAI. После достижения лимита новые запросы автоматически блокируются.</div></div>
    <div class="start-row"><div class="start-note">Тест можно завершить раньше в любой момент.</div><button id="start" class="primary">Начать тест с Тьютором</button></div>
    <details class="tech"><summary>Техническая безопасность теста</summary><p>Страница работает только на этом Mac. API-ключ в браузер не передаётся. Публичный доступ и голос выключены. Production PEIS-записи не выполняются.</p></details>
  </div>
</div>
<div id="chat" class="chat">
  <div class="chat-head">
    <div class="tutor-id"><div class="avatar">E</div><div><div class="tutor-name">Eksamio Тьютор</div><div id="topicLabel" class="topic-name"></div></div></div>
    <div class="progress-wrap"><div class="progress-label">Ход теста</div><div class="progress"><span id="progressBar"></span></div><div id="turns" class="turn-text"></div></div>
  </div>
  <div id="messages" class="messages"></div>
  <div id="doneCard" class="done-card"><b>Тест завершён</b><span id="doneText">Результат сохранён локально.</span></div>
  <div class="composer"><textarea id="input" maxlength="2000" placeholder="Напишите сообщение Тьютору…"></textarea><div class="composer-foot"><div><span id="busy" class="busy">Тьютор формулирует ответ…</span><span id="keyHint" class="hint">Enter — отправить · Shift+Enter — новая строка</span></div><div class="actions"><button id="finish" class="secondary">Завершить тест</button><button id="send" class="send">Отправить</button></div></div></div>
</div>
</section>
</main>
<script>
const $=s=>document.querySelector(s); let session=null, maxTurns=20;
function updateProgress(turn){$('#turns').textContent=`${turn} из ${maxTurns} сообщений`;$('#progressBar').style.width=`${Math.min(100,(turn/maxTurns)*100)}%`}
function add(text,cls){if(cls==='system'){const d=document.createElement('div');d.className='msg system';d.textContent=text;$('#messages').appendChild(d)}else{const line=document.createElement('div');line.className='line '+(cls==='me'?'me-line':'');if(cls==='tutor'){const a=document.createElement('div');a.className='mini-avatar';a.textContent='E';line.appendChild(a)}const d=document.createElement('div');d.className='msg '+cls;d.textContent=text;line.appendChild(d);$('#messages').appendChild(line)}$('#messages').scrollTop=$('#messages').scrollHeight}
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const j=await r.json();if(!r.ok)throw new Error(j.error||'Ошибка');return j}
async function boot(){const s=await api('/api/status');maxTurns=s.max_turns;$('#limitText').textContent=maxTurns;const sel=$('#topic');s.topics.forEach(t=>{const o=document.createElement('option');o.value=t.semantic_id;o.textContent=t.title;o.dataset.desc=t.explanation;sel.appendChild(o)});function info(){const o=sel.selectedOptions[0];$('#topicInfo').textContent=o?o.dataset.desc:''}sel.onchange=info;info()}
$('#start').onclick=async()=>{try{$('#start').disabled=true;const j=await api('/api/start',{semantic_id:$('#topic').value});session=j.session_ref;$('#setupScreen').style.display='none';$('#chat').style.display='flex';$('#topicLabel').textContent=j.title;updateProgress(0);add('Тест начался. Пиши Тьютору так, как писал бы обычному преподавателю.','system');$('#input').focus()}catch(e){$('#start').disabled=false;alert(e.message)}};
async function send(){const text=$('#input').value.trim();if(!text||!session)return;$('#input').value='';$('#send').disabled=true;$('#busy').style.display='inline';$('#keyHint').style.display='none';add(text,'me');try{const j=await api('/api/turn',{session_ref:session,text});add(j.tutor_text,'tutor');updateProgress(j.turn_count);if(j.turn_count>=maxTurns){$('#input').disabled=true;$('#send').disabled=true;add('Достигнут лимит этой тестовой сессии. Новые платные запросы заблокированы.','system')}}catch(e){add('Не удалось получить ответ: '+e.message,'system')}finally{$('#busy').style.display='none';$('#keyHint').style.display='inline';if(!$('#input').disabled)$('#send').disabled=false;$('#input').focus()}}
$('#send').onclick=send;$('#input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
$('#finish').onclick=async()=>{if(!session)return;$('#finish').disabled=true;try{const j=await api('/api/end',{session_ref:session});$('#doneText').textContent='Диалог сохранён локально для последующего разбора качества. Файл: '+j.report_name;$('#doneCard').style.display='block';add('Сессия завершена. Спасибо — тест сохранён для анализа.','system');$('#input').disabled=true;$('#send').disabled=true;$('#composer')?.classList.add('ended')}catch(e){$('#finish').disabled=false;alert(e.message)}};
boot().catch(e=>alert(e.message));
</script></body></html>'''


@dataclass
class TestSession:
    session_ref: str
    semantic_id: str
    title: str
    started_at: float
    transcript: list[dict[str, str]] = field(default_factory=list)
    ended: bool = False


class App:
    def __init__(self, *, max_turns: int) -> None:
        if not 1 <= max_turns <= 20:
            raise ValueError("private live test max_turns must be 1..20")
        self.max_turns = max_turns
        self.assembly = assemble_private_openai_yandex_tutor(
            engine_root=ENGINE,
            config=PrivateOpenAIYandexTutorConfig(
                yandex_voice="text-test-inert",
                private_staging=True,
                public_traffic_enabled=False,
                owner_live_authorized=True,
                text_execution_enabled=True,
                speech_execution_enabled=False,
            ),
        )
        self.sessions: dict[str, TestSession] = {}
        self.lock = threading.Lock()
        self.report_dir = Path.home() / ".eksamio" / "private-tutor-tests"

    def topics(self) -> list[dict[str, str]]:
        rows=[]
        for semantic_id in self.assembly.tutor.accepted_semantics.semantic_ids:
            g=self.assembly.tutor.accepted_semantics.require(semantic_id)
            rows.append({"semantic_id":semantic_id,"title":g.title,"explanation":g.explanation})
        return rows

    def start(self, semantic_id: str) -> dict[str, Any]:
        g=self.assembly.tutor.accepted_semantics.require(semantic_id)
        state=self.assembly.tutor.open_semantic_session(
            learner_profile_id="learner:private-family-test",
            semantic_id=semantic_id,
        )
        with self.lock:
            self.sessions[state.session_ref]=TestSession(state.session_ref,semantic_id,g.title,time.time())
        return {"session_ref":state.session_ref,"semantic_id":semantic_id,"title":g.title}

    def turn(self, session_ref: str, text: str) -> dict[str, Any]:
        if not isinstance(text,str) or not text.strip() or len(text)>MAX_MESSAGE_CHARS:
            raise ValueError("Сообщение должно содержать 1–2000 символов")
        with self.lock:
            record=self.sessions.get(session_ref)
            if record is None or record.ended:
                raise ValueError("Тестовая сессия не найдена или уже завершена")
            state=self.assembly.tutor.sessions[session_ref]
            if state.turn_count >= self.max_turns:
                raise ValueError("Лимит платных реплик этой тестовой сессии достигнут")
        interaction=self.assembly.tutor.text_turn(session_ref,text.strip())
        with self.lock:
            record.transcript.append({"role":"learner","text":text.strip()})
            record.transcript.append({"role":"tutor","text":interaction.tutor_text})
            turn_count=self.assembly.tutor.sessions[session_ref].turn_count
        return {"tutor_text":interaction.tutor_text,"turn_count":turn_count,"max_turns":self.max_turns}

    def end(self, session_ref: str) -> dict[str, str]:
        with self.lock:
            record=self.sessions.get(session_ref)
            if record is None:
                raise ValueError("Тестовая сессия не найдена")
            record.ended=True
            state=self.assembly.tutor.sessions[session_ref]
            payload={
                "schema":"eksamio.private-tutor-family-test.v1",
                "semantic_id":record.semantic_id,
                "topic_title":record.title,
                "started_at_unix":record.started_at,
                "ended_at_unix":time.time(),
                "turn_count":state.turn_count,
                "max_turns":self.max_turns,
                "model":self.assembly.config.openai_model,
                "public_traffic_enabled":False,
                "speech_execution_enabled":False,
                "production_peis_writes":0,
                "raw_audio_persisted_bytes":0,
                "transcript":record.transcript,
            }
        self.report_dir.mkdir(parents=True,exist_ok=True)
        name=f"tutor-test-{int(time.time())}-{secrets.token_hex(3)}.json"
        (self.report_dir/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        return {"report_name":name}


class Handler(BaseHTTPRequestHandler):
    app: App

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep learner text and provider payloads out of access logs.
        return

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
        self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(data)));self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(data)

    def _body(self) -> dict[str, Any]:
        length=int(self.headers.get("Content-Length","0"))
        if length<1 or length>8_000: raise ValueError("Некорректный размер запроса")
        value=json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(value,dict): raise ValueError("Некорректный запрос")
        return value

    def do_GET(self) -> None:
        if self.path=="/":
            data=PAGE.encode("utf-8");self.send_response(HTTPStatus.OK);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(data)));self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(data);return
        if self.path=="/api/status":
            self._json(200,{"status":"READY","model":self.app.assembly.config.openai_model,"max_turns":self.app.max_turns,"public_traffic":False,"speech":False,"topics":self.app.topics()});return
        self._json(404,{"error":"Не найдено"})

    def do_POST(self) -> None:
        try:
            body=self._body()
            if self.path=="/api/start": result=self.app.start(str(body.get("semantic_id","")))
            elif self.path=="/api/turn": result=self.app.turn(str(body.get("session_ref","")),str(body.get("text","")))
            elif self.path=="/api/end": result=self.app.end(str(body.get("session_ref","")))
            else: self._json(404,{"error":"Не найдено"});return
            self._json(200,result)
        except Exception as exc:
            # Do not expose provider secrets or raw exception repr to the browser.
            message=str(exc)
            if "credential" in message.lower() or "keychain" in message.lower() or "authorization" in message.lower():
                message="Не удалось выполнить приватный запрос к провайдеру. Проверьте локальную конфигурацию доступа."
            self._json(400,{"error":message[:500]})


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser()
    p.add_argument("--owner-authorized",action="store_true")
    p.add_argument("--port",type=int,default=DEFAULT_PORT)
    p.add_argument("--max-turns",type=int,default=DEFAULT_MAX_TURNS)
    p.add_argument("--no-browser",action="store_true")
    return p.parse_args()


def main() -> int:
    args=parse_args()
    if not args.owner_authorized:
        print("PRIVATE_TUTOR_UI=BLOCKED_OWNER_AUTHORIZATION")
        return 2
    if not 1024 <= args.port <= 65535:
        raise SystemExit("port must be 1024..65535")
    Handler.app=App(max_turns=args.max_turns)
    server=ThreadingHTTPServer((HOST,args.port),Handler)
    url=f"http://{HOST}:{args.port}/"
    print("PRIVATE_TUTOR_UI=READY")
    print(f"URL={url}")
    print(f"MAX_PAID_TURNS={args.max_turns}")
    print("PUBLIC_TRAFFIC=OFF")
    print("SPEECH_EXECUTION=OFF")
    if not args.no_browser:
        threading.Timer(0.4,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0

if __name__=="__main__":
    raise SystemExit(main())