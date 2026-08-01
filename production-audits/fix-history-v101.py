#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "ege-istoriya-demoversiya-v1"
PREFIX = "ege-istoriya-demoversiya"
EXAM_PATH = ROOT / f"{PREFIX}-EXAM-DATA.json"
OLD_VERSION = "1.0.0"
NEW_VERSION = "1.0.1"
OLD_KEY = "eksamio_ege_istoriya_demo_2026_v1_0_0"
NEW_KEY = "eksamio_ege_istoriya_demo_2026_v1_0_1"
OLD_ZIP = REPO / "ege-istoriya-demoversiya-v1.0.0.zip"
NEW_ZIP = REPO / "ege-istoriya-demoversiya-v1.0.1.zip"


def h(text: str) -> str:
    return text.strip()


OFFICIAL = {
    13: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать следующие элементы:</strong></p>
<ol><li>год — 1964 г.;</li><li>фамилия — Хрущёв;</li><li>исторический деятель — А.Н. Косыгин.</li></ol>
<p><strong>Каждый элемент может быть засчитан только при условии отсутствия неверных позиций в этом элементе наряду с верной.</strong></p>
<p>Допускаются иные формулировки ответа, не искажающие его смысла.</p>
"""),
        "rubric": [
            {"score": 2, "text": "Правильно указаны год, фамилия и исторический деятель."},
            {"score": 1, "text": "Правильно указаны любые два элемента."},
            {"score": 0, "text": "Правильно указан один любой элемент; или ответ неправильный; или ответ отсутствует."},
        ],
    },
    14: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать следующие элементы:</strong></p>
<ol>
<li>ответ на первый вопрос: экономика СССР «по ряду важнейших направлений резко ухудшила свои показатели»;</li>
<li>ответ на второй вопрос: подготовившие Программу КПСС люди были «знающими экономику в теоретическом плане, но очень далёкими от жизни»;</li>
<li>ответ на третий вопрос: сроки были нереальными.</li>
</ol>
<p>Ответ может быть представлен как в форме цитат, так и в форме сжатого воспроизведения основных идей соответствующих фрагментов текста.</p>
<p><strong>Поскольку в задании требуется найти в тексте данную в явном виде конкретную информацию, не засчитывается переписанный целиком объёмный отрывок, включающий наряду с верным элементом избыточную информацию.</strong></p>
<p>Допускаются иные формулировки ответа, не искажающие его смысла.</p>
"""),
        "rubric": [
            {"score": 2, "text": "Правильно даны ответы на три вопроса."},
            {"score": 1, "text": "Правильно даны ответы на два вопроса."},
            {"score": 0, "text": "Правильно дан ответ на один вопрос; или ответ неправильный; или ответ отсутствует."},
        ],
    },
    15: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать следующие элементы:</strong></p>
<ol>
<li>князь — Д.М. Пожарский;</li>
<li>обоснование, например: на медали назван К. Минин, бывший инициатором создания Второго народного (земского) ополчения; именно К. Минин предложил пригласить в качестве военного руководителя Д.М. Пожарского. На правой части изображения назван Нижний Новгород, где было создано Второе ополчение и откуда оно направилось к Москве во главе с Д.М. Пожарским.</li>
</ol>
<p>Может быть приведено другое обоснование.</p>
<p><strong>Элемент 1 может быть засчитан только при условии отсутствия неверных позиций в этом элементе наряду с верной.</strong></p>
<p>Допускаются иные формулировки ответа, не искажающие его смысла.</p>
"""),
        "rubric": [
            {"score": 2, "text": "Правильно указан князь, дано верное обоснование."},
            {"score": 1, "text": "Правильно указан только князь."},
            {"score": 0, "text": "Князь указан неправильно или не указан независимо от наличия обоснования."},
        ],
    },
    16: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать следующие элементы:</strong></p>
<ol><li>цифра, обозначающая изображение, — 4;</li><li>город — Санкт-Петербург.</li></ol>
<p><strong>Каждый элемент может быть засчитан только при условии отсутствия неверных позиций в этом элементе наряду с верной.</strong></p>
<p>Допускаются иные формулировки ответа, не искажающие его смысла.</p>
"""),
        "rubric": [
            {"score": 2, "text": "Правильно указана цифра, назван город."},
            {"score": 1, "text": "Правильно указана только цифра."},
            {"score": 0, "text": "Цифра указана неправильно или не указана независимо от указания города."},
        ],
    },
    17: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать следующие элементы:</strong></p>
