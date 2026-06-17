# System Patterns — Template (Memory Bank, Cline 6-file convention)

> **Purpose:** The architecture file. Documents system architecture, key technical decisions, design patterns in use, component relationships, and critical implementation paths.
> **Schema:** v3.0
> **Deploys to:** `memory/projects/<slug>/memory-bank/systemPatterns.md`

---

````markdown
# System Patterns — <Project Name>

---
id: SYSTEMPATTERNS-<slug>
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: <user | orchestrator>
source_session: <N>
status: active
schema_version: "3.0"
project_slug: <slug>
---

## System Architecture

[High-level diagram in ASCII or markdown — show major components + relationships]

```
┌──────────────┐      ┌──────────────┐
│ Component A  │ ───→ │ Component B  │
└──────────────┘      └──────────────┘
       │                     │
       └─────────────────────┘
              ↓
       ┌──────────────┐
       │ Component C  │
       └──────────────┘
```

## Key Technical Decisions

- **<Decision 1 short name>:** [What was decided + brief WHY. Link to DEC-### if formally captured]
- **<Decision 2>:** [What + WHY + link]

## Design Patterns in Use

### Pattern 1: <Pattern name>
- **Where used:** [Components / modules]
- **Why:** [Problem it solves]
- **Trade-offs:** [What you give up by using this]

### Pattern 2: <Pattern name>
- (Same structure)

## Component Relationships

| Component | Depends On | Used By | Notes |
|-----------|------------|---------|-------|
| A | (none) | B, C | Foundation |
| B | A | (consumers) | Mid-layer |
| C | A, B | (terminal) | Output |

## Critical Implementation Paths

### Path 1: [User action → outcome]
1. Step 1
2. Step 2
3. ...

### Path 2: [Another important path]

## Failure Modes + Recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| <failure mode 1> | <how it surfaces> | <how to recover> |
| <failure mode 2> | | |

## Architecture Decisions Log (project-specific)

- [DEC-### if any project-specific architecture decisions live in the global decisions.md, reference them here]
- [Or capture inline if not yet promoted to global decisions]

---

> **Reminder:** This file describes the ARCHITECTURE — what components exist and how they relate. Tech stack details (libraries, versions, env setup) belong in techContext.md. Current work-in-flight belongs in activeContext.md.
````

---

## Usage notes

- **Architecture, not stack:** Component-level diagrams + design patterns; NOT library versions or env setup (that's techContext.md)
- **Diagrams matter:** Even ASCII diagrams clarify relationships better than prose. Update when architecture changes.
- **Reference global DECs:** If a project-relevant decision is captured in `memory/decisions/decisions.md`, link here. Avoid duplicating content.
- **Update on architectural change:** When components are added/removed/restructured

## Cross-references

- `SCHEMA_A3_per_project_memory_bank.md` (this file's role)
- `projectbrief.md` (this architecture serves THIS scope)
- `techContext.md` (sibling — the tech stack supporting this architecture)
- `activeContext.md` (sibling — what's being worked on in this architecture right now)
