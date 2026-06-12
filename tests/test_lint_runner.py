"""
Characterization + edge-case unit tests for lint_runner.py (UMS §10.5 lint surface tool).

Loaded by absolute path via importlib (stdlib-only module living outside an
importable package). Builds fixture memory/ trees under pytest tmp_path and
asserts the module's real outputs.

Run:
    python -m pytest tests/test_lint_runner.py -q
"""

from __future__ import annotations

import importlib.util
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


mod = _load("core/openclaw-adapter/scripts/lint_runner.py", "lint_runner")


# --------------------------------------------------------------------------- #
# Fixture helpers
# --------------------------------------------------------------------------- #

def _write(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# A fully-compliant DEC block using the shipped template's bold-label form.
_DEC_BOLD_TEMPLATE = """## {dec_id}: {title}

**Purpose:** Why this exists.

**Rationale:** Because reasons.

**Sound reasoning:** The logic checks out.

**Scope — CAN:** It may do these things.

**Scope — CANNOT:** It may not do these things.
"""

# A fully-compliant DEC block using heading form (### Purpose).
_DEC_HEADING_TEMPLATE = """## {dec_id}: {title}

### Purpose
Why this exists.

### Rationale
Because reasons.

### Sound reasoning
The logic checks out.

### Scope — CAN
It may do these things.

### Scope — CANNOT
It may not do these things.
"""


# --------------------------------------------------------------------------- #
# detect_harness
# --------------------------------------------------------------------------- #

class TestDetectHarness:
    def test_forced_openclaw_returns_memory_md_seed(self, tmp_path):
        harness, seed = mod.detect_harness(tmp_path, forced="openclaw")
        assert harness == "openclaw"
        assert seed == tmp_path / "MEMORY.md"

    def test_forced_claude_code_returns_index_seed(self, tmp_path):
        harness, seed = mod.detect_harness(tmp_path, forced="claude_code")
        assert harness == "claude_code"
        assert seed == tmp_path / "memory" / "MEMORY_INDEX.md"

    def test_forced_overrides_even_when_no_markers_present(self, tmp_path):
        # Empty dir, but forced openclaw still returns openclaw seed.
        harness, seed = mod.detect_harness(tmp_path, forced="openclaw")
        assert harness == "openclaw"

    def test_auto_openclaw_via_dot_openclaw_dir(self, tmp_path):
        (tmp_path / ".openclaw").mkdir()
        harness, seed = mod.detect_harness(tmp_path)
        assert harness == "openclaw"
        assert seed == tmp_path / "MEMORY.md"

    def test_auto_openclaw_via_root_files(self, tmp_path):
        _write(tmp_path / "MEMORY.md", "# memory")
        _write(tmp_path / "AGENTS.md", "# agents")
        harness, seed = mod.detect_harness(tmp_path)
        assert harness == "openclaw"

    def test_auto_openclaw_root_files_requires_both(self, tmp_path):
        # Only MEMORY.md present (no AGENTS.md) -> not enough for the root-files path.
        _write(tmp_path / "MEMORY.md", "# memory")
        harness, seed = mod.detect_harness(tmp_path)
        assert harness == "unknown"
        assert seed is None

    def test_auto_claude_code_via_rules_marker(self, tmp_path):
        _write(tmp_path / ".claude" / "rules" / "memory_protocol.md", "# proto")
        harness, seed = mod.detect_harness(tmp_path)
        assert harness == "claude_code"
        assert seed == tmp_path / "memory" / "MEMORY_INDEX.md"

    def test_auto_claude_code_via_memory_index(self, tmp_path):
        _write(tmp_path / "memory" / "MEMORY_INDEX.md", "# index")
        harness, seed = mod.detect_harness(tmp_path)
        assert harness == "claude_code"

    def test_auto_unknown_when_no_markers(self, tmp_path):
        harness, seed = mod.detect_harness(tmp_path)
        assert harness == "unknown"
        assert seed is None

    def test_openclaw_marker_takes_precedence_over_claude(self, tmp_path):
        # Both markers present; openclaw is checked first.
        (tmp_path / ".openclaw").mkdir()
        _write(tmp_path / ".claude" / "rules" / "memory_protocol.md", "# proto")
        harness, _ = mod.detect_harness(tmp_path)
        assert harness == "openclaw"


# --------------------------------------------------------------------------- #
# collect_all_entries
# --------------------------------------------------------------------------- #

class TestCollectAllEntries:
    def test_no_memory_dir_returns_empty(self, tmp_path):
        assert mod.collect_all_entries(tmp_path) == []

    def test_collects_nested_md_files(self, tmp_path):
        _write(tmp_path / "memory" / "decisions" / "decisions.md", "x")
        _write(tmp_path / "memory" / "core" / "user_profile.md", "y")
        _write(tmp_path / "memory" / "MEMORY_INDEX.md", "z")
        entries = mod.collect_all_entries(tmp_path)
        names = {p.name for p in entries}
        assert names == {"decisions.md", "user_profile.md", "MEMORY_INDEX.md"}

    def test_skips_archive_dir(self, tmp_path):
        _write(tmp_path / "memory" / "live.md", "a")
        _write(tmp_path / "memory" / "archive" / "old.md", "b")
        _write(tmp_path / "memory" / "archived" / "older.md", "c")
        names = {p.name for p in mod.collect_all_entries(tmp_path)}
        assert names == {"live.md"}

    def test_skips_hidden_directory(self, tmp_path):
        _write(tmp_path / "memory" / "visible.md", "a")
        _write(tmp_path / "memory" / ".hidden" / "secret.md", "b")
        names = {p.name for p in mod.collect_all_entries(tmp_path)}
        assert names == {"visible.md"}

    def test_skips_template_path_case_insensitive(self):
        # NOTE: the skip rule is `"template" in str(md_path).lower()`, which
        # inspects the FULL absolute path. pytest's tmp_path can itself contain
        # "template" (from the test name), which would skip everything. Build the
        # fixture under a self-managed temp dir whose path is guaranteed clean.
        import tempfile
        with tempfile.TemporaryDirectory(prefix="lintvault_") as td:
            root = pathlib.Path(td)
            assert "template" not in str(root).lower()
            _write(root / "memory" / "real.md", "a")
            _write(root / "memory" / "tpl_subdir" / "Template_Decision.md", "b")
            names = {p.name for p in mod.collect_all_entries(root)}
        assert names == {"real.md"}

    def test_non_md_files_ignored(self, tmp_path):
        _write(tmp_path / "memory" / "real.md", "a")
        _write(tmp_path / "memory" / "notes.txt", "b")
        names = {p.name for p in mod.collect_all_entries(tmp_path)}
        assert names == {"real.md"}

    def test_memory_dir_is_file_returns_empty(self, tmp_path):
        # memory exists but is a file, not a directory.
        _write(tmp_path / "memory", "not a dir")
        assert mod.collect_all_entries(tmp_path) == []


# --------------------------------------------------------------------------- #
# extract_entry_ids
# --------------------------------------------------------------------------- #

class TestExtractEntryIds:
    def test_heading_ids_all_prefixes(self):
        content = (
            "## DEC-001: a\n"
            "### FB-012: b\n"
            "## VET-003: c\n"
            "## PRJ-9: d\n"
            "## REF-7: e\n"
            "## SEC-2: f\n"
            "## LEARN-1: g\n"
            "## OBS-5: h\n"
        )
        ids = mod.extract_entry_ids(content)
        assert ids == {
            "DEC-001", "FB-012", "VET-003", "PRJ-9",
            "REF-7", "SEC-2", "LEARN-1", "OBS-5",
        }

    def test_frontmatter_id_field(self):
        content = "id: DEC-099\nother: stuff\n"
        ids = mod.extract_entry_ids(content)
        assert "DEC-099" in ids

    def test_unknown_prefix_not_matched(self):
        # XYZ- is not in the allow-list of prefixes.
        content = "## XYZ-001: heading\n"
        assert mod.extract_entry_ids(content) == set()

    def test_single_hash_not_matched(self):
        # Pattern requires ##+ (two or more), single # H1 should not match heading rule.
        content = "# DEC-001: top-level title\n"
        assert "DEC-001" not in mod.extract_entry_ids(content)

    def test_empty_content(self):
        assert mod.extract_entry_ids("") == set()

    def test_id_must_be_at_line_start(self):
        # Heading not at line start -> no match.
        content = "prose mentioning ## DEC-001: inline\n"
        assert mod.extract_entry_ids(content) == set()


# --------------------------------------------------------------------------- #
# extract_references
# --------------------------------------------------------------------------- #

class TestExtractReferences:
    def test_inline_wiki_links(self):
        content = "See [[DEC-001]] and [[FB-007]] for context."
        assert mod.extract_references(content) == {"DEC-001", "FB-007"}

    def test_related_yaml_list(self):
        content = "related: [DEC-001, DEC-002, FB-9]\n"
        assert mod.extract_references(content) == {"DEC-001", "DEC-002", "FB-9"}

    def test_related_yaml_strips_quotes(self):
        content = 'related: ["DEC-001", \'DEC-002\']\n'
        assert mod.extract_references(content) == {"DEC-001", "DEC-002"}

    def test_related_yaml_skips_non_matching_tokens(self):
        content = "related: [DEC-001, garbage, foo]\n"
        # Only DEC-001 matches the ID grammar.
        assert mod.extract_references(content) == {"DEC-001"}

    def test_supersedes_field(self):
        content = "supersedes: DEC-042\n"
        assert mod.extract_references(content) == {"DEC-042"}

    def test_combined_sources(self):
        content = (
            "supersedes: DEC-042\n"
            "related: [DEC-001]\n"
            "Body mentions [[VET-003]].\n"
        )
        assert mod.extract_references(content) == {"DEC-042", "DEC-001", "VET-003"}

    def test_empty_content(self):
        assert mod.extract_references("") == set()

    def test_unknown_prefix_inline_not_matched(self):
        assert mod.extract_references("[[ZZZ-001]]") == set()


# --------------------------------------------------------------------------- #
# check_doc_completeness — THE KEY ONE
# --------------------------------------------------------------------------- #

class TestCheckDocCompleteness:
    def _decisions_path(self, tmp_path):
        return tmp_path / "memory" / "decisions" / "decisions.md"

    def test_no_decisions_file_returns_empty(self, tmp_path):
        assert mod.check_doc_completeness(tmp_path, "claude_code") == []

    def test_bold_label_form_complete_no_findings(self, tmp_path):
        # The shipped template's bold-label form must be accepted (the #13 fix).
        _write(
            self._decisions_path(tmp_path),
            _DEC_BOLD_TEMPLATE.format(dec_id="DEC-100", title="Complete bold entry"),
        )
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert findings == []

    def test_heading_form_complete_no_findings(self, tmp_path):
        _write(
            self._decisions_path(tmp_path),
            _DEC_HEADING_TEMPLATE.format(dec_id="DEC-101", title="Complete heading entry"),
        )
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert findings == []

    def test_entry_missing_all_five_flagged_medium(self, tmp_path):
        _write(
            self._decisions_path(tmp_path),
            "## DEC-200: Bare entry\n\nJust prose, no required sections at all.\n",
        )
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert len(findings) == 1
        f = findings[0]
        assert f.check_id == "doc_completeness_gap"
        assert f.severity == "medium"  # missing >= 3
        assert "missing 5 of 5" in f.message
        # All 5 element names appear in the message.
        for el in ("Purpose", "Rationale", "Sound reasoning", "Scope — CAN", "Scope — CANNOT"):
            assert el in f.message

    def test_entry_missing_two_flagged_low(self, tmp_path):
        # Provide 3 elements, omit 2 -> severity low (missing < 3).
        text = (
            "## DEC-201: Partial entry\n\n"
            "**Purpose:** p\n\n"
            "**Rationale:** r\n\n"
            "**Sound reasoning:** s\n\n"
        )
        _write(self._decisions_path(tmp_path), text)
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert len(findings) == 1
        f = findings[0]
        assert f.severity == "low"
        assert "missing 2 of 5" in f.message
        assert "Scope — CAN" in f.message
        assert "Scope — CANNOT" in f.message

    def test_dec_install_is_skipped(self, tmp_path):
        # DEC-INSTALL has a colon (so the block regex matches) but must be skipped.
        text = (
            "## DEC-INSTALL: Installer decision\n\n"
            "No required sections here at all.\n\n"
            "## DEC-300: Other\n\n"
            "Also missing all sections.\n"
        )
        _write(self._decisions_path(tmp_path), text)
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        # Only DEC-300 should be flagged; DEC-INSTALL skipped.
        ids = {f.message.split(" ")[0] for f in findings}
        assert ids == {"DEC-300"}

    def test_scope_can_not_confused_with_cannot(self, tmp_path):
        # An entry that has CANNOT but NOT a standalone CAN should still flag "Scope — CAN".
        # (CANNOT must not accidentally satisfy the CAN matcher.)
        text = (
            "## DEC-400: Scope edge\n\n"
            "**Purpose:** p\n\n"
            "**Rationale:** r\n\n"
            "**Sound reasoning:** s\n\n"
            "**Scope — CANNOT:** only cannot present\n\n"
        )
        _write(self._decisions_path(tmp_path), text)
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert len(findings) == 1
        msg = findings[0].message
        assert "Scope — CAN" in msg
        assert "missing 1 of 5" in msg

    def test_heading_cannot_does_not_satisfy_can(self, tmp_path):
        # Heading form: '### Scope — CANNOT' must not satisfy the 'Scope — CAN' element.
        text = (
            "## DEC-401: Heading scope edge\n\n"
            "### Purpose\np\n\n"
            "### Rationale\nr\n\n"
            "### Sound reasoning\ns\n\n"
            "### Scope — CANNOT\nonly cannot\n\n"
        )
        _write(self._decisions_path(tmp_path), text)
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert len(findings) == 1
        assert "Scope — CAN" in findings[0].message
        assert "missing 1 of 5" in findings[0].message

    def test_multiple_entries_independent(self, tmp_path):
        text = (
            _DEC_BOLD_TEMPLATE.format(dec_id="DEC-500", title="Good")
            + "\n"
            + "## DEC-501: Bad\n\nNothing here.\n"
        )
        _write(self._decisions_path(tmp_path), text)
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert len(findings) == 1
        assert findings[0].message.startswith("DEC-501")

    def test_block_without_colon_not_matched(self, tmp_path):
        # The block regex requires '## DEC-...:' (colon). A header without a colon
        # is not treated as a decision block, so it is not audited.
        text = "## DEC-600 No colon here\n\nNo sections.\n"
        _write(self._decisions_path(tmp_path), text)
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert findings == []

    def test_file_path_is_relative_to_root(self, tmp_path):
        _write(self._decisions_path(tmp_path), "## DEC-700: x\n\nbare\n")
        findings = mod.check_doc_completeness(tmp_path, "claude_code")
        assert len(findings) == 1
        # Use forward-slash normalization for cross-platform comparison.
        assert findings[0].file_path.replace("\\", "/") == "memory/decisions/decisions.md"


# --------------------------------------------------------------------------- #
# check_broken_references
# --------------------------------------------------------------------------- #

class TestCheckBrokenReferences:
    def test_no_entries_returns_empty(self, tmp_path):
        assert mod.check_broken_references(tmp_path, "claude_code") == []

    def test_valid_reference_no_finding(self, tmp_path):
        _write(tmp_path / "memory" / "a.md", "## DEC-001: a\nbody\n")
        _write(tmp_path / "memory" / "b.md", "Refers to [[DEC-001]].\n")
        assert mod.check_broken_references(tmp_path, "claude_code") == []

    def test_broken_reference_flagged_medium(self, tmp_path):
        _write(tmp_path / "memory" / "a.md", "## DEC-001: a\nbody\n")
        _write(tmp_path / "memory" / "b.md", "Refers to [[DEC-999]].\n")
        findings = mod.check_broken_references(tmp_path, "claude_code")
        assert len(findings) == 1
        assert findings[0].check_id == "broken_reference"
        assert findings[0].severity == "medium"
        assert "DEC-999" in findings[0].message

    def test_exempt_external_placeholders_not_flagged(self, tmp_path):
        _write(
            tmp_path / "memory" / "b.md",
            "Refs [[DEC-INSTALL]] [[DEC-XXX]] [[DEC-NNN]].\n",
        )
        # Note: DEC-### contains '#' which the [[...]] regex ([\w-]+) won't match,
        # so it never becomes a reference in the first place.
        findings = mod.check_broken_references(tmp_path, "claude_code")
        assert findings == []

    def test_supersedes_broken_reference_flagged(self, tmp_path):
        _write(tmp_path / "memory" / "b.md", "supersedes: DEC-888\n")
        findings = mod.check_broken_references(tmp_path, "claude_code")
        assert len(findings) == 1
        assert "DEC-888" in findings[0].message

    def test_reference_to_id_in_another_file_resolves(self, tmp_path):
        # ID declared in frontmatter of one file, referenced in another.
        _write(tmp_path / "memory" / "decl.md", "id: VET-005\n")
        _write(tmp_path / "memory" / "ref.md", "uses [[VET-005]]\n")
        assert mod.check_broken_references(tmp_path, "claude_code") == []


# --------------------------------------------------------------------------- #
# check_orphan_entries
# --------------------------------------------------------------------------- #

class TestCheckOrphanEntries:
    def test_no_entries_returns_empty(self, tmp_path):
        assert mod.check_orphan_entries(tmp_path, "claude_code") == []

    def test_orphan_flagged_low(self, tmp_path):
        # DEC-050 declared, nothing references it.
        _write(tmp_path / "memory" / "a.md", "## DEC-050: lonely\nbody\n")
        findings = mod.check_orphan_entries(tmp_path, "claude_code")
        assert len(findings) == 1
        assert findings[0].check_id == "orphan_entry"
        assert findings[0].severity == "low"
        assert "DEC-050" in findings[0].message

    def test_referenced_entry_not_orphan(self, tmp_path):
        _write(tmp_path / "memory" / "a.md", "## DEC-050: linked\nbody\n")
        _write(tmp_path / "memory" / "b.md", "see [[DEC-050]]\n")
        assert mod.check_orphan_entries(tmp_path, "claude_code") == []

    def test_exempt_ids_not_flagged(self, tmp_path):
        _write(
            tmp_path / "memory" / "a.md",
            "## DEC-001: root\nbody\n\n## DEC-INSTALL: installer\nbody\n",
        )
        # Both DEC-001 and DEC-INSTALL are exempt root-of-graph ids.
        assert mod.check_orphan_entries(tmp_path, "claude_code") == []

    def test_self_reference_counts_as_incoming(self, tmp_path):
        # A file that declares DEC-060 and also references [[DEC-060]] -> not orphan
        # (the module counts any outgoing ref, including self-references).
        _write(tmp_path / "memory" / "a.md", "## DEC-060: x\nsee [[DEC-060]]\n")
        assert mod.check_orphan_entries(tmp_path, "claude_code") == []

    def test_multiple_orphans(self, tmp_path):
        _write(tmp_path / "memory" / "a.md", "## DEC-070: a\nbody\n")
        _write(tmp_path / "memory" / "b.md", "## FB-080: b\nbody\n")
        findings = mod.check_orphan_entries(tmp_path, "claude_code")
        ids = {f.message.split(" ")[0] for f in findings}
        assert ids == {"DEC-070", "FB-080"}


# --------------------------------------------------------------------------- #
# check_promotion_candidates
# --------------------------------------------------------------------------- #

class TestCheckPromotionCandidates:
    def _fb_path(self, tmp_path):
        return tmp_path / "memory" / "feedback" / "feedback.md"

    def test_no_feedback_file_returns_empty(self, tmp_path):
        assert mod.check_promotion_candidates(tmp_path, "claude_code") == []

    def test_recurrence_below_threshold_not_flagged(self, tmp_path):
        _write(
            self._fb_path(tmp_path),
            "## FB-001: thing\nrecurrence_count: 4\nbody\n",
        )
        assert mod.check_promotion_candidates(tmp_path, "claude_code") == []

    def test_recurrence_at_threshold_flagged(self, tmp_path):
        _write(
            self._fb_path(tmp_path),
            "## FB-002: thing\nrecurrence_count: 5\nbody\n",
        )
        findings = mod.check_promotion_candidates(tmp_path, "claude_code")
        assert len(findings) == 1
        assert findings[0].check_id == "promotion_candidate"
        assert findings[0].severity == "low"
        assert "FB-002" in findings[0].message
        assert "recurrence_count=5" in findings[0].message

    def test_recurrence_above_threshold_flagged(self, tmp_path):
        _write(
            self._fb_path(tmp_path),
            "## FB-003: thing\nrecurrence_count: 12\nbody\n",
        )
        findings = mod.check_promotion_candidates(tmp_path, "claude_code")
        assert len(findings) == 1
        assert "recurrence_count=12" in findings[0].message

    def test_multiple_fb_blocks_mixed(self, tmp_path):
        text = (
            "## FB-010: low\nrecurrence_count: 2\nbody\n\n"
            "## FB-011: high\nrecurrence_count: 7\nbody\n\n"
            "## FB-012: alsohigh\nrecurrence_count: 5\nbody\n"
        )
        _write(self._fb_path(tmp_path), text)
        findings = mod.check_promotion_candidates(tmp_path, "claude_code")
        ids = {f.message.split(" ")[0] for f in findings}
        assert ids == {"FB-011", "FB-012"}

    def test_fb_block_without_recurrence_not_flagged(self, tmp_path):
        _write(self._fb_path(tmp_path), "## FB-020: no count\nbody only\n")
        assert mod.check_promotion_candidates(tmp_path, "claude_code") == []


# --------------------------------------------------------------------------- #
# Placeholder checks (deferred) — characterize current no-op behavior
# --------------------------------------------------------------------------- #

class TestPlaceholderChecks:
    def test_stale_tentative_is_noop(self, tmp_path):
        _write(tmp_path / "memory" / "decisions" / "decisions.md", "## DEC-1: x\n")
        assert mod.check_stale_tentative(tmp_path, "claude_code") == []

    def test_naming_inconsistencies_is_noop(self, tmp_path):
        _write(tmp_path / "memory" / "decisions" / "decisions.md", "## DEC-1: x\n")
        assert mod.check_naming_inconsistencies(tmp_path, "claude_code") == []


# --------------------------------------------------------------------------- #
# LintFinding.to_dict
# --------------------------------------------------------------------------- #

class TestLintFindingToDict:
    def test_full_serialization(self):
        f = mod.LintFinding(
            check_id="orphan_entry",
            severity="low",
            message="msg",
            file_path="memory/a.md",
            line=42,
        )
        assert f.to_dict() == {
            "check_id": "orphan_entry",
            "severity": "low",
            "message": "msg",
            "file_path": "memory/a.md",
            "line": 42,
        }

    def test_defaults(self):
        f = mod.LintFinding("c", "info", "m")
        d = f.to_dict()
        assert d["file_path"] == ""
        assert d["line"] == 0

    def test_is_json_serializable(self):
        import json
        f = mod.LintFinding("c", "high", "m", "p", 1)
        # Round-trips through json without error.
        assert json.loads(json.dumps(f.to_dict())) == f.to_dict()


# --------------------------------------------------------------------------- #
# Module-level constants sanity
# --------------------------------------------------------------------------- #

def test_severity_levels_order():
    assert mod.SEVERITY_LEVELS == ["info", "low", "medium", "high", "critical"]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
