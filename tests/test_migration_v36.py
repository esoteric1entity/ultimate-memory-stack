"""Tests for PLAN-migration-v36x-to-v400 — the v3.6.x -> v4.0.0 migration mode
(`--migrate-from=v3.6`) in both general-edition installers (setup.py, setup.sh).

Fixture: a real v3.6.2 install (from `git archive` of the pre-v4.0.0 baseline,
see tests/conftest.py's `v36_source_dir`) aged into a vault that trips every
recon-migration.md risk #1-6 — see tests/fixtures/build_v36_vault.py.

Design note — tiering opt-in reconciled away (§2.2e superseded): the original
design-round plan asked for an interactive y/N tiering opt-in during
migration, default N, because at design time (2026-07-10) `create_archive_indexes()`
did not exist yet. It shipped at train step 6/7 as an UNCONDITIONAL,
idempotent, create-only-if-absent scaffold step that ALREADY runs on every
fresh install and re-install with no consent gate at all (verified live: it
never overwrites, never touches existing data). `TIERING-MIGRATION-NOTES.md`
(the authoritative step-6 handoff, written after the plan) confirms this
explicitly: re-running the installer already creates the ARCHIVE_INDEX files
as a harmless side effect. Requiring the migration path alone to gate this
behind a NEW interactive prompt would (a) diverge from what fresh/re-installs
already do, (b) break `--dry-run`/non-interactive testability, and (c) add a
prompt for a change with zero data risk. Migration therefore lets the shared
setup_fresh() flow create the ARCHIVE_INDEX files unconditionally, same as
any other re-install — tested below as "created automatically", not
"skipped under --yes".
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
SETUP_PY = PKG / "general-edition" / "setup.py"
SETUP_SH = PKG / "general-edition" / "setup.sh"

sys.path.insert(0, str(PKG / "tests" / "fixtures"))
from build_v36_vault import (  # noqa: E402
    build_v36_vault,
    SENTINEL_SESSION_STATE,
    SENTINEL_MEMORY_INDEX,
    SENTINEL_USER_PROFILE,
    SENTINEL_FEEDBACK,
    STALE_IMPORT_LINE,
)


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


def _tree_hash(root: pathlib.Path) -> str:
    """Order-stable content+structure hash — used to prove "zero writes"."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        h.update(str(p.relative_to(root)).encode())
        if p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


