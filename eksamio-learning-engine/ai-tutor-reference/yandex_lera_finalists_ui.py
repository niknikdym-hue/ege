#!/usr/bin/env python3
"""Local-only A/B final for two Yandex Lera native profiles on one fixed text."""
from __future__ import annotations

import argparse
import base64
import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Mapping

from yandex_lera_casting_ui import ENDPOINT, prepare_casting_speech
from yandex_live_adapters import CredentialKind, YandexCredential
from yandex_speech_secret_provider import YandexSpeechSecretProvider
from yandex_speechkit_v3_tts import UrllibStreamingJsonTransport, YandexSpeechKitV3TTS

HOST = "127.0.0.1"
PORT = 8769
TEXT = (
    "Ваши рассуждения верны в том, что в однокоренных словах обычно сохраняется одна и та же гласная в корне. "
    "Но в случае с «сочетание»/«сочетать» нужно помнить: это исключение из правила для корней ЧЕТ‑/ЧИТ‑. "
    "Несмотря на наличие буквы «а» после корня, в них пишется «е», а не «и». "
    "Запомните эту пару как особый случай."
)
FINALISTS = {
    "A": {"label": "A · neutral / 1.04 / 0 Hz / marked", "role": "neutral", "speed": 1.04, "pitch": 0.0},
    "D": {"label": "D · friendly / 0.97 / −35 Hz / marked", "role": "friendly", "speed": 0.97, "pitch": -35.0},
}
MAX_CALLS = 40


class App:
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
        return {"ready": ready, "text": TEXT, "finalists": FINALISTS, "remaining": MAX_CALLS - self.calls}

    def synthesize(self, finalist: str) -> dict[str, object]:
        p = FINALISTS.get(finalist)
        if p is None:
            raise ValueError("unknown finalist")
        with self.lock:
            if self.calls >= MAX_CALLS:
                raise ValueError("finalist synthesis call cap reached")
            self.calls += 1
            call = self.calls
        spoken = prepare_casting_speech(TEXT, "marked")
        body: Mapping[str, object] = {
            "text": spoken,
            "hints": [
                {"voice": "lera"},
                {"role": str(p["role"])},
                {"speed": f'{float(p["speed"]):.2f}'},
                {"pitchShift": f'{float(p["pitch"]):.1f}'},
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
            encoded = YandexSpeechKitV3TTS._audio_data(item)
            if encoded:
                audio.extend(base64.b64decode(encoded, validate=True))
        if not audio:
            raise RuntimeError("SpeechKit returned no audio")
        return {
            "audio_b64": base64.b64encode(bytes(audio)).decode("ascii"),
            "finalist": finalist,
            "label": p["label"],
            "call": call,
            "remaining": MAX_CALLS - call,
            "brain_calls": 0,
            "persistent_audio_bytes": 0,
        }


PAGE = r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Лера — финал A vs D</title><style>:root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#182230;background:#f5f7fb}*{box-sizing:border-box}body{margin:0}.wrap{max-width:900px;margin:auto;padding:24px}.box{background:white;border:1px solid #dde3ec;border-radius:18px;padding:22px}.text{padding:16px;background:#f8f8ff;border-radius:12px;line-height:1.55;margin:18px 0}.buttons{display:grid;grid-template-columns:1fr 1fr;gap:12px}.b{border:0;border-radius:12px;padding:14px;font-weight:750;cursor:pointer;background:#eef1f5}.b:hover{outline:2px solid #4d56d8}.result{margin-top:16px}.muted{color:#667085}audio{width:100%;margin-top:8px}@media(max-width:650px){.buttons{grid-template-columns:1fr}.wrap{padding:8px}}</style></head><body><main class="wrap"><section class="box"><h1>Лера — финал A vs D</h1><div class="muted">Один и тот же текст. Только Yandex SpeechKit. Никаких LLM-вызовов.</div><div id="text" class="text"></div><div class="buttons"><button id="A" class="b">▶ A · neutral / 1.04 / 0 / marked</button><button id="D" class="b">▶ D · friendly / 0.97 / −35 / marked</button></div><div id="status" class="muted" style="margin-top:12px"></div><div class="result"><div id="meta" class="muted"></div><audio id="audio" controls></audio></div></section></main><script>
const $=s=>document.querySelector(s);let remaining=0;
async function boot(){const r=await fetch('/api/status');const s=await r.json();$('#text').textContent=s.text;remaining=s.remaining;$('#status').textContent=s.ready?`SpeechKit READY · осталось ${remaining} прослушиваний`:'SpeechKit BLOCKED';$('#A').disabled=$('#D').disabled=!s.ready;}
async function play(id){$('#A').disabled=$('#D').disabled=true;$('#status').textContent=`Синтезирую ${id}…`;try{const r=await fetch('/api/synthesize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({finalist:id})});const j=await r.json();if(!r.ok)throw new Error(j.error||'Ошибка');$('#audio').src='data:audio/mpeg;base64,'+j.audio_b64;$('#audio').play();$('#meta').textContent=j.label;remaining=j.remaining;$('#status').textContent=`Готово · осталось ${remaining}. Прослушай A и D несколько раз и выбери победителя.`;}catch(e){$('#status').textContent=e.message}finally{$('#A').disabled=$('#D').disabled=false}}
$('#A').onclick=()=>play('A');$('#D').onclick=()=>play('D');boot();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    app: App
    def log_message(self, format: str, *args: object) -> None: return
    def _json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        raw=json.dumps(payload,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
    def do_GET(self) -> None:  # noqa: N802
        if self.path=='/':
            raw=PAGE.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Security-Policy',"default-src 'self' 'unsafe-inline' data:; connect-src 'self'; media-src 'self' data:");self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
        if self.path=='/api/status': self._json(HTTPStatus.OK,self.app.status());return
        self._json(HTTPStatus.NOT_FOUND,{'error':'not found'})
    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path!='/api/synthesize': self._json(HTTPStatus.NOT_FOUND,{'error':'not found'});return
            length=int(self.headers.get('Content-Length','0'));body=json.loads(self.rfile.read(length).decode());self._json(HTTPStatus.OK,self.app.synthesize(str(body.get('finalist',''))))
        except Exception as exc: self._json(HTTPStatus.BAD_REQUEST,{'error':str(exc)[:300]})


def main() -> int:
    p=argparse.ArgumentParser();p.add_argument('--owner-authorized',action='store_true');p.add_argument('--no-browser',action='store_true');args=p.parse_args()
    if not args.owner_authorized: print('YANDEX_LERA_FINALISTS=BLOCKED_OWNER_AUTHORIZATION');return 2
    app=App();Handler.app=app;server=ThreadingHTTPServer((HOST,PORT),Handler);url=f'http://{HOST}:{PORT}/';print(f'YANDEX_LERA_FINALISTS=READY {url}');print('FINALISTS=A,D');print('BRAIN_CALLS=0');print('PERSISTENT_AUDIO_BYTES=0')
    if not args.no_browser: threading.Timer(0.4,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
    return 0


if __name__=='__main__': raise SystemExit(main())
