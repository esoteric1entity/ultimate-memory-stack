# Project Brief — Template (Memory Bank, Cline 6-file convention)

> **Purpose:** Foundation document for a project. Created at project start; defines core requirements and goals. All other memory-bank files derive from this. Treat as immutable except for scope changes.
> **Schema:** v3.0 (per SCHEMA_A18 + SCHEMA_A3)
> **Deploys to:** `memory/projects/<slug>/memory-bank/projectbrief.md`

---

```markdown
# Project Brief — <Project Name>

---
id: PROJECTBRIEF-<slug>
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: <user | orchestrator>
source_session: <N>
status: active
schema_version: "3.0"
project_slug: <slug>
project_status: planning | active | paused | complete | archived
memory_bank_path: projects/<slug>/memory-bank/
---

## Project Scope

[1-2 paragraph definition of WHAT this project IS. Be specific. This is the immutable anchor.]

## Core Requirements

- [Requirement 1 — what MUST be true for project success]
- [Requirement 2]
- [Requirement 3]

## Goals

### Primary goal
[The single most important outcome — 1 sentence]

### Secondary goals
- [Goal 2]
- [Goal 3]

## Success Criteria

- [Measurable / verifiable outcome 1]
- [Measurable / verifiable outcome 2]

## Constraints

- [Hard constraint — e.g., must be done by date, must use specific tech]
- [Soft constraint — e.g., prefer to avoid X if possible]

## Out of Scope

[Explicit non-goals — what this project is NOT trying to accomplish. Prevents scope creep.]

- [Non-goal 1]
- [Non-goal 2]

## Stakeholders

- **Primary:** [Who owns this — typically you]
- **Secondary:** [Anyone else with input — manager, customer, team]

## Anchored decisions

- [DEC-### if any structural decisions were captured before this brief existed]

---

> **Reminder:** This file is the foundation. If priorities, scope, or success criteria change, update this file FIRST. All other memory-bank files inherit from it.
```

---

## Usage notes

- **Created once, rarely modified.** Scope changes are the only valid reason to edit this file.
- **All other memory-bank files derive from this.** productContext explains the WHY, systemPatterns the architecture, techContext the stack, activeContext the current state, progress the status — but all anchor to projectbrief's scope definition.
- **Out of Scope is load-bearing:** Be explicit about what this project is NOT. Prevents scope creep mid-project.
- **Size cap:** 200 lines per MEMORY_PROTOCOL.md §11 (per-memory-bank-file). If growing past that, split off detail into systemPatterns or techContext.

## Cross-references

- `SCHEMA_A3_per_project_memory_bank.md` (6-file Memory Bank convention)
- `SCHEMA_A18` §Project-specific-additional-fields
- `MEMORY_PROTOCOL.md` §1.2 Tier 3 (memory-bank files load on demand when working on the project)