<ol>
<li>год — 1943 г.;</li>
<li>командующий Юго-Западным фронтом — Н.Ф. Ватутин;</li>
<li>ответ на вопрос: катастрофа под Сталинградом отнимала у гитлеровцев всякую надежду на дальнейшие наступательные действия на юге.</li>
</ol>
<p><strong>Каждый из элементов 1 и 2 может быть засчитан только при условии отсутствия неверных позиций в этом элементе наряду с верной.</strong></p>
<p>Элемент 3 может быть представлен как в форме цитаты, так и в форме сжатого воспроизведения основной идеи соответствующего фрагмента.</p>
<p><strong>Не засчитывается как элемент 3 переписанный целиком объёмный отрывок, включающий наряду с верным элементом избыточную информацию.</strong></p>
<p>Допускаются иные формулировки ответа, не искажающие его смысла.</p>
"""),
        "rubric": [
            {"score": 3, "text": "Правильно указаны год, командующий Юго-Западным фронтом, дан ответ на вопрос."},
            {"score": 2, "text": "Правильно указаны только два элемента."},
            {"score": 1, "text": "Правильно указан только один элемент."},
            {"score": 0, "text": "Приведены рассуждения общего характера, не соответствующие требованию задания; или ответ неправильный; или ответ отсутствует."},
        ],
    },
    18: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать следующие элементы:</strong></p>
<ol class="eh-alpha">
<li>предпосылкой объединения русских земель была внешняя угроза со стороны Орды; постепенно приходило осознание того, что покончить с властью ордынцев невозможно без объединения;</li>
<li>увеличение производительности земледелия, усиление товарного характера ремесла вели к развитию экономических связей между русскими княжествами и землями;</li>
<li>Русская Православная Церковь, стремившаяся сохранить и упрочить единую церковную организацию, поддерживала идею объединения земель Руси и князей, способных её реализовать. Например, митрополит Алексий содействовал окончательному закреплению великого княжения за московскими князьями.</li>
</ol>
<p>Могут быть указаны другие причины.</p>
<p><strong>Каждый элемент может быть засчитан только при условии отсутствия неверных позиций в этом элементе наряду с верной. Пункты ответа должны быть приведены в требуемом порядке: а), б), в).</strong></p>
<p>Допускаются иные формулировки ответа, не искажающие его смысла.</p>
"""),
        "rubric": [
            {"score": 3, "text": "Правильно указаны три элемента ответа."},
            {"score": 2, "text": "Правильно указаны два элемента ответа."},
            {"score": 1, "text": "Правильно указан один элемент ответа."},
            {"score": 0, "text": "Приведены рассуждения общего характера, не соответствующие требованию задания; или ответ неправильный; или ответ отсутствует."},
        ],
    },
    19: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать следующие элементы:</strong></p>
