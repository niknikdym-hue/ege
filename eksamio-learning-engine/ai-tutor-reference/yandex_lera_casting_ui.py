#!/usr/bin/env python3
"""Local-only Yandex Lera casting page for native SpeechKit v3 settings.

No Tutor brain or LLM is called. The owner listens to one fixed difficult
Russian pedagogical phrase while varying only Yandex-native TTS controls:
Lera role, speed, pitchShift and pause profile. Audio is returned transiently
and never written to disk.
"""
from __future__ import annotations

import argparse
import base64
import json
import secrets
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping

from yandex_lera_native_clean import prepare_yandex_lera_native_speech
from yandex_live_adapters import CredentialKind, YandexCredential
from yandex_speech_secret_provider import YandexSpeechSecretProvider
from yandex_speechkit_v3_tts import UrllibStreamingJsonTransport, YandexSpeechKitV3TTS

HOST = "127.0.0.1"
DEFAULT_PORT = 8768
MAX_SYNTHESIS_CALLS = 30
ENDPOINT = "https://tts.api.cloud.yandex.net/tts/v3/utteranceSynthesis"

CASTING_TEXT = (
    "Вы почти правы, но здесь особый случай. "
    "В корнях ЧЕТ‑/ЧИТ‑ обычно перед буквой «а» пишется «и», однако слово «сочетание» — "
    "исключение, в нём сохраняется буква «е»."
)

PRESETS: dict[str, dict[str, object]] = {
    "A": {"label": "A · Нейтральная база", "role": "neutral", "speed": 1.04, "pitch": 0.0, "pauses": "balanced"},
    "B": {"label": "B · Спокойная дикторская", "role": "neutral", "speed": 1.00, "pitch": -20.0, "pauses": "light"},
    "C": {"label": "C · Мягкая учебная", "role": "friendly", "speed": 1.00, "pitch": -20.0, "pauses": "light"},
    "D": {"label": "D · Медленнее и ниже", "role": "friendly", "speed": 0.97, "pitch": -35.0, "pauses": "balanced"},
    "E": {"label": "E · Чёткая нейтральная", "role": "neutral", "speed": 1.00, "pitch": -10.0, "pauses": "marked"},
    "F": {"label": "F · Живая дружелюбная", "role": "friendly", "speed": 1.03, "pitch": -10.0, "pauses": "light"},
}


def _pause_variant(text: str, profile: str) -> str:
    if profile == "light":
        # Prefer Yandex context-sensitive pauses over fixed silence.
        text = text.replace("sil<[260]>", "<[small]>")
        text = text.replace("<[medium]>", "<[small]>")
        return text
    if profile == "marked":
        # Keep sentence boundary and make contrastive boundaries more explicit.
        text = text.replace("<[small]>", "<[medium]>")
        return text
    if profile == "balanced":
        return text
    raise ValueError("unknown pause profile")


def prepare_casting_speech(text: str, pauses: str) -> str:
    return _pause_variant(prepare_yandex_lera_native_speech(text), pauses)


def _audio_data(item: Mapping[str, object]) -> str | None:
    return YandexSpeechKitV3TTS._audio_data(item)


