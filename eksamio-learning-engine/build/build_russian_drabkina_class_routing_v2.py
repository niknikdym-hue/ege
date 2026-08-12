from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import build_russian_drabkina_class_routing as v1

_HERE = Path(__file__).resolve()
ROOT = _HERE.parents[1] if _HERE.parent.name == 'build' else Path.cwd()
CANONICAL = ROOT / 'build' / 'RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json'
OUT = ROOT / 'build' / 'RUSSIAN-CURRENT-127-DRABKINA-CLASS-ROUTING-v2.json'
AUDIT = ROOT / 'audits' / 'RUSSIAN-CURRENT-127-DRABKINA-CLASS-ROUTING-v2.txt'


def _route_classes(first, reinf=(), extra=()):
    values = []
    for value in ([first] if first is not None else []) + list(reinf) + list(extra):
        if value not in values:
            values.append(value)
    return values


def _with_route_classes(result: dict, extra=()) -> dict:
    result = dict(result)
    result['route_classes'] = _route_classes(
        result.get('first_studied_class'),
        result.get('reinforcement_classes', []),
        extra,
    )
    return result


def classify(row: dict) -> dict:
    eid = row['exception_id']

    # Direct Drabkina grade-6 practical, section
    # «Чередующиеся гласные в корне слова. Обобщение и систематизация изученного»:
    # task 23 СКАК-/СКОЧ- + скачок/скачу;
    # task 24 ПЛАВ-/ПЛОВ- + пловец/пловчиха;
    # task 25 ТВАР-/ТВОР- + утварь;
    # task 26 ЗАР-/ЗОР- (old edition has obsolete зоревать; current norm replacement is заревать).
    if eid == 'alt_root_skachok_skachu':
        return _with_route_classes(v1.route(
            6, [10], status='verified_class_route',
            basis=['6: Драбкина, обобщение чередующихся корней, задание 23: СКАК-/СКОЧ-, исключения СКАЧОК/СКАЧУ',
                   '10: orthography/EGE systematization'],
        ))
    if eid == 'alt_root_plovets_plovchikha':
        return _with_route_classes(v1.route(
            6, [10], status='verified_class_route',
            basis=['6: Драбкина, обобщение чередующихся корней, задание 24: ПЛОВЕЦ/ПЛОВЧИХА',
                   '10: orthography/EGE systematization'],
        ))
    if eid == 'alt_root_plyvuny':
        return _with_route_classes(v1.route(
            6, [10], status='family_route_verified_item_locator_pending',
            basis=['6: Драбкина, задание 24 confirms ПЛАВ-/ПЛОВ- family; exact ПЛЫВУНЫ item occurrence still pending',
                   '10: orthography/EGE systematization'],
        ))
    if eid == 'alt_root_utvar':
        return _with_route_classes(v1.route(
            6, [10], status='verified_class_route',
            basis=['6: Драбкина, обобщение чередующихся корней, задание 25: ТВАР-/ТВОР-, исключение УТВАРЬ',
                   '10: orthography/EGE systematization'],
        ))
    if eid == 'alt_root_zarevat_current':
        return _with_route_classes(v1.route(
            6, [10], status='verified_class_route_current_norm_override',
            basis=['6: Драбкина, обобщение чередующихся корней, задание 26: ЗАР-/ЗОР- family',
                   '10: orthography/EGE systematization'],
            note='Class route follows Drabkina grade 6. Learner norm is current ЗАРЕВАТЬ; obsolete textbook exception ЗОРЕВАТЬ must remain disabled.',
        ))

    # Direct Drabkina grade-10 project practical confirms these exact suffix cases as
    # part of the grade-10 route, but the earlier first-study grade has not yet been
    # established from the 5-9 Drabkina vertical. Keep first_studied_class null.
    if eid in {'suffix_milostivyy', 'suffix_yurodivyy'}:
        return _with_route_classes(v1.route(
            None, status='route_class_verified_first_study_pending',
            basis=['10: Драбкина, «Правописание суффиксов имён прилагательных»: МИЛОСТИВЫЙ, ЮРОДИВЫЙ'],
            denominator='candidate_include',
            note='Exact earlier first-study class in Drabkina 5-9 vertical remains pending.',
        ), extra=[10])
    if eid in {'verb_zastrevat', 'verb_zatmevat', 'verb_prodlevat'}:
        return _with_route_classes(v1.route(
            None, status='route_class_verified_first_study_pending',
            basis=['10: Драбкина, «Правописание глагольных суффиксов»: ЗАСТРЕВАТЬ, ЗАТМЕВАТЬ, ПРОДЛЕВАТЬ'],
            denominator='candidate_include',
            note='Exact earlier first-study class in Drabkina 5-9 vertical remains pending.',
        ), extra=[10])

    result = v1.classify(row)
    return _with_route_classes(result)


