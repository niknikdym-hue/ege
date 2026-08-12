#!/usr/bin/env python3
"""Run dependency-free Node tests for the standalone Exceptions browser core.

The test suite reads the current generated runtime/T123 chunks and compares the
JavaScript selector against the accepted Python reference implementation. It does
not write production data or localStorage.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    node = shutil.which("node")
    if not node:
        print("BROWSER CORE TEST ERROR: Node.js is required for browser-core validation.", file=sys.stderr)
        return 2
    script = root / "standalone-exceptions-trainer" / "tests" / "test-core.js"
    if not script.is_file():
        print(f"BROWSER CORE TEST ERROR: missing {script}", file=sys.stderr)
        return 2
    proc = subprocess.run([node, str(script)], cwd=str(root), text=True, encoding="utf-8", errors="replace", check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
