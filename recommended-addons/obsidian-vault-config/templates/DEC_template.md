## DEC-{{id}}: {{title}}

---
id: DEC-{{id}}
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
confidence: TENTATIVE
---

- **Status:** TENTATIVE | FINAL
- **Confidence:** 0.0-1.0
- **Session:** {{session}}
- **Date:** {{date}}
- **Decision:** _One-line summary of what was decided_

### Purpose
_What is the user-facing goal? What problem does this decision solve?_

### Rationale
_Why this approach over alternatives? What constraints drove the choice?_

### Sound reasoning
_What evidence, research, or decisions back this? Cite DEC-### or VET-### entries._

1.
2.
3.

### Scope — CAN
_What this decision EMPOWERS or PERMITS — explicit boundaries._

-
-

### Scope — CANNOT
_What this decision PROHIBITS or EXCLUDES — explicit boundaries._

-
-

### Cross-references
_Related DECs, VETs, schemas, protocol sections._

- [[DEC-XXX]] (reason for relation)
- [[VET-XXX]] (reason for relation)

### Bi-temporal (if applicable)

- `supersedes:` [[DEC-XXX]] (if this replaces an older decision)
- `superseded_by:` (filled in when a future decision replaces this one)
- `invalid_at:` (filled in when this decision becomes invalid; preserves history per MEMORY_PROTOCOL §3 B5)

### Tags

[project-tag], [topic], [feature-area]

---

> **Template author note (DELETE before saving):**
> This template implements the documentation discipline standing rule. All 5 sections (Purpose / Rationale / Sound reasoning / Scope CAN / Scope CANNOT) are MANDATORY. Undocumented decisions do NOT promote to FINAL.
>
> **Templater variable expansion (if Templater installed):**
> Replace `{{date}}` with `<% tp.date.now("YYYY-MM-DD") %>`
> Replace `{{session}}` with `<% tp.system.prompt("Session number?") %>`
> Replace `{{id}}` with `<% tp.system.prompt("Decision ID (next available number)?") %>`
> Replace `{{title}}` with `<% tp.system.prompt("Decision title (short)") %>`
