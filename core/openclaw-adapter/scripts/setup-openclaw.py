#!/usr/bin/env python3
"""
setup-openclaw.py — OpenClaw General Edition Adapter Installer (Python parity)
================================================================================

Python parity to setup-openclaw.sh — Bash and Python
implementations MUST stay in sync; never let one drift ahead.

Authority: SKILL.md (workflow source); idempotent re-runs by design
Foundation: MAPPING.md

Usage:
    python setup-openclaw.py <openclaw-root> [--compliance none|enterprise] [--no-cron] [--update-profile]

Exit codes:
    0 = success
    1 = invalid arguments
    2 = OpenClaw not detected
    3 = adapter templates missing
    4 = self-test failed
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Legacy consoles (Windows cp1252, non-UTF-8 locales elsewhere) can't encode
# this script's progress glyphs — force UTF-8 so output can never crash the
# install (UnicodeEncodeError). Same guard as general-edition/setup.py.
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


ROOT_FILES = [
    "MEMORY.md",
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "IDENTITY.md",
    "USER.md",
    "HEARTBEAT.md",
    "BOOTSTRAP.md",
    "DREAMS.md",
]

MEMORY_SUBDIRS = [
    "memory/decisions",
    "memory/sessions",
    "memory/feedback",
    "memory/feedback/archive",
    "memory/security",
    "memory/references",
    "memory/user",
    "memory/projects",
    "memory/archive/heartbeats",
    "memory/archive/daily_logs",
    "memory/quarantine",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenClaw General Edition Adapter installer")
    parser.add_argument("openclaw_root", help="Path to OpenClaw harness root")
    parser.add_argument(
        "--compliance",
        choices=["none", "enterprise"],
        default="none",
        help="Compliance preset (healthcare not supported in this edition)",
    )
    parser.add_argument("--no-cron", action="store_true", help="Skip cron wiring suggestion")
    parser.add_argument("--update-profile", action="store_true", help="Update PROFILE.md only; skip all other steps")
    return parser.parse_args()


def step_1_detect_openclaw(openclaw_root: Path) -> None:
    print("[Step 1] Detecting OpenClaw installation...")
    if not openclaw_root.exists():
        print(f"ERROR: {openclaw_root} does not exist", file=sys.stderr)
        sys.exit(2)
    openclaw_meta = openclaw_root / ".openclaw"
    if not openclaw_meta.exists():
        print(f"  WARN: {openclaw_meta} not found — proceeding with fresh-install assumption")
        openclaw_meta.mkdir(parents=True, exist_ok=True)
    print("  OpenClaw root: OK")


def step_2_backup(openclaw_root: Path, datestamp: str) -> int:
    print("\n[Step 2] Backing up existing root files...")
    backup_dir = openclaw_root / ".openclaw" / "backup" / f"pre-adapter-install-{datestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backed_up = 0
    for fname in ROOT_FILES:
        src = openclaw_root / fname
        if src.exists():
            shutil.copy2(src, backup_dir / fname)
            backed_up += 1
    print(f"  Backed up: {backed_up} existing root files → {backup_dir}")
    return backed_up


def step_3_verify_templates(templates_dir: Path) -> None:
    print("\n[Step 3] Verifying adapter templates...")
    missing = []
    for fname in ROOT_FILES:
        tmpl = templates_dir / f"{fname}.template"
        if not tmpl.exists():
            missing.append(tmpl.name)
    if missing:
        print("ERROR: Adapter templates missing:", file=sys.stderr)
        for t in missing:
            print(f"  - {t}", file=sys.stderr)
        sys.exit(3)
    print("  All 9 templates present: OK")


def step_4_generate_root_files(openclaw_root: Path, templates_dir: Path) -> None:
    print("\n[Step 4] Generating 9 root files...")
    for fname in ROOT_FILES:
        src = templates_dir / f"{fname}.template"
        dst = openclaw_root / fname
        shutil.copy2(src, dst)
        print(f"  {fname}")


def step_5_memory_tree(openclaw_root: Path) -> None:
    print("\n[Step 5] Generating memory/ subdirectory tree...")
    for d in MEMORY_SUBDIRS:
        (openclaw_root / d).mkdir(parents=True, exist_ok=True)
        print(f"  {d}/")


def step_6_init_logs(openclaw_root: Path, datestamp: str, timestamp: str, compliance: str) -> None:
    print("\n[Step 6] Initializing audit + quarantine logs...")
    audit_log = openclaw_root / "memory" / "security" / "audit_log.jsonl"
    audit_log.touch(exist_ok=True)

    # Append adapter-install event (compact JSON, second-precision timestamps)
    event = {
        "ts": timestamp,
        "actor": "orchestrator",
        "session": 0,
        "action": "adapter-install",
        "entry_id": "<bootstrap>",
        "subject": "openclaw-general-edition-adapter-v1.0",
        "outcome": "success",
        "compliance": compliance,
    }
    with audit_log.open("a") as f:
        f.write(json.dumps(event, separators=(",", ":")) + "\n")

    (openclaw_root / "memory" / "quarantine" / "quarantine_log.jsonl").touch(exist_ok=True)
    (openclaw_root / "memory" / "archive" / "daily_logs" / f"DAILY_LOG_{datestamp}.md").touch(exist_ok=True)

    print("  audit_log.jsonl: initialized with adapter-install event (canonical format)")
    print("  quarantine_log.jsonl: empty")
    print(f"  DAILY_LOG_{datestamp}.md: created")


def step_7_write_profile(openclaw_root: Path, compliance: str, timestamp: str) -> None:
    print("\n[Step 7] Writing edition profile...")
    profile_dir = openclaw_root / "ultimate-memory-stack" / "general-edition"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / "PROFILE.md"

    profile_content = f"""# General Edition Profile

