"""Shared pytest fixtures for the suite.

V36_SOURCE_COMMIT pins the pre-v4.0.0 baseline used to build a v3.6.2-shaped
vault fixture for the migration tests (PLAN-migration-v36x-to-v400 §step 2:
`git archive` does NOT extract trees via `git show <rev>:<dir>` — verified —
so this materializes the old source with `git archive | tar -x` into a
session-scoped temp dir, extracted once and reused read-only by every test
that needs a v3.6.2 vault, since the source tree itself never changes.
"""

from __future__ import annotations

import pathlib
import subprocess
import tarfile
import io

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]

# Pre-v4.0.0 baseline (v3.6.2, tagged in the plan's evidence base) — the last
# commit before the v4.0.0 train's protocol-split/overrides/tiering/refactor
# work landed. Verified reachable and VERSION==3.6.2 (00-V4 §3.0 stale-citation
# rule: re-checked live, not trusted from the design-round citation).
V36_SOURCE_COMMIT = "59541b9"


@pytest.fixture(scope="session")
def v36_source_dir(tmp_path_factory):
    """Extract the v3.6.2 source tree once per test session (read-only)."""
    dest = tmp_path_factory.mktemp("ums-v36-source")
    proc = subprocess.run(
        ["git", "archive", V36_SOURCE_COMMIT],
        cwd=str(PKG), capture_output=True, timeout=30,
    )
    assert proc.returncode == 0, (
        "git archive of the v3.6.2 baseline %s failed: %s\n"
        "In CI this usually means a shallow checkout — the migration fixture "
        "needs full git history (set fetch-depth: 0 on actions/checkout)."
        % (V36_SOURCE_COMMIT, proc.stderr.decode("utf-8", errors="replace"))
    )
    with tarfile.open(fileobj=io.BytesIO(proc.stdout)) as tf:
        tf.extractall(str(dest), filter="data")
    assert (dest / "VERSION").read_text(encoding="utf-8").strip() == "3.6.2"
    assert (dest / "general-edition" / "setup.py").exists()
    assert (dest / "general-edition" / "setup.sh").exists()
    return dest
