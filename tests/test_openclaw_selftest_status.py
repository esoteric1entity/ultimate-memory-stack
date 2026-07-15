"""OpenClaw installer self-test tri-state handling + cross-door summary parity.

self_test.py's exit contract is 0=PASS, 2=CRITICAL, 3=WARN, 4=INFO — warn/info
are non-blocking ("adapter is usable"). setup-openclaw.sh always honored that;
setup-openclaw.py used to treat ANY non-zero as install failure, so every
fresh install (T5 warns — decisions.md/session_state.md/feedback.md are
created on first use, not at install) exited 4 and skipped its own Step-11
install log. These tests pin the fixed behavior on BOTH doors, including the
final-summary "Self-test:" label, which Bash previously hardcoded to "PASSED"
regardless of the actual outcome (even with self_test.py missing).

The two doors must print the IDENTICAL summary label for the same outcome —
each test asserts the same literal, which is the parity pin.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
SETUP_OPENCLAW_PY = PKG / "core" / "openclaw-adapter" / "scripts" / "setup-openclaw.py"
SETUP_OPENCLAW_SH = PKG / "core" / "openclaw-adapter" / "scripts" / "setup-openclaw.sh"

WARN_STEP_LINE = "PASSED with WARNINGS"
WARN_SUMMARY_LINE = "Self-test:            PASSED with warnings"


def _find_bash():
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


def test_python_door_fresh_install_warn_is_nonblocking(tmp_path):
    r = subprocess.run(
        [sys.executable, str(SETUP_OPENCLAW_PY), str(tmp_path), "--compliance", "none", "--no-cron"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert WARN_STEP_LINE in r.stdout            # step-10 line reflects the T5 warn
    assert WARN_SUMMARY_LINE in r.stdout         # summary label is honest, not a blanket PASSED
    # The warn must not have skipped Step 11's install log (the old bug's blast radius).
    decisions = tmp_path / "memory" / "decisions" / "decisions.md"
    assert decisions.exists() and "DEC-INSTALL" in decisions.read_text(encoding="utf-8")


@pytest.mark.skipif(BASH is None, reason="no usable bash — covered on CI ubuntu")
def test_bash_door_fresh_install_warn_summary_matches_python(tmp_path):
    r = subprocess.run(
        [BASH, str(SETUP_OPENCLAW_SH), str(tmp_path), "--compliance", "none", "--no-cron"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert WARN_STEP_LINE in r.stdout
    # Same literal the Python door prints — cross-door summary parity.
    assert WARN_SUMMARY_LINE in r.stdout
