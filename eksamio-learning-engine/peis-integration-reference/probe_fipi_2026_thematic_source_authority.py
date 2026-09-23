#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

UA = "Eksamio-source-reconciliation/0.1 (+https://github.com/niknikdym-hue/ege)"
SOURCES = {
    "orthography": "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-5-orfografija.pdf",
    "lexicon_phraseology": "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-2-leksika-i-frazeologija.pdf",
    "phonetics_orthoepy": "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-1-fonetika.pdf",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    last = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
            if not data.startswith(b"%PDF-"):
                raise RuntimeError(f"not PDF bytes: {data[:16]!r}")
            return data
        except Exception as exc:  # pragma: no cover - network boundary
            last = exc
            time.sleep(attempt * 2)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def page_lines(pdf: Path, page: int) -> list[str]:
    proc = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-layout", str(pdf), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    text = proc.stdout.decode("utf-8", errors="strict").replace("\u00a0", " ")
    return [" ".join(line.strip().split()) for line in text.splitlines() if line.strip()]


def span(lines: list[str], start: str, end: str) -> list[str]:
    folded = [line.casefold() for line in lines]
    s = next((i for i, line in enumerate(folded) if line.startswith(start.casefold())), None)
    e = next((i for i, line in enumerate(folded) if i >= (s or 0) and line.startswith(end.casefold())), None)
    if s is None or e is None or e < s:
        raise AssertionError(f"span not found: {start!r} .. {end!r}")
    return lines[s : e + 1]


def page_spans(pdf: Path, specs: list[tuple[int, str, str, int]]) -> dict:
    counts = []
    boundaries = []
    for page, start, end, expected in specs:
        values = span(page_lines(pdf, page), start, end)
        actual = len(values)
        if actual != expected:
            raise AssertionError(f"page {page}: {start!r}..{end!r}: expected {expected}, got {actual}; values={values}")
        counts.append(actual)
        boundaries.append({"page": page, "first": values[0], "last": values[-1], "count": actual})
    return {"page_counts": counts, "total": sum(counts), "boundaries": boundaries}


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    local = {}
    exact = {}
    for key, url in SOURCES.items():
        data = fetch(url)
        path = root / f"{key}.pdf"
        path.write_bytes(data)
        local[key] = path
        exact[key] = {"url": url, "byte_count": len(data), "sha256": sha256(data)}

    dictionary = page_spans(
        local["orthography"],
        [
            (1, "абитуриент", "аттракцион", 18),
            (2, "аукцион", "декларация", 52),
            (3, "декорация", "колебание", 52),
            (4, "коллектив", "оборона", 52),
            (5, "одолеть", "рациональный", 52),
            (6, "реалист", "уничтожить", 52),
            (7, "утрамбовать", "эстакада", 30),
        ],
    )
    assert dictionary["total"] == 308

    phraseology = page_spans(
        local["lexicon_phraseology"],
        [
            (6, "альфа и омега", "во весь рост", 44),
            (7, "во всяком случае", "души не чаять", 52),
            (8, "душой и телом", "между делом", 52),
            (9, "между прочим", "по белу свету", 52),
            (10, "поднять на ноги", "спать мёртвым сном", 52),
            (11, "с первого взгляда", "язык не повернулся", 33),
        ],
    )
    assert phraseology["total"] == 285

    paronyms = page_spans(
        local["lexicon_phraseology"],
        [
            (2, "абонемент", "выплатить", 25),
            (3, "вырастить", "микроскопический", 52),
            (4, "мороженый", "сценический", 52),
            (5, "сытный", "яблочный", 15),
        ],
    )
    assert paronyms["total"] == 144

    orthoepy_page1 = " ".join(page_lines(local["phonetics_orthoepy"], 1)).casefold()
    orthoepy_page1 = orthoepy_page1.replace("–", "-").replace("—", "-")
    required_markers = [
        "основные нормы современного литературного произношения",
        "произношение безударных гласных",
        "особенности произношения иноязычных слов",
        "нормы ударения",
        "орфоэпическому списку",
        "2026",
    ]
    missing = [marker for marker in required_markers if marker.casefold() not in orthoepy_page1]
    if missing:
        raise AssertionError(f"missing orthoepy scope markers: {missing}")

    result = {
        "schema": "eksamio.fipi-2026-thematic-source-authority-probe.v0.1",
        "authority": "official FIPI 2026 Navigator PDFs fetched read-only at runtime",
        "exact_sources": exact,
        "dictionary_words": {
            **dictionary,
            "live_known_count": 308,
            "count_correspondence": "EXACT_308_VS_308_BUT_ROW_BY_ROW_BINDING_NOT_YET_ADMITTED",
        },
        "phraseology": {
            **phraseology,
            "live_known_count": 285,
            "count_correspondence": "EXACT_285_VS_285_BUT_ROW_BY_ROW_BINDING_NOT_YET_ADMITTED",
        },
        "paronyms": {
            **paronyms,
            "official_group_count": 144,
            "live_exam_bank_row_count": 30,
            "finding": "LIVE_30_ROW_EXAM_BANK_IS_NOT_THE_FULL_FIPI_PARONYM_GROUP_INVENTORY",
        },
        "orthoepy": {
            "scope_markers_present": True,
            "finding": "FIPI_2026_SCOPE_EXPLICITLY_INCLUDES_PRONUNCIATION_AND_STRESS; STRESS_LIST_DOES_NOT_BY_ITSELF_CLOSE_PRONUNCIATION_EVIDENCE",
        },
        "admission_effect": "NONE",
        "semantic_admissions": 0,
        "object_closures": 0,
        "mastery_admissions": 0,
        "false_exact_mastery": 0,
        "registered_user_identity_required_for_future_canonical_evidence": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
