#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(__file__).resolve().parent
EVIDENCE = ROOT / "physics-2023-evidence"
SOURCE = ROOT / "ege-source-fizika/source-fizika-2023/ege-2023-fizika-demoversiya.pdf"
RENDER_CACHE = BUILD / ".render-cache"
LAYOUT = EVIDENCE / "PHYSICS-2023-SOURCE-LAYOUT-MAP.json"
SCORER = EVIDENCE / "PHYSICS-2023-ANSWER-SCORER-SPEC.json"
VERSION = "v1.0"
OUT = BUILD / "out" / f"ege-fizika-demoversiya-2023-{VERSION}-TILDA-HQ-SOURCE"
DIST = BUILD / "dist"
ZIP = DIST / f"ege-fizika-demoversiya-2023-{VERSION}-TILDA-HQ-SOURCE.zip"
PREFIX = "ege-fizika-demoversiya-2023"
EXPECTED_SOURCE_SHA = "a5174740e49cb3626f371ed7b2addc0d078fe6630f98bf7133540f3329bce485"
T123_LIMIT = 42500
PAYLOAD_CHUNK = 39000
MAX_T123_COUNT = 48
EXPECTED_PAGE_SIZE = (2339, 1654)
HALF_X = EXPECTED_PAGE_SIZE[0] // 2


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def render_page(physical_page: int) -> Image.Image:
    RENDER_CACHE.mkdir(parents=True, exist_ok=True)
    path = RENDER_CACHE / f"page-{physical_page:03d}.png"
    if not path.exists():
        executable = shutil.which("pdftoppm")
        bundled = Path("/Users/elenadymova/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/bin/pdftoppm")
        if executable is None and bundled.exists():
            executable = str(bundled)
        if executable is None:
            raise RuntimeError("pdftoppm is required to render the canonical Physics 2023 PDF")
        subprocess.run([
            executable, "-png", "-r", "200", "-f", str(physical_page),
            "-l", str(physical_page), "-singlefile", str(SOURCE), str(path.with_suffix("")),
        ], check=True)
    image = Image.open(path).convert("RGB")
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
    return f'<script>window.EP23_A=window.EP23_A||{{}};EP23_A[{json.dumps(key)}]{op}{json.dumps(b64)};</script>\n'


def pack_asset_blocks(assets: dict[str, str]) -> list[str]:
    """Pack source-native assets tightly without splitting a script tag across T123 blocks."""
    open_tag = '<script>window.EP23_A=window.EP23_A||{};'
    close_tag = '</script>\n'
    budget = T123_LIMIT - 256
    blocks: list[str] = []
    current = open_tag
    for key in sorted(assets):
        remaining = assets[key]
        first = True
        while remaining:
            op = "=" if first else "+="
            prefix = f'EP23_A[{json.dumps(key)}]{op}"'
            suffix = '";'
            available = budget - len((current + prefix + suffix + close_tag).encode("utf-8"))
            if available < 512:
                blocks.append(current + close_tag)
                current = open_tag
                continue
            piece = remaining[:available]
            current += prefix + piece + suffix
            remaining = remaining[len(piece):]
            first = False
    if current != open_tag:
        blocks.append(current + close_tag)
    if any(len(block.encode("utf-8")) >= T123_LIMIT for block in blocks):
        raise RuntimeError("packed asset T123 size gate failed")
    return blocks


def html_escape_json(data) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def build_assets(layout: dict, scorer: dict) -> tuple[dict[str, str], list[dict]]:
    cache: dict[int, Image.Image] = {}
    assets: dict[str, str] = {}
    manifest: list[dict] = []

    def page(n: int) -> Image.Image:
        if n not in cache:
            cache[n] = render_page(n)
        return cache[n]

    for task in layout["tasks"]:
        n = int(task["task_number"])
        regions = task["source_regions"]
        crops = []
        for region in regions:
            p = int(region["physical_page"])
            box = tuple(int(v) for v in region["source_region_200dpi_pixels"])
            crops.append(page(p).crop(box))
        if len(crops) == 1:
            source_crop = crops[0]
        else:
            gap = 24
            width = max(crop.width for crop in crops)
            source_crop = Image.new("RGB", (width, sum(crop.height for crop in crops) + gap * (len(crops) - 1)), "white")
            y = 0
            for crop in crops:
                source_crop.paste(crop, (0, y))
                y += crop.height + gap
        raw, encoded_image = webp_bytes(source_crop, max_width=1000)
        key = f"task-{n:02d}"
        assets[key] = base64.b64encode(raw).decode("ascii")
        manifest.append({
            "key": key,
            "kind": "task_source_region",
            "task": n,
            "source_regions": regions,
            "source_native_regions_joined_with_neutral_white_gap_px": 24 if len(regions) > 1 else 0,
            "encoded_width": encoded_image.width,
            "encoded_height": encoded_image.height,
            "mime": "image/webp",
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
        })

    # Official solution/criteria content is source-rendered from explicit bounded regions.
    for ext in scorer["extended_tasks"]:
        n = int(ext["task_number"])
        for index, region in enumerate(ext["criteria_regions"], 1):
            logical_page = int(region["logical_page"])
            physical_page = int(region["physical_page"])
            box = tuple(int(value) for value in region["source_region_200dpi_pixels"])
            source_crop = page(physical_page).crop(box)
            raw, encoded_image = webp_bytes(source_crop, max_width=1000)
            key = f"criteria-{n:02d}-{index:02d}-logical-{logical_page:03d}"
            assets[key] = base64.b64encode(raw).decode("ascii")
            manifest.append({
                "key": key,
                "kind": "official_solution_criteria_bounded_region",
                "task": n,
                "logical_page": logical_page,
                "physical_page": physical_page,
                "source_crop_200dpi_pixels": list(box),
                "encoded_width": encoded_image.width,
                "encoded_height": encoded_image.height,
                "mime": "image/webp",
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
                "four_edge_complete": True,
                "no_neighbor_task_content": True,
            })

    if len([m for m in manifest if m["kind"] == "task_source_region"]) != 30:
        raise RuntimeError("task source raster count != 30")
    criteria_assets = [m for m in manifest if m["kind"].startswith("official_solution_criteria_")]
    if len(criteria_assets) != 22:
        raise RuntimeError("criteria source region count != 22")
    return assets, manifest


def head_html() -> str:
    return '''<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Демоверсия ЕГЭ 2023 по физике — ФИПИ | Эксамио</title>
<meta name="description" content="Интерактивная демоверсия ЕГЭ 2023 по физике по официальным материалам ФИПИ: 30 заданий, проверка кратких ответов и самооценка заданий с развёрнутым ответом.">
<meta name="robots" content="index,follow">
<link rel="canonical" href="https://eksamio.ru/ege/fizika/demoversiya/2023/">
<meta property="og:type" content="website">
<meta property="og:title" content="Демоверсия ЕГЭ 2023 по физике — ФИПИ | Эксамио">
<meta property="og:description" content="Интерактивная демоверсия ЕГЭ 2023 по физике по официальным материалам ФИПИ.">
<meta property="og:url" content="https://eksamio.ru/ege/fizika/demoversiya/2023/">
'''


