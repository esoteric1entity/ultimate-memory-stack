"""Characterization + edge-case unit tests for general-edition/setup.py (ge_setup).

Covers the PURE / decision logic of the General-Edition setup script:
  - update_profile_compliance  (regex substitution on a fixture PROFILE.md)
  - update_profile_extensions  (appends extension list after the compliance line)
  - generate_hmac_secret       (non-empty urlsafe token; two calls differ)
  - detect_tier                (dict with python_version always; node/cryptography keys)
  - VALID_PRESETS / VALID_EXTENSIONS / BIOTECH_ONLY constants
  - setup_fresh refusal/guard branches (biotech refusal, invalid preset,
    invalid extension, missing common-specs) — all via pytest.raises(SystemExit)
  - verify_environment scaffold-present-but-MEMORY_INDEX-missing branch
  - change_preset refusal / invalid-preset / missing-PROFILE branches

The full file-copy install (copytree) is treated as integration-covered; only
its guard/refusal branches are exercised here.

Module is stdlib-only and lives outside an importable package, so it is loaded
by absolute path via importlib (NOT plain-imported).
"""

import importlib.util
import pathlib
import sys
import types

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1]


def _load(relpath, name):
    spec = importlib.util.spec_from_file_location(name, PKG / relpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load("general-edition/setup.py", "ge_setup")


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_profile(tmp_path, body):
    p = tmp_path / "PROFILE.md"
    p.write_text(body, encoding="utf-8")
    return p


def _args(**overrides):
    """Build a minimal argparse-like namespace for setup_fresh."""
    ns = types.SimpleNamespace(generate_hmac_secret=False)
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


SAMPLE_PROFILE = """\
# General-Edition Profile

```yaml
edition: general
compliance: none                    # DEFAULT — user changes at bootstrap
compliance_overridable: true
```
"""


# ===========================================================================
# Constants
# ===========================================================================

def test_valid_presets_exact():
    assert mod.VALID_PRESETS == {"none", "enterprise", "custom"}


def test_valid_extensions_exact():
    assert mod.VALID_EXTENSIONS == {"gdpr", "soc2", "pci-dss"}


def test_biotech_only_excludes_healthcare_from_general():
    assert mod.BIOTECH_ONLY == {"healthcare"}
    # healthcare must NOT be a valid general-edition preset
    assert "healthcare" not in mod.VALID_PRESETS


def test_edition_is_general():
    assert mod.EDITION == "general"


def test_stack_version_loaded_from_version_file():
    # Module reads ../VERSION at import; it must be a non-empty string.
    assert isinstance(mod.STACK_VERSION, str)
    assert mod.STACK_VERSION.strip() != ""


# ===========================================================================
# update_profile_compliance — regex substitution
# ===========================================================================

def test_update_compliance_happy_path(tmp_path):
    p = _make_profile(tmp_path, SAMPLE_PROFILE)
    mod.update_profile_compliance(p, "enterprise")
    out = p.read_text(encoding="utf-8")
    assert "compliance: enterprise" in out
    assert "compliance: none" not in out


def test_update_compliance_preserves_trailing_comment(tmp_path):
    # Regex is `^compliance: \w+` with count=1 — it matches only the word and
    # leaves the trailing inline comment intact.
    p = _make_profile(tmp_path, SAMPLE_PROFILE)
    mod.update_profile_compliance(p, "enterprise")
    out = p.read_text(encoding="utf-8")
    assert "compliance: enterprise                    # DEFAULT" in out


def test_update_compliance_only_first_occurrence(tmp_path):
    body = "compliance: none\nsomething\ncompliance: none\n"
    p = _make_profile(tmp_path, body)
    mod.update_profile_compliance(p, "enterprise")
    out = p.read_text(encoding="utf-8")
    # count=1 → only the first line is rewritten
    assert out == "compliance: enterprise\nsomething\ncompliance: none\n"


def test_update_compliance_no_match_is_noop(tmp_path):
    body = "# no compliance field here\nedition: general\n"
    p = _make_profile(tmp_path, body)
    mod.update_profile_compliance(p, "enterprise")
    assert p.read_text(encoding="utf-8") == body


def test_update_compliance_anchored_at_line_start(tmp_path):
    # An indented occurrence (not at line start) must NOT be substituted
    # because the regex uses ^ in MULTILINE mode.
    body = "  compliance: none\ncompliance: none\n"
    p = _make_profile(tmp_path, body)
    mod.update_profile_compliance(p, "custom")
    out = p.read_text(encoding="utf-8")
    # The indented line is untouched; the first line-anchored one is changed.
    assert out == "  compliance: none\ncompliance: custom\n"


def test_update_compliance_empty_file_noop(tmp_path):
    p = _make_profile(tmp_path, "")
    mod.update_profile_compliance(p, "enterprise")
    assert p.read_text(encoding="utf-8") == ""


# ===========================================================================
# update_profile_extensions — append block after compliance line
# ===========================================================================

def test_update_extensions_empty_list_noop(tmp_path):
    p = _make_profile(tmp_path, SAMPLE_PROFILE)
    before = p.read_text(encoding="utf-8")
    mod.update_profile_extensions(p, [])
    assert p.read_text(encoding="utf-8") == before


def test_update_extensions_inserts_block_after_compliance(tmp_path):
    body = "compliance: none\ncompliance_overridable: true\n"
    p = _make_profile(tmp_path, body)
    mod.update_profile_extensions(p, ["gdpr", "soc2"])
    out = p.read_text(encoding="utf-8")
    expected = (
        "compliance: none\n"
        "extensions:\n"
        "  - gdpr\n"
        "  - soc2\n"
        "compliance_overridable: true\n"
    )
    assert out == expected


def test_update_extensions_single(tmp_path):
    body = "compliance: enterprise\n"
    p = _make_profile(tmp_path, body)
    mod.update_profile_extensions(p, ["pci-dss"])
    out = p.read_text(encoding="utf-8")
    assert out == "compliance: enterprise\nextensions:\n  - pci-dss\n"


def test_update_extensions_no_compliance_line_noop(tmp_path):
    body = "edition: general\nschema_version: 3.0\n"
    p = _make_profile(tmp_path, body)
    mod.update_profile_extensions(p, ["gdpr"])
    # No `^compliance: \w+` to anchor on → substitution is a no-op.
    assert p.read_text(encoding="utf-8") == body


def test_update_extensions_then_compliance_independent(tmp_path):
    # Order used by setup_fresh: compliance first, then extensions.
    body = "compliance: none\n"
    p = _make_profile(tmp_path, body)
    mod.update_profile_compliance(p, "enterprise")
    mod.update_profile_extensions(p, ["gdpr"])
    out = p.read_text(encoding="utf-8")
    assert out == "compliance: enterprise\nextensions:\n  - gdpr\n"


# ===========================================================================
# generate_hmac_secret
# ===========================================================================

def test_hmac_secret_non_empty_string():
    s = mod.generate_hmac_secret()
    assert isinstance(s, str)
    assert len(s) > 0


def test_hmac_secret_two_calls_differ():
    a = mod.generate_hmac_secret()
    b = mod.generate_hmac_secret()
    assert a != b


def test_hmac_secret_is_urlsafe():
    # token_urlsafe → base64-url alphabet only (A-Za-z0-9-_)
    s = mod.generate_hmac_secret()
    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    )
    assert set(s) <= allowed


