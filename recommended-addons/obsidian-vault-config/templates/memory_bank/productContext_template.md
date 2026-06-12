---
project: {{project_slug}}
file: productContext
created_at: {{date}}
last_updated: {{date}}
source_agent: orchestrator
source_session: {{session}}
status: active
schema_version: "3.0"
schema: A3
purpose: "Why this project exists — problem statement, user pain, market context"
---

# Product Context — {{project_name}}

> **Schema:** A3 #2 of 6
> **Purpose:** Why this project exists. The PROBLEM it solves and the user/market context. Distinct from `projectbrief.md` (which says WHAT we're building) — this says WHY.
> **Updated:** {{date}} ({{session_label}})

---

## The Problem

_What user pain or market gap motivates this project? Be concrete — name the symptom, not just the solution._

## Affected Users

_Who has this problem? How many? How does it impact their work?_

| User type | Scale | Impact |
|---|---|---|
| | | |

## Current Workarounds (Before This Project)

_How do users solve this today without our solution? What are the costs/frictions?_

-
-

## Why Now

_What's changed recently that makes this the right time to address this problem? (Market shift, regulatory change, tech enabler, user demand, etc.)_

## Solution Hypothesis

_What's our proposed solution at a high level? (Details belong in `systemPatterns.md` and `techContext.md`; this is the value-prop summary.)_

## Anti-Hypotheses (What We're NOT Doing)

_Adjacent problems we're explicitly NOT solving. Helps stakeholders calibrate expectations._

-
-

## Success Stories We're Targeting

_What does "win" look like from the user's perspective? Concrete scenarios, not metrics (metrics live in `projectbrief.md`)._

> _Example: "User X reports they used to spend 4 hours per week on task Y; now they spend 15 minutes."_

## Cross-References

- `projectbrief.md` — scope and success criteria
- `activeContext.md` — current state
- `systemPatterns.md` — how the solution is architected
- `progress.md` — what's been delivered toward the hypothesis

---

> **Template author note (DELETE before saving):**
> Per SCHEMA_A3 #2: this captures WHY before HOW. If you can't articulate the problem clearly here, the project's foundation may be shaky.
> Update when: market shifts, new user feedback reframes the problem, or the hypothesis evolves substantially.