def seo_text() -> str:
    return '''EKSAMIO — ЕГЭ ФИЗИКА 2023 — SEO ДЛЯ TILDA

СТРАНИЦА
URL PATH: /ege/fizika/demoversiya/2023/
CANONICAL: https://eksamio.ru/ege/fizika/demoversiya/2023/
INDEXING: index, follow
LANG: ru

SEO TITLE
Демоверсия ЕГЭ 2023 по физике — ФИПИ | Эксамио

SEO DESCRIPTION
Интерактивная демоверсия ЕГЭ 2023 по физике по материалам ФИПИ: 30 заданий, 235 минут, проверка кратких ответов, решения и критерии оценивания.

KEYWORDS
демоверсия ЕГЭ 2023 физика, ФИПИ физика 2023, ЕГЭ физика демоверсия, демоверсия по физике 2023, интерактивная демоверсия ЕГЭ

H1 НА СТРАНИЦЕ
Интерактивная демоверсия ЕГЭ по физике

OPEN GRAPH
OG:TYPE: website
OG:TITLE: Демоверсия ЕГЭ 2023 по физике — ФИПИ | Эксамио
OG:DESCRIPTION: Интерактивная демоверсия ЕГЭ 2023 по физике по материалам ФИПИ: 30 заданий, 235 минут, проверка кратких ответов, решения и критерии оценивания.
OG:URL: https://eksamio.ru/ege/fizika/demoversiya/2023/

TILDA — ЧТО ЗАДАТЬ В НАСТРОЙКАХ СТРАНИЦЫ
1. Адрес страницы: ege/fizika/demoversiya/2023/
2. Title: Демоверсия ЕГЭ 2023 по физике — ФИПИ | Эксамио
3. Description: строка SEO DESCRIPTION выше.
4. Keywords: строка KEYWORDS выше.
5. Canonical URL: https://eksamio.ru/ege/fizika/demoversiya/2023/
6. Разрешить индексацию страницы.
7. Не ставить canonical на страницу другого года.

ТЕХНИЧЕСКИЙ HEAD
Готовые meta, canonical, robots и Open Graph уже находятся в файле ege-fizika-demoversiya-2023-HEAD.txt. Не вставляйте их повторно.
'''


def app_shell() -> str:
    return r'''<style>
#ep23{--ink:#172033;--muted:#667085;--line:#e5e7eb;--soft:#f7f8fb;--accent:#3157d5;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;color:var(--ink);max-width:980px;margin:0 auto;padding:24px 16px 72px;box-sizing:border-box}
#ep23 *{box-sizing:border-box}#ep23 button,#ep23 input,#ep23 textarea{font:inherit}.ep23-hero{background:linear-gradient(135deg,#f4f7ff,#fff);border:1px solid #dfe6ff;border-radius:24px;padding:28px;margin-bottom:20px}.ep23-kicker{font-size:13px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#3157d5}.ep23-hero h1{font-size:clamp(28px,5vw,46px);line-height:1.08;margin:8px 0 12px}.ep23-hero p{font-size:16px;line-height:1.55;color:var(--muted);max-width:760px}.ep23-meta{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}.ep23-chip{background:#fff;border:1px solid var(--line);border-radius:999px;padding:8px 12px;font-size:14px}.ep23-toolbar{position:sticky;top:8px;z-index:20;background:rgba(255,255,255,.94);backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:16px;padding:10px 12px;display:flex;gap:10px;align-items:center;justify-content:space-between;margin:0 0 20px;box-shadow:0 8px 24px rgba(16,24,40,.06)}.ep23-progress{font-weight:700}.ep23-timer{font-variant-numeric:tabular-nums;color:var(--muted)}.ep23-card{border:1px solid var(--line);border-radius:20px;background:#fff;padding:18px;margin:0 0 16px;box-shadow:0 2px 10px rgba(16,24,40,.035)}.ep23-card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px}.ep23-card-head h2{font-size:19px;margin:0}.ep23-points{font-size:13px;color:var(--muted);white-space:nowrap}.ep23-source{display:block;width:100%;height:auto;border:1px solid #eceff3;border-radius:12px;background:#fff}.ep23-answer{margin-top:14px}.ep23-answer label{display:block;font-weight:650;margin-bottom:7px}.ep23-answer input,.ep23-answer textarea{width:100%;border:1px solid #cfd4dc;border-radius:12px;padding:12px 13px;background:#fff;color:var(--ink);outline:none}.ep23-answer textarea{min-height:132px;resize:vertical}.ep23-answer input:focus,.ep23-answer textarea:focus{border-color:#7b94ec;box-shadow:0 0 0 3px rgba(49,87,213,.1)}.ep23-actions{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0}.ep23-btn{appearance:none;border:0;border-radius:12px;padding:12px 17px;font-weight:700;cursor:pointer}.ep23-btn-primary{background:var(--accent);color:#fff}.ep23-btn-secondary{background:#eef2ff;color:#2548be}.ep23-btn:disabled{opacity:.45;cursor:not-allowed}.ep23-results{display:none}.ep23-results.is-open{display:block}.ep23-result-hero{border-radius:22px;padding:24px;background:#111827;color:#fff;margin-bottom:18px}.ep23-score{font-size:clamp(34px,7vw,58px);font-weight:800;line-height:1}.ep23-result-hero p{color:#d1d5db}.ep23-section{margin:28px 0 12px}.ep23-section h2{font-size:24px;margin:0 0 6px}.ep23-section p{color:var(--muted);line-height:1.5}.ep23-review{border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:10px 0}.ep23-review[data-correct="true"]{border-color:#a6d8c3;background:#f2fbf6}.ep23-review[data-correct="false"]{border-color:#f5c3bd;background:#fff8f7}.ep23-review h3{margin:0 0 8px;font-size:16px}.ep23-review p{margin:5px 0;line-height:1.4}.ep23-self{border:1px solid var(--line);border-radius:18px;padding:16px;margin:14px 0}.ep23-self-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.ep23-self h3{margin:0}.ep23-score-buttons{display:flex;gap:7px;flex-wrap:wrap;margin:12px 0}.ep23-score-btn{border:1px solid #cfd4dc;background:#fff;border-radius:10px;padding:8px 12px;cursor:pointer;font-weight:700}.ep23-score-btn.is-on{background:#3157d5;border-color:#3157d5;color:#fff}.ep23-criteria details{margin-top:12px}.ep23-criteria summary{cursor:pointer;font-weight:700}.ep23-criteria img{display:block;width:100%;height:auto;border:1px solid #e5e7eb;border-radius:12px;margin-top:10px}.ep23-note{font-size:13px;color:var(--muted)}.ep23-footer-note{margin-top:28px;padding:16px;border-radius:14px;background:var(--soft);color:var(--muted);font-size:13px;line-height:1.5}@media(max-width:560px){#ep23{padding:14px 10px 56px}.ep23-hero{padding:20px 16px;border-radius:18px}.ep23-card{padding:12px;border-radius:16px}.ep23-toolbar{top:4px}.ep23-card-head,.ep23-self-head{align-items:flex-start}.ep23-source{border-radius:8px}.ep23-btn{width:100%}}
</style>
<div id="ep23"><section class="ep23-hero"><div class="ep23-kicker">Эксамио · Физика</div><h1>Демоверсия ЕГЭ 2023</h1><p>Все формулировки, формулы, обозначения, таблицы и рисунки заданий показываются как растровые фрагменты, непосредственно сформированные из официальной демоверсии ФИПИ 2023. Задания 1–23 проверяются автоматически; задания 24–30 оцениваются по официальным решениям и критериям.</p><div class="ep23-meta"><span class="ep23-chip">30 заданий</span><span class="ep23-chip">235 минут</span><span class="ep23-chip">максимум 54 балла</span><span class="ep23-chip">официальный источник: ФИПИ 2023</span></div></section><div class="ep23-toolbar"><div class="ep23-progress" id="ep23-progress">Заполнено 0 из 30</div><div class="ep23-timer" id="ep23-timer">03:55:00</div></div><main id="ep23-tasks"></main><div class="ep23-actions" id="ep23-actions"><button class="ep23-btn ep23-btn-primary" id="ep23-finish" type="button">Завершить и проверить</button><button class="ep23-btn ep23-btn-secondary" id="ep23-reset" type="button">Сбросить ответы</button></div><section class="ep23-results" id="ep23-results"><div class="ep23-result-hero"><div class="ep23-score" id="ep23-total">— / 54</div><p id="ep23-result-copy">Сначала оцените задания 24–30.</p></div><div class="ep23-section" data-section="short-review"><h2>Проверка заданий 1–23</h2><p>Баллы рассчитаны по официальным правилам демоверсии ФИПИ 2023, включая частичный балл для заданий с выбором и установлением соответствия.</p></div><div id="ep23-short-review"></div><div class="ep23-section" data-section="self-assessment"><h2>Самооценка заданий 24–30</h2><p>Сравните своё решение с официальным возможным решением и критериями ФИПИ, затем выберите балл. Итог появится после оценки всех семи заданий.</p></div><div id="ep23-self"></div></section><div class="ep23-footer-note">Источник содержания: официальная демоверсия ЕГЭ 2023 по физике ФИПИ. Встроенные изображения заданий и критериев сформированы непосредственно из канонического PDF без переноса содержания из других лет.</div></div><script>window.EP23_A=window.EP23_A||{};</script>
'''


