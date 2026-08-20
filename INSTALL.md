---
file: INSTALL
title: "Install Guide (UMS v4.0.1)"
license: Apache 2.0
---

# Install — Ultimate Memory Stack

> **In a hurry → you're in the right place.** Need full detail (prerequisites, pre-install decisions, multi-machine deployment, v2→v3 migration)? Jump to the [**Full Guide**](#full-guide) below.

This is the **short install guide** for users who just want to get going. Four doors, one engine — pick what fits you:

| Door | For | Start here |
|---|---|---|
| **Script** | CLI users | below ↓ |
| **Tell your agent** | any agent harness | clone, then: *"install this — read `INSTALL_AGENT.md`"* |
| **Marketplace** | Claude Code users | Run **inside Claude Code** (these are slash commands, not shell): `/plugin marketplace add …` → `/plugin install …` → exit Claude Code (`/exit` or Ctrl-D), `cd` to your project in your shell, relaunch, `/install-ultimate-memory-stack` (see README Door 3). Prereq: Claude Code installed + authenticated. **Re-installing, or have an existing `memory/` store? Back it up first** — or use the Script / agent door, which preserve it automatically. |
| **Manual** | no tooling | copy the package as `ultimate-memory-stack/`, then paste the activation prompt |

**New to UMS? Use Door 1 (script) — the TL;DR below.**

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

HIPAA/PHI is out of scope for this edition; the `healthcare` compliance preset is a reserved value the installer refuses.

## Script — Bash (Linux / macOS / WSL / Git Bash)

Run from your workspace (or pass `--target`):

```bash
setup-memory-stack.sh                                   # full install (all addons)
setup-memory-stack.sh --minimal                         # core only (no addons)
setup-memory-stack.sh --addon memory-vault --addon memory-graphiti
                                                         # valid --addon values: memory-vault, memory-graphiti, memory-graphify, memory-llmlingua
setup-memory-stack.sh --no-templater                    # skip Obsidian Templater auto-enable
setup-memory-stack.sh --target ~/my-workspace           # explicit install target
setup-memory-stack.sh --yes --skip-wizard --compliance=none   # fully non-interactive
```

