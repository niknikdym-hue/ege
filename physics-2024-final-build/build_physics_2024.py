#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import shutil
import zipfile
from pathlib import Path

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(__file__).resolve().parent
EVIDENCE = ROOT / "physics-2024-evidence"
SOURCE = ROOT / "ege-source-fizika/source-fizika-2024/ege-2024-fizika-demoversiya.pdf"
LAYOUT = EVIDENCE / "PHYSICS-2024-SOURCE-LAYOUT-MAP.json"
SCORER = EVIDENCE / "PHYSICS-2024-ANSWER-SCORER-SPEC.json"
OUT = BUILD / "out" / "ege-fizika-demoversiya-2024-v1.0-TILDA-HQ-SOURCE"
DIST = BUILD / "dist"
ZIP = DIST / "ege-fizika-demoversiya-2024-v1.0-TILDA-HQ-SOURCE.zip"
PREFIX = "ege-fizika-demoversiya-2024"
EXPECTED_SOURCE_SHA = "746903cadd391a52948aea59155f713c7677521ba22b52c369d2473fb0fc2057"
T123_LIMIT = 42500
PAYLOAD_CHUNK = 39000
MAX_T123_COUNT = 80
EXPECTED_PAGE_SIZE = (2339, 1654)
HALF_X = EXPECTED_PAGE_SIZE[0] // 2


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def render_page(doc: fitz.Document, physical_page: int) -> Image.Image:
    page = doc[physical_page - 1]
    pix = page.get_pixmap(dpi=200, alpha=False)
    image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    if image.size != EXPECTED_PAGE_SIZE:
        raise RuntimeError(f"physical page {physical_page}: raster size {image.size}, expected {EXPECTED_PAGE_SIZE}")
    return image


