"""Characterization + edge-case unit tests for heartbeat_compactor.py.

Target lives outside an importable package and is stdlib-only, so it is loaded
by absolute path via importlib rather than a plain import.

Run from the package root:
    python -m pytest tests/test_heartbeat_compactor.py -q
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]


def _load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, PKG / relpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load("core/openclaw-adapter/scripts/heartbeat_compactor.py", "heartbeat_compactor")


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #
def _heartbeat_block(kind: str, label: str, body: str = "stuff here") -> str:
    """Build one heartbeat section. kind in {'🔵','🟦'}, label in {'Current','Prior'}."""
    return f"## {kind} {label} heartbeat\n\n{body}\n\n"


def _make_heartbeat_doc(n: int) -> str:
    """Build a HEARTBEAT.md body with n heartbeat headers.

    First is Current (🔵), the rest are Prior (🟦) — mirrors real shape.
    """
    parts = ["# HEARTBEAT.md\n\n"]
    for i in range(n):
        if i == 0:
            parts.append(_heartbeat_block("🔵", "Current", f"heartbeat number {i}"))
        else:
            parts.append(_heartbeat_block("🟦", "Prior", f"heartbeat number {i}"))
    return "".join(parts)


# --------------------------------------------------------------------------- #
# HEARTBEAT_HEADER_RE
# --------------------------------------------------------------------------- #
def test_header_re_matches_current_and_prior():
    text = (
        "## 🔵 Current heartbeat\nbody\n\n"
        "## 🟦 Prior heartbeat\nmore body\n"
    )
    matches = mod.HEARTBEAT_HEADER_RE.findall(text)
    assert len(matches) == 2


def test_header_re_matches_at_line_start_only():
    # The pattern is anchored with ^ + re.MULTILINE; a header indented or
    # prefixed mid-line should NOT match.
    text = "prose ## 🔵 Current heartbeat inline\n"
    assert mod.HEARTBEAT_HEADER_RE.search(text) is None


def test_header_re_requires_correct_emoji():
    # A plain "## Current heartbeat" without the emoji must not match.
    text = "## Current heartbeat\n"
    assert mod.HEARTBEAT_HEADER_RE.search(text) is None


def test_header_re_rejects_other_words():
    text = "## 🔵 Stale heartbeat\n"
    assert mod.HEARTBEAT_HEADER_RE.search(text) is None


def test_header_re_counts_multiple_priors():
    doc = _make_heartbeat_doc(5)
    assert len(list(mod.HEARTBEAT_HEADER_RE.finditer(doc))) == 5


# --------------------------------------------------------------------------- #
# rotate_heartbeats
# --------------------------------------------------------------------------- #
def test_rotate_no_op_when_exactly_max_depth(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    original = _make_heartbeat_doc(3)
    hb.write_text(original, encoding="utf-8")
    archive_dir = tmp_path / "archive" / "heartbeats"

    result = mod.rotate_heartbeats(hb, archive_dir)

    assert result == []
    # File untouched, no archive created.
    assert hb.read_text(encoding="utf-8") == original
    assert not archive_dir.exists()


def test_rotate_no_op_when_fewer_than_max_depth(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text(_make_heartbeat_doc(1), encoding="utf-8")
    archive_dir = tmp_path / "archive" / "heartbeats"

    assert mod.rotate_heartbeats(hb, archive_dir) == []
    assert not archive_dir.exists()


def test_rotate_no_op_when_zero_heartbeats(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text("# HEARTBEAT.md\n\njust prose, no heartbeats here\n", encoding="utf-8")
    archive_dir = tmp_path / "archive" / "heartbeats"

    assert mod.rotate_heartbeats(hb, archive_dir) == []
    assert not archive_dir.exists()


def test_rotate_archives_when_over_max_depth(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text(_make_heartbeat_doc(4), encoding="utf-8")
    archive_dir = tmp_path / "archive" / "heartbeats"

    result = mod.rotate_heartbeats(hb, archive_dir)

    # One heartbeat rotated (4 - 3).
    assert len(result) == 1
    assert "Rotated 1 heartbeat" in result[0]

    # Archive file created.
    archive_files = list(archive_dir.glob("*.md"))
    assert len(archive_files) == 1
    archive_text = archive_files[0].read_text(encoding="utf-8")
    assert "Archived Heartbeats" in archive_text
    # The 4th heartbeat (index 3) is the oldest one archived.
    assert "heartbeat number 3" in archive_text

    # Kept file now has exactly 3 heartbeats.
    kept = hb.read_text(encoding="utf-8")
    assert len(list(mod.HEARTBEAT_HEADER_RE.finditer(kept))) == 3
    assert "heartbeat number 3" not in kept


def test_rotate_reports_correct_count_for_many(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text(_make_heartbeat_doc(7), encoding="utf-8")
    archive_dir = tmp_path / "archive" / "heartbeats"

    result = mod.rotate_heartbeats(hb, archive_dir)
    # 7 - 3 == 4 rotated.
    assert "Rotated 4 heartbeat(s)" in result[0]
    kept = hb.read_text(encoding="utf-8")
    assert len(list(mod.HEARTBEAT_HEADER_RE.finditer(kept))) == 3


def test_rotate_second_run_appends_to_existing_archive(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    archive_dir = tmp_path / "archive" / "heartbeats"

    # First rotation: 4 -> 3, creates archive.
    hb.write_text(_make_heartbeat_doc(4), encoding="utf-8")
    first = mod.rotate_heartbeats(hb, archive_dir)
    assert len(first) == 1
    archive_files = list(archive_dir.glob("*.md"))
    assert len(archive_files) == 1
    archive_file = archive_files[0]
    after_first = archive_file.read_text(encoding="utf-8")

    # Now overwrite HEARTBEAT.md with a fresh 4-deep doc using distinct bodies
    # so we can prove the second archive content was appended.
    second_doc = (
        _heartbeat_block("🔵", "Current", "ROUND2-keep-0")
        + _heartbeat_block("🟦", "Prior", "ROUND2-keep-1")
        + _heartbeat_block("🟦", "Prior", "ROUND2-keep-2")
        + _heartbeat_block("🟦", "Prior", "ROUND2-archive-3")
    )
    hb.write_text("# HEARTBEAT.md\n\n" + second_doc, encoding="utf-8")
    second = mod.rotate_heartbeats(hb, archive_dir)
    assert len(second) == 1

    # Same monthly archive file is reused (no new file created).
    assert list(archive_dir.glob("*.md")) == [archive_file]

    after_second = archive_file.read_text(encoding="utf-8")
    # Appended, not overwritten: original content preserved + separator + new.
    assert after_second.startswith(after_first)
    assert "\n---\n\n" in after_second[len(after_first) - 5:]
    assert "ROUND2-archive-3" in after_second
    # The previously archived content remains.
    assert "heartbeat number 3" in after_second


def test_rotate_custom_max_depth(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text(_make_heartbeat_doc(3), encoding="utf-8")
    archive_dir = tmp_path / "archive" / "heartbeats"

    # With max_depth=1, three headers (>1) trigger rotation of 2.
    result = mod.rotate_heartbeats(hb, archive_dir, max_depth=1)
    assert "Rotated 2 heartbeat(s)" in result[0]
    kept = hb.read_text(encoding="utf-8")
    assert len(list(mod.HEARTBEAT_HEADER_RE.finditer(kept))) == 1


# --------------------------------------------------------------------------- #
# check_size_cap
# --------------------------------------------------------------------------- #
def test_check_size_cap_under_limit(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text("a" * (mod.HEARTBEAT_MAX_CHARS - 100), encoding="utf-8")
    assert mod.check_size_cap(hb) == []


def test_check_size_cap_at_exact_limit_is_not_over(tmp_path):
    # Boundary: size == cap uses strict '>' so it is NOT flagged.
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text("a" * mod.HEARTBEAT_MAX_CHARS, encoding="utf-8")
    assert hb.stat().st_size == mod.HEARTBEAT_MAX_CHARS
    assert mod.check_size_cap(hb) == []


def test_check_size_cap_one_over_limit_is_flagged(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text("a" * (mod.HEARTBEAT_MAX_CHARS + 1), encoding="utf-8")
    result = mod.check_size_cap(hb)
    assert len(result) == 1
    assert "exceeds" in result[0]
    assert str(mod.HEARTBEAT_MAX_CHARS) in result[0]


def test_check_size_cap_empty_file(tmp_path):
    hb = tmp_path / "HEARTBEAT.md"
    hb.write_text("", encoding="utf-8")
    assert mod.check_size_cap(hb) == []


# --------------------------------------------------------------------------- #
# lint_doc_completeness
# --------------------------------------------------------------------------- #
def _write_decisions(tmp_path: pathlib.Path, content: str) -> pathlib.Path:
    dec = tmp_path / "memory" / "decisions" / "decisions.md"
    dec.parent.mkdir(parents=True, exist_ok=True)
    dec.write_text(content, encoding="utf-8")
    return tmp_path


def test_doc_completeness_no_file_returns_empty(tmp_path):
    # decisions.md does not exist.
    assert mod.lint_doc_completeness(tmp_path) == []


def test_doc_completeness_accepts_heading_form(tmp_path):
    content = (
        "## DEC-001: Use heading form\n\n"
        "### Purpose\nwhy\n\n"
        "### Rationale\nbecause\n\n"
        "### Sound reasoning\nlogic\n\n"
        "### Scope — CAN\ncan do\n\n"
        "### Scope — CANNOT\ncannot do\n\n"
    )
    root = _write_decisions(tmp_path, content)
    # All 5 elements present in heading form -> no gap finding.
    assert mod.lint_doc_completeness(root) == []


def test_doc_completeness_accepts_bold_label_form(tmp_path):
    content = (
        "## DEC-002: Use bold-label form\n\n"
        "**Purpose:** why\n\n"
        "**Rationale:** because\n\n"
        "**Sound reasoning:** logic\n\n"
        "**Scope — CAN:** can do\n\n"
        "**Scope — CANNOT:** cannot do\n\n"
    )
    root = _write_decisions(tmp_path, content)
    # All 5 elements present in bold-label form -> no gap finding.
    assert mod.lint_doc_completeness(root) == []


def test_doc_completeness_accepts_bold_label_without_colon(tmp_path):
    # The matcher allows an optional colon: **Purpose** as well as **Purpose:**.
    content = (
        "## DEC-003: Bold without colon\n\n"
        "**Purpose** why\n\n"
        "**Rationale** because\n\n"
        "**Sound reasoning** logic\n\n"
        "**Scope — CAN** can do\n\n"
        "**Scope — CANNOT** cannot do\n\n"
    )
    root = _write_decisions(tmp_path, content)
    assert mod.lint_doc_completeness(root) == []


def test_doc_completeness_catches_real_gap(tmp_path):
    # Missing 'Rationale' and 'Sound reasoning'.
    content = (
        "## DEC-004: Incomplete decision\n\n"
        "### Purpose\nwhy\n\n"
        "### Scope — CAN\ncan do\n\n"
        "### Scope — CANNOT\ncannot do\n\n"
    )
    root = _write_decisions(tmp_path, content)
    findings = mod.lint_doc_completeness(root)
    assert len(findings) == 1
    msg = findings[0]
    assert "DEC-004" in msg
    assert "missing 2 of 5" in msg
    assert "Rationale" in msg
    assert "Sound reasoning" in msg


def test_doc_completeness_reports_all_five_missing(tmp_path):
    content = "## DEC-005: Empty body\n\nNo discipline sections at all.\n"
    root = _write_decisions(tmp_path, content)
    findings = mod.lint_doc_completeness(root)
    assert len(findings) == 1
    assert "missing 5 of 5" in findings[0]


def test_doc_completeness_multiple_blocks_independently(tmp_path):
    content = (
        "## DEC-006: Complete one\n\n"
        "### Purpose\np\n### Rationale\nr\n### Sound reasoning\ns\n"
        "### Scope — CAN\nc\n### Scope — CANNOT\nn\n\n"
        "## DEC-007: Incomplete one\n\n"
        "### Purpose\nonly purpose\n\n"
    )
    root = _write_decisions(tmp_path, content)
    findings = mod.lint_doc_completeness(root)
    # Only DEC-007 should produce a finding.
    assert len(findings) == 1
    assert "DEC-007" in findings[0]
    assert "missing 4 of 5" in findings[0]


def test_doc_completeness_ignores_non_dec_headings(tmp_path):
    content = (
        "## Overview\n\nThis is not a DEC block.\n\n"
        "## DEC-008: A real one\n\n"
        "### Purpose\np\n### Rationale\nr\n### Sound reasoning\ns\n"
        "### Scope — CAN\nc\n### Scope — CANNOT\nn\n\n"
    )
    root = _write_decisions(tmp_path, content)
    assert mod.lint_doc_completeness(root) == []


# --------------------------------------------------------------------------- #
# find_openclaw_root — resolution priority
# --------------------------------------------------------------------------- #
def _make_valid_root(tmp_path: pathlib.Path) -> pathlib.Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "HEARTBEAT.md").write_text(_make_heartbeat_doc(1), encoding="utf-8")
    return tmp_path


def test_find_root_explicit_arg_success(tmp_path):
    root = _make_valid_root(tmp_path)
    resolved = mod.find_openclaw_root(str(root))
    assert resolved == root.resolve()


def test_find_root_explicit_arg_beats_env(tmp_path, monkeypatch):
    arg_root = _make_valid_root(tmp_path / "arg_root")
    env_root = _make_valid_root(tmp_path / "env_root")
    monkeypatch.setenv("OPENCLAW_ROOT", str(env_root))
    resolved = mod.find_openclaw_root(str(arg_root))
    # Explicit arg wins over env.
    assert resolved == arg_root.resolve()


def test_find_root_env_used_when_no_arg(tmp_path, monkeypatch):
    env_root = _make_valid_root(tmp_path / "env_root")
    monkeypatch.setenv("OPENCLAW_ROOT", str(env_root))
    resolved = mod.find_openclaw_root(None)
    assert resolved == env_root.resolve()


def test_find_root_cwd_last_resort(tmp_path, monkeypatch):
    # No arg, no env, and self-locate target (script's parent.parent/HEARTBEAT.md)
    # must not exist for the cwd fallback to engage. The real install location
    # has no HEARTBEAT.md, so self-locate falls through to cwd in this repo.
    monkeypatch.delenv("OPENCLAW_ROOT", raising=False)
    valid_cwd = _make_valid_root(tmp_path / "cwd_root")
    monkeypatch.chdir(valid_cwd)
    resolved = mod.find_openclaw_root(None)
    assert resolved == valid_cwd.resolve()


def test_find_root_missing_heartbeat_exits_2(tmp_path, monkeypatch):
    # Root exists but has no HEARTBEAT.md -> sys.exit(2).
    monkeypatch.delenv("OPENCLAW_ROOT", raising=False)
    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    with pytest.raises(SystemExit) as exc:
        mod.find_openclaw_root(str(empty_root))
    assert exc.value.code == 2


def test_find_root_nonexistent_path_exits_1(tmp_path, monkeypatch):
    # Path does not exist at all -> sys.exit(1).
    monkeypatch.delenv("OPENCLAW_ROOT", raising=False)
    missing = tmp_path / "does_not_exist_at_all"
    with pytest.raises(SystemExit) as exc:
        mod.find_openclaw_root(str(missing))
    assert exc.value.code == 1


# --------------------------------------------------------------------------- #
# Lint stubs (orphans / stale-tentative / naming / standing-rule) — empty by design
# --------------------------------------------------------------------------- #
def test_lint_orphans_stub_empty(tmp_path):
    assert mod.lint_orphans(tmp_path) == []


def test_lint_stale_tentative_stub_empty(tmp_path):
    assert mod.lint_stale_tentative(tmp_path) == []


def test_lint_naming_inconsistencies_stub_empty(tmp_path):
    assert mod.lint_naming_inconsistencies(tmp_path) == []


def test_lint_standing_rule_candidates_stub_empty(tmp_path):
    assert mod.lint_standing_rule_candidates(tmp_path) == []