def main() -> None:
    data = json.loads(CANONICAL.read_text(encoding='utf-8'))
    rows = data['items']
    assert len(rows) == 127, f'Expected current canonical 127 items, got {len(rows)}'

    ids = [r['exception_id'] for r in rows]
    assert len(ids) == len(set(ids)), 'Duplicate exception_id in canonical bank'
    assert 'alt_root_zorevat' not in ids, 'Obsolete ЗОРЕВАТЬ must remain disabled'
    assert 'alt_root_zarevat_current' in ids, 'Current ЗАРЕВАТЬ replacement missing'

    mapped = []
    for row in sorted(rows, key=lambda x: x['exception_id']):
        result = classify(row)
        mapped.append({
            'exception_id': row['exception_id'],
            'source_bank': row['source_bank'],
            'topic': v1.topic(row),
            'subskill_ids': row.get('subskill_ids', []),
            'exam_task_numbers': row.get('exam_task_numbers', []),
            **result,
        })

    assert len(mapped) == 127
    statuses = Counter(x['route_status'] for x in mapped)
    first_counts = Counter(x['first_studied_class'] for x in mapped)
    denom = Counter(x['denominator_policy'] for x in mapped)
    route_counts = Counter()
    for row in mapped:
        for grade in row['route_classes']:
            route_counts[grade] += 1

    unassigned_route = [x['exception_id'] for x in mapped if not x['route_classes'] and x['denominator_policy'] != 'exclude_legacy_exam']
    exact_pending = [x['exception_id'] for x in mapped if x['denominator_policy'] == 'pending_source']

    output = {
        'schema_version': '0.2.0',
        'subject': 'russian',
        'purpose': 'current_127_canonical_items_to_drabkina_class_route_inventory',
        'status': 'complete_inventory_partial_class_verification',
        'source_canonical_build_version': data.get('build_version'),
        'routing_policy': {
            'primary_class_source': 'Drabkina/Subbotin 5-11 project corpus',
            'first_studied_class_is_not_route_membership': True,
            'class_mode_denominator_uses_route_classes_after_full_master_map': True,
            'class_is_separate_from_exam_route': True,
            'single_card_is_not_programme_unit': True,
            'grade8_exact_project_toc_pending': True,
            'progress_denominators_allowed_now': False,
        },
        'summary': {
            'total_items': len(mapped),
            'first_class_counts': {('unassigned' if k is None else str(k)): v for k, v in sorted(first_counts.items(), key=lambda kv: (kv[0] is None, kv[0] or 99))},
            'route_class_counts_overlapping': {str(k): v for k, v in sorted(route_counts.items())},
            'route_status_counts': dict(sorted(statuses.items())),
            'denominator_policy_counts': dict(sorted(denom.items())),
            'items_without_any_class_route_excluding_legacy': len(unassigned_route),
            'pending_source_items': len(exact_pending),
            'obsolete_alt_root_zorevat_present': False,
            'current_alt_root_zarevat_present': True,
        },
        'items_without_any_class_route_excluding_legacy': unassigned_route,
        'pending_source_items': exact_pending,
        'items': mapped,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    lines = [
        'RUSSIAN CURRENT 127 -> DRABKINA CLASS ROUTING AUDIT v2',
        '',
        f'TOTAL: {len(mapped)}',
        '',
        'FIRST-STUDIED CLASS COUNTS (NOT class-mode denominators):',
    ]
    for key in [5, 6, 7, 8, 9, None]:
        lines.append(f'- {"UNASSIGNED" if key is None else key}: {first_counts.get(key, 0)}')
    lines += ['', 'ROUTE-CLASS MEMBERSHIP COUNTS (OVERLAPPING; NOT final denominators):']
    for key, value in sorted(route_counts.items()):
        lines.append(f'- {key}: {value}')
    lines += ['', 'ROUTE STATUS:']
    for key, value in sorted(statuses.items()):
        lines.append(f'- {key}: {value}')
    lines += ['', 'DENOMINATOR POLICY:']
    for key, value in sorted(denom.items()):
        lines.append(f'- {key}: {value}')
    lines += [
        '',
        f'ITEMS WITHOUT ANY CLASS ROUTE (excluding legacy): {len(unassigned_route)}',
        f'PENDING-SOURCE ITEMS: {len(exact_pending)}',
        '',
        'NEW DIRECT DRABKINA RESOLUTIONS:',
        '- grade 6: СКАК-/СКОЧ- + СКАЧОК/СКАЧУ;',
        '- grade 6: ПЛАВ-/ПЛОВ- + ПЛОВЕЦ/ПЛОВЧИХА (ПЛЫВУНЫ family routed; exact item occurrence still pending);',
        '- grade 6: ТВАР-/ТВОР- + УТВАРЬ;',
        '- grade 6: ЗАР-/ЗОР- family; current learner form remains ЗАРЕВАТЬ;',
        '- grade 10 route: МИЛОСТИВЫЙ/ЮРОДИВЫЙ; earlier first-study class pending;',
        '- grade 10 route: ЗАСТРЕВАТЬ/ЗАТМЕВАТЬ/ПРОДЛЕВАТЬ; earlier first-study class pending.',
        '',
        'GUARDS:',
        '- `first_studied_class` and `route_classes` are separate.',
        '- A class mode eventually uses verified `route_classes`, not only first-study classes.',
        '- Canonical source count is exactly 127.',
        '- Every current canonical item is classified.',
        '- Obsolete alt_root_zorevat is absent.',
        '- Current alt_root_zarevat_current is present.',
        '- Progress denominators remain DISALLOWED until full Drabkina 5-11 itemization/deduplication + completeness/current-norm passes.',
        '',
        'RESULT: PASS (routing inventory only; NOT a 100% coverage or publication gate)',
    ]
    AUDIT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('PASS:', json.dumps(output['summary'], ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
