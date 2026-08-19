#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import pymupdf as fitz


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def transformed_bounds(rect: fitz.Rect, matrix: fitz.Matrix) -> fitz.Rect:
    pts = [
        fitz.Point(rect.x0, rect.y0) * matrix,
        fitz.Point(rect.x1, rect.y0) * matrix,
        fitz.Point(rect.x0, rect.y1) * matrix,
        fitz.Point(rect.x1, rect.y1) * matrix,
    ]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    return fitz.Rect(min(xs), min(ys), max(xs), max(ys))


def group_words(words: list[dict]) -> list[str]:
    words = sorted(words, key=lambda w: (w['y0'], w['x0']))
    lines: list[dict] = []
    for word in words:
        y = word['y0']
        h = max(1.0, word['y1'] - word['y0'])
        tol = max(2.2, min(5.0, h * 0.45))
        if not lines or abs(y - lines[-1]['anchor']) > tol:
            lines.append({'anchor': y, 'items': [word]})
        else:
            lines[-1]['items'].append(word)
            lines[-1]['anchor'] = (lines[-1]['anchor'] * 3 + y) / 4
    return [' '.join(w['text'] for w in sorted(line['items'], key=lambda x: x['x0'])) for line in lines]


def local_word(vr: fitz.Rect, origin_x: float, origin_y: float, raw) -> dict:
    return {
        'text': raw[4],
        'x0': round(vr.x0 - origin_x, 3),
        'y0': round(vr.y0 - origin_y, 3),
        'x1': round(vr.x1 - origin_x, 3),
        'y1': round(vr.y1 - origin_y, 3),
        'block': raw[5], 'line': raw[6], 'word': raw[7],
    }


