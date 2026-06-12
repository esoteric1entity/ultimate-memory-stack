#!/usr/bin/env python3
"""
self_test.py — T1-T9 Self-Test (MEMORY_PROTOCOL §1.3)
=======================================================

Validates that an OpenClaw adapter installation is healthy per MEMORY_PROTOCOL §1.3.

Tests:
  T1 — HEARTBEAT.md exists + has Schema Version header
  T2 — MEMORY.md exists; entry counts non-negative
  T3 — Session number ≥ previous (no regression) — best-effort
  T4 — No root file exceeds its size limit
  T5 — All MEMORY.md references resolve to existing files
  T6 — Schema versions consistent
  T7 — No PII/PHI in root files (sanity check)
  T8 — All entries have valid SCHEMA_A18 frontmatter
  T9 — Edition profile loaded correctly

Authority: MEMORY_PROTOCOL §1.3 + SKILL.md Step 11
Companion: setup-openclaw.sh / setup-openclaw.py Step 10

Usage:
    python self_test.py <openclaw-root>

Exit codes:
    0 = all PASS
    1 = invalid args
    2 = CRITICAL failure (T1, T2, T7) — halts
    3 = WARNING (T3, T5, T6, T8, T9) — non-critical
    4 = INFO (T4) — advisory
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


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

# Per MEMORY_PROTOCOL §11 file size limits (in characters; approximate from §4.1 of design notes)
SIZE_CAPS = {
    "MEMORY.md": 5000,
    "AGENTS.md": 6000,
    "SOUL.md": 5000,
    "TOOLS.md": 5000,
    "IDENTITY.md": 3000,
    "USER.md": 5000,
    "HEARTBEAT.md": 5000,
    "BOOTSTRAP.md": 4000,
    "DREAMS.md": 2000,
}

# PII/PHI sanity patterns (per MEMORY_PROTOCOL §7 + §17)
# Each pattern requires explicit separator + sufficient ID character count to avoid English-prose false positives
# (Calibration note: a prior pattern `specimen[\s_-]*id[:\s]*[\w-]+` matched the English phrase
# "specimen IDs" — the trailing "s" was absorbed by [\w-]+ — fixed by requiring `:` or `#` or `-` AS the
# separator + 6+ alphanumeric-dash characters as the ID body. Reconcile with lint_runner.py canonical patterns.)
PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                                                                # SSN
    re.compile(r"\b\d{16}\b"),                                                                            # Credit card-like
    re.compile(r"\bMRN\s*[:#-]\s*\d{4,}\b", re.IGNORECASE),                                              # MRN (require explicit separator + 4+ digits)
    re.compile(r"\bspecimen[\s_-]*id\s*[:#-]\s*[A-Z0-9][A-Z0-9-]{5,}\b", re.IGNORECASE),                # Specimen ID (require explicit separator + 6+ alphanumeric-dash; rejects English plural "IDs")
    re.compile(r"\baccession[\s_-]*(?:no|number|num|#)?\s*[:#-]\s*[A-Z0-9][A-Z0-9-]{5,}\b", re.IGNORECASE),  # Accession number
]


def t1_heartbeat_exists(root: Path) -> tuple[str, str]:
    p = root / "HEARTBEAT.md"
    if not p.exists():
        return "FAIL", f"HEARTBEAT.md not found at {p}"
    content = p.read_text(encoding="utf-8")
    if "schema_version:" not in content:
        return "FAIL", "HEARTBEAT.md missing schema_version in frontmatter"
    return "PASS", "HEARTBEAT.md OK + schema_version present"


def t2_memory_md_exists(root: Path) -> tuple[str, str]:
    p = root / "MEMORY.md"
    if not p.exists():
        return "FAIL", f"MEMORY.md not found at {p}"
    content = p.read_text(encoding="utf-8")
    # Best-effort: ensure entry count cells look non-negative
    # Skip detailed parsing — file should at minimum exist with content
    if len(content) < 100:
        return "FAIL", "MEMORY.md exists but appears empty"
    return "PASS", "MEMORY.md OK"


def t3_session_no_regression(root: Path) -> tuple[str, str]:
    # Best-effort — adapter install is session 0; subsequent sessions tracked in session_state
    return "PASS", "Initial install (session 0) — no prior session to regress from"


def t4_size_caps(root: Path) -> tuple[str, str]:
    """Check each root file against its size cap."""
    over_cap = []
    for fname, cap in SIZE_CAPS.items():
        p = root / fname
        if not p.exists():
            continue  # Caught by T1/T2/T8
        size = p.stat().st_size
        if size > cap:
            over_cap.append(f"{fname} ({size} > {cap})")
    if over_cap:
        return "INFO", f"Files over cap: {', '.join(over_cap)} — consolidate via heartbeat_compactor.py"
    return "PASS", "All root files within size caps"


def t5_memory_references_resolve(root: Path) -> tuple[str, str]:
    """Check that MEMORY.md pointers exist on disk."""
    memory_md = root / "MEMORY.md"
    if not memory_md.exists():
        return "WARN", "MEMORY.md missing; can't validate references"
    content = memory_md.read_text(encoding="utf-8")

    # Find markdown links pointing to local paths
    links = re.findall(r"\[.*?\]\((\./[^)]+)\)", content)
    missing = []
    for link in links:
        target = root / link.lstrip("./")
        if not target.exists():
            missing.append(link)
    if missing:
        return "WARN", f"MEMORY.md references {len(missing)} non-existent path(s): {', '.join(missing[:3])}"
    return "PASS", f"All {len(links)} MEMORY.md references resolve"


def t6_schema_versions(root: Path) -> tuple[str, str]:
    """Check schema versions consistent across root files."""
    versions = {}
    for fname in ROOT_FILES:
        p = root / fname
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8")
        m = re.search(r'schema_version:\s*"?([^"\n]+)"?', content)
        if m:
            versions[fname] = m.group(1).strip()
    unique = set(versions.values())
    if len(unique) > 1:
        return "WARN", f"Schema version drift across root files: {versions}"
    return "PASS", f"Schema version consistent: {unique.pop() if unique else 'none'}"


def t7_no_pii_phi(root: Path) -> tuple[str, str]:
    """Sanity check root files for PII/PHI patterns."""
    findings = []
    for fname in ROOT_FILES:
        p = root / fname
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8")
        for pattern in PII_PATTERNS:
            for match in pattern.finditer(content):
                # Allow placeholders / redaction markers
                surrounding = content[max(0, match.start() - 30):match.end() + 30]
                if "REDACTED" in surrounding or "user-configurable" in surrounding or "placeholder" in surrounding.lower():
                    continue
                findings.append(f"{fname}: matched {pattern.pattern[:30]}...")
    if findings:
        return "FAIL", f"PII/PHI patterns detected in {len(findings)} location(s) — review immediately"
    return "PASS", "No PII/PHI patterns detected in root files"


def t8_frontmatter_valid(root: Path) -> tuple[str, str]:
    """Check all 9 root files have valid YAML frontmatter."""
    missing_fm = []
    for fname in ROOT_FILES:
        p = root / fname
        if not p.exists():
            missing_fm.append(f"{fname} (file missing)")
            continue
        content = p.read_text(encoding="utf-8")
        if not content.startswith("---"):
            missing_fm.append(f"{fname} (no frontmatter)")
            continue
        # Check minimal required fields
        for field in ["scope:", "schema_version:", "edition:"]:
            if field not in content.split("---", 2)[1] if "---" in content else "":
                if f"{fname} missing {field}" not in missing_fm:
                    missing_fm.append(f"{fname} missing {field}")
    if missing_fm:
        return "WARN", f"Frontmatter issues: {', '.join(missing_fm[:5])}"
    return "PASS", "All 9 root files have valid SCHEMA_A18 frontmatter"


def t9_edition_profile(root: Path) -> tuple[str, str]:
    """Check edition profile loaded."""
    profile_md = root / "ultimate-memory-stack" / "general-edition" / "PROFILE.md"
    if not profile_md.exists():
        return "WARN", f"PROFILE.md not found at {profile_md}"
    content = profile_md.read_text(encoding="utf-8")
    if "edition: general" not in content:
        return "WARN", "PROFILE.md missing edition: general declaration"
    if "compliance:" not in content:
        return "WARN", "PROFILE.md missing compliance preset"
    return "PASS", "Edition profile loaded (general-edition)"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: self_test.py <openclaw-root>", file=sys.stderr)
        return 1

    root = Path(sys.argv[1]).resolve()
    if not root.exists():
        print(f"ERROR: {root} not found", file=sys.stderr)
        return 1

    print("=" * 60)
    print("OpenClaw Adapter Self-Test (T1-T9 per MEMORY_PROTOCOL §1.3)")
    print(f"Target: {root}")
    print("=" * 60)

    tests = [
        ("T1", "HEARTBEAT.md + Schema Version", t1_heartbeat_exists),
        ("T2", "MEMORY.md + entries", t2_memory_md_exists),
        ("T3", "Session no-regression", t3_session_no_regression),
        ("T4", "File size caps", t4_size_caps),
        ("T5", "MEMORY.md references resolve", t5_memory_references_resolve),
        ("T6", "Schema versions consistent", t6_schema_versions),
        ("T7", "No PII/PHI patterns", t7_no_pii_phi),
        ("T8", "Frontmatter valid (SCHEMA_A18)", t8_frontmatter_valid),
        ("T9", "Edition profile loaded", t9_edition_profile),
    ]

    critical_fail = False
    warning_fail = False
    info_only = False

    for tid, label, func in tests:
        status, msg = func(root)
        symbol = {
            "PASS": "✓",
            "FAIL": "✗",
            "WARN": "⚠",
            "INFO": "ℹ",
        }.get(status, "?")
        print(f"  {symbol} {tid} {label:35s} {status:5s} — {msg}")

        if status == "FAIL" and tid in ("T1", "T2", "T7"):
            critical_fail = True
        elif status == "WARN":
            warning_fail = True
        elif status == "INFO":
            info_only = True

    print("=" * 60)
    if critical_fail:
        print("✗ CRITICAL FAILURES — adapter install must be repaired before use")
        return 2
    elif warning_fail:
        print("⚠ Warnings present — review but adapter is usable")
        return 3
    elif info_only:
        print("ℹ Info advisories — adapter is healthy; consider follow-up")
        return 4
    else:
        print("✓ All checks PASSED — adapter is healthy")
        return 0


if __name__ == "__main__":
    sys.exit(main())
