---
project: {{project_slug}}
file: systemPatterns
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
schema: A3
purpose: "System architecture — design patterns, key technical decisions, component relationships"
---

# System Patterns — {{project_name}}

> **Schema:** A3 #4 of 6
> **Purpose:** ARCHITECTURAL decisions and patterns. The "HOW" of the solution.
> **Updated:** {{date}} ({{session_label}})

---

## Architectural Overview

_One paragraph: what's the high-level architecture? Reference diagrams if available._

```
[Visual / ASCII / Mermaid diagram if appropriate]
```

## Core Components

| Component | Purpose | Owner | Status |
|---|---|---|---|
| | | | |

## Key Design Decisions

_FINAL decisions that constrain how this system can evolve. Reference DEC-### entries in `decisions/decisions.md` for full provenance._

| # | Pattern | Decision | DEC-### | Why |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |

## Component Relationships

_How components communicate. APIs, message formats, sync vs async, etc._

-
-

## Data Flow

_How data moves through the system. From input to output._

```
Input → [Component A] → [Component B] → Output
```

## Patterns We Use

_Recurring patterns adopted across the system. (E.g., "all log files use JSONL append-only", "all installer Skills use 5-file convention", etc.)_

| Pattern | Where applied | Why |
|---|---|---|
| | | |

## Patterns We Avoid

_Anti-patterns explicitly avoided + the reasoning. (E.g., "no auto-mutation of memory entries — surface-only per DEC-###".)_

| Anti-pattern | Why avoided | Cross-ref |
|---|---|---|
| | | |

## Trade-offs

_Important trade-offs made during architecture. What was gained vs lost._

| Trade-off | Gained | Lost | Justified by |
|---|---|---|---|
| | | | |

## Cross-References

- `projectbrief.md` — what we're building
- `techContext.md` — tech stack that implements these patterns
- `progress.md` — what patterns are in production
- `decisions/decisions.md` — DEC-### entries for FINAL pattern decisions

---

> **Template author note (DELETE before saving):**
> Per SCHEMA_A3 #4: this captures HOW the system is shaped. Update when an architectural decision is made (typically promoted to FINAL DEC in parallel).
> Size discipline: per MEMORY_PROTOCOL §11, target ≤200 lines. Keep summaries here; detailed reasoning belongs in DEC entries.
