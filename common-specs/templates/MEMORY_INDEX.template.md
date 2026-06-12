# MEMORY_INDEX — Template

> **Purpose:** Scaffolding for `memory/MEMORY_INDEX.md`. Master registry of all memory entries by category. Updated whenever entries are added/removed/consolidated.
> **Schema:** v3.0 (this file is the index; lives at `memory/MEMORY_INDEX.md` not in templates)
> **Companion:** MEMORY_PROTOCOL.md §10 (self-trimming uses Last Accessed column), §11 (this file is size-limited)

---

```markdown
# Memory Index — Master Registry

> **Schema Version:** 3.0
> **Created:** <YYYY-MM-DD>
> **Total Entries:** 0 (initial)
> **Last Updated:** <YYYY-MM-DD>

---

## Category Summary

### Active (populated — backtick refs trigger T5 existence check)

| Category | File | Entries | Last Updated | Last Accessed |
|----------|------|---------|--------------|---------------|
| User Profile | `user/user_profile.md` | 1 | <YYYY-MM-DD> | <session-N> |
| Sessions | `sessions/session_state.md` | <N> | <YYYY-MM-DD> | <session-N> |
| Feedback | `feedback/feedback.md` | <N> | <YYYY-MM-DD> | <session-N> |
| Projects | `projects/project_context.md` | <N> | <YYYY-MM-DD> | <session-N> |

### Future categories (created on first use — plain text, NOT linked, so T5 self-test ignores)

- Decisions — decisions/decisions.md (created on first DEC-NNN entry)
- Security vetting — security/vetting_log.md (created on first vetting event)
- References — references/references.md (created on first cross-ref entry)
- Audit log — security/audit_log.jsonl (biotech: pre-created; general: opt-in)
- Quarantine — quarantine/quarantine_log.jsonl (biotech: pre-created; general: opt-in)

> Promote rows from Future → Active by adding backticks around the file path and filling the Entries / Last Updated / Last Accessed columns once the file exists. (keeps the T5 self-test green pre-population.)

---

## Recent Entries (Last Session)

- <Entry ID>: <one-line summary>
- ...

---

## Quick Access — Critical Files

### Active (populated)

| Purpose | File |
|---------|------|
| Current session state | `sessions/session_state.md` |
| User preferences | `feedback/feedback.md` |
| Edition profile | `<path-to-PROFILE.md>` |

> Fill the PROFILE path for your install method: script/Skill installs keep it at `../ultimate-memory-stack/<edition>-edition/PROFILE.md`; manual installs copy it to `PROFILE.md` (vault root).

### Future (created on first use — not linked until populated)

- All decisions — decisions/decisions.md
- Security audit trail — security/audit_log.jsonl
- Quarantine queue — quarantine/quarantine_log.jsonl
- File location lookup — references/references.md
- Vetting log — security/vetting_log.md

---

## Per-Project Memory Banks

| Project Slug | Status | Path |
|--------------|--------|------|
| `<slug-1>` | active | `projects/<slug-1>/memory-bank/` |
| `<slug-2>` | paused | `projects/<slug-2>/memory-bank/` |

(See `projects/project_context.md` for full project details.)

---

## Schema Notes

- All files conform to **Schema Version 3.0** (SCHEMA_A18 frontmatter required)
- Entry IDs: DEC-NNN (decisions), FB-NNN (feedback), PRJ-NNN (projects), VET-NNN (vetting), CR-NNN (code reviews), REF-NNN (references), SESSION-NNN (session-state entries)
- Confidence levels (decisions only): FINAL, TENTATIVE, EXPLORATORY
- Status values: active, superseded, quarantined, archived, discarded
- Bi-temporal fields (B5): `valid_at` / `invalid_at` — biotech enforced, general available
- This index updates whenever entries are added/removed/consolidated
- Last Accessed column powers self-trimming protocol (MEMORY_PROTOCOL.md §10)
```

---

## Usage notes

- **Size-strict:** 80 lines per MEMORY_PROTOCOL.md §11. This file is JUST POINTERS — don't bloat with content.
- **Last Accessed enables self-trimming:** Update this column on every Tier 1/2/3 load of the corresponding file
- **Update on consolidation:** When entries get promoted/archived/discarded, refresh counts and dates
- **Critical files quick-access:** Keep that table current — it's the operator's at-a-glance map of where things live
- **Per-project memory banks separately tracked:** The main index summarizes; full project state in `projects/<slug>/memory-bank/`

## Cross-references

- `MEMORY_PROTOCOL.md` §10 (self-trimming uses Last Accessed), §11 (80-line size cap)
- `SCHEMA_A18` (entry ID conventions, status values, confidence levels)
- `SCHEMA_A3` (per-project memory bank — index lists projects, content lives in memory-bank)
