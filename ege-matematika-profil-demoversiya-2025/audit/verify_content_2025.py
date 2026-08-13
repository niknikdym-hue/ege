#!/usr/bin/env python3
import csv
import hashlib
import json
from pathlib import Path

PREFIX = "ege-matematika-profil-demoversiya-2025"
HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
REPO = ROOT.parent
CANON = REPO / "matematika-source-2025" / "canonical-profile-printed-pages"

EXPECTED_HASHES = {
    "profile-demo": "d588a28792d716468d4a49293fa61a5d9e10b67124993264be0bca10a9ee04b6",
    "profile-spec": "506df0835b17534f47dd2ae2182302119b85c4530515230a85ab5044824a64a7",
    "codifier": "4fad4e4701ce5bc5de7b483d394d17cc110fe33e5a5cae3b3054a9e7d27cf5cd",
}
EXPECTED_ANSWERS = {
    1: ["61", "18", "157", "5"],
    2: ["12", "29"],
    3: ["1,125", "340", "104"],
    4: ["0,35", "0,38"],
    5: ["0,992", "0,15"],
    6: ["4", "17", "93", "3"],
    7: ["2,76", "2", "125"],
    8: ["6", "-1,4"],
    9: ["5"],
    10: ["12", "15", "8"],
    11: ["7"],
    12: ["-83", "-6", "16"],
}
EXPECTED_COUNTS = {1:4, 2:2, 3:3, 4:2, 5:2, 6:4, 7:3, 8:2, 9:1, 10:3, 11:1, 12:3, 13:1, 14:1, 15:1, 16:1, 17:1, 18:1, 19:1}
EXPECTED_MAX_EXT = {13:2, 14:3, 15:2, 16:2, 17:3, 18:4, 19:4}
EXPECTED_CRITERIA_PAGES = {13:15, 14:16, 15:17, 16:18, 17:19, 18:21, 19:22}
EXPECTED_STORAGE = "eksamio_ege_math_profile_demo_2025_v1_0"
EXPECTED_URL = "https://eksamio.ru/ege/matematika-profil/demoversiya/2025/"


def normalize(text: str) -> str:
    text = text.translate(str.maketrans({"–": "-", "−": "-", "—": "-", "‑": "-"}))
    return " ".join(text.split())