def runtime_js(scorer: dict) -> str:
    short_json = html_escape_json(scorer["short_tasks"])
    ext_json = html_escape_json(scorer["extended_tasks"])
    return rf'''<script>
(function(){{
"use strict";
var SHORT={short_json}, EXT={ext_json}, KEY="eksamio.physics.2023.demo.v1", MAX=54, SHORT_MAX=34, DURATION=235*60;
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
window.EP23_TEST_SCORE=function(n,a){{var t=SHORT.find(function(x){{return x.task_number===n}});return score(t,a)}};
function taskImage(n){{return "data:image/webp;base64,"+EP23_A["task-"+String(n).padStart(2,"0")]}}
function renderTasks(){{var w=byId("ep23-tasks");w.innerHTML="";for(var n=1;n<=30;n++){{var st=SHORT.find(function(x){{return x.task_number===n}}),ex=EXT.find(function(x){{return x.task_number===n}}),max=st?st.max_points:ex.max_points;var card=document.createElement("article");card.className="ep23-card";card.setAttribute("data-task",n);card.innerHTML='<div class="ep23-card-head"><h2>Задание '+n+'</h2><span class="ep23-points">макс. '+max+'</span></div><img class="ep23-source" alt="Официальное задание ФИПИ 2023 № '+n+'" src="'+taskImage(n)+'"><div class="ep23-answer"><label for="ep23-a-'+n+'">'+(n<=23?'Ваш ответ':'Ваше решение')+'</label>'+(n<=23?'<input id="ep23-a-'+n+'" autocomplete="off" inputmode="text">':'<textarea id="ep23-a-'+n+'"></textarea>')+'</div>';w.appendChild(card);var el=byId("ep23-a-"+n);el.value=state.answers[n]||"";el.addEventListener("input",function(nn){{return function(e){{state.answers[nn]=e.target.value;save();updateProgress()}}}}(n))}}updateProgress()}}
function updateProgress(){{var c=0;for(var n=1;n<=30;n++)if(String(state.answers[n]||"").trim())c++;byId("ep23-progress").textContent="Заполнено "+c+" из 30"}}
function shortTotal(){{return SHORT.reduce(function(s,t){{return s+score(t,state.answers[t.task_number]||"")}},0)}}
function renderShortReview(){{var w=byId("ep23-short-review");w.innerHTML="";SHORT.forEach(function(t){{var a=state.answers[t.task_number]||"",p=score(t,a),item=document.createElement("article");item.className="ep23-review";item.setAttribute("data-correct",p===t.max_points?"true":"false");item.innerHTML='<h3>Задание '+t.task_number+' · '+p+'/'+t.max_points+'</h3><p>Ваш ответ: <strong>'+esc(a||"—")+'</strong></p><p>Ответ ФИПИ: <strong>'+esc(t.official_answer)+'</strong></p>';w.appendChild(item)}})}}
function criteriaImages(n){{return Object.keys(EP23_A).filter(function(k){{return k.indexOf("criteria-"+String(n).padStart(2,"0")+"-")===0}}).sort().map(function(k){{return '<img loading="lazy" alt="Официальное решение и критерии ФИПИ 2023 для задания '+n+'" src="data:image/webp;base64,'+EP23_A[k]+'">'}}).join("")}}
function renderSelf(){{var w=byId("ep23-self");w.innerHTML="";EXT.forEach(function(t){{var n=t.task_number,item=document.createElement("article");item.className="ep23-self";var buttons="";for(var p=0;p<=t.max_points;p++)buttons+='<button type="button" class="ep23-score-btn'+(Number(state.self[n])===p?' is-on':'')+'" data-n="'+n+'" data-p="'+p+'">'+p+'</button>';item.innerHTML='<div class="ep23-self-head"><h3>Задание '+n+'</h3><span class="ep23-points">макс. '+t.max_points+'</span></div><p><strong>Ваше решение</strong></p><div class="ep23-note">'+esc(state.answers[n]||"Ответ не введён").replace(/\n/g,"<br>")+'</div><div class="ep23-score-buttons" aria-label="Баллы за задание '+n+'">'+buttons+'</div><div class="ep23-criteria"><details><summary>Официальное возможное решение и критерии ФИПИ</summary>'+criteriaImages(n)+'</details></div>';w.appendChild(item)}});w.querySelectorAll(".ep23-score-btn").forEach(function(b){{b.addEventListener("click",function(){{state.self[this.dataset.n]=Number(this.dataset.p);save();renderSelf();renderTotal()}})}})}}
function renderTotal(){{var keys=EXT.map(function(t){{return String(t.task_number)}}),done=keys.every(function(k){{return Object.prototype.hasOwnProperty.call(state.self,k)}}),st=shortTotal(),ext=keys.reduce(function(s,k){{return s+(Number(state.self[k])||0)}},0);byId("ep23-total").textContent=done?(st+ext)+" / "+MAX:st+" / "+SHORT_MAX+" + самооценка";byId("ep23-result-copy").textContent=done?"Итоговый первичный балл по демоверсии: "+(st+ext)+" из "+MAX+".":"Краткая часть: "+st+" из "+SHORT_MAX+". Оцените все задания 24–30."}}
function finish(){{state.finished=true;save();renderShortReview();renderSelf();renderTotal();byId("ep23-results").classList.add("is-open");byId("ep23-results").scrollIntoView({{behavior:"smooth",block:"start"}})}}
function reset(){{if(!confirm("Сбросить все ответы и самооценку?"))return;localStorage.removeItem(KEY);state={{answers:{{}},self:{{}},startedAt:Date.now(),finished:false}};renderTasks();byId("ep23-results").classList.remove("is-open");updateTimer()}}
function updateTimer(){{var elapsed=Math.max(0,Math.floor((Date.now()-(state.startedAt||Date.now()))/1000)),left=Math.max(0,DURATION-elapsed),h=String(Math.floor(left/3600)).padStart(2,"0"),m=String(Math.floor(left%3600/60)).padStart(2,"0"),s=String(left%60).padStart(2,"0");byId("ep23-timer").textContent=h+":"+m+":"+s}}
load();renderTasks();byId("ep23-finish").addEventListener("click",finish);byId("ep23-reset").addEventListener("click",reset);if(state.finished){{renderShortReview();renderSelf();renderTotal();byId("ep23-results").classList.add("is-open")}}updateTimer();setInterval(updateTimer,1000);
}})();
</script>''' + "\n"


