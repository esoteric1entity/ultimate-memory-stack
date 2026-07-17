"""End-to-end lifecycle tests for the USER_OVERRIDES pattern (v4.0.0).

Real subprocess invocations of general-edition/setup.py against tmp_path working
dirs — the four mandatory scenarios: fresh install, re-install-over-customized,
upgrade-from-3.6.x-style vault, and aborted/interrupted install. Each asserts
zero user-value loss and USER_OVERRIDES.md byte-stability where it pre-existed.

Unit-level coverage of the individual functions (build_user_overrides_body,
create_user_overrides, upsert_override_key, archive_edited_profile) lives in
test_ge_setup.py; this file exercises the real CLI end-to-end instead.
"""

import pathlib
import subprocess
import sys

PKG = pathlib.Path(__file__).resolve().parents[1]
SETUP_PY = PKG / "general-edition" / "setup.py"


def _run(working_dir, *extra_args):
    return subprocess.run(
        [sys.executable, str(SETUP_PY), "--working-dir", str(working_dir), *extra_args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(PKG),
        timeout=60,
    )


def _overrides_path(working_dir):
    return pathlib.Path(working_dir) / "memory" / "user" / "USER_OVERRIDES.md"


def _profile_path(working_dir):
    return pathlib.Path(working_dir) / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"


# ===========================================================================
# 1. Fresh install
# ===========================================================================

def test_fresh_install_creates_user_overrides_with_bootstrap_values(tmp_path):
    r = _run(tmp_path, "--compliance", "enterprise", "--extensions", "gdpr,soc2")
    assert r.returncode == 0, r.stdout + r.stderr
    overrides = _overrides_path(tmp_path).read_text(encoding="utf-8")
    assert "compliance: enterprise" in overrides
    assert "extensions:\n  - gdpr\n  - soc2" in overrides
    # PROFILE.md stays the shipped default — never edited.
    assert "compliance: none" in _profile_path(tmp_path).read_text(encoding="utf-8")


def test_fresh_install_default_preset_leaves_overrides_minimal(tmp_path):
    r = _run(tmp_path, "--compliance", "none")
    assert r.returncode == 0, r.stdout + r.stderr
    out = _overrides_path(tmp_path).read_text(encoding="utf-8")
    assert "\ncompliance: none" not in out
    assert "\nextensions:" not in out


# ===========================================================================
# 2. Re-install over customized (USER_OVERRIDES.md pre-exists + PROFILE.md hand-edited)
# ===========================================================================

def test_reinstall_over_customized_preserves_overrides_byte_for_byte(tmp_path):
    r1 = _run(tmp_path, "--compliance", "enterprise", "--extensions", "gdpr")
    assert r1.returncode == 0, r1.stdout + r1.stderr

    overrides = _overrides_path(tmp_path)
    overrides.write_text(overrides.read_text(encoding="utf-8") + "\n# MY CUSTOM ADDITION\n", encoding="utf-8")
    before = overrides.read_bytes()

    profile = _profile_path(tmp_path)
    profile.write_text(profile.read_text(encoding="utf-8") + "\n# USER HAND-EDIT\n", encoding="utf-8")

    r2 = _run(tmp_path, "--compliance", "enterprise", "--extensions", "gdpr")
    assert r2.returncode == 0, r2.stdout + r2.stderr

    # Zero user-value loss: overrides file byte-identical, custom addition survives.
    assert overrides.read_bytes() == before

    # PROFILE.md's hand-edit was archived, not silently discarded.
    archived = list((tmp_path / "memory" / "archive").glob("PROFILE.pre-upgrade.*.md"))
    assert len(archived) == 1
    assert "USER HAND-EDIT" in archived[0].read_text(encoding="utf-8")

    # PROFILE.md itself was regenerated back to the shipped default.
    assert "USER HAND-EDIT" not in profile.read_text(encoding="utf-8")


def test_reinstall_with_no_profile_edit_does_not_archive(tmp_path):
    # An unedited PROFILE.md (identical to the shipped source) must NOT
    # trigger an archive — only genuine divergence does.
    r1 = _run(tmp_path, "--compliance", "none")
    assert r1.returncode == 0, r1.stdout + r1.stderr
    r2 = _run(tmp_path, "--compliance", "none")
    assert r2.returncode == 0, r2.stdout + r2.stderr
    archive_dir = tmp_path / "memory" / "archive"
    assert not archive_dir.exists() or not list(archive_dir.glob("PROFILE.pre-upgrade.*.md"))


# ===========================================================================
# 3. Upgrade from a 3.6.x-style vault (PROFILE.md edited, USER_OVERRIDES.md
#    absent entirely — it didn't exist before v4.0.0)
# ===========================================================================

def test_upgrade_from_pre_v4_vault_creates_overrides_and_archives_profile(tmp_path):
    r1 = _run(tmp_path, "--compliance", "none")
    assert r1.returncode == 0, r1.stdout + r1.stderr
    _overrides_path(tmp_path).unlink()  # this vault predates the file entirely

    profile = _profile_path(tmp_path)
    content = profile.read_text(encoding="utf-8").replace("compliance: none", "compliance: enterprise", 1)
    profile.write_text(content, encoding="utf-8")

    r2 = _run(tmp_path, "--compliance", "none")
    assert r2.returncode == 0, r2.stdout + r2.stderr

    archived = list((tmp_path / "memory" / "archive").glob("PROFILE.pre-upgrade.*.md"))
    assert len(archived) == 1
    assert "compliance: enterprise" in archived[0].read_text(encoding="utf-8")

    # A fresh USER_OVERRIDES.md now exists (created because it was absent) —
    # zero crash, zero silent loss of the old customization (it's in the archive).
    assert _overrides_path(tmp_path).exists()

    # PROFILE.md was regenerated to the shipped default, not left at the old value.
    assert "compliance: none" in profile.read_text(encoding="utf-8")


# ===========================================================================
# 4. Aborted / interrupted install (partial prior state)
# ===========================================================================

def test_aborted_install_partial_scaffold_recovers_cleanly(tmp_path):
    # Simulate a crash mid-install: common-specs/ copied, general-edition/ was
    # not, and a stale .deployment-info completion certificate was left behind.
    stack = tmp_path / "ultimate-memory-stack"
    (stack / "common-specs").mkdir(parents=True)
    (tmp_path / ".deployment-info").write_text("stale: true\n", encoding="utf-8")

    r = _run(tmp_path, "--compliance", "enterprise", "--extensions", "gdpr")
    assert r.returncode == 0, r.stdout + r.stderr

    # Completes cleanly — no crash, both trees present.
    assert (stack / "general-edition" / "PROFILE.md").exists()
    assert "compliance: enterprise" in _overrides_path(tmp_path).read_text(encoding="utf-8")

    # A fresh completion certificate was written (proves the install actually
    # finished) — the stale one from the "crash" does not survive untouched.
    info = (tmp_path / ".deployment-info").read_text(encoding="utf-8")
    assert "stale: true" not in info
    assert "compliance_preset: enterprise" in info


# ===========================================================================
# 5. Self-reference guard (adversarial-round finding, 2026-07-14)
# ===========================================================================

def test_running_installed_copy_refuses_instead_of_destroying_common_specs(tmp_path):
    # CRITICAL finding: SCRIPT_DIR is wherever the running script lives. If a
    # user re-runs the INSTALLED copy (a real, plausible action — INSTALL.md's
    # own examples point at it), SCRIPT_DIR and the install target collapse to
    # the same directory: the "differs from shipped" check compares the file
    # to itself (always false, so a hand-edited PROFILE.md is never archived),
    # then the wipe deletes common-specs/ and tries to copy FROM the path it
    # just deleted — crashing and permanently destroying it. Must refuse first.
    r1 = _run(tmp_path, "--compliance", "none")
    assert r1.returncode == 0, r1.stdout + r1.stderr

    installed_setup_py = tmp_path / "ultimate-memory-stack" / "general-edition" / "setup.py"
    assert installed_setup_py.exists()

    r2 = subprocess.run(
        [sys.executable, str(installed_setup_py), "--working-dir", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert r2.returncode == 1, r2.stdout + r2.stderr
    assert "INSTALLED copy" in r2.stdout

    # common-specs/ must have survived — the whole point of the guard.
    assert (tmp_path / "ultimate-memory-stack" / "common-specs").exists()


def test_change_preset_from_installed_copy_still_works(tmp_path):
    # The guard must NOT block the one documented, actually-safe use of the
    # installed copy: --change-preset never reaches setup_fresh()'s wipe logic.
    r1 = _run(tmp_path, "--compliance", "none")
    assert r1.returncode == 0, r1.stdout + r1.stderr
    installed_setup_py = tmp_path / "ultimate-memory-stack" / "general-edition" / "setup.py"

    r2 = subprocess.run(
        [sys.executable, str(installed_setup_py), "--working-dir", str(tmp_path), "--change-preset=enterprise"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "compliance: enterprise" in _overrides_path(tmp_path).read_text(encoding="utf-8")
