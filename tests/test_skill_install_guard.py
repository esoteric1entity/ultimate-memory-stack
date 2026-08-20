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


# --------------------------------------------------------------------------- #
# Addon payload completeness (2026-08-19).
#
# v4.0.0 shipped every pip addon with its own documented install procedure
# impossible to follow: the installers copied ONLY SKILL.md into
# .claude/skills/<name>/, while the skills instruct the user to run
#     pip install -r <path-to-this-skill>/requirements.txt
#     pip-audit  --requirement <path-to-this-skill>/requirements.txt
#     python                   <path-to-this-skill>/smoke_test.py
# against files that were never installed. Nothing caught it because no test
# had ever inspected an INSTALLED addon skill for the files its own text cites.
#
# This test derives its expectations FROM the SKILL.md text, so it cannot go
# stale: add a new `<path-to-this-skill>/thing` reference to any skill and this
# starts requiring `thing` to be installed.
# --------------------------------------------------------------------------- #

ADDON_DIRS = sorted(
    p for p in (PKG / "recommended-addons").iterdir()
    if p.is_dir() and (p / "SKILL.md").is_file()
)

# `<path-to-this-skill>/requirements.txt`, `<path-to-skill>/smoke_test.py`, etc.
SELF_REF = re.compile(r"<path[- ]to[- ](?:this[- ])?skill>/([A-Za-z0-9_.\-/]+)")


def _referenced_files(skill_md: pathlib.Path) -> set[str]:
    text = skill_md.read_text(encoding="utf-8")
    return {m.group(1).rstrip(".,;:)") for m in SELF_REF.finditer(text)}


# Files a skill may cite that live once in recommended-addons/ and are copied
# into each installed skill directory by the installers, rather than being
# duplicated per add-on in the source tree.
INSTALLER_PROVIDED = {"preflight.py": PKG / "recommended-addons" / "preflight.py"}


@pytest.mark.parametrize("addon_dir", ADDON_DIRS, ids=lambda p: p.name)
def test_every_self_referenced_file_exists_in_the_source_addon(addon_dir):
    """Whatever a SKILL.md tells the user to run must exist in the package —
    either in the add-on's own directory, or as shared tooling the installer
    injects (INSTALLER_PROVIDED). The installed-side test below is what proves
    the shared ones actually arrive."""
    missing = []
    for ref in _referenced_files(addon_dir / "SKILL.md"):
        if (addon_dir / ref).exists():
            continue
        shared = INSTALLER_PROVIDED.get(ref)
        if shared is not None and shared.exists():
            continue
        missing.append(ref)
    assert not sorted(missing), f"{addon_dir.name}/SKILL.md cites missing file(s): {sorted(missing)}"


