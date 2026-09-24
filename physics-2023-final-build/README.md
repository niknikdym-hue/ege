# Physics 2023 final Tilda build

Deterministic, source-faithful Tilda package for the official FIPI Physics 2023 demo.

- Authority: tracked PDFs in `ege-source-fizika/source-fizika-2023/`.
- Tasks: 30 total; short answers 1–23; extended answers 24–30.
- Official primary score: 34 + 20 = 54.
- Production task and criteria content is rasterized directly from the official demo PDF; no reconstructed task text is used.
- Task 30 displays official example 1 (the first task numbered 30 in the FIPI demo) and its matching solution/criteria; the alternative after «ИЛИ» is not mixed into the card.
- Tasks 28–30 use a dedicated 1000 px / WebP quality 90 source-native HQ profile.
- The current package emits 40 ordered T123 blocks, each below 42,500 bytes.
- The archive includes `ege-fizika-demoversiya-2023-SEO.txt` with exact Tilda SEO settings for the 2023 route.

Build:

```bash
python physics-2023-final-build/build_physics_2023_compact.py
```

Verify after installing Playwright Chromium:

```bash
python physics-2023-final-build/verify_physics_2023_v1_0.py
```

The ready tracked archive is:

`physics-2023-final-build/dist/ege-fizika-demoversiya-2023-v1.0-TILDA-HQ-SOURCE.zip`
