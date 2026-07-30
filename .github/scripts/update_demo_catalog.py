from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
footer_path = ROOT / "site-footer-T123.txt"
catalog_path = ROOT / "ege-demoversii-T123.txt"

footer = footer_path.read_text(encoding="utf-8")
catalog = catalog_path.read_text(encoding="utf-8")

footer_old = '''          <a href="https://eksamio.ru/ege/fizika/demoversiya/">Физика</a>
          <a href="https://eksamio.ru/ege/matematika-baza/demoversiya/">Базовая математика</a>'''
footer_new = '''          <a href="https://eksamio.ru/ege/fizika/demoversiya/">Физика</a>
          <a href="https://eksamio.ru/ege/khimiya/demoversiya/">Химия</a>
          <a href="https://eksamio.ru/ege/matematika-baza/demoversiya/">Базовая математика</a>'''

css_old = '''    #eksamio-ege-demos-v2 .ed-subject--physics{
      background:
        radial-gradient(circle at 94% 4%,rgba(47,128,255,.12),transparent 26%),
        linear-gradient(180deg,#FFFFFF,#F7FBFF);
    }
    #eksamio-ege-demos-v2 .ed-subject__top{'''
css_new = '''    #eksamio-ege-demos-v2 .ed-subject--physics{
      background:
        radial-gradient(circle at 94% 4%,rgba(47,128,255,.12),transparent 26%),
        linear-gradient(180deg,#FFFFFF,#F7FBFF);
    }
    #eksamio-ege-demos-v2 .ed-subject--chemistry{
      background:
        radial-gradient(circle at 94% 4%,rgba(13,148,136,.12),transparent 26%),
        linear-gradient(180deg,#FFFFFF,#F5FFFD);
    }
    #eksamio-ege-demos-v2 .ed-subject--math-base{
      background:
        radial-gradient(circle at 94% 4%,rgba(21,128,61,.10),transparent 26%),
        linear-gradient(180deg,#FFFFFF,#F8FFF9);
    }
    #eksamio-ege-demos-v2 .ed-subject--math-profile{
      background:
        radial-gradient(circle at 94% 4%,rgba(47,128,255,.10),transparent 26%),
        linear-gradient(180deg,#FFFFFF,#F8FBFF);
    }
    #eksamio-ege-demos-v2 .ed-subject--social{
      background:
        radial-gradient(circle at 94% 4%,rgba(245,158,11,.11),transparent 26%),
        linear-gradient(180deg,#FFFFFF,#FFFCF5);
    }
    #eksamio-ege-demos-v2 .ed-subject__top{'''

icon_old = '''    #eksamio-ege-demos-v2 .ed-subject--physics .ed-subject__icon{
      background:var(--ed-primary-soft);color:var(--ed-primary-hover);
    }
    #eksamio-ege-demos-v2 .ed-status{'''
icon_new = '''    #eksamio-ege-demos-v2 .ed-subject--physics .ed-subject__icon,
    #eksamio-ege-demos-v2 .ed-subject--math-profile .ed-subject__icon{
      background:var(--ed-primary-soft);color:var(--ed-primary-hover);
    }
    #eksamio-ege-demos-v2 .ed-subject--chemistry .ed-subject__icon{
      background:#CCFBF1;color:#0F766E;
    }
    #eksamio-ege-demos-v2 .ed-subject--math-base .ed-subject__icon{
      background:var(--ed-green-soft);color:var(--ed-green);
    }
    #eksamio-ege-demos-v2 .ed-subject--social .ed-subject__icon{
      background:var(--ed-warning-soft);color:var(--ed-warning);
    }
    #eksamio-ege-demos-v2 .ed-status{'''

cards_old = '''                <!-- Для нового предмета скопируйте одну карточку .ed-subject.
                     Сетка автоматически перестроится без изменения CSS и заголовков страницы. -->'''
