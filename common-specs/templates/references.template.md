# References — Template

> **Purpose:** Scaffolding for `memory/references/references.md`. Holds file-location pointers and quick-access map. Loaded on demand (Tier 3) when a specific file needs to be found.
> **Schema:** v3.0 (per SCHEMA_A18)
> **Companion:** MEMORY_PROTOCOL.md §1.2 Tier 3

---

```markdown
# References — File Location Map

> **Schema Version:** 3.0
> **Last Updated:** <YYYY-MM-DD>

---

## REF-001: <Topic — e.g., "Claude Code logs location">

---
id: REF-001
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
last_validated: <YYYY-MM-DD>
source_agent: orchestrator
source_session: <N>
status: active
schema_version: "3.0"
tags: [<category>, <tool>]
---

**Topic:** [What this references]

**Path:** `<absolute or relative path>`

**Purpose:** [What's at this location — 1 sentence]

**When to load:** [Which session contexts make this useful]

**Notes:** [Any caveats — e.g., requires admin, large file, etc.]

---

## REF-002: <Next reference>

[Same structure]
```

---

## Worked examples

```markdown
## REF-001: Claude Code logs

---
id: REF-001
created_at: 2026-04-09
last_validated: 2026-05-14
source_agent: orchestrator
source_session: 1
status: active
schema_version: "3.0"
tags: [logs, claude-code, infrastructure]
---

**Topic:** Shared logs across Claude Code + Desktop instances

**Path:** `<YOUR_WORKSPACE>`

**Purpose:** Auto-logged errors, ongoing projects log, MCP server bug tracker

**When to load:** When investigating system issues, listing project history, or auditing MCP behavior

**Notes:**
- `Access_Restrictions_Log.md` — capabilities pending admin (Code Exec, Skills, Web Search, Node.js)
- `Ongoing_Projects_Log.md` — work project history
- `MCP_Server_Error_Log.md` — primary timeout trigger: filesystem MCP edit_file (prefer write_file)


## REF-002: Cross-instance sync

---
id: REF-002
created_at: 2026-04-09
last_validated: 2026-05-14
tags: [sync, cross-instance, claude-desktop]
---

**Topic:** Cross-instance communication (Desktop ↔ Code)

**Path:** `<YOUR_WORKSPACE>`

**Purpose:** Shared state for handoffs between Claude Desktop chat and Claude Code CLI

**When to load:** At session start (already in CLAUDE.md auto-load); when switching instances

**Notes:**
- `SYNC_PROTOCOL.md` — communication rules
- `sync_state.md` — current handoff state
- `decision_log.md` — append-only decision archive
- `task_queue.md` — tasks assigned to each instance


## REF-003: Design-docs canonical location

---
id: REF-003
created_at: 2026-05-12
last_validated: 2026-05-14
tags: [design-docs, canonical]
---

**Topic:** Design-docs source-of-truth location (DEC-020 mirror rule)

**Path:** `<primary-location>`

**Purpose:** Canonical home for design research, plans, and memory-stack design artifacts

**When to load:** When working on memory stack design; when verifying mirror parity (DEC-020)

**Notes:**
- `<primary-location>` is source of truth; `<mirror-location>` is the working mirror
- Both must stay byte-parity (mirror discipline)
- v3.0 design lives at `common-specs/` (8 files as of 2026-05-14)
```

## Usage notes

- **Tier 3 loading:** Loaded on demand only, when a specific file/location is needed
- **last_validated matters:** References can rot — file paths change, permissions change. Re-validate on use; update last_validated if still accurate.
- **Group by topic:** Use tags consistently (e.g., `logs`, `sync`, `external-docs`, `tool-paths`)
- **Don't duplicate content:** This is a POINTER file. Actual content lives at the referenced path.
- **Size cap:** 100 lines per MEMORY_PROTOCOL.md §11. Split by domain (per-project, per-tool) at the size limit.

## Cross-references

- `MEMORY_PROTOCOL.md` §1.2 (Tier 3 load), §11 (size limits)
- `SCHEMA_A18` (entry metadata)
- `DEC-020` (example: your mirror-rule decision)
