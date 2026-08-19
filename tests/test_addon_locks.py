"""Tests for the add-on hash-pinned lockfiles.

Every add-on with a `requirements.txt` carries `locks/requirements-py<VER>.lock`
for each supported Python version: a fully-resolved, hash-pinned closure.

`requirements.txt` expresses COMPATIBILITY; the lock expresses REPRODUCIBILITY.
A version pin alone does not make "upstream moving cannot break our users"
true — the pinned package's own dependencies still resolve live, which is how
the graphify add-on shipped v4.0.0 uninstallable.

These checks are deliberately OFFLINE. The `addon-manifests` CI job does the
live resolve; this suite catches the far more common failure — someone edits a
`requirements.txt` and does not regenerate the locks, so the shipped lock
silently no longer matches the manifest it claims to lock.
"""

from __future__ import annotations

import pathlib
import re

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
ADDONS = PKG / "recommended-addons"

# Must match recommended-addons/regenerate-locks.py PYTHON_VERSIONS and the
# `addon-manifests` CI matrix. A version tested live but not locked here would
# install unpinned.
PYTHON_VERSIONS = ("3.10", "3.12", "3.13")

ADDON_DIRS = sorted(p for p in ADDONS.iterdir()
                    if p.is_dir() and (p / "requirements.txt").is_file())

# `name==1.2.3 \` at the start of a lock line. uv writes extras as `name[x]==`.
LOCK_PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==([^\s\\;]+)", re.MULTILINE)


def _canon(name: str) -> str:
    """PEP 503 normalization — `tree_sitter`, `Tree-Sitter` and `tree-sitter`
    are the same project."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_names(req_file: pathlib.Path) -> set[str]:
    """Top-level requirement names from a requirements.txt, ignoring comments,
    blank lines, and commented-out optional entries."""
    names = set()
    for raw in req_file.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if m:
            names.add(_canon(m.group(1)))
    return names


def _lock_pins(lock_file: pathlib.Path) -> dict[str, str]:
    text = lock_file.read_text(encoding="utf-8")
    return {_canon(m.group(1)): m.group(2) for m in LOCK_PIN.finditer(text)}


def test_addon_dirs_discovered():
    """Guard against the whole suite silently passing on an empty list."""
    assert ADDON_DIRS, "no add-ons with a requirements.txt were found"


@pytest.mark.parametrize("addon", ADDON_DIRS, ids=lambda p: p.name)
@pytest.mark.parametrize("version", PYTHON_VERSIONS)
def test_lockfile_exists(addon, version):
    lock = addon / "locks" / f"requirements-py{version}.lock"
    assert lock.is_file(), (
        f"{lock.relative_to(PKG)} is missing — run "
        f"`python recommended-addons/regenerate-locks.py`"
    )


@pytest.mark.parametrize("addon", ADDON_DIRS, ids=lambda p: p.name)
@pytest.mark.parametrize("version", PYTHON_VERSIONS)
def test_lockfile_is_hash_pinned(addon, version):
    """A lock without hashes gives reproducibility but not tamper-evidence —
    `pip install --require-hashes` would reject it outright."""
    lock = addon / "locks" / f"requirements-py{version}.lock"
    text = lock.read_text(encoding="utf-8")
    assert "--hash=" in text, f"{lock.relative_to(PKG)} has no hashes"
    pins = _lock_pins(lock)
    assert pins, f"{lock.relative_to(PKG)} pins nothing"
    # Every pinned distribution must carry at least one hash. Count blocks
    # rather than trusting a single occurrence anywhere in the file.
    assert text.count("--hash=") >= len(pins), (
        f"{lock.relative_to(PKG)}: {len(pins)} pins but only "
        f"{text.count('--hash=')} hashes"
    )


@pytest.mark.parametrize("addon", ADDON_DIRS, ids=lambda p: p.name)
@pytest.mark.parametrize("version", PYTHON_VERSIONS)
def test_lock_covers_every_top_level_requirement(addon, version):
    """The regeneration-drift check: if someone adds a dependency to
    requirements.txt without re-running regenerate-locks.py, the shipped lock
    no longer locks what the manifest asks for."""
    lock = addon / "locks" / f"requirements-py{version}.lock"
    required = _requirement_names(addon / "requirements.txt")
    locked = set(_lock_pins(lock))

    # Entries gated behind an environment marker legitimately drop out of a
    # lock for a Python version they exclude (e.g. `kuzu; python_version <
    # "3.12"`). Only those may be absent.
    #
    # An earlier version of this check excused ANY requirement that appeared in
    # some OTHER lock. That was too permissive in precisely the scenario the
    # module docstring says this exists to catch: regenerate one lock after
    # editing the manifest, leave the other two stale, and all three pass.
    # Marker-gated entries are now identified from the MANIFEST, not inferred
    # from the other locks.
    marker_gated = set()
    for raw in (addon / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ";" not in line:
            continue
        name = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if name:
            marker_gated.add(_canon(name.group(1)))

    truly_missing = sorted((required - locked) - marker_gated)
    assert not truly_missing, (
        f"{addon.name}: requirements.txt lists {truly_missing} but "
        f"requirements-py{version}.lock does not pin them — run "
        f"`python recommended-addons/regenerate-locks.py`"
    )


@pytest.mark.parametrize("addon", ADDON_DIRS, ids=lambda p: p.name)
def test_locked_version_satisfies_the_manifest_constraint(addon):
    """Catches the subtler drift: the manifest's pin was CHANGED but the lock
    still carries the old resolution, so users install a version the manifest
    forbids."""
    packaging = pytest.importorskip("packaging.specifiers")
    from packaging.requirements import Requirement
    from packaging.version import InvalidVersion, Version

    constraints = {}
    for raw in (addon / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        try:
            req = Requirement(line)
        except Exception:
            continue
        if req.specifier:
            constraints[_canon(req.name)] = req.specifier

    violations = []
    for version in PYTHON_VERSIONS:
        lock = addon / "locks" / f"requirements-py{version}.lock"
        if not lock.is_file():
            continue
        pins = _lock_pins(lock)
        for name, spec in constraints.items():
            if name not in pins:
                continue
            try:
                locked_version = Version(pins[name])
            except InvalidVersion:
                continue
            if not spec.contains(locked_version, prereleases=True):
                violations.append(f"py{version}: {name}=={pins[name]} violates '{spec}'")

    assert not violations, (
        f"{addon.name}: lockfile(s) out of step with requirements.txt — "
        f"{violations}. Run `python recommended-addons/regenerate-locks.py`."
    )