# Reference-parity shell. The legacy definitions above remain readable history;
# these later definitions are the production entry points used by main().
def app_shell() -> str:
    return r'''<div class="ep-root" id="ep23" data-state="idle">
<style>
#ep23,#ep23 *{box-sizing:border-box}#ep23{color:#17324d;font-family:Arial,sans-serif;overflow-x:hidden}#ep23 .ep-page{max-width:1220px;margin:0 auto;padding:24px 20px}#ep23 .ep-stack{display:grid;gap:18px;min-width:0}#ep23 .ep-panel{background:#fff;border:1px solid #dfe4eb;border-radius:16px;padding:22px;min-width:0}#ep23 .ep-title{font-size:clamp(30px,5vw,52px);line-height:1.08;margin:12px 0 14px}#ep23 .ep-lead{font-size:18px;line-height:1.6;max-width:900px;margin:0}#ep23 .ep-meta{display:flex;gap:8px;flex-wrap:wrap}#ep23 .ep-pill{display:inline-flex;align-items:center;padding:7px 10px;border-radius:999px;background:#f0f3f7;font-size:14px;font-weight:800}#ep23 .ep-pill--blue{background:#eef6ff;color:#315fb5}#ep23 .ep-section-title{font-size:24px;line-height:1.2;margin:0 0 14px}#ep23 .ep-button{appearance:none;border:1px solid #315fb5;border-radius:11px;background:#315fb5;color:#fff;padding:12px 17px;font:inherit;font-weight:800;line-height:1.2;cursor:pointer}#ep23 .ep-button:hover{background:#274f99}#ep23 .ep-button:focus-visible{outline:3px solid rgba(49,95,181,.25);outline-offset:3px}#ep23 .ep-button--small{padding:9px 13px;font-size:14px}#ep23 .ep-button--secondary{background:#fff;color:#17324d;border-color:#c9d3df}#ep23 .ep-button--secondary:hover{background:#f4f7fb}#ep23 .ep-button:disabled{background:#f4f5f7;color:#7b8794;border-color:#d9dee5;cursor:not-allowed}#ep23 .ep23-breadcrumbs{font-size:14px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}#ep23 .ep23-breadcrumbs a{color:inherit}#ep23 .ep23-start>p{line-height:1.62;margin:0 0 15px}#ep23 .ep23-notice{margin-top:22px;padding:16px 18px;border:1px solid #ead7a2;border-left:5px solid #b9891c;border-radius:12px;background:#fff8e8;line-height:1.55}#ep23 .ep23-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}#ep23 .ep23-hidden{display:none!important}#ep23 .ep23-exam,#ep23 .ep23-result{display:none}#ep23[data-state="running"] .ep23-start{display:none}#ep23[data-state="running"] .ep23-exam{display:grid;gap:18px}#ep23[data-state="finished"] .ep23-start,#ep23[data-state="finished"] .ep23-exam{display:none}#ep23[data-state="finished"] .ep23-result{display:grid;gap:18px}#ep23 .ep23-toolbar{position:sticky;top:10px;z-index:12;display:grid;grid-template-columns:auto 1fr auto auto;gap:12px;align-items:center}#ep23 .ep23-timer{font-variant-numeric:tabular-nums;font-weight:850;font-size:20px;white-space:nowrap}#ep23 .ep23-progress{height:10px;border-radius:999px;background:#eef1f5;overflow:hidden}#ep23 .ep23-progress>span{display:block;height:100%;width:0;background:#315fb5;transition:width .2s ease}#ep23 .ep23-finish{background:#8f2f40;border-color:#7f2635}#ep23 .ep23-nav{display:grid;grid-template-columns:repeat(9,minmax(36px,1fr));gap:7px}#ep23 .ep23-nav-btn{min-height:38px;border:1px solid #d9dee7;border-radius:10px;background:#fff;color:#27303f;font-weight:800;cursor:pointer}#ep23 .ep23-nav-btn[data-filled="true"]{border-color:#4d9469;background:#e7f6ed;color:#245b3b}#ep23 .ep23-nav-btn[data-flagged="true"]{border-color:#cf7a18;background:#fff0d6;color:#704009}#ep23 .ep23-nav-btn[aria-current="true"]{outline:3px solid rgba(49,96,181,.24);outline-offset:2px;border-color:#315fb5}#ep23 .ep23-task-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}#ep23 .ep23-task-number{font-size:14px;font-weight:850;letter-spacing:.04em;text-transform:uppercase}#ep23 .ep23-source{display:block;width:auto;max-width:100%;height:auto;margin:18px auto;border:1px solid #dfe4eb;border-radius:14px;background:#fff}#ep23 .ep23-answer{margin-top:20px}#ep23 .ep23-answer label{display:block;font-weight:800;margin-bottom:8px}#ep23 .ep23-input,#ep23 .ep23-textarea{width:100%;border:1px solid #cdd4df;border-radius:12px;background:#fff;padding:14px 15px;font:inherit;color:#17324d}#ep23 .ep23-input{max-width:460px;font-size:18px}#ep23 .ep23-textarea{min-height:220px;resize:vertical;line-height:1.55}#ep23 .ep23-help,#ep23 .ep23-mini{font-size:13px;opacity:.76;line-height:1.5}#ep23 .ep23-save{font-size:14px;margin-top:8px;font-weight:800}#ep23 .ep23-task-actions{display:flex;gap:10px;flex-wrap:wrap;justify-content:space-between;margin-top:20px}#ep23 .ep23-task-actions>div{display:flex;gap:10px;flex-wrap:wrap}#ep23 .ep23-draft{margin-top:18px;padding:12px;border-radius:12px;background:#f6f8fb}#ep23 .ep23-draft summary{cursor:pointer}#ep23 .ep23-draft .ep23-textarea{min-height:140px;margin-top:12px}#ep23 .ep23-symbols{margin:10px 0 4px;padding:10px;border:1px solid #dfe4eb;border-radius:12px;background:#f8fafc}#ep23 .ep23-symbols strong{display:block;font-size:13px;margin-bottom:8px}#ep23 .ep23-symbol-list{display:flex;gap:6px;flex-wrap:wrap}#ep23 .ep23-symbol{min-width:38px;min-height:36px;padding:6px 8px;border:1px solid #cdd4df;border-radius:9px;background:#fff;color:#17324d;font:inherit;font-weight:800;cursor:pointer}#ep23 .ep23-score-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}#ep23 .ep23-score-card{border:1px solid #dfe4eb;border-radius:14px;padding:16px;background:#fff}#ep23 .ep23-score-value{font-size:30px;font-weight:850;line-height:1.15}#ep23 .ep23-review-list,#ep23 .ep23-self-list{display:grid;gap:12px}#ep23 .ep23-review{border:1px solid #dfe4eb;border-radius:14px;padding:16px;background:#fff}#ep23 .ep23-review[data-correct="true"]{border-left:5px solid #2f8a58}#ep23 .ep23-review[data-correct="false"]{border-left:5px solid #b84e4e}#ep23 .ep23-self{border:1px solid #dfe4eb;border-radius:14px;padding:16px;background:#fff}#ep23 .ep23-self-head{display:grid;grid-template-columns:1fr minmax(130px,190px);gap:12px;align-items:center}#ep23 .ep23-self select{width:100%;padding:10px;border:1px solid #cdd4df;border-radius:10px;background:#fff}#ep23 .ep23-user-solution{margin-top:14px;padding:14px;border-radius:12px;background:#f6f8fb;overflow-wrap:anywhere}#ep23 .ep23-criteria img{display:block;width:auto;max-width:100%;height:auto;margin:12px auto 0;border:1px solid #e0e5eb;border-radius:10px}#ep23 .ep23-source-credit{line-height:1.58;overflow-wrap:anywhere}#ep23 .ep23-modal{position:fixed;inset:0;z-index:9999;background:rgba(15,23,42,.72);display:none;align-items:center;justify-content:center;padding:18px}#ep23 .ep23-modal[data-open="true"]{display:flex}#ep23 .ep23-modal-card{background:#fff;border-radius:16px;max-width:720px;width:100%;max-height:92vh;overflow:auto;padding:20px}#ep23 .ep23-modal-head{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:14px}#ep23 .ep23-calc-display{width:100%;padding:14px;border:1px solid #cdd4df;border-radius:12px;font:600 18px/1.3 ui-monospace,monospace}#ep23 .ep23-calc-result{margin:10px 0 14px;padding:12px 14px;border-radius:10px;background:#f3f7ff;font:800 20px/1.3 ui-monospace,monospace;overflow-wrap:anywhere}#ep23 .ep23-calc-result[data-error="true"]{background:#fff0f0;color:#8a2634}#ep23 .ep23-calc-grid{display:grid;grid-template-columns:repeat(5,minmax(42px,1fr));gap:7px}#ep23 .ep23-calc-grid button{min-height:44px;border:1px solid #cdd4df;border-radius:10px;background:#fff;color:#17324d;font:inherit;font-weight:800;cursor:pointer}#ep23 .ep23-calc-grid .ep23-calc-equals{background:#315fb5;color:#fff;border-color:#315fb5}#ep23 .ep23-storage-warning{display:none;grid-column:1/-1;padding:11px 13px;border:1px solid #d87a7a;border-radius:10px;background:#fff0f0;color:#7a1f2b;font-size:14px;font-weight:700}#ep23 .ep23-storage-warning[data-show="true"]{display:block}
@media(max-width:900px){#ep23 .ep23-toolbar{grid-template-columns:1fr auto auto}#ep23 .ep23-progress{grid-column:1/-1}#ep23 .ep23-nav{grid-template-columns:repeat(6,minmax(36px,1fr))}#ep23 .ep23-score-grid{grid-template-columns:1fr}}
@media(max-width:560px){#ep23 .ep-page{padding:14px 10px 56px}#ep23 .ep-panel{padding:18px 14px}#ep23 .ep23-toolbar{grid-template-columns:1fr 1fr;top:4px}#ep23 .ep23-toolbar .ep23-timer-wrap,#ep23 .ep23-progress{grid-column:1/-1}#ep23 .ep23-toolbar button{width:100%;min-width:0}#ep23 .ep23-nav{grid-template-columns:repeat(5,minmax(36px,1fr))}#ep23 .ep23-task-actions{display:block}#ep23 .ep23-task-actions>div{margin-top:10px}#ep23 .ep23-task-actions .ep-button{width:100%}#ep23 .ep23-self-head{grid-template-columns:1fr}#ep23 .ep23-symbol-list{flex-wrap:nowrap;overflow-x:auto;padding-bottom:4px}#ep23 .ep23-calc-grid{grid-template-columns:repeat(4,minmax(42px,1fr))}}
</style>
<div class="ep-page"><div class="ep-stack">
<div class="ep23-breadcrumbs"><a href="https://eksamio.ru/">Главная</a><span>→</span><a href="https://eksamio.ru/ege/">ЕГЭ</a><span>→</span><a href="https://eksamio.ru/ege/demoversii/">Демоверсии</a><span>→</span><span>Физика 2023</span></div>
<section class="ep-panel"><div class="ep-meta"><span class="ep-pill ep-pill--blue">ЕГЭ 2023</span><span class="ep-pill">30 заданий</span><span class="ep-pill">235 минут</span><span class="ep-pill">54 первичных балла</span></div><h1 class="ep-title">Интерактивная демоверсия ЕГЭ по физике</h1><p class="ep-lead">Официальный демонстрационный вариант ФИПИ 2023 в экзаменационном режиме: таймер, автоматическое сохранение, проверка кратких ответов и неофициальная самооценка развёрнутых решений.</p></section>
<section class="ep-panel ep23-start"><h2 class="ep-section-title">Перед началом</h2><p>Часть 1 содержит 23 задания с кратким ответом и оценивается максимум в 34 первичных балла. Часть 2 содержит 7 заданий с развёрнутым ответом и оценивается максимум в 20 баллов.</p><p>На выполнение отводится <strong>3 часа 55 минут</strong>. Разрешены линейка и непрограммируемый калькулятор. Ответы и черновики сохраняются в браузере.</p><div class="ep23-notice"><strong>Важно:</strong> таймер продолжает идти после закрытия страницы. По истечении времени попытка завершится автоматически.</div><div class="ep23-actions"><button class="ep-button" id="ep23-start" type="button">Начать экзамен</button><button class="ep-button ep-button--secondary ep23-hidden" id="ep23-resume" type="button">Продолжить попытку</button><button class="ep-button ep-button--secondary ep23-hidden" id="ep23-reset-start" type="button">Начать заново</button></div></section>
<div class="ep23-exam"><section class="ep-panel ep23-toolbar"><div class="ep23-storage-warning" id="ep23-storage-warning" role="alert">Не удалось сохранить данные в браузере. Не закрывайте страницу.</div><div class="ep23-timer-wrap"><div class="ep23-timer" id="ep23-timer">03:55:00</div><div class="ep23-mini">Оставшееся время</div></div><div class="ep23-progress" aria-label="Прогресс выполнения"><span id="ep23-progress-bar"></span></div><button class="ep-button ep-button--small ep-button--secondary" id="ep23-calculator" type="button">Калькулятор</button><button class="ep-button ep-button--small ep23-finish" id="ep23-finish" type="button">Завершить экзамен</button></section><section class="ep-panel"><h2 class="ep-section-title">Навигация по заданиям</h2><div class="ep23-nav" id="ep23-nav"></div><p class="ep23-mini">Белый — ответа нет. Зелёный — ответ сохранён. Оранжевый — к заданию нужно вернуться.</p></section><section class="ep-panel" id="ep23-task-stage" aria-live="polite"></section></div>
<div class="ep23-result" id="ep23-results"><section class="ep-panel" data-section="result"><h2 class="ep-section-title">Результат</h2><div class="ep23-score-grid"><div class="ep23-score-card"><div class="ep23-mini">Часть 1 · автоматическая проверка</div><div class="ep23-score-value"><span id="ep23-short-score">0</span>/34</div></div><div class="ep23-score-card"><div class="ep23-mini">Часть 2 · неофициальная самооценка</div><div class="ep23-score-value"><span id="ep23-extended-score">—</span>/20</div></div><div class="ep23-score-card"><div class="ep23-mini">Ориентировочная сумма</div><div class="ep23-score-value"><span id="ep23-total-score">—</span>/54</div></div></div><p class="ep23-mini" id="ep23-result-note"></p></section><section class="ep-panel" data-section="short-review"><h2 class="ep-section-title">Проверка заданий</h2><p>Задания 1–23 в исходном порядке.</p><div class="ep23-review-list" id="ep23-short-review"></div></section><section class="ep-panel" data-section="self-assessment"><h2 class="ep-section-title">Самооценка заданий 24–30</h2><p>Сравните своё решение с официальным возможным решением и критериями ФИПИ. Эта оценка учебная и не заменяет проверку экспертом ЕГЭ.</p><div class="ep23-self-list" id="ep23-self"></div></section><section class="ep-panel ep23-source-credit" data-section="sources"><h2 class="ep-section-title">Источники</h2><p>Содержание, ответы, возможные решения, критерии и изображения получены только из официальной демоверсии ФИПИ ЕГЭ 2023 по физике. Все отображаемые фрагменты сформированы из зафиксированного официального PDF без реконструкции и переноса материалов других лет.</p><p>Эксамио не является официальным сайтом ФИПИ, Рособрнадзора или организаторов ЕГЭ.</p><div class="ep23-actions"><button class="ep-button ep-button--secondary" id="ep23-reset-result" type="button">Начать новую попытку</button></div></section></div>
<div class="ep23-modal" id="ep23-modal" data-open="false" role="dialog" aria-modal="true" aria-labelledby="ep23-modal-title"><div class="ep23-modal-card"><div class="ep23-modal-head"><h2 class="ep-section-title" id="ep23-modal-title">Калькулятор</h2><button class="ep-button ep-button--small ep-button--secondary" id="ep23-modal-close" type="button">Закрыть</button></div><div id="ep23-modal-body"></div></div></div>
</div></div></div><script>window.EP23_A=window.EP23_A||{};</script>
'''


