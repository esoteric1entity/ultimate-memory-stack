"""Every arXiv citation in a tracked document must be registered in CITATIONS.md.

WHY THIS EXISTS
---------------
On 2026-08-20 one review pass found two wrong citations in shipped docs — a
misattributed author list ("Chalef et al." for a paper whose first author is
Rasmussen) and an arXiv preprint labelled "peer-reviewed" in two separate
evidence tables. In the internal planning docs the same pass found a headline
statistic wrong on five counts, including a number spliced in from a source we
had ourselves marked debunked.

Every one of those was written from memory of a paper rather than from the
paper, and then copied forward by documents that had no way to distinguish a
checked claim from an unchecked one. "Verify your citations" was already the
rule. Prose rules are invisible to the gates; this is the gate.

WHAT IT DOES AND DOES NOT PROVE
-------------------------------
It proves every cited arXiv ID has been registered with a verification date.
It does NOT prove the citation is USED correctly — that a paper's numbers are
quoted accurately, or that it supports the sentence it is attached to. Only a
human reading the paper decides that. This test makes registration mandatory
and dated, so the next reader can tell what was checked and when.

Deliberately OFFLINE: it never contacts arXiv. A test suite that needs the
network to pass is a test suite that fails on a plane and gets skipped in CI.
Verification is a human act recorded in the registry; this only enforces that
the record exists.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
REGISTRY = PKG / "common-specs" / "CITATIONS.md"

# `arXiv:2501.13956` and the `[arXiv-2501.13956]` reference-style form both appear.
ARXIV_ID = re.compile(r"arXiv[:\-]([0-9]{4}\.[0-9]{4,5})", re.IGNORECASE)

# Extensions worth scanning. Lockfiles are excluded: their sha256 hashes are
# long hex strings that can coincidentally satisfy a loose pattern, and they
# never contain prose citations.
DOC_SUFFIXES = {".md", ".py", ".sh", ".ps1", ".txt", ".yml", ".yaml"}
EXCLUDE_PARTS = {"tmp", ".git", "__pycache__", "locks", ".venv"}


def _tracked_files() -> list[pathlib.Path]:
    """Ask git for tracked files, so untracked scratch never fails the suite.

    Falls back to a filesystem walk when git is unavailable (e.g. an sdist with
    no .git). The fallback is deliberately not silent about which mode ran —
    a reader debugging a failure needs to know which set was scanned.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(PKG), "ls-files"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
        if out.returncode == 0 and out.stdout.strip():
            return [PKG / line for line in out.stdout.splitlines() if line.strip()]
    except (OSError, subprocess.SubprocessError):
        pass
    return [p for p in PKG.rglob("*") if p.is_file()]


def _scannable(p: pathlib.Path) -> bool:
    if p.suffix.lower() not in DOC_SUFFIXES:
        return False
    try:
        parts = set(p.relative_to(PKG).parts)
    except ValueError:
        return False
    if parts & EXCLUDE_PARTS:
        return False
    return p.name != "CITATIONS.md" and p.name != "test_citations.py"