cards_new = '''                <article class="ed-subject ed-subject--chemistry">
                  <div class="ed-subject__top">
                    <span class="ed-subject__icon" aria-hidden="true">Х</span>
                    <span class="ed-status">Доступно</span>
                  </div>
                  <h3>ЕГЭ по химии</h3>
                  <p>Краткие ответы проверяются автоматически. Расчётные и развёрнутые задания сохраняются для проверки по официальным решениям и критериям.</p>
                  <div class="ed-facts">
                    <span class="ed-fact">34 задания</span>
                    <span class="ed-fact">Справочные таблицы</span>
                    <span class="ed-fact">Критерии второй части</span>
                  </div>
                  <div class="ed-actions">
                    <a class="ed-button" href="https://eksamio.ru/ege/khimiya/demoversiya/">Начать демоверсию</a>
                  </div>
                </article>

                <article class="ed-subject ed-subject--math-base">
                  <div class="ed-subject__top">
                    <span class="ed-subject__icon" aria-hidden="true">МБ</span>
                    <span class="ed-status">Доступно</span>
                  </div>
                  <h3>ЕГЭ по базовой математике</h3>
                  <p>Ответы проверяются автоматически по официальному формату. Попытка сохраняет ответы, отметки и оставшееся время до завершения.</p>
                  <div class="ed-facts">
                    <span class="ed-fact">Полный вариант</span>
                    <span class="ed-fact">Автопроверка</span>
                    <span class="ed-fact">Непрерывный таймер</span>
                  </div>
                  <div class="ed-actions">
                    <a class="ed-button" href="https://eksamio.ru/ege/matematika-baza/demoversiya/">Начать демоверсию</a>
                  </div>
                </article>

                <article class="ed-subject ed-subject--math-profile">
                  <div class="ed-subject__top">
                    <span class="ed-subject__icon" aria-hidden="true">МП</span>
                    <span class="ed-status">Доступно</span>
                  </div>
                  <h3>ЕГЭ по профильной математике</h3>
                  <p>Краткая часть проверяется автоматически. Развёрнутые решения сохраняются и после завершения сверяются по официальным критериям.</p>
                  <div class="ed-facts">
                    <span class="ed-fact">Полный вариант</span>
                    <span class="ed-fact">Развёрнутые задачи</span>
                    <span class="ed-fact">Критерии оценивания</span>
                  </div>
                  <div class="ed-actions">
                    <a class="ed-button" href="https://eksamio.ru/ege/matematika-profil/demoversiya/">Начать демоверсию</a>
                  </div>
                </article>

                <article class="ed-subject ed-subject--social">
                  <div class="ed-subject__top">
                    <span class="ed-subject__icon" aria-hidden="true">ОБ</span>
                    <span class="ed-status">Доступно</span>
                  </div>
                  <h3>ЕГЭ по обществознанию</h3>
                  <p>Краткие ответы проверяются автоматически. Развёрнутая часть сохраняется для самостоятельной проверки по официальным критериям.</p>
                  <div class="ed-facts">
                    <span class="ed-fact">Полный вариант</span>
                    <span class="ed-fact">Работа с источниками</span>
                    <span class="ed-fact">Критерии второй части</span>
                  </div>
                  <div class="ed-actions">
                    <a class="ed-button" href="https://eksamio.ru/ege/obshchestvoznaniye/demoversiya/">Начать демоверсию</a>
                  </div>
                </article>'''

for label, text, old in (
    ("footer chemistry link", footer, footer_old),
    ("catalog subject styles", catalog, css_old),
    ("catalog icon styles", catalog, icon_old),
    ("catalog cards placeholder", catalog, cards_old),
):
    if old not in text:
        raise SystemExit(f"Missing expected fragment: {label}")

footer = footer.replace(footer_old, footer_new, 1)
catalog = catalog.replace(css_old, css_new, 1)
catalog = catalog.replace(icon_old, icon_new, 1)
catalog = catalog.replace(cards_old, cards_new, 1)

required_urls = [
    "https://eksamio.ru/ege/russkiy/demoversiya/",
    "https://eksamio.ru/ege/fizika/demoversiya/",
    "https://eksamio.ru/ege/khimiya/demoversiya/",
    "https://eksamio.ru/ege/matematika-baza/demoversiya/",
    "https://eksamio.ru/ege/matematika-profil/demoversiya/",
    "https://eksamio.ru/ege/obshchestvoznaniye/demoversiya/",
]
for url in required_urls:
    if url not in footer:
        raise SystemExit(f"Footer missing {url}")
    if url not in catalog:
        raise SystemExit(f"Catalog missing {url}")

if "Для нового предмета скопируйте" in catalog:
    raise SystemExit("Technical placeholder remains in catalog")
if catalog.count('<article class="ed-subject ') != 6:
    raise SystemExit("Catalog must contain exactly six subject cards")

footer_path.write_text(footer, encoding="utf-8", newline="\n")
catalog_path.write_text(catalog, encoding="utf-8", newline="\n")
print("Updated footer and demo catalog")