def test_hmac_secret_has_reasonable_entropy_length():
    # token_urlsafe(32) yields ~43 chars of base64url.
    s = mod.generate_hmac_secret()
    assert len(s) >= 32


# ===========================================================================
# detect_tier
# ===========================================================================

def test_detect_tier_returns_dict_with_required_keys():
    t = mod.detect_tier()
    assert isinstance(t, dict)
    assert "python_version" in t
    assert "node" in t
    assert "cryptography" in t


def test_detect_tier_python_version_matches_running_interpreter():
    t = mod.detect_tier()
    expected = f"{sys.version_info.major}.{sys.version_info.minor}"
    assert t["python_version"] == expected


def test_detect_tier_node_is_falsey_or_version_string():
    t = mod.detect_tier()
    node = t["node"]
    # Either False (not installed) or a non-empty version string.
    assert node is False or (isinstance(node, str) and node != "")


def test_detect_tier_cryptography_is_falsey_or_version_string():
    t = mod.detect_tier()
    cr = t["cryptography"]
    assert cr is False or (isinstance(cr, str) and cr != "")


def test_detect_tier_node_falls_back_when_node_missing(monkeypatch):
    # If `node` binary is absent, subprocess.run raises FileNotFoundError which
    # the module swallows, leaving node=False.
    def _raise(*a, **k):
        raise FileNotFoundError("node not found")

    monkeypatch.setattr(mod.subprocess, "run", _raise)
    t = mod.detect_tier()
    assert t["node"] is False


