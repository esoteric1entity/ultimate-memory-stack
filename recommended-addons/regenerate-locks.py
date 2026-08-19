#!/usr/bin/env python3
"""
regenerate-locks.py — rebuild the add-on hash-pinned lockfiles.

Each add-on carries `locks/requirements-py<VER>.lock` for every Python version
in PYTHON_VERSIONS: a fully-resolved, hash-pinned closure compiled from that
add-on's `requirements.txt`.

WHY LOCKFILES EXIST
-------------------
`requirements.txt` expresses COMPATIBILITY (what versions are acceptable).
The lockfile expresses REPRODUCIBILITY (exactly what you get, verified by
hash). A version pin alone does not deliver "upstream moving cannot break our
users": the pinned package's own dependencies are still resolved live, so a
transitive release can change what lands. That is precisely how the graphify
add-on broke — an unsatisfiable `tree-sitter` bound went unnoticed because
nothing ever executed the manifest.

`--require-hashes` additionally makes the install tamper-evident: pip refuses
any artifact whose hash is not listed, so a compromised or substituted
distribution fails closed instead of installing silently.

The locks are `--universal`, so one file per Python version covers every
platform rather than pinning to whichever machine ran the compile.

USAGE
-----
    python recommended-addons/regenerate-locks.py            # all add-ons
    python recommended-addons/regenerate-locks.py graphify   # one add-on
    python recommended-addons/regenerate-locks.py --check    # verify only

Requires `uv` (https://docs.astral.sh/uv/). Install it however you prefer;
an isolated venv keeps it out of your working interpreter:

    python -m venv .lockenv && .lockenv/bin/pip install uv

WHEN TO RUN THIS
----------------
After ANY edit to an add-on's `requirements.txt`, and when deliberately
advancing a pin. Never edit a `.lock` by hand — regenerate it, then re-run the
add-on's smoke test. Advancing a pin is a security-vetting decision, not a
mechanical refresh; see each `requirements.txt` header.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Floor is the lowest version any add-on declares support for (graphifyy and
# graphiti-core both require_python >= 3.10). Keep in step with the
# `addon-manifests` CI job's matrix — a version tested there but not locked
# here would install unpinned.
PYTHON_VERSIONS = ("3.10", "3.11", "3.12", "3.13")

ADDONS_DIR = Path(__file__).resolve().parent


def _uv_command() -> list[str]:
    """Locate uv: on PATH, or inside a sibling venv, or as a module."""
    exe = shutil.which("uv")
    if exe:
        return [exe]
    for venv in (ADDONS_DIR.parent / "tmp" / "lockenv", ADDONS_DIR.parent / ".lockenv"):
        for rel in ("Scripts/python.exe", "bin/python"):
            candidate = venv / rel
            if candidate.exists():
                return [str(candidate), "-m", "uv"]
    return [sys.executable, "-m", "uv"]


def addon_dirs(names: list[str]) -> list[Path]:
    found = sorted(p for p in ADDONS_DIR.iterdir()
                   if p.is_dir() and (p / "requirements.txt").is_file())
    if not names:
        return found
    selected = []
    for name in names:
        matches = [p for p in found if p.name == name or p.name == f"{name}-installer"]
        if not matches:
            sys.exit(f"ERROR: no add-on matching {name!r}. Available: "
                     + ", ".join(p.name for p in found))
        selected.extend(matches)
    return selected


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("addons", nargs="*", help="Add-on names (default: all)")
    ap.add_argument("--check", action="store_true",
                    help="Verify every expected lockfile exists and is hash-pinned; write nothing.")
    args = ap.parse_args()

    targets = addon_dirs(args.addons)
    failures = 0

    if args.check:
        for addon in targets:
            for version in PYTHON_VERSIONS:
                lock = addon / "locks" / f"requirements-py{version}.lock"
                if not lock.is_file():
                    print(f"MISSING  {lock.relative_to(ADDONS_DIR.parent)}")
                    failures += 1
                elif "--hash=" not in lock.read_text(encoding="utf-8"):
                    print(f"NO HASHES {lock.relative_to(ADDONS_DIR.parent)}")
                    failures += 1
                else:
                    print(f"ok       {lock.relative_to(ADDONS_DIR.parent)}")
        return 1 if failures else 0

    uv = _uv_command()
    for addon in targets:
        (addon / "locks").mkdir(exist_ok=True)
        for version in PYTHON_VERSIONS:
            lock = addon / "locks" / f"requirements-py{version}.lock"
            print(f"{addon.name:24} py{version} ... ", end="", flush=True)
            proc = subprocess.run(
                uv + ["pip", "compile", "--quiet", "--generate-hashes", "--universal",
                      "--python-version", version,
                      "--output-file", str(lock), str(addon / "requirements.txt")],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
            if proc.returncode == 0:
                print("OK")
            else:
                print("FAILED")
                print(proc.stderr.strip()[-800:])
                failures += 1

    if failures:
        print(f"\n{failures} lockfile(s) failed to compile.", file=sys.stderr)
        return 1
    print("\nAll lockfiles regenerated. Re-run the add-on smoke tests before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
