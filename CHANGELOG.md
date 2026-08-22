# Changelog — Ultimate Memory Stack

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **`RELEASE.md` — a release checklist where every line is paid for.** Each item cites the specific
  defect this project shipped that put it there: manifests nothing ever executed, ~20 capability
  claims with no implementing code, a guard documented as CI-gated that CI never invoked, a printed
  verify command bash could not run, a dependency licence stated wrong in three places where the
  "correction" was the error. Items with no such history were deliberately left out. Includes the
  R2 external-user gate, marked honestly as **not started**.
- **A weekly CI schedule (`cron: 17 6 * * 0`).** The failures most likely to break this package do
  not happen when we push — a pinned release gets yanked, a backend stops declaring the extra its
  driver needs — and push-triggered CI structurally cannot see any of it. A test validates the cron
  is well-formed, because GitHub never fires a malformed schedule and says nothing, and this project
  has previously shipped an invalid cron across four surfaces.
- **A citation registry with a gate behind it — `common-specs/CITATIONS.md` + `tests/test_citations.py`.**
  Every arXiv ID cited in a tracked document must have a registry entry recording its real title,
  authors, publication date, venue status, what we cite it for, and when a human last checked it.
  The test fails on an unregistered citation, on a registry entry missing any required field, on a
  registry entry nobody cites any more, and on any line that claims peer review for a paper
  identified only by an arXiv ID. It is deliberately offline — a suite that needs the network to
  pass is a suite that gets skipped. It cannot prove a citation is *used* correctly; it makes
  registration mandatory and dated, which is the checkable part.

### Fixed
- **Four stale siblings the earlier licence revert missed, plus CI job timeouts.** Reverting the
  wrong Graphify licence across four documents did not touch everything that repeated it:
  `graphify-installer/SKILL.md` Step 7 still told the reader to expect a flat `License: MIT` and to
  treat an unexpected `Author:` as a red flag (that field is **empty** on 0.8.21, so the check was
  unusable), its pre-install banner stated the licence without the per-version qualifier, and
  `ARCHITECTURE.md` §11.5 still carried `49.6k stars, MIT license` — a star count stale by more than
  half. Worst of all, `tests/test_addon_locks.py`'s own rationale comment still asserted Apache-2.0
  was "the real licence", so the test guarding the corrected files argued for re-introducing the
  defect. All corrected, with the per-version rule stated at each site.
  Separately: `addon-manifests` and `addon-smoke` now carry `timeout-minutes` (15 / 20). Both talk
  to PyPI, and GitHub's default job timeout is **six hours** — one hung index call would hold a
  runner for an afternoon. And the `SecurityLingua` call site now matches what `CITATIONS.md`
  prescribes: a successor *line of work* sharing authors, not a Microsoft-designated successor.
- **The Graphify smoke test's core check could never pass, and CI was about to trust it.** Symbol
  extraction guessed three top-level entry points (`graphify.parse`, `graphify.extract_symbols`,
  `graphify.Graphify`) and printed WARN while exiting **0** when none matched.
  `graphify/__init__.py` exports nothing at all, so none could ever resolve — the WARN branch was
  the only reachable outcome, and `INSTALL_GRAPHIFY.md` documented it as a normal possibility. It
  now calls the real API, `graphify.extract.extract_python(path)`, asserts the sample's
  `alpha_func`, `BetaClass` and `gamma_method` all come back, and **exits 4** otherwise.
- **`INSTALL_GRAPHIFY.md`'s `pip show` worked example matched none of the real output.** `Summary:`
  was a different sentence, `License:` is the full 1,068-character licence text rather than the
  token `MIT`, and **`Author:` is empty** — which made the documented red flag "Maintainer is NOT
  captainturbo / Safi Shamsi" impossible to check against anything. Replaced with the verified
  output and red flags a reader can actually evaluate.
- **Regenerated lockfiles no longer embed the regenerating machine's absolute path.**
  `regenerate-locks.py` passed absolute paths to `uv pip compile`, which writes the invoking command
  verbatim into each lock header — so a public-repo file carried a local Windows directory layout
  and username, and every regeneration from a different checkout produced a spurious header-only
  diff. Now passes repo-relative paths with `cwd` at the repo root, matching every other lock.
- **The cron gate rejected a valid schedule carrying a trailing comment**, and the date stamp on the
  new openai ceiling said 2026-08-20 — a fresh instance of the very defect the same release fixed in
  21 other places.
- 🔴 **The Graphiti add-on's shipped lock produced an install that could not be imported at all.**
  `pip install --require-hashes` succeeded (exit 0) and `import graphiti_core` then failed with
  `ModuleNotFoundError: No module named 'httpx'`. Root cause: **graphiti-core does not declare
  httpx**, but imports it directly at `graphiti_core/llm_client/client.py:23` to catch
  `httpx.HTTPStatusError` in its retry-on-5xx path — relying on getting it transitively from
  `openai`. **`openai 3.0.0` migrated from `httpx` to `httpx2`**, so it stopped arriving. Fixed by
  pinning `openai>=1.91.0,<3` and regenerating; the lock now carries `openai==2.54.0` and
  `httpx==0.28.1`, and the add-on's smoke test passes end to end including a Kuzu ingest→query
  round trip.
  A ceiling was the right fix rather than re-adding `httpx`: openai 3.x raises `httpx2` exception
  types that `except httpx.HTTPStatusError` can never match, so re-adding httpx would have fixed
  the ImportError and left the 5xx retry **silently dead** — a green import hiding a dead safety
  net. This is exactly the class v4.0.0 shipped: resolution is not installation, and installation
  is not working. It surfaced only because the new `addon-smoke` CI job was proven by running it
  before being wired up.
- **Three self-inflicted defects in this release's own new gates, found by council review.**
  (a) The cron-validity test opened with `pytest.importorskip("yaml")` while CI installs only
  pytest — so it **silently skipped on every CI run** while passing locally: the exact
  "a guard nothing invokes" failure, committed inside a guard. Rewritten to parse with a regex and
  depend on nothing. (b) The licence-consistency test only matched a licence token on the same
  physical line as `print(`, so wrapping one call across two lines silently disabled it; it now
  parses with `ast`. (c) 21 date stamps read 2026-08-20 when the work was done on 2026-08-22 —
  a long session crossed days. Stamps belonging to genuine 08-20 work were left alone.