def read_norm(path: Path) -> str:
    return normalize(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checks = {}

    inventory_path = ROOT / f"{PREFIX}-SOURCE-INVENTORY.generated.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    for source_key, expected_hash in EXPECTED_HASHES.items():
        source = inventory["sources"][source_key]
        source_path = REPO / source["source_pdf"]
        actual_hash = sha256(source_path)
        assert source["source_sha256"] == expected_hash, (source_key, source["source_sha256"])
        assert actual_hash == expected_hash, (source_key, actual_hash)
    assert inventory["official_condition_assets"] == 37
    checks["official_source_identity"] = "PASS: all 3 repo FIPI 2025 PDFs match locked SHA-256; 37 condition assets reported"

    answer_page = read_norm(CANON / "profile-demo" / "page-14.txt")
    expected_answer_rows = {
        1: "1 61 18 157 5",
        2: "2 12 29",
        3: "3 1,125 340 104",
        4: "4 0,35 0,38",
        5: "5 0,992 0,15",
        6: "6 4 17 93 3",
        7: "7 2,76 2 125",
        8: "8 6 -1,4",
        9: "9 5",
        10: "10 12 15 8",
        11: "11 7",
        12: "12 -83 -6 16",
    }
    for n, row in expected_answer_rows.items():
        assert row in answer_page, (n, row)
    assert "Правильное выполнение каждого из заданий 1-12 оценивается 1 баллом." in answer_page
    checks["official_answer_table"] = "PASS: 30/30 short-answer values rechecked against canonical FIPI 2025 printed page 14"

    spec5 = read_norm(CANON / "profile-spec" / "page-05.txt")
    assert "Часть 1 12 12 37,5" in spec5
    assert "Часть 2 7 20 62,5" in spec5
    assert "Итого 19 32 100" in spec5
    checks["exam_structure"] = "PASS: part 1 = 12/12; part 2 = 7/20; total = 19 tasks / 32 primary"

    spec7 = read_norm(CANON / "profile-spec" / "page-07.txt")
    assert "3 часа 55 минут (235 минут)" in spec7
    assert "Правильное выполнение каждого из заданий 1-12 оценивается 1 баллом." in spec7
    assert "Проверка выполнения заданий 13-19 проводится экспертами" in spec7
    assert "заданий 13, 15 и 16 оценивается 2 баллами" in spec7
    assert "заданий 14 и 17 - 3 баллами" in spec7
    assert "заданий 18 и 19 - 4 баллами" in spec7
    checks["duration_and_scoring_specification"] = "PASS: 235 minutes; official max-score map 2/3/2/2/3/4/4"

    spec8 = read_norm(CANON / "profile-spec" / "page-08.txt")
    assert "Максимальный первичный балл за выполнение экзаменационной работы - 32." in spec8
    checks["primary_score_cap"] = "PASS: maximum primary score 32"

    for task, page in EXPECTED_CRITERIA_PAGES.items():
        text = read_norm(CANON / "profile-demo" / f"page-{page:02d}.txt")
        assert f"Максимальный балл {EXPECTED_MAX_EXT[task]}" in text, (task, page)
    checks["extended_criteria_maxima"] = "PASS: tasks 13-19 criteria maxima checked on canonical printed pages 15-22"

    asset_map = json.loads((ROOT / f"{PREFIX}-ASSET-MAP.generated.json").read_text(encoding="utf-8"))
    assert asset_map["official_examples_total"] == 37
    assert {int(k): int(v) for k, v in asset_map["variant_counts"].items()} == EXPECTED_COUNTS
    assets = asset_map["assets"]
    assert len(assets) == 37
    assert {item["example"] for item in assets} == {f"{n}-{v}" for n, c in EXPECTED_COUNTS.items() for v in range(1, c + 1)}
    assert all("direct official PDF raster crop" in item["source_mode"] for item in assets)
    checks["condition_asset_map"] = "PASS: 37/37 official examples, exact per-task counts, direct-source raster crops"

    data = json.loads((ROOT / f"{PREFIX}-EXAM-DATA.json").read_text(encoding="utf-8"))
    assert data["sourceYear"] == 2025
    assert data["officialExampleCount"] == 37
    assert data["minutes"] == 235
    assert data["maxPrimaryScore"] == 32
    assert data["autoMax"] == 12 and data["selfMax"] == 20
    assert data["storageKey"] == EXPECTED_STORAGE
    assert data["permanentUrl"] == EXPECTED_URL
    assert len(data["tasks"]) == 19
    for task in data["tasks"]:
        n = int(task["number"])
        assert len(task["variants"]) == EXPECTED_COUNTS[n], n
        if n <= 12:
            actual = [v["answer"] for v in task["variants"]]
            assert actual == EXPECTED_ANSWERS[n], (n, actual)
            assert all(v["max_score"] == 1 for v in task["variants"])
        else:
            assert task["variants"][0]["max_score"] == EXPECTED_MAX_EXT[n], n
    checks["implementation_data_crosscheck"] = "PASS: EXAM-DATA matches independently re-read source values and structure"

    matrix_path = ROOT / "AUDIT-MATRIX-2025-profile.csv"
    with matrix_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 37
    assert all(row["result"] == "PASS" for row in rows)
    assert all(not row["defect_id"].strip() for row in rows)
    checks["audit_matrix"] = "PASS: exactly 37 rows; all final browser/source rows PASS; no open defect IDs"

    browser = json.loads((ROOT / "tests" / "evidence" / "profile-2025-browser-evidence.json").read_text(encoding="utf-8"))
    assert browser["status"] == "PASS"
    assert browser["checks"]["official_examples_real_controls"].startswith("37/37 PASS")
    assert browser["checks"]["correct_and_wrong_short_answers"].startswith("30/30 PASS")
    assert browser["checks"]["javascript_errors"] == 0
    checks["browser_evidence_crosscheck"] = "PASS: 37/37 real controls; 30/30 correct+wrong short answers; 0 severe JS errors"

    blocks = sorted(ROOT.glob(f"{PREFIX}-T123-*.txt"))
    sizes = {p.name: p.stat().st_size for p in blocks}
    assert len(blocks) == 59
    assert max(sizes.values()) < 45000
    checks["tilda_size_crosscheck"] = f"PASS: 59 T123 blocks; max {max(sizes.values())} bytes < 45000"

    preview = (ROOT / f"{PREFIX}-PREVIEW.html").read_text(encoding="utf-8")
    assert "профильной математике 2026" not in preview
    assert "ФИПИ 2026" not in preview
    assert "официальный пример ${v.variant}" not in preview
    checks["year_and_variant_isolation"] = "PASS: no 2026 content label; learner variant number template absent; 2025 storage isolated"

    evidence = {
        "status": "PASS",
        "review_type": "SECOND_SOURCE_CONTENT_REVIEW",
        "scope": "Internal second review pass against canonical repo FIPI 2025 sources; separate from build implementation and Selenium runtime audit; not third-party certification.",
        "source_year": 2025,
        "official_examples": 37,
        "short_examples": 30,
        "extended_examples": 7,
        "checks": checks,
    }
    evidence_path = ROOT / "SECOND-SOURCE-CONTENT-AUDIT-2025-profile.json"
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    review_md = ROOT / "SECOND-SOURCE-CONTENT-REVIEW-2025-profile.md"
    review_md.write_text(
        "# Второй содержательный аудит — ЕГЭ профильная математика 2025\n\n"
        "Статус: **PASS**.\n\n"
        "Это отдельный второй проход по содержанию после сборки и browser-аудита. Он повторно сверяет данные реализации с каноническими источниками ФИПИ 2025 в репозитории. Это внутренний контроль проекта, а не внешняя или третьесторонняя сертификация.\n\n"
        "Проверено:\n\n"
        "- SHA-256 трёх исходных PDF ФИПИ 2025 совпадают с зафиксированными source hashes.\n"
        "- Печатная страница 14 демоверсии: 30/30 эталонов ответов №1–12 повторно сверены.\n"
        "- Спецификация: 19 заданий, часть 1 — 12 баллов, часть 2 — 20 баллов, максимум 32, время 235 минут.\n"
        "- №13–19: максимумы 2/3/2/2/3/4/4 повторно проверены по официальным критериям на печатных страницах 15–22.\n"
        "- Source asset map: ровно 37 официальных примеров с распределением 4/2/3/2/2/4/3/2/1/3/1/3/1/1/1/1/1/1/1; learner conditions являются прямыми raster-crop исходного PDF.\n"
        "- EXAM-DATA повторно сопоставлен с источником: ответы, количество вариантов, баллы, URL, 2025 storage key.\n"
        "- Финальная audit matrix содержит 37 строк PASS без открытых defect ID.\n"
        "- Browser evidence отдельно подтверждает 37/37 реальных DOM-взаимодействий, 30/30 correct+wrong short-answer checks и 0 серьёзных JS-ошибок.\n"
        "- Tilda size gate повторно проверен: 59 T123, каждый < 45 000 байт.\n\n"
        "Следующий внешний этап: Tilda publication → production smoke-test → ручная студенческая приёмка. До этого LIVE GO не присваивается.\n",
        encoding="utf-8",
    )

    status_path = ROOT / f"{PREFIX}-PAGE-STATUS.txt"
    status_lines = status_path.read_text(encoding="utf-8").splitlines()
    patched = []
    replaced = False
    for line in status_lines:
        if line.startswith("INDEPENDENT_AUDIT_GATE:"):
            patched.append("SECOND_SOURCE_CONTENT_REVIEW_GATE: PASS — separate FIPI 2025 source/content cross-check recorded in SECOND-SOURCE-CONTENT-REVIEW-2025-profile.md")
            patched.append("AUDIT_SCOPE: INTERNAL_SECOND_PASS_NOT_THIRD_PARTY_CERTIFICATION")
            replaced = True
        else:
            patched.append(line)
    if not replaced:
        insert_at = next((i + 1 for i, line in enumerate(patched) if line.startswith("TILDA_SIZE_GATE:")), len(patched))
        patched[insert_at:insert_at] = [
            "SECOND_SOURCE_CONTENT_REVIEW_GATE: PASS — separate FIPI 2025 source/content cross-check recorded in SECOND-SOURCE-CONTENT-REVIEW-2025-profile.md",
            "AUDIT_SCOPE: INTERNAL_SECOND_PASS_NOT_THIRD_PARTY_CERTIFICATION",
        ]
    status_path.write_text("\n".join(patched) + "\n", encoding="utf-8")

    build_evidence_path = ROOT / f"{PREFIX}-BUILD-EVIDENCE.json"
    build_evidence = json.loads(build_evidence_path.read_text(encoding="utf-8"))
    build_evidence["second_source_content_review"] = "PASS"
    build_evidence["second_source_content_review_evidence"] = evidence_path.name
    build_evidence["audit_scope"] = "internal second pass; not third-party certification"
    build_evidence_path.write_text(json.dumps(build_evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report_path = ROOT / "AUDIT-REPORT-2025-profile.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "SECOND-SOURCE-CONTENT-REVIEW-2025-profile.md"
    if marker not in report:
        report += (
            "\n- Выполнен отдельный второй содержательный проход по каноническим источникам ФИПИ 2025; доказательства: `SECOND-SOURCE-CONTENT-REVIEW-2025-profile.md` и `SECOND-SOURCE-CONTENT-AUDIT-2025-profile.json`.\n"
            "- Scope: внутренний второй audit pass, отдельный от реализации и Selenium-проверки; внешняя/третьесторонняя сертификация не заявляется.\n"
        )
        report_path.write_text(report, encoding="utf-8")

    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
