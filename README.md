# Ultimate Memory Stack

> **Persistent, modular memory for AI agents.** Works with Claude Code, OpenClaw, and any harness that supports the 9-root-file convention. Install in one command; opt-in to addons; verify after install.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status: v3.6.0](https://img.shields.io/badge/Status-v3.6.0-green.svg)](#)
[![Skills: 7](https://img.shields.io/badge/Skills-7-orange.svg)](#)
[![Tests](https://github.com/esoteric1entity/ultimate-memory-stack/actions/workflows/test.yml/badge.svg)](https://github.com/esoteric1entity/ultimate-memory-stack/actions/workflows/test.yml)

---

## What it does

Ultimate Memory Stack (UMS) gives AI agents **persistent memory across sessions** — knowledge that survives context resets, gets searchable as a graph, and stays organized in a human-readable vault.

It's not a replacement for your agent harness. It's an **integration layer** that any harness can adopt.

| Component | What it provides | Tier |
|---|---|---|
| **Core stack** (`common-specs/` + `general-edition/` + install engine) | The memory vault scaffold, protocol auto-registration, schemas, templates, wizard, and `verify.sh` | A — core |
| **`/config-obsidian-vault`** (addon `memory-vault`) | Obsidian-based personal-knowledge-management interface; the human-readable layer | B — primary |
| **`/install-graphiti`** (addon `memory-graphiti`) | Bi-temporal knowledge graph over entities + relationships + temporal facts | C — opt-in |
| **`/install-graphify`** (addon `memory-graphify`) | Code symbol graph (functions, classes, imports) across 19+ languages | C — opt-in |
| **`/install-llmlingua`** (addon `memory-llmlingua`) | Prompt compression at a quality-preserving threshold | C — opt-in |

**Modular install** — `--addon memory-graphiti` to include selectively; `--minimal` for core-only. Addons register as Claude Code Skills under the slash-command names shown (each completes its own install when invoked).

---

## Install — pick your door

**🚪 Door 1 — Marketplace (Claude Code)**

```
/plugin marketplace add esoteric1entity/ultimate-memory-stack
/plugin install ultimate-memory-stack@ultimate-memory-stack
```

Then, in the project where the memory should live: `/install-ultimate-memory-stack` — the skill scaffolds and verifies the whole workspace interactively. *(If `marketplace add` reports "not found", the plugin hasn't propagated yet — use Door 2 or Door 3 in the meantime.)*

**🚪 Door 2 — Tell your agent**

```bash
git clone https://github.com/esoteric1entity/ultimate-memory-stack.git
```

Then tell your agent — Claude Code, OpenClaw, or any capable harness — *"install this: read `INSTALL_AGENT.md` and follow it."* The agent walks a documented flow: detect your harness → confirm the target → scaffold → register → verify. `INSTALL_AGENT.md` is the entire spec, human-readable — review it before you run it.

**🚪 Door 3 — Script**

```bash
git clone https://github.com/esoteric1entity/ultimate-memory-stack.git

cd /path/to/your/workspace                       # where the memory stack should live
/path/to/ultimate-memory-stack/setup-memory-stack.sh     # interactive; or --target <dir> --yes
/path/to/ultimate-memory-stack/verify.sh
```

Windows: `setup-memory-stack.ps1` — same options, PowerShell-style: `-Minimal`, `-Addon`, `-Compliance`, … (requires Python 3.8+). The installer detects your harness (Claude Code project, OpenClaw workspace, or generic), confirms the target, and registers the protocol so it auto-loads.

**🚪 Door 4 — Manual**

Drag `common-specs/` + `general-edition/` into your workspace and paste the activation prompt from `common-specs/BOOTSTRAP_PROMPT.md`. No tooling needed at all. New to the stack? Read [`QUICKSTART.md`](./QUICKSTART.md) first for a 5-minute tour. (Full step-by-step: the **Manual** section in [`INSTALL.md`](./INSTALL.md).)

> **Your data stays yours:** every door refuses to install into the package's own directory, never touches your `memory/` data on re-install, and records exactly what it did in `.ums-manifest.json`.

---

## Supported harnesses

| Harness | Status | Notes |
|---|---|---|
| **Claude Code** | ✅ Supported | Installs as a plugin marketplace entry |
| **OpenClaw** | ✅ Supported | Via the OpenClaw adapter (`core/openclaw-adapter/` — generates the OpenClaw root files + memory tree; see its QUICKSTART) |
| **Other** | 🟡 Compatible | If your harness uses the 9-root-file convention (AGENTS.md / SOUL.md / TOOLS.md / IDENTITY.md / USER.md / HEARTBEAT.md / BOOTSTRAP.md / MEMORY.md / DREAMS.md), UMS will work |

UMS does **NOT replace** your harness. It complements it. Each Skill is opt-in.

---

## What you get after install

This tree is the verified output of the script door (the other doors produce the same layout):

```
your-workspace/
├── memory/                      ← YOUR data vault (empty until the wizard runs)
│   ├── sessions/                ← session_state.md — where you left off
│   ├── decisions/               ← DEC-### entries (durable decisions)
│   ├── feedback/                ← FB-### entries (corrections + preferences)
│   ├── projects/                ← per-project memory banks
│   ├── security/                ← vetting log + audit log (preset-dependent)
│   ├── references/              ← pointers to external sources
│   ├── user/                    ← identity + user profile
│   ├── archive/                 ← compacted/retired entries
│   └── quarantine/              ← lint-quarantined content
│
├── .claude/
│   ├── rules/memory_protocol.md     ← protocol, auto-loaded by Claude Code
│   └── skills/<name>/SKILL.md       ← the addon installer Skills you selected
│
├── .ums-manifest.json           ← what the installer did (door, harness, addons)
├── .deployment-info             ← completion certificate (absent = incomplete install)
│
└── ultimate-memory-stack/       ← the package (specs, templates, editions) — code, not data
```

The activation wizard (paste `ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md` into your agent) then seeds `memory/MEMORY_INDEX.md` and `memory/sessions/session_state.md` — the installer never invents data on your behalf.

---

## Modular install flags

```bash
# Core only (no addons)
./setup-memory-stack.sh --minimal

# Specific addons
./setup-memory-stack.sh --addon memory-vault --addon memory-graphiti

# All addons (default)
./setup-memory-stack.sh

# Skip Templater auto-enable in Obsidian community-plugins.json
./setup-memory-stack.sh --no-templater
```

---

## Documentation

- **[INSTALL.md](INSTALL.md)** — Quick install (the four doors: marketplace / agent / script / manual)
- **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)** — Comprehensive multi-method install (long form)
- **[QUICKSTART.md](QUICKSTART.md)** — 5-minute tour of what UMS does
- **[USER_GUIDE.md](USER_GUIDE.md)** — Long-form usage guide
- **[common-specs/ARCHITECTURE.md](common-specs/ARCHITECTURE.md)** — How UMS is structured (7 layers, tier markers)
- **[common-specs/MEMORY_PROTOCOL.md](common-specs/MEMORY_PROTOCOL.md)** — Operational rules + configuration reference
- **[common-specs/USER_CHEAT_SHEET_core.md](common-specs/USER_CHEAT_SHEET_core.md)** — User best practices
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — How to contribute
- **[CHANGELOG.md](CHANGELOG.md)** — Version history

---

## Sibling packages (Agent Architect Stack)

UMS is the **Memory branch** of the broader Agent Architect Stack. Sibling branches:

| Branch | Repo | Purpose |
|---|---|---|
| **Memory** (this) | [ultimate-memory-stack](https://github.com/esoteric1entity/ultimate-memory-stack) | Persistent memory + knowledge graphs |
| **Security** | agent-shield *(release imminent)* | 8-layer defensive overlay for agents |
| *(more planned)* | — | — |

UMS and agent-shield are **independent** — no runtime dependencies. They cooperate via shared conventions; install either or both.

---

## What UMS is NOT

To set expectations:

- ❌ NOT an agent harness — runs INSIDE Claude Code / OpenClaw / similar
- ❌ NOT a daemon / system service — install-time tool only
- ❌ NOT cloud-mediated — local-first; your data stays on your machine
- ❌ NOT a replacement for your existing memory — integrates with, doesn't replace
- ❌ NOT specific to any business or compliance regime — general-purpose by default

> **Looking for the biotech edition?** This public release ships the general edition. The biotech-edition (HIPAA-grade) is also available for institutional adopters — see [CONTRIBUTING.md](CONTRIBUTING.md) for licensing terms.

---

## Project status

**v3.6.0 — first public release.** Predecessor versions (v3.0/v3.5) have run in production on the maintainer's own machines since 2026-05-19, across Claude Code and OpenClaw deployments on three platforms, with a cross-machine validation cycle before this release was cut.

- Build: production-ready
- Verification: two complementary layers — `verify.sh` validates an *install* (scaffold, registration, manifest), and `tests/` holds a **177-test pytest unit suite** covering the logic modules (lint runner, heartbeat compactor, edition setup, quarantine review). Run the units with `python -m pytest tests/`
- License: Apache-2.0
- Maintenance: actively maintained

**Quality process.** This project is AI-assisted by design — built with AI agents under human architectural direction — and engineered accordingly: every change is developed test-first and must pass the full unit, integration, and end-to-end suites before it ships. Releases additionally go through an independent adversarial review pass, with reviewers tasked to break the changes rather than approve them. Behind every release claim sits an append-only, internally maintained test-evidence register.

---

## License

[Apache License 2.0](LICENSE). Use, modify, distribute, fork — go forth.

---

## Citing this work

Everything here is free under Apache-2.0 — no strings attached. If UMS helps you
build something, powers your agent, or simply earns its keep, the one thing we ask
— **entirely optional, always appreciated** — is a citation or mention of
**esoteric1entity** / **PDuk Brainworks**: a link back to this repo, a line in your
credits, or GitHub's "Cite this repository" button (powered by
[`CITATION.cff`](./CITATION.cff)).

---

## Authors

- **`esoteric1entity`** — architect + design lead. A PDuk Brainworks project.

This stack was developed across multiple deployments with peer-review at each step. See [`AUTHORS.md`](AUTHORS.md) for the full contributor list and [`CONTRIBUTING.md`](CONTRIBUTING.md) for how the work is governed.

---

## Acknowledgments

Built on the shoulders of:
- **Obsidian** + **Templater** community
- **Graphiti** (Zep AI) — bi-temporal knowledge graph
- **Graphify** + tree-sitter parsers — symbol graph
- **LLMLingua-2** (Microsoft Research) — prompt compression
- **Anthropic Claude** + **OpenClaw** — harnesses we target

---

## Get involved

- 🐛 [Report a bug](https://github.com/esoteric1entity/ultimate-memory-stack/issues)
- 💡 [Suggest a feature](https://github.com/esoteric1entity/ultimate-memory-stack/discussions)
- 🛠️ [Contribute](CONTRIBUTING.md)
- 📦 ClawHub listing — forthcoming

---

*"Persistent memory shouldn't be an afterthought. It should be a primitive."*
