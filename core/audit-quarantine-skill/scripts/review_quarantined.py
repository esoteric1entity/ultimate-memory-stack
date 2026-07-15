#!/usr/bin/env python3
"""
review_quarantined.py — Standalone Audit Quarantine Review CLI
==============================================================

Python equivalent of the `/audit-quarantine` Skill. Implements the 9-step workflow
defined in SKILL.md for use outside of Claude Code Skills environment.

Authority: MEMORY_PROTOCOL_EXTENDED.md §E3.3
Companion: SKILL.md (Claude-executable equivalent)

Usage:
    python review_quarantined.py <working-dir> [--edition biotech|general] [--mode interactive|batch]

Modes:
    interactive  — Present each entry for review; user decides via stdin (default)
    batch        — Read decisions from stdin; one per line: "ACTION entry-id [reason]"

Exit codes:
    0 = success
    1 = invalid args
    2 = working-dir invalid
    3 = no quarantined entries
    4 = user aborted
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Legacy consoles (Windows cp1252, non-UTF-8 locales elsewhere) can't encode
# this script's review glyphs — force UTF-8 so output can never crash a
# review session (UnicodeEncodeError). Same guard as general-edition/setup.py.
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Audit Quarantine Review CLI")
    p.add_argument("working_dir", help="Working directory containing memory/quarantine/")
    p.add_argument("--edition", choices=["biotech", "general"], default="general")
    p.add_argument("--mode", choices=["interactive", "batch"], default="interactive")
    p.add_argument(
        "--default-action",
        dest="default_action",
        choices=["approve", "reject", "defer"],
        default=None,
        help="Non-interactive default action applied to every entry — bypasses prompt. "
             "Enables true batch mode under non-tty stdin (cron, CI). "
             "Biotech edition requires this WITH a reason when --mode batch is used.",
    )
    p.add_argument(
        "--default-reason",
        dest="default_reason",
        default="",
        help="Required reason text when --default-action defer is used under biotech edition (per B2 quarantine policy).",
    )
    p.add_argument("--session", type=int, default=0, help="Session number for log entries")
    p.add_argument("--actor", default="orchestrator", help="Actor identifier for log entries")
    return p.parse_args()


def iso_timestamp() -> str:
    """UTC ISO 8601 second-precision timestamp (canonical format)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def find_quarantined_entries(working_dir: Path) -> list[Path]:
    """Step 1: Find all .md files in memory/quarantine/."""
    quarantine_root = working_dir / "memory" / "quarantine"
    if not quarantine_root.exists():
        return []
    return sorted([p for p in quarantine_root.rglob("*.md") if p.is_file()])


def read_quarantine_log_for(entry_id: str, working_dir: Path) -> list[dict]:
    """Step 2: Read quarantine_log.jsonl for matching entry.

    Fix: Original implementation only matched the
    canonical `entry_id` field; legacy data may use `original_entry_id` instead.
    Added backward-compat by checking BOTH field names — handles legacy + canonical records uniformly.
    """
    log_path = working_dir / "memory" / "quarantine" / "quarantine_log.jsonl"
    if not log_path.exists():
        return []
    matches = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                # Backward-compat field match — canonical `entry_id` OR legacy `original_entry_id`
                if rec.get("entry_id") == entry_id or rec.get("original_entry_id") == entry_id:
                    matches.append(rec)
            except json.JSONDecodeError:
                continue
    return matches


def parse_entry_frontmatter(entry_path: Path) -> dict[str, str]:
    """Parse SCHEMA_A18 YAML-ish frontmatter from an entry file."""
    content = entry_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter = parts[1]
    result = {}
    for line in frontmatter.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def get_entry_category(entry_path: Path, working_dir: Path) -> str:
    """Derive original category from quarantine subdirectory."""
    relative = entry_path.relative_to(working_dir / "memory" / "quarantine")
    parts = relative.parts
    if len(parts) > 1:
        return parts[0]
    return "decisions"  # Default fallback