- **Documented that Graphify's upstream relicensed mid-stream, so the licence depends on the
  version.** `graphifyy` **0.8.21 — the version this add-on pins and ships — is MIT**; 0.9.0 is MIT;
  the current 0.9.48 is **Apache-2.0**. The docs said MIT and were **right**; a check of *current*
  upstream (LICENSE file, GitHub API, PyPI `license_expression` — three sources that agreed with
  each other and all described 0.9.48) briefly "corrected" them to Apache-2.0 during this release
  and was reverted. Anyone advancing the pin must re-check the licence for the target version; it
  does not carry over. A new test refuses to let `SKILL.md` and `smoke_test.py` disagree about a
  licence, so a future drift cannot sit unnoticed in one file while the other is right.
- **`smoke_test.py`'s licence read now covers all three places the value can live.** Licence
  metadata is in PEP 639 `License-Expression` on modern wheels, in the legacy `License` field on
  older ones — where it may be a short name *or the entire licence text* — or in trove classifiers.
  Reading only one field meant the check reported a licence it had not actually established, while
  the summary line beneath it asserted one as a verified "defense layer". It now tries all three
  and prints only the first line, because graphifyy 0.8.21 stores **1,068 characters of licence
  text** in that field and was dumping the whole thing into the smoke-test output.
- **Two wrong citations in shipped documentation.** `ARCHITECTURE.md` attributed `arXiv:2501.13956`
  to "Chalef et al." — Daniel Chalef is the **last of five** authors; the first is Rasmussen. The
  same line also called it "the Graphiti paper" without noting it is titled *"Zep: A Temporal
  Knowledge Graph Architecture for Agent Memory"*, Graphiti being the open-source engine beneath
  Zep. Separately, **two** evidence tables (`SCHEMA_quarantine.md` §3 and `SCHEMA_A18`) labelled
  `arXiv:2503.03704` a "peer-reviewed paper"; its arXiv metadata records no `journal_ref` and no
  DOI, so it is a preprint — the same overclaim these specs explicitly refuse to grant vendor
  preprints two files away. The papers themselves are real and support what they are cited for;
  only the attribution and the evidence-strength labels were wrong.
- **The Windows installer printed a `verify.sh` command that bash could not run.** It emitted
  `bash C:\pkg\verify.sh C:\vault` — unusable twice over, since bash eats each backslash as an
  escape and an unquoted path splits on spaces. Now forward-slashed and quoted, and a test runs
  the printed command rather than pattern-matching it.
- **`.ums-manifest.json` was written with a UTF-8 BOM by the PowerShell door only.** `json.loads()`
  fails outright on it, so the two installers disagreed about whether a file we document as
  machine-readable actually was. It went unnoticed because the only in-repo consumer is a
  BOM-tolerant `grep -o`. Windows PowerShell 5.1 has no `utf8NoBOM`, so the manifest is now written
  via `[System.IO.File]::WriteAllText` with `UTF8Encoding($false)` — plus an explicit trailing
  newline, which `Set-Content` used to supply and `WriteAllText` does not, so the two doors do not
  disagree about whether the file ends properly.
- **A `SKILL.md` with no `name:` frontmatter aborted the PowerShell installer** with a raw
  PowerShell error instead of the one-line skip the bash door prints. The extraction dereferenced
  the `Select-String` result without checking it, which made the guard immediately below it
  unreachable dead code.
- **`TIER_C_ACTIVATION.md`'s C4 "Deactivation" section still described rotating a signing key so
  that "existing signatures become unverifiable".** There are no signatures — 4.0.1 withdrew the
  signing claims because no signing or verification code exists, and this instance survived that
  sweep. `--generate-hmac-secret` does generate a secret; nothing consumes it, so rotating it
  invalidates nothing.
- **`verify.sh` claimed `.ums-manifest.json` was "written only by the setup-memory-stack.sh
  wrapper".** Both top-level installers write it; the comment had been wrong since the PowerShell
  door gained one.

### Changed
- **The Graphiti add-on's Kuzu disclosure is now accurate, and enforced by a mechanism.** 4.0.1
  described Kuzu as "cold upstream" with an unresolved maintenance decision. Verified against
  primary sources: `kuzudb/kuzu` was **archived read-only on 2025-10-10** — the day it shipped its
  final release — after Kùzu Inc. was acquired by Apple. It is finished, not drifting. The
  position is now settled rather than deferred: **keep Kuzu, do not ceiling `graphiti-core`.**
  Users were never exposed — every documented install path uses the hash-pinned lockfiles, which
  pin `graphiti-core` and `kuzu` exactly — and the floor pin is how CVE patches reach people. The
  real exposure is at lock *regeneration*, so `regenerate-locks.py` now fails there if a lock stops
  pinning a required backend, or if the pinned `graphiti-core` release stops declaring the `kuzu`
  extra. Also corrected: FalkorDB Lite cannot be used on Windows *at all* — not merely missing
  wheels, its `setup.py` raises on any non-darwin/linux platform — and graphiti-core is healthy
  (0.29.3, 2026-07-27), with the Kuzu driver still shipping and no removal scheduled.
- **An open Windows write-crash report against Kuzu is now disclosed at every decision point.**
  graphiti-core issue #1469 (OPEN, filed 2026-05-06, last activity 2026-08-14) reports
  `add_episode` crashing the host process with an access violation inside Kuzu's C extension on
  Windows 11 at ~50 episodes; reads are unaffected. It is a single report with a faulthandler
  trace, no maintainer has responded, and we have not reproduced it — so it is documented as
  credible-not-confirmed, not as a known defect. It matters because an archived upstream cannot
  ship an engine fix, and because our smoke test could never catch it: it opens a connection and
  never writes at volume. Previously the docs said only that 0.11.3 "works" — true of installation,
  and doing far too much work as a claim about reliability.
- **Those backend guards run in CI, not just on a maintainer's machine.** The `addon-manifests` job
  now runs `regenerate-locks.py --check --probe-upstream` (one leg, one PyPI call). Without that
  step the guard existed, was unit-tested, and was described in `requirements.txt` as enforced —
  while nothing ever invoked it. `test_the_upstream_probe_is_actually_wired_into_ci` now asserts
  the wiring itself, because a passing unit test says nothing about whether a function runs.
- **The upstream probe distinguishes "unreachable" from "answered, and the answer was no".**
  `HTTPError` subclasses `URLError` subclasses `OSError`, so one broad `except` filed a genuine
  PyPI **404** — a pinned release that does not exist, from a typo'd or deleted pin — under the
  same "network unreachable, not a failure" excuse, and CI exited `0` on a lock nobody could
  install. A 404 is now a real finding; `429`/`5xx` and true connection failures remain UNVERIFIED
  and still do not fail. Paired tests pin both directions so neither over- nor under-correcting
  passes.
