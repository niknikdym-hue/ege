# Physics 2022 final Tilda build

Deterministic, source-faithful Tilda package for the official FIPI Physics 2022 demo.

- Authority: tracked PDFs in `ege-source-fizika/source-fizika-2022/`.
- Tasks: 30 total; short answers 1–23; extended answers 24–30.
- Official primary score: 34 + 20 = 54.
- Task and criteria content is rasterized directly from the official demo PDF; reconstructed task text is not used.
- Task 30 displays official example 1 (the first task numbered 30 in the FIPI demo) and its matching solution/criteria. The second official alternative is not mixed into the card.
- Tasks 28–30 use a dedicated 1000 px / WebP quality 90 source-native HQ profile.
- Every task shows `ФИПИ 2022 · официальный пример N`.
- The package emits 41 ordered T123 blocks, each below 42,500 bytes.
- The archive includes `ege-fizika-demoversiya-2022-SEO.txt` with exact Tilda SEO settings for the 2022 route.

Build:

```bash
python physics-2022-final-build/build_physics_2022_compact.py
```

Verify after installing Playwright Chromium:

```bash
python physics-2022-final-build/verify_physics_2022_v1_0.py
```

The ready tracked archive is:

`physics-2022-final-build/dist/ege-fizika-demoversiya-2022-v1.0-TILDA-HQ-SOURCE.zip`