# ===========================================================================
# verify_environment — branches
# ===========================================================================

def test_verify_no_memory_dir_exits_1(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        mod.verify_environment(tmp_path)
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "No memory/ directory found" in out


def test_verify_scaffold_present_index_missing_returns_none(tmp_path, capsys):
    # memory/ exists but MEMORY_INDEX.md does not → informational return (no exit)
    (tmp_path / "memory").mkdir()
    result = mod.verify_environment(tmp_path)
    assert result is None
    out = capsys.readouterr().out
    assert "Setup scaffold present" in out
    assert "Activation wizard has not run yet" in out


def test_verify_full_scaffold_preset_none(tmp_path, capsys):
    mem = tmp_path / "memory"
    (mem / "sessions").mkdir(parents=True)
    (mem / "quarantine").mkdir(parents=True)
    (mem / "MEMORY_INDEX.md").write_text("idx", encoding="utf-8")
    (mem / "sessions" / "session_state.md").write_text("s", encoding="utf-8")
    # preset=none, no audit log present → "Not initialized (this is OK ...)"
    result = mod.verify_environment(tmp_path, "none")
    assert result is None
    out = capsys.readouterr().out
    assert "MEMORY_INDEX.md" in out
    assert "Not initialized (this is OK for 'none')" in out


def test_verify_preset_enterprise_reports_audit_presence(tmp_path, capsys):
    mem = tmp_path / "memory"
    (mem / "sessions").mkdir(parents=True)
    (mem / "quarantine").mkdir(parents=True)
    (mem / "security").mkdir(parents=True)
    (mem / "MEMORY_INDEX.md").write_text("idx", encoding="utf-8")
    (mem / "security" / "audit_log.jsonl").write_text("", encoding="utf-8")
    mod.verify_environment(tmp_path, "enterprise")
    out = capsys.readouterr().out
    assert "preset=enterprise" in out


# ===========================================================================
# setup_fresh — guard / refusal branches (no copytree reached)
# ===========================================================================

def test_setup_fresh_refuses_healthcare_preset(tmp_path):
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "healthcare", [], _args())
    assert exc.value.code == 1


def test_setup_fresh_refuses_biotech_only_extension(tmp_path):
    # A biotech-only value requested as an extension also triggers refusal.
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "none", ["healthcare"], _args())
    assert exc.value.code == 1


def test_setup_fresh_refusal_message_points_to_biotech(tmp_path, capsys):
    with pytest.raises(SystemExit):
        mod.setup_fresh(tmp_path, "healthcare", [], _args())
    out = capsys.readouterr().out
    assert "biotech-edition" in out


def test_setup_fresh_invalid_preset_exits_1(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "bogus", [], _args())
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Invalid preset" in out


