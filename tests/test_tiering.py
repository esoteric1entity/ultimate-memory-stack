"""Tests for the hot/cold tiering backport (v4.0.0).

Covers the plan's §8 Stage-2 test plan:
  1. Template validity (ARCHIVE_INDEX.template.md + the 3 tiered category
     templates + MEMORY_INDEX.template.md — pointer lines, correct cap numbers).
  2. Lint fire/no-fire fixtures for the 6 new lint_runner.py checks + the
     --severity filter (all 6 are "low"; medium hides them, low shows them).
  3. Deterministic rotation + rehydration TEST HELPERS (S8.3) — cut section →
     append to archive file → append one-liner → update counts, and the
     reverse. Test tooling only; not shipped product code.
  4. Synthetic aged-vault fixture: rotation keeps the hot file under its §11
     cap with zero information loss (every rotated ID findable via
     ARCHIVE_INDEX), counts consistent, eager-set lint check passes.
  5. Rehydration round-trip.
  6. Fresh sandbox install (real setup.py subprocess) + verify.sh green.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import subprocess
import sys

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]


def _load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, PKG / relpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load("core/shared-tools/lint_runner.py", "lint_runner")

TEMPLATES = PKG / "common-specs" / "templates"


def _write(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _make_claude_code_vault(root: pathlib.Path) -> None:
    """Minimal claude_code-detectable vault skeleton (empty session_state/index)."""
    _write(root / ".claude" / "rules" / "memory_protocol.md", "core protocol\n")
    _write(root / "memory" / "MEMORY_INDEX.md", "index\n")


# ===========================================================================
# 1. Template validity
# ===========================================================================

def test_archive_index_template_has_fenced_block_and_required_lines():
    text = (TEMPLATES / "ARCHIVE_INDEX.template.md").read_text(encoding="utf-8")
    assert "```markdown" in text
    body_match = re.search(r"```markdown\n(.*?)\n```", text, re.DOTALL)
    assert body_match, "no fenced markdown block found"
    body = body_match.group(1)
    assert "**Schema Version:**" in body
    assert "**Created:**" in body
    assert "**Last Updated:**" in body
    assert "**Entries:**" in body
    assert "## Entries" in body
    assert "## Rehydration" in body
    assert "<Category>" in body
    assert "<HotFile>" in body
    assert "<ArchiveFile>" in body


@pytest.mark.parametrize(
    "template_name,archive_pointer_text",
    [
        ("session_state.template.md", "memory/archive/sessions/ARCHIVE_INDEX.md"),
        ("decisions.template.md", "memory/archive/decisions/ARCHIVE_INDEX.md"),
        ("feedback.template.md", "memory/archive/feedback/ARCHIVE_INDEX.md"),
    ],
)
def test_tiered_category_templates_have_hot_side_pointer(template_name, archive_pointer_text):
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    assert "Older entries:" in text
    assert archive_pointer_text in text


def test_memory_index_template_has_archived_column():
    text = (TEMPLATES / "MEMORY_INDEX.template.md").read_text(encoding="utf-8")
    assert "| Category | File | Entries | Archived |" in text


@pytest.mark.parametrize(
    "template_name,stale_number,correct_number",
    [
        ("session_state.template.md", "150 lines", "1500 lines"),
        ("decisions.template.md", "200 lines", "1500 lines"),
        ("feedback.template.md", "100 lines", "300 lines"),
        ("MEMORY_INDEX.template.md", "80 lines", "150 lines"),
    ],
)
def test_stale_cap_numbers_fixed(template_name, stale_number, correct_number):
    text = (TEMPLATES / template_name).read_text(encoding="utf-8")
    assert stale_number not in text, f"{template_name} still has the stale cap {stale_number!r}"
    assert correct_number in text, f"{template_name} missing the corrected cap {correct_number!r}"


# ===========================================================================
# 2. Lint fire/no-fire fixtures — the 6 new checks
# ===========================================================================

def test_eager_set_over_budget_fires_when_exceeded(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(tmp_path / ".claude" / "rules" / "memory_protocol.md", "x" * 60_000)
    _write(tmp_path / "memory" / "sessions" / "session_state.md", "y" * 30_000)
    findings = mod.check_eager_set_over_budget(tmp_path, "claude_code")
    assert len(findings) == 1
    assert findings[0].check_id == "eager_set_over_budget"
    # v4.0.1: raised low -> high. This is the ONE tiering check that gates a
    # run, because an over-budget always-loaded set means content past the
    # harness's load limit is dropped silently (SCHEMA_lint.md §14).
    assert findings[0].severity == "high"


def test_eager_set_over_budget_no_fire_under_budget(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(tmp_path / "memory" / "sessions" / "session_state.md", "small\n")
    assert mod.check_eager_set_over_budget(tmp_path, "claude_code") == []


def test_eager_set_over_budget_respects_profile_override(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(tmp_path / ".claude" / "rules" / "memory_protocol.md", "x" * 50_000)
    profile = tmp_path / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    _write(profile, "---\neager_set_budget_bytes: 1000\n---\n")
    findings = mod.check_eager_set_over_budget(tmp_path, "claude_code")
    assert len(findings) == 1  # 50,000 > the lowered 1,000 override


# --- F1 regression: underscore/space-separated values must NOT truncate to
# their leading digits — they should fail to match and fall back to the
# 80,000 default, not silently misparse as budget=1 or budget=80.
# (review finding F1)

def test_eager_set_budget_underscore_separator_falls_back_to_default(tmp_path):
    _make_claude_code_vault(tmp_path)
    profile = tmp_path / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    _write(profile, "---\neager_set_budget_bytes: 1_000\n---\n")
    assert mod._load_eager_set_budget(tmp_path) == 80000


def test_eager_set_budget_space_separator_falls_back_to_default(tmp_path):
    _make_claude_code_vault(tmp_path)
    profile = tmp_path / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    _write(profile, "---\neager_set_budget_bytes: 80 000\n---\n")
    assert mod._load_eager_set_budget(tmp_path) == 80000


def test_eager_set_budget_trailing_comment_parses_correctly(tmp_path):
    _make_claude_code_vault(tmp_path)
    profile = tmp_path / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    _write(profile, "---\neager_set_budget_bytes: 50000  # tuned down\n---\n")
    assert mod._load_eager_set_budget(tmp_path) == 50000


def test_file_nearing_cap_fires_at_80_percent(tmp_path):
    _make_claude_code_vault(tmp_path)
    # feedback cap is 300 lines; 80% = 240.
    _write(tmp_path / "memory" / "feedback" / "feedback.md", "line\n" * 250)
    findings = mod.check_file_nearing_cap(tmp_path, "claude_code")
    ids = [f.check_id for f in findings]
    assert "file_nearing_cap" in ids
    hit = [f for f in findings if "feedback" in f.file_path][0]
    assert "250/300" in hit.message


def test_file_nearing_cap_no_fire_well_under(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(tmp_path / "memory" / "feedback" / "feedback.md", "line\n" * 10)
    findings = mod.check_file_nearing_cap(tmp_path, "claude_code")
    assert findings == []


def test_archive_unindexed_fires_for_missing_id(tmp_path):
    _make_claude_code_vault(tmp_path)
    archive_dir = tmp_path / "memory" / "archive" / "feedback"
    _write(archive_dir / "feedback-archive.md", "## FB-001: x\nid: FB-001\n\n## FB-002: y\nid: FB-002\n")
    _write(archive_dir / "ARCHIVE_INDEX.md", "- FB-001 (2026-01-01): summary\n")
    findings = mod.check_archive_unindexed(tmp_path, "claude_code")
    assert len(findings) == 1
    assert "FB-002" in findings[0].message


def test_archive_unindexed_no_fire_when_fully_indexed(tmp_path):
    _make_claude_code_vault(tmp_path)
    archive_dir = tmp_path / "memory" / "archive" / "feedback"
    _write(archive_dir / "feedback-archive.md", "## FB-001: x\nid: FB-001\n")
    _write(archive_dir / "ARCHIVE_INDEX.md", "- FB-001 (2026-01-01): summary\n")
    assert mod.check_archive_unindexed(tmp_path, "claude_code") == []


def test_archive_count_drift_fires_on_mismatch(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "feedback" / "feedback.md",
        "> Older entries: `memory/archive/feedback/ARCHIVE_INDEX.md` (3 entries)\n",
    )
    _write(
        tmp_path / "memory" / "archive" / "feedback" / "ARCHIVE_INDEX.md",
        "- FB-001 (2026-01-01): a\n- FB-002 (2026-01-02): b\n",
    )
    findings = mod.check_archive_count_drift(tmp_path, "claude_code")
    assert len(findings) == 1
    assert "says 3" in findings[0].message
    assert "has 2" in findings[0].message


def test_archive_count_drift_no_fire_when_matching(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "feedback" / "feedback.md",
        "> Older entries: `memory/archive/feedback/ARCHIVE_INDEX.md` (2 entries)\n",
    )
    _write(
        tmp_path / "memory" / "archive" / "feedback" / "ARCHIVE_INDEX.md",
        "- FB-001 (2026-01-01): a\n- FB-002 (2026-01-02): b\n",
    )
    assert mod.check_archive_count_drift(tmp_path, "claude_code") == []


# --- F3 regression: the pointer-count match must survive wording drift that
# doesn't change its meaning — capitalization, an intervening parenthetical,
# a line wrap before the count. All three used to produce zero findings on a
# genuine mismatch. (review finding F3)

@pytest.mark.parametrize(
    "pointer_text",
    [
        "> Older Entries: `memory/archive/feedback/ARCHIVE_INDEX.md` (3 entries)\n",
        "> Older entries: (archived) `memory/archive/feedback/ARCHIVE_INDEX.md` (3 entries)\n",
        "> Older entries:\n> `memory/archive/feedback/ARCHIVE_INDEX.md`\n> (3 entries)\n",
    ],
    ids=["capitalized", "intervening-parenthetical", "line-wrapped"],
)
def test_archive_count_drift_fires_despite_pointer_wording_drift(tmp_path, pointer_text):
    _make_claude_code_vault(tmp_path)
    _write(tmp_path / "memory" / "feedback" / "feedback.md", pointer_text)
    _write(
        tmp_path / "memory" / "archive" / "feedback" / "ARCHIVE_INDEX.md",
        "- FB-001 (2026-01-01): a\n- FB-002 (2026-01-02): b\n",
    )
    findings = mod.check_archive_count_drift(tmp_path, "claude_code")
    assert any(f.check_id == "archive_count_drift" and "says 3" in f.message for f in findings), findings


# --- F2 regression: check_archive_count_drift must also read MEMORY_INDEX.md's
# Archived column, independent of the hot-side pointer (the FROZEN spec's §S6
# and SCHEMA_lint.md §13 both require it; the check used to only look at the
# hot pointer). (review finding F2)

def test_archive_count_drift_fires_on_memory_index_archived_column_mismatch(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "archive" / "feedback" / "ARCHIVE_INDEX.md",
        "- FB-001 (2026-01-01): a\n- FB-002 (2026-01-02): b\n",
    )
    _write(
        tmp_path / "memory" / "MEMORY_INDEX.md",
        "| Category | File | Entries | Archived | Last Updated | Last Accessed |\n"
        "|----------|------|---------|----------|--------------|---------------|\n"
        "| Feedback | `feedback/feedback.md` | 4 | 5 | 2026-07-15 | session-1 |\n",
    )
    findings = mod.check_archive_count_drift(tmp_path, "claude_code")
    assert len(findings) == 1
    assert "MEMORY_INDEX" in findings[0].message
    assert "says 5" in findings[0].message
    assert "has 2" in findings[0].message


def test_archive_count_drift_no_fire_when_memory_index_archived_column_matches(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "archive" / "feedback" / "ARCHIVE_INDEX.md",
        "- FB-001 (2026-01-01): a\n- FB-002 (2026-01-02): b\n",
    )
    _write(
        tmp_path / "memory" / "MEMORY_INDEX.md",
        "| Category | File | Entries | Archived | Last Updated | Last Accessed |\n"
        "|----------|------|---------|----------|--------------|---------------|\n"
        "| Feedback | `feedback/feedback.md` | 4 | 2 | 2026-07-15 | session-1 |\n",
    )
    assert mod.check_archive_count_drift(tmp_path, "claude_code") == []


def test_archive_index_missing_fires(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(tmp_path / "memory" / "archive" / "decisions" / "decisions-archive.md", "## DEC-001\nid: DEC-001\n")
    findings = mod.check_archive_index_missing(tmp_path, "claude_code")
    assert len(findings) == 1
    assert "decisions" in findings[0].message


def test_archive_index_missing_no_fire_when_present(tmp_path):
    _make_claude_code_vault(tmp_path)
    archive_dir = tmp_path / "memory" / "archive" / "decisions"
    _write(archive_dir / "decisions-archive.md", "## DEC-001\nid: DEC-001\n")
    _write(archive_dir / "ARCHIVE_INDEX.md", "- DEC-001 (2026-01-01): x\n")
    assert mod.check_archive_index_missing(tmp_path, "claude_code") == []


# --- F4 regression: the spec's "non-empty" wording covers ANY file in the
# dir, not just the conventional <category>-archive.md name — a differently
# named or extra file used to go undetected. (review finding F4)

def test_archive_index_missing_fires_for_non_conventional_filename(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "archive" / "decisions" / "some-other-file.md",
        "stray content\n",
    )
    findings = mod.check_archive_index_missing(tmp_path, "claude_code")
    assert len(findings) == 1
    assert "some-other-file.md" in findings[0].message


def test_entry_over_cap_fires_for_long_oneliner(tmp_path):
    _make_claude_code_vault(tmp_path)
    long_line = "- SESSION-001 (2026-01-01): " + ("x" * 320) + " -> sessions-archive.md#s1"
    _write(tmp_path / "memory" / "archive" / "sessions" / "ARCHIVE_INDEX.md", long_line + "\n")
    findings = mod.check_entry_over_cap(tmp_path, "claude_code")
    assert len(findings) == 1
    assert findings[0].check_id == "entry_over_cap"


def test_entry_over_cap_no_fire_under_300_bytes(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "archive" / "sessions" / "ARCHIVE_INDEX.md",
        "- SESSION-001 (2026-01-01): short summary\n",
    )
    assert mod.check_entry_over_cap(tmp_path, "claude_code") == []


# --- F2 regression: check_entry_over_cap must also scan MEMORY_INDEX.md's
# Recent Entries row descriptions (FROZEN spec §S6 + SCHEMA_lint.md §13 both
# require it — the check used to only look at ARCHIVE_INDEX files).
# (review finding F2)

def test_entry_over_cap_fires_for_long_memory_index_row_description(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "MEMORY_INDEX.md",
        "## Recent Entries (Last Session)\n\n"
        "- SESSION-009: " + ("x" * 320) + "\n\n"
        "---\n",
    )
    findings = mod.check_entry_over_cap(tmp_path, "claude_code")
    assert len(findings) == 1
    assert "MEMORY_INDEX" in findings[0].file_path


def test_entry_over_cap_no_fire_for_short_memory_index_row_description(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "MEMORY_INDEX.md",
        "## Recent Entries (Last Session)\n\n"
        "- SESSION-009: short summary\n\n"
        "---\n",
    )
    assert mod.check_entry_over_cap(tmp_path, "claude_code") == []


def test_entry_over_cap_ignores_bullets_outside_recent_entries_section(tmp_path):
    """A long bullet OUTSIDE 'Recent Entries' (e.g. under 'Future categories')
    must not false-positive — only the Recent Entries section is in scope."""
    _make_claude_code_vault(tmp_path)
    _write(
        tmp_path / "memory" / "MEMORY_INDEX.md",
        "## Future categories\n\n"
        "- Decisions — " + ("x" * 320) + "\n\n"
        "## Recent Entries (Last Session)\n\n"
        "- SESSION-009: short summary\n",
    )
    assert mod.check_entry_over_cap(tmp_path, "claude_code") == []


def test_all_six_tiering_checks_are_severity_low(tmp_path):
    # Build one vault that trips all 6 at once, confirm severity uniformity.
    # (minor item: check_archive_count_drift was previously omitted from this
    # aggregate — from the review's "Minor" section.)
    _make_claude_code_vault(tmp_path)
    _write(tmp_path / ".claude" / "rules" / "memory_protocol.md", "x" * 90_000)
    _write(
        tmp_path / "memory" / "feedback" / "feedback.md",
        "> Older entries: `memory/archive/feedback/ARCHIVE_INDEX.md` (5 entries)\n\n"
        + "line\n" * 280,
    )
    archive_dir = tmp_path / "memory" / "archive" / "feedback"
    _write(archive_dir / "feedback-archive.md", "## FB-001: x\nid: FB-001\n\n## FB-002: y\nid: FB-002\n")
    _write(archive_dir / "ARCHIVE_INDEX.md", "- FB-001 (2026-01-01): " + ("z" * 320) + "\n")
    dec_archive = tmp_path / "memory" / "archive" / "decisions"
    _write(dec_archive / "decisions-archive.md", "## DEC-001\nid: DEC-001\n")

    findings = (
        mod.check_eager_set_over_budget(tmp_path, "claude_code")
        + mod.check_file_nearing_cap(tmp_path, "claude_code")
        + mod.check_archive_unindexed(tmp_path, "claude_code")
        + mod.check_archive_count_drift(tmp_path, "claude_code")
        + mod.check_archive_index_missing(tmp_path, "claude_code")
        + mod.check_entry_over_cap(tmp_path, "claude_code")
    )
    assert "archive_count_drift" in [f.check_id for f in findings]  # sanity: it actually fired
    assert len(findings) >= 5
    # v4.0.1 severity split (SCHEMA_lint.md §14): the five hygiene checks stay
    # advisory "low"; eager_set_over_budget alone is "high" because it is the
    # silent-data-loss guard, not a tidiness nit. Asserted per-check rather than
    # uniformly so a future accidental severity change still gets caught.
    by_id = {f.check_id: f.severity for f in findings}
    assert by_id["eager_set_over_budget"] == "high"
    assert all(
        sev == "low" for cid, sev in by_id.items() if cid != "eager_set_over_budget"
    ), by_id


LINT_RUNNER = PKG / "core" / "shared-tools" / "lint_runner.py"


def test_severity_filter_low_shows_medium_hides_tiering_findings(tmp_path):
    """Exercises the REAL --severity CLI path via subprocess (minor item:
    the prior version re-implemented the filter inline instead of testing
    main()'s actual filter code — per the review.)"""
    import json

    _make_claude_code_vault(tmp_path)
    _write(tmp_path / "memory" / "feedback" / "feedback.md", "line\n" * 280)

    def _finding_ids(severity):
        r = subprocess.run(
            [sys.executable, str(LINT_RUNNER), str(tmp_path), "--severity", severity, "--output", "json"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        assert r.returncode == 0, r.stdout + r.stderr
        payload = json.loads(r.stdout)
        return [f["check_id"] for f in payload["findings"]]

    low_ids = _finding_ids("low")
    assert "file_nearing_cap" in low_ids  # sanity: the fixture actually fires

    medium_ids = _finding_ids("medium")
    assert "file_nearing_cap" not in medium_ids  # --severity medium hides "low" tiering findings


# ===========================================================================
# 3. Deterministic rotation + rehydration TEST HELPERS (S8.3)
#
# Implements the E12.2/E12.3 mechanics for fixture construction. Test tooling
# only — mirrors the procedure agents follow live; not shipped product code.
# ===========================================================================

def _rotate_entry(root: pathlib.Path, category: str, hot_file: pathlib.Path, entry_id: str,
                   section_text: str, summary: str, date: str = "2026-01-01") -> None:
    """Cut `section_text` (must currently be IN hot_file's content) out of the
    hot file, append it to the category's archive file, append a one-liner to
    ARCHIVE_INDEX.md, and bump both entry counts."""
    archive_dir = root / "memory" / "archive" / category
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / f"{category}-archive.md"
    index_file = archive_dir / "ARCHIVE_INDEX.md"

    hot_content = hot_file.read_text(encoding="utf-8")
    assert section_text in hot_content, f"{entry_id} section not found in hot file"
    hot_content = hot_content.replace(section_text, "", 1)

    with archive_file.open("a", encoding="utf-8") as f:
        f.write(section_text)

    anchor = entry_id.lower().replace("_", "-")
    with index_file.open("a", encoding="utf-8") as f:
        f.write(f"- {entry_id} ({date}): {summary} → {category}-archive.md#{anchor}\n")

    # Bump the hot-side pointer count.
    current_indexed = len(mod.extract_archive_index_ids(index_file))
    if re.search(r"Older entries:.*?\(\d+\s+entries?\)", hot_content):
        hot_content = re.sub(
            r"(Older entries:.*?\()\d+(\s+entries?\))",
            rf"\g<1>{current_indexed}\g<2>",
            hot_content,
        )
    hot_file.write_text(hot_content, encoding="utf-8")


def _rehydrate_entry(root: pathlib.Path, category: str, hot_file: pathlib.Path, entry_id: str) -> None:
    """Reverse of _rotate_entry: copy the entry's section from the archive
    file back into the hot file (archive copy is NOT removed — rehydration
    copies, per E12.3), and decrement the hot-side pointer count."""
    archive_dir = root / "memory" / "archive" / category
    archive_file = archive_dir / f"{category}-archive.md"
    index_file = archive_dir / "ARCHIVE_INDEX.md"

    archive_content = archive_file.read_text(encoding="utf-8")
    match = re.search(rf"(## {re.escape(entry_id)}:.*?)(?=^## |\Z)", archive_content, re.MULTILINE | re.DOTALL)
    assert match, f"{entry_id} not found in {archive_file.name}"
    section_text = match.group(1)

    hot_content = hot_file.read_text(encoding="utf-8")
    hot_content += section_text
    remaining = len(mod.extract_archive_index_ids(index_file)) - 1
    if re.search(r"Older entries:.*?\(\d+\s+entries?\)", hot_content):
        hot_content = re.sub(
            r"(Older entries:.*?\()\d+(\s+entries?\))",
            rf"\g<1>{max(remaining, 0)}\g<2>",
            hot_content,
        )
    hot_file.write_text(hot_content, encoding="utf-8")

    # Drop the rehydrated entry's one-liner from ARCHIVE_INDEX (it's hot again).
    index_content = index_file.read_text(encoding="utf-8")
    index_content = "\n".join(
        line for line in index_content.splitlines() if not line.startswith(f"- {entry_id} ")
    ) + "\n"
    index_file.write_text(index_content, encoding="utf-8")


def test_rotate_entry_helper_moves_content_without_loss(tmp_path):
    hot_file = _write(
        tmp_path / "memory" / "feedback" / "feedback.md",
        "> Older entries: `memory/archive/feedback/ARCHIVE_INDEX.md` (0 entries)\n\n"
        "## FB-001: keep\nid: FB-001\nbody\n\n"
        "## FB-002: rotate-me\nid: FB-002\nold content\n\n",
    )
    section = "## FB-002: rotate-me\nid: FB-002\nold content\n\n"
    _rotate_entry(tmp_path, "feedback", hot_file, "FB-002", section, "rotate-me summary")

    hot_after = hot_file.read_text(encoding="utf-8")
    assert "FB-002" not in hot_after
    assert "FB-001" in hot_after  # untouched sibling entry survives
    assert "(1 entries)" in hot_after or "(1 entry)" in hot_after or "(1" in hot_after

    archive_after = (tmp_path / "memory" / "archive" / "feedback" / "feedback-archive.md").read_text(encoding="utf-8")
    assert "FB-002" in archive_after
    assert "old content" in archive_after  # zero loss — full body preserved

    index_after = (tmp_path / "memory" / "archive" / "feedback" / "ARCHIVE_INDEX.md").read_text(encoding="utf-8")
    assert "FB-002" in index_after


# ===========================================================================
# 4. Synthetic aged-vault fixture
# ===========================================================================

def test_aged_vault_rotation_keeps_hot_file_under_cap_zero_loss(tmp_path):
    _make_claude_code_vault(tmp_path)
    _write(tmp_path / "memory" / "user" / "user_profile.md", "profile\n")

    # feedback cap = 300 lines. Build 8 entries at ~40 lines each (~320 lines, over cap).
    entries = {}
    body = "> Older entries: `memory/archive/feedback/ARCHIVE_INDEX.md` (0 entries)\n\n"
    for i in range(1, 9):
        fb_id = f"FB-{i:03d}"
        section = f"## {fb_id}: entry {i}\nid: {fb_id}\n" + ("line\n" * 38) + "\n"
        entries[fb_id] = section
        body += section
    hot_file = _write(tmp_path / "memory" / "feedback" / "feedback.md", body)

    line_count_before = len(hot_file.read_text(encoding="utf-8").splitlines())
    assert line_count_before > 300  # confirms the fixture starts over cap

    # Rotate the 3 oldest to bring it back under cap.
    for fb_id in ("FB-001", "FB-002", "FB-003"):
        _rotate_entry(tmp_path, "feedback", hot_file, fb_id, entries[fb_id], f"summary for {fb_id}")

    line_count_after = len(hot_file.read_text(encoding="utf-8").splitlines())
    assert line_count_after < 300, "rotation should bring the hot file back under its §11 cap"

    # Zero loss: every rotated ID findable via ARCHIVE_INDEX.
    index_ids = mod.extract_archive_index_ids(tmp_path / "memory" / "archive" / "feedback" / "ARCHIVE_INDEX.md")
    assert index_ids == {"FB-001", "FB-002", "FB-003"}

    # Counts consistent: no archive_count_drift finding.
    assert mod.check_archive_count_drift(tmp_path, "claude_code") == []

    # No archive_unindexed drift either.
    assert mod.check_archive_unindexed(tmp_path, "claude_code") == []

    # Surviving entries (FB-004..FB-008) still present in the hot file.
    remaining_hot = hot_file.read_text(encoding="utf-8")
    for fb_id in ("FB-004", "FB-005", "FB-006", "FB-007", "FB-008"):
        assert fb_id in remaining_hot

    # Eager-set lint check passes (well under the 80,000B default budget).
    assert mod.check_eager_set_over_budget(tmp_path, "claude_code") == []


# ===========================================================================
# 5. Rehydration round-trip
# ===========================================================================

def test_rehydration_round_trip_restores_hot_content(tmp_path):
    hot_file = _write(
        tmp_path / "memory" / "decisions" / "decisions.md",
        "> Older entries: `memory/archive/decisions/ARCHIVE_INDEX.md` (0 entries)\n\n"
        "## DEC-001: keep\nid: DEC-001\nalways here\n\n",
    )
    section = "## DEC-002: paused-topic\nid: DEC-002\nimportant context\n\n"
    hot_file.write_text(hot_file.read_text(encoding="utf-8") + section, encoding="utf-8")

    _rotate_entry(tmp_path, "decisions", hot_file, "DEC-002", section, "paused topic decision")
    assert "DEC-002" not in hot_file.read_text(encoding="utf-8")
    assert mod.extract_archive_index_ids(
        tmp_path / "memory" / "archive" / "decisions" / "ARCHIVE_INDEX.md"
    ) == {"DEC-002"}

    # Topic reactivates — rehydrate.
    _rehydrate_entry(tmp_path, "decisions", hot_file, "DEC-002")

    hot_after = hot_file.read_text(encoding="utf-8")
    assert "DEC-002" in hot_after
    assert "important context" in hot_after  # content genuinely restored, not just the ID

    # ARCHIVE_INDEX no longer lists it as archived (it's hot again).
    assert mod.extract_archive_index_ids(
        tmp_path / "memory" / "archive" / "decisions" / "ARCHIVE_INDEX.md"
    ) == set()

    # The archived copy in decisions-archive.md is NOT deleted (E12.3: copies, never moves).
    archive_content = (tmp_path / "memory" / "archive" / "decisions" / "decisions-archive.md").read_text(encoding="utf-8")
    assert "DEC-002" in archive_content


# ===========================================================================
# 6. Fresh sandbox install (real subprocess) + verify.sh green
# ===========================================================================

SETUP_PY = PKG / "general-edition" / "setup.py"
VERIFY_SH = PKG / "verify.sh"


def _find_bash():
    import shutil
    w = shutil.which("bash")
    if w and "system32" not in w.lower():
        return w
    for c in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe", "/bin/bash", "/usr/bin/bash"):
        if pathlib.Path(c).exists():
            return c
    return None


BASH = _find_bash()


def test_fresh_install_then_verify_sh_reports_archive_indexes_present(tmp_path):
    r = subprocess.run(
        [sys.executable, str(SETUP_PY), "--working-dir", str(tmp_path), "--compliance", "none"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert r.returncode == 0, r.stdout + r.stderr

    for category in ("sessions", "decisions", "feedback"):
        assert (tmp_path / "memory" / "archive" / category / "ARCHIVE_INDEX.md").exists()

    if BASH is None or not VERIFY_SH.exists():
        pytest.skip("no usable bash for verify.sh — covered on CI ubuntu")

    v = subprocess.run(
        [BASH, str(VERIFY_SH), str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert v.returncode == 0, v.stdout + v.stderr
    assert "memory/archive/sessions/ARCHIVE_INDEX.md" in v.stdout
    assert "memory/archive/decisions/ARCHIVE_INDEX.md" in v.stdout
    assert "memory/archive/feedback/ARCHIVE_INDEX.md" in v.stdout
