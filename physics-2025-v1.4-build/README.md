# Physics 2025 v1.4 bounded build

This directory deterministically builds the versioned v1.4 Tilda checkpoint from the immutable, tracked v1.3 directory. The script refuses to run unless the complete v1.3 tree inventory hashes to `4824df3e91e11a24d999ccc973f367150045a985b1f57e23adf0bb816155dc0e`.

From the repository root, with Python 3.12 and the pinned packages installed:

```sh
python3 -m pip install -r physics-2025-v1.4-build/requirements.txt
python3 physics-2025-v1.4-build/build_v1_4.py
python3 physics-2025-v1.4-build/verify_v1_4.py
```

The canonical output directory name is part of the ZIP entry paths. Keep the default output name when comparing ZIP hashes. The expected deterministic outputs are:

```text
OUTPUT_BUILD_SHA256=2780a729967e70355a8ae52e726c67abe8597dff3ce2d5b0c55da635791f2e13
OUTPUT_ZIP_SHA256=21a6fdeffa1696b5f134ce50eab10dd5b279c82764bfe5165ae3c50ab330c80d
```

The responsive harness creates exact-width iframe browsing contexts for 1280, 768, 390, 360, and 320 CSS pixels. It is test-only and does not alter the deployable package.
