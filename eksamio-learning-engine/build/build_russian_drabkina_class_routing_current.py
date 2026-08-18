from __future__ import annotations

import build_russian_drabkina_class_routing_v2 as base


_original_classify = base.classify


def classify(row: dict) -> dict:
    eid = row['exception_id']

    # Direct Drabkina grade-10 final EGE-format test, task 8:
    # sentence «В пьесе „Грозе“ Островского...» is explicitly matched to
    # «нарушение в построении предложения с несогласованным приложением».
    # This proves grade-10 route membership for the current title/apposition trap.
    # Earlier first-study stage is not inferred from this later exam-systematization route.
    if eid == 'syntax_apposition_title_declension':
        return base._with_route_classes(base.v1.route(
            None,
            status='route_class_verified_first_study_pending',
            basis=[
                '10: Драбкина, итоговый тест №2, задание 8: «В пьесе „Грозе“ Островского...» диагностируется как нарушение в построении предложения с несогласованным приложением'
            ],
            denominator='candidate_include',
            note='Grade-10 route membership is direct. Exact earlier first-study class remains pending.',
        ), extra=[10])

    return _original_classify(row)


# Keep one generated current artifact path and all v2 guards/summaries.
base.classify = classify


if __name__ == '__main__':
    base.main()
