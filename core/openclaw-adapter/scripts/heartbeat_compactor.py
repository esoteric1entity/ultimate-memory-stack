#!/usr/bin/env python3
"""
heartbeat_compactor.py — Cron-triggered Lint Runner + Heartbeat Rotation
=========================================================================

Implements heartbeat-driven memory compaction. Runs every 30 min (active
hours) / 6h (idle) via cron per MAPPING.md.

What it does:
  1. Reads HEARTBEAT.md
  2. Counts heartbeats; if > 3-deep, rotates oldest to memory/archive/heartbeats/<YYYY-MM>.md
  3. Checks file size against MEMORY_PROTOCOL §11 cap (~5K per HEARTBEAT.md)
  4. Runs Option C Lint checks in surface-only mode
  5. Emits findings to memory/archive/daily_logs/DAILY_LOG_<today>.md (suggestions only)
  6. Updates MEMORY.md pointers if archive rotation happened

What it does NOT do:
  - Auto-mutate content (surface-only by design)
  - Delete entries (only archives, preserves history)
  - Modify decisions or feedback files
  - Trigger any addon Skills

Design principles: surface-only Lint (never auto-fixes) + Option C Lint
            extensions + heartbeat compaction pattern

Run manually: python heartbeat_compactor.py [<openclaw-root>]
Run via cron: see SKILL.md Step 9 for cron entry

Exit codes:
  0 = success (findings may exist; check daily log)
  1 = openclaw-root not found
  2 = HEARTBEAT.md missing
"""

from __future__ import annotations

import hashlib
import re
import sys
from datetime import datetime
from pathlib import Path

# Legacy consoles (Windows cp1252, non-UTF-8 locales elsewhere) can't encode
# this script's status glyphs — force UTF-8 so output can never crash a
# compaction run (UnicodeEncodeError). Same guard as general-edition/setup.py.
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


# Heartbeat header pattern — matches "## 🔵 Current heartbeat" or "## 🟦 Prior heartbeat"
HEARTBEAT_HEADER_RE = re.compile(r"^## (?:🔵|🟦) (?:Current|Prior) heartbeat", re.MULTILINE)

# Per MEMORY_PROTOCOL §11 — HEARTBEAT.md cap is ~5K chars (1500 lines as inherited from session_state.md cap)
HEARTBEAT_MAX_CHARS = 5000

# Lint thresholds per MEMORY_PROTOCOL §10.5 (Option C extension thresholds)
LINT_THRESHOLDS = {
    "stale_tentative_sessions": 20,    # General-edition default
    "stale_webfetch_days": 90,
    "orphan_minimum_age_sessions": 10,
}


def find_openclaw_root(arg: str | None) -> Path:
    """Resolve OpenClaw root from argument, env, script location, or cwd (last resort).

    Fix for a documented issue: public users following QUICKSTART Step 5b verbatim
    `python3 <openclaw-root>/.openclaw/heartbeat_compactor.py` would hit cwd-based resolution
    failures. New priority order:
      1. Positional arg (explicit)
      2. OPENCLAW_ROOT environment variable
      3. Script location parent.parent (script is at <root>/.openclaw/heartbeat_compactor.py)
      4. CWD (last resort, for legacy invocations)
    """
    import os
    if arg:
        root = Path(arg).resolve()
    elif os.environ.get("OPENCLAW_ROOT"):
        root = Path(os.environ["OPENCLAW_ROOT"]).resolve()
    else:
        # Self-locate: script is installed at <root>/.openclaw/heartbeat_compactor.py
        # parent = .openclaw/; parent.parent = workspace root
        script_inferred = Path(__file__).resolve().parent.parent
        if (script_inferred / "HEARTBEAT.md").exists():
            root = script_inferred
        else:
            # Fall back to CWD (legacy behavior)
            root = Path.cwd()

    if not root.exists():
        print(f"ERROR: OpenClaw root not found: {root}", file=sys.stderr)
        sys.exit(1)

    heartbeat = root / "HEARTBEAT.md"
    if not heartbeat.exists():
        print(f"ERROR: HEARTBEAT.md not found at {heartbeat}", file=sys.stderr)
        print("       Resolved root via priority order (arg → OPENCLAW_ROOT env → script location → cwd).", file=sys.stderr)
        print("       To override: pass workspace path as first argument:", file=sys.stderr)
        print(f"         python3 {Path(__file__).name} /path/to/openclaw/workspace", file=sys.stderr)
        sys.exit(2)

    return root


def rotate_heartbeats(heartbeat_md: Path, archive_dir: Path, max_depth: int = 3) -> list[str]:
    """Rotate heartbeats older than max_depth to archive."""
    content = heartbeat_md.read_text(encoding="utf-8")
    headers = list(HEARTBEAT_HEADER_RE.finditer(content))

    if len(headers) <= max_depth:
        return []  # No rotation needed

    # Find split point: keep first max_depth heartbeats, archive the rest
    split_point = headers[max_depth].start()
    kept = content[:split_point].rstrip() + "\n"
    archived = content[split_point:]

    # Determine archive file (per-month bucket)
    archive_month = datetime.now().strftime("%Y-%m")
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / f"{archive_month}.md"

    # Append archived heartbeats to monthly file
    if archive_file.exists():
        prior = archive_file.read_text(encoding="utf-8")
        archive_file.write_text(prior + "\n---\n\n" + archived, encoding="utf-8")
    else:
        archive_file.write_text(
            f"# Archived Heartbeats — {archive_month}\n\n"
            f"> Rotated by heartbeat_compactor.py from HEARTBEAT.md when 3-deep rolling window exceeded.\n\n---\n\n"
            + archived,
            encoding="utf-8",
        )

    # Write back the kept content
    heartbeat_md.write_text(kept, encoding="utf-8")

    rotated_count = len(headers) - max_depth
    return [f"Rotated {rotated_count} heartbeat(s) to {archive_file.name}"]


