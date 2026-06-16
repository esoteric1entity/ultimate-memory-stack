# Changelog — Ultimate Memory Stack

All notable changes to this package will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed
- **macOS: installer failed at addon registration** — `setup-memory-stack.sh` used a bash-4 associative array (`declare -A`), but macOS ships bash 3.2; replaced with a portable case-statement lookup. Caught by the cross-OS install CI on launch day (the macOS leg had never run on real Apple hardware before).
- **Install skill could overwrite an existing `memory/` store** — the `/install-ultimate-memory-stack` skill (≤ v1.1) created `session_state.md` / `MEMORY_INDEX.md` / `user_profile.md` / project briefs / `feedback.md` without checking whether they already existed, so re-running it over an existing project-local memory store reset accumulated memory to empty templates. Skill **v1.2** adds an existing-store safety gate (detect → timestamped `memory.backup.<ts>/` → preserve mode; user-data files are now create-if-absent), matching the shell and agent install doors, which already preserved data. (Claude Code's native memory and `CLAUDE.md` are unaffected — UMS writes only to the project-local `memory/`.)
- **Windows installer accepted a compliance preset it then rejected** — `general-edition/setup.ps1` listed `healthcare` as a valid preset/extension while `setup.sh`/`setup.py` refuse it, so passing `-Compliance healthcare` produced a confusing downstream failure. The PS1 now rejects it up-front with the institutional-edition message, matching the other installers.

### Changed
- **Install doors reordered to lead with the safe paths** — the landing page, `README.md`, and `INSTALL.md` now present the **script** and **agent** doors first (both detect and preserve an existing `memory/` store); the Claude Code **marketplace** door follows, with a "back up an existing store first" note. The backup guidance is scoped to the marketplace door — the only one with overwrite potential.
- **Gated the public biotech/healthcare offer** — the public package ships **general-edition only** (compliance presets `none`/`enterprise`/`custom`; extensions `gdpr`/`soc2`/`pci-dss`). Docs, prompts, the install skill, and `setup.ps1` no longer offer the `healthcare` preset/extension or a selectable biotech edition (the installers already refused them — this aligns the docs to that gate). A HIPAA/PHI-focused institutional edition is **planned for a future release (not yet available)**; all references are now forward-looking rather than present-availability claims.

### Documentation
- `INSPIRATIONS.md`: documented the project's architecture-origin provenance — the architecture is original to esoteric1entity (design begun early 2026; the Memory and Security branches are descendants of that original design) — and clarified contributor / inspiration credit across `AUTHORS.md` and `NOTICE`.

---

## [3.6.0] — 2026-06-12 — first public release

### Added (2026-06-12 — citation convention)
- `CITATION.cff` (GitHub "Cite this repository" support) + "Citing this work" README section — a courtesy citation request (esoteric1entity / PDuk Brainworks), entirely optional; the Apache-2.0 terms are unchanged.

### Added (2026-06-12 — unit-test suite)
- **`tests/` — a 177-test pytest unit suite** (282 assertions) covering the package's logic modules: `lint_runner.py`, `heartbeat_compactor.py`, `general-edition/setup.py`, and `review_quarantined.py`. Previously these modules were exercised only by full install runs + `verify.sh` (an install validator); they now have isolated, deterministic unit coverage. Includes a regression guard for the doc-completeness matcher fix (both `### Purpose` and `**Purpose:**` forms) and for the biotech/healthcare-refusal branches. Run with `python -m pytest tests/`. (No bugs surfaced — the modules were sound post-audit; the suite locks current behavior in.)

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
- "Institutional adoption (biotech edition)" section in CONTRIBUTING.md; biotech-edition availability note in README / INSTALL / ARCHITECTURE
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
- `INSTALLATION_GUIDE.md` comprehensively revised (guide rev 3.0): documents the top-level entry scripts + `verify.sh` throughout; install-skill section made present-tense (it ships); biotech-edition consistently framed as the institutional package; expected-output blocks replaced with verified live-run output; §17/§18 section order restored; internal references and sanitization artifacts removed
- License decision locked: **Apache-2.0** (was: deferred per the long-standing DEC-017 placeholder)
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
- SHA-256 hashing for forensic audit-log integrity (biotech edition)
- Quarantine workflow lockable in biotech edition; non-overridable healthcare compliance preset
- B7 compliance preset (custom)
- Claudeless QUICKSTART guide for general-edition deployments

### Fixed
- Bug #12 — v3.2.1 tier-marker regression in `MEMORY.md`
- Bug #13 — v3.2.2 `HEARTBEAT.md` injection-limit overflow
- Bug #14 — B2 field-type validation failure in biotech edition
- Bug #15 — typo (`decission` → `decision`)
- Bug #16 — `setup-openclaw.sh` python vs python3 detection mismatch

### Deprecated
- DGM-H (Darwinian Generative Meta-HyperAgents) deferred from Tier B core to v4.0 candidate
- v3.2 schema patterns superseded by v3.5 SCHEMA_A18 frontmatter

---

## [3.0] — 2026-05-19 — first deployable release

### Added
- 9-root-file convention formalized (per `MEMORY_PROTOCOL.md` §2)
- SCHEMA_A18 frontmatter standard
- bash-guard + write-guard hooks (precursor to the agent-shield Layer 4)
- B1/B2/B7 biotech edition locks
- Edition split: biotech-edition (HIPAA-grade) vs general-edition (user-configurable)

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
| 1.0–2.0 | 2026-04-10 | Rapid early iterations: core files + session protocol → adaptive loading tiers, conflict resolution, risk scoring, cascade detection → subdirectory structure, MEMORY_INDEX, consolidation protocol → tiered context budget, 9-level conflict hierarchy, healthcare compliance profile, self-test suite |
| 3.0 | 2026-05-13 | Paradigm shift to the referencing model: per-entry frontmatter (A18), per-project memory banks (A3), Layer 0–6 architecture with T0–T4 tier markers, edition profiles, compliance-preset hybrid, audit/quarantine/signature features, migration path from v2.0 — drawn from a 210-source research base |
| 3.0 rev-1 | 2026-05-14 | Corrected Tier C ID mismatches; all 12 Tier B items listed explicitly; surfaced B5 bi-temporal fields, C2 Graphiti+Kuzu, C3 Graphify with the adjacent-tool distinction; Obsidian-vault compatibility callout; "borrow ideas, not numbers" framing |

### Runtime schemas
| Document | Version | Date | Notes |
|---|---|---|---|
| `SCHEMA_audit_log.md` | 1.0 | 2026-05-14 | JSONL audit format; canonical formatting (compact JSON, second-precision ts, `entry_id` sentinels) locked 2026-05-26 after cross-script drift was caught in validation |
| `SCHEMA_quarantine.md` | 1.0 | 2026-05-14 | Quarantine workflow + reason codes |
| `SCHEMA_compliance_profile.md` | 1.0 | 2026-05-14 | 3-preset hybrid (none / healthcare / enterprise) + custom |
| `SCHEMA_lint.md` | 1.0 | 2026-05-15 | 6 lint checks (Karpathy LLM Wiki pattern); +5 self-improvement checks added with the v3.5 retrofits |
| `SCHEMA_sync_log.md` | 1.0 | 2026-05-28 | Cross-machine sync provenance schema (implementation is a future deliverable; schema ships now) |
| `USER_CHEAT_SHEET_core.md` | 1.1 | 2026-05-29 | v1.0 (2026-05-15) + v1.1 deployment section |

### `content_sha256` normalization (cross-cutting)
Locked 2026-06-04 after cross-machine round-trip verification produced hash mismatches: the canonical computation is `file_text.split('---', 2)[2].lstrip('\n')` encoded UTF-8 (no BOM), LF preserved, trailing whitespace preserved. See SCHEMA_A18 §"`content_sha256` normalization".

---

*Maintained by `esoteric1entity`. A PDuk Brainworks project — part of [The Agent Architect Stack](https://github.com/esoteric1entity/agent-architect-stack).*
