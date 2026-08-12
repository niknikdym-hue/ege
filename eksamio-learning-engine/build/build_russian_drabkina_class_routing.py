from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

_HERE = Path(__file__).resolve()
ROOT = _HERE.parents[1] if _HERE.parent.name == 'build' else Path.cwd()
CANONICAL = ROOT / 'build' / 'RUSSIAN-EXCEPTIONS-BANK-CANONICAL.json'
OUT = ROOT / 'build' / 'RUSSIAN-CURRENT-127-DRABKINA-CLASS-ROUTING.json'
AUDIT = ROOT / 'audits' / 'RUSSIAN-CURRENT-127-DRABKINA-CLASS-ROUTING.txt'

TOPIC_BY_SKILL = {
    'orthographic_norms': 'Орфография',
    'punctuation_norms': 'Пунктуация',
    'morphological_norms': 'Морфология',
    'syntactic_norms': 'Синтаксис',
    'lexical_norms_and_semantics': 'Лексические нормы',
    'orthoepic_norms': 'Орфоэпия',
}


def topic(row: dict) -> str:
    for skill in row.get('skill_ids', []):
        if skill in TOPIC_BY_SKILL:
            return TOPIC_BY_SKILL[skill]
    return 'Другое'


def route(first=None, reinf=(), status='verified_class_route', basis=(), prereq=(),
          complexity='single_family', denominator='candidate_include', note=None):
    value = {
        'first_studied_class': first,
        'reinforcement_classes': list(reinf),
        'prerequisite_classes': list(prereq),
        'route_complexity': complexity,
        'route_status': status,
        'drabkina_basis': list(basis),
        'denominator_policy': denominator,
    }
    if note:
        value['note'] = note
    return value