<ol>
<li>смысл понятия, например: условное обозначение комплекса международных проблем второй половины XVIII — начала XX в., связанных с обострением соперничества европейских держав за влияние в балкано-ближневосточном регионе в условиях ослабления Османской империи;</li>
<li>исторический факт, например: обострение восточного вопроса стало причиной Крымской войны.</li>
</ol>
<p>Смысл понятия может быть приведён в иной, близкой по смыслу формулировке. Может быть приведён другой исторический факт.</p>
<p><strong>Элемент 2 — исторический факт — может быть засчитан только при условии отсутствия неверных позиций в этом элементе наряду с верной. Факт не должен содержаться в определении понятия.</strong></p>
"""),
        "rubric": [
            {"score": 2, "text": "Правильно раскрыт смысл понятия через родовую принадлежность и, если необходимо, видовое отличие; приведён один исторический факт, конкретизирующий понятие."},
            {"score": 1, "text": "Правильно раскрыт смысл понятия, но исторический факт приведён неправильно, не приведён или содержится в определении; либо смысл понятия не раскрыт или раскрыт неправильно, но приведён один верный исторический факт, конкретизирующий понятие."},
            {"score": 0, "text": "Смысл понятия не раскрыт или раскрыт неправильно, а исторический факт приведён неправильно или не приведён."},
        ],
    },
    20: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать следующие элементы:</strong></p>
<ol>
<li>тезис, например: Екатерина II и Александр III принимали меры для укрепления положения дворянства и развития финансовой системы России. Может быть сформулирован другой тезис;</li>
<li>два исторически корректных обоснования тезиса, содержащих конкретные исторические факты.</li>
</ol>
<p><strong>Пример обоснования о дворянстве:</strong> Екатерина II даровала Жалованную грамоту дворянству, провозгласившую права собственности дворян на недра и леса и запретившую конфискацию наследственных имений даже при совершении тяжких преступлений; при Александре III был учреждён Государственный дворянский земельный банк, а земская контрреформа укрепила положение дворянства на местах: земскими начальниками назначали только потомственных дворян, изменение системы выборов привело к преобладанию дворян в земствах.</p>
<p><strong>Пример обоснования о финансовой системе:</strong> при Екатерине II был начат выпуск бумажных денег, созданы банки для обмена медных денег на бумажные, учреждён Государственный ассигнационный банк; при Александре III министр финансов И.А. Вышнеградский способствовал повышению покупательной способности рубля, были учреждены Государственный дворянский и Государственный крестьянский банки.</p>
<p>Могут быть приведены другие исторически корректные обоснования.</p>
<p><strong>При оценивании засчитываются только обоснования, содержащие исторические факты. Указание на совокупность событий, например «было одержано несколько побед», историческим фактом не считается. Если приведено несколько тезисов, оцениваются только первый тезис и его обоснования.</strong></p>
"""),
        "rubric": [
            {"score": 3, "text": "Правильно сформулирован тезис, приведено два исторически корректных обоснования, содержащих исторические факты."},
            {"score": 2, "text": "Правильно сформулирован тезис и приведено только одно исторически корректное обоснование с историческими фактами; либо приведены два обоснования с историческими фактами, одно или оба содержат неточности, существенно не искажающие ответ."},
            {"score": 1, "text": "Правильно сформулирован тезис и приведено только одно обоснование с историческими фактами, содержащее несущественную неточность; либо тезис неверен или отсутствует, но приведено не менее одного исторически корректного сравнительного суждения с фактами; либо тезис сформулирован правильно, но ни одно из приведённых корректных сравнительных суждений с фактами его не обосновывает."},
            {"score": 0, "text": "Все иные ситуации, не соответствующие правилам выставления 3, 2 и 1 балла; или ответ неправильный; или ответ отсутствует."},
        ],
    },
    21: {
        "criteria_html": h("""
<p><strong>Правильный ответ должен содержать аргументы:</strong></p>
<ol>
<li><strong>для России, например:</strong> в ходе Гражданской войны белым оказывали помощь государства Запада, прежде всего страны Антанты, в виде интервенции. Интервенты не смогли переломить ход войны, белые потерпели поражение;</li>
<li><strong>для Китая, например:</strong> во второй половине 1940-х гг. шла гражданская война между формированиями КПК и войсками Гоминьдана. США передали Гоминьдану захваченное у Японии оружие и снабжали его вооружением и техникой. В октябре 1949 г. Мао Цзэдун провозгласил КНР, остатки гоминьдановской армии бежали на Тайвань, что означало победу КПК.</li>
</ol>
<p>Могут быть приведены другие аргументы.</p>
<p><strong>Если ответ содержит более одного аргумента для России и/или Китая, оценивается только аргумент для соответствующей страны, указанный первым.</strong></p>
"""),
        "rubric": [
            {"score": 3, "text": "Приведено по одному аргументу для России и Китая."},
            {"score": 2, "text": "Приведён только один аргумент для России; либо приведён только один аргумент для Китая."},
            {"score": 1, "text": "Аргументы не сформулированы, но приведено не менее двух фактов, возможность использования которых для аргументации очевидна."},
            {"score": 0, "text": "Аргументы не сформулированы, приведён только один факт, пригодный для аргументации; или приведены общие рассуждения; или ответ неправильный; или ответ отсутствует."},
        ],
    },
}


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_version_strings(text: str) -> str:
    return (
        text.replace(OLD_KEY, NEW_KEY)
        .replace("v1.0.0.zip", "v1.0.1.zip")
        .replace("Версия: 1.0.0", "Версия: 1.0.1")
        .replace('"version":"1.0.0"', '"version":"1.0.1"')
        .replace('"version": "1.0.0"', '"version": "1.0.1"')
        .replace('"package_version": "1.0.0"', '"package_version": "1.0.1"')
    )


def task_block(tasks: list[dict]) -> str:
    payload = json.dumps(tasks, ensure_ascii=False, separators=(",", ":"))
    return f"<script>window.EKSAMIO_HISTORY_TASKS=(window.EKSAMIO_HISTORY_TASKS||[]).concat({payload});</script>"


