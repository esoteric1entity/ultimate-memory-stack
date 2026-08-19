"""Tests for recommended-addons/preflight.py.

preflight reports what an add-on will install versus what upstream has today,
so an abandoned dependency is visible BEFORE install. It exists because `kuzu`
went cold for ten months while our manifest still presented it as the vetted
recommendation.

Every test here is OFFLINE. The tool's whole value is that it degrades
gracefully without network — a CI job that needed PyPI to test the offline path
would be testing the wrong thing, and would go red whenever PyPI hiccuped.
"""

from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
PREFLIGHT = PKG / "recommended-addons" / "preflight.py"


def _load():
    spec = importlib.util.spec_from_file_location("addon_preflight", PREFLIGHT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["addon_preflight"] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load()


def _run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(PREFLIGHT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120, cwd=cwd,
    )


def test_offline_run_succeeds_and_lists_every_addon():
    r = _run("--offline")
    assert r.returncode == 0, r.stdout + r.stderr
    for addon in ("graphify-installer", "graphiti-installer", "llmlingua-installer"):
        assert addon in r.stdout, r.stdout


def test_offline_never_reports_a_finding():
    """Being offline is not a finding — it must not look like staleness."""
    r = _run("--offline")
    assert "COLD" not in r.stdout
    assert "unknown (offline)" in r.stdout


def test_strict_offline_still_exits_zero():
    """--strict gates on staleness, which cannot be determined offline. It must
    not fail merely because the network is unavailable."""
    r = _run("--offline", "--strict")
    assert r.returncode == 0, r.stdout + r.stderr


def test_unknown_addon_name_exits_2():
    r = _run("no-such-addon", "--offline")
    assert r.returncode == 2
    assert "Available" in r.stderr


def test_single_addon_selection_by_short_name():
    r = _run("graphify", "--offline")
    assert r.returncode == 0
    assert "graphify-installer" in r.stdout
    assert "llmlingua-installer" not in r.stdout


def test_installed_sibling_layout_is_not_a_silent_noop(tmp_path):
    """The installers copy preflight.py INTO each installed skill directory,
    where requirements.txt is a SIBLING and there are no add-on subdirectories.
    Without explicit handling this layout finds zero add-ons and prints nothing
    while still exiting 0 — a silent no-op that looks like success."""
    (tmp_path / "preflight.py").write_bytes(PREFLIGHT.read_bytes())
    (tmp_path / "requirements.txt").write_text(
        "# comment\nsomepkg==1.2.3\nother>=2.0\n", encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(tmp_path / "preflight.py"), "--offline"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "somepkg" in r.stdout, f"sibling layout produced no rows:\n{r.stdout}"
    assert "other" in r.stdout


class TestParseRequirements:
    def test_skips_comments_and_commented_out_options(self, tmp_path):
        req = tmp_path / "requirements.txt"
        req.write_text(
            "# header comment\n"
            "\n"
            "realpkg==1.0.0\n"
            "# neo4j>=5.0.0,<6.0.0\n"
            "marked>=1.0; python_version >= \"3.12\"\n"
            "trailing==2.0  # inline note\n",
            encoding="utf-8",
        )
        got = {name: (spec, marker) for name, spec, marker in mod.parse_requirements(req)}
        assert set(got) == {"realpkg", "marked", "trailing"}, got
        assert "neo4j" not in got, "a commented-out optional entry is not what will install"
        assert got["realpkg"][0] == "==1.0.0"
        assert got["trailing"][0] == "==2.0", "inline comment leaked into the specifier"
        assert "python_version" in got["marked"][1]

    def test_real_manifests_parse_to_something(self):
        for addon in sorted((PKG / "recommended-addons").iterdir()):
            req = addon / "requirements.txt"
            if req.is_file():
                assert mod.parse_requirements(req), f"{addon.name} parsed to nothing"


class TestDaysSince:
    def test_none_and_garbage_are_tolerated(self):
        assert mod.days_since(None) is None
        assert mod.days_since("not-a-date") is None

    def test_naive_timestamp_is_treated_as_utc(self):
        # PyPI returns both `upload_time` (naive) and `upload_time_iso_8601`.
        # A naive value must not raise on the aware/naive subtraction.
        assert mod.days_since("2020-01-01T00:00:00") > 0

    def test_aware_timestamp_parses(self):
        assert mod.days_since("2020-01-01T00:00:00Z") > 0


def test_stale_threshold_is_documented_and_sane():
    assert 90 <= mod.STALE_DAYS <= 730, mod.STALE_DAYS
