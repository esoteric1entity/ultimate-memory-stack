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


def update_profile_compliance(profile_path: Path, new_preset: str):
    """Update compliance field in PROFILE.md."""
    content = profile_path.read_text(encoding="utf-8")
    content = re.sub(r"^compliance: \w+", f"compliance: {new_preset}", content, count=1, flags=re.MULTILINE)
    profile_path.write_text(content, encoding="utf-8")


def update_profile_extensions(profile_path: Path, extensions: list):
    """Add/update extensions list in PROFILE.md."""
    if not extensions:
        return
    content = profile_path.read_text(encoding="utf-8")
    ext_block = "extensions:\n" + "\n".join(f"  - {e}" for e in extensions)
    # Append after compliance line; simple approach
    content = re.sub(
        r"^(compliance: \w+)",
        rf"\1\n{ext_block}",
        content,
        count=1,
        flags=re.MULTILINE,
    )
    profile_path.write_text(content, encoding="utf-8")


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

    # Custom preset complexity floor
    if compliance_preset == "custom":
        override_path = SCRIPT_DIR / "overrides" / "compliance.override.md"
        if not override_path.exists():
            print(f"✗ ERROR: 'custom' preset requires {override_path}")
            print(f"  The 'custom' preset needs explicit configuration with ≥1 override.")
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

    # Update PROFILE.md
    profile_path = target_root / "general-edition" / "PROFILE.md"
    if compliance_preset != "none":
        update_profile_compliance(profile_path, compliance_preset)
    if extensions:
        update_profile_extensions(profile_path, extensions)

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
        f"extensions: {extensions if extensions else '[]'}\n"
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
    """Change compliance preset on existing deployment."""
    if new_preset in BIOTECH_ONLY:
        print(f"✗ '{new_preset}'/PHI handling is biotech-edition only, not available in the public general-edition.")
        sys.exit(1)
    if new_preset not in VALID_PRESETS:
        print(f"✗ Invalid preset: {new_preset}")
        sys.exit(1)

    profile_path = working_dir / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    if not profile_path.exists():
        print(f"✗ PROFILE.md not found at {profile_path}")
        sys.exit(1)

    # Backup
    backup_path = profile_path.with_suffix(f".backup.{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.md")
    shutil.copy(profile_path, backup_path)

    # Update
    update_profile_compliance(profile_path, new_preset)

    # Log
    log_audit_event(
        working_dir,
        action="preset-change",
        summary=f"Compliance preset changed to {new_preset}",
    )

    print(f"✓ Preset changed to {new_preset}")
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