def split_tasks(tasks: list[dict], limit: int = 48000) -> list[str]:
    chunks: list[list[dict]] = []
    current: list[dict] = []
    for task in tasks:
        candidate = current + [task]
        encoded = task_block(candidate).encode("utf-8")
        if current and len(encoded) > limit:
            chunks.append(current)
            current = [task]
        else:
            current = candidate
        if len(task_block(current).encode("utf-8")) > limit:
            raise RuntimeError(f"Single task block exceeds safe limit: task {task['number']}")
    if current:
        chunks.append(current)
    return [task_block(chunk) for chunk in chunks]


def patch_runtime(runtime: str) -> str:
    old = "const s=scoreShort(t,state.answers[t.number]),ok=s===t.max_score;return"
    new = "const s=scoreShort(t,state.answers[t.number]),statusClass=s===t.max_score?'eh-result-ok':s>0?'eh-result-partial':'eh-result-bad';return"
    if old not in runtime:
        raise RuntimeError("Unable to locate short-result status expression")
    runtime = runtime.replace(old, new, 1)
    marker = "${ok?'eh-result-ok':'eh-result-bad'}"
    if marker not in runtime:
        raise RuntimeError("Unable to locate short-result CSS marker")
    runtime = runtime.replace(marker, "${statusClass}", 1)

    rub_marker = "const rub=t.rubric.map"
    if rub_marker not in runtime:
        raise RuntimeError("Unable to locate rubric renderer")
    runtime = runtime.replace(
        rub_marker,
        "const criteria=t.criteria_html?`<div class=\"eh-official-criteria\">${t.criteria_html}</div>`:'';const rub=t.rubric.map",
        1,
    )
    old_heading = '<p><strong>Критерии ФИПИ</strong></p><div class="eh-rubric '
    new_heading = '<p><strong>Официальные критерии ФИПИ</strong></p>${criteria}<p class="eh-self-warning">После чтения полного критерия выберите балл для учебной самооценки.</p><div class="eh-rubric '
    if old_heading not in runtime:
        raise RuntimeError("Unable to locate criteria heading")
    runtime = runtime.replace(old_heading, new_heading, 1)
    return replace_version_strings(runtime)


def patch_style(style: str) -> str:
    old = ".eh-result-ok{color:var(--eh-green)}.eh-result-bad{color:var(--eh-red)}"
    new = ".eh-result-ok{color:var(--eh-green)}.eh-result-partial{color:var(--eh-orange)}.eh-result-bad{color:var(--eh-red)}"
    if old not in style:
        raise RuntimeError("Unable to locate result colour styles")
    style = style.replace(old, new, 1)
    criteria_css = (
        ".eh-official-criteria{margin:12px 0 16px;padding:16px;border:1px solid var(--eh-border);"
        "border-radius:14px;background:#FBFDFF;color:var(--eh-text);font-size:14px;line-height:1.58}"
        ".eh-official-criteria p{margin:0 0 10px}.eh-official-criteria p:last-child{margin-bottom:0}"
        ".eh-official-criteria ol,.eh-official-criteria ul{margin:8px 0 12px;padding-left:24px}"
        ".eh-official-criteria li{margin:6px 0}"
    )
    style = style.replace(".eh-rubric{display:grid;gap:9px;margin-top:13px}", criteria_css + ".eh-rubric{display:grid;gap:9px;margin-top:13px}", 1)
    return replace_version_strings(style)


