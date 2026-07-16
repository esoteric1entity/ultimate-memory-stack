#!/usr/bin/env python3
"""
Ultimate Memory Stack — General-Edition Setup Script (Cross-Platform)
Version: 1.1 — 2026-06-16
Tier: T2+ (Python 3.8+); HMAC secrets at T3+ via cryptography package
Author: see /AUTHORS.md
License: Apache-2.0 (general-edition is the public-distribution candidate; biotech-edition is private)
"""

import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys

# Legacy consoles (Windows cp1252, non-UTF-8 locales elsewhere) can't encode
# this script's progress glyphs — force UTF-8 on stdout so output can never
# crash the install (UnicodeEncodeError). The crash class isn't Windows-only,
# and tests/test_console_encoding.py exercises it everywhere. stdout ONLY:
# stderr already defaults to errors="backslashreplace" (crash-proof, and it
# preserves exact codepoints in diagnostics — reconfiguring it would lose
# that). Gated on __main__ so importing this module (tests) never mutates
# process-wide streams.
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
from datetime import datetime, timezone
from pathlib import Path

EDITION = "general"

SCRIPT_DIR = Path(__file__).resolve().parent
COMMON_SPECS_DIR = SCRIPT_DIR.parent / "common-specs"

# Version is single-sourced from the package-root VERSION file (#14 fix,
# 2026-06-11 — installers previously carried diverging hardcoded strings).
try:
    STACK_VERSION = (SCRIPT_DIR.parent / "VERSION").read_text(encoding="utf-8").strip()
except OSError:
    STACK_VERSION = "3.6.2"  # fallback for a general-edition dir copied standalone

# Public general-edition presets. healthcare/PHI is intentionally EXCLUDED —
# PHI/HIPAA handling ships ONLY in the institutional biotech-edition (not public).
VALID_PRESETS = {"none", "enterprise", "custom"}
VALID_EXTENSIONS = {"gdpr", "soc2", "pci-dss"}
BIOTECH_ONLY = {"healthcare"}  # requested in general-edition -> redirect to biotech


def log_audit_event(working_dir: Path, action: str, summary: str,
                    outcome: str = "success", entry_id: str = "<system>"):
    """Append entry to audit_log.jsonl if preset enables audit.

    Canonical format per SCHEMA_audit_log.md §canonical-format:
    - entry_id: "<bootstrap>" for install/init events, "<system>" for other system events
    - timestamp: ISO 8601 UTC with Z suffix, second-precision (no microseconds)
    - JSON: compact (no whitespace between key-value pairs) — separators=(",", ":")
    """
    audit_path = working_dir / "memory" / "security" / "audit_log.jsonl"
    if not audit_path.parent.exists():
        return  # Audit log not initialized; skip silently

    entry = {
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "actor": "migration-script",
        "actor_session": 0,
        "action": action,
        "entry_id": entry_id,
        "entry_path": "memory/",
        "entry_category": "system",
        "entry_summary": summary,
        "outcome": outcome,
    }

    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


# ---------------------------------------------------------------------------
# USER_OVERRIDES pattern (v4.0.0, PLAN-merge-on-install) — permanent fix for
# the 2026-06-15 data-loss debt. PROFILE.md is now regenerable; user config
# lives in memory/user/USER_OVERRIDES.md, created once and never rewritten.
# ---------------------------------------------------------------------------

