"""Characterization + edge-case unit tests for general-edition/setup.py (ge_setup).

Covers the PURE / decision logic of the General-Edition setup script:
  - update_profile_compliance  (regex substitution on a fixture PROFILE.md)
  - update_profile_extensions  (appends extension list after the compliance line)
  - generate_hmac_secret       (non-empty urlsafe token; two calls differ)
  - detect_tier                (dict with python_version always; node/cryptography keys)
  - VALID_PRESETS / VALID_EXTENSIONS / UNAVAILABLE_PRESETS constants
  - setup_fresh refusal/guard branches (healthcare-preset refusal, invalid preset,
    invalid extension, missing common-specs) — all via pytest.raises(SystemExit)
  - verify_environment scaffold-present-but-MEMORY_INDEX-missing branch
  - change_preset refusal / invalid-preset / missing-PROFILE branches

The full file-copy install (copytree) is exercised end-to-end by the
setup_fresh real-tree/custom-preset tests below (against tmp_path working
dirs); the remaining setup_fresh tests cover its guard/refusal branches.

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


def test_unavailable_presets_excludes_healthcare_from_general():
    assert mod.UNAVAILABLE_PRESETS == {"healthcare"}
    # healthcare must NOT be a valid general-edition preset
    assert "healthcare" not in mod.VALID_PRESETS


def test_edition_is_general():
    assert mod.EDITION == "general"


def test_stack_version_loaded_from_version_file():
    # Module reads ../VERSION at import; it must be a non-empty string.
    assert isinstance(mod.STACK_VERSION, str)
    assert mod.STACK_VERSION.strip() != ""


# ===========================================================================
# build_user_overrides_body — pure template-filling function (v4.0.0)
# ===========================================================================

TEMPLATE_BODY = """\
---
schema_version: "3.0"
created_at: <YYYY-MM-DD>
---

