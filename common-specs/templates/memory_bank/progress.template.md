# Progress — Template (Memory Bank, Cline 6-file convention)

> **Purpose:** The status file. Tracks completed work, current milestones, what's left to build, known issues, and the evolution of project decisions over time.
> **Schema:** v3.0
> **Deploys to:** `memory/projects/<slug>/memory-bank/progress.md`
> **Append-mostly:** This is a HISTORICAL log; entries are added, rarely modified.

---

```markdown
# Progress — <Project Name>

---
id: PROGRESS-<slug>
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: <user | orchestrator>
source_session: <N>
status: active
schema_version: "3.0"
project_slug: <slug>
---

## Current Status

**Phase:** [Current phase / milestone — e.g., "Phase 2 — schema design"]
**Overall completion:** [Estimate — e.g., "40% of current phase; 8% of total project"]
**On track for:** [Target date / outcome]

## Completed Work (chronological — newest first)

### <YYYY-MM-DD> Session <N> — <Milestone short name>
- [Completed item 1]
- [Completed item 2]
- **Notes:** [Anything important about HOW it was completed — file paths, design choices, decisions made]

### <YYYY-MM-DD> Session <N> — <Earlier milestone>
- ...

## Current Milestones

- [ ] **<Milestone 1>** — Target: <date>
  - [Sub-task A]
  - [Sub-task B]
- [ ] **<Milestone 2>** — Target: <date>

## What's Left to Build

### Near-term (this phase)
- [Item 1]
- [Item 2]

### Mid-term (next phase)
- [Item 1]

### Long-term (eventual)
- [Item 1]

## Known Issues

- **Issue 1:** [Description] — **Status:** [open / mitigated / accepted] — **Mitigation:** [If applicable]
- **Issue 2:** [Description] — **Status:** open

## Decision Evolution (project-specific)

Some decisions evolve as the project progresses. Capture the evolution here for future-you:

- **<Topic 1>:** Initial approach was X (session N); revised to Y (session N+M) after learning Z. Driver: [why we changed]
- **<Topic 2>:** ...

## Velocity / Effort tracking (optional)

| Period | Effort | Outcome |
|--------|--------|---------|
| Session N–N+5 | ~3 sessions | [Milestone X] |
| Session N+5–N+10 | ~3 sessions | [Milestone Y] |

(Useful if you want to estimate future capacity)

---

> **Reminder:** progress.md is HISTORICAL — append, don't modify. The exception: status fields on Known Issues can update (open → mitigated → resolved). Everything else is immutable once written.
```

---

## Usage notes

- **Append, don't edit:** Historical truth — newer info goes at the top of "Completed Work"; older entries stay verbatim
- **Rotation target for activeContext:** When sub-tasks complete in activeContext.md, summarize them here
- **Decision evolution section is valuable:** Captures the WHY of changes that don't show up in the latest version of files
- **Size cap:** 200 lines per MEMORY_PROTOCOL.md §11. Archive sessions older than 20 to `memory/archive/projects/<slug>/progress_<YYYY-MM>.md` when the limit approaches.

## Cross-references

- `SCHEMA_A3_per_project_memory_bank.md`
- `activeContext.md` (rotation source — completed work flows here)
- `projectbrief.md` (milestones target the project's success criteria)
- `MEMORY_PROTOCOL.md` §11 (size limits + archival)
