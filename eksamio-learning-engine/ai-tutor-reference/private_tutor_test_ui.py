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
<title>Eksamio — приватный тест Тьютора</title>
<style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#15171a;background:#f5f6f8}
*{box-sizing:border-box}body{margin:0}.wrap{max-width:860px;margin:0 auto;padding:24px 16px 40px}
.card{background:white;border:1px solid #e4e7ec;border-radius:18px;box-shadow:0 8px 30px rgba(0,0,0,.05);overflow:hidden}
.head{padding:20px 22px;border-bottom:1px solid #eceef2}.head h1{font-size:22px;margin:0 0 6px}.muted{color:#68707c;font-size:14px;line-height:1.45}
.setup{padding:22px;display:grid;gap:14px}.setup label{font-weight:600}.setup select,.composer textarea{width:100%;font:inherit;border:1px solid #ccd2da;border-radius:12px;padding:12px;background:white}
button{font:inherit;border:0;border-radius:12px;padding:11px 16px;cursor:pointer;background:#15171a;color:white;font-weight:650}button.secondary{background:#eef1f5;color:#20242a}button:disabled{opacity:.5;cursor:not-allowed}
.chat{display:none;min-height:580px;flex-direction:column}.status{padding:10px 18px;background:#fafbfc;border-bottom:1px solid #eceef2;display:flex;gap:12px;justify-content:space-between;flex-wrap:wrap;font-size:13px;color:#626a75}
.messages{padding:18px;display:flex;flex-direction:column;gap:12px;flex:1;max-height:560px;overflow:auto}.msg{max-width:82%;padding:11px 14px;border-radius:15px;white-space:pre-wrap;line-height:1.48}.me{align-self:flex-end;background:#15171a;color:white;border-bottom-right-radius:5px}.tutor{align-self:flex-start;background:#eef1f5;border-bottom-left-radius:5px}.system{align-self:center;background:#fff5cf;color:#594600;font-size:13px;max-width:94%}
.composer{padding:14px 18px 18px;border-top:1px solid #eceef2;display:grid;gap:10px}.composer textarea{resize:vertical;min-height:74px}.row{display:flex;gap:10px;justify-content:space-between;align-items:center;flex-wrap:wrap}.row .actions{display:flex;gap:8px}.busy{display:none;color:#68707c;font-size:13px}
.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:#e8f7ec;color:#17662b;font-size:12px;font-weight:650}
</style>
</head>
<body><div class="wrap"><div class="card">
<div class="head"><h1>Приватный тест Тьютора Eksamio</h1><div class="muted">Настоящий OpenAI Tutor. Страница работает только на этом Mac. Публичный доступ и голос выключены. API-ключ в браузер не передаётся.</div></div>
<div id="setup" class="setup"><div><span class="badge">PRIVATE · TEXT ONLY</span></div><label for="topic">Выберите тему</label><select id="topic"></select><div id="topicInfo" class="muted"></div><div class="muted">Лимит теста: <b id="limitText">20</b> платных реплик. Сценарий теста можно проходить свободно — специально ошибаться, спорить и просить объяснять проще.</div><div><button id="start">Начать тест</button></div></div>
<div id="chat" class="chat"><div class="status"><span id="topicLabel"></span><span id="turns"></span></div><div id="messages" class="messages"></div><div class="composer"><textarea id="input" maxlength="2000" placeholder="Напишите сообщение Тьютору…"></textarea><div class="row"><span id="busy" class="busy">Тьютор отвечает…</span><div class="actions"><button id="finish" class="secondary">Завершить тест</button><button id="send">Отправить</button></div></div></div></div>
</div></div>
<script>
const $=s=>document.querySelector(s); let session=null, maxTurns=20;
function add(text,cls){const d=document.createElement('div');d.className='msg '+cls;d.textContent=text;$('#messages').appendChild(d);$('#messages').scrollTop=$('#messages').scrollHeight}
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const j=await r.json();if(!r.ok)throw new Error(j.error||'Ошибка');return j}
async function boot(){const s=await api('/api/status');maxTurns=s.max_turns;$('#limitText').textContent=maxTurns;const sel=$('#topic');s.topics.forEach(t=>{const o=document.createElement('option');o.value=t.semantic_id;o.textContent=t.title;o.dataset.desc=t.explanation;sel.appendChild(o)});function info(){const o=sel.selectedOptions[0];$('#topicInfo').textContent=o?o.dataset.desc:''}sel.onchange=info;info()}
$('#start').onclick=async()=>{try{const j=await api('/api/start',{semantic_id:$('#topic').value});session=j.session_ref;$('#setup').style.display='none';$('#chat').style.display='flex';$('#topicLabel').textContent=j.title;$('#turns').textContent=`0 / ${maxTurns} реплик`;add('Можно начинать. Пишите так, как писал бы обычный ученик.','system');$('#input').focus()}catch(e){alert(e.message)}};
async function send(){const text=$('#input').value.trim();if(!text||!session)return;$('#input').value='';$('#send').disabled=true;$('#busy').style.display='inline';add(text,'me');try{const j=await api('/api/turn',{session_ref:session,text});add(j.tutor_text,'tutor');$('#turns').textContent=`${j.turn_count} / ${maxTurns} реплик`;if(j.turn_count>=maxTurns){$('#input').disabled=true;$('#send').disabled=true;add('Лимит тестовой сессии достигнут. Завершите тест.','system')}}catch(e){add('Ошибка теста: '+e.message,'system')}finally{$('#busy').style.display='none';if(!$('#input').disabled)$('#send').disabled=false;$('#input').focus()}}
$('#send').onclick=send;$('#input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
$('#finish').onclick=async()=>{if(!session)return;try{const j=await api('/api/end',{session_ref:session});add('Тест завершён. Результат сохранён локально: '+j.report_name,'system');$('#input').disabled=true;$('#send').disabled=true;$('#finish').disabled=true}catch(e){alert(e.message)}};
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