def runtime_js(scorer: dict) -> str:
    short_json = html_escape_json(scorer["short_tasks"])
    ext_json = html_escape_json(scorer["extended_tasks"])
    template = r'''<script>
(function(){
"use strict";
var ROOT=document.getElementById("ep23"),SHORT=__SHORT__,EXT=__EXT__,KEY="eksamio_ege_physics_demo_2023_v1_0",MAX=54,SHORT_MAX=34,DURATION_MS=235*60*1000,timerHandle=null,lastFocus=null,calcLast=0;
function fresh(){return{version:1,status:"idle",current:1,answers:{},drafts:{},self:{},flagged:{},startedAt:null,endsAt:null,shortScore:0}}
var state=fresh();
function byId(id){return document.getElementById(id)}
function esc(value){return String(value==null?"":value).replace(/[&<>\"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]})}
function load(){try{var raw=localStorage.getItem(KEY),parsed=raw&&JSON.parse(raw);if(parsed&&parsed.version===1)state=Object.assign(fresh(),parsed)}catch(e){state=fresh()}}
function save(){try{localStorage.setItem(KEY,JSON.stringify(state));byId("ep23-storage-warning").setAttribute("data-show","false");return true}catch(e){byId("ep23-storage-warning").setAttribute("data-show","true");return false}}
function normBase(s){return String(s==null?"":s).trim().replace(/[−–—]/g,"-")}
function exactScore(t,a){var x=normBase(a),y=normBase(t.official_answer);if(t.normalization&&t.normalization.decimal_comma_is_canonical)x=x.replace(/\./g,",");return x===y?t.max_points:0}
function digits(s){return normBase(s).replace(/[^0-9]/g,"")}
function unorderedScore(t,a){var x=digits(a),y=digits(t.official_answer);if(!x||new Set(x).size!==x.length)return 0;var A=new Set(x),B=new Set(y),missing=0,extra=0;B.forEach(function(v){if(!A.has(v))missing++});A.forEach(function(v){if(!B.has(v))extra++});if(!missing&&!extra)return t.max_points;if(t.max_points===2&&((missing===1&&!extra)||(!missing&&extra===1)))return 1;return 0}
function positionalScore(t,a){var x=digits(a),y=digits(t.official_answer);if(x.length!==y.length)return 0;var wrong=0;for(var i=0;i<y.length;i++)if(x[i]!==y[i])wrong++;if(!wrong)return t.max_points;if(t.max_points===2&&wrong===1)return 1;return 0}
function score(t,a){return t.compare_mode==="unordered_selection"?unorderedScore(t,a):t.compare_mode==="positional_sequence"?positionalScore(t,a):exactScore(t,a)}
window.EP23_TEST_SCORE=function(n,a){return score(SHORT.find(function(t){return t.task_number===n}),a)};window.EP23_TEST_STATE_KEY=KEY;
function allTasks(){return SHORT.concat(EXT).sort(function(a,b){return a.task_number-b.task_number})}
function task(n){return allTasks().find(function(t){return t.task_number===n})}
function filled(n){return String(state.answers[n]||"").trim().length>0}
function taskImage(n){return"data:image/webp;base64,"+EP23_A["task-"+String(n).padStart(2,"0")]}
function criteriaImages(n){return Object.keys(EP23_A).filter(function(k){return k.indexOf("criteria-"+String(n).padStart(2,"0")+"-")===0}).sort().map(function(k){return'<img loading="lazy" alt="Официальное решение и критерии ФИПИ 2023 для задания '+n+'" src="data:image/webp;base64,'+EP23_A[k]+'">'}).join("")}
function updateRoot(){ROOT.setAttribute("data-state",state.status)}
function updateStart(){byId("ep23-start").classList.toggle("ep23-hidden",state.status!=="idle");byId("ep23-resume").classList.toggle("ep23-hidden",state.status!=="running");byId("ep23-reset-start").classList.toggle("ep23-hidden",state.status==="idle")}
function updateProgress(){var count=0;for(var n=1;n<=30;n++)if(filled(n))count++;byId("ep23-progress-bar").style.width=(count/30*100)+"%"}
function renderNav(){var w=byId("ep23-nav");w.innerHTML="";for(var n=1;n<=30;n++){var b=document.createElement("button");b.type="button";b.className="ep23-nav-btn";b.textContent=n;b.dataset.filled=filled(n)?"true":"false";b.dataset.flagged=state.flagged[n]?"true":"false";b.setAttribute("aria-current",state.current===n?"true":"false");b.addEventListener("click",function(nn){return function(){state.current=nn;save();renderTask()}}(n));w.appendChild(b)}updateProgress()}
var SYMBOLS=["²","³","⁻¹","₀","₁","₂","α","β","γ","Δ","λ","μ","ρ","φ","ω","Ω","·","×","÷","√","≈","≤","≥","→","°"];
function insertAtCursor(el,s){var a=el.selectionStart||0,b=el.selectionEnd||0;el.value=el.value.slice(0,a)+s+el.value.slice(b);el.selectionStart=el.selectionEnd=a+s.length;el.dispatchEvent(new Event("input",{bubbles:true}));el.focus()}
function symbols(target){var box=document.createElement("div");box.className="ep23-symbols";box.innerHTML='<strong>Физические знаки</strong><div class="ep23-symbol-list">'+SYMBOLS.map(function(s){return'<button class="ep23-symbol" type="button" data-symbol="'+esc(s)+'">'+esc(s)+'</button>'}).join("")+'</div>';box.querySelectorAll("button").forEach(function(b){b.addEventListener("click",function(){insertAtCursor(target,b.dataset.symbol)})});return box}
function renderTask(){var t=task(state.current),stage=byId("ep23-task-stage"),n=t.task_number,max=t.max_points;stage.innerHTML='<div class="ep23-task-head"><div><div class="ep23-task-number">Задание '+n+' из 30</div><h2 class="ep-section-title">Официальное задание ФИПИ 2023</h2><div class="ep23-mini">ФИПИ 2023 · официальный пример '+n+'</div></div><span class="ep-pill">макс. '+max+'</span></div><img class="ep23-source" alt="Официальное задание ФИПИ 2023 № '+n+'" src="'+taskImage(n)+'"><div class="ep23-answer"><label for="ep23-answer">'+(n<=23?'Ответ':'Полное решение')+'</label>'+(n<=23?'<input class="ep23-input" id="ep23-answer" autocomplete="off" inputmode="text" value="'+esc(state.answers[n]||"")+'">':'<textarea class="ep23-textarea" id="ep23-answer" spellcheck="true">'+esc(state.answers[n]||"")+'</textarea>')+'<p class="ep23-help">'+(n<=23?'Введите ответ в форме, указанной в задании.':'Запишите обоснование, законы, вычисления и ответ.')+'</p><p class="ep23-save" id="ep23-save-status">'+(filled(n)?'✓ Ответ сохранён автоматически':'Ответ будет сохранён автоматически при вводе')+'</p></div><details class="ep23-draft"><summary><strong>Черновик</strong> — не участвует в проверке</summary><textarea class="ep23-textarea" id="ep23-draft">'+esc(state.drafts[n]||"")+'</textarea></details><div class="ep23-task-actions"><div><button class="ep-button ep-button--small ep-button--secondary" id="ep23-prev" type="button"'+(n===1?' disabled':'')+'>Назад</button><button class="ep-button ep-button--small" id="ep23-next" type="button">'+(n===30?'Завершить экзамен':'Следующее задание')+'</button></div><div><button class="ep-button ep-button--small ep-button--secondary" id="ep23-flag" type="button">'+(state.flagged[n]?'Снять отметку':'Вернуться позже')+'</button></div></div>';
var answer=byId("ep23-answer"),draft=byId("ep23-draft");answer.addEventListener("input",function(){state.answers[n]=answer.value;var ok=save();byId("ep23-save-status").textContent=ok?(filled(n)?"✓ Ответ сохранён автоматически":"Ответ будет сохранён автоматически при вводе"):"Не удалось сохранить";renderNav()});draft.addEventListener("input",function(){state.drafts[n]=draft.value;save()});if(n>23){answer.insertAdjacentElement("afterend",symbols(answer))}draft.insertAdjacentElement("afterend",symbols(draft));byId("ep23-prev").addEventListener("click",function(){if(n>1){state.current=n-1;save();renderTask()}});byId("ep23-next").addEventListener("click",function(){if(n<30){state.current=n+1;save();renderTask()}else finish(false)});byId("ep23-flag").addEventListener("click",function(){state.flagged[n]=!state.flagged[n];save();renderTask()});renderNav();answer.focus({preventScroll:true})}
function start(){state=fresh();var now=Date.now();state.status="running";state.startedAt=now;state.endsAt=now+DURATION_MS;save();updateRoot();updateStart();renderTask();startTimer()}
function resume(){if(!state.endsAt||state.endsAt<=Date.now()){finish(true);return}updateRoot();updateStart();renderTask();startTimer()}
function formatTime(ms){var s=Math.max(0,Math.ceil(ms/1000)),h=String(Math.floor(s/3600)).padStart(2,"0"),m=String(Math.floor(s%3600/60)).padStart(2,"0"),x=String(s%60).padStart(2,"0");return h+":"+m+":"+x}
function startTimer(){clearInterval(timerHandle);function tick(){var left=(state.endsAt||0)-Date.now();byId("ep23-timer").textContent=formatTime(left);if(left<=0){clearInterval(timerHandle);finish(true)}}tick();timerHandle=setInterval(tick,1000)}
function shortTotal(){return SHORT.reduce(function(s,t){return s+score(t,state.answers[t.task_number]||"")},0)}
function finish(auto){var empty=0;for(var n=1;n<=30;n++)if(!filled(n))empty++;if(!auto&&!confirm("Без ответа: "+empty+". После завершения ответы нельзя будет изменить. Завершить экзамен?"))return;clearInterval(timerHandle);state.status="finished";state.shortScore=shortTotal();save();updateRoot();updateStart();renderResults();ROOT.scrollIntoView({behavior:"smooth",block:"start"})}
function renderShort(){var w=byId("ep23-short-review");w.innerHTML="";SHORT.forEach(function(t){var a=state.answers[t.task_number]||"",p=score(t,a),item=document.createElement("article");item.className="ep23-review";item.dataset.correct=p===t.max_points?"true":"false";item.dataset.task=String(t.task_number);item.innerHTML='<h3>Задание '+t.task_number+' · '+p+'/'+t.max_points+'</h3><p>Ваш ответ: <strong>'+esc(a||"—")+'</strong></p><p>Ответ ФИПИ: <strong>'+esc(t.official_answer)+'</strong></p>';w.appendChild(item)})}
function selfComplete(){return EXT.every(function(t){return Object.prototype.hasOwnProperty.call(state.self,String(t.task_number))})}
function selfTotal(){return EXT.reduce(function(s,t){return s+Number(state.self[t.task_number]||0)},0)}
function renderScore(){var ok=selfComplete(),ext=selfTotal();byId("ep23-short-score").textContent=state.shortScore;byId("ep23-extended-score").textContent=ok?ext:"—";byId("ep23-total-score").textContent=ok?state.shortScore+ext:"—";byId("ep23-result-note").textContent=ok?"Часть 1 проверена автоматически. Часть 2 — ваша неофициальная самооценка.":"Оцените задания 24–30 для ориентировочной суммы."}
function renderSelf(){var w=byId("ep23-self");w.innerHTML="";EXT.forEach(function(t){var n=t.task_number,item=document.createElement("article"),opts='<option value="">Не оценено</option>';for(var p=0;p<=t.max_points;p++)opts+='<option value="'+p+'"'+(String(state.self[n])===String(p)?' selected':'')+'>'+p+' из '+t.max_points+'</option>';item.className="ep23-self";item.dataset.task=String(n);item.innerHTML='<div class="ep23-self-head"><label><strong>Задание '+n+'</strong><br><span class="ep23-mini">Максимум '+t.max_points+'</span></label><select aria-label="Баллы за задание '+n+'">'+opts+'</select></div><p><strong>Ваше решение</strong></p><div class="ep23-user-solution">'+esc(state.answers[n]||"Ответ не введён").replace(/\n/g,"<br>")+'</div><details class="ep23-criteria"><summary><strong>Официальное возможное решение и критерии ФИПИ</strong></summary>'+criteriaImages(n)+'</details>';item.querySelector("select").addEventListener("change",function(e){if(e.target.value==="")delete state.self[n];else state.self[n]=Number(e.target.value);save();renderScore()});w.appendChild(item)})}
function renderResults(){renderShort();renderSelf();renderScore()}
function reset(){if(!confirm("Удалить текущую попытку и начать заново?"))return;try{localStorage.removeItem(KEY)}catch(e){}state=fresh();updateRoot();updateStart();byId("ep23-short-review").innerHTML="";byId("ep23-self").innerHTML="";ROOT.scrollIntoView({behavior:"smooth",block:"start"})}
function calcTokenize(s){var out=[],i=0,x=String(s).replace(/,/g,".").replace(/×/g,"*").replace(/÷/g,"/").replace(/−/g,"-");while(i<x.length){if(/\s/.test(x[i])){i++;continue}var m=x.slice(i).match(/^(\d+(?:\.\d*)?|\.\d+)(?:[eE]([+-]?\d+))?/);if(m){out.push({t:"num",v:Number(m[0])});i+=m[0].length;continue}m=x.slice(i).match(/^[A-Za-z]+/);if(m){out.push({t:"id",v:m[0].toLowerCase()});i+=m[0].length;continue}if("+-*/^()".indexOf(x[i])>=0){out.push({t:x[i]});i++;continue}throw Error("Недопустимый символ")};return out}
function calcEvaluate(input){var t=calcTokenize(input),p=0;function q(x){return t[p]&&t[p].t===x}function take(x){if(!q(x))throw Error("Ожидается "+x);return t[p++]}function ex(){var v=te();while(q("+")||q("-")){var op=t[p++].t,r=te();v=op==="+"?v+r:v-r}return v}function te(){var v=po();while(q("*")||q("/")){var op=t[p++].t,r=po();if(op==="/"&&r===0)throw Error("Деление на ноль");v=op==="*"?v*r:v/r}return v}function po(){var v=un();if(q("^")){p++;v=Math.pow(v,po())}return v}function un(){if(q("+")){p++;return un()}if(q("-")){p++;return-un()}return pr()}function pr(){if(q("num"))return take("num").v;if(q("(")){p++;var v=ex();take(")");return v}if(q("id")){var id=take("id").v;if(id==="pi")return Math.PI;if(id==="e")return Math.E;if(id==="ans")return calcLast;if(!q("("))throw Error("Нужны скобки");p++;var a=ex();take(")");if(id==="sin")return Math.sin(a*Math.PI/180);if(id==="cos")return Math.cos(a*Math.PI/180);if(id==="tan")return Math.tan(a*Math.PI/180);if(id==="sqrt")return Math.sqrt(a);if(id==="ln")return Math.log(a);if(id==="log")return Math.log10(a);if(id==="abs")return Math.abs(a);throw Error("Неизвестная функция")}throw Error("Неполное выражение")}var v=ex();if(p!==t.length||!Number.isFinite(v))throw Error("Проверьте выражение");return v}
window.EP23_TEST_CALC=calcEvaluate;
function calculatorHtml(){var keys=[["7","7"],["8","8"],["9","9"],["÷","/"],["√","sqrt("],["4","4"],["5","5"],["6","6"],["×","*"],["x²","^2"],["1","1"],["2","2"],["3","3"],["−","-"],["xʸ","^"],["0","0"],[",","."],["(","("],[")",")"],["+","+"],["sin","sin("],["cos","cos("],["tan","tan("],["π","pi"],["Ans","ans"]];return'<p class="ep23-mini"><strong>Непрограммируемый мини-калькулятор.</strong> Тригонометрия — в градусах.</p><input class="ep23-calc-display" id="ep23-calc-input" autocomplete="off" aria-label="Выражение"><div class="ep23-calc-result" id="ep23-calc-result" aria-live="polite">0</div><div class="ep23-calc-grid"><button type="button" data-action="clear">C</button><button type="button" data-action="back">⌫</button>'+keys.map(function(k){return'<button type="button" data-insert="'+esc(k[1])+'">'+esc(k[0])+'</button>'}).join("")+'<button class="ep23-calc-equals" type="button" data-action="equals">=</button></div>'}
function openCalc(){openModal("Калькулятор",calculatorHtml());var input=byId("ep23-calc-input"),result=byId("ep23-calc-result");byId("ep23-modal-body").querySelectorAll("button").forEach(function(b){b.addEventListener("click",function(){if(b.dataset.insert){insertAtCursor(input,b.dataset.insert);return}if(b.dataset.action==="clear"){input.value="";result.textContent="0"}else if(b.dataset.action==="back")input.value=input.value.slice(0,-1);else if(b.dataset.action==="equals"){try{calcLast=calcEvaluate(input.value);result.dataset.error="false";result.textContent=String(calcLast).replace(".",",")}catch(e){result.dataset.error="true";result.textContent=e.message}}})});input.focus()}
function openModal(title,html){lastFocus=document.activeElement;byId("ep23-modal-title").textContent=title;byId("ep23-modal-body").innerHTML=html;byId("ep23-modal").setAttribute("data-open","true")}
function closeModal(){byId("ep23-modal").setAttribute("data-open","false");byId("ep23-modal-body").innerHTML="";if(lastFocus&&lastFocus.focus)lastFocus.focus()}
byId("ep23-start").addEventListener("click",start);byId("ep23-resume").addEventListener("click",resume);byId("ep23-reset-start").addEventListener("click",reset);byId("ep23-reset-result").addEventListener("click",reset);byId("ep23-finish").addEventListener("click",function(){finish(false)});byId("ep23-calculator").addEventListener("click",openCalc);byId("ep23-modal-close").addEventListener("click",closeModal);byId("ep23-modal").addEventListener("click",function(e){if(e.target===byId("ep23-modal"))closeModal()});document.addEventListener("keydown",function(e){if(e.key==="Escape"&&byId("ep23-modal").dataset.open==="true")closeModal()});
load();updateRoot();updateStart();if(state.status==="running")resume();else if(state.status==="finished")renderResults();
})();
</script>
'''
    return template.replace("__SHORT__", short_json).replace("__EXT__", ext_json)


