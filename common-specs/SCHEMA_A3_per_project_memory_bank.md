# Schema Sketch — A3: Per-Project Memory Bank

> **File Version:** 1.0 (APPROVED initial — open to revision during Tier B/C/D review)
> **Created:** 2026-05-13
> **Last Updated:** 2026-06-16

> **Source research:** memory-bank + PKM patterns from the project research base (210-source review)
> **Status:** stable — ships with UMS v3.6.0
> Open questions are tracked in §7.

---

## 1. Statement of Purpose

The Ultimate Memory Stack's global 7-category structure (`memory/{sessions,decisions,feedback,projects,security,references,user}/`) decomposes memory by **function and durability** (user-spanning, cross-session). It captures what kind of information is stored.

But for any non-trivial project, the global structure provides no place to keep **project-domain knowledge** — the architecture diagrams, technical decisions, system patterns, and current-state information that belong to ONE specific project and don't generalize across projects.

A3 introduces a **per-project memory bank** following the widely-adopted 6-file Cline Memory Bank convention, nested inside the existing `projects/` directory. Each active project gets its own structured local memory.

**The goal:** preserve our function-axis decomposition globally, AND add a project-domain decomposition locally. They're orthogonal, not competing.

---

## 2. Rationale

### Why per-project memory at all?

Real-world projects accumulate **structured knowledge** that doesn't fit the function-based 7-category global structure:
- Architecture decisions (project-specific, not user-spanning)
- Tech stack choices (project-specific)
- Current work state (project-local, not "session-level")
- What works and what doesn't yet (project-progress, not generic)

Without a place to put this, project knowledge either:
1. Gets crammed into `projects/project_context.md` (which becomes unwieldy as projects grow), or
2. Lives outside memory entirely (in user's head — defeating the persistent memory purpose)

### Why the specific Cline Memory Bank 6-file pattern?

The research survey covered Memory Bank's variants:
- **Cline original** (the canonical version) — 6 files with dependency hierarchy
- **Roo Code** — 4 files + modes
- **Cursor community** — commands + progressive rule loading
- **MCP server variants** — same 6 files, tool-call interface

All variants preserve the same invariants: 6 files (or close to it), markdown-only, root location, session-start auto-read.

Cline's 6-file pattern was chosen for the Ultimate Memory Stack because:
1. It's the most-adopted upstream pattern (highest external compatibility)
2. The dependency hierarchy (foundation → semantic → operational) is well-thought-out
3. 6 files = ~5-10k tokens loaded = fits Tier 2 (≤30% budget) cleanly
4. Single-responsibility per file keeps agent retrieval clean
5. Humans can hold 6 categories in working memory (matches our 7-cat ceiling)

### Why nest it under `projects/` (not at memory root)?

The 7-category structure represents the **global memory contract**. Adding per-project files at the root would:
- Inflate the global structure (loadable categories explode)
- Force every session to consider all projects' bank state
- Break the function-axis invariant

By nesting under `projects/<project-name>/memory-bank/`, the structure preserves:
- 7-category global contract unchanged
- Per-project bank loaded ONLY when that project is active
- Clear scoping — the bank IS the project's local state

### Alternatives considered and rejected

- **Single global Memory Bank (no per-project nesting)** — Rejected. Doesn't scale beyond 1 project. We have 11 projects in scope.
- **Per-project sub-categories in the global structure** (e.g., `decisions/<project>/` instead of `projects/<project>/memory-bank/`) — Rejected. Splits the function axis across project boundaries, defeats the purpose of having global decisions/feedback/etc.
- **Drop our 7-cat in favor of Memory Bank entirely** — Rejected. We'd lose user_profile, security/vetting_log, feedback (cross-project), references. These have proven value.
- **Optional Obsidian vault per project as the bank** — Rejected for v1 of the stack. Obsidian is good as an editor; not required as a backend. Bank is markdown so any editor works.

---

## 3. Sound Reasoning (Sources + Evidence)

| Claim | Source | Evidence type |
|-------|--------|---------------|
| Memory Bank 6-file is the dominant 2026 pattern across IDE tools | project research findings, multiple adoptions cited | Cross-tool convergence (Cline, Roo Code, Cursor variants, MCP server variants) |
| 6-file fits ~5-10k tokens | project research measurement | Practitioner experience |
| Dependency hierarchy matters as much as file count | `[Cline-MemoryBankDocs]` | First-party docs |
| Markdown-first is the right backend (not vector DB) | Independent research-pass convergence | multiple independent reviews |
| Per-project scoping prevents token bloat | project research + tiered context budget research | Architectural inference + Chroma context-rot research |

**Caveats:**
- Memory Bank's 6-file pattern is widely-adopted but **not peer-reviewed** (it's a convention, not a research finding)
- Cline's original Threads post is the methodology origin, no formal paper
- Treat this as adopting a **community best practice**, not adopting a research result

---

## 4. Schema Definition

### Directory layout

```
memory/
├── projects/
│   ├── project_context.md                    ← GLOBAL: index of all projects (existing)
│   └── <project-slug>/                       ← per-project root (NEW)
│       └── memory-bank/                      ← the 6-file Memory Bank (NEW)
│           ├── projectbrief.md               (foundation)
│           ├── productContext.md             (semantic — what/why)
│           ├── systemPatterns.md             (semantic — how — architecture)
│           ├── techContext.md                (semantic — what tech)
│           ├── activeContext.md              (operational — current focus)
│           └── progress.md                   (operational — status, known issues)
```

### Per-file purpose (the dependency hierarchy)