---
edition: general
compliance: {compliance}
audit_log: false
quarantine_ux: toast
pattern_key_recurrence_threshold: 5
signature_scheme: none
adapter_version: "1.0"
adapter_installed_at: "{timestamp}"
---

## Active settings

- **Edition:** general-edition
- **Compliance preset:** {compliance}
- **Audit log:** opt-in (default OFF)
- **Quarantine UX:** toast (one-line at session start)
- **Pattern-key recurrence threshold:** 5 (per MEMORY_PROTOCOL §4.2 B6)
- **Cryptographic signatures:** none (NOT IMPLEMENTED in this release)

## Addon registry

(Populated by addon installer Skills on completion.)

```yaml
addons: {{}}
```

## Cross-references

- MEMORY_PROTOCOL §6 (edition profile application)
- Compliance preset (healthcare not supported in this edition)
- Modular consumer architecture (adapter design principle)
"""
    profile_path.write_text(profile_content, encoding="utf-8")
    print("  PROFILE.md: written")


def step_8_install_lint(openclaw_root: Path, script_dir: Path) -> None:
    print("\n[Step 8] Installing Lint runner...")
    lint_dir = openclaw_root / ".openclaw" / "lint"
    lint_dir.mkdir(parents=True, exist_ok=True)

    # lint_runner.py moved to core/shared-tools/ in v4.0.0 (shared cross-harness
    # tooling, not adapter-specific) — script_dir is core/openclaw-adapter/scripts/.
    src = script_dir.parent.parent / "shared-tools" / "lint_runner.py"
    if src.exists():
        shutil.copy2(src, lint_dir / "lint_runner.py")
        print(f"  lint_runner.py: installed at {lint_dir}")
    else:
        print(f"  WARN: lint_runner.py not found at {src}")


def step_9_install_heartbeat_compactor(openclaw_root: Path, script_dir: Path, wire_cron: bool) -> None:
    print("\n[Step 9] Installing heartbeat compactor...")
    src = script_dir / "heartbeat_compactor.py"
    if src.exists():
        shutil.copy2(src, openclaw_root / ".openclaw" / "heartbeat_compactor.py")
        print(f"  heartbeat_compactor.py: installed at {openclaw_root / '.openclaw'}")
    else:
        print(f"  WARN: heartbeat_compactor.py not found in {script_dir}")

    if wire_cron:
        print("")
        print("=" * 60)
        print("CRON ENTRY — Add this to your crontab manually via 'crontab -e':")
        print("=" * 60)
        print(f"""
# Ultimate Memory Stack — heartbeat compactor (active hours 08-22 + idle checkpoints)
*/30 8-22 * * * cd "{openclaw_root}" && python3 .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1
0 0,6 * * * cd "{openclaw_root}" && python3 .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1
""")
        print("=" * 60)
        print("Per SKILL.md Step 9: this script does NOT mutate crontab (security boundary).")
        print("Run 'crontab -e' yourself and paste the entry above.")
        print("")


def step_10_self_test(openclaw_root: Path, script_dir: Path) -> str | None:
    """Run T1-T9; returns a status label for the summary, or None on failure.

    Exit codes interpreted per self_test.py's own contract (0=PASS,
    2=CRITICAL, 3=WARN, 4=INFO) — warn/info are non-blocking, the install is
    valid. setup-openclaw.sh Step 10 has always handled this correctly; this
    function used to treat ANY non-zero as failure, so every fresh install
    (where T5 warns about not-yet-created memory files) exited 4 and skipped
    the Step-11 install log. Parity restored to the Bash behavior.

    Note the exit-code namespaces are distinct: THIS installer's own exit 4
    means "self-test failed", while self_test.py's exit 4 means INFO
    (non-blocking) — do not conflate them when wrapping either script.
    """
    print("\n[Step 10] Running T1-T9 self-test...")
    self_test = script_dir / "self_test.py"
    if not self_test.exists():
        print(f"  WARN: self_test.py not found in {script_dir}; skipping")
        return "SKIPPED (self_test.py not found)"

    result = subprocess.run(
        [sys.executable, str(self_test), str(openclaw_root)],
        capture_output=False,
    )
    if result.returncode == 0:
        print("  self_test.py: PASSED (all T1-T9 green)")
        return "PASSED"
    if result.returncode == 3:
        print("  self_test.py: PASSED with WARNINGS (T1-T9 mostly green; non-blocking warns)")
        print("  Install is valid — review warnings above when convenient.")
        return "PASSED with warnings"
    if result.returncode == 4:
        print("  self_test.py: PASSED with INFO notes (T1-T9 green; informational items)")
        print("  Install is valid — review info notes above when convenient.")
        return "PASSED with info notes"
    if result.returncode == 2:
        print("  self_test.py: FAILED (CRITICAL — see output above)", file=sys.stderr)
        return None
    print(f"  self_test.py: FAILED (unexpected exit code {result.returncode})", file=sys.stderr)
    return None


def step_11_log_install(openclaw_root: Path, datestamp: str, compliance: str, wire_cron: bool) -> None:
    print("\n[Step 11] Logging installation...")
    decisions_md = openclaw_root / "memory" / "decisions" / "decisions.md"

    # Create header if file doesn't exist
    if not decisions_md.exists():
        decisions_md.write_text(
            f"""# Decisions Log

