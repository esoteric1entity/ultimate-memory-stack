---
file: QUICKSTART
title: "Memory Branch — Quickstart (5-minute tour)"
branch: memory
audience: anyone who just installed UMS
license: Apache 2.0
---

# Quickstart — Memory Branch (Ultimate Memory Stack)

Welcome! If you just installed UMS (general-edition), this 5-minute tour shows you what it does and how to use it. For the long-form guide, see [`USER_GUIDE.md`](./USER_GUIDE.md). For the install steps, see [`INSTALL.md`](./INSTALL.md).

> **OpenClaw user?** The OpenClaw adapter generates a different surface (9 root
> files — `MEMORY.md`, `HEARTBEAT.md`, etc.). Its tour lives at
> [`core/openclaw-adapter/QUICKSTART.md`](./core/openclaw-adapter/QUICKSTART.md).
> This tour covers the Claude Code / generic layout.

## What UMS does (in one sentence)

UMS gives your AI agent **persistent memory with a decision log, feedback trail, and per-project memory banks** — so it can pick up where it left off in any session and remember what worked, what didn't, and why.

## What you got

The **installer** scaffolds; the **activation wizard** populates. Right after install you have:

| Path | Purpose |
|---|---|
| `memory/` | Your data vault — nine empty directories: `sessions/ decisions/ feedback/ projects/ security/ references/ user/ archive/ quarantine/` |
| `.claude/rules/memory_protocol.md` | The memory protocol, registered so Claude Code auto-loads it (OpenClaw and other harnesses register it per their convention — see `core/openclaw-adapter/`) |
| `.claude/skills/<name>/SKILL.md` | The addon installer Skills you selected (`/install-graphiti`, `/install-graphify`, `/install-llmlingua`, `/config-obsidian-vault`) — Claude Code skill door; the script/agent/manual doors (incl. OpenClaw) scaffold the same addons without registering Claude skills |
| `.ums-manifest.json` | Exactly what the installer did (door, harness, addons) |
| `.deployment-info` | Completion certificate — present only if install finished |
| `ultimate-memory-stack/` | The package itself (specs, templates, editions) — code, not your data |

Then you paste the activation prompt from `ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md` into your agent, answer the wizard, and it creates the two living files everything orbits:

- **`memory/MEMORY_INDEX.md`** — master index; what your agent reads first to "wake up"
- **`memory/sessions/session_state.md`** — where you left off (the lifeline)

## The 5-minute tour

### Minute 1 — Run the wizard (if you haven't)

Open your agent in the workspace and paste the activation prompt from
`ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md`. It asks a few
questions (name, role, preferences) and seeds the vault.

### Minute 2 — Look at the index and the lifeline

*(These two files are created by the wizard in Minute 1 — if you skipped it,
you'll get "No such file" here; run the activation prompt first.)*

```bash
cat memory/MEMORY_INDEX.md
cat memory/sessions/session_state.md
```

The index lists every memory category with entry counts and pointers. The
session state shows what you and your agent were doing, what's in progress,
and the next actions — it's the first thing read at session start (protocol
checks T1/T2 fail loudly if either file goes missing).

### Minute 3 — See how a decision is recorded

Durable decisions live in `memory/decisions/decisions.md` as `DEC-###`
entries following the **5-element discipline** — the shipped template is
`ultimate-memory-stack/common-specs/templates/decisions.template.md`:

```markdown
## DEC-001: Adopt X over Y

**Purpose:** [What this enables / why we need it]

**Rationale:** [Why this approach over alternatives]

**Sound reasoning:** [Evidence chain backing this]

**Scope — CAN:**
- [what this decision enables]

**Scope — CANNOT:**
- [what it does NOT cover]
```

Your agent writes these as decisions happen; the lint pipeline flags entries
missing the 5 elements.

### Minute 4 — Feedback and project banks

- Corrections and preferences go to `memory/feedback/` as `FB-###` entries
  (template: `templates/feedback.template.md`).
- Per-project working memory goes to `memory/projects/<project-name>/`
  (spec: `common-specs/SCHEMA_A3_per_project_memory_bank.md`; templates:
  `templates/memory_bank/`).

### Minute 5 — Know the lint exists

The Memory branch ships a hygiene linter that **surfaces** problems for human
review (it never auto-mutates content) — it runs from the cloned package, not
the installed scaffold (the scaffold doesn't include `core/`):

```bash
python3 /path/to/ultimate-memory-stack/core/openclaw-adapter/scripts/lint_runner.py <YOUR_WORKSPACE>
```

It auto-detects your vault shape (Claude Code via `.claude/rules/`, OpenClaw
via `.openclaw/`) and checks frontmatter, ID numbering, doc completeness, and
quarantine triggers.

## What's next?

1. **Just use it.** Start a session; your agent reads the index + session
   state and resumes with context.
2. **Read [`USER_GUIDE.md`](./USER_GUIDE.md)** for decision capture, feedback
   flow, and project memory banks in depth.
3. **Install the addons you skipped** — each addon self-installs when invoked:
   on Claude Code as a slash command (`/install-graphiti` for the knowledge
   graph, `/install-graphify` for the code symbol graph, `/install-llmlingua`
   for prompt compression, `/config-obsidian-vault` for the GUI vault view);
   via the script, agent, or manual doors (including OpenClaw) the same addons
   scaffold directly. The script and agent doors register them automatically;
   if you installed via the marketplace, copy the addon `SKILL.md` files first
   — see the addon section of [`INSTALLATION_GUIDE.md`](./INSTALLATION_GUIDE.md).

## Common gotchas

- **"My agent doesn't load context at session start"** — confirm
  `.claude/rules/memory_protocol.md` exists (Claude Code) or your harness
  references the protocol from its rules/bootstrap. Re-run `verify.sh` to
  check registration.
- **"verify.sh says the wizard hasn't run"** — that's accurate until you
  paste the activation prompt; the installer deliberately ships an empty
  vault and never invents data.
- **"I want my own schema"** — per-project memory banks
  (`common-specs/SCHEMA_A3_per_project_memory_bank.md`) are the extension
  point; they live under `memory/projects/<project-name>/`.

## Cross-references

- [`USER_GUIDE.md`](./USER_GUIDE.md) — long-form usage
- [`INSTALL.md`](./INSTALL.md) — install guide (four doors)
- [`INSTALLATION_GUIDE.md`](./INSTALLATION_GUIDE.md) — full multi-method install
- [`common-specs/MEMORY_PROTOCOL.md`](./common-specs/MEMORY_PROTOCOL.md) — the master protocol doc
- [`common-specs/SCHEMA_A18_per_entry_metadata.md`](./common-specs/SCHEMA_A18_per_entry_metadata.md) — frontmatter spec
- [`core/openclaw-adapter/QUICKSTART.md`](./core/openclaw-adapter/QUICKSTART.md) — the OpenClaw tour
