from __future__ import annotations

import importlib.util
from pathlib import Path


def load_command_verify():
    path = Path(__file__).resolve().parents[1] / "project-control" / "owner_control_command_verify.py"
    spec = importlib.util.spec_from_file_location("owner_control_command_verify", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load owner_control_command_verify")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