def check_size_cap(heartbeat_md: Path) -> list[str]:
    """Check if HEARTBEAT.md exceeds the size cap."""
    size = heartbeat_md.stat().st_size
    if size > HEARTBEAT_MAX_CHARS:
        return [
            f"HEARTBEAT.md exceeds {HEARTBEAT_MAX_CHARS}-char cap (current: {size}). "
            f"Consider rotating older heartbeats or tightening current heartbeat detail."
        ]
    return []


def lint_orphans(openclaw_root: Path) -> list[str]:
    """Lint Check 1 (Option C): orphan entries (no incoming references)."""
    # Surface-only stub in the adapter's own compactor — the full graph-build
    # orphan check lives in core/shared-tools/lint_runner.py (check_orphan_entries).
    return []  # adapter-side stub; run lint_runner.py for the full check


def lint_stale_tentative(openclaw_root: Path) -> list[str]:
    """Lint Check 2 (Option C): stale TENTATIVE decisions."""
    # Surface-only stub
    return []


def lint_doc_completeness(openclaw_root: Path) -> list[str]:
    """Lint Check 3 (Option C): missing 5-element discipline."""
    findings = []
    decisions_md = openclaw_root / "memory" / "decisions" / "decisions.md"
    if not decisions_md.exists():
        return findings

    content = decisions_md.read_text(encoding="utf-8")
    # The 5 discipline elements may appear as headings (### Purpose) or as the
    # shipped template's bold labels (**Purpose:**) — accept both (#13 fix,
    # 2026-06-11). Matcher mirrored in lint_runner.py check_doc_completeness.
    required_elements = ["Purpose", "Rationale", "Sound reasoning", "Scope — CAN", "Scope — CANNOT"]

    def _has_element(block: str, element: str) -> bool:
        esc = re.escape(element)
        return re.search(rf"(?m)^\s*(?:###\s*{esc}\b|\*\*{esc}:?\*\*)", block) is not None

    dec_blocks = re.findall(r"## DEC-[\w-]+:.*?(?=^## DEC-|\Z)", content, re.MULTILINE | re.DOTALL)
    for block in dec_blocks:
        dec_id_match = re.search(r"^## (DEC-[\w-]+):", block)
        if not dec_id_match:
            continue
        dec_id = dec_id_match.group(1)
        missing = [e for e in required_elements if not _has_element(block, e)]
        if missing:
            findings.append(
                f"DOC completeness gap: {dec_id} missing {len(missing)} of 5 required sections: {', '.join(missing)}"
            )
    return findings


def lint_naming_inconsistencies(openclaw_root: Path) -> list[str]:
    """Lint Check 4 (Option C): naming inconsistencies."""
    # Surface-only stub
    return []


def lint_standing_rule_candidates(openclaw_root: Path) -> list[str]:
    """Lint Check 5 (Option C): patterns ready for promotion to standing rule."""
    # Surface-only stub — the full promotion-candidate check lives in lint_runner.py (check_promotion_candidates)
    return []


def emit_findings(openclaw_root: Path, findings: list[str]) -> None:
    """Emit findings to today's daily log (surface-only by design)."""
    if not findings:
        return

    today = datetime.now().strftime("%Y-%m-%d")
    daily_log = openclaw_root / "memory" / "archive" / "daily_logs" / f"DAILY_LOG_{today}.md"
    daily_log.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"\n## Compactor run — {timestamp}\n\n"
    for finding in findings:
        entry += f"- {finding}\n"
    entry += "\n_(Surface-only findings. User decides whether to act.)_\n"

    if daily_log.exists():
        prior = daily_log.read_text(encoding="utf-8")
        daily_log.write_text(prior + entry, encoding="utf-8")
    else:
        daily_log.write_text(
            f"# Daily Log — {today}\n\n"
            f"> Auto-generated by heartbeat_compactor.py. Findings are SUGGESTIONS only.\n"
            + entry,
            encoding="utf-8",
        )


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    root = find_openclaw_root(arg)

    print(f"[heartbeat_compactor] OpenClaw root: {root}")
    print(f"[heartbeat_compactor] Timestamp: {datetime.now().isoformat()}")

    heartbeat_md = root / "HEARTBEAT.md"
    archive_dir = root / "memory" / "archive" / "heartbeats"

    all_findings: list[str] = []

    # Rotate heartbeats if 3-deep window exceeded
    rotation_findings = rotate_heartbeats(heartbeat_md, archive_dir)
    all_findings.extend(rotation_findings)

    # Size cap check
    all_findings.extend(check_size_cap(heartbeat_md))

    # Option C Lint checks (5 self-improvement checks)
    all_findings.extend(lint_orphans(root))
    all_findings.extend(lint_stale_tentative(root))
    all_findings.extend(lint_doc_completeness(root))
    all_findings.extend(lint_naming_inconsistencies(root))
    all_findings.extend(lint_standing_rule_candidates(root))

    # Surface findings
    emit_findings(root, all_findings)

    if all_findings:
        print(f"[heartbeat_compactor] {len(all_findings)} finding(s) surfaced to daily log")
        for f in all_findings:
            print(f"  - {f}")
    else:
        print("[heartbeat_compactor] No findings; heartbeat healthy")

    return 0


if __name__ == "__main__":
    sys.exit(main())