- **`regenerate-locks.py` gained `--no-probe`, and `--help` now says which path each flag governs.**
  Regeneration always probes PyPI — that is the moment the risk is real — while `--check` stays
  fully offline unless given `--probe-upstream`. The help text previously implied probing was
  opt-in everywhere, so an offline maintainer had no way to avoid a 30-second timeout per add-on.
- **An `anthropic` provider line was added to the Graphiti add-on's `requirements.txt`** (commented
  out, alongside the existing `mcp` and `falkordb` options). `ARCHITECTURE.md` had been pointing at
  a procedure for enabling Claude API ingestion that did not exist. It names `anthropic>=0.49.0`
  directly rather than via `graphiti-core[anthropic]`, for the same reason `kuzu` is named
  directly: an extra can be withdrawn upstream and pip will install without it, silently.
- **Every "then regenerate the locks" instruction now says you need the source package.**
  `regenerate-locks.py` is a maintainer tool and is not copied into an installed skill, so a user
  reading their vendored `TIER_C_ACTIVATION.md` — or the `SKILL.md` inside
  `.claude/skills/install-graphiti/` — was told to run a script that exists nowhere in their
  install. The dead end already applied to the `mcp` and `falkordb` options and was inherited, not
  introduced. All five places now state the prerequisite, and a test enforces the pairing for the
  four that name the script — `ARCHITECTURE.md` describes the step in prose without naming it, so
  its case skips rather than asserting.
- **`TIER_C_ACTIVATION.md` no longer tells users to run `pip install graphiti-core[kuzu]`.** That
  command is unpinned *and* uses the deprecated extra — and that second failure is silent: pip
  exits `0` and installs the package without an extra the distribution no longer provides, with no
  warning at all on pip 25.3. Once upstream removes it, the command would install graphiti-core
  with no graph backend and report success. It now points at the hash-pinned lock the installer
  uses, which names `kuzu` directly rather than through the extra.

## [4.0.1] — 2026-08-19

A correctness release. Every pip add-on now installs — two of the three manifests were unresolvable in 4.0.0 — and the machinery that let that ship undetected is closed: CI now resolves and hash-verifies every manifest, and the installers place the files their own instructions tell users to run. Lint gains a real exit-code contract so a finding can fail a build instead of being printed and ignored.

### Added
- **Lint can now fail a run.** `lint_runner.py` previously returned exit code `0` unconditionally, so no finding could ever break a build — every check was advisory by construction. A new `--fail-on {none,info,low,medium,high,critical}` (default `high`) exits `1` when a finding at or above that severity is present, printing the blocking findings to stderr. `--fail-on none` restores the previous behavior for anyone whose pipeline depends on the old exit code. `--severity` remains a *display* filter and is deliberately not allowed to narrow the gate, so `--severity critical` cannot silently switch it off. Contract: `SCHEMA_lint.md` §14.
- **Two lint checks for silent recall failure** — cases where memory goes missing without anything looking broken. `archive-pointer-dangling` (severity `high`, gates) fires when an `ARCHIVE_INDEX.md` one-liner names an entry that is not present in that category's archive file: the index promises a rotated entry is one on-demand read away and it is gone, which is the exact failure `MEMORY_PROTOCOL_EXTENDED.md` §E12.2's "loss-proof by construction" states cannot happen. It also fires — rather than skipping the category — when an archive file or cold index cannot be decoded, because for a gate "unverifiable" must not be treated as "clean". It requires a non-empty `ARCHIVE_INDEX.md`, so it cannot fire on a vault that has never rotated anything. `unreachable-memory-file` (severity `low`, advisory) fires when a file under `memory/` has content but is referenced nowhere in `MEMORY_INDEX.md` — present on disk, invisible through the index an agent actually reads; a file is reachable through any ancestor directory the index points at, so SCHEMA_A3 per-project memory banks (registered as directories) don't produce per-file noise.
- **Hash-pinned lockfiles for every add-on.** Each add-on now ships `locks/requirements-py<VER>.lock` for Python 3.10 / 3.11 / 3.12 / 3.13 — a fully-resolved, universal (all-platform), hash-pinned closure compiled from its `requirements.txt`. `requirements.txt` states what versions are *acceptable*; the lock states exactly what you *get*. Installing with `pip install --require-hashes -r <lock>` makes pip refuse any artifact whose hash is not listed, so a substituted or tampered distribution fails closed. A version pin alone never delivered "upstream moving cannot break our users" — the pinned package's own dependencies still resolved live, which is how the graphify add-on shipped uninstallable. Regenerate with `python recommended-addons/regenerate-locks.py`; offline tests fail if a manifest is edited without regenerating, and CI verifies every lock installs under `--require-hashes`.
- **`preflight.py` — dependency freshness, before you install.** Reports each dependency's shipped constraint against the latest version on PyPI and when it was published, flagging anything with no release in ~9 months. Informational by design: it never blocks an install, never edits anything, and treats being offline as "unknown" rather than as a finding. Stdlib-only. The installers copy it into each installed add-on skill so it works without the package tree. It exists because `kuzu` went cold for ten months while our own manifest still presented it as the vetted recommendation, and because `graphifyy` drifted 77 releases past our pin with nothing surfacing it.

### Fixed
- **Two of the three pip add-ons could never be installed.** `graphify` pinned `tree-sitter>=0.20.0,<0.22.0` while `graphifyy==0.8.21` requires `tree-sitter>=0.23.0` — the ceiling excluded every version the package accepts, so `pip install -r` failed with `ResolutionImpossible` on every platform and every Python version. `llmlingua` pinned `torch>=2.0.0,<2.3.0` and `transformers>=4.30.0,<4.40.0`; both ceilings were ours (llmlingua declares those dependencies unbounded), and the oldest torch publishing a cp313 wheel is 2.5.0, so the manifest had no solution on Python 3.13 either. It also listed `sentencepiece`, which llmlingua does not depend on, and omitted `accelerate`, which it does. All three manifests are now verified to resolve on Python 3.10 / 3.11 / 3.12 / 3.13.
- **The add-on manifests were never installed.** Both installers copied only `SKILL.md` into `.claude/skills/<name>/`, while the skills instruct the user to run `pip install -r <path-to-this-skill>/requirements.txt`, `pip-audit --requirement …`, and `python …/smoke_test.py` — against files that were never placed. The documented install procedure could not be followed at all, and the llmlingua skill explicitly forbids the unpinned fallback that would otherwise have worked. Both `setup-memory-stack.sh` and `setup-memory-stack.ps1` now install the complete add-on payload.
- **Root cause, addressed as a class:** nothing in the repository ever *executed* a `requirements.txt` — the CI install jobs only registered skills, and the sole repo-wide reference outside the manifests was a `print()` in a smoke test. A new `addon-manifests` CI job resolves every manifest on Python 3.10/3.11/3.12/3.13 across Linux, Windows, and macOS, and verifies every lockfile installs under `--require-hashes`, and a new test derives each skill's `<path-to-this-skill>/…` references from the SKILL.md text and asserts the installer actually places them — so adding a new reference automatically extends the check.