The default install is interactive — it confirms the install target (auto-detecting an OpenClaw workspace if you have one) and prints a Next-steps pointer. Your name, role/organization, and preferences are collected afterward, when your agent runs the activation prompt (the setup wizard — see [Step 4](#step-4--paste-the-activation-prompt--answer-the-setup-wizard) below).

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
   auto-loads. Also copy `ultimate-memory-stack/common-specs/MEMORY_PROTOCOL_EXTENDED.md`
   to `<YOUR_WORKSPACE>/memory/MEMORY_PROTOCOL_EXTENDED.md` — an on-demand
   reference, **not** `.claude/rules/` (that would auto-load it every session).
   *(OpenClaw: use the adapter — `core/openclaw-adapter/QUICKSTART.md`.
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

The full manual walkthrough is in the [Full Guide → Manual walkthrough](#manual-walkthrough) below.

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

Validates the installed structure, schemas, profile, and edition configuration. If anything reports `FAIL`, check [Full Guide → Troubleshooting](#troubleshooting) below.

## Next steps

- Read [`QUICKSTART.md`](./QUICKSTART.md) for a 5-minute tour of what UMS does
- Read [`USER_GUIDE.md`](./USER_GUIDE.md) for the long-form usage guide
- Check out the recommended add-ons (Obsidian vault config, Graphiti, Graphify, LLMLingua) in `recommended-addons/`

## Cross-references

- [`README.md`](./README.md) — project overview
- [`QUICKSTART.md`](./QUICKSTART.md) — 5-minute tour
- [`USER_GUIDE.md`](./USER_GUIDE.md) — long-form usage
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — contributing + institutional adoption
- [`general-edition/`](./general-edition/) — general-edition PROFILE + overrides + setup
- [`general-edition/DEPLOYMENT.md`](./general-edition/DEPLOYMENT.md) — edition deploy guidance (prerequisites, scenarios, tier detection)
- [`skills/install-ultimate-memory-stack/SKILL.md`](./skills/install-ultimate-memory-stack/SKILL.md) — Skill-based install
- The **[Full Guide](#full-guide)** below — the comprehensive multi-method reference (formerly `INSTALLATION_GUIDE.md`)

---

# Full Guide

> The deep reference — prerequisites, pre-install decisions, every method step-by-step, multi-machine deployment, v2→v3 migration, troubleshooting, edition/preset switching, uninstall, the secondary (PowerShell / Python) methods, and the addon catalog. **Consolidated from the former `INSTALLATION_GUIDE.md` as of v3.6.2.**
>
> The four install doors are summarized at the top of this file; this guide is the prescriptive detail behind them — it leaves nothing up for guesses. Start by picking a method, jump to that section, then run [Post-install verification](#post-install-verification-in-depth).

## Pick your install method

> These are sub-methods of the four install "doors" of the Agent Architect Stack convention. **Door 2 (agent-executed install)** lives mostly outside this section — point any capable agent at [`INSTALL_AGENT.md`](./INSTALL_AGENT.md) and say "install this." **New to UMS? Use Door 1a (Bash script).**

### Three primary methods (recommended for most users)

| Method | Works on | Prerequisites | Harness | User actions | Time |
|--------|----------|---------------|---------|--------------|------|
| **Door 4 — Manual Drag-and-Drop** | Windows / Mac / Linux | None | Any agent (to activate) | 4 actions | ~5 min total |
| **Door 1a — Bash `setup-memory-stack.sh`** | Mac / Linux / WSL | Bash 4.0+ (standard) | None to scaffold; any agent to activate | 1 command | ~30 sec + wizard |
| **Door 3 — Claude Code Skill** | Anywhere with Skills enabled | Skills capability enabled | **Claude Code only** | 1 slash command | ~5 sec + wizard |

These three cover ~95% of user contexts. The **Harness** column is the key difference: the manual and script doors run on any 9-root-file agent (or none, for the script's file-copy step) — only the Skill door requires Claude Code specifically. Door 3 also covers the **marketplace install** (Claude Code: `/plugin marketplace add esoteric1entity/ultimate-memory-stack`, then `/install-ultimate-memory-stack` — the [Claude Code Skill installer](#claude-code-skill-installer) covers the skill it runs).

### Secondary methods (kept available, see [Secondary and advanced options](#secondary-and-advanced-options))

Both of these are Door 1 (script) variants:

| Method | Works on | Prerequisites | Why secondary |
|--------|----------|---------------|---------------|
| **Door 1b — PowerShell `setup-memory-stack.ps1`** | Windows | Python 3.8+ (the core install delegates to setup.py) | Requires Python — not a fully "native Windows" option yet. Slated for native-PowerShell rewrite. |
| **Door 1c — Python `setup.py`** | Anywhere with Python 3.8+ | Python 3.8+ + optional `cryptography` for T3 | Power-user option with crypto key generation built in. Most users don't need this. |

If you don't already have Python installed, use Door 4 or Door 1a instead.

### Tier detection (optional pre-check)

If you want to know what features will be available at install time:

```bash
# Linux/Mac/WSL (bash)
node --version 2>/dev/null && echo "✓ T2+ (Node.js)" || echo "T0 or T1 only"
python3 -c "import cryptography" 2>/dev/null && echo "✓ T3+ (Python crypto)" || echo "T2 or lower"
```

```powershell
# Windows PowerShell
node --version                     # version prints -> T2+ (Node.js)
python -c "import cryptography"    # no error -> T3+ (Python crypto)
```

Don't have these? No problem — the system runs fine at T0; higher-tier features activate automatically when their infrastructure unblocks.

## Prerequisites

### Required (everyone)
- **A capable agent harness** — Claude Code, OpenClaw, or any 9-root-file agent — to run the activation prompt and operate the stack. (The script door needs no agent to *scaffold* the files; you only need an agent to *activate* the stack afterward. Verify Claude Code, if that's your harness, with `claude --version` — get it from https://claude.ai/code.)
- **Writable working directory** (~50 MB total for memory + audit logs)
- **The deployable package** (this directory) accessible:
  - Cloned via git, OR
  - Copied from a source-of-truth location (e.g., a network share or backed-up drive), OR
  - Extracted from a release archive

### Method-specific prerequisites (only if you pick that method)
- **Door 4 (Manual):** any agent harness to paste the activation prompt into — no shell tooling
- **Door 1a (Bash):** Bash 4.0+ — standard on Linux/Mac/WSL
- **Door 3 (Skill):** **Claude Code** with the Skills capability enabled (this is the one method that depends on Claude Code specifically)
- **Door 1b/1c (secondary script variants):** See [Secondary and advanced options](#secondary-and-advanced-options)

## Pre-install decisions

Before ANY install method, decide:

### Decision 1: Edition

This package ships the **general-edition** — suited to software dev, research, writing, education, B2B SaaS, and enterprise contexts, with compliance preset flexibility (see Decision 2). HIPAA/PHI is out of scope for this edition.

(Every install method places `common-specs/` and `general-edition/` under `ultimate-memory-stack/` in your working directory — see your chosen method above for exact steps.)

### Decision 2: Compliance preset

| Preset | If you need |
|--------|-------------|
| **`none`** | No regulatory exposure (personal projects, hobby code, learning) |
| **`enterprise`** | Business-customer PII, SOC2 prep, GDPR awareness |
| **`custom`** | Multiple regulatory regimes (advanced — requires `overrides/compliance.override.md`) |

**Pick `none` if unsure.** You can change later — no need to commit upfront. Your choice (and any extensions from Decision 3) is written to `memory/user/USER_OVERRIDES.md` at install time — a file the installer creates once and never overwrites again; see "Compliance preset switching" below for changing it later.

### Decision 3: Extensions (general-edition only, optional)

Optional add-ons that compose with base preset (per `EXTENSIONS/`):
- `gdpr` — EU jurisdiction + consent tracking
- `soc2` — SOC2 Trust Services Criteria audit-ready evidence
- `pci-dss` — Payment card data context

**You can enable multiple.** Most users start with NONE.

### Decision 4: Consumer agent topology

If you have sub-agents (e.g., Warden, Sentinel, Vault, Clerk in an orchestrated setup), register them at the wizard. Otherwise, answer "none" — standard slots (`user`, `orchestrator`, etc.) cover everything.

### Decision 5: Deployment tier (auto-detected when possible)

You don't need to know this upfront — setup will detect. For reference:
- T0 = no infrastructure (everyone has this)
- T1 = + Ollama (semantic search)
- T2 = + Node.js (hybrid retrieval, graph backend)
- T3 = + Code Execution (cryptographic signatures, advanced compaction)
- T4 = + Skills + Anthropic Dreaming beta (full ideal state)

## Manual walkthrough

**Door 4 — Manual Drag-and-Drop.** Recommended when you don't have automation tooling installed (no Bash on Windows, no Python, no Skills), you prefer visual file management (Finder / Explorer / Files), you want to understand what's being deployed, or you're on Windows without WSL.

**This method requires only:** a file manager (Finder on Mac / File Explorer on Windows / Files on Linux) and an agent harness to paste the activation prompt into. NO shell commands needed.

### Total: 4 user actions, ~5 minutes

### Step 1 — Pick (or create) your working directory

This is where your memory stack will live. Examples:

| OS | Suggested working directory |
|----|-----------------------------|
| Mac | `~/Documents/my-memory-deployment/` or any project folder |
| Windows | `C:\Users\<you>\Documents\my-memory-deployment\` |
| Linux | `~/projects/my-memory-deployment/` |

Create this folder if it doesn't exist (right-click in your file manager → New Folder).

### Step 2 — Copy the package into the working directory via drag-and-drop

In your file manager:

1. **Create a folder named `ultimate-memory-stack`** inside your working directory.
2. **Open the source package location** (e.g., your local copy of the cloned `ultimate-memory-stack` package)
3. **Select `common-specs/`** — drag into the new `ultimate-memory-stack/` folder
4. **Select `general-edition/`** — drag into the new `ultimate-memory-stack/` folder

After this step, your working directory contains:

```
my-memory-deployment/
└── ultimate-memory-stack/
    ├── common-specs/         (the universal foundation)
    └── general-edition/      (the edition profile + overrides + setup)
```

(`memory/` is **your data vault** — it's created separately in Step 4, below. Keeping it out of `ultimate-memory-stack/` keeps your data and the package's own files from mixing.)

**Mac tip:** Use Finder; hold Option to copy (instead of move). Or use Cmd+C / Cmd+V.
**Windows tip:** Use File Explorer; Ctrl+Drag to copy. Or right-click → Copy → paste in working dir.
**Linux tip:** Use your file manager (Files / Nautilus / Dolphin) with same drag-and-drop semantics.

### Step 3 — Open your agent in the working directory

Open your agent harness with the working directory as its active context — e.g. run `claude` from that directory (Claude Code), open your OpenClaw workspace there, or use your harness's working-directory selector.

**Expected:** an agent session opens with your working directory as the active context.

### Step 4 — Paste the activation prompt + answer the setup wizard

Open `ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md`, copy the block under **## The Activation Prompt**, and paste it into your agent. That single paste tells the agent to do all the scaffolding — register the memory protocol (on Claude Code by copying it to `.claude/rules/memory_protocol.md`; on OpenClaw/other harnesses per their rules convention), initialize the `memory/` directory structure, set up audit log + quarantine per preset, and run the setup wizard.

> **Paste from the file, not from here.** `ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md` (the section labeled "## The Activation Prompt") is the single source of truth — paste from that file so you always get the current version. (Earlier guide revisions inlined the full prompt here; it was removed to prevent drift.)

**What your agent does next** (handles automatically — just confirm any permission prompts as they appear):
- Reads `MEMORY_PROTOCOL.md` from the `ultimate-memory-stack/common-specs/` folder
- Registers the protocol for auto-load (`.claude/rules/memory_protocol.md` on Claude Code; per-harness convention otherwise) and copies `MEMORY_PROTOCOL_EXTENDED.md` to `memory/MEMORY_PROTOCOL_EXTENDED.md` — an on-demand reference, never `.claude/rules/`
- Creates the `memory/` directory structure (9 subdirectories)
- Initializes `audit_log.jsonl` + `quarantine_log.jsonl` per preset
- Asks you the 6 setup-wizard questions
- Runs the T1–T9 self-test
- Greets you with a "Last session we [setup]…" message

### Done

After Step 4 completes (~3-5 minutes including answering wizard questions), your memory stack is operational.

**Verify with the next session:** Close your agent. Reopen it in the working directory. It should greet you with a "Last session we [setup]…" line. That confirms `session_state.md` was created properly.

### If something doesn't work

See [Troubleshooting](#troubleshooting). The most common issue is "my agent doesn't see the memory" — usually because the protocol file (`.claude/rules/memory_protocol.md` on Claude Code) wasn't created. Verify it exists in your working directory (you may need to enable "Show hidden files" in your file manager — `.claude/` starts with a dot).

## Bash install in depth

**Door 1a — `setup-memory-stack.sh`.** Use when you're on Mac, Linux, or WSL and want one-command install.

### Prerequisites for this method
- Bash 4.0+ (standard on Mac and Linux; WSL on Windows works too)
- The deployable package accessible
- Optional: Python 3.8+ + `cryptography` for T3+ cryptographic features

### Mac note

The setup scripts declare `#!/bin/bash`, so they run correctly under bash even though macOS defaults to zsh. If you see "permission denied", the execute bit isn't set — run `chmod +x` on the script, or invoke it as `bash <script>` (interpreter invocation doesn't require the execute bit).

### Steps

**Step 1: Navigate to your working directory** (where you want the stack installed — the install lands in the directory you run from):

```bash
cd /path/to/your-working-directory
```

**Step 2: Run the top-level setup script by its path:**

```bash
/path/to/ultimate-memory-stack/setup-memory-stack.sh                  # full install (all addons)
/path/to/ultimate-memory-stack/setup-memory-stack.sh --minimal       # core only (no addons)
/path/to/ultimate-memory-stack/setup-memory-stack.sh --addon memory-vault --addon memory-graphiti
                                                      # valid --addon values: memory-vault, memory-graphiti, memory-graphify, memory-llmlingua
/path/to/ultimate-memory-stack/setup-memory-stack.sh --no-templater  # skip Obsidian Templater auto-enable
/path/to/ultimate-memory-stack/setup-memory-stack.sh --compliance=enterprise --extensions=soc2,gdpr
/path/to/ultimate-memory-stack/setup-memory-stack.sh --migrate-from=v2.0
/path/to/ultimate-memory-stack/setup-memory-stack.sh --target ~/my-workspace   # explicit target
/path/to/ultimate-memory-stack/setup-memory-stack.sh --yes          # non-interactive (accept defaults)
/path/to/ultimate-memory-stack/setup-memory-stack.sh --help          # full flag list
```

The script confirms the install target interactively (auto-detecting an OpenClaw workspace if present), refuses to install into its own package directory, refreshes only product-owned files on re-install (your `memory/` data is never touched), and writes a `.ums-manifest.json` recording what it did.

> Advanced: `general-edition/setup.sh` can be run directly (`cd general-edition && ./setup.sh`); it accepts the same pass-through flags plus `--verify`, `--status`, and `--change-preset=<preset>`.

**Expected output (default preset `none`):**

```
==========================================
Ultimate Memory Stack — General-Edition Setup
Version: 4.0.1
Working directory: <working-dir>
Compliance preset: none
Extensions: none
Mode: fresh-install
==========================================

→ Copying memory stack files...
ℹ️  Audit log: OPT-IN (compliance: none — default OFF)
   Enable later via PROFILE.md edit: audit_log: true
✓ Memory directory structure initialized
✓ Deployment-info marker written to <working-dir>/.deployment-info

==========================================
✓ General-edition setup complete
==========================================

Effective tier detection:
  Node.js:      available  (T2 features active)
  cryptography: NOT installed  (T3 signatures dormant)
  Ollama:       NOT installed  (T1 semantic dormant)

Next steps:
  1. cd <working-dir>
  2. Open your agent harness in this directory (e.g. Claude Code or OpenClaw)
  3. Paste activation prompt from:
     <working-dir>/ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md
  4. Answer setup wizard
```

(Tier-detection lines vary by machine. With `--compliance=enterprise|custom` the audit-log lines become "✓ Audit log initialized for compliance: `<preset>`".)

**Step 3: Open your agent + paste activation prompt + answer wizard**

Same as Door 4 Step 4.

**Step 4: Verify:**

```bash
/path/to/ultimate-memory-stack/verify.sh    # run from the working directory; or pass it as an argument
```

Expected: ends with `✅ All checks passed — Ultimate Memory Stack v4.0.1 install is valid.` If anything fails, see [Troubleshooting](#troubleshooting).

**Total time: ~30 sec for script + ~2-3 min for wizard.**

### Version control (`.gitignore`)

When you install into a directory that is already a git repo, the script and Python installers append a fenced block to your `.gitignore`:

```gitignore
# >>> ultimate-memory-stack >>>
ultimate-memory-stack/
.deployment-info
.ums-manifest.json
# <<< ultimate-memory-stack <<<
```

This ignores the regenerable vendored package + the install markers. Your `memory/` vault is **deliberately left tracked** — it's your data; commit it if you want history. The block is idempotent (re-installs never duplicate it) and is added only when a `.git/` directory is present.

## Claude Code Skill installer

> **Claude Code only.** This is the one install method that requires Claude Code specifically — the manual, script, and agent doors work on any harness (or none). Use it when you have Skills enabled in Claude Code and want the native slash-command experience.

**Status:** ✅ **AVAILABLE** — the install skill ships in `skills/install-ultimate-memory-stack/` (see `skills/install-ultimate-memory-stack/INSTALL_SKILL.md` for how to register the skill itself; STABLE — current version and history in `SKILL.md`'s changelog).

### What the install looks like

```
> /install-ultimate-memory-stack

Welcome to the Ultimate Memory Stack installer.

Edition? [general]: general

Compliance preset? [none / enterprise / custom]: none

Extensions? (comma-separated, or 'none'): none

Consumer agent topology? (list agent names, or 'none'): none

[The skill handles everything else automatically]

✓ Files copied to working directory
✓ memory_protocol.md installed to .claude/rules/
✓ Memory directory structure initialized
✓ Setup wizard complete

Self-test: All T1–T9 checks passed.

Your memory stack is operational. Type any message to begin.
```

### Why this is the easiest method (when you're on Claude Code)

- **1 user action:** type `/install-ultimate-memory-stack`
- **Auto-prompted decisions:** edition + preset + extensions + topology all via inline UI
- **No file management:** the skill handles all file operations
- **Native Claude Code UX:** consistent with other skill-based workflows
- **Security-reviewed:** the skill passed security review before release

### What this method requires

- Claude Code with Skills capability enabled

**Total time: ~30 seconds + wizard prompts.**

## Multi-machine deployment

If deploying to multiple machines (e.g., a desktop and a laptop, or team-member setups):

### Pattern: Independent per-machine deployments

Each machine is independent. Memory entries do NOT auto-sync (single-deployment scope by design).

**Steps per machine:**
1. Copy `common-specs/` + your chosen edition to the target machine (drag-and-drop via shared folder; git clone; archive transfer)
2. Run your preferred install method on that machine
3. Setup wizard runs per machine — user profile + projects + topology may differ

### Pattern: Source-of-truth + work mirror

Used when you want **one canonical location** + working mirrors on multiple machines.

**Setup pattern:**
- **Canonical location** — a stable, slow-changing location (network share, backed-up drive, git repo origin, removable drive). Houses the master copy of the `ultimate-memory-stack/` package.
- **Mirror locations** — each working machine has a copy at a consistent logical path.
- **Drift detection** — byte-parity verification via file size / hash comparison.

**Pick paths that fit YOUR environment.** Common patterns:
- Canonical on a network share, mirrors on local SSDs of each machine
- Canonical on an external drive, mirrors on internal drives
- Canonical in a private git repo, mirrors via `git clone` per machine
- Canonical on one local drive, mirror on another (single-machine setup)

For other deployments without explicit mirroring, just keep ONE canonical source and copy from there as needed.

## Post-install verification in depth

After ANY install method, verify these:

> **Two test namespaces, same `T#` prefix — don't conflate them.** `verify.sh` runs its own **[T1]–[T7] structural install-checks** (scaffold, registration, profile, logs). The protocol's **T1–T9 self-test** (`common-specs/MEMORY_PROTOCOL.md` §1.3) is a different, entry-level suite the agent runs each session over your memory entries. The shared prefix does not map 1:1.

### Verification A: Self-Test (T1–T9)

**Manual-install users:** Just confirm the activation prompt's self-test passed (your agent reports it inline).

**Script users** (and any method, from the package root):
```bash
./verify.sh                      # run from the working directory
./verify.sh /path/to/working-dir # or pass the working directory as an argument
```

**Skill users:** the install skill runs the self-test as its final step and reports results inline; you can also run `verify.sh` above at any time.

**Expected output (verify.sh, preset `none`):** sectioned `[T1]`–`[T7]` checks (memory dirs, edition profile, audit logs per preset, common-specs, registered skills, bootstrap prompt), ending with:
```
✅ All checks passed — Ultimate Memory Stack v4.0.1 install is valid.
```

(The edition-level alternative `general-edition/setup.sh --verify` prints a shorter check: T1/T2 lines, an audit-log status line, and a "Deployment tier:" section.)

All checks green = good. Any failure = see [Troubleshooting](#troubleshooting).

### Verification B: Session greeting

Close your agent. Reopen it in the working directory.

**Expected:** your agent greets you with "Last session we [setup]. Ready to continue with [active project] or work on something else?"

If you DON'T see this, the protocol file (`.claude/rules/memory_protocol.md` on Claude Code) isn't being auto-loaded. See [Troubleshooting](#troubleshooting).

### Verification C: Memory write test

Ask your agent: "Remember that my preferred test framework is jest."

**Expected:** your agent writes an entry. Verify by opening `memory/feedback/feedback.md` — should see a markdown entry with YAML frontmatter (id, dates, source_agent: user) and content mentioning jest.

### Verification D: PII detection (`enterprise` preset or `gdpr` extension only)

With the `enterprise` preset (or `gdpr` extension) active, say: "Test detection: my fake customer SSN is 123-45-6789 (testing only)."

**Expected:** your agent flags the PII, routes the entry to quarantine (non-blocking toast notification), and the audit log captures the attempt.

## Migration v2.0 to v3.x

If you have an existing v2.0 memory stack:

**Pre-migration:**
1. **Backup `memory/` directory.** Drag-and-drop a copy to a safe location, name it `memory.backup.v2.<date>/`.
2. **Read your edition's `MIGRATION_v2_to_v3.md`** for edition-specific safeguards.

**Run migration** (pick a method):

```bash
# Door 1a (Bash)
./setup.sh --migrate-from=v2.0 --backup-location=memory.backup.v2.$(date +%Y%m%d-%H%M%S)

# Door 4 (Manual) — copy the package in as ultimate-memory-stack/ alongside your v2.0 memory/, then paste the activation prompt
# (Activation prompt at BOOTSTRAP_PROMPT.md handles migration if v2.0 is detected)
```

**What happens:**
1. Backup created
2. v2.0 entries get YAML frontmatter added (legacy fields preserved)
3. Audit log initialized (general per preset)
4. Quarantine directory initialized
5. Re-validation pass on legacy entries — failures route to quarantine
6. PROFILE.md created with selected preset

**Post-migration:**
1. Review quarantine queue (entries from re-validation)
2. Verify with self-test
3. Test a few memory writes
4. Keep backup until confident; then optionally remove

**Migration is non-destructive** — backup preserves v2.0 for full rollback.

## Troubleshooting

### Symptom: "My agent doesn't reference memory at session start"

**Cause:** the protocol file (`.claude/rules/memory_protocol.md` on Claude Code) isn't auto-loaded.

**Fix:**
1. Verify the file exists at `<working-dir>/.claude/rules/memory_protocol.md` (you may need to show hidden files); on OpenClaw/other harnesses, confirm the protocol is referenced from your harness's rules/bootstrap
2. Verify your agent is running from the working directory (not a parent)
3. If the activation prompt was used: manually paste it again — your agent should re-create the file

### Symptom: Setup script (Door 1a) fails with "common-specs not found"

**Cause:** You ran the setup script from the wrong directory.

**Fix:** Run from inside the edition's directory (`cd general-edition && ./setup.sh`). The script expects `../common-specs/` to exist.

### Symptom: Door 1a fails on Mac with "permission denied"

**Cause:** Execute bit not set on the script.

**Fix:** Run `chmod +x <script>` then re-run, or invoke it as `bash <script>` (interpreter invocation doesn't require the execute bit).

### Symptom: "Audit log MISSING" (compliance preset enterprise/custom)

**Cause:** These presets enable the audit log by default; setup should have created it. (With preset `none` the audit log is OPT-IN — a missing log is normal, not an error.)

**Fix:** Re-run setup, OR manually create:
- Drag-and-drop create empty file `memory/security/audit_log.jsonl` (any text editor — save empty file)
- Drag-and-drop create empty file `memory/quarantine/quarantine_log.jsonl`

### Symptom: PII detection misfiring (false positives)

**Cause:** Layer 2 patterns may be too aggressive for your context.

**Fix:** Tune the active detection patterns (`common-specs/detection_patterns_<preset>.md`, or `general-edition/overrides/generic-examples.override.md`) to your formats. Run verify after.

### Symptom: Quarantine queue growing without review

**Cause:** Detection firing on legitimate content.

**Fix:**
- Run `/audit-quarantine` to review the queue
- Detection patterns may need tuning OR change preset to less aggressive

### Symptom: Compliance preset 'custom' rejected at install

**Cause:** The `custom` preset requires `overrides/compliance.override.md` with ≥1 explicit override.

**Fix:** Create `general-edition/overrides/compliance.override.md` with at least one section override. See `general-edition/overrides/compliance-presets.override.md` §5.4 for example.

### Symptom: Setup wizard never completed

**Cause:** Interrupted; activation prompt not pasted.

**Fix:** Re-paste activation prompt from `BOOTSTRAP_PROMPT.md`. Wizard re-runs from where it stopped.

## Edition switching

This package ships the **general-edition** only. HIPAA/PHI is out of scope for this edition. For day-to-day regulatory tuning within the general-edition, use compliance-preset switching (next section) rather than an edition change.

Edition is a structural choice — not a simple preset change. When a future edition becomes available, the recommended path between editions would be:
1. Backup current deployment: copy `memory/` to `memory.backup.<date>/` via drag-and-drop
2. Run a fresh install with the target edition
3. Manually port memory entries from backup, then re-verify detection under the new edition's posture
4. Test thoroughly before discarding backup

**There's no automated `--change-edition`** — intentional, since editions have fundamentally different compliance posture.

## Compliance preset switching

(General-edition only.) **To change preset on an existing general-edition deployment:**

```bash
# Door 1a (Bash) / Door 1b (PowerShell) / Door 1c (Python)
./setup.sh --change-preset=enterprise

# Door 4 (Manual) — edit memory/user/USER_OVERRIDES.md directly (NOT PROFILE.md —
# PROFILE.md is regenerable as of v4.0.0 and a hand-edit to it will not survive
# the next install/upgrade; see "Customizing your configuration" in USER_GUIDE.md)
# Uncomment/add the line "compliance: <new>". Save the file. Next agent session
# re-validates entries against the new patterns.
```

**What happens (Door 1a/1b/1c):**
1. `memory/user/USER_OVERRIDES.md` backed up automatically
2. `USER_OVERRIDES.md` updated with the new preset (created first if it didn't exist yet)
3. Audit log captures the change
4. Existing entries re-validated against new patterns at next session
5. Failed validations route to quarantine

**This is reversible** — change back with the same command.


## Uninstall and cleanup

To completely remove the memory stack from a working directory:

**Door 4 (Drag-and-drop, all OSes):**
1. **Backup first** if you want to preserve memory: drag `memory/` to a backup location named `memory-stack-backup-<date>/`
2. Delete `memory/` directory
3. Delete the `ultimate-memory-stack/` folder (or, for older installs that copied them to the workspace root, the `common-specs/` and `general-edition/` directories)
4. Remove the protocol registration: on Claude Code delete `.claude/rules/memory_protocol.md` (the rest of `.claude/` may have other rules — only delete `memory_protocol.md`); on OpenClaw/other harnesses, remove the protocol reference from your harness's rules/bootstrap instead

**Door 1a (Bash):**
```bash
# Backup first
cp -r memory/ ~/memory-stack-backup-$(date +%Y%m%d-%H%M%S)/

# Remove everything
rm -rf .claude/rules/memory_protocol.md      # Claude Code; other harnesses: unhook the protocol per your convention
rm -rf memory/
rm -rf common-specs/ general-edition/ ultimate-memory-stack/   # whichever of these your install method copied here
```

**Caution:** Once removed, memory entries are gone unless backed up.

## Getting help

- **General questions:** Read `common-specs/USER_CHEAT_SHEET_core.md` first; then your edition's addendum
- **Architecture questions:** Read `common-specs/ARCHITECTURE.md`
- **Compliance / preset questions:** Read `common-specs/SCHEMA_compliance_profile.md` + your edition's `PROFILE.md`
- **Migration questions:** Read your edition's `MIGRATION_v2_to_v3.md`
- **Privacy/IP questions:** Read your edition's `PRIVACY_REVIEW.md`
- **Modularity questions:** Read `common-specs/MODULARITY.md`
- **The activation prompt:** [`common-specs/BOOTSTRAP_PROMPT.md`](common-specs/BOOTSTRAP_PROMPT.md)
- **Operational rules:** `common-specs/MEMORY_PROTOCOL.md`

## Secondary and advanced options

These methods exist but are NOT the recommended path for most users.

### Door 1b — PowerShell `setup-memory-stack.ps1` (Windows)

**Status:** The core install DELEGATES to Python — requires Python 3.8+ in PATH. This means a fresh Windows user without Python can't use it as a true "Windows-native" option.

**When to use:** You're on Windows AND have Python installed AND prefer PowerShell over a Python prompt.

**Prerequisites:**
- PowerShell 5.1+ (standard on Windows 10+)
- Python 3.8+ in PATH
- Execution policy allowing local scripts:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

**Steps** (run from your working directory — the install lands in the directory you run from):
```powershell
cd "<path to your working directory>"
& "<path to>\ultimate-memory-stack\setup-memory-stack.ps1"
# Or with options:
& "<path to>\ultimate-memory-stack\setup-memory-stack.ps1" -Compliance enterprise -Extensions "soc2,gdpr"
# Flags: -Edition, -Minimal, -Addon, -NoTemplater, -Compliance, -Extensions, -MigrateFrom, -SkipWizard, -Help
```

**Future plan:** Rewrite the PowerShell path as native PowerShell (no Python dependency) — promote to a primary install method for Windows users without Python.

### Door 1c — Python `setup.py` (Cross-platform advanced)

**When to use:**
- You're a developer with Python 3.8+ already installed
- You want T3+ cryptographic key generation built into install
- You want the most feature-complete setup automation

**Prerequisites:**
- Python 3.8+ (`python3 --version`)
- Optional: `cryptography` package (`pip install cryptography`) for HMAC key generation at T3+

**Steps** (run from your working directory — `setup.py` installs into the current directory by default; the `WORKING_DIR` env var or `--working-dir` flag override it):

```bash
cd /path/to/your-working-directory

# Default install (compliance preset: none)
python3 /path/to/ultimate-memory-stack/general-edition/setup.py

# With options
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --compliance=enterprise --extensions=soc2,gdpr

# Generate an HMAC secret (T3+). NOTE: signing itself is NOT IMPLEMENTED —
# nothing reads this secret yet; it only pre-provisions a key.
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --generate-hmac-secret

# Other flags
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --help
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --verify
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --change-preset=enterprise
```

**T3+ crypto key generation path:**

⚠️ Entry signing is **NOT IMPLEMENTED** in this release — nothing signs a memory entry and nothing verifies a signature. The command below only generates and stores a secret for future use.

When Code Execution + the `cryptography` package are available, this method generates an HMAC secret at install:

```bash
python3 setup.py --generate-hmac-secret
```

**Action required after generation:** store the secret in your password manager. (Stronger offline-key entry signing is not implemented in this release.)

**Total time for Doors 1b / 1c: ~30 sec setup + ~2-3 min wizard.**

## Recommended addons and core skills

> These components ship as part of v4.0.0.

### What the addons add beyond the base stack

After the base stack install (any door above), the package includes **6 additional components**:

| # | Component | Path | Tier | Time |
|---|---|---|---|---|
| 1 | **Obsidian vault config** | `recommended-addons/obsidian-vault-config/` | B | ~5 min after Obsidian app installed |
| 2 | **LLMLingua installer** | `recommended-addons/llmlingua-installer/` | C (opt-in) | ~10 min |
| 3 | **Graphiti installer** | `recommended-addons/graphiti-installer/` | C (opt-in) | ~15 min |
| 4 | **Graphify installer** | `recommended-addons/graphify-installer/` | C (opt-in) | ~10 min |
| 5 | **Audit Quarantine Skill** | `core/audit-quarantine-skill/` | A | auto-available |
| 6 | **OpenClaw General Edition Adapter** | `core/openclaw-adapter/` | A (for OpenClaw target) | ~15 min |

### Per-component quick reference

| # | Skill command | Vetting | Critical note |
|---|---|---|---|
| 1 | `/config-obsidian-vault` | n/a (config-only) | Install Obsidian app from https://obsidian.md/ first |
| 2 | `/install-llmlingua` | Security-reviewed | Exact pin `llmlingua==0.2.2`; planned migration → SecurityLingua in a future release |
| 3 | `/install-graphiti` | Security-reviewed | Set `GRAPHITI_TELEMETRY_ENABLED=false` BEFORE first import; CVE-2026-32247 patched at 0.28.2 (installer floor-pins ≥0.29.1); Kuzu backend recommended |
| 4 | `/install-graphify` | Security-reviewed | Pin `graphifyy==0.8.21` (DOUBLE-y); single-y `graphify` is a blocked typosquat — the Python *module* is single-y by upstream design, but the distribution + CLI are double-y; home page: github.com/safishamsi/graphify |
| 5 | `/audit-quarantine` | n/a (built-in) | One-line toast at session start; full review workflow available via the skill |
| 6 | `/install-openclaw-adapter` | n/a (built-in) | Requires OpenClaw harness installed at target; adapter generates 9 root files |

### Install order recommendation

```
1. Obsidian vault config (#1)   — easiest, no Python install
2. LLMLingua installer (#2)     — independent, smallest surface
3. Graphiti installer (#3)      — independent, LLM provider decision
4. Graphify installer (#4)      — independent, L1 bash-guard config
5. OpenClaw adapter (#6)        — only if deploying to OpenClaw harness
```

Audit-Quarantine (#5) auto-available; use `/audit-quarantine` when needed.

### Two install modes per addon

| Mode | How | Pros | Cons |
|---|---|---|---|
| **A. Claude Code Skill** | Copy folder to `~/.claude/skills/` → restart Claude Code → `/install-<addon>` | Structured + logged + error-checked | Requires Skills capability |
| **B. Manual standalone** | `cd <addon>-installer/` + follow `INSTALL_<NAME>.md` | No Claude Code prerequisite | Manual log discipline required |

Both produce identical installed state.

### Post-install validation (after all installs)

After installing addons, run each addon's smoke test, then re-run the base verification (`./verify.sh` from the package root, or [Verification A](#post-install-verification-in-depth)) to confirm the stack is still healthy. If you deploy to multiple machines, also verify that a memory entry written on one machine is readable on another.

## Design principles

This guide follows the project's standing documentation principles:
- **Ideal-first design with tier markers** — document the full feature set; mark what each tier requires
- **Prescriptive documentation** — leave nothing up for guesses
- **Modular consumer architecture** — common-specs foundation + edition overlays, composing without core modification
- **Four first-class doors** — script, agent (`INSTALL_AGENT.md`), marketplace/skill, and manual are all first-class; PowerShell / Python are secondary
