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
PYTHON_VERSIONS = ("3.10", "3.11", "3.12", "3.13")

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


# ---------------------------------------------------------------------------
# Backend-integrity guards (regenerate-locks.py)
#
# A lock that compiles is not a lock that works. `uv pip compile` succeeds
# happily on a manifest whose backend has silently dropped out, so these guard
# the thing the guards guard: that the enforcement in regenerate-locks.py is
# real and fires.
#
# These tests are OFFLINE by design — the network path is monkeypatched, so a
# passing suite says nothing about upstream's current state. The LIVE probe runs
# in CI instead: the `addon-manifests` job executes
# `regenerate-locks.py --check --probe-upstream` (ubuntu/py3.13 leg). Keep that
# step and these tests in step; neither substitutes for the other.
# ---------------------------------------------------------------------------

def _load_regen():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "regenerate_locks", ADDONS / "regenerate-locks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_required_pins_table_covers_every_addon():
    """Every add-on must declare which packages define it.

    An add-on missing from REQUIRED_PINS gets NO backend guard at all, silently.
    A new add-on should fail this test until someone states what it must pin.
    """
    regen = _load_regen()
    declared = set(regen.REQUIRED_PINS)
    actual = {p.name for p in ADDON_DIRS}
    assert actual <= declared, (
        f"add-on(s) with no REQUIRED_PINS entry: {sorted(actual - declared)} — "
        "add them to regenerate-locks.py or they ship unguarded"
    )
    assert declared <= actual, (
        f"REQUIRED_PINS names a non-existent add-on: {sorted(declared - actual)}"
    )


@pytest.mark.parametrize("addon", ADDON_DIRS, ids=lambda p: p.name)
def test_shipped_locks_pin_their_required_backends(addon):
    """The locks we actually ship contain the backends they promise."""
    regen = _load_regen()
    errors = regen.check_required_pins(addon)
    assert not errors, f"{addon.name}: {errors}"


def test_required_pin_guard_fires_when_a_backend_vanishes(tmp_path):
    """Negative control — the guard above must not be vacuous.

    Strip the backend out of every lock for an add-on and the guard has to
    notice. Without this, `check_required_pins` returning [] proves nothing:
    it returns [] for an add-on it has no entry for, too.
    """
    import shutil
    regen = _load_regen()
    name = "graphiti-installer"
    backend = "kuzu"

    broken = tmp_path / name
    shutil.copytree(ADDONS / name, broken)
    for version in PYTHON_VERSIONS:
        lock = broken / "locks" / f"requirements-py{version}.lock"
        if not lock.is_file():
            continue
        kept = [ln for ln in lock.read_text(encoding="utf-8").splitlines()
                if not ln.startswith(f"{backend}==")]
        lock.write_text("\n".join(kept), encoding="utf-8")

    regen.ADDONS_DIR = tmp_path  # keep the error message's relative_to() working
    errors = regen.check_required_pins(broken)
    assert len(errors) == len(PYTHON_VERSIONS), (
        f"expected one error per lock, got {len(errors)}: {errors}"
    )
    assert all(backend in e for e in errors)


def test_upstream_probe_treats_unreachable_pypi_as_unverified(monkeypatch):
    """A blocked network is NOT evidence that upstream removed a capability.

    This machine's work network fails blocked hosts as certificate errors, and
    CI can run offline. If the probe failed closed on a network error it would
    manufacture a false "upstream dropped the extra" alarm — the exact mistake
    of reporting an unreachable site as a dead one.
    """
    regen = _load_regen()

    def boom(*a, **k):
        raise OSError("simulated network failure")

    monkeypatch.setattr(regen.urllib.request, "urlopen", boom)
    assert regen.probe_upstream_extra(ADDONS / "graphiti-installer") == []