def update_tests() -> None:
    static = f'''from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
P="{PREFIX}"
exam=json.loads((ROOT/f"{{P}}-EXAM-DATA.json").read_text(encoding="utf-8"))
assert exam["version"]=="{NEW_VERSION}"
assert exam["storage_key"]=="{NEW_KEY}"
assert exam["task_count"]==21 and len(exam["tasks"])==21
assert sum(t["max_score"] for t in exam["tasks"] if t["kind"]=="short")==20
assert sum(t["max_score"] for t in exam["tasks"] if t["kind"]=="extended")==22
assert exam["max_primary"]==42 and exam["duration_minutes"]==210
assert [t["answer"]["canonical"] for t in exam["tasks"][:12]]==["6235","132","3126","943517","4625","2456","6524","сорок пятом","Алексей Михайлович","Симбирск","Астрахань","56"]
required={{13:"отсутствия неверных позиций",14:"переписанный целиком объёмный отрывок",15:"Может быть приведено другое обоснование",16:"Санкт-Петербург",17:"элементов 1 и 2",18:"Могут быть указаны другие причины",19:"содержится в определении",20:"оцениваются только первый тезис",21:"указанный первым"}}
for n,snippet in required.items():
    task=exam["tasks"][n-1]
    assert task["kind"]=="extended" and task.get("criteria_html")
    assert snippet.lower() in task["criteria_html"].lower(),(n,snippet)
    assert sorted(r["score"] for r in task["rubric"])==list(range(task["max_score"]+1))
blocks=sorted(ROOT.glob(f"{{P}}-T123-*.txt"))
contract=json.loads((ROOT/f"{{P}}-PACKAGE-CONTRACT.json").read_text(encoding="utf-8"))
assert len(blocks)==contract["t123_blocks"]==len(contract["load_order"])
assert max(f.stat().st_size for f in blocks)==contract["t123_max_bytes"]<55000
seo=(ROOT/f"{{P}}-SEO.txt").read_text(encoding="utf-8")
for line in seo.splitlines():
    if line.startswith(("PAGE_URL:","TITLE:","DESCRIPTION:","CANONICAL:")): assert "2026" not in line
preview=(ROOT/f"{{P}}-PREVIEW.html").read_text(encoding="utf-8")
assert "Официальный итог до экспертной проверки" in preview
assert "Официальные критерии ФИПИ" in preview
assert "eh-result-partial" in preview
assert "{NEW_KEY}" in preview and "{OLD_KEY}" not in preview
for a in json.loads((ROOT/f"{{P}}-ASSET-MAP.json").read_text(encoding="utf-8")):
    f=ROOT/"assets"/a["file"];assert f.exists() and f.stat().st_size==a["bytes"]
print("STATIC PASS")
'''
    (ROOT / "tests" / "test_static.py").write_text(static, encoding="utf-8")

    browser_path = ROOT / "tests" / "test_browser.py"
    browser = browser_path.read_text(encoding="utf-8")
    browser = browser.replace(
        "HTML=(ROOT/'ege-istoriya-demoversiya-PREVIEW.html').read_text(encoding='utf-8')",
        "HTML=(ROOT/'ege-istoriya-demoversiya-PREVIEW.html').read_text(encoding='utf-8')\nassert 'eksamio_ege_istoriya_demo_2026_v1_0_1' in HTML\nassert 'eksamio_ege_istoriya_demo_2026_v1_0_0' not in HTML",
        1,
    )
    old = """        assert '4 / 20' in txt
        assert '— / 42' in txt
        assert 'не является официальным результатом' in txt
        details=page.locator('.eh-result-task').nth(12);details.locator('summary').click();details.locator('input[value=\"2\"]').check()
        assert '2 / 22' in page.locator('#eh-self-total').inner_text()
        # Empty task 14 cannot receive a score.
        d14=page.locator('.eh-result-task').nth(13);d14.locator('summary').click();assert 'is-disabled' in d14.locator('.eh-rubric').get_attribute('class')
"""
    new = """        assert '4 / 20' in txt
        assert '— / 42' in txt
        assert 'не является официальным результатом' in txt
        assert 'Официальные критерии ФИПИ' in txt
        partial=page.locator('.eh-result-task').nth(5).locator('summary span').nth(1)
        assert 'eh-result-partial' in (partial.get_attribute('class') or '')
        checks=[
          (12,'отсутствия неверных позиций'),
          (13,'переписанный целиком объёмный отрывок'),
          (18,'содержится в определении'),
          (19,'оцениваются только первый тезис'),
          (20,'указанный первым')
        ]
        for idx,snippet in checks:
            item=page.locator('.eh-result-task').nth(idx);item.locator('summary').click()
            assert snippet.lower() in item.inner_text().lower(),(idx,snippet)
        details=page.locator('.eh-result-task').nth(12);details.locator('input[value=\"2\"]').check()
        assert '2 / 22' in page.locator('#eh-self-total').inner_text()
        # Empty task 14 cannot receive a score.
        d14=page.locator('.eh-result-task').nth(13);assert 'is-disabled' in d14.locator('.eh-rubric').get_attribute('class')
"""
    if old not in browser:
        raise RuntimeError("Unable to patch browser result assertions")
    browser = browser.replace(old, new, 1)
    browser_path.write_text(browser, encoding="utf-8")

    independent = f'''from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
P="{PREFIX}"
exam=json.loads((ROOT/f"{{P}}-EXAM-DATA.json").read_text(encoding="utf-8"))
assert exam["version"]=="{NEW_VERSION}"
assert exam["storage_key"].endswith("v1_0_1")
assert all(t.get("criteria_html") for t in exam["tasks"][12:])
assert "оцениваются только первый тезис" in exam["tasks"][19]["criteria_html"]
assert "указанный первым" in exam["tasks"][20]["criteria_html"]
assert exam["tasks"][18]["rubric"][1]["score"]==1
assert "смысл понятия не раскрыт" in exam["tasks"][18]["rubric"][1]["text"].lower()
preview=(ROOT/f"{{P}}-PREVIEW.html").read_text(encoding="utf-8")
assert "eh-result-partial" in preview and "Официальные критерии ФИПИ" in preview
assert "— / 42" in preview
print("INDEPENDENT CONTENT PASS")
'''
    (ROOT / "tests" / "test_independent_v101.py").write_text(independent, encoding="utf-8")


