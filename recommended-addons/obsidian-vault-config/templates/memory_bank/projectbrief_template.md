---
project: {{project_slug}}
file: projectbrief
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
schema: A3
purpose: "Foundation document — defines project scope, goals, and success criteria"
---

# Project Brief — {{project_name}}

> **Schema:** A3 #1 of 6 (Cline Memory Bank convention)
> **Purpose:** Foundation document — every other memory_bank file flows from what's defined here.
> **Updated:** {{date}} ({{session_label}})

---

## Project Identity

- **Slug:** {{project_slug}}
- **Full name:** {{project_name}}
- **Owner:** {{owner}}
- **Started:** {{start_date}}
- **Status:** active | paused | done | archived

## Mission Statement

_One paragraph: what is this project trying to accomplish, and for whom?_

## Scope — IN

_What this project will deliver._

-
-
-

## Scope — OUT

_What this project explicitly will NOT deliver. Set boundaries early to prevent scope creep._

-
-
-

## Success Criteria

_How will we know this project is "done"? Concrete, measurable._

| # | Criterion | Measurement | Target |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |

## Stakeholders

| Name | Role | Interest |
|---|---|---|
| | | |

## Constraints

_Hard limits — time, budget, regulatory, technical._

-
-

## Cross-References

- `productContext.md` — why this project exists (the problem)
- `activeContext.md` — current state
- `systemPatterns.md` — architectural decisions
- `techContext.md` — tech stack
- `progress.md` — what's done / what's left

---

> **Template author note (DELETE before saving):**
> Per SCHEMA_A3 #1: this is the FOUNDATION document. All other 5 memory_bank files inherit from what's defined here.
> Update sparingly — projectbrief.md should be stable. If mission/scope changes substantially, that's a new project (new slug, new memory_bank/).
>
> Templater variables:
> - `{{project_slug}}` → `<% tp.file.title.split('-').slice(0,-1).join('-') %>` or manual
> - `{{project_name}}` → `<% tp.system.prompt("Project name?") %>`
> - `{{date}}` → `<% tp.date.now("YYYY-MM-DD") %>`
> - `{{session}}` → `<% tp.system.prompt("Session number?") %>`
> - `{{owner}}` → typically "the project owner"
> - `{{start_date}}` → `<% tp.date.now("YYYY-MM-DD") %>`
