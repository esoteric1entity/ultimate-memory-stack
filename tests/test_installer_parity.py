"""Installer parity pinning test.

general-edition/setup.sh and setup.py duplicate copy/write logic by design —
the plan's §1 explicitly REJECTED consolidating them (the Bash door's value
is exactly that it needs no Python; a shared declarative op-list is a new
abstraction with its own drift risk). What the punchlist amendment (train
step 2) already fixed were three confirmed divergences between the two; this
test pins them so future drift is caught immediately instead of silently
accumulating. A FOURTH divergence (audit-log initialization missing
`actor_session`/`entry_path`/`entry_category` in Bash, plus a Python-list-repr
bug in the summary text) was found while writing this test — fixed alongside
it in setup.py/setup.sh (see SCHEMA_audit_log.md's canonical-format section).

Sensitivity proof (plan §5 acceptance, "verify once, revert"): the
extensions-write regression this test would have caught pre-punchlist was
manually re-introduced against a scratch-restored copy of setup.sh and
confirmed to make test_same_user_overrides_effective_values fail, then
reverted — not committed as a permanent test (that would require keeping a
brittle source-text marker in sync with setup.sh indefinitely for no
ongoing benefit; the real fixed-forever regression coverage is this file's
other tests running against the current shipped installers every time).
"""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
SETUP_PY = PKG / "general-edition" / "setup.py"
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
    BASH is None or not SETUP_SH.exists() or not SETUP_PY.exists(),
    reason="no usable bash (or an installer is missing) — must run in the "
           "project's normal dev environment (Git Bash present); covered on CI ubuntu",
)


def _install_py(target, compliance="enterprise", extensions="gdpr"):
    return subprocess.run(
        [sys.executable, str(SETUP_PY), "--working-dir", str(target),
         "--compliance", compliance, "--extensions", extensions],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )


def _install_sh(target, compliance="enterprise", extensions="gdpr"):
    env = dict(os.environ)
    env["WORKING_DIR"] = str(target)
    return subprocess.run(
        [BASH, str(SETUP_SH), f"--compliance={compliance}", f"--extensions={extensions}", "--skip-wizard"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=60,
    )


def _relative_file_set(root):
    return {
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }


@pytest.fixture
def parity_pair(tmp_path):
    py_dir = tmp_path / "py"
    sh_dir = tmp_path / "sh"
    py_dir.mkdir()
    sh_dir.mkdir()
    r_py = _install_py(py_dir)
    assert r_py.returncode == 0, r_py.stdout + r_py.stderr
    r_sh = _install_sh(sh_dir)
    assert r_sh.returncode == 0, r_sh.stdout + r_sh.stderr
    return py_dir, sh_dir


def test_same_file_set(parity_pair):
    py_dir, sh_dir = parity_pair
    assert _relative_file_set(py_dir) == _relative_file_set(sh_dir)


def test_same_profile_md(parity_pair):
    # PROFILE.md is fully regenerable (v4.0.0 overrides pattern) — always the
    # shipped default, so this should be byte-identical regardless of flags.
    py_dir, sh_dir = parity_pair
    py_profile = (py_dir / "ultimate-memory-stack" / "general-edition" / "PROFILE.md").read_text(encoding="utf-8")
    sh_profile = (sh_dir / "ultimate-memory-stack" / "general-edition" / "PROFILE.md").read_text(encoding="utf-8")
    assert py_profile == sh_profile


def test_same_user_overrides_effective_values(parity_pair):
    # The ACTUAL effective compliance/extensions values live here post-v4.0.0
    # (the v4.0.0 overrides pattern moved them out of PROFILE.md).
    py_dir, sh_dir = parity_pair
    py_ov = (py_dir / "memory" / "user" / "USER_OVERRIDES.md").read_text(encoding="utf-8")
    sh_ov = (sh_dir / "memory" / "user" / "USER_OVERRIDES.md").read_text(encoding="utf-8")
    # Normalize the one genuinely inert diff: created_at (today's date, not a value).
    norm = lambda s: re.sub(r"^created_at: .*$", "created_at: <normalized>", s, flags=re.MULTILINE)
    assert norm(py_ov) == norm(sh_ov)
    assert "compliance: enterprise" in py_ov
    assert "  - gdpr" in py_ov


def test_same_audit_log_initialization(parity_pair):
    py_dir, sh_dir = parity_pair
    py_line = (py_dir / "memory" / "security" / "audit_log.jsonl").read_text(encoding="utf-8").strip()
    sh_line = (sh_dir / "memory" / "security" / "audit_log.jsonl").read_text(encoding="utf-8").strip()
    # Normalize the one genuinely inert diff: ts (a timestamp).
    norm = lambda s: re.sub(r'"ts":"[^"]*"', '"ts":"<normalized>"', s)
    assert norm(py_line) == norm(sh_line)
    assert '"actor_session":0' in py_line
    assert '"entry_path":"memory/"' in py_line
    assert '"entry_category":"system"' in py_line


def test_same_gitignore_block_in_a_git_repo(tmp_path):
    # ensure_gitignore() only fires inside a git repo — exercise that path.
    py_dir = tmp_path / "py"
    sh_dir = tmp_path / "sh"
    py_dir.mkdir()
    sh_dir.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=py_dir, check=True, timeout=30)
    subprocess.run(["git", "init", "-q"], cwd=sh_dir, check=True, timeout=30)
    r_py = _install_py(py_dir)
    assert r_py.returncode == 0, r_py.stdout + r_py.stderr
    r_sh = _install_sh(sh_dir)
    assert r_sh.returncode == 0, r_sh.stdout + r_sh.stderr

    py_gi = (py_dir / ".gitignore").read_text(encoding="utf-8")
    sh_gi = (sh_dir / ".gitignore").read_text(encoding="utf-8")
    assert py_gi == sh_gi
    assert "ultimate-memory-stack/" in py_gi


def test_same_deployment_info_field_for_field(parity_pair):
    py_dir, sh_dir = parity_pair
    py_di = (py_dir / ".deployment-info").read_text(encoding="utf-8")
    sh_di = (sh_dir / ".deployment-info").read_text(encoding="utf-8")

    def parse(text):
        fields = {}
        for line in text.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
        return fields

    py_fields = parse(py_di)
    sh_fields = parse(sh_di)
    # Genuinely inert diffs, normalized explicitly (not loosened assertions):
    # deployment_path (different sandbox dirs) and installed_at (a timestamp).
    for inert in ("deployment_path", "installed_at"):
        py_fields.pop(inert, None)
        sh_fields.pop(inert, None)
    assert py_fields == sh_fields
    # The unified comma-string extensions format (punchlist amendment 3.2e) —
    # assert it explicitly, don't just normalize it away.
    assert py_fields["extensions"] == "gdpr"
