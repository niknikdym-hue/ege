from pathlib import Path

BIOLOGY_URL = "https://eksamio.ru/ege/biologiya/demoversiya/"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def update_catalog() -> None:
    path = Path("ege-demoversii-T123.txt")
    text = path.read_text(encoding="utf-8")
    if BIOLOGY_URL in text:
        return

    biology_background = """    #eksamio-ege-demos-v2 .ed-subject--biology{
      background:
        radial-gradient(circle at 94% 4%,rgba(25,122,92,.12),transparent 26%),
        linear-gradient(180deg,#FFFFFF,#F5FCF8);
    }
"""
    text = replace_once(
        text,
        "    #eksamio-ege-demos-v2 .ed-subject--math-base{",
        biology_background + "    #eksamio-ege-demos-v2 .ed-subject--math-base{",
        "catalog biology background",
    )

    biology_icon = """    #eksamio-ege-demos-v2 .ed-subject--biology .ed-subject__icon{
      background:#E3F5ED;color:#197A5C;
    }
"""
    text = replace_once(
        text,
        "    #eksamio-ege-demos-v2 .ed-subject--math-base .ed-subject__icon{",
        biology_icon + "    #eksamio-ege-demos-v2 .ed-subject--math-base .ed-subject__icon{",
        "catalog biology icon",
    )

    biology_card = """                <article class="ed-subject ed-subject--biology">
                  <div class="ed-subject__top">
                    <span class="ed-subject__icon" aria-hidden="true">Б</span>
                    <span class="ed-status">Доступно</span>
                  </div>
                  <h3>ЕГЭ по биологии</h3>
                  <p>Краткие ответы проверяются автоматически. После завершения для семи развёрнутых заданий доступны официальные критерии и материалы для самостоятельной оценки.</p>
                  <div class="ed-facts">
                    <span class="ed-fact">28 заданий</span>
                    <span class="ed-fact">235 минут</span>
                    <span class="ed-fact">11 рисунков</span>
                  </div>
                  <div class="ed-actions">
                    <a class="ed-button" href="https://eksamio.ru/ege/biologiya/demoversiya/">Начать демоверсию</a>
                  </div>
                </article>

"""
    text = replace_once(
        text,
        "                <article class=" + '"ed-subject ed-subject--math-base"' + ">",
        biology_card + "                <article class=" + '"ed-subject ed-subject--math-base"' + ">",
        "catalog biology card",
    )
    path.write_text(text, encoding="utf-8")


def update_home() -> None:
    path = Path("home-T123.txt")
    text = path.read_text(encoding="utf-8")
    if "/ege/biologiya/demoversiya/" in text:
        return

    text = replace_once(
        text,
        "#eksamio-home-final .eh-demo:nth-child(4){background:radial-gradient(circle at 94% 4%,rgba(184,78,69,.11),transparent 27%),linear-gradient(180deg,#fff,#FFF8F6)}",
        "#eksamio-home-final .eh-demo:nth-child(4){background:radial-gradient(circle at 94% 4%,rgba(184,78,69,.11),transparent 27%),linear-gradient(180deg,#fff,#FFF8F6)}\n#eksamio-home-final .eh-demo:nth-child(5){background:radial-gradient(circle at 94% 4%,rgba(25,122,92,.12),transparent 27%),linear-gradient(180deg,#fff,#F5FCF8)}",
        "home biology background",
    )
    text = replace_once(
        text,
        "#eksamio-home-final .eh-demo:nth-child(4) .eh-demo__icon{background:var(--eh-coral-soft);color:var(--eh-coral)}",
        "#eksamio-home-final .eh-demo:nth-child(4) .eh-demo__icon{background:var(--eh-coral-soft);color:var(--eh-coral)}\n#eksamio-home-final .eh-demo:nth-child(5) .eh-demo__icon{background:#E3F5ED;color:#197A5C}",
        "home biology icon",
    )

    chemistry_card = "    <a class=" + '"eh-demo"' + " href=" + '"/ege/khimiya/demoversiya/"' + "><div class=" + '"eh-demo__top"' + "><span class=" + '"eh-demo__icon"' + ">ХИ</span><span class=" + '"eh-status"' + ">Доступно</span></div><h3>Химия</h3><p>Автоматическая проверка первой части, критерии для развёрнутых заданий и справочные материалы ФИПИ.</p><div class=" + '"eh-facts"' + "><span class=" + '"eh-fact"' + ">34 задания</span><span class=" + '"eh-fact"' + ">210 минут</span></div><span class=" + '"eh-demo__link"' + ">Начать демоверсию →</span></a>"
    biology_card = "    <a class=" + '"eh-demo"' + " href=" + '"/ege/biologiya/demoversiya/"' + "><div class=" + '"eh-demo__top"' + "><span class=" + '"eh-demo__icon"' + ">БИ</span><span class=" + '"eh-status"' + ">Доступно</span></div><h3>Биология</h3><p>Автоматическая проверка первой части, 11 официальных рисунков и критерии для самостоятельной оценки развёрнутых ответов.</p><div class=" + '"eh-facts"' + "><span class=" + '"eh-fact"' + ">28 заданий</span><span class=" + '"eh-fact"' + ">235 минут</span></div><span class=" + '"eh-demo__link"' + ">Начать демоверсию →</span></a>"
    text = replace_once(
        text,
        chemistry_card,
        chemistry_card + "\n" + biology_card,
        "home biology card",
    )
    path.write_text(text, encoding="utf-8")


def update_footer() -> None:
    path = Path("site-footer-T123.txt")
    text = path.read_text(encoding="utf-8")
    if BIOLOGY_URL in text:
        return
    chemistry_link = '          <a href="https://eksamio.ru/ege/khimiya/demoversiya/">Химия</a>'
    biology_link = '          <a href="https://eksamio.ru/ege/biologiya/demoversiya/">Биология</a>'
    text = replace_once(
        text,
        chemistry_link,
        chemistry_link + "\n" + biology_link,
        "footer biology link",
    )
    path.write_text(text, encoding="utf-8")


update_catalog()
update_home()
update_footer()
