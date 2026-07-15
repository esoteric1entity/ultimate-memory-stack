"""Subprocess tests for verify.sh's [T8] manifest <-> registered-skills
cross-check (PLAN-refactor-structural Part C — additive, informational only,
never touches EXIT_CODE).

Exercises the plan's 4 acceptance scenarios (§4) against the REAL
setup-memory-stack.sh wrapper (the only writer of .ums-manifest.json),
general-edition/setup.py (a manifest-less door), and the REAL verify.sh — not
a synthetic fixture. Mirrors the bash-subprocess pattern in
test_setup_sh_nextsteps.py (the suite's other bash-subprocess tests).
"""

import pathlib
import shutil
import subprocess
import sys

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
SETUP_WRAPPER = PKG / "setup-memory-stack.sh"
SETUP_PY = PKG / "general-edition" / "setup.py"
VERIFY_SH = PKG / "verify.sh"


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
    BASH is None or not SETUP_WRAPPER.exists() or not VERIFY_SH.exists(),
    reason="no usable bash (or scripts missing) — covered on CI ubuntu",
)


def _install_with_addon(target):
    return subprocess.run(
        [
            BASH, str(SETUP_WRAPPER),
            "--target", str(target),
            "--addon", "memory-llmlingua",
            "--yes",
            "--edition", "general",
            "--compliance=none",
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120,
    )


def _install_without_manifest(target):
    return subprocess.run(
        [sys.executable, str(SETUP_PY), "--working-dir", str(target), "--compliance", "none"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )


def _run_verify(target):
    return subprocess.run(
        [BASH, str(VERIFY_SH), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60,
    )


def test_t8_passes_with_matching_addon(tmp_path):
    r = _install_with_addon(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / ".ums-manifest.json").exists()

    v = _run_verify(tmp_path)
    assert v.returncode == 0, v.stdout + v.stderr
    assert "[T8]" in v.stdout
    assert "memory-llmlingua → matching skill found" in v.stdout


def test_t8_warns_on_fake_addon_without_failing(tmp_path):
    r = _install_with_addon(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    manifest = tmp_path / ".ums-manifest.json"
    content = manifest.read_text(encoding="utf-8")
    content = content.replace(
        '"addons": ["memory-llmlingua"]',
        '"addons": ["memory-llmlingua", "memory-totally-fake-addon"]',
    )
    manifest.write_text(content, encoding="utf-8")

    v = _run_verify(tmp_path)
    assert v.returncode == 0, v.stdout + v.stderr  # WARN, never fail
    assert "memory-totally-fake-addon" in v.stdout
    assert "no matching registered skill found" in v.stdout


def test_t8_absent_when_no_manifest(tmp_path):
    r = _install_without_manifest(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (tmp_path / ".ums-manifest.json").exists()

    v = _run_verify(tmp_path)
    assert v.returncode == 0, v.stdout + v.stderr
    assert "[T8]" not in v.stdout


def test_t8_passes_silently_with_empty_addons_array(tmp_path):
    r = _install_without_manifest(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    manifest = tmp_path / ".ums-manifest.json"
    manifest.write_text(
        '{\n  "package": "ultimate-memory-stack",\n  "addons": [],\n  "minimal": true\n}\n',
        encoding="utf-8",
    )

    v = _run_verify(tmp_path)
    assert v.returncode == 0, v.stdout + v.stderr
    assert "0 addon(s) listed in manifest" in v.stdout
