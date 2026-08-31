#!/usr/bin/env python3
"""Shared OpenAI/Yandex human benchmark UI with resilient, half-duplex voice.

This wrapper keeps the existing benchmark UI and subject contract, but hardens
human interaction for both brains:
- transient STT/TTS retries stay below the LLM layer;
- Tutor playback and learner microphone are half-duplex;
- starting learner recording always stops any Tutor audio first;
- older Tutor audio never autoplays because of a microphone action;
- browser-facing Tutor Markdown is rendered safely instead of showing raw `*`.
"""
from __future__ import annotations

import secrets
import threading
import webbrowser
from http.server import ThreadingHTTPServer

import private_openai_yandex_121_tutor_ui as base_ui
from private_openai_yandex_121_tutor import FastTutorConfig, assemble_fast_tutor, open_benchmark_session
from resilient_speechkit_transports import RetryingBinaryTransport, RetryingStreamingJsonTransport
from stdlib_speechkit_transport import UrllibBinaryTransport
from yandex_speechkit_v3_tts import UrllibStreamingJsonTransport


def _install_half_duplex_voice_ui() -> None:
    start_marker = "async function startRec(){try{stream=await navigator.mediaDevices.getUserMedia"
    guarded_start = (
        "let activeTutorAudio=null;\n"
        "function stopTutorPlayback(){for(const a of document.querySelectorAll('audio')){"
        "try{a.pause();a.currentTime=0}catch(_){}}activeTutorAudio=null;}\n"
        "async function startRec(){try{stopTutorPlayback();await new Promise(r=>setTimeout(r,180));"
        "stream=await navigator.mediaDevices.getUserMedia"
    )
    audio_marker = (
        "if(r.audio_b64){const a=document.createElement('audio');a.controls=true;a.autoplay=true;"
        "a.src='data:audio/mpeg;base64,'+r.audio_b64;$('#messages').appendChild(a)}"
    )
    guarded_audio = (
        "if(r.audio_b64){stopTutorPlayback();const a=document.createElement('audio');a.controls=true;"
        "a.autoplay=false;a.dataset.tutorAudio='1';a.src='data:audio/mpeg;base64,'+r.audio_b64;"
        "activeTutorAudio=a;const releaseMic=()=>{if(activeTutorAudio===a)activeTutorAudio=null;"
        "if(!recording){$('#mic').disabled=false;$('#busy').textContent='';}};"
        "a.onplay=()=>{$('#mic').disabled=true;$('#busy').textContent='Tutor говорит…';};"
        "a.onended=releaseMic;a.onpause=releaseMic;a.onerror=releaseMic;"
        "$('#messages').appendChild(a);$('#mic').disabled=true;$('#busy').textContent='Tutor говорит…';"
        "const pp=a.play();if(pp&&pp.catch)pp.catch(()=>releaseMic())}"
    )
    if base_ui.PAGE.count(start_marker) != 1 or base_ui.PAGE.count(audio_marker) != 1:
        raise RuntimeError("shared half-duplex voice UI markers not found")
    base_ui.PAGE = base_ui.PAGE.replace(start_marker, guarded_start, 1)
    base_ui.PAGE = base_ui.PAGE.replace(audio_marker, guarded_audio, 1)


def _install_safe_tutor_markdown_ui() -> None:
    """Render a tiny safe Markdown subset without ever injecting provider HTML."""

    add_marker = (
        "function add(text,cls,provider){const d=document.createElement('div');d.className='msg '+cls;"
        "d.textContent=text;$('#messages').appendChild(d);if(provider){const p=document.createElement('div');"
        "p.className='provider';p.textContent=provider;$('#messages').appendChild(p)}"
        "$('#messages').scrollTop=$('#messages').scrollHeight}"
    )
    rendered_add = (
        "function renderTutorMarkdown(node,text){const s=String(text),re=/(\\*\\*[^*\\n]+\\*\\*|`[^`\\n]+`|\\*[^*\\n]+\\*)/g;"
        "let last=0,m;while((m=re.exec(s))){if(m.index>last)node.appendChild(document.createTextNode(s.slice(last,m.index)));"
        "const raw=m[0];let el;if(raw.startsWith('**')){el=document.createElement('strong');el.textContent=raw.slice(2,-2)}"
        "else if(raw.startsWith('`')){el=document.createElement('code');el.textContent=raw.slice(1,-1)}"
        "else{el=document.createElement('em');el.textContent=raw.slice(1,-1)}node.appendChild(el);last=m.index+raw.length}"
        "if(last<s.length){const tail=s.slice(last).replace(/\\*\\*/g,'').replace(/\\*/g,'').replace(/`/g,'');"
        "node.appendChild(document.createTextNode(tail))}}\n"
        "function add(text,cls,provider){const d=document.createElement('div');d.className='msg '+cls;"
        "if(cls==='tutor')renderTutorMarkdown(d,text);else d.textContent=text;$('#messages').appendChild(d);"
        "if(provider){const p=document.createElement('div');p.className='provider';p.textContent=provider;"
        "$('#messages').appendChild(p)}$('#messages').scrollTop=$('#messages').scrollHeight}"
    )
    if base_ui.PAGE.count(add_marker) != 1:
        raise RuntimeError("safe Tutor Markdown UI marker not found")
    base_ui.PAGE = base_ui.PAGE.replace(add_marker, rendered_add, 1)


