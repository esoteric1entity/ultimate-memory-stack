"""Builds a v3.6.2-shaped installed vault for the migration tests
(materializes the v3.6.2 source tree the migration tests run against).

The fixture must trip ALL of the known migration risks #1-6:
  1. stale 55KB .claude/rules/memory_protocol.md (v3.6.2's real installer
     output — untouched)
  2. stale CLAUDE.md `@...MEMORY_PROTOCOL.md` import line (hand-added)
  3. PROFILE.md lacking YAML frontmatter (v3.6.2's real shape — no edit
     needed, the format itself predates frontmatter)
  4. flat un-tiered MEMORY_INDEX.md (no per-category ARCHIVE_INDEX.md files
     exist yet — true by construction, v3.6.2 never created them)
  5. no memory/user/USER_OVERRIDES.md (true by construction)
  6. PROFILE.md edits that would be lost on a naive wipe path (hand-edited
     compliance preset)

Sentinel content is written into the four user-data files migration must
never touch, so tests can assert byte-for-byte preservation.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SENTINEL_SESSION_STATE = "SENTINEL-SESSION-7f3a2c1d: legacy session note from v3.6.2 — do not lose me"
SENTINEL_MEMORY_INDEX = "SENTINEL-INDEX-9b4e6a02: legacy pointer entry from v3.6.2"
SENTINEL_USER_PROFILE = "SENTINEL-PROFILE-USER-2d81f4c9: the user's v3.6.2 user profile note"
SENTINEL_FEEDBACK = "SENTINEL-FEEDBACK-5a17c3e8: legacy feedback entry from v3.6.2"

STALE_IMPORT_LINE = "@ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md"


def build_v36_vault(v36_source_dir: Path, target_dir: Path, compliance: str = "none") -> None:
    """Install a real v3.6.2 vault into target_dir, then age it into a vault
    that has been in active use since v3.6.2 (populated user files, a hand-
    edited PROFILE.md, a stale CLAUDE.md import) — everything a v4.0.0
    migration needs to detect and fix."""
    setup_py = v36_source_dir / "general-edition" / "setup.py"
    proc = subprocess.run(
        [sys.executable, str(setup_py), "--working-dir", str(target_dir), "--compliance", compliance],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr

    # Risk #6 + #3-adjacent: a hand-edited PROFILE.md (v3.6.2's own format —
    # no YAML frontmatter at all, which is risk #3 by construction).
    profile = target_dir / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    text = profile.read_text(encoding="utf-8")
    assert "compliance: none" in text
    profile.write_text(
        text.replace(
            "compliance: none                    # DEFAULT — user changes at bootstrap if needed",
            "compliance: enterprise              # hand-edited by the user, v3.6.2 era",
        ),
        encoding="utf-8",
    )

    # Sentinel user-data content in the four files migration must never touch.
    memory_dir = target_dir / "memory"
    (memory_dir / "sessions" / "session_state.md").write_text(
        f"# Session State\n\n## Session 42\n\n{SENTINEL_SESSION_STATE}\n", encoding="utf-8",
    )
    (memory_dir / "MEMORY_INDEX.md").write_text(
        f"# Memory Index — Master Registry\n\n- {SENTINEL_MEMORY_INDEX}\n", encoding="utf-8",
    )
    (memory_dir / "user" / "user_profile.md").write_text(
        f"# User Profile\n\n{SENTINEL_USER_PROFILE}\n", encoding="utf-8",
    )
    (memory_dir / "feedback" / "feedback.md").write_text(
        f"# Feedback\n\n## FB-001\n\n{SENTINEL_FEEDBACK}\n", encoding="utf-8",
    )

    # Risk #2: stale CLAUDE.md @-import (never auto-edited — detect + instruct only).
    (target_dir / "CLAUDE.md").write_text(
        "# Project instructions\n\n"
        f"{STALE_IMPORT_LINE}\n\n"
        "Some other project-specific notes here.\n",
        encoding="utf-8",
    )
