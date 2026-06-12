# Active Context — Template (Memory Bank, Cline 6-file convention)

> **Purpose:** The current-state file. Documents current work focus, recent changes, next steps, active decisions, important patterns and preferences, and learnings/insights.
> **Schema:** v3.0
> **Deploys to:** `memory/projects/<slug>/memory-bank/activeContext.md`
> **Changes most often** of all 6 memory-bank files. Update at end of every working session.

---

```markdown
# Active Context — <Project Name>

---
id: ACTIVECONTEXT-<slug>
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>           # Update on every meaningful change
source_agent: <user | orchestrator>
source_session: <N>
status: active
schema_version: "3.0"
project_slug: <slug>
---

## Current Work Focus

[1-2 sentences: what we're working on RIGHT NOW. Be specific.]

## Active Sub-Tasks

- [ ] [Sub-task 1 — file:line if known]
- [ ] [Sub-task 2]
- [x] [Completed since last update — kept for context, will move to progress.md at session end]

## Recent Changes (this session / last 1-2 sessions)

- [Change 1 — file modified + what changed]
- [Change 2]
- (Be specific — file paths, function names, what state went from→to)

## Next Steps

- [Step 1 — what to do next]
- [Step 2]
- (Concrete enough that future-you can pick up cold)

## Active Decisions (inline, may promote later)

- [Decision 1 — inline; if it accumulates >5 related, promote to global `decisions.md` per MEMORY_PROTOCOL.md §12]
- [Decision 2]

## Important Patterns / Preferences (project-specific)

- [Pattern 1 — convention adopted in this project]
- [Pattern 2]
- (If recurring, may promote to global feedback.md or standing rules)

## Learnings / Insights

- [Insight 1 — something learned while working on this]
- [Insight 2]
- (Where surprising or counterintuitive findings live; valuable for future-you)

## Blockers / Waiting On

- [Blocker 1 — what's blocked + what would unblock it]

## Heartbeat (last <HH:MM>)

- Task: <currently-active>
- File: <path:line>
- Status: <state>
- Estimated time to checkpoint: <minutes>

---

> **Reminder:** This file changes constantly. progress.md is the rotation target — when a task completes, move its summary there. activeContext.md should reflect the LIVING WORK.
```

---

## Usage notes

- **Update most often:** Of all 6 memory-bank files, this one gets the most edits. Plan for it.
- **Rotate to progress.md:** When a sub-task completes, move it to progress.md. Don't let activeContext bloat with completed work.
- **Heartbeat lives here:** Per MEMORY_PROTOCOL.md §4.4, ~30-minute checkpoints update this file's heartbeat section
- **Useful at session start:** When resuming work on a project, activeContext is one of the first reads (Tier 2)
- **Size cap:** 200 lines per MEMORY_PROTOCOL.md §11. If growing past, rotate completed items to progress.md.

## Cross-references

- `SCHEMA_A3_per_project_memory_bank.md`
- `progress.md` (rotation target — completed work moves there)
- `MEMORY_PROTOCOL.md` §4.4 (heartbeat), §1.2 Tier 2 load, §12 (decision promotion)