@pytest.mark.parametrize("addon_dir", ADDON_DIRS, ids=lambda p: p.name)
def test_installer_copies_every_self_referenced_file(addon_dir, tmp_path):
    """NEGATIVE CONTROL for the copy-only-SKILL.md bug: run the real installer
    and assert the installed skill directory contains every file its own
    SKILL.md tells the user to run."""
    bash = _find_bash()
    if bash is None:
        pytest.skip("no usable bash")

    referenced = _referenced_files(addon_dir / "SKILL.md")
    if not referenced:
        pytest.skip(f"{addon_dir.name} cites no bundled files")

    target = tmp_path / "vault"
    target.mkdir()
    r = subprocess.run(
        [bash, str(PKG / "setup-memory-stack.sh"), "--skip-wizard",
         "--compliance=none", "--target", str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
    )
    assert r.returncode == 0, r.stdout + r.stderr

    skill_name = re.search(r"^name:\s*(.+)$",
                           (addon_dir / "SKILL.md").read_text(encoding="utf-8"),
                           re.MULTILINE).group(1).strip()
    installed = target / ".claude" / "skills" / skill_name
    assert installed.is_dir(), f"{skill_name} not installed at {installed}"

    missing = sorted(r for r in referenced if not (installed / r).exists())
    assert not missing, (
        f"{skill_name}: SKILL.md tells the user to use {missing}, "
        f"but the installer did not place them. Installed: "
        f"{sorted(p.name for p in installed.iterdir())}"
    )


def _find_powershell():
    """Locate a PowerShell host — but ONLY on Windows.

    Gating on "is PowerShell installed" is wrong: GitHub's ubuntu-latest and
    macos-latest runners ship PowerShell Core, so a bare `shutil.which("pwsh")`
    finds it and the test then runs a Windows installer on Linux (`$env:USERPROFILE`
    undefined, backslash paths) and fails the unit-tests job on every non-Windows
    leg. setup-memory-stack.ps1 is the WINDOWS door; the platform is the gate,
    not the interpreter's presence.
    """
    if os.name != "nt":
        return None
    for c in ("powershell", "pwsh"):
        w = shutil.which(c)
        if w:
            return w
    for c in (r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",):
        if pathlib.Path(c).exists():
            return c
    return None


@pytest.mark.parametrize("addon_dir", ADDON_DIRS, ids=lambda p: p.name)
def test_powershell_installer_copies_the_same_payload(addon_dir, tmp_path):
    """Parity guard for setup-memory-stack.ps1.

    The bash test above covered only ONE of the two installers. The PowerShell
    copy block is a hand-written parallel — different filter semantics, different
    path handling — so 'the bash one works' is not evidence about it. A Windows
    user taking the PowerShell door is exactly who the original copy-only-SKILL.md
    bug hurt, and nothing verified that door until this test.
    """
    ps = _find_powershell()
    if ps is None:
        pytest.skip("not Windows — the PowerShell door is covered on CI windows-latest")

    referenced = _referenced_files(addon_dir / "SKILL.md")
    if not referenced:
        pytest.skip(f"{addon_dir.name} cites no bundled files")

    target = tmp_path / "vault"
    target.mkdir()
    r = subprocess.run(
        [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(PKG / "setup-memory-stack.ps1"),
         "-SkipWizard", "-Compliance", "none", "-Target", str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
    )
    assert r.returncode == 0, r.stdout + r.stderr

    skill_name = re.search(r"^name:\s*(.+)$",
                           (addon_dir / "SKILL.md").read_text(encoding="utf-8"),
                           re.MULTILINE).group(1).strip()
    installed = target / ".claude" / "skills" / skill_name
    assert installed.is_dir(), f"{skill_name} not installed at {installed}"

    missing = sorted(r_ for r_ in referenced
                     if not (installed / r_).exists()
                     and r_ not in INSTALLER_PROVIDED)
    shared_missing = sorted(r_ for r_ in referenced
                            if r_ in INSTALLER_PROVIDED and not (installed / r_).exists())
    assert not missing and not shared_missing, (
        f"{skill_name} (PowerShell door): missing {missing + shared_missing}. "
        f"Installed: {sorted(p.name for p in installed.iterdir())}"
    )


def test_powershell_installer_reports_the_real_target(tmp_path):
    """Regression: the addon copy loop must not clobber the script's own $Target.

    PowerShell variables are CASE-INSENSITIVE and a ForEach-Object script block
    runs in the CALLER's scope, so a loop variable named `$target` silently
    overwrote `$Target` (the install directory) with the last copied file's path.
    Everything after the loop then used a lockfile path as the workspace: the
    post-install protocol copy, the "Workspace:" summary, and the verify.sh
    command printed for the user — which would fail if they ran it.

    Nothing caught this. The payload test passes either way (the payload is
    copied BEFORE the corruption matters) and verify.sh passes because the
    install itself is driven by $env:WORKING_DIR, set before the loop. Only the
    user-facing output was wrong, which is exactly why it needs a test.
    """
    ps = _find_powershell()
    if ps is None:
        pytest.skip("not Windows — the PowerShell door is covered on CI windows-latest")

    target = tmp_path / "vault"
    target.mkdir()
    r = subprocess.run(
        [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(PKG / "setup-memory-stack.ps1"),
         "-SkipWizard", "-Compliance", "none", "-Target", str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
    )
    assert r.returncode == 0, r.stdout + r.stderr

    workspace_lines = [ln for ln in r.stdout.splitlines() if "Workspace:" in ln]
    assert workspace_lines, f"no Workspace: line in installer output:\n{r.stdout}"
    reported = workspace_lines[0].split("Workspace:", 1)[1].strip()
    assert pathlib.Path(reported).resolve() == target.resolve(), (
        f"installer reported workspace {reported!r}, expected {str(target)!r} — "
        "a loop variable has clobbered $Target"
    )
    # The path it tells the user to validate must be the vault, not a file.
    assert ".lock" not in reported and pathlib.Path(reported).is_dir()