### Changed
- **Graphiti's graph backend carries an explicit maintenance disclosure.** Kuzu's last release was 0.11.3 on 2025-10-10, and `graphiti-core`'s own `pyproject.toml` marks its `[kuzu]` extra deprecated for removal in a future release. It remains the default because it is the only *embedded* backend covering the full support matrix — FalkorDB Lite, the maintained embedded alternative, is Python 3.12+ and publishes macOS/manylinux wheels only, with no Windows wheels — but the manifest now states the staleness and the deprecation plainly, documents the upgrade path, and flags that `graphiti-core`'s floor-only pin means a future release dropping Kuzu driver support would be adopted automatically — a disclosed, dated risk for the maintainer to resolve, not a settled position. The `kuzu` floor is raised to `>=0.11.3` to match `graphiti-core`'s own declared minimum.
- **`eager-set-over-budget` raised from severity `low` to `high`** and now gates at the default threshold. An always-loaded set over its budget is not a style nit: content past a harness's load limit is dropped without warning on the next session load, so the first symptom is an agent that has quietly forgotten something. The v4.0.0 notes below describe all 6 tiering checks as advisory `low`, which was accurate for that release and is superseded here. **Note for upgraders:** unlike `archive-pointer-dangling`, this check is independent of rotation — it measures the live always-loaded set, so it can newly fail a lint run on a vault that has never tiered anything. `--fail-on none` restores the previous advisory-only behavior.

## [4.0.0] — 2026-07-16

> **Upgrading from 3.6.x?** See [`general-edition/MIGRATION_v3.6_to_v4.0.md`](general-edition/MIGRATION_v3.6_to_v4.0.md) for the one-command, non-destructive migration (`--dry-run`-previewable).

This release changes the installed layout, not just repo content — that's the reason for a major version bump rather than another 3.6.x patch. The protocol-split fix promised for v3.6.3 ships here; v3.6.3 was folded into 4.0.0 because it ships alongside layout-changing features (the PROFILE.md/USER_OVERRIDES.md split, hot/cold tiering) that warrant a major version on their own.

### Added
- **One-command migration from v3.6.x to v4.0.0** (`setup.sh`/`setup.py --migrate-from=v3.6`, `--dry-run`-previewable, non-destructive — backs up `memory/` before any write, and a second run against an already-migrated vault is a recognized zero-write no-op). See `general-edition/MIGRATION_v3.6_to_v4.0.md`.
- **Hot/cold tiering — memory stays lean as it grows.** `sessions/`, `decisions/`, and `feedback/` now rotate their oldest entries once a file hits its `MEMORY_PROTOCOL.md` §11 line cap: the full entry moves to `memory/archive/<category>/<category>-archive.md` (nothing deleted), and a one-line pointer lands in a new per-category `ARCHIVE_INDEX.md`, so every rotated entry stays findable by ID without loading the archive file. Fresh installs get empty `ARCHIVE_INDEX.md` files at all three locations from day one. 6 new advisory lint checks (all severity LOW — `eager-set-over-budget`, `file-nearing-cap`, `archive-unindexed`, `archive-count-drift`, `archive-index-missing`, `entry-over-cap`) watch for drift; `verify.sh` checks existence post-install. Backports the maintainer's own field-proven pattern — measured over ~87 days of production use, the always-loaded index went 26.5KB → ~12KB across two tiering iterations with zero information loss — adapted to UMS's category layout, not a code transplant.

### Fixed
- **Protocol core/extended split — eager-load cost cut from ~22.3K to ~9.8K tokens on a fresh install.** `common-specs/MEMORY_PROTOCOL.md` (the file that auto-loads into `.claude/rules/` every session) shrank from 54,892 bytes (~13.7K tokens) to under 12,000 bytes (~3.0K tokens); everything else moved to the new on-demand `common-specs/MEMORY_PROTOCOL_EXTENDED.md`, installed at the vault root (`memory/MEMORY_PROTOCOL_EXTENDED.md`) — never auto-loaded, referenced by explicit section pointers (`EXTENDED §E#`) from the core file. Fulfills the core/extended split promised in the `[3.6.1]` Known Issues note above.
- **CLAUDE.md `@`-import double-load eliminated.** `INSTALL_AGENT.md` and the install skill no longer offer adding `@ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md` to a project's `CLAUDE.md` — the `.claude/rules/` copy already auto-loads every session, so the import doubled the cost for anyone who accepted it (up to ~36K tokens). Upgrading users with the old import line are warned to remove it (never auto-edited).
- **`PROFILE.md` now has a machine-readable frontmatter block** carrying the scalars the protocol's Edition Detection step needs (`edition`, `compliance`, `audit_log`, `quarantine_ux`, `crypto_signatures_scheme`, `pattern_key_threshold`, `override_file_map`) in the first ~40 lines, so the protocol can read a bounded slice instead of the full file every session.
- **Cron templates fixed** (installer output and install docs): generated cron entries now invoke `python3` explicitly, and the idle-checkpoint entry's schedule is valid cron — an out-of-range day-of-month field previously made stock cron reject the pasted line.
- **Install-skill upgrade path fixed** (skill **v1.6**) — on a re-install over an existing scaffold, the skill door's file copy nested the new package copy inside the old directory instead of refreshing it, so upgrades via that door silently kept the stale protocol files. User data is untouched; fresh installs unaffected.
- Installer hygiene: both edition installers now clear a stale `.deployment-info` completion certificate before a fresh install (parity between `setup.sh` and `setup.py`), the `.deployment-info` `extensions` field now uses the same shell-parseable comma-string format in both installers, the custom-preset refusal message now points at the pattern to follow, and a dead agent-shield-specific block was removed from the repo-root `.gitignore`.
- **PROFILE.md customization now survives upgrades.** User configuration — compliance preset, extensions, and anything else `PROFILE.md` defines — moves to `memory/user/USER_OVERRIDES.md`: created once at install time, never rewritten by the installer again. `PROFILE.md` becomes fully regenerable; a pre-existing customized copy is archived (with a migration notice) before any refresh. Replaces the previous re-install-over-an-existing-scaffold behavior, which was either a hard refusal (Bash) or a silent overwrite with no backup (Python) — both doors, plus the install skill, now behave the same way.
- **Scripts no longer crash on legacy Windows consoles.** Eight scripts (`setup-openclaw.py`, `self_test.py`, `heartbeat_compactor.py`, `review_quarantined.py`, `lint_runner.py`, and the three addon smoke tests) printed checkmark/arrow glyphs — or runtime library/exception text — that a default cp1252 console can't encode, dying mid-run with `UnicodeEncodeError`. All now carry a unified UTF-8 stdout guard (stderr is left on Python's crash-proof, codepoint-preserving default; `setup.py`'s existing guard is aligned to the same form, dropping its Windows-only gate so any non-UTF-8 locale is covered). Regression-locked by a sweep test that fails if a future script prints glyphs without the guard.
- **The OpenClaw Python installer no longer fails fresh installs over self-test warnings.** `self_test.py` distinguishes warnings (non-blocking, "adapter is usable") from critical failures, and `setup-openclaw.sh` always honored that — but `setup-openclaw.py` treated any non-zero self-test exit as install failure, so every fresh install exited with an error and skipped its own install-log step (masked until now by the console-encoding crash above). Both doors now report the same granular self-test status in their final summary too — the Bash summary previously claimed `PASSED` unconditionally, even when `self_test.py` was missing.

