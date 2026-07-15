# Unit tests — Ultimate Memory Stack

Pytest unit suite for the package's logic modules. These complement `verify.sh`
(which validates an *install* — scaffold, registration, manifest); this suite
exercises the **code** in isolation.

## Run

```bash
# from the package root, with pytest available (pip install pytest)
python -m pytest tests/ -q

# bare invocation also works (pytest.ini scopes discovery to tests/,
# so it doesn't collide with the recommended-addons/*/smoke_test.py scripts)
pytest -q
```

No package install or network needed — each test file loads its target module
by absolute path (the modules are stdlib-only and live outside an importable
package), and all fixtures use pytest's `tmp_path`.

## Coverage

| Test file | Module under test | What it covers |
|---|---|---|
| `test_lint_runner.py` | `core/shared-tools/lint_runner.py` (moved from `core/openclaw-adapter/scripts/` in v4.0.0; a compat shim remains at the old path) | harness detection; entry/reference parsing; the 5-element **doc-completeness** check (both `### Purpose` heading and `**Purpose:**` bold-label forms — the regression guard for the matcher fix); broken-reference, orphan, promotion-candidate checks; `LintFinding` serialization; old-path shim still executes |
| `test_heartbeat_compactor.py` | `core/openclaw-adapter/scripts/heartbeat_compactor.py` | 3-deep heartbeat rotation + archive create/append; size-cap boundary; the heartbeat-header regex; doc-completeness matcher; `find_openclaw_root` resolution priority + its `SystemExit` paths |
| `test_ge_setup.py` | `general-edition/setup.py` | preset/extension constants; `update_profile_*` regex edits; HMAC-secret generation; tier detection; **biotech/healthcare refusal** branches (`SystemExit`); the `verify_environment` wizard-not-run branch |
| `test_review_quarantined.py` | `core/audit-quarantine-skill/scripts/review_quarantined.py` | timestamp format; frontmatter parsing; entry categorization; quarantine-log reading; quarantine entry discovery; append-JSONL helpers |
| `test_setup_sh_nextsteps.py` | `general-edition/setup.sh` | harness-aware "Next steps" block: suppressed under `UMS_PARENT=1`, harness-neutral wording when standalone; subprocess bash test, skip-aware |
| `test_skill_install_guard.py` | `skills/install-ultimate-memory-stack/SKILL.md` | Step-0 unsafe-location guard: refuses `$HOME`/system dirs, canonicalizes via `pwd -P` to catch symlink escapes; structural + behavioral checks, skip-aware |
| `test_verify_manifest_crosscheck.py` | `verify.sh` `[T8]` | manifest addons vs registered skills: matches, warns on a fake addon (exit code unaffected), silent when no manifest exists, passes silently on an empty `addons` array — real subprocess installs + `verify.sh`, skip-aware |
| `test_installer_parity.py` | `general-edition/setup.sh` + `setup.py` | Bash/Python output parity: same file set, `PROFILE.md`, `USER_OVERRIDES.md` effective values, audit-log initialization, `.gitignore` block, `.deployment-info` field-for-field (inert diffs like timestamps normalized explicitly, not loosened away) — real subprocess installs, skip-aware |
| `test_console_encoding.py` | all glyph-printing scripts | legacy-console (cp1252) survival: `setup-openclaw.py` full install, `self_test.py` result loop, and `general-edition/setup.py` under forced `PYTHONIOENCODING=cp1252`, plus a static sweep pinning that every repo script printing non-cp1252 glyphs carries the UTF-8 reconfigure guard |
| `test_openclaw_selftest_status.py` | `setup-openclaw.py` + `setup-openclaw.sh` Step 10 | self-test tri-state handling (WARN/INFO are non-blocking per `self_test.py`'s exit contract): fresh-install WARN → installer exits 0, Step-11 install log written, and both doors print the identical granular `Self-test:` summary label — real subprocess installs, bash test skip-aware |

Pure orchestration (`main`, argparse wiring, the file-copy install steps,
interactive review loops) is intentionally left to the end-to-end install runs
and `verify.sh`, not duplicated here.
