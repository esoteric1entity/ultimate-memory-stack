# Project Context — Template

> **Purpose:** Scaffolding for `memory/projects/project_context.md`. **High-level project registry** — one short entry per active project. Detailed project state lives in `memory/projects/<slug>/memory-bank/` (per SCHEMA_A3).
> **Schema:** v3.0 (per SCHEMA_A18)
> **Companion:** SCHEMA_A3 (per-project memory bank), MEMORY_PROTOCOL.md §1.2 (Tier 2 load when working on a project)

---

```markdown
# Project Context — Registry

> **Schema Version:** 3.0
> **Active projects:** <N>
> **Last Updated:** <YYYY-MM-DD>

---

## PRJ-001: <Project slug — e.g., my-webapp>

---
id: PRJ-001
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: orchestrator
source_session: <N>
status: active
schema_version: "3.0"
project_slug: <slug>
project_status: planning | active | paused | complete | archived
memory_bank_path: projects/<slug>/memory-bank/
related: [DEC-NNN, ...]
tags: [<domain-tag>, <status-tag>]
---

**One-line description:** [What this project is, in 1 sentence]

**Status:** [planning / active / paused / complete / archived]

**Active priority:** [HIGH / MEDIUM / LOW — for triage during multi-project sessions]

**Goal:** [What we're trying to accomplish — 1-2 sentences]

**Current milestone:** [What's the immediate next step / deliverable]

**Recent activity:** [1-2 sentences on what happened in the last 1-2 sessions]

**Key files / locations:**
- `<path>` — <what's there>
- `<path>` — <what's there>

**Blockers / dependencies:**
- <blocker if any>

**Next session focus:**
- <what to work on next>

**See full state at:** `memory/projects/<slug>/memory-bank/` (SCHEMA_A3 — 6 files: projectbrief, productContext, systemPatterns, techContext, activeContext, progress)

---

## PRJ-002: <Next project>

[Same structure]
```

---

## Worked example

```markdown
## PRJ-007: my-webapp

---
id: PRJ-007
created_at: 2026-05-11
last_updated: 2026-05-14
source_agent: orchestrator
source_session: 8
status: active
schema_version: "3.0"
project_slug: my-webapp
project_status: active
memory_bank_path: projects/my-webapp/memory-bank/
related: [DEC-019, DEC-021, DEC-023, DEC-024, DEC-028, DEC-029, DEC-030]
tags: [webapp, active-development]
---

**One-line description:** R&D for a memory-stack schema package with full documentation discipline.

**Status:** active

**Active priority:** HIGH (current focus)

**Goal:** [Example: Deliver the v1.0 schema package — common specs, edition profiles, user cheat sheets — per the project plan.]

**Current milestone:** [Example: Phase 1 in progress — 4 of 6 sub-deliverables complete.]

**Recent activity:** Drafted 8 common-specs files (~192 KB) covering bootstrap, architecture, protocol, and 5 schemas. Corrected Tier C ID misalignments. Added bi-temporal B5 + Obsidian compat + wiki-link syntax.

**Key files:**
- `docs/PLAN.md` — master plan
- `src/` — application code
- `tests/` — test suite

**Blockers:** None — pending the maintainer's review at each sub-deliverable.

**Next session focus:** finish the auth module, then start the API integration tests.

**See full state at:** `memory/projects/my-webapp/memory-bank/`
```

## Usage notes

- **This is a REGISTRY, not full state.** Detailed work lives in `<slug>/memory-bank/` per SCHEMA_A3.
- **Update at session end:** When project state changes meaningfully, update the corresponding PRJ entry
- **Priority field aids triage:** When multiple projects are active, HIGH priority gets attention first
- **Size cap:** 150 lines per MEMORY_PROTOCOL.md §11. If file grows, split into per-project files in `memory/projects/`.
- **Archive complete projects:** When a project closes, move to status `archived` and consider moving its entry + memory-bank to `memory/archive/projects/<slug>/`

## Cross-references

- `MEMORY_PROTOCOL.md` §1.2 (Tier 2 load when project work active), §11 (size limits)
- `SCHEMA_A3_per_project_memory_bank.md` (full project memory bank structure)
- `SCHEMA_A18` §Project-specific-additional-fields
