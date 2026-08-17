# VISUAL UI CROP AUDIT — обязательный шаблон для демоверсий

Этот шаблон используется **для каждого официального visual asset отдельно**. Source fidelity и UI crop quality — разные gates: точный source crop может быть интерфейсно непригодным, если он обрезает подписи или захватывает лишний соседний блок.

## Запись на один asset

- `YEAR:`
- `EXAM:` ЕГЭ
- `LEVEL:` база / профиль
- `TASK:`
- `OFFICIAL_VARIANT:`
- `ASSET_ID:`
- `SOURCE_PDF:`
- `SOURCE_PDF_SHA256:`
- `PRINTED_PAGE:`
- `PHYSICAL_PDF_PAGE:`
- `PAGE_HALF:` left / right / full / n/a
- `CROP_RECT:` x1,y1,x2,y2
- `SOURCE_ORIGIN_PROOF:`

### Four-edge / completeness check

- `TOP_EDGE_COMPLETE:` YES/NO/N-A
- `RIGHT_EDGE_COMPLETE:` YES/NO/N-A
- `BOTTOM_EDGE_COMPLETE:` YES/NO/N-A
- `LEFT_EDGE_COMPLETE:` YES/NO/N-A
- `AXES_COMPLETE:` YES/NO/N-A
- `AXIS_LABELS_COMPLETE:` YES/NO/N-A
- `TICKS_NUMBERS_COMPLETE:` YES/NO/N-A
- `UNITS_COMPLETE:` YES/NO/N-A
- `LEGEND_COMPLETE:` YES/NO/N-A
- `POINT_VERTEX_LABELS_COMPLETE:` YES/NO/N-A
- `DIMENSIONS_COMPLETE:` YES/NO/N-A
- `NO_MEANINGFUL_CONTENT_CUT:` YES/NO

### Content boundary decision

- `UNRELATED_NEIGHBOR_CONTENT_INCLUDED:` YES/NO
- `COMPANION_TABLE_OR_CHARACTERISTICS:` none / separate-source-crop / exact-HTML-from-source / intentionally-same-crop
- `BOUNDARY_DECISION_REASON:`

Нельзя оставлять в рисунке случайно захваченные характеристики, таблицу или соседнее условие только потому, что они находятся рядом на странице PDF. Нельзя и вырезать их, если без них рисунок теряет смысл. Решение принимается по конкретному официальному примеру.

### Interface sizing

- `DESKTOP_TARGET_WIDTH:`
- `TABLET_TARGET_WIDTH:`
- `MOBILE_BEHAVIOR:` fit / horizontal-scroll / zoom-required
- `ZOOM_REQUIRED:` YES/NO
- `ZOOM_IN_TESTED:` YES/NO/N-A
- `ZOOM_OUT_TESTED:` YES/NO/N-A
- `ZOOM_RESET_TESTED:` YES/NO/N-A
- `MOBILE_ZOOM_TESTED:` YES/NO/N-A
- `READABLE_1280:` YES/NO
- `READABLE_768:` YES/NO
- `READABLE_390:` YES/NO
- `READABLE_360:` YES/NO
- `READABLE_320:` YES/NO

### Final proof

- `SOURCE_PIXEL_FIDELITY:` PASS/FAIL
- `T123_EMBEDDED_BYTES_MATCH:` PASS/FAIL/N-A
- `TASK_REFERENCE_MATCH:` PASS/FAIL
- `VISUAL_UI_CROP_GATE:` PASS/FAIL
- `EVIDENCE:`
- `NOTES:`

## PASS rule

`VISUAL_UI_CROP_GATE = PASS` разрешён только если asset доказуемо происходит из официального PDF нужного года; ни один смысловой элемент не обрезан; нет случайно захваченного соседнего содержания; подписи/оси/единицы/обозначения читаемы; размер выбран по специфике asset; крупный visual имеет рабочий zoom; desktop/mobile проверки пройдены.

Нельзя закрывать весь год одним общим утверждением «картинки проверены». Нужна отдельная запись на каждый asset.
