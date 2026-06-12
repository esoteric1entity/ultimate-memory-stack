"""Characterization + edge-case unit tests for review_quarantined.py.

Target: core/audit-quarantine-skill/scripts/review_quarantined.py
The module is stdlib-only and lives outside an importable package, so it is
loaded by absolute path via importlib (NOT plain-imported).

Covered functions:
  - iso_timestamp
  - parse_entry_frontmatter
  - get_entry_category
  - read_quarantine_log_for
  - find_quarantined_entries
  - append_quarantine_log
  - append_audit_log

The interactive present_entry()/main() loop is intentionally NOT exercised.
"""

import importlib.util
import json
import pathlib
import re
import sys

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]


def _load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, PKG / relpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load("core/audit-quarantine-skill/scripts/review_quarantined.py", "review_quarantined")


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_entry(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def working_dir(tmp_path):
    """A bare working dir with a memory/ tree (no quarantine contents yet)."""
    (tmp_path / "memory").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# iso_timestamp
# ---------------------------------------------------------------------------

class TestIsoTimestamp:
    def test_ends_with_z_not_offset(self):
        ts = mod.iso_timestamp()
        assert ts.endswith("Z")
        # The literal "+00:00" must have been substituted out.
        assert "+00:00" not in ts

    def test_second_precision_no_microseconds(self):
        ts = mod.iso_timestamp()
        # No fractional-second component before the Z.
        assert "." not in ts

    def test_iso8601_z_shape(self):
        ts = mod.iso_timestamp()
        # YYYY-MM-DDTHH:MM:SSZ
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts), ts

    def test_parseable_back_to_datetime(self):
        from datetime import datetime, timezone

        ts = mod.iso_timestamp()
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed.tzinfo == timezone.utc
        assert parsed.microsecond == 0


# ---------------------------------------------------------------------------
# parse_entry_frontmatter
# ---------------------------------------------------------------------------

class TestParseEntryFrontmatter:
    def test_happy_path_extracts_keys(self, tmp_path):
        p = _make_entry(
            tmp_path / "e.md",
            "---\nid: DEC-099\nstatus: quarantined\nquarantine_reason: schema-drift\n---\nBody here.\n",
        )
        fm = mod.parse_entry_frontmatter(p)
        assert fm == {
            "id": "DEC-099",
            "status": "quarantined",
            "quarantine_reason": "schema-drift",
        }

    def test_strips_double_and_single_quotes(self, tmp_path):
        p = _make_entry(
            tmp_path / "e.md",
            "---\n"
            'title: "Quoted Double"\n'
            "author: 'Quoted Single'\n"
            "---\nbody\n",
        )
        fm = mod.parse_entry_frontmatter(p)
        assert fm["title"] == "Quoted Double"
        assert fm["author"] == "Quoted Single"

    def test_value_with_colon_keeps_remainder(self, tmp_path):
        # partition() on first ':' must preserve the rest of the value (e.g. a URL).
        p = _make_entry(
            tmp_path / "e.md",
            "---\nurl: https://example.com/path\n---\nbody\n",
        )
        fm = mod.parse_entry_frontmatter(p)
        assert fm["url"] == "https://example.com/path"

    def test_missing_frontmatter_returns_empty(self, tmp_path):
        # Content that does not start with '---'.
        p = _make_entry(tmp_path / "e.md", "Just a plain body with no frontmatter.\n")
        assert mod.parse_entry_frontmatter(p) == {}

    def test_empty_frontmatter_block_returns_empty(self, tmp_path):
        # Valid delimiters but nothing parseable inside.
        p = _make_entry(tmp_path / "e.md", "---\n\n---\nbody\n")
        assert mod.parse_entry_frontmatter(p) == {}

    def test_only_one_delimiter_returns_empty(self, tmp_path):
        # Starts with '---' but never closes -> fewer than 3 split parts.
        p = _make_entry(tmp_path / "e.md", "---\nid: X\nno closing delimiter\n")
        assert mod.parse_entry_frontmatter(p) == {}

    def test_lines_without_colon_are_skipped(self, tmp_path):
        p = _make_entry(
            tmp_path / "e.md",
            "---\nid: KEEP\nthis line has no colon\nstatus: active\n---\nbody\n",
        )
        fm = mod.parse_entry_frontmatter(p)
        assert fm == {"id": "KEEP", "status": "active"}

    def test_completely_empty_file_returns_empty(self, tmp_path):
        p = _make_entry(tmp_path / "e.md", "")
        assert mod.parse_entry_frontmatter(p) == {}