_install_half_duplex_voice_ui()
_install_safe_tutor_markdown_ui()


class ResilientHumanApp(base_ui.App):
    def start(self, provider: str, mode: str) -> dict[str, object]:
        if provider not in base_ui.PROVIDERS or mode not in base_ui.RUN_MODES:
            raise ValueError("unknown benchmark provider/mode")
        status = self.status()
        providers = status["providers"]
        if not isinstance(providers, dict) or not providers[provider]["ready"]:  # type: ignore[index]
            raise ValueError(f"{provider} credential/config preflight BLOCKED")
        if mode == "voice" and not status["speech_ready"]:
            raise ValueError("Yandex SpeechKit credential preflight BLOCKED")

        config = FastTutorConfig(
            brain_mode=provider,  # type: ignore[arg-type]
            yandex_folder_id=self.yandex_folder_id,
            owner_live_authorized=True,
            text_execution_enabled=True,
            speech_execution_enabled=mode == "voice",
        )
        stt_transport = RetryingBinaryTransport(UrllibBinaryTransport())
        tts_transport = RetryingStreamingJsonTransport(UrllibStreamingJsonTransport())
        assembly = assemble_fast_tutor(
            engine_root=base_ui.ENGINE,
            config=config,
            stt_transport=stt_transport,
            tts_v3_transport=tts_transport,
        )
        learner_profile_id = "private-fast-human-" + secrets.token_hex(6)
        tutor_state = open_benchmark_session(assembly, learner_profile_id)
        public_session = secrets.token_urlsafe(24)
        with self.lock:
            self.sessions[public_session] = base_ui.LiveSession(
                assembly=assembly,
                tutor_session_ref=tutor_state.session_ref,
                provider=provider,
                run_mode=mode,
                model=assembly.exact_brain_model,
            )
        return {
            "session": public_session,
            "provider": provider,
            "mode": mode,
            "model": assembly.exact_brain_model,
            "semantic_id": tutor_state.grounding.semantic_id,
        }


def main() -> int:
    args = base_ui.parse_args()
    if not args.owner_authorized:
        print("FAST_TUTOR_UI=BLOCKED_OWNER_AUTHORIZATION")
        return 2
    if not 1024 <= args.port <= 65535:
        print("FAST_TUTOR_UI=BLOCKED_INVALID_PORT")
        return 2

    app = ResilientHumanApp(yandex_folder_id=args.yandex_folder_id)
    base_ui.Handler.app = app
    server = ThreadingHTTPServer((base_ui.HOST, args.port), base_ui.Handler)
    url = f"http://{base_ui.HOST}:{args.port}/"
    print(f"FAST_TUTOR_UI=READY {url}")
    print("BRAIN_PROVIDERS=openai,yandex")
    print("SPEECHKIT_TRANSIENT_RETRIES=2")
    print("VOICE_HALF_DUPLEX=1")
    print("TUTOR_PLAYBACK_MIC_OVERLAP=BLOCKED")
    print("TUTOR_SPEECH_TEXT_NORMALIZATION=1")
    print("TUTOR_VISIBLE_MARKDOWN_RENDERING=SAFE")
    print("PUBLIC_TRAFFIC_ENABLED=0")
    print("PRODUCTION_PEIS_WRITES_ENABLED=0")
    print("PERSISTENT_EVIDENCE=0")
    print("RAW_AUDIO_PERSISTED_BYTES=0")
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
