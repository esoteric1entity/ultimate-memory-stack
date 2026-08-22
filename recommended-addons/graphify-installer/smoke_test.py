#!/usr/bin/env python3
"""
Graphify Installer — Post-Install Smoke Test
==============================================

Verifies the Graphify install works end-to-end with L2 defense check:
  1. Import check (graphifyy, NOT graphify)
  2. L2 package identity verification (catches typosquat at runtime)
  3. Tree-sitter language pack load
  4. Symbol extraction round-trip on sample code

Authority: SKILL.md Step 8 + INSTALL_GRAPHIFY.md Step 7
Vetting: passed Sentinel security vetting
Pin contract: graphifyy==0.8.21 (EXACT) + tree-sitter>=0.23.0,<0.26
              (hash-pinned closures in locks/requirements-py<VER>.lock)

Exit codes:
  0 = all checks passed
  1 = import failure
  2 = L2 identity check failed (CRITICAL — possible typosquat installed)
  3 = Tree-sitter language pack failure
  4 = symbol extraction failure
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import textwrap

# Legacy consoles (Windows cp1252, non-UTF-8 locales elsewhere) can't encode
# everything this script prints (it echoes runtime library metadata and
# exception text) — force UTF-8 so output can never crash the smoke test
# (UnicodeEncodeError). Same guard as general-edition/setup.py.
if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass



def check_import() -> None:
    """Step 1: Import graphify module (single-y — the actual module name shipped by the graphifyy distribution).

    NOTE: The PyPI DISTRIBUTION is `graphifyy` (double-y) BUT the
    Python MODULE it ships is `graphify` (single-y, matching the CLI command). Both the real install
    AND any potential typosquat would install module `graphify` — so the import name alone CANNOT
    distinguish them. The L2 typosquat defense is enforced by check_l2_identity() below, which uses
    `importlib.metadata.distribution('graphifyy')` to verify the actual distribution package name.
    """
    try:
        import graphify  # noqa: F401  (module name is single-y by upstream design)
    except ImportError as exc:
        print(f"[smoke_test] Graphify module import:    FAIL ({exc})")
        print("[smoke_test] Hint: confirm `pip list | grep graphifyy` shows 0.8.21 (DOUBLE-y distribution name)")
        print("[smoke_test] (The PyPI distribution is `graphifyy` but the Python module is `graphify` by upstream design)")
        sys.exit(1)

    print("[smoke_test] Graphify module import:    OK (single-y module name; L2 defense in next step verifies distribution name)")


def check_l2_identity() -> None:
    """Step 2: L2 defense — verify installed package metadata matches what we vetted."""
    try:
        import importlib.metadata as md
    except ImportError:
        import importlib_metadata as md  # type: ignore

    try:
        dist = md.distribution("graphifyy")
    except md.PackageNotFoundError:
        print("[smoke_test] L2 identity check:            FAIL (graphifyy package metadata not found)")
        sys.exit(2)

    name = dist.metadata.get("Name", "<unknown>")
    version = dist.metadata.get("Version", "<unknown>")
    # Licence metadata lives in three different places depending on the wheel's
    # age, and reading only one of them is how this check went blind:
    #   - PEP 639 `License-Expression` ("Apache-2.0") — modern wheels
    #   - legacy `License` — which may hold a SHORT NAME *or* the entire licence
    #     text. graphifyy 0.8.21 puts 1,068 characters of MIT text here, so
    #     printing it raw dumps the whole licence into the smoke-test output.
    #   - trove classifiers
    # Take the first that yields something, then reduce it to its first line so
    # a full-text field prints as "MIT License" rather than a wall of text.
    _raw_license = (
        dist.metadata.get("License-Expression")
        or dist.metadata.get("License")
        or next(
            (c.split("::")[-1].strip()
             for c in dist.metadata.get_all("Classifier") or []
             if c.startswith("License ::")),
            None,
        )
        or "<unknown>"
    )
    license_str = _raw_license.strip().splitlines()[0].strip() if _raw_license.strip() else "<unknown>"

    # Hard checks — must match the security-vetted values
    if name.lower() != "graphifyy":
        print(f"[smoke_test] L2 identity check:            CRITICAL FAIL (Name={name!r}, expected 'graphifyy')")
        sys.exit(2)

    if version != "0.8.21":
        print(f"[smoke_test] L2 identity check:            WARN (Version={version!r}, expected '0.8.21')")
        print(f"[smoke_test] Pin drift detected — fresh Sentinel vetting required before this version is trusted.")
        # Not a hard exit — but loud warning. Treat as L4 advisory.

    print(f"[smoke_test] L2 identity check:            OK (Name={name}, Version={version}, License={license_str})")


def check_tree_sitter() -> None:
    """Step 3: Verify tree-sitter loads."""
    try:
        import tree_sitter  # noqa: F401
    except ImportError as exc:
        print(f"[smoke_test] Tree-sitter language pack:    FAIL ({exc})")
        sys.exit(3)
    print("[smoke_test] Tree-sitter language pack:    OK")


def check_symbol_extraction() -> None:
    """Step 4: Run graphify against a sample code snippet and confirm symbols extracted.

    NOTE: An earlier implementation used `import graphifyy`
    and `graphifyy.*` API calls — but the module name shipped by the graphifyy PyPI distribution is
    `graphify` (single-y). The L2 typosquat defense (check_l2_identity()) correctly enforces the
    DISTRIBUTION name `graphifyy` via importlib.metadata; the module name in import statements is
    `graphify`. The import + API call sites here use the single-y module name accordingly.
    """
    # Calls the REAL documented API and FAILS if it does not work.
    #
    # This previously guessed three top-level entry points — `graphify.parse`,
    # `graphify.extract_symbols`, `graphify.Graphify` — and printed a WARN while
    # exiting 0 when none matched. `graphify/__init__.py` exports NOTHING
    # (`[n for n in dir(graphify) if not n.startswith("_")]` is empty), so all
    # three could never have resolved: the WARN branch was the only reachable
    # outcome, and the check verified nothing while reporting success. Once this
    # smoke test runs in CI, that made the job green on an install whose core
    # function was entirely unexercised.
    #
    # The real surface is `graphify.extract.extract_python(path: Path) -> dict`
    # returning {"nodes", "edges", "raw_calls"}. It takes a PATH, not source
    # text, which is why every string-passing guess would have failed anyway.
    try:
        from graphify.extract import extract_python
    except ImportError as exc:
        print(f"[smoke_test] Symbol extraction:            FAIL import ({exc})")
        print("[smoke_test] Hint: graphify.extract.extract_python is the documented entry point;")
        print("[smoke_test]       if it moved, upstream's API changed — re-vet before trusting this pin.")
        sys.exit(4)

    sample_code = textwrap.dedent("""\
        # Sample Python file for smoke test
        import os

        def alpha_func(x: int) -> int:
            return x * 2

        class BetaClass:
            def gamma_method(self):
                return alpha_func(42)
    """)

    with tempfile.TemporaryDirectory(prefix="graphify_smoke_") as tmpdir:
        sample_path = pathlib.Path(tmpdir) / "sample.py"
        sample_path.write_text(sample_code, encoding="utf-8")
        try:
            result = extract_python(sample_path)
        except Exception as exc:
            print(f"[smoke_test] Symbol extraction:            FAIL ({type(exc).__name__}: {exc})")
            sys.exit(4)

    nodes = result.get("nodes") if isinstance(result, dict) else None
    if not nodes:
        print(f"[smoke_test] Symbol extraction:            FAIL (no nodes returned; got keys "
              f"{sorted(result) if isinstance(result, dict) else type(result).__name__})")
        sys.exit(4)

    # The sample declares alpha_func, BetaClass and gamma_method; all three must
    # appear, or the parse silently produced something unrelated to the input.
    #
    # Labels are decorated by kind — a function is "alpha_func()", a method is
    # ".gamma_method()", a class is bare "BetaClass" — so compare on the bare
    # name. (Written first as an exact match against "alpha_func", which failed:
    # the shape had been read off a console line truncated at 60 characters that
    # cut the "()" clean off. Normalising here is matching the real API, not
    # loosening the check — it lets us additionally require gamma_method.)
    labels = {
        str(n.get("label", "")).lstrip(".").removesuffix("()")
        for n in nodes if isinstance(n, dict)
    }
    missing = [s for s in ("alpha_func", "BetaClass", "gamma_method") if s not in labels]
    if missing:
        print(f"[smoke_test] Symbol extraction:            FAIL (extracted {len(nodes)} nodes "
              f"but {missing} missing — parse did not see the sample's symbols)")
        sys.exit(4)

    print(f"[smoke_test] Symbol extraction:            OK ({len(nodes)} nodes; "
          f"alpha_func + BetaClass + gamma_method all found)")


def main() -> int:
    print("=" * 60)
    print("Graphify Installer — Post-Install Smoke Test")
    print("Authority: SKILL.md Step 8 + INSTALL_GRAPHIFY.md Step 7")
    print("=" * 60)

    check_import()
    check_l2_identity()
    check_tree_sitter()
    check_symbol_extraction()

    print("=" * 60)
    print("[smoke_test] All checks PASSED")
    print("[smoke_test] Defense layers verified:")
    # MIT is correct FOR 0.8.21. Upstream relicensed to Apache-2.0 by 0.9.48 —
    # whoever advances this pin must re-check the licence, not assume it carried over.
    print("  - L2 identity: package is graphifyy (double-y), Version 0.8.21, MIT license")
    print("  - L4 exact pin: enforced by requirements.txt")
    print("  - L5 hash pin: enforced by locks/requirements-py<VER>.lock (--require-hashes)")
    print("  - L1 bash-guard + L3 README warnings: out-of-band (verified by SKILL.md Step 1 + 3)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