### Changed
- **`lint_runner.py` moved to `core/shared-tools/`** (from `core/openclaw-adapter/scripts/`) — it's cross-harness tooling documented to and used by every edition, not adapter-specific. A compat shim remains at the old path; installed vaults and existing invocations keep working unchanged.
- **`verify.sh` gains a `[T8]` manifest cross-check** — informational only, never fails the exit code. If `.ums-manifest.json` exists (Door-1 script installs write one; Door 2/4 don't), each listed addon is checked against `.claude/skills/` for a matching registered skill and a warning is printed if none is found.
- **New `tests/test_installer_parity.py` pins Bash/Python installer output parity** (file set, `PROFILE.md`, `USER_OVERRIDES.md` effective values, audit-log initialization, `.gitignore` block, `.deployment-info`) — found and fixed two more real divergences while writing it: Bash's audit-log lines were missing the `actor_session`/`entry_path`/`entry_category` fields the canonical schema requires (plus a Python-side list-repr bug in the summary text), and Python's `USER_OVERRIDES.md` was missing its trailing newline.

### Documentation
- Tightened public docs to release-granularity detail (internal record-ID citations trimmed from `INSPIRATIONS.md`, `MAPPING.md`, this file, and the addon `requirements.txt` headers; substance preserved everywhere).
- Install-guide corrections: unified door taxonomy, fixed manual-install layout contradiction, corrected the wizard-step description, documented the addon flag values, component version-labels reconciled (install skill → v1.9).

## [3.6.2] — 2026-06-16

### Changed
- **Harness-agnostic messaging.** Claude Code is now consistently presented as **one of four install doors** (and the marketplace packaging target), not a stack prerequisite. The universal prerequisites, the activation prompt (`BOOTSTRAP_PROMPT.md`), `DEPLOYMENT.md`, `README.md`, and `QUICKSTART.md` no longer assume Claude Code; harness-specific install steps now show the OpenClaw (and generic) path alongside the Claude Code one. The genuine Claude Code requirement is isolated to the marketplace/skill door.
- **Install docs consolidated.** `INSTALL.md` and `INSTALLATION_GUIDE.md` were merged into a single `INSTALL.md` (quick start + full reference); `INSTALLATION_GUIDE.md` is now a redirect stub pointing to it.

### Fixed
- **Installer no longer assumes Claude Code in its output.** The edition installers (`general-edition/setup.{sh,py,ps1}`) previously printed "Run: claude" next-steps to every user (and duplicated them on Windows). They now defer the summary to the top-level installer when launched by it, and print harness-neutral next-steps when run standalone.
- **Install-skill location guard hardened** (skill **v1.4**) — the Step 0 `$HOME`/system-dir refusal now canonicalises the working-directory path before matching, so a symlinked path can't bypass it.
- Minor: installer version banners/fallbacks aligned to the shipped `VERSION`; the doubled YAML frontmatter in the `user_profile` template example removed; the install skill auto-detects its own package directory before prompting for a source path; installing into a git repo appends a scoped `.gitignore` block for the vendored package tree.

### Documentation
- Install-doc cross-references repointed to the consolidated `INSTALL.md`; the install guide's universal prerequisites reframed so Claude Code is required only for the marketplace/skill door. Landing page refreshed (hero, tagline, Original Work & Influences, Project Status).

## [3.6.1] — 2026-06-16

### Fixed
- **macOS: installer failed at addon registration** — `setup-memory-stack.sh` used a bash-4 associative array (`declare -A`), but macOS ships bash 3.2; replaced with a portable case-statement lookup. Caught by the cross-OS install CI on launch day (the macOS leg had never run on real Apple hardware before).
- **Install skill could overwrite an existing `memory/` store** — the `/install-ultimate-memory-stack` skill (≤ v1.1) created `session_state.md` / `MEMORY_INDEX.md` / `user_profile.md` / project briefs / `feedback.md` without checking whether they already existed, so re-running it over an existing project-local memory store reset accumulated memory to empty templates. Skill **v1.2** adds an existing-store safety gate (detect → timestamped `memory.backup.<ts>/` → preserve mode; user-data files are now create-if-absent), matching the shell and agent install doors, which already preserved data. (Claude Code's native memory and `CLAUDE.md` are unaffected — UMS writes only to the project-local `memory/`.)
- **Windows installer accepted a compliance preset it then rejected** — `general-edition/setup.ps1` listed `healthcare` as a valid preset/extension while `setup.sh`/`setup.py` refuse it, so passing `-Compliance healthcare` produced a confusing downstream failure. The PS1 now rejects it up-front, matching the other installers.
- **Install skill now refuses unsafe install locations** — the `/install-ultimate-memory-stack` skill (v1.3) guards against scaffolding into `$HOME` or a system directory (`/`, `/etc`, `/usr`, `/var`, `/root`, `/tmp`), which would otherwise scatter `memory/`, `.claude/`, and `ultimate-memory-stack/` across the user's home/root. It now stops and asks the user to `cd` into a dedicated project directory first.
- **Install-skill data-preservation guard made explicit** — Step 8 of the install skill (v1.3) now spells out the per-file existence check (`[ -e <target> ]` → preserve, do not write, ask first) so the Step 0.5 existing-store protection is mechanical rather than advisory prose; Step 7f now confirms before resetting a user-customized `PROFILE.md` on a re-install.

### Changed
- **Install doors reordered to lead with the safe paths** — the landing page, `README.md`, and `INSTALL.md` now present the **script** and **agent** doors first (both detect and preserve an existing `memory/` store); the Claude Code **marketplace** door follows, with a "back up an existing store first" note. The backup guidance is scoped to the marketplace door — the only one with overwrite potential.
- **Gated the public healthcare/institutional offer** — the public package ships **general-edition only** (compliance presets `none`/`enterprise`/`custom`; extensions `gdpr`/`soc2`/`pci-dss`). Docs, prompts, the install skill, and `setup.ps1` no longer offer the `healthcare` preset/extension or a selectable institutional edition (the installers already refused them — this aligns the docs to that gate). A HIPAA/PHI-focused institutional edition is **planned for a future release (not yet available)**; all references are now forward-looking rather than present-availability claims.
- **Marketplace (Door 3) install docs hardened** — added a "these are Claude Code slash commands, not shell commands" callout, a Prerequisites line (Claude Code installed + authenticated), and the explicit exit → `cd` → relaunch steps, and promoted the back-up-an-existing-store note from a parenthetical to a prominent warning (README, INSTALL.md, landing page). Addresses UX gaps surfaced by the post-launch install test.
- **Version bumped 3.6.0 → 3.6.1** so existing marketplace installs receive the install-skill data-safety fix (existing-store backup + preserve, shipped in skill v1.1/1.2) via `/plugin update` — the fix was committed but undelivered while the package still advertised 3.6.0.

### Known issues
- The always-loaded `memory_protocol.md` (~55k chars) exceeds Claude Code's 40k rules-file recommendation, so Claude Code shows a per-session performance notice at launch. A protocol core/extended split that brings the always-loaded core under the threshold is scheduled for **v3.6.3**. No functional impact — sessions work normally. *(that release was folded into and shipped as v4.0.0)*

### Documentation
- `INSPIRATIONS.md`: documented the project's architecture-origin provenance — the architecture is original to esoteric1entity (design begun early 2026; the Memory and Security branches are descendants of that original design) — and clarified contributor / inspiration credit across `AUTHORS.md` and `NOTICE`.

---

## [3.6.0] — 2026-06-12 — first public release

### Added (2026-06-12 — citation convention)
- `CITATION.cff` (GitHub "Cite this repository" support) + "Citing this work" README section — a courtesy citation request (esoteric1entity / PDuk Brainworks), entirely optional; the Apache-2.0 terms are unchanged.

### Added (2026-06-12 — unit-test suite)
- **`tests/` — a 177-test pytest unit suite** (282 assertions) covering the package's logic modules: `lint_runner.py`, `heartbeat_compactor.py`, `general-edition/setup.py`, and `review_quarantined.py`. Previously these modules were exercised only by full install runs + `verify.sh` (an install validator); they now have isolated, deterministic unit coverage. Includes a regression guard for the doc-completeness matcher fix (both `### Purpose` and `**Purpose:**` forms) and for the compliance-preset refusal branches. Run with `python -m pytest tests/`. (No bugs surfaced — the modules were sound post-audit; the suite locks current behavior in.)

### Fixed (2026-06-12 final pre-push review)
- Removed dead `AGENTS.md` cross-references from `INSPIRATIONS.md` (the file isn't shipped); replaced the dangling `OPENCLAW_GENERAL_EDITION_DESIGN_NOTES.md` references throughout the OpenClaw adapter (×7, in SKILL/MAPPING/scripts) with the shipped `MAPPING.md`.
- Skills badge corrected 5 → 7 (real count of shipped SKILL.md files); `general-edition/README.md` directory diagram corrected to the actual `*.override.md` filenames; stale "(forthcoming)" marker dropped from the agent-shield sibling row (ships together); `USER_GUIDE.md` security-branch link repointed, then de-linked pending agent-shield's public release (the relative path broke for standalone clones); Door 1 / Door 4 first-touch guidance added.

### Fixed (2026-06-11 pre-launch quality pass — audit findings #11–#20)
- **Addon Skill registration was broken on BOTH installers** (#12): skills were copied as flat `.claude/skills/install-<addon>.md` files, which Claude Code never discovers, and the printed slash-command hints didn't match the skills' real frontmatter names — every advertised addon command was dead. Both installers now register `.claude/skills/<frontmatter-name>/SKILL.md` and print the real commands (`/config-obsidian-vault`, `/install-graphiti`, `/install-graphify`, `/install-llmlingua`); `verify.sh` T6 now asserts discoverability (dir name == frontmatter name; flat files fail the check) instead of counting the broken layout as a pass. The `--no-templater` variant also prepended an HTML comment **above** the YAML frontmatter, breaking it — the note is now appended after the body.
- **Half-configured installs were undetectable** (#11): `setup.py` wrote the `.deployment-info` marker *before* applying the compliance preset, so a mid-install failure left a "completed-looking" install whose PROFILE.md still said `compliance: none`. The marker is now a completion certificate written last. (The cp1252 `UnicodeDecodeError` crash that triggered this scenario was fixed by forcing `encoding="utf-8"` on all PROFILE reads/writes.)
- **`lint_runner.py` flagged every template-conformant decision entry** (#13): the doc-completeness check required `### Purpose`-style headings while the shipped `decisions.template.md` uses `**Purpose:**` bold labels — 100% false-positive rate. Both lint implementations (`lint_runner.py` + `heartbeat_compactor.py`) now accept both forms with a shared matcher and aligned reporting.
- **Version banners single-sourced** (#14): installers carried diverging hardcoded versions (`setup.ps1` announced "3.0" on a 3.6.0 release; an audit-log line stamped "v3.0"). All five installers now read the package-root `VERSION` file.
- Installer "Next steps" hints renumber dynamically (no more 1→3 gap on minimal installs) and dangling "See DEPLOYMENT.md" prints now point to docs that answer the question.

### Changed (2026-06-11 doc-truth pass)
- **README / QUICKSTART / USER_GUIDE scaffold descriptions regenerated from verified installer output** (#15): all three previously described different (and fictional) post-install trees — `daily/`, `.learnings/`, `templates/`, `config/memory_stack.json`, root `HEARTBEAT.md`/`MEMORY.md` (those are OpenClaw-adapter surfaces, now linked as such). The canonical tree is the live-verified script-door output; the wizard-vs-installer split (installer scaffolds, wizard seeds) is stated explicitly.
- **INSTALL.md manual method rewritten to a verify-passing procedure** (#17): the previous steps mixed package files into the data vault, never created the nine memory directories, and never registered the protocol — following it to the letter failed the package's own `verify.sh`. The new procedure was executed literally and passes.
- Fabricated "≥80% test coverage" claim removed (#16) — `verify.sh` is an install validator, not a unit-test suite; the README now says exactly that.
- Graphiti attribution corrected to **Zep AI** (#18; was "Microsoft Research").
- README component table/badge now name the real shipped units (#19) — the previously listed `memory-coordinator` component never existed.
- `RELEASE_NOTES_v3.5.md` removed from the release (#20, maintainer D-B ruling): it was an internal validation retro (machine inventory, agent codenames, internal decision IDs) mislabeled `audience: public`; the original is preserved in the R&D tree, and CHANGELOG.md is the public release record. `INSPIRATIONS.md` §3 recreated with role-based anonymized credits.
- Smaller truth fixes: 9-root-file convention list no longer names SOUL.md twice (the ninth is DREAMS.md); OpenClaw support row points at the adapter rather than claiming "5 Skills under ~/.openclaw/skills/"; dead ClawHub listing link marked forthcoming; project-status claims date-anchored; broken umbrella-relative links replaced; `TIER_C_ACTIVATION.md` references path-qualified to `common-specs/`; `DEPLOYMENT.md` status DRAFT → stable; `SECURITY.md` + `CODE_OF_CONDUCT.md` added.

### Added
- Top-level `setup-memory-stack.sh` + `setup-memory-stack.ps1` entry points with `--minimal`, `--addon <name>`, `--no-templater`, `--edition <name>` flags
- Top-level `verify.sh` post-install validation (T1–T7 install-checkable self-test wrapper)
- Public README with debut-quality framing
- Influences & Original Work section recognising upstream work (Obsidian, Graphiti, Graphify, LLMLingua, Cline memory-bank, Karpathy lint philosophy)
- "Institutional adoption" section in CONTRIBUTING.md; institutional-edition availability note in README / INSTALL / ARCHITECTURE
- **Four-door install architecture** (the Agent Architect Stack install convention): (1) self-hosted Claude Code **marketplace** (`.claude-plugin/plugin.json` + `marketplace.json`, `/plugin marketplace add esoteric1entity/ultimate-memory-stack`); (2) **agent-executed install** — `INSTALL_AGENT.md`, a human-reviewable spec any agent harness can execute (Claude Code, OpenClaw, Hermes, generic); (3) upgraded **script** installers; (4) **manual** + activation prompt
- Install engine in `setup-memory-stack.sh`/`.ps1`: harness detection (Claude Code / OpenClaw workspace / generic), interactive target confirmation with detected defaults, `--target`/`-Target` + `--yes`/`-Yes` flags, package-root guard (refuses to mix user memory into the package tree), safe re-install (refreshes only the product-owned scaffold; `memory/` data never touched), harness registration (`.claude/rules/memory_protocol.md`), and a `.ums-manifest.json` install manifest
- Modular install entry points (`setup-memory-stack.{sh,ps1}` + `verify.sh`)
- 5 Skills: `install-ultimate-memory-stack` (workspace installer/wizard) + 4 addon installers (`config-obsidian-vault`, `install-graphiti`, `install-graphify`, `install-llmlingua`) *(corrected 2026-06-11: an earlier entry listed invented `memory-*` component names including a `memory-coordinator` that never existed)*
- Apache-2.0 LICENSE + NOTICE + AUTHORS + CONTRIBUTING + CLA + INSPIRATIONS at package root
- ClawHub marketplace metadata — planned; not yet shipped (listing is post-launch)

### Changed (install packaging)
- `skill/` directory renamed `skills/` to match the Claude Code plugin component layout (all references updated)

### Fixed
- `setup-memory-stack.ps1`: pass-through now uses named (hashtable) splatting — array splatting bound positionally and fed literal flag strings into the wrong parameters; the wrapper now also aborts with the inner exit code when the edition setup fails, instead of registering addons and reporting a successful install
- `setup.py`: stdout/stderr forced to UTF-8 on Windows (cp1252 consoles crashed with UnicodeEncodeError on unicode progress glyphs); `setup.ps1` also sets `PYTHONIOENCODING=utf-8`
- `MEMORY_INDEX` template: edition-profile quick-access path clarified per install method (previous placeholder resolved under no method's real layout)
- `project_context` template: example project slug genericized

### Changed
- `INSTALL.md` rewritten for the standalone repo: entry-point scripts first, per-method requirements stated (Windows route requires Python 3.8+), umbrella-era cross-references removed
- `install-ultimate-memory-stack` Skill promoted v1.0 DRAFT → **v1.0 STABLE** after first end-to-end execution (T1–T9 self-test 9/9 PASS); Step 2 now offers only editions actually present in the source package
- `INSTALLATION_GUIDE.md` comprehensively revised (guide rev 3.0): documents the top-level entry scripts + `verify.sh` throughout; install-skill section made present-tense (it ships); the institutional edition consistently framed as the planned package; expected-output blocks replaced with verified live-run output; §17/§18 section order restored; internal references and sanitization artifacts removed
- License decision locked: **Apache-2.0** (was: a long-standing deferred placeholder)
- All internal `branches/memory/package/` paths in install + spec docs rewritten to be self-contained for the per-package repo layout
- Top-level README replaced with the v3.6.0 debut release version (former v3.0 R&D README archived in the umbrella's R&D tree)
- Author attribution consolidated under the `esoteric1entity` handle across NOTICE / AUTHORS (privacy-preserving copyright pattern)
- Branding aligned: package is a PDuk Brainworks project under the Agent Architect Stack umbrella
- Repo layout flattened for standalone publication (no longer requires the umbrella's `branches/<branch>/` nesting)
- Schema discipline (SCHEMA_A18) is the canonical entry shape

---

## [3.5] — 2026-05-28 — final R&D-internal release

This was the last R&D-internal release before the v3.6.0 cut. Highlights:

### Added
- v3.5 BUILD COMPLETE — 10 core components shipped (Option C self-improvement Lint, OpenClaw General Edition Adapter, Multi-Machine Sync DESIGN, 4 PASS-vetted addons, claudeless QUICKSTART, etc.)
- Cross-machine round-trip validated: Claude Code ↔ OpenClaw byte-identical memory entries
- SHA-256 hashing for forensic audit-log integrity
- Quarantine workflow lockable under a strict compliance preset; non-overridable compliance profile
- B7 compliance preset (custom)
- Claudeless QUICKSTART guide for general-edition deployments

### Fixed
- v3.2.1 tier-marker regression in `MEMORY.md`
- v3.2.2 `HEARTBEAT.md` injection-limit overflow
- B2 field-type validation failure
- Typo (`decission` → `decision`)
- `setup-openclaw.sh` python vs python3 detection mismatch

### Deprecated
- DGM-H (Darwinian Generative Meta-HyperAgents) deferred from Tier B core to v4.0 candidate
- v3.2 schema patterns superseded by v3.5 SCHEMA_A18 frontmatter

---

## [3.0] — 2026-05-19 — first deployable release

### Added
- 9-root-file convention formalized (per `MEMORY_PROTOCOL.md` §2)
- SCHEMA_A18 frontmatter standard
- bash-guard + write-guard hooks (precursor to the agent-shield Layer 4)
- B1/B2/B7 compliance locks
- Edition split: an institutional compliance edition vs a user-configurable general edition

### Breaking
- v2.0 files no longer canonical (preserved in upstream R&D archive)
- AGENTS.md format changed from v2.0 narrative to v3.0 role-tables
- MEMORY.md injection limit: 12K enforced (was unbounded in v2.0)

---

## [2.0] — 2026-04-03 — pre-package R&D stack

### Added
- HOT/WARM/COLD tier architecture formalized
- `.learnings/` directory structure
- `SESSION-STATE.md` as HOT-RAM (survives compaction)
- `MEMORY.md` as curated COLD archive
- A18 frontmatter conventions (later codified as SCHEMA_A18 in v3.0)

### Notes
- v2.0 was an operational stack on the maintainer's workstation, not a packaged release artifact. Later promoted to the v3.0 deployable foundation.

---

## Spec document history

The individual spec documents in `common-specs/` previously carried their own version-history blocks in their headers. That history now lives here; the specs state current truth only.

### `SCHEMA_A18_per_entry_metadata.md`
| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-05-13 | Initial approval — core frontmatter fields (id, timestamps, provenance, pattern-key, confidence, status, content_sha256, signature) |
| 1.1 | 2026-05-14 | Added bi-temporal fields (`valid_at` / `invalid_at`) + wiki-link inline syntax (`[[ID]]`) as supplemental cross-reference form |
| 1.2 | 2026-05-15 | Decoupled `source_agent` into standard slots (defined by the stack) + consumer-defined slots (defined by the consuming architecture); reference 4-agent topology repositioned as example, not canonical enum |
| 1.3 | 2026-05-27 | Extended to file-level frontmatter via the `scope:` field; added optional `loaded_when:` + `points_to:` progressive-disclosure fields. Backward compatible (absent `scope:` defaults to `entry`) |
| 1.4 | 2026-05-27 | Added access-tracking fields (`access_count`, `last_accessed`, `recent_sessions`) for PageRank-style promotion signal. Backward compatible (defaults = no signal) |

### `ARCHITECTURE.md`
| Version | Date | Changes |
|---|---|---|
| 3.0 | 2026-05-13 | Initial 7-layer architecture (Layer 0–6) with deployment-tier markers |
| 3.0 rev-1 | 2026-05-14 | Corrected Tier C ID assignments; added Obsidian-vault compatibility (§5); selected Graphiti+Kuzu for Layer 5 (§9); clarified debunked-claims vs included-tools distinction (§13); added §11.5 adjacent tools (Graphify, Aider repo-map) |
| — | 2026-05-19 | Layer 5 refresh: Graphiti v0.29.0 (MCP server, Ollama support → T1 activation path, REST service) |

### `MEMORY_PROTOCOL.md`
| Version | Date | Changes |
|---|---|---|
| 3.0 | 2026-05-14 | Initial operational contract — session start, context budget, 9-level conflict hierarchy, validation-on-read, write ops, edition profiles, self-test, compaction handoff |
| 3.5 retrofits | 2026-05-27 | §2.5 context-rot mitigation (Tier 1 pinned start AND end); §10.5 +5 self-improvement Lint checks (Option C, replaces the deferred DGM-H scope) + subagent execution model; §11 caps upgraded advisory → enforced hard errors (§11.5); §12 PageRank-style promotion signal |

### `BOOTSTRAP_PROMPT.md`
| Version | Date | Changes |
|---|---|---|
| 1.0–2.0 | 2026-04-10 | Rapid early iterations: core files + session protocol → adaptive loading tiers, conflict resolution, risk scoring, cascade detection → subdirectory structure, MEMORY_INDEX, consolidation protocol → tiered context budget, 9-level conflict hierarchy, compliance profile, self-test suite |
| 3.0 | 2026-05-13 | Paradigm shift to the referencing model: per-entry frontmatter (A18), per-project memory banks (A3), Layer 0–6 architecture with T0–T4 tier markers, edition profiles, compliance-preset hybrid, audit/quarantine/signature features, migration path from v2.0 — drawn from a 210-source research base |
| 3.0 rev-1 | 2026-05-14 | Corrected Tier C ID mismatches; all 12 Tier B items listed explicitly; surfaced B5 bi-temporal fields, C2 Graphiti+Kuzu, C3 Graphify with the adjacent-tool distinction; Obsidian-vault compatibility callout; "borrow ideas, not numbers" framing |

### Runtime schemas
| Document | Version | Date | Notes |
|---|---|---|---|
| `SCHEMA_audit_log.md` | 1.0 | 2026-05-14 | JSONL audit format; canonical formatting (compact JSON, second-precision ts, `entry_id` sentinels) locked 2026-05-26 after cross-script drift was caught in validation |
| `SCHEMA_quarantine.md` | 1.0 | 2026-05-14 | Quarantine workflow + reason codes |
| `SCHEMA_compliance_profile.md` | 1.0 | 2026-05-14 | 3-preset hybrid + custom |
| `SCHEMA_lint.md` | 1.0 | 2026-05-15 | 6 lint checks (Karpathy LLM Wiki pattern); +5 self-improvement checks added with the v3.5 retrofits |
| `SCHEMA_sync_log.md` | 1.0 | 2026-05-28 | Cross-machine sync provenance schema (implementation is a future deliverable; schema ships now) |
| `USER_CHEAT_SHEET_core.md` | 1.1 | 2026-05-29 | v1.0 (2026-05-15) + v1.1 deployment section |

### `content_sha256` normalization (cross-cutting)
Locked 2026-06-04 after cross-machine round-trip verification produced hash mismatches: the canonical computation is `file_text.split('---', 2)[2].lstrip('\n')` encoded UTF-8 (no BOM), LF preserved, trailing whitespace preserved. See SCHEMA_A18 §"`content_sha256` normalization".

---

*Maintained by `esoteric1entity`. A PDuk Brainworks project — part of [The Agent Architect Stack](https://github.com/esoteric1entity/agent-architect-stack).*