class CastingApp:
    def __init__(self) -> None:
        self.transport = UrllibStreamingJsonTransport()
        self.credential = YandexCredential(CredentialKind.API_KEY, YandexSpeechSecretProvider())
        self.calls = 0
        self.lock = threading.Lock()

    def status(self) -> dict[str, object]:
        try:
            ready = bool(YandexSpeechSecretProvider()().strip())
        except Exception:
            ready = False
        return {
            "ready": ready,
            "text": CASTING_TEXT,
            "presets": PRESETS,
            "max_calls": MAX_SYNTHESIS_CALLS,
            "calls": self.calls,
            "brain_calls": 0,
            "persistent_audio_bytes": 0,
        }

    def synthesize(self, role: str, speed: float, pitch: float, pauses: str) -> dict[str, object]:
        if role not in {"neutral", "friendly"}:
            raise ValueError("Lera role must be neutral or friendly")
        if not 0.90 <= speed <= 1.12:
            raise ValueError("casting speed must be in [0.90, 1.12]")
        if not -100.0 <= pitch <= 100.0:
            raise ValueError("casting pitchShift must be in [-100, 100] Hz")
        if pauses not in {"light", "balanced", "marked"}:
            raise ValueError("unknown pause profile")
        with self.lock:
            if self.calls >= MAX_SYNTHESIS_CALLS:
                raise ValueError("casting synthesis call cap reached")
            self.calls += 1
            call_no = self.calls

        spoken = prepare_casting_speech(CASTING_TEXT, pauses)
        body: Mapping[str, object] = {
            "text": spoken,
            "hints": [
                {"voice": "lera"},
                {"role": role},
                {"speed": f"{speed:.2f}"},
                {"pitchShift": f"{pitch:.1f}"},
            ],
            "outputAudioSpec": {"containerAudio": {"containerAudioType": "MP3"}},
            "loudnessNormalizationType": "LUFS",
        }
        responses = self.transport.post_json_stream(
            url=ENDPOINT,
            headers={"Authorization": self.credential.authorization_header()},
            body=body,
            timeout_seconds=30.0,
        )
        audio = bytearray()
        for item in responses:
            encoded = _audio_data(item)
            if encoded:
                audio.extend(base64.b64decode(encoded, validate=True))
        if not audio:
            raise RuntimeError("SpeechKit v3 returned no casting audio")
        return {
            "audio_b64": base64.b64encode(bytes(audio)).decode("ascii"),
            "role": role,
            "speed": speed,
            "pitch": pitch,
            "pauses": pauses,
            "call": call_no,
            "brain_calls": 0,
            "persistent_audio_bytes": 0,
        }


