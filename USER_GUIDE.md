---
file: USER_GUIDE
title: "Memory Branch — User Guide (long-form usage)"
branch: memory
audience: anyone using UMS day-to-day
license: Apache 2.0
---

# User Guide — Memory Branch (Ultimate Memory Stack)

This is the long-form usage guide for the Memory branch (UMS — general-edition). For install, see [`INSTALL.md`](./INSTALL.md). For a 5-minute tour, see [`QUICKSTART.md`](./QUICKSTART.md).

## Table of contents

1. [How UMS thinks about memory](#1-how-ums-thinks-about-memory)
2. [The 5 entry types](#2-the-5-entry-types)
3. [Per-project memory banks](#3-per-project-memory-banks)
4. [Session state + heartbeat](#4-session-state--heartbeat)
5. [The lint + quarantine pipeline](#5-the-lint--quarantine-pipeline)
6. [The security hooks](#6-the-security-hooks)
7. [Obsidian GUI (optional)](#7-obsidian-gui-optional)
8. [Graphiti knowledge graph (optional)](#8-graphiti-knowledge-graph-optional)
9. [Troubleshooting](#9-troubleshooting)
10. [When to escalate to a DEC](#10-when-to-escalate-to-a-dec)

## 1. How UMS thinks about memory

UMS treats memory as a **layered structure**:

```
┌─────────────────────────────────────────┐
│  MEMORY.md (master index, ALWAYS read)  │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│  HEARTBEAT.md (current state, 3-deep)   │
│  BOOTSTRAP.md (next-actions handoff)    │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│  Daily log (chronological session log)  │
│  Decisions (architectural)              │
│  Learnings (patterns, gotchas)          │
│  Feedback (user corrections)            │
│  Vetting (security decisions)           │
└─────────────┬───────────────────────────┘
              ▼
┌─────────────────────────────────────────┐
│  Per-project memory banks (deep dive)   │
│  References (external pointers)         │
│  Quarantine (held for review)           │
└─────────────────────────────────────────┘
```

*(The root-file names shown — `MEMORY.md`, `HEARTBEAT.md`, `BOOTSTRAP.md` — are the OpenClaw-adapter surface; on the Claude Code default install the same layers live in `memory/MEMORY_INDEX.md` and `memory/sessions/session_state.md`.)*

**Reading order at session start:** MEMORY.md → HEARTBEAT.md → BOOTSTRAP.md → relevant daily log → relevant decision/learning entries *(OpenClaw adapter; on the Claude Code default: `memory/MEMORY_INDEX.md` → `memory/sessions/session_state.md` → relevant entries)*.

## 2. The 5 entry types

Every entry in UMS has a type and follows a schema. The 5 main types:

### DEC-### (Decisions)

Architectural choices that the agent makes with rationale. Numbered sequentially. **5-element discipline** is mandatory:

1. **Purpose** — what this decision is for
2. **Rationale** — why this approach over alternatives
3. **Sound reasoning** — what tradeoffs were accepted
4. **Scope CAN** — what this decision enables
5. **Scope CANNOT** — what this decision does NOT do

See `common-specs/MEMORY_PROTOCOL.md` §6 for the full spec and examples.

### LEARN-### (Learnings)

Captured insights. Less formal than DEC, but follows a similar shape. Used for "I wish I'd known this earlier" moments. Tags for searchability.

### FB-### (Feedback)

User corrections or preferences. Promotes to a standing rule when pattern_count >= 5. The promotion is logged in `decisions.md` and creates a new DEC entry.

### VET-### (Vetting)

Security vetting decisions for new tools/skills. Mandatory under the stack's security-first standing rule. Each entry has: tool name, version, vetting method, finding severity, recommendation, sign-off.

### Session continuity entries

`memory/sessions/session_state.md` — the lifeline. Carries where you left off
(current task, files in flight, blockers, next actions) in a rolling heartbeat
section, plus recent-session history. Protocol check T1 fails loudly if this
file goes missing. *(The OpenClaw adapter additionally maintains per-day logs
at `memory/daily/YYYY-MM-DD.md` — that surface is documented in
`core/openclaw-adapter/`.)*

## 3. Per-project memory banks

If you have multiple projects, each gets its own memory bank — the layout
follows the widely-adopted 6-file Cline Memory Bank convention
(`common-specs/SCHEMA_A3_per_project_memory_bank.md`; templates ship in
`common-specs/templates/memory_bank/`):

```
memory/projects/
├── project_context.md                ← GLOBAL: index of all projects
└── <project-slug>/
    └── memory-bank/
        ├── projectbrief.md           (foundation)
        ├── productContext.md         (semantic — what/why)
        ├── systemPatterns.md         (semantic — how — architecture)
        ├── techContext.md            (semantic — what tech)
        ├── activeContext.md          (operational — current focus)
        └── progress.md               (operational — status, known issues)
```

Why separate? So the agent doesn't confuse cross-project context. When you start a session on project-alpha, the agent reads only that project's bank, not the full memory tree.

## 4. Session state + heartbeat

**`memory/sessions/session_state.md`** holds the current state in a rolling heartbeat window (oldest slices archive to `memory/archive/`). It captures:

- Current task + sub-step + files in flight + blocker
- Last 1-2 prior heartbeats
- Open items for next session
- Carried-forward decisions + their status

To mitigate long-context attention rot, the protocol pins the heartbeat at BOTH the start and end of the bootstrap injection (see MEMORY_PROTOCOL.md §2.5).

*(On the OpenClaw adapter the same concepts surface as root files — `HEARTBEAT.md` with a compactor, per-day `memory/daily/` logs, and a `BOOTSTRAP.md` entry point. See `core/openclaw-adapter/QUICKSTART.md`.)*

## 5. The lint + quarantine pipeline

UMS has a lint pipeline that you run manually (or wire into a hook of your choice) — it runs from the cloned package, not the installed scaffold (the scaffold doesn't include `core/`):

```bash
python3 /path/to/ultimate-memory-stack/core/openclaw-adapter/scripts/lint_runner.py <YOUR_WORKSPACE>
```

(It auto-detects your vault shape — Claude Code via `.claude/rules/`, OpenClaw via `.openclaw/`.)

It checks:
- **SCHEMA_A18 frontmatter** on every entry (every .md file with a DEC/LEARN/FB/etc. type must have the right frontmatter)
- **Numbering consistency** (DEC-001 exists, DEC-002 exists, no gaps unless intentional)
- **Path consistency** (mirror paths use the correct format)
- **Quarantine triggers** (PII detected → move to quarantine/)

The lint is **non-mutating** by default. It surfaces problems for human review; the user decides what to act on. (Per the design principle: "Karpathy Lint surface-only".)

## 6. The security hooks

The Memory branch doesn't ship its own security hooks — it relies on the **Security branch (agent-shield)** for that. If you have the Security branch installed, the hooks automatically check every file write the agent makes:

- RED tier: hard blocks (e.g., modifying the agent's own settings)
- YELLOW tier: prompts the user (e.g., modifying decision log files)
- GREEN tier: silent pass

Install the Security branch for production-shape deployments — it ships as its own package, `agent-shield` (release imminent); either package works alone, and they compose when both are installed.

## 7. Obsidian GUI (optional)

The Memory vault is a directory of markdown files — Obsidian reads it as a vault. To use the GUI:

1. Install Obsidian: https://obsidian.md/download
2. Open Obsidian → "Open folder as vault" → point at `<YOUR_WORKSPACE>/memory/`
3. Obsidian reads the frontmatter, renders the markdown, and provides:
   - Graph view (visualizes the decision/learn links)
   - Backlinks (shows where each entry is referenced)
   - Search across all entries
   - Tags filter

Recommended add-on: `recommended-addons/obsidian-vault-config/` provides pre-configured community plugins + hotkeys for the UMS vault.

## 8. Graphiti knowledge graph (optional)

For a real knowledge graph (entities + relationships, time-aware), install Graphiti:

```bash
# After Memory branch is installed
cd recommended-addons/graphiti-installer
# Follow the installer skill
```

Graphiti ingests the decisions + learnings as Episodic nodes, extracts entities, and lets you query "what does the agent know about X" via natural language.

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Agent doesn't read MEMORY.md at start (OpenClaw-adapter installs) | Harness doesn't have a "load context" hook | Add a `SessionStart` hook in your harness config |
| `lint_runner.py` reports `SCHEMA_A18 missing` | Entry was written without frontmatter | Add frontmatter (see SCHEMA_A18 spec) |
| Heartbeat stale (more than 2 sessions old; OpenClaw-adapter installs) | Heartbeat compactor isn't running | Manually update HEARTBEAT.md; check compactor cron |
| `git log` shows duplicate entries | Two agents wrote the same DEC simultaneously | Merge, dedupe, add cross-ref |
| `quarantine/` keeps growing | Lint is detecting content that needs review | Review and either move back to memory/ or delete |

## 10. When to escalate to a DEC

**Use a DEC when:**
- The choice affects the project architecture (adds/renames a component, changes a protocol)
- The choice has tradeoffs worth documenting for future agents
- The choice is a "standing rule" that future work should follow
- The choice is irreversible (or expensive to reverse)

**Don't use a DEC when:**
- It's a one-off decision in a single session
- It's a tactical choice (e.g., "use sed instead of awk for this one-liner")
- The choice has no tradeoffs (only one reasonable option)

The threshold: would you want a future agent to know about this decision? If yes, DEC. If no, just do it.

## Cross-references

- [`README.md`](./README.md) — package overview
- [`INSTALL.md`](./INSTALL.md) — Memory branch install
- [`QUICKSTART.md`](./QUICKSTART.md) — 5-minute tour
- [`INSTALLATION_GUIDE.md`](./INSTALLATION_GUIDE.md) — full multi-method install
- [`common-specs/MEMORY_PROTOCOL.md`](./common-specs/MEMORY_PROTOCOL.md) — master protocol spec
- [`common-specs/SCHEMA_A18_per_entry_metadata.md`](./common-specs/SCHEMA_A18_per_entry_metadata.md) — frontmatter spec
- [`common-specs/SCHEMA_A3_per_project_memory_bank.md`](./common-specs/SCHEMA_A3_per_project_memory_bank.md) — per-project memory banks
- `agent-shield` — the sibling Security package (release imminent)
