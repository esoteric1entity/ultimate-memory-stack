#!/usr/bin/env python3
"""Compat shim — moved to core/shared-tools/lint_runner.py in v4.0.0 (it's
cross-harness shared tooling, not adapter-specific). Kept here so existing
installed vaults and old docs keep working (deprecate-never-delete rule).
Do not add logic here — edit the real file at the new location."""
import sys
from pathlib import Path
from runpy import run_path

print(
    "[lint_runner] NOTE: this is a compat shim — the real tool now lives at "
    "core/shared-tools/lint_runner.py (moved in v4.0.0)",
    file=sys.stderr,
)
_target = Path(__file__).resolve().parent.parent.parent / "shared-tools" / "lint_runner.py"
run_path(str(_target), run_name="__main__")