def test_setup_fresh_custom_without_override_exits_1(tmp_path, capsys, monkeypatch):
    # 'custom' is a valid preset but requires overrides/compliance.override.md.
    # Point SCRIPT_DIR at an empty tmp dir so the override file is absent.
    monkeypatch.setattr(mod, "SCRIPT_DIR", tmp_path)
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "custom", [], _args())
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "custom" in out and "override" in out.lower()


def test_setup_fresh_invalid_extension_exits_1(tmp_path, capsys):
    # 'enterprise' is a valid preset; an unknown extension must be rejected.
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "enterprise", ["not-a-real-ext"], _args())
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Invalid extension" in out


def test_setup_fresh_missing_common_specs_exits_1(tmp_path, capsys, monkeypatch):
    # Valid preset + valid extensions, but common-specs/ absent → preflight exit.
    monkeypatch.setattr(mod, "COMMON_SPECS_DIR", tmp_path / "does-not-exist")
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "enterprise", ["gdpr"], _args())
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "common-specs" in out


def test_setup_fresh_refusal_precedes_preset_validation(tmp_path, capsys):
    # healthcare is both biotech-only AND not in VALID_PRESETS. The biotech
    # refusal branch must fire first, producing the biotech message (not the
    # generic "Invalid preset" message).
    with pytest.raises(SystemExit):
        mod.setup_fresh(tmp_path, "healthcare", [], _args())
    out = capsys.readouterr().out
    assert "biotech-edition" in out
    assert "Invalid preset" not in out


# ===========================================================================
# change_preset — refusal / validation branches
# ===========================================================================

def test_change_preset_refuses_healthcare(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        mod.change_preset(tmp_path, "healthcare")
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "biotech-edition" in out


def test_change_preset_invalid_exits_1(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        mod.change_preset(tmp_path, "nonsense")
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Invalid preset" in out


def test_change_preset_missing_profile_exits_1(tmp_path, capsys):
    # Valid preset, but the expected PROFILE.md path does not exist.
    with pytest.raises(SystemExit) as exc:
        mod.change_preset(tmp_path, "enterprise")
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "PROFILE.md not found" in out


def test_change_preset_happy_path_updates_profile(tmp_path):
    # Build the exact scaffold change_preset expects, then verify it rewrites
    # the compliance line (and writes a backup copy alongside it).
    profile_dir = tmp_path / "ultimate-memory-stack" / "general-edition"
    profile_dir.mkdir(parents=True)
    profile = profile_dir / "PROFILE.md"
    profile.write_text("compliance: none\n", encoding="utf-8")
    mod.change_preset(tmp_path, "enterprise")
    assert profile.read_text(encoding="utf-8") == "compliance: enterprise\n"
    backups = list(profile_dir.glob("PROFILE.backup.*.md"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "compliance: none\n"


# ===========================================================================
# log_audit_event — silent-skip + append behavior
# ===========================================================================

def test_log_audit_event_skips_when_no_security_dir(tmp_path):
    # No memory/security/ → silent no-op, no file created.
    mod.log_audit_event(tmp_path, action="initialize", summary="x")
    assert not (tmp_path / "memory" / "security" / "audit_log.jsonl").exists()


def test_log_audit_event_appends_compact_json(tmp_path):
    import json
    sec = tmp_path / "memory" / "security"
    sec.mkdir(parents=True)
    (sec / "audit_log.jsonl").write_text("", encoding="utf-8")
    mod.log_audit_event(tmp_path, action="preset-change", summary="changed to enterprise")
    lines = (sec / "audit_log.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["action"] == "preset-change"
    assert rec["entry_summary"] == "changed to enterprise"
    assert rec["outcome"] == "success"
    assert rec["entry_id"] == "<system>"
    # ts must be ISO-8601 UTC with Z suffix, no microseconds.
    assert rec["ts"].endswith("Z")
    assert "." not in rec["ts"]
    # Compact JSON: no ", " separators.
    assert ", " not in lines[0]
