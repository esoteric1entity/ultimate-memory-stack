#!/usr/bin/env python3
"""
lint_runner.py — Standalone MEMORY_PROTOCOL §10.5 Lint Surface Tool
=====================================================================

Standalone runner for Memory Protocol §10.5 Lint checks (Karpathy LLM Wiki Pattern
+ Option C extensions). Invoked manually or on a cron schedule.

SURFACE-ONLY by design — NEVER auto-mutates content. Emits findings as suggestions.

Multi-platform (v3.5 multi-platform lint patch):
  - Auto-detects harness via .openclaw/ vs .claude/rules/memory_protocol.md presence
  - Runs equivalent checks on both Claude Code and OpenClaw vault shapes
  - Optional --seed-file flag for explicit override

Lint checks implemented (Option C extensions + original §10.5):
  1. Orphan entries (no incoming references) — IMPLEMENTED v3.5
  2. Broken references — IMPLEMENTED
  3. Stale TENTATIVE/EXPLORATORY decisions — placeholder (session-tracking deferred)
  4. Stale webfetch citations — placeholder
  5. Cross-entry contradictions (T3+ only) — deferred to v3.6+
  6. Missing concept entries (T3+ only) — deferred to v3.6+
  7. [Option C] Promotion candidates — IMPLEMENTED (FB recurrence-count signal)
  8. [Option C] Pattern condensation opportunities — deferred to v3.6+ (LLM-assisted)
  9. [Option C] Naming inconsistencies — deferred to v3.6+ (LLM-assisted)
 10. [Option C] Doc completeness gaps (5-element documentation audit) — IMPLEMENTED
 11. [Option C] Standing-rule candidates — deferred to v3.6+ (LLM-assisted)

Silent-recall-failure checks (SCHEMA_lint.md §13) — a pointer that promises
content which isn't there, or content nothing points at:
 12. Dangling archive pointers (ARCHIVE_INDEX one-liner → missing entry) — GATING
 13. Unreachable memory files (content under memory/ that MEMORY_INDEX.md never cites)

Design principles: ideal-first design; Karpathy Lint pattern (surface-only);
Option C check extensions; v3.5 multi-platform lint patch.

Usage:
    python lint_runner.py <workspace-root> [options]
    python lint_runner.py /home/user/.openclaw/workspace           # OpenClaw vault
    python lint_runner.py ~/workspace            # Claude Code vault
    python lint_runner.py ~/some-vault --seed-file MEMORY.md       # explicit override
    python lint_runner.py ~/vault --severity high                  # filter
    python lint_runner.py ~/vault --output jsonl                   # append to lint_runs.jsonl

Exit codes:
    0 = success (with or without findings)
    1 = invalid arguments
    2 = workspace-root invalid or harness undetectable
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Legacy consoles (Windows cp1252, non-UTF-8 locales elsewhere) can't encode
# all output glyphs — force UTF-8 so a finding's text can never crash the
# lint run (UnicodeEncodeError). Same guard as general-edition/setup.py.
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


SEVERITY_LEVELS = ["info", "low", "medium", "high", "critical"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="MEMORY_PROTOCOL §10.5 Lint runner (surface-only; multi-platform Claude Code + OpenClaw)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Multi-platform: auto-detects harness via .openclaw/ vs .claude/rules/ markers. "
            "Use --seed-file to override detection."
        ),
    )
    p.add_argument("workspace_root", help="Path to workspace root (Claude Code or OpenClaw)")
    p.add_argument(
        "--severity",
        choices=["all", "info", "low", "medium", "high", "critical"],
        default="all",
        help="Filter findings by minimum severity (default: all)",
    )
    p.add_argument(
        "--output",
        choices=["stdout", "json", "jsonl"],
        default="stdout",
        help="Output format (default: stdout)",
    )
    p.add_argument(
        "--fail-on",
        choices=["none", "info", "low", "medium", "high", "critical"],
        default="high",
        help=(
            "Exit non-zero (1) when a finding at or above this severity is present. "
            "Default: high — an over-budget always-loaded set is a real data-loss risk, "
            "not an advisory. Use --fail-on none for the pre-v4 advisory-only behavior."
        ),
    )
    p.add_argument(
        "--seed-file",
        default=None,
        help="Explicit seed-file path override (e.g., MEMORY.md or MEMORY_INDEX.md). Default: auto-detect.",
    )
    p.add_argument(
        "--harness",
        choices=["auto", "openclaw", "claude_code"],
        default="auto",
        help="Force harness type. Default: auto-detect from workspace markers.",
    )
    return p.parse_args()


def detect_harness(root: Path, forced: str = "auto") -> tuple[str, Path | None]:
    """
    Auto-detect which harness the workspace belongs to.

    Returns (harness_name, seed_file_path).
    harness_name: "openclaw" | "claude_code" | "unknown"
    seed_file_path: Path to canonical seed file (MEMORY.md or MEMORY_INDEX.md), or None
    """
    if forced == "openclaw":
        return ("openclaw", root / "MEMORY.md")
    if forced == "claude_code":
        return ("claude_code", root / "memory" / "MEMORY_INDEX.md")

    # Auto-detection via marker files
    has_openclaw_marker = (root / ".openclaw").is_dir()
    has_openclaw_root_files = (root / "MEMORY.md").is_file() and (root / "AGENTS.md").is_file()
    has_claude_code_marker = (root / ".claude" / "rules" / "memory_protocol.md").is_file()
    has_claude_code_index = (root / "memory" / "MEMORY_INDEX.md").is_file()

    if has_openclaw_marker or has_openclaw_root_files:
        return ("openclaw", root / "MEMORY.md")
    if has_claude_code_marker or has_claude_code_index:
        return ("claude_code", root / "memory" / "MEMORY_INDEX.md")
    return ("unknown", None)


class LintFinding:
    def __init__(self, check_id: str, severity: str, message: str, file_path: str = "", line: int = 0) -> None:
        self.check_id = check_id
        self.severity = severity
        self.message = message
        self.file_path = file_path
        self.line = line

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "severity": self.severity,
            "message": self.message,
            "file_path": self.file_path,
            "line": self.line,
        }


def collect_all_entries(root: Path) -> list[Path]:
    """
    Walk memory/ subtree and return all .md entry files.

    Returns paths to entries that look like they have content (not pure templates).
    Skips: archived files, template files, hidden directories.
    """
    entries = []
    memory_dir = root / "memory"
    if not memory_dir.is_dir():
        return entries

    for md_path in memory_dir.rglob("*.md"):
        # Skip archived, template, and hidden directories
        parts = md_path.relative_to(memory_dir).parts
        if any(p.startswith(".") for p in parts):
            continue
        if "archive" in parts or "archived" in parts:
            continue
        if "template" in str(md_path).lower():
            continue
        entries.append(md_path)
    return entries


def extract_entry_ids(content: str) -> set[str]:
    """Extract all entry IDs declared in a file (DEC-NNN, FB-NNN, VET-NNN, etc.)."""
    ids = set()
    # Common ID patterns at section headings
    for match in re.finditer(r"^##+ ((?:DEC|FB|VET|PRJ|REF|SEC|LEARN|OBS)-[\w-]+)", content, re.MULTILINE):
        ids.add(match.group(1))
    # IDs in YAML frontmatter (id: field)
    for match in re.finditer(r"^id:\s*([\w-]+)", content, re.MULTILINE):
        ids.add(match.group(1).strip())
    return ids


def extract_references(content: str) -> set[str]:
    """Extract all inline references [[ID]] and YAML `related: [...]` references from content."""
    refs = set()
    # Inline wiki-link references
    for match in re.finditer(r"\[\[((?:DEC|FB|VET|PRJ|REF|SEC|LEARN|OBS)-[\w-]+)\]\]", content):
        refs.add(match.group(1))
    # YAML related: list (single line: related: [DEC-001, DEC-002])
    for match in re.finditer(r"^related:\s*\[([^\]]+)\]", content, re.MULTILINE):
        for ref in match.group(1).split(","):
            ref = ref.strip().strip('"').strip("'")
            if re.match(r"^(?:DEC|FB|VET|PRJ|REF|SEC|LEARN|OBS)-[\w-]+$", ref):
                refs.add(ref)
    # YAML supersedes: field
    for match in re.finditer(r"^supersedes:\s*((?:DEC|FB|VET|PRJ|REF|SEC|LEARN|OBS)-[\w-]+)", content, re.MULTILINE):
        refs.add(match.group(1))
    return refs


def check_orphan_entries(root: Path, harness: str) -> list[LintFinding]:
    """
    Lint Check 1: Orphan entries (entries with no incoming references).

    Walks memory/**/*.md, builds entry-id graph, identifies entries that:
      - Declare an ID (e.g., DEC-042)
      - Have ZERO incoming references from any other entry

    NEW in v3.5. Multi-platform: works on both Claude Code and OpenClaw vault shapes.
    """
    findings: list[LintFinding] = []
    entries = collect_all_entries(root)
    if not entries:
        return findings

    # Build maps: entry_id → declaring file, and incoming-reference count per entry_id
    declaring_file: dict[str, Path] = {}
    incoming_refs: dict[str, int] = {}

    for entry_path in entries:
        try:
            content = entry_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        # Track IDs declared in this file
        for entry_id in extract_entry_ids(content):
            declaring_file.setdefault(entry_id, entry_path)
            incoming_refs.setdefault(entry_id, 0)

        # Track outgoing references — each one becomes an incoming for the target
        for ref_id in extract_references(content):
            incoming_refs[ref_id] = incoming_refs.get(ref_id, 0) + 1

    # Identify orphans: declared but zero incoming refs
    # Exclude very common entries that are root-of-graph by design (e.g., DEC-001, root user_profile)
    exempt_ids = {"DEC-001", "DEC-INSTALL"}

    for entry_id, count in incoming_refs.items():
        if count > 0:
            continue
        if entry_id in exempt_ids:
            continue
        if entry_id not in declaring_file:
            continue
        # Skip if entry was just declared this run as a side effect (e.g., placeholder IDs)
        findings.append(
            LintFinding(
                check_id="orphan_entry",
                severity="low",
                message=f"{entry_id} has zero incoming references (no [[ID]] or related: pointing to it)",
                file_path=str(declaring_file[entry_id].relative_to(root)),
            )
        )
    return findings


def check_broken_references(root: Path, harness: str) -> list[LintFinding]:
    """Lint Check 2: broken [[ID]] or supersedes: references — multi-platform via collect_all_entries."""
    findings = []
    entries = collect_all_entries(root)
    if not entries:
        return findings

    all_declared_ids: set[str] = set()
    file_references: dict[Path, set[str]] = {}

    for entry_path in entries:
        try:
            content = entry_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        all_declared_ids.update(extract_entry_ids(content))
        file_references[entry_path] = extract_references(content)

    # External / known placeholder references that aren't expected to be in this vault
    exempt_external = {"DEC-INSTALL", "DEC-XXX", "DEC-###", "DEC-NNN"}

    for entry_path, refs in file_references.items():
        for ref in refs:
            if ref in all_declared_ids or ref in exempt_external:
                continue
            findings.append(
                LintFinding(
                    check_id="broken_reference",
                    severity="medium",
                    message=f"Reference {ref} points to non-existent entry",
                    file_path=str(entry_path.relative_to(root)),
                )
            )
    return findings


def check_doc_completeness(root: Path, harness: str) -> list[LintFinding]:
    """Lint Check 10 (Option C): 5-element documentation-discipline audit — multi-platform."""
    findings = []
    decisions_md_candidates = [
        root / "memory" / "decisions" / "decisions.md",
    ]
    target_files = [p for p in decisions_md_candidates if p.exists()]
    if not target_files:
        return findings

    # The 5 discipline elements may appear as headings (### Purpose) or as the
    # shipped template's bold labels (**Purpose:**) — accept both (#13 fix,
    # 2026-06-11: heading-only matching flagged every template-conformant
    # entry as missing all 5). Matcher mirrored in heartbeat_compactor.py.
    required_elements = ["Purpose", "Rationale", "Sound reasoning", "Scope — CAN", "Scope — CANNOT"]

    def _has_element(block: str, element: str) -> bool:
        esc = re.escape(element)
        return re.search(rf"(?m)^\s*(?:###\s*{esc}\b|\*\*{esc}:?\*\*)", block) is not None

    for decisions_md in target_files:
        try:
            content = decisions_md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for match in re.finditer(r"^## (DEC-[\w-]+):.*?(?=^## DEC-|\Z)", content, re.MULTILINE | re.DOTALL):
            block = match.group(0)
            dec_id = match.group(1)
            if dec_id in ("DEC-INSTALL",):
                continue
            missing = [e for e in required_elements if not _has_element(block, e)]
            if missing:
                findings.append(
                    LintFinding(
                        check_id="doc_completeness_gap",
                        severity="medium" if len(missing) >= 3 else "low",
                        message=f"{dec_id} missing {len(missing)} of 5 required documentation sections: {', '.join(missing)}",
                        file_path=str(decisions_md.relative_to(root)),
                    )
                )
    return findings


def check_stale_tentative(root: Path, harness: str, threshold_sessions: int = 20) -> list[LintFinding]:
    """Lint Check 3: TENTATIVE entries not promoted in N sessions. (Placeholder — session-tracking deferred.)"""
    return []


def check_promotion_candidates(root: Path, harness: str) -> list[LintFinding]:
    """Lint Check 7 (Option C): patterns ready for promotion based on FB recurrence — multi-platform."""
    findings = []
    feedback_md = root / "memory" / "feedback" / "feedback.md"
    if not feedback_md.exists():
        return findings

    try:
        content = feedback_md.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return findings

    fb_blocks = re.finditer(
        r"^## FB-[\w-]+:.*?recurrence_count:\s*(\d+).*?(?=^## FB-|\Z)",
        content,
        re.MULTILINE | re.DOTALL,
    )
    for match in fb_blocks:
        count = int(match.group(1))
        if count >= 5:
            id_match = re.search(r"^## (FB-[\w-]+):", match.group(0))
            if id_match:
                findings.append(
                    LintFinding(
                        check_id="promotion_candidate",
                        severity="low",
                        message=f"{id_match.group(1)} has recurrence_count={count}; consider promoting to standing rule",
                        file_path=str(feedback_md.relative_to(root)),
                    )
                )
    return findings


def check_naming_inconsistencies(root: Path, harness: str) -> list[LintFinding]:
    """Lint Check 9 (Option C): naming inconsistencies. (Placeholder — LLM-assisted deferred to v3.6+.)"""
    return []


# ---------------------------------------------------------------------------
# Tiering checks (v4.0.0 hot/cold backport) — SCHEMA_lint.md §13.
# All fire at severity "low". Claude-Code-taxonomy-specific (product memory/
# layout) — no-op on OpenClaw harness (same implicit-gating pattern the
# existing checks above already use: paths that don't exist there).
# ---------------------------------------------------------------------------

TIERED_CATEGORIES = ("sessions", "decisions", "feedback")

# MEMORY_INDEX.md Category Summary table row labels for each tiered category
# (MEMORY_INDEX.template.md's "| Category | File | Entries | Archived | ... |").
CATEGORY_LABELS: dict[str, str] = {
    "sessions": "Sessions",
    "decisions": "Decisions",
    "feedback": "Feedback",
}

# §11 File Size Limits caps (MEMORY_PROTOCOL.md §11 table) — hardcoded per
# SCHEMA_lint.md §13 implementation note 1 (parsing the markdown table is more
# fragile than this documented drift risk). A future §11 cap change must also
# update this dict. Path is relative to memory/. Value = (line_cap, remedy_text).
SECTION11_CAPS: dict[str, tuple[int, str]] = {
    "sessions/session_state.md": (1500, "archive old summaries (EXTENDED §Tiering)"),
    "decisions/decisions.md": (1500, "archive FINALs >20 sessions old (EXTENDED §Tiering)"),
    "feedback/feedback.md": (300, "consolidate into standing rules, then rotate superseded originals (EXTENDED §Tiering)"),
    "projects/project_context.md": (400, "split to per-slug memory-banks"),
    "user/user_profile.md": (100, "consolidate"),
    "security/vetting_log.md": (400, "archive entries >1yr"),
    "references/references.md": (100, "split by domain"),
    "MEMORY_INDEX.md": (150, "keep pointers only"),
}


def _load_eager_set_budget(root: Path) -> int:
    """Defensive, limited read of PROFILE.md then USER_OVERRIDES.md frontmatter
    for eager_set_budget_bytes. Defaults to 80000 on absence or any parse
    failure — the runner had zero PROFILE/overrides-reading infrastructure
    before this check (SCHEMA_lint.md §13 implementation note 3)."""
    default = 80000
    value = default
    # Anchored to end-of-line (optionally a trailing comment) so a value that
    # ISN'T a bare integer — "1_000" (Python-literal habit), "80 000" — fails
    # to match and falls back to the default instead of silently truncating
    # to its leading digits (F1).
    pattern = re.compile(r"^eager_set_budget_bytes:\s*(\d+)\s*(?:#.*)?$", re.MULTILINE)

    for profile_path in sorted(root.glob("ultimate-memory-stack/*-edition/PROFILE.md")):
        try:
            head = profile_path.read_text(encoding="utf-8")[:2000]
            match = pattern.search(head)
            if match:
                value = int(match.group(1))
        except (OSError, UnicodeDecodeError, ValueError):
            pass

    overrides_path = root / "memory" / "user" / "USER_OVERRIDES.md"
    if overrides_path.exists():
        try:
            content = overrides_path.read_text(encoding="utf-8")
            match = pattern.search(content)
            if match:
                value = int(match.group(1))
        except (OSError, UnicodeDecodeError, ValueError):
            pass

    return value


def collect_archive_entry_ids(archive_file: Path) -> set[str]:
    """Extract entry IDs from a memory/archive/<category>/<category>-archive.md
    file. Dedicated walker — collect_all_entries() deliberately SKIPS any path
    containing "archive"/"archived" (correct for the 6 original checks, unusable
    here per SCHEMA_lint.md §13 implementation note 2). Does not change that
    walker's semantics."""
    if not archive_file.exists():
        return set()
    try:
        content = archive_file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return set()
    return extract_entry_ids(content)