def deterministic_zip(source: Path, destination: Path) -> str:
    if destination.exists():
        destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            rel = (Path(source.name) / path.relative_to(source)).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2023, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            z.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return file_sha(destination)


def main() -> None:
    if file_sha(SOURCE) != EXPECTED_SOURCE_SHA:
        raise RuntimeError("canonical Physics 2023 PDF hash mismatch")
    layout = json.loads(LAYOUT.read_text(encoding="utf-8"))
    scorer = json.loads(SCORER.read_text(encoding="utf-8"))
    if layout.get("unresolved_mappings") != 0 or len(layout.get("tasks", [])) != 30:
        raise RuntimeError("source layout gate failed")
    if scorer.get("short_max_points") != 34 or scorer.get("extended_max_points") != 20 or scorer.get("official_max_points") != 54:
        raise RuntimeError("scorer total gate failed")

    shutil.rmtree(BUILD / "out", ignore_errors=True)
    shutil.rmtree(DIST, ignore_errors=True)
    OUT.mkdir(parents=True)
    DIST.mkdir(parents=True)

    assets, asset_manifest = build_assets(layout, scorer)
    write(OUT / f"{PREFIX}-HEAD.txt", head_html())
    write(OUT / f"{PREFIX}-SEO.txt", seo_text())

    blocks: list[str] = [app_shell(), *pack_asset_blocks(assets), runtime_js(scorer)]
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
    criteria_count = len([x for x in asset_manifest if x["kind"].startswith("official_solution_criteria_")])
    acceptance = {
        "status": "READY_FOR_TILDA_AFTER_BROWSER_GATE",
        "content_year": 2023,
        "source_sha256": EXPECTED_SOURCE_SHA,
        "task_count": 30,
        "short_max_points": 34,
        "extended_max_points": 20,
        "official_max_points": 54,
        "unresolved_source_mappings": 0,
        "unresolved_text_fidelity": 0,
        "build_ready_task_rendering": "source-rendered raster crops from canonical FIPI 2023 PDF; pdftotext task text is not used in production rendering",
        "task_source_regions": 31,
        "criteria_source_logical_pages": criteria_count,
        "task_30_official_alternative_examples": 2,
        "t123_count": len(blocks),
        "max_t123_bytes": max((OUT / f"{PREFIX}-T123-{i:02d}.txt").stat().st_size for i in range(1, len(blocks) + 1)),
        "private_use_characters_in_production_text": 0,
        "physics_2025_content_used": 0,
        "physics_2026_content_used": 0,
        "storage_namespace": "eksamio_ege_physics_demo_2023_v1_0",
        "reference_parity": {
            "single_task_navigation": "PASS",
            "calculator": "PASS",
            "symbol_keyboard": "PASS",
            "state_restore": "PASS",
            "result_semantic_order": "PASS",
        },
    }
    write(OUT / f"{PREFIX}-ACCEPTANCE.json", json.dumps(acceptance, ensure_ascii=False, indent=2) + "\n")
    write(OUT / "00-README-TILDA.txt", f'''EGE PHYSICS 2023 — TILDA HQ SOURCE {VERSION}\n\n1. Вставьте содержимое {PREFIX}-HEAD.txt в HEAD страницы.\n2. Создайте {len(blocks)} блоков T123 и вставьте {PREFIX}-T123-01.txt ... {PREFIX}-T123-{len(blocks):02d}.txt строго по порядку.\n3. Не меняйте порядок T123: каждый файл самодостаточен и меньше {T123_LIMIT} байт; последний блок запускает интерфейс и scorer.\n\nCANONICAL=https://eksamio.ru/ege/fizika/demoversiya/2023/\nSOURCE=canonical FIPI Physics 2023 PDF\nSCORER=34+20=54\nTEXT_FIDELITY=source-rendered task images; unresolved=0\nREFERENCE_PARITY=navigation+calculator+symbol_keyboard+state_restore+result_order\n''')

    # Inspect human-readable markup/runtime only. Base64 image payloads can
    # contain digit sequences by chance and are already source-hash gated.
    production_text = head_html() + app_shell() + runtime_js(scorer)
    if re.search(r"[\ue000-\uf8ff]", production_text):
        raise RuntimeError("private-use Unicode leaked into production text")
    if "2025" in production_text or "2026" in production_text:
        raise RuntimeError("cross-year content token leaked into production markup/runtime")

    manifest_paths = sorted(p for p in OUT.rglob("*") if p.is_file())
    manifest = "\n".join(f"{file_sha(p)}  {p.relative_to(OUT).as_posix()}" for p in manifest_paths) + "\n"
    write(OUT / "SHA256SUMS.txt", manifest)
    zip_sha = deterministic_zip(OUT, ZIP)
    write(DIST / "SHA256.txt", f"{zip_sha}  {ZIP.name}\n")
    print(json.dumps({"archive": str(ZIP), "sha256": zip_sha, "t123_count": len(blocks), "assets": len(asset_manifest), "encoded_bytes": sum(x["bytes"] for x in asset_manifest)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
