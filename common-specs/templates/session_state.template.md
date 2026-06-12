# Session State — Template

> **Purpose:** Initial scaffolding for `memory/sessions/session_state.md`. Copy this file to `memory/sessions/session_state.md` at first deployment; populate Session 1 fields; subsequent sessions append below.
> **Schema:** v3.0 (per SCHEMA_A18)
> **Companion:** MEMORY_PROTOCOL.md §1.2 (Tier 1 always-load), §4.4 (heartbeat), §14 (session end protocol)

---

```markdown
# Session State — Current

> **Schema Version:** 3.0
> **Current Session:** 1
> **Date:** <YYYY-MM-DD>
> **Updated:** <last-update-summary>

---

## Session 1 — Initial Setup (<YYYY-MM-DD>)

---
id: SESSION-001
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
valid_at: <YYYY-MM-DD>
source_agent: orchestrator
source_session: 1
status: active
schema_version: "3.0"
---

### Session Summary
[2-3 sentences: what we worked on, what was accomplished]

### What Was In Progress
[Any task that was started but not finished — include file names, line numbers, specific details]

### Pending Items
[Ordered list of what needs to happen next]

### Active Decisions
[Inline decisions made this session — to be promoted to decisions.md when topic accumulates >5 related entries per MEMORY_PROTOCOL.md §12]

### Key Files Modified Recently
[List of files changed in last 1-2 sessions with brief description]

### Blockers / Waiting On
[Anything we can't proceed on and why]

### Heartbeat — Current Work (last updated <HH:MM>)
[Per MEMORY_PROTOCOL.md §4.4: ~30-minute checkpoint. Updates here prevent context loss if session ends unexpectedly]
- Task: <what>
- File: <path:line>
- Status: <progress>
- Blocker (if any): <description>

---

(Append future sessions below. Older sessions archive to `memory/archive/` once file exceeds 150-line limit per MEMORY_PROTOCOL.md §11.)
```

---

## Usage notes

- **session_state.md is the lifeline.** First file loaded every session (Tier 1). Make it informative.
- **Be specific:** "Fixed the bug in auth.py" is useless next session. "Fixed race condition in auth.py:47 where token refresh wasn't awaited — changed to `await refresh_token()` and added 3-second backoff retry" is useful.
- **Heartbeat early, heartbeat often:** Don't wait until session end. ~30-min intervals during active work; ~10-min if approaching context limit (pre-compact).
- **Confidence levels on Active Decisions:** Mark each as FINAL / TENTATIVE / EXPLORATORY per SCHEMA_A18.
- **Size cap:** 150 lines per MEMORY_PROTOCOL.md §11. Archive older sessions to `memory/archive/`.

## Cross-references

- `MEMORY_PROTOCOL.md` §1 (session start), §4.4 (heartbeat), §11 (size limits), §14 (session end)
- `SCHEMA_A18` (entry metadata structure)
- `MEMORY_INDEX.md` (this file is registered)
