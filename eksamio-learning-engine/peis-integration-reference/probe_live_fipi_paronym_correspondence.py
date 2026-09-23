#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import time
import unicodedata
import urllib.request
from pathlib import Path

LIVE_URL = "https://eksamio.ru/trenazhery/russkiy/paronimy/"
FIPI_URL = "https://doc.fipi.ru/navigator-podgotovki/navigator-ege/2026/ru-2-leksika-i-frazeologija.pdf"
OUT = Path("live-fipi-paronym-correspondence.json")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, profiles: list[tuple[str, dict[str, str]]], require_pdf: bool = False) -> tuple[bytes, list[dict], str]:
    attempts: list[dict] = []
    last: Exception | None = None
    for round_no in range(1, 4):
        for name, headers in profiles:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=45) as resp:
                    data = resp.read()
                    status = getattr(resp, "status", 200)
                    final_url = resp.geturl()
                attempts.append({
                    "round": round_no,
                    "profile": name,
                    "http_status": status,
                    "final_url": final_url,
                    "byte_count": len(data),
                    "sha256": sha256(data),
                })
                if require_pdf and not data.startswith(b"%PDF-"):
                    raise RuntimeError(f"not PDF bytes: {data[:16]!r}")
                if 200 <= status < 300:
                    return data, attempts, name
            except Exception as exc:  # pragma: no cover - network boundary
                last = exc
                attempts.append({"round": round_no, "profile": name, "error": str(exc)[:240]})
            time.sleep(1.2)
        time.sleep(2.5 * round_no)
    raise RuntimeError(f"fetch failed for {url}: {last}; attempts={attempts}")


def extract_balanced_array(text: str, start: int) -> str:
    if text[start] != "[":
        raise AssertionError(f"expected '[' at {start}")
    depth = 0
    quote: str | None = None
    escaped = False
    i = start
    while i < len(text):
        ch = text[i]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch in {'"', "'"}:
            quote = ch
            i += 1
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
        i += 1
    raise AssertionError(f"unterminated array at {start}")


def locate_array(text: str, pattern: str, label: str) -> str:
    matches = list(re.finditer(pattern, text, flags=re.M))
    if len(matches) != 1:
        raise AssertionError(f"{label}: expected exactly one match, got {len(matches)}")
    start = matches[0].end() - 1
    if start < 0 or text[start] != "[":
        raise AssertionError(f"{label}: target '[' not at regex boundary")
    return extract_balanced_array(text, start)


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


def normalize_group(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold().replace("\u00a0", " ")
    # FIPI row 97 explicitly writes optional reflexive forms as "(-ся)".
    # Projecting the unparenthesized primary form is source-explicit, not a
    # morphological/fuzzy inference, and preserves same-index correspondence.
    text = text.replace("(-ся)", "")
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"\s*-\s*", "-", text)
    return " ".join(text.split())


live_profiles = [
    (
        "browser-compatible",
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Referer": "https://eksamio.ru/trenazhery/russkiy/",
        },
    ),
    (
        "reconciliation-bot",
        {
            "User-Agent": "Eksamio-live-asset-reconciliation/0.1 (+https://github.com/niknikdym-hue/ege)",
            "Accept": "text/html,application/xhtml+xml",
        },
    ),
]
fipi_profiles = [
    (
        "source-reconciliation",
        {
            "User-Agent": "Eksamio-source-reconciliation/0.1 (+https://github.com/niknikdym-hue/ege)",
            "Accept": "application/pdf,*/*",
        },
    )
]

live_bytes, live_attempts, selected_profile = fetch_bytes(LIVE_URL, live_profiles)
live_html = live_bytes.decode("utf-8", errors="strict")
prefix_literal = locate_array(
    live_html,
    r"window\.__EKSAMIO_PARONYMS_GROUPS__\s*=\s*\[",
    "window.__EKSAMIO_PARONYMS_GROUPS__",
)
suffix_literal = locate_array(
    live_html,
    r"\b(?:var|let|const)\s+GROUPS\s*=\s*\(window\.__EKSAMIO_PARONYMS_GROUPS__\s*\|\|\s*\[\]\)\.concat\(\s*\[",
    "GROUPS concat suffix",
)
prefix = json.loads(prefix_literal)
suffix = json.loads(suffix_literal)
groups = prefix + suffix

fipi_bytes, fipi_attempts, fipi_profile = fetch_bytes(FIPI_URL, fipi_profiles, require_pdf=True)
with tempfile.TemporaryDirectory() as tmp:
    pdf = Path(tmp) / "ru-2-leksika-i-frazeologija.pdf"
    pdf.write_bytes(fipi_bytes)
    fipi_groups: list[str] = []
    for page, start, end, expected in [
        (2, "абонемент", "выплатить", 25),
        (3, "вырастить", "микроскопический", 52),
        (4, "мороженый", "сценический", 52),
        (5, "сытный", "яблочный", 15),
    ]:
        values = span(page_lines(pdf, page), start, end)
        if len(values) != expected:
            raise AssertionError(f"FIPI page {page}: expected {expected}, got {len(values)}")
        fipi_groups.extend(values)