# ---------------------------------------------------------------------------
# get_entry_category
# ---------------------------------------------------------------------------

class TestGetEntryCategory:
    def test_subdir_category(self, working_dir):
        q = working_dir / "memory" / "quarantine"
        entry = q / "decisions" / "DEC-001.md"
        entry.parent.mkdir(parents=True)
        entry.write_text("x", encoding="utf-8")
        assert mod.get_entry_category(entry, working_dir) == "decisions"

    def test_nested_subdir_uses_first_part(self, working_dir):
        q = working_dir / "memory" / "quarantine"
        entry = q / "knowledge" / "sub" / "K-1.md"
        entry.parent.mkdir(parents=True)
        entry.write_text("x", encoding="utf-8")
        assert mod.get_entry_category(entry, working_dir) == "knowledge"

    def test_file_directly_in_quarantine_root_defaults_to_decisions(self, working_dir):
        q = working_dir / "memory" / "quarantine"
        q.mkdir(parents=True)
        entry = q / "loose.md"
        entry.write_text("x", encoding="utf-8")
        # Only one path part -> fallback default.
        assert mod.get_entry_category(entry, working_dir) == "decisions"


# ---------------------------------------------------------------------------
# read_quarantine_log_for
# ---------------------------------------------------------------------------

class TestReadQuarantineLogFor:
    def _write_log(self, working_dir, lines):
        log = working_dir / "memory" / "quarantine" / "quarantine_log.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text("".join(lines), encoding="utf-8")
        return log

    def test_missing_log_returns_empty(self, working_dir):
        assert mod.read_quarantine_log_for("DEC-1", working_dir) == []

    def test_matches_canonical_entry_id(self, working_dir):
        self._write_log(
            working_dir,
            [
                json.dumps({"entry_id": "DEC-1", "action": "quarantine"}) + "\n",
                json.dumps({"entry_id": "DEC-2", "action": "quarantine"}) + "\n",
            ],
        )
        out = mod.read_quarantine_log_for("DEC-1", working_dir)
        assert len(out) == 1
        assert out[0]["entry_id"] == "DEC-1"

    def test_matches_legacy_original_entry_id(self, working_dir):
        self._write_log(
            working_dir,
            [json.dumps({"original_entry_id": "DEC-9", "action": "route"}) + "\n"],
        )
        out = mod.read_quarantine_log_for("DEC-9", working_dir)
        assert len(out) == 1
        assert out[0]["original_entry_id"] == "DEC-9"

    def test_multiple_matches_preserve_file_order(self, working_dir):
        self._write_log(
            working_dir,
            [
                json.dumps({"entry_id": "DEC-1", "action": "quarantine", "n": 1}) + "\n",
                json.dumps({"entry_id": "OTHER", "action": "x"}) + "\n",
                json.dumps({"entry_id": "DEC-1", "action": "review", "n": 2}) + "\n",
            ],
        )
        out = mod.read_quarantine_log_for("DEC-1", working_dir)
        assert [r["n"] for r in out] == [1, 2]

    def test_blank_lines_skipped(self, working_dir):
        self._write_log(
            working_dir,
            [
                "\n",
                "   \n",
                json.dumps({"entry_id": "DEC-1"}) + "\n",
                "\n",
            ],
        )
        out = mod.read_quarantine_log_for("DEC-1", working_dir)
        assert len(out) == 1

    def test_malformed_json_line_skipped_not_raised(self, working_dir):
        self._write_log(
            working_dir,
            [
                "{not valid json}\n",
                json.dumps({"entry_id": "DEC-1"}) + "\n",
                "still {bad\n",
            ],
        )
        out = mod.read_quarantine_log_for("DEC-1", working_dir)
        assert len(out) == 1
        assert out[0]["entry_id"] == "DEC-1"

    def test_no_matching_id_returns_empty(self, working_dir):
        self._write_log(
            working_dir,
            [json.dumps({"entry_id": "DEC-1"}) + "\n"],
        )
        assert mod.read_quarantine_log_for("DEC-NOPE", working_dir) == []


# ---------------------------------------------------------------------------
# find_quarantined_entries
# ---------------------------------------------------------------------------