def extract_archive_index_ids(index_file: Path) -> set[str]:
    """Extract entry IDs listed as one-liners in an ARCHIVE_INDEX.md
    (`- <ID> (<date>): ...` lines)."""
    if not index_file.exists():
        return set()
    try:
        content = index_file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return set()
    ids = set()
    for match in re.finditer(r"^-\s+((?:DEC|FB|SESSION)-[\w-]+)\s*\(", content, re.MULTILINE):
        ids.add(match.group(1))
    return ids


def check_eager_set_over_budget(root: Path, harness: str) -> list[LintFinding]:
    """Tiering check: summed live always-load bytes vs eager_set_budget_bytes
    (default 80,000) — an ongoing live-vault advisory, distinct from the
    fresh-install release gate (EXTENDED §E12.5)."""
    findings: list[LintFinding] = []
    memory_dir = root / "memory"
    if not memory_dir.is_dir():
        return findings

    always_load = [
        root / ".claude" / "rules" / "memory_protocol.md",
        memory_dir / "sessions" / "session_state.md",
        memory_dir / "user" / "user_profile.md",
        memory_dir / "MEMORY_INDEX.md",
    ]
    total = 0
    found_any = False
    for p in always_load:
        if p.exists():
            try:
                total += p.stat().st_size
                found_any = True
            except OSError:
                pass
    if not found_any:
        return findings

    budget = _load_eager_set_budget(root)
    if total > budget:
        findings.append(
            LintFinding(
                check_id="eager_set_over_budget",
                # "high", not "low": an over-budget always-loaded set is the
                # silent-truncation risk — content past a harness's load limit
                # is dropped without warning on the next session. This is the
                # one tiering finding that must be able to FAIL a run
                # (see --fail-on and SCHEMA_lint.md §14).
                severity="high",
                message=(
                    f"Live always-loaded set is {total:,} bytes, over the {budget:,}-byte "
                    f"eager_set_budget_bytes ceiling by {total - budget:,} bytes — rotate "
                    "sessions/decisions/feedback to cold storage before the next session "
                    "(EXTENDED §Tiering). Content past a harness load limit is dropped silently."
                ),
            )
        )
    return findings