def _extract_template_body(template_path: Path) -> str:
    """Pull the fenced ```markdown ... ``` block out of a doc-wrapped template file."""
    text = template_path.read_text(encoding="utf-8")
    match = re.search(r"```markdown\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError(f"Template {template_path} has no fenced markdown block")
    return match.group(1)


def build_user_overrides_body(template_body: str, compliance_preset: str, extensions: list) -> str:
    """Fill the template body with any bootstrap-collected values. Pure function — no I/O."""
    body = template_body.replace("<YYYY-MM-DD>", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    if compliance_preset and compliance_preset != "none":
        body = re.sub(
            r"^# compliance: <preset>.*$",
            f"compliance: {compliance_preset}",
            body, count=1, flags=re.MULTILINE,
        )
    if extensions:
        ext_block = "extensions:\n" + "\n".join(f"  - {e}" for e in extensions)
        body = re.sub(
            r"^# extensions:.*\n#   - <ext>$",
            ext_block,
            body, count=1, flags=re.MULTILINE,
        )
    return body


def create_user_overrides(working_dir: Path, compliance_preset: str, extensions: list) -> bool:
    """Create memory/user/USER_OVERRIDES.md from the template if absent. NEVER write if present
    — not even to reformat it; this file is user-owned from the moment it exists."""
    overrides_path = working_dir / "memory" / "user" / "USER_OVERRIDES.md"
    if overrides_path.exists():
        return False
    template_path = COMMON_SPECS_DIR / "templates" / "USER_OVERRIDES.template.md"
    body = build_user_overrides_body(_extract_template_body(template_path), compliance_preset, extensions)
    if not body.endswith("\n"):
        body += "\n"
    overrides_path.parent.mkdir(parents=True, exist_ok=True)
    overrides_path.write_text(body, encoding="utf-8")
    return True


# Categories that tier per SPEC-hotcold-v4 §S2 — MEMORY_PROTOCOL.md §11.6.
# category -> (Title-case label, hot file relpath under memory/, archive file name)
TIERED_CATEGORIES = {
    "sessions": ("Sessions", "sessions/session_state.md", "sessions-archive.md"),
    "decisions": ("Decisions", "decisions/decisions.md", "decisions-archive.md"),
    "feedback": ("Feedback", "feedback/feedback.md", "feedback-archive.md"),
}


def create_archive_indexes(working_dir: Path) -> None:
    """Create empty memory/archive/<category>/ARCHIVE_INDEX.md for each tiered
    category on fresh install (SPEC-hotcold-v4 §S4: fresh installs get these by
    default, not lazily on first rotation). Idempotent per category — never
    overwrites an existing ARCHIVE_INDEX.md (rotation may have populated it)."""
    template_path = COMMON_SPECS_DIR / "templates" / "ARCHIVE_INDEX.template.md"
    template_body = _extract_template_body(template_path)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for category, (label, hot_file, archive_file) in TIERED_CATEGORIES.items():
        archive_dir = working_dir / "memory" / "archive" / category
        index_path = archive_dir / "ARCHIVE_INDEX.md"
        if index_path.exists():
            continue
        body = (
            template_body
            .replace("<Category>", label)
            .replace("<YYYY-MM-DD>", today)
            .replace("<HotFile>", hot_file)
            .replace("<ArchiveFile>", archive_file)
        )
        # A genuinely fresh, empty index has no example entry — strip the
        # illustrative placeholder line so it doesn't read as real content.
        body = re.sub(r"\n- <ENTRY-ID>.*\n", "\n", body)
        if not body.endswith("\n"):
            body += "\n"
        archive_dir.mkdir(parents=True, exist_ok=True)
        index_path.write_text(body, encoding="utf-8")


def upsert_override_key(overrides_path: Path, key: str, value_line: str):
    """Set `key` in USER_OVERRIDES.md to value_line's content, touching nothing else.
    Order: replace a live `key: ...` line; else uncomment+replace the template's
    commented `# key: ...` line; else append after the frontmatter close. Used by
    --change-preset now that PROFILE.md is regenerable and no longer authoritative."""
    content = overrides_path.read_text(encoding="utf-8")
    live_re = re.compile(rf"^{re.escape(key)}: .*$", re.MULTILINE)
    if live_re.search(content):
        content = live_re.sub(value_line, content, count=1)
    else:
        commented_re = re.compile(rf"^# {re.escape(key)}:.*$", re.MULTILINE)
        if commented_re.search(content):
            content = commented_re.sub(value_line, content, count=1)
        else:
            # Fallback: insert right after the frontmatter's closing `---`.
            content = re.sub(r"^---$", f"---\n{value_line}", content, count=1, flags=re.MULTILINE)
    overrides_path.write_text(content, encoding="utf-8")


def archive_edited_profile(working_dir: Path, installed_profile: Path) -> Path:
    """Archive a PROFILE.md that differs from the shipped default before it gets
    regenerated, and print a migration notice. Never auto-ports values — the
    user decides what to carry into USER_OVERRIDES.md."""
    archive_dir = working_dir / "memory" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive_path = archive_dir / f"PROFILE.pre-upgrade.{ts}.md"
    shutil.copy(installed_profile, archive_path)
    print(f"⚠️  Existing PROFILE.md differs from the shipped default — archived to {archive_path}")
    print("   PROFILE.md is regenerable as of v4.0.0; your edits are not auto-applied.")
    print(f"   Compare {archive_path.name} against the new PROFILE.md, then port any values you")
    print("   want to keep into memory/user/USER_OVERRIDES.md (create it if it doesn't exist yet —")
    print("   see common-specs/templates/USER_OVERRIDES.template.md for the format).")
    return archive_path


def generate_hmac_secret() -> str:
    """Generate HMAC secret (general-edition default for cryptographic signatures)."""
    return secrets.token_urlsafe(32)


def verify_environment(working_dir: Path, compliance_preset: str = "none"):
    """Self-test verification."""
    print("\n=== Self-Test ===")
    print(f"Working directory: {working_dir}")

    # Pre-check: handle scaffold-present-but-wizard-not-run state.
    # Mirrors Bash setup.sh behavior so cross-script UX is consistent.
    memory_dir = working_dir / "memory"
    if not memory_dir.exists():
        print(f"✗ No memory/ directory found at {working_dir}")
        print(f"  Run setup.py without --verify to install")
        sys.exit(1)

    if not (memory_dir / "MEMORY_INDEX.md").exists():
        print(f"✓ Setup scaffold present at {working_dir}")
        print()
        print(f"ℹ️  Activation wizard has not run yet.")
        print(f"    Open your agent harness from {working_dir} (e.g. Claude Code or OpenClaw), paste the activation prompt from:")
        print(f"    {working_dir}/ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md")
        print(f"    Then re-run --verify.")
        return

    checks = {
        "T1 session_state.md": (working_dir / "memory" / "sessions" / "session_state.md").exists(),
        "T2 MEMORY_INDEX.md": (working_dir / "memory" / "MEMORY_INDEX.md").exists(),
        "Quarantine dir": (working_dir / "memory" / "quarantine").exists(),
    }

    audit_path = working_dir / "memory" / "security" / "audit_log.jsonl"
    if compliance_preset == "none":
        if audit_path.exists():
            line_count = sum(1 for _ in open(audit_path, encoding="utf-8"))
            checks[f"Audit log (opt-in; preset=none)"] = f"{line_count} entries"
        else:
            checks[f"Audit log (opt-in; preset=none)"] = "Not initialized (this is OK for 'none')"
    else:
        checks[f"Audit log (preset={compliance_preset})"] = audit_path.exists()

    for check, result in checks.items():
        mark = "✓" if result else "✗"
        print(f"{mark} {check}: {result}")


def detect_tier() -> dict:
    """Detect available infrastructure."""
    tier_info = {
        "node": False,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "cryptography": False,
    }

    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            tier_info["node"] = result.stdout.strip()
    except FileNotFoundError:
        pass

    try:
        import cryptography
        tier_info["cryptography"] = cryptography.__version__
    except ImportError:
        pass

    return tier_info


GITIGNORE_MARKER = "# >>> ultimate-memory-stack >>>"
GITIGNORE_BLOCK = (
    f"{GITIGNORE_MARKER}\n"
    "# Installer artifacts + the vendored package (regenerable). The user's\n"
    "# memory vault (the data) is intentionally left tracked — not ignored here.\n"
    "ultimate-memory-stack/\n"
    ".deployment-info\n"
    ".ums-manifest.json\n"
    "# <<< ultimate-memory-stack <<<\n"
)


def ensure_gitignore(working_dir: Path) -> bool:
    """If working_dir is a git repo, append the UMS ignore block to .gitignore.

    Ignores the regenerable package scaffold + install markers — NEVER memory/
    (the user's data). Idempotent: skips if the block marker is already present.
    Returns True only if it wrote the block.
    """
    if not (working_dir / ".git").exists():
        return False
    gitignore = working_dir / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if GITIGNORE_MARKER in existing:
        return False
    parts = []
    if existing:
        parts.append(existing if existing.endswith("\n") else existing + "\n")
        parts.append("\n")  # separate the user's lines from our block
    parts.append(GITIGNORE_BLOCK)
    gitignore.write_text("".join(parts), encoding="utf-8")
    return True


def _refuse_if_installed_copy(working_dir: Path) -> None:
    """Self-reference guard (adversarial-round finding, 2026-07-14): SCRIPT_DIR is
    wherever THIS script happens to be running from. If that's the INSTALLED
    copy inside working_dir/ultimate-memory-stack/general-edition/, then
    SCRIPT_DIR and the install target are the same directory — a "differs
    from shipped" comparison against SCRIPT_DIR would compare a file to itself
    (always false, so a hand-edited PROFILE.md is never archived), and a wipe
    of common-specs/general-edition would then try to copytree FROM the path
    it just deleted, crashing and permanently destroying the directory. Refuse
    before any of that runs. Shared by setup_fresh() and migrate() (v3.6) —
    both wipe-and-refresh the same way; --change-preset/--verify/--status
    don't call this and remain safe to run from the installed copy."""
    installed_general_edition = (working_dir / "ultimate-memory-stack" / "general-edition").resolve()
    if SCRIPT_DIR.resolve() == installed_general_edition:
        print(f"✗ ERROR: this is the INSTALLED copy of setup.py, running against its own directory.")
        print(f"  {SCRIPT_DIR} IS the install target — there is no separate shipped source to refresh from.")
        print(f"  To re-install or add extensions, run the ORIGINAL package's setup.py (the one you")
        print(f"  cloned/downloaded), not the copy inside {working_dir}.")
        print(f"  To change the compliance preset on this existing install, use --change-preset instead")
        print(f"  (safe to run from the installed copy).")
        sys.exit(1)


# ---------------------------------------------------------------------------
# MIGRATION MODE (v4.0.0, PLAN-migration-v36x-to-v400) — a single entry point
# for existing vaults. v3.6 adds already-migrated detection (idempotency),
# --dry-run, and disclosure-only detections; both branches fall through into
# setup_fresh()'s existing conditional refresh (rules copy, EXTENDED,
# USER_OVERRIDES, PROFILE archive-if-differs, tiering scaffold) rather than
# duplicating that logic.
# ---------------------------------------------------------------------------

# Whole-line anchored (MULTILINE) so a mention of the old import syntax in
# prose, a fenced code example, or an HTML comment doesn't false-positive —
# only a line that IS (only) the import counts. Combined with
# _strip_fenced_code_blocks() below for the fenced-example case specifically
# (step-8 adversarial round Finding 9 — a false positive here would
# permanently defeat the already-migrated idempotency check for any vault
# whose CLAUDE.md ever documents the old syntax).
STALE_CLAUDE_IMPORT_RE = re.compile(r"^[ \t]*@[A-Za-z0-9_./-]*MEMORY_PROTOCOL\.md[ \t]*$", re.MULTILINE)


def _strip_fenced_code_blocks(text: str) -> str:
    """Blank out (never delete — must preserve line numbers for anything
    reported after a fence) fenced ```...``` code-block content."""
    return re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.DOTALL)


def _find_stale_claude_imports(text: str) -> list[int]:
    """1-based line numbers of every stale @-import line, ignoring fenced
    code examples. Empty list if none. Used for both the idempotency check
    (any hit = not yet migrated) and the disclosure message (report ALL of
    them, not just the first — Finding 10)."""
    stripped = _strip_fenced_code_blocks(text)
    return [stripped[:m.start()].count("\n") + 1 for m in STALE_CLAUDE_IMPORT_RE.finditer(stripped)]


def _unique_backup_destination(base: Path) -> Path:
    """Second-granularity timestamps collide on a fast re-run (every real
    migration attempt creates one, and the disclosure-only CLAUDE.md item is
    never auto-resolved, so back-to-back runs are a realistic pattern) — never
    crash (Python's shutil.copytree) or silently nest into an existing dir
    (Bash's cp -r) on a collision; find the next free name instead (step-8
    adversarial round Findings 1/2/12)."""
    if not base.exists():
        return base
    n = 2
    while True:
        candidate = base.with_name(f"{base.name}-{n}")
        if not candidate.exists():
            return candidate
        n += 1


def _refuse_if_backup_location_unsafe(working_dir: Path, backup_location: Path) -> None:
    """--backup-location under memory/ itself plants a permanent nested copy
    inside the very tree it's meant to safeguard (Finding 11)."""
    memory_dir = (working_dir / "memory").resolve()
    resolved = backup_location.resolve() if backup_location.exists() else (
        backup_location.parent.resolve() / backup_location.name
    )
    if resolved == memory_dir or memory_dir in resolved.parents:
        print(f"✗ ERROR: --backup-location ({backup_location}) is inside memory/ — refusing.")
        print(f"  A backup must live OUTSIDE the tree it's backing up. Pick a location outside {memory_dir}.")
        sys.exit(1)


def _safe_copy_file(src: Path, dst: Path) -> None:
    """Copy src to dst, replacing whatever currently exists at dst — a
    regular file, a symlink (removed, never written THROUGH — Findings 3/4),
    or even a directory (removed, never silently nested into — Finding 7)."""
    if dst.is_symlink() or dst.is_file():
        dst.unlink()
    elif dst.is_dir():
        shutil.rmtree(dst)
    shutil.copy(src, dst)


def _refuse_if_not_writable(working_dir: Path) -> None:
    """Mirrors setup.sh's `[ ! -w "${WORKING_DIR}" ]` check (Finding 6) —
    Python had no equivalent and crashed with a raw PermissionError on the
    first write instead of a clean refusal."""
    if not working_dir.exists():
        print(f"✗ ERROR: {working_dir} does not exist.")
        sys.exit(1)
    if not os.access(working_dir, os.W_OK):
        print(f"✗ ERROR: {working_dir} is not writable.")
        sys.exit(1)


def _has_real_yaml_frontmatter(profile_file: Path) -> bool:
    """A bare `---`-starts-the-file check is a 3-byte heuristic a truncated or
    corrupted PROFILE.md can satisfy by accident (step-8 adversarial round
    Finding 5), permanently misclassifying it as already-migrated. Require an
    actual closing `---` fence within the first 4096 bytes — the real shape
    of every shipped PROFILE.md's frontmatter block."""
    head = profile_file.read_bytes()[:4096]
    if not head.startswith(b"---"):
        return False
    return b"\n---" in head[3:]


def _already_migrated_v36(working_dir: Path) -> bool:
    """Step-zero idempotency check (§2.2): all 5 conditions must hold. Every
    check uses is_file() (not exists()) so a directory or dangling symlink at
    any of these paths is correctly treated as "not a valid file yet," never
    crashes here, and gets properly replaced if a real migration proceeds
    (step-8 adversarial round Findings 7/8)."""
    rules_file = working_dir / ".claude" / "rules" / "memory_protocol.md"
    if not rules_file.is_file() or rules_file.stat().st_size >= 15000:
        return False
    if not (working_dir / "memory" / "MEMORY_PROTOCOL_EXTENDED.md").is_file():
        return False
    if not (working_dir / "memory" / "user" / "USER_OVERRIDES.md").is_file():
        return False
    profile_file = working_dir / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    if not profile_file.is_file() or not _has_real_yaml_frontmatter(profile_file):
        return False
    claude_md = working_dir / "CLAUDE.md"
    if claude_md.is_file() and _find_stale_claude_imports(claude_md.read_text(encoding="utf-8", errors="replace")):
        return False
    return True


def _print_v36_dry_run_plan(working_dir: Path) -> None:
    overrides_file = working_dir / "memory" / "user" / "USER_OVERRIDES.md"
    profile_file = working_dir / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    claude_md = working_dir / "CLAUDE.md"

    print(f"→ DRY RUN: v3.6 → v{STACK_VERSION} migration plan (no writes will be made):")
    # These three always happen once migration proceeds past the
    # already-migrated gate — they're unconditional overwrites in
    # setup_fresh()'s shared flow, not gated on the file's current state
    # (step-8 adversarial round Finding 4 — the old preview under-reported
    # this, listing them as conditional when they never actually are).
    print("  - refresh the vendored ultimate-memory-stack/ scaffold (common-specs/, general-edition/)")
    print("  - refresh .claude/rules/memory_protocol.md")
    print("  - refresh memory/MEMORY_PROTOCOL_EXTENDED.md")
    if not overrides_file.is_file():
        print("  - create memory/user/USER_OVERRIDES.md")
    if profile_file.is_file() and profile_file.read_bytes() != (SCRIPT_DIR / "PROFILE.md").read_bytes():
        print("  - archive existing PROFILE.md (differs from the shipped default) and regenerate")
    print("  - create per-category ARCHIVE_INDEX.md files where absent (tiering scaffold)")
    if claude_md.is_file():
        stale_lines = _find_stale_claude_imports(claude_md.read_text(encoding="utf-8", errors="replace"))
        if stale_lines:
            where = ", ".join(f"CLAUDE.md:{n}" for n in stale_lines)
            print(f"  - DETECTED: stale @-import at {where} — will NOT be auto-edited; see MIGRATION_v3.6_to_v4.0.md for the exact line(s) to remove")
    if (working_dir / ".openclaw").is_dir():
        print("  - DETECTED: .openclaw/ present — the OpenClaw adapter's own overwrite semantics are unchanged by this migration; its own backups apply")
    preview_backup = _unique_backup_destination(working_dir / "memory.backup.v3.6.<timestamp>")
    print(f"→ Backup would be created at: {preview_backup}/")


def _print_v2_dry_run_plan(working_dir: Path, args) -> None:
    """v2.0's --dry-run used to be silently ignored (a real migration ran
    anyway) — step-8 adversarial round Finding 13. Now a genuine preview,
    same as v3.6's."""
    backup_preview = args.backup_location or (working_dir / "memory.backup.v2.<timestamp>")
    print(f"→ DRY RUN: v2.0 → v{STACK_VERSION} migration plan (no writes will be made):")
    print(f"  - back up memory/ to {backup_preview}/")
    print("  - delegate schema migration to the Claude Code wizard (per MIGRATION_v2_to_v3.md)")
    print("  - refresh the vendored ultimate-memory-stack/ scaffold, rules copy, USER_OVERRIDES/tiering scaffold (same conditional items as any re-install)")


def migrate(working_dir: Path, migrate_from: str, compliance_preset: str, extensions: list, args) -> None:
    """MIGRATION MODE dispatcher. v2.0 preserves the same backup-then-delegate
    shape the Bash installer has always used for that path (acceptance
    criterion (b): unchanged); v3.6 is the new v3.6.x → v4.0.0 entry point.
    Both branches (when not already-migrated / dry-run) fall through into
    setup_fresh() at the end, which does the actual conditional refresh —
    migrate() only adds the backup + disclosure-only detections on top."""
    if migrate_from not in {"v2.0", "v3.6"}:
        print(f"✗ ERROR: Invalid --migrate-from value '{migrate_from}'")
        print("  Valid: v2.0 | v3.6")
        sys.exit(1)

    if migrate_from == "v3.6":
        if _already_migrated_v36(working_dir):
            print(f"✓ Already migrated to v{STACK_VERSION} — nothing to do.")
            return
        if args.dry_run:
            _print_v36_dry_run_plan(working_dir)
            return
    elif args.dry_run:
        _print_v2_dry_run_plan(working_dir, args)
        return

    _refuse_if_installed_copy(working_dir)
    _refuse_if_not_writable(working_dir)

    if not (working_dir / "memory").exists():
        print(f"✗ No existing memory/ at {working_dir}")
        sys.exit(1)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    if migrate_from == "v3.6":
        backup_location = args.backup_location or (working_dir / f"memory.backup.v3.6.{ts}")
        _refuse_if_backup_location_unsafe(working_dir, backup_location)
        backup_location = _unique_backup_destination(backup_location)
        print(f"→ Migrating v3.6 → v{STACK_VERSION}")
        print(f"→ Backup: {backup_location}")
        shutil.copytree(working_dir / "memory", backup_location)
        print("✓ Backup complete")

        # Disclosure-only detections (§2.3): never auto-edited, never fixed here.
        claude_md = working_dir / "CLAUDE.md"
        if claude_md.is_file():
            stale_lines = _find_stale_claude_imports(claude_md.read_text(encoding="utf-8", errors="replace"))
            if stale_lines:
                where = ", ".join(f"CLAUDE.md:{n}" for n in stale_lines)
                print(f"⚠️  {where} still imports MEMORY_PROTOCOL.md — this doubles the eager-load cost")
                print("   since .claude/rules/memory_protocol.md already auto-loads every session.")
                print("   Delete that line from CLAUDE.md by hand (never auto-edited).")
        if (working_dir / ".openclaw").is_dir():
            print("ℹ️  .openclaw/ detected — this migration only covers the general-edition Claude Code vault.")
            print("   The OpenClaw adapter's own overwrite semantics are unchanged by v4.0.0; its own backups apply.")
        print("→ Continuing with the standard refresh (rules copy, EXTENDED, USER_OVERRIDES, PROFILE, tiering scaffold)...")
    else:
        backup_location = args.backup_location or (working_dir / f"memory.backup.v2.{ts}")
        _refuse_if_backup_location_unsafe(working_dir, backup_location)
        backup_location = _unique_backup_destination(backup_location)
        print(f"→ Migrating v{migrate_from} → v{STACK_VERSION}")
        print(f"→ Backup: {backup_location}")
        shutil.copytree(working_dir / "memory", backup_location)
        print("✓ Backup complete")
        print("→ Schema migration via Claude Code wizard (per MIGRATION_v2_to_v3.md)")

    setup_fresh(working_dir, compliance_preset, extensions, args)


def setup_fresh(working_dir: Path, compliance_preset: str, extensions: list, args):
    """Fresh install of general-edition."""
    print(f"\n=== Fresh Install: General-Edition v{STACK_VERSION} ===")
    print(f"Working directory: {working_dir}")
    print(f"Compliance preset: {compliance_preset}")
    print(f"Extensions: {extensions if extensions else 'none'}")

    _refuse_if_installed_copy(working_dir)
    _refuse_if_not_writable(working_dir)

    # PHI/HIPAA is biotech-edition only — refuse it in the public general-edition
    if compliance_preset in BIOTECH_ONLY or any(e in BIOTECH_ONLY for e in extensions):
        print(f"✗ '{compliance_preset}'/PHI handling is part of the institutional biotech-edition, not the public general-edition.")
        print(f"  The general-edition does not ship PHI/HIPAA compliance. See CONTRIBUTING.md for institutional adoption.")
        sys.exit(1)

    # Validate compliance preset
    if compliance_preset not in VALID_PRESETS:
        print(f"✗ Invalid preset: {compliance_preset}")
        print(f"  Valid: {VALID_PRESETS}")
        sys.exit(1)

    # Custom preset complexity floor — overrides/compliance.override.md is USER-AUTHORED
    # and does not ship with the package (SCHEMA_compliance_profile §4.4); this gate is
    # the documented footgun guard, NOT a check for the shipped compliance-presets file.
    if compliance_preset == "custom":
        override_path = SCRIPT_DIR / "overrides" / "compliance.override.md"
        if not override_path.exists():
            print(f"✗ ERROR: 'custom' preset requires {override_path}")
            print(f"  The 'custom' preset needs explicit configuration with ≥1 override — write that file first")
            print(f"  (see overrides/compliance-presets.override.md §5.4 for the pattern).")
            sys.exit(1)

    # Validate extensions
    for ext in extensions:
        if ext not in VALID_EXTENSIONS:
            print(f"✗ Invalid extension: {ext}")
            print(f"  Valid: {VALID_EXTENSIONS}")
            sys.exit(1)

    # Pre-flight
    if not COMMON_SPECS_DIR.exists():
        print(f"✗ common-specs/ not found at {COMMON_SPECS_DIR}")
        sys.exit(1)

    # Clear any prior completion certificate up-front (#11 re-audit follow-on):
    # a crashed re-install must not leave a stale .deployment-info claiming a
    # configured install. It is rewritten at the very end on success only.
    stale_marker = working_dir / ".deployment-info"
    if stale_marker.exists():
        stale_marker.unlink()

    # Copy files
    print("\n→ Copying memory stack files...")
    target_root = working_dir / "ultimate-memory-stack"
    target_root.mkdir(parents=True, exist_ok=True)

    # v4.0.0 (PLAN-merge-on-install, unified existing-scaffold behavior): archive
    # anything user-touched, THEN refresh. A pre-v4.0.0 vault may have a hand-edited
    # PROFILE.md — archive it (with a migration notice) BEFORE the regenerable
    # general-edition/ tree gets wiped below, so the edit is never silently lost.
    # Compared against the SHIPPED source about to be copied, never a version stamp
    # the user could have edited away.
    installed_profile = target_root / "general-edition" / "PROFILE.md"
    shipped_profile = SCRIPT_DIR / "PROFILE.md"
    if installed_profile.exists() and installed_profile.read_bytes() != shipped_profile.read_bytes():
        archive_edited_profile(working_dir, installed_profile)

    # Surface re-install action with explicit warning before wipe
    if (target_root / "common-specs").exists():
        print(f"⚠️  Existing common-specs at {target_root / 'common-specs'} — wiping for clean install")
        shutil.rmtree(target_root / "common-specs")
    shutil.copytree(COMMON_SPECS_DIR, target_root / "common-specs")

    if (target_root / "general-edition").exists():
        print(f"⚠️  Existing general-edition at {target_root / 'general-edition'} — wiping for clean install")
        shutil.rmtree(target_root / "general-edition")
    shutil.copytree(SCRIPT_DIR, target_root / "general-edition")

    # Copy the package-root VERSION file into the scaffold (#14 re-audit
    # follow-on) so a re-run of the COPIED setup.py reads the real version
    # instead of silently falling back to the hardcoded default.
    version_src = SCRIPT_DIR.parent / "VERSION"
    if version_src.exists():
        shutil.copy(version_src, target_root / "VERSION")

    # Copy MEMORY_PROTOCOL.md
    claude_rules_dir = working_dir / ".claude" / "rules"
    claude_rules_dir.mkdir(parents=True, exist_ok=True)
    _safe_copy_file(COMMON_SPECS_DIR / "MEMORY_PROTOCOL.md", claude_rules_dir / "memory_protocol.md")
    os.chmod(claude_rules_dir / "memory_protocol.md", 0o644)  # normalize permissions

    print("✓ Files copied")

    # Keep the vendored package + install markers out of the user's git history
    # (only when the target is a git repo); memory/ is their data and stays tracked.
    if ensure_gitignore(working_dir):
        print("✓ .gitignore updated (package scaffold + install markers ignored; memory/ left tracked)")

    # NOTE (#11 half-config fix, 2026-06-11): the .deployment-info marker is
    # written at the END of setup_fresh — it is a completion certificate, not
    # a start record. Pre-fix it was written here, so a failure during
    # compliance application left a marker claiming a configured install
    # whose PROFILE.md still said `compliance: none` (redaction silently off).

    # Initialize memory/ directory
    memory_dir = working_dir / "memory"
    for subdir in ["sessions", "decisions", "feedback", "projects", "security",
                   "references", "user", "archive", "quarantine"]:
        (memory_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Extended protocol reference — on-demand only, vault root, NEVER .claude/rules/ (would recreate eager-load cost)
    _safe_copy_file(COMMON_SPECS_DIR / "MEMORY_PROTOCOL_EXTENDED.md", memory_dir / "MEMORY_PROTOCOL_EXTENDED.md")

    # Initialize audit log based on preset
    if compliance_preset == "none":
        print("ℹ️  Audit log: OPT-IN (compliance: none — default OFF)")
        print("   Enable later via PROFILE.md edit: audit_log: true")
    else:
        (memory_dir / "security" / "audit_log.jsonl").touch()
        (memory_dir / "quarantine" / "quarantine_log.jsonl").touch()
        log_audit_event(
            working_dir,
            action="initialize",
            summary=f"General-edition v{STACK_VERSION} deployment initialized; preset={compliance_preset}; extensions={','.join(extensions) if extensions else 'none'}",
            entry_id="<bootstrap>",  # canonical init entry_id matches Bash setup.sh
        )
        print(f"✓ Audit log initialized (compliance: {compliance_preset})")

    # v4.0.0: compliance/extensions choices are USER choices — they land in
    # USER_OVERRIDES.md (create-once, never rewritten again), not PROFILE.md.
    # PROFILE.md's frontmatter carries only the shipped default and is never
    # edited by the installer (it stays regenerable — see PROFILE.md §2.1).
    create_user_overrides(working_dir, compliance_preset, extensions)
    print("✓ memory/user/USER_OVERRIDES.md ready")

    # v4.0.0 hot/cold tiering (SPEC-hotcold-v4 §S4): pre-scaffold empty
    # ARCHIVE_INDEX.md files for the 3 tiered categories.
    create_archive_indexes(working_dir)
    print("✓ memory/archive/{sessions,decisions,feedback}/ARCHIVE_INDEX.md ready")

    # Tier detection
    tier = detect_tier()
    print(f"\n=== Tier Detection ===")
    print(f"  Python: {tier['python_version']}")
    print(f"  Node.js: {tier['node'] or 'NOT installed (T2 dormant)'}")
    print(f"  cryptography: {tier['cryptography'] or 'NOT installed (T3 HMAC dormant)'}")

    # Generate HMAC secret if at T3+ (cryptography available)
    if tier["cryptography"] and args.generate_hmac_secret:
        secret = generate_hmac_secret()
        key_dir = Path.home() / ".config" / "ultimate-memory-stack" / "keys"
        key_dir.mkdir(parents=True, exist_ok=True)
        secret_path = key_dir / "general-edition.hmac.secret"
        secret_path.write_text(secret)
        os.chmod(secret_path, 0o600)
        print(f"✓ HMAC secret generated: {secret_path}")
        print(f"  Reference in PROFILE.md as 'hmac_secret_path: ~/.config/ultimate-memory-stack/keys/general-edition.hmac.secret'")

    # Self-test
    verify_environment(working_dir, compliance_preset)

    # Completion certificate — written LAST (#11): if anything above failed,
    # no marker exists and --verify reports the install as incomplete.
    deployment_info = working_dir / ".deployment-info"
    deployment_info.write_text(
        f"deployment_path: {working_dir}\n"
        f"edition: {EDITION}\n"
        f"compliance_preset: {compliance_preset}\n"
        f"extensions: {','.join(extensions) if extensions else 'none'}\n"
        f"installed_at: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}\n"
        f'stack_version: "{STACK_VERSION}"\n',
        encoding="utf-8",
    )
    print(f"✓ Deployment-info marker written to {deployment_info}")

    print(f"\n=== Setup Complete ===")

    # Harness-aware next steps (Option C): when the top-level installer launches
    # this script it sets UMS_PARENT=1 and prints its own harness-correct summary,
    # so suppress the per-edition block to avoid a duplicate (and the old
    # "Run: claude" Claude-Code assumption). Standalone runs print a neutral block.
    if os.environ.get("UMS_PARENT") != "1":
        print(f"\nNext steps:")
        print(f"  1. cd {working_dir}")
        print(f"  2. Open your agent harness in this directory (e.g. Claude Code or OpenClaw)")
        print(f"  3. Paste the activation prompt from BOOTSTRAP_PROMPT.md")
        print(f"  4. Answer the setup wizard")
        print(f"  5. Verify (after wizard completes):")
        print(f"     WORKING_DIR={working_dir} python3 {SCRIPT_DIR}/setup.py --verify")
        print(f"\nCompliance: {compliance_preset}")
        print(f"Extensions: {extensions if extensions else 'none'}")
        print(f"\nTo change later: python3 setup.py --change-preset=<new>")
        print(f"See INSTALL.md for details.")


def change_preset(working_dir: Path, new_preset: str):
    """Change compliance preset on existing deployment. Writes to USER_OVERRIDES.md
    (v4.0.0) — PROFILE.md is regenerable and no longer authoritative for this value."""
    if new_preset in BIOTECH_ONLY:
        print(f"✗ '{new_preset}'/PHI handling is biotech-edition only, not available in the public general-edition.")
        sys.exit(1)
    if new_preset not in VALID_PRESETS:
        print(f"✗ Invalid preset: {new_preset}")
        sys.exit(1)

    # Custom preset complexity floor (adversarial-round finding, 2026-07-14):
    # setup_fresh() has always enforced this gate but change_preset() never did
    # — `--change-preset=custom` silently "succeeded" with no override file at
    # all, the exact footgun this gate exists to prevent (§3.2a). Mirrors
    # setup_fresh()'s check, but against the INSTALLED deployment's overrides/
    # dir (working_dir), not SCRIPT_DIR — change_preset is designed to run
    # from the installed copy.
    if new_preset == "custom":
        override_path = working_dir / "ultimate-memory-stack" / "general-edition" / "overrides" / "compliance.override.md"
        if not override_path.exists():
            print(f"✗ ERROR: 'custom' preset requires {override_path}")
            print(f"  The 'custom' preset needs explicit configuration with ≥1 override — write that file first")
            print(f"  (see overrides/compliance-presets.override.md §5.4 for the pattern).")
            sys.exit(1)

    profile_path = working_dir / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    if not profile_path.exists():
        print(f"✗ PROFILE.md not found at {profile_path}")
        sys.exit(1)

    overrides_path = working_dir / "memory" / "user" / "USER_OVERRIDES.md"
    if not overrides_path.exists():
        # Deployment predates USER_OVERRIDES.md (or it was never created) —
        # create it now, empty of bootstrap values, so there's something to upsert into.
        create_user_overrides(working_dir, "none", [])

    # Backup before mutating (belt and suspenders — mirrors the pre-v4.0.0 PROFILE.md backup)
    backup_path = overrides_path.with_suffix(f".backup.{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.md")
    shutil.copy(overrides_path, backup_path)

    upsert_override_key(overrides_path, "compliance", f"compliance: {new_preset}")

    # Log
    log_audit_event(
        working_dir,
        action="preset-change",
        summary=f"Compliance preset changed to {new_preset}",
    )

    print(f"✓ Preset changed to {new_preset} (memory/user/USER_OVERRIDES.md)")
    print(f"→ At next session, Claude will re-validate existing entries")
    print(f"→ Entries failing new detection patterns route to quarantine")


def main():
    parser = argparse.ArgumentParser(
        description=f"Ultimate Memory Stack — General-Edition Setup v{STACK_VERSION}"
    )
    parser.add_argument("--working-dir", type=Path,
                        default=Path(os.environ.get("WORKING_DIR", str(Path.cwd()))),
                        help="Target deployment directory (env var WORKING_DIR honored; flag overrides env var)")
    parser.add_argument("--compliance", default="none",
                        help="none | enterprise | custom (PHI/healthcare is biotech-edition only)")
    parser.add_argument("--extensions", default="",
                        help="Comma-separated: gdpr,soc2,pci-dss")
    parser.add_argument("--migrate-from", choices=["v2.0", "v3.6"])
    parser.add_argument("--backup-location", type=Path)
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview --migrate-from=v3.6's planned actions; writes nothing")
    parser.add_argument("--change-preset")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--generate-hmac-secret", action="store_true")

    args = parser.parse_args()

    extensions = [e.strip() for e in args.extensions.split(",") if e.strip()] if args.extensions else []

    if args.verify or args.status:
        verify_environment(args.working_dir, args.compliance)
        return

    if args.change_preset:
        change_preset(args.working_dir, args.change_preset)
        return

    if args.migrate_from:
        migrate(args.working_dir, args.migrate_from, args.compliance, extensions, args)
        return

    setup_fresh(args.working_dir, args.compliance, extensions, args)


if __name__ == "__main__":
    main()
