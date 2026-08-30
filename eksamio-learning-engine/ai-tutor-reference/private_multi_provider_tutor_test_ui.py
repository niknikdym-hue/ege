#!/usr/bin/env python3
"""Local-only real-user UI for Eksamio Tutor provider acceptance.

One page tests OpenAI, Qwen, Yandex Alice or AUTO text routing using the same
Eksamio grounding. Voice input/output uses Yandex SpeechKit only. Provider
secrets never enter the browser or CLI. Learner/generated audio is transient.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import sys
import threading
import webbrowser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent
sys.path.insert(0, str(HERE))

from openai_secret_provider import OpenAISecretProvider  # noqa: E402
from private_staging_multi_provider_tutor import (  # noqa: E402
    PrivateMultiProviderTutorAssembly,
    PrivateMultiProviderTutorConfig,
    assemble_private_multi_provider_tutor,
)
from qwen_secret_provider import QwenSecretProvider  # noqa: E402
from yandex_ai_secret_provider import YandexAISecretProvider  # noqa: E402
from yandex_speech_secret_provider import YandexSpeechSecretProvider  # noqa: E402

HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_MESSAGE_CHARS = 12_000
DEFAULT_MAX_TURNS = 20
MAX_AUDIO_BYTES = 1_000_000
PROVIDER_MODES = {"auto", "openai", "qwen", "yandex"}


PAGE = r'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Eksamio — тест AI-Тьютора</title>
<style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#17202a;background:#f4f7fb;--brand:#4b5cf0;--brand2:#7656e8;--muted:#667085;--line:#e4e9f1;--ok:#157347;--warn:#8a5b00}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0,rgba(75,92,240,.12),transparent 32rem),#f4f7fb}.page{max-width:1040px;margin:auto;padding:28px 16px 48px}.brand{font-weight:850;font-size:21px;margin:0 0 16px}.shell{background:#fff;border:1px solid var(--line);border-radius:24px;box-shadow:0 22px 60px rgba(30,42,70,.1);overflow:hidden}.hero{padding:28px 30px 20px;border-bottom:1px solid var(--line)}h1{margin:0 0 8px;font-size:31px;letter-spacing:-.03em}.hero p{margin:0;color:var(--muted);line-height:1.5}.setup{padding:24px 30px 30px;display:grid;gap:17px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.card{border:1px solid var(--line);border-radius:16px;padding:15px}.card label{font-weight:750;font-size:14px;display:block;margin-bottom:8px}.card select{width:100%;padding:11px;border:1px solid #cdd5df;border-radius:11px;background:#fff}.status{font-size:12px;line-height:1.55;color:var(--muted);margin-top:8px}.ok{color:var(--ok)}.bad{color:#a33}.notice{padding:13px 14px;border-radius:13px;background:#faf8ff;border:1px solid #e9e3ff;color:#51466c;font-size:13px;line-height:1.5}.primary,.send,.mic{border:0;color:#fff;background:linear-gradient(135deg,var(--brand),var(--brand2));border-radius:12px;padding:12px 17px;font-weight:750;cursor:pointer}.secondary{border:0;background:#eef1f5;border-radius:12px;padding:11px 15px;font-weight:700;cursor:pointer}.primary:disabled,.send:disabled,.mic:disabled{opacity:.45;cursor:not-allowed}.chat{display:none;min-height:700px;flex-direction:column}.chat-head{padding:15px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:14px;align-items:center;flex-wrap:wrap}.title{font-weight:800}.meta{font-size:12px;color:var(--muted);margin-top:4px}.messages{flex:1;min-height:380px;max-height:560px;overflow:auto;padding:22px;background:#fbfcfe;display:flex;flex-direction:column;gap:12px}.msg{max-width:78%;padding:12px 14px;border-radius:16px;white-space:pre-wrap;line-height:1.5}.me{align-self:flex-end;background:#293144;color:white;border-bottom-right-radius:5px}.tutor{align-self:flex-start;background:#fff;border:1px solid var(--line);border-bottom-left-radius:5px}.system{align-self:center;background:#fff7d8;color:#795d00;font-size:13px;text-align:center}.provider{font-size:11px;color:#8a93a1;margin-top:-7px;align-self:flex-start}.composer{padding:15px 20px 18px;border-top:1px solid var(--line);display:grid;gap:10px}.composer textarea{width:100%;min-height:180px;max-height:520px;resize:vertical;border:1px solid #cbd3df;border-radius:14px;padding:13px;font:inherit;line-height:1.45}.composer textarea:focus{outline:none;border-color:#8e99f7;box-shadow:0 0 0 4px rgba(75,92,240,.09)}.foot{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}.left,.actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.hint{font-size:12px;color:var(--muted)}.mic.recording{background:#b42318}.audio{margin-top:8px;width:min(420px,100%)}.summary{display:none;padding:18px;margin:18px;border:1px solid #d5eadc;background:#f3fbf5;border-radius:14px;color:#28543a}.badge{font-size:12px;font-weight:700;padding:5px 9px;border-radius:999px;background:#eef0ff;color:#4754cc}.counter{font-size:12px;color:#475467;font-weight:700}.error{color:#b42318}.hidden{display:none!important}
@media(max-width:720px){.grid{grid-template-columns:1fr}.page{padding:12px 8px 30px}.hero,.setup{padding-left:18px;padding-right:18px}.msg{max-width:90%}.composer textarea{min-height:210px}}
</style></head><body><main class="page"><div class="brand">Eksamio</div><section class="shell">
<div id="setupScreen"><div class="hero"><h1>Старт тестового Тьютора</h1><p>Один интерфейс для сравнения трёх AI-мозгов и проверки автоматического переключения. Учебный контекст у всех одинаковый.</p></div><div class="setup">
<div class="grid"><div class="card"><label for="provider">AI-мозг</label><select id="provider"><option value="openai">OpenAI</option><option value="qwen">Qwen</option><option value="yandex">Яндекс</option><option value="auto">Авто: OpenAI → Qwen → Яндекс</option></select><div id="providerStatus" class="status"></div></div>
<div class="card"><label for="topic">Тема</label><select id="topic"></select><div id="topicInfo" class="status"></div></div></div>
<div class="notice"><b>До <span id="maxTurns">20</span> успешных сообщений ученика.</b> Неудачный STT или полностью недоступный AI не должен списывать успешную реплику. Текст можно вставлять до 12 000 символов. Голос ответа — Yandex Lera / neutral / 1.04.</div>
<div><button id="start" class="primary">Начать тест</button></div><div id="preflight" class="status"></div>
</div></div>
<div id="chat" class="chat"><div class="chat-head"><div><div class="title">Eksamio Тьютор <span id="providerBadge" class="badge"></span></div><div id="topicLabel" class="meta"></div></div><div id="counter" class="counter"></div></div>
<div id="messages" class="messages"></div><div id="summary" class="summary"></div>
<div id="composer" class="composer"><textarea id="input" maxlength="12000" placeholder="Напишите вопрос, вставьте свой текст или фрагмент сочинения…"></textarea><div class="foot"><div class="left"><button id="mic" class="mic hidden">🎙 Говорить</button><span id="recording" class="hint"></span><span id="busy" class="hint"></span></div><div class="actions"><button id="finish" class="secondary">Завершить</button><button id="send" class="send">Отправить</button></div></div><div class="hint">Enter — отправить · Shift+Enter — новая строка · голосовая реплика ограничена 25 секундами</div></div>
</div></section></main>
<script>
const $=s=>document.querySelector(s);let session=null,maxTurns=20,turns=0,speech=false,recording=false,audioCtx=null,stream=null,processor=null,chunks=[],startedAt=0,timer=null;
const labels={openai:'OpenAI',qwen:'Qwen',yandex:'Яндекс',auto:'Авто'};
async function api(path,body){const r=await fetch(path,{method:body?'POST':'GET',headers:{'Content-Type':'application/json'},body:body?JSON.stringify(body):undefined});const j=await r.json();if(!r.ok)throw new Error(j.error||'Ошибка');return j}
function add(text,cls,provider){const d=document.createElement('div');d.className='msg '+cls;d.textContent=text;$('#messages').appendChild(d);if(provider){const p=document.createElement('div');p.className='provider';p.textContent='Ответил: '+provider;$('#messages').appendChild(p)}$('#messages').scrollTop=$('#messages').scrollHeight}
function update(){ $('#counter').textContent=`${turns} из ${maxTurns}`;if(turns>=maxTurns){$('#send').disabled=true;$('#mic').disabled=true;$('#input').disabled=true;add('Достигнут лимит тестовой сессии.','system')}}
function providerLine(p){const bits=[];for(const k of ['openai','qwen','yandex']){const v=p[k];bits.push(`${labels[k]}: ${v.ready?'готов':'не готов'}${v.detail?' — '+v.detail:''}`)}return bits.join(' · ')}
async function boot(){try{const s=await api('/api/status');maxTurns=s.max_turns;speech=s.speech_enabled;$('#maxTurns').textContent=maxTurns;$('#mic').classList.toggle('hidden',!speech);for(const t of s.topics){const o=document.createElement('option');o.value=t.id;o.textContent=t.title;$('#topic').appendChild(o)}const refreshTopic=()=>{const t=s.topics.find(x=>x.id===$('#topic').value);$('#topicInfo').textContent=t?t.id:''};$('#topic').onchange=refreshTopic;refreshTopic();$('#preflight').textContent=providerLine(s.providers);const refreshProvider=()=>{const k=$('#provider').value;if(k==='auto'){$('#providerStatus').textContent='При отказе одного AI система продолжит ход через следующий backend.'}else{const v=s.providers[k];$('#providerStatus').textContent=v.ready?'Локальная конфигурация найдена. Реальную доступность подтвердит запрос.':'Перед живым тестом требуется безопасная локальная конфигурация: '+v.detail}};$('#provider').onchange=refreshProvider;refreshProvider()}catch(e){$('#preflight').textContent='Не удалось подготовить страницу: '+e.message;$('#preflight').className='status error';$('#start').disabled=true}}
$('#start').onclick=async()=>{try{$('#start').disabled=true;const p=$('#provider').value;const t=$('#topic').value;const r=await api('/api/start',{provider:p,semantic_id:t});session=r.session;turns=0;$('#providerBadge').textContent=labels[p];$('#topicLabel').textContent=r.topic_title;$('#setupScreen').style.display='none';$('#chat').style.display='flex';add('Тест начат. Общайтесь как обычный ученик.','system');update();$('#input').focus()}catch(e){alert(e.message);$('#start').disabled=false}}
async function sendText(){const text=$('#input').value.trim();if(!text||!session||turns>=maxTurns)return;$('#send').disabled=true;$('#mic').disabled=true;$('#busy').textContent='Тьютор отвечает…';add(text,'me');$('#input').value='';try{const r=await api('/api/message',{session,text});turns=r.turns;add(r.text,'tutor',r.brain_provider);update()}catch(e){add('Ошибка: '+e.message,'system')}finally{$('#busy').textContent='';if(turns<maxTurns){$('#send').disabled=false;$('#mic').disabled=false}}}
$('#send').onclick=sendText;$('#input').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendText()}});
function mergeChunks(list){let n=0;for(const a of list)n+=a.length;const out=new Float32Array(n);let o=0;for(const a of list){out.set(a,o);o+=a.length}return out}
function to16kPcm(samples,rate){const ratio=rate/16000;const length=Math.floor(samples.length/ratio);const buffer=new ArrayBuffer(length*2);const view=new DataView(buffer);for(let i=0;i<length;i++){const start=Math.floor(i*ratio),end=Math.min(samples.length,Math.floor((i+1)*ratio));let sum=0,c=0;for(let j=start;j<end;j++){sum+=samples[j];c++}let s=c?sum/c:0;s=Math.max(-1,Math.min(1,s));view.setInt16(i*2,s<0?s*0x8000:s*0x7fff,true)}return new Uint8Array(buffer)}
function b64(bytes){let binary='';const step=0x8000;for(let i=0;i<bytes.length;i+=step)binary+=String.fromCharCode(...bytes.subarray(i,i+step));return btoa(binary)}
async function startRec(){try{stream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true},video:false});audioCtx=new (window.AudioContext||window.webkitAudioContext)();const source=audioCtx.createMediaStreamSource(stream);processor=audioCtx.createScriptProcessor(4096,1,1);const mute=audioCtx.createGain();mute.gain.value=0;chunks=[];processor.onaudioprocess=e=>chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));source.connect(processor);processor.connect(mute);mute.connect(audioCtx.destination);recording=true;startedAt=Date.now();$('#mic').textContent='■ Остановить';$('#mic').classList.add('recording');timer=setInterval(()=>{const sec=Math.floor((Date.now()-startedAt)/1000);$('#recording').textContent=`Запись ${sec} сек.`;if(sec>=25)stopRec()},250)}catch(e){add('Микрофон недоступен: '+e.message,'system')}}
async function stopRec(){if(!recording)return;recording=false;clearInterval(timer);$('#mic').textContent='🎙 Говорить';$('#mic').classList.remove('recording');$('#recording').textContent='';processor&&processor.disconnect();stream&&stream.getTracks().forEach(t=>t.stop());const rate=audioCtx.sampleRate;await audioCtx.close();const pcm=to16kPcm(mergeChunks(chunks),rate);if(pcm.length<6400){add('Голосовая реплика слишком короткая — скажите фразу ещё раз.','system');return}$('#send').disabled=true;$('#mic').disabled=true;$('#busy').textContent='Распознаю речь и готовлю ответ…';try{const r=await api('/api/voice',{session,audio_b64:b64(pcm)});turns=r.turns;add('🎙 '+r.transcript,'me');add(r.text,'tutor',r.brain_provider);if(r.audio_b64){const a=document.createElement('audio');a.controls=true;a.autoplay=true;a.className='audio';a.src='data:'+r.audio_mime+';base64,'+r.audio_b64;$('#messages').appendChild(a);$('#messages').scrollTop=$('#messages').scrollHeight}else add('Озвучка временно недоступна — текст ответа сохранён.','system');update()}catch(e){add('Голосовая реплика не принята: '+e.message,'system')}finally{$('#busy').textContent='';if(turns<maxTurns){$('#send').disabled=false;$('#mic').disabled=false}}}
$('#mic').onclick=()=>recording?stopRec():startRec();
$('#finish').onclick=async()=>{if(recording)await stopRec();try{const r=await api('/api/finish',{session});$('#composer').style.display='none';$('#summary').style.display='block';$('#summary').textContent=`Тест завершён: ${r.turns} успешных реплик. ${r.provider_counts_text}`;add('Тест завершён. Для сравнения другого AI обновите страницу и начните новую сессию.','system')}catch(e){alert(e.message)}};
boot();
</script></body></html>'''


@dataclass
class LiveSession:
    assembly: PrivateMultiProviderTutorAssembly
    tutor_session_ref: str
    provider_mode: str
    semantic_id: str
    max_turns: int
    successful_turns: int = 0
    provider_counts: dict[str, int] = field(default_factory=dict)


def _provider_used(interaction: Any) -> str:
    for event in reversed(interaction.reliable_result.events):
        if event.event_type == "logical_turn_accepted" and event.provider_id:
            return event.provider_id
    return "unknown"


def _credential_ready(provider: Any) -> bool:
    try:
        value = provider()
    except Exception:
        return False
    return isinstance(value, str) and bool(value.strip())


class App:
    def __init__(self, *, max_turns: int, speech_enabled: bool, qwen_base_url: str | None, yandex_folder_id: str | None) -> None:
        self.max_turns = max_turns
        self.speech_enabled = speech_enabled
        self.qwen_base_url = qwen_base_url or os.environ.get("QWEN_BASE_URL") or os.environ.get("DASHSCOPE_BASE_URL") or None
        self.yandex_folder_id = yandex_folder_id or os.environ.get("YANDEX_FOLDER_ID") or None
        self.sessions: dict[str, LiveSession] = {}
        self.lock = threading.Lock()
        catalog = assemble_private_multi_provider_tutor(engine_root=ENGINE, config=PrivateMultiProviderTutorConfig())
        self.topics = [
            {
                "id": semantic_id,
                "title": catalog.tutor.accepted_semantics.require(semantic_id).title,
            }
            for semantic_id in catalog.tutor.accepted_semantics.semantic_ids
        ]

    def provider_status(self) -> dict[str, dict[str, object]]:
        openai_ready = _credential_ready(OpenAISecretProvider())
        qwen_key = _credential_ready(QwenSecretProvider())
        yandex_ai = _credential_ready(YandexAISecretProvider())
        speech = _credential_ready(YandexSpeechSecretProvider())
        return {
            "openai": {"ready": openai_ready, "detail": "ключ не найден" if not openai_ready else ""},
            "qwen": {
                "ready": bool(qwen_key and self.qwen_base_url),
                "detail": ("ключ не найден" if not qwen_key else "Model Studio base URL не задан" if not self.qwen_base_url else ""),
            },
            "yandex": {
                "ready": bool(yandex_ai and self.yandex_folder_id),
                "detail": ("AI Studio ключ не найден" if not yandex_ai else "YANDEX_FOLDER_ID не задан" if not self.yandex_folder_id else ""),
                "speech_ready": speech,
            },
        }

    def start(self, provider: str, semantic_id: str) -> dict[str, object]:
        if provider not in PROVIDER_MODES:
            raise ValueError("неизвестный AI-провайдер")
        topic = next((item for item in self.topics if item["id"] == semantic_id), None)
        if not topic:
            raise ValueError("тема не допущена к тестовому Tutor")
        config = PrivateMultiProviderTutorConfig(
            text_provider_mode=provider,  # type: ignore[arg-type]
            qwen_base_url=self.qwen_base_url,
            yandex_folder_id=self.yandex_folder_id,
            owner_live_authorized=True,
            text_execution_enabled=True,
            speech_execution_enabled=self.speech_enabled,
        )
        assembly = assemble_private_multi_provider_tutor(engine_root=ENGINE, config=config)
        tutor_state = assembly.tutor.open_semantic_session(
            learner_profile_id="private-test-" + secrets.token_hex(6),
            semantic_id=semantic_id,
        )
        public_session = secrets.token_urlsafe(24)
        with self.lock:
            self.sessions[public_session] = LiveSession(
                assembly=assembly,
                tutor_session_ref=tutor_state.session_ref,
                provider_mode=provider,
                semantic_id=semantic_id,
                max_turns=self.max_turns,
            )
        return {"session": public_session, "topic_title": topic["title"]}

    def _session(self, public_session: str) -> LiveSession:
        with self.lock:
            session = self.sessions.get(public_session)
        if session is None:
            raise ValueError("тестовая сессия не найдена")
        if session.successful_turns >= session.max_turns:
            raise ValueError("достигнут максимум 20 успешных реплик")
        return session

    def _accept(self, session: LiveSession, interaction: Any) -> dict[str, object]:
        provider = _provider_used(interaction)
        with self.lock:
            session.successful_turns += 1
            session.provider_counts[provider] = session.provider_counts.get(provider, 0) + 1
            turns = session.successful_turns
        return {
            "text": interaction.tutor_text,
            "brain_provider": provider,
            "turns": turns,
        }

    def text(self, public_session: str, text: str) -> dict[str, object]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("сообщение пустое")
        if len(text) > MAX_MESSAGE_CHARS:
            raise ValueError(f"сообщение длиннее {MAX_MESSAGE_CHARS} символов")
        session = self._session(public_session)
        interaction = session.assembly.tutor.text_turn(session.tutor_session_ref, text.strip())
        return self._accept(session, interaction)

    def voice(self, public_session: str, encoded: str) -> dict[str, object]:
        if not self.speech_enabled:
            raise ValueError("голосовой тест не включён при запуске сервера")
        session = self._session(public_session)
        try:
            audio = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("некорректные данные микрофона") from exc
        if not audio or len(audio) > MAX_AUDIO_BYTES:
            raise ValueError("голосовая реплика пустая или слишком длинная")
        interaction = session.assembly.tutor.voice_turn(session.tutor_session_ref, audio)
        result = self._accept(session, interaction)
        result.update(
            {
                "transcript": interaction.transcript,
                "audio_b64": base64.b64encode(interaction.audio).decode("ascii") if interaction.audio else None,
                "audio_mime": "audio/mpeg",
            }
        )
        return result

    def finish(self, public_session: str) -> dict[str, object]:
        with self.lock:
            session = self.sessions.pop(public_session, None)
        if session is None:
            raise ValueError("тестовая сессия не найдена")
        counts = ", ".join(f"{name}: {count}" for name, count in sorted(session.provider_counts.items())) or "ответов нет"
        return {"turns": session.successful_turns, "provider_counts_text": f"Backend: {counts}."}


class Handler(BaseHTTPRequestHandler):
    app: App

    def log_message(self, format: str, *args: object) -> None:
        # Do not place learner text or provider response bodies in terminal logs.
        return

    def _json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("некорректный запрос") from exc
        if length <= 0 or length > 2_000_000:
            raise ValueError("некорректный размер запроса")
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("некорректный JSON") from exc
        if not isinstance(value, dict):
            raise ValueError("ожидался JSON-объект")
        return value

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            raw = PAGE.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline' data: blob:; connect-src 'self'; media-src 'self' data: blob:")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.path == "/api/status":
            self._json(
                HTTPStatus.OK,
                {
                    "max_turns": self.app.max_turns,
                    "speech_enabled": self.app.speech_enabled,
                    "topics": self.app.topics,
                    "providers": self.app.provider_status(),
                    "message_char_limit": MAX_MESSAGE_CHARS,
                },
            )
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "не найдено"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._body()
            if self.path == "/api/start":
                result = self.app.start(str(body.get("provider", "")), str(body.get("semantic_id", "")))
            elif self.path == "/api/message":
                result = self.app.text(str(body.get("session", "")), str(body.get("text", "")))
            elif self.path == "/api/voice":
                result = self.app.voice(str(body.get("session", "")), str(body.get("audio_b64", "")))
            elif self.path == "/api/finish":
                result = self.app.finish(str(body.get("session", "")))
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "не найдено"})
                return
            self._json(HTTPStatus.OK, result)
        except Exception as exc:
            # Fail closed, but never echo secret-containing reprs/tracebacks into the browser.
            message = str(exc)
            if len(message) > 400:
                message = message[:400]
            self._json(HTTPStatus.BAD_REQUEST, {"error": message or "операция не выполнена"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local Eksamio multi-provider Tutor user test")
    parser.add_argument("--owner-authorized", action="store_true", help="required explicit gate for live provider execution")
    parser.add_argument("--enable-speech", action="store_true", help="enable Yandex SpeechKit STT plus v3 Lera TTS")
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--qwen-base-url", default=None, help="non-secret Model Studio workspace base URL; never accepts a key")
    parser.add_argument("--yandex-folder-id", default=None, help="non-secret Yandex Cloud folder id")
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.owner_authorized:
        print("PRIVATE_TUTOR_TEST_UI=BLOCKED_OWNER_AUTHORIZATION")
        return 2
    if not 1 <= args.max_turns <= 20:
        print("PRIVATE_TUTOR_TEST_UI=BLOCKED_MAX_TURNS_MUST_BE_1_TO_20")
        return 2
    if not 1024 <= args.port <= 65535:
        print("PRIVATE_TUTOR_TEST_UI=BLOCKED_INVALID_PORT")
        return 2

    app = App(
        max_turns=args.max_turns,
        speech_enabled=args.enable_speech,
        qwen_base_url=args.qwen_base_url,
        yandex_folder_id=args.yandex_folder_id,
    )
    Handler.app = app
    server = ThreadingHTTPServer((HOST, args.port), Handler)
    url = f"http://{HOST}:{args.port}/"
    print(f"PRIVATE_TUTOR_TEST_UI=READY {url}")
    print("PUBLIC_TRAFFIC_ENABLED=0")
    print(f"MAX_SUCCESSFUL_LEARNER_TURNS={args.max_turns}")
    print(f"SPEECH_ENABLED={int(args.enable_speech)}")
    print("SECRETS_IN_BROWSER=0")
    print("RAW_AUDIO_PERSISTED=0")
    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