| File | Tier | Purpose | Typical size |
|------|------|---------|--------------|
| `projectbrief.md` | Foundation | The "why" — vision, mission, success criteria, non-goals | 500-1000 words |
| `productContext.md` | Semantic | The "what" — problems solved, user goals, key features | 500-1500 words |
| `systemPatterns.md` | Semantic | The "how (architecture)" — system architecture, design patterns, technical decisions | 1000-2000 words |
| `techContext.md` | Semantic | The "how (tech)" — languages, frameworks, runtimes, dev setup, dependencies | 500-1500 words |
| `activeContext.md` | Operational | The "now" — what's actively being worked on, recent changes, next steps | 300-800 words |
| `progress.md` | Operational | The "where" — what works, what's left, known issues, milestones | 500-1000 words |

**Total token budget per active project:** ~3,000-8,000 tokens. Fits Tier 2 budget (≤30% context) cleanly when 1-2 projects are concurrently active.

### Loading rules

Per the existing Tiered Context Loading protocol:

- **Tier 1 (always):** Global `sessions/session_state.md` + `user/user_profile.md` (existing rule)
- **Tier 2 (project-active):** If the current session is working on a specific project, load that project's `memory-bank/` (NEW rule)
- **Tier 3 (on-demand):** Other projects' memory banks are NOT loaded by default; loaded only if cross-referenced

### Integration with existing `projects/project_context.md`

The global `projects/project_context.md` remains the **project INDEX**:
- One entry per project: PRJ-NNN, status, brief, tags
- Each entry has a `memory_bank_path` field pointing to the project's bank

The per-project Memory Bank is the **project's deep state**:
- Stored separately, scoped to the project
- Referenced from the global index
- Loaded conditionally

This preserves the existing global structure unchanged AND adds per-project depth.

### YAML frontmatter convention (cross-references A18)

Each Memory Bank file begins with frontmatter per A18 schema (separate SCHEMA file). Critical fields:

```yaml
---
project_slug: <slug>
file_role: projectbrief | productContext | systemPatterns | techContext | activeContext | progress
created_at: YYYY-MM-DD
last_updated: YYYY-MM-DD
last_validated: YYYY-MM-DD
schema_version: 3.0
---
```

Memory Bank files participate in the same TTL/validation/audit machinery as other memory entries.

---

## 5. Scope — What This CAN and CANNOT Do

### CAN

- Capture project-specific knowledge that doesn't generalize cross-project
- Scale to many concurrent projects without inflating global context
- Be authored by both agent and human (markdown source of truth)
- Integrate with Obsidian or any markdown editor
- Be versioned via the same per-entry metadata system (last_validated, expires_at)
- Be quarantined when poisoned (the standard quarantine mechanism applies)
- Be archived when a project ends (move `projects/<project>/` to `archive/`)

### CANNOT

- Replace the global 7-category structure (it complements, not replaces)
- Hold cross-project knowledge (that's what `references/`, `decisions/`, `feedback/` are for)
- Substitute for `projects/project_context.md` as an index
- Be loaded automatically for non-active projects (would blow Tier 2 budget)
- Solve the multi-project comparison problem on its own (need a separate cross-cutting view)

### Deployment tier

**T0** — works anywhere. Pure markdown + filesystem. No Code Execution, Node.js, or Skills needed.

### Edition fit

- **Biotech-edition:** Includes Memory Bank by default. PHI detection (Section 11) applies to ALL memory bank files. Audit log captures every write.
- **General-edition:** Includes Memory Bank by default. Compliance section in memory bank is opt-in. Audit log is opt-in.

---

## 6. What Is to Come (and Why)

### Stage 1 (immediate)
- Schema documented (this file)
- Implementation: create empty templates for the 6 Memory Bank files in `common-specs/templates/`
- Update memory_protocol.md with the Tier 2 conditional loading rule

### Stage 2 (after Stage 1 in-place)
- `extract_project_template.py` — given an existing project's memory bank, scaffold an empty template for a new similar project
- Karpathy Lint pass adapted to scan Memory Bank files for: contradictions across the 6 files, stale activeContext (over 30 days unchanged + progress not updated), missing dependencies (e.g., productContext mentions tech not in techContext)
- Background consolidation: weekly check that every active project's `activeContext.md` was updated in the past N days

### Stage 3 / v3.0 (Code Execution unblocked)
- Cross-project semantic search across all Memory Bank files (Ollama-backed)
- Auto-generation of `progress.md` from session_state.md mentions of the project
- Graphiti backend storing project facts with `valid_at`/`invalid_at` from Memory Bank metadata

### NOT in scope (and why)

- **AGENTS.md / CLAUDE.md auto-generation per project** — Out of scope for v1. Those are agent-runtime files; this is memory. Future possibility.
- **Multi-project graph reasoning** — Out of scope until Code Execution + Graphiti unblock (Stage 3+).
- **Obsidian-as-required-frontend** — Never required. Optional integration only.

---

## 7. Open Questions

1. **When is a "project" worth a Memory Bank?** Triggered by: explicit user opt-in? Auto-created when project_context.md entry passes a threshold? Default-on for every project?
2. **Migration path for existing projects.** Projects already listed in `projects/project_context.md` — do they retroactively get Memory Banks, or only new projects going forward?
3. **`activeContext.md` lifecycle.** Does it ever get archived (when a project completes), or always live in the current `projects/<project>/memory-bank/`?
4. **Naming collision risk** with the existing `projects/project_context.md`. Should the global index be renamed (e.g., `projects/_index.md`) to disambiguate from per-project content?

---

## 8. Cross-References

- **Source research:** memory-bank + PKM findings from the project research base
- **Citation:** `[Cline-MemoryBankDocs]` in `_master.md`
- **Sister schema:** `SCHEMA_A18_per_entry_metadata.md` (frontmatter spec, applies to Memory Bank files too)

- **Templates:** `templates/memory_bank/*.template.md` (6 Cline-convention templates)