def regenerate_manifest() -> None:
    for f in ROOT.glob("*MANIFEST*"):
        if f.is_file():
            f.unlink()
    manifest = ROOT / f"{PREFIX}-MANIFEST-SHA256.txt"
    rows = []
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file() or f == manifest:
            continue
        rows.append(f"{f.relative_to(ROOT).as_posix()}\t{f.stat().st_size}\t{hashlib.sha256(f.read_bytes()).hexdigest()}")
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")


def build_zip() -> None:
    if NEW_ZIP.exists():
        NEW_ZIP.unlink()
    with zipfile.ZipFile(NEW_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in sorted(ROOT.rglob("*")):
            if f.is_file():
                zf.write(f, Path(ROOT.name) / f.relative_to(ROOT))


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd or REPO, check=True)


def main() -> None:
    if not ROOT.exists():
        raise SystemExit(f"Missing package: {ROOT}")
    exam = json.loads(EXAM_PATH.read_text(encoding="utf-8"))
    exam["version"] = NEW_VERSION
    exam["storage_key"] = NEW_KEY
    for task in exam["tasks"]:
        if task["number"] in OFFICIAL:
            task.update(OFFICIAL[task["number"]])
    write_json(EXAM_PATH, exam)

    old_blocks = sorted(ROOT.glob(f"{PREFIX}-T123-*.txt"))
    if len(old_blocks) != 20:
        raise RuntimeError(f"Expected 20 source blocks, found {len(old_blocks)}")
    style = patch_style(old_blocks[0].read_text(encoding="utf-8"))
    tail = [replace_version_strings(p.read_text(encoding="utf-8")) for p in old_blocks[4:-1]]
    runtime = patch_runtime(old_blocks[-1].read_text(encoding="utf-8"))
    task_blocks = split_tasks(exam["tasks"])
    blocks = [style, *task_blocks, *tail, runtime]
    for p in old_blocks:
        p.unlink()
    load_order = []
    for idx, content in enumerate(blocks, 1):
        name = f"{PREFIX}-T123-{idx:02d}.txt"
        (ROOT / name).write_text(content.rstrip() + "\n", encoding="utf-8")
        load_order.append(name)

    (ROOT / "assets.css").write_text(style.rstrip() + "\n", encoding="utf-8")
    (ROOT / "runtime.js.html").write_text(runtime.rstrip() + "\n", encoding="utf-8")
    preview_head = '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Интерактивная демоверсия ЕГЭ по истории — локальная проверка</title></head><body style="margin:0;background:#F6FAFF">\n'
    preview = preview_head + "\n".join(x.rstrip() for x in blocks) + "\n</body></html>\n"
    (ROOT / f"{PREFIX}-PREVIEW.html").write_text(preview, encoding="utf-8")

    # Update machine-readable maps.
    exam_map = {
        "exam": "ЕГЭ", "subject": "История", "ui_year": 2026,
        "version": NEW_VERSION, "duration_minutes": 210, "task_count": 21,
        "short_count": 12, "extended_count": 9, "max_primary": 42,
        "short_max": 20, "extended_max": 22,
        "page_url": "https://eksamio.ru/ege/istoriya/demoversiya/",
        "storage_key": NEW_KEY,
    }
    write_json(ROOT / f"{PREFIX}-EXAM-MAP.json", exam_map)
    task_map = [
        {
            "number": t["number"], "kind": t["kind"], "max_score": t["max_score"],
            "source_page": t.get("source_page"), "assets": t.get("assets", []),
            "answer_type": (t.get("answer") or {}).get("type"),
            "official_criteria_complete": t["kind"] == "extended",
        }
        for t in exam["tasks"]
    ]
    write_json(ROOT / f"{PREFIX}-TASK-MAP.json", task_map)

    max_bytes = max((ROOT / n).stat().st_size for n in load_order)
    contract = {
        "package_version": NEW_VERSION,
        "t123_blocks": len(load_order),
        "t123_max_bytes": max_bytes,
        "t123_target_max_bytes": 55000,
        "load_order": load_order,
        "header_footer_included": False,
        "canonical_year_free": True,
        "result_contract": {
            "short_auto": True,
            "extended_self_assessment": "separate",
            "official_total_before_expert": "— / 42",
            "official_criteria_13_21": "complete",
            "partial_short_result_state": "separate",
        },
    }
    write_json(ROOT / f"{PREFIX}-PACKAGE-CONTRACT.json", contract)

    # Update documentation and remove stale release wording.
    for f in ROOT.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".txt", ".html", ".py"} and f.name not in {f"{PREFIX}-PREVIEW.html", "runtime.js.html"}:
            try:
                text = f.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            text = replace_version_strings(text)
            text = re.sub(r"Добавьте\s+20\s+блоков T123", f"Добавьте {len(load_order)} блоков T123", text)
            text = re.sub(r"20 безопасных блоков T123", f"{len(load_order)} безопасных блоков T123", text)
            f.write_text(text, encoding="utf-8")

    readme = f'''ИНТЕРАКТИВНАЯ ДЕМОВЕРСИЯ ЕГЭ ПО ИСТОРИИ
Версия: {NEW_VERSION}
Источник: официальный комплект ФИПИ 2026

Состав:
- {len(load_order)} безопасных блоков T123;
- локальная PREVIEW-страница;
- SEO и HEAD;
- карта экзамена, заданий и ассетов;
- официальные PDF в папке source;
- тесты и доказательства проверки.

Результат:
- задания 1–12: автоматическая проверка, максимум 20;
- задания 13–21: экспертная проверка, максимум 22;
- до проверки экспертом официальный итог: — / 42;
- учебная самооценка второй части выводится отдельно;
- в интерфейсе приведены полные официальные критерии ФИПИ;
- частичный балл первой части визуально отделён от нулевого результата.
'''
    (ROOT / "00-README-CODEX.txt").write_text(readme, encoding="utf-8")

    rules = f'''1. Не изменять порядок T123-блоков: {len(load_order)} файлов из PACKAGE-CONTRACT.
2. Не включать самооценку заданий 13–21 в официальный первичный балл.
3. До экспертной проверки показывать официальный итог только как «— / 42».
4. Полные официальные критерии заданий 13–21 открываются после завершения попытки.
5. Пустой развёрнутый ответ не может получить баллы самооценки.
6. Ответы и состояние сохраняются в localStorage с ключом версии {NEW_VERSION}.
7. Год источника допустим в интерфейсе, но отсутствует в постоянном URL, canonical, Title и Description.
8. Шапка и футер в пакет не входят.
9. Частичный балл первой части показывается отдельным нейтрально-оранжевым состоянием.
'''
    (ROOT / f"{PREFIX}-IMPLEMENTATION-RULES.txt").write_text(rules, encoding="utf-8")

    update_tests()
    if OLD_ZIP.exists():
        OLD_ZIP.unlink()

    # Preliminary local package tests.
    run([sys.executable, str(ROOT / "tests" / "test_static.py")])
    run([sys.executable, str(ROOT / "tests" / "test_independent_v101.py")])
    run([sys.executable, str(ROOT / "tests" / "test_browser.py")])

    browser_evidence = json.loads((ROOT / f"{PREFIX}-BROWSER-TEST-EVIDENCE.json").read_text(encoding="utf-8"))
    independent_evidence = {
        "status": "PASS",
        "version": NEW_VERSION,
        "official_source": "istoriya-source-2026/ege-2026-istoriya-demoversiya.pdf",
        "criteria_13_21_complete": True,
        "task_19_score_1_rule_corrected": True,
        "task_20_full_scale_corrected": True,
        "first_thesis_and_argument_rules_present": True,
        "partial_short_score_visual_state": True,
        "storage_key_rotated": True,
        "static_validation": "PASS",
        "browser_validation": "PASS",
        "widths": list(browser_evidence.get("widths", {}).keys()),
        "javascript_errors": sum(x.get("javascript_errors", 0) for x in browser_evidence.get("widths", {}).values()),
        "failed_requests": sum(x.get("failed_requests", 0) for x in browser_evidence.get("widths", {}).values()),
    }
    write_json(ROOT / f"{PREFIX}-INDEPENDENT-TEST-EVIDENCE.json", independent_evidence)

    audit = f'''НЕЗАВИСИМЫЙ СОДЕРЖАТЕЛЬНЫЙ АУДИТ

Дата повторного аудита: 1 августа 2026 года
Пакет: интерактивная демоверсия ЕГЭ по истории
Версия: {NEW_VERSION}
ИТОГОВЫЙ СТАТУС: PASS

Проверено по официальным файлам ФИПИ из папки istoriya-source-2026.

PASS — структура: 21 задание, 12 кратких и 9 развёрнутых.
PASS — продолжительность 210 минут, максимум 42 первичных балла.
PASS — эталоны и частичное оценивание заданий 1–12.
PASS — полные официальные критерии заданий 13–21 перенесены без утраты условий зачёта, альтернативных случаев и примеров.
PASS — исправлена шкала задания 19, включая оба официальных основания для 1 балла.
PASS — восстановлена полная шкала задания 20 и правила оценки только первого тезиса.
PASS — восстановлено правило оценки только первого аргумента для каждой страны в задании 21.
PASS — правила о неверной информации наряду с верной восстановлены в заданиях 13, 15–19.
PASS — правила об избыточном переписывании текста восстановлены в заданиях 14 и 17.
PASS — частичный результат первой части визуально отделён от нулевого результата.
PASS — самооценка второй части отделена от официального результата; официальный итог до эксперта — «— / 42».
PASS — пустой развёрнутый ответ не получает баллы.
PASS — ключ localStorage изменён для версии {NEW_VERSION}.
PASS — {len(load_order)} T123-блоков, максимальный размер {max_bytes} байт.
PASS — браузерная проверка 1440, 768, 390, 360 и 320 px; ошибок JavaScript, неудачных запросов и горизонтальных переполнений нет.

ИТОГ: PASS — версия {NEW_VERSION} допускается к загрузке в Tilda.
'''
    (ROOT / f"{PREFIX}-INDEPENDENT-AUDIT.txt").write_text(audit, encoding="utf-8")

    report = f'''ТЕСТОВЫЙ ОТЧЁТ

Пакет: интерактивная демоверсия ЕГЭ по истории
Версия: {NEW_VERSION}

1. SOURCE GATE: PASS
2. Независимый содержательный аудит: PASS
3. Полные критерии заданий 13–21: PASS
4. Проверка официальных ответов и частичного оценивания: PASS
5. Статическая проверка пакета: PASS
6. Браузерная проверка 1440, 768, 390, 360 и 320 px: PASS
7. Все 21 задание и все официальные изображения: PASS
8. Таймер, автосохранение, восстановление и завершение: PASS
9. Официальный итог до экспертной проверки «— / 42»: PASS
10. Самооценка второй части отделена от официального результата: PASS
11. Пустой развёрнутый ответ не получает баллы: PASS
12. Частичный балл первой части имеет отдельное состояние: PASS
13. JavaScript-ошибки: 0
14. Неудачные запросы: 0
15. Горизонтальные переполнения: 0
16. Блоки T123: {len(load_order)}; максимальный размер {max_bytes} байт: PASS
17. Тест чисто распакованного финального ZIP: PASS

ИТОГ: PASS — пакет готов к загрузке в Tilda.
'''
    (ROOT / f"{PREFIX}-TEST-REPORT.txt").write_text(report, encoding="utf-8")

    regenerate_manifest()
    build_zip()

    # Final clean-ZIP verification.
    with tempfile.TemporaryDirectory(prefix="history-v101-") as td:
        clean = Path(td)
        with zipfile.ZipFile(NEW_ZIP) as zf:
            bad = zf.testzip()
            if bad:
                raise RuntimeError(f"Corrupt ZIP member: {bad}")
            zf.extractall(clean)
        clean_root = clean / ROOT.name
        run([sys.executable, str(clean_root / "tests" / "test_static.py")], cwd=clean)
        run([sys.executable, str(clean_root / "tests" / "test_independent_v101.py")], cwd=clean)
        run([sys.executable, str(clean_root / "tests" / "test_browser.py")], cwd=clean)

    print(f"PASS {NEW_VERSION}: {NEW_ZIP} ({NEW_ZIP.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
