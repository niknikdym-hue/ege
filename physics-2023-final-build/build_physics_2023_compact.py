#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("physics2023_builder", HERE / "build_physics_2023.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load Physics 2023 builder")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def compact_webp_bytes(image: Image.Image, max_width: int = 1000):
    output = image.convert("L")
    # The 2023 demo contains 30 task regions and 22 criteria regions.  This
    # bounded grayscale profile keeps all source text legible while fitting
    # the complete package into a practical 43 T123 blocks.
    max_width = min(max_width, 580)
    if output.width > max_width:
        height = round(output.height * max_width / output.width)
        output = output.resize((max_width, height), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    output.save(buf, format="WEBP", quality=48, method=6)
    return buf.getvalue(), output


builder.webp_bytes = compact_webp_bytes
builder.MAX_T123_COUNT = 48
builder.main()
