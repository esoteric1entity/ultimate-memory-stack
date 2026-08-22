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
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Floor is the lowest version any add-on declares support for (graphifyy and
# graphiti-core both require_python >= 3.10). Keep in step with the
# `addon-manifests` CI job's matrix — a version tested there but not locked
# here would install unpinned.
PYTHON_VERSIONS = ("3.10", "3.11", "3.12", "3.13")

ADDONS_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Backend-integrity guards
#
# A lockfile that compiles cleanly is not the same as a lockfile that still
# contains the thing the add-on exists to install. Resolution succeeds happily
# after a backend silently drops out — you get exit 0 and a package that cannot
# do its job. These two guards make that failure loud.
# ---------------------------------------------------------------------------

# Packages that MUST appear pinned in every lock for an add-on. Structural,
# offline, and checked by --check as well as after a regeneration.
REQUIRED_PINS: dict[str, tuple[str, ...]] = {
    "graphiti-installer": ("graphiti-core", "kuzu"),
    "graphify-installer": ("graphifyy", "tree-sitter"),
    "llmlingua-installer": ("llmlingua", "torch", "transformers"),
}

# Upstream capabilities that must still exist for a pin to be meaningful.
#   addon -> (distribution to probe, extra that must survive, why it matters)
#
# The `kuzu` entry is the enforcement half of the maintenance position recorded
# in graphiti-installer/requirements.txt: Kuzu upstream is archived (Kùzu Inc.
# was acquired by Apple; final release 0.11.3, 2025-10-10) and graphiti-core has
# deprecated its `[kuzu]` extra without scheduling removal. We deliberately do
# NOT ceiling graphiti-core — the floor pin is how CVE patches reach users — so
# the safeguard belongs here, at the moment a maintainer advances the lock.
UPSTREAM_EXTRAS: dict[str, tuple[str, str, str]] = {
    "graphiti-installer": (
        "graphiti-core", "kuzu",
        "Kuzu is the only embedded backend that works on every platform this "
        "package supports (FalkorDB Lite cannot build on native Windows at all). "
        "If graphiti-core has dropped the kuzu extra, the driver is going or gone "
        "and the default backend must be reconsidered — do NOT just re-run this.",
    ),
}

# `name==1.2.3 \` at line start. The optional `[...]` matters: uv writes a
# requirement installed with extras as `name[extra]==1.2.3`, and without this
# group such a line would not match — the guard would then report a pinned
# package as missing, or miss it entirely. Kept in step with tests/test_addon_locks.py.
_PIN_RE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==([^\s\\;]+)", re.MULTILINE)


def _canon(name: str) -> str:
    """PEP 503 normalisation, so graphiti_core and graphiti-core compare equal."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _pins(lock_text: str) -> dict[str, str]:
    return {_canon(m.group(1)): m.group(2) for m in _PIN_RE.finditer(lock_text)}


def check_required_pins(addon: Path) -> list[str]:
    """Every lock for this add-on still pins the packages that define it."""
    required = REQUIRED_PINS.get(addon.name)
    if not required:
        return []
    errors = []
    for version in PYTHON_VERSIONS:
        lock = addon / "locks" / f"requirements-py{version}.lock"
        if not lock.is_file():
            continue  # absence is reported by the caller's own MISSING check
        pins = _pins(lock.read_text(encoding="utf-8"))
        for pkg in required:
            if _canon(pkg) not in pins:
                errors.append(
                    f"{lock.relative_to(ADDONS_DIR.parent)}: {pkg} is NOT pinned — "
                    f"this lock installs the add-on without it"
                )
    return errors


def probe_upstream_extra(addon: Path) -> list[str]:
    """Confirm the pinned distribution still declares the extra we depend on.

    Network is REQUIRED for a verdict here, and an UNREACHABLE network is not a
    verdict — offline, proxy, or a corporate DNS filter surfacing as a cert
    error all report UNVERIFIED and do not fail. A blocked host is not evidence
    that an upstream capability was removed.

    But "the server answered, and the answer was 404" IS evidence, and must not
    be filed under the same excuse. `HTTPError` subclasses `URLError` subclasses
    `OSError`, so a single broad `except` silently swallows a genuine "this
    version does not exist on PyPI" — a typo'd or deleted pin — as though the
    network were down. It is caught FIRST and separated here:
      404          -> the pinned release is not on PyPI. A real finding.
      other 4xx/5xx-> PyPI itself is unhappy (429, 503). UNVERIFIED.
      URLError/OSError -> could not reach PyPI at all. UNVERIFIED.
    """
    spec = UPSTREAM_EXTRAS.get(addon.name)
    if not spec:
        return []
    dist, extra, why = spec

    lock = addon / "locks" / f"requirements-py{PYTHON_VERSIONS[0]}.lock"
    if not lock.is_file():
        return []
    version = _pins(lock.read_text(encoding="utf-8")).get(_canon(dist))
    if not version:
        return [f"{addon.name}: {dist} is not pinned; cannot probe its extras"]

    url = f"https://pypi.org/pypi/{dist}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as fh:
            info = json.load(fh)["info"]
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return [
                f"{addon.name}: {dist}=={version} DOES NOT EXIST on PyPI (404).\n"
                f"      The lock pins a release the index does not have — a typo'd pin, or a\n"
                f"      release that was removed. Nobody can install this lock. (A merely\n"
                f"      YANKED release still returns 200 with metadata, so this is not that.)"
            ]
        print(f"  [?] {dist}=={version}: extras UNVERIFIED "
              f"(HTTP {exc.code}) — PyPI did not serve the metadata, not a failure")
        return []
    except (urllib.error.URLError, OSError, ValueError, KeyError) as exc:
        print(f"  [?] {dist}=={version}: extras UNVERIFIED "
              f"({type(exc).__name__}) — network unreachable, not a failure")
        return []

    if extra in (info.get("provides_extra") or []):
        print(f"  [+] {dist}=={version} still provides the '{extra}' extra")
        return []
    return [
        f"{addon.name}: {dist}=={version} NO LONGER declares the '{extra}' extra.\n"
        f"      {why}"
    ]


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
    ap.add_argument("--probe-upstream", action="store_true",
                    help="With --check (which is otherwise fully OFFLINE): also ask PyPI whether "
                         "each pinned distribution still declares the extra its backend depends "
                         "on. Ignored without --check, because regeneration ALWAYS probes.")
    ap.add_argument("--no-probe", action="store_true",
                    help="Skip that PyPI probe during regeneration, which performs it by default "
                         "— regeneration is the moment the risk is real. Use when working offline; "
                         "an unreachable PyPI would otherwise cost a 30s timeout per add-on.")
    args = ap.parse_args()
    if args.probe_upstream and not args.check:
        print("note: --probe-upstream applies to --check only; regeneration always probes "
              "(pass --no-probe to skip).", file=sys.stderr)

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
            for err in check_required_pins(addon):
                print(f"BACKEND  {err}")
                failures += 1
            if args.probe_upstream:
                for err in probe_upstream_extra(addon):
                    print(f"UPSTREAM {err}")
                    failures += 1
        return 1 if failures else 0

    uv = _uv_command()
    for addon in targets:
        (addon / "locks").mkdir(exist_ok=True)
        for version in PYTHON_VERSIONS:
            lock = addon / "locks" / f"requirements-py{version}.lock"
            print(f"{addon.name:24} py{version} ... ", end="", flush=True)
            # Paths passed REPO-RELATIVE, with cwd at the repo root — never
            # absolute. uv writes the invoking command verbatim into each lock's
            # header, so absolute paths bake the regenerating developer's local
            # directory layout and username into a file that ships in a public
            # repo. It also destroys the locks' minimal-diff property: the next
            # maintainer regenerating from a different checkout path produces a
            # header-only diff even when no dependency changed, burying the
            # signal these hash-pinned files exist to provide.
            repo_root = ADDONS_DIR.parent
            proc = subprocess.run(
                uv + ["pip", "compile", "--quiet", "--generate-hashes", "--universal",
                      "--python-version", version,
                      "--output-file", lock.relative_to(repo_root).as_posix(),
                      (addon / "requirements.txt").relative_to(repo_root).as_posix()],
                cwd=repo_root,
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

    # A clean compile is not a clean result — verify the locks still contain the
    # backends the add-ons exist to install, and that upstream still offers them.
    print("\nBackend integrity:")
    backend_errors: list[str] = []
    for addon in targets:
        backend_errors.extend(check_required_pins(addon))
        if args.no_probe:
            print(f"  [-] {addon.name}: upstream probe SKIPPED (--no-probe)")
        else:
            backend_errors.extend(probe_upstream_extra(addon))
    if backend_errors:
        print("\n" + "=" * 70, file=sys.stderr)
        print("BACKEND INTEGRITY FAILURE — locks compiled, but:", file=sys.stderr)
        for err in backend_errors:
            print(f"  [X] {err}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print("Do NOT commit these locks. See the add-on's requirements.txt "
              "header for the maintenance position.", file=sys.stderr)
        return 1

    print("\nAll lockfiles regenerated. Re-run the add-on smoke tests before committing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
