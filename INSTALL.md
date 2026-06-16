---
file: INSTALL
title: "Install Guide (UMS v3.6.1)"
license: Apache 2.0
---

# Install — Ultimate Memory Stack

> **In a hurry → you're in the right place.** Need full detail (prerequisites, pre-install decisions, multi-machine deployment, v2→v3 migration) → [`INSTALLATION_GUIDE.md`](./INSTALLATION_GUIDE.md).

This is the **short install guide** for users who just want to get going. Four doors, one engine — pick what fits you:

| Door | For | Start here |
|---|---|---|
| **Script** | CLI users | below ↓ |
| **Tell your agent** | any agent harness | clone, then: *"install this — read `INSTALL_AGENT.md`"* |
| **Marketplace** | Claude Code users | Run **inside Claude Code** (these are slash commands, not shell): `/plugin marketplace add …` → `/plugin install …` → exit Claude Code (`/exit` or Ctrl-D), `cd` to your project in your shell, relaunch, `/install-ultimate-memory-stack` (see README Door 3). Prereq: Claude Code installed + authenticated. **Re-installing, or have an existing `memory/` store? Back it up first** — or use the Script / agent door, which preserve it automatically. |
| **Manual** | no tooling | drag 2 folders + paste `common-specs/BOOTSTRAP_PROMPT.md` |

## TL;DR (script door)

```bash
# 1. Clone (anywhere)
git clone https://github.com/esoteric1entity/ultimate-memory-stack.git

# 2. Install — run FROM the directory where the memory stack should live:
cd /path/to/your/workspace
/path/to/ultimate-memory-stack/setup-memory-stack.sh    # or add: --target <dir> --yes

# 3. Verify
/path/to/ultimate-memory-stack/verify.sh
```

That's the stack installed. The installer detects your harness (Claude Code / OpenClaw workspace / generic), confirms the target with you, refuses to install into its own package directory, and writes a `.ums-manifest.json` recording what it did. `verify.sh` runs the post-install validation suite.

## Edition

This repo ships **general-edition** only — it is the default and there is no edition to pick. It covers solo dev, research, education, B2B SaaS, enterprise, and custom compliance, distributed here under Apache 2.0.

| Edition | Use case | Availability |
|---|---|---|
| **General** (`general-edition/`) | Solo dev, research, education, B2B SaaS, enterprise, custom compliance | ✅ This repo (Apache 2.0) |
| ~~Biotech~~ | HIPAA-regulated healthcare / lab R&D | 🚧 Not available — see note below |

A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

## Script — Bash (Linux / macOS / WSL / Git Bash)

Run from your workspace (or pass `--target`):

```bash
setup-memory-stack.sh                                   # full install (all addons)
setup-memory-stack.sh --minimal                         # core only (no addons)
setup-memory-stack.sh --addon memory-vault --addon memory-graphiti
setup-memory-stack.sh --no-templater                    # skip Obsidian Templater auto-enable
setup-memory-stack.sh --target ~/my-workspace           # explicit install target
setup-memory-stack.sh --yes --skip-wizard --compliance=none   # fully non-interactive
```

The default install is interactive — it confirms the install target (auto-detecting an OpenClaw workspace if you have one), then asks for your name, role/organization, and preferences.

Time: ~30 seconds + interactive prompts.

## Script — PowerShell (Windows)

```powershell
.\setup-memory-stack.ps1
```

Same flags and behavior as the Bash script. Requires PowerShell 5.1+ and **Python 3.8+** (the Windows path delegates the core install to `setup.py`).

## Manual (no tooling)

For users who prefer to copy files by hand. This procedure produces the same
layout as the script door — `verify.sh` passes on the result. (`memory/` is
**your data vault**; the package's own files live in a separate
`ultimate-memory-stack/` directory — don't mix the two.)

1. Copy the cloned package into your workspace as a subdirectory:
   `<YOUR_WORKSPACE>/ultimate-memory-stack/` (it needs at least
   `common-specs/` and `general-edition/` inside).
2. Create the memory vault skeleton — nine empty directories:
   `memory/sessions`, `memory/decisions`, `memory/feedback`,
   `memory/projects`, `memory/security`, `memory/references`,
   `memory/user`, `memory/archive`, `memory/quarantine`.
3. **Claude Code:** copy
   `ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md` to
   `<YOUR_WORKSPACE>/.claude/rules/memory_protocol.md` so the protocol
   auto-loads. *(OpenClaw: use the adapter — `core/openclaw-adapter/QUICKSTART.md`.
   Other harnesses: reference the protocol from your `AGENTS.md`.)*
4. **Optional addons (Claude Code):** for each addon you want, copy its
   `SKILL.md` to `.claude/skills/<name>/SKILL.md`, where `<name>` is the
   `name:` field inside that SKILL.md — e.g.
   `recommended-addons/graphiti-installer/SKILL.md` →
   `.claude/skills/install-graphiti/SKILL.md`. (A flat `.md` directly under
   `.claude/skills/` is **not** discovered.)
5. Restart your agent harness, then paste the activation prompt from
   `ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md` to run the wizard.
6. Validate: `ultimate-memory-stack/verify.sh <YOUR_WORKSPACE>` (Git Bash/WSL
   on Windows).

The full manual walkthrough is in [`INSTALLATION_GUIDE.md`](./INSTALLATION_GUIDE.md).

## Skill-based (Claude Code only)

If you're using Claude Code, the install-ultimate-memory-stack Skill can be invoked directly:

```
/install-ultimate-memory-stack
```

This Skill guides you through the install interactively. See [`skills/install-ultimate-memory-stack/SKILL.md`](./skills/install-ultimate-memory-stack/SKILL.md) for details.

## Post-install verification

```bash
./verify.sh
```

Validates the installed structure, schemas, profile, and edition configuration. If anything reports `FAIL`, check the troubleshooting section in [`INSTALLATION_GUIDE.md`](./INSTALLATION_GUIDE.md).

## Next steps

- Read [`QUICKSTART.md`](./QUICKSTART.md) for a 5-minute tour of what UMS does
- Read [`USER_GUIDE.md`](./USER_GUIDE.md) for the long-form usage guide
- Check out the recommended add-ons (Obsidian vault config, Graphiti, Graphify, LLMLingua) in `recommended-addons/`

## Cross-references

- [`README.md`](./README.md) — project overview
- [`INSTALLATION_GUIDE.md`](./INSTALLATION_GUIDE.md) — full multi-method install (comprehensive)
- [`QUICKSTART.md`](./QUICKSTART.md) — 5-minute tour
- [`USER_GUIDE.md`](./USER_GUIDE.md) — long-form usage
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — contributing + institutional adoption
- [`general-edition/`](./general-edition/) — general-edition PROFILE + overrides + setup
- [`skills/install-ultimate-memory-stack/SKILL.md`](./skills/install-ultimate-memory-stack/SKILL.md) — Skill-based install
