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
| `test_lint_runner.py` | `core/openclaw-adapter/scripts/lint_runner.py` | harness detection; entry/reference parsing; the 5-element **doc-completeness** check (both `### Purpose` heading and `**Purpose:**` bold-label forms — the regression guard for the matcher fix); broken-reference, orphan, promotion-candidate checks; `LintFinding` serialization |
| `test_heartbeat_compactor.py` | `core/openclaw-adapter/scripts/heartbeat_compactor.py` | 3-deep heartbeat rotation + archive create/append; size-cap boundary; the heartbeat-header regex; doc-completeness matcher; `find_openclaw_root` resolution priority + its `SystemExit` paths |
| `test_ge_setup.py` | `general-edition/setup.py` | preset/extension constants; `update_profile_*` regex edits; HMAC-secret generation; tier detection; **biotech/healthcare refusal** branches (`SystemExit`); the `verify_environment` wizard-not-run branch |
| `test_review_quarantined.py` | `core/audit-quarantine-skill/scripts/review_quarantined.py` | timestamp format; frontmatter parsing; entry categorization; quarantine-log reading; quarantine entry discovery; append-JSONL helpers |
| `test_setup_sh_nextsteps.py` | `general-edition/setup.sh` | harness-aware "Next steps" block: suppressed under `UMS_PARENT=1`, harness-neutral wording when standalone; subprocess bash test, skip-aware |
| `test_skill_install_guard.py` | `skills/install-ultimate-memory-stack/SKILL.md` | Step-0 unsafe-location guard: refuses `$HOME`/system dirs, canonicalizes via `pwd -P` to catch symlink escapes; structural + behavioral checks, skip-aware |

Pure orchestration (`main`, argparse wiring, the file-copy install steps,
interactive review loops) is intentionally left to the end-to-end install runs
and `verify.sh`, not duplicated here.
