"""Subprocess test for the Bash installer's harness-aware next-steps (Option C).

general-edition/setup.sh prints a "Next steps" block ONLY when run standalone;
when the top-level installer launches it (UMS_PARENT=1) it suppresses the block
so the parent owns the single harness-correct summary. The standalone block must
be harness-neutral — never the old "Run: claude" Claude-Code assumption.

This is the suite's only bash-subprocess test; the rest are pure-Python. It is
skip-aware: it runs where a clean bash exists (CI ubuntu + Git Bash on Windows)
and skips otherwise. It deliberately avoids the Windows System32 `bash.exe` WSL
shim, which can hang under a non-interactive subprocess.
"""

import os
import pathlib
import shutil
import subprocess

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
SETUP_SH = PKG / "general-edition" / "setup.sh"


def _find_bash():
    # Prefer a real bash. On Windows, skip the System32 WSL shim (hang risk) and
    # fall back to the common Git Bash locations.
    w = shutil.which("bash")
    if w and "system32" not in w.lower():
        return w
    for c in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        "/bin/bash",
        "/usr/bin/bash",
    ):
        if pathlib.Path(c).exists():
            return c
    return None


BASH = _find_bash()

pytestmark = pytest.mark.skipif(
    BASH is None or not SETUP_SH.exists(),
    reason="no usable bash (or setup.sh missing) — covered on CI ubuntu",
)


def _run_setup(working_dir, parented):
    env = {k: v for k, v in os.environ.items() if k != "UMS_PARENT"}
    env["WORKING_DIR"] = str(working_dir)
    if parented:
        env["UMS_PARENT"] = "1"
    return subprocess.run(
        [BASH, str(SETUP_SH), "--compliance=none", "--skip-wizard"],
        capture_output=True,
        text=True,
        encoding="utf-8",  # setup.sh emits UTF-8 glyphs; don't decode as the Windows cp1252 locale
        errors="replace",
        env=env,
        cwd=str(PKG),
        timeout=120,
    )


def test_setup_sh_nextsteps_suppressed_when_parented(tmp_path):
    r = _run_setup(tmp_path, parented=True)
    assert r.returncode == 0, r.stdout + r.stderr
    # Parent owns the summary — the edition block (and "Run: claude") is suppressed.
    assert "Next steps" not in r.stdout
    assert "Run: claude" not in r.stdout


def test_setup_sh_nextsteps_neutral_when_standalone(tmp_path):
    r = _run_setup(tmp_path, parented=False)
    assert r.returncode == 0, r.stdout + r.stderr
    # Standalone prints next steps, harness-neutral — never the old Claude assumption.
    assert "Run: claude" not in r.stdout
    assert "your agent" in r.stdout.lower()