PAGE = r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Кастинг Леры — Яндекс</title><style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#172033;background:#f6f7fb;--line:#dfe4ec;--brand:#4d56d8}*{box-sizing:border-box}body{margin:0}.wrap{max-width:900px;margin:auto;padding:24px}.box{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 14px 40px rgba(30,40,70,.08)}h1{margin:0 0 8px}.muted{color:#667085;line-height:1.45}.text{margin:18px 0;padding:16px;border-radius:12px;background:#f8f8ff;border:1px solid #e1e2fa;line-height:1.55}.presets{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.preset,.play{border:0;border-radius:11px;padding:11px 13px;font-weight:700;cursor:pointer}.preset{background:#eef1f5}.preset.active{outline:2px solid var(--brand)}.controls{display:grid;gap:14px;margin:18px 0}.row{display:grid;grid-template-columns:180px 1fr 80px;gap:10px;align-items:center}.play{background:var(--brand);color:white}.status{margin-top:12px;color:#667085}.result{margin-top:16px;padding:14px;border:1px solid var(--line);border-radius:12px}audio{width:100%}@media(max-width:650px){.presets{grid-template-columns:1fr}.row{grid-template-columns:1fr}.wrap{padding:8px}}</style></head><body><main class="wrap"><section class="box"><h1>Кастинг Леры — Яндекс</h1><div class="muted">Только Yandex SpeechKit v3. OpenAI и Tutor-мозг не вызываются. Слушаем один и тот же сложный абзац и выбираем чистые настройки Леры.</div><div id="text" class="text"></div><div id="presets" class="presets"></div><div class="controls"><div class="row"><label>Амплуа</label><select id="role"><option value="neutral">neutral</option><option value="friendly">friendly</option></select><span></span></div><div class="row"><label>Скорость</label><input id="speed" type="range" min="0.90" max="1.12" step="0.01" value="1.04"><output id="speedOut">1.04</output></div><div class="row"><label>Высота pitchShift</label><input id="pitch" type="range" min="-100" max="100" step="5" value="0"><output id="pitchOut">0 Hz</output></div><div class="row"><label>Паузы</label><select id="pauses"><option value="light">light — мягкие</option><option value="balanced">balanced — базовые</option><option value="marked">marked — выраженные</option></select><span></span></div></div><button id="play" class="play">▶ Синтезировать и послушать</button><div id="status" class="status"></div><div id="result" class="result" hidden><div id="meta" class="muted"></div><audio id="audio" controls autoplay></audio></div></section></main><script>
const $=s=>document.querySelector(s);let presets={};
function sync(){ $('#speedOut').textContent=Number($('#speed').value).toFixed(2);$('#pitchOut').textContent=`${$('#pitch').value} Hz`;}
$('#speed').oninput=sync;$('#pitch').oninput=sync;
function applyPreset(id){const p=presets[id];if(!p)return;$('#role').value=p.role;$('#speed').value=p.speed;$('#pitch').value=p.pitch;$('#pauses').value=p.pauses;sync();document.querySelectorAll('.preset').forEach(b=>b.classList.toggle('active',b.dataset.id===id));}
async function boot(){const r=await fetch('/api/status');const s=await r.json();$('#text').textContent=s.text;presets=s.presets;for(const [id,p] of Object.entries(presets)){const b=document.createElement('button');b.className='preset';b.dataset.id=id;b.textContent=p.label;b.onclick=()=>applyPreset(id);$('#presets').appendChild(b)}applyPreset('A');$('#status').textContent=s.ready?`SpeechKit READY · лимит ${s.max_calls} проб`:'SpeechKit BLOCKED';$('#play').disabled=!s.ready;}
$('#play').onclick=async()=>{const body={role:$('#role').value,speed:Number($('#speed').value),pitch:Number($('#pitch').value),pauses:$('#pauses').value};$('#play').disabled=true;$('#status').textContent='Лера синтезирует…';try{const r=await fetch('/api/synthesize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw new Error(j.error||'Ошибка');$('#audio').src='data:audio/mpeg;base64,'+j.audio_b64;$('#meta').textContent=`role=${j.role} · speed=${j.speed.toFixed(2)} · pitch=${j.pitch} Hz · pauses=${j.pauses} · проба ${j.call}`;$('#result').hidden=false;$('#status').textContent='Готово. Если нравится — запиши мне букву профиля или эти четыре значения.';}catch(e){$('#status').textContent=e.message}finally{$('#play').disabled=false}};
boot();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    app: CastingApp
    def log_message(self, format: str, *args: object) -> None: return
    def _json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        raw=json.dumps(payload,ensure_ascii=False).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self) -> None:  # noqa: N802
        if self.path=='/':
            raw=PAGE.encode('utf-8');self.send_response(HTTPStatus.OK);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'self' 'unsafe-inline' data:; connect-src 'self'; media-src 'self' data:");self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path=='/api/status': self._json(HTTPStatus.OK,self.app.status());return
        self._json(HTTPStatus.NOT_FOUND,{'error':'not found'})
    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path!='/api/synthesize': self._json(HTTPStatus.NOT_FOUND,{'error':'not found'});return
            length=int(self.headers.get('Content-Length','0'));body=json.loads(self.rfile.read(length).decode('utf-8'))
            result=self.app.synthesize(str(body.get('role','')),float(body.get('speed',0)),float(body.get('pitch',0)),str(body.get('pauses','')))
            self._json(HTTPStatus.OK,result)
        except Exception as exc: self._json(HTTPStatus.BAD_REQUEST,{'error':str(exc)[:300] or 'operation failed'})


def parse_args() -> argparse.Namespace:
    p=argparse.ArgumentParser();p.add_argument('--owner-authorized',action='store_true');p.add_argument('--port',type=int,default=DEFAULT_PORT);p.add_argument('--no-browser',action='store_true');return p.parse_args()


def main() -> int:
    args=parse_args()
    if not args.owner_authorized:
        print('YANDEX_LERA_CASTING=BLOCKED_OWNER_AUTHORIZATION');return 2
    app=CastingApp();Handler.app=app;server=ThreadingHTTPServer((HOST,args.port),Handler);url=f'http://{HOST}:{args.port}/';print(f'YANDEX_LERA_CASTING=READY {url}');print('BRAIN_CALLS=0');print('PERSISTENT_AUDIO_BYTES=0');print(f'MAX_SYNTHESIS_CALLS={MAX_SYNTHESIS_CALLS}')
    if not args.no_browser: threading.Timer(0.4,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0


if __name__=='__main__': raise SystemExit(main())