def webp_bytes(image: Image.Image, max_width: int = 1000) -> tuple[bytes, Image.Image]:
    output = image.copy()
    if output.width > max_width:
        height = round(output.height * max_width / output.width)
        output = output.resize((max_width, height), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    output.save(buf, format="WEBP", quality=90, method=6, exact=True)
    return buf.getvalue(), output


def asset_script(key: str, b64: str, first: bool) -> str:
    op = "=" if first else "+="
    return f'<script>window.EP24_A=window.EP24_A||{{}};EP24_A[{json.dumps(key)}]{op}{json.dumps(b64)};</script>\n'


def html_escape_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def build_assets(layout: dict, scorer: dict) -> tuple[dict[str, str], list[dict]]:
    doc = fitz.open(SOURCE)
    cache: dict[int, Image.Image] = {}
    assets: dict[str, str] = {}
    manifest: list[dict] = []

    def page(n: int) -> Image.Image:
        if n not in cache:
            cache[n] = render_page(doc, n)
        return cache[n]

    for task in layout["tasks"]:
        n = int(task["task_number"])
        p = int(task["physical_page"])
        box = tuple(int(v) for v in task["task_region_200dpi_pixels"])
        source_crop = page(p).crop(box)
        raw, encoded_image = webp_bytes(source_crop, max_width=1000)
        key = f"task-{n:02d}"
        assets[key] = base64.b64encode(raw).decode("ascii")
        manifest.append({
            "key": key,
            "kind": "task_source_region",
            "task": n,
            "physical_page": p,
            "source_crop_200dpi_pixels": list(box),
            "encoded_width": encoded_image.width,
            "encoded_height": encoded_image.height,
            "mime": "image/webp",
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
        })

    # Official solution/criteria content is kept as individual logical half-pages.
    # This is source-rendered content, not OCR or retyped prose, while staying practical for Tilda.
    seen_criteria: set[tuple[int, int]] = set()
    for ext in scorer["extended_tasks"]:
        n = int(ext["task_number"])
        for logical_page in ext["criteria_logical_pages"]:
            logical_page = int(logical_page)
            physical_page = (logical_page + 1) // 2
            pair = (n, logical_page)
            if pair in seen_criteria:
                continue
            seen_criteria.add(pair)
            if logical_page % 2:
                box = (0, 0, HALF_X, EXPECTED_PAGE_SIZE[1])
            else:
                box = (HALF_X, 0, EXPECTED_PAGE_SIZE[0], EXPECTED_PAGE_SIZE[1])
            source_crop = page(physical_page).crop(box)
            raw, encoded_image = webp_bytes(source_crop, max_width=1000)
            key = f"criteria-{n:02d}-logical-{logical_page:03d}"
            assets[key] = base64.b64encode(raw).decode("ascii")
            manifest.append({
                "key": key,
                "kind": "official_solution_criteria_logical_page",
                "task": n,
                "logical_page": logical_page,
                "physical_page": physical_page,
                "source_crop_200dpi_pixels": list(box),
                "encoded_width": encoded_image.width,
                "encoded_height": encoded_image.height,
                "mime": "image/webp",
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
            })

    if len([m for m in manifest if m["kind"] == "task_source_region"]) != 26:
        raise RuntimeError("task source raster count != 26")
    if len([m for m in manifest if m["kind"] == "official_solution_criteria_logical_page"]) != 17:
        raise RuntimeError("criteria logical page count != 17")
    return assets, manifest


def head_html() -> str:
    return '''<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Демоверсия ЕГЭ 2024 по физике — ФИПИ | Эксамио</title>
<meta name="description" content="Интерактивная демоверсия ЕГЭ 2024 по физике по официальным материалам ФИПИ: 26 заданий, проверка кратких ответов и самооценка заданий с развёрнутым ответом.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://eksamio.ru/ege/fizika/demoversiya/2024/">
<meta property="og:type" content="website">
<meta property="og:title" content="Демоверсия ЕГЭ 2024 по физике — ФИПИ | Эксамио">
<meta property="og:description" content="Интерактивная демоверсия ЕГЭ 2024 по физике по официальным материалам ФИПИ.">
<meta property="og:url" content="https://eksamio.ru/ege/fizika/demoversiya/2024/">
'''


def app_shell() -> str:
    return r'''<style>
#ep24{--ink:#172033;--muted:#667085;--line:#e5e7eb;--soft:#f7f8fb;--accent:#3157d5;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--ink);max-width:980px;margin:0 auto;padding:24px 16px 72px;box-sizing:border-box}
#ep24 *{box-sizing:border-box}#ep24 button,#ep24 input,#ep24 textarea{font:inherit}.ep24-hero{background:linear-gradient(135deg,#f4f7ff,#fff);border:1px solid #dfe6ff;border-radius:24px;padding:28px;margin-bottom:20px}.ep24-kicker{font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#3157d5}.ep24-hero h1{font-size:clamp(28px,5vw,46px);line-height:1.08;margin:8px 0 12px}.ep24-hero p{font-size:16px;line-height:1.55;color:var(--muted);max-width:760px}.ep24-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.ep24-chip{background:#fff;border:1px solid var(--line);border-radius:999px;padding:8px 12px;font-size:14px}.ep24-toolbar{position:sticky;top:8px;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:16px;padding:10px 12px;display:flex;gap:10px;align-items:center;justify-content:space-between;margin:0 0 20px;box-shadow:0 8px 24px rgba(16,24,40,.06)}.ep24-progress{font-weight:700}.ep24-timer{font-variant-numeric:tabular-nums;color:var(--muted)}.ep24-card{border:1px solid var(--line);border-radius:20px;background:#fff;padding:18px;margin:0 0 16px;box-shadow:0 2px 10px rgba(16,24,40,.035)}.ep24-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.ep24-card-head h2{font-size:19px;margin:0}.ep24-points{font-size:13px;color:var(--muted);white-space:nowrap}.ep24-source{display:block;width:100%;height:auto;border:1px solid #eceff3;border-radius:12px;background:#fff}.ep24-answer{margin-top:14px}.ep24-answer label{display:block;font-weight:650;margin-bottom:7px}.ep24-answer input,.ep24-answer textarea{width:100%;border:1px solid #cfd4dc;border-radius:12px;padding:12px 13px;background:#fff;color:var(--ink);outline:none}.ep24-answer textarea{min-height:132px;resize:vertical}.ep24-answer input:focus,.ep24-answer textarea:focus{border-color:#7b94ec;box-shadow:0 0 0 3px rgba(49,87,213,.1)}.ep24-actions{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0}.ep24-btn{appearance:none;border:0;border-radius:12px;padding:12px 17px;font-weight:700;cursor:pointer}.ep24-btn-primary{background:var(--accent);color:#fff}.ep24-btn-secondary{background:#eef2ff;color:#2548be}.ep24-btn:disabled{opacity:.45;cursor:not-allowed}.ep24-results{display:none}.ep24-results.is-open{display:block}.ep24-result-hero{border-radius:22px;padding:24px;background:#111827;color:#fff;margin-bottom:18px}.ep24-score{font-size:clamp(34px,7vw,58px);font-weight:800;line-height:1}.ep24-result-hero p{color:#d1d5db}.ep24-section{margin:28px 0 12px}.ep24-section h2{font-size:24px;margin:0 0 6px}.ep24-section p{color:var(--muted);line-height:1.5}.ep24-review{border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:10px 0}.ep24-review[data-correct="true"]{border-color:#a6d8c3;background:#f2fbf6}.ep24-review[data-correct="false"]{border-color:#f5c3bd;background:#fff8f7}.ep24-review h3{margin:0 0 8px;font-size:16px}.ep24-review p{margin:5px 0;line-height:1.4}.ep24-self{border:1px solid var(--line);border-radius:18px;padding:16px;margin:14px 0}.ep24-self-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.ep24-self h3{margin:0}.ep24-score-buttons{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0}.ep24-score-btn{border:1px solid #cfd4dc;background:#fff;border-radius:10px;padding:8px 12px;cursor:pointer;font-weight:700}.ep24-score-btn.is-on{background:#3157d5;border-color:#3157d5;color:#fff}.ep24-criteria details{margin-top:12px}.ep24-criteria summary{cursor:pointer;font-weight:700}.ep24-criteria img{display:block;width:100%;height:auto;border:1px solid #e5e7eb;border-radius:12px;margin-top:10px}.ep24-note{font-size:13px;color:var(--muted)}.ep24-footer-note{margin-top:28px;padding:16px;border-radius:14px;background:var(--soft);color:var(--muted);font-size:13px;line-height:1.5}@media(max-width:560px){#ep24{padding:14px 10px 56px}.ep24-hero{padding:20px 16px;border-radius:18px}.ep24-card{padding:12px;border-radius:16px}.ep24-toolbar{top:4px}.ep24-card-head,.ep24-self-head{align-items:flex-start}.ep24-source{border-radius:8px}.ep24-btn{width:100%}}
</style>
<div id="ep24"><section class="ep24-hero"><div class="ep24-kicker">Эксамио · Физика</div><h1>Демоверсия ЕГЭ 2024</h1><p>Все формулировки, формулы, обозначения, таблицы и рисунки заданий показываются как растровые фрагменты, непосредственно сформированные из официальной демоверсии ФИПИ 2024. Задания 1–20 проверяются автоматически; задания 21–26 оцениваются по официальным решениям и критериям.</p><div class="ep24-meta"><span class="ep24-chip">26 заданий</span><span class="ep24-chip">235 минут</span><span class="ep24-chip">максимум 45 баллов</span><span class="ep24-chip">официальный источник: ФИПИ 2024</span></div></section><div class="ep24-toolbar"><div class="ep24-progress" id="ep24-progress">Заполнено 0 из 26</div><div class="ep24-timer" id="ep24-timer">03:55:00</div></div><main id="ep24-tasks"></main><div class="ep24-actions" id="ep24-actions"><button class="ep24-btn ep24-btn-primary" id="ep24-finish" type="button">Завершить и проверить</button><button class="ep24-btn ep24-btn-secondary" id="ep24-reset" type="button">Сбросить ответы</button></div><section class="ep24-results" id="ep24-results"><div class="ep24-result-hero"><div class="ep24-score" id="ep24-total">— / 45</div><p id="ep24-result-copy">Сначала оцените задания 21–26.</p></div><div class="ep24-section" data-section="short-review"><h2>Проверка заданий 1–20</h2><p>Баллы рассчитаны по официальным правилам демоверсии ФИПИ 2024, включая частичный балл для заданий с выбором и установлением соответствия.</p></div><div id="ep24-short-review"></div><div class="ep24-section" data-section="self-assessment"><h2>Самооценка заданий 21–26</h2><p>Сравните своё решение с официальным возможным решением и критериями ФИПИ, затем выберите балл. Итог появится после оценки всех шести заданий.</p></div><div id="ep24-self"></div></section><div class="ep24-footer-note">Источник содержания: официальная демоверсия ЕГЭ 2024 по физике ФИПИ. Встроенные изображения заданий и критериев сформированы непосредственно из канонического PDF без переноса содержания из других лет.</div></div><script>window.EP24_A=window.EP24_A||{};</script>
'''


def runtime_js(scorer: dict) -> str:
    short_json = html_escape_json(scorer["short_tasks"])
    ext_json = html_escape_json(scorer["extended_tasks"])
    return rf'''<script>
(function(){{
"use strict";
var SHORT={short_json}, EXT={ext_json}, KEY="eksamio.physics.2024.demo.v1", MAX=45, SHORT_MAX=28, DURATION=235*60;
var state={{answers:{{}},self:{{}},startedAt:Date.now(),finished:false}};
function byId(x){{return document.getElementById(x)}}
function load(){{try{{var s=JSON.parse(localStorage.getItem(KEY)||"null");if(s&&typeof s==="object")state=Object.assign(state,s)}}catch(e){{}}}}
function save(){{localStorage.setItem(KEY,JSON.stringify(state))}}
function esc(s){{return String(s==null?"":s).replace(/[&<>\"]/g,function(c){{return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]}})}}
function normBase(s){{return String(s==null?"":s).trim().replace(/[−–—]/g,"-")}}
function exactScore(t,a){{var x=normBase(a),y=normBase(t.official_answer);if(t.normalization&&t.normalization.decimal_comma_is_canonical)x=x.replace(/\./g,",");return x===y?t.max_points:0}}
function digits(s){{return normBase(s).replace(/[^0-9]/g,"")}}
function unorderedScore(t,a){{var x=digits(a),y=digits(t.official_answer);if(!x||new Set(x).size!==x.length)return 0;var A=new Set(x),B=new Set(y),missing=0,extra=0;B.forEach(function(v){{if(!A.has(v))missing++}});A.forEach(function(v){{if(!B.has(v))extra++}});if(missing===0&&extra===0)return t.max_points;if(t.max_points===2&&((missing===1&&extra===0)||(missing===0&&extra===1)))return 1;return 0}}
function positionalScore(t,a){{var x=digits(a),y=digits(t.official_answer);if(x.length!==y.length)return 0;var wrong=0;for(var i=0;i<y.length;i++)if(x[i]!==y[i])wrong++;if(wrong===0)return t.max_points;if(t.max_points===2&&wrong===1)return 1;return 0}}
function score(t,a){{return t.compare_mode==="unordered_selection"?unorderedScore(t,a):t.compare_mode==="positional_sequence"?positionalScore(t,a):exactScore(t,a)}}
window.EP24_TEST_SCORE=function(n,a){{var t=SHORT.find(function(x){{return x.task_number===n}});return score(t,a)}};
function taskImage(n){{return "data:image/webp;base64,"+EP24_A["task-"+String(n).padStart(2,"0")]}}
function renderTasks(){{var w=byId("ep24-tasks");w.innerHTML="";for(var n=1;n<=26;n++){{var st=SHORT.find(function(x){{return x.task_number===n}}),ex=EXT.find(function(x){{return x.task_number===n}}),max=st?st.max_points:ex.max_points;var card=document.createElement("article");card.className="ep24-card";card.setAttribute("data-task",n);card.innerHTML='<div class="ep24-card-head"><h2>Задание '+n+'</h2><span class="ep24-points">макс. '+max+'</span></div><img class="ep24-source" alt="Официальное задание ФИПИ 2024 № '+n+'" src="'+taskImage(n)+'"><div class="ep24-answer"><label for="ep24-a-'+n+'">'+(n<=20?'Ваш ответ':'Ваше решение')+'</label>'+(n<=20?'<input id="ep24-a-'+n+'" autocomplete="off" inputmode="text">':'<textarea id="ep24-a-'+n+'"></textarea>')+'</div>';w.appendChild(card);var el=byId("ep24-a-"+n);el.value=state.answers[n]||"";el.addEventListener("input",function(nn){{return function(e){{state.answers[nn]=e.target.value;save();updateProgress()}}}}(n))}}updateProgress()}}
function updateProgress(){{var c=0;for(var n=1;n<=26;n++)if(String(state.answers[n]||"").trim())c++;byId("ep24-progress").textContent="Заполнено "+c+" из 26"}}
function shortTotal(){{return SHORT.reduce(function(s,t){{return s+score(t,state.answers[t.task_number]||"")}},0)}}
function renderShortReview(){{var w=byId("ep24-short-review");w.innerHTML="";SHORT.forEach(function(t){{var a=state.answers[t.task_number]||"",p=score(t,a),item=document.createElement("article");item.className="ep24-review";item.setAttribute("data-correct",p===t.max_points?"true":"false");item.innerHTML='<h3>Задание '+t.task_number+' · '+p+'/'+t.max_points+'</h3><p>Ваш ответ: <strong>'+esc(a||"—")+'</strong></p><p>Ответ ФИПИ: <strong>'+esc(t.official_answer)+'</strong></p>';w.appendChild(item)}})}}
function criteriaImages(n){{return Object.keys(EP24_A).filter(function(k){{return k.indexOf("criteria-"+String(n).padStart(2,"0")+"-")===0}}).sort().map(function(k){{return '<img loading="lazy" alt="Официальное решение и критерии ФИПИ 2024 для задания '+n+'" src="data:image/webp;base64,'+EP24_A[k]+'">'}}).join("")}}
function renderSelf(){{var w=byId("ep24-self");w.innerHTML="";EXT.forEach(function(t){{var n=t.task_number,item=document.createElement("article");item.className="ep24-self";var buttons="";for(var p=0;p<=t.max_points;p++)buttons+='<button type="button" class="ep24-score-btn'+(Number(state.self[n])===p?' is-on':'')+'" data-n="'+n+'" data-p="'+p+'">'+p+'</button>';item.innerHTML='<div class="ep24-self-head"><h3>Задание '+n+'</h3><span class="ep24-points">макс. '+t.max_points+'</span></div><p><strong>Ваше решение</strong></p><div class="ep24-note">'+esc(state.answers[n]||"Ответ не введён").replace(/\n/g,"<br>")+'</div><div class="ep24-score-buttons" aria-label="Баллы за задание '+n+'">'+buttons+'</div><div class="ep24-criteria"><details><summary>Официальное возможное решение и критерии ФИПИ</summary>'+criteriaImages(n)+'</details></div>';w.appendChild(item)}});w.querySelectorAll(".ep24-score-btn").forEach(function(b){{b.addEventListener("click",function(){{state.self[this.dataset.n]=Number(this.dataset.p);save();renderSelf();renderTotal()}})}})}}
function renderTotal(){{var keys=EXT.map(function(t){{return String(t.task_number)}}),done=keys.every(function(k){{return Object.prototype.hasOwnProperty.call(state.self,k)}}),st=shortTotal(),ext=keys.reduce(function(s,k){{return s+(Number(state.self[k])||0)}},0);byId("ep24-total").textContent=done?(st+ext)+" / "+MAX:st+" / "+SHORT_MAX+" + самооценка";byId("ep24-result-copy").textContent=done?"Итоговый первичный балл по демоверсии: "+(st+ext)+" из "+MAX+".":"Краткая часть: "+st+" из "+SHORT_MAX+". Оцените все задания 21–26."}}
function finish(){{state.finished=true;save();renderShortReview();renderSelf();renderTotal();byId("ep24-results").classList.add("is-open");byId("ep24-results").scrollIntoView({{behavior:"smooth",block:"start"}})}}
function reset(){{if(!confirm("Сбросить все ответы и самооценку?"))return;localStorage.removeItem(KEY);state={{answers:{{}},self:{{}},startedAt:Date.now(),finished:false}};renderTasks();byId("ep24-results").classList.remove("is-open");updateTimer()}}
function updateTimer(){{var elapsed=Math.max(0,Math.floor((Date.now()-(state.startedAt||Date.now()))/1000)),left=Math.max(0,DURATION-elapsed),h=String(Math.floor(left/3600)).padStart(2,"0"),m=String(Math.floor(left%3600/60)).padStart(2,"0"),s=String(left%60).padStart(2,"0");byId("ep24-timer").textContent=h+":"+m+":"+s}}
load();renderTasks();byId("ep24-finish").addEventListener("click",finish);byId("ep24-reset").addEventListener("click",reset);if(state.finished){{renderShortReview();renderSelf();renderTotal();byId("ep24-results").classList.add("is-open")}}updateTimer();setInterval(updateTimer,1000);
}})();
</script>''' + "\n"


def deterministic_zip(source: Path, destination: Path) -> str:
    if destination.exists():
        destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            rel = (Path(source.name) / path.relative_to(source)).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2024, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            z.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return file_sha(destination)


def main() -> None:
    if file_sha(SOURCE) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("canonical Physics 2024 PDF hash mismatch")
    layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
    scorer = json.loads(SCORER.read_text(encoding="utf-8"))
    if layout.get("unresolved_mappings") != 0 or len(layout.get("tasks", [])) != 26:
        raise RuntimeError("source layout gate failed")
    if scorer.get("short_max_points") != 28 or scorer.get("extended_max_points") != 17 or scorer.get("official_max_points") != 45:
        raise RuntimeError("scorer total gate failed")

    shutil.rmtree(BUILD / "out", ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)
    OUT.mkdir(parents=True)
    DIST.mkdir(parents=True)

    assets, asset_manifest = build_assets(layout, scorer)
    write(OUT / f"{PREFIX}-HEAD.txt", head_html())

    blocks: list[str] = [app_shell()]
    for key in sorted(assets):
        value = assets[key]
        first = True
        for i in range(0, len(value), PAYLOAD_CHUNK):
            blocks.append(asset_script(key, value[i:i + PAYLOAD_CHUNK], first))
            first = False
    blocks.append(runtime_js(scorer))
    if len(blocks) > MAX_T123_COUNT:
        raise RuntimeError(f"Tilda practicality gate failed: {len(blocks)} T123 blocks > {MAX_T123_COUNT}")

    for i, block in enumerate(blocks, 1):
        path = OUT / f"{PREFIX}-T123-{i:02d}.txt"
        write(path, block)
        if path.stat().st_size >= T123_LIMIT:
            raise RuntimeError(f"T123 size gate failed: {path.name} {path.stat().st_size}")

    preview = '<!doctype html><html lang="ru"><head>\n' + head_html() + '</head><body>\n' + ''.join(blocks) + '</body></html>\n'
    write(OUT / f"{PREFIX}-PREVIEW.html", preview)
    (OUT / f"{PREFIX}-ASSET-MANIFEST.json").write_text(json.dumps(asset_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    criteria_count = len([x for x in asset_manifest if x["kind"] == "official_solution_criteria_logical_page"])
    acceptance = {
        "status": "READY_FOR_TILDA_AFTER_BROWSER_GATE",
        "content_year": 2024,
        "source_sha256": EXPECTED_SOURCE_SHA,
        "task_count": 26,
        "short_max_points": 28,
        "extended_max_points": 17,
        "official_max_points": 45,
        "unresolved_source_mappings": 0,
        "unresolved_text_fidelity": 0,
        "build_ready_task_rendering": "source-rendered raster crops from canonical FIPI 2024 PDF; pdftotext task text is not used in production rendering",
        "task_source_regions": 26,
        "criteria_source_logical_pages": criteria_count,
        "t123_count": len(blocks),
        "max_t123_bytes": max((OUT / f"{PREFIX}-T123-{i:02d}.txt").stat().st_size for i in range(1, len(blocks) + 1)),
        "private_use_characters_in_production_text": 0,
        "physics_2025_content_used": 0,
        "physics_2026_content_used": 0,
    }
    write(OUT / f"{PREFIX}-ACCEPTANCE.json", json.dumps(acceptance, ensure_ascii=False, indent=2) + "\n")
    write(OUT / "00-README-TILDA.txt", f'''EGE PHYSICS 2024 — TILDA HQ SOURCE v1.0\n\n1. Вставьте содержимое {PREFIX}-HEAD.txt в HEAD страницы.\n2. Создайте {len(blocks)} блоков T123 и вставьте {PREFIX}-T123-01.txt ... {PREFIX}-T123-{len(blocks):02d}.txt строго по порядку.\n3. Не меняйте порядок T123: изображения официального источника загружаются частями, последний блок запускает интерфейс и scorer.\n\nCANONICAL=https://eksamio.ru/ege/fizika/demoversiya/2024/\nSOURCE=canonical FIPI Physics 2024 PDF\nSCORER=28+17=45\nTEXT_FIDELITY=source-rendered task images; unresolved=0\n''')

    production_text = ''.join(p.read_text(encoding="utf-8") for p in OUT.glob("*.txt"))
    if re.search(r"[\ue000-\uf8ff]", production_text):
        raise RuntimeError("private-use Unicode leaked into production text")
    for p in OUT.glob("*.txt"):
        txt = p.read_text(encoding="utf-8")
        if "2025" in txt or "2026" in txt:
            raise RuntimeError(f"cross-year content token leaked into {p.name}")

    manifest_paths = sorted(p for p in OUT.rglob("*") if p.is_file())
    manifest = "\n".join(f"{file_sha(p)}  {p.relative_to(OUT).as_posix()}" for p in manifest_paths) + "\n"
    write(OUT / "SHA256SUMS.txt", manifest)
    zip_sha = deterministic_zip(OUT, ZIP)
    write(DIST / "SHA256.txt", f"{zip_sha}  {ZIP.name}\n")
    print(json.dumps({"archive": str(ZIP), "sha256": zip_sha, "t123_count": len(blocks), "assets": len(asset_manifest), "encoded_bytes": sum(x["bytes"] for x in asset_manifest)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
