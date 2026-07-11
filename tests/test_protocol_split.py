"""Tests for the MEMORY_PROTOCOL.md CORE/EXTENDED split (v4.0.0 eager-load fix).

Covers: CORE byte-size ceiling, EXTENDED file existence + backreference, every
EXTENDED pointer in CORE resolving to a real heading, all install entry points
carrying the EXTENDED copy step with the correct vault-root destination, and
PROFILE.md frontmatter parsing within a 40-line read limit and matching the
prose-declared values it mirrors.

Modules under test are stdlib-only and live outside an importable package, so
markdown/text files are read directly by path (no import machinery needed).
"""

import pathlib
import re

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]
CORE = PKG / "common-specs" / "MEMORY_PROTOCOL.md"
EXTENDED = PKG / "common-specs" / "MEMORY_PROTOCOL_EXTENDED.md"
PROFILE = PKG / "general-edition" / "PROFILE.md"


def _read(path):
    return path.read_text(encoding="utf-8")


# T-a: core file size ceiling ------------------------------------------------

def test_core_under_hard_ceiling():
    size = len(_read(CORE).encode("utf-8"))
    assert size <= 12000, f"CORE is {size} bytes — exceeds the 12,000-byte hard ceiling"


def test_core_reports_its_own_size_honestly():
    # Not a hardcoded golden number (would rot) — just confirms the file wasn't
    # accidentally left at its pre-split ~54,892-byte size.
    size = len(_read(CORE).encode("utf-8"))
    assert size < 20000, "CORE looks unsplit — still near the pre-split ~54.9KB size"


# T-b: extended file exists + is referenced by core --------------------------

def test_extended_file_exists_in_common_specs():
    assert EXTENDED.exists(), "MEMORY_PROTOCOL_EXTENDED.md missing from common-specs/"


def test_core_references_extended():
    core = _read(CORE)
    assert "MEMORY_PROTOCOL_EXTENDED.md" in core
    assert "memory/MEMORY_PROTOCOL_EXTENDED.md" in core


def test_extended_is_never_described_as_auto_loaded():
    extended = _read(EXTENDED)
    assert "never auto-loaded" in extended.lower() or "not auto-loaded" in extended.lower()


# T-c: every EXTENDED pointer in core resolves to a real heading -------------

POINTER_RE = re.compile(r"EXTENDED §(E\d+(?:\.\d+)?)")
# Matches "## E1. Title" or "### E3.1 Title" style headings in EXTENDED.
HEADING_RE = re.compile(r"^#{2,3}\s+(E\d+(?:\.\d+)?)[.\s]", re.MULTILINE)


def test_every_core_extended_pointer_resolves_to_a_real_heading():
    core = _read(CORE)
    extended = _read(EXTENDED)
    pointers = sorted(set(POINTER_RE.findall(core)))
    assert pointers, "expected at least one 'EXTENDED §E#' pointer in CORE"
    headings = set(HEADING_RE.findall(extended))
    missing = [p for p in pointers if p not in headings]
    assert not missing, f"CORE pointers with no matching EXTENDED heading: {missing}"


def test_extended_has_no_dangling_top_level_sections():
    # Sanity check the other direction: every E-numbered top-level heading
    # should be reachable from something (not required to be from CORE, since
    # E-subsections like E3.1 nest under E3 — just confirms the numbering is
    # contiguous, catching a copy/rename slip).
    extended = _read(EXTENDED)
    top_level = re.findall(r"^##\s+(E\d+)\.", extended, re.MULTILINE)
    assert top_level == [f"E{i}" for i in range(1, len(top_level) + 1)], (
        f"EXTENDED top-level E-sections are not contiguous: {top_level}"
    )


# T-d: installer file-lists include the extended copy ------------------------

INSTALLERS_DIRECT_LOGIC = [
    ("setup-memory-stack.sh", "MEMORY_PROTOCOL_EXTENDED.md", "memory/MEMORY_PROTOCOL_EXTENDED.md"),
    ("setup-memory-stack.ps1", "MEMORY_PROTOCOL_EXTENDED.md", "memoryDir"),
    ("general-edition/setup.sh", "MEMORY_PROTOCOL_EXTENDED.md", "memory/MEMORY_PROTOCOL_EXTENDED.md"),
    ("general-edition/setup.py", "MEMORY_PROTOCOL_EXTENDED.md", "memory_dir"),
    ("skills/install-ultimate-memory-stack/SKILL.md", "MEMORY_PROTOCOL_EXTENDED.md", "<MEMORY_DIR>/MEMORY_PROTOCOL_EXTENDED.md"),
]


@pytest.mark.parametrize("relpath,needle,dest_needle", INSTALLERS_DIRECT_LOGIC)
def test_direct_logic_installer_copies_extended(relpath, needle, dest_needle):
    text = _read(PKG / relpath)
    assert needle in text, f"{relpath} never mentions {needle}"
    assert dest_needle in text, f"{relpath} doesn't copy EXTENDED to the expected vault-root destination"


def test_setup_ps1_still_delegates_no_direct_protocol_logic():
    # general-edition/setup.ps1 delegates to setup.py; it must NOT gain
    # duplicate copy logic (edge case: a fix applied to only one direct-logic
    # script is the exact bug class this split must not repeat).
    text = _read(PKG / "general-edition" / "setup.ps1")
    assert "MEMORY_PROTOCOL" not in text
    assert ".claude" not in text.replace(".claude\\rules", "")  # no direct rules-dir writes


