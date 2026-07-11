"""Regression test: printed cron-entry templates must not invoke bare `python`.

Target lives outside an importable package, so it is loaded by absolute path
via importlib rather than a plain import (same pattern as test_heartbeat_compactor.py).

Run from the package root:
    python -m pytest tests/test_setup_openclaw_cron.py -q
"""

from __future__ import annotations

import importlib.util
import io
import pathlib
import re
import sys
from contextlib import redirect_stdout

PKG = pathlib.Path(__file__).resolve().parents[1]

BARE_PYTHON_RE = re.compile(r"""(^|[\s'"])python\s""")


def _load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, PKG / relpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load("core/openclaw-adapter/scripts/setup-openclaw.py", "setup_openclaw")


def _captured_cron_output(openclaw_root: pathlib.Path, wire_cron: bool = True) -> str:
    # Empty script_dir (no heartbeat_compactor.py present) so step_9 takes its
    # "not found" branch and skips the shutil.copy2 call (no .openclaw/ dir
    # exists under tmp_path) — the cron-entry print logic below is unconditional
    # on wire_cron and independent of the copy outcome.
    empty_script_dir = openclaw_root / "no_such_scripts_dir"
    buf = io.StringIO()
    with redirect_stdout(buf):
        mod.step_9_install_heartbeat_compactor(openclaw_root, empty_script_dir, wire_cron)
    return buf.getvalue()


def test_cron_entries_use_python3_not_bare_python(tmp_path):
    output = _captured_cron_output(tmp_path)
    cron_lines = [line for line in output.splitlines() if "heartbeat_compactor.py" in line and "*" in line]
    assert len(cron_lines) == 2, f"expected 2 cron entry lines, got {len(cron_lines)}: {cron_lines}"
    for line in cron_lines:
        assert "python3 .openclaw/heartbeat_compactor.py" in line
        assert not BARE_PYTHON_RE.search(line), f"cron line invokes bare python: {line!r}"


CRON_FIELD_RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]  # min hour dom month dow


def _assert_valid_cron_schedule(fields):
    """Validate 5 cron schedule fields against standard crontab(5) ranges.

    Supports the syntax these templates use: '*', '*/N', 'a', 'a-b', and
    comma-separated lists of those. Regression for the shipped '0-7,23'
    day-of-month field (dom range is 1-31, so 0 was invalid and stock
    cron rejected the pasted line).
    """
    assert len(fields) == 5, f"expected 5 cron fields, got {fields}"
    for field, (lo, hi) in zip(fields, CRON_FIELD_RANGES):
        for part in field.split(","):
            if part == "*" or re.fullmatch(r"\*/\d+", part):
                continue
            m = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
            assert m, f"unsupported cron token {part!r} in field {field!r}"
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            assert lo <= a <= b <= hi, f"cron value {part!r} outside {lo}-{hi} in field {field!r}"


def test_cron_entries_are_valid_cron_syntax(tmp_path):
    output = _captured_cron_output(tmp_path)
    cron_lines = [line for line in output.splitlines() if "heartbeat_compactor.py" in line and "*" in line]
    assert len(cron_lines) == 2
    for line in cron_lines:
        _assert_valid_cron_schedule(line.split()[:5])


def test_known_bad_dom_field_would_have_been_caught():
    # Sanity: the pre-fix schedule ('0-7,23' in the day-of-month slot) fails the validator.
    import pytest
    with pytest.raises(AssertionError):
        _assert_valid_cron_schedule("0 0,6 0-7,23 * *".split())


def test_cron_entries_known_bad_pattern_would_have_been_caught():
    # Demonstrates the assertion is sensitive: the pre-fix literal would fail it.
    known_bad_line = '*/30 8-22 * * * cd "/root" && python .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1'
    assert BARE_PYTHON_RE.search(known_bad_line), "sanity check: regex should flag the pre-fix bare-python literal"


def test_no_cron_flag_prints_no_cron_entry(tmp_path):
    output = _captured_cron_output(tmp_path, wire_cron=False)
    assert "CRON ENTRY" not in output