> **Schema Version:** 3.0
> **Created:** {datestamp} (adapter install)
> **Entries:** 0
""",
            encoding="utf-8",
        )

    dec_entry = f"""

## DEC-INSTALL: OpenClaw General Edition Adapter Installed

---
id: DEC-INSTALL
created_at: {datestamp}
last_updated: {datestamp}
source_agent: orchestrator
source_session: 0
status: active
schema_version: "3.0"
confidence: FINAL
---

- **Status:** FINAL
- **Confidence:** 1.0
- **Session:** 0 (adapter install)
- **Date:** {datestamp}
- **Decision:** Installed Ultimate Memory Stack General Edition Adapter v1.0 on this OpenClaw deployment
- **Compliance preset:** {compliance}
- **Cron wired:** {wire_cron}
- **Cross-references:** MAPPING.md
- **Tags:** adapter-installed, openclaw, general-edition, v3-5
"""
    with decisions_md.open("a", encoding="utf-8") as f:
        f.write(dec_entry)

    print("  decisions.md: DEC-INSTALL appended")


def main() -> int:
    args = parse_args()
    openclaw_root = Path(args.openclaw_root).resolve()
    compliance = args.compliance
    wire_cron = not args.no_cron

    script_dir = Path(__file__).parent
    adapter_root = script_dir.parent
    templates_dir = adapter_root / "templates"

    datestamp = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    print("=" * 60)
    print("OpenClaw General Edition Adapter — Installer (Python)")
    print("=" * 60)
    print(f"OpenClaw root:     {openclaw_root}")
    print(f"Compliance preset: {compliance}")
    print(f"Wire cron:         {wire_cron}")
    print(f"Templates from:    {templates_dir}")
    print("=" * 60)

    step_1_detect_openclaw(openclaw_root)
    step_2_backup(openclaw_root, datestamp)
    step_3_verify_templates(templates_dir)
    step_4_generate_root_files(openclaw_root, templates_dir)
    step_5_memory_tree(openclaw_root)
    step_6_init_logs(openclaw_root, datestamp, timestamp, compliance)
    step_7_write_profile(openclaw_root, compliance, timestamp)

    if args.update_profile:
        print("\n[--update-profile mode] Profile updated. Skipping subsequent steps.")
        return 0

    step_8_install_lint(openclaw_root, script_dir)
    step_9_install_heartbeat_compactor(openclaw_root, script_dir, wire_cron)

    self_test_status = step_10_self_test(openclaw_root, script_dir)
    if self_test_status is None:
        return 4

    step_11_log_install(openclaw_root, datestamp, compliance, wire_cron)

    print("\n" + "=" * 60)
    print("✅ OpenClaw General Edition Adapter installed successfully")
    print("=" * 60)
    print()
    print(f"Root files:           9 generated at {openclaw_root}/")
    print(f"Memory tree:          {len(MEMORY_SUBDIRS)} subdirectories created")
    print(f"Compliance preset:    {compliance}")
    print("Lint runner:          installed at .openclaw/lint/")
    print("Heartbeat compactor:  installed at .openclaw/")
    print(f"Self-test:            {self_test_status}")
    print()
    print("Next steps:")
    print(f"  1. Open OpenClaw in this directory: {openclaw_root}")
    print("  2. Verify bootstrap budget under 60K (check OpenClaw startup log)")
    if wire_cron:
        print("  3. Paste the cron entry above via 'crontab -e'")
    print("  4. Optionally install addons:")
    print("     /install-llmlingua  /install-graphiti  /install-graphify  /config-obsidian-vault")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