def test_verify_sh_has_the_three_new_checks():
    text = _read(PKG / "verify.sh")
    assert "memory/MEMORY_PROTOCOL_EXTENDED.md" in text  # (b) extended exists check
    assert "40000" in text  # (a) core size < 40,000 bytes
    assert "EXTENDED_IN_RULES" in text  # (c) no-EXTENDED-in-rules regression guard


COPY_COMMAND_RE = re.compile(
    r"\b(cp\s|Copy-Item\b|shutil\.copy)"  # the actual copy operations used in this repo
)


def test_no_extended_destination_ever_targets_claude_rules():
    # THE killer edge (plan §6.1): the extended file must never be placed
    # under .claude/rules/, which would recreate the eager-load bug at a
    # bigger size. Scan every install entry point for an actual copy
    # OPERATION (not prose) whose line mentions both EXTENDED and a
    # .claude/rules-style destination.
    candidates = [
        "setup-memory-stack.sh", "setup-memory-stack.ps1",
        "general-edition/setup.sh", "general-edition/setup.py",
        "skills/install-ultimate-memory-stack/SKILL.md",
    ]
    offenders = []
    for relpath in candidates:
        for lineno, line in enumerate(_read(PKG / relpath).splitlines(), start=1):
            if COPY_COMMAND_RE.search(line) and "EXTENDED" in line:
                if ".claude" in line and "rules" in line:
                    offenders.append(f"{relpath}:{lineno}: {line.strip()}")
    assert not offenders, "a copy operation sends EXTENDED into .claude/rules/:\n" + "\n".join(offenders)


def test_verify_sh_regression_guard_checks_claude_rules_not_memory():
    # The regression guard itself must actually scan .claude/rules/ (not some
    # other directory) for a stray EXTENDED file.
    text = _read(PKG / "verify.sh")
    guard_block = text[text.index("EXTENDED_IN_RULES") - 200 : text.index("EXTENDED_IN_RULES") + 400]
    assert ".claude/rules" in guard_block
    assert "EXTENDED" in guard_block


# T-e: PROFILE.md frontmatter parses within 40 lines and matches prose -------

def _parse_frontmatter(text):
    """Minimal stdlib-only parser for this file's specific frontmatter shape:
    flat top-level scalars, plus one key (`override_file_map`) holding a block
    sequence of 2-key mappings. Not a general YAML parser — CI only installs
    pytest (see .github/workflows/test.yml), so this avoids a PyYAML dependency
    the rest of the suite deliberately doesn't have (see tests/README.md).
    """
    result = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\w+):\s*(.*)$", line)
        assert m, f"unparseable frontmatter line: {line!r}"
        key, value = m.group(1), m.group(2).strip()
        if value:
            result[key] = value.strip('"')
            i += 1
        else:
            # Block sequence of mappings under this key.
            items = []
            i += 1
            current = None
            while i < len(lines) and (lines[i].startswith("  ") or not lines[i].strip()):
                item_line = lines[i]
                seq_m = re.match(r"^  - (\w+):\s*(.*)$", item_line)
                sub_m = re.match(r"^    (\w+):\s*(.*)$", item_line)
                if seq_m:
                    if current is not None:
                        items.append(current)
                    current = {seq_m.group(1): seq_m.group(2).strip().strip('"')}
                elif sub_m and current is not None:
                    current[sub_m.group(1)] = sub_m.group(2).strip().strip('"')
                i += 1
            if current is not None:
                items.append(current)
            result[key] = items
    return result


def test_profile_frontmatter_parses_within_first_40_lines():
    lines = _read(PROFILE).splitlines()[:40]
    text = "\n".join(lines)
    assert text.startswith("---"), "PROFILE.md must open with YAML frontmatter"
    end = text.index("---", 3)
    frontmatter = _parse_frontmatter(text[3:end])
    assert isinstance(frontmatter, dict)
    for key in ("edition", "compliance", "audit_log", "quarantine_ux",
                "crypto_signatures_scheme", "pattern_key_threshold", "override_file_map"):
        assert key in frontmatter, f"PROFILE.md frontmatter missing '{key}'"


def test_profile_frontmatter_matches_prose_body_values():
    full_text = _read(PROFILE)
    fm_end = full_text.index("---", 3)
    frontmatter = _parse_frontmatter(full_text[3:fm_end])
    body = full_text[fm_end:]

    assert frontmatter["edition"] == "general"
    assert re.search(r"^edition:\s*general\s*$", body, re.MULTILINE)

    assert frontmatter["compliance"] == "none"
    assert re.search(r"^compliance:\s*none\b", body, re.MULTILINE)

    assert frontmatter["audit_log"] == "opt-in"
    assert re.search(r"^audit_log:\s*opt-in\b", body, re.MULTILINE)

    assert frontmatter["quarantine_ux"] == "toast"
    assert re.search(r"^quarantine_ux:\s*toast\b", body, re.MULTILINE)

    assert frontmatter["crypto_signatures_scheme"] == "hmac-sha256"
    assert '"hmac-sha256"' in body

    assert frontmatter["pattern_key_threshold"] == "5"
    assert re.search(r"^pattern_key_threshold:\s*5\b", body, re.MULTILINE)

    override_files = {entry["override_file"] for entry in frontmatter["override_file_map"]}
    assert len(override_files) == 3
    for override_file in override_files:
        assert override_file in body, f"frontmatter override_file_map entry not in body table: {override_file}"


def test_core_instructs_a_limited_read_for_profile():
    core = _read(CORE)
    assert "limit: 40" in core or "first ~40 lines" in core