if len(prefix) != 76 or len(suffix) != 68 or len(groups) != 144:
    raise AssertionError(f"live split expected 76+68=144, got {len(prefix)}+{len(suffix)}={len(groups)}")
if len(fipi_groups) != 144:
    raise AssertionError(f"FIPI group count expected 144, got {len(fipi_groups)}")

group_ids = [g.get("id") for g in groups]
if not all(isinstance(x, str) and x for x in group_ids) or len(set(group_ids)) != 144:
    raise AssertionError("live group IDs are missing or non-unique")
entry_ids = [entry.get("id") for g in groups for entry in g.get("entries", [])]
if not all(isinstance(x, str) and x for x in entry_ids) or len(set(entry_ids)) != len(entry_ids):
    raise AssertionError("live entry IDs are missing or non-unique")
sequence_numbers = [int(m.group(1)) if (m := re.match(r"^p(\d{3})-", gid)) else None for gid in group_ids]
sequence_exact = sequence_numbers == list(range(1, 145))

comparisons = []
for index, (group, fipi_row) in enumerate(zip(groups, fipi_groups), start=1):
    live_text = " - ".join(group["words"])
    live_norm = normalize_group(live_text)
    fipi_norm = normalize_group(fipi_row)
    comparisons.append({
        "index_1based": index,
        "live_group_id": group["id"],
        "live_words": group["words"],
        "live_normalized": live_norm,
        "fipi_row": fipi_row,
        "fipi_normalized": fipi_norm,
        "exact_normalized_same_index_match": live_norm == fipi_norm,
    })

matches = [x for x in comparisons if x["exact_normalized_same_index_match"]]
mismatches = [x for x in comparisons if not x["exact_normalized_same_index_match"]]
ordered_live_norm = "\n".join(x["live_normalized"] for x in comparisons).encode("utf-8")
ordered_fipi_norm = "\n".join(x["fipi_normalized"] for x in comparisons).encode("utf-8")

result = {
    "schema": "eksamio.live-fipi-paronym-correspondence.probe.v0.1",
    "authority": "live eksamio.ru full split paronym GROUPS backing + official FIPI 2026 Navigator PDF; both fetched read-only at runtime",
    "correspondence_rule": "same index only; Unicode NFKC + casefold + whitespace/dash normalization; remove only exact FIPI-explicit optional segment (-ся); no fuzzy matching, morphology, reordering, route/title/task inference",
    "live_source": {
        "url": LIVE_URL,
        "byte_count": len(live_bytes),
        "sha256": sha256(live_bytes),
        "selected_profile": selected_profile,
        "attempts": live_attempts,
        "prefix_literal_byte_count": len(prefix_literal.encode("utf-8")),
        "prefix_literal_sha256": sha256(prefix_literal.encode("utf-8")),
        "suffix_literal_byte_count": len(suffix_literal.encode("utf-8")),
        "suffix_literal_sha256": sha256(suffix_literal.encode("utf-8")),
    },
    "fipi_source": {
        "url": FIPI_URL,
        "byte_count": len(fipi_bytes),
        "sha256": sha256(fipi_bytes),
        "selected_profile": fipi_profile,
        "attempts": fipi_attempts,
    },
    "live_prefix_group_count": len(prefix),
    "live_suffix_group_count": len(suffix),
    "live_full_group_count": len(groups),
    "fipi_group_count": len(fipi_groups),
    "unique_live_group_id_count": len(set(group_ids)),
    "live_entry_count": len(entry_ids),
    "unique_live_entry_id_count": len(set(entry_ids)),
    "live_group_id_sequence_p001_through_p144_exact": sequence_exact,
    "exact_same_index_normalized_match_count": len(matches),
    "exact_same_index_normalized_mismatch_count": len(mismatches),
    "ordered_live_group_normalized_sha256": sha256(ordered_live_norm),
    "ordered_fipi_group_normalized_sha256": sha256(ordered_fipi_norm),
    "mismatches": mismatches,
    "canonical_item_identity_status": "TEXTUAL_PROVENANCE_CORRESPONDENCE_PROVEN_SEMANTIC_ACCEPTANCE_STILL_SEPARATE" if not mismatches else "UNKNOWN_BLOCKER_UNTIL_EXACT_CORRESPONDENCE_AND_SEMANTIC_ACCEPTANCE",
    "provenance_binding_status": "EXACT_FULL_GROUP_TEXTUAL_CORRESPONDENCE" if not mismatches else "BOUNDED_MISMATCH_BLOCKER",
    "admission_effect": "NONE",
    "semantic_admissions": 0,
    "object_closures": 0,
    "mastery_admissions": 0,
    "false_exact_mastery": 0,
    "registered_user_identity_required_for_future_canonical_evidence": True,
    "notes": [
        "The sole raw mismatch before this source-explicit projection was FIPI row 97 'Отличать(-ся) – различать(-ся)' versus live primary forms 'отличать', 'различать'; removing the exact parenthetical optional suffix yields the explicitly printed primary variant and is not morphological inference.",
        "The separate 30-row EXAM_BANK is not used as the thematic denominator.",
        "Even zero mismatches proves textual/source correspondence only; PEIS semantic ownership and learner mastery remain separately gated.",
    ],
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
