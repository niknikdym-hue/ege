# Physics 2024 source access pack

`PHYSICS-2024-SOURCE-ACCESS.zip` is derived review/access evidence, not source authority.

The canonical source authority remains:

`ege-source-fizika/source-fizika-2024/`

The ZIP contains byte-identical copies of the tracked official FIPI 2024 source files together with derived review evidence.

ZIP SHA-256:

`7634e9a0397137fd87e28fafbcf6a7fc2707ccf70cb57882c96bc2b82837ab8a`

## Materialized review evidence

The canonical source authority remains `ege-source-fizika/source-fizika-2024/`.

`materialized/` contains deterministic derived review evidence only. No derived file replaces an official FIPI PDF.

Canonical source SHA-256 values:

- Demo: `746903cadd391a52948aea59155f713c7677521ba22b52c369d2473fb0fc2057`
- Specification: `f4703bbe704c0220e44faca64cb1fe834fc06c5eeab21d57f6f428e2b3bd775c`
- Codifier: `bc4c1ee2a603572e5342227a8c90aa34a772a22cc750164c443f4921c4eeca30`

The demo and specification full-page PNGs were rendered at 200 DPI with Poppler `pdftoppm 26.05.0`, preserving the complete page canvas without crop or post-render resampling. Layout-preserving text was generated with `pdftotext 26.05.0`; the demo also has bbox-layout extraction and `pdfimages -list` inspection evidence.

Subject review should use `demo-pages/` and `specification-pages/` for page-by-page inspection, `demo-contact-sheet.png` only for navigation, and `text/` plus `layout/demo-bbox.html` to identify physical pages, text boundaries, slots, page transitions, and future crop coordinates. Task answers, crop decisions, scoring, and subject interpretation are outside this materialization.

All materialized outputs can be regenerated from the tracked canonical source using `materialized/generate-materialization.py`. Two clean runs produced byte-identical deterministic outputs; see `materialized/DETERMINISM-TWICE.txt` and `materialized/OUTPUT-SHA256SUMS.txt`.
