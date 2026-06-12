---
project: {{project_slug}}
file: progress
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
schema: A3
purpose: "Status tracker — what works, what's left, known issues, milestones"
---

# Progress — {{project_name}}

> **Schema:** A3 #6 of 6
> **Purpose:** Status of work. What's DONE, what's LEFT, what's BLOCKED. Receives content rotated from `activeContext.md`.
> **Updated:** {{date}} ({{session_label}})

---

## What Works

_Features/components that are DONE and verified._

| Feature | Verified by | Date | Cross-ref |
|---|---|---|---|
| | | | |

## What's Left

_Features/components NOT YET shipped or verified._

| Feature | Priority | Estimate | Blocker (if any) |
|---|---|---|---|
| | | | |

## Known Issues

_Bugs, limitations, technical debt._

| Issue | Severity | Workaround | Tracked in |
|---|---|---|---|
| | | | |

## Milestones

_Major checkpoints. Past + planned._

| # | Milestone | Status | Date | Notes |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

## Iteration History

_Past validation runs / iterations._

| Iter # | Date | Result | Decisions captured |
|---|---|---|---|
| | | | DEC-### |

## Cumulative Validation Tally

_Bugs filed vs cleared; observations filed vs cleared; etc._

- **Bugs filed:** 0 · **Bugs cleared:** 0
- **Observations filed:** 0 · **Observations cleared:** 0
- **DECs logged:** 0
- **VETs logged:** 0

## Strategic Posture

_What strategic path are we on? (Path A/B/C framing, if applicable.)_

- **Path A:** maintenance / light iterations — [active / inactive]
- **Path B:** drive forward — [active / inactive]
- **Path C:** scope-carve future-state — [active / inactive]

## Next Up

_Top 3-5 things to do next, ordered by priority._

1.
2.
3.

## Cross-References

- `projectbrief.md` — success criteria (the destination)
- `activeContext.md` — what's happening RIGHT NOW
- `systemPatterns.md` + `techContext.md` — what's been built
- `decisions/decisions.md` — DEC-### entries for FINAL decisions
- `sessions/session_state.md` — session-by-session history

---

> **Template author note (DELETE before saving):**
> Per SCHEMA_A3 #6: this is the STATUS TRACKER. Update at session-end (per MEMORY_PROTOCOL §14) and after major milestones.
> Size discipline: per MEMORY_PROTOCOL §11, target ≤200 lines. Archive old iterations to `memory/archive/` when needed.
> When `activeContext.md` grows beyond 200 lines, rotate older content here.