class TestFindQuarantinedEntries:
    def test_missing_quarantine_dir_returns_empty(self, working_dir):
        # memory/ exists but memory/quarantine/ does not.
        assert mod.find_quarantined_entries(working_dir) == []

    def test_empty_quarantine_dir_returns_empty(self, working_dir):
        (working_dir / "memory" / "quarantine").mkdir(parents=True)
        assert mod.find_quarantined_entries(working_dir) == []

    def test_finds_md_files_recursively_and_sorted(self, working_dir):
        q = working_dir / "memory" / "quarantine"
        _make_entry(q / "decisions" / "b.md", "x")
        _make_entry(q / "decisions" / "a.md", "x")
        _make_entry(q / "knowledge" / "z.md", "x")
        out = mod.find_quarantined_entries(working_dir)
        names = [p.name for p in out]
        assert names == sorted(names)
        assert set(names) == {"a.md", "b.md", "z.md"}

    def test_ignores_non_md_files(self, working_dir):
        q = working_dir / "memory" / "quarantine"
        _make_entry(q / "decisions" / "real.md", "x")
        _make_entry(q / "quarantine_log.jsonl", "{}\n")
        _make_entry(q / "decisions" / "notes.txt", "x")
        out = mod.find_quarantined_entries(working_dir)
        assert [p.name for p in out] == ["real.md"]

    def test_returns_path_objects(self, working_dir):
        q = working_dir / "memory" / "quarantine"
        _make_entry(q / "decisions" / "real.md", "x")
        out = mod.find_quarantined_entries(working_dir)
        assert all(isinstance(p, pathlib.Path) for p in out)
        assert all(p.is_file() for p in out)


# ---------------------------------------------------------------------------
# append_quarantine_log
# ---------------------------------------------------------------------------

class TestAppendQuarantineLog:
    def test_creates_file_and_parent_dirs(self, working_dir):
        entry = {"ts": "2026-01-01T00:00:00Z", "action": "defer", "entry_id": "DEC-1"}
        mod.append_quarantine_log(working_dir, entry)
        log = working_dir / "memory" / "quarantine" / "quarantine_log.jsonl"
        assert log.exists()

    def test_writes_exactly_one_well_formed_json_line(self, working_dir):
        entry = {"ts": "2026-01-01T00:00:00Z", "action": "approve", "entry_id": "DEC-1"}
        mod.append_quarantine_log(working_dir, entry)
        log = working_dir / "memory" / "quarantine" / "quarantine_log.jsonl"
        raw = log.read_text(encoding="utf-8")
        # Exactly one trailing newline -> exactly one non-empty line.
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        assert len(lines) == 1
        assert json.loads(lines[0]) == entry
        assert raw.endswith("\n")

    def test_compact_separators_no_spaces(self, working_dir):
        entry = {"a": 1, "b": 2}
        mod.append_quarantine_log(working_dir, entry)
        log = working_dir / "memory" / "quarantine" / "quarantine_log.jsonl"
        line = log.read_text(encoding="utf-8").strip()
        # separators=(",", ":") -> no ", " or ": " spacing.
        assert line == '{"a":1,"b":2}'

    def test_appends_second_line_without_clobbering(self, working_dir):
        mod.append_quarantine_log(working_dir, {"n": 1})
        mod.append_quarantine_log(working_dir, {"n": 2})
        log = working_dir / "memory" / "quarantine" / "quarantine_log.jsonl"
        lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert [json.loads(ln)["n"] for ln in lines] == [1, 2]


# ---------------------------------------------------------------------------
# append_audit_log
# ---------------------------------------------------------------------------

class TestAppendAuditLog:
    def test_creates_file_under_security_dir(self, working_dir):
        entry = {"ts": "2026-01-01T00:00:00Z", "action": "audit-quarantine-review"}
        mod.append_audit_log(working_dir, entry)
        log = working_dir / "memory" / "security" / "audit_log.jsonl"
        assert log.exists()

    def test_writes_exactly_one_well_formed_json_line(self, working_dir):
        entry = {"ts": "2026-01-01T00:00:00Z", "outcome": "reject", "entry_id": "DEC-1"}
        mod.append_audit_log(working_dir, entry)
        log = working_dir / "memory" / "security" / "audit_log.jsonl"
        raw = log.read_text(encoding="utf-8")
        lines = [ln for ln in raw.splitlines() if ln.strip()]
        assert len(lines) == 1
        assert json.loads(lines[0]) == entry
        assert raw.endswith("\n")

    def test_round_trip_with_read_quarantine_log_for(self, working_dir):
        # Cross-function characterization: a record appended to the quarantine log
        # is then findable by read_quarantine_log_for via its entry_id.
        rec = {
            "ts": "2026-01-01T00:00:00Z",
            "actor": "orchestrator",
            "action": "defer",
            "entry_id": "DEC-RT",
            "resolution": "deferred",
        }
        mod.append_quarantine_log(working_dir, rec)
        out = mod.read_quarantine_log_for("DEC-RT", working_dir)
        assert len(out) == 1
        assert out[0] == rec