def present_entry(entry_path: Path, working_dir: Path, default_action: str | None = None) -> str:
    """Step 3: Show entry summary + content; return user decision.

    Fix: previously looked up quarantine metadata from the entry file's
    frontmatter, which doesn't carry the routing-event fields. Now correctly looks up from the
    matching quarantine_log.jsonl event by `entry_id`. Falls back to entry frontmatter if log silent.

    Fix: if default_action is supplied (non-interactive batch mode),
    return that action directly without calling input() — prevents EOFError under non-tty stdin.
    """
    frontmatter = parse_entry_frontmatter(entry_path)
    entry_id = frontmatter.get("id", entry_path.stem)
    category = get_entry_category(entry_path, working_dir)

    # Pull quarantine routing context from quarantine_log.jsonl FIRST (authoritative);
    # fall back to entry-file frontmatter only if log silent.
    log_records = read_quarantine_log_for(entry_id, working_dir)

    # Prefer the most recent routing event for headline metadata
    quarantine_ts = "<unknown>"
    quarantine_reason = "<unknown>"
    routing_agent = "<unknown>"
    for rec in reversed(log_records):
        # Headline metadata from the matching log record(s)
        if quarantine_ts == "<unknown>":
            quarantine_ts = rec.get("ts", rec.get("quarantined_at", "<unknown>"))
        if quarantine_reason == "<unknown>":
            # Try multiple key variants — JSONL schema has used both 'reason' and 'prior_quarantine_reason'
            quarantine_reason = (
                rec.get("prior_quarantine_reason")
                or rec.get("quarantine_reason")
                or rec.get("reason_code")
                or rec.get("reason")
                or quarantine_reason
            )
        if routing_agent == "<unknown>":
            routing_agent = rec.get("actor", rec.get("routing_agent", "<unknown>"))
        if quarantine_ts != "<unknown>" and quarantine_reason != "<unknown>" and routing_agent != "<unknown>":
            break

    # Final fallback to entry frontmatter
    if quarantine_reason == "<unknown>":
        quarantine_reason = frontmatter.get("quarantine_reason", "<unknown>")
    if quarantine_ts == "<unknown>":
        quarantine_ts = frontmatter.get("quarantine_ts", frontmatter.get("created_at", "<unknown>"))
    if routing_agent == "<unknown>":
        routing_agent = frontmatter.get("source_agent", "<unknown>")

    print("─" * 60)
    print(f"ENTRY: {entry_id}")
    print(f"Category: {category}")
    print(f"Quarantined at: {quarantine_ts}")
    print(f"Reason: {quarantine_reason}")
    print(f"Routing agent: {routing_agent}")
    print()
    print("ENTRY CONTENT (first 500 chars):")
    content = entry_path.read_text(encoding="utf-8")
    body = content.split("---", 2)[2] if "---" in content else content
    print(body.strip()[:500])
    print("..." if len(body.strip()) > 500 else "")
    print()
    print(f"QUARANTINE LOG CONTEXT ({len(log_records)} record(s)):")
    for rec in log_records[-3:]:  # Show last 3 records
        print(f"  {rec.get('ts', '<no-ts>')} | {rec.get('action', '<no-action>')} | {rec.get('outcome', '')}")
    print()

    # If default_action supplied (batch/non-interactive mode), skip prompt.
    if default_action is not None:
        action_upper = default_action.upper()
        print(f"[non-interactive] Applying default action: {action_upper}")
        return action_upper

    # Also detect non-tty stdin — if no terminal, fail gracefully instead of EOFError
    if not sys.stdin.isatty():
        print(f"[non-tty stdin detected] Defaulting to DEFER. Use --default-action {{approve,reject,defer}} to override.")
        return "DEFER"

    while True:
        print("Action?")
        print("  (a) APPROVE — release back to original category")
        print("  (b) REJECT — delete the entry")
        print("  (c) DEFER — leave in quarantine")
        print("  (d) DETAIL — show full entry content")
        print("  (e) SKIP TO END — defer all remaining")
        try:
            choice = input("Choice: ").strip().lower()
        except EOFError:
            # Belt-and-suspenders: if input() throws EOF (non-tty edge case), fall back to DEFER
            print("\n[EOFError on input — non-interactive stdin] Defaulting to DEFER.")
            return "DEFER"

        if choice in ("a", "approve"):
            return "APPROVE"
        elif choice in ("b", "reject"):
            return "REJECT"
        elif choice in ("c", "defer"):
            return "DEFER"
        elif choice in ("d", "detail"):
            print()
            print(body.strip())
            print()
        elif choice in ("e", "skip"):
            return "SKIP_TO_END"
        else:
            print(f"Invalid choice: {choice!r}. Please pick a/b/c/d/e.")


def apply_approve(entry_path: Path, working_dir: Path, category: str) -> Path:
    """Step 4: Move entry back to original category; update frontmatter."""
    entry_id = entry_path.stem
    target_dir = working_dir / "memory" / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / entry_path.name

    # Read current content; update frontmatter
    content = entry_path.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # Naive frontmatter update — replace `status: quarantined` and add resolution fields
    updated = content.replace("status: quarantined", "status: active")
    if "quarantine_resolved_at:" not in updated:
        # Insert before closing ---
        if "---" in updated[3:]:
            split_idx = updated.find("---", 3)
            updated = (
                updated[:split_idx]
                + f"quarantine_resolved_at: {today}\nquarantine_resolution: approved-after-review\n"
                + updated[split_idx:]
            )

    target_path.write_text(updated, encoding="utf-8")
    entry_path.unlink()
    return target_path


