"""Tests for the install-skill Step-0 unsafe-location guard (SKILL.md).

The guard is a bash snippet the skill runs before any write; it refuses to
install into `$HOME` or a system directory. v3.6.2 hardens it to canonicalize
paths (`pwd -P`) so a path that logically isn't `$HOME` but physically resolves
into it (e.g. through a symlink) is refused too. The snippet is extracted from
SKILL.md and exercised directly — the documented guard IS the unit under test.

Note on fixtures: pytest's tmp_path lives under /tmp (Git Bash maps %TEMP% ->
/tmp; CI uses the real /tmp), which the guard refuses by design — so it cannot
host an "allowed" case. The behavioral tests use a scratch dir under the repo
(neither /tmp nor the guard's overridden $HOME) and clean it up.

The structural check (`pwd -P` present) runs everywhere. Behavioral checks need
a clean bash; the symlink case additionally needs OS symlink support (CI ubuntu)
and skips where unavailable (e.g. Git Bash on Windows without developer mode).
"""

import os
import pathlib
import re
import shutil
import subprocess

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
SKILL_MD = PKG / "skills" / "install-ultimate-memory-stack" / "SKILL.md"


def _find_bash():
    w = shutil.which("bash")
    if w and "system32" not in w.lower():
        return w
    for c in (r"C:\Program Files\Git\bin\bash.exe",
              r"C:\Program Files\Git\usr\bin\bash.exe",
              "/bin/bash", "/usr/bin/bash"):
        if pathlib.Path(c).exists():
            return c
    return None


def _extract_guard():
    text = SKILL_MD.read_text(encoding="utf-8")
    for m in re.finditer(r"```bash\n(.*?)```", text, re.DOTALL):
        block = m.group(1)
        if "REFUSE" in block and "esac" in block:
            return block
    return None


BASH = _find_bash()
GUARD = _extract_guard()
bashmark = pytest.mark.skipif(BASH is None or GUARD is None,
                              reason="no usable bash / guard — covered on CI ubuntu")


def _posix(p):
    return pathlib.Path(p).as_posix()


def _run_guard(cd_target, home):
    # cd INTO the target inside bash (so the logical $PWD is the cd target, which
    # is what the guard must canonicalize), then run the extracted guard verbatim.
    script = f'cd "{_posix(cd_target)}" || exit 9\n{GUARD}'
    env = dict(os.environ)
    env["HOME"] = _posix(home)
    r = subprocess.run(
        [BASH, "-c", script],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, timeout=30,
    )
    return r.stdout.strip()


def _symlinks_work(base):
    base.mkdir(parents=True, exist_ok=True)
    real = base / "_real"
    real.mkdir()
    try:
        os.symlink(real, base / "_link")
        return (base / "_link").is_symlink()
    except (OSError, NotImplementedError):
        return False


@pytest.fixture
def safe_base():
    base = PKG / "tests" / "_guard_scratch"
    if base.exists():
        shutil.rmtree(base, ignore_errors=True)
    base.mkdir()
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)


# --------------------------------------------------------------------------
# Structural — the hardening is present in the documented guard (runs anywhere)
# --------------------------------------------------------------------------

@pytest.mark.skipif(GUARD is None, reason="Step-0 guard not found in SKILL.md")
def test_guard_canonicalizes_before_matching():
    # pwd -P resolves symlinks before the case-match — the core v3.6.2 hardening.
    assert "pwd -P" in GUARD
    # and the refusal set is intact
    assert "REFUSE" in GUARD
    assert "/etc/*" in GUARD


# --------------------------------------------------------------------------
# Behavioral — run the extracted guard (need bash; scratch dir under the repo)
# --------------------------------------------------------------------------

@bashmark
def test_guard_refuses_home(safe_base):
    home = safe_base / "home"
    home.mkdir()
    assert _run_guard(home, home) == "REFUSE"


@bashmark
def test_guard_allows_project_dir(safe_base):
    home = safe_base / "home"
    proj = home / "projects" / "app"
    proj.mkdir(parents=True)
    # A project dir UNDER $HOME is fine — only the bare $HOME (and system dirs)
    # is refused.
    assert _run_guard(proj, home) == "OK"


@bashmark
def test_guard_refuses_symlink_resolving_into_home(safe_base):
    if not _symlinks_work(safe_base / "probe"):
        pytest.skip("OS symlink support unavailable (CI ubuntu covers this case)")
    home = safe_base / "home"
    home.mkdir()
    link = safe_base / "link"
    os.symlink(home, link)  # logical path 'link' != physical 'home'
    # Old guard matched the logical $PWD (link) -> OK (escape). Hardened guard
    # canonicalizes to 'home' -> REFUSE.
    assert _run_guard(link, home) == "REFUSE"
