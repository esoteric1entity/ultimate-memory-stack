#!/usr/bin/env python3
"""
preflight.py — report what an add-on will install, versus what upstream has now.

Answers the question a pinned manifest cannot: *is the version we vetted still
a reasonable thing to install today?* For each top-level requirement it prints
the constraint this package ships, the latest version on PyPI, and when that
version was published — so an abandoned dependency is visible BEFORE install
rather than discovered months later.

This exists because `kuzu` went ten months without a release while our manifest
still presented it as the vetted recommendation, and because `graphifyy` drifted
77 releases past our pin without anything surfacing it. The kuzu case shows the
limit of a staleness signal as well as its value: the reason for the silence was
that the repo had been ARCHIVED and the company acquired, which no release-date
heuristic can tell you. Read a flag here as "go look", never as a diagnosis.

INFORMATIONAL BY DEFAULT. It never blocks an install and never edits anything.
Advancing a pin is a security-vetting decision (see each `requirements.txt`
header), not something a script should do on your behalf.

USAGE
-----
    python recommended-addons/preflight.py                 # all add-ons
    python recommended-addons/preflight.py graphify        # one add-on
    python recommended-addons/preflight.py --strict        # exit 1 on a stale dep
    python recommended-addons/preflight.py --offline       # skip network entirely

Requires only the standard library. Needs network access for the upstream
column; without it, every row degrades to "unknown" and the exit code is
unchanged — being offline is not a finding.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

if __name__ == "__main__":
    # Package metadata carries arbitrary Unicode (a star glyph in one summary
    # was enough to kill a run under cp1252). Same guard as setup.py.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

ADDONS_DIR = Path(__file__).resolve().parent

# Days since the latest release before a dependency is called out as cold.
# ~9 months: long enough that ordinary quiet periods don't trip it, short
# enough to catch genuine abandonment while it still matters.
STALE_DAYS = 270

REQ_LINE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(\[[^\]]*\])?\s*([^;]*)(;.*)?$")


def parse_requirements(path: Path) -> list[tuple[str, str, str]]:
    """Return (name, specifier, marker) for each active top-level requirement.
    Commented-out optional entries are deliberately skipped — they are not
    what this install will pull."""
    out = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = REQ_LINE.match(line)
        if m:
            out.append((m.group(1), (m.group(3) or "").strip(), (m.group(4) or "").strip(" ;")))
    return out


def pypi_info(name: str, timeout: float = 15.0) -> dict | None:
    try:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/json", timeout=timeout) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    version = data.get("info", {}).get("version")
    files = data.get("releases", {}).get(version) or []
    uploaded = files[0].get("upload_time_iso_8601") or files[0].get("upload_time") if files else None
    return {"version": version, "uploaded": uploaded}


def days_since(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        stamp = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - stamp).days


def main() -> int:
    ap = argparse.ArgumentParser(description="Report add-on dependency freshness before install.")
    ap.add_argument("addons", nargs="*", help="Add-on names (default: all)")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any dependency's latest release is older than the staleness threshold.")
    ap.add_argument("--offline", action="store_true", help="Skip network lookups.")
    args = ap.parse_args()

    # Two layouts. In the package this script sits in `recommended-addons/`
    # alongside one directory per add-on. The installers also copy it INTO each
    # installed skill directory, where `requirements.txt` is a sibling and
    # there are no add-on subdirectories — handle both so the installed copy is
    # not silently a no-op.
    if (ADDONS_DIR / "requirements.txt").is_file():
        available = [ADDONS_DIR]
    else:
        available = sorted(p for p in ADDONS_DIR.iterdir()
                           if p.is_dir() and (p / "requirements.txt").is_file())
    if args.addons:
        wanted = set(args.addons) | {f"{a}-installer" for a in args.addons}
        targets = [p for p in available if p.name in wanted]
        if not targets:
            print("No matching add-on. Available: " + ", ".join(p.name for p in available),
                  file=sys.stderr)
            return 2
    else:
        targets = available

    stale_found = False
    unreachable = 0

    for addon in targets:
        print(f"\n{addon.name}")
        print("  " + "-" * 74)
        for name, spec, marker in parse_requirements(addon / "requirements.txt"):
            ships = spec or "(any)"
            suffix = f"  [{marker}]" if marker else ""
            if args.offline:
                print(f"  {name:<18} ships {ships:<24} upstream unknown (offline){suffix}")
                continue
            info = pypi_info(name)
            if info is None or not info.get("version"):
                unreachable += 1
                print(f"  {name:<18} ships {ships:<24} upstream unreachable{suffix}")
                continue
            age = days_since(info.get("uploaded"))
            when = (info.get("uploaded") or "")[:10] or "?"
            note = ""
            if age is not None and age >= STALE_DAYS:
                note = f"  <-- COLD: no release in {age} days"
                stale_found = True
            print(f"  {name:<18} ships {ships:<24} upstream {info['version']} ({when}){note}{suffix}")

    print()
    if unreachable:
        print(f"note: {unreachable} package(s) could not be reached — being offline is not a finding.")
    if stale_found:
        print("One or more dependencies look abandoned upstream. That is a risk to accept")
        print("deliberately, not a reason the install will fail. See the add-on's")
        print("requirements.txt header for the reasoning behind its current pin.")
    if args.strict and stale_found:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