def apply_reject(entry_path: Path) -> None:
    """Step 5: Delete entry file."""
    entry_path.unlink()


def append_quarantine_log(working_dir: Path, entry: dict) -> None:
    """Step 6: Append decision to quarantine_log.jsonl."""
    log_path = working_dir / "memory" / "quarantine" / "quarantine_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def append_audit_log(working_dir: Path, entry: dict) -> None:
    """Step 7: Append decision to audit_log.jsonl."""
    log_path = working_dir / "memory" / "security" / "audit_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def main() -> int:
    args = parse_args()
    working_dir = Path(args.working_dir).resolve()

    if not working_dir.exists():
        print(f"ERROR: working-dir not found: {working_dir}", file=sys.stderr)
        return 2

    entries = find_quarantined_entries(working_dir)
    if not entries:
        print("[audit-quarantine] No quarantined entries found.")
        return 3

    print(f"[audit-quarantine] Found {len(entries)} quarantined entries to review.")
    print(f"[audit-quarantine] Edition: {args.edition} · Mode: {args.mode}")
    if args.default_action:
        print(f"[audit-quarantine] Non-interactive batch: default_action={args.default_action}, default_reason={args.default_reason!r}")
    print()

    # Biotech edition with --default-action defer REQUIRES --default-reason
    if args.edition == "biotech" and args.default_action == "defer" and not args.default_reason:
        print("ERROR: biotech edition + --default-action defer requires --default-reason (per B2 quarantine policy)", file=sys.stderr)
        return 1

    counters = {"APPROVE": 0, "REJECT": 0, "DEFER": 0, "SKIP_TO_END": 0}
    skip_to_end = False

    for entry_path in entries:
        if skip_to_end:
            decision = "DEFER"
        else:
            try:
                # Pass default_action through (None = interactive; otherwise non-interactive)
                decision = present_entry(entry_path, working_dir, default_action=args.default_action)
            except KeyboardInterrupt:
                print("\n[audit-quarantine] User aborted.")
                return 4

        if decision == "SKIP_TO_END":
            skip_to_end = True
            decision = "DEFER"

        # Biotech edition: DEFER requires reason
        reason = args.default_reason if args.default_action == "defer" else ""
        if args.edition == "biotech" and decision == "DEFER" and not reason:
            # Under non-tty stdin, this input() would have EOFError'd; now caught at present_entry
            # level (returns DEFER with empty reason); biotech enforcement below catches that case.
            if not sys.stdin.isatty():
                print(f"ERROR: biotech edition DEFER without --default-reason and no tty — aborting at entry {entry_path.name}", file=sys.stderr)
                return 1
            while not reason:
                try:
                    reason = input("DEFER reason (biotech edition requires explicit reason): ").strip()
                except EOFError:
                    print("\n[non-tty stdin] biotech DEFER requires --default-reason flag; aborting.", file=sys.stderr)
                    return 1

        frontmatter = parse_entry_frontmatter(entry_path)
        entry_id = frontmatter.get("id", entry_path.stem)
        category = get_entry_category(entry_path, working_dir)
        prior_quarantine_reason = frontmatter.get("quarantine_reason", "<unknown>")

        ts = iso_timestamp()

        if decision == "APPROVE":
            apply_approve(entry_path, working_dir, category)
            resolution = "approved-after-review"
        elif decision == "REJECT":
            apply_reject(entry_path)
            resolution = "rejected-after-review"
        else:  # DEFER
            resolution = f"deferred{f': {reason}' if reason else ''}"

        # Update logs
        append_quarantine_log(working_dir, {
            "ts": ts,
            "actor": args.actor,
            "session": args.session,
            "action": decision.lower(),
            "entry_id": entry_id,
            "entry_category": category,
            "resolution": resolution,
            "prior_quarantine_reason": prior_quarantine_reason,
        })

        append_audit_log(working_dir, {
            "ts": ts,
            "actor": args.actor,
            "session": args.session,
            "action": "audit-quarantine-review",
            "entry_id": entry_id,
            "outcome": decision.lower(),
            "decision_basis": resolution,
        })

        counters[decision] += 1
        print(f"  → {decision}: {entry_id}")
        print()

    # Step 8: Summary report
    print("=" * 60)
    print("✅ Audit Quarantine Review Complete")
    print("=" * 60)
    print(f"Total entries reviewed: {len(entries)}")
    print(f"  ✓ Approved: {counters['APPROVE']}")
    print(f"  ✗ Rejected: {counters['REJECT']}")
    print(f"  ⏸ Deferred: {counters['DEFER']}")
    print()
    print("Logs updated:")
    print(f"  - {working_dir}/memory/quarantine/quarantine_log.jsonl")
    print(f"  - {working_dir}/memory/security/audit_log.jsonl")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
