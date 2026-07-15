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


def _run_setup(working_dir, parented, compliance="none", extensions=None, extra_args=None):
    env = {k: v for k, v in os.environ.items() if k != "UMS_PARENT"}
    env["WORKING_DIR"] = str(working_dir)
    if parented:
        env["UMS_PARENT"] = "1"
    args = [BASH, str(SETUP_SH), f"--compliance={compliance}", "--skip-wizard"]
    if extensions:
        args.append(f"--extensions={extensions}")
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args,
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


def test_setup_sh_compliance_custom_refused_on_stock_tree(tmp_path):
    # The complexity-floor gate must hold against the REAL shipped tree:
    # overrides/compliance.override.md is user-authored and does NOT ship,
    # so bare --compliance=custom is refused (documented footgun guard).
    # Guards against pointing the gate at the always-shipped
    # compliance-presets.override.md spec file, which would silently
    # disable the gate.
    r = _run_setup(tmp_path, parented=False, compliance="custom")
    assert r.returncode == 1, r.stdout + r.stderr
    assert "compliance.override.md" in r.stdout
    assert not (tmp_path / ".deployment-info").exists()


def test_setup_sh_extensions_written_to_user_overrides(tmp_path):
    # v4.0.0: compliance/extensions choices are USER choices — they land in
    # USER_OVERRIDES.md (create-once, never rewritten), not PROFILE.md, which
    # is now regenerable (PLAN-merge-on-install §3.4b).
    r = _run_setup(tmp_path, parented=False, compliance="enterprise", extensions="gdpr,soc2")
    assert r.returncode == 0, r.stdout + r.stderr
    overrides = tmp_path / "memory" / "user" / "USER_OVERRIDES.md"
    lines = overrides.read_text(encoding="utf-8").splitlines()
    assert "compliance: enterprise" in lines
    assert "extensions:" in lines
    idx = lines.index("extensions:")
    assert lines[idx + 1] == "  - gdpr"
    assert lines[idx + 2] == "  - soc2"
    assert lines.count("extensions:") == 1

    # PROFILE.md stays the shipped default — never edited by the installer.
    profile = tmp_path / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    assert "compliance: none" in profile.read_text(encoding="utf-8").splitlines()


def test_setup_sh_no_extensions_leaves_overrides_minimal(tmp_path):
    r = _run_setup(tmp_path, parented=False, compliance="none")
    assert r.returncode == 0, r.stdout + r.stderr
    overrides = tmp_path / "memory" / "user" / "USER_OVERRIDES.md"
    out = overrides.read_text(encoding="utf-8")
    assert "\ncompliance: none" not in out
    assert "\nextensions:" not in out


def test_setup_sh_reinstall_over_existing_no_longer_hard_refuses(tmp_path):
    # v4.0.0 (§3.4a): the old "common-specs already exists → exit 1, rm -rf
    # manually" hard refusal is replaced by unified archive-then-refresh.
    r1 = _run_setup(tmp_path, parented=False, compliance="none")
    assert r1.returncode == 0, r1.stdout + r1.stderr
    r2 = _run_setup(tmp_path, parented=False, compliance="enterprise")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "already exists" not in r2.stdout
    assert "wiping for clean install" in r2.stdout


def test_setup_sh_running_installed_copy_refuses_instead_of_destroying_common_specs(tmp_path):
    # CRITICAL finding (adversarial round, 2026-07-14): SCRIPT_DIR is wherever
    # the running script lives. Re-running the INSTALLED copy collapses
    # SCRIPT_DIR onto the install target — the "differs from shipped" cmp
    # compares the file to itself (archive never fires), then the wipe deletes
    # common-specs/ and tries to cp -r FROM the path it just deleted, crashing
    # and permanently destroying it. Must refuse before any of that runs.
    r1 = _run_setup(tmp_path, parented=False, compliance="none")
    assert r1.returncode == 0, r1.stdout + r1.stderr

    installed_setup_sh = tmp_path / "ultimate-memory-stack" / "general-edition" / "setup.sh"
    assert installed_setup_sh.exists()

    env = {k: v for k, v in os.environ.items() if k != "UMS_PARENT"}
    env["WORKING_DIR"] = str(tmp_path)
    r2 = subprocess.run(
        [BASH, str(installed_setup_sh)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(tmp_path), timeout=120,
    )
    assert r2.returncode == 1, r2.stdout + r2.stderr
    assert "INSTALLED copy" in r2.stdout
    assert (tmp_path / "ultimate-memory-stack" / "common-specs").exists()


def test_setup_sh_change_preset_from_installed_copy_still_works(tmp_path):
    r1 = _run_setup(tmp_path, parented=False, compliance="none")
    assert r1.returncode == 0, r1.stdout + r1.stderr
    installed_setup_sh = tmp_path / "ultimate-memory-stack" / "general-edition" / "setup.sh"

    env = {k: v for k, v in os.environ.items() if k != "UMS_PARENT"}
    env["WORKING_DIR"] = str(tmp_path)
    r2 = subprocess.run(
        [BASH, str(installed_setup_sh), "--change-preset=enterprise"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(tmp_path), timeout=120,
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr
    overrides = tmp_path / "memory" / "user" / "USER_OVERRIDES.md"
    assert "compliance: enterprise" in overrides.read_text(encoding="utf-8")


def test_setup_sh_clears_stale_deployment_info_before_failing_install(tmp_path):
    # Regression: setup.py clears a stale .deployment-info completion
    # certificate up-front (a crashed re-install must not leave a marker
    # claiming a configured install); setup.sh didn't mirror this. Force a
    # controlled failure AFTER the clear point — the old forcing mechanism
    # (pre-existing common-specs/ → hard refusal) no longer fails as of
    # v4.0.0's archive-then-refresh (§3.4a), so use migrate-mode's "no
    # existing memory/" guard instead, which still fails after the clear point.
    (tmp_path / ".deployment-info").write_text("stale: true\n", encoding="utf-8")
    r = _run_setup(tmp_path, parented=False, extra_args=["--migrate-from=v2.0"])
    assert r.returncode == 1, r.stdout + r.stderr
    assert "No existing memory/" in r.stdout
    assert not (tmp_path / ".deployment-info").exists()