def check_file_nearing_cap(root: Path, harness: str) -> list[LintFinding]:
    """Tiering check: a §11-capped file exceeds ~80% of its line cap."""
    findings: list[LintFinding] = []
    memory_dir = root / "memory"
    if not memory_dir.is_dir():
        return findings

    for rel_path, (cap, remedy) in SECTION11_CAPS.items():
        p = memory_dir / rel_path
        if not p.exists():
            continue
        try:
            line_count = sum(1 for _ in p.open(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            continue
        if line_count >= cap * 0.8:
            findings.append(
                LintFinding(
                    check_id="file_nearing_cap",
                    severity="low",
                    message=f"{rel_path} is {line_count}/{cap} lines (§11 cap) — remedy: {remedy}",
                    file_path=str(p.relative_to(root)),
                )
            )
    return findings


def check_archive_unindexed(root: Path, harness: str) -> list[LintFinding]:
    """Tiering check: an archive file has entry sections not listed in its
    category's ARCHIVE_INDEX.md."""
    findings: list[LintFinding] = []
    for category in TIERED_CATEGORIES:
        archive_dir = root / "memory" / "archive" / category
        archive_file = archive_dir / f"{category}-archive.md"
        archived_ids = collect_archive_entry_ids(archive_file)
        if not archived_ids:
            continue
        indexed_ids = extract_archive_index_ids(archive_dir / "ARCHIVE_INDEX.md")
        for missing_id in sorted(archived_ids - indexed_ids):
            findings.append(
                LintFinding(
                    check_id="archive_unindexed",
                    severity="low",
                    message=f"{missing_id} exists in {category}-archive.md but is not listed in ARCHIVE_INDEX.md",
                    file_path=str(archive_file.relative_to(root)),
                )
            )
    return findings


def _parse_memory_index_archived_column(content: str, category_label: str) -> int | None:
    """Extract the Archived-column integer for a category's row in
    MEMORY_INDEX.md's Category Summary table (`| Category | File | Entries |
    Archived | Last Updated | Last Accessed |`). Returns None if the row is
    absent, not yet tiered ("—"), or the cell isn't a plain integer."""
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0].lower() == category_label.lower() and cells[3].isdigit():
            return int(cells[3])
    return None


def check_archive_count_drift(root: Path, harness: str) -> list[LintFinding]:
    """Tiering check: a hot-side "Older entries: ... (N entries)" pointer, or
    MEMORY_INDEX.md's Archived column, doesn't match the actual
    ARCHIVE_INDEX.md entry count (SCHEMA_lint.md §13 — both sources, checked
    independently; either can drift on its own)."""
    findings: list[LintFinding] = []
    category_files = {
        "sessions": root / "memory" / "sessions" / "session_state.md",
        "decisions": root / "memory" / "decisions" / "decisions.md",
        "feedback": root / "memory" / "feedback" / "feedback.md",
    }
    memory_index_file = root / "memory" / "MEMORY_INDEX.md"
    memory_index_content: str | None = None
    if memory_index_file.exists():
        try:
            memory_index_content = memory_index_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            memory_index_content = None

    for category, hot_file in category_files.items():
        index_file = root / "memory" / "archive" / category / "ARCHIVE_INDEX.md"
        if not index_file.exists():
            continue
        actual_count = len(extract_archive_index_ids(index_file))

        if hot_file.exists():
            try:
                hot_content = hot_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                hot_content = None
            if hot_content is not None:
                # Case-insensitive; scan a window after the phrase for the
                # FIRST "(N entries)"-shaped parenthetical, tolerating an
                # intervening parenthetical (e.g. "(archived)") or a line
                # wrap before the count (F3 — the old inline regex was
                # defeated by any of these wording drifts).
                phrase = re.search(r"older\s+entries", hot_content, re.IGNORECASE)
                if phrase:
                    tail = hot_content[phrase.end():phrase.end() + 300]
                    count_match = re.search(r"\(\s*(\d+)\s*entr(?:y|ies)\s*\)", tail, re.IGNORECASE)
                    if count_match:
                        pointer_count = int(count_match.group(1))
                        if pointer_count != actual_count:
                            findings.append(
                                LintFinding(
                                    check_id="archive_count_drift",
                                    severity="low",
                                    message=(
                                        f"{category}: hot-side pointer says {pointer_count} archived entries "
                                        f"but ARCHIVE_INDEX.md has {actual_count}"
                                    ),
                                    file_path=str(hot_file.relative_to(root)),
                                )
                            )

        if memory_index_content is not None:
            archived_value = _parse_memory_index_archived_column(
                memory_index_content, CATEGORY_LABELS[category]
            )
            if archived_value is not None and archived_value != actual_count:
                findings.append(
                    LintFinding(
                        check_id="archive_count_drift",
                        severity="low",
                        message=(
                            f"{category}: MEMORY_INDEX.md Archived column says {archived_value} "
                            f"but ARCHIVE_INDEX.md has {actual_count}"
                        ),
                        file_path=str(memory_index_file.relative_to(root)),
                    )
                )
    return findings


def check_archive_pointer_dangling(root: Path, harness: str) -> list[LintFinding]:
    """Tiering check: an ARCHIVE_INDEX.md one-liner names an entry that is NOT
    present in that category's archive file — the cold index promises a rotated
    entry is still findable, and it is not.

    Exact inverse of `archive_unindexed`, and the severities are deliberately
    ASYMMETRIC:
      - `archive_unindexed` (low): the CONTENT exists, the pointer is missing.
        A bookkeeping lapse — nothing has been lost.
      - `archive_pointer_dangling` (high): the POINTER exists, the content is
        gone. This is precisely the failure EXTENDED §E12.2's "loss-proof by
        construction" states cannot happen, and the reader is told the memory
        is one on-demand read away when it no longer exists. Silent recall
        failure — the same class as `eager_set_over_budget`, so it gates
        (see --fail-on and SCHEMA_lint.md §14).

    Deliberately conservative — a gating check must not cry wolf. An ID counts
    as present if EITHER structured extraction finds it OR it appears anywhere
    in the archive file as a literal string. That admits a false NEGATIVE (an
    ID mentioned only inside another entry's prose suppresses the finding) and
    excludes false positives. For a gate, that is the correct direction.

    Anchors (the `→ <file>#<anchor>` tail) are deliberately NOT validated:
    the entry's PRESENCE is what proves the content survived, while
    heading-slug derivation is fragile enough to have produced a wrong "fix"
    in this project's own history. Presence is the invariant; the anchor is
    navigation. Do not "upgrade" this to anchor matching without a fixture
    proving the slug rule on real rotated headings.
    """
    findings: list[LintFinding] = []
    for category in TIERED_CATEGORIES:
        archive_dir = root / "memory" / "archive" / category
        index_file = archive_dir / "ARCHIVE_INDEX.md"
        if index_file.exists():
            # Probe readability FIRST: extract_archive_index_ids() returns an
            # empty set on a decode/OS error, which is indistinguishable from
            # "index lists nothing" and would make the gate pass an unreadable
            # cold index. Same reasoning as the archive-file branch below.
            try:
                index_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as exc:
                findings.append(
                    LintFinding(
                        check_id="archive_pointer_dangling",
                        severity="high",
                        message=(
                            f"ARCHIVE_INDEX.md for {category} could not be read "
                            f"({type(exc).__name__}) — the cold index cannot be verified, so no "
                            "claim that rotated entries remain findable can be trusted "
                            "(re-save as UTF-8)"
                        ),
                        file_path=str(index_file.relative_to(root)),
                    )
                )
                continue
        indexed_ids = extract_archive_index_ids(index_file)
        if not indexed_ids:
            # No index, or an empty one (the fresh-install state) — nothing is
            # being promised, so nothing can dangle.
            continue

        archive_file = archive_dir / f"{category}-archive.md"
        if not archive_file.exists():
            for missing_id in sorted(indexed_ids):
                findings.append(
                    LintFinding(
                        check_id="archive_pointer_dangling",
                        severity="high",
                        message=(
                            f"ARCHIVE_INDEX.md lists {missing_id} but {category}-archive.md "
                            "does not exist — the indexed entry is unrecoverable from this "
                            "vault (EXTENDED §E12.2 rotation is CUT-then-APPEND; the archive "
                            "file must exist before the one-liner is written)"
                        ),
                        file_path=str(index_file.relative_to(root)),
                    )
                )
            continue

        try:
            raw = archive_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            # Do NOT `continue` here. Every other check treats an unreadable
            # file as "nothing to report", which is right for an advisory. For
            # a GATE it is the worst possible behavior: one stray cp1252 byte
            # from a Notepad edit would silently switch off the check that
            # exists to catch corruption, precisely when the vault is already
            # damaged. Unverifiable is not the same as clean.
            findings.append(
                LintFinding(
                    check_id="archive_pointer_dangling",
                    severity="high",
                    message=(
                        f"{category}-archive.md could not be read ({type(exc).__name__}), so the "
                        f"{len(indexed_ids)} entr{'y' if len(indexed_ids) == 1 else 'ies'} promised by "
                        "ARCHIVE_INDEX.md cannot be verified — treat as unrecoverable until the file "
                        "is readable (re-save as UTF-8)"
                    ),
                    file_path=str(archive_file.relative_to(root)),
                )
            )
            continue
        present_ids = extract_entry_ids(raw)
        for missing_id in sorted(indexed_ids):
            if missing_id in present_ids or missing_id in raw:
                continue
            findings.append(
                LintFinding(
                    check_id="archive_pointer_dangling",
                    severity="high",
                    message=(
                        f"ARCHIVE_INDEX.md lists {missing_id} but no such entry exists in "
                        f"{category}-archive.md — the index promises a rotated entry that is "
                        "gone (EXTENDED §E12.2 'loss-proof by construction')"
                    ),
                    file_path=str(index_file.relative_to(root)),
                )
            )
    return findings


# Paths under memory/ that are NOT memory entries and so are never expected to
# appear in MEMORY_INDEX.md (see check_unreachable_memory_file).
UNREACHABLE_EXEMPT_DIRS = ("archive", "quarantine")
UNREACHABLE_EXEMPT_RELPATHS = {
    "MEMORY_INDEX.md",              # the index itself
    "MEMORY_PROTOCOL_EXTENDED.md",  # on-demand protocol doc installed at the vault root
    "user/USER_OVERRIDES.md",       # user configuration, created once (E4.3) — not an entry
}


def _index_references(index_text: str, rel_posix: str) -> bool:
    """True if MEMORY_INDEX.md reaches `rel_posix` (a memory/-relative POSIX
    path) either directly or via any ANCESTOR DIRECTORY it points at.

    Directory-level reachability is required, not a nicety: SCHEMA_A3
    per-project memory banks are registered in MEMORY_INDEX.template.md as
    directories (`projects/<slug>/memory-bank/`), and that template states
    outright that the index summarizes while full state lives in the bank. An
    exact-path-only test would flag all six Cline convention files for every
    project on every run — noise from day one, on the most common real layout.

    An ancestor counts only when the index names the DIRECTORY itself: the
    match must be followed by a character that cannot continue a path segment.
    Otherwise the Category Summary's `projects/project_context.md` row would
    make the bare prefix `projects/` match and silently exempt everything
    beneath it.
    """
    if rel_posix in index_text:
        return True
    segments = rel_posix.split("/")[:-1]
    for depth in range(len(segments), 0, -1):
        prefix = "/".join(segments[:depth]) + "/"
        start = 0
        while True:
            hit = index_text.find(prefix, start)
            if hit == -1:
                break
            after = hit + len(prefix)
            if after >= len(index_text) or not (
                index_text[after].isalnum() or index_text[after] in "-_."
            ):
                return True
            start = hit + 1
    return False


def _has_body_content(text: str) -> bool:
    """True if `text` has at least one line of actual content — i.e. a line
    that is not blank, a heading, a horizontal rule, a blockquote header, or a
    YAML frontmatter delimiter. Distinguishes a written-in file from a bare
    scaffold so `check_unreachable_memory_file` doesn't flag empty stubs."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", ">", "---", "***", "___", "```")):
            continue
        return True
    return False


def check_unreachable_memory_file(root: Path, harness: str) -> list[LintFinding]:
    """Tiering check: a fact-bearing file under memory/ that MEMORY_INDEX.md
    never references — content that is present on disk but unreachable through
    the index an agent actually reads.

    The complement of the archive-side checks: `archive_unindexed` covers the
    cold tier, this covers the hot tier. MEMORY_INDEX.md is the master registry
    (core §1.3); a file no row points at is effectively invisible at recall
    time even though nothing was deleted.

    NO-OPS when MEMORY_INDEX.md is absent. A fresh install ships no index at
    all (it is written by the agent on first use), and "unreachable" is
    meaningless without something to be reachable FROM — inferring one would
    make every fresh install fire on day zero.

    Severity `low`, non-blocking: an unindexed file is hard to find, not lost,
    and legitimate reasons to keep a file out of the index exist. Matching is a
    plain substring test on the memory/-relative POSIX path, so it is
    insensitive to whether the row backticks the path (MEMORY_INDEX.template.md
    distinguishes backticked "Active" rows from plain-text "Future" rows — both
    count as a reference here).
    """
    findings: list[LintFinding] = []
    memory_dir = root / "memory"
    index_file = memory_dir / "MEMORY_INDEX.md"
    if not index_file.is_file():
        return findings
    try:
        index_text = index_file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return findings

    for md_path in sorted(memory_dir.rglob("*.md")):
        rel = md_path.relative_to(memory_dir)
        parts = rel.parts
        if any(p.startswith(".") for p in parts):
            continue
        if any(p in UNREACHABLE_EXEMPT_DIRS for p in parts[:-1]):
            continue
        if "template" in str(rel).lower():
            continue
        rel_posix = rel.as_posix()
        if rel_posix in UNREACHABLE_EXEMPT_RELPATHS:
            continue
        if _index_references(index_text, rel_posix):
            continue
        try:
            content = md_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not _has_body_content(content):
            continue
        findings.append(
            LintFinding(
                check_id="unreachable_memory_file",
                severity="low",
                message=(
                    f"{rel_posix} has content but is referenced nowhere in MEMORY_INDEX.md "
                    "— it is on disk but unreachable through the master index at recall time; "
                    "add a Category Summary row or a Quick Access pointer"
                ),
                file_path=str(md_path.relative_to(root)),
            )
        )
    return findings


def check_archive_index_missing(root: Path, harness: str) -> list[LintFinding]:
    """Tiering check: memory/archive/<category>/ is non-empty (spec §S6
    wording) but has no ARCHIVE_INDEX.md. Fires on ANY file other than
    ARCHIVE_INDEX.md itself, not just the conventional <category>-archive.md
    (F4 — a differently-named or extra file in the dir used to go undetected)."""
    findings: list[LintFinding] = []
    for category in TIERED_CATEGORIES:
        archive_dir = root / "memory" / "archive" / category
        if not archive_dir.is_dir():
            continue
        index_file = archive_dir / "ARCHIVE_INDEX.md"
        if index_file.exists():
            continue
        other_files = sorted(
            p.name for p in archive_dir.iterdir() if p.is_file() and p.name != "ARCHIVE_INDEX.md"
        )
        if other_files:
            findings.append(
                LintFinding(
                    check_id="archive_index_missing",
                    severity="low",
                    message=(
                        f"memory/archive/{category}/ contains {', '.join(other_files)} "
                        "but no ARCHIVE_INDEX.md"
                    ),
                    file_path=str(archive_dir.relative_to(root)),
                )
            )
    return findings


def _iter_memory_index_recent_entry_lines(content: str) -> list[tuple[int, str]]:
    """Yield (1-based line number, line text) for bullet lines inside
    MEMORY_INDEX.md's "## Recent Entries" section, up to the next "## "
    heading or end of file — the per-entry one-liner analog of an
    ARCHIVE_INDEX.md row (EXTENDED §E12.4: same R5 cap discipline)."""
    result: list[tuple[int, str]] = []
    in_section = False
    for i, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped[3:].strip().lower().startswith("recent entries")
            continue
        if in_section and stripped.startswith("- "):
            result.append((i, line))
    return result


def check_entry_over_cap(root: Path, harness: str, cap_bytes: int = 300) -> list[LintFinding]:
    """Tiering check: an ARCHIVE_INDEX.md one-liner, or a MEMORY_INDEX.md
    Recent Entries row description, exceeds its R5 cap (~300B) (F2 — the
    MEMORY_INDEX side was previously unchecked despite SCHEMA_lint.md §13 and
    the FROZEN spec's §S6 requiring it)."""
    findings: list[LintFinding] = []
    for category in TIERED_CATEGORIES:
        index_file = root / "memory" / "archive" / category / "ARCHIVE_INDEX.md"
        if not index_file.exists():
            continue
        try:
            content = index_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_num, line in enumerate(content.splitlines(), start=1):
            if not line.startswith("- "):
                continue
            size = len(line.encode("utf-8"))
            if size > cap_bytes:
                findings.append(
                    LintFinding(
                        check_id="entry_over_cap",
                        severity="low",
                        message=f"ARCHIVE_INDEX entry is {size}B, over the {cap_bytes}B R5 cap",
                        file_path=str(index_file.relative_to(root)),
                        line=line_num,
                    )
                )

    memory_index_file = root / "memory" / "MEMORY_INDEX.md"
    if memory_index_file.exists():
        try:
            mi_content = memory_index_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            mi_content = None
        if mi_content is not None:
            for line_num, line in _iter_memory_index_recent_entry_lines(mi_content):
                size = len(line.encode("utf-8"))
                if size > cap_bytes:
                    findings.append(
                        LintFinding(
                            check_id="entry_over_cap",
                            severity="low",
                            message=f"MEMORY_INDEX.md row description is {size}B, over the {cap_bytes}B R5 cap",
                            file_path=str(memory_index_file.relative_to(root)),
                            line=line_num,
                        )
                    )
    return findings


def emit_stdout(findings: list[LintFinding], harness: str, seed_file: Path | None) -> None:
    print(f"[lint_runner] Harness detected: {harness}", file=sys.stderr)
    if seed_file:
        print(f"[lint_runner] Seed file: {seed_file}", file=sys.stderr)
    if not findings:
        print("[lint_runner] No findings — memory is clean per MEMORY_PROTOCOL §10.5")
        return

    print(f"[lint_runner] {len(findings)} finding(s):\n")
    by_severity: dict[str, list[LintFinding]] = {}
    for f in findings:
        by_severity.setdefault(f.severity, []).append(f)

    for sev in ("critical", "high", "medium", "low", "info"):
        if sev not in by_severity:
            continue
        print(f"  === {sev.upper()} ({len(by_severity[sev])}) ===")
        for f in by_severity[sev]:
            loc = f" ({f.file_path})" if f.file_path else ""
            print(f"    [{f.check_id}] {f.message}{loc}")
        print()


def emit_jsonl(findings: list[LintFinding], output_path: Path, harness: str) -> None:
    """Append findings to lint_runs.jsonl per SCHEMA_lint.md §4.1."""
    run_record = {
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "tool": "lint_runner.py",
        "version": "1.1",  # bumped for the v3.5 multi-platform lint patch
        "harness": harness,
        "findings_count": len(findings),
        "findings": [f.to_dict() for f in findings],
    }
    with output_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(run_record, separators=(",", ":")) + "\n")


def main() -> int:
    args = parse_args()
    root = Path(args.workspace_root).resolve()
    if not root.exists():
        print(f"ERROR: {root} not found", file=sys.stderr)
        return 2

    # Detect harness (or use override)
    harness, auto_seed = detect_harness(root, args.harness)
    seed_file = Path(args.seed_file).resolve() if args.seed_file else auto_seed

    if harness == "unknown" and not args.seed_file:
        print(
            f"ERROR: Cannot detect harness at {root}. Expected one of:\n"
            f"  - .openclaw/ (OpenClaw harness)\n"
            f"  - .claude/rules/memory_protocol.md (Claude Code harness)\n"
            f"Use --harness openclaw|claude_code or --seed-file <path> to override.",
            file=sys.stderr,
        )
        return 2

    # Run checks (each is multi-platform aware via collect_all_entries or shared paths)
    findings = []
    findings.extend(check_orphan_entries(root, harness))
    findings.extend(check_broken_references(root, harness))
    findings.extend(check_doc_completeness(root, harness))
    findings.extend(check_stale_tentative(root, harness))
    findings.extend(check_promotion_candidates(root, harness))
    findings.extend(check_naming_inconsistencies(root, harness))
    # Tiering checks (v4.0.0 hot/cold backport) — SCHEMA_lint.md §13.
    findings.extend(check_eager_set_over_budget(root, harness))
    findings.extend(check_file_nearing_cap(root, harness))
    findings.extend(check_archive_unindexed(root, harness))
    findings.extend(check_archive_count_drift(root, harness))
    findings.extend(check_archive_index_missing(root, harness))
    findings.extend(check_entry_over_cap(root, harness))
    findings.extend(check_archive_pointer_dangling(root, harness))
    findings.extend(check_unreachable_memory_file(root, harness))

    # The --fail-on gate is evaluated against the UNFILTERED findings on purpose:
    # --severity is a display filter, and letting it narrow the gate would mean
    # `--severity critical` silently disables the high-severity gate. A gate that
    # can be turned off by a display option is not a gate.
    gating_findings = list(findings)

    # Filter by severity (display only)
    if args.severity != "all":
        keep_levels = SEVERITY_LEVELS[SEVERITY_LEVELS.index(args.severity):]
        findings = [f for f in findings if f.severity in keep_levels]

    # Emit
    if args.output == "stdout":
        emit_stdout(findings, harness, seed_file)
    elif args.output == "json":
        run_record = {
            "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "harness": harness,
            "findings_count": len(findings),
            "findings": [f.to_dict() for f in findings],
        }
        print(json.dumps(run_record, indent=2))
    elif args.output == "jsonl":
        log_path = root / "memory" / "security" / "lint_runs.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        emit_jsonl(findings, log_path, harness)
        print(f"[lint_runner] harness={harness}; {len(findings)} finding(s) appended to {log_path}")

    # Exit-code contract (SCHEMA_lint.md §14): 0 = clean/advisory-only,
    # 1 = a finding at or above --fail-on, 2 = usage/detection error.
    if args.fail_on != "none":
        gate_levels = SEVERITY_LEVELS[SEVERITY_LEVELS.index(args.fail_on):]
        blocking = [f for f in gating_findings if f.severity in gate_levels]
        if blocking:
            print(
                f"[lint_runner] FAILED: {len(blocking)} finding(s) at or above "
                f"severity '{args.fail_on}':",
                file=sys.stderr,
            )
            for f in blocking:
                loc = f" ({f.file_path})" if f.file_path else ""
                print(f"    [{f.severity}] {f.check_id}: {f.message}{loc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
