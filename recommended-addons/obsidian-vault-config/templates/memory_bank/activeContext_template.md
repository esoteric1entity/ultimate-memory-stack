---
project: {{project_slug}}
file: activeContext
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
schema: A3
purpose: "Current state — what we're working on RIGHT NOW; rotates to progress.md frequently"
---

# Active Context — {{project_name}}

> **Schema:** A3 #3 of 6
> **Purpose:** What's happening RIGHT NOW. This file rotates content to `progress.md` frequently (per MEMORY_PROTOCOL §11 — keep this file under 200 lines).
> **Updated:** {{date}} ({{session_label}})

---

## Right Now

_One paragraph: current task, current blocker if any, expected next 1-3 days._

## Today's Work ({{date}})

### Done
-
-

### In Progress
-
-

### Blocked
-
-

## Active Threads (Carry Forward)

_Things to remember to surface next session._

-
-

## Recent Decisions

_New TENTATIVE decisions in this session. Promoted FINAL decisions belong in `decisions/decisions.md`, not here._

| Topic | Decision | Confidence | Cross-ref |
|---|---|---|---|
| | | TENTATIVE | |

## Open Questions

_Things we don't know yet that affect direction._

-
-

## Stale Items (Candidates for Archive)

_Items in this file older than 5 sessions; consider rotating to `progress.md`._

-

## Cross-References

- `projectbrief.md` — what success looks like (the destination)
- `productContext.md` — why we're going there
- `progress.md` — what's been done (history)
- `systemPatterns.md` — architectural decisions that constrain current work
- `techContext.md` — tools/dependencies in use

---

> **Template author note (DELETE before saving):**
> Per SCHEMA_A3 #3: this is the MOST DYNAMIC of the 6 memory_bank files. Update at heartbeat cadence (~30 min during active sessions per MEMORY_PROTOCOL §4).
> Size discipline: per MEMORY_PROTOCOL §11, target ≤200 lines. Rotate older entries to `progress.md` frequently.
