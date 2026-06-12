# Decisions — Template

> **Purpose:** Scaffolding for `memory/decisions/decisions.md`. Holds promoted decisions (per MEMORY_PROTOCOL.md §12 promotion pattern). New decisions start inline in session_state.md; promote here at >5 related entries per topic.
> **Schema:** v3.0 (per SCHEMA_A18)
> **Companion:** MEMORY_PROTOCOL.md §12 (decision promotion), SCHEMA_A18 §Decision-specific-additional-fields

---

```markdown
# Decisions Log

> **Schema Version:** 3.0
> **Entries:** 0 (initial)
> **Last Updated:** <YYYY-MM-DD>

---

## DEC-001: <Title — short noun phrase describing decision>

---
id: DEC-001
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
last_validated: <YYYY-MM-DD>
expires_at: <YYYY-MM-DD>           # 28 days from last_validated
valid_at: <YYYY-MM-DD>             # B5 — when fact became true (often same as created_at for new decisions)
source_agent: orchestrator         # or user / warden / etc.
source_session: <N>
status: active                     # active | superseded | quarantined | archived
schema_version: "3.0"
confidence: FINAL                  # FINAL | TENTATIVE | EXPLORATORY
related: [DEC-NNN, DEC-NNN]        # cross-references
tags: [<tag1>, <tag2>]
content_sha256: <hex>              # for CAS concurrency per B3
---

**Decision:** [What was decided — single declarative sentence]

**Purpose:** [What this enables / why we need it]

**Rationale:** [Why this approach over alternatives — 2-3 sentences. List alternatives considered.]

**Sound reasoning:** [Evidence chain — research findings, decisions, examples backing this]

**Scope — CAN:**
- [Capability 1]
- [Capability 2]

**Scope — CANNOT:**
- [Explicit boundary 1]
- [Explicit boundary 2]

**Revisit trigger** (if TENTATIVE/EXPLORATORY): [What would cause us to reconsider]

This decision builds on [[DEC-NNN]] (when wiki-link syntax is used inline — auto-synced with `related` at T2+ per MEMORY_PROTOCOL.md §4.3).

---

## DEC-002: <Next decision title>

[Same structure]
```

---

## Worked example — Supersession

When a new decision supersedes an older one, two entries update simultaneously (per MEMORY_PROTOCOL.md §5.4):

```markdown
## DEC-001 (UPDATED by supersession event)

---
id: DEC-001
created_at: 2026-04-10
last_updated: 2026-08-15            # touched by supersession event today
valid_at: 2026-04-10
invalid_at: 2026-08-15              # B5 — factual end of validity
status: superseded                  # was: active
superseded_by: DEC-040              # forward pointer
---

[Body preserved verbatim — DO NOT modify the body of a superseded entry]


## DEC-040 (NEW — supersedes DEC-001)

---
id: DEC-040
created_at: 2026-08-15
valid_at: 2026-08-15
status: active
supersedes: DEC-001                 # this drives DEC-001's invalid_at auto-set
---

**Decision:** [new decision]
[etc.]
```

Point-in-time queries (per SCHEMA_A18 §4 bi-temporal section) on this pair return DEC-001 for queries with `query_time < 2026-08-15` and DEC-040 for queries on or after that date. **History is preserved.**

## Usage notes

- **Promotion threshold:** >5 inline decisions on the same topic in session_state.md → promote to here (MEMORY_PROTOCOL.md §12)
- **DEC-IDs are sequential:** DEC-001, DEC-002, ... never reuse numbers even after supersession
- **Confidence levels matter:** FINAL = settled, don't re-ask; TENTATIVE = subject to revision; EXPLORATORY = testing
- **Tags enable search:** common tags include `security`, `policy`, `architecture`, `compliance`, `user-approved`, `tier-A/B/C/D`
- **Size cap:** 200 lines per MEMORY_PROTOCOL.md §11. FINAL decisions older than 20 sessions archive to `memory/archive/`.

## Cross-references

- `MEMORY_PROTOCOL.md` §12 (promotion), §11 (size limits), §3 (conflict resolution hierarchy)
- `SCHEMA_A18` (frontmatter, especially Decision-specific fields)
- `SCHEMA_A18` §Bi-temporal-fields (B5 — `valid_at`/`invalid_at` for supersession)