def _run_py(target, *extra_args, timeout=60):
    return subprocess.run(
        [sys.executable, str(SETUP_PY), "--working-dir", str(target), "--migrate-from=v3.6", *extra_args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout,
    )


def _run_sh(target, *extra_args, timeout=60):
    env = dict(os.environ)
    env["WORKING_DIR"] = str(target)
    return subprocess.run(
        [BASH, str(SETUP_SH), "--migrate-from=v3.6", *extra_args],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=timeout,
    )


RUNNERS = [pytest.param(_run_py, id="python")] + (
    [pytest.param(_run_sh, id="bash")] if BASH else
    [pytest.param(_run_sh, id="bash", marks=pytest.mark.skip(reason="no usable bash — covered on CI ubuntu"))]
)


def _clear_stale_import(target: pathlib.Path) -> None:
    """Simulate the user manually deleting the stale @-import line — the one
    disclosure-only item migration never auto-edits, per §2.3."""
    claude_md = target / "CLAUDE.md"
    text = claude_md.read_text(encoding="utf-8")
    claude_md.write_text(text.replace(f"{STALE_IMPORT_LINE}\n\n", ""), encoding="utf-8")


# ===========================================================================
# 1. Fixture sanity — trips all of recon-migration.md's risks #1-6
# ===========================================================================

def test_fixture_trips_all_six_risks(tmp_path, v36_source_dir):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")

    # #1 stale oversized rules copy
    assert (tmp_path / ".claude" / "rules" / "memory_protocol.md").stat().st_size >= 15000
    # #2 stale CLAUDE.md @-import
    assert STALE_IMPORT_LINE in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    # #3 PROFILE lacks YAML frontmatter
    profile = tmp_path / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    assert not profile.read_bytes().startswith(b"---")
    # #4 flat, un-tiered — no ARCHIVE_INDEX.md anywhere yet
    assert not (tmp_path / "memory" / "archive" / "sessions" / "ARCHIVE_INDEX.md").exists()
    # #5 no USER_OVERRIDES.md
    assert not (tmp_path / "memory" / "user" / "USER_OVERRIDES.md").exists()
    # #6 PROFILE hand-edit that would be lost on a naive wipe
    assert "compliance: enterprise" in profile.read_text(encoding="utf-8")


# ===========================================================================
# 2. --dry-run writes NOTHING
# ===========================================================================

@pytest.mark.parametrize("runner", RUNNERS)
def test_dry_run_writes_nothing(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    before = _tree_hash(tmp_path)

    r = runner(tmp_path, "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DRY RUN" in r.stdout
    assert "refresh .claude/rules/memory_protocol.md" in r.stdout
    assert "create memory/user/USER_OVERRIDES.md" in r.stdout
    assert "archive existing PROFILE.md" in r.stdout
    assert "stale @-import at CLAUDE.md" in r.stdout

    after = _tree_hash(tmp_path)
    assert before == after, "dry-run must not write anything"


# ===========================================================================
# 3. Real migration: every plan-§5 assertion
# ===========================================================================

@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_backup_created_and_matches_pre_state(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    pre_session_state = (tmp_path / "memory" / "sessions" / "session_state.md").read_bytes()
    pre_memory_index = (tmp_path / "memory" / "MEMORY_INDEX.md").read_bytes()

    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    backups = list(tmp_path.glob("memory.backup.v3.6.*"))
    assert len(backups) == 1, backups
    backup = backups[0]
    assert (backup / "sessions" / "session_state.md").read_bytes() == pre_session_state
    assert (backup / "MEMORY_INDEX.md").read_bytes() == pre_memory_index


@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_preserves_sentinel_user_content(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    assert SENTINEL_SESSION_STATE in (tmp_path / "memory" / "sessions" / "session_state.md").read_text(encoding="utf-8")
    assert SENTINEL_MEMORY_INDEX in (tmp_path / "memory" / "MEMORY_INDEX.md").read_text(encoding="utf-8")
    assert SENTINEL_USER_PROFILE in (tmp_path / "memory" / "user" / "user_profile.md").read_text(encoding="utf-8")
    assert SENTINEL_FEEDBACK in (tmp_path / "memory" / "feedback" / "feedback.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_creates_user_overrides(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "memory" / "user" / "USER_OVERRIDES.md").exists()


@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_archives_and_regenerates_profile(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    archived = list((tmp_path / "memory" / "archive").glob("PROFILE.pre-upgrade.*.md"))
    assert len(archived) == 1, archived
    assert "compliance: enterprise" in archived[0].read_text(encoding="utf-8")

    profile = tmp_path / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    assert profile.read_bytes().startswith(b"---"), "regenerated PROFILE.md must have YAML frontmatter"


@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_refreshes_rules_copy_under_cap(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / ".claude" / "rules" / "memory_protocol.md").stat().st_size < 40000


@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_extended_lands_in_memory_never_in_claude_rules(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (tmp_path / "memory" / "MEMORY_PROTOCOL_EXTENDED.md").exists()
    rules_dir_files = [p.name for p in (tmp_path / ".claude" / "rules").iterdir()]
    assert not any("EXTENDED" in n for n in rules_dir_files), rules_dir_files


@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_creates_tiering_scaffold_automatically(tmp_path, v36_source_dir, runner):
    """Superseded design: no interactive opt-in (see module docstring) — the
    ARCHIVE_INDEX files are created the same unconditional way any re-install
    already creates them."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    for category in ("sessions", "decisions", "feedback"):
        assert (tmp_path / "memory" / "archive" / category / "ARCHIVE_INDEX.md").exists()


@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_detects_stale_import_without_editing_it(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CLAUDE.md" in r.stdout
    assert "never auto-edited" in r.stdout.lower() or "NOT be auto-edited" in r.stdout
    # Never edited — the stale line is exactly where it started.
    assert STALE_IMPORT_LINE in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("runner", RUNNERS)
def test_migration_discloses_openclaw_presence_without_touching_it(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    openclaw_dir = tmp_path / ".openclaw"
    openclaw_dir.mkdir()
    (openclaw_dir / "sentinel.txt").write_text("do not touch\n", encoding="utf-8")

    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert ".openclaw" in r.stdout
    assert (openclaw_dir / "sentinel.txt").read_text(encoding="utf-8") == "do not touch\n"


# ===========================================================================
# 4. Idempotency — second run is a recognized, zero-write no-op
# ===========================================================================

@pytest.mark.parametrize("runner", RUNNERS)
def test_second_run_after_disclosure_resolved_is_zero_write_noop(tmp_path, v36_source_dir, runner):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")

    r1 = runner(tmp_path)
    assert r1.returncode == 0, r1.stdout + r1.stderr

    # Simulate the user acting on the one disclosure migration can't auto-fix.
    _clear_stale_import(tmp_path)

    before = _tree_hash(tmp_path)
    r2 = runner(tmp_path)
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "already migrated" in r2.stdout.lower()
    after = _tree_hash(tmp_path)
    assert before == after, "a recognized already-migrated run must write nothing"


@pytest.mark.parametrize("runner", RUNNERS)
def test_second_run_without_resolving_disclosure_is_not_falsely_noop(tmp_path, v36_source_dir, runner):
    """Guards against a too-loose detector: if the stale CLAUDE.md import is
    still present, a second run must NOT claim already-migrated — it's a
    genuine unresolved risk (#2), not a false positive."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r1 = runner(tmp_path)
    assert r1.returncode == 0, r1.stdout + r1.stderr

    r2 = runner(tmp_path)
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "already migrated" not in r2.stdout.lower()


# ===========================================================================
# 5. verify.sh green after a real end-to-end migration
# ===========================================================================

@pytest.mark.skipif(BASH is None, reason="no usable bash — covered on CI ubuntu")
def test_verify_sh_green_after_migration(tmp_path, v36_source_dir):
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    r = _run_py(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    verify_sh = PKG / "verify.sh"
    v = subprocess.run(
        [BASH, str(verify_sh), str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert v.returncode == 0, v.stdout + v.stderr


# ===========================================================================
# 6. Invalid --migrate-from value is rejected
# ===========================================================================

def test_invalid_migrate_from_value_rejected_python(tmp_path):
    r = subprocess.run(
        [sys.executable, str(SETUP_PY), "--working-dir", str(tmp_path), "--migrate-from=v3.7"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert r.returncode != 0


@pytest.mark.skipif(BASH is None, reason="no usable bash — covered on CI ubuntu")
def test_invalid_migrate_from_value_rejected_bash(tmp_path):
    env = dict(os.environ)
    env["WORKING_DIR"] = str(tmp_path)
    r = subprocess.run(
        [BASH, str(SETUP_SH), "--migrate-from=v3.7"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=30,
    )
    assert r.returncode != 0
    assert "Invalid --migrate-from" in r.stdout


# ===========================================================================
# 7. Step-8 adversarial round regressions — every fix below is paired with a
#    reproduction of the finding it closes (findings are numbered per the
#    3-reviewer round, 2026-07-15; see 00-V4-SCOPE-AND-ROUTING.md §6).
# ===========================================================================

@pytest.mark.parametrize("runner", RUNNERS)
def test_rapid_repeated_migrations_never_crash_or_corrupt_backups(tmp_path, v36_source_dir, runner):
    """Findings 1/2/12: same-second backup-destination collisions used to
    crash Python (FileExistsError) or silently nest Bash's cp -r into an
    existing dir. Run several real migrations back-to-back (clearing the
    CLAUDE.md disclosure between each so every run is a REAL migration, not
    an already-migrated no-op) and assert every run succeeds with a
    distinctly-shaped backup — never nested one level too deep."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    for _ in range(4):
        r = runner(tmp_path)
        assert r.returncode == 0, r.stdout + r.stderr
        _clear_stale_import(tmp_path)
        # Re-introduce the disclosure so the NEXT run is real again too —
        # a fresh vault always regenerates a stale-import-bearing CLAUDE.md
        # would be unrealistic, so instead just re-add the sentinel line.
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(claude_md.read_text(encoding="utf-8") + f"\n{STALE_IMPORT_LINE}\n", encoding="utf-8")

    backups = sorted(tmp_path.glob("memory.backup.v3.6.*"))
    assert len(backups) == 4, backups
    for backup in backups:
        # A correctly-shaped backup has sessions/ etc. directly inside it —
        # a colliding cp -r would instead nest a second "memory/" level.
        assert (backup / "sessions" / "session_state.md").exists(), f"{backup} is malformed (nested?)"
        assert not (backup / "memory").exists(), f"{backup} was nested inside a colliding prior backup"


@pytest.mark.parametrize("runner", RUNNERS)
def test_claude_md_as_directory_does_not_crash_dry_run(tmp_path, v36_source_dir, runner):
    """Finding 8 (Python) / general robustness (Bash): a directory at
    CLAUDE.md's path used to crash Python's dry-run (.exists() then
    .read_text() -> PermissionError/IsADirectoryError) — dry-run is
    documented as always-safe and must never crash."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.unlink()
    claude_md.mkdir()

    r = runner(tmp_path, "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DRY RUN" in r.stdout


@pytest.mark.parametrize("runner", RUNNERS)
def test_claude_md_as_directory_does_not_crash_real_migration(tmp_path, v36_source_dir, runner):
    """Finding 7's directory-confusion class, applied to CLAUDE.md specifically
    for the real (non-dry-run) path."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.unlink()
    claude_md.mkdir()

    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.parametrize("runner", RUNNERS)
def test_stale_import_inside_fenced_code_block_is_not_a_false_positive(tmp_path, v36_source_dir, runner):
    """Finding 9: a documented EXAMPLE of the old import syntax inside a
    fenced code block used to permanently defeat idempotency detection for
    that vault. Only a real, live import line (not inside a fence) counts."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        "# Project instructions\n\n"
        "Example of the OLD import syntax (do not use):\n\n"
        "```\n"
        f"{STALE_IMPORT_LINE}\n"
        "```\n\n"
        "This is example text only, not a live import.\n",
        encoding="utf-8",
    )

    r = runner(tmp_path, "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "stale @-import" not in r.stdout


@pytest.mark.parametrize("runner", RUNNERS)
def test_stale_import_inside_html_comment_is_not_a_false_positive(tmp_path, v36_source_dir, runner):
    """Finding 6: a mention of the old syntax inside an HTML comment must not
    count as a live import either."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        f"# Project instructions\n\n<!-- {STALE_IMPORT_LINE} -->\n\nSome other notes.\n",
        encoding="utf-8",
    )

    r = runner(tmp_path, "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "stale @-import" not in r.stdout


@pytest.mark.parametrize("runner", RUNNERS)
def test_all_stale_import_lines_reported_not_just_the_first(tmp_path, v36_source_dir, runner):
    """Finding 10: a second stale import used to go completely unmentioned —
    a user who deleted only the first-reported line would see the warning
    persist with no indication a second one exists."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        f"# Project instructions\n{STALE_IMPORT_LINE}\n\nSome text.\n\n@another/path/MEMORY_PROTOCOL.md\n",
        encoding="utf-8",
    )

    r = runner(tmp_path, "--dry-run")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CLAUDE.md:2" in r.stdout
    assert "CLAUDE.md:6" in r.stdout


@pytest.mark.parametrize("runner", RUNNERS)
def test_backup_location_inside_memory_is_refused(tmp_path, v36_source_dir, runner):
    """Finding 11: --backup-location under memory/ itself used to plant a
    permanent nested copy inside the very tree it's meant to safeguard
    (Python: silent success; Bash: only saved by cp's own built-in guard)."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    unsafe_location = tmp_path / "memory" / "nested_backup"

    r = runner(tmp_path, f"--backup-location={unsafe_location}")
    assert r.returncode != 0, r.stdout + r.stderr
    assert not unsafe_location.exists()


def test_v2_dry_run_writes_nothing(tmp_path):
    """Finding 13: --migrate-from=v2.0 --dry-run used to print a warning and
    then perform a REAL backup+migration anyway — --dry-run must mean
    preview-only regardless of which version is being migrated from."""
    (tmp_path / "memory" / "sessions").mkdir(parents=True)
    (tmp_path / "memory" / "sessions" / "session_state.md").write_text("v2 sentinel\n", encoding="utf-8")
    before = _tree_hash(tmp_path)

    r = subprocess.run(
        [sys.executable, str(SETUP_PY), "--working-dir", str(tmp_path), "--migrate-from=v2.0", "--dry-run"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DRY RUN" in r.stdout
    assert "back up memory/" in r.stdout

    after = _tree_hash(tmp_path)
    assert before == after, "v2.0 --dry-run must not write anything"


@pytest.mark.skipif(BASH is None, reason="no usable bash — covered on CI ubuntu")
def test_v2_dry_run_writes_nothing_bash(tmp_path):
    (tmp_path / "memory" / "sessions").mkdir(parents=True)
    (tmp_path / "memory" / "sessions" / "session_state.md").write_text("v2 sentinel\n", encoding="utf-8")
    before = _tree_hash(tmp_path)

    env = dict(os.environ)
    env["WORKING_DIR"] = str(tmp_path)
    r = subprocess.run(
        [BASH, str(SETUP_SH), "--migrate-from=v2.0", "--dry-run"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "DRY RUN" in r.stdout

    after = _tree_hash(tmp_path)
    assert before == after, "v2.0 --dry-run must not write anything"


def _symlinks_supported(tmp_path) -> bool:
    target = tmp_path / "_symlink_probe_target.txt"
    link = tmp_path / "_symlink_probe_link.txt"
    target.write_text("x", encoding="utf-8")
    try:
        link.symlink_to(target)
    except OSError:
        return False
    return link.is_symlink()


@pytest.mark.parametrize("runner", RUNNERS)
def test_rules_file_as_directory_is_replaced_not_nested_into(tmp_path, v36_source_dir, runner):
    """Finding 7's directory-confusion class applied to the rules-copy
    destination directly (no symlink privilege needed to test this shape —
    same _safe_copy_file/_safe_replace_dest code path a symlink would hit)."""
    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    rules_file = tmp_path / ".claude" / "rules" / "memory_protocol.md"
    rules_file.unlink()
    rules_file.mkdir()

    r = runner(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert rules_file.is_file(), "the stray directory should have been replaced with a real file"
    assert rules_file.stat().st_size < 40000


def test_symlinked_rules_file_is_replaced_not_written_through(tmp_path, v36_source_dir):
    """Findings 3/4: a symlinked .claude/rules/memory_protocol.md used to get
    written THROUGH, destroying whatever external file it pointed at — a
    realistic pattern for dotfile-management tooling (Stow/chezmoi/yadm)."""
    if not _symlinks_supported(tmp_path):
        pytest.skip("this environment/user cannot create symlinks (no privilege)")

    build_v36_vault(v36_source_dir, tmp_path, compliance="none")
    external_target = tmp_path.parent / f"external_target_{tmp_path.name}.md"
    external_target.write_text("EXTERNAL SENTINEL — must never be overwritten\n", encoding="utf-8")

    rules_file = tmp_path / ".claude" / "rules" / "memory_protocol.md"
    rules_file.unlink()
    rules_file.symlink_to(external_target)

    r = _run_py(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr

    assert external_target.read_text(encoding="utf-8") == "EXTERNAL SENTINEL — must never be overwritten\n"
    assert not rules_file.is_symlink(), "the symlink should have been replaced with a real file"
    assert rules_file.stat().st_size < 40000