def classify(row: dict) -> dict:
    eid = row['exception_id']
    bank = row['source_bank']
    rule_ref = row.get('rule_ref')

    if bank.startswith('33-'):
        if eid in {'n_nn_glass', 'n_nn_tin', 'n_nn_windy', 'n_nn_wooden'}:
            return route(6, [7, 10], basis=[
                '6: Н/НН в суффиксах отымённых прилагательных',
                '7: повторение/различение Н/НН отымённых прилагательных',
                '10: Н/НН в отымённых прилагательных',
            ])
        return route(7, [10], basis=[
            '7: Н/НН в причастиях и отглагольных прилагательных',
            '10: систематизация Н/НН',
        ])

    if bank.startswith('35-'):
        if eid == 'alt_root_rast_ros_group':
            return route(5, [6, 10], basis=['5: РАСТ-/РАЩ-/РОС-', '6/10: систематизация чередующихся корней'])
        if eid == 'alt_root_polog':
            return route(5, [6, 10], status='family_route_verified_item_locator_pending', basis=['5: ЛАГ-/ЛОЖ-', '6/10: систематизация чередующихся корней'])
        if eid == 'alt_root_sochetat':
            return route(5, [6, 10], status='family_route_verified_item_locator_pending', basis=['5: Е/И в корнях с чередованием', '6/10: систематизация чередующихся корней'])
        if eid == 'alt_root_gar_gor_special':
            return route(6, [10], status='family_route_verified_item_locator_pending', basis=['6: ГОР-/ГАР-', '10: чередующиеся гласные в корнях'])
        if eid in {'alt_root_plovets_plovchikha', 'alt_root_plyvuny', 'alt_root_skachok_skachu', 'alt_root_utvar'}:
            return route(None, status='requires_exact_drabkina_item_locator', basis=['Exact Drabkina family/item locator still required'], denominator='pending_source')
        if eid.startswith('pre_pri_'):
            return route(6, [10], basis=['6: ПРЕ-/ПРИ-', '10: ПРЕ-/ПРИ- systematization'])
        if eid.startswith('tsy_'):
            return route(5, [10], status='family_route_verified_item_locator_pending', basis=['5: И/Ы после Ц', '10: orthography systematization'])
        if eid.startswith('yi_'):
            return route(6, [10], status='family_route_verified_item_locator_pending', basis=['6: И/Ы после приставок', '10: orthography systematization'])
        raise AssertionError(f'Unclassified bank-35 item: {eid}')

    if bank.startswith('37-'):
        if rule_ref == 'verb_conjugation_endings':
            return route(5, [7, 10], status='family_route_verified_item_locator_pending', basis=['5: личные окончания глаголов', '7: verb/conjugation review', '10: verb systematization'])
        if rule_ref == 'participle_suffixes':
            return route(7, [10], status='family_route_verified_item_locator_pending', basis=['7: система причастий / суффиксы причастий', '10: причастия systematization'])
        if rule_ref == 'suffix_spelling_by_part_of_speech':
            return route(None, status='requires_exact_drabkina_item_locator', basis=['Exact school-stage locator for these suffix/-ВА exceptions not yet established'], denominator='pending_source')
        raise AssertionError(f'Unclassified bank-37 item: {eid}')

    if bank.startswith('39-'):
        if rule_ref == 'solid_separate_conjunctions':
            return route(7, [10], basis=['7: союзы и омонимичные сочетания', '10: systematization'])
        if rule_ref == 'solid_separate_prepositions':
            return route(7, [10], basis=['7: производные предлоги', '10: systematization'])
        if rule_ref == 'solid_separate_adverbs':
            return route(7, [10], basis=['7: слитное/раздельное написание наречий', '10: systematization'])
        if eid == 'koe_with_preposition':
            return route(6, [7, 10], basis=['6: неопределённые местоимения', '7/10: later orthographic systematization'])
        if eid == 'taki_position':
            return route(7, [10], basis=['7: частица', '10: orthography systematization'])
        if rule_ref == 'ni_pronoun_adverb_spelling':
            return route(7, [10], status='family_route_verified_item_locator_pending', basis=['7: НЕ/НИ и различение НЕ/НИ', '10: systematization'])
        raise AssertionError(f'Unclassified bank-39 item: {eid}')

    if bank.startswith('42-'):
        fixed = {
            'address_vs_subject': route(5, [8, 11], status='composite_verified_prerequisites', basis=['5: обращение', '8/11: syntax-punctuation reinforcement'], prereq=[5], complexity='composite'),
            'and_compound_common_element': route(9, [11], status='family_route_verified_item_locator_pending', basis=['9: сложносочинённое предложение', '11: ССП systematization'], prereq=[5], complexity='composite', note='Common-element exception belongs to the advanced compound-sentence layer.'),
            'and_homogeneous_vs_compound': route(9, [11], status='composite_verified_prerequisites', basis=['5: однородные члены / simple-vs-complex basis', '9: сложносочинённое предложение', '11: systematization'], prereq=[5], complexity='composite'),
            'participle_before_after_noun': route(7, [8, 11], status='family_route_verified_item_locator_pending', basis=['7: причастный оборот', '8/11: detached-attribute punctuation reinforcement']),
            'gerund_regular_vs_fixed': route(7, [8, 11], status='family_route_verified_item_locator_pending', basis=['7: деепричастие', '8/11: obособление reinforcement']),
            'introductory_vidimo_vs_slovno': route(8, [11], status='provisional_grade8_exact_toc_pending', basis=['8: introductory words scope corroborated; exact project TOC pending', '11: вводные слова']),
            'homogeneous_subordinate_and': route(9, [11], basis=['9: СПП / однородное подчинение', '11: systematization']),
            'junction_conjunction_if_then': route(9, [11], status='family_route_verified_item_locator_pending', basis=['9: СПП / nested subordination', '11: systematization']),
            'dash_subject_predicate_vs_generalizing': route(5, [8, 11], status='composite_verified_prerequisites', basis=['5: тире между подлежащим и сказуемым; обобщающие слова', '11: systematization'], prereq=[5], complexity='composite'),
            'colon_explanation_vs_enumeration_vs_quote': route(9, [11], status='composite_verified_prerequisites', basis=['5: обобщающие слова / прямая речь', '9: БСП', '11: colon/dash systematization'], prereq=[5], complexity='composite'),
            'comma_rule_analysis_multi_rule_sentence': route(9, [11], status='composite_verified_prerequisites', basis=['5: однородные члены', '9: СПП', '11: systematization'], prereq=[5], complexity='composite'),
        }
        assert eid in fixed, f'Unclassified bank-42 item: {eid}'
        return fixed[eid]

    if bank.startswith('48-'):
        if eid == 'syntax_gerund_same_actor_test':
            return route(7, [10], status='family_route_verified_item_locator_pending', basis=['7: деепричастие', '10: normative gerund construction systematization'])
        if eid == 'task25_historical_synonym_not_current_phraseology':
            return route(None, status='legacy_exam_only_excluded', basis=['Historical EGE task-format record; not a school difficult-case denominator item'], complexity='legacy_exam_format', denominator='exclude_legacy_exam')
        return route(None, status='requires_exact_drabkina_item_locator', basis=['Exact Drabkina class-stage locator required'], denominator='pending_source')

    if bank.startswith('84-'):
        return route(8, [11], status='provisional_grade8_exact_toc_pending', basis=['8: introductory words scope corroborated; exact project practicum TOC pending', '11: вводные слова systematization'])

    if bank.startswith('85-'):
        if eid in {'ne_kto_inoi_vs_nikto_inoi', 'ne_chto_inoe_vs_nichto_inoe'}:
            return route(7, [10], status='family_route_verified_item_locator_pending', basis=['7: НЕ/НИ distinction', '10: systematization'])
        if eid in {'nesmotrya_na_vs_ne_smotrya', 'nevziraya_na_vs_ne_vziraya'}:
            return route(7, [10], status='composite_verified_prerequisites', basis=['7: производные предлоги; НЕ с деепричастиями', '10: systematization'], prereq=[7], complexity='composite')
        if eid == 'nedo_prefix_vs_ne_completed_action':
            return route(7, [10], status='family_route_verified_item_locator_pending', basis=['7: НЕ с разными частями речи / distinction', '10: systematization'], prereq=[5], complexity='composite')
        if eid == 'ne_words_without_independent_form':
            return route(7, [10], status='composite_verified_prerequisites', basis=['5: НЕ с глаголами', '6: НЕ с существительными/прилагательными', '7: broader НЕ system'], prereq=[5, 6], complexity='composite')
        if eid == 'far_not_by_no_means_not_negative_pronoun':
            return route(7, [10], status='composite_verified_prerequisites', basis=['6: НЕ with adjectives', '7: НЕ with adverbs / НИ intensifiers', '10: systematization'], prereq=[6], complexity='composite')
        raise AssertionError(f'Unclassified bank-85 item: {eid}')

    if bank.startswith('86-'):
        return route(7, [10], status='family_route_verified_item_locator_pending', basis=['7: производные предлоги / наречия and homonymous combinations', '10: systematization'])

    if bank.startswith('87-'):
        return route(None, status='requires_exact_drabkina_item_locator', basis=['Difficult noun-form school stage must be located explicitly'], denominator='pending_source')

    if bank.startswith('88-'):
        return route(None, status='requires_exact_drabkina_item_locator', basis=['Syntax/government item requires explicit Drabkina school-stage locator'], denominator='pending_source')

    if bank.startswith('89-'):
        return route(None, status='requires_exact_drabkina_item_locator', basis=['Paronym pair requires explicit Drabkina vertical locator'], denominator='pending_source')

    if bank.startswith('132-') and eid == 'alt_root_zarevat_current':
        return route(None, status='requires_exact_drabkina_item_locator', basis=['Current norm replacement; exact ЗАР-/ЗОР- class position must be located in Drabkina vertical'], denominator='pending_source', note='Current learner form ЗАРЕВАТЬ; obsolete ЗОРЕВАТЬ remains disabled.')

    raise AssertionError(f'Unknown source bank/item: {bank} :: {eid}')


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
        r = classify(row)
        mapped.append({
            'exception_id': row['exception_id'],
            'source_bank': row['source_bank'],
            'topic': topic(row),
            'subskill_ids': row.get('subskill_ids', []),
            'exam_task_numbers': row.get('exam_task_numbers', []),
            **r,
        })

    assert len(mapped) == 127
    statuses = Counter(x['route_status'] for x in mapped)
    first_counts = Counter(x['first_studied_class'] for x in mapped)
    denom = Counter(x['denominator_policy'] for x in mapped)

    output = {
        'schema_version': '0.1.0',
        'subject': 'russian',
        'purpose': 'current_127_canonical_items_to_drabkina_class_route_inventory',
        'status': 'complete_inventory_partial_class_verification',
        'source_canonical_build_version': data.get('build_version'),
        'routing_policy': {
            'primary_class_source': 'Drabkina/Subbotin 5-11 project corpus',
            'class_is_separate_from_exam_route': True,
            'single_card_is_not_programme_unit': True,
            'exact_item_locator_required_for_final_verified_status': True,
            'grade8_exact_project_toc_pending': True,
            'progress_denominators_allowed_now': False,
        },
        'summary': {
            'total_items': len(mapped),
            'first_class_counts': {('unassigned' if k is None else str(k)): v for k, v in sorted(first_counts.items(), key=lambda kv: (kv[0] is None, kv[0] or 99))},
            'route_status_counts': dict(sorted(statuses.items())),
            'denominator_policy_counts': dict(sorted(denom.items())),
            'obsolete_alt_root_zorevat_present': False,
            'current_alt_root_zarevat_present': True,
        },
        'items': mapped,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    lines = [
        'RUSSIAN CURRENT 127 -> DRABKINA CLASS ROUTING AUDIT',
        '',
        f'TOTAL: {len(mapped)}',
        'CLASS COUNTS (first-study route; not final programme denominator):',
    ]
    for key in [5, 6, 7, 8, 9, None]:
        lines.append(f'- {"UNASSIGNED" if key is None else key}: {first_counts.get(key, 0)}')
    lines += ['', 'ROUTE STATUS:']
    for key, value in sorted(statuses.items()):
        lines.append(f'- {key}: {value}')
    lines += ['', 'DENOMINATOR POLICY:']
    for key, value in sorted(denom.items()):
        lines.append(f'- {key}: {value}')
    lines += [
        '',
        'GUARDS:',
        '- Canonical source count is exactly 127.',
        '- Every current canonical item is classified by this audit.',
        '- Obsolete alt_root_zorevat is absent.',
        '- Current alt_root_zarevat_current is present.',
        '- 8-class routes remain provisional until exact project practicum TOC is verified.',
        '- Items without exact Drabkina school-stage evidence remain explicitly unassigned.',
        '- Historical task-25 synonym record is excluded from the future school-programme denominator.',
        '- Progress denominators remain DISALLOWED until the full Drabkina 5-11 master map is itemized/deduplicated and completeness/current-norm passes are complete.',
        '',
        'RESULT: PASS (inventory/routing audit only; NOT a publication or 100% coverage gate)',
    ]
    AUDIT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'PASS: mapped {len(mapped)} canonical items; class counts={dict(first_counts)}; statuses={dict(statuses)}')


if __name__ == '__main__':
    main()
