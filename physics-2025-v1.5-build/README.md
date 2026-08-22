# Physics 2025 v1.5 bounded result-order build

This builder creates the versioned v1.5 candidate from the immutable accepted
v1.4 package. It changes only the result-page DOM composition and the two
renderer functions that separate tasks 1–20 from tasks 21–26.

```sh
python3 physics-2025-v1.5-build/build_v1_5.py
python3 physics-2025-v1.5-build/verify_v1_5.py
```

Tilda patch from deployed v1.4:

- HEAD: unchanged
- T123-01: replace
- T123-48: replace
- T123-02…T123-47: unchanged