def inspect_pdf(pdf_path: Path, out_dir: Path, year: int, role: str) -> dict:
    doc = fitz.open(pdf_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    page_rows = []
    full_text_parts = []
    printed_no = 0

    for physical_index, page in enumerate(doc, start=1):
        matrix = page.rotation_matrix
        visual = transformed_bounds(page.mediabox, matrix)
        is_two_up = visual.width > visual.height * 1.18
        mid = (visual.x0 + visual.x1) / 2
        buckets = {'full': [], 'left': [], 'right': []}

        for raw in page.get_text('words', sort=False):
            vr = transformed_bounds(fitz.Rect(raw[0], raw[1], raw[2], raw[3]), matrix)
            if is_two_up:
                half = 'left' if (vr.x0 + vr.x1) / 2 < mid else 'right'
                origin_x = visual.x0 if half == 'left' else mid
                buckets[half].append(local_word(vr, origin_x, visual.y0, raw))
            else:
                buckets['full'].append(local_word(vr, visual.x0, visual.y0, raw))

        halves = ('left', 'right') if is_two_up else ('full',)
        for half in halves:
            words = buckets[half]
            lines = group_words(words)
            text = '\n'.join(lines).strip()
            if len(re.sub(r'\s+', '', text)) < 8:
                continue
            printed_no += 1
            text += '\n'
            full_text_parts.append(text)
            ordered = sorted(words, key=lambda w: (w['y0'], w['x0']))
            width_pt = visual.width / 2 if is_two_up else visual.width
            task_candidates = []
            for w in ordered:
                t = w['text'].strip().rstrip('.)')
                if t.isdigit() and 1 <= int(t) <= 30 and w['x0'] < min(100, width_pt * 0.25):
                    task_candidates.append({'task': int(t), 'rect': [w['x0'], w['y0'], w['x1'], w['y1']]})
            ors = [
                [w['x0'], w['y0'], w['x1'], w['y1']]
                for w in ordered if w['text'].strip().upper() == 'ИЛИ'
            ]
            (out_dir / f'page-{printed_no:02d}.txt').write_text(text, encoding='utf-8')
            (out_dir / f'page-{printed_no:02d}.json').write_text(json.dumps({
                'printed_page': printed_no,
                'physical_pdf_page': physical_index,
                'half': half,
                'visual_width_pt': round(width_pt, 3),
                'visual_height_pt': round(visual.height, 3),
                'word_count': len(ordered),
                'task_candidates': task_candidates,
                'or_marks': ors,
                'words': ordered,
            }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            page_rows.append({
                'printed_page': printed_no,
                'physical_pdf_page': physical_index,
                'half': half,
                'visual_width_pt': round(width_pt, 3),
                'visual_height_pt': round(visual.height, 3),
                'word_count': len(ordered),
                'task_candidates': task_candidates,
                'or_count': len(ors),
                'text_file': f'{role}/page-{printed_no:02d}.txt',
                'coordinates_file': f'{role}/page-{printed_no:02d}.json',
            })

    full_text = '\n'.join(full_text_parts)
    lower = full_text.lower()
    checks = {
        'contains_year': str(year) in full_text,
        'contains_mathematics_marker': 'математ' in lower,
        'contains_profile_marker': ('профиль' in lower) if role in {'demo', 'spec'} else None,
        'standalone_project_marker': bool(re.search(r'(?mi)^\s*проект\s*$', full_text)),
    }
    page_map = {
        'role': role,
        'source_file': pdf_path.name,
        'source_bytes': pdf_path.stat().st_size,
        'source_sha256': sha256_file(pdf_path),
        'physical_pdf_pages': len(doc),
        'generated_printed_pages': printed_no,
        'geometry_rule': 'rotation-aware; landscape/two-up pages split at transformed visual midpoint; portrait pages kept whole',
        'checks': checks,
        'pages': page_rows,
    }
    (out_dir / 'PAGE-MAP.json').write_text(json.dumps(page_map, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (out_dir / 'ALL-TEXT.txt').write_text(full_text, encoding='utf-8')
    return page_map, full_text


def structure_candidates(text: str) -> dict:
    compact = re.sub(r'\s+', ' ', text)
    low = compact.lower()
    patterns = {
        'task_count_phrases': [r'(?:содержит|включает|состоит из)\s+(\d+)\s+задан'],
        'duration_minutes': [r'(\d+)\s*минут'],
        'duration_hours': [r'(\d+)\s*час(?:а|ов)?(?:\s+(\d+)\s*минут)?'],
        'max_score_phrases': [r'максимальн[^.]{0,120}?первичн[^.]{0,120}?(\d+)'],
        'short_part_ranges': [r'задан(?:ия|ий)\s+(\d+)\s*[–-]\s*(\d+)'],
    }
    out = {}
    for key, pats in patterns.items():
        vals = []
        for pat in pats:
            for m in re.finditer(pat, low, flags=re.I):
                vals.append({'match': m.group(0), 'groups': list(m.groups())})
        out[key] = vals[:50]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--out-dir', required=True)
    args = ap.parse_args()

    repo = Path(args.repo_root).resolve()
    src = repo / f'matematika-source-{args.year}'
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    files = {
        'demo': src / f'ege-{args.year}-matematika-profil-demoversiya.pdf',
        'spec': src / f'ege-{args.year}-matematika-profil-specifikatsiya.pdf',
        'cod': src / f'ege-{args.year}-matematika-kodifikator.pdf',
    }
    for role, fp in files.items():
        if not fp.exists():
            raise FileNotFoundError(f'{role}: {fp}')

    maps = {}
    texts = {}
    for role, fp in files.items():
        maps[role], texts[role] = inspect_pdf(fp, out / role, args.year, role)

    hard_errors = []
    for role in ('demo', 'spec', 'cod'):
        c = maps[role]['checks']
        if not c['contains_year']:
            hard_errors.append(f'{role}: year marker {args.year} not found')
        if not c['contains_mathematics_marker']:
            hard_errors.append(f'{role}: mathematics marker not found')
    for role in ('demo', 'spec'):
        if not maps[role]['checks']['contains_profile_marker']:
            hard_errors.append(f'{role}: profile marker not found')

    lock = {
        'exam': 'ЕГЭ', 'subject': 'математика', 'level': 'профильный', 'year': args.year,
        'source_authority': 'official FIPI source files mirrored in repository; content authority is FIPI for the exact year',
        'sources': {role: {
            'file': fp.name,
            'sha256': maps[role]['source_sha256'],
            'bytes': maps[role]['source_bytes'],
            'physical_pdf_pages': maps[role]['physical_pdf_pages'],
            'printed_pages': maps[role]['generated_printed_pages'],
            'checks': maps[role]['checks'],
        } for role, fp in files.items()},
        'status': 'SOURCE_BYTES_AND_PAGE_MAP_LOCKED' if not hard_errors else 'SOURCE_PRELOCK_FAIL',
        'hard_errors': hard_errors,
    }
    (out / 'SOURCE-LOCK.json').write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    candidates = {
        'year': args.year,
        'status': 'DIAGNOSTIC_ONLY_NOT_EXAM_LOCK',
        'demo': structure_candidates(texts['demo']),
        'spec': structure_candidates(texts['spec']),
        'note': 'Candidates must be manually/source-audited before EXAM-LOCK. Never inherit neighboring-year numbers.',
    }
    (out / 'STRUCTURE-CANDIDATES.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    validation = [
        f'PROFILE MATH {args.year} SOURCE PRELOCK ' + ('PASS' if not hard_errors else 'FAIL'),
        'authority: official FIPI year-specific repo sources',
    ]
    for role in ('demo','spec','cod'):
        s = lock['sources'][role]
        validation.append(f"{role}: {s['file']} sha256={s['sha256']} bytes={s['bytes']} physical={s['physical_pdf_pages']} printed={s['printed_pages']} checks={s['checks']}")
    if hard_errors:
        validation.extend('ERROR: ' + e for e in hard_errors)
    else:
        validation.append('READY_FOR_EXAM_ANSWER_VISUAL_LOCK: YES')
        validation.append('READY_FOR_BUILD: NO')
    (out / 'SOURCE-VALIDATION.txt').write_text('\n'.join(validation) + '\n', encoding='utf-8')
    print('\n'.join(validation))
    if hard_errors:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