# --- Values the installer writes at bootstrap (edit freely after) ---
# compliance: <preset>          # written here only if you chose something other than PROFILE.md's shipped default (none)
# extensions:                   # written here only if you selected any at bootstrap
#   - <ext>
"""


def test_build_body_fills_date():
    out = mod.build_user_overrides_body(TEMPLATE_BODY, "none", [])
    assert "<YYYY-MM-DD>" not in out
    assert "created_at: " in out


def test_build_body_default_preset_leaves_compliance_commented():
    out = mod.build_user_overrides_body(TEMPLATE_BODY, "none", [])
    assert "# compliance: <preset>" in out
    assert "\ncompliance: none" not in out


def test_build_body_nondefault_preset_uncomments_compliance():
    out = mod.build_user_overrides_body(TEMPLATE_BODY, "enterprise", [])
    assert "compliance: enterprise" in out
    assert "# compliance: <preset>" not in out


def test_build_body_no_extensions_leaves_placeholder_commented():
    out = mod.build_user_overrides_body(TEMPLATE_BODY, "none", [])
    assert "# extensions:" in out
    assert "\nextensions:" not in out


def test_build_body_extensions_replace_placeholder_pair():
    out = mod.build_user_overrides_body(TEMPLATE_BODY, "none", ["gdpr", "soc2"])
    assert "extensions:\n  - gdpr\n  - soc2" in out
    assert "#   - <ext>" not in out


def test_build_body_both_together_independent():
    out = mod.build_user_overrides_body(TEMPLATE_BODY, "custom", ["pci-dss"])
    assert "compliance: custom" in out
    assert "extensions:\n  - pci-dss" in out


# ===========================================================================
# create_user_overrides — create-once, never-rewrite (v4.0.0)
# ===========================================================================

def test_create_user_overrides_creates_when_absent(tmp_path):
    created = mod.create_user_overrides(tmp_path, "enterprise", ["gdpr"])
    assert created is True
    out = (tmp_path / "memory" / "user" / "USER_OVERRIDES.md").read_text(encoding="utf-8")
    assert "compliance: enterprise" in out
    assert "extensions:\n  - gdpr" in out


def test_create_user_overrides_never_touches_existing_file(tmp_path):
    overrides = tmp_path / "memory" / "user" / "USER_OVERRIDES.md"
    overrides.parent.mkdir(parents=True)
    original = "# MY CUSTOM CONTENT — must survive byte for byte\n"
    overrides.write_text(original, encoding="utf-8")
    created = mod.create_user_overrides(tmp_path, "enterprise", ["gdpr", "soc2"])
    assert created is False
    assert overrides.read_text(encoding="utf-8") == original


def test_create_user_overrides_default_preset_no_extensions_stays_minimal(tmp_path):
    mod.create_user_overrides(tmp_path, "none", [])
    out = (tmp_path / "memory" / "user" / "USER_OVERRIDES.md").read_text(encoding="utf-8")
    # Stock bootstrap choices leave both placeholders commented (no live keys).
    assert "\ncompliance: none" not in out
    assert "\nextensions:" not in out


# ===========================================================================
# upsert_override_key — replace-live / uncomment-commented / insert-fallback
# ===========================================================================

def test_upsert_replaces_live_key(tmp_path):
    p = tmp_path / "USER_OVERRIDES.md"
    p.write_text("---\nschema_version: \"3.0\"\n---\ncompliance: none\nextensions:\n  - gdpr\n", encoding="utf-8")
    mod.upsert_override_key(p, "compliance", "compliance: enterprise")
    out = p.read_text(encoding="utf-8")
    assert "compliance: enterprise" in out
    assert "extensions:\n  - gdpr" in out  # untouched


def test_upsert_uncomments_commented_key(tmp_path):
    p = tmp_path / "USER_OVERRIDES.md"
    p.write_text("---\nschema_version: \"3.0\"\n---\n# compliance: <preset>          # comment\n", encoding="utf-8")
    mod.upsert_override_key(p, "compliance", "compliance: custom")
    out = p.read_text(encoding="utf-8")
    assert out.splitlines()[-1] == "compliance: custom"


def test_upsert_inserts_inside_frontmatter_when_key_absent(tmp_path):
    # Insert right after the OPENING `---` — inside the frontmatter block,
    # where a YAML-frontmatter-only reader (protocol §1.1) will find it.
    p = tmp_path / "USER_OVERRIDES.md"
    p.write_text("---\nschema_version: \"3.0\"\n---\n# no compliance key anywhere\n", encoding="utf-8")
    mod.upsert_override_key(p, "compliance", "compliance: enterprise")
    out = p.read_text(encoding="utf-8")
    lines = out.splitlines()
    assert lines[0] == "---"
    assert lines[1] == "compliance: enterprise"
    assert lines[2] == 'schema_version: "3.0"'
    assert lines[3] == "---"
    assert "# no compliance key anywhere" in out


# ===========================================================================
# archive_edited_profile — migration-notice archival (v4.0.0)
# ===========================================================================

def test_archive_edited_profile_copies_and_preserves_content(tmp_path, capsys):
    installed = tmp_path / "PROFILE.md"
    installed.write_text("compliance: none\n# USER HAND-EDIT\n", encoding="utf-8")
    archive_path = mod.archive_edited_profile(tmp_path, installed)
    assert archive_path.exists()
    assert archive_path.read_text(encoding="utf-8") == "compliance: none\n# USER HAND-EDIT\n"
    assert archive_path.parent == tmp_path / "memory" / "archive"
    out = capsys.readouterr().out
    assert "USER_OVERRIDES.md" in out


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


def test_setup_fresh_refuses_unavailable_extension(tmp_path):
    # An unavailable value requested as an extension also triggers refusal.
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "none", ["healthcare"], _args())
    assert exc.value.code == 1


def test_setup_fresh_refusal_message_names_the_alternative(tmp_path, capsys):
    with pytest.raises(SystemExit):
        mod.setup_fresh(tmp_path, "healthcare", [], _args())
    out = capsys.readouterr().out
    assert "reserved preset value" in out
    assert "enterprise" in out


def test_setup_fresh_invalid_preset_exits_1(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "bogus", [], _args())
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "Invalid preset" in out


def test_setup_fresh_custom_without_override_exits_1(tmp_path, capsys, monkeypatch):
    # 'custom' is a valid preset but requires the USER-AUTHORED
    # overrides/compliance.override.md (SCHEMA_compliance_profile §4.4).
    # Point SCRIPT_DIR at an empty tmp dir so the override file is absent.
    monkeypatch.setattr(mod, "SCRIPT_DIR", tmp_path)
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "custom", [], _args())
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "custom" in out and "override" in out.lower()


def test_setup_fresh_custom_on_stock_tree_is_refused(tmp_path, capsys):
    # The complexity-floor gate must hold against the REAL shipped tree:
    # compliance.override.md is user-authored and does NOT ship, so `custom`
    # with zero user configuration is refused (the documented footgun guard).
    # Guards against re-introducing the misdiagnosed "fix" that pointed the
    # gate at the always-shipped compliance-presets.override.md spec file,
    # which would make bare `--compliance=custom` silently pass.
    with pytest.raises(SystemExit) as exc:
        mod.setup_fresh(tmp_path, "custom", [], _args())
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "compliance.override.md" in out
    assert not (tmp_path / ".deployment-info").exists()


def test_setup_fresh_custom_with_user_override_passes_gate(tmp_path, capsys, monkeypatch):
    # With the user-authored file present, the gate opens and the install
    # completes. Fake edition dir = overrides/compliance.override.md + a
    # minimal PROFILE.md (needed by the compliance-update step downstream).
    fake_edition = tmp_path / "fake-edition"
    (fake_edition / "overrides").mkdir(parents=True)
    (fake_edition / "overrides" / "compliance.override.md").write_text(
        "---\ncompliance: custom\nbase_preset: enterprise\n---\n", encoding="utf-8"
    )
    (fake_edition / "PROFILE.md").write_text(SAMPLE_PROFILE, encoding="utf-8")
    monkeypatch.setattr(mod, "SCRIPT_DIR", fake_edition)
    working = tmp_path / "work"
    working.mkdir()
    mod.setup_fresh(working, "custom", [], _args())
    out = capsys.readouterr().out
    assert "ERROR" not in out
    assert (working / ".deployment-info").exists()
    assert "compliance_preset: custom" in (working / ".deployment-info").read_text()


def test_setup_fresh_deployment_info_extensions_none_when_empty(tmp_path):
    mod.setup_fresh(tmp_path, "none", [], _args())
    text = (tmp_path / ".deployment-info").read_text(encoding="utf-8")
    assert "extensions: none\n" in text


def test_setup_fresh_deployment_info_extensions_comma_string_format(tmp_path):
    # Regression: this used to emit Python list-repr ("['gdpr', 'soc2']"),
    # diverging from setup.sh's shell-parseable comma-string format
    # ("gdpr,soc2"). Both installers must now write the identical shape.
    mod.setup_fresh(tmp_path, "enterprise", ["gdpr", "soc2"], _args())
    text = (tmp_path / ".deployment-info").read_text(encoding="utf-8")
    assert "extensions: gdpr,soc2\n" in text
    assert "[" not in text and "]" not in text


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
    # healthcare is both an unavailable preset AND not in VALID_PRESETS. The
    # unavailable-preset refusal branch must fire first, producing the
    # unavailable-preset message (not the generic "Invalid preset" message).
    with pytest.raises(SystemExit):
        mod.setup_fresh(tmp_path, "healthcare", [], _args())
    out = capsys.readouterr().out
    assert "reserved preset value" in out
    assert "enterprise" in out
    assert "Invalid preset" not in out


# ===========================================================================
# change_preset — refusal / validation branches
# ===========================================================================

def test_change_preset_refuses_healthcare(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        mod.change_preset(tmp_path, "healthcare")
    assert exc.value.code == 1
    out = capsys.readouterr().out
    assert "reserved preset value" in out
    assert "enterprise" in out


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


def test_change_preset_happy_path_updates_user_overrides_not_profile(tmp_path):
    # v4.0.0: change_preset targets USER_OVERRIDES.md (create-once, then
    # upsert) — PROFILE.md is regenerable and must NOT be touched at all.
    profile_dir = tmp_path / "ultimate-memory-stack" / "general-edition"
    profile_dir.mkdir(parents=True)
    profile = profile_dir / "PROFILE.md"
    profile.write_text("compliance: none\n", encoding="utf-8")
    mod.change_preset(tmp_path, "enterprise")

    # PROFILE.md is the presence gate only — untouched by the change.
    assert profile.read_text(encoding="utf-8") == "compliance: none\n"
    assert list(profile_dir.glob("PROFILE.backup.*.md")) == []

    overrides = tmp_path / "memory" / "user" / "USER_OVERRIDES.md"
    assert "compliance: enterprise" in overrides.read_text(encoding="utf-8")
    backups = list((tmp_path / "memory" / "user").glob("USER_OVERRIDES.backup.*.md"))
    assert len(backups) == 1


def test_change_preset_creates_user_overrides_when_predates_it(tmp_path):
    # A deployment from before USER_OVERRIDES.md existed (PROFILE.md present,
    # no overrides file yet) must not crash — change_preset creates it first.
    profile_dir = tmp_path / "ultimate-memory-stack" / "general-edition"
    profile_dir.mkdir(parents=True)
    (profile_dir / "PROFILE.md").write_text("compliance: none\n", encoding="utf-8")
    assert not (tmp_path / "memory" / "user" / "USER_OVERRIDES.md").exists()
    mod.change_preset(tmp_path, "enterprise")
    overrides = tmp_path / "memory" / "user" / "USER_OVERRIDES.md"
    assert overrides.exists()
    assert "compliance: enterprise" in overrides.read_text(encoding="utf-8")


def test_change_preset_custom_refused_without_override_file(tmp_path, capsys):
    # Adversarial-round finding (2026-07-14): change_preset() had NO
    # complexity-floor check — `--change-preset=custom` silently "succeeded"
    # with no override file at all, the exact footgun the gate (§3.2a) exists
    # to prevent. setup_fresh() always enforced this; change_preset() must too.
    profile_dir = tmp_path / "ultimate-memory-stack" / "general-edition"
    profile_dir.mkdir(parents=True)
    (profile_dir / "PROFILE.md").write_text("compliance: none\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        mod.change_preset(tmp_path, "custom")
    assert exc.value.code == 1
    assert "compliance.override.md" in capsys.readouterr().out
    # Refused BEFORE creating USER_OVERRIDES.md — no stray file on the refused path.
    assert not (tmp_path / "memory" / "user" / "USER_OVERRIDES.md").exists()


def test_change_preset_custom_succeeds_with_override_file_present(tmp_path):
    profile_dir = tmp_path / "ultimate-memory-stack" / "general-edition"
    profile_dir.mkdir(parents=True)
    (profile_dir / "PROFILE.md").write_text("compliance: none\n", encoding="utf-8")
    (profile_dir / "overrides").mkdir()
    (profile_dir / "overrides" / "compliance.override.md").write_text("# user config\n", encoding="utf-8")
    mod.change_preset(tmp_path, "custom")
    overrides = tmp_path / "memory" / "user" / "USER_OVERRIDES.md"
    assert "compliance: custom" in overrides.read_text(encoding="utf-8")


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


# ===========================================================================
# setup_fresh — harness-aware next steps (Option C, UMS_PARENT)
# ===========================================================================

def test_fresh_nextsteps_suppressed_when_parented(tmp_path, capsys, monkeypatch):
    # Launched by the top-level installer (UMS_PARENT=1): the edition script must
    # NOT print its own "Next steps" block — the parent owns the harness-correct
    # summary, so a duplicate (and the old "Run: claude" assumption) is suppressed.
    monkeypatch.setenv("UMS_PARENT", "1")
    mod.setup_fresh(tmp_path, "none", [], _args())
    out = capsys.readouterr().out
    assert "Run: claude" not in out
    assert "Next steps" not in out


def test_fresh_nextsteps_neutral_when_standalone(tmp_path, capsys, monkeypatch):
    # Run standalone (no UMS_PARENT): the edition script DOES print next steps,
    # but harness-neutral — never the old Claude-Code-only "Run: claude" line.
    monkeypatch.delenv("UMS_PARENT", raising=False)
    mod.setup_fresh(tmp_path, "none", [], _args())
    out = capsys.readouterr().out
    assert "Run: claude" not in out
    assert "your agent" in out.lower()


# ===========================================================================
# ensure_gitignore — append UMS ignore block in a git repo (idempotent)
# ===========================================================================

def test_gitignore_skipped_when_not_git_repo(tmp_path):
    # No .git/ -> do nothing, create nothing.
    assert mod.ensure_gitignore(tmp_path) is False
    assert not (tmp_path / ".gitignore").exists()


def test_gitignore_appended_when_git_repo(tmp_path):
    (tmp_path / ".git").mkdir()
    assert mod.ensure_gitignore(tmp_path) is True
    gi = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "ultimate-memory-stack/" in gi
    assert ".deployment-info" in gi
    assert ".ums-manifest.json" in gi


def test_gitignore_does_not_ignore_memory(tmp_path):
    # memory/ is the user's DATA — it must never be gitignored.
    (tmp_path / ".git").mkdir()
    mod.ensure_gitignore(tmp_path)
    gi = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "memory/" not in gi


def test_gitignore_idempotent(tmp_path):
    (tmp_path / ".git").mkdir()
    assert mod.ensure_gitignore(tmp_path) is True
    first = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    # Second run is a no-op (marker already present) — no duplicate block.
    assert mod.ensure_gitignore(tmp_path) is False
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == first


def test_gitignore_preserves_existing_lines(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\n", encoding="utf-8")
    mod.ensure_gitignore(tmp_path)
    gi = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in gi
    assert "*.log" in gi
    assert "ultimate-memory-stack/" in gi
