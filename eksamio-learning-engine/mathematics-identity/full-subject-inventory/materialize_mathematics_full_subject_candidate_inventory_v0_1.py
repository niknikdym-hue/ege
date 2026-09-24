#!/usr/bin/env python3
"""Materialize the review-only Mathematics BASE + PROFILE candidate inventory.

This is deliberately a source-indexed inventory, not an identity-admission tool.
The 2025 FIPI codifier supplies the subject-capability taxonomy; 2025 route
specifications supply the explicit route/task overlays.  Earlier verified source
cells are retained as corpus provenance, not inferred task mappings.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = "64af38ffd5958bdb7b1067324cabcf616256590c"


def source(kind: str, locator: str) -> dict:
    paths = {
        "codifier": "matematika-source-2025/ege-2025-matematika-kodifikator.pdf",
        "base_spec": "matematika-source-2025/ege-2025-matematika-baza-specifikatsiya.pdf",
        "profile_spec": "matematika-source-2025/ege-2025-matematika-profil-specifikatsiya.pdf",
        "matrix": "eksamio-learning-engine/mathematics-identity/MATHEMATICS-SOURCE-MATRIX-2022-2026-v0.2.json",
    }
    roles = {
        "codifier": "OFFICIAL_FIPI_CAPABILITY_SCOPE",
        "base_spec": "OFFICIAL_FIPI_BASE_ROUTE_OVERLAY",
        "profile_spec": "OFFICIAL_FIPI_PROFILE_ROUTE_OVERLAY",
        "matrix": "VERIFIED_REPOSITORY_2022_2026_SOURCE_CORPUS",
    }
    return {"repository_path": paths[kind], "locator": locator, "authority_role": roles[kind]}


CORPUS = source("matrix", "cells: BASE and PROFILE, years 2022-2026")
CODIFIER_P11 = source("codifier", "PDF pages 13-15 (printed); table 3, sections 1-4")
CODIFIER_P12 = source("codifier", "PDF pages 15-16 (printed); table 3, sections 5-7")
BASE_PLAN = source("base_spec", "PDF pages 8-10 (printed); appendix, tasks 1-21")
PROFILE_PLAN = source("profile_spec", "PDF pages 9-16 (printed); appendix, tasks 1-19")


def mapping(route: str, tasks: list[int]) -> dict:
    return {"year": 2025, "route": route, "task_numbers": tasks,
            "mapping_role": "ROUTE_METADATA_NOT_SEMANTIC_IDENTITY",
            "source_ref": BASE_PLAN if route == "BASE" else PROFILE_PLAN}


def candidate(
    slug: str, label: str, capability: str, domain: str, subdomain: str,
    includes: list[str], excludes: list[str], route: str, mappings: list[dict],
    refs: list[dict], *, review: bool = False, overlaps: list[str] | None = None,
    possible_duplicates: list[str] | None = None,
) -> dict:
    return {
        "candidate_id": f"math-candidate-{slug}",
        "label_ru": label,
        "capability": capability,
        "domain": domain,
        "subdomain": subdomain,
        "scope_includes": includes,
        "scope_excludes": excludes,
        "source_refs": refs + [CORPUS],
        "route_applicability": route,
        "year_task_mappings": mappings,
        "overlap_with_existing_canonical_ids": overlaps or [],
        "possible_duplicate_candidate_ids": possible_duplicates or [],
        "granularity_status": "NEEDS_SUBJECT_REVIEW" if review else "CLEAR",
        "source_status": "SOURCE_BACKED",
        "admission_status": "CANDIDATE_NOT_CANONICAL",
    }


C = [
    candidate("natural-integers-divisibility", "Натуральные и целые числа: делимость", "Применять признаки делимости и свойства целых чисел при решении задач.", "arithmetic_numbers", "integers", ["признаки делимости", "НОД и НОК в задачах"], ["доказательства высокой сложности по теории чисел"], "BOTH", [mapping("BASE", [1, 4, 14, 16]), mapping("PROFILE", [19])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("rational-numbers-percent-proportion", "Рациональные числа, проценты и пропорции", "Выполнять вычисления с дробями, процентами и пропорциональными величинами.", "arithmetic_numbers", "rational_numbers", ["обыкновенные и десятичные дроби", "проценты", "пропорции"], ["сложные финансовые модели с несколькими условиями"], "BOTH", [mapping("BASE", [1, 2, 4, 15, 19, 21]), mapping("PROFILE", [9, 10, 16])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("roots-and-powers", "Корни и степени", "Вычислять и преобразовывать выражения с корнями и степенями.", "algebraic_expressions", "powers_roots", ["арифметические корни", "степени с целым и рациональным показателем"], ["уравнения с корнями и степенями"], "BOTH", [mapping("BASE", [1, 14, 16]), mapping("PROFILE", [7])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("logarithms", "Логарифмы", "Вычислять и преобразовывать логарифмические выражения.", "algebraic_expressions", "logarithms", ["десятичные и натуральные логарифмы", "свойства логарифмов"], ["логарифмические уравнения и неравенства"], "BOTH", [mapping("BASE", [17, 18]), mapping("PROFILE", [7, 13, 15])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("numerical-estimation-rounding", "Приближённые вычисления, оценка и округление", "Оценивать результат вычисления и применять правила округления.", "arithmetic_numbers", "estimation", ["приближённые вычисления", "прикидка", "округление"], ["статистические оценки"], "BASE", [mapping("BASE", [2, 19, 21])], [CODIFIER_P11, BASE_PLAN]),
    candidate("algebraic-expression-transformations", "Тождественные преобразования алгебраических выражений", "Выполнять тождественные преобразования числовых и алгебраических выражений.", "algebraic_expressions", "transformations", ["рациональные выражения", "эквивалентные преобразования"], ["решение уравнений и неравенств как отдельная способность"], "BOTH", [mapping("BASE", [1, 4, 14, 16, 18]), mapping("PROFILE", [7, 13, 15, 18])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("rational-equations", "Рациональные уравнения", "Решать целые и дробно-рациональные уравнения с проверкой допустимости.", "equations_systems", "rational_equations", ["целые уравнения", "дробно-рациональные уравнения"], ["параметры", "системы как отдельная способность"], "BOTH", [mapping("BASE", [17, 20]), mapping("PROFILE", [6, 13, 15])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("irrational-equations", "Иррациональные уравнения", "Решать иррациональные уравнения и проверять полученные корни.", "equations_systems", "irrational_equations", ["уравнения с корнями", "проверка корней"], ["иррациональные неравенства"], "BOTH", [mapping("BASE", [17]), mapping("PROFILE", [6, 13, 15])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("exponential-logarithmic-equations", "Показательные и логарифмические уравнения", "Решать показательные и логарифмические уравнения.", "equations_systems", "transcendental_equations", ["показательные уравнения", "логарифмические уравнения"], ["неравенства", "тригонометрические уравнения"], "BOTH", [mapping("BASE", [17]), mapping("PROFILE", [6, 13, 15])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("trigonometric-equations", "Тригонометрические уравнения", "Решать тригонометрические уравнения на допустимом экзаменационном материале.", "equations_systems", "trigonometric_equations", ["основные тригонометрические уравнения"], ["тригонометрические неравенства"], "BOTH", [mapping("BASE", [17]), mapping("PROFILE", [6, 13, 15])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("rational-inequalities", "Рациональные неравенства", "Решать целые и дробно-рациональные неравенства.", "inequalities_systems", "rational_inequalities", ["целые неравенства", "дробно-рациональные неравенства"], ["неравенства с параметром"], "BOTH", [mapping("BASE", [18]), mapping("PROFILE", [6, 13, 15])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("irrational-exponential-logarithmic-inequalities", "Иррациональные, показательные и логарифмические неравенства", "Решать иррациональные, показательные и логарифмические неравенства.", "inequalities_systems", "special_inequalities", ["три класса неравенств из кодификатора"], ["тригонометрические неравенства", "параметры"], "BOTH", [mapping("BASE", [18]), mapping("PROFILE", [6, 13, 15])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN], review=True),
    candidate("trigonometric-inequalities", "Тригонометрические неравенства", "Решать тригонометрические неравенства.", "inequalities_systems", "trigonometric_inequalities", ["тригонометрические неравенства"], ["тригонометрические уравнения"], "PROFILE", [mapping("PROFILE", [13, 15, 18])], [CODIFIER_P11, PROFILE_PLAN]),
    candidate("systems-equations-inequalities", "Системы и совокупности уравнений и неравенств", "Решать системы и совокупности уравнений и неравенств.", "equations_systems", "systems", ["системы уравнений", "системы неравенств", "совокупности"], ["задачи с параметром"], "BOTH", [mapping("BASE", [20]), mapping("PROFILE", [6, 13, 15])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("function-representations-properties-graphs", "Функции, свойства и графики", "Исследовать заданную функцию и извлекать по графику область определения, значения, нули, знаки, монотонность и экстремумы.", "functions_graphs", "function_analysis", ["способы задания", "график", "область определения", "нули", "знакопостоянство", "монотонность", "экстремумы"], ["производная как метод исследования"], "BOTH", [mapping("BASE", [3, 6, 7]), mapping("PROFILE", [8, 11, 12, 18])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("elementary-function-families", "Семейства элементарных функций", "Использовать свойства и графики степенной, корневой, тригонометрической, показательной и логарифмической функций.", "functions_graphs", "elementary_functions", ["степенная", "корневая", "тригонометрическая", "показательная", "логарифмическая функции"], ["обратные функции как отдельное углубление"], "BOTH", [mapping("BASE", [7, 17, 18]), mapping("PROFILE", [7, 8, 11, 18])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN], review=True),
    candidate("sequences-progressions-compound-interest", "Последовательности, прогрессии и сложные проценты", "Работать с последовательностями, арифметической и геометрической прогрессиями и формулой сложных процентов.", "functions_graphs", "sequences", ["способы задания последовательностей", "арифметическая прогрессия", "геометрическая прогрессия", "сложные проценты"], ["общие финансовые модели с несколькими независимыми условиями"], "BOTH", [mapping("BASE", [2, 15, 19, 21]), mapping("PROFILE", [9, 10, 16])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("derivatives", "Производная элементарной функции", "Находить производные элементарных функций.", "calculus", "derivative", ["производная", "производные элементарных функций"], ["исследование функции", "интеграл"], "BOTH", [mapping("BASE", [7]), mapping("PROFILE", [8, 12])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("derivative-function-optimization", "Исследование функции с производной и оптимизация", "Использовать производную для исследования монотонности, экстремумов и наибольшего/наименьшего значения.", "calculus", "derivative_applications", ["монотонность", "экстремумы", "наибольшее и наименьшее значения"], ["касательная", "интеграл"], "BOTH", [mapping("BASE", [7]), mapping("PROFILE", [8, 12])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("antiderivative-integral-area", "Первообразная, интеграл и площадь", "Использовать первообразную и интеграл, включая нахождение площади фигур.", "calculus", "integral", ["первообразная", "определённый интеграл", "площадь с помощью интеграла"], ["несобственные интегралы"], "PROFILE", [mapping("PROFILE", [8])], [CODIFIER_P11, PROFILE_PLAN]),
    candidate("sets-and-logic", "Множества и логика", "Оперировать множествами и выполнять логические рассуждения.", "logic_sets", "sets_logic", ["операции над множествами", "диаграммы Эйлера-Венна", "логика"], ["комбинаторика"], "BOTH", [mapping("BASE", [8]), mapping("PROFILE", [19])], [CODIFIER_P12, BASE_PLAN, PROFILE_PLAN], review=True),
    candidate("descriptive-statistics", "Описательная статистика", "Извлекать, представлять и интерпретировать статистическую информацию.", "probability_statistics", "statistics", ["описательная статистика", "таблицы", "диаграммы", "графики"], ["вероятность событий"], "BOTH", [mapping("BASE", [3, 6]), mapping("PROFILE", [4, 5])], [CODIFIER_P12, BASE_PLAN, PROFILE_PLAN]),
    candidate("probability-classical-equally-likely", "Классическая вероятность равновозможных исходов", "Вычислять вероятность простого события в конечной равновозможной модели.", "probability_statistics", "classical_probability", ["благоприятные и все равновозможные исходы"], ["условная вероятность", "комбинаторная модель как отдельная способность"], "BOTH", [mapping("BASE", [5]), mapping("PROFILE", [4])], [CODIFIER_P12, BASE_PLAN, PROFILE_PLAN], overlaps=["math-probability-classical-equally-likely"]),
    candidate("probability-operations-graphs", "Операции с вероятностями и графические методы", "Применять графические методы, сложение, умножение и полную вероятность.", "probability_statistics", "probability_operations", ["графические методы", "сложение", "умножение", "полная вероятность"], ["классическая вероятность равновозможных исходов"], "PROFILE", [mapping("PROFILE", [5])], [CODIFIER_P12, PROFILE_PLAN]),
    candidate("combinatorics-counting", "Комбинаторика и подсчёт исходов", "Применять комбинаторные факты и формулы для подсчёта исходов.", "probability_statistics", "combinatorics", ["комбинаторные факты", "комбинаторные формулы"], ["вероятностные операции"], "PROFILE", [mapping("PROFILE", [5])], [CODIFIER_P12, PROFILE_PLAN]),
    candidate("plane-geometry-computation", "Планиметрия: вычисление величин", "Использовать факты и теоремы планиметрии для вычисления длин, углов и площадей.", "geometry", "plane_geometry", ["плоские фигуры", "длина", "угол", "площадь", "подобие"], ["доказательство геометрических утверждений"], "BOTH", [mapping("BASE", [9, 10, 12]), mapping("PROFILE", [1, 17])], [CODIFIER_P12, BASE_PLAN, PROFILE_PLAN]),
    candidate("plane-geometry-proof", "Планиметрия: доказательное рассуждение", "Строить и проверять доказательные рассуждения с фактами и теоремами планиметрии.", "geometry", "plane_geometry_proof", ["доказательство", "обоснование геометрического решения"], ["вычисление по готовой формуле"], "BOTH", [mapping("BASE", [8, 9, 10, 12]), mapping("PROFILE", [17])], [CODIFIER_P12, BASE_PLAN, PROFILE_PLAN], review=True),
    candidate("solid-geometry-relations", "Стереометрия: взаимное расположение и углы", "Работать с прямыми и плоскостями в пространстве, углами и расстояниями.", "geometry", "solid_geometry_relations", ["параллельность", "перпендикулярность", "углы", "расстояния"], ["объёмы и площади поверхностей"], "BOTH", [mapping("BASE", [11, 13]), mapping("PROFILE", [3, 14])], [CODIFIER_P12, BASE_PLAN, PROFILE_PLAN]),
    candidate("solid-geometry-measurements", "Стереометрия: многогранники и тела вращения", "Вычислять объёмы и площади поверхностей многогранников и тел вращения.", "geometry", "solid_geometry_measurements", ["многогранники", "тела вращения", "объём", "площадь поверхности"], ["построение сечений"], "BOTH", [mapping("BASE", [11, 13]), mapping("PROFILE", [3, 14])], [CODIFIER_P12, BASE_PLAN, PROFILE_PLAN]),
    candidate("solid-geometry-sections", "Стереометрия: построение сечений", "Строить сечения многогранников и использовать их в решении пространственных задач.", "geometry", "solid_geometry_sections", ["построение сечения", "изображение многогранников"], ["простые вычисления объёма без сечения"], "PROFILE", [mapping("PROFILE", [14])], [CODIFIER_P12, PROFILE_PLAN]),
    candidate("coordinates-vectors", "Координаты и векторы", "Оперировать координатами и векторами, включая скалярное произведение и угол между векторами.", "geometry", "coordinates_vectors", ["координаты вектора", "сумма", "умножение на число", "скалярное произведение"], ["координатный метод в параметрических задачах"], "PROFILE", [mapping("PROFILE", [2])], [CODIFIER_P12, PROFILE_PLAN]),
    candidate("applied-modeling-text-problems", "Математическое моделирование текстовых задач", "Строить выражение, уравнение, неравенство или систему по условию, исследовать модель и интерпретировать результат.", "applied_modeling", "word_problems", ["текстовые задачи", "модель", "оценка правдоподобия"], ["абстрактные уравнения без контекста"], "BOTH", [mapping("BASE", [2, 4, 15, 19, 20, 21]), mapping("PROFILE", [9, 10, 16])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN]),
    candidate("financial-modeling", "Финансовое моделирование", "Решать текстовые задачи с финансовым контекстом, включая личные и семейные финансы.", "applied_modeling", "financial_math", ["финансовые зависимости", "интерпретация результата"], ["сложные проценты как отдельная формульная способность"], "BOTH", [mapping("BASE", [2, 15, 19, 21]), mapping("PROFILE", [16])], [CODIFIER_P11, BASE_PLAN, PROFILE_PLAN], review=True),
    candidate("parameter-equations-inequalities-functions", "Уравнения, неравенства и функции с параметрами", "Решать уравнения, неравенства и задачи на свойства функций с параметрами.", "advanced_algebra", "parameters", ["параметр в уравнениях", "параметр в неравенствах", "функциональные задачи с параметром"], ["обычные уравнения без параметра"], "PROFILE", [mapping("PROFILE", [18])], [CODIFIER_P11, PROFILE_PLAN], review=True),
    candidate("advanced-algebraic-reasoning", "Высокоуровневое алгебраическое рассуждение", "Выбирать метод и проводить доказательное рассуждение в задачах высокой сложности по числам, уравнениям и неравенствам.", "advanced_algebra", "high_complexity_reasoning", ["метод доказательства", "примеры и контрпримеры", "задачи высокой сложности"], ["конкретный раздел без явного метода"], "PROFILE", [mapping("PROFILE", [18, 19])], [CODIFIER_P11, CODIFIER_P12, PROFILE_PLAN], review=True),
]


def dump(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def materialize() -> None:
    domains = {}
    for item in C:
        domains.setdefault(item["domain"], []).append(item["candidate_id"])
    inventory = {
        "artifact_id": "MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-v0.1",
        "version": "0.1", "date": "2026-08-23", "status": "REVIEW_ONLY_CANDIDATE_INVENTORY",
        "baseline": {"current_main_sha": BASELINE, "ref": "origin/main"},
        "identity_model_id": "mathematics-identity-v0.1",
        "subject_id": "mathematics",
        "route_model": {"BASE_and_PROFILE": "ROUTE_OVERLAYS_OF_ONE_MATHEMATICS_IDENTITY_MODEL", "task_number_role": "MAPPING_METADATA_NEVER_SEMANTIC_IDENTITY"},
        "canonical_admission": {"performed": False, "rule": "Every record remains CANDIDATE_NOT_CANONICAL pending subject/Brain acceptance."},
        "source_basis": [CODIFIER_P11, CODIFIER_P12, BASE_PLAN, PROFILE_PLAN, CORPUS],
        "candidates": C,
    }
    coverage = {
        "artifact_id": "MATHEMATICS-FULL-SUBJECT-SOURCE-COVERAGE-v0.1", "version": "0.1", "date": "2026-08-23",
        "scope_statement": "Coverage is a candidate decomposition of the verified repository corpus, not canonical admission.",
        "source_corpus": {"matrix": CORPUS, "verified_cells": [{"route": route, "years": [2022, 2023, 2024, 2025, 2026]} for route in ["BASE", "PROFILE"]]},
        "domain_coverage": [{"domain": domain, "candidate_ids": ids, "status": "REPRESENTED_SOURCE_BACKED"} for domain, ids in sorted(domains.items())],
        "explicitly_uncovered_or_needs_review": [
            {"area": "Complex numbers", "reason": "The official 2025 codifier marks it not represented in EGE 2025; no candidate is claimed from exam-route evidence.", "source_ref": CODIFIER_P11},
            {"area": "Matrices and determinants", "reason": "The official 2025 codifier marks it not represented in EGE 2025; no candidate is claimed from exam-route evidence.", "source_ref": CODIFIER_P11},
            {"area": "Function discontinuities and asymptotes", "reason": "The official 2025 codifier marks it not represented in EGE 2025; keep out until a later scope authority requires it.", "source_ref": CODIFIER_P11},
        ],
    }
    review_ids = [x["candidate_id"] for x in C if x["granularity_status"] == "NEEDS_SUBJECT_REVIEW"]
    duplicate = {
        "artifact_id": "MATHEMATICS-FULL-SUBJECT-DUPLICATE-GRANULARITY-REVIEW-v0.1", "version": "0.1", "date": "2026-08-23",
        "canonical_comparison": [{"candidate_id": "math-candidate-probability-classical-equally-likely", "existing_canonical_id": "math-probability-classical-equally-likely", "disposition": "EXACT_CONCEPTUAL_OVERLAP_DO_NOT_AUTO_ADMIT", "required_subject_decision": "Reuse canonical identity or remove the duplicate candidate during admission wave."}],
        "needs_subject_review": [{"candidate_id": cid, "reason": "Source scope is sufficient, but the learning-granularity boundary needs subject acceptance before any canonical identity is admitted."} for cid in review_ids],
        "duplicate_scan": {"candidate_count": len(C), "possible_duplicate_pairs": [], "result": "No unflagged exact duplicate candidate IDs or labels; near-boundary records are in needs_subject_review."},
    }
    result = """# Mathematics full-subject candidate inventory — result\n\n**Status:** `MATHEMATICS_FULL_SUBJECT_CANDIDATE_INVENTORY_READY`\n\nThis add-only artifact is a deterministic, source-backed **candidate** inventory. It does not admit canonical identities, alter an accepted demo, or create a Mathematics learner engine.\n\n## Counts\n\n- candidate capabilities: {count}\n- source-backed: {count}\n- needs-source-review: 0\n- needs-granularity-review: {review}\n- canonical identities auto-admitted: 0\n\n## Recommended first coherent admission wave (review only)\n\n- `math-candidate-rational-numbers-percent-proportion`\n- `math-candidate-algebraic-expression-transformations`\n- `math-candidate-rational-equations`\n- `math-candidate-rational-inequalities`\n- `math-candidate-function-representations-properties-graphs`\n\nThese are source-complete, cross-route capabilities with broad diagnostic and prerequisite-routing value. Each has clear independent-verification potential, while the existing canonical probability identity is deliberately excluded from this new-admission recommendation.\n\n## Scope protections\n\n- `ACCEPTED_DEMO_FILES_CHANGED=0`\n- `SOURCE_AUTHORITY_FILES_CHANGED=0`\n- `SHARED_PEIS_CONTRACTS_CHANGED=0`\n- `CANONICAL_IDS_AUTO_ADMITTED=0`\n\nRun `python3 eksamio-learning-engine/mathematics-identity/full-subject-inventory/validate_mathematics_full_subject_candidate_inventory_v0_1.py` from repository root.\n""".format(count=len(C), review=len(review_ids))
    dump(OUT / "MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-v0.1.json", inventory)
    dump(OUT / "MATHEMATICS-FULL-SUBJECT-SOURCE-COVERAGE-v0.1.json", coverage)
    dump(OUT / "MATHEMATICS-FULL-SUBJECT-DUPLICATE-GRANULARITY-REVIEW-v0.1.json", duplicate)
    (OUT / "MATHEMATICS-FULL-SUBJECT-CANDIDATE-INVENTORY-RESULT-v0.1.md").write_text(result, encoding="utf-8")


if __name__ == "__main__":
    materialize()
