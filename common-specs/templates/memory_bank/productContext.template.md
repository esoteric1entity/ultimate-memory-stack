# Product Context — Template (Memory Bank, Cline 6-file convention)

> **Purpose:** The "WHY" file. Explains why this project exists, what problems it solves, how it should work, and user experience goals. Sits between business intent and technical execution.
> **Schema:** v3.0
> **Deploys to:** `memory/projects/<slug>/memory-bank/productContext.md`

---

```markdown
# Product Context — <Project Name>

---
id: PRODUCTCONTEXT-<slug>
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: <user | orchestrator>
source_session: <N>
status: active
schema_version: "3.0"
project_slug: <slug>
---

## Why this project exists

[Origin story — what triggered the work. 1-2 paragraphs.]

## Problems it solves

- **Problem 1:** [User-facing problem this project addresses]
- **Problem 2:** [Another problem]
- (Be specific about WHO has the problem and WHEN they experience it)

## How it should work — User experience goals

- [UX principle 1 — e.g., "minimal friction; works without setup"]
- [UX principle 2]
- (Frame these from the user's perspective, not the implementer's)

## How it should NOT work — Anti-patterns to avoid

- [Anti-pattern 1 — what would make this worse than no solution]
- [Anti-pattern 2]

## Target users / contexts

- **Primary:** [Who uses this — be specific]
- **Secondary:** [Other contexts where it might apply]
- **Not for:** [Explicit non-users — clarifies intent]

## Value proposition

[1 sentence: "This project delivers X for Y by doing Z."]

## Relationship to other projects

- **Replaces:** [If applicable — what existing approach this supersedes]
- **Complements:** [Sister projects that work together]
- **Depends on:** [Upstream dependencies]
- **Depended on by:** [Downstream consumers]

---

> **Reminder:** This is the WHY file. If the project starts feeling unmoored, re-read this. If the answers here are now wrong, that's a scope change — update projectbrief.md too.
```

---

## Usage notes

- **WHY anchors HOW.** When implementation decisions feel arbitrary, the answer is usually in this file.
- **Update when motivation shifts.** If a stakeholder priority changes or you learn new things about the user's actual problem, edit this.
- **Anti-patterns are valuable.** Explicit "don't do this" guidance prevents drift.

## Cross-references

- `SCHEMA_A3_per_project_memory_bank.md` (this file's role in the 6-file convention)
- `projectbrief.md` (this file's parent — productContext expands on the WHY from projectbrief)
- `systemPatterns.md` + `techContext.md` (sibling files — the HOW for this WHY)
