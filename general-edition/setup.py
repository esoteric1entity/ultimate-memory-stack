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

# Windows consoles often default to cp1252 — force UTF-8 so unicode glyphs in
# progress output cannot crash the install (UnicodeEncodeError).
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
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


def setup_fresh(working_dir: Path, compliance_preset: str, extensions: list, args):
    """Fresh install of general-edition."""
    print(f"\n=== Fresh Install: General-Edition v{STACK_VERSION} ===")
    print(f"Working directory: {working_dir}")
    print(f"Compliance preset: {compliance_preset}")
    print(f"Extensions: {extensions if extensions else 'none'}")

    # Self-reference guard (adversarial-round finding, 2026-07-14): SCRIPT_DIR is
    # wherever THIS script happens to be running from. If that's the INSTALLED
    # copy inside working_dir/ultimate-memory-stack/general-edition/, then
    # SCRIPT_DIR and the install target are the same directory — the "differs
    # from shipped" archive check below compares the file to itself (always
    # false, so a hand-edited PROFILE.md is never archived), and the wipe step
    # then deletes common-specs/ and tries to copytree FROM the path it just
    # deleted, crashing and permanently destroying the directory. Refuse before
    # any of that runs. --change-preset/--verify/--status don't reach this
    # function and remain safe to run from the installed copy.
    installed_general_edition = (working_dir / "ultimate-memory-stack" / "general-edition").resolve()
    if SCRIPT_DIR.resolve() == installed_general_edition:
        print(f"✗ ERROR: this is the INSTALLED copy of setup.py, running against its own directory.")
        print(f"  {SCRIPT_DIR} IS the install target — there is no separate shipped source to refresh from.")
        print(f"  To re-install or add extensions, run the ORIGINAL package's setup.py (the one you")
        print(f"  cloned/downloaded), not the copy inside {working_dir}.")
        print(f"  To change the compliance preset on this existing install, use --change-preset instead")
        print(f"  (safe to run from the installed copy).")
        sys.exit(1)

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
    shutil.copy(COMMON_SPECS_DIR / "MEMORY_PROTOCOL.md", claude_rules_dir / "memory_protocol.md")
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
    shutil.copy(COMMON_SPECS_DIR / "MEMORY_PROTOCOL_EXTENDED.md", memory_dir / "MEMORY_PROTOCOL_EXTENDED.md")

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
            summary=f"General-edition v{STACK_VERSION} initialized; preset={compliance_preset}; extensions={extensions}",
            entry_id="<bootstrap>",  # canonical init entry_id matches Bash setup.sh
        )
        print(f"✓ Audit log initialized (compliance: {compliance_preset})")

    # v4.0.0: compliance/extensions choices are USER choices — they land in
    # USER_OVERRIDES.md (create-once, never rewritten again), not PROFILE.md.
    # PROFILE.md's frontmatter carries only the shipped default and is never
    # edited by the installer (it stays regenerable — see PROFILE.md §2.1).
    create_user_overrides(working_dir, compliance_preset, extensions)

    # v4.0.0 hot/cold tiering (SPEC-hotcold-v4 §S4): pre-scaffold empty
    # ARCHIVE_INDEX.md files for the 3 tiered categories.
    create_archive_indexes(working_dir)

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
    parser.add_argument("--migrate-from", choices=["v2.0"])
    parser.add_argument("--backup-location", type=Path)
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

    setup_fresh(args.working_dir, args.compliance, extensions, args)


if __name__ == "__main__":
    main()