def test_upstream_probe_fails_when_the_extra_is_gone(monkeypatch):
    """Negative control for the probe: a missing extra must be reported."""
    import io
    import json as _json
    regen = _load_regen()

    class FakeResponse(io.StringIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(url, timeout=None):
        # graphiti-core, but with every backend extra withdrawn
        return FakeResponse(_json.dumps(
            {"info": {"provides_extra": ["anthropic", "dev", "neo4j-opensearch"]}}))

    monkeypatch.setattr(regen.urllib.request, "urlopen", fake_urlopen)
    errors = regen.probe_upstream_extra(ADDONS / "graphiti-installer")
    assert len(errors) == 1, errors
    assert "kuzu" in errors[0] and "NO LONGER" in errors[0]


def test_the_upstream_probe_is_actually_wired_into_ci():
    """No-listener assertion: a guard nobody calls is decoration.

    An adversarial review caught exactly this — `probe_upstream_extra` existed,
    was tested, and was described in requirements.txt as enforced, while nothing
    in CI ever invoked it. The function passing its unit tests said nothing about
    whether it would ever run. This test asserts the WIRING, not the function.

    It is deliberately coarse (a substring check on the workflow file): its job
    is to fail loudly if someone deletes or renames the step, not to validate
    YAML semantics. Pair with test_probe_upstream_flag_exists below — the step
    is worthless if the flag it passes has been removed.
    """
    workflow = (PKG / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    assert "regenerate-locks.py --check --probe-upstream" in workflow, (
        "the live upstream backend probe is not invoked anywhere in CI — either "
        "restore the `addon-manifests` step that runs it, or withdraw the "
        "enforcement claims in graphiti-installer/requirements.txt and in this file"
    )


def test_probe_upstream_flag_exists_and_is_off_by_default():
    """The flag CI passes must exist, and must not make the default path networked.

    `--check` is documented as an offline verification and is what a maintainer
    reaches for first; silently adding a live PyPI call to it would make the
    common path fail on a plane or behind a proxy.
    """
    import subprocess
    import sys
    r = subprocess.run(
        [sys.executable, str(ADDONS / "regenerate-locks.py"), "--help"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "--probe-upstream" in r.stdout, (
        f"--probe-upstream is gone but CI still passes it:\n{r.stdout}"
    )

    regen = _load_regen()
    import inspect
    src = inspect.getsource(regen.main)
    check_block = src.split("if args.check:", 1)[1].split("uv = _uv_command()", 1)[0]
    assert "args.probe_upstream" in check_block, (
        "--check no longer honors --probe-upstream; the CI step would be a no-op"
    )


def test_upstream_probe_reports_a_404_as_a_real_finding_not_as_unverified(monkeypatch):
    """A 404 means the server ANSWERED. That is evidence, not an outage.

    `HTTPError` subclasses `URLError` subclasses `OSError`, so one broad `except`
    files "this pinned release does not exist on PyPI" under the same excuse as
    "the network is down" — and the CI probe exits 0 on a lock nobody can
    install. Round-2 review caught this; the fail-open rule is about UNREACHABLE
    hosts, and over-applying it turns a guard into a rubber stamp.
    """
    import urllib.error
    regen = _load_regen()

    def fake_urlopen(url, timeout=None):
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

    # monkeypatch, not hand-assignment: `regen.urllib` IS the process-wide
    # urllib module (the script does `import urllib.request`), so patching it is
    # global. pytest restores it even if an assertion below raises.
    monkeypatch.setattr(regen.urllib.request, "urlopen", fake_urlopen)
    errors = regen.probe_upstream_extra(ADDONS / "graphiti-installer")

    assert len(errors) == 1, f"a 404 must be reported, got: {errors}"
    assert "DOES NOT EXIST" in errors[0] and "404" in errors[0]


@pytest.mark.parametrize("label,exc_factory", [
    ("HTTP 503", lambda url: __import__("urllib.error", fromlist=["error"])
     .HTTPError(url, 503, "Service Unavailable", {}, None)),
    ("HTTP 429", lambda url: __import__("urllib.error", fromlist=["error"])
     .HTTPError(url, 429, "Too Many Requests", {}, None)),
    ("URLError", lambda url: __import__("urllib.error", fromlist=["error"])
     .URLError("dns failure")),
    ("OSError", lambda url: OSError("cert error")),
])
def test_upstream_probe_still_fails_open_on_server_errors_and_outages(
        monkeypatch, label, exc_factory):
    """The complement: 5xx/429 and true connection failures stay UNVERIFIED.

    Without this, the 404 fix could be "corrected" into failing closed on any
    HTTPError, which would break CI every time PyPI rate-limits us. Paired with
    the 404 test above, the two pin the behavior from both sides — neither
    over- nor under-correcting can pass.
    """
    regen = _load_regen()

    def fake_urlopen(url, timeout=None):
        raise exc_factory(url)

    monkeypatch.setattr(regen.urllib.request, "urlopen", fake_urlopen)
    errors = regen.probe_upstream_extra(ADDONS / "graphiti-installer")
    assert errors == [], f"{label} must be UNVERIFIED, not a finding: {errors}"


def test_no_probe_flag_exists_so_regeneration_can_run_offline():
    """Regeneration probes PyPI by default; there must be a documented way out.

    A maintainer offline would otherwise eat a 30s timeout per add-on with no
    opt-out, and --help must say which path each flag governs — the round-2
    review found the original --help implied probing was opt-in everywhere when
    the write path always probed.
    """
    import subprocess
    import sys
    r = subprocess.run(
        [sys.executable, str(ADDONS / "regenerate-locks.py"), "--help"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "--no-probe" in r.stdout, f"no offline escape hatch documented:\n{r.stdout}"
    assert "regeneration ALWAYS probes" in r.stdout or "always probes" in r.stdout, (
        f"--help does not disclose that the write path probes unconditionally:\n{r.stdout}"
    )


# Files that a USER can end up reading — either vendored into their workspace by
# the installer (common-specs/*) or copied into an installed skill (the add-on's
# own docs). Maintainer-only files are excluded deliberately.
USER_FACING_DOCS = [
    PKG / "common-specs" / "TIER_C_ACTIVATION.md",
    PKG / "common-specs" / "ARCHITECTURE.md",
    ADDONS / "graphiti-installer" / "SKILL.md",
    ADDONS / "graphiti-installer" / "INSTALL_GRAPHITI.md",
    ADDONS / "graphiti-installer" / "requirements.txt",
]


def test_regenerate_locks_is_not_shipped_into_an_installed_skill():
    """Pins the PREMISE of the test below. If this ever stops being true, the
    caveats that test enforces become wrong and should be removed, not kept.

    The installer copies the add-on payload plus preflight.py into
    `.claude/skills/<name>/`. regenerate-locks.py lives one level up in
    recommended-addons/ and is deliberately not part of that payload — it needs
    `uv`, the network, and the sibling add-on directories to do anything.
    """
    regen = ADDONS / "regenerate-locks.py"
    assert regen.is_file(), "regenerate-locks.py moved; update these tests"
    assert regen.parent == ADDONS, (
        "regenerate-locks.py now lives inside an add-on directory, so it WOULD be "
        "copied into installed skills — the source-package caveats are now wrong"
    )


@pytest.mark.parametrize("doc", USER_FACING_DOCS, ids=lambda p: p.name)
def test_docs_that_say_regenerate_also_say_you_need_the_source_package(doc):
    """A doc that tells a user to run a tool they do not have is a dead end.

    Round-3 review found TIER_C_ACTIVATION.md telling users to run
    `python recommended-addons/regenerate-locks.py graphiti` — a path that does
    not exist in any install, in a file the installer vendors verbatim into every
    workspace. The same dead end was already present for the `mcp` and
    `falkordb` options; it was inherited, not introduced.

    This is the general form: mention the regenerator, mention the prerequisite.
    """
    text = doc.read_text(encoding="utf-8")
    if "regenerate-locks.py" not in text:
        pytest.skip(f"{doc.name} does not mention the regenerator")
    assert "source package" in text.lower(), (
        f"{doc.relative_to(PKG)} tells the reader to run regenerate-locks.py but "
        "never says it requires a clone of the source package — that script is "
        "not copied into an installed skill, so the instruction is a dead end"
    )


# ---------------------------------------------------------------------------
# Upstream-licence consistency.
#
# On 2026-08-20 the graphify add-on stated THREE different things about its
# upstream's licence: SKILL.md frontmatter said MIT, smoke_test.py printed "MIT
# license" as a verified defence-layer fact, and TIER_C_ACTIVATION.md said MIT
# while noting it had "corrected" an earlier Apache-2.0 — the correction was the
# error. The real licence, read from the repo's own LICENSE file, is Apache-2.0.
#
# A test cannot know what upstream's licence IS. It can refuse to let our own
# files disagree with each other, which is what allowed one wrong value to sit
# next to two right ones without anything noticing.
# ---------------------------------------------------------------------------

LICENCE_TOKEN = re.compile(r"\b(Apache[- ]?2\.0|MIT|BSD-3-Clause|GPL-3\.0|LGPL-3\.0|MPL-2\.0)\b")


def _normalise_licence(tok: str) -> str:
    t = tok.upper().replace(" ", "-")
    return "APACHE-2.0" if t.startswith("APACHE") else t


@pytest.mark.parametrize("addon", ADDON_DIRS, ids=lambda p: p.name)
def test_addon_states_one_upstream_licence_consistently(addon):
    """SKILL.md frontmatter and smoke_test.py must not disagree about the licence."""
    skill = addon / "SKILL.md"
    smoke = addon / "smoke_test.py"
    if not skill.is_file() or not smoke.is_file():
        pytest.skip(f"{addon.name} has no SKILL.md + smoke_test.py pair")

    # Frontmatter `license:` line — the add-on's declared upstream licence.
    m = re.search(r"^license:\s*(.+)$", skill.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        pytest.skip(f"{addon.name}/SKILL.md declares no license: field")
    declared = LICENCE_TOKEN.search(m.group(1))
    if not declared:
        pytest.skip(f"{addon.name}: license: line names no recognised licence")
    declared_norm = _normalise_licence(declared.group(1))

    # Any licence token smoke_test.py PRINTS as fact (string literals only).
    printed = {
        _normalise_licence(t)
        for line in smoke.read_text(encoding="utf-8").splitlines()
        if "license" in line.lower() and line.lstrip().startswith("print(")
        for t in LICENCE_TOKEN.findall(line)
    }
    conflicting = printed - {declared_norm}
    assert not conflicting, (
        f"{addon.name}: SKILL.md declares {declared_norm} but smoke_test.py prints "
        f"{sorted(conflicting)} as verified fact. One of them is telling users "
        f"something false — check the upstream LICENSE file, not a badge."
    )


def test_ci_has_a_weekly_schedule_with_a_valid_cron():
    """The weekly trigger must exist AND its cron must be well-formed.

    Two separate failure modes, both real here:
      - No schedule at all. Push-triggered CI only re-runs when WE change
        something, so it structurally cannot notice an upstream release being
        yanked or a backend dropping the extra its driver needs — exactly what
        the upstream probe was built to catch.
      - A malformed cron. GitHub does not reject a bad schedule loudly; the
        workflow simply never fires. This project has previously shipped an
        invalid cron across four surfaces, so "it's in the file" is not enough.

    PyYAML parses a bare `on:` key as the boolean True (the Norway problem's
    cousin) — hence the two-key lookup below, which is a YAML quirk rather than
    a bug in the workflow.
    """
    yaml = pytest.importorskip("yaml")
    wf = yaml.safe_load(
        (PKG / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8"))
    triggers = wf.get("on") or wf.get(True) or {}
    assert "schedule" in triggers, (
        "no `schedule:` trigger in test.yml — the upstream backend probe then "
        "only ever runs when someone pushes, which is not when upstream breaks"
    )
    entries = triggers["schedule"]
    assert entries and isinstance(entries, list), f"malformed schedule: {entries!r}"

    for entry in entries:
        cron = entry.get("cron", "")
        fields = cron.split()
        assert len(fields) == 5, (
            f"cron {cron!r} has {len(fields)} fields, POSIX cron takes 5 — "
            "GitHub silently never fires a malformed schedule"
        )
        minute, hour, dom, month, dow = fields
        for value, lo, hi, label in (
            (minute, 0, 59, "minute"), (hour, 0, 23, "hour"),
            (dom, 1, 31, "day-of-month"), (month, 1, 12, "month"),
            (dow, 0, 6, "day-of-week"),
        ):
            if value == "*" or not re.fullmatch(r"\d+", value):
                continue  # ranges/steps/lists are legal; only bare ints are range-checked
            assert lo <= int(value) <= hi, (
                f"cron {cron!r}: {label}={value} is outside {lo}-{hi}"
            )