def _cited_ids() -> dict[str, list[str]]:
    """Map every arXiv ID found in tracked docs -> the files citing it."""
    found: dict[str, list[str]] = {}
    for path in _tracked_files():
        if not _scannable(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # Unreadable is not clean, but a binary/oddly-encoded file cannot
            # carry a prose citation either. Skipping is correct here and is
            # NOT the "unverifiable == clean" pattern the gating lint checks
            # deliberately refuse — nothing is being asserted about this file.
            continue
        for m in ARXIV_ID.finditer(text):
            found.setdefault(m.group(1), []).append(str(path.relative_to(PKG)))
    return found


def _registered_ids() -> set[str]:
    if not REGISTRY.is_file():
        return set()
    return {m.group(1) for m in ARXIV_ID.finditer(REGISTRY.read_text(encoding="utf-8"))}


def test_registry_exists():
    """Premise guard: everything below passes vacuously without this file."""
    assert REGISTRY.is_file(), (
        f"{REGISTRY.relative_to(PKG)} is missing — the citation gate cannot run, "
        "and every test in this module would pass while checking nothing"
    )


def test_some_citations_are_actually_found():
    """Guard against the scanner silently matching nothing.

    If a refactor moves the docs or breaks the regex, every other test here
    would go green while scanning an empty set — the classic vacuous gate.
    """
    cited = _cited_ids()
    assert cited, (
        "no arXiv citations found in any tracked document — either the docs "
        "changed shape or ARXIV_ID no longer matches; this gate is not running"
    )


def test_every_cited_paper_is_registered():
    """The gate itself."""
    cited = _cited_ids()
    registered = _registered_ids()
    unregistered = {k: v for k, v in cited.items() if k not in registered}
    assert not unregistered, (
        "arXiv IDs cited but not registered in common-specs/CITATIONS.md:\n"
        + "\n".join(f"  arXiv:{k} — cited in {', '.join(sorted(set(v)))}"
                    for k, v in sorted(unregistered.items()))
        + "\n\nFetch it, read it, add a registry entry with a verification date, "
          "then cite it:\n"
          '  curl -s "http://export.arxiv.org/api/query?id_list=<ID>" '
          '| grep -E "<title>|<name>|<published>"'
    )


def test_registry_has_no_orphans():
    """A registered paper nobody cites is dead weight that will rot.

    Not a failure of correctness, but a registry drifting out of step with the
    docs is how a registry stops being trusted, and an untrusted registry gets
    ignored rather than fixed.
    """
    cited = set(_cited_ids())
    orphans = _registered_ids() - cited
    assert not orphans, (
        f"registered but cited nowhere: {sorted('arXiv:' + o for o in orphans)} — "
        "remove the entry, or restore the citation that used it"
    )


@pytest.mark.parametrize("field", ["**Title**", "**Authors**", "**Published**",
                                   "**Venue**", "**We cite it for**", "**Verified**"])
def test_every_registry_entry_carries_the_required_fields(field):
    """A registry row missing 'Verified' is an unchecked claim wearing a badge.

    Checked per-field so a failure names exactly what is missing, and counted
    against the number of entries so a half-filled row cannot hide behind a
    complete one.
    """
    text = REGISTRY.read_text(encoding="utf-8")
    entry_count = len(re.findall(r"^### `arXiv:", text, re.MULTILINE))
    assert entry_count, "registry has no entries"
    assert text.count(field) >= entry_count, (
        f"{field} appears {text.count(field)} time(s) but there are "
        f"{entry_count} registry entries — at least one entry is missing it"
    )


def test_peer_reviewed_is_not_claimed_without_a_venue():
    """Lock the specific overclaim that shipped.

    Two evidence tables called arXiv:2503.03704 a "peer-reviewed paper" while
    its arXiv metadata records no venue — the same standard we explicitly
    refuse to grant vendor preprints elsewhere in these specs. This makes the
    regression detectable rather than dependent on someone remembering.
    """
    offenders = []
    for path in _tracked_files():
        if not _scannable(path) or path.suffix.lower() != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if not ARXIV_ID.search(line):
                continue
            # Evaluate a small WINDOW, not one line. Markdown prose wraps, so a
            # claim and the sentence correcting it routinely land on different
            # lines — this check first failed on the changelog entry describing
            # the very overclaim it exists to prevent. The window stays tight (2
            # following lines): the real target is an evidence-table row, which
            # is always a single line, so widening it further would only add
            # ways to be let off.
            low = " ".join(lines[i - 1:i + 2]).lower()
            if "peer-reviewed" not in low and "peer reviewed" not in low:
                continue
            # A line is FINE if it makes the preprint distinction rather than
            # asserting peer review. Negations are matched loosely because real
            # prose puts words in between ("we do NOT CLAIM peer review",
            # "NOT CLAIMED AS peer-reviewed") — an anchored `not\s+peer` misses
            # both, which is exactly how this check first false-positived on the
            # very lines it was written to protect.
            #   NB: bounded \w\s punctuation class, never `[^.]` — that matches
            #   newlines and has destroyed a file in this repo before.
            exonerating = (
                "preprint" in low
                or re.search(r"\b(not|no|never)\b[\w\s,'\"()—–-]{0,40}peer[\s-]?review", low)
                or re.search(r"peer[\s-]?review(ed)?\b[\w\s,'\"()—–-]{0,20}\b(status|or not)\b", low)
            )
            if not exonerating:
                offenders.append(f"{path.relative_to(PKG)}:{i}")
    assert not offenders, (
        "a line citing an arXiv ID claims peer review: "
        f"{offenders}\nAn arXiv ID alone is a preprint. State the venue you "
        "have seen, or say 'arXiv preprint'."
    )
