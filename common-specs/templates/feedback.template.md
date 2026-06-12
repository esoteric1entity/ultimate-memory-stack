# Feedback — Template

> **Purpose:** Scaffolding for `memory/feedback/feedback.md`. Holds explicit user corrections that should permanently change behavior. Recurring patterns auto-promote to standing rules per B6.
> **Schema:** v3.0 (per SCHEMA_A18)
> **Companion:** MEMORY_PROTOCOL.md §4.2 (pattern-key promotion), SCHEMA_A18 §Feedback-specific-additional-fields

---

```markdown
# Feedback Log

> **Schema Version:** 3.0
> **Entries:** 0 (initial)
> **Last Updated:** <YYYY-MM-DD>

---

## FB-001: <Title — what was corrected>

---
id: FB-001
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: user
source_session: <N>
status: active
schema_version: "3.0"
pattern_key: <stable.dotted.key>            # e.g., "output.formatting.tables"
recurrence_count: 1                          # increment if same pattern_key recurs
first_seen: <YYYY-MM-DD>
last_seen: <YYYY-MM-DD>
related: [FB-NNN, DEC-NNN]                   # optional cross-refs
tags: [<tag1>, <tag2>]
---

**Correction:** [What I was doing wrong]

**What user said:** [Verbatim user quote or close paraphrase]

**Behavior to change:** [What I will now do differently]

**Reasoning user provided:** [If user explained the WHY — capture it. Otherwise note "not stated"]

**Apply to:** [Specific contexts — file types, project types, task types]

**Do NOT apply to:** [Negative scope — when this rule does not apply]

---

## FB-002: <Next feedback entry>

[Same structure]
```

---

## Worked example — Pattern promotion

After 3 occurrences (biotech) or 5 occurrences (general) of the same pattern_key, per B6:

```markdown
## FB-003: Output formatting — tables should use markdown pipe syntax, not ASCII

---
id: FB-003
created_at: 2026-04-15
pattern_key: output.formatting.tables
recurrence_count: 3                           # auto-promoted at threshold
first_seen: 2026-04-01
last_seen: 2026-04-15
related: [FB-001, FB-002]                     # prior instances same pattern_key
tags: [formatting, ux, promoted-to-standing-rule]
---

**Correction:** Was generating ASCII-art tables with `+---+---+`; user wanted markdown pipe syntax.
**What user said:** "use markdown tables, not ASCII"
**Behavior to change:** Default to `| col | col |\n|-----|-----|` for ALL tables.
**Reasoning:** Renders in markdown viewers; ASCII tables don't.
**Apply to:** All output, all contexts.
**Promotion:** This pattern hit threshold (recurrence_count=3 for biotech, ≥5 general). Auto-promoted to standing rule in `.claude/rules/auto_rules.md` per MEMORY_PROTOCOL.md §4.2.
```

When promoted, a corresponding DEC entry captures the source feedback chain (provenance):

```markdown
## DEC-XXX: Standing rule — markdown tables (auto-promoted from FB-003)

---
source_agent: auto-promoted-from-pattern
related: [FB-001, FB-002, FB-003]
tags: [standing-rule, auto-promoted, formatting]
---
[Body documents the rule]
```

## Usage notes

- **Patterns auto-promote at threshold:** Biotech recurrence_count ≥3, general ≥5 (per the B6 recurrence convention)
- **pattern_key naming:** Use stable dotted notation. Hierarchical. Examples: `output.formatting.tables`, `tool.use.parallel`, `git.commit.never-amend`. Consistent keys enable counting.
- **first_seen / last_seen:** Temporal range — useful for "how stable is this pattern?"
- **Promotion creates standing rule:** Once auto-promoted, the rule lives in `.claude/rules/auto_rules.md` AND a DEC entry with full provenance
- **Size cap:** 100 lines per MEMORY_PROTOCOL.md §11. Consolidate repeated feedback into standing rules at the size limit.

## Cross-references

- `MEMORY_PROTOCOL.md` §4.2 (pattern-key promotion), §11 (size limits)
- `SCHEMA_A18` §Feedback-specific-additional-fields
- `DEC-012` (example: the decision this feedback relates to)
