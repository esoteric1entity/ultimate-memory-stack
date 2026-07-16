"""Legacy-console (cp1252) encoding regression tests.

Windows consoles default to a legacy codepage (commonly cp1252) that cannot
encode the checkmark/arrow glyphs this package's scripts print — without a
UTF-8 reconfigure guard, an install crashes mid-run with UnicodeEncodeError
(reproduced live: setup-openclaw.py died after Step 7 on the arrow in its
backup-count message; self_test.py died inside its result-print loop).

The guard (unified across all glyph-printing scripts):

    if __name__ == "__main__":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

stdout ONLY — stderr already defaults to errors="backslashreplace"
(crash-proof, codepoint-preserving); __main__-gated so importing a module
in-process (as the test suite does) never mutates process-wide streams.

Subprocess tests simulate the legacy console cross-platform by forcing
PYTHONIOENCODING=cp1252 (strict errors — exactly what a real cp1252 console
does); the guard's runtime reconfigure() overrides it, so a fixed script
survives and an unfixed one crashes. This works on CI ubuntu too, which is
why the guard is NOT gated on sys.platform — a non-UTF-8 locale anywhere
reproduces the same crash class.

The static sweep test pins the class shut for LITERAL glyphs: any repo script
that both prints and contains non-cp1252 characters must carry the guard.
Known blind spot (accepted): a pure-ASCII script printing non-cp1252 content
built at RUNTIME (exception text, library metadata) passes the sweep — the
convention is to guard those too (the addon smoke tests are examples), but
only literal glyphs are statically enforceable.

Note: test_setup_openclaw_survives_legacy_console's rc==0 assertion also
depends on setup-openclaw.py's warn-tolerant self-test handling (a fresh
install always WARNs on T5) — that tri-state behavior is pinned directly in
tests/test_openclaw_selftest_status.py; a failure HERE may be either an
encoding or a tri-state regression.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

PKG = pathlib.Path(__file__).resolve().parents[1]
SETUP_OPENCLAW = PKG / "core" / "openclaw-adapter" / "scripts" / "setup-openclaw.py"
SELF_TEST = PKG / "core" / "openclaw-adapter" / "scripts" / "self_test.py"
SETUP_PY = PKG / "general-edition" / "setup.py"


def _run_with_legacy_console(args, timeout=90):
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"  # strict errors — like a real legacy console
    env.pop("PYTHONUTF8", None)  # ensure UTF-8 mode doesn't mask the repro
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, timeout=timeout,
    )


def test_setup_openclaw_survives_legacy_console(tmp_path):
    r = _run_with_legacy_console([str(SETUP_OPENCLAW), str(tmp_path), "--compliance", "none", "--no-cron"])
    assert "UnicodeEncodeError" not in r.stderr, r.stderr
    assert r.returncode == 0, r.stdout + r.stderr
    # Sanity: it got past the Step-7/8 glyph-printing sections, not just exited early.
    assert (tmp_path / ".openclaw" / "lint" / "lint_runner.py").exists()


def test_self_test_survives_legacy_console(tmp_path):
    # Needs an installed sandbox to run against — install first (already
    # covered above; UTF-8 env here so a setup failure can't mask the target).
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    setup = subprocess.run(
        [sys.executable, str(SETUP_OPENCLAW), str(tmp_path), "--compliance", "none", "--no-cron"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=90,
    )
    assert setup.returncode == 0, setup.stdout + setup.stderr

    r = _run_with_legacy_console([str(SELF_TEST), str(tmp_path)])
    assert "UnicodeEncodeError" not in r.stderr, r.stderr
    # self_test.py's documented exit contract: 0=PASS, 2=CRITICAL, 3=WARN,
    # 4=INFO. A fresh install may legitimately WARN (T5 references files that
    # are created on first use) but must never be CRITICAL — and a bare
    # Python crash exits 1, which this assertion also rejects.
    assert r.returncode in (0, 3, 4), r.stdout + r.stderr
    assert "T1" in r.stdout  # the results table actually printed


def test_general_setup_survives_legacy_console(tmp_path):
    # Pins the guard staying UNCONDITIONAL (it was originally win32-gated,
    # which left non-UTF-8 locales elsewhere unprotected and untestable on CI).
    r = _run_with_legacy_console([str(SETUP_PY), "--working-dir", str(tmp_path), "--compliance", "none"])
    assert "UnicodeEncodeError" not in r.stderr, r.stderr
    assert r.returncode == 0, r.stdout + r.stderr


def test_every_glyph_printing_script_has_the_guard():
    """Class-pinning sweep: a repo script that prints AND contains any
    character cp1252 can't encode must carry the reconfigure guard — so this
    crash class can't silently reappear in a new or edited script. Scoped to
    git-tracked files (not a raw filesystem walk) so untracked debris sitting
    in the working tree — build artifacts, editor caches, anything not
    actually shipped — can never make this test fail for the wrong reason."""
    tracked = subprocess.run(
        ["git", "ls-files", "*.py"], cwd=str(PKG), capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    offenders = []
    for line in sorted(tracked):
        rel = pathlib.PurePosixPath(line)
        if rel.parts[0] == "tests":
            continue
        p = PKG / line
        text = p.read_text(encoding="utf-8", errors="replace")
        if "print(" not in text:
            continue
        has_non_cp1252 = False
        for ch in set(text):
            if ord(ch) > 127:
                try:
                    ch.encode("cp1252")
                except UnicodeEncodeError:
                    has_non_cp1252 = True
                    break
        if has_non_cp1252 and "reconfigure" not in text:
            offenders.append(str(rel))
    assert not offenders, (
        "scripts printing non-cp1252 glyphs without a UTF-8 reconfigure guard "
        f"(crashes on legacy Windows consoles): {offenders}"
    )
